import ast
import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "contracts" / "epm-maturity-boundary-v1.json"
SCHEMA = ROOT / "schemas" / "epm-maturity-boundary-v1.schema.json"
AUTHORITY = ROOT / "src" / "epm" / "authority.py"

EXPECTED_OWNS = {
    "admissibility_evaluation",
    "evidence_authority_binding",
    "explicit_constraint_definition",
    "fail_closed_decision_state",
    "decision_receipt_emission",
}

EXPECTED_DOES_NOT_OWN = {
    "external_mutation",
    "credential_exercise",
    "network_action",
    "process_execution",
    "external_constraint_enforcement",
    "executor_compliance_proof",
    "production_deployment_authority",
}

FORBIDDEN_AUTHORITY_IMPORT_ROOTS = {
    "asyncio",
    "ftplib",
    "http",
    "httpx",
    "requests",
    "shutil",
    "smtplib",
    "socket",
    "subprocess",
    "urllib",
}

FORBIDDEN_AUTHORITY_CALLS = {
    "eval",
    "exec",
    "open",
}


def _contract():
    return json.loads(CONTRACT.read_text())


def test_maturity_boundary_contract_validates():
    contract = _contract()
    schema = json.loads(SCHEMA.read_text())

    Draft202012Validator(schema).validate(contract)


def test_epm_core_is_definition_only():
    contract = _contract()

    assert contract["current_stage"] == "definition_only"
    assert set(contract["core_boundary"]["owns"]) == EXPECTED_OWNS
    assert set(contract["core_boundary"]["does_not_own"]) == EXPECTED_DOES_NOT_OWN


def test_layer_identity_cannot_collapse():
    contract = _contract()
    layers = contract["layers"]

    assert [layer["id"] for layer in layers] == [
        "definition",
        "enforcement",
        "execution",
        "execution_evidence",
    ]
    assert layers[0]["owner"] == "EPM Core"
    assert layers[0]["status"] == "active"
    assert all(layer["status"] == "future" for layer in layers[1:])
    assert len({layer["owner"] for layer in layers}) == 4


def test_maturity_stages_are_monotonic_and_explicit():
    contract = _contract()

    assert [gate["stage"] for gate in contract["maturity_gates"]] == [
        "M1",
        "M2",
        "M3",
        "M4",
        "M5",
    ]

    invariants = set(contract["permanent_invariants"])
    assert "later_maturity_does_not_rewrite_earlier_evidence" in invariants
    assert "integrated_distribution_does_not_collapse_layer_identity" in invariants


def test_authority_path_has_no_execution_capability():
    tree = ast.parse(AUTHORITY.read_text())

    imported_roots = set()
    direct_calls = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            direct_calls.add(node.func.id)

    assert imported_roots.isdisjoint(FORBIDDEN_AUTHORITY_IMPORT_ROOTS)
    assert direct_calls.isdisjoint(FORBIDDEN_AUTHORITY_CALLS)


def test_frozen_release_refs_are_preserved_in_contract():
    contract = _contract()

    assert contract["frozen_release_refs"] == {
        "v0.1.1": "87903f2d53531bf28d97f1271af62b6d9b3e64be",
        "v0.1.2": "bb0559ddb8eff7f78acc432c0334ce7596c1045c",
    }
