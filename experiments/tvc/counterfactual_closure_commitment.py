"""Prospective counterfactual closure commitment experiment.

At claim time, commit to the transition's counterfactual response surface rather
than reconstructing the entire closure object only after the fact.  The artifact
is intentionally experimental and remains outside the public EPM API.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from itertools import combinations
from typing import Callable, Iterable


Reconstruct = Callable[[frozenset[str]], str]


@dataclass(frozen=True)
class CounterfactualClosureCommitment:
    transition_id: str
    claim_time: datetime
    committed_at: datetime
    policy_id: str
    material_dependencies: tuple[str, ...]
    baseline_standing: str
    response_surface: tuple[tuple[tuple[str, ...], str], ...]
    surface_digest: str
    anchor_ref: str


@dataclass(frozen=True)
class CommitmentVerification:
    valid: bool
    reason: str
    reproduced_digest: str
    committed_digest: str


def _canonical_surface(
    material_dependencies: Iterable[str],
    reconstruct: Reconstruct,
) -> tuple[tuple[tuple[str, ...], str], ...]:
    """Enumerate the finite counterfactual response surface deterministically."""
    deps = tuple(sorted(set(material_dependencies)))
    full = frozenset(deps)
    rows: list[tuple[tuple[str, ...], str]] = []
    for size in range(0, len(deps) + 1):
        for removed in combinations(deps, size):
            rows.append((tuple(removed), reconstruct(full - frozenset(removed))))
    return tuple(rows)


def _digest(
    *,
    transition_id: str,
    claim_time: datetime,
    policy_id: str,
    dependencies: tuple[str, ...],
    surface: tuple[tuple[tuple[str, ...], str], ...],
) -> str:
    lines = [
        f"transition={transition_id}",
        f"claim_time={claim_time.isoformat()}",
        f"policy={policy_id}",
        "dependencies=" + ",".join(dependencies),
    ]
    lines.extend(f"remove={','.join(removed)}=>{standing}" for removed, standing in surface)
    return sha256("\n".join(lines).encode("utf-8")).hexdigest()


def issue_commitment(
    *,
    transition_id: str,
    claim_time: datetime,
    committed_at: datetime,
    policy_id: str,
    material_dependencies: Iterable[str],
    reconstruct: Reconstruct,
    anchor: Callable[[str], str],
) -> CounterfactualClosureCommitment:
    if committed_at > claim_time:
        raise ValueError("counterfactual closure commitment must not post-date claim time")
    dependencies = tuple(sorted(set(material_dependencies)))
    surface = _canonical_surface(dependencies, reconstruct)
    digest = _digest(
        transition_id=transition_id,
        claim_time=claim_time,
        policy_id=policy_id,
        dependencies=dependencies,
        surface=surface,
    )
    return CounterfactualClosureCommitment(
        transition_id=transition_id,
        claim_time=claim_time,
        committed_at=committed_at,
        policy_id=policy_id,
        material_dependencies=dependencies,
        baseline_standing=reconstruct(frozenset(dependencies)),
        response_surface=surface,
        surface_digest=digest,
        anchor_ref=anchor(digest),
    )


def verify_commitment(
    commitment: CounterfactualClosureCommitment,
    *,
    reconstruct: Reconstruct,
    verify_anchor: Callable[[str, str], bool],
) -> CommitmentVerification:
    if commitment.committed_at > commitment.claim_time:
        return CommitmentVerification(False, "LATE_COMMITMENT", "", commitment.surface_digest)
    if not verify_anchor(commitment.surface_digest, commitment.anchor_ref):
        return CommitmentVerification(False, "ANCHOR_MISMATCH", "", commitment.surface_digest)

    reproduced_surface = _canonical_surface(commitment.material_dependencies, reconstruct)
    reproduced = _digest(
        transition_id=commitment.transition_id,
        claim_time=commitment.claim_time,
        policy_id=commitment.policy_id,
        dependencies=commitment.material_dependencies,
        surface=reproduced_surface,
    )
    if reproduced != commitment.surface_digest:
        return CommitmentVerification(False, "COUNTERFACTUAL_SURFACE_MISMATCH", reproduced, commitment.surface_digest)
    return CommitmentVerification(True, "VERIFIED", reproduced, commitment.surface_digest)
