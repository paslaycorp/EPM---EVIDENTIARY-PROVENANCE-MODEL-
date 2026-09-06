# EPM — Evidentiary Provenance Model

**Epistemic Trust Architecture**  
**Status: ACTIVE RESEARCH · NOT ARCHITECTURE-COMMITTED**

EPM is a research program for epistemic trust architecture: how systems distinguish what is observed, evidenced, derived, inferred, predicted, unresolved, constrained, invalidated, and authorized for action.

> **Research before architecture.**

## Current research hypothesis

### Two-Stage Trust Architecture — Constrained Future Answer-Space

The current hypothesis separates:

1. **constraining the answer-space** — establishing which answers remain admissible; and
2. **resolving the answer** — establishing which admissible answer is actually true.

A system may therefore know that the eventual answer lies in `{X, Y}` without knowing whether the answer is X or Y. It may also identify a discriminator capable of resolving that distinction later.

Stage 1 does **not** establish X or Y. It establishes structure around the unresolved question.

## Epistemic ladder

`OBSERVED → EVIDENCED → DERIVED → INFERRED → PREDICTED`

The current research treats constrained answer-space as potentially **orthogonal** to this ladder rather than as a new epistemic rung.

## Critical trust boundary

`same evidence + more computation ≠ new epistemic fact`

Computation may expose a consequence already logically entailed by existing evidence. That consequence can be valuable while remaining a derivation rather than new evidence.

## Adversarial program

The repository now contains a structured research library covering:

- constraint entailment
- derivation vs. epistemic closure
- discriminator integrity and sufficiency
- multiple and dependent discriminators
- constraint failure and revision
- circular resolution
- adversarial narrowing
- UNKNOWN / DEFER / Governor behavior
- answer-space granularity
- computational discovery
- provenance continuity
- dependency propagation
- expectation leakage
- counterexamples and model variants

## Repository map

- `EPM_LIBRARY/` — research-library index and terminology
- `01_CANONICAL/` — canonical architecture hypothesis
- `02_HYPOTHESIS/` — formal hypothesis statement
- `03_SPEC/` — adversarial specification
- `04_TESTS/` — adversarial test suite
- `05_COUNTEREXAMPLES/` — failure cases
- `06_VARIANTS/` — alternative formulations
- `07_DECISION_LOG/` — research decisions and reopen triggers
- `08_GOVERNANCE/` — provenance and change-control rules

## Non-claims

This repository does **not** currently claim that:

- an unresolved answer has been resolved;
- a constraint is evidence;
- computation necessarily creates a new epistemic fact;
- a discriminator predicts its outcome;
- there is only one valid discriminator;
- constrained answer-space is an EPM state or new enum;
- constrained answer-space is a new epistemic rung; or
- constrained answer-space authorizes action.

## Research lifecycle

`KEEP → ISOLATE → ATTACK → FORMALIZE → ONLY THEN CONSIDER ARCHITECTURAL INTEGRATION`

## Provenance

Claims about earlier EPM artifacts remain provisional until their source material is directly reviewed. The research library therefore preserves distinctions among evidence, derivations, constraints, discriminators, invalidations, revisions, dependencies, and architectural decisions.

## License

MIT. See [`LICENSE`](LICENSE).
