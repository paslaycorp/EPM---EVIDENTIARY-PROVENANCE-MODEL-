# EPM ↔ FAP Assurance Contract v1

Contract identifier: `epm-fap-assurance/1.0`

## Purpose

This contract defines the narrow interoperability boundary between the Evidentiary Provenance Model (EPM) and FAP implementations. It absorbs shared assurance invariants into EPM without absorbing FAP product code, domain logic, deployment configuration, authentication, scoring, or orchestration.

EPM owns the meaning of assurance state, preservation, material transition, temporal admissibility, authority, rule binding, failure codes, fail-closed behavior, and decision receipts. FAP components own observation, verification, domain translation, authenticated ingress, and product execution.

## Roles

- **EPM** is the constitutional assurance kernel. It determines what a transition is entitled to conclude from the supplied typed state and evidence.
- **FAP-Core** is an evidence-producing execution component. It may emit an EPM-FAP Evidence Receipt describing what it observed or verified. A FAP score or verdict is not itself an EPM assurance decision.
- **FAP-Insurance** is a domain adapter and operational consumer. It binds insurance context to EPM inputs, performs legitimate ingress validation, invokes EPM, and consumes EPM Decision Receipts.

No component may silently inherit another component's authority.

## Canonical artifacts

### Evidence Receipt

Schema: `schemas/epm-fap-evidence-receipt-v1.schema.json`

An Evidence Receipt records bounded facts about evidence availability, provenance, attestation, producing component, and an ingestion-boundary validation result. It is not a truth certificate and does not authorize a transition.

### Decision Receipt

Schema: `schemas/epm-fap-decision-receipt-v1.schema.json`

A Decision Receipt records the exact EPM engine identity, exact EPM release commit, transition, assurance state, decision, failure code, rule binding, evidence references, and fail-closed status used for an evaluation.

## Mandatory invariants

1. **Raw input cannot self-authorize boundary trust.** A `boundary_validation.validated` value is authoritative only when produced or verified by the trusted ingestion adapter. Copying a field from an untrusted payload is not validation.
2. **Internal proof validity and boundary validation are independent.** `PreservationProof.valid=True` cannot substitute for a legitimate ingestion-boundary trust decision.
3. **Exact runtime provenance is mandatory.** A Decision Receipt identifies the exact EPM engine version and 40-character EPM release commit SHA used for the evaluation.
4. **Uncertainty is conserved.** `UNKNOWN` and `DEFER` must not be promoted merely because a FAP score, confidence value, or verdict is strong.
5. **FAP scores are observations, not EPM authority.** A score or verdict may contribute evidence but cannot by itself establish preservation, applicability, authority, temporal admissibility, or permission.
6. **Material transitions remain EPM-governed.** Identity, purpose, scope, jurisdiction, temporal context, and rule-binding changes cannot be made non-material by caller omission.
7. **Temporal comparison must be typed and comparable.** Incomparable or untrusted time evidence remains unresolved/fail-closed rather than raising or silently ordering values.
8. **Decision receipts are non-destructive.** A downstream consumer may add domain execution metadata but may not rewrite the EPM state, decision, failure, rule binding, engine identity, or release SHA represented by the receipt.
9. **Authority diagnostics retain precedence.** A wrong preservation authority remains `AUTHORITY_MISMATCH`; boundary validation must not conceal the authority failure.
10. **No cross-component trust by naming.** A component name, repository name, network location, or possession of a schema-conforming object is not proof of authority.

## Boundary-validation rule

External or raw preservation data enters FAP as untrusted. Translation into an EPM `PreservationProof` MUST set `boundary_validated=False` unless a trusted adapter has independently completed its legitimate validation procedure. An untrusted payload field such as:

```json
{"boundary_validated": true}
```

MUST NOT cause the resulting typed proof to become boundary validated.

Trusted in-process code may construct a typed `PreservationProof(boundary_validated=True)` only after the validating component can identify the validation authority, method, basis, and associated evidence.

## Release binding

Consumers that execute EPM MUST pin an exact EPM release commit. Branch names, floating tags, `main`, version ranges, and unverified local copies are insufficient for production release evidence.

During release-candidate testing, a consumer may temporarily pin an exact RC commit if the branch and pull request are explicitly marked non-production. Before production merge, that pin MUST be replaced by the exact certified EPM release SHA and the consumer's complete CI and release-verification chain MUST be rerun.

## Non-claims

This contract does not establish universal truth, universal external-proof authenticity, media origin, legal admissibility, or correctness of a FAP domain model. It specifies what must be preserved and proven at the interoperability boundary.

## Ownership boundary

EPM does **not** absorb FAP API endpoints, insurance rules, Render deployment configuration, API-key handling, request authentication, oracle implementations, scoring algorithms, or product orchestration. Those remain FAP responsibilities.
