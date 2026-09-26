from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

from epm.justification import (
    JustificationGraph,
    JustificationNode,
    JustificationNodeStatus,
    JustificationNodeType,
    SupportEdge,
    SupportRelation,
)


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "dynamic.py"
spec = importlib.util.spec_from_file_location("tvc_odin_dynamic", MODULE)
assert spec and spec.loader
dynamic = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dynamic
spec.loader.exec_module(dynamic)


def n(node_id, kind, *, external=False, status=JustificationNodeStatus.ACTIVE):
    return JustificationNode(node_id, kind, (f"prov-{node_id}",), external_origin=external, status=status)


def generic_graph_verifier(graph: JustificationGraph, target_id: str):
    """Strongest generic equal-information opponent used by Odin.

    It traverses every reachable incoming dependency and rejects missing,
    inactive, or provenance-less material.  It deliberately has no concept of
    asserted epistemic standing, historical claim time, reconstruction, or
    forward epistemic-state reproduction.
    """
    obligations = dynamic.derive_graph_obligations(graph, target_id=target_id)
    defects = []
    for obligation in obligations:
        source = graph.nodes.get(obligation.source_id)
        if source is None:
            defects.append((obligation.obligation_id, "SOURCE_MISSING"))
        elif source.status is not JustificationNodeStatus.ACTIVE:
            defects.append((obligation.obligation_id, source.status.value))
        elif not obligation.provenance_ref.strip():
            defects.append((obligation.obligation_id, "PROVENANCE_MISSING"))
    return obligations, tuple(defects)


def topology(case):
    nodes = {
        "X": n("X", JustificationNodeType.CLAIM),
        "D1": n("D1", JustificationNodeType.DERIVATION),
        "E1": n("E1", JustificationNodeType.EVIDENCE, external=True),
    }
    edges = [
        SupportEdge("D1", "X", SupportRelation.SUPPORTS, "p-d1-x"),
        SupportEdge("E1", "D1", SupportRelation.DERIVATION_INPUT, "p-e1-d1"),
    ]
    if case in {"nested", "shared", "attested", "mutated"}:
        nodes["D2"] = n("D2", JustificationNodeType.DERIVATION)
        nodes["E2"] = n("E2", JustificationNodeType.EVIDENCE, external=True)
        edges += [
            SupportEdge("D2", "D1", SupportRelation.DERIVATION_INPUT, "p-d2-d1"),
            SupportEdge("E2", "D2", SupportRelation.DERIVATION_INPUT, "p-e2-d2"),
        ]
    if case in {"shared", "attested", "mutated"}:
        edges.append(SupportEdge("E1", "D2", SupportRelation.DERIVATION_INPUT, "p-e1-d2"))
    if case in {"attested", "mutated"}:
        nodes["A1"] = n("A1", JustificationNodeType.ATTESTATION, external=True)
        edges.append(SupportEdge("A1", "D2", SupportRelation.ATTESTS, "p-a1-d2"))
    if case == "mutated":
        nodes["E2"] = n("E2", JustificationNodeType.EVIDENCE, external=True, status=JustificationNodeStatus.INVALIDATED)
    return JustificationGraph(nodes=nodes, edges=tuple(edges))


@pytest.mark.parametrize("case", ["simple", "nested", "shared", "attested", "mutated"])
def test_odin_generic_verifier_handles_unseen_topologies_without_fixed_obligation_table(case):
    graph = topology(case)
    obligations, defects = generic_graph_verifier(graph, "X")

    assert obligations
    if case == "mutated":
        assert any(reason == "INVALIDATED" for _, reason in defects)
    else:
        assert defects == ()


def test_odin_result_kills_topology_derivation_as_unique_claim():
    """Falsification: dynamic graph obligation discovery is not uniquely TVC.

    A generic graph-aware verifier can discover the same runtime dependency set.
    Therefore TVC cannot claim novelty merely because its obligations vary with
    graph topology.  Any surviving distinction must lie in historical
    admissibility + reconstruction + epistemic self-reproduction/closure.
    """
    graph = topology("attested")
    tvc_ids = {o.obligation_id for o in dynamic.derive_graph_obligations(graph, target_id="X")}
    generic_ids = {o.obligation_id for o in generic_graph_verifier(graph, "X")[0]}
    assert generic_ids == tvc_ids


def test_odin_exposes_remaining_unimplemented_boundary():
    """The generic opponent cannot decide epistemic closure from graph state alone."""
    graph = topology("simple")
    obligations, defects = generic_graph_verifier(graph, "X")
    assert obligations and not defects

    # Identical graph facts can accompany different historical epistemic claims.
    # The graph verifier has no claim-time or reproduced-standing inputs, so its
    # result is necessarily identical.  This identifies, but does not yet prove,
    # the remaining TVC boundary to implement and test.
    claimed_states = ("EVIDENCED", "INFERRED")
    results = [(tuple(o.obligation_id for o in obligations), defects) for _ in claimed_states]
    assert results[0] == results[1]
