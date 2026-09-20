from __future__ import annotations

import importlib.util
import random
import sys
from pathlib import Path

import pytest


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_sephiroth", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


def c(name, status=tvc.ObligationStatus.SATISFIED, *, available=True, provenance=True):
    return tvc.HistoricalCondition(name, status, available, provenance)


def snapshot(case, standing, conditions):
    return tvc.EpistemicSnapshot(
        case,
        "X",
        standing,
        "2026-09-06T20:56:00-05:00",
        conditions,
    )


def blind_reconstruct(snapshot):
    admissible = {
        name
        for name, condition in snapshot.conditions.items()
        if condition.available_at_claim_time
        and condition.provenance_valid
        and condition.status is tvc.ObligationStatus.SATISFIED
    }
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def tvc_reverify(snapshot, _admissible):
    return blind_reconstruct(snapshot)


def generic_equal_information_control(snapshot, policy):
    """Strong control: same snapshot, claim time, policy semantics, and conditions.

    It independently compiles the standing-specific duties, validates them,
    reconstructs from all historically admissible conditions, and compares the
    reconstructed standing against the assertion. It deliberately uses no TVC
    implementation functions.
    """
    obligations = tuple(policy.get(snapshot.asserted_standing, ()))
    failed = []
    unresolved = []
    boundary = None

    for obligation in obligations:
        condition = snapshot.conditions.get(obligation.obligation_id)
        if condition is None:
            unresolved.append(obligation.obligation_id)
            boundary = boundary or obligation.obligation_id
            continue
        if not condition.available_at_claim_time or not condition.provenance_valid:
            failed.append(obligation.obligation_id)
            boundary = boundary or obligation.obligation_id
            continue
        if condition.status is tvc.ObligationStatus.FAILED:
            failed.append(obligation.obligation_id)
            boundary = boundary or obligation.obligation_id
            continue
        if condition.status is tvc.ObligationStatus.UNRESOLVED:
            unresolved.append(obligation.obligation_id)
            boundary = boundary or obligation.obligation_id

    reproduced = blind_reconstruct(snapshot)
    if failed:
        status = tvc.ClosureStatus.FAILED
    elif unresolved:
        status = tvc.ClosureStatus.UNRESOLVED
    elif reproduced != snapshot.asserted_standing:
        status = tvc.ClosureStatus.DEGRADED
    else:
        status = tvc.ClosureStatus.CLOSED

    return status, reproduced, boundary, tuple(failed), tuple(unresolved)


def obligation_only(snapshot, policy):
    obligations = tuple(policy.get(snapshot.asserted_standing, ()))
    failed, unresolved, _admissible, boundary = tvc.validate_historical_obligations(snapshot, obligations)
    if failed:
        return tvc.ClosureStatus.FAILED, boundary
    if unresolved:
        return tvc.ClosureStatus.UNRESOLVED, boundary
    return tvc.ClosureStatus.CLOSED, boundary


def test_sephiroth_equal_information_control_reproduces_tvc_matrix():
    cases = [
        snapshot(
            "clean-inferred",
            "INFERRED",
            {
                "support": c("support"),
                "provenance": c("provenance"),
                "entailment": c("entailment"),
                "contradictions": c("contradictions"),
            },
        ),
        snapshot(
            "weaker-assertion",
            "EVIDENCED",
            {
                "support": c("support"),
                "provenance": c("provenance"),
                "entailment": c("entailment"),
                "contradictions": c("contradictions"),
            },
        ),
        snapshot(
            "future-entailment",
            "INFERRED",
            {
                "support": c("support"),
                "provenance": c("provenance"),
                "entailment": c("entailment", available=False),
                "contradictions": c("contradictions"),
            },
        ),
        snapshot(
            "unresolved-contradiction",
            "INFERRED",
            {
                "support": c("support"),
                "provenance": c("provenance"),
                "entailment": c("entailment"),
                "contradictions": c("contradictions", tvc.ObligationStatus.UNRESOLVED),
            },
        ),
        snapshot(
            "bad-provenance",
            "EVIDENCED",
            {
                "support": c("support"),
                "provenance": c("provenance", provenance=False),
                "entailment": c("entailment"),
                "contradictions": c("contradictions"),
            },
        ),
    ]

    for s in cases:
        actual = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, tvc_reverify)
        control = generic_equal_information_control(s, tvc.DEFAULT_POLICY)
        assert (
            actual.status,
            actual.reproduced_standing,
            actual.closure_boundary,
            actual.failed,
            actual.unresolved,
        ) == control


