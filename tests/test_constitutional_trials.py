from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

from epm import (
    AssuranceContext,
    AssuranceState,
    AvailabilityAttestation,
    Constraint,
    EntailmentStatus,
    EvidenceAvailability,
    EvidentiaryEnvelope,
    EvidentiaryState,
    PremiseState,
    PreservationProof,
    RuleBinding,
    State,
    assess_temporal_availability,
    assess_transition,
    inspect_state,
)
from epm.resolution import (
    AnswerSpaceOperation,
    EpistemicStanding,
    ResolutionState,
    create_answer_space,
    recompute_with_constraints,
    record_derivation,
)
from epm.sources import (
    EpistemicSourceRecord,
    EpistemicSourceType,
    observation_reclassification_allowed,
    validate_source_record,
)

AT = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def _context(*, purpose: str = "review", at: datetime = AT) -> AssuranceContext:
    return AssuranceContext(
        identity="subject",
        purpose=purpose,
        scope="record",
        jurisdiction="US",
        at=at,
    )


def _rule(*, authority: str = "court", effective_at: datetime = AT) -> RuleBinding:
    return RuleBinding(
        rule_id="evidence-rule",
        version="1",
        authority=authority,
        jurisdiction="US",
        effective_at=effective_at,
    )


def _envelope(
    *,
    source_assurance: AssuranceState = AssuranceState.PRESERVED,
    target_purpose: str = "review",
    source_rule: RuleBinding | None = None,
    target_rule: RuleBinding | None = None,
    proof: PreservationProof | None = None,
) -> EvidentiaryEnvelope:
    source_rule = source_rule or _rule()
    target_rule = target_rule or source_rule
    return EvidentiaryEnvelope(
        transition_id="constitutional-trial",
        source=State(
            "E-1",
            {"applicability": source_assurance},
            _context(),
            source_rule,
        ),
        target=State(
            "E-1:target",
            {"applicability": AssuranceState.PRESERVED},
            _context(purpose=target_purpose),
            target_rule,
        ),
        # Deliberately empty in several attacks: EPM must detect material
        # applicability changes rather than trust caller-declared materiality.
        material_properties=frozenset(),
        preservation={"applicability": proof} if proof else {},
        consequence="critical",
    )


def _constraint() -> Constraint:
    return Constraint(
        constraint_id="C-1",
        proposition="Premise excludes Y.",
        premise_refs=("P-1",),
        premise_states={"P-1": PremiseState.ESTABLISHED},
        provenance_refs=("prov:P-1",),
        entailment_basis="P-1 entails exclusion of Y at the declared granularity.",
        entailment_status=EntailmentStatus.ESTABLISHED,
        excluded_candidates=("Y",),
        source_ref="source:P-1",
    )


def test_csm_01_authority_cannot_transmute_unknown_into_authorized_state():
    result = assess_transition(
        _envelope(
            source_assurance=AssuranceState.UNKNOWN,
            source_rule=_rule(authority="court"),
            target_rule=_rule(authority="court"),
        )
    )

    assert result["state"] == "UNKNOWN"
    assert result["decision"] == "DEFER"


def test_csm_02_caller_cannot_hide_material_purpose_change():
    result = assess_transition(_envelope(target_purpose="public-disclosure"))

    assert result["decision"] == "DENY"
    assert result["failure"] == "MISAPPLICATION"
    assert result["fail_closed"] is True


def test_csm_03_wrong_authority_preservation_proof_fails_closed():
    proof = PreservationProof(
        property_name="applicability",
        transition_id="constitutional-trial",
        rule_id="evidence-rule",
        rule_version="1",
        authority="not-the-court",
        evidence_refs=("receipt:1",),
        source_purpose="review",
        target_purpose="public-disclosure",
        source_scope="record",
        target_scope="record",
        source_jurisdiction="US",
        target_jurisdiction="US",
    )
    result = assess_transition(
        _envelope(
            target_purpose="public-disclosure",
            target_rule=_rule(authority="court"),
            proof=proof,
        )
    )

    assert result["decision"] == "DENY"
    assert result["failure"] == "AUTHORITY_MISMATCH"
    assert result["fail_closed"] is True


