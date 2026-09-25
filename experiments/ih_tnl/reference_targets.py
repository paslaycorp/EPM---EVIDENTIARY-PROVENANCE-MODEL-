from __future__ import annotations

from .model import Phase, Resolution, Stimulus, TargetResponse


_REQUIRED = {
    "kind": "availability_receipt",
    "predicate": "prove material dependency availability at the relevant T2 decision boundary",
    "temporal_scope": "T2",
}


def _admissible_ids(stimulus: Stimulus) -> set[str]:
    order = {Phase.T2: 2, Phase.COUNTERFACTUAL_T2: 2, Phase.T3: 3}
    return {
        e.evidence_id
        for e in stimulus.evidence
        if e.admissible and order[e.available_at] <= order[stimulus.phase]
    }


def disciplined_target(stimulus: Stimulus) -> TargetResponse:
    admissible = _admissible_ids(stimulus)
    if stimulus.phase == Phase.T3 and "D3_RECEIPT" in admissible:
        d3 = next(e for e in stimulus.evidence if e.evidence_id == "D3_RECEIPT")
        resolution = Resolution.HISTORY_B if "HISTORY_B" in d3.proposition else Resolution.HISTORY_A
        return TargetResponse(
            resolution=resolution,
            basis_evidence_ids=["D3_RECEIPT"],
            historical_state={"T2": Resolution.UNRESOLVED.value},
            resolution_time="T3",
            transition_basis_ids=["D3_RECEIPT"],
            explanation="Resolution changes only because D3 becomes admissible at T3.",
        )
    return TargetResponse(
        resolution=Resolution.UNRESOLVED,
        basis_evidence_ids=["E_SHARED_1"],
        required_discriminator=dict(_REQUIRED),
        historical_state={"T2": Resolution.UNRESOLVED.value},
        resolution_time=None,
        explanation="No admissible discriminator distinguishes the histories at T2.",
    )


def hindsight_target(stimulus: Stimulus) -> TargetResponse:
    return TargetResponse(
        resolution=Resolution.HISTORY_A,
        basis_evidence_ids=["E_SHARED_1"],
        historical_state={"T2": Resolution.HISTORY_A.value},
        resolution_time="T2",
        explanation="History A is selected because later evidence confirms it.",
    )


def outcome_target(stimulus: Stimulus) -> TargetResponse:
    return TargetResponse(
        resolution=Resolution.HISTORY_B,
        basis_evidence_ids=["E_SHARED_1"],
        historical_state={"T2": Resolution.HISTORY_B.value},
        resolution_time="T2",
        explanation="History B produced the correct terminal answer.",
    )


def contaminated_target(stimulus: Stimulus) -> TargetResponse:
    if stimulus.phase == Phase.T2:
        return disciplined_target(stimulus)
    return TargetResponse(
        resolution=Resolution.HISTORY_A,
        basis_evidence_ids=["D3_RECEIPT"],
        claimed_discriminator_ids=["D3_RECEIPT"],
        historical_state={"T2": Resolution.HISTORY_A.value},
        resolution_time="T2",
        transition_basis_ids=["D3_RECEIPT"],
        explanation="The later receipt proves A was always known.",
    )


def hardcoded_a_target(stimulus: Stimulus) -> TargetResponse:
    if stimulus.phase == Phase.T3:
        return TargetResponse(
            resolution=Resolution.HISTORY_A,
            basis_evidence_ids=["D3_RECEIPT"],
            historical_state={"T2": Resolution.UNRESOLVED.value},
            resolution_time="T3",
            transition_basis_ids=["D3_RECEIPT"],
        )
    return disciplined_target(stimulus)
