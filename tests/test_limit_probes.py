from __future__ import annotations

from datetime import UTC, datetime

import pytest

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
LATER = datetime(2026, 9, 14, 12, 1, tzinfo=UTC)
NAIVE = datetime(2026, 9, 14, 12, 0)


def _state(
    state_id: str,
    *,
    identity: str = "subject",
    purpose: str = "review",
    scope: str = "record",
    jurisdiction: str = "US",
    at: datetime = AWARE,
    rule_id: str = "rule",
    rule_version: str = "1",
    rule_authority: str = "authority",
    rule_jurisdiction: str = "US",
    rule_effective_at: datetime = AWARE,
) -> State:
    return State(
        state_id,
        {"applicability": AssuranceState.PRESERVED},
        AssuranceContext(
            identity=identity,
            purpose=purpose,
            scope=scope,
            jurisdiction=jurisdiction,
            at=at,
        ),
        RuleBinding(
            rule_id=rule_id,
            version=rule_version,
            authority=rule_authority,
            jurisdiction=rule_jurisdiction,
            effective_at=rule_effective_at,
        ),
    )


@pytest.mark.parametrize(
    "target_overrides",
    (
        {"identity": "other-subject"},
        {"purpose": "secondary-use"},
        {"scope": "other-record"},
        {"jurisdiction": "CA"},
        {"at": LATER},
        {"rule_version": "2"},
    ),
    ids=(
        "identity",
        "purpose",
        "scope",
        "jurisdiction",
        "temporal-context",
        "rule-binding",
    ),
)
def test_caller_cannot_hide_material_applicability_change_by_omitting_materiality(
    target_overrides,
):
    source = _state("E-1")
    target = _state("E-1:target", **target_overrides)
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
        "A caller-declared empty materiality set must not authorize an applicability "
        "transition whose identity/purpose/scope/jurisdiction/time/rule context changed."
    )


@pytest.mark.parametrize(
    ("target_at", "rule_effective_at"),
    ((AWARE, NAIVE), (NAIVE, AWARE)),
    ids=("naive-rule-aware-state", "aware-rule-naive-state"),
)
def test_incomparable_rule_and_state_times_fail_typed_not_with_exception(
    target_at,
    rule_effective_at,
):
    source = _state("E-2")
    target = _state(
        "E-2:target",
        purpose="secondary-use",
        at=target_at,
        rule_effective_at=rule_effective_at,
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


@pytest.mark.parametrize(
    ("available_at", "observed_at"),
    ((AWARE, NAIVE), (NAIVE, AWARE)),
    ids=("aware-available-naive-observed", "naive-available-aware-observed"),
)
def test_incomparable_availability_times_fail_typed_not_with_exception(
    available_at,
    observed_at,
):
    availability = EvidenceAvailability(
        evidence_id="E-3",
        available_at=available_at,
        observed_at=observed_at,
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
