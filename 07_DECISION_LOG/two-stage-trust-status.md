# EPM Research Decision Log

**Decision:** KEEP / ISOLATE / ATTACK / FORMALIZE / THEN CONSIDER INTEGRATION

**Current status:** HIGH-VALUE ARCHITECTURAL HYPOTHESIS; NOT ARCHITECTURE-COMMITTED.

## Decision basis

The two-stage distinction is useful because it separates narrowing an unresolved space from establishing its actual answer. It also creates a useful trust boundary around computation, provenance, and prediction.

## Conditions before integration

1. All core adversarial tests have explicit pass criteria.
2. Counterexamples are represented without ambiguity.
3. Constraint provenance is machine-trackable in any eventual implementation.
4. UNKNOWN/DEFER behavior remains safe under narrowing.
5. No new enum or epistemic rung is introduced solely to accommodate the hypothesis.
6. Authorization remains governed independently.

## Reopen triggers

Reopen this decision if a counterexample demonstrates that constrained answer-space cannot be kept epistemically distinct, or if a simpler model explains the same behavior without the proposed two-stage distinction.
