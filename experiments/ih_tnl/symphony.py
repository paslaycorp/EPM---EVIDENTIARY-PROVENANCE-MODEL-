from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

from .epm_adapter import adapter_identity, epm_temporal_target
from .fixtures import canonical_case, label_swapped_case
from .model import CaseBundle, TargetResponse
from .reference_targets import (
    contaminated_target,
    disciplined_target,
    hardcoded_a_target,
    hindsight_target,
    outcome_target,
)
from .verifier import verify_transcript

Target = Callable[[object], TargetResponse]

SYMPHONY_VERSION = "ih-tnl.symphony/0.3"

_MOVEMENTS = {
    "I_OVERTURE_PARITY": (
        "t2_underdetermination",
        "public_hidden_separation",
    ),
    "II_COUNTERPOINT_PROVENANCE": (
        "basis_is_admissibility_bound",
        "future_evidence_nonuse",
        "inadmissible_evidence_nonuse",
    ),
    "III_DEVELOPMENT_DELTA": (
        "t3_legitimate_resolution",
        "delta_bound_resolution",
    ),
    "IV_RETROGRADE_TIME": (
        "temporal_non_laundering",
        "counterfactual_reversion",
    ),
    "V_FUGUE_STABILITY": (
        "decoy_invariance",
        "order_invariance",
        "determinism",
    ),
}


@dataclass(frozen=True)
class MovementReceipt:
    movement: str
    checks: dict[str, bool]
    passed: bool


@dataclass(frozen=True)
class CasePerformance:
    case_name: str
    public_score_digest: str
    transcript_digest: str
    movements: tuple[MovementReceipt, ...]
    verifier_passed: bool
    findings: tuple[dict[str, str], ...]


@dataclass(frozen=True)
class SymphonyReceipt:
    schema: str
    target: str
    classification: str
    passed: bool
    cases: tuple[CasePerformance, ...]
    ensemble_digest: str
    target_metadata: dict[str, str]

    def to_dict(self) -> dict:
        return asdict(self)


def _digest(payload) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _public_case_payload(case: CaseBundle) -> dict:
    return {
        "case_name": case.case_name,
        "t2": case.t2.to_public(),
        "t3": case.t3.to_public(),
        "counterfactual_t2": case.counterfactual_t2.to_public(),
        "decoy_t2": case.decoy_t2.to_public(),
        "reordered_t2": case.reordered_t2.to_public(),
        "repeat_t2": case.t2.to_public(),
        "future_evidence_t2": case.future_evidence_t2.to_public(),
        "inadmissible_evidence_t2": case.inadmissible_evidence_t2.to_public(),
    }


def _perform_case(case: CaseBundle, target: Target) -> CasePerformance:
    responses = {
        "t2": target(case.t2),
        "t3": target(case.t3),
        "counterfactual_t2": target(case.counterfactual_t2),
        "decoy_t2": target(case.decoy_t2),
        "reordered_t2": target(case.reordered_t2),
        "repeat_t2": target(case.t2),
        "future_evidence_t2": target(case.future_evidence_t2),
        "inadmissible_evidence_t2": target(case.inadmissible_evidence_t2),
    }
    report = verify_transcript(
        case,
        t2=responses["t2"],
        t3=responses["t3"],
        counterfactual_t2=responses["counterfactual_t2"],
        decoy_t2=responses["decoy_t2"],
        reordered_t2=responses["reordered_t2"],
        repeat_t2=responses["repeat_t2"],
        future_evidence_t2=responses["future_evidence_t2"],
        inadmissible_evidence_t2=responses["inadmissible_evidence_t2"],
    )
    movements = []
    for movement, names in _MOVEMENTS.items():
        checks = {name: report.checks.get(name, False) for name in names}
        movements.append(
            MovementReceipt(
                movement=movement,
                checks=checks,
                passed=all(checks.values()),
            )
        )

    transcript_payload = {
        name: response.to_dict() for name, response in responses.items()
    }
    findings = tuple(
        {
            "code": finding.code.value,
            "phase": finding.phase,
            "message": finding.message,
        }
        for finding in report.findings
    )
    return CasePerformance(
        case_name=case.case_name,
        public_score_digest=_digest(_public_case_payload(case)),
        transcript_digest=_digest(transcript_payload),
        movements=tuple(movements),
        verifier_passed=report.passed,
        findings=findings,
    )


