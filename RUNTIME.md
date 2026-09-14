# EPM Runtime — v0.1.1

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

Accordingly, EPM v0.1.1 supplies the generic temporal machinery and reference connector contract; production adapters remain responsible for supplying trustworthy, correctly bounded availability provenance.

### Rule-time admissibility

An epistemic state may not rely on a governing rule that was not yet effective at that state's historical time.

`inspect_state(...)` therefore reports:

- `RULE_NOT_YET_EFFECTIVE` when `RuleBinding.effective_at` is later than `AssuranceContext.at`;
- `RULE_EFFECTIVE_TIME_UNCOMPARABLE` when the supplied rule-effective time cannot be safely compared;
- `STATE_TIME_UNCOMPARABLE_FOR_RULE` when a rule-effective time exists but the epistemic-state time is absent or uncomparable.

The runtime preserves temporal uncertainty rather than guessing when the two times cannot be legitimately ordered.

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
- Material context changes require valid preservation or fail closed.
- Unsupported/invalidated constraints do not keep narrowing the answer space.
- A singleton produced by constraints is not resolution.
- Computation is not observation.
- A discriminator is not its outcome.
- Circular/shared-origin support does not become independent corroboration.
- Dependency invalidation propagates downstream.
- A future-effective rule cannot justify an earlier epistemic state.
- State inspection and a clean graph do not grant authorization.

## Release boundary

`0.1.1` is a bounded corrective release over the frozen `0.1.0` standalone runtime.

The corrective semantic change is narrow: state inspection now enforces the already represented relationship between rule effective time and epistemic-state time. This closes an executable temporal-admissibility defect discovered by the isolated TVC falsification experiment. It does not merge TVC, change the epistemic ladder, alter answer-space semantics, or add a new authorization rule.

Production C-21 remains connector-scoped. The FAP production integration closes the authenticated request-receipt availability boundary, while media-origin or pre-receipt existence still requires an independent provenance source if a caller needs to make that stronger claim.

TVC and Variant Hunter are not part of EPM v0.1.1.
