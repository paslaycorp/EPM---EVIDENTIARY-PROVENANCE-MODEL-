from datetime import UTC, datetime

from epm import (
    AvailabilityAttestation,
    EvidenceAvailability,
    assess_temporal_availability,
)


def run_example():
    state_at = datetime(2026, 9, 14, 15, 0, tzinfo=UTC)
    available_at = datetime(2026, 9, 14, 18, 0, tzinfo=UTC)

    availability = EvidenceAvailability(
        evidence_id="evidence-1",
        available_at=available_at,
        observed_at=available_at,
        source="trusted-receipt",
        provenance_ref="receipt:1",
        attestation=AvailabilityAttestation(
            "attestation-1",
            "receipt-authority",
            "authenticated-receipt",
            "server-observed receipt",
            True,
        ),
    )

    return assess_temporal_availability(
        evidence_id="evidence-1",
        state_at=state_at,
        availability=availability,
    )


if __name__ == "__main__":
    result = run_example()
    print(result.status.value)
    print(result.reason_code)
