# EPM vNext Executable Engine Gate — 2026-09-14

## Decision

The EPM vNext domain-neutral engine hardening/conformance cycle is complete at the reviewable branch boundary.

This is **not** a merge, release, deployment, or production C-21 declaration.

## Frozen baseline preserved

The following historical baselines were not modified:

- EPM `main`: `cfcd33d26e4ff24b9ec824e43bc47e75310181a1`
- FAP-Insurance `main`: `54d8719875d6945e864c68717c7e5ddfc7ba65b0`
- `04_TESTS/EPM-CONFORMANCE-MATRIX-v0.2.md`

All new work remained on `vnext/generic-evidentiary-envelope-v0.1` branches and draft pull requests.

## Final executable implementation baseline

FAP-Insurance vNext:

- commit: `bd1421c485085adbaf8428c0ca1bfb36f5915313`
- draft PR: `paslaycorp/FAP-Insurance#10`
- Production Verification #83, run `34797796926`: **SUCCESS**
- Production Verification pytest: **151 passed, 1 warning**
- FAP-Insurance CI/CD #203, run `34797797078`: **SUCCESS**

Final CI #203 passed:

- assurance-layer lint
- EPM vNext engine lint
- EPM vNext test correctness lint
- assurance-layer compile
- EPM vNext compile
- public `epm` façade import
- API import
- API health/auth/validation/media/timestamp/witness/verdict/demo checks
- DPIE assurance tests
- DPIE audit tests
- DPIE composition tests
- DPIE FAP-boundary tests
- DPIE red-team tests
- DPIE smoke test
- dedicated EPM vNext semantic gate
- full pytest regression suite

## Implemented vNext semantic layers

1. Generic domain-neutral `EvidentiaryEnvelope`.
2. FAP compatibility translation with the legacy public return contract preserved.
3. Trusted evidence-availability provenance with `AVAILABLE`, `UNAVAILABLE`, and `UNKNOWN`.
4. Epistemic source typing separating observation, derivation, discriminator, constraint, assertion, external attestation, and computational discovery.
5. First-class constraint objects with typed premises, provenance, entailment, assumptions, governance review, exclusions, and immutable revision lineage.
6. Answer-space state machine separating `UNRESOLVED`, `CONSTRAINED`, `RESOLVED`, and `CLOSED` from epistemic standing.
7. Justification/dependency graph with cycle detection, independence analysis, and invalidation propagation.
8. Aggregate domain-neutral `EvidentiaryState`.
9. Stable public `epm` engine façade with no universal truth/confidence score.
10. Cross-domain adversarial execution across seven domain contexts.

## Defects exposed by executable gates

### 1. Legacy return-shape regression

When `assess_fap_transition()` was first routed through the generic envelope evaluator, the native `schema_version` field leaked into the legacy FAP return mapping.

**Disposition:** patched at the compatibility boundary only. Native EPM callers retain `schema_version`; legacy FAP callers retain their historical shape.

### 2. Packaging/lint debt

The stricter vNext CI gate exposed mechanical typing/import issues in new engine modules.

**Disposition:** production EPM modules were normalized to current Python typing/import conventions without weakening semantic tests or changing reason codes/behavior.

### 3. Residual import-order defects

Two final Ruff import-order findings remained in `epm_engine.py` and `epm_state.py`.

**Disposition:** corrected and re-executed.

### 4. Test-lint scope mismatch

The first test-correctness lint configuration selected both `E` and `F` rules. It failed only on historical/test-layout `E501` line-length findings, not undefined names, unused imports, or semantic/test defects.

**Disposition:** test correctness lint was scoped to Pyflakes `F` rules. Engine modules remain under the full Ruff gate. Compile and pytest remain mandatory and both passed.

## Cross-domain gate

The same semantic invariants were executed in insurance, legal, scientific, machine-analysis, financial, compliance, and intelligence contexts without relying on insurance request fields.

The cross-domain gate demonstrated that the new abstractions are not merely renamed claim-processing structures.

## C-21 decision

C-21 is now split deliberately:

- **Generic engine capability:** implemented and tested.
- **FAP production integration:** excluded.

The engine has a typed, provenance-bearing evidence-availability abstraction and preserves missing/untrusted availability as UNKNOWN. Production FAP does not yet supply a trustworthy end-to-end availability record.

No code in this cycle treats `timestamp_claimed`, capture time, request receipt, or processing time as a substitute for trusted evidence availability.

## Claimed boundary

The completed gate supports a **reviewable EPM vNext engine candidate** whose executable behavior includes:

- domain-neutral transition assurance;
- epistemic source preservation;
- uncertainty-preserving temporal availability;
- first-class constraints and entailment;
- constraint/revision/reopening history;
- discriminator-versus-observation separation;
- resolution-versus-closure separation;
- circular-support detection;
- shared-origin versus independent support analysis;
- dependency invalidation propagation;
- cross-domain execution;
- compatibility with the frozen FAP assurance boundary.

## Non-claims

This decision does not authorize or claim:

- merge to `main`;
- production deployment;
- release/version freeze;
- production C-21 conformance;
- TVC integration;
- Variant Hunter integration.

Those remain separate future decisions requiring their own evidence and authorization.