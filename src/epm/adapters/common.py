"""Shared domain-adapter construction for EPM."""
from __future__ import annotations

from dataclasses import dataclass

from ..assurance import (
    AssuranceContext,
    AssuranceState,
    PreservationProof,
    RuleBinding,
    State,
)
from ..envelope import EvidentiaryEnvelope


class AdapterInputError(ValueError):
    """Raised when a domain adapter omits material context required by EPM."""


@dataclass(frozen=True)
class DomainTransition:
    transition_id: str
    evidence_id: str
    source_assurance: AssuranceState
    source_context: AssuranceContext
    target_context: AssuranceContext
    source_rule: RuleBinding
    target_rule: RuleBinding
    consequence: str = "standard"
    preservation: PreservationProof | None = None


def _require_context(label: str, context: AssuranceContext) -> None:
    missing = [
        name
        for name, value in (
            ("purpose", context.purpose),
            ("scope", context.scope),
            ("jurisdiction", context.jurisdiction),
            ("at", context.at),
        )
        if value is None or (isinstance(value, str) and not value.strip())
    ]
    if missing:
        raise AdapterInputError(f"{label} context missing: {', '.join(missing)}")


def _require_rule(label: str, rule: RuleBinding) -> None:
    if not rule.rule_id.strip() or not rule.version.strip() or not rule.authority.strip():
        raise AdapterInputError(f"{label} rule requires id, version, and authority")


def build_domain_envelope(item: DomainTransition) -> EvidentiaryEnvelope:
    """Translate a complete domain transition into the generic EPM envelope."""
    if not item.transition_id.strip() or not item.evidence_id.strip():
        raise AdapterInputError("transition_id and evidence_id are required")
    _require_context("source", item.source_context)
    _require_context("target", item.target_context)
    _require_rule("source", item.source_rule)
    _require_rule("target", item.target_rule)

    source = State(
        item.evidence_id,
        {
            "integrity": item.source_assurance,
            "provenance": item.source_assurance,
            "evidence": item.source_assurance,
            "applicability": item.source_assurance,
        },
        item.source_context,
        item.source_rule,
    )
    target = State(
        f"{item.evidence_id}:target",
        {"applicability": AssuranceState.PRESERVED},
        item.target_context,
        item.target_rule,
    )
    material = any(
        (
            item.source_context.purpose != item.target_context.purpose,
            item.source_context.scope != item.target_context.scope,
            item.source_context.jurisdiction != item.target_context.jurisdiction,
            item.source_context.at != item.target_context.at,
            item.source_rule != item.target_rule,
        )
    )
    return EvidentiaryEnvelope(
        transition_id=item.transition_id,
        source=source,
        target=target,
        material_properties=frozenset({"applicability"}) if material else frozenset(),
        preservation={"applicability": item.preservation} if item.preservation else {},
        consequence=item.consequence,
    )