def conduct(
    *,
    target_name: str,
    target: Target,
    classification: str = "candidate",
    target_metadata: dict[str, str] | None = None,
) -> SymphonyReceipt:
    cases = (
        _perform_case(canonical_case(), target),
        _perform_case(label_swapped_case(), target),
    )
    body = {
        "schema": SYMPHONY_VERSION,
        "target": target_name,
        "classification": classification,
        "cases": [asdict(case) for case in cases],
        "target_metadata": target_metadata or {},
    }
    return SymphonyReceipt(
        schema=SYMPHONY_VERSION,
        target=target_name,
        classification=classification,
        passed=all(
            case.verifier_passed
            and all(movement.passed for movement in case.movements)
            for case in cases
        ),
        cases=cases,
        ensemble_digest=_digest(body),
        target_metadata=target_metadata or {},
    )


def calibration_orchestra() -> dict[str, SymphonyReceipt]:
    targets = {
        "disciplined-reference": (
            disciplined_target,
            "positive-control",
            {"role": "known-good benchmark control"},
        ),
        "epm-temporal-adapter": (
            epm_temporal_target,
            "candidate-adapter",
            adapter_identity(),
        ),
        "hindsight-defect": (
            hindsight_target,
            "negative-control",
            {"role": "known temporal-laundering defect"},
        ),
        "outcome-defect": (
            outcome_target,
            "negative-control",
            {"role": "known correct-outcome substitution defect"},
        ),
        "contamination-defect": (
            contaminated_target,
            "negative-control",
            {"role": "known irreversible-contamination defect"},
        ),
        "hardcoded-a-defect": (
            hardcoded_a_target,
            "negative-control",
            {"role": "known label-memorization defect"},
        ),
    }
    return {
        name: conduct(
            target_name=name,
            target=target,
            classification=classification,
            target_metadata=metadata,
        )
        for name, (target, classification, metadata) in targets.items()
    }


def orchestra_summary(receipts: dict[str, SymphonyReceipt]) -> dict:
    return {
        "schema": SYMPHONY_VERSION,
        "performances": {
            name: {
                "classification": receipt.classification,
                "passed": receipt.passed,
                "ensemble_digest": receipt.ensemble_digest,
                "movements": {
                    case.case_name: {
                        movement.movement: movement.passed
                        for movement in case.movements
                    }
                    for case in receipt.cases
                },
                "failure_codes": sorted(
                    {
                        finding["code"]
                        for case in receipt.cases
                        for finding in case.findings
                    }
                ),
            }
            for name, receipt in receipts.items()
        },
    }


def _write_or_print(payload: dict, output: str | None) -> None:
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if output:
        Path(output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ih-tnl-symphony")
    sub = parser.add_subparsers(dest="command", required=True)

    perform = sub.add_parser("perform")
    perform.add_argument(
        "--target",
        choices=("reference", "epm"),
        default="epm",
    )
    perform.add_argument("--output")

    ensemble = sub.add_parser("ensemble")
    ensemble.add_argument("--output")

    args = parser.parse_args(argv)
    if args.command == "perform":
        if args.target == "reference":
            receipt = conduct(
                target_name="disciplined-reference",
                target=disciplined_target,
                classification="positive-control",
                target_metadata={"role": "known-good benchmark control"},
            )
        else:
            receipt = conduct(
                target_name="epm-temporal-adapter",
                target=epm_temporal_target,
                classification="candidate-adapter",
                target_metadata=adapter_identity(),
            )
        _write_or_print(receipt.to_dict(), args.output)
        return 0 if receipt.passed else 1

    receipts = calibration_orchestra()
    summary = orchestra_summary(receipts)
    _write_or_print(summary, args.output)
    controls_ok = (
        receipts["disciplined-reference"].passed
        and receipts["epm-temporal-adapter"].passed
        and not receipts["hindsight-defect"].passed
        and not receipts["outcome-defect"].passed
        and not receipts["contamination-defect"].passed
        and not receipts["hardcoded-a-defect"].passed
    )
    return 0 if controls_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
