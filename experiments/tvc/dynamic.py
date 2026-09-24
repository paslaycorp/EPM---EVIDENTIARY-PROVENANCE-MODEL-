"""Dynamic obligation derivation experiment for TVC.

Unlike DEFAULT_POLICY, this module derives material obligations from the actual
runtime justification graph. It remains experimental and outside src/epm.
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from epm.justification import JustificationGraph, JustificationNodeType
from epm.temporal import (
    EvidenceAvailability,
    TemporalAvailability,
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
    provenance_refs: tuple[str, ...] = ()


def derive_graph_obligations(
    graph: JustificationGraph,
    *,
    target_id: str,
) -> tuple[DerivedGraphObligation, ...]:
    """Derive obligations by traversing the target's recorded justification structure.

    The obligation set is not selected from a fixed standing table. Every
    material incoming dependency reachable from target_id becomes a concrete
    obligation identified by relation and endpoints.
    """
    if target_id not in graph.nodes:
        return ()

    incoming: dict[str, list] = {node_id: [] for node_id in graph.nodes}
    provenance_by_edge: dict[tuple[str, str, str], set[str]] = {}
    for edge in graph.edges:
        incoming.setdefault(edge.target_id, []).append(edge)
        identity = (edge.source_id, edge.target_id, edge.relation.value)
        provenance_by_edge.setdefault(identity, set()).add(edge.provenance_ref)

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
            provenance_refs = tuple(sorted(provenance_by_edge[key]))
            obligations.append(
                DerivedGraphObligation(
                    obligation_id=f"{edge.relation.value}:{edge.source_id}->{edge.target_id}",
                    kind=edge.relation.value,
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    # A first-seen provenance is not a justified resolution.
                    provenance_ref=provenance_refs[0] if len(provenance_refs) == 1 else "",
                    provenance_refs=provenance_refs,
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

    This deliberately reuses EPM's trusted availability primitive. The
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
        if len(obligation.provenance_refs) > 1:
            results.append(
                TemporalAvailabilityResult(
                    evidence_id=obligation.obligation_id,
                    state_at=state_at,
                    status=TemporalAvailability.UNKNOWN,
                    trusted=False,
                    reason_code="DEPENDENCY_PROVENANCE_AMBIGUOUS",
                    reason="Parallel graph assertions have distinct provenance; availability cannot resolve their identity.",
                )
            )
            continue
        if obligation.obligation_id in duplicate_ids:
            results.append(
                TemporalAvailabilityResult(
                    evidence_id=obligation.obligation_id,
                    state_at=state_at,
                    status=TemporalAvailability.UNKNOWN,
                    trusted=False,
                    reason_code="DEPENDENCY_AVAILABILITY_AMBIGUOUS",
                    reason=(
                        "Multiple availability records claim the same graph-derived "
                        "dependency identity."
                    ),
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
