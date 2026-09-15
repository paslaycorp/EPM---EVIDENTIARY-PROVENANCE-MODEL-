# EPM Conformance Matrix v0.1.2 — Corrective Limit-Hardening Record

**Status:** RELEASE CANDIDATE — EXECUTABLE GATE GREEN  
**Date:** 2026-09-14 (America/Chicago; CI evidence recorded 2026-09-15 UTC)  
**Predecessor certified release:** `0.1.1` at `87903f2d53531bf28d97f1271af62b6d9b3e64be`  
**Current-main productization base:** `c85504e2d195adeb51a755bae5a91aa8c78f9071`  
**Package candidate:** `0.1.2` / `epm-engine/0.1.2`  
**Scope:** adversarial limit hardening only  
**Explicit exclusions:** TVC, Variant Hunter, universal proof authenticity, universal media-origin availability, universal truth determination

## Falsification evidence

The v0.1.1 certified runtime was copied unchanged to isolated branch `vnext/limit-probes-2026-09-14` and attacked through the public runtime surface.

Falsification commit containing all four probes:

`96d47ceb437926a6dda163eff7dc89a6f5eede87`

EPM Runtime CI run `34928796032` failed on both Python 3.12 and Python 3.13.

The probes demonstrated four bounded failures:

1. **Materiality under-declaration** — a caller could submit a purpose-changing applicability transition with an empty `material_properties` set and receive `AUTHORIZED`.
2. **Rule/state time comparability** — a timezone-naive `RuleBinding.effective_at` compared with a timezone-aware target state time raised `TypeError` during preservation evaluation.
3. **Availability-time comparability** — mixed timezone-naive/timezone-aware `observed_at` and `available_at` values raised `TypeError` during availability trust evaluation.
4. **Preservation boundary state** — proof-shaped input with matching metadata and a non-empty evidence reference had no first-class distinction between internal proof validity and ingestion-boundary validation.

These findings qualify under the EPM freeze rule because they were demonstrated by executable falsification rather than architectural speculation.

## Corrective behavior

The v0.1.2 candidate adds the following bounded corrections:

- Applicability materiality is derived from actual identity, purpose, scope, jurisdiction, temporal-context, and rule-binding changes even when the caller omits the applicability property from `material_properties`.
- Preservation evaluation checks datetime comparability before ordering rule-effective and state timestamps, preventing mixed-aware/naive comparison exceptions from becoming an uncontrolled runtime outcome.
- Availability trust checks timestamp awareness before ordering `observed_at` and `available_at`; incomparable availability records remain untrusted/unknown.
- `PreservationProof` carries explicit `boundary_validated` state. A boundary-unvalidated proof cannot authorize a material transition merely because its fields are internally consistent.
- Wrong-authority preservation proofs retain `AUTHORITY_MISMATCH` diagnostic precedence.

## Corrective execution evidence

The verified fixes were first proven on the isolated falsification branch. The same four-file semantic/test delta was then transplanted onto a fresh release-candidate branch created from current `main`, preserving all post-v0.1.1 productization work.

Release-candidate branch:

`rc/v0.1.2-corrective`

Pre-version-metadata RC head:

`97a12463deb4666b1f9ff87bb0b35cc1b8997c25`

EPM Runtime CI run `34929157287` — **SUCCESS**:

- Python 3.12 — PASS
- Python 3.13 — PASS
- runtime lint — PASS
- public reference-example lint — PASS
- certification-test correctness lint — PASS
- runtime/public-example compile — PASS
- public package import — PASS
- public reference examples — PASS
- certification suite, including all four adversarial limit probes — PASS
- wheel/sdist build — PASS

A final CI run after version and evidence-record insertion is required before merge.

## Conformance delta

The correction strengthens the executable basis for:

- **Boundary preservation** — actual context/rule drift cannot be hidden by caller materiality under-declaration.
- **Conservation of uncertainty** — uncomparable temporal availability remains untrusted rather than escaping through a comparison exception.
- **Temporal integrity / C-18 and C-21 support** — preservation evaluation no longer assumes timestamp comparability.
- **Authority boundary** — preservation validity and boundary validation are represented separately.
- **Adversarial truth** — proof-shaped and declaration-shaped inputs are explicitly tested as hostile or erroneous boundary input.

No claim is made that EPM itself authenticates arbitrary external evidence references. External adapters remain responsible for the trust procedure that can legitimately set `boundary_validated` for externally sourced preservation claims.

## Release claim

> EPM v0.1.2 is a bounded corrective release candidate that closes four executable limit failures in applicability materiality, temporal comparability, availability comparability, and preservation-boundary validation while preserving the v0.1.1 architecture and all post-release productization outside the corrected runtime surface.
