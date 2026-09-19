from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest


_MODULE_PATH = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "selective_surface.py"
_SPEC = spec_from_file_location("tvc_selective_surface", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = module_from_spec(_SPEC)
sys.modules[_SPEC.name] = _MODULE
_SPEC.loader.exec_module(_MODULE)
analyze_counterfactual_boundary = _MODULE.analyze_counterfactual_boundary
material_counterfactual_frontier = _MODULE.material_counterfactual_frontier
NonMonotonicFrontierError = _MODULE.NonMonotonicFrontierError


def redundant_paths(active: frozenset[str]) -> str:
    path_a = {"a_support", "a_rule"}.issubset(active)
    path_b = {"b_support", "b_rule"}.issubset(active)
    provenance = "provenance" in active
    contradiction_clear = "contradictions" in active
    if provenance and contradiction_clear and (path_a or path_b):
        return "INFERRED"
    if provenance and ("a_support" in active or "b_support" in active):
        return "EVIDENCED"
    return "UNKNOWN"


def test_frontier_captures_compositional_failures_hidden_by_single_ablation():
    deps = {"a_support", "a_rule", "b_support", "b_rule", "provenance", "contradictions"}
    frontier = material_counterfactual_frontier(deps, redundant_paths)
    removals = {frozenset(r) for r, _ in frontier.minimal_failure_interventions}
    assert frozenset({"contradictions"}) in removals
    assert frozenset({"provenance"}) in removals
    assert frozenset({"a_rule", "b_rule"}) in removals
    assert frozenset({"a_support", "b_support"}) in removals


def test_frontier_is_smaller_than_full_powerset_for_redundant_graph():
    deps = {"a_support", "a_rule", "b_support", "b_rule", "provenance", "contradictions"}
    frontier = material_counterfactual_frontier(deps, redundant_paths)
    assert len(frontier.minimal_failure_interventions) < (2 ** len(deps))


def test_same_endpoint_can_have_different_material_frontier():
    deps = {"a_support", "a_rule", "b_support", "b_rule", "provenance", "contradictions"}

    def later_semantics(active: frozenset[str]) -> str:
        if {"a_support", "a_rule", "provenance", "contradictions"}.issubset(active):
            return "INFERRED"
        if {"b_support", "provenance", "contradictions"}.issubset(active):
            return "INFERRED"
        if "provenance" in active and ("a_support" in active or "b_support" in active):
            return "EVIDENCED"
        return "UNKNOWN"

    original = material_counterfactual_frontier(deps, redundant_paths)
    later = material_counterfactual_frontier(deps, later_semantics)
    assert original.baseline_standing == later.baseline_standing == "INFERRED"
    assert original.digest != later.digest
    assert original.minimal_failure_interventions != later.minimal_failure_interventions


def test_frontier_is_order_invariant_and_deterministic():
    deps_a = ["b_rule", "a_support", "contradictions", "provenance", "a_rule", "b_support"]
    deps_b = list(reversed(deps_a))
    a = material_counterfactual_frontier(deps_a, redundant_paths)
    b = material_counterfactual_frontier(deps_b, redundant_paths)
    assert a == b


def monotone_failure(active: frozenset[str]) -> str:
    return "INFERRED" if "a" in active else "EVIDENCED"


def recovery_island(active: frozenset[str]) -> str:
    if "a" in active:
        return "INFERRED"
    if "b" not in active:
        return "INFERRED"
    return "EVIDENCED"


def test_recovery_island_has_same_minimal_failure_as_monotone_system():
    deps = {"a", "b", "c"}
    monotone = analyze_counterfactual_boundary(deps, monotone_failure)
    island = analyze_counterfactual_boundary(deps, recovery_island)

    assert monotone.minimal_failure_interventions == island.minimal_failure_interventions
    assert monotone.baseline_failure_monotone is True
    assert island.baseline_failure_monotone is False
    assert island.recovery_crossings
    assert monotone.digest != island.digest


def test_material_frontier_fails_closed_on_nonmonotonic_recovery():
    deps = {"a", "b", "c"}

    with pytest.raises(NonMonotonicFrontierError) as exc:
        material_counterfactual_frontier(deps, recovery_island)

    audit = exc.value.audit
    assert audit.baseline_standing == "INFERRED"
    assert audit.baseline_failure_monotone is False
    assert any(
        crossing.failed_intervention == ("a",)
        and crossing.recovered_intervention == ("a", "b")
        for crossing in audit.recovery_crossings
    )


def test_monotone_frontier_still_compresses_after_full_boundary_audit():
    deps = {"a", "b", "c"}
    audit = analyze_counterfactual_boundary(deps, monotone_failure)
    frontier = material_counterfactual_frontier(deps, monotone_failure)

    assert audit.baseline_failure_monotone is True
    assert audit.recovery_crossings == ()
    assert frontier.minimal_failure_interventions == ((("a",), "EVIDENCED"),)
    assert len(frontier.minimal_failure_interventions) < (2 ** len(deps))


def test_exhaustive_three_dependency_surfaces_validate_compression_gate():
    deps = ("a", "b", "c")
    full = frozenset(deps)
    removals = [
        frozenset(removed)
        for size in range(1, len(deps) + 1)
        for removed in __import__("itertools").combinations(deps, size)
    ]

    for pattern in range(1 << len(removals)):
        failed = {
            removed
            for index, removed in enumerate(removals)
            if pattern & (1 << index)
        }

        def semantics(active: frozenset[str], failed=failed) -> str:
            removed = full - active
            return "EVIDENCED" if removed in failed else "INFERRED"

        expected_monotone = all(
            not any(
                failed_set.issubset(candidate) and candidate not in failed
                for candidate in removals
            )
            for failed_set in failed
        )
        audit = analyze_counterfactual_boundary(deps, semantics)
        assert audit.baseline_failure_monotone is expected_monotone

        if not expected_monotone:
            with pytest.raises(NonMonotonicFrontierError):
                material_counterfactual_frontier(deps, semantics)
            continue

        frontier = material_counterfactual_frontier(deps, semantics)
        minimal = {
            frozenset(removed)
            for removed, _ in frontier.minimal_failure_interventions
        }
        represented = {
            candidate
            for candidate in removals
            if any(seed.issubset(candidate) for seed in minimal)
        }
        assert represented == failed
