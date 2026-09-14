# Justification and Dependency Graph v0.1

**Status:** vNext implementation specification  
**Depends on:** First-Class Constraint Model v0.1, Epistemic Source Typing v0.1, Answer-Space Resolution v0.1  
**Target:** implementation foundation for C-11 and explicit dependency invalidation  
**Historical boundary:** EPM v0.2 closure remains frozen and unchanged

## 1. Purpose

EPM must represent why a claim, constraint, derivation, discriminator, attestation, or decision basis is supported and must detect when supposed corroboration is circular, shared, stale, or invalidated.

The graph records justification. It does not itself authorize an action.

## 2. Node types

The first executable vocabulary is:

- `CLAIM`
- `EVIDENCE`
- `CONSTRAINT`
- `DERIVATION`
- `DISCRIMINATOR`
- `ATTESTATION`
- `DECISION`

A node records its identity, provenance references, external-origin status where applicable, and current dependency status.

## 3. Support edge

All graph edges have the same direction:

`source -> target`

meaning that the source contributes to the justification of the target.

Typed relations include:

- `SUPPORTS`
- `DERIVATION_INPUT`
- `CONSTRAINT_INPUT`
- `DISCRIMINATOR_INPUT`
- `ATTESTS`
- `DECISION_BASIS`

Every edge requires provenance for the asserted dependency relation.

`DECISION_BASIS` means only that the source is part of a recorded basis. It does not mean that the graph grants authorization.

## 4. Circular support

A support edge MUST NOT be accepted if it creates a directed cycle.

The implementation must also be able to inspect a pre-existing/imported graph and report cycles rather than assuming all stored graphs were built through the safe insertion path.

Example prohibited structure:

`Claim A <- Constraint C <- Evidence B <- Claim A`

A node cannot ultimately support itself through any number of intermediate nodes.

## 5. Independent corroboration

Two support paths are independent only when:

1. both legitimately contribute to the same target;
2. neither path contains a cycle;
3. their upstream external-origin root sets are non-empty;
4. the two root sets are disjoint.

Two derivations from the same underlying evidence are correlated support, not independent corroboration.

Two constraints derived from one source are correlated support, even if their immediate node identifiers differ.

## 6. Invalidation propagation

When an upstream node is invalidated, every reachable downstream dependent node must become `STALE` unless it is already in a stronger failure state such as `INVALIDATED` or `CONTRADICTED`.

Invalidation creates a new graph state and an explicit invalidation event; historical graph state is not silently rewritten.

This provides the dependency machinery needed for broken premises or provenance to reopen answer-spaces and invalidate dependent conclusions.

## 7. Node status

The initial runtime statuses are:

- `ACTIVE`
- `STALE`
- `INVALIDATED`
- `CONTRADICTED`

`STALE` means a dependency changed or failed and the node can no longer be treated as current support without re-evaluation.

## 8. Support assessment

A target's support is not established when:

- the target is missing;
- it has no incoming justification edge;
- a cycle reaches or includes the target;
- any upstream dependency is `INVALIDATED`, `CONTRADICTED`, or `STALE`;
- edge provenance is absent.

A clean acyclic support graph can establish a justification relation, but that relation remains separate from epistemic status, applicability, and authorization.

## 9. Adversarial probes

The executable gate MUST demonstrate at least:

1. direct self-support is rejected;
2. multi-node circular support is detected and rejected;
3. an imported cyclic graph is detected;
4. two immediate supports sharing one upstream external source are not independent;
5. two genuinely disjoint external-source paths can be classified independent;
6. invalidating an upstream evidence node marks downstream constraints/claims/decision bases stale;
7. a stale or invalidated path cannot establish current support;
8. a clean justification graph does not itself return an authorization decision.

## 10. Claim boundary

Passing this gate provides executable circular-support and dependency-propagation machinery sufficient for the core C-11 distinction.

It does not claim that every production domain supplies complete justification graphs yet.

It does not change the historical v0.2 closure matrix and does not authorize decisions merely because their graph is acyclic.
