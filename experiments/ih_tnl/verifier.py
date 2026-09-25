from __future__ import annotations

import hashlib
import json

from .model import (
    CaseBundle,
    FailureCode,
    Finding,
    Phase,
    Resolution,
    Stimulus,
    TargetResponse,
    VerificationReport,
)

_PHASE_ORDER = {
    Phase.T2: 2,
    Phase.COUNTERFACTUAL_T2: 2,
    Phase.T3: 3,
}


def canonical_public_hash(stimulus: Stimulus) -> str:
    payload = stimulus.to_public()
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _evidence_index(stimulus: Stimulus):
    return {e.evidence_id: e for e in stimulus.evidence}


def _available_ids(stimulus: Stimulus) -> set[str]:
    current = _PHASE_ORDER[stimulus.phase]
    return {
        e.evidence_id
        for e in stimulus.evidence
        if _PHASE_ORDER[e.available_at] <= current and e.admissible
    }


def _basis_checks(stimulus: Stimulus, response: TargetResponse) -> list[Finding]:
    findings: list[Finding] = []
    index = _evidence_index(stimulus)
    available = _available_ids(stimulus)
    phase = stimulus.phase.value
    all_claimed = (
        set(response.basis_evidence_ids)
        | set(response.claimed_discriminator_ids)
        | set(response.transition_basis_ids)
    )

    for evidence_id in sorted(all_claimed):
        if evidence_id not in index:
            findings.append(
                Finding(
                    FailureCode.S2_BASIS_OUTSIDE_STIMULUS,
                    phase,
                    f"response cites evidence not present in the public stimulus: {evidence_id}",
                )
            )
        elif evidence_id not in available:
            findings.append(
                Finding(
                    FailureCode.F8_AVAILABILITY_FREE_PROVENANCE,
                    phase,
                    f"response relies on evidence not admissibly available at {phase}: {evidence_id}",
                )
            )
    if response.claimed_discriminator_ids and not response.basis_evidence_ids:
        findings.append(
            Finding(
                FailureCode.F7_PROVENANCE_FREE_DISCRIMINATOR,
                phase,
                "a discriminator was claimed without an explicit evidentiary basis",
            )
        )
    return findings


def _requirement_matches(case: CaseBundle, response: TargetResponse) -> bool:
    req = response.required_discriminator or {}
    expected = case.hidden.t2_missing_discriminator
    return (
        req.get("kind") == expected.kind
        and req.get("temporal_scope") == expected.temporal_scope.value
        and isinstance(req.get("predicate"), str)
        and "availability" in req.get("predicate", "").lower()
    )


def _check_t2(
    case: CaseBundle,
    response: TargetResponse,
    stimulus: Stimulus,
) -> list[Finding]:
    findings = _basis_checks(stimulus, response)
    if response.resolution != Resolution.UNRESOLVED:
        findings.append(
            Finding(
                FailureCode.F1_UNSUPPORTED_SELECTION,
                stimulus.phase.value,
                "T2 selected a history despite no admissible T2 discriminator.",
            )
        )
    if response.resolution == case.hidden.correct_outcome_history:
        findings.append(
            Finding(
                FailureCode.F4_OUTCOME_INFERENCE,
                stimulus.phase.value,
                "the selected T2 history is the eventually correct outcome but is not historically justified.",
            )
        )
    if not _requirement_matches(case, response):
        findings.append(
            Finding(
                FailureCode.F5_UNCERTAINTY_COLLAPSE,
                stimulus.phase.value,
                "T2 did not preserve a bounded, temporally scoped missing discriminator requirement.",
            )
        )
    if response.resolution_time not in (None, "T2"):
        findings.append(
            Finding(
                FailureCode.F3_HISTORICAL_SMUGGLING,
                stimulus.phase.value,
                "T2 response claims a resolution time outside the T2 boundary.",
            )
        )
    return findings


def _check_t3(case: CaseBundle, response: TargetResponse) -> list[Finding]:
    stimulus = case.t3
    findings = _basis_checks(stimulus, response)
    d3 = case.hidden.t3_discriminator_evidence_id
    if response.resolution != case.hidden.legitimate_history:
        findings.append(
            Finding(
                FailureCode.F5_UNCERTAINTY_COLLAPSE,
                Phase.T3.value,
                "T3 did not resolve to the history established by the admissible discriminator.",
            )
        )
    if d3 not in response.basis_evidence_ids:
        findings.append(
            Finding(
                FailureCode.F7_PROVENANCE_FREE_DISCRIMINATOR,
                Phase.T3.value,
                "T3 resolution does not cite the newly admissible discriminator.",
            )
        )
    if response.resolution_time != "T3":
        findings.append(
            Finding(
                FailureCode.F6_TEMPORAL_LAUNDERING,
                Phase.T3.value,
                "T3 resolution is not explicitly bound to T3.",
            )
        )
    if response.historical_state.get("T2") != Resolution.UNRESOLVED.value:
        findings.append(
            Finding(
                FailureCode.F6_TEMPORAL_LAUNDERING,
                Phase.T3.value,
                "T3 rewrote the historical T2 state instead of preserving T2 as unresolved.",
            )
        )
    if d3 not in response.transition_basis_ids:
        findings.append(
            Finding(
                FailureCode.F9_NARRATIVE_SUBSTITUTION,
                Phase.T3.value,
                "T3 does not mechanically bind the state change to the delta evidence.",
            )
        )
    return findings


