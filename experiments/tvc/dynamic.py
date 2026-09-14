"""Dynamic obligation derivation experiment for TVC.

Unlike DEFAULT_POLICY, this module derives material obligations from the actual
runtime justification graph.  It remains experimental and outside src/epm.
"""
from __future__ import annotations

from dataclasses import dataclass

from epm.justification import JustificationGraph, JustificationNodeType, SupportRelation


@dataclass(frozen=True)
class DerivedGraphObligation:
    obligation_id: str
    kind: str
    source_id: str
    target_id: str
    provenance_ref: str


def derive_graph_obligations(graph: JustificationGraph, *, target_id: str) -> tuple[DerivedGraphObligation, ...]:
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
            if source.node_type not in {JustificationNodeType.EVIDENCE, JustificationNodeType.ATTESTATION}:
                stack.append(edge.source_id)

    return tuple(sorted(obligations, key=lambda o: o.obligation_id))
