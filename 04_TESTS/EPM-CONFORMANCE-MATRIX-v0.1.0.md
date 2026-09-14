# EPM Conformance Matrix v0.1.0 — Release Record

**Status:** RELEASE GATE GREEN — STANDALONE RUNTIME CERTIFIED, FAP PRODUCTION HARDENED  
**Date:** 2026-09-14  
**Historical baseline:** `04_TESTS/EPM-CONFORMANCE-MATRIX-v0.2.md` remains frozen and unchanged  
**RC evidence record:** `04_TESTS/EPM-VNEXT-CONFORMANCE-MATRIX-v0.1.md` remains preserved as the release-candidate record  
**Standalone package:** `0.1.0` / `epm-engine/0.1.0`  
**Explicit exclusions:** TVC, Variant Hunter, universal media-origin availability claims

## Governing evidence rule

This document records the v0.1.0 release boundary. It does not rewrite the v0.2 historical closure record or the v0.1.0rc1 evidence record.

A capability is marked **PASS** only where executable evidence exists for the claimed boundary. A bounded connector may satisfy an invariant only for the provenance claim that connector can legitimately make.

## Standalone v0.1.0 release evidence

- release-finalization branch: `release/epm-v0.1.0-finalization-2026-09-14`
- tested finalization head: `7bd31f876e0ed2bcc7b837c178861aa49a8025b7`
- EPM Runtime CI #26 — run `34806337856` — **SUCCESS**
- Python 3.12 certification — **PASS**
- Python 3.13 certification — **PASS**
- runtime lint — **PASS**
- certification-test correctness lint — **PASS**
- compile/public import — **PASS**
- certification suite — **PASS**
- wheel/sdist build — **PASS**

Graduation from `0.1.0rc1` to `0.1.0` changes the release/version boundary only. No epistemic ladder, transition rule, temporal rule, constraint rule, resolution rule, or audit rule was added during version graduation.

## FAP production integration evidence

- repository: `paslaycorp/FAP-Insurance`
- production merge commit: `9d3040eabd4079b3d4675e326318819cf14fd9a9`
- pre-merge Production Verification #93 — run `34805838995` — **SUCCESS**
- pre-merge FAP CI/CD #213 — run `34805838855` — **SUCCESS**, including Docker build
- post-merge Production Verification #94 — run `34805991302` — **SUCCESS**
- post-merge FAP CI/CD #214 — run `34805991301` — **SUCCESS**, including Docker build
- Render production deploy: `dep-dajnfie7bikc73coqr50` — **LIVE**
- Render production service: `https://fap-core.onrender.com`
- application startup — **PASS**
- Render readiness HEAD `/` — **200**
- Render readiness GET `/` — **200**

The FAP production connector establishes only that an authenticated FAP request contained an exact SHA-256 evidence reference at the recorded server receipt time. It does not assert that the underlying media existed at the claimed capture time or at any earlier external time.

## Evidence-state vocabulary

- **PASS** — executable evidence demonstrates the invariant in the claimed boundary.
- **PASS — BOUNDED FAP RECEIPT** — executable evidence demonstrates the invariant at the authenticated FAP request-receipt boundary; stronger pre-receipt/media-origin claims remain outside that connector.
- **FAIL** — executable evidence demonstrates a violation.
- **UNVERIFIED** — implementation exists but fresh executable evidence is absent.

## Conformance matrix

