from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_kamehameha", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


def c(name, status=tvc.ObligationStatus.SATISFIED, *, available=True, provenance=True):
    return tvc.HistoricalCondition(name, status, available, provenance)


def reverify(snapshot, admissible):
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def snapshot(case, standing="INFERRED", **overrides):
    conditions = {
        "support": c("support"),
        "provenance": c("provenance"),
        "entailment": c("entailment"),
        "contradictions": c("contradictions"),
    }
    conditions.update(overrides)
    return tvc.EpistemicSnapshot(case, "X", standing, "2026-09-06T20:56:00-05:00", conditions)


def ablated_no_reverify(s):
    obligations = tvc.derive_obligations(s, tvc.DEFAULT_POLICY)
    failed, unresolved, admissible, boundary = tvc.validate_historical_obligations(s, obligations)
    return not failed and not unresolved, admissible, boundary


def test_alexander_future_justification_cannot_cross_historical_boundary():
    s = snapshot("alexander", entailment=c("entailment", available=False))
    result = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, reverify)
    assert result.status is tvc.ClosureStatus.FAILED
    assert result.closure_boundary == "entailment"
    assert result.reproduced_standing == "EVIDENCED"


def test_phoenix_invalidated_support_cannot_resurrect_old_standing():
    s = snapshot("phoenix", support=c("support", status=tvc.ObligationStatus.FAILED))
    result = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, reverify)
    assert result.status is tvc.ClosureStatus.FAILED
    assert result.reproduced_standing == "UNKNOWN"


def test_buster_sword_records_conclusion_conditioned_reproduction():
    inferred = snapshot("claim-inferred", "INFERRED")
    evidenced = snapshot("claim-evidenced", "EVIDENCED")
    ri = tvc.evaluate_closure(inferred, tvc.DEFAULT_POLICY, reverify)
    re = tvc.evaluate_closure(evidenced, tvc.DEFAULT_POLICY, reverify)
    assert ri.status is tvc.ClosureStatus.CLOSED
    assert re.status is tvc.ClosureStatus.CLOSED
    assert ri.reproduced_standing == "INFERRED"
    assert re.reproduced_standing == "EVIDENCED"


def test_buster_sword_records_reverify_uses_only_assertion_derived_admissible_set():
    s = snapshot("reverify-conditioned", "EVIDENCED")
    obligation_only_closed, admissible, _ = ablated_no_reverify(s)
    full = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, reverify)

    assert obligation_only_closed is True
    assert admissible == frozenset({"support", "provenance"})
    assert full.status is tvc.ClosureStatus.CLOSED
    assert full.reproduced_standing == "EVIDENCED"


@pytest.mark.parametrize(
    "case,s,expected",
    [
        ("clean", snapshot("clean"), tvc.ClosureStatus.CLOSED),
        ("future-rule", snapshot("future-rule", entailment=c("entailment", available=False)), tvc.ClosureStatus.FAILED),
        ("unresolved-contradiction", snapshot("unresolved", contradictions=c("contradictions", tvc.ObligationStatus.UNRESOLVED)), tvc.ClosureStatus.UNRESOLVED),
        ("invalid-provenance", snapshot("bad-prov", provenance=c("provenance", provenance=False)), tvc.ClosureStatus.FAILED),
        ("weaker-assertion", snapshot("weak", "EVIDENCED"), tvc.ClosureStatus.CLOSED),
    ],
)
def test_knights_matrix(case, s, expected):
    result = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, reverify)
    assert result.status is expected


def test_bahamut_zero_deterministic_replay():
    s = snapshot("bahamut-zero", contradictions=c("contradictions", tvc.ObligationStatus.UNRESOLVED))
    runs = [tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, reverify) for _ in range(100)]
    assert all(result == runs[0] for result in runs)


def test_bahamut_zero_permutation_invariance_of_outcome():
    base = snapshot(
        "permutation",
        entailment=c("entailment", available=False),
        contradictions=c("contradictions", tvc.ObligationStatus.UNRESOLVED),
    )
    reversed_policy = {
        **tvc.DEFAULT_POLICY,
        "INFERRED": tuple(reversed(tvc.DEFAULT_POLICY["INFERRED"])),
    }
    a = tvc.evaluate_closure(base, tvc.DEFAULT_POLICY, reverify)
    b = tvc.evaluate_closure(base, reversed_policy, reverify)
    assert a.status == b.status == tvc.ClosureStatus.FAILED
    assert set(a.failed) == set(b.failed)
    assert set(a.unresolved) == set(b.unresolved)
    # Priority is explicit policy data; tuple order no longer chooses a boundary.
    # The pre-repair counterexample remains recorded at parent 5597b0b.
    assert a == b
