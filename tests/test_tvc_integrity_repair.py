"""Regression witnesses from the independent PR #31 review, outside EPM Core."""
from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from itertools import permutations
from pathlib import Path

import pytest

from epm import AvailabilityAttestation, EvidenceAvailability
from epm.justification import (
    JustificationGraph,
    JustificationNode,
    JustificationNodeType,
    SupportEdge,
    SupportRelation,
)


def load(name):
    path = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / (name + ".py")
    spec = importlib.util.spec_from_file_location("integrity_repair_" + name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


contract_api = load("prospective_closure_contract")
closure_api = load("tvc")
dynamic_api = load("dynamic")
AT = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)


def original(active):
    return "INFERRED" if "a" in active else "EVIDENCED"


def drifted(active):
    return "INFERRED" if "b" in active else "EVIDENCED"


def issue(oracle=original, **changes):
    values = dict(transition_id="claim-X", issued_at=AT, policy_id="p1",
                  prior_standing="EVIDENCED", material_dependencies=("a", "b"),
                  reconstruct=oracle)
    values.update(changes)
    registry = {}

    def anchor(value):
        registry["original-receipt"] = value
        return "original-receipt"

    artifact = contract_api.issue_contract(**values, anchor=anchor)
    return artifact, lambda value, ref: registry.get(ref) == value


@pytest.mark.parametrize("field,value", [
    ("transition_id", "different-claim"),
    ("policy_id", "p2"),
    ("issued_at", AT + timedelta(days=1)),
    ("prior_standing", "UNKNOWN"),
])
def test_changed_payload_with_original_receipt_is_rejected_before_reconstruction(field, value):
    artifact, verify = issue()
    calls = []

    def oracle(active):
        calls.append(active)
        return original(active)

    result = contract_api.close_against_contract(
        replace(artifact, **{field: value}), asserted_standing="INFERRED",
        reconstruct=oracle, verify_anchor=verify)
    assert not result.valid
    assert result.reason == "PAYLOAD_DIGEST_MISMATCH"
    assert calls == []


def test_replaced_surface_cannot_conceal_drift_behind_original_receipt():
    artifact, verify = issue()
    later, _ = issue(drifted)
    assert original(frozenset(("a", "b"))) == drifted(frozenset(("a", "b")))
    forged = replace(artifact, prospective_surface=later.prospective_surface)
    result = contract_api.close_against_contract(
        forged, asserted_standing="INFERRED", reconstruct=drifted, verify_anchor=verify)
    assert not result.valid
    assert result.reason == "PAYLOAD_DIGEST_MISMATCH"


def test_rehashing_changed_payload_does_not_make_old_receipt_valid():
    artifact, verify = issue()
    other, _ = issue(transition_id="different-claim")
    assert artifact.anchor_ref == other.anchor_ref
    result = contract_api.close_against_contract(
        other, asserted_standing="INFERRED", reconstruct=original, verify_anchor=verify)
    assert not result.valid
    assert result.reason == "ANCHOR_MISMATCH"


def test_newline_metadata_cannot_collide_across_field_boundaries():
    # These metadata sequences collide under the previous newline serialization.
    left, _ = issue(policy_id="p\nx", prior_standing="y")
    right, _ = issue(policy_id="p", prior_standing="x\ny")
    assert left.contract_digest != right.contract_digest


def test_dependency_delimiters_do_not_collide_with_separate_identifiers():
    left, _ = issue(material_dependencies=("a,b",))
    right, _ = issue(material_dependencies=("a", "b"))
    assert left.contract_digest != right.contract_digest


def test_equivalent_timezone_and_dependency_order_have_same_v2_commitment():
    left, _ = issue()
    right, _ = issue(issued_at=AT.astimezone(timezone(timedelta(hours=-5))),
                     material_dependencies=("b", "a"))
    assert left.contract_digest == right.contract_digest
    assert left.prospective_surface == right.prospective_surface


def test_naive_issue_time_is_rejected():
    with pytest.raises(ValueError, match="timezone"):
        issue(issued_at=AT.replace(tzinfo=None))


@pytest.mark.parametrize("field,value", [
    ("schema", "tvc.prospective-closure/v1"),
    ("material_dependencies", ("b", "a")),
    ("material_dependencies", ("a", "a", "b")),
    ("prospective_surface", ()),
    ("issued_at", AT.replace(tzinfo=None)),
])
def test_noncanonical_or_unsupported_payload_fails_closed(field, value):
    artifact, verify = issue()
    result = contract_api.close_against_contract(
        replace(artifact, **{field: value}), asserted_standing="INFERRED",
        reconstruct=original, verify_anchor=verify)
    assert not result.valid
    assert result.reason in {"CONTRACT_SCHEMA_UNSUPPORTED", "CONTRACT_PAYLOAD_INVALID"}


