from __future__ import annotations

import json
from pathlib import Path

from epm import AssuranceState, Decision, FailureCode
from epm.assurance import Property

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE_SCHEMA = ROOT / "schemas" / "epm-fap-evidence-receipt-v1.schema.json"
DECISION_SCHEMA = ROOT / "schemas" / "epm-fap-decision-receipt-v1.schema.json"
CONTRACT_VERSION = "epm-fap-assurance/1.0"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_contract_schemas_parse_and_share_contract_identity():
    evidence = _load(EVIDENCE_SCHEMA)
    decision = _load(DECISION_SCHEMA)

    assert evidence["properties"]["contract_version"]["const"] == CONTRACT_VERSION
    assert decision["properties"]["contract_version"]["const"] == CONTRACT_VERSION
    assert evidence["additionalProperties"] is False
    assert decision["additionalProperties"] is False


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
    assert schema["properties"]["epm_release_sha"]["pattern"] == "^[0-9a-f]{40}$"
    assert "fail_closed" in required
