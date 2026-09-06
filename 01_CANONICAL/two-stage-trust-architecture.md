# Two-Stage Trust Architecture

**Status:** PROVISIONAL

## 1. Purpose

This document defines the current EPM research hypothesis that trust work may be separated into two logically different activities:

1. constraining the set of answers still admissible; and
2. resolving which admissible answer is actually true.

The distinction is useful only if it prevents premature conversion of a derived constraint into evidence, inference, prediction, or authorization.

## 2. Core model

Given evidence set E, a question Q, a candidate answer domain A, and a set of valid constraints C:

`A_C = {a in A | a satisfies every valid constraint in C}`

Stage 1 may establish properties of `A_C` without establishing any particular `a` as the answer.

Stage 2 introduces new information capable of discriminating among members of `A_C` and may then resolve the answer.

## 3. Epistemic separation

The working ladder remains:

`OBSERVED -> EVIDENCED -> DERIVED -> INFERRED -> PREDICTED`

Constrained answer-space is not automatically a sixth rung. It is currently treated as an orthogonal object whose provenance must identify what generated the constraint.

## 4. Trust boundary

More computation over the same evidence does not, by itself, create a new external epistemic fact. Computation may reveal a logical consequence already entailed by the evidence; that consequence remains derived unless new evidence enters the system.

## 5. Authorization boundary

A narrowed answer-space is not authorization to act. Any action decision requires an independently defined policy and an appropriate epistemic basis.

## 6. Revision

Constraints may be invalidated, weakened, strengthened, or replaced when their supporting evidence, assumptions, logic, or dependency graph changes. A downstream conclusion must not outlive a broken provenance chain.

## 7. Research questions

- When is a constraint genuinely entailed?
- What makes a discriminator sufficient?
- Can multiple independent discriminators coexist?
- How should UNKNOWN and DEFER interact with constrained spaces?
- What prevents adversarial narrowing?
- When does computational discovery remain derivation rather than evidence?
- How should invalidation propagate through dependencies?
