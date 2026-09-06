# EPM Research Library

This directory is the working library for the Evidentiary Provenance Model (EPM) research program.

It is deliberately organized as a research corpus rather than a production SDK. Documents are classified by role so that evidence, hypotheses, specifications, tests, counterexamples, variants, and decisions remain distinguishable.

## Research rule

> Research before architecture.

A document may describe a useful model without thereby committing EPM to an implementation, enum, state machine, or authorization mechanism.

## Status vocabulary

- **PROVISIONAL** — proposed for investigation.
- **UNDER ATTACK** — actively tested against counterexamples.
- **SUPPORTED** — survives the currently recorded tests; not necessarily proven universally.
- **REJECTED** — contradicted by evidence or a decisive counterexample.
- **ARCHITECTURE-CANDIDATE** — eligible for a later implementation decision.
- **ARCHITECTURE-COMMITTED** — explicitly adopted after governance review.

## Provenance rule

Every substantive claim should be traceable to its source, derivation, test, counterexample, or decision. Derived constraints are not evidence merely because they were computed from evidence.
