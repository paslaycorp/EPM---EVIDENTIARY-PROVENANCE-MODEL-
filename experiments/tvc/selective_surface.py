"""Material counterfactual frontier for prospective TVC closure.

The full powerset response surface is exact but exponential. This experiment
binds only the inclusion-minimal interventions that change the baseline
standing, plus the baseline outcome.  It is a canonical failure frontier:
the smallest dependency removals at which the proposed transition ceases to
behave as originally committed.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from itertools import combinations
from typing import Callable, Iterable

Reconstruct = Callable[[frozenset[str]], str]


@dataclass(frozen=True)
class MaterialFrontier:
    dependencies: tuple[str, ...]
    baseline_standing: str
    minimal_failure_interventions: tuple[tuple[tuple[str, ...], str], ...]
    digest: str


def material_counterfactual_frontier(
    dependencies: Iterable[str], reconstruct: Reconstruct
) -> MaterialFrontier:
    deps = tuple(sorted(set(dependencies)))
    full = frozenset(deps)
    baseline = reconstruct(full)
    minimal: list[tuple[tuple[str, ...], str]] = []

    for size in range(1, len(deps) + 1):
        for raw in combinations(deps, size):
            removed = frozenset(raw)
            if any(frozenset(existing).issubset(removed) for existing, _ in minimal):
                continue
            outcome = reconstruct(full - removed)
            if outcome != baseline:
                minimal.append((tuple(raw), outcome))

    rows = tuple(sorted(minimal, key=lambda row: (len(row[0]), row[0], row[1])))
    canonical = [baseline, ",".join(deps)]
    canonical.extend(f"{','.join(removed)}=>{outcome}" for removed, outcome in rows)
    digest = sha256("\n".join(canonical).encode("utf-8")).hexdigest()
    return MaterialFrontier(deps, baseline, rows, digest)
