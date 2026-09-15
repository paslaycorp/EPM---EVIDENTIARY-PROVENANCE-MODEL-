from __future__ import annotations

from datetime import UTC, datetime

from epm import (
    AssuranceContext,
    AssuranceState,
    AvailabilityAttestation,
    EvidenceAvailability,
    EvidentiaryEnvelope,
    PreservationProof,
    RuleBinding,
    State,
    assess_temporal_availability,
    assess_transition,
)

AWARE = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
NAIVE = datetime(2026, 9, 14, 12, 0)


def _state(
    state_id: str,
    *,
    purpose: str = "review",
    at: datetime = AWARE,
    rule_effective_at: datetime = AWARE,
) -> State:
    return State(
        state_id,
        {"applicability": AssuranceState.PRESERVED},
        AssuranceContext(
            identity="subject",
            purpose=purpose,
            scope="record",
            jurisdiction="US",
            at=at,
        ),
        RuleBinding(
            rule_id="rule",
            version="1",
            authority="authority",
            jurisdiction="US",
            effective_at=rule_effective_at,
        ),
    )


def test_caller_cannot_hide_material_context_change_by_omitting_materiality():
    source = _state("E-1", purpose="review")
    target = _state("E-1:target", purpose="secondary-use")
    envelope = EvidentiaryEnvelope(
        transition_id="LIMIT-MATERIALITY-1",
        source=source,
        target=target,
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] != "AUTHORIZED", (
        "A caller-declared empty materiality set must not authorize a transition "
        "whose purpose/scope/jurisdiction/time/rule context changed."
    )


def test_incomparable_rule_and_state_times_fail_typed_not_with_exception():
    source = _state("E-2")
    target = _state(
        "E-2:target",
        purpose="secondary-use",
        at=AWARE,
        rule_effective_at=NAIVE,
    )
    proof = PreservationProof(
        property_name="applicability",
        transition_id="LIMIT-TIME-1",
        rule_id="rule",
        rule_version="1",
        authority="authority",
        evidence_refs=("prov:bridge",),
        source_purpose="review",
        target_purpose="secondary-use",
        source_scope="record",
        target_scope="record",
        source_jurisdiction="US",
        target_jurisdiction="US",
    )
    envelope = EvidentiaryEnvelope(
        transition_id="LIMIT-TIME-1",
        source=source,
        target=target,
        material_properties=frozenset({"applicability"}),
        preservation={"applicability": proof},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] in {"DEFER", "QUARANTINE", "DENY"}
    assert result["decision"] != "AUTHORIZED"


def test_incomparable_availability_times_fail_typed_not_with_exception():
    availability = EvidenceAvailability(
        evidence_id="E-3",
        available_at=AWARE,
        observed_at=NAIVE,
        source="probe",
        provenance_ref="prov:E-3",
        attestation=AvailabilityAttestation(
            attestation_id="A-3",
            authority="probe-authority",
            method="probe",
            basis="limit test",
            validated=True,
        ),
    )

    result = assess_temporal_availability(
        evidence_id="E-3",
        state_at=AWARE,
        availability=availability,
    )

    assert result.status.value == "UNKNOWN"
    assert result.trusted is False
