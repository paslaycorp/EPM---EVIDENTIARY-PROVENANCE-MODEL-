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


def _envelope(proof: PreservationProof) -> EvidentiaryEnvelope:
    return EvidentiaryEnvelope(
        transition_id="LIMIT-PROOF-1",
        source=_state("E-4", purpose="review"),
        target=_state("E-4:target", purpose="secondary-use"),
        material_properties=frozenset({"applicability"}),
        preservation={"applicability": proof},
        consequence="critical",
    )


def test_unvalidated_proof_shaped_claim_cannot_authorize_material_transition():
    fabricated = PreservationProof(
        property_name="applicability",
        transition_id="LIMIT-PROOF-1",
        rule_id="rule",
        rule_version="1",
        authority="authority",
        evidence_refs=("fabricated:unvalidated",),
        valid=True,
        boundary_validated=False,
        source_purpose="review",
        target_purpose="secondary-use",
        source_scope="record",
        target_scope="record",
        source_jurisdiction="US",
        target_jurisdiction="US",
    )

    result = assess_transition(_envelope(fabricated))

    assert result["decision"] != "AUTHORIZED", (
        "A proof-shaped claim with matching metadata and a non-empty evidence ref "
        "must not authorize a material transition unless proof trust was validated "
        "at the ingestion boundary."
    )
    assert result["failure"] == "PRESERVATION_UNESTABLISHED"


def test_wrong_authority_precedes_boundary_validation_diagnostic():
    fabricated = PreservationProof(
        property_name="applicability",
        transition_id="LIMIT-PROOF-1",
        rule_id="rule",
        rule_version="1",
        authority="wrong-authority",
        evidence_refs=("fabricated:wrong-authority",),
        valid=True,
        boundary_validated=False,
        source_purpose="review",
        target_purpose="secondary-use",
        source_scope="record",
        target_scope="record",
        source_jurisdiction="US",
        target_jurisdiction="US",
    )

    result = assess_transition(_envelope(fabricated))

    assert result["decision"] != "AUTHORIZED"
    assert result["failure"] == "AUTHORITY_MISMATCH"
