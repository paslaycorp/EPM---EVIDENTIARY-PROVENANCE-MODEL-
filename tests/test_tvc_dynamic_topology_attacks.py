from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime
from pathlib import Path

from epm import AvailabilityAttestation, EvidenceAvailability, TemporalAvailability
from epm.justification import (
    JustificationGraph,
    JustificationNode,
    JustificationNodeType,
    SupportEdge,
    SupportRelation,
)


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "dynamic.py"
spec = importlib.util.spec_from_file_location("tvc_dynamic_topology_attacks", MODULE)
assert spec and spec.loader
dynamic = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dynamic
spec.loader.exec_module(dynamic)

T1 = datetime(2026, 9, 6, 20, 56, tzinfo=UTC)


def _node(node_id: str, node_type: JustificationNodeType, *, external: bool = False):
    return JustificationNode(
        node_id=node_id,
        node_type=node_type,
        provenance_refs=(f"prov:{node_id}",),
        external_origin=external,
    )


def _base_graph() -> JustificationGraph:
    return JustificationGraph(
        nodes={
            "claim-X": _node("claim-X", JustificationNodeType.CLAIM),
            "derive-X": _node("derive-X", JustificationNodeType.DERIVATION),
            "sensor-E": _node("sensor-E", JustificationNodeType.EVIDENCE, external=True),
        },
        edges=(
            SupportEdge(
                "derive-X",
                "claim-X",
                SupportRelation.SUPPORTS,
                "prov:derive-claim",
            ),
            SupportEdge(
                "sensor-E",
                "derive-X",
                SupportRelation.DERIVATION_INPUT,
                "prov:sensor-derive",
            ),
        ),
    )


def _expanded_graph() -> JustificationGraph:
    base = _base_graph()
    nodes = dict(base.nodes)
    nodes["calibration-A"] = _node(
        "calibration-A", JustificationNodeType.ATTESTATION, external=True
    )
    return JustificationGraph(
        nodes=nodes,
        edges=base.edges
        + (
            SupportEdge(
                "calibration-A",
                "derive-X",
                SupportRelation.ATTESTS,
                "prov:calibration-later",
            ),
        ),
    )


def _availability(obligation_id: str) -> EvidenceAvailability:
    return EvidenceAvailability(
        evidence_id=obligation_id,
        available_at=T1,
        observed_at=T1,
        source="historical-fixture",
        provenance_ref=f"availability:{obligation_id}",
        attestation=AvailabilityAttestation(
            attestation_id=f"att:{obligation_id}",
            authority="fixture-authority",
            method="signed-history",
            basis="bounded topology attack fixture",
            validated=True,
        ),
    )


def _ids(graph: JustificationGraph) -> tuple[str, ...]:
    return tuple(
        item.obligation_id
        for item in dynamic.derive_graph_obligations(graph, target_id="claim-X")
    )


def test_current_dynamic_graph_can_project_later_topology_into_earlier_state():
    """Falsification: graph edges have no historical/effective-time boundary.

    The same T1 availability set closes against the T1 graph but becomes
    UNKNOWN when a later dependency is present in the graph supplied for replay.
    Dynamic v0.1 cannot tell whether that dependency existed at T1.
    """
    historical_graph = _base_graph()
    current_graph = _expanded_graph()
    historical_records = tuple(_availability(item) for item in _ids(historical_graph))

    at_t1 = dynamic.assess_graph_obligation_availability(
        historical_graph,
        target_id="claim-X",
        state_at=T1,
        availability=historical_records,
    )
    projected = dynamic.assess_graph_obligation_availability(
        current_graph,
        target_id="claim-X",
        state_at=T1,
        availability=historical_records,
    )

    assert all(result.status is TemporalAvailability.AVAILABLE for result in at_t1)
    assert any(
        result.evidence_id.startswith("ATTESTS:calibration-A->derive-X")
        and result.status is TemporalAvailability.UNKNOWN
        for result in projected
    )


def test_partial_graph_can_hide_a_material_dependency():
    """Falsification: no graph-completeness attestation exists in dynamic v0.1."""
    partial = _base_graph()
    complete = _expanded_graph()
    records = tuple(_availability(item) for item in _ids(partial))

    partial_results = dynamic.assess_graph_obligation_availability(
        partial,
        target_id="claim-X",
        state_at=T1,
        availability=records,
    )
    complete_results = dynamic.assess_graph_obligation_availability(
        complete,
        target_id="claim-X",
        state_at=T1,
        availability=records,
    )

    assert all(result.status is TemporalAvailability.AVAILABLE for result in partial_results)
    assert any(result.status is TemporalAvailability.UNKNOWN for result in complete_results)
    assert len(complete_results) == len(partial_results) + 1


def test_parallel_dependency_provenance_is_currently_collapsed():
    """Falsification: provenance-distinct parallel edges share one obligation key."""
    base = _base_graph()
    graph = JustificationGraph(
        nodes=base.nodes,
        edges=base.edges
        + (
            SupportEdge(
                "sensor-E",
                "derive-X",
                SupportRelation.DERIVATION_INPUT,
                "prov:second-independent-edge-assertion",
            ),
        ),
    )

    obligations = dynamic.derive_graph_obligations(graph, target_id="claim-X")
    sensor_obligations = [
        item
        for item in obligations
        if item.source_id == "sensor-E" and item.target_id == "derive-X"
    ]

    assert len(sensor_obligations) == 1
    assert len(
        [
            edge
            for edge in graph.edges
            if edge.source_id == "sensor-E"
            and edge.target_id == "derive-X"
            and edge.relation is SupportRelation.DERIVATION_INPUT
        ]
    ) == 2
