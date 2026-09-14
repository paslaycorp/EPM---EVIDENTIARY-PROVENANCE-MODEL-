from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
from epm.constraints import Constraint, ConstraintStatus, EntailmentStatus, PremiseState
from epm.resolution import AnswerSpaceSnapshot, EpistemicStanding, ResolutionState
from epm.temporal import TemporalAvailability


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_temporal_parity", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


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


def _reverify(snapshot, admissible):
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def _condition(name: str, *, available: bool = True):
    return tvc.HistoricalCondition(
        obligation_id=name,
        status=tvc.ObligationStatus.SATISFIED,
        available_at_claim_time=available,
        provenance_valid=True,
    )


def _state(*, claim_time: datetime, rule_effective_at: datetime, evidence_available_at: datetime) -> EvidentiaryState:
    rule = RuleBinding(
        rule_id="rule-temporal-inference-v1",
        version="1.0",
        authority="tvc-experiment",
        effective_at=rule_effective_at,
    )
    assurance = State(
        state_id="evidence-temporal-X",
        properties={"evidence": AssuranceState.VALID},
        context=AssuranceContext(at=claim_time),
        rule=rule,
    )
    availability = EvidenceAvailability(
        evidence_id=assurance.state_id,
        available_at=evidence_available_at,
        observed_at=max(evidence_available_at, claim_time),
        source="canonical-temporal-fixture",
        provenance_ref="prov-temporal-X",
        attestation=AvailabilityAttestation(
            attestation_id="att-temporal-X",
            authority="fixture-authority",
            method="signed-test-fixture",
            basis="same temporal facts supplied to EPM and TVC",
            validated=True,
        ),
    )
    constraint = Constraint(
        constraint_id="constraint-temporal-X",
        proposition="X",
        premise_refs=("support-X",),
        premise_states={"support-X": PremiseState.ESTABLISHED},
        provenance_refs=("prov-temporal-X",),
        entailment_basis="rule-temporal-inference-v1",
        entailment_status=EntailmentStatus.ESTABLISHED,
        source_ref="canonical-temporal-fixture",
    )
    answer_space = AnswerSpaceSnapshot(
        question_id="question-temporal-X",
        candidate_universe=("X", "not-X"),
        admissible_candidates=("X", "not-X"),
        resolution_state=ResolutionState.UNRESOLVED,
        epistemic_standing=EpistemicStanding.INFERRED,
        granularity="binary proposition",
        granularity_basis="fixture evaluates X versus not-X",
    )
    return EvidentiaryState(
        state_id="state-temporal-X",
        proposition="X",
        assurance_state=assurance,
        availability=(availability,),
        constraints=(constraint,),
        answer_space=answer_space,
    )


def test_future_rule_effective_time_delta_is_retired_after_epm_remediation():
    """A future-effective rule is now rejected by both the EPM control and TVC.

    TVC originally exposed this defect under equal information. EPM absorbed the
    invariant, so this case must remain as overlap evidence rather than continue
    to count as incremental TVC assurance.
    """
    claim_time = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)
    rule_time = claim_time + timedelta(days=1)
    epm_state = _state(
        claim_time=claim_time,
        rule_effective_at=rule_time,
        evidence_available_at=claim_time,
    )

    epm_report = inspect_state(epm_state)
    assert epm_state.assurance_state.rule.effective_at == rule_time
    assert "RULE_NOT_YET_EFFECTIVE" in epm_report.structural_issues
    assert _epm_failure_count(epm_report) > 0

    snapshot = tvc.EpistemicSnapshot(
        state_id=epm_state.state_id,
        proposition=epm_state.proposition,
        asserted_standing="INFERRED",
        claimed_at=claim_time.isoformat(),
        conditions={
            "support": _condition("support"),
            "provenance": _condition("provenance"),
            "entailment": _condition("entailment", available=False),
            "contradictions": _condition("contradictions"),
        },
    )
    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)

    assert result.status is tvc.ClosureStatus.FAILED
    assert result.closure_boundary == "entailment"
    assert result.reproduced_standing == "EVIDENCED"


def test_future_evidence_is_overlap_not_tvc_unique_value():
    """When evidence itself is future-dated, current EPM already catches it."""
    claim_time = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)
    epm_state = _state(
        claim_time=claim_time,
        rule_effective_at=claim_time,
        evidence_available_at=claim_time + timedelta(hours=1),
    )
    epm_report = inspect_state(epm_state)

    assert any(
        result.status is TemporalAvailability.UNAVAILABLE
        and result.reason_code == "EVIDENCE_NOT_YET_AVAILABLE"
        for result in epm_report.availability_results
    )
    assert _epm_failure_count(epm_report) > 0

    snapshot = tvc.EpistemicSnapshot(
        state_id=epm_state.state_id,
        proposition=epm_state.proposition,
        asserted_standing="INFERRED",
        claimed_at=claim_time.isoformat(),
        conditions={
            "support": _condition("support", available=False),
            "provenance": _condition("provenance"),
            "entailment": _condition("entailment"),
            "contradictions": _condition("contradictions"),
        },
    )
    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)
    assert result.status is tvc.ClosureStatus.FAILED
    assert result.closure_boundary == "support"


def test_rule_available_at_claim_time_closes_cleanly():
    claim_time = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)
    epm_state = _state(
        claim_time=claim_time,
        rule_effective_at=claim_time,
        evidence_available_at=claim_time,
    )
    assert _epm_failure_count(inspect_state(epm_state)) == 0

    snapshot = tvc.EpistemicSnapshot(
        state_id=epm_state.state_id,
        proposition=epm_state.proposition,
        asserted_standing="INFERRED",
        claimed_at=claim_time.isoformat(),
        conditions={
            "support": _condition("support"),
            "provenance": _condition("provenance"),
            "entailment": _condition("entailment"),
            "contradictions": _condition("contradictions"),
        },
    )
    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)
    assert result.status is tvc.ClosureStatus.CLOSED
    assert result.reproduced_standing == "INFERRED"
