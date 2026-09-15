from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from epm.justification import (
    JustificationGraph,
    JustificationNode,
    JustificationNodeType,
    SupportEdge,
    SupportRelation,
)


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "dynamic.py"
spec = importlib.util.spec_from_file_location("tvc_dynamic_obligations", MODULE)
assert spec and spec.loader
dynamic = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dynamic
spec.loader.exec_module(dynamic)


def node(node_id, node_type, *, external=False):
    return JustificationNode(node_id, node_type, (f"prov-{node_id}",), external_origin=external)


def graph(with_calibration: bool) -> JustificationGraph:
    nodes = {
        "claim-X": node("claim-X", JustificationNodeType.CLAIM),
        "derive-X": node("derive-X", JustificationNodeType.DERIVATION),
        "sensor-E": node("sensor-E", JustificationNodeType.EVIDENCE, external=True),
    }
    edges = [
        SupportEdge("derive-X", "claim-X", SupportRelation.SUPPORTS, "prov-derive-claim"),
        SupportEdge("sensor-E", "derive-X", SupportRelation.DERIVATION_INPUT, "prov-sensor-derive"),
    ]
    if with_calibration:
        nodes["calibration-A"] = node("calibration-A", JustificationNodeType.ATTESTATION, external=True)
        edges.append(SupportEdge("calibration-A", "derive-X", SupportRelation.ATTESTS, "prov-calibration"))
    return JustificationGraph(nodes=nodes, edges=tuple(edges))


def test_obligations_are_generated_from_runtime_graph_not_fixed_standing_table():
    base = dynamic.derive_graph_obligations(graph(False), target_id="claim-X")
    expanded = dynamic.derive_graph_obligations(graph(True), target_id="claim-X")

    base_ids = {o.obligation_id for o in base}
    expanded_ids = {o.obligation_id for o in expanded}

    assert base_ids == {
        "SUPPORTS:derive-X->claim-X",
        "DERIVATION_INPUT:sensor-E->derive-X",
    }
    assert expanded_ids == base_ids | {"ATTESTS:calibration-A->derive-X"}


def test_same_epistemic_target_can_require_different_obligations_when_topology_changes():
    first = dynamic.derive_graph_obligations(graph(False), target_id="claim-X")
    second = dynamic.derive_graph_obligations(graph(True), target_id="claim-X")

    # Same claim identity and standing can no longer be represented by one fixed
    # obligation vector unless the validator first inspects/compiles the graph.
    assert len(first) == 2
    assert len(second) == 3
    assert first != second
