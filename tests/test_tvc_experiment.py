from pathlib import Path
import importlib.util


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_experiment", MODULE)
tvc = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(tvc)


def _reverify(snapshot, admissible):
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def _condition(name, *, status=tvc.ObligationStatus.SATISFIED, available=True, provenance=True):
    return tvc.HistoricalCondition(
        obligation_id=name,
        status=status,
        available_at_claim_time=available,
        provenance_valid=provenance,
    )


def test_tvc_closes_when_status_reproduces_from_all_historical_obligations():
    snapshot = tvc.EpistemicSnapshot(
        state_id="s-001",
        proposition="X",
        asserted_standing="INFERRED",
        claimed_at="2026-09-06T20:56:00-05:00",
        conditions={
            "support": _condition("support"),
            "provenance": _condition("provenance"),
            "entailment": _condition("entailment"),
            "contradictions": _condition("contradictions"),
        },
    )

    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)

    assert result.status is tvc.ClosureStatus.CLOSED
    assert result.reproduced_standing == "INFERRED"
    assert result.closure_boundary is None


def test_tvc_detects_retroactive_epistemic_promotion():
    snapshot = tvc.EpistemicSnapshot(
        state_id="s-002",
        proposition="X",
        asserted_standing="INFERRED",
        claimed_at="T1",
        conditions={
            "support": _condition("support"),
            "provenance": _condition("provenance"),
            "entailment": _condition("entailment", available=False),
            "contradictions": _condition("contradictions"),
        },
    )

    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)

    assert result.status is tvc.ClosureStatus.FAILED
    assert result.closure_boundary == "entailment"
    assert result.reproduced_standing == "EVIDENCED"


def test_tvc_preserves_unresolved_status_obligation_instead_of_promoting():
    snapshot = tvc.EpistemicSnapshot(
        state_id="s-003",
        proposition="X",
        asserted_standing="INFERRED",
        claimed_at="T1",
        conditions={
            "support": _condition("support"),
            "provenance": _condition("provenance"),
            "entailment": _condition("entailment"),
            "contradictions": _condition(
                "contradictions", status=tvc.ObligationStatus.UNRESOLVED
            ),
        },
    )

    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)

    assert result.status is tvc.ClosureStatus.UNRESOLVED
    assert result.unresolved == ("contradictions",)
    assert result.closure_boundary == "contradictions"
    assert result.reproduced_standing == "EVIDENCED"


def test_tvc_exposes_incremental_assurance_delta_after_structural_checks_pass():
    # Control condition: assume ordinary structural/provenance/time checks report no defect.
    epm_visible_failures = 0

    snapshot = tvc.EpistemicSnapshot(
        state_id="s-004",
        proposition="X",
        asserted_standing="INFERRED",
        claimed_at="T1",
        conditions={
            "support": _condition("support"),
            "provenance": _condition("provenance"),
            "entailment": _condition("entailment"),
            "contradictions": _condition(
                "contradictions", status=tvc.ObligationStatus.UNRESOLVED
            ),
        },
    )

    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)
    tvc_detected_failures = int(result.status is not tvc.ClosureStatus.CLOSED)

    assert epm_visible_failures == 0
    assert tvc_detected_failures == 1
    assert tvc_detected_failures - epm_visible_failures == 1
