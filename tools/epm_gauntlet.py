"""EPM Blackbox Gauntlet.

Run a bounded set of adversarial attacks against the released EPM semantics and
emit a machine-readable validation receipt. The gauntlet is intentionally
boring in one respect: it does not invent a score. Every case has an explicit
invariant and a pass/fail observation.
"""
from __future__ import annotations

import argparse
import json
import platform
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Callable

from epm import (
    AssuranceContext,
    AssuranceState,
    AvailabilityAttestation,
    EvidenceAvailability,
    EvidentiaryEnvelope,
    EvidentiaryState,
    EPM_ENGINE_VERSION,
    PreservationProof,
    RuleBinding,
    State,
    assess_temporal_availability,
    assess_transition,
    inspect_state,
)
from epm.resolution import (
    ResolutionState,
    create_answer_space,
    record_derivation,
)
from epm.sources import (
    EpistemicSourceRecord,
    EpistemicSourceType,
    observation_reclassification_allowed,
)

GAUNTLET_SCHEMA = "epm.external-validation-receipt/1.0"
RELEASE_SHA = "87903f2d53531bf28d97f1271af62b6d9b3e64be"


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    attack_class: str
    invariant: str
    passed: bool
    observed: dict[str, Any]
    expected: dict[str, Any]


@dataclass(frozen=True)
class ValidationReceipt:
    schema_version: str
    engine_version: str
    release_sha: str
    python_version: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    result: str
    cases: tuple[CaseResult, ...]


def _rule(*, authority: str = "court", at: datetime) -> RuleBinding:
    return RuleBinding(
        rule_id="evidence-rule",
        version="1",
        authority=authority,
        jurisdiction="US-TX",
        effective_at=at,
    )


def _context(
    *,
    at: datetime,
    purpose: str = "admission-review",
    scope: str = "case-record",
    jurisdiction: str = "US-TX",
) -> AssuranceContext:
    return AssuranceContext(
        identity="MAT-001",
        purpose=purpose,
        scope=scope,
        jurisdiction=jurisdiction,
        at=at,
    )


def _transition(
    *,
    source_at: datetime,
    target_at: datetime | None = None,
    source_purpose: str = "admission-review",
    target_purpose: str = "admission-review",
    source_scope: str = "case-record",
    target_scope: str = "case-record",
    source_jurisdiction: str = "US-TX",
    target_jurisdiction: str = "US-TX",
    source_assurance: AssuranceState = AssuranceState.PRESERVED,
    source_rule: RuleBinding | None = None,
    target_rule: RuleBinding | None = None,
    preservation: PreservationProof | None = None,
    consequence: str = "critical",
) -> dict[str, object]:
    target_at = target_at or source_at
    source_rule = source_rule or _rule(at=source_at)
    target_rule = target_rule or _rule(at=target_at)
    source_context = _context(
        at=source_at,
        purpose=source_purpose,
        scope=source_scope,
        jurisdiction=source_jurisdiction,
    )
    target_context = _context(
        at=target_at,
        purpose=target_purpose,
        scope=target_scope,
        jurisdiction=target_jurisdiction,
    )
    material = any(
        (
            source_context != target_context,
            source_rule != target_rule,
        )
    )
    source = State(
        "EX-001",
        {"applicability": source_assurance},
        source_context,
        source_rule,
    )
    target = State(
        "EX-001:target",
        {"applicability": AssuranceState.PRESERVED},
        target_context,
        target_rule,
    )
    envelope = EvidentiaryEnvelope(
        transition_id="gauntlet:EX-001",
        source=source,
        target=target,
        material_properties=frozenset({"applicability"}) if material else frozenset(),
        preservation={"applicability": preservation} if preservation else {},
        consequence=consequence,
    )
    return dict(assess_transition(envelope))


def _case(
    case_id: str,
    attack_class: str,
    invariant: str,
    observed: dict[str, Any],
    expected: dict[str, Any],
) -> CaseResult:
    passed = all(observed.get(key) == value for key, value in expected.items())
    return CaseResult(case_id, attack_class, invariant, passed, observed, expected)


