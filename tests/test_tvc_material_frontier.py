from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


_MODULE_PATH = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "selective_surface.py"
_SPEC = spec_from_file_location("tvc_selective_surface", _MODULE_PATH)
assert _SPEC is not None and _SPEC.loader is not None
_MODULE = module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)
material_counterfactual_frontier = _MODULE.material_counterfactual_frontier


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
