"""Run the independent reduction and payload-binding gates in fresh processes."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "experiments" / "tvc" / "review_v2"


def test_integrity_review_passes_with_byte_identical_three_process_replay(tmp_path):
    outputs = []
    for seed in (0, 1, 42):
        target = tmp_path / f"review-{seed}.json"
        subprocess.run(
            [sys.executable, str(REVIEW / "run.py"), "--out", str(target)],
            env={**os.environ, "PYTHONHASHSEED": str(seed)},
            check=True, capture_output=True, text=True,
        )
        outputs.append(target.read_bytes())
    assert outputs[0] == outputs[1] == outputs[2]
    result = json.loads(outputs[0])
    assert result["closure"]["comparisons"] == 114244
    assert result["closure"]["mismatches"] == 0
    assert result["dynamic_graph"]["mismatches"] == 0
    assert result["frontier"]["mismatches"] == 0
    assert result["integrity_probes"]["prospective_payload_binding"]["original_five_witnesses_rejected"] == 5
    assert result["gates"]["irreducible_capability"] == "NOT_ESTABLISHED"


def test_equal_history_control_still_reproduces_prospective_issuance_and_detection(tmp_path):
    target = tmp_path / "history.json"
    subprocess.run([sys.executable, str(REVIEW / "prospective_factorial.py"), "--out", str(target)],
                   check=True, capture_output=True, text=True)
    result = json.loads(target.read_text())
    assert result["independently_issued_identical_contracts"] == 27
    assert result["original_later_pairs"] == 729
    assert result["tvc_full_history_detected"] == result["generic_full_history_detected"] == 702
    assert result["tvc_endpoint_only_detected"] == result["generic_endpoint_only_detected"] == 0
    assert result["full_history_false_positives_each"] == 0
