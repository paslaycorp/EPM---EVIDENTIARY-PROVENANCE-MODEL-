from datetime import UTC, datetime

from epm import (
    AssuranceContext,
    AssuranceState,
    EvidentiaryState,
    RuleBinding,
    State,
    inspect_state,
)


def run_example():
    state_at = datetime(2026, 9, 14, 15, 0, tzinfo=UTC)
    rule_effective_at = datetime(2026, 9, 14, 18, 0, tzinfo=UTC)

    assurance_state = State(
        "evidence-1",
        {"applicability": AssuranceState.PRESERVED},
        AssuranceContext("record-1", "review", "record", "US-TX", state_at),
        RuleBinding(
            "review-rule",
            "2",
            "review-authority",
            "US-TX",
            rule_effective_at,
        ),
    )

    state = EvidentiaryState(
        state_id="state-1",
        proposition="Evidence is evaluated under the declared review rule.",
        assurance_state=assurance_state,
    )

    return inspect_state(state)


if __name__ == "__main__":
    report = run_example()
    print(report.structural_issues)
