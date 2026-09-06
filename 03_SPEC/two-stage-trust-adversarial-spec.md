# Two-Stage Trust Adversarial Specification

**Status:** UNDER ATTACK

## Object model

A research case contains: question, evidence, assumptions, derivations, constraints, candidate answers, discriminators, provenance links, invalidations, dependencies, and action-policy references.

## Invariants

- A constraint MUST identify its supporting premises and derivation.
- A derived constraint MUST NOT be relabeled as evidence without new evidence.
- A discriminator MUST specify which alternatives it can distinguish.
- A discriminator MUST NOT be treated as a prediction of its outcome.
- UNKNOWN and DEFER MUST remain available when resolution is unavailable or unauthorized.
- Invalidated premises MUST propagate invalidation to dependent conclusions.
- A singleton answer-space is not automatically proof of the remaining answer unless exclusion of all alternatives is itself validly established.
- No research artifact authorizes an action merely by narrowing an answer-space.

## Attack classes

A conforming implementation should be challenged with: poisoned premises, false exclusions, circular dependencies, leaked expectations, incomplete discriminators, competing discriminators, non-monotonic constraints, stale provenance, and computationally discovered consequences.

## Acceptance criterion

The model is not considered architecture-ready until each attack has an explicit expected behavior and no unresolved trust-boundary ambiguity remains material to the proposed use.
