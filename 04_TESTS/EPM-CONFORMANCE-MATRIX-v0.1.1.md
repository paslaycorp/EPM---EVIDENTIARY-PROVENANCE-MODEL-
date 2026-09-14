# EPM Conformance Matrix v0.1.1 — Corrective Release Record

**Status:** CORRECTIVE RELEASE GATE GREEN  
**Date:** 2026-09-14  
**Historical release record:** `04_TESTS/EPM-CONFORMANCE-MATRIX-v0.1.0.md` remains preserved and unchanged  
**Package:** `0.1.1` / `epm-engine/0.1.1`  
**Scope:** temporal rule-validity correction only  
**Explicit exclusions:** TVC, Variant Hunter, universal media-origin availability claims

## Corrective evidence

A falsification probe on the isolated TVC branch demonstrated that EPM v0.1.0 state inspection could accept an epistemic state whose governing `RuleBinding.effective_at` was later than the state's `AssuranceContext.at`.

The defect was corrected in PR #5 and merged to `main` at:

`639a719ac7344605ee536157312130b5888dc189`

Post-fix EPM Runtime CI #34 — run `34808791118` — **SUCCESS**.

The v0.1.1 release candidate head is:

`725d9d776e00b906e863261af15d08208c8fea8c`

EPM Runtime CI #41 — run `34809214688` — **SUCCESS**:

- Python 3.12 — PASS
- Python 3.13 — PASS
- runtime lint — PASS
- certification-test correctness lint — PASS
- compile/public import — PASS
- certification suite — PASS
- wheel/sdist build — PASS

## Corrected invariant

For an epistemic state at `T_state` with governing rule effective time `T_rule`:

- when both times are safely comparable and `T_rule > T_state`, state inspection reports `RULE_NOT_YET_EFFECTIVE`;
- when the rule-effective time cannot be safely compared, inspection reports `RULE_EFFECTIVE_TIME_UNCOMPARABLE`;
- when a rule-effective time exists but the state time cannot be safely compared, inspection reports `STATE_TIME_UNCOMPARABLE_FOR_RULE`;
- uncertainty in temporal comparability is preserved rather than converted into admissibility.

## Regression coverage

The corrective tests lock four boundaries:

1. a future-effective rule cannot justify an earlier epistemic state;
2. a rule effective exactly at the state time remains admissible;
3. a naive/uncomparable rule timestamp is not silently ordered;
4. missing state time preserves the temporal boundary as unresolved/uncomparable.

## Conformance delta

All v0.1.0 PASS determinations remain bounded by their original release record.

The v0.1.1 correction strengthens the executable basis for:

- **C-16 Rule/version preservation** — rule applicability now includes represented effective-time admissibility at state inspection;
- **C-18 Temporal preservation** — governing rule time cannot silently cross the epistemic-state boundary;
- **C-21 Temporal non-retroactivity** — a later-effective rule cannot be used as though it governed an earlier epistemic state.

No other conformance determination is expanded by this patch.

## Non-claims

This corrective release does not establish:

- TVC conformance or promotion;
- historical completeness of justification graphs;
- temporal closure across every graph dependency;
- universal media-origin provenance;
- universal truth determination;
- authority beyond the existing transition/Governor boundary.

## Release claim

> EPM v0.1.1 is a bounded corrective release of the standalone EPM runtime that prevents a future-effective governing rule from silently justifying an earlier epistemic state while preserving uncertainty when rule/state times are not safely comparable.