def test_csm_04_future_rule_cannot_be_presented_as_currently_effective():
    future_rule = _rule(effective_at=AT + timedelta(hours=1))
    assurance = State(
        "E-future",
        {"applicability": AssuranceState.PRESERVED},
        _context(at=AT),
        future_rule,
    )

    report = inspect_state(
        EvidentiaryState(
            state_id="constitutional:future-rule",
            proposition="The evidence is applicable under the governing rule.",
            assurance_state=assurance,
        )
    )

    assert "RULE_NOT_YET_EFFECTIVE" in report.structural_issues


def test_csm_05_future_evidence_remains_unavailable_to_earlier_state():
    available_at = AT + timedelta(hours=2)
    availability = EvidenceAvailability(
        evidence_id="E-future",
        available_at=available_at,
        observed_at=available_at,
        source="authenticated-receipt",
        provenance_ref="receipt:E-future",
        attestation=AvailabilityAttestation(
            "att-1",
            "evidence-system",
            "authenticated-receipt",
            "server-observed receipt",
            True,
        ),
    )

    result = assess_temporal_availability(
        evidence_id="E-future",
        state_at=AT,
        availability=availability,
    )

    assert result.status.value == "UNAVAILABLE"
    assert result.trusted is True


def test_csm_06_computation_cannot_relabel_itself_as_observation():
    source = EpistemicSourceRecord(
        source_id="calc-1",
        source_type=EpistemicSourceType.COMPUTATIONAL_DISCOVERY,
        producer="constitutional-trial",
        provenance_refs=("prov:calc-1",),
        input_refs=("E-1",),
        external_origin=False,
    )

    result = observation_reclassification_allowed(source)

    assert result.valid is False
    assert result.reason_code == "NEW_OBSERVATION_REQUIRED"


def test_csm_07_internal_observation_claim_requires_external_origin():
    source = EpistemicSourceRecord(
        source_id="obs-1",
        source_type=EpistemicSourceType.OBSERVATION,
        producer="constitutional-trial",
        provenance_refs=("prov:obs-1",),
        external_origin=False,
    )

    result = validate_source_record(source)

    assert result.valid is False
    assert result.reason_code == "OBSERVATION_EXTERNAL_ORIGIN_REQUIRED"


def test_csm_08_derivation_cannot_manufacture_resolution():
    space = create_answer_space(
        question_id="Q-1",
        candidates=("X", "Y"),
        granularity="binary identity",
        granularity_basis="The trial declares exactly two alternatives.",
    )

    result = record_derivation(
        space,
        candidate="X",
        derivation_ref="calc:constitutional-trial",
    )

    assert result.applied is True
    assert result.snapshot.resolution_state is ResolutionState.UNRESOLVED
    assert result.snapshot.epistemic_standing is EpistemicStanding.DERIVED


def test_csm_09_revision_reopens_without_erasing_prior_history():
    space = create_answer_space(
        question_id="Q-2",
        candidates=("X", "Y"),
        granularity="binary identity",
        granularity_basis="The trial declares exactly two alternatives.",
    )
    original_constraint = _constraint()
    constrained = recompute_with_constraints(space, (original_constraint,)).snapshot

    invalidated = replace(
        original_constraint,
        premise_states={"P-1": PremiseState.INVALIDATED},
    )
    reopened = recompute_with_constraints(constrained, (invalidated,)).snapshot

    assert constrained.admissible_candidates == ("X",)
    assert reopened.admissible_candidates == ("X", "Y")
    assert reopened.history[0] == constrained.history[0]
    assert reopened.history[-1].operation is AnswerSpaceOperation.REOPENED
    assert space.admissible_candidates == ("X", "Y")
