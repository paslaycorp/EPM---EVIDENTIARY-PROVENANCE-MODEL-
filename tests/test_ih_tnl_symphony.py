from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from experiments.ih_tnl.epm_adapter import (
    adapter_identity,
    epm_temporal_target,
    observe_epm_availability,
)
from experiments.ih_tnl.fixtures import canonical_case
from experiments.ih_tnl.reference_targets import disciplined_target, hindsight_target
from experiments.ih_tnl.symphony import (
    SYMPHONY_VERSION,
    calibration_orchestra,
    conduct,
    orchestra_summary,
)


def test_epm_adapter_observes_future_evidence_as_unavailable_at_t2():
    case = canonical_case()
    observed = observe_epm_availability(case.future_evidence_t2)
    assert observed["D3_RECEIPT"]["status"] == "UNAVAILABLE"
    assert observed["D3_RECEIPT"]["trusted"] is True


def test_epm_adapter_observes_inadmissible_evidence_as_untrusted():
    case = canonical_case()
    observed = observe_epm_availability(case.inadmissible_evidence_t2)
    assert observed["INVALID_AUTHORITY"]["status"] == "UNKNOWN"
    assert observed["INVALID_AUTHORITY"]["trusted"] is False


def test_epm_adapter_performs_full_symphony():
    receipt = conduct(
        target_name="epm-temporal-adapter",
        target=epm_temporal_target,
        classification="candidate-adapter",
        target_metadata=adapter_identity(),
    )
    assert receipt.schema == SYMPHONY_VERSION
    assert receipt.passed is True
    assert len(receipt.cases) == 2
    assert all(case.verifier_passed for case in receipt.cases)
    assert all(
        movement.passed
        for case in receipt.cases
        for movement in case.movements
    )


def test_reference_performs_full_symphony():
    receipt = conduct(
        target_name="disciplined-reference",
        target=disciplined_target,
        classification="positive-control",
    )
    assert receipt.passed is True


def test_known_hindsight_defect_cannot_hide_inside_aggregate():
    receipt = conduct(
        target_name="hindsight-defect",
        target=hindsight_target,
        classification="negative-control",
    )
    assert receipt.passed is False
    codes = {
        finding["code"]
        for case in receipt.cases
        for finding in case.findings
    }
    assert "F1" in codes
    assert "F6" in codes


def test_calibration_orchestra_accepts_good_and_rejects_bad_controls():
    receipts = calibration_orchestra()
    assert receipts["disciplined-reference"].passed is True
    assert receipts["epm-temporal-adapter"].passed is True
    assert receipts["hindsight-defect"].passed is False
    assert receipts["outcome-defect"].passed is False
    assert receipts["contamination-defect"].passed is False
    assert receipts["hardcoded-a-defect"].passed is False


def test_public_score_is_target_independent():
    reference = conduct(
        target_name="reference",
        target=disciplined_target,
    )
    defective = conduct(
        target_name="defective",
        target=hindsight_target,
    )
    assert [c.public_score_digest for c in reference.cases] == [
        c.public_score_digest for c in defective.cases
    ]
    assert [c.transcript_digest for c in reference.cases] != [
        c.transcript_digest for c in defective.cases
    ]


def test_performance_receipt_is_deterministic():
    first = conduct(
        target_name="epm-temporal-adapter",
        target=epm_temporal_target,
        classification="candidate-adapter",
        target_metadata=adapter_identity(),
    )
    second = conduct(
        target_name="epm-temporal-adapter",
        target=epm_temporal_target,
        classification="candidate-adapter",
        target_metadata=adapter_identity(),
    )
    assert first.to_dict() == second.to_dict()
    assert first.ensemble_digest == second.ensemble_digest


def test_orchestra_summary_is_deterministic_and_non_ranking():
    first = orchestra_summary(calibration_orchestra())
    second = orchestra_summary(calibration_orchestra())
    assert first == second
    assert "ranking" not in first
    assert "score" not in first
