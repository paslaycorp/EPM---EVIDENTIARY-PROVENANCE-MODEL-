"""Second-domain reference proof: legal/evidentiary chain-of-custody use.

This example demonstrates the distinction between preserved evidence and
permitted evidence use. It is an engineering reference, not legal advice.
"""
from datetime import UTC, datetime, timedelta

from epm import AssuranceState, PreservationProof, assess_transition
from epm.adapters import LegalEvidenceUse, legal_envelope

MATTER_ID = "MAT-002"
EXHIBIT_ID = "EX-042"
TRANSITION_ID = f"legal:{MATTER_ID}:{EXHIBIT_ID}"


def run_reference():
    collected_at = datetime(2026, 9, 14, 9, 0, tzinfo=UTC)
    review_at = collected_at + timedelta(hours=2)

    custody_proof = PreservationProof(
        property_name="applicability",
        transition_id=TRANSITION_ID,
        rule_id="evidence-rule",
        rule_version="1",
        authority="court",
        evidence_refs=("custody-receipt:EX-042",),
        valid=True,
        source_purpose="collection-review",
        target_purpose="trial-admission-review",
        source_scope="case-record",
        target_scope="case-record",
        source_jurisdiction="US-TX",
        target_jurisdiction="US-TX",
    )

    preserved_use = LegalEvidenceUse(
        matter_id=MATTER_ID,
        exhibit_id=EXHIBIT_ID,
        source_assurance=AssuranceState.PRESERVED,
        source_use="collection-review",
        target_use="trial-admission-review",
        source_record_scope="case-record",
        target_record_scope="case-record",
        source_jurisdiction="US-TX",
        target_jurisdiction="US-TX",
        source_at=collected_at,
        target_at=review_at,
        source_rule_id="evidence-rule",
        source_rule_version="1",
        source_authority="court",
        target_rule_id="evidence-rule",
        target_rule_version="1",
        target_authority="court",
        consequence="critical",
        preservation=custody_proof,
    )

    unauthorized_disclosure = LegalEvidenceUse(
        matter_id=MATTER_ID,
        exhibit_id=EXHIBIT_ID,
        source_assurance=AssuranceState.PRESERVED,
        source_use="trial-admission-review",
        target_use="public-disclosure",
        source_record_scope="case-record",
        target_record_scope="public-record",
        source_jurisdiction="US-TX",
        target_jurisdiction="US-TX",
        source_at=review_at,
        target_at=review_at,
        source_rule_id="evidence-rule",
        source_rule_version="1",
        source_authority="court",
        target_rule_id="evidence-rule",
        target_rule_version="1",
        target_authority="court",
        consequence="critical",
    )

    return {
        "custody_preserved": dict(assess_transition(legal_envelope(preserved_use))),
        "secondary_use_blocked": dict(
            assess_transition(legal_envelope(unauthorized_disclosure))
        ),
    }


if __name__ == "__main__":
    print(run_reference())