def case_control_authorized() -> CaseResult:
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    observed = _transition(source_at=at)
    return _case(
        "G-00",
        "Control",
        "Unchanged valid context remains usable without manufacturing a failure.",
        observed,
        {"decision": "AUTHORIZED", "failure": "NONE", "fail_closed": False},
    )


def case_purpose_laundering() -> CaseResult:
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    observed = _transition(
        source_at=at,
        target_purpose="public-disclosure",
    )
    return _case(
        "G-01",
        "Purpose laundering",
        "Valid evidence does not become applicable to a materially different purpose by reuse alone.",
        observed,
        {"decision": "DENY", "failure": "MISAPPLICATION", "fail_closed": True},
    )


def case_scope_laundering() -> CaseResult:
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    observed = _transition(
        source_at=at,
        target_scope="public-record",
    )
    return _case(
        "G-02",
        "Scope laundering",
        "Scope expansion requires an explicit preservation determination.",
        observed,
        {"decision": "DENY", "failure": "MISAPPLICATION", "fail_closed": True},
    )


def case_jurisdiction_laundering() -> CaseResult:
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    observed = _transition(
        source_at=at,
        target_jurisdiction="US-CA",
    )
    return _case(
        "G-03",
        "Jurisdiction laundering",
        "Evidence does not silently preserve applicability across jurisdictions.",
        observed,
        {"decision": "DENY", "failure": "JURISDICTION_MISMATCH", "fail_closed": True},
    )


def case_temporal_laundering() -> CaseResult:
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    observed = _transition(
        source_at=at,
        target_at=at + timedelta(hours=1),
    )
    return _case(
        "G-04",
        "Temporal context laundering",
        "A changed decision time is material unless preservation is established.",
        observed,
        {"decision": "DENY", "failure": "TEMPORAL_MISMATCH", "fail_closed": True},
    )


def case_rule_laundering() -> CaseResult:
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    source_rule = _rule(at=at)
    target_rule = RuleBinding("evidence-rule", "2", "court", "US-TX", at)
    observed = _transition(
        source_at=at,
        source_rule=source_rule,
        target_rule=target_rule,
    )
    return _case(
        "G-05",
        "Rule/version laundering",
        "A different rule binding is not equivalent merely because the artifact is intact.",
        observed,
        {"decision": "DENY", "failure": "RULE_MISMATCH", "fail_closed": True},
    )


def case_authority_laundering() -> CaseResult:
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    target_rule = _rule(authority="court", at=at)
    proof = PreservationProof(
        property_name="applicability",
        transition_id="gauntlet:EX-001",
        rule_id=target_rule.rule_id,
        rule_version=target_rule.version,
        authority="not-the-court",
        evidence_refs=("receipt:1",),
        valid=True,
    )
    observed = _transition(
        source_at=at,
        target_purpose="public-disclosure",
        target_rule=target_rule,
        preservation=proof,
    )
    return _case(
        "G-06",
        "Authority laundering",
        "A preservation proof from the wrong authority cannot authorize the target rule.",
        observed,
        {"decision": "DENY", "failure": "AUTHORITY_MISMATCH", "fail_closed": True},
    )


def case_unknown_inflation() -> CaseResult:
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    observed = _transition(
        source_at=at,
        source_assurance=AssuranceState.UNKNOWN,
    )
    return _case(
        "G-07",
        "Unknown inflation",
        "UNKNOWN is conserved rather than upgraded to authorization.",
        observed,
        {"decision": "DEFER", "state": "UNKNOWN", "fail_closed": False},
    )


def case_future_rule_leakage() -> CaseResult:
    state_at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    rule = RuleBinding(
        "evidence-rule",
        "2",
        "court",
        "US-TX",
        state_at + timedelta(hours=2),
    )
    assurance = State(
        "EX-001",
        {"applicability": AssuranceState.PRESERVED},
        _context(at=state_at),
        rule,
    )
    report = inspect_state(
        EvidentiaryState(
            state_id="gauntlet:future-rule",
            proposition="The exhibit may be used under the governing rule.",
            assurance_state=assurance,
        )
    )
    observed = {"structural_issues": list(report.structural_issues)}
    expected = {"structural_issues": ["RULE_NOT_YET_EFFECTIVE"]}
    return _case(
        "G-08",
        "Future-rule leakage",
        "A rule cannot be projected backward onto a state that predates its effective time.",
        observed,
        expected,
    )


