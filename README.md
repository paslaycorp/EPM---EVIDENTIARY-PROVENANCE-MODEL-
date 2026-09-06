# EPM---EVIDENTIARY-PROVENANCE-MODEL-
Dpies successor including fap-core, &amp; fap-insurance. 
EPM — Epistemic Trust Architecture

Status: ACTIVE RESEARCH · NOT ARCHITECTURE-COMMITTED

EPM is a research effort into epistemic trust architecture: how systems distinguish what is observed, evidenced, derived, inferred, predicted, unresolved, and authorized for action.

This repository contains working specifications, adversarial tests, counterexamples, and research checkpoints.

«Research before architecture.»

Current Research Area

Two-Stage Trust Architecture — Constrained Future Answer-Space

The current hypothesis investigates a distinction between:

- resolving an answer, and
- resolving the structure of the unresolved answer-space.

Working formulation:

Present constraints → future answer-space

An unresolved answer may have a constrained structure of admissible possibilities without the answer itself being known.

For example:

CURRENT KNOWLEDGE

N1 ... N6
   │
   ▼
Constrain answer space
   │
   ├── X
   └── Y
        │
        ▼
Identify discriminator D


FUTURE RESOLUTION

D
│
├── X
└── Y

Stage 1 does not establish X or Y.

It establishes that the eventual resolution must discriminate within "{X, Y}", and may identify information capable of performing that discrimination.

This is currently a hypothesis, not a committed architecture.

Important Distinctions

The research currently examines four potentially distinct concepts:

1. Resolution — establishing the answer.
2. Constraint resolution — establishing which answers remain admissible.
3. Discriminator identification — establishing what future information could distinguish the remaining alternatives.
4. Prediction — asserting what the eventual answer is likely to be.

The current hypothesis is that constrained answer-space may be orthogonal to the epistemic ladder, rather than another epistemic rung.

OBSERVED
   ↓
EVIDENCED
   ↓
DERIVED
   ↓
INFERRED
   ↓
PREDICTED

A constrained answer-space does not automatically belong on this ladder.

Critical Trust Boundary

A central question is:

same evidence + more computation
        ≠
new epistemic fact

with an important qualification:

computation may expose a consequence
already logically entailed by the evidence
without creating new evidence.

Therefore a derived constraint must not silently become evidence.

Adversarial Research

The current work is intentionally adversarial.

Primary attacks:

1. Constraint entailment
2. Discriminator integrity
3. UNKNOWN / DEFER / Governor interaction

Additional tests include:

- derivation vs. epistemic closure
- multiple discriminators
- constraint failure and revision
- circular resolution
- adversarial narrowing
- constraint monotonicity
- discriminator sufficiency
- discriminator independence
- answer-space granularity
- computational discovery
- provenance continuity
- dependency propagation
- expectation leakage

A proposed distinction should survive adversarial counterexamples before architectural integration is considered.

Non-Claims

This repository does not currently claim that:

- an unresolved answer has been resolved;
- a constraint is evidence;
- additional computation necessarily creates a new epistemic fact;
- a discriminator predicts the answer;
- there is only one valid discriminator;
- constrained answer-space is an EPM state;
- constrained answer-space should become a new enum;
- constrained answer-space should become a new epistemic rung;
- constrained answer-space provides authorization to act.

Repository Structure

01_CANONICAL/
    two-stage-trust-architecture.md

02_HYPOTHESIS/
    constrained-future-answer-space.md

03_SPEC/
    two-stage-trust-adversarial-spec.md

04_TESTS/
    test-derivation-vs-closure.md
    test-constraint-entailment.md
    test-discriminator-integrity.md
    test-multiple-discriminators.md
    test-constraint-failure.md
    test-circular-resolution.md
    test-adversarial-narrowing.md
    test-unknown-defer-governor.md
    test-constraint-monotonicity.md
    test-discriminator-sufficiency.md
    test-discriminator-independence.md
    test-answer-space-granularity.md
    test-computational-discovery.md
    test-provenance-continuity.md
    test-dependency-propagation.md
    test-expectation-leakage.md

05_COUNTEREXAMPLES/
    singleton-answer-space.md
    circular-discriminator.md
    poisoned-constraint.md
    false-narrowing.md
    expected-answer-leakage.md

06_VARIANTS/
    two-stage-basic.md
    two-stage-multiple-discriminators.md
    two-stage-revisable-constraints.md
    two-stage-orthogonal-to-epistemic-ladder.md

07_DECISION_LOG/
    two-stage-trust-status.md

Research Status

Current decision:

KEEP
  ↓
ISOLATE
  ↓
ATTACK
  ↓
FORMALIZE
  ↓
ONLY THEN CONSIDER ARCHITECTURAL INTEGRATION

Current status:

HIGH-VALUE ARCHITECTURAL HYPOTHESIS

Not yet:

- committed architecture
- new enum
- new epistemic rung
- authorization mechanism

Provenance

Research claims concerning earlier EPM artifacts remain provisional until their source files are directly reviewed.

This repository should preserve provenance for:

- evidence
- constraints
- derivations
- discriminators
- invalidations
- revisions
- downstream dependencies
- architectural decisions

License

This project is licensed under the MIT License. See ""LICENSE"" (LICENSE).
