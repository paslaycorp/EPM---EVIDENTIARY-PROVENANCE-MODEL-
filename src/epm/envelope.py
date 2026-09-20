"""Domain-neutral EPM evidentiary transition envelope."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from .assurance import (
    AssuranceState,
    Decision,
    FailureCode,
    PreservationProof,
    State,
    Transition,
    evaluate_transition,
)
from .governor import govern

EPM_ENVELOPE_SCHEMA_VERSION = "epm.evidentiary-envelope/0.1"


@dataclass(frozen=True)
class EvidentiaryEnvelope:
    transition_id: str
    source: State
    target: State
    material_properties: frozenset[str]
    preservation: Mapping[str, PreservationProof] = field(default_factory=dict)
    consequence: str = "standard"
    schema_version: str = EPM_ENVELOPE_SCHEMA_VERSION

    def to_transition(self) -> Transition:
        return Transition(
            transition_id=self.transition_id,
            source=self.source,
            target=self.target,
            material_properties=self.material_properties,
            preservation=self.preservation,
        )


def _envelope_result(
    envelope: EvidentiaryEnvelope,
    *,
    property_name: str,
    state: AssuranceState,
    decision: Decision,
    failure: FailureCode,
    reason: str,
    component_results: tuple[Mapping[str, object], ...] = (),
) -> Mapping[str, object]:
    return {
        "transition_id": envelope.transition_id,
        "property": property_name,
        "state": state.value,
        "decision": decision.value,
        "failure": failure.value,
        "reason": reason,
        "rule_id": envelope.target.rule.rule_id,
        "rule_version": envelope.target.rule.version,
        "source_evidence_id": envelope.source.state_id,
        "fail_closed": decision in {Decision.DENY, Decision.QUARANTINE},
        "schema_version": envelope.schema_version,
        "component_results": component_results,
    }


def evaluate_evidentiary_envelope(
    envelope: EvidentiaryEnvelope,
    property_name: str = "applicability",
) -> Mapping[str, object]:
    """Evaluate an envelope without allowing unsupported or partial semantics to authorize."""
    if envelope.schema_version != EPM_ENVELOPE_SCHEMA_VERSION:
        decision = (
            Decision.DENY
            if envelope.consequence.lower() == "critical"
            else Decision.QUARANTINE
        )
        return _envelope_result(
            envelope,
            property_name=property_name,
            state=AssuranceState.UNKNOWN,
            decision=decision,
            failure=FailureCode.SCHEMA_UNSUPPORTED,
            reason=(
                "Envelope schema is unsupported; semantic capability was not "
                "established, so authorization is withheld."
            ),
        )

    transition = envelope.to_transition()
    primary = evaluate_transition(
        transition,
        property_name,
        consequence=envelope.consequence,
    )
    primary_decision = govern(
        assurance_state=primary.state,
        failure=primary.failure,
        consequence=envelope.consequence,
    )

    if primary_decision is not Decision.AUTHORIZED:
        return _envelope_result(
            envelope,
            property_name=primary.property_name,
            state=primary.state,
            decision=primary_decision,
            failure=primary.failure,
            reason=primary.reason,
        )

    component_results: list[Mapping[str, object]] = []
    blocking_components = []
    for component_name in sorted(envelope.material_properties):
        if component_name == property_name:
            continue
        component = evaluate_transition(
            transition,
            component_name,
            consequence=envelope.consequence,
        )
        component_decision = govern(
            assurance_state=component.state,
            failure=component.failure,
            consequence=envelope.consequence,
        )
        component_results.append(
            {
                "property": component.property_name,
                "state": component.state.value,
                "decision": component_decision.value,
                "failure": component.failure.value,
                "reason": component.reason,
            }
        )
        if (
            component_decision is not Decision.AUTHORIZED
            or component.failure is not FailureCode.NONE
            or component.state is not AssuranceState.PRESERVED
        ):
            blocking_components.append(component)

    if blocking_components:
        contradicted = any(
            component.state is AssuranceState.CONTRADICTED
            for component in blocking_components
        )
        state = (
            AssuranceState.CONTRADICTED
            if contradicted
            else AssuranceState.UNKNOWN
        )
        failure = (
            FailureCode.CONTRADICTORY_EVIDENCE
            if contradicted
            else FailureCode.COMPOSITION_UNRESOLVED
        )
        decision = (
            Decision.DENY
            if envelope.consequence.lower() == "critical"
            else Decision.QUARANTINE
        )
        blocked = ", ".join(
            component.property_name for component in blocking_components
        )
        return _envelope_result(
            envelope,
            property_name=property_name,
            state=state,
            decision=decision,
            failure=failure,
            reason=(
                "Envelope authorization withheld because one or more material "
                f"assurance components are unresolved: {blocked}."
            ),
            component_results=tuple(component_results),
        )

    return _envelope_result(
        envelope,
        property_name=primary.property_name,
        state=primary.state,
        decision=primary_decision,
        failure=primary.failure,
        reason=primary.reason,
        component_results=tuple(component_results),
    )
