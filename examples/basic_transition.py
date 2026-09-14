from datetime import UTC, datetime

from epm import (
    AssuranceContext,
    AssuranceState,
    EvidentiaryEnvelope,
    RuleBinding,
    State,
    assess_transition,
)


def run_example():
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)
    rule = RuleBinding("review-rule", "1", "review-authority", "US-TX", at)
    context = AssuranceContext("record-1", "review", "record", "US-TX", at)

    source = State(
        "evidence-1",
        {"applicability": AssuranceState.PRESERVED},
        context,
        rule,
    )
    target = State(
        "evidence-1:target",
        {"applicability": AssuranceState.PRESERVED},
        context,
        rule,
    )

    return assess_transition(
        EvidentiaryEnvelope(
            transition_id="example:basic",
            source=source,
            target=target,
            material_properties=frozenset(),
        )
    )


if __name__ == "__main__":
    print(run_example())
