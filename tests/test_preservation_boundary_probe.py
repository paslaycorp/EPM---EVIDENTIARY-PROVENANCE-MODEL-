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

AT = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)


def _state(state_id: str, *, purpose: str) -> State:
    return State(
        state_id,
        {"applicability": AssuranceState.PRESERVED},
        AssuranceContext(
            identity="subject",
            purpose=purpose,
            scope="record",
            jurisdiction="US",
            at=AT,
        ),
        RuleBinding(
            rule_id="rule",
            version="1",
            authority="authority",
            jurisdiction="US",
            effective_at=AT,
        ),
    )


def test_unvalidated_proof_shaped_claim_cannot_authorize_material_transition():
    source = _state("E-4", purpose="review")
    target = _state("E-4:target", purpose="secondary-use")

    fabricated = PreservationProof(
        property_name="applicability",
        transition_id="LIMIT-PROOF-1",
        rule_id="rule",
        rule_version="1",
        authority="authority",
        evidence_refs=("fabricated:unvalidated",),
        valid=True,
        source_purpose="review",
        target_purpose="secondary-use",
        source_scope="record",
        target_scope="record",
        source_jurisdiction="US",
        target_jurisdiction="US",
    )

    envelope = EvidentiaryEnvelope(
        transition_id="LIMIT-PROOF-1",
        source=source,
        target=target,
        material_properties=frozenset({"applicability"}),
        preservation={"applicability": fabricated},
        consequence="critical",
    )

    result = assess_transition(envelope)

    assert result["decision"] != "AUTHORIZED", (
        "A proof-shaped claim with matching metadata and a non-empty evidence ref "
        "must not authorize a material transition unless proof trust was validated "
        "at the ingestion boundary."
    )
