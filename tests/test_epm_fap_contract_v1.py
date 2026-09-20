from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from epm import AssuranceState, Decision, FailureCode
from epm.assurance import Property

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_SCHEMA = ROOT / "schemas" / "epm-fap-evidence-receipt-v1.schema.json"
DECISION_SCHEMA = ROOT / "schemas" / "epm-fap-decision-receipt-v1.schema.json"
CONTRACT_VERSION = "epm-fap-assurance/1.0"
SHA = "a" * 40


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _errors(schema: dict, instance: dict) -> list:
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    return sorted(validator.iter_errors(instance), key=lambda error: list(error.path))


def _valid_evidence_receipt() -> dict:
    return {
        "schema_version": "epm-fap-evidence-receipt/1.0",
        "contract_version": CONTRACT_VERSION,
        "contract_revision_sha": SHA,
        "receipt_id": "receipt:evidence:1",
        "evidence_id": "evidence-1",
        "source": "fap-core",
        "provenance_ref": "sha256:deadbeef",
        "observed_at": "2026-09-20T05:00:00Z",
        "available_at": "2026-09-20T04:59:59Z",
        "attestation": {
            "attestation_id": "attestation-1",
            "authority": "fap-core-test",
            "method": "fixture",
            "basis": "deterministic schema test",
            "validated": True,
        },
        "boundary_validation": {
            "validated": False,
            "validator": "fap-core",
            "method": "not-evaluated",
            "basis": "no trusted boundary validator supplied",
            "validated_at": "2026-09-20T05:00:00Z",
        },
        "producer": {
            "component": "fap-core",
            "repository": "paslaycorp/FAP-Core-v0.2.0",
            "commit_sha": "b" * 40,
        },
    }


def _valid_decision_receipt() -> dict:
    return {
        "schema_version": "epm-fap-decision-receipt/1.0",
        "contract_version": CONTRACT_VERSION,
        "contract_revision_sha": SHA,
        "receipt_id": "receipt:decision:1",
        "epm_engine_version": "epm-engine/0.1.2",
        "epm_release_sha": "c" * 40,
        "transition_id": "transition-1",
        "source_evidence_id": "evidence-1",
        "property": "applicability",
        "state": "UNKNOWN",
        "decision": "DEFER",
        "failure": "NONE",
        "reason": "Evidence remains unresolved.",
        "rule": {
            "rule_id": "rule-1",
            "version": "1",
            "authority": "authority-1",
            "jurisdiction": "US-TX",
            "effective_at": "2026-09-20T04:00:00Z",
        },
        "evidence_refs": ["evidence-1"],
        "fail_closed": True,
        "evaluated_at": "2026-09-20T05:00:00Z",
    }


def test_contract_schemas_parse_and_share_contract_identity():
    evidence = _load(EVIDENCE_SCHEMA)
    decision = _load(DECISION_SCHEMA)

    Draft202012Validator.check_schema(evidence)
    Draft202012Validator.check_schema(decision)

    assert evidence["properties"]["contract_version"]["const"] == CONTRACT_VERSION
    assert decision["properties"]["contract_version"]["const"] == CONTRACT_VERSION
    assert evidence["$id"] == "urn:epm:schema:epm-fap-evidence-receipt:1.0"
    assert decision["$id"] == "urn:epm:schema:epm-fap-decision-receipt:1.0"
    assert evidence["additionalProperties"] is False
    assert decision["additionalProperties"] is False


def test_valid_receipt_instances_pass_full_schema_and_format_validation():
    assert _errors(_load(EVIDENCE_SCHEMA), _valid_evidence_receipt()) == []
    assert _errors(_load(DECISION_SCHEMA), _valid_decision_receipt()) == []


def test_contract_revision_is_required_and_exact():
    for schema_path, instance in (
        (EVIDENCE_SCHEMA, _valid_evidence_receipt()),
        (DECISION_SCHEMA, _valid_decision_receipt()),
    ):
        schema = _load(schema_path)
        assert "contract_revision_sha" in schema["required"]

        missing = dict(instance)
        missing.pop("contract_revision_sha")
        assert _errors(schema, missing)

        malformed = dict(instance)
        malformed["contract_revision_sha"] = "main"
        assert _errors(schema, malformed)


def test_schema_format_validation_rejects_invalid_timestamp():
    schema = _load(EVIDENCE_SCHEMA)
    receipt = _valid_evidence_receipt()
    receipt["observed_at"] = "not-a-date"

    assert _errors(schema, receipt)


def test_evidence_receipt_does_not_encode_score_confidence_or_decision_authority():
    schema = _load(EVIDENCE_SCHEMA)
    fields = set(schema["properties"])

    assert "score" not in fields
    assert "confidence" not in fields
    assert "verdict" not in fields
    assert "decision" not in fields
    assert "state" not in fields


def test_boundary_validation_is_adapter_owned_metadata():
    schema = _load(EVIDENCE_SCHEMA)
    boundary = schema["properties"]["boundary_validation"]

    assert set(boundary["required"]) == {
        "validated",
        "validator",
        "method",
        "basis",
        "validated_at",
    }
    for field in boundary["required"]:
        assert boundary["properties"][field]["readOnly"] is True


def test_decision_receipt_enums_match_runtime_exactly():
    schema = _load(DECISION_SCHEMA)

    assert set(schema["properties"]["state"]["enum"]) == {item.value for item in AssuranceState}
    assert set(schema["properties"]["decision"]["enum"]) == {item.value for item in Decision}
    assert set(schema["properties"]["failure"]["enum"]) == {item.value for item in FailureCode}
    assert set(schema["properties"]["property"]["enum"]) == {item.value for item in Property}


def test_decision_receipt_requires_exact_runtime_provenance_fields():
    schema = _load(DECISION_SCHEMA)
    required = set(schema["required"])

    assert "epm_engine_version" in required
    assert "epm_release_sha" in required
    assert "contract_revision_sha" in required
    assert schema["properties"]["epm_release_sha"]["pattern"] == "^[0-9a-f]{40}$"
    assert schema["properties"]["contract_revision_sha"]["pattern"] == "^[0-9a-f]{40}$"
    assert "fail_closed" in required
