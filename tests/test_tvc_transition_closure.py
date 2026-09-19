from __future__ import annotations

import importlib.util
import sys
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "transition_closure.py"
spec = importlib.util.spec_from_file_location("tvc_transition_closure", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


UTC = timezone.utc
T0 = datetime(2026, 9, 6, 20, 0, tzinfo=UTC)
T1 = datetime(2026, 9, 6, 21, 0, tzinfo=UTC)
T2 = datetime(2026, 9, 6, 22, 0, tzinfo=UTC)


def dep(name, *, te=T0, tj=T0, tu=T0, provenance=True, active=True):
    return tvc.TemporalDependency(
        dependency_id=name,
        evidence_available_at=te,
        justification_available_at=tj,
        incorporated_at=tu,
        provenance_valid=provenance,
        active=active,
    )


def reconstruct(admissible):
    support = bool({"support_a", "support_b"} & admissible)
    if support and {"provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if support and "provenance" in admissible:
        return "EVIDENCED"
    return "UNKNOWN"


def record(name, **dependency_overrides):
    dependencies = {
        "support_a": dep("support_a"),
        "support_b": dep("support_b"),
        "provenance": dep("provenance"),
        "entailment": dep("entailment"),
        "contradictions": dep("contradictions"),
    }
    dependencies.update(dependency_overrides)
    return tvc.TransitionRecord(
        transition_id=name,
        proposition="X",
        prior_standing="EVIDENCED",
        asserted_standing="INFERRED",
        claim_time=T1,
        dependencies=dependencies,
    )


def generic_equal_information_control(r):
    admissible = frozenset(
        name
        for name, d in r.dependencies.items()
        if d.active
        and d.provenance_valid
        and d.evidence_available_at <= r.claim_time
        and d.justification_available_at <= r.claim_time
        and d.incorporated_at is not None
        and d.incorporated_at <= r.claim_time
    )
    baseline = reconstruct(admissible)
    cuts = []
    ordered = tuple(sorted(admissible))
    from itertools import combinations

    for size in range(1, len(ordered) + 1):
        for candidate_tuple in combinations(ordered, size):
            candidate = frozenset(candidate_tuple)
            if any(existing.issubset(candidate) for existing in cuts):
                continue
            if reconstruct(admissible - candidate) != baseline:
                cuts.append(candidate)
    return baseline, admissible, tuple(sorted(cuts, key=lambda s: (len(s), tuple(sorted(s)))))


def test_transition_closure_blocks_retroactive_justification_even_when_evidence_preexisted():
    r = record(
        "future-meaning",
        entailment=dep("entailment", te=T0, tj=T2, tu=T2),
    )

    result = tvc.evaluate_transition_closure(r, reconstruct)

    assert result.status is tvc.TransitionClosureStatus.FAILED
    assert result.reproduced_standing == "EVIDENCED"
    assert result.closure_boundary == "entailment"


def test_transition_closure_splits_evidence_justification_and_use_times():
    evidence_early_justification_late = record(
        "split-clocks-j",
        entailment=dep("entailment", te=T0, tj=T2, tu=T2),
    )
    evidence_and_justification_early_use_late = record(
        "split-clocks-u",
        entailment=dep("entailment", te=T0, tj=T0, tu=T2),
    )

    rj = tvc.evaluate_transition_closure(evidence_early_justification_late, reconstruct)
    ru = tvc.evaluate_transition_closure(evidence_and_justification_early_use_late, reconstruct)

    assert rj.status is tvc.TransitionClosureStatus.FAILED
    assert ru.status is tvc.TransitionClosureStatus.FAILED
    assert rj.closure_boundary == "entailment"
    assert ru.closure_boundary == "entailment"


def test_transition_closure_can_relax_actual_use_when_policy_does_not_require_it():
    r = record(
        "no-use-policy",
        entailment=dep("entailment", te=T0, tj=T0, tu=None),
    )

    strict = tvc.evaluate_transition_closure(r, reconstruct, require_incorporation=True)
    relaxed = tvc.evaluate_transition_closure(r, reconstruct, require_incorporation=False)

    assert strict.status is tvc.TransitionClosureStatus.FAILED
    assert relaxed.status is tvc.TransitionClosureStatus.CLOSED


def test_transition_closure_discovers_compositional_cut_sets():
    r = record("cut-sets")
    result = tvc.evaluate_transition_closure(r, reconstruct)

    cuts = {frozenset(item) for item in result.minimal_cut_sets}
    assert result.status is tvc.TransitionClosureStatus.CLOSED
    assert frozenset({"support_a", "support_b"}) in cuts
    assert frozenset({"provenance"}) in cuts
    assert frozenset({"entailment"}) in cuts
    assert frozenset({"contradictions"}) in cuts


def test_transition_closure_detects_recorded_necessity_topology_drift_without_label_change():
    baseline = tvc.evaluate_transition_closure(record("derive-baseline"), reconstruct)
    recorded_sets = tuple(frozenset(item) for item in baseline.minimal_cut_sets)

    r = replace(record("topology-drift"), recorded_minimal_sets=recorded_sets)
    # A new historically admissible independent support path appears. The final
    # standing remains INFERRED, but the necessity structure changes.
    deps = dict(r.dependencies)
    deps["support_c"] = dep("support_c")

    def reconstruct_with_c(admissible):
        support = bool({"support_a", "support_b", "support_c"} & admissible)
        if support and {"provenance", "entailment", "contradictions"}.issubset(admissible):
            return "INFERRED"
        if support and "provenance" in admissible:
            return "EVIDENCED"
        return "UNKNOWN"

    mutated = replace(r, dependencies=deps)
    result = tvc.evaluate_transition_closure(mutated, reconstruct_with_c)

    assert result.reproduced_standing == "INFERRED"
    assert result.status is tvc.TransitionClosureStatus.MISMATCH
    assert result.closure_boundary == "necessity_topology"


def test_transition_closure_necessity_fingerprint_changes_on_temporal_semantic_change():
    a = tvc.evaluate_transition_closure(record("fingerprint"), reconstruct)
    late = record(
        "fingerprint",
        entailment=dep("entailment", te=T0, tj=T2, tu=T2),
    )
    b = tvc.evaluate_transition_closure(late, reconstruct)

    assert a.necessity_fingerprint != b.necessity_fingerprint


def test_transition_closure_matches_equal_information_generic_control_for_current_semantics():
    cases = (
        record("equal-clean"),
        record("equal-late-j", entailment=dep("entailment", te=T0, tj=T2, tu=T2)),
        record("equal-late-use", entailment=dep("entailment", te=T0, tj=T0, tu=T2)),
        record("equal-bad-prov", provenance=dep("provenance", provenance=False)),
    )

    for r in cases:
        result = tvc.evaluate_transition_closure(r, reconstruct)
        baseline, admissible, cuts = generic_equal_information_control(r)
        assert result.reproduced_standing == baseline
        assert frozenset(result.admissible_dependencies) == admissible
        assert {frozenset(item) for item in result.minimal_cut_sets} == set(cuts)


def test_transition_closure_is_deterministic_across_dependency_orderings():
    base = record("deterministic")
    items = list(base.dependencies.items())
    reversed_record = replace(base, dependencies=dict(reversed(items)))

    a = tvc.evaluate_transition_closure(base, reconstruct)
    b = tvc.evaluate_transition_closure(reversed_record, reconstruct)

    assert a.status == b.status
    assert a.reproduced_standing == b.reproduced_standing
    assert a.minimal_cut_sets == b.minimal_cut_sets
    assert a.necessity_fingerprint == b.necessity_fingerprint


def test_transition_boundary_changes_exactly_at_justification_availability():
    before = record(
        "boundary-before",
        entailment=dep("entailment", te=T0, tj=T1 + timedelta(seconds=1), tu=T1 + timedelta(seconds=1)),
    )
    at = record(
        "boundary-at",
        entailment=dep("entailment", te=T0, tj=T1, tu=T1),
    )

    rb = tvc.evaluate_transition_closure(before, reconstruct)
    ra = tvc.evaluate_transition_closure(at, reconstruct)

    assert rb.status is tvc.TransitionClosureStatus.FAILED
    assert ra.status is tvc.TransitionClosureStatus.CLOSED
