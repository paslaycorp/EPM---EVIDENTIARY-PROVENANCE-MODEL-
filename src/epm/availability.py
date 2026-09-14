"""Trusted evidence-availability ingestion contracts and reference connectors."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse

from .temporal import AvailabilityAttestation, EvidenceAvailability


class AvailabilityIngestionError(ValueError):
    """Raised when a connector cannot establish a trusted availability record."""


@dataclass(frozen=True)
class GitHubActionsRunReceipt:
    """Receipt for a GitHub Actions workflow run obtained from GitHub's REST API.

    `transport_verified` means the integration obtained the payload from
    `api.github.com` over an authenticated/validated HTTPS path. The timestamp
    is therefore useful only inside this explicitly bounded connector claim.
    """

    evidence_id: str
    repository: str
    run_id: int
    created_at: datetime
    observed_at: datetime
    api_url: str
    transport_verified: bool


def _aware(value: datetime) -> bool:
    return value.tzinfo is not None and value.utcoffset() is not None


def ingest_github_actions_run(receipt: GitHubActionsRunReceipt) -> EvidenceAvailability:
    """Create trusted availability from a validated GitHub Actions API receipt."""
    if not receipt.evidence_id.strip():
        raise AvailabilityIngestionError("evidence_id is required")
    if not receipt.repository.strip() or "/" not in receipt.repository:
        raise AvailabilityIngestionError("repository must be owner/name")
    if receipt.run_id <= 0:
        raise AvailabilityIngestionError("run_id must be positive")
    if not receipt.transport_verified:
        raise AvailabilityIngestionError("GitHub API transport was not verified")
    if not _aware(receipt.created_at) or not _aware(receipt.observed_at):
        raise AvailabilityIngestionError("created_at and observed_at must be timezone-aware")
    if receipt.observed_at < receipt.created_at:
        raise AvailabilityIngestionError("observed_at cannot precede created_at")

    parsed = urlparse(receipt.api_url)
    expected_path = f"/repos/{receipt.repository}/actions/runs/{receipt.run_id}"
    if parsed.scheme != "https" or parsed.hostname != "api.github.com":
        raise AvailabilityIngestionError("api_url must use https://api.github.com")
    if parsed.path.rstrip("/") != expected_path:
        raise AvailabilityIngestionError("api_url does not match repository/run identity")

    provenance_ref = f"https://api.github.com{expected_path}"
    attestation = AvailabilityAttestation(
        attestation_id=f"github-actions-run:{receipt.repository}:{receipt.run_id}",
        authority="GitHub Actions",
        method="GitHub REST workflow-run created_at over verified HTTPS transport",
        basis=(
            "GitHub server workflow-run metadata establishes when this CI evidence "
            "record existed within the bounded GitHub Actions integration."
        ),
        validated=True,
    )
    return EvidenceAvailability(
        evidence_id=receipt.evidence_id,
        available_at=receipt.created_at,
        observed_at=receipt.observed_at,
        source="github-actions-rest-api",
        provenance_ref=provenance_ref,
        attestation=attestation,
    )
