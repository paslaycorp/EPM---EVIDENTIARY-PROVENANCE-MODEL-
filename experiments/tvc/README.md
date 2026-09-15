# Temporal Verification Closure v0.1 — Experimental Verifier

**Status:** experimental / falsification target  
**Boundary:** outside the EPM runtime package and outside the frozen EPM baseline  
**Purpose:** determine whether conclusion-conditioned temporal closure produces incremental assurance beyond existing EPM inspection semantics.

## Kernel under test

TVC v0.1 evaluates this cycle:

```text
asserted epistemic standing
  -> derive obligations intrinsic to that standing
  -> validate each obligation at the claimed historical boundary
  -> preserve failed and unresolved obligations
  -> construct the admissible obligation set
  -> forward re-verify the proposition
  -> compare reproduced standing with asserted standing
  -> CLOSED / DEGRADED / FAILED / UNRESOLVED
```

The candidate technical distinction is the **conclusion-conditioned closure cycle as a composition**, not timestamps, provenance, replay, dependency graphs, truth maintenance, reverse reasoning, or model checking individually.

## Non-claims

This experiment does not claim novelty, patentability, production readiness, or inclusion in normative EPM.

It does not authorize state transitions and does not rewrite EPM state. TVC emits an assurance result for a caller or governor to interpret.

## v0.1 operations

- `derive_obligations()`
- `validate_historical_obligations()`
- `evaluate_closure()`
- caller-supplied forward `reverify()` operation

## Initial falsification probes

1. Full historical obligation set reproduces the asserted standing -> `CLOSED`.
2. An inferential relation exists only after the claimed historical boundary -> `FAILED`; reproduced state is weaker.
3. A material status obligation remains unresolved -> `UNRESOLVED`; no silent promotion.
4. A control condition with no ordinary structural/provenance/time defect is compared with TVC detection to expose a candidate incremental assurance delta.

## Acceptance gate

TVC earns further integration work only if executable tests demonstrate a material integrity failure that:

1. is not already detected by the EPM runtime under equivalent information;
2. is not created by giving TVC information withheld from the control;
3. is reproducible;
4. does not require silent assumption promotion; and
5. produces an actionable closure boundary or status degradation.

If the incremental assurance delta is zero across meaningful adversarial cases, TVC should remain research-only or be discarded rather than merged into EPM.