| ID | Invariant / failure mode | v0.1.0 executable determination | State |
|---|---|---|---|
| C-01 | Epistemic status conservation | Weaker/unknown source standing cannot be promoted by target request; UNKNOWN remains UNKNOWN/DEFER. | **PASS** |
| C-02 | Provenance continuity | Sources, constraints, temporal attestations, graph relations, transition results, and audit records preserve explicit provenance. | **PASS** |
| C-03 | Adversarial narrowing | Constraints require identified premises, provenance, entailment basis, source reference, and governance state before narrowing. | **PASS** |
| C-04 | Constraint ≠ resolution | Constraint-derived singleton remains `CONSTRAINED`; external observation is required for `RESOLVED`. | **PASS** |
| C-05 | Constraint monotonicity | Invalidated constraints can reopen previously excluded candidates while history remains represented. | **PASS** |
| C-06 | Constraint entailment | Exclusions are ineffective without established entailment and basis. | **PASS** |
| C-07 | Constraint failure preservation | Unknown, invalidated, contradicted, or rejected constraints remain typed and cannot silently continue narrowing. | **PASS** |
| C-08 | Dependency propagation | Invalidation propagates staleness to dependent derivations/claims. | **PASS** |
| C-09 | Derivation ≠ closure | Derivation cannot close an answer space; closure requires legitimate resolution and explicit external basis. | **PASS** |
| C-10 | Discriminator ≠ observation | A discriminator definition remains distinct from an observed discriminator outcome. | **PASS** |
| C-11 | Circular resolution | Cyclic/self-support is rejected or exposed and cannot become independent corroboration. | **PASS** |
| C-12 | Computational discovery ≠ observation | Computational output cannot be relabeled as external observation without new external evidence. | **PASS** |
| C-13 | Answer-space granularity | Candidate universe and granularity remain explicit. | **PASS** |
| C-14 | Authorization separation | State inspection/evidence validity does not silently grant downstream authorization. | **PASS** |
| C-15 | Context preservation | Purpose, scope, jurisdiction, time, rule and authority remain typed transition context. | **PASS** |
| C-16 | Rule/version preservation | Material unpreserved rule/version drift remains detectable and fail-closed. | **PASS** |
| C-17 | Jurisdiction preservation | Material unpreserved jurisdiction crossing remains detectable and fail-closed. | **PASS** |
| C-18 | Temporal preservation | Transition time and evidence-availability time remain separately represented and evaluated. | **PASS** |
| C-19 | UNKNOWN preservation | Missing/untrusted required availability remains UNKNOWN/DEFER rather than being fabricated. | **PASS** |
| C-20 | Epistemic inflation through composition | Aggregate state retains component assessments and does not create a master truth score that overwrites weaker states. | **PASS** |
| C-21 | Temporal non-retroactivity | Standalone typed availability plus FAP authenticated request-receipt provenance prevent a later-observed evidence reference from being used as though FAP possessed it before receipt. Retroactive target times are quarantined/denied; missing required trusted availability fails closed. | **PASS — BOUNDED FAP RECEIPT** |
| C-22 | Provenance tamper visibility / authority | Provenance-bearing semantic/audit records retain authority boundaries and tamper visibility. | **PASS** |
| C-23 | Materiality boundary | Material vs non-material context changes remain explicit and preservation requirements apply only where warranted. | **PASS** |
| C-24 | Misapplication without tampering | Evidence can remain intact while an impermissible purpose/scope/context transition is independently blocked. | **PASS** |

## C-21 boundary statement

The production FAP integration now closes the previously excluded request-receipt portion of C-21:

1. authentication succeeds before the receipt is trusted;
2. an exact SHA-256 evidence reference is required;
3. FAP records a timezone-aware server receipt time;
4. the connector creates a typed `EvidenceAvailability` record whose claim is limited to availability to FAP at receipt;
5. the claimed event/capture time is not substituted for evidence availability;
6. a target epistemic time before the trusted receipt is treated as temporally unavailable;
7. missing/untrusted required availability fails closed;
8. temporal provenance is represented in the audit payload;
9. structured operational telemetry records EPM decision/failure/availability state without producing a truth score.

This does **not** prove that media existed before FAP observed it. A stronger media-origin/pre-receipt claim still requires an independent provenance source capable of making that claim.

## Release claim

> EPM v0.1.0 is an independently installable, domain-neutral evidentiary provenance and transition-assurance engine whose core invariants are executable, whose standalone runtime is certified on Python 3.12 and 3.13, and whose FAP integration demonstrates production enforcement of a bounded authenticated evidence-availability boundary without backdating knowledge.

## Non-claims

This release does not claim:

- universal truth determination;
- universal domain completeness;
- universal media-origin provenance;
- that claimed capture time establishes evidence availability;
- that request receipt proves prior external existence;
- that confidence overrides typed uncertainty;
- TVC implementation/conformance;
- Variant Hunter implementation/conformance.
