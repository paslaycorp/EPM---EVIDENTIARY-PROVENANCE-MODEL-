from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pytest

from epm import (
    AssuranceContext,
    AssuranceState,
    AvailabilityAttestation,
    EvidenceAvailability,
    EvidentiaryState,
    RuleBinding,
    State,
    inspect_state,
)
from epm.constraints import (
    Constraint,
    ConstraintStatus,
    EntailmentStatus,
    PremiseState,
)
from epm.resolution import AnswerSpaceSnapshot, EpistemicStanding, ResolutionState
from epm.temporal import TemporalAvailability


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_differential_matrix", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


@dataclass(frozen=True)
class Case:
    case_id: str
    support: bool
    provenance: bool
    entailment: str  # ESTABLISHED | UNKNOWN | CONTRADICTED
    contradictions: str  # SATISFIED | UNRESOLVED | FAILED
    expected_epm_failure: bool
    expected_tvc_status: tvc.ClosureStatus
    expected_delta: int


CASES = (
    # Positive-delta case: EPM currently has no status-derived contradiction-disposition check.
    Case("missing-contradiction-disposition", True, True, "ESTABLISHED", "UNRESOLVED", False, tvc.ClosureStatus.UNRESOLVED, 1),
    # Clean control: TVC must not manufacture a failure when every obligation is satisfied.
    Case("clean-closure", True, True, "ESTABLISHED", "SATISFIED", False, tvc.ClosureStatus.CLOSED, 0),
    # Existing EPM semantics already catch explicit contradiction; TVC must not claim unique value.
    Case("explicit-contradiction", True, True, "CONTRADICTED", "FAILED", True, tvc.ClosureStatus.FAILED, 0),
    # Existing EPM semantics already catch missing entailment; TVC may also fail/unresolve but delta must be zero.
    Case("missing-entailment", True, True, "UNKNOWN", "SATISFIED", True, tvc.ClosureStatus.FAILED, 0),
    # False-positive guard: evidence-level standing should not inherit INFERRED-only contradiction obligations.
    Case("evidenced-no-inference-duty", True, True, "ESTABLISHED", "UNRESOLVED", False, tvc.ClosureStatus.CLOSED, 0),
)


def _epm_failure_count(report) -> int:
    count = len(report.structural_issues) + len(report.unresolved_conditions)
    count += sum(
        result.status is not TemporalAvailability.AVAILABLE or not result.trusted
        for result in report.availability_results
    )
    count += sum(result.status is not ConstraintStatus.VALID for result in report.constraint_results)
    if report.answer_space_result is not None and not report.answer_space_result.valid:
        count += 1
    if report.graph_cycle_result is not None and report.graph_cycle_result.cyclic:
        count += 1
    return count


def _condition(name: str, status: tvc.ObligationStatus = tvc.ObligationStatus.SATISFIED):
    return tvc.HistoricalCondition(
        obligation_id=name,
        status=status,
        available_at_claim_time=True,
        provenance_valid=True,
    )


