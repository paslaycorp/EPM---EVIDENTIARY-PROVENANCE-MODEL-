from __future__ import annotations

from datetime import UTC, datetime

from epm import (
    AssuranceContext,
    AssuranceState,
    EvidentiaryEnvelope,
    PreservationProof,
    RuleBinding,
    State,
    assess_transition,
)

AT = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)


def _context() -> AssuranceContext:
    return AssuranceContext(
        identity="subject",
        purpose="review",
        scope="record",
        jurisdiction="US",
        at=AT,
    )


def _rule() -> RuleBinding:
    return RuleBinding(
        rule_id="evidence-rule",
        version="1",
        authority="court",
        jurisdiction="US",
        effective_at=AT,
    )


def _state(
    state_id: str,
    *,
    applicability: AssuranceState = AssuranceState.PRESERVED,
    provenance: AssuranceState = AssuranceState.PRESERVED,
) -> State:
    return State(
        state_id,
        {
            "applicability": applicability,
            "provenance": provenance,
        },
        _context(),
        _rule(),
    )


def test_csm_10_omitted_material_property_cannot_hide_state_change():
    envelope = EvidentiaryEnvelope(
        transition_id="csm-hidden-materiality",
        source=_state("E-10", provenance=AssuranceState.UNKNOWN),
        target=_state("E-10:target", provenance=AssuranceState.PRESERVED),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] != "AUTHORIZED"
    assert result["failure"] == "COMPOSITION_UNRESOLVED"
    assert result["fail_closed"] is True


def test_csm_11_contradicted_component_remains_typed_through_composition():
    envelope = EvidentiaryEnvelope(
        transition_id="csm-contradicted-component",
        source=_state("E-11", provenance=AssuranceState.CONTRADICTED),
        target=_state("E-11:target", provenance=AssuranceState.PRESERVED),
        material_properties=frozenset({"provenance"}),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["state"] == "CONTRADICTED"
    assert result["failure"] == "CONTRADICTORY_EVIDENCE"
    assert result["decision"] == "DENY"


def test_csm_12_valid_material_component_proof_allows_composed_authorization():
    proof = PreservationProof(
        property_name="provenance",
        transition_id="csm-valid-composition",
        rule_id="evidence-rule",
        rule_version="1",
        authority="court",
        evidence_refs=("prov:bridge",),
    )
    envelope = EvidentiaryEnvelope(
        transition_id="csm-valid-composition",
        source=_state("E-12"),
        target=_state("E-12:target"),
        material_properties=frozenset({"provenance"}),
        preservation={"provenance": proof},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "AUTHORIZED"
    assert result["failure"] == "NONE"
    assert result["state"] == "PRESERVED"
    assert result["component_results"][0]["property"] == "provenance"
    assert result["component_results"][0]["decision"] == "AUTHORIZED"


def test_csm_13_unsupported_schema_quarantines_noncritical_envelope():
    envelope = EvidentiaryEnvelope(
        transition_id="csm-schema-standard",
        source=_state("E-13"),
        target=_state("E-13:target"),
        material_properties=frozenset(),
        preservation={},
        consequence="standard",
        schema_version="epm.evidentiary-envelope/999.0",
    )

    result = assess_transition(envelope)

    assert result["decision"] == "QUARANTINE"
    assert result["failure"] == "PRESERVATION_UNESTABLISHED"
    assert result["fail_closed"] is True
