"""Material counterfactual boundary analysis for prospective TVC closure.

A minimal failure frontier is a compact commitment only when failure relative to
the baseline is monotone under additional dependency removal. This module
therefore separates two operations:

1. analyze the complete finite intervention lattice and expose any recovery
   crossings where additional removal restores the baseline standing; and
2. emit the compressed MaterialFrontier only when that audit proves the
   baseline-failure relation is monotone.

The commitment can remain substantially smaller than the powerset even though
issuance audits the powerset before compression. This prevents a recovery island
from being hidden behind an inclusion-minimal failure.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
from typing import Callable, Iterable

Reconstruct = Callable[[frozenset[str]], str]


@dataclass(frozen=True)
class RecoveryCrossing:
    failed_intervention: tuple[str, ...]
    failed_outcome: str
    recovered_intervention: tuple[str, ...]
    recovered_outcome: str


@dataclass(frozen=True)
class CounterfactualBoundaryAudit:
    dependencies: tuple[str, ...]
    baseline_standing: str
    minimal_failure_interventions: tuple[tuple[tuple[str, ...], str], ...]
    recovery_crossings: tuple[RecoveryCrossing, ...]
    baseline_failure_monotone: bool
    digest: str


@dataclass(frozen=True)
class MaterialFrontier:
    dependencies: tuple[str, ...]
    baseline_standing: str
    minimal_failure_interventions: tuple[tuple[tuple[str, ...], str], ...]
    digest: str


class NonMonotonicFrontierError(ValueError):
    """Raised when a compressed frontier would hide baseline recovery."""

    def __init__(self, audit: CounterfactualBoundaryAudit):
        self.audit = audit
        super().__init__("NON_MONOTONIC_COUNTERFACTUAL_RECOVERY")


def _surface(
    dependencies: tuple[str, ...], reconstruct: Reconstruct
) -> tuple[tuple[tuple[str, ...], str], ...]:
    full = frozenset(dependencies)
    rows: list[tuple[tuple[str, ...], str]] = []
    for size in range(len(dependencies) + 1):
        for removed in combinations(dependencies, size):
            rows.append((tuple(removed), reconstruct(full - frozenset(removed))))
    return tuple(rows)


def _minimal_failures(
    rows: tuple[tuple[tuple[str, ...], str], ...], baseline: str
) -> tuple[tuple[tuple[str, ...], str], ...]:
    minimal: list[tuple[tuple[str, ...], str]] = []
    for removed, outcome in rows:
        if not removed or outcome == baseline:
            continue
        removed_set = frozenset(removed)
        if any(frozenset(existing).issubset(removed_set) for existing, _ in minimal):
            continue
        minimal.append((removed, outcome))
    return tuple(sorted(minimal, key=lambda row: (len(row[0]), row[0], row[1])))


def _recovery_crossings(
    rows: tuple[tuple[tuple[str, ...], str], ...], baseline: str
) -> tuple[RecoveryCrossing, ...]:
    by_removed = {frozenset(removed): outcome for removed, outcome in rows}
    crossings: list[RecoveryCrossing] = []
    for removed, outcome in rows:
        removed_set = frozenset(removed)
        if not removed_set or outcome != baseline:
            continue
        for restored_after_removing in sorted(removed_set):
            predecessor = removed_set - {restored_after_removing}
            predecessor_outcome = by_removed[predecessor]
            if predecessor_outcome == baseline:
                continue
            crossings.append(
                RecoveryCrossing(
                    failed_intervention=tuple(sorted(predecessor)),
                    failed_outcome=predecessor_outcome,
                    recovered_intervention=tuple(sorted(removed_set)),
                    recovered_outcome=outcome,
                )
            )
    return tuple(
        sorted(
            crossings,
            key=lambda row: (
                len(row.recovered_intervention),
                row.recovered_intervention,
                row.failed_intervention,
                row.failed_outcome,
                row.recovered_outcome,
            ),
        )
    )


def analyze_counterfactual_boundary(
    dependencies: Iterable[str], reconstruct: Reconstruct
) -> CounterfactualBoundaryAudit:
    deps = tuple(sorted(set(dependencies)))
    rows = _surface(deps, reconstruct)
    baseline = rows[0][1]
    minimal = _minimal_failures(rows, baseline)
    recoveries = _recovery_crossings(rows, baseline)

    canonical = [f"baseline={baseline}", "dependencies=" + ",".join(deps)]
    canonical.extend(f"failure:{','.join(removed)}=>{outcome}" for removed, outcome in minimal)
    canonical.extend(
        "recovery:"
        + ",".join(row.failed_intervention)
        + "=>"
        + row.failed_outcome
        + "|"
        + ",".join(row.recovered_intervention)
        + "=>"
        + row.recovered_outcome
        for row in recoveries
    )
    digest = sha256("\n".join(canonical).encode("utf-8")).hexdigest()
    return CounterfactualBoundaryAudit(
        dependencies=deps,
        baseline_standing=baseline,
        minimal_failure_interventions=minimal,
        recovery_crossings=recoveries,
        baseline_failure_monotone=not recoveries,
        digest=digest,
    )


def material_counterfactual_frontier(
    dependencies: Iterable[str], reconstruct: Reconstruct
) -> MaterialFrontier:
    """Return a compact frontier only after proving compression is sound.

    A recovery crossing means that a superset of a failed intervention restores
    the original baseline. In that case, the minimal failure antichain is not a
    complete representation of the counterfactual boundary, so issuance fails
    closed rather than silently discarding the recovery topology.
    """
    audit = analyze_counterfactual_boundary(dependencies, reconstruct)
    if not audit.baseline_failure_monotone:
        raise NonMonotonicFrontierError(audit)

    canonical = [audit.baseline_standing, ",".join(audit.dependencies)]
    canonical.extend(
        f"{','.join(removed)}=>{outcome}"
        for removed, outcome in audit.minimal_failure_interventions
    )
    digest = sha256("\n".join(canonical).encode("utf-8")).hexdigest()
    return MaterialFrontier(
        audit.dependencies,
        audit.baseline_standing,
        audit.minimal_failure_interventions,
        digest,
    )
