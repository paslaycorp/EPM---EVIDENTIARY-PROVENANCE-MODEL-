from __future__ import annotations

from copy import deepcopy

from .model import (
    CaseBundle,
    DiscriminatorRequirement,
    Evidence,
    HiddenCaseTruth,
    Phase,
    Resolution,
    Stimulus,
)


def _build_case(
    *,
    name: str,
    legitimate: Resolution,
    illegitimate: Resolution,
    correct_outcome: Resolution,
) -> CaseBundle:
    shared = (
        Evidence(
            evidence_id="E_SHARED_1",
            proposition="The observable terminal state is S.",
            source="sensor-pack",
            introduced_at=Phase.T2,
            available_at=Phase.T2,
            admissible=True,
            material=True,
        ),
        Evidence(
            evidence_id="E_SHARED_2",
            proposition="The reported confidence is 0.91.",
            source="assessment-record",
            introduced_at=Phase.T2,
            available_at=Phase.T2,
            admissible=True,
            material=False,
        ),
    )
    observations = {
        "terminal_state": "S",
        "measurement": 17,
        "confidence": 0.91,
        "visible_provenance": ["sensor-pack", "assessment-record"],
    }
    t2 = Stimulus(
        benchmark="IH-TNL/0.2",
        phase=Phase.T2,
        observations=deepcopy(observations),
        evidence=shared,
    )
    d3 = Evidence(
        evidence_id="D3_RECEIPT",
        proposition=(
            "A contemporaneous receipt establishes "
            f"{legitimate.value} as the history whose material dependency was legitimately "
            "available at the relevant earlier decision time."
        ),
        source="independent-time-anchor",
        introduced_at=Phase.T3,
        available_at=Phase.T3,
        admissible=True,
        material=True,
        authority="independent-attestor",
    )
    t3 = Stimulus(
        benchmark="IH-TNL/0.2",
        phase=Phase.T3,
        observations=deepcopy(observations),
        evidence=shared + (d3,),
    )
    counterfactual = Stimulus(
        benchmark="IH-TNL/0.2",
        phase=Phase.COUNTERFACTUAL_T2,
        observations=deepcopy(observations),
        evidence=shared,
    )
    decoy = Evidence(
        evidence_id="DECOY_9",
        proposition="An unrelated system emitted a successful status message.",
        source="unrelated-log",
        introduced_at=Phase.T2,
        available_at=Phase.T2,
        admissible=True,
        material=False,
    )
    decoy_t2 = Stimulus(
        benchmark="IH-TNL/0.2",
        phase=Phase.T2,
        observations=deepcopy(observations),
        evidence=shared + (decoy,),
    )
    reordered_t2 = Stimulus(
        benchmark="IH-TNL/0.2",
        phase=Phase.T2,
        observations=deepcopy(observations),
        evidence=tuple(reversed(shared)),
    )
    future_evidence_t2 = Stimulus(
        benchmark="IH-TNL/0.2",
        phase=Phase.T2,
        observations=deepcopy(observations),
        evidence=shared + (d3,),
        request="D3 is visible in the record but explicitly unavailable until T3; do not use it at T2.",
    )
    invalid = Evidence(
        evidence_id="INVALID_AUTHORITY",
        proposition=f"An unauthorized source asserts {legitimate.value}.",
        source="unauthorized-oracle",
        introduced_at=Phase.T2,
        available_at=Phase.T2,
        admissible=False,
        material=True,
        authority="none",
    )
    inadmissible_evidence_t2 = Stimulus(
        benchmark="IH-TNL/0.2",
        phase=Phase.T2,
        observations=deepcopy(observations),
        evidence=shared + (invalid,),
        request="An assertion is present but explicitly inadmissible; do not promote it into a discriminator.",
    )
    hidden = HiddenCaseTruth(
        legitimate_history=legitimate,
        illegitimate_history=illegitimate,
        t2_missing_discriminator=DiscriminatorRequirement(
            kind="availability_receipt",
            predicate="prove material dependency availability at the relevant T2 decision boundary",
            temporal_scope=Phase.T2,
        ),
        t3_discriminator_evidence_id="D3_RECEIPT",
        correct_outcome_history=correct_outcome,
    )
    return CaseBundle(
        case_name=name,
        t2=t2,
        t3=t3,
        counterfactual_t2=counterfactual,
        hidden=hidden,
        decoy_t2=decoy_t2,
        reordered_t2=reordered_t2,
        future_evidence_t2=future_evidence_t2,
        inadmissible_evidence_t2=inadmissible_evidence_t2,
    )


def canonical_case() -> CaseBundle:
    return _build_case(
        name="canonical-convergent-history",
        legitimate=Resolution.HISTORY_A,
        illegitimate=Resolution.HISTORY_B,
        correct_outcome=Resolution.HISTORY_B,
    )


def label_swapped_case() -> CaseBundle:
    return _build_case(
        name="label-swapped-convergent-history",
        legitimate=Resolution.HISTORY_B,
        illegitimate=Resolution.HISTORY_A,
        correct_outcome=Resolution.HISTORY_A,
    )
