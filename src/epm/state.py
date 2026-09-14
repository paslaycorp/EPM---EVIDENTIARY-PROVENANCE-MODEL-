"""Aggregate domain-neutral evidentiary state for EPM."""
from __future__ import annotations

from dataclasses import dataclass

from .assurance import State
from .constraints import Constraint, ConstraintEvaluation, evaluate_constraint
from .justification import CycleResult, JustificationGraph, detect_cycle
from .resolution import AnswerSpaceSnapshot, AnswerSpaceValidation, validate_answer_space
from .sources import EpistemicSourceRecord, SourceTypingResult, validate_source_record
from .temporal import EvidenceAvailability, TemporalAvailabilityResult, assess_temporal_availability

EVIDENTIARY_STATE_SCHEMA = "epm.evidentiary-state/0.1"


@dataclass(frozen=True)
class EvidentiaryState:
    state_id: str
    proposition: str
    assurance_state: State
    sources: tuple[EpistemicSourceRecord, ...] = ()
    availability: tuple[EvidenceAvailability, ...] = ()
    constraints: tuple[Constraint, ...] = ()
    answer_space: AnswerSpaceSnapshot | None = None
    justification_graph: JustificationGraph | None = None
    limitations: tuple[str, ...] = ()
    unresolved_conditions: tuple[str, ...] = ()
    schema_version: str = EVIDENTIARY_STATE_SCHEMA


@dataclass(frozen=True)
class EvidentiaryStateReport:
    schema_version: str
    state_id: str
    structural_issues: tuple[str, ...]
    source_results: tuple[SourceTypingResult, ...]
    availability_results: tuple[TemporalAvailabilityResult, ...]
    constraint_results: tuple[ConstraintEvaluation, ...]
    answer_space_result: AnswerSpaceValidation | None
    graph_cycle_result: CycleResult | None
    limitations: tuple[str, ...]
    unresolved_conditions: tuple[str, ...]


def _duplicate_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if value in seen and value not in duplicates:
            duplicates.append(value)
        seen.add(value)
    return tuple(duplicates)


def _timezone_aware(value) -> bool:
    return value is not None and value.tzinfo is not None and value.utcoffset() is not None


def inspect_evidentiary_state(state: EvidentiaryState) -> EvidentiaryStateReport:
    """Inspect components without collapsing them into one truth score or decision."""
    issues: list[str] = []
    if state.schema_version != EVIDENTIARY_STATE_SCHEMA:
        issues.append("SCHEMA_VERSION_UNSUPPORTED")
    if not state.state_id.strip():
        issues.append("STATE_ID_REQUIRED")
    if not state.proposition.strip():
        issues.append("PROPOSITION_REQUIRED")
    if not state.assurance_state.state_id.strip():
        issues.append("ASSURANCE_STATE_ID_REQUIRED")

    duplicate_sources = _duplicate_ids(tuple(source.source_id for source in state.sources))
    if duplicate_sources:
        issues.append("DUPLICATE_SOURCE_IDS:" + ",".join(duplicate_sources))
    duplicate_constraints = _duplicate_ids(tuple(item.constraint_id for item in state.constraints))
    if duplicate_constraints:
        issues.append("DUPLICATE_CONSTRAINT_IDS:" + ",".join(duplicate_constraints))

    state_at = state.assurance_state.context.at
    rule_effective_at = state.assurance_state.rule.effective_at
    if rule_effective_at is not None:
        if not _timezone_aware(rule_effective_at):
            issues.append("RULE_EFFECTIVE_TIME_UNCOMPARABLE")
        elif not _timezone_aware(state_at):
            issues.append("STATE_TIME_UNCOMPARABLE_FOR_RULE")
        elif rule_effective_at > state_at:
            issues.append("RULE_NOT_YET_EFFECTIVE")

    source_results = tuple(validate_source_record(source) for source in state.sources)
    constraint_results = tuple(evaluate_constraint(item) for item in state.constraints)
    answer_result = validate_answer_space(state.answer_space) if state.answer_space is not None else None
    graph_cycle = detect_cycle(state.justification_graph) if state.justification_graph is not None else None

    primary_evidence_id = state.assurance_state.state_id
    matching = [record for record in state.availability if record.evidence_id == primary_evidence_id]
    availability_results = [
        assess_temporal_availability(
            evidence_id=primary_evidence_id,
            state_at=state_at,
            availability=matching[0] if matching else None,
        )
    ]
    for record in state.availability:
        if record.evidence_id != primary_evidence_id:
            availability_results.append(
                assess_temporal_availability(
                    evidence_id=record.evidence_id,
                    state_at=state_at,
                    availability=record,
                )
            )

    return EvidentiaryStateReport(
        schema_version=state.schema_version,
        state_id=state.state_id,
        structural_issues=tuple(issues),
        source_results=source_results,
        availability_results=tuple(availability_results),
        constraint_results=constraint_results,
        answer_space_result=answer_result,
        graph_cycle_result=graph_cycle,
        limitations=state.limitations,
        unresolved_conditions=state.unresolved_conditions,
    )
