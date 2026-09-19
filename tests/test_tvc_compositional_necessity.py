from __future__ import annotations

import importlib.util
import itertools
import sys
from dataclasses import dataclass, replace
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_compositional_necessity", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


def c(name, status=tvc.ObligationStatus.SATISFIED, *, available=True, provenance=True):
    return tvc.HistoricalCondition(name, status, available, provenance)


def snapshot(case, conditions, standing="INFERRED"):
    return tvc.EpistemicSnapshot(
        case,
        "X",
        standing,
        "2026-09-06T20:56:00-05:00",
        conditions,
    )


def admissible_names(s):
    return {
        name
        for name, condition in s.conditions.items()
        if condition.available_at_claim_time
        and condition.provenance_valid
        and condition.status is tvc.ObligationStatus.SATISFIED
    }


def reconstruct_two_path(s):
    """Two independent inference paths share one contradiction disposition.

    Path A: support_a + provenance_a + rule_a
    Path B: support_b + provenance_b + rule_b
    Either complete path can support INFERRED, but contradictions is globally required.
    """
    a = admissible_names(s)
    path_a = {"support_a", "provenance_a", "rule_a"}.issubset(a)
    path_b = {"support_b", "provenance_b", "rule_b"}.issubset(a)
    if (path_a or path_b) and "contradictions" in a:
        return "INFERRED"
    if ({"support_a", "provenance_a"}.issubset(a) or {"support_b", "provenance_b"}.issubset(a)):
        return "EVIDENCED"
    return "UNKNOWN"


def remove_set(s, dependency_ids):
    conditions = dict(s.conditions)
    for dependency_id in dependency_ids:
        original = conditions[dependency_id]
        conditions[dependency_id] = replace(
            original,
            status=tvc.ObligationStatus.FAILED,
            reason="counterfactual set removal",
        )
    suffix = "+".join(sorted(dependency_ids))
    return replace(s, state_id=f"{s.state_id}-without-{suffix}", conditions=conditions)


@dataclass(frozen=True)
class CutSetFinding:
    members: frozenset[str]
    baseline: str
    reproduced: str


def minimal_cut_sets(s, dependency_ids):
    """Return inclusion-minimal dependency sets whose removal changes standing."""
    baseline = reconstruct_two_path(s)
    cuts = []
    ordered = tuple(sorted(dependency_ids))
    for size in range(1, len(ordered) + 1):
        for combo in itertools.combinations(ordered, size):
            members = frozenset(combo)
            if any(existing.members < members for existing in cuts):
                continue
            reproduced = reconstruct_two_path(remove_set(s, members))
            if reproduced != baseline:
                cuts.append(CutSetFinding(members, baseline, reproduced))
    return tuple(cuts)


def singleton_only_control(s, dependency_ids):
    baseline = reconstruct_two_path(s)
    return {
        dependency_id
        for dependency_id in dependency_ids
        if reconstruct_two_path(remove_set(s, {dependency_id})) != baseline
    }


def generic_exhaustive_control(s, dependency_ids):
    """Equal-information generic control with unrestricted subset interventions."""
    baseline = reconstruct_two_path(s)
    ordered = tuple(sorted(dependency_ids))
    cuts = []
    for size in range(1, len(ordered) + 1):
        for combo in itertools.combinations(ordered, size):
            members = frozenset(combo)
            if any(existing[0] < members for existing in cuts):
                continue
            reproduced = reconstruct_two_path(remove_set(s, members))
            if reproduced != baseline:
                cuts.append((members, baseline, reproduced))
    return tuple(cuts)


def base_snapshot():
    return snapshot(
        "two-path",
        {
            "support_a": c("support_a"),
            "provenance_a": c("provenance_a"),
            "rule_a": c("rule_a"),
            "support_b": c("support_b"),
            "provenance_b": c("provenance_b"),
            "rule_b": c("rule_b"),
            "contradictions": c("contradictions"),
        },
    )


def test_compositional_hunt_singletons_miss_cross_path_cut_sets():
    s = base_snapshot()
    deps = tuple(s.conditions)

    singletons = singleton_only_control(s, deps)
    assert singletons == {"contradictions"}

    cuts = minimal_cut_sets(s, deps)
    cut_members = {finding.members for finding in cuts}

    # Cross-path pairs are jointly material even though neither member is
    # individually necessary. One dependency must be cut from each viable path.
    assert frozenset({"support_a", "support_b"}) in cut_members
    assert frozenset({"support_a", "provenance_b"}) in cut_members
    assert frozenset({"rule_a", "rule_b"}) in cut_members
    assert frozenset({"contradictions"}) in cut_members


def test_compositional_hunt_cut_sets_are_inclusion_minimal():
    s = base_snapshot()
    cuts = minimal_cut_sets(s, tuple(s.conditions))
    members = [finding.members for finding in cuts]

    for cut in members:
        assert not any(other < cut for other in members)
        for member in cut:
            proper_subset = set(cut)
            proper_subset.remove(member)
            assert reconstruct_two_path(remove_set(s, proper_subset)) == "INFERRED"


def test_compositional_hunt_alternate_path_masks_recorded_path_failure():
    s = base_snapshot()

    # Destroy every component of path A. Ordinary status replay still succeeds
    # because path B silently substitutes for it.
    altered = remove_set(s, {"support_a", "provenance_a", "rule_a"})
    assert reconstruct_two_path(s) == "INFERRED"
    assert reconstruct_two_path(altered) == "INFERRED"

    # But path identity is not preserved: removing one member from the remaining
    # path now collapses the state. Closure over label alone cannot express this.
    collapsed = remove_set(altered, {"rule_b"})
    assert reconstruct_two_path(collapsed) == "EVIDENCED"


def test_compositional_hunt_global_shared_dependency_is_first_order_cut():
    s = base_snapshot()
    cuts = minimal_cut_sets(s, tuple(s.conditions))
    contradictions = next(f for f in cuts if f.members == frozenset({"contradictions"}))
    assert contradictions.baseline == "INFERRED"
    assert contradictions.reproduced == "EVIDENCED"


def test_compositional_hunt_equal_information_exhaustive_generic_control_matches():
    s = base_snapshot()
    deps = tuple(s.conditions)

    candidate = tuple((f.members, f.baseline, f.reproduced) for f in minimal_cut_sets(s, deps))
    generic = generic_exhaustive_control(s, deps)

    # Hard falsification: compositional cut-set discovery is stronger than
    # singleton ablation, but it is not unique once a generic verifier receives
    # the same subset-intervention power and complete historical state.
    assert candidate == generic


def test_compositional_hunt_temporal_unavailability_changes_cut_topology():
    s = base_snapshot()
    conditions = dict(s.conditions)
    conditions["rule_b"] = c("rule_b", available=False)
    historical = replace(s, state_id="two-path-historical", conditions=conditions)

    # At the historical boundary path B does not exist. Path A components become
    # individually material even though they were redundant in the later world.
    assert reconstruct_two_path(historical) == "INFERRED"
    singletons = singleton_only_control(historical, tuple(historical.conditions))
    assert {"support_a", "provenance_a", "rule_a", "contradictions"}.issubset(singletons)
    assert "support_b" not in singletons
    assert "rule_b" not in singletons


def test_compositional_hunt_order_invariance():
    s = base_snapshot()
    deps = tuple(s.conditions)
    expected = {f.members for f in minimal_cut_sets(s, deps)}

    for ordering in (deps, tuple(reversed(deps)), tuple(sorted(deps))):
        assert {f.members for f in minimal_cut_sets(s, ordering)} == expected