def test_clean_contract_and_genuine_drift_still_have_distinct_outcomes():
    artifact, verify = issue()
    clean = contract_api.close_against_contract(
        artifact, asserted_standing="INFERRED", reconstruct=original, verify_anchor=verify)
    changed = contract_api.close_against_contract(
        artifact, asserted_standing="INFERRED", reconstruct=drifted, verify_anchor=verify)
    assert clean.valid and clean.reason == "CLOSED"
    assert not changed.valid and changed.reason == "PROSPECTIVE_SURFACE_MISMATCH"


def test_full_closure_result_is_identical_under_policy_and_condition_reordering():
    required = closure_api.DEFAULT_POLICY["INFERRED"]
    conditions = {o.obligation_id: closure_api.HistoricalCondition(
        o.obligation_id, closure_api.ObligationStatus.SATISFIED, True, True) for o in required}
    conditions["entailment"] = replace(conditions["entailment"], available_at_claim_time=False)
    conditions["contradictions"] = replace(conditions["contradictions"], status=closure_api.ObligationStatus.UNRESOLVED)
    snapshot = closure_api.EpistemicSnapshot("X", "X", "INFERRED", AT.isoformat(), conditions)
    reverify = lambda _snapshot, active: "EVIDENCED" if {"support", "provenance"} <= active else "UNKNOWN"
    expected = closure_api.evaluate_closure(snapshot, closure_api.DEFAULT_POLICY, reverify)
    for order in permutations(required):
        policy = {**closure_api.DEFAULT_POLICY, "INFERRED": order}
        changed = replace(snapshot, conditions=dict(reversed(list(conditions.items()))))
        assert closure_api.evaluate_closure(changed, policy, reverify) == expected


def test_explicit_priority_and_custom_tie_break_are_policy_data():
    # Covers custom obligations, not just names in DEFAULT_POLICY.
    duties = (closure_api.Obligation("z", "z", "CUSTOM", priority=-1),
              closure_api.Obligation("b", "b", "CUSTOM"),
              closure_api.Obligation("a", "a", "CUSTOM"))
    snapshot = closure_api.EpistemicSnapshot("X", "X", "CUSTOM", AT.isoformat(), {})
    reverify = lambda _snapshot, _active: "UNKNOWN"
    for order in permutations(duties):
        result = closure_api.evaluate_closure(snapshot, {"CUSTOM": order}, reverify)
        assert result.unresolved == ("z", "a", "b")
        assert result.closure_boundary == "z"


def parallel_graph(reverse=False, same_provenance=False):
    nodes = {name: JustificationNode(name, kind, ("p:"+name,)) for name, kind in (
        ("e", JustificationNodeType.EVIDENCE), ("d", JustificationNodeType.DERIVATION),
        ("x", JustificationNodeType.CLAIM))}
    edges = (SupportEdge("e", "d", SupportRelation.DERIVATION_INPUT, "prov-A"),
             SupportEdge("e", "d", SupportRelation.DERIVATION_INPUT, "prov-A" if same_provenance else "prov-B"),
             SupportEdge("d", "x", SupportRelation.SUPPORTS, "prov-X"))
    return JustificationGraph(nodes=nodes, edges=tuple(reversed(edges)) if reverse else edges)


def test_parallel_provenance_is_preserved_and_cannot_be_resolved_by_one_availability_record():
    left = dynamic_api.derive_graph_obligations(parallel_graph(), target_id="x")
    right = dynamic_api.derive_graph_obligations(parallel_graph(True), target_id="x")
    assert left == right
    dependent = next(o for o in left if o.source_id == "e")
    assert dependent.provenance_refs == ("prov-A", "prov-B")
    assert dependent.provenance_ref == ""
    record = EvidenceAvailability(dependent.obligation_id, AT, AT, "fixture", "p", AvailabilityAttestation("a", "a", "m", "b", True))
    results = dynamic_api.assess_graph_obligation_availability(parallel_graph(), target_id="x", state_at=AT, availability=(record,))
    result = next(r for r in results if r.evidence_id == dependent.obligation_id)
    assert result.status.value == "UNKNOWN" and not result.trusted
    assert result.reason_code == "DEPENDENCY_PROVENANCE_AMBIGUOUS"


def test_exact_duplicate_edge_does_not_fabricate_provenance_conflict():
    obligations = dynamic_api.derive_graph_obligations(parallel_graph(same_provenance=True), target_id="x")
    dependent = next(o for o in obligations if o.source_id == "e")
    assert dependent.provenance_refs == ("prov-A",)
    assert dependent.provenance_ref == "prov-A"
