# EPM vNext Conformance Matrix v0.1 — Release Candidate Record

**Status:** RC1 CERTIFIED — STANDALONE PACKAGE GREEN, FAP EXTRACTION GREEN, STAGING LIVE  
**Date:** 2026-09-14  
**Historical baseline:** `04_TESTS/EPM-CONFORMANCE-MATRIX-v0.2.md` remains frozen and unchanged  
**Standalone package version:** `0.1.0rc1` / `epm-engine/0.1.0-rc1`  
**Explicit exclusions:** FAP production C-21 integration, TVC, Variant Hunter, production promotion

## Governing evidence rule

This is a post-v0.2 vNext release-candidate evidence record. It does not rewrite, supersede, backdate, or reinterpret the frozen EPM v0.2 closure matrix.

A capability is marked **PASS** only where executable behavior exists and fresh verification has exercised the claimed boundary. Specification text and repository inspection are not substitutes for runtime evidence.

## Release-candidate evidence baseline

### Standalone EPM package

- repository: `paslaycorp/EPM---EVIDENTIARY-PROVENANCE-MODEL-`
- package RC branch: `rc/epm-engine-v0.1`
- tested/frozen package commit: `dc08ad7454c31a4a8fb804a37597569d03d3ea5e`
- EPM Runtime CI #6 — run `34798881500` — **SUCCESS**
- Python 3.12 certification job — **PASS**
- Python 3.13 certification job — **PASS**
- runtime lint — **PASS**
- test correctness lint — **PASS**
- compile/public import — **PASS**
- adversarial certification suite — **PASS**
- wheel/sdist build — **PASS**

The generic runtime is now packaged under `src/epm` and no longer depends on FAP-Insurance request models.

### FAP-Insurance external-package integration

- repository: `paslaycorp/FAP-Insurance`
- RC branch: `rc/epm-engine-v0.1`
- tested/frozen FAP commit: `7df323a9d910403c50923e9e736c8228717fe7c9`
- standalone EPM dependency is pinned to exact commit `dc08ad7454c31a4a8fb804a37597569d03d3ea5e`
- Production Verification #85 — run `34799199150` — **SUCCESS**
- FAP-Insurance CI/CD #205 — run `34799199254` — **SUCCESS**
- CI explicitly verifies `import epm` resolves from installed site-packages — **PASS**
- legacy API / assurance / audit / composition / boundary / red-team / smoke suites — **PASS**
- EPM semantic gate through external package — **PASS**
- full regression suite — **PASS**

FAP retains only domain translation and compatibility shims for historical import names. Generic EPM semantic ownership resides in the standalone package.

### Staging deployment

- Render service: `fap-epm-rc1-staging`
- service id: `srv-dajln7e7bikc73cib9s0`
- branch: `rc/epm-engine-v0.1`
- deployed FAP commit: `7df323a9d910403c50923e9e736c8228717fe7c9`
- auto-deploy: disabled
- region: Virginia
- runtime pin: Python `3.12.14`
- package installed during build: `epm-evidentiary-provenance-model==0.1.0rc1`
- successful deploy: `dep-dajlnh7qj5pc73e4i8qg` — **LIVE**
- application startup completed under Uvicorn — **PASS**

The first staging build, `dep-dajln867bikc73cibbp0`, failed because Render selected Python 3.14.3 and `pydantic-core==2.33.0` fell back to a Rust source build in a read-only Cargo environment. This deployment defect was preserved in the record. The service was then pinned to the already-certified Python 3.12.14 runtime and redeployed without application-code changes.

No production API secret was copied into the staging service.

## Evidence-state vocabulary

- **PASS** — fresh executable evidence demonstrates the invariant in the claimed RC boundary.
- **ENGINE + BOUNDED CONNECTOR PRESENT / FAP PRODUCTION INTEGRATION EXCLUDED** — the generic engine and a real bounded availability integration exist, but the production FAP domain still lacks trustworthy claim/media availability provenance.
- **FAIL** — executable evidence demonstrates a violation.
- **UNVERIFIED** — implementation exists but fresh executable evidence is absent.

## Conformance matrix

