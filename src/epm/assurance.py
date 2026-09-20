"""Domain-neutral assurance primitives for EPM.

These primitives preserve the executed vNext transition semantics without
binding the core package to FAP, insurance, or the historical DPIE module name.
"""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class AssuranceState(str, Enum):
    PRESERVED = "PRESERVED"
    CHANGED = "CHANGED"
    INVALIDATED = "INVALIDATED"
    UNKNOWN = "UNKNOWN"
    CONTRADICTED = "CONTRADICTED"
    VALID = "VALID"


class Decision(str, Enum):
    AUTHORIZED = "AUTHORIZED"
    AUTHORIZED_WITH_CONSTRAINTS = "AUTHORIZED_WITH_CONSTRAINTS"
    DEFER = "DEFER"
    QUARANTINE = "QUARANTINE"
    DENY = "DENY"


class FailureCode(str, Enum):
    NONE = "NONE"
    MISAPPLICATION = "MISAPPLICATION"
    AUTHORITY_MISMATCH = "AUTHORITY_MISMATCH"
    JURISDICTION_MISMATCH = "JURISDICTION_MISMATCH"
    TEMPORAL_MISMATCH = "TEMPORAL_MISMATCH"
    RULE_MISMATCH = "RULE_MISMATCH"
    COMPOSITION_UNRESOLVED = "COMPOSITION_UNRESOLVED"
    PRESERVATION_UNESTABLISHED = "PRESERVATION_UNESTABLISHED"
    CONTRADICTORY_EVIDENCE = "CONTRADICTORY_EVIDENCE"


class Materiality(str, Enum):
    MATERIAL = "MATERIAL"
    NON_MATERIAL = "NON_MATERIAL"


class Property(str, Enum):
    INTEGRITY = "integrity"
    PROVENANCE = "provenance"
    IDENTITY = "identity"
    EVIDENCE = "evidence"
    APPLICABILITY = "applicability"


@dataclass(frozen=True)
class AssuranceProperty:
    name: str
    dependencies: frozenset[str] = field(default_factory=frozenset)


@dataclass(frozen=True)
class RuleBinding:
    rule_id: str
    version: str
    authority: str
    jurisdiction: str | None = None
    effective_at: datetime | None = None


@dataclass(frozen=True)
class AssuranceContext:
    identity: str | None = None
    purpose: str | None = None
    scope: str | None = None
    jurisdiction: str | None = None
    at: datetime | None = None


@dataclass(frozen=True)
class State:
    state_id: str
    properties: Mapping[str, AssuranceState]
    context: AssuranceContext
    rule: RuleBinding


@dataclass(frozen=True)
class PreservationProof:
    property_name: str = ""
    transition_id: str = ""
    rule_id: str = ""
    rule_version: str = ""
    authority: str = ""
    evidence_refs: tuple[str, ...] = ()
    valid: bool = True
    boundary_validated: bool = True
    reason: str = ""
    property: Property | None = None
    source_purpose: str | None = None
    target_purpose: str | None = None
    source_scope: str | None = None
    target_scope: str | None = None
    source_jurisdiction: str | None = None
    target_jurisdiction: str | None = None

    def normalized_property_name(self) -> str:
        return self.property_name or (self.property.value if self.property else "")


@dataclass(frozen=True)
class Transition:
    transition_id: str
    source: State
    target: State
    material_properties: frozenset[str]
    preservation: Mapping[str, PreservationProof] = field(default_factory=dict)


@dataclass(frozen=True)
class AssuranceResult:
    property_name: str
    state: AssuranceState
    decision: Decision
    failure: FailureCode
    reason: str
    transition_id: str
    rule_id: str
    rule_version: str

    @property
    def reason_code(self) -> str:
        return self.failure.value


def _is_valid_source(value: AssuranceState) -> bool:
    return value in {AssuranceState.PRESERVED, AssuranceState.VALID}


def _timezone_aware(value: datetime | None) -> bool:
    return value is not None and value.tzinfo is not None and value.utcoffset() is not None


def _context_or_rule_changed(transition: Transition) -> bool:
    src = transition.source.context
    dst = transition.target.context
    return any(
        (
            src.identity != dst.identity,
            src.purpose != dst.purpose,
            src.scope != dst.scope,
            src.jurisdiction != dst.jurisdiction,
            src.at != dst.at,
            transition.source.rule != transition.target.rule,
        )
    )


def is_material(transition: Transition, property_name: str) -> bool:
    if property_name in transition.material_properties:
        return True
    return property_name == Property.APPLICABILITY.value and _context_or_rule_changed(transition)


