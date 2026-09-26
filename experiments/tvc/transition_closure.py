"""Temporal Counterfactual Transition Closure experiment.

Experimental only.  This module is intentionally outside ``src/epm`` and the
public EPM API.  It tests whether a claimed epistemic transition was historically
admissible, whether its material dependency structure is reproducible, and
whether later information is being used to retroactively legitimate an earlier
transition.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from itertools import combinations
from typing import Callable, Iterable, Mapping


class TransitionClosureStatus(str, Enum):
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"
    MISMATCH = "MISMATCH"


@dataclass(frozen=True)
class TemporalDependency:
    dependency_id: str
    evidence_available_at: datetime
    justification_available_at: datetime
    incorporated_at: datetime | None
    provenance_valid: bool = True
    active: bool = True

    def admissible_at(self, claim_time: datetime, *, require_incorporation: bool = True) -> bool:
        if not self.active or not self.provenance_valid:
            return False
        if self.evidence_available_at > claim_time:
            return False
        if self.justification_available_at > claim_time:
            return False
        if require_incorporation:
            return self.incorporated_at is not None and self.incorporated_at <= claim_time
        return self.incorporated_at is None or self.incorporated_at <= claim_time


@dataclass(frozen=True)
class TransitionRecord:
    transition_id: str
    proposition: str
    prior_standing: str
    asserted_standing: str
    claim_time: datetime
    dependencies: Mapping[str, TemporalDependency]
    recorded_minimal_sets: tuple[frozenset[str], ...] = ()


@dataclass(frozen=True)
class TransitionClosureCertificate:
    transition_id: str
    status: TransitionClosureStatus
    prior_standing: str
    asserted_standing: str
    reproduced_standing: str
    admissible_dependencies: tuple[str, ...]
    minimal_cut_sets: tuple[tuple[str, ...], ...]
    recorded_minimal_sets: tuple[tuple[str, ...], ...]
    closure_boundary: str | None
    necessity_fingerprint: str


ReconstructStanding = Callable[[frozenset[str]], str]


def historically_admissible_dependencies(
    record: TransitionRecord,
    *,
    require_incorporation: bool = True,
) -> frozenset[str]:
    return frozenset(
        dependency_id
        for dependency_id, dependency in record.dependencies.items()
        if dependency.admissible_at(record.claim_time, require_incorporation=require_incorporation)
    )


def minimal_failure_cut_sets(
    admissible: frozenset[str],
    reconstruct: ReconstructStanding,
    *,
    baseline: str | None = None,
) -> tuple[frozenset[str], ...]:
    """Return inclusion-minimal dependency removals that change standing."""
    baseline_standing = baseline if baseline is not None else reconstruct(admissible)
    ordered = tuple(sorted(admissible))
    minimal: list[frozenset[str]] = []
    for size in range(1, len(ordered) + 1):
        for candidate_tuple in combinations(ordered, size):
            candidate = frozenset(candidate_tuple)
            if any(existing.issubset(candidate) for existing in minimal):
                continue
            if reconstruct(admissible - candidate) != baseline_standing:
                minimal.append(candidate)
    return tuple(sorted(minimal, key=lambda s: (len(s), tuple(sorted(s)))))


def necessity_fingerprint(
    *,
    record: TransitionRecord,
    admissible: Iterable[str],
    cut_sets: Iterable[frozenset[str]],
    reproduced_standing: str,
) -> str:
    """Hash transition semantics, not merely raw evidence identities."""
    canonical = [
        f"transition={record.transition_id}",
        f"prior={record.prior_standing}",
        f"asserted={record.asserted_standing}",
        f"reproduced={reproduced_standing}",
        f"claim_time={record.claim_time.isoformat()}",
        "admissible=" + ",".join(sorted(admissible)),
        "cuts=" + ";".join(
            ",".join(sorted(cut))
            for cut in sorted(cut_sets, key=lambda s: (len(s), tuple(sorted(s))))
        ),
    ]
    return sha256("\n".join(canonical).encode("utf-8")).hexdigest()


def evaluate_transition_closure(
    record: TransitionRecord,
    reconstruct: ReconstructStanding,
    *,
    require_incorporation: bool = True,
) -> TransitionClosureCertificate:
    admissible = historically_admissible_dependencies(
        record,
        require_incorporation=require_incorporation,
    )
    reproduced = reconstruct(admissible)
    cut_sets = minimal_failure_cut_sets(admissible, reconstruct, baseline=reproduced)

    recorded = tuple(
        sorted(
            (frozenset(item) for item in record.recorded_minimal_sets),
            key=lambda s: (len(s), tuple(sorted(s))),
        )
    )
    observed = tuple(sorted(cut_sets, key=lambda s: (len(s), tuple(sorted(s)))))

    boundary: str | None = None
    if reproduced != record.asserted_standing:
        status = TransitionClosureStatus.FAILED
        for dependency_id in sorted(record.dependencies):
            if dependency_id not in admissible:
                boundary = dependency_id
                break
    elif recorded and recorded != observed:
        status = TransitionClosureStatus.MISMATCH
        boundary = "necessity_topology"
    else:
        status = TransitionClosureStatus.CLOSED

    return TransitionClosureCertificate(
        transition_id=record.transition_id,
        status=status,
        prior_standing=record.prior_standing,
        asserted_standing=record.asserted_standing,
        reproduced_standing=reproduced,
        admissible_dependencies=tuple(sorted(admissible)),
        minimal_cut_sets=tuple(tuple(sorted(cut)) for cut in observed),
        recorded_minimal_sets=tuple(tuple(sorted(cut)) for cut in recorded),
        closure_boundary=boundary,
        necessity_fingerprint=necessity_fingerprint(
            record=record,
            admissible=admissible,
            cut_sets=cut_sets,
            reproduced_standing=reproduced,
        ),
    )
