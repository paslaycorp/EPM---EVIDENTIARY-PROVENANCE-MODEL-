"""Temporal conservation of the Material Counterfactual Frontier.

Research-only TVC experiment. A frontier is allowed to change, but the change
must be explained by admissible, provenance-bearing mutation evidence. Merely
reaching the same epistemic endpoint is insufficient.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from hashlib import sha256
from typing import Iterable


class FrontierTransitionStatus(str, Enum):
    PRESERVED = "PRESERVED"
    REVISED = "REVISED"
    FAILED = "FAILED"
    UNRESOLVED = "UNRESOLVED"


@dataclass(frozen=True)
class FrontierSnapshot:
    observed_at: datetime
    baseline_standing: str
    frontier_digest: str
    authority_id: str
    policy_id: str


@dataclass(frozen=True)
class FrontierMutationEvidence:
    evidence_id: str
    available_at: datetime
    effective_at: datetime
    incorporated_at: datetime | None
    provenance_valid: bool
    authority_id: str
    policy_id: str
    permits_from_digest: str
    permits_to_digest: str

    def admissible_at(self, transition_time: datetime) -> bool:
        return (
            self.provenance_valid
            and self.available_at <= transition_time
            and self.effective_at <= transition_time
            and self.incorporated_at is not None
            and self.incorporated_at <= transition_time
        )


@dataclass(frozen=True)
class FrontierTransitionCertificate:
    status: FrontierTransitionStatus
    prior_digest: str
    current_digest: str
    evidence_ids: tuple[str, ...]
    reason: str
    certificate_digest: str


def _certificate_digest(
    prior: FrontierSnapshot,
    current: FrontierSnapshot,
    evidence_ids: tuple[str, ...],
    status: FrontierTransitionStatus,
    reason: str,
) -> str:
    rows = (
        f"prior={prior.frontier_digest}",
        f"current={current.frontier_digest}",
        f"prior_time={prior.observed_at.isoformat()}",
        f"current_time={current.observed_at.isoformat()}",
        f"prior_authority={prior.authority_id}",
        f"current_authority={current.authority_id}",
        f"prior_policy={prior.policy_id}",
        f"current_policy={current.policy_id}",
        "evidence=" + ",".join(evidence_ids),
        f"status={status.value}",
        f"reason={reason}",
    )
    return sha256("\n".join(rows).encode("utf-8")).hexdigest()


def evaluate_frontier_transition(
    prior: FrontierSnapshot,
    current: FrontierSnapshot,
    mutation_evidence: Iterable[FrontierMutationEvidence],
) -> FrontierTransitionCertificate:
    if current.observed_at < prior.observed_at:
        status, reason, ids = FrontierTransitionStatus.FAILED, "TEMPORAL_REVERSAL", ()
    elif current.frontier_digest == prior.frontier_digest:
        # Conservation needs no mutation evidence when the object did not mutate.
        status, reason, ids = FrontierTransitionStatus.PRESERVED, "FRONTIER_UNCHANGED", ()
    else:
        candidates = tuple(
            sorted(
                (
                    e for e in mutation_evidence
                    if e.admissible_at(current.observed_at)
                    and e.permits_from_digest == prior.frontier_digest
                    and e.permits_to_digest == current.frontier_digest
                ),
                key=lambda e: e.evidence_id,
            )
        )
        if not candidates:
            status, reason, ids = (
                FrontierTransitionStatus.UNRESOLVED,
                "FRONTIER_MUTATION_WITHOUT_ADMISSIBLE_EVIDENCE",
                (),
            )
        else:
            authority_match = tuple(
                e for e in candidates
                if e.authority_id == current.authority_id
                and e.policy_id == current.policy_id
            )
            if not authority_match:
                status, reason, ids = (
                    FrontierTransitionStatus.FAILED,
                    "FRONTIER_MUTATION_AUTHORITY_OR_POLICY_MISMATCH",
                    tuple(e.evidence_id for e in candidates),
                )
            else:
                status, reason, ids = (
                    FrontierTransitionStatus.REVISED,
                    "ADMISSIBLE_FRONTIER_REVISION",
                    tuple(e.evidence_id for e in authority_match),
                )

    digest = _certificate_digest(prior, current, ids, status, reason)
    return FrontierTransitionCertificate(
        status=status,
        prior_digest=prior.frontier_digest,
        current_digest=current.frontier_digest,
        evidence_ids=ids,
        reason=reason,
        certificate_digest=digest,
    )
