# EPM Runtime — v0.1.2

## Purpose

This package is the independent, domain-neutral runtime for the Evidentiary Provenance Model (EPM).

It enforces a narrow proposition: evidence, conclusions, and downstream uses must not gain certainty, applicability, or authority merely because they crossed a system boundary or were processed by additional computation.

## Public surface

```python
from epm import assess_transition, inspect_state, audit_state
```

The runtime exposes typed models for assurance context, rule binding, evidentiary envelopes, source typing, temporal availability, constraints, answer-space state, justification graphs, and audit artifacts.

There is deliberately no universal truth score.

## Separation from FAP

FAP-Insurance is a domain adapter/client. It is not the semantic definition of EPM.

The independent package contains no claim-specific request model, policy number, adjuster field, fraud score, media URL, weather oracle, or insurance endpoint contract.

Reference adapters are provided for:

- insurance evidence use;
- legal/evidentiary use;
- scientific evidence reuse.

They translate domain vocabulary into the same generic EPM envelope and do not change the engine's invariants.

## Trusted evidence availability

EPM never equates capture time, claimed event time, request receipt time, or processing time with one another by implication.

`EvidenceAvailability` must be created by a provenance-bearing integration path whose claim is explicitly bounded.

The standalone runtime includes a GitHub Actions workflow-run receipt connector. It accepts only a bounded receipt whose repository/run identity matches an `https://api.github.com/repos/<owner>/<repo>/actions/runs/<id>` source, whose transport is declared verified, and whose timestamps are timezone-aware and internally ordered.

That connector establishes availability only inside the bounded GitHub Actions integration. It does **not** make GitHub a universal time authority.

FAP-Insurance separately implements a production request-receipt connector at its domain boundary. That integration attests only that an authenticated FAP request contained an exact SHA-256 evidence reference at the server receipt time. It does not backdate availability to the claimed capture/event time and does not prove external media existence before FAP observed the reference.

Accordingly, EPM v0.1.2 supplies the generic temporal machinery and reference connector contract; production adapters remain responsible for supplying trustworthy, correctly bounded availability provenance.

### Rule-time admissibility

An epistemic state may not rely on a governing rule that was not yet effective at that state's historical time.

`inspect_state(...)` reports:

- `RULE_NOT_YET_EFFECTIVE` when `RuleBinding.effective_at` is later than `AssuranceContext.at`;
- `RULE_EFFECTIVE_TIME_UNCOMPARABLE` when the supplied rule-effective time cannot be safely compared;
- `STATE_TIME_UNCOMPARABLE_FOR_RULE` when a rule-effective time exists but the epistemic-state time is absent or uncomparable.

The transition path also refuses to treat incomparable rule/state timestamps as a valid preservation relation. Mixed timezone-aware and timezone-naive values must not escape as an unhandled comparison exception.

### Availability-time comparability

Evidence-availability trust is evaluated only after both `available_at` and `observed_at` are confirmed timezone-aware. An uncomparable availability record is reported as untrusted/unknown rather than raising during timestamp ordering.

## Materiality and preservation boundaries

For the `applicability` property, EPM no longer relies exclusively on the caller's `material_properties` declaration. A change in identity, purpose, scope, jurisdiction, temporal context, or governing rule is itself sufficient to make the transition material.

`PreservationProof` also carries an explicit `boundary_validated` state. A proof may be internally well-formed (`valid=True`) while still being ineligible to authorize a material transition because an ingestion boundary did not validate it. Adapters accepting untrusted external proof claims are responsible for marking those claims unvalidated until their own trust procedure succeeds.

The typed low-level API preserves backward compatibility for already trusted in-process `PreservationProof` construction. External/raw input must not acquire trusted proof status merely by copying matching metadata into a proof-shaped object.

## Operator audit artifact

`audit_state(...)` emits a deterministic, human-readable record containing:

- structural issues;
- source typing results;
- temporal availability state and provenance;
- constraint validity;
- answer-space/resolution state;
- dependency-cycle state;
- limitations;
- unresolved conditions;
- optional transition assurance and authorization boundary.

The caller supplies the audit issue time explicitly. EPM does not inject an untracked current timestamp into an otherwise reproducible report.

## Failure behavior

- UNKNOWN remains UNKNOWN/DEFER when required assurance is absent.
- Material applicability changes are derived from the actual transition context even when the caller under-declares materiality.
- Material context changes require valid preservation or fail closed.
- Unvalidated preservation claims do not authorize material transitions.
- Incomparable rule/state timestamps do not escape as Python comparison failures.
- Incomparable evidence-availability timestamps remain untrusted/unknown.
- Unsupported/invalidated constraints do not keep narrowing the answer space.
- A singleton produced by constraints is not resolution.
- Computation is not observation.
- A discriminator is not its outcome.
- Circular/shared-origin support does not become independent corroboration.
- Dependency invalidation propagates downstream.
- A future-effective rule cannot justify an earlier epistemic state.
- State inspection and a clean graph do not grant authorization.

## Release boundary

`0.1.2` is a bounded corrective release candidate over `0.1.1`.

The corrective scope is limited to four executable limit findings discovered by adversarial use of the public runtime:

1. caller under-declaration of material applicability could authorize a context-changing transition;
2. mixed timezone-aware/timezone-naive rule and state timestamps could raise during preservation evaluation;
3. mixed timezone-aware/timezone-naive availability timestamps could raise during trust evaluation;
4. proof-shaped preservation input needed an explicit boundary-validation state distinct from internal proof validity.

The correction does not merge TVC, Variant Hunter, or a new epistemic ladder. It does not claim universal provenance, universal truth determination, or external proof authenticity where no validating integration exists.

Production C-21 remains connector-scoped. FAP production adapters must be tested and repinned to the exact v0.1.2 release commit before the production integration can claim the strengthened boundary behavior.

TVC and Variant Hunter remain outside EPM v0.1.2.
