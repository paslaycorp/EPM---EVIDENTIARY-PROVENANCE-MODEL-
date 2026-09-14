from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_static_compilation_attack", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


def condition(name: str, status=tvc.ObligationStatus.SATISFIED, *, available=True, provenance=True):
    return tvc.HistoricalCondition(
        obligation_id=name,
        status=status,
        available_at_claim_time=available,
        provenance_valid=provenance,
    )


def reverify(snapshot, admissible):
    if snapshot.asserted_standing == "EVIDENCED":
        return "EVIDENCED" if {"support", "provenance"}.issubset(admissible) else "UNKNOWN"
    if snapshot.asserted_standing == "INFERRED":
        if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
            return "INFERRED"
        if {"support", "provenance"}.issubset(admissible):
            return "EVIDENCED"
    return "UNKNOWN"


def compiled_static_validator(snapshot, policy):
    """Compile TVC's current fixed policy into ordinary standing-specific checks.

    This deliberately omits TVC's reverse/forward orchestration.  If it predicts
    the same closure acceptance for all fixtures, current TVC semantics are
    reducible to a static validator for this policy domain.
    """
    required = tuple(o.obligation_id for o in policy.get(snapshot.asserted_standing, ()))
    admissible = set()
    failed = []
    unresolved = []
    for obligation_id in required:
        c = snapshot.conditions.get(obligation_id)
        if c is None or c.status is tvc.ObligationStatus.UNRESOLVED:
            unresolved.append(obligation_id)
            continue
        if not c.available_at_claim_time or not c.provenance_valid or c.status is tvc.ObligationStatus.FAILED:
            failed.append(obligation_id)
            continue
        admissible.add(obligation_id)
    reproduced = reverify(snapshot, frozenset(admissible))
    closed = not failed and not unresolved and reproduced == snapshot.asserted_standing
    return closed, reproduced, tuple(failed), tuple(unresolved)


FIXTURES = (
    ("clean-inferred", "INFERRED", {
        "support": condition("support"), "provenance": condition("provenance"),
        "entailment": condition("entailment"), "contradictions": condition("contradictions")}),
    ("missing-contradiction", "INFERRED", {
        "support": condition("support"), "provenance": condition("provenance"), "entailment": condition("entailment")}),
    ("future-rule", "INFERRED", {
        "support": condition("support"), "provenance": condition("provenance"),
        "entailment": condition("entailment", available=False), "contradictions": condition("contradictions")}),
    ("bad-provenance", "INFERRED", {
        "support": condition("support"), "provenance": condition("provenance", provenance=False),
        "entailment": condition("entailment"), "contradictions": condition("contradictions")}),
    ("clean-evidenced", "EVIDENCED", {"support": condition("support"), "provenance": condition("provenance")}),
)


@pytest.mark.parametrize("case_id,standing,conditions", FIXTURES, ids=lambda x: x if isinstance(x, str) else None)
def test_current_fixed_tvc_policy_is_compilable_to_static_validation(case_id, standing, conditions):
    snapshot = tvc.EpistemicSnapshot(
        state_id=case_id,
        proposition="X",
        asserted_standing=standing,
        claimed_at="2026-09-06T20:56:00+00:00",
        conditions=conditions,
    )
    tvc_result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, reverify)
    static_closed, static_reproduced, static_failed, static_unresolved = compiled_static_validator(snapshot, tvc.DEFAULT_POLICY)

    assert static_closed is (tvc_result.status is tvc.ClosureStatus.CLOSED)
    assert static_reproduced == tvc_result.reproduced_standing
    assert set(static_failed) == set(tvc_result.failed)
    assert set(static_unresolved) == set(tvc_result.unresolved)


def test_attack_result_documents_current_boundary():
    """The current DEFAULT_POLICY is intentionally fixed and therefore compilable.

    This is a falsification result, not a TVC victory: v0.1 does not yet prove a
    non-static mechanism.  The next candidate boundary must involve obligations
    generated from runtime justification structure rather than a fixed standing table.
    """
    assert set(tvc.DEFAULT_POLICY) == {"EVIDENCED", "INFERRED"}
