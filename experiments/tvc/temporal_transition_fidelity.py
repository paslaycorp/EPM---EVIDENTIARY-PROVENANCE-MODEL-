"""Temporal transition fidelity experiment for TVC.

Experimental only.  The object under test is not merely an endpoint standing but
an historically claimed transition and the justification topology that made the
transition possible at the time it was asserted.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from itertools import combinations
from typing import Callable, Mapping


class FidelityStatus(str, Enum):
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    PATH_MISMATCH = "PATH_MISMATCH"
    TOPOLOGY_DRIFT = "TOPOLOGY_DRIFT"


@dataclass(frozen=True)
class DependencyClock:
    dependency_id: str
    evidence_available_at: datetime
    justification_available_at: datetime
    bound_at: datetime | None
    used_at: datetime | None
    provenance_valid: bool = True
    active: bool = True

    def admissible_at(self, when: datetime) -> bool:
        return (
            self.active
            and self.provenance_valid
            and self.evidence_available_at <= when
            and self.justification_available_at <= when
            and self.bound_at is not None
            and self.bound_at <= when
            and self.used_at is not None
            and self.used_at <= when
        )


@dataclass(frozen=True)
class HistoricalTransition:
    transition_id: str
    proposition: str
    before_time: datetime
    claim_time: datetime
    prior_standing: str
    asserted_standing: str
    dependencies: Mapping[str, DependencyClock]
    recorded_path: frozenset[str] = frozenset()
    recorded_cut_sets: tuple[frozenset[str], ...] = ()


@dataclass(frozen=True)
class FidelityCertificate:
    transition_id: str
    status: FidelityStatus
    reconstructed_prior_standing: str
    reconstructed_claim_standing: str
    admissible_before: tuple[str, ...]
    admissible_at_claim: tuple[str, ...]
    newly_usable: tuple[str, ...]
    minimal_cut_sets: tuple[tuple[str, ...], ...]
    recorded_cut_sets: tuple[tuple[str, ...], ...]
    reconstructed_path: tuple[str, ...]
    recorded_path: tuple[str, ...]
    closure_boundary: str | None
    transition_fingerprint: str


Reconstruct = Callable[[frozenset[str]], str]
SelectPath = Callable[[frozenset[str]], frozenset[str]]


def admissible_ids(transition: HistoricalTransition, when: datetime) -> frozenset[str]:
    return frozenset(
        dependency_id
        for dependency_id, dep in transition.dependencies.items()
        if dep.admissible_at(when)
    )


def minimal_failure_cut_sets(
    admissible: frozenset[str], reconstruct: Reconstruct
) -> tuple[frozenset[str], ...]:
    baseline = reconstruct(admissible)
    ordered = tuple(sorted(admissible))
    minimal: list[frozenset[str]] = []
    for size in range(1, len(ordered) + 1):
        for raw in combinations(ordered, size):
            candidate = frozenset(raw)
            if any(existing.issubset(candidate) for existing in minimal):
                continue
            if reconstruct(admissible - candidate) != baseline:
                minimal.append(candidate)
    return tuple(sorted(minimal, key=lambda x: (len(x), tuple(sorted(x)))))


def evaluate_temporal_transition_fidelity(
    transition: HistoricalTransition,
    reconstruct: Reconstruct,
    select_path: SelectPath,
) -> FidelityCertificate:
    before = admissible_ids(transition, transition.before_time)
    at_claim = admissible_ids(transition, transition.claim_time)
    prior = reconstruct(before)
    reproduced = reconstruct(at_claim)
    newly_usable = at_claim - before
    cut_sets = minimal_failure_cut_sets(at_claim, reconstruct)
    path = select_path(at_claim)

    boundary: str | None = None
    if prior != transition.prior_standing:
        status = FidelityStatus.FAILED
        boundary = "prior_state"
    elif reproduced != transition.asserted_standing:
        status = FidelityStatus.FAILED
        boundary = next(
            (
                dependency_id
                for dependency_id in sorted(transition.dependencies)
                if dependency_id not in at_claim
            ),
            "claim_state",
        )
    elif transition.recorded_path and path != transition.recorded_path:
        status = FidelityStatus.PATH_MISMATCH
        boundary = "justification_path"
    else:
        recorded_cuts = tuple(
            sorted(
                transition.recorded_cut_sets,
                key=lambda x: (len(x), tuple(sorted(x))),
            )
        )
        if recorded_cuts and cut_sets != recorded_cuts:
            status = FidelityStatus.TOPOLOGY_DRIFT
            boundary = "necessity_topology"
        else:
            status = FidelityStatus.CLOSED

    canonical = "\n".join(
        [
            transition.transition_id,
            transition.prior_standing,
            transition.asserted_standing,
            transition.before_time.isoformat(),
            transition.claim_time.isoformat(),
            ",".join(sorted(before)),
            ",".join(sorted(at_claim)),
            ",".join(sorted(newly_usable)),
            ",".join(sorted(path)),
            ";".join(",".join(sorted(cut)) for cut in cut_sets),
        ]
    )
    fingerprint = sha256(canonical.encode("utf-8")).hexdigest()

    return FidelityCertificate(
        transition_id=transition.transition_id,
        status=status,
        reconstructed_prior_standing=prior,
        reconstructed_claim_standing=reproduced,
        admissible_before=tuple(sorted(before)),
        admissible_at_claim=tuple(sorted(at_claim)),
        newly_usable=tuple(sorted(newly_usable)),
        minimal_cut_sets=tuple(tuple(sorted(cut)) for cut in cut_sets),
        recorded_cut_sets=tuple(
            tuple(sorted(cut))
            for cut in sorted(
                transition.recorded_cut_sets,
                key=lambda x: (len(x), tuple(sorted(x))),
            )
        ),
        reconstructed_path=tuple(sorted(path)),
        recorded_path=tuple(sorted(transition.recorded_path)),
        closure_boundary=boundary,
        transition_fingerprint=fingerprint,
    )
