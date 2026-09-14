"""Scientific evidence-use reference adapter for EPM."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..assurance import AssuranceContext, AssuranceState, PreservationProof, RuleBinding
from ..envelope import EvidentiaryEnvelope
from .common import DomainTransition, build_domain_envelope


@dataclass(frozen=True)
class ScientificEvidenceUse:
    study_id: str
    dataset_id: str
    source_assurance: AssuranceState
    source_purpose: str
    target_purpose: str
    source_protocol: str
    target_protocol: str
    source_governance_domain: str
    target_governance_domain: str
    source_at: datetime
    target_at: datetime
    source_rule_id: str
    source_rule_version: str
    source_authority: str
    target_rule_id: str
    target_rule_version: str
    target_authority: str
    consequence: str = "standard"
    preservation: PreservationProof | None = None


def scientific_envelope(item: ScientificEvidenceUse) -> EvidentiaryEnvelope:
    return build_domain_envelope(
        DomainTransition(
            transition_id=f"scientific:{item.study_id}:{item.dataset_id}",
            evidence_id=item.dataset_id,
            source_assurance=item.source_assurance,
            source_context=AssuranceContext(
                identity=item.study_id,
                purpose=item.source_purpose,
                scope=item.source_protocol,
                jurisdiction=item.source_governance_domain,
                at=item.source_at,
            ),
            target_context=AssuranceContext(
                identity=item.study_id,
                purpose=item.target_purpose,
                scope=item.target_protocol,
                jurisdiction=item.target_governance_domain,
                at=item.target_at,
            ),
            source_rule=RuleBinding(
                item.source_rule_id,
                item.source_rule_version,
                item.source_authority,
                item.source_governance_domain,
                item.source_at,
            ),
            target_rule=RuleBinding(
                item.target_rule_id,
                item.target_rule_version,
                item.target_authority,
                item.target_governance_domain,
                item.target_at,
            ),
            consequence=item.consequence,
            preservation=item.preservation,
        )
    )
