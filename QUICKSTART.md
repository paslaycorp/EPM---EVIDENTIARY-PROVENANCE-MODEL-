# EPM v0.1.1 — Five-Minute Quickstart

This guide uses the verified EPM v0.1.1 runtime at commit:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

## 1. Install

```bash
python -m pip install "git+https://github.com/paslaycorp/EPM---EVIDENTIARY-PROVENANCE-MODEL-.git@87903f2d53531bf28d97f1271af62b6d9b3e64be"
```

Verify:

```bash
python -c "import epm; print(epm.EPM_ENGINE_VERSION)"
```

Expected:

```text
epm-engine/0.1.1
```

## 2. Evaluate a transition

```python
from datetime import UTC, datetime

from epm import (
    AssuranceContext,
    AssuranceState,
    EvidentiaryEnvelope,
    RuleBinding,
    State,
    assess_transition,
)

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

envelope = EvidentiaryEnvelope(
    transition_id="quickstart-1",
    source=source,
    target=target,
    material_properties=frozenset(),
)

print(assess_transition(envelope))
```

The unchanged context is outside the declared materiality boundary, so the applicability property remains preserved and the decision is `AUTHORIZED`.

## 3. Change the purpose

Change the target context from `review` to `public-disclosure`, mark `applicability` as material, and provide no preservation proof.

EPM will not treat the intact evidence as automatically applicable to that new purpose. The transition is quarantined or denied according to consequence.

That distinction is central:

`valid evidence != valid downstream use`

## 4. Check temporal availability

```python
from datetime import UTC, datetime

from epm import (
    AvailabilityAttestation,
    EvidenceAvailability,
    assess_temporal_availability,
)

state_at = datetime(2026, 9, 14, 15, 0, tzinfo=UTC)
available_at = datetime(2026, 9, 14, 18, 0, tzinfo=UTC)

availability = EvidenceAvailability(
    evidence_id="evidence-1",
    available_at=available_at,
    observed_at=available_at,
    source="trusted-receipt",
    provenance_ref="receipt:1",
    attestation=AvailabilityAttestation(
        "attestation-1",
        "receipt-authority",
        "authenticated-receipt",
        "server-observed receipt",
        True,
    ),
)

result = assess_temporal_availability(
    evidence_id="evidence-1",
    state_at=state_at,
    availability=availability,
)

print(result.status.value)
```

Expected:

```text
UNAVAILABLE
```

Evidence received at 18:00 cannot be silently used in a 15:00 decision state.

## 5. Reject a future-effective rule

EPM v0.1.1 also checks whether the governing rule was actually effective at the historical state time.

If a state is dated 15:00 and its rule becomes effective at 18:00, `inspect_state(...)` reports:

```text
RULE_NOT_YET_EFFECTIVE
```

A later rule does not get silently projected backward onto an earlier state.

## 6. Use a domain adapter

Reference adapters are available under `epm.adapters`:

```python
from epm.adapters import (
    InsuranceEvidenceUse,
    LegalEvidenceUse,
    ScientificEvidenceUse,
)
```

The adapters translate domain vocabulary into the same domain-neutral EPM envelope. They do not redefine the engine's invariants.

## 7. Run the reference examples

```bash
python examples/basic_transition.py
python examples/temporal_availability.py
python examples/future_effective_rule.py
python examples/legal_secondary_use.py
```

## 8. What to test first in your own integration

Before adding confidence scores, heuristics, or workflow automation, try to break these boundaries:

1. reuse valid evidence under a different purpose;
2. cross jurisdictions without preservation;
3. change rule/version without preservation;
4. use evidence before its trusted availability time;
5. apply a rule before its effective time;
6. relabel a computation as an external observation;
7. keep a conclusion alive after its supporting evidence is invalidated.

If an integration can cross one of those boundaries without EPM exposing it, that is a useful defect report.
