from __future__ import annotations

import importlib.util
import random
import sys
from datetime import datetime, timedelta, timezone
from itertools import combinations
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "temporal_transition_fidelity.py"
spec = importlib.util.spec_from_file_location("tvc_temporal_transition_fidelity_zero", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)

UTC = timezone.utc
BASE = datetime(2026, 9, 6, 20, 0, tzinfo=UTC)
CLAIM = BASE + timedelta(hours=1)

NAMES = ("support_a", "prov_a", "rule_a", "support_b", "prov_b", "rule_b", "contradictions")


def reconstruct(ids):
    a = {"support_a", "prov_a", "rule_a"}.issubset(ids)
    b = {"support_b", "prov_b", "rule_b"}.issubset(ids)
    if (a or b) and "contradictions" in ids:
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


def independently_admissible(dep, when):
    return (
        dep.active
        and dep.provenance_valid
        and dep.evidence_available_at <= when
        and dep.justification_available_at <= when
        and dep.bound_at is not None
        and dep.bound_at <= when
        and dep.used_at is not None
        and dep.used_at <= when
    )


def generic_cut_sets(ids):
    baseline = reconstruct(ids)
    ordered = tuple(sorted(ids))
    result = []
    for size in range(1, len(ordered) + 1):
        for raw in combinations(ordered, size):
            candidate = frozenset(raw)
            if any(existing.issubset(candidate) for existing in result):
                continue
            if reconstruct(ids - candidate) != baseline:
                result.append(candidate)
    return tuple(sorted(result, key=lambda x: (len(x), tuple(sorted(x)))))


def generic_verify(tr):
    before = frozenset(name for name, dep in tr.dependencies.items() if independently_admissible(dep, tr.before_time))
    at_claim = frozenset(name for name, dep in tr.dependencies.items() if independently_admissible(dep, tr.claim_time))
    return {
        "prior": reconstruct(before),
        "claim": reconstruct(at_claim),
        "before": before,
        "at_claim": at_claim,
        "new": at_claim - before,
        "path": select_path(at_claim),
        "cuts": generic_cut_sets(at_claim),
    }


def random_time(rng):
    return BASE + timedelta(minutes=rng.choice((-60, -1, 0, 30, 60, 61, 120)))


def make_case(rng, index):
    deps = {}
    for name in NAMES:
        te = random_time(rng)
        tj = random_time(rng)
        tb = None if rng.random() < 0.08 else random_time(rng)
        tu = None if rng.random() < 0.08 else random_time(rng)
        deps[name] = tvc.DependencyClock(
            dependency_id=name,
            evidence_available_at=te,
            justification_available_at=tj,
            bound_at=tb,
            used_at=tu,
            provenance_valid=rng.random() > 0.1,
            active=rng.random() > 0.1,
        )
    before = frozenset(name for name, d in deps.items() if independently_admissible(d, BASE))
    at_claim = frozenset(name for name, d in deps.items() if independently_admissible(d, CLAIM))
    prior = reconstruct(before)
    asserted = reconstruct(at_claim)
    return tvc.HistoricalTransition(
        transition_id=f"zero-{index}",
        proposition="X",
        before_time=BASE,
        claim_time=CLAIM,
        prior_standing=prior,
        asserted_standing=asserted,
        dependencies=deps,
        recorded_path=select_path(at_claim),
        recorded_cut_sets=generic_cut_sets(at_claim),
    )


def test_sephiroth_zero_2000_equal_information_randomized_states_match_generic_control():
    rng = random.Random(0x5E9F1A07)
    for index in range(2000):
        case = make_case(rng, index)
        candidate = tvc.evaluate_temporal_transition_fidelity(case, reconstruct, select_path)
        generic = generic_verify(case)
        assert candidate.reconstructed_prior_standing == generic["prior"]
        assert candidate.reconstructed_claim_standing == generic["claim"]
        assert frozenset(candidate.admissible_before) == generic["before"]
        assert frozenset(candidate.admissible_at_claim) == generic["at_claim"]
        assert frozenset(candidate.newly_usable) == generic["new"]
        assert frozenset(candidate.reconstructed_path) == generic["path"]
        assert {frozenset(x) for x in candidate.minimal_cut_sets} == set(generic["cuts"])
        assert candidate.status is tvc.FidelityStatus.CLOSED


def test_sephiroth_zero_deterministic_replay_250_times():
    rng = random.Random(20260914)
    case = make_case(rng, 9999)
    first = tvc.evaluate_temporal_transition_fidelity(case, reconstruct, select_path)
    for _ in range(250):
        assert tvc.evaluate_temporal_transition_fidelity(case, reconstruct, select_path) == first
