from __future__ import annotations

from datetime import UTC, datetime

from epm import (
    AssuranceContext,
    AssuranceState,
    EvidentiaryEnvelope,
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
    provenance: AssuranceState | None = None,
) -> State:
    properties = {"applicability": applicability}
    if provenance is not None:
        properties["provenance"] = provenance
    return State(state_id, properties, _context(), _rule())


def test_falsify_01_contradiction_must_not_collapse_into_plain_unknown():
    envelope = EvidentiaryEnvelope(
        transition_id="falsify-contradiction",
        source=_state("E-1", applicability=AssuranceState.CONTRADICTED),
        target=_state("E-1:target"),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["state"] == "CONTRADICTED"
    assert result["failure"] == "CONTRADICTORY_EVIDENCE"
    assert result["decision"] != "AUTHORIZED"


def test_falsify_02_unsupported_envelope_schema_must_not_authorize():
    envelope = EvidentiaryEnvelope(
        transition_id="falsify-schema",
        source=_state("E-2"),
        target=_state("E-2:target"),
        material_properties=frozenset(),
        preservation={},
        consequence="critical",
        schema_version="epm.evidentiary-envelope/999.0",
    )

    result = assess_transition(envelope)

    assert result["decision"] != "AUTHORIZED"
    assert result["failure"] != "NONE"


def test_falsify_03_unresolved_material_component_must_block_global_authorization():
    envelope = EvidentiaryEnvelope(
        transition_id="falsify-composition",
        source=_state(
            "E-3",
            applicability=AssuranceState.PRESERVED,
            provenance=AssuranceState.UNKNOWN,
        ),
        target=_state(
            "E-3:target",
            applicability=AssuranceState.PRESERVED,
            provenance=AssuranceState.PRESERVED,
        ),
        material_properties=frozenset({"provenance"}),
        preservation={},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] != "AUTHORIZED"
    assert result["failure"] == "COMPOSITION_UNRESOLVED"
    assert result["fail_closed"] is True
