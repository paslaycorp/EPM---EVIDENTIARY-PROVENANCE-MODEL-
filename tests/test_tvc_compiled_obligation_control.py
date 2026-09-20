from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

from epm import AssuranceContext, AssuranceState, EvidentiaryState, RuleBinding, State, inspect_state


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "tvc.py"
spec = importlib.util.spec_from_file_location("tvc_compiled_obligation_control", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)


def _reverify(snapshot, admissible):
    if {"support", "provenance", "entailment", "contradictions"}.issubset(admissible):
        return "INFERRED"
    if {"support", "provenance"}.issubset(admissible):
        return "EVIDENCED"
    return "UNKNOWN"


def _condition(name: str):
    return tvc.HistoricalCondition(
        obligation_id=name,
        status=tvc.ObligationStatus.SATISFIED,
        available_at_claim_time=True,
        provenance_valid=True,
    )


def test_tvc_advantage_disappears_when_same_obligation_is_manually_authored_into_epm():
    """Adversarial control for the 'generated property' objection.

    TVC's candidate distinction is not that EPM is incapable of representing an
    unresolved contradiction-disposition requirement.  If a caller manually
    authors that same requirement into EPM, current EPM preserves it and reports
    it.  TVC's candidate contribution is therefore the automatic derivation of
    that obligation from the asserted epistemic standing plus closure replay.
    """
    claim_time = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)
    assurance = State(
        state_id="compiled-control-evidence",
        properties={"evidence": AssuranceState.VALID},
        context=AssuranceContext(at=claim_time),
        rule=RuleBinding(
            rule_id="compiled-control-rule",
            version="1.0",
            authority="control",
            effective_at=claim_time,
        ),
    )

    # This is the manually compiled equivalent of TVC's status-derived duty.
    epm_state = EvidentiaryState(
        state_id="compiled-control-state",
        proposition="X",
        assurance_state=assurance,
        unresolved_conditions=("contradiction disposition required for INFERRED",),
    )
    epm_report = inspect_state(epm_state)
    assert epm_report.unresolved_conditions == (
        "contradiction disposition required for INFERRED",
    )

    snapshot = tvc.EpistemicSnapshot(
        state_id=epm_state.state_id,
        proposition=epm_state.proposition,
        asserted_standing="INFERRED",
        claimed_at=claim_time.isoformat(),
        conditions={
            "support": _condition("support"),
            "provenance": _condition("provenance"),
            "entailment": _condition("entailment"),
            # no contradiction disposition exists
        },
    )
    result = tvc.evaluate_closure(snapshot, tvc.DEFAULT_POLICY, _reverify)
    assert result.status is tvc.ClosureStatus.UNRESOLVED
    assert result.closure_boundary == "contradictions"

    # Both systems now expose the defect. TVC earns no unique detection credit
    # when the same obligation is manually pre-authored for EPM.
    epm_detects = bool(epm_report.unresolved_conditions)
    tvc_detects = result.status is not tvc.ClosureStatus.CLOSED
    assert epm_detects and tvc_detects
