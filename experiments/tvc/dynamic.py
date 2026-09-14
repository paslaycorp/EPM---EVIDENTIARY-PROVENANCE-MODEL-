"""Dynamic obligation derivation experiment for TVC.

Unlike DEFAULT_POLICY, this module derives material obligations from the actual
runtime justification graph.  It remains experimental and outside src/epm.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from epm.justification import JustificationGraph, JustificationNodeType
from epm.temporal import (
    EvidenceAvailability,
    TemporalAvailabilityResult,
    assess_temporal_availability,
)


@dataclass(frozen=True)
class DerivedGraphObligation:
    obligation_id: str
    kind: str
    source_id: str
    target_id: str
    provenance_ref: str


def derive_graph_obligations(
    graph: JustificationGraph,
    *,
    target_id: str,
) -> tuple[DerivedGraphObligation, ...]:
    """Derive obligations by traversing the target's recorded justification structure.

    The obligation set is not selected from a fixed standing table.  Every
    material incoming dependency reachable from target_id becomes a concrete
    obligation identified by relation and endpoints.
    """
    if target_id not in graph.nodes:
        return ()

    incoming: dict[str, list] = {node_id: [] for node_id in graph.nodes}
    for edge in graph.edges:
        incoming.setdefault(edge.target_id, []).append(edge)

    obligations: list[DerivedGraphObligation] = []
    visited_edges: set[tuple[str, str, str]] = set()
    stack = [target_id]
    while stack:
        target = stack.pop()
        for edge in incoming.get(target, []):
            key = (edge.source_id, edge.target_id, edge.relation.value)
            if key in visited_edges:
                continue
            visited_edges.add(key)
            source = graph.nodes.get(edge.source_id)
            if source is None:
                continue
            obligations.append(
                DerivedGraphObligation(
                    obligation_id=f"{edge.relation.value}:{edge.source_id}->{edge.target_id}",
                    kind=edge.relation.value,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    provenance_ref=edge.provenance_ref,
                )
            )
            # Evidence/attestation nodes terminate a dependency chain; derived
            # and constraint nodes recursively expose their own prerequisites.
            if source.node_type not in {
                JustificationNodeType.EVIDENCE,
                JustificationNodeType.ATTESTATION,
            }:
                stack.append(edge.source_id)

    return tuple(sorted(obligations, key=lambda o: o.obligation_id))


def assess_graph_obligation_availability(
    graph: JustificationGraph,
    *,
    target_id: str,
    state_at: datetime | None,
    availability: Iterable[EvidenceAvailability],
) -> tuple[TemporalAvailabilityResult, ...]:
    """Demand historical availability for every dependency derived from the graph.

    This deliberately reuses EPM's trusted availability primitive.  The
    experimental delta is obligation generation: callers do not pre-author a
    fixed list of dependency identifiers for validation.
    """
    obligations = derive_graph_obligations(graph, target_id=target_id)
    records: dict[str, EvidenceAvailability] = {}
    duplicate_ids: set[str] = set()
    for record in availability:
        if record.evidence_id in records:
            duplicate_ids.add(record.evidence_id)
        records[record.evidence_id] = record

    results: list[TemporalAvailabilityResult] = []
    for obligation in obligations:
        if obligation.obligation_id in duplicate_ids:
            results.append(
                TemporalAvailabilityResult(
                    evidence_id=obligation.obligation_id,
                    state_at=state_at,
                    status=__import__("epm.temporal", fromlist=["TemporalAvailability"]).TemporalAvailability.UNKNOWN,
                    trusted=False,
                    reason_code="DEPENDENCY_AVAILABILITY_AMBIGUOUS",
                    reason="Multiple availability records claim the same graph-derived dependency identity.",
                )
            )
            continue
        results.append(
            assess_temporal_availability(
                evidence_id=obligation.obligation_id,
                state_at=state_at,
                availability=records.get(obligation.obligation_id),
            )
        )
    return tuple(results)
