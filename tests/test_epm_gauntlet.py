import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GAUNTLET = ROOT / "tools" / "epm_gauntlet.py"
RELEASE_SHA = "87903f2d53531bf28d97f1271af62b6d9b3e64be"
GAUNTLET_SCHEMA = "epm.external-validation-receipt/1.0"


def _run_gauntlet(tmp_path: Path) -> dict:
    receipt_path = tmp_path / "validation-receipt.json"
    completed = subprocess.run(
        [sys.executable, str(GAUNTLET), "--output", str(receipt_path)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return json.loads(receipt_path.read_text(encoding="utf-8"))


def test_blackbox_gauntlet_passes_every_declared_invariant(tmp_path):
    receipt = _run_gauntlet(tmp_path)

    assert receipt["schema_version"] == GAUNTLET_SCHEMA
    assert receipt["release_sha"] == RELEASE_SHA
    assert receipt["engine_version"] == "epm-engine/0.1.2"
    assert receipt["total_cases"] >= 12
    assert receipt["failed_cases"] == 0
    assert receipt["passed_cases"] == receipt["total_cases"]
    assert receipt["result"] == "PASS"


def test_blackbox_gauntlet_case_ids_are_unique(tmp_path):
    receipt = _run_gauntlet(tmp_path)
    case_ids = [case["case_id"] for case in receipt["cases"]]
    assert len(case_ids) == len(set(case_ids))
