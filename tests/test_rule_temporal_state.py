from __future__ import annotations

from datetime import UTC, datetime, timedelta

from epm import (
    AssuranceContext,
    AssuranceState,
    EvidentiaryState,
    RuleBinding,
    State,
    inspect_state,
)


AT = datetime(2026, 9, 6, 20, 56, tzinfo=UTC)


def _state(*, state_at=AT, rule_effective_at=AT) -> EvidentiaryState:
    assurance = State(
        state_id="evidence-X",
        properties={"evidence": AssuranceState.VALID},
        context=AssuranceContext(at=state_at),
        rule=RuleBinding(
            rule_id="rule-inference-v1",
            version="1.0",
            authority="temporal-regression",
            effective_at=rule_effective_at,
        ),
    )
    return EvidentiaryState(
        state_id="state-X",
        proposition="X",
        assurance_state=assurance,
    )


def test_future_effective_rule_cannot_justify_earlier_epistemic_state():
    report = inspect_state(
        _state(rule_effective_at=AT + timedelta(seconds=1))
    )
    assert "RULE_NOT_YET_EFFECTIVE" in report.structural_issues


def test_rule_effective_at_state_time_is_admissible():
    report = inspect_state(_state(rule_effective_at=AT))
    assert "RULE_NOT_YET_EFFECTIVE" not in report.structural_issues
    assert "RULE_EFFECTIVE_TIME_UNCOMPARABLE" not in report.structural_issues
    assert "STATE_TIME_UNCOMPARABLE_FOR_RULE" not in report.structural_issues


def test_naive_rule_effective_time_does_not_get_silently_compared():
    naive_rule_time = datetime(2026, 9, 6, 20, 56)
    report = inspect_state(_state(rule_effective_at=naive_rule_time))
    assert "RULE_EFFECTIVE_TIME_UNCOMPARABLE" in report.structural_issues
    assert "RULE_NOT_YET_EFFECTIVE" not in report.structural_issues


def test_missing_state_time_preserves_temporal_uncertainty():
    report = inspect_state(_state(state_at=None, rule_effective_at=AT))
    assert "STATE_TIME_UNCOMPARABLE_FOR_RULE" in report.structural_issues
    assert "RULE_NOT_YET_EFFECTIVE" not in report.structural_issues
