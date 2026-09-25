from __future__ import annotations

from datetime import datetime, timezone

from epm import (
    EPM_ENGINE_VERSION,
    AvailabilityAttestation,
    EvidenceAvailability,
    TemporalAvailability,
    assess_temporal_availability,
)

from .model import Phase, Resolution, Stimulus, TargetResponse


_PHASE_TIME = {
    Phase.T2: datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
    Phase.COUNTERFACTUAL_T2: datetime(2026, 1, 2, 0, 0, tzinfo=timezone.utc),
    Phase.T3: datetime(2026, 1, 3, 0, 0, tzinfo=timezone.utc),
}

_REQUIRED = {
    "kind": "availability_receipt",
    "predicate": "prove material dependency availability at the relevant T2 decision boundary",
    "temporal_scope": "T2",
}


def _availability_record(stimulus_evidence):
    available_at = _PHASE_TIME[stimulus_evidence.available_at]
    return EvidenceAvailability(
        evidence_id=stimulus_evidence.evidence_id,
        available_at=available_at,
        observed_at=available_at,
        source=stimulus_evidence.source,
        provenance_ref=f"ih-tnl:{stimulus_evidence.evidence_id}",
        attestation=AvailabilityAttestation(
            attestation_id=f"att:{stimulus_evidence.evidence_id}",
            authority=stimulus_evidence.authority,
            method="ih-tnl-public-stimulus",
            basis="benchmark-declared availability boundary",
            validated=stimulus_evidence.admissible,
        ),
    )


def observe_epm_availability(stimulus: Stimulus) -> dict[str, dict[str, object]]:
    state_at = _PHASE_TIME[stimulus.phase]
    observations: dict[str, dict[str, object]] = {}
    for item in stimulus.evidence:
        result = assess_temporal_availability(
            evidence_id=item.evidence_id,
            state_at=state_at,
            availability=_availability_record(item),
        )
        observations[item.evidence_id] = {
            "status": result.status.value,
            "trusted": result.trusted,
            "reason_code": result.reason_code,
            "admissible": item.admissible,
            "material": item.material,
        }
    return observations


def epm_temporal_target(stimulus: Stimulus) -> TargetResponse:
    """Benchmark adapter backed by EPM's public temporal-availability primitive.

    This demonstrates adapter-level composition. It is not, by itself, a claim
    that EPM Core natively implements the complete IH-TNL target contract.
    """
    observed = observe_epm_availability(stimulus)
    usable = {
        evidence_id
        for evidence_id, result in observed.items()
        if result["status"] == TemporalAvailability.AVAILABLE.value
        and result["trusted"] is True
        and result["admissible"] is True
    }

    if "D3_RECEIPT" in usable:
        receipt = next(
            item for item in stimulus.evidence if item.evidence_id == "D3_RECEIPT"
        )
        if Resolution.HISTORY_A.value in receipt.proposition:
            resolution = Resolution.HISTORY_A
        elif Resolution.HISTORY_B.value in receipt.proposition:
            resolution = Resolution.HISTORY_B
        else:
            resolution = Resolution.UNRESOLVED

        if resolution is not Resolution.UNRESOLVED:
            return TargetResponse(
                resolution=resolution,
                basis_evidence_ids=["D3_RECEIPT"],
                historical_state={"T2": Resolution.UNRESOLVED.value},
                resolution_time="T3",
                transition_basis_ids=["D3_RECEIPT"],
                explanation=(
                    f"{EPM_ENGINE_VERSION}: EPM temporal availability marks the "
                    "independent receipt usable only at T3."
                ),
            )

    basis = ["E_SHARED_1"] if "E_SHARED_1" in usable else []
    return TargetResponse(
        resolution=Resolution.UNRESOLVED,
        basis_evidence_ids=basis,
        required_discriminator=dict(_REQUIRED),
        historical_state={"T2": Resolution.UNRESOLVED.value},
        resolution_time=None,
        explanation=(
            f"{EPM_ENGINE_VERSION}: no admissibly available discriminator "
            "establishes either history at this boundary."
        ),
    )


def adapter_identity() -> dict[str, str]:
    return {
        "adapter": "ih-tnl.epm-temporal-adapter/0.1",
        "epm_engine_version": EPM_ENGINE_VERSION,
        "claim_boundary": "adapter-mediated temporal availability composition",
    }
