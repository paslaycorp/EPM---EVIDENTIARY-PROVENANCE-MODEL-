"""Insurance reference adapter for the domain-neutral EPM engine."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..assurance import AssuranceContext, AssuranceState, PreservationProof, RuleBinding
from ..envelope import EvidentiaryEnvelope
from .common import DomainTransition, build_domain_envelope


@dataclass(frozen=True)
class InsuranceEvidenceUse:
    claim_id: str
    evidence_id: str
    source_assurance: AssuranceState
    source_purpose: str
    target_purpose: str
    source_scope: str
    target_scope: str
    source_jurisdiction: str
    target_jurisdiction: str
    source_at: datetime
    target_at: datetime
    source_rule_id: str
    source_rule_version: str
    source_rule_authority: str
    target_rule_id: str
    target_rule_version: str
    target_rule_authority: str
    consequence: str = "standard"
    preservation: PreservationProof | None = None


def insurance_envelope(item: InsuranceEvidenceUse) -> EvidentiaryEnvelope:
    return build_domain_envelope(
        DomainTransition(
            transition_id=f"insurance:{item.claim_id}:{item.evidence_id}",
            evidence_id=item.evidence_id,
            source_assurance=item.source_assurance,
            source_context=AssuranceContext(
                identity=item.claim_id,
                purpose=item.source_purpose,
                scope=item.source_scope,
                jurisdiction=item.source_jurisdiction,
                at=item.source_at,
            ),
            target_context=AssuranceContext(
                identity=item.claim_id,
                purpose=item.target_purpose,
                scope=item.target_scope,
                jurisdiction=item.target_jurisdiction,
                at=item.target_at,
            ),
            source_rule=RuleBinding(
                item.source_rule_id,
                item.source_rule_version,
                item.source_rule_authority,
                item.source_jurisdiction,
                item.source_at,
            ),
            target_rule=RuleBinding(
                item.target_rule_id,
                item.target_rule_version,
                item.target_rule_authority,
                item.target_jurisdiction,
                item.target_at,
            ),
            consequence=item.consequence,
            preservation=item.preservation,
        )
    )
