from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "temporal_transition_fidelity.py"
spec = importlib.util.spec_from_file_location("tvc_temporal_transition_fidelity", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)

UTC = timezone.utc
T0 = datetime(2026, 9, 6, 20, 0, tzinfo=UTC)
T1 = datetime(2026, 9, 6, 21, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 6, 22, 0, tzinfo=UTC)


def dep(name, *, te=T0, tj=T0, tb=T0, tu=T0, provenance=True, active=True):
    return tvc.DependencyClock(
        dependency_id=name,
        evidence_available_at=te,
        justification_available_at=tj,
        bound_at=tb,
        used_at=tu,
        provenance_valid=provenance,
        active=active,
    )


def reconstruct(ids):
    path_a = {"support_a", "prov_a", "rule_a"}.issubset(ids)
    path_b = {"support_b", "prov_b", "rule_b"}.issubset(ids)
    if (path_a or path_b) and "contradictions" in ids:
        return "INFERRED"
    if {"support_a", "prov_a"}.issubset(ids) or {"support_b", "prov_b"}.issubset(ids):
        return "EVIDENCED"
    return "UNKNOWN"


def select_path(ids):
    if {"support_a", "prov_a", "rule_a"}.issubset(ids):
        return frozenset({"support_a", "prov_a", "rule_a", "contradictions"})
    if {"support_b", "prov_b", "rule_b"}.issubset(ids):
        return frozenset({"support_b", "prov_b", "rule_b", "contradictions"})
    return frozenset()


def transition(name="base"):
    return tvc.HistoricalTransition(
        transition_id=name,
        proposition="X",
        before_time=T0,
        claim_time=T1,
        prior_standing="EVIDENCED",
        asserted_standing="INFERRED",
        dependencies={
            "support_a": dep("support_a"),
            "prov_a": dep("prov_a"),
            "rule_a": dep("rule_a", tb=T1, tu=T1),
            "support_b": dep("support_b", tb=T2, tu=T2),
            "prov_b": dep("prov_b", tb=T2, tu=T2),
            "rule_b": dep("rule_b", tb=T2, tu=T2),
            "contradictions": dep("contradictions", tb=T1, tu=T1),
        },
        recorded_path=frozenset({"support_a", "prov_a", "rule_a", "contradictions"}),
    )


def generic_equal_information_control(tr):
    before = frozenset(name for name, d in tr.dependencies.items() if d.admissible_at(tr.before_time))
    at_claim = frozenset(name for name, d in tr.dependencies.items() if d.admissible_at(tr.claim_time))
    return reconstruct(before), reconstruct(at_claim), select_path(at_claim)


def test_historical_transition_closes_when_only_actual_t1_path_is_used():
    result = tvc.evaluate_temporal_transition_fidelity(transition(), reconstruct, select_path)
    assert result.status is tvc.FidelityStatus.CLOSED
    assert result.reconstructed_prior_standing == "EVIDENCED"
    assert result.reconstructed_claim_standing == "INFERRED"
    assert result.reconstructed_path == tuple(sorted({"support_a", "prov_a", "rule_a", "contradictions"}))


def test_later_alternative_path_cannot_retroactively_substitute_for_missing_t1_path():
    tr = transition("retroactive-substitution")
    deps = dict(tr.dependencies)
    deps["rule_a"] = dep("rule_a", tj=T2, tb=T2, tu=T2)
    mutated = replace(tr, dependencies=deps)
    result = tvc.evaluate_temporal_transition_fidelity(mutated, reconstruct, select_path)
    assert result.status is tvc.FidelityStatus.FAILED
    assert result.reconstructed_claim_standing == "EVIDENCED"
    assert "rule_a" not in result.admissible_at_claim


