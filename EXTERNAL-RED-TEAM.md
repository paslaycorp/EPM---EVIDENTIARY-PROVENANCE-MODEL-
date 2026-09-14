# EPM v0.1.1 — External Red-Team Contract

## Objective

Try to make EPM authorize or accept a state where evidence gains applicability, authority, certainty, or temporal legitimacy that it did not possess.

A useful report demonstrates one of two things:

1. an executable invariant violation; or
2. a materially ambiguous boundary that allows two reasonable integrations to produce incompatible authorization behavior.

Do not report stylistic preferences as semantic defects.

## Frozen target

Standalone EPM release commit:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

Engine identifier:

`epm-engine/0.1.1`

Install:

```bash
python -m pip install "git+https://github.com/paslaycorp/EPM---EVIDENTIARY-PROVENANCE-MODEL-.git@87903f2d53531bf28d97f1271af62b6d9b3e64be"
```

## Primary attack classes

### 1. Purpose/scope laundering

Start with valid evidence under one purpose or scope. Reuse it under a materially different purpose or scope without a valid preservation proof.

Success condition for the attacker:

EPM returns authorization without exposing the material context change.

### 2. Authority laundering

Present a preservation proof issued by an authority that is not bound to the target rule.

Success condition:

EPM treats the proof as sufficient.

### 3. Rule/version laundering

Change the governing rule or version without an explicit preservation determination.

Success condition:

The changed rule binding is silently treated as equivalent.

### 4. Future-rule leakage

Inspect a historical state under a rule whose `effective_at` is later than the state's epistemic time.

Success condition:

The state is accepted without `RULE_NOT_YET_EFFECTIVE` or an equivalent visible failure.

### 5. Jurisdiction laundering

Move evidence across jurisdictions without establishing preservation.

Success condition:

EPM authorizes without exposing the jurisdiction boundary.

### 6. Temporal evidence leakage

Give EPM trustworthy evidence-availability provenance that places evidence after the decision-state time.

Success condition:

The evidence is treated as available to the earlier state.

Do not substitute capture time, claimed event time, EXIF, request receipt, or processing time unless the tested integration explicitly establishes that field as trustworthy availability provenance.

### 7. Unknown inflation

Supply missing, contradictory, or untrusted assurance and attempt to obtain a stronger state through additional computation or downstream composition.

Success condition:

UNKNOWN becomes VALID/PRESERVED/AUTHORIZED without new legitimate evidence or preservation.

### 8. Computation-to-observation laundering

Produce a computational result from existing evidence and relabel it as a new external observation.

Success condition:

The runtime accepts the reclassification without a new external evidentiary source.

### 9. Constraint-to-resolution laundering

Narrow an answer-space, including to a singleton, without an external discriminator observation.

Success condition:

The narrowed state becomes RESOLVED/CLOSED solely because of constraint processing.

### 10. Circular support

Construct a justification cycle or multiple derivations sharing one external origin and attempt to count them as independent corroboration.

Success condition:

Circular/shared-origin support becomes independent evidence.

### 11. Dependency resurrection

Invalidate an upstream evidence node after dependent derivations and conclusions exist.

Success condition:

Dependents remain current without visible staleness/invalidation propagation.

## Required report format

The repository includes a structured GitHub issue form at:

`.github/ISSUE_TEMPLATE/epm-red-team.yml`

A high-quality defect report must include:

- EPM commit SHA;
- Python version;
- attack class;
- minimal executable reproduction;
- exact input state and context;
- expected decision and invariant;
- observed decision or structural result;
- whether the defect is deterministic;
- whether the defect requires malformed input, ambiguous integration semantics, or valid typed input;
- proposed remediation if known.

Reports that cannot identify the tested commit or provide a reproducible input should be treated as hypotheses until reproduced.

## Out of scope

The following are not v0.1.1 defects by themselves:

- absence of a universal truth score;
- absence of universal media-origin time attestation;
- absence of domain-specific policy logic not supplied by an adapter;
- disagreement with the deliberate rule that computation is not observation;
- TVC behavior;
- Variant Hunter behavior.

## Passing outcome

A failed attack is still useful. Record the attempted transition, the decision returned, and the invariant that blocked it.

The purpose of external validation is not to prove EPM infallible. It is to establish whether an independent operator can reproduce, challenge, and meaningfully falsify the release boundary.
