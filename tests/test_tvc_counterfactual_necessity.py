from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass, replace
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_counterfactual_necessity", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


def c(name, status=tvc.ObligationStatus.SATISFIED, *, available=True, provenance=True):
    return tvc.HistoricalCondition(name, status, available, provenance)


def snapshot(case, standing="INFERRED", **overrides):
    conditions = {
        "support_a": c("support_a"),
        "support_b": c("support_b"),
        "provenance": c("provenance"),
        "entailment": c("entailment"),
        "contradictions": c("contradictions"),
    }
    conditions.update(overrides)
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


def reconstruct(s):
    a = admissible_names(s)
    # Either support path can establish the evidentiary base. The inference
    # additionally requires entailment and contradiction disposition.
    support_ok = bool({"support_a", "support_b"} & a)
    if support_ok and {"provenance", "entailment", "contradictions"}.issubset(a):
        return "INFERRED"
    if support_ok and "provenance" in a:
        return "EVIDENCED"
    return "UNKNOWN"


@dataclass(frozen=True)
class DependencyClaim:
    dependency_id: str
    claimed_material: bool


@dataclass(frozen=True)
class CounterfactualFinding:
    dependency_id: str
    baseline: str
    without_dependency: str
    claimed_material: bool
    observed_material: bool

    @property
    def faithful(self):
        return self.claimed_material == self.observed_material


def remove_dependency(s, dependency_id):
    conditions = dict(s.conditions)
    original = conditions[dependency_id]
    conditions[dependency_id] = replace(
        original,
        status=tvc.ObligationStatus.FAILED,
        reason="counterfactual removal",
    )
    return replace(s, state_id=f"{s.state_id}-without-{dependency_id}", conditions=conditions)


def counterfactual_fidelity(s, claims):
    baseline = reconstruct(s)
    findings = []
    for claim in claims:
        altered = remove_dependency(s, claim.dependency_id)
        reproduced = reconstruct(altered)
        findings.append(
            CounterfactualFinding(
                dependency_id=claim.dependency_id,
                baseline=baseline,
                without_dependency=reproduced,
                claimed_material=claim.claimed_material,
                observed_material=reproduced != baseline,
            )
        )
    return tuple(findings)


def status_only_generic_control(s):
    """Strong prior control: reconstruct the standing, but do not perturb dependencies."""
    return reconstruct(s)


def generic_counterfactual_control(s, claims):
    """Equal-information control granted the exact same intervention semantics."""
    baseline = reconstruct(s)
    out = []
    for claim in claims:
        conditions = dict(s.conditions)
        original = conditions[claim.dependency_id]
        conditions[claim.dependency_id] = tvc.HistoricalCondition(
            original.obligation_id,
            tvc.ObligationStatus.FAILED,
            original.available_at_claim_time,
            original.provenance_valid,
            "generic counterfactual removal",
        )
        altered = tvc.EpistemicSnapshot(
            s.state_id + "-generic-" + claim.dependency_id,
            s.proposition,
            s.asserted_standing,
            s.claimed_at,
            conditions,
        )
        reproduced = reconstruct(altered)
        out.append((claim.dependency_id, baseline, reproduced, claim.claimed_material, reproduced != baseline))
    return tuple(out)


def test_hunt_hidden_redundancy_same_standing_but_materiality_claim_is_false():
    s = snapshot("redundant-support")
    claims = (
        DependencyClaim("support_a", True),
        DependencyClaim("support_b", False),
    )

    # Ordinary replay sees a perfectly reproducible INFERRED standing.
    assert status_only_generic_control(s) == "INFERRED"

    findings = counterfactual_fidelity(s, claims)
    by_id = {finding.dependency_id: finding for finding in findings}

    # support_a was declared material, but support_b independently preserves the
    # same standing. The status is reproducible while the dependency story is not.
    assert by_id["support_a"].baseline == "INFERRED"
    assert by_id["support_a"].without_dependency == "INFERRED"
    assert by_id["support_a"].claimed_material is True
    assert by_id["support_a"].observed_material is False
    assert by_id["support_a"].faithful is False


def test_hunt_hidden_material_dependency_same_baseline_label_exposes_missing_claim():
    s = snapshot("hidden-entailment")
    claims = (
        DependencyClaim("entailment", False),
    )

    assert status_only_generic_control(s) == "INFERRED"
    finding = counterfactual_fidelity(s, claims)[0]

    # The recorded dependency story says entailment is incidental, but removing
    # it downgrades the standing. Counterfactual replay exposes hidden materiality.
    assert finding.without_dependency == "EVIDENCED"
    assert finding.claimed_material is False
    assert finding.observed_material is True
    assert finding.faithful is False


def test_hunt_truthful_dependency_claims_survive_counterfactual_probe():
    s = snapshot("faithful")
    claims = (
        DependencyClaim("support_a", False),
        DependencyClaim("support_b", False),
        DependencyClaim("entailment", True),
        DependencyClaim("provenance", True),
        DependencyClaim("contradictions", True),
    )

    findings = counterfactual_fidelity(s, claims)
    assert all(finding.faithful for finding in findings)


def test_hunt_equal_information_generic_counterfactual_control_matches_exactly():
    s = snapshot("equal-info")
    claims = (
        DependencyClaim("support_a", True),
        DependencyClaim("support_b", False),
        DependencyClaim("entailment", True),
        DependencyClaim("provenance", True),
        DependencyClaim("contradictions", True),
    )

    candidate = tuple(
        (
            f.dependency_id,
            f.baseline,
            f.without_dependency,
            f.claimed_material,
            f.observed_material,
        )
        for f in counterfactual_fidelity(s, claims)
    )
    generic = generic_counterfactual_control(s, claims)

    # Critical falsification: dependency-fidelity checking is useful relative to
    # status-only replay, but it is not unique once the generic verifier receives
    # the same intervention operator and materiality declarations.
    assert candidate == generic


def test_hunt_double_removal_exposes_compositional_necessity_missed_by_single_ablation():
    s = snapshot("joint-necessity")

    # Neither redundant support is individually material.
    single = counterfactual_fidelity(
        s,
        (
            DependencyClaim("support_a", False),
            DependencyClaim("support_b", False),
        ),
    )
    assert all(f.faithful for f in single)

    # But the pair is jointly necessary. This is the first genuinely richer
    # target: materiality may belong to a dependency set, not to a single edge.
    once = remove_dependency(s, "support_a")
    twice = remove_dependency(once, "support_b")
    assert reconstruct(s) == "INFERRED"
    assert reconstruct(once) == "INFERRED"
    assert reconstruct(twice) == "UNKNOWN"
