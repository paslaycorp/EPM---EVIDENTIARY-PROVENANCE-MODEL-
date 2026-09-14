"""Legal/evidentiary-use reference adapter for EPM."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from ..assurance import AssuranceContext, AssuranceState, PreservationProof, RuleBinding
from ..envelope import EvidentiaryEnvelope
from .common import DomainTransition, build_domain_envelope


@dataclass(frozen=True)
class LegalEvidenceUse:
    matter_id: str
    exhibit_id: str
    source_assurance: AssuranceState
    source_use: str
    target_use: str
    source_record_scope: str
    target_record_scope: str
    source_jurisdiction: str
    target_jurisdiction: str
    source_at: datetime
    target_at: datetime
    source_rule_id: str
    source_rule_version: str
    source_authority: str
    target_rule_id: str
    target_rule_version: str
    target_authority: str
    consequence: str = "critical"
    preservation: PreservationProof | None = None


def legal_envelope(item: LegalEvidenceUse) -> EvidentiaryEnvelope:
    return build_domain_envelope(
        DomainTransition(
            transition_id=f"legal:{item.matter_id}:{item.exhibit_id}",
            evidence_id=item.exhibit_id,
            source_assurance=item.source_assurance,
            source_context=AssuranceContext(
                identity=item.matter_id,
                purpose=item.source_use,
                scope=item.source_record_scope,
                jurisdiction=item.source_jurisdiction,
                at=item.source_at,
            ),
            target_context=AssuranceContext(
                identity=item.matter_id,
                purpose=item.target_use,
                scope=item.target_record_scope,
                jurisdiction=item.target_jurisdiction,
                at=item.target_at,
            ),
            source_rule=RuleBinding(
                item.source_rule_id,
                item.source_rule_version,
                item.source_authority,
                item.source_jurisdiction,
                item.source_at,
            ),
            target_rule=RuleBinding(
                item.target_rule_id,
                item.target_rule_version,
                item.target_authority,
                item.target_jurisdiction,
                item.target_at,
            ),
            consequence=item.consequence,
            preservation=item.preservation,
        )
    )
