from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_chunli", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


def c(name, status=tvc.ObligationStatus.SATISFIED, *, available=True, provenance=True):
    return tvc.HistoricalCondition(name, status, available, provenance)


def snapshot(case, standing, **overrides):
    conditions = {
        "support": c("support"),
        "provenance": c("provenance"),
        "entailment": c("entailment"),
        "contradictions": c("contradictions"),
    }
    conditions.update(overrides)
    return tvc.EpistemicSnapshot(case, "X", standing, "2026-09-06T20:56:00-05:00", conditions)


def standing_conditioned_reverify(_snapshot, admissible):
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def independent_historical_reverify(snapshot, _admissible):
    """Reconstruct from the complete historically admissible condition universe.

    The asserted standing may generate duties, but it cannot censor stronger
    admissible facts from the forward reconstruction.
    """
    admissible = {
        name
        for name, condition in snapshot.conditions.items()
        if condition.available_at_claim_time
        and condition.provenance_valid
        and condition.status is tvc.ObligationStatus.SATISFIED
    }
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def test_lightning_kick_exposes_conclusion_conditioned_self_reproduction():
    s = snapshot("lightning-kick", "EVIDENCED")
    conditioned = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, standing_conditioned_reverify)
    independent = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, independent_historical_reverify)

    assert conditioned.status is tvc.ClosureStatus.CLOSED
    assert conditioned.reproduced_standing == "EVIDENCED"
    assert independent.status is tvc.ClosureStatus.DEGRADED
    assert independent.reproduced_standing == "INFERRED"


def test_spinning_bird_kick_assertion_cannot_hide_stronger_historical_state():
    evidenced = snapshot("same-world-evidenced", "EVIDENCED")
    inferred = snapshot("same-world-inferred", "INFERRED")

    evidenced_result = tvc.evaluate_closure(evidenced, tvc.DEFAULT_POLICY, independent_historical_reverify)
    inferred_result = tvc.evaluate_closure(inferred, tvc.DEFAULT_POLICY, independent_historical_reverify)

    assert evidenced_result.status is tvc.ClosureStatus.DEGRADED
    assert evidenced_result.reproduced_standing == "INFERRED"
    assert inferred_result.status is tvc.ClosureStatus.CLOSED
    assert inferred_result.reproduced_standing == "INFERRED"


def test_hyakuretsukyaku_future_entailment_still_cannot_promote_historical_state():
    s = snapshot("future-entailment", "INFERRED", entailment=c("entailment", available=False))
    result = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, independent_historical_reverify)

    assert result.status is tvc.ClosureStatus.FAILED
    assert result.closure_boundary == "entailment"
    assert result.reproduced_standing == "EVIDENCED"


def test_kikoken_unresolved_contradiction_remains_nonadmissible():
    s = snapshot(
        "unresolved-contradiction",
        "INFERRED",
        contradictions=c("contradictions", tvc.ObligationStatus.UNRESOLVED),
    )
    result = tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, independent_historical_reverify)

    assert result.status is tvc.ClosureStatus.UNRESOLVED
    assert result.closure_boundary == "contradictions"
    assert result.reproduced_standing == "EVIDENCED"


@pytest.mark.parametrize("standing", ["EVIDENCED", "INFERRED"])
def test_tenshokyaku_reconstruction_is_deterministic(standing):
    s = snapshot("determinism-" + standing.lower(), standing)
    runs = [tvc.evaluate_closure(s, tvc.DEFAULT_POLICY, independent_historical_reverify) for _ in range(100)]
    assert all(result == runs[0] for result in runs)