def test_same_endpoint_but_wrong_historical_path_is_detected():
    tr = transition("path-substitution")
    deps = dict(tr.dependencies)
    deps["support_a"] = dep("support_a", tb=T2, tu=T2)
    deps["prov_a"] = dep("prov_a", tb=T2, tu=T2)
    deps["rule_a"] = dep("rule_a", tb=T2, tu=T2)
    deps["support_b"] = dep("support_b", tb=T0, tu=T0)
    deps["prov_b"] = dep("prov_b", tb=T0, tu=T0)
    deps["rule_b"] = dep("rule_b", tb=T1, tu=T1)
    mutated = replace(tr, dependencies=deps)
    result = tvc.evaluate_temporal_transition_fidelity(mutated, reconstruct, select_path)
    assert result.reconstructed_claim_standing == "INFERRED"
    assert result.status is tvc.FidelityStatus.PATH_MISMATCH
    assert result.closure_boundary == "justification_path"


def test_temporal_cut_topology_changes_when_second_path_becomes_usable_later():
    tr = transition("cut-drift")
    at_t1 = tvc.evaluate_temporal_transition_fidelity(tr, reconstruct, select_path)
    late = replace(tr, claim_time=T2, asserted_standing="INFERRED", recorded_path=frozenset())
    at_t2 = tvc.evaluate_temporal_transition_fidelity(late, reconstruct, select_path)
    assert set(map(frozenset, at_t1.minimal_cut_sets)) != set(map(frozenset, at_t2.minimal_cut_sets))


def test_recorded_cut_topology_detects_drift_even_with_same_standing():
    tr = transition("record-cuts")
    baseline = tvc.evaluate_temporal_transition_fidelity(tr, reconstruct, select_path)
    recorded = tuple(frozenset(x) for x in baseline.minimal_cut_sets)
    late = replace(
        tr,
        claim_time=T2,
        asserted_standing="INFERRED",
        recorded_path=frozenset(),
        recorded_cut_sets=recorded,
    )
    result = tvc.evaluate_temporal_transition_fidelity(late, reconstruct, select_path)
    assert result.reconstructed_claim_standing == "INFERRED"
    assert result.status is tvc.FidelityStatus.TOPOLOGY_DRIFT
    assert result.closure_boundary == "necessity_topology"


def test_equal_information_generic_transition_verifier_matches_endpoint_and_path():
    cases = [transition("equal-clean")]
    tr = transition("equal-future-rule")
    deps = dict(tr.dependencies)
    deps["rule_a"] = dep("rule_a", tj=T2, tb=T2, tu=T2)
    cases.append(replace(tr, dependencies=deps))

    for case in cases:
        result = tvc.evaluate_temporal_transition_fidelity(case, reconstruct, select_path)
        prior, claimed, path = generic_equal_information_control(case)
        assert result.reconstructed_prior_standing == prior
        assert result.reconstructed_claim_standing == claimed
        assert frozenset(result.reconstructed_path) == path


def test_binding_time_and_use_time_are_independent_failure_boundaries():
    base = transition("split-binding-use")
    deps_bound_late = dict(base.dependencies)
    deps_bound_late["rule_a"] = dep("rule_a", te=T0, tj=T0, tb=T2, tu=T2)
    deps_used_late = dict(base.dependencies)
    deps_used_late["rule_a"] = dep("rule_a", te=T0, tj=T0, tb=T0, tu=T2)

    a = tvc.evaluate_temporal_transition_fidelity(replace(base, dependencies=deps_bound_late), reconstruct, select_path)
    b = tvc.evaluate_temporal_transition_fidelity(replace(base, dependencies=deps_used_late), reconstruct, select_path)

    assert a.status is tvc.FidelityStatus.FAILED
    assert b.status is tvc.FidelityStatus.FAILED


def test_transition_fingerprint_changes_on_path_history_change():
    a = tvc.evaluate_temporal_transition_fidelity(transition("fingerprint"), reconstruct, select_path)
    tr = transition("fingerprint")
    deps = dict(tr.dependencies)
    deps["rule_a"] = dep("rule_a", tb=T0, tu=T1)
    b = tvc.evaluate_temporal_transition_fidelity(replace(tr, dependencies=deps), reconstruct, select_path)
    assert a.transition_fingerprint != b.transition_fingerprint
