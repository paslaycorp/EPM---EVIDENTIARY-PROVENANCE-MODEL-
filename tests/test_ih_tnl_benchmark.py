from experiments.ih_tnl.fixtures import canonical_case, label_swapped_case
from experiments.ih_tnl.model import FailureCode, Resolution
from experiments.ih_tnl.reference_targets import (
    contaminated_target,
    disciplined_target,
    hardcoded_a_target,
    hindsight_target,
    outcome_target,
)
from experiments.ih_tnl.verifier import canonical_public_hash, verify_transcript


def run_target(target, case=None):
    case = case or canonical_case()
    return case, verify_transcript(
        case,
        t2=target(case.t2),
        t3=target(case.t3),
        counterfactual_t2=target(case.counterfactual_t2),
        decoy_t2=target(case.decoy_t2),
        reordered_t2=target(case.reordered_t2),
        repeat_t2=target(case.t2),
        future_evidence_t2=target(case.future_evidence_t2),
        inadmissible_evidence_t2=target(case.inadmissible_evidence_t2),
    )


def codes(report):
    return {f.code for f in report.findings}


def test_reference_target_passes_every_gate_canonical():
    _, report = run_target(disciplined_target)
    assert report.passed, report.to_dict()
    assert all(report.checks.values())


def test_reference_target_passes_label_swapped_case():
    _, report = run_target(disciplined_target, label_swapped_case())
    assert report.passed, report.to_dict()


def test_hardcoded_history_a_fails_label_swap():
    _, report = run_target(hardcoded_a_target, label_swapped_case())
    assert not report.passed
    assert FailureCode.F5_UNCERTAINTY_COLLAPSE in codes(report)


def test_hindsight_selection_is_rejected():
    _, report = run_target(hindsight_target)
    assert not report.passed
    assert FailureCode.F1_UNSUPPORTED_SELECTION in codes(report)
    assert FailureCode.F6_TEMPORAL_LAUNDERING in codes(report)


def test_correct_but_illegitimate_outcome_is_rejected():
    _, report = run_target(outcome_target)
    assert not report.passed
    assert FailureCode.F4_OUTCOME_INFERENCE in codes(report)


def test_later_evidence_cannot_rewrite_t2():
    _, report = run_target(contaminated_target)
    assert not report.passed
    assert FailureCode.F6_TEMPORAL_LAUNDERING in codes(report)
    assert FailureCode.F10_IRREVERSIBLE_CONTAMINATION in codes(report)


def test_basis_cannot_cite_absent_evidence():
    case = canonical_case()
    bad = disciplined_target(case.t2)
    bad.claimed_discriminator_ids = ["D3_RECEIPT"]
    report = verify_transcript(
        case,
        t2=bad,
        t3=disciplined_target(case.t3),
        counterfactual_t2=disciplined_target(case.counterfactual_t2),
    )
    assert FailureCode.S2_BASIS_OUTSIDE_STIMULUS in codes(report)


def test_visible_but_future_evidence_cannot_be_used_at_t2():
    case = canonical_case()
    bad = disciplined_target(case.future_evidence_t2)
    bad.basis_evidence_ids = ["D3_RECEIPT"]
    bad.claimed_discriminator_ids = ["D3_RECEIPT"]
    report = verify_transcript(
        case,
        t2=disciplined_target(case.t2),
        t3=disciplined_target(case.t3),
        counterfactual_t2=disciplined_target(case.counterfactual_t2),
        future_evidence_t2=bad,
    )
    assert FailureCode.F8_AVAILABILITY_FREE_PROVENANCE in codes(report)


def test_present_but_inadmissible_authority_cannot_be_used_at_t2():
    case = canonical_case()
    bad = disciplined_target(case.inadmissible_evidence_t2)
    bad.basis_evidence_ids = ["INVALID_AUTHORITY"]
    bad.claimed_discriminator_ids = ["INVALID_AUTHORITY"]
    report = verify_transcript(
        case,
        t2=disciplined_target(case.t2),
        t3=disciplined_target(case.t3),
        counterfactual_t2=disciplined_target(case.counterfactual_t2),
        inadmissible_evidence_t2=bad,
    )
    assert FailureCode.F8_AVAILABILITY_FREE_PROVENANCE in codes(report)


def test_counterfactual_removal_restores_uncertainty():
    case = canonical_case()
    cf = disciplined_target(case.counterfactual_t2)
    assert cf.resolution == Resolution.UNRESOLVED
    report = verify_transcript(
        case,
        t2=disciplined_target(case.t2),
        t3=disciplined_target(case.t3),
        counterfactual_t2=cf,
    )
    assert FailureCode.F10_IRREVERSIBLE_CONTAMINATION not in codes(report)


def test_decoy_does_not_change_epistemic_state():
    case = canonical_case()
    report = verify_transcript(
        case,
        t2=disciplined_target(case.t2),
        t3=disciplined_target(case.t3),
        counterfactual_t2=disciplined_target(case.counterfactual_t2),
        decoy_t2=disciplined_target(case.decoy_t2),
    )
    assert report.checks["decoy_invariance"] is True


def test_evidence_order_does_not_change_epistemic_state():
    case = canonical_case()
    report = verify_transcript(
        case,
        t2=disciplined_target(case.t2),
        t3=disciplined_target(case.t3),
        counterfactual_t2=disciplined_target(case.counterfactual_t2),
        reordered_t2=disciplined_target(case.reordered_t2),
    )
    assert report.checks["order_invariance"] is True


def test_identical_replay_is_deterministic():
    case = canonical_case()
    report = verify_transcript(
        case,
        t2=disciplined_target(case.t2),
        t3=disciplined_target(case.t3),
        counterfactual_t2=disciplined_target(case.counterfactual_t2),
        repeat_t2=disciplined_target(case.t2),
    )
    assert report.checks["determinism"] is True


def test_t3_discriminator_is_absent_from_t2_public_payload():
    case = canonical_case()
    ids = {e.evidence_id for e in case.t2.evidence}
    assert case.hidden.t3_discriminator_evidence_id not in ids


def test_hidden_truth_is_not_serialized_in_public_stimulus():
    case = canonical_case()
    serialized = str(case.t2.to_public())
    assert "legitimate_history" not in serialized
    assert "correct_outcome_history" not in serialized
    assert "D3_RECEIPT" not in serialized


def test_canonical_hash_is_deterministic():
    case = canonical_case()
    assert canonical_public_hash(case.t2) == canonical_public_hash(case.t2)
