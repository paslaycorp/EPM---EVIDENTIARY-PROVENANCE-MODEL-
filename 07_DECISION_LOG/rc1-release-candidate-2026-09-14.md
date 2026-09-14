# EPM v0.1.0rc1 — Release Candidate Decision Record

**Date:** 2026-09-14  
**Decision:** Advance vNext to release-candidate merge boundary after standalone certification, FAP extraction, and staging validation.  
**Historical baseline:** EPM v0.2 closure remains frozen and unchanged.

## Frozen executable inputs

### Standalone EPM

- tested package commit: `dc08ad7454c31a4a8fb804a37597569d03d3ea5e`
- frozen branch: `rc/epm-engine-v0.1`
- package: `epm-evidentiary-provenance-model==0.1.0rc1`
- engine identifier: `epm-engine/0.1.0-rc1`
- EPM Runtime CI #6 / run `34798881500`: SUCCESS
- Python 3.12: PASS
- Python 3.13: PASS
- lint / compile / public import / certification / distribution build: PASS

### FAP-Insurance adapter host

- tested FAP commit: `7df323a9d910403c50923e9e736c8228717fe7c9`
- frozen branch: `rc/epm-engine-v0.1`
- EPM dependency pinned to exact package commit `dc08ad7454c31a4a8fb804a37597569d03d3ea5e`
- Production Verification #85 / run `34799199150`: SUCCESS
- FAP-Insurance CI/CD #205 / run `34799199254`: SUCCESS
- standalone site-packages import proof: PASS
- EPM semantic gate through external package: PASS
- full FAP regression: PASS

## Extraction decision

Generic EPM semantics are no longer owned by FAP-Insurance.

The standalone EPM package owns:

- assurance primitives and transition evaluation;
- Governor mapping;
- generic evidentiary envelope;
- source typing;
- trusted temporal-availability semantics;
- constraints;
- answer-space resolution and closure;
- justification/dependency graph;
- aggregate evidentiary state;
- deterministic operator audit artifacts;
- bounded trusted-availability connector contract;
- reference domain adapters.

FAP-Insurance owns only FAP translation/compatibility behavior. Historical top-level `epm_*` imports are thin shims into the pinned package to avoid breaking existing consumers during the RC transition.

## C-21 decision

RC1 adds a real bounded connector for GitHub Actions workflow-run availability provenance. It accepts only identity-matched GitHub REST workflow-run receipts obtained over a verified HTTPS integration path with timezone-aware and internally consistent timestamps.

This moves C-21 from a purely abstract engine capability to:

**ENGINE + BOUNDED CONNECTOR PRESENT / FAP PRODUCTION INTEGRATION EXCLUDED**

The connector is intentionally not used to manufacture claim/media evidence availability. Production FAP still requires a domain-appropriate trusted source for when claim evidence actually became available to the relevant epistemic state.

## Staging deployment decision

A separate Render service was created:

- name: `fap-epm-rc1-staging`
- service id: `srv-dajln7e7bikc73cib9s0`
- branch: `rc/epm-engine-v0.1`
- auto-deploy: disabled
- region: Virginia
- FAP commit: `7df323a9d910403c50923e9e736c8228717fe7c9`

### Failed deployment preserved

Deploy `dep-dajln867bikc73cibbp0` failed because Render selected Python 3.14.3. `pydantic-core==2.33.0` therefore fell back to a Rust source build and Cargo could not write its registry cache in the build environment.

This was classified as a deployment-runtime mismatch, not an application semantic defect.

### Remediation

The staging service was pinned to `PYTHON_VERSION=3.12.14`, matching the certified CI runtime. No application code was altered for this remediation.

### Successful deployment

Deploy `dep-dajlnh7qj5pc73e4i8qg` reached `live`.

Build/runtime evidence includes:

- Python 3.12-compatible wheels resolved;
- standalone EPM `0.1.0rc1` wheel built and installed;
- build completed successfully;
- Uvicorn started;
- FastAPI application startup completed;
- Render marked the service live.

No production API secret was copied into staging.

## Audit artifact decision

RC1 audit output is intentionally multi-dimensional. It does not collapse provenance, source origin, temporal status, constraints, answer-space state, graph integrity, limitations, and transition assurance into a single score.

Audit issue time is supplied explicitly and must be timezone-aware, preserving reproducibility and avoiding hidden current-time injection.

## Reference-adapter decision

Insurance, legal, and scientific adapters are included as reference translations, not new policy engines. All adapters fail on absent material context rather than inventing context equivalence.

## Release-candidate merge rule

The tested package commit and tested FAP commit are retained as immutable RC branches even after PR merge. FAP remains pinned to the tested EPM package commit rather than an untested merge commit.

Production promotion is not part of this decision. The existing production FAP-Insurance service remains untouched.

## Exclusions

- TVC remains parked.
- Variant Hunter remains parked.
- FAP production C-21 remains excluded.
- Existing production endpoints are not repointed by this RC decision.
