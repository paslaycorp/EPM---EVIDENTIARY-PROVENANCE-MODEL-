from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas" / "epm-release-attestation-v1.schema.json"


def _load() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def test_release_attestation_schema_identity_and_closed_world():
    schema = _load()

    assert schema["properties"]["schema_version"]["const"] == "epm-release-attestation/1.0"
    assert schema["additionalProperties"] is False


def test_release_attestation_requires_complete_evidence_chain():
    schema = _load()
    required = set(schema["required"])

    assert {
        "subject",
        "source",
        "checks",
        "artifacts",
        "dependencies",
        "deployment",
        "runtime_verification",
        "rollback",
    } <= required


def test_release_attestation_binds_exact_git_and_artifact_identities():
    schema = _load()

    assert schema["properties"]["source"]["properties"]["commit_sha"]["pattern"] == "^[0-9a-f]{40}$"
    assert schema["properties"]["artifacts"]["items"]["properties"]["sha256"]["pattern"] == "^[0-9a-f]{64}$"


def test_release_attestation_keeps_deployment_and_runtime_observation_distinct():
    schema = _load()
    deployment = schema["properties"]["deployment"]
    runtime = schema["properties"]["runtime_verification"]

    assert "deployed_commit_sha" in deployment["required"]
    assert "observed_commit_sha" in runtime["required"]
    assert deployment is not runtime


def test_release_attestation_preserves_explicit_non_execution():
    schema = _load()

    assert "performed" in schema["properties"]["deployment"]["required"]
    assert "performed" in schema["properties"]["runtime_verification"]["required"]
    assert "available" in schema["properties"]["rollback"]["required"]