def preservation_established(transition: Transition, property_name: str) -> bool:
    proof = transition.preservation.get(property_name)
    if (
        proof is None
        or not proof.valid
        or not proof.boundary_validated
        or proof.normalized_property_name() != property_name
    ):
        return False
    rule = transition.target.rule
    if (
        proof.transition_id != transition.transition_id
        or proof.rule_id != rule.rule_id
        or proof.rule_version != rule.version
        or proof.authority != rule.authority
        or not proof.evidence_refs
    ):
        return False
    if rule.effective_at is not None:
        target_at = transition.target.context.at
        if not _timezone_aware(rule.effective_at) or not _timezone_aware(target_at):
            return False
        if rule.effective_at > target_at:
            return False
    src = transition.source.context
    dst = transition.target.context
    declared_actual = (
        (proof.source_purpose, src.purpose),
        (proof.target_purpose, dst.purpose),
        (proof.source_scope, src.scope),
        (proof.target_scope, dst.scope),
        (proof.source_jurisdiction, src.jurisdiction),
        (proof.target_jurisdiction, dst.jurisdiction),
    )
    return all(declared is None or declared == actual for declared, actual in declared_actual)


def _result(
    transition: Transition,
    property_name: str,
    state: AssuranceState,
    decision: Decision,
    failure: FailureCode,
    reason: str,
) -> AssuranceResult:
    return AssuranceResult(
        property_name,
        state,
        decision,
        failure,
        reason,
        transition.transition_id,
        transition.target.rule.rule_id,
        transition.target.rule.version,
    )


def evaluate_transition(
    transition: Transition,
    property_name: str,
    *,
    consequence: str = "standard",
) -> AssuranceResult:
    """Evaluate whether one assurance property survives a transition."""
    source_value = transition.source.properties.get(
        property_name,
        AssuranceState.UNKNOWN,
    )
    if source_value is AssuranceState.UNKNOWN:
        return _result(
            transition,
            property_name,
            AssuranceState.UNKNOWN,
            Decision.DEFER,
            FailureCode.NONE,
            "Required source assurance is unknown; no invalidity is fabricated.",
        )
    if source_value is AssuranceState.CONTRADICTED:
        decision = (
            Decision.DENY
            if consequence.lower() == "critical"
            else Decision.QUARANTINE
        )
        return _result(
            transition,
            property_name,
            AssuranceState.CONTRADICTED,
            decision,
            FailureCode.CONTRADICTORY_EVIDENCE,
            "Required source assurance is contradicted; contradiction is preserved as a typed blocking condition.",
        )
    if not is_material(transition, property_name):
        if _is_valid_source(source_value):
            return _result(
                transition,
                property_name,
                AssuranceState.PRESERVED,
                Decision.AUTHORIZED,
                FailureCode.NONE,
                "Transition is outside the materiality boundary for this property.",
            )
        return _result(
            transition,
            property_name,
            source_value,
            Decision.DEFER,
            FailureCode.PRESERVATION_UNESTABLISHED,
            "Source assurance is not established for this property.",
        )

    proof = transition.preservation.get(property_name)
    if preservation_established(transition, property_name):
        return _result(
            transition,
            property_name,
            AssuranceState.PRESERVED,
            Decision.AUTHORIZED,
            FailureCode.NONE,
            "Explicit boundary-validated preservation relation established for the material transition.",
        )

    src = transition.source.context
    dst = transition.target.context
    if proof is not None and proof.valid and proof.authority != transition.target.rule.authority:
        failure = FailureCode.AUTHORITY_MISMATCH
        reason = "Preservation proof was issued by an authority not bound to the target rule."
    elif proof is not None and proof.valid and not proof.boundary_validated:
        failure = FailureCode.PRESERVATION_UNESTABLISHED
        reason = "Preservation proof was not validated at the ingestion boundary."
    elif src.purpose != dst.purpose or src.scope != dst.scope:
        failure = FailureCode.MISAPPLICATION
        reason = "Artifact assurance remains intact, but application context changed without valid preservation proof."
    elif src.jurisdiction != dst.jurisdiction:
        failure = FailureCode.JURISDICTION_MISMATCH
        reason = "Jurisdiction changed without an explicit preservation determination."
    elif src.at != dst.at:
        failure = FailureCode.TEMPORAL_MISMATCH
        reason = "Temporal context changed without an explicit preservation determination."
    elif transition.source.rule != transition.target.rule:
        failure = FailureCode.RULE_MISMATCH
        reason = "Governing rule binding changed without an explicit preservation determination."
    elif proof is not None and proof.valid and proof.target_purpose not in (None, dst.purpose):
        failure = FailureCode.MISAPPLICATION
        reason = "Preservation proof is scoped to a different purpose."
    elif proof is not None and proof.valid and proof.target_scope not in (None, dst.scope):
        failure = FailureCode.MISAPPLICATION
        reason = "Preservation proof is scoped to a different target scope."
    else:
        failure = FailureCode.PRESERVATION_UNESTABLISHED
        reason = "Material transition detected, but preservation was not established."

    decision = Decision.DENY if consequence.lower() == "critical" else Decision.QUARANTINE
    return _result(
        transition,
        property_name,
        AssuranceState.INVALIDATED,
        decision,
        failure,
        reason,
    )
