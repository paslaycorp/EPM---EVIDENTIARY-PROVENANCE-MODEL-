from __future__ import annotations

import importlib.util
import itertools
import random
import sys
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_blind_mirror", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


ALL = ("support", "provenance", "entailment", "contradictions")


def c(name, status=tvc.ObligationStatus.SATISFIED, *, available=True, provenance=True):
    return tvc.HistoricalCondition(name, status, available, provenance)


def snapshot(case, standing="INFERRED", *, conditions=None):
    conditions = conditions or {name: c(name) for name in ALL}
    return tvc.EpistemicSnapshot(case, "X", standing, "2026-09-06T20:56:00-05:00", conditions)


def blind_reconstruct(snapshot):
    admissible = {
        name
        for name, condition in snapshot.conditions.items()
        if condition.available_at_claim_time
        and condition.provenance_valid
        and condition.status is tvc.ObligationStatus.SATISFIED
    }
    if set(ALL).issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def generic_mirror(snapshot):
    reproduced = blind_reconstruct(snapshot)
    obligations = tuple(tvc.DEFAULT_POLICY.get(snapshot.asserted_standing, ()))
    failed, unresolved, _, boundary = tvc.validate_historical_obligations(snapshot, obligations)
    if failed:
        status = tvc.ClosureStatus.FAILED
    elif unresolved:
        status = tvc.ClosureStatus.UNRESOLVED
    elif reproduced != snapshot.asserted_standing:
        status = tvc.ClosureStatus.DEGRADED
    else:
        status = tvc.ClosureStatus.CLOSED
    return status, reproduced, failed, unresolved, boundary


def tvc_with_blind_reconstruction(snapshot):
    return tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, lambda s, _admissible: blind_reconstruct(s))


def test_blindfold_reconstruction_does_not_consult_asserted_standing():
    facts = {name: c(name) for name in ALL}
    a = snapshot("blind-evidenced", "EVIDENCED", conditions=facts)
    b = snapshot("blind-inferred", "INFERRED", conditions=facts)
    assert blind_reconstruct(a) == blind_reconstruct(b) == "INFERRED"


def test_counterfactual_standing_swap_changes_only_final_comparison():
    facts = {name: c(name) for name in ALL}
    evidenced = tvc_with_blind_reconstruction(snapshot("swap-e", "EVIDENCED", conditions=facts))
    inferred = tvc_with_blind_reconstruction(snapshot("swap-i", "INFERRED", conditions=facts))
    assert evidenced.status is tvc.ClosureStatus.DEGRADED
    assert evidenced.reproduced_standing == "INFERRED"
    assert inferred.status is tvc.ClosureStatus.CLOSED
    assert inferred.reproduced_standing == "INFERRED"


def test_equal_information_generic_mirror_matches_blind_tvc_on_curated_cases():
    cases = [
        snapshot("clean", "INFERRED"),
        snapshot("weak", "EVIDENCED"),
        snapshot("future-entailment", "INFERRED", conditions={
            "support": c("support"),
            "provenance": c("provenance"),
            "entailment": c("entailment", available=False),
            "contradictions": c("contradictions"),
        }),
        snapshot("unresolved", "INFERRED", conditions={
            "support": c("support"),
            "provenance": c("provenance"),
            "entailment": c("entailment"),
            "contradictions": c("contradictions", tvc.ObligationStatus.UNRESOLVED),
        }),
        snapshot("bad-prov", "INFERRED", conditions={
            "support": c("support"),
            "provenance": c("provenance", provenance=False),
            "entailment": c("entailment"),
            "contradictions": c("contradictions"),
        }),
    ]
    for s in cases:
        t = tvc_with_blind_reconstruction(s)
        g = generic_mirror(s)
        assert (t.status, t.reproduced_standing, t.failed, t.unresolved, t.closure_boundary) == g


def test_metamorphic_condition_order_does_not_change_blind_reconstruction():
    base_items = [(name, c(name)) for name in ALL]
    expected = None
    for permutation in itertools.permutations(base_items):
        s = snapshot("perm", "INFERRED", conditions=dict(permutation))
        result = tvc_with_blind_reconstruction(s)
        signature = (result.status, result.reproduced_standing, set(result.failed), set(result.unresolved))
        expected = expected or signature
        assert signature == expected


def test_irrelevant_condition_does_not_change_blind_reconstruction():
    base = snapshot("base", "INFERRED")
    noisy_conditions = dict(base.conditions)
    noisy_conditions["irrelevant-metadata"] = c("irrelevant-metadata")
    noisy = snapshot("noisy", "INFERRED", conditions=noisy_conditions)
    a = tvc_with_blind_reconstruction(base)
    b = tvc_with_blind_reconstruction(noisy)
    assert (a.status, a.reproduced_standing, a.failed, a.unresolved) == (
        b.status,
        b.reproduced_standing,
        b.failed,
        b.unresolved,
    )


def test_seeded_fuzz_equal_information_mirror_equivalence():
    rng = random.Random(20260906)
    statuses = (
        tvc.ObligationStatus.SATISFIED,
        tvc.ObligationStatus.FAILED,
        tvc.ObligationStatus.UNRESOLVED,
    )
    standings = ("EVIDENCED", "INFERRED")

    for i in range(500):
        conditions = {}
        for name in ALL:
            conditions[name] = c(
                name,
                rng.choice(statuses),
                available=rng.choice((True, False)),
                provenance=rng.choice((True, False)),
            )
        s = snapshot(f"fuzz-{i}", rng.choice(standings), conditions=conditions)
        t = tvc_with_blind_reconstruction(s)
        g = generic_mirror(s)
        assert (t.status, t.reproduced_standing, t.failed, t.unresolved, t.closure_boundary) == g