| ID | Invariant / failure mode | RC executable evidence / boundary determination | State |
|---|---|---|---|
| C-01 | Epistemic status conservation | Generic transition evaluation conserves weaker source states; UNKNOWN remains UNKNOWN/DEFER and cannot be promoted by target request. | **PASS** |
| C-02 | Provenance continuity | Provenance-bearing sources, constraints, availability attestations, graph nodes/edges, audit artifacts, and frozen legacy audit behavior remain explicit. | **PASS** |
| C-03 | Adversarial narrowing | Constraints require identified premises, provenance, entailment basis, source reference, and required governance review before exclusions become effective. | **PASS** |
| C-04 | Constraint ≠ resolution | Constraint recomputation may narrow to a singleton while state remains `CONSTRAINED`; Stage 2 external observation is required for `RESOLVED`. | **PASS** |
| C-05 | Constraint monotonicity | Answer-space recomputation starts from the declared universe and valid current constraints; invalidation can reopen alternatives with history preserved. | **PASS** |
| C-06 | Constraint entailment | Candidate exclusions are ineffective without `ESTABLISHED` entailment plus explicit basis. | **PASS** |
| C-07 | Constraint failure preservation | Unknown, invalidated, contradicted, or rejected constraints remain typed and cannot keep stale narrowing active. | **PASS** |
| C-08 | Dependency propagation | Justification invalidation propagates staleness to every reachable dependent; legacy FAP dependency behavior remains green. | **PASS** |
| C-09 | Derivation ≠ closure | Derivation records `DERIVED` standing without resolution/closure; closure requires legitimate resolution, exhaustive-domain basis, external resolution refs, and no material unresolved conditions. | **PASS** |
| C-10 | Discriminator ≠ observation | Discriminator definition/sufficiency is separate from typed external observation. | **PASS** |
| C-11 | Circular resolution | Self-support/cycle-creating edges are rejected; imported cycles remain visible and cannot become independent corroboration. | **PASS** |
| C-12 | Computational discovery ≠ observation | Computational discovery/derivation are explicit source types and cannot be relabeled as observations without new external evidence. | **PASS** |
| C-13 | Answer-space granularity | Answer-space requires explicit granularity and basis; admissible candidates remain within declared universe. | **PASS** |
| C-14 | Authorization separation | Transition assessment and state inspection do not silently grant unrelated authorization; Governor behavior remains explicit. | **PASS** |
| C-15 | Context preservation | Purpose, scope, jurisdiction, time, rule, and authority remain typed transition inputs. | **PASS** |
| C-16 | Rule/version preservation | Unpreserved rule/version drift remains detectable and fail-closed where material. | **PASS** |
| C-17 | Jurisdiction preservation | Jurisdiction crossing without preservation remains detectable and fail-closed where material. | **PASS** |
| C-18 | Temporal preservation | Transition-time preservation remains enforced; typed evidence availability is separately modeled. | **PASS** |
| C-19 | UNKNOWN preservation | Missing/untrusted availability remains UNKNOWN; unknown assurance remains UNKNOWN/DEFER. | **PASS** |
| C-20 | Epistemic inflation through composition | Aggregate state returns component assessments instead of a master truth/confidence score; composition cannot overwrite weaker states. | **PASS** |
| C-21 | Temporal non-retroactivity | `EvidenceAvailability` is implemented. A real GitHub Actions REST connector now creates a validated, provenance-bearing availability record from a matching workflow-run `created_at` obtained over verified HTTPS. The connector rejects wrong host, identity mismatch, unverified transport, naive times, and impossible temporal ordering. This establishes a bounded real connector capability only. FAP production still does not ingest trustworthy claim/media evidence-availability provenance. | **ENGINE + BOUNDED CONNECTOR PRESENT / FAP PRODUCTION INTEGRATION EXCLUDED** |
| C-22 | Provenance tamper visibility / authority | Provenance-bearing semantic records and frozen tamper/audit behavior preserve authority boundaries. | **PASS** |
| C-23 | Materiality boundary | Generic envelope preserves material/non-material distinction and preservation requirement. | **PASS** |
| C-24 | Misapplication without tampering | Purpose/scope/context misuse remains detectable even where underlying evidence itself is intact. | **PASS** |

## Real bounded availability connector

The first concrete trusted-availability integration in RC1 is deliberately narrow: a `GitHubActionsRunReceipt` accepted only when repository/run identity matches an `https://api.github.com/repos/<owner>/<repo>/actions/runs/<id>` source, transport is verified, timestamps are timezone-aware, and observation time is not earlier than server-created time.

The certification suite uses the real FAP Production Verification #83 workflow-run record as one bounded receipt. This proves that EPM can ingest a real external availability provenance source without manufacturing time.

It does **not** establish:

- that GitHub is a universal temporal authority;
- that workflow creation time is media/claim evidence availability;
- that FAP production C-21 is solved;
- that capture time, claimed event time, request receipt time, or processing time can substitute for trusted availability provenance.

## Reference adapters

RC1 includes explicit reference adapters for:

- insurance evidence use;
- legal/evidentiary use;
- scientific evidence reuse.

Each adapter translates domain vocabulary into the same generic EPM envelope and refuses missing material context rather than silently inventing equivalence.

## Operator audit artifact

RC1 emits deterministic operator-facing audit artifacts containing:

- structural issues;
- source typing results;
- temporal availability and provenance;
- constraint status;
- answer-space/resolution state;
- dependency-cycle state;
- limitations;
- unresolved conditions;
- optional transition assurance / decision / failure context.

The audit artifact intentionally contains no universal confidence/truth score and requires an explicit timezone-aware issue time.

## RC1 claimed boundary

> EPM v0.1.0rc1 is an independently installable, domain-neutral evidentiary integrity engine whose transition assurance, source typing, temporal-availability uncertainty, constraint semantics, answer-space resolution boundaries, dependency structure, and audit output have survived standalone certification on Python 3.12/3.13, external-package integration back into FAP-Insurance, full FAP regression, and an isolated staging deployment.

## Non-claims

This record does not claim:

- production FAP C-21 conformance;
- production promotion of the staging RC;
- universal domain completeness;
- that a graph being acyclic authorizes an action;
- that confidence can override typed uncertainty;
- TVC implementation/conformance;
- Variant Hunter implementation/conformance.

The frozen EPM v0.2 historical closure record remains intact.
