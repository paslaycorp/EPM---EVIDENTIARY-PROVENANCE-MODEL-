from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
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
from epm.constraints import (
    Constraint,
    ConstraintStatus,
    EntailmentStatus,
    PremiseState,
)
from epm.resolution import AnswerSpaceSnapshot, EpistemicStanding, ResolutionState
from epm.temporal import TemporalAvailability


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_parity_experiment", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


def _condition(name: str) -> tvc.HistoricalCondition:
    return tvc.HistoricalCondition(
        obligation_id=name,
        status=tvc.ObligationStatus.SATISFIED,
        available_at_claim_time=True,
        provenance_valid=True,
    )


def _reverify(snapshot, admissible):
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def _epm_failure_count(report) -> int:
    count = len(report.structural_issues) + len(report.unresolved_conditions)
    count += sum(
        result.status is not TemporalAvailability.AVAILABLE or not result.trusted
        for result in report.availability_results
    )
    count += sum(
        result.status is not ConstraintStatus.VALID
        for result in report.constraint_results
    )
    if report.answer_space_result is not None and not report.answer_space_result.valid:
        count += 1
    if report.graph_cycle_result is not None and report.graph_cycle_result.cyclic:
        count += 1
    return count


def test_tvc_adds_conclusion_conditioned_check_without_privileged_information():
    """Run EPM and TVC from the same historical facts and asserted standing.

    The historical record establishes support, provenance and entailment, and
    both systems receive the asserted INFERRED standing.  There is no
    contradiction-disposition record.  That absence is shared information;
    TVC receives no hidden contradiction fact.  Its only extra operation is to
    derive the obligations required by INFERRED and demand historical closure.
    """
    claim_time = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)

    facts = {
        "support": True,
        "provenance": True,
        "entailment": True,
        "contradictions": None,
        "asserted_standing": "INFERRED",
    }

    rule = RuleBinding(
        rule_id="rule-inference-v1",
        version="1.0",
        authority="tvc-experiment",
        effective_at=claim_time,
    )
    assurance = State(
        state_id="evidence-X",
        properties={"evidence": AssuranceState.VALID},
        context=AssuranceContext(at=claim_time),
        rule=rule,
    )
    availability = EvidenceAvailability(
        evidence_id="evidence-X",
        available_at=claim_time,
        observed_at=claim_time,
        source="canonical-fixture",
        provenance_ref="prov-X",
        attestation=AvailabilityAttestation(
            attestation_id="att-X",
            authority="fixture-authority",
            method="signed-test-fixture",
            basis="same canonical historical facts supplied to both systems",
            validated=True,
        ),
    )
    inferential_constraint = Constraint(
        constraint_id="constraint-X",
        proposition="X",
        premise_refs=("support-X",),
        premise_states={"support-X": PremiseState.ESTABLISHED},
        provenance_refs=("prov-X",),
        entailment_basis="rule-inference-v1",
        entailment_status=EntailmentStatus.ESTABLISHED,
        source_ref="canonical-fixture",
    )
    answer_space = AnswerSpaceSnapshot(
        question_id="question-X",
        candidate_universe=("X", "not-X"),
        admissible_candidates=("X", "not-X"),
        resolution_state=ResolutionState.UNRESOLVED,
        epistemic_standing=EpistemicStanding.INFERRED,
        granularity="binary proposition",
        granularity_basis="fixture evaluates X versus not-X",
    )
    epm_state = EvidentiaryState(
        state_id="state-X",
        proposition="X",
        assurance_state=assurance,
        availability=(availability,),
        constraints=(inferential_constraint,),
        answer_space=answer_space,
    )

    epm_report = inspect_state(epm_state)
    epm_failures = _epm_failure_count(epm_report)

    # TVC is adapted from the same canonical facts.  Missing information stays
    # missing; the adapter must not manufacture a contradiction disposition.
    tvc_conditions = {
        name: _condition(name)
        for name in ("support", "provenance", "entailment")
        if facts[name] is True
    }
    snapshot = tvc.EpistemicSnapshot(
        state_id="state-X",
        proposition="X",
        asserted_standing=facts["asserted_standing"],
        claimed_at=claim_time.isoformat(),
        conditions=tvc_conditions,
    )
    tvc_result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)
    tvc_failures = int(tvc_result.status is not tvc.ClosureStatus.CLOSED)

    # EPM sees the INFERRED standing and the same absence, but its current
    # inspection surface does not derive a contradiction-disposition obligation
    # from that standing.  TVC does, so the missing obligation remains explicit.
    assert epm_report.answer_space_result is not None
    assert epm_report.answer_space_result.valid
    assert epm_state.answer_space.epistemic_standing is EpistemicStanding.INFERRED
    assert epm_failures == 0
    assert tvc_result.status is tvc.ClosureStatus.UNRESOLVED
    assert tvc_result.closure_boundary == "contradictions"
    assert tvc_result.reproduced_standing == "EVIDENCED"
    assert tvc_failures - epm_failures == 1