def _reverify(snapshot, admissible):
    if snapshot.asserted_standing == "EVIDENCED":
        return "EVIDENCED" if {"support", "provenance"}.issubset(admissible) else "UNKNOWN"
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def _build_epm_state(case: Case, asserted_standing: EpistemicStanding) -> EvidentiaryState:
    claim_time = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)
    rule = RuleBinding(
        rule_id="rule-inference-v1",
        version="1.0",
        authority="tvc-experiment",
        effective_at=claim_time,
    )
    assurance = State(
        state_id=f"evidence-{case.case_id}",
        properties={"evidence": AssuranceState.VALID},
        context=AssuranceContext(at=claim_time),
        rule=rule,
    )
    availability = EvidenceAvailability(
        evidence_id=assurance.state_id,
        available_at=claim_time,
        observed_at=claim_time,
        source="canonical-fixture",
        provenance_ref=f"prov-{case.case_id}",
        attestation=AvailabilityAttestation(
            attestation_id=f"att-{case.case_id}",
            authority="fixture-authority",
            method="signed-test-fixture",
            basis="same canonical historical facts supplied to both systems",
            validated=True,
        ),
    )

    if case.entailment == "ESTABLISHED":
        entailment_status = EntailmentStatus.ESTABLISHED
    elif case.entailment == "CONTRADICTED":
        entailment_status = EntailmentStatus.CONTRADICTED
    else:
        entailment_status = EntailmentStatus.UNESTABLISHED

    premise_state = PremiseState.ESTABLISHED if case.support else PremiseState.UNKNOWN
    constraint = Constraint(
        constraint_id=f"constraint-{case.case_id}",
        proposition="X",
        premise_refs=("support-X",),
        premise_states={"support-X": premise_state},
        provenance_refs=(availability.provenance_ref,) if case.provenance else (),
        entailment_basis="rule-inference-v1" if case.entailment == "ESTABLISHED" else "",
        entailment_status=entailment_status,
        source_ref="canonical-fixture",
    )
    answer_space = AnswerSpaceSnapshot(
        question_id=f"question-{case.case_id}",
        candidate_universe=("X", "not-X"),
        admissible_candidates=("X", "not-X"),
        resolution_state=ResolutionState.UNRESOLVED,
        epistemic_standing=asserted_standing,
        granularity="binary proposition",
        granularity_basis="fixture evaluates X versus not-X",
    )
    return EvidentiaryState(
        state_id=f"state-{case.case_id}",
        proposition="X",
        assurance_state=assurance,
        availability=(availability,),
        constraints=(constraint,),
        answer_space=answer_space,
    )


def _build_tvc_snapshot(case: Case, asserted_standing: str) -> tvc.EpistemicSnapshot:
    conditions = {}
    if case.support:
        conditions["support"] = _condition("support")
    if case.provenance:
        conditions["provenance"] = _condition("provenance")

    if case.entailment == "ESTABLISHED":
        conditions["entailment"] = _condition("entailment")
    elif case.entailment == "CONTRADICTED":
        conditions["entailment"] = _condition("entailment", tvc.ObligationStatus.FAILED)
    elif asserted_standing == "INFERRED":
        # Missing/unknown entailment remains explicit rather than fabricated.
        conditions["entailment"] = _condition("entailment", tvc.ObligationStatus.FAILED)

    if case.contradictions == "SATISFIED":
        conditions["contradictions"] = _condition("contradictions")
    elif case.contradictions == "FAILED":
        conditions["contradictions"] = _condition("contradictions", tvc.ObligationStatus.FAILED)
    # UNRESOLVED intentionally means no disposition record is fabricated.

    return tvc.EpistemicSnapshot(
        state_id=f"state-{case.case_id}",
        proposition="X",
        asserted_standing=asserted_standing,
        claimed_at="2026-09-06T20:56:00+00:00",
        conditions=conditions,
    )


@pytest.mark.parametrize("case", CASES, ids=lambda c: c.case_id)
def test_tvc_differential_assurance_matrix(case: Case):
    asserted = EpistemicStanding.EVIDENCED if case.case_id == "evidenced-no-inference-duty" else EpistemicStanding.INFERRED

    epm_state = _build_epm_state(case, asserted)
    epm_report = inspect_state(epm_state)
    epm_failures = _epm_failure_count(epm_report)

    snapshot = _build_tvc_snapshot(case, asserted.value)
    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)
    tvc_failures = int(result.status is not tvc.ClosureStatus.CLOSED)

    assert (epm_failures > 0) is case.expected_epm_failure
    assert result.status is case.expected_tvc_status

    # Differential value is binary at the case level: TVC earns +1 only where
    # it correctly identifies a closure defect that current EPM inspection does not.
    delta = int(tvc_failures > 0 and epm_failures == 0)
    assert delta == case.expected_delta

    if case.case_id == "missing-contradiction-disposition":
        assert result.closure_boundary == "contradictions"
        assert result.reproduced_standing == "EVIDENCED"
    if case.case_id == "clean-closure":
        assert result.closure_boundary is None
        assert result.reproduced_standing == "INFERRED"
    if case.case_id == "evidenced-no-inference-duty":
        assert all(obligation.obligation_id != "contradictions" for obligation in result.obligations)