def case_evidence_availability_leakage() -> CaseResult:
    state_at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    available_at = state_at + timedelta(hours=3)
    availability = EvidenceAvailability(
        evidence_id="EX-001",
        available_at=available_at,
        observed_at=available_at,
        source="authenticated-receipt",
        provenance_ref="receipt:EX-001",
        attestation=AvailabilityAttestation(
            "att-1",
            "evidence-system",
            "authenticated-receipt",
            "server-observed receipt",
            True,
        ),
    )
    result = assess_temporal_availability(
        evidence_id="EX-001",
        state_at=state_at,
        availability=availability,
    )
    observed = {"status": result.status.value}
    return _case(
        "G-09",
        "Temporal evidence leakage",
        "Evidence available later cannot be treated as available to an earlier state.",
        observed,
        {"status": "UNAVAILABLE"},
    )


def case_computation_to_observation() -> CaseResult:
    source = EpistemicSourceRecord(
        source_id="calc-1",
        source_type=EpistemicSourceType.COMPUTATIONAL_DISCOVERY,
        producer="gauntlet",
        provenance_refs=("EX-001",),
        input_refs=("EX-001",),
        external_origin=False,
    )
    result = observation_reclassification_allowed(source)
    observed = {"valid": result.valid, "reason_code": result.reason_code}
    return _case(
        "G-10",
        "Computation-to-observation laundering",
        "Internal computation cannot relabel itself as a new external observation.",
        observed,
        {"valid": False, "reason_code": "NEW_OBSERVATION_REQUIRED"},
    )


def case_constraint_to_resolution() -> CaseResult:
    snapshot = create_answer_space(
        question_id="who-signed",
        candidates=("A", "B"),
        granularity="named-signer",
        granularity_basis="case question",
    )
    narrowed = record_derivation(snapshot, candidate="A", derivation_ref="calc:1")
    observed = {
        "resolution_state": narrowed.snapshot.resolution_state.value,
        "epistemic_standing": narrowed.snapshot.epistemic_standing.value,
        "applied": narrowed.applied,
    }
    return _case(
        "G-11",
        "Derivation-to-resolution laundering",
        "A derivation may be recorded without manufacturing external resolution.",
        observed,
        {
            "resolution_state": ResolutionState.UNRESOLVED.value,
            "epistemic_standing": "DERIVED",
            "applied": True,
        },
    )


CASES: tuple[Callable[[], CaseResult], ...] = (
    case_control_authorized,
    case_purpose_laundering,
    case_scope_laundering,
    case_jurisdiction_laundering,
    case_temporal_laundering,
    case_rule_laundering,
    case_authority_laundering,
    case_unknown_inflation,
    case_future_rule_leakage,
    case_evidence_availability_leakage,
    case_computation_to_observation,
    case_constraint_to_resolution,
)


def run_gauntlet() -> ValidationReceipt:
    results = tuple(case() for case in CASES)
    passed = sum(result.passed for result in results)
    failed = len(results) - passed
    return ValidationReceipt(
        schema_version=GAUNTLET_SCHEMA,
        engine_version=EPM_ENGINE_VERSION,
        release_sha=RELEASE_SHA,
        python_version=platform.python_version(),
        total_cases=len(results),
        passed_cases=passed,
        failed_cases=failed,
        result="PASS" if failed == 0 else "FAIL",
        cases=results,
    )


def write_receipt(receipt: ValidationReceipt, output: Path | None) -> None:
    payload = json.dumps(asdict(receipt), indent=2, sort_keys=True) + "\n"
    if output is None:
        print(payload, end="")
        return
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(payload, encoding="utf-8")
    print(output)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the EPM Blackbox Gauntlet")
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the machine-readable validation receipt.",
    )
    args = parser.parse_args()
    receipt = run_gauntlet()
    write_receipt(receipt, args.output)
    return 0 if receipt.failed_cases == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