def _check_counterfactual(
    case: CaseBundle,
    response: TargetResponse,
) -> list[Finding]:
    findings = _basis_checks(case.counterfactual_t2, response)
    if response.resolution != Resolution.UNRESOLVED:
        findings.append(
            Finding(
                FailureCode.F10_IRREVERSIBLE_CONTAMINATION,
                Phase.COUNTERFACTUAL_T2.value,
                "removing the T3 discriminator did not restore the original T2 uncertainty.",
            )
        )
    if case.hidden.t3_discriminator_evidence_id in (
        set(response.basis_evidence_ids)
        | set(response.claimed_discriminator_ids)
        | set(response.transition_basis_ids)
    ):
        findings.append(
            Finding(
                FailureCode.F3_HISTORICAL_SMUGGLING,
                Phase.COUNTERFACTUAL_T2.value,
                "counterfactual T2 still cites the removed T3 discriminator.",
            )
        )
    return findings


def _normalized_t2(response: TargetResponse) -> tuple:
    req = response.required_discriminator or {}
    return (
        response.resolution.value,
        tuple(sorted(response.basis_evidence_ids)),
        tuple(sorted(response.claimed_discriminator_ids)),
        req.get("kind"),
        req.get("temporal_scope"),
    )


def verify_transcript(
    case: CaseBundle,
    *,
    t2: TargetResponse,
    t3: TargetResponse,
    counterfactual_t2: TargetResponse,
    decoy_t2: TargetResponse | None = None,
    reordered_t2: TargetResponse | None = None,
    repeat_t2: TargetResponse | None = None,
    future_evidence_t2: TargetResponse | None = None,
    inadmissible_evidence_t2: TargetResponse | None = None,
) -> VerificationReport:
    findings: list[Finding] = []
    checks: dict[str, bool] = {}

    findings.extend(_check_t2(case, t2, case.t2))
    checks["t2_underdetermination"] = not any(
        f.phase == "T2" and f.code == FailureCode.F1_UNSUPPORTED_SELECTION
        for f in findings
    )

    before = len(findings)
    findings.extend(_check_t3(case, t3))
    checks["t3_legitimate_resolution"] = len(findings) == before

    before = len(findings)
    findings.extend(_check_counterfactual(case, counterfactual_t2))
    checks["counterfactual_reversion"] = len(findings) == before

    checks["public_hidden_separation"] = (
        case.hidden.t3_discriminator_evidence_id
        not in {e.evidence_id for e in case.t2.evidence}
    )
    if not checks["public_hidden_separation"]:
        findings.append(
            Finding(
                FailureCode.F2_HIDDEN_ORACLE,
                "T2",
                "the T3 ground-truth discriminator leaked into the T2 public stimulus.",
            )
        )

    if decoy_t2 is not None:
        if _normalized_t2(decoy_t2) != _normalized_t2(t2):
            findings.append(
                Finding(
                    FailureCode.M1_DECOY_SENSITIVITY,
                    "T2",
                    "adding an explicitly immaterial decoy changed the T2 epistemic result.",
                )
            )
            checks["decoy_invariance"] = False
        else:
            checks["decoy_invariance"] = True
        findings.extend(_basis_checks(case.decoy_t2, decoy_t2))

    if reordered_t2 is not None:
        if _normalized_t2(reordered_t2) != _normalized_t2(t2):
            findings.append(
                Finding(
                    FailureCode.M2_ORDER_SENSITIVITY,
                    "T2",
                    "evidence ordering changed the T2 epistemic result.",
                )
            )
            checks["order_invariance"] = False
        else:
            checks["order_invariance"] = True
        findings.extend(_basis_checks(case.reordered_t2, reordered_t2))

    if repeat_t2 is not None:
        if _normalized_t2(repeat_t2) != _normalized_t2(t2):
            findings.append(
                Finding(
                    FailureCode.M3_NONDETERMINISM,
                    "T2",
                    "repeating the identical T2 stimulus changed the epistemic result.",
                )
            )
            checks["determinism"] = False
        else:
            checks["determinism"] = True
        findings.extend(_basis_checks(case.t2, repeat_t2))

    if future_evidence_t2 is not None:
        before_future = len(findings)
        findings.extend(
            _check_t2(case, future_evidence_t2, case.future_evidence_t2)
        )
        checks["future_evidence_nonuse"] = not any(
            f.code == FailureCode.F8_AVAILABILITY_FREE_PROVENANCE
            for f in findings[before_future:]
        )

    if inadmissible_evidence_t2 is not None:
        before_inadmissible = len(findings)
        findings.extend(
            _check_t2(
                case,
                inadmissible_evidence_t2,
                case.inadmissible_evidence_t2,
            )
        )
        checks["inadmissible_evidence_nonuse"] = not any(
            f.code == FailureCode.F8_AVAILABILITY_FREE_PROVENANCE
            for f in findings[before_inadmissible:]
        )

    checks["basis_is_admissibility_bound"] = not any(
        f.code
        in {
            FailureCode.S2_BASIS_OUTSIDE_STIMULUS,
            FailureCode.F8_AVAILABILITY_FREE_PROVENANCE,
        }
        for f in findings
    )
    checks["temporal_non_laundering"] = not any(
        f.code == FailureCode.F6_TEMPORAL_LAUNDERING for f in findings
    )
    checks["delta_bound_resolution"] = not any(
        f.code == FailureCode.F9_NARRATIVE_SUBSTITUTION for f in findings
    )

    return VerificationReport(
        passed=not findings,
        findings=tuple(findings),
        checks=checks,
    )


def response_from_payload(payload: dict) -> TargetResponse:
    return TargetResponse.from_dict(payload)