def test_sephiroth_forward_reverification_has_incremental_effect_over_obligation_only():
    s = snapshot(
        "reverify-delta",
        "EVIDENCED",
        {
            "support": c("support"),
            "provenance": c("provenance"),
            "entailment": c("entailment"),
            "contradictions": c("contradictions"),
        },
    )
    ablated, _ = obligation_only(s, tvc.DEFAULT_POLICY)
    full = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, tvc_reverify)

    assert ablated is tvc.ClosureStatus.CLOSED
    assert full.status is tvc.ClosureStatus.DEGRADED
    assert full.reproduced_standing == "INFERRED"


def test_sephiroth_asserted_standing_is_not_visible_to_blind_reconstruction():
    conditions = {
        "support": c("support"),
        "provenance": c("provenance"),
        "entailment": c("entailment"),
        "contradictions": c("contradictions"),
    }
    results = {
        standing: blind_reconstruct(snapshot("blind-" + standing.lower(), standing, conditions))
        for standing in ("EVIDENCED", "INFERRED", "UNKNOWN")
    }
    assert set(results.values()) == {"INFERRED"}


def test_sephiroth_random_equal_information_differential_2000_cases():
    rng = random.Random(0x5E9A1)
    names = ("support", "provenance", "entailment", "contradictions")
    statuses = tuple(tvc.ObligationStatus)

    for i in range(2000):
        conditions = {}
        for name in names:
            conditions[name] = c(
                name,
                rng.choice(statuses),
                available=rng.choice((True, False)),
                provenance=rng.choice((True, False)),
            )
        standing = rng.choice(("EVIDENCED", "INFERRED", "UNKNOWN"))
        s = snapshot(f"fuzz-{i}", standing, conditions)

        actual = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, tvc_reverify)
        control = generic_equal_information_control(s, tvc.DEFAULT_POLICY)
        assert (
            actual.status,
            actual.reproduced_standing,
            actual.closure_boundary,
            actual.failed,
            actual.unresolved,
        ) == control


def test_sephiroth_irrelevant_fact_invariance():
    base = {
        "support": c("support"),
        "provenance": c("provenance"),
        "entailment": c("entailment"),
        "contradictions": c("contradictions"),
    }
    a = snapshot("irrelevant-a", "INFERRED", base)
    b = snapshot("irrelevant-b", "INFERRED", {**base, "irrelevant": c("irrelevant")})

    ra = tvc.evaluate_closure(a, tvc.DEFAULT_POLICY, tvc_reverify)
    rb = tvc.evaluate_closure(b, tvc.DEFAULT_POLICY, tvc_reverify)
    assert ra.status == rb.status
    assert ra.reproduced_standing == rb.reproduced_standing
    assert ra.failed == rb.failed
    assert ra.unresolved == rb.unresolved


@pytest.mark.parametrize("standing", ["EVIDENCED", "INFERRED", "UNKNOWN"])
def test_sephiroth_deterministic_replay_250_runs(standing):
    s = snapshot(
        "determinism-" + standing.lower(),
        standing,
        {
            "support": c("support"),
            "provenance": c("provenance"),
            "entailment": c("entailment", available=False),
            "contradictions": c("contradictions", tvc.ObligationStatus.UNRESOLVED),
        },
    )
    runs = [tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, tvc_reverify) for _ in range(250)]
    assert all(result == runs[0] for result in runs)
