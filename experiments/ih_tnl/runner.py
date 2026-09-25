from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from .fixtures import canonical_case, label_swapped_case
from .model import TargetResponse
from .verifier import verify_transcript


def _load(path: str) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _response(data: dict[str, Any], key: str) -> TargetResponse:
    try:
        return TargetResponse.from_dict(data[key])
    except KeyError as exc:
        raise SystemExit(f"transcript missing required response: {key}") from exc


def _stimuli(case):
    return {
        "t2": case.t2.to_public(),
        "t3": case.t3.to_public(),
        "counterfactual_t2": case.counterfactual_t2.to_public(),
        "decoy_t2": case.decoy_t2.to_public(),
        "reordered_t2": case.reordered_t2.to_public(),
        "repeat_t2": case.t2.to_public(),
        "future_evidence_t2": case.future_evidence_t2.to_public(),
        "inadmissible_evidence_t2": case.inadmissible_evidence_t2.to_public(),
    }


def emit_bundle() -> dict[str, Any]:
    cases = [canonical_case(), label_swapped_case()]
    return {
        "benchmark": "IH-TNL/0.2",
        "profile": "canonical-plus-label-swap",
        "cases": {case.case_name: _stimuli(case) for case in cases},
        "target_contract": {
            "required_fields": [
                "resolution",
                "basis_evidence_ids",
                "claimed_discriminator_ids",
                "required_discriminator",
                "historical_state",
                "resolution_time",
                "transition_basis_ids",
            ],
            "rule": (
                "Respond independently to every stimulus. "
                "Do not assume hidden state or previous-run answers."
            ),
        },
    }


def _verify_case(case, data: dict[str, Any]) -> dict[str, Any]:
    report = verify_transcript(
        case,
        t2=_response(data, "t2"),
        t3=_response(data, "t3"),
        counterfactual_t2=_response(data, "counterfactual_t2"),
        decoy_t2=(
            TargetResponse.from_dict(data["decoy_t2"])
            if "decoy_t2" in data
            else None
        ),
        reordered_t2=(
            TargetResponse.from_dict(data["reordered_t2"])
            if "reordered_t2" in data
            else None
        ),
        repeat_t2=(
            TargetResponse.from_dict(data["repeat_t2"])
            if "repeat_t2" in data
            else None
        ),
        future_evidence_t2=(
            TargetResponse.from_dict(data["future_evidence_t2"])
            if "future_evidence_t2" in data
            else None
        ),
        inadmissible_evidence_t2=(
            TargetResponse.from_dict(data["inadmissible_evidence_t2"])
            if "inadmissible_evidence_t2" in data
            else None
        ),
    )
    return report.to_dict()


def verify_file(path: str) -> dict[str, Any]:
    data = _load(path)
    case_map = {
        "canonical-convergent-history": canonical_case(),
        "label-swapped-convergent-history": label_swapped_case(),
    }
    if "cases" not in data:
        report = _verify_case(case_map["canonical-convergent-history"], data)
        return {
            "passed": report["passed"],
            "cases": {"canonical-convergent-history": report},
        }

    reports = {}
    for name, case in case_map.items():
        if name not in data["cases"]:
            reports[name] = {
                "passed": False,
                "findings": [
                    {
                        "code": "S1",
                        "phase": "PROFILE",
                        "message": f"missing transcript case: {name}",
                    }
                ],
                "checks": {},
            }
            continue
        reports[name] = _verify_case(case, data["cases"][name])

    passed = all(r["passed"] for r in reports.values())
    return {
        "passed": passed,
        "profile": "canonical-plus-label-swap",
        "cases": reports,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ih-tnl")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("emit", help="emit the public benchmark stimulus bundle")
    verify = sub.add_parser(
        "verify",
        help="verify a machine-readable target transcript",
    )
    verify.add_argument("transcript")
    args = parser.parse_args(argv)

    if args.command == "emit":
        print(json.dumps(emit_bundle(), indent=2, sort_keys=True))
        return 0

    report = verify_file(args.transcript)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
