# Temporal Verification Closure v0.2 — Current-Main Parity Candidate

**Status:** experimental / current-main parity validated  
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

### Integrity repair after the independent PR #31 review

The experimental prospective contract now uses schema
`tvc.prospective-closure/v2`, binding the complete canonical payload before
anchor verification and reconstruction. Closure reporting uses explicit policy
priorities, and parallel graph provenance remains retained and unresolved.
The original review and failing witnesses are preserved under
`review_v2/baseline.json`; the parent `5597b0b` remains the unmodified record.
See [the repair protocol](review_v2/PROTOCOL.md) and
[the repair record](review_v2/REPAIR-RECORD.md). Old prospective digests are not
silently migrated or reissued with historical dates.

The independent controls still reproduce the tested detection behavior.
Integrity repair does not establish an irreducible TVC capability.

This experiment does not claim novelty, patentability, production readiness, or inclusion in normative EPM.

It does not authorize state transitions and does not rewrite EPM state. TVC emits an assurance result for a caller or governor to interpret.

## v0.2 provenance

- current hardened EPM base: `adb1c31cdb428816c95a3cf98c9a4427c13ec482`
- frozen TVC v0.1 provenance head: `3bf03d1df25361941af042cf23a4559cce374fbe`
- initial v0.2 forward-port: `9f823b5f753e4c35e139491e56eaec20b0587501`
- parity CI: EPM Runtime CI run `35519465917`, green on Python 3.12 and 3.13

The v0.2 candidate is a clean forward-port of the isolated TVC experiment onto current hardened EPM `main`. It does not modify `src/epm`, EPM public APIs, the Authority Envelope, the Maturity Boundary, release tags, or production authority.

## Verified current-main delta

Under the shared INFERRED parity fixture, EPM and TVC receive the same historical facts: support, provenance, entailment, the same asserted standing, and the same absence of a contradiction-disposition record.

Current EPM inspection reports no failure on that fixture. TVC derives the contradiction-disposition obligation from the asserted INFERRED standing, preserves the missing disposition as unresolved, returns `UNRESOLVED`, and reproduces only `EVIDENCED`.

This establishes a bounded incremental detection result against the current hardened EPM inspection surface. It does not establish that TVC uses a wholly irreducible primitive: the dynamic-availability parity tests separately demonstrate cases where TVC orchestration can be reproduced from equal-information EPM primitives.

## v0.2 operations

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

TVC earns continued sibling-architecture research only while executable tests demonstrate a material integrity failure that:

1. is not already detected by the EPM runtime under equivalent information;
2. is not created by giving TVC information withheld from the control;
3. is reproducible;
4. does not require silent assumption promotion; and
5. produces an actionable closure boundary or status degradation.

If the incremental assurance delta is zero across meaningful adversarial cases, TVC should remain research-only or be discarded rather than merged into EPM.
