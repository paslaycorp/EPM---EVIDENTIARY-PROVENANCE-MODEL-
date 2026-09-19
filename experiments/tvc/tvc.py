"""Temporal Verification Closure (TVC) v0.1 experimental verifier.

This module is deliberately outside the EPM runtime package.  It consumes an
EPM-style epistemic snapshot and tests whether an asserted standing can be
reproduced from obligations that remain admissible at the claimed historical
boundary.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Mapping


class ObligationStatus(str, Enum):
    SATISFIED = "SATISFIED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"


class ClosureStatus(str, Enum):
    CLOSED = "CLOSED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class Obligation:
    obligation_id: str
    description: str
    required_for: str


@dataclass(frozen=True)
class HistoricalCondition:
    obligation_id: str
    status: ObligationStatus
    available_at_claim_time: bool
    provenance_valid: bool
    reason: str = ""


@dataclass(frozen=True)
class EpistemicSnapshot:
    state_id: str
    proposition: str
    asserted_standing: str
    claimed_at: str
    conditions: Mapping[str, HistoricalCondition]


@dataclass(frozen=True)
class ClosureResult:
    status: ClosureStatus
    asserted_standing: str
    reproduced_standing: str
    closure_boundary: str | None
    obligations: tuple[Obligation, ...]
    failed: tuple[str, ...]
    unresolved: tuple[str, ...]


ObligationPolicy = Mapping[str, tuple[Obligation, ...]]
Reverify = Callable[[EpistemicSnapshot, frozenset[str]], str]


def derive_obligations(snapshot: EpistemicSnapshot, policy: ObligationPolicy) -> tuple[Obligation, ...]:
    """Derive obligations from the asserted epistemic standing itself."""
    return tuple(policy.get(snapshot.asserted_standing, ()))


def validate_historical_obligations(
    snapshot: EpistemicSnapshot,
    obligations: tuple[Obligation, ...],
) -> tuple[tuple[str, ...], tuple[str, ...], frozenset[str], str | None]:
    """Validate status, temporal availability, and provenance for each obligation."""
    failed: list[str] = []
    unresolved: list[str] = []
    admissible: set[str] = set()
    boundary: str | None = None

    for obligation in obligations:
        condition = snapshot.conditions.get(obligation.obligation_id)
        if condition is None:
            unresolved.append(obligation.obligation_id)
            boundary = boundary or obligation.obligation_id
            continue
        if not condition.available_at_claim_time or not condition.provenance_valid:
            failed.append(obligation.obligation_id)
            boundary = boundary or obligation.obligation_id
            continue
        if condition.status is ObligationStatus.FAILED:
            failed.append(obligation.obligation_id)
            boundary = boundary or obligation.obligation_id
            continue
        if condition.status is ObligationStatus.UNRESOLVED:
            unresolved.append(obligation.obligation_id)
            boundary = boundary or obligation.obligation_id
            continue
        admissible.add(obligation.obligation_id)

    return tuple(failed), tuple(unresolved), frozenset(admissible), boundary


def evaluate_closure(
    snapshot: EpistemicSnapshot,
    policy: ObligationPolicy,
    reverify: Reverify,
) -> ClosureResult:
    """Perform conclusion-conditioned temporal closure.

    Sequence:
      asserted standing -> derived obligations -> historical validation ->
      admissible justification -> forward re-verification -> state comparison.
    """
    obligations = derive_obligations(snapshot, policy)
    failed, unresolved, admissible, boundary = validate_historical_obligations(snapshot, obligations)
    reproduced = reverify(snapshot, admissible)

    if failed:
        status = ClosureStatus.FAILED
    elif unresolved:
        status = ClosureStatus.UNRESOLVED
    elif reproduced != snapshot.asserted_standing:
        status = ClosureStatus.DEGRADED
    else:
        status = ClosureStatus.CLOSED

    return ClosureResult(
        status=status,
        asserted_standing=snapshot.asserted_standing,
        reproduced_standing=reproduced,
        closure_boundary=boundary,
        obligations=obligations,
        failed=failed,
        unresolved=unresolved,
    )


DEFAULT_POLICY: ObligationPolicy = {
    "EVIDENCED": (
        Obligation("support", "material supporting evidence is admissible", "EVIDENCED"),
        Obligation("provenance", "material support has valid provenance", "EVIDENCED"),
    ),
    "INFERRED": (
        Obligation("support", "material supporting evidence is admissible", "INFERRED"),
        Obligation("provenance", "material support has valid provenance", "INFERRED"),
        Obligation("entailment", "inferential relation is established", "INFERRED"),
        Obligation("contradictions", "material contradictions are dispositioned", "INFERRED"),
    ),
}
