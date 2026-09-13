# EPM Conformance Matrix v0.2 — Closure Record

**Status:** CRITICAL GATE CLOSED — FAP/DPIE CONFORMANCE BOUNDARY LOCKABLE  
**Date:** 2026-09-13  
**Supersedes:** `EPM-CONFORMANCE-MATRIX-v0.1.md` for current closure status  
**Scope:** EPM invariants as presently mapped into the FAP-Insurance / DPIE runtime boundary  
**Explicit exclusion:** Temporal Verification Closure (TVC) remains outside this gate and was not modified.

## Governing evidence rule

Repository inspection is implementation evidence, not runtime conformance evidence. A row is marked **PASS** only where the current integrated branch has fresh executable coverage through the claimed implementation boundary. A specification whose required runtime abstraction does not exist in that boundary is marked **NOT IMPLEMENTED / EXCLUDED**, rather than being simulated with a tautological test or by inventing a new subsystem solely to satisfy the matrix.

The current integrated evidence baseline is FAP-Insurance branch `recovery/epm-c21-enforcement`, commit `3fd80d6b2acb5e0bf72860fa46b0b080b4fd9992`:

- Production Verification #61 — **SUCCESS**
- `pytest -q` — **60 passed, 1 warning**
- FAP-Insurance CI/CD #181 — **SUCCESS**

## Evidence-state vocabulary

- **PASS** — fresh executable evidence demonstrates the invariant in the claimed boundary.
- **NOT IMPLEMENTED / EXCLUDED** — the EPM invariant remains normative, but the runtime abstraction or integration required to claim conformance is absent from the present FAP/DPIE boundary. It is intentionally excluded from this implementation claim.
- **FAIL** — executable evidence demonstrates a violation.
- **UNVERIFIED** — implementation exists but fresh executable evidence is absent.

## Conformance matrix

| ID | Invariant / failure mode | Current executable evidence or boundary determination | State | Priority |
|---|---|---|---|---|
| C-01 | Epistemic status conservation | `test_epm_c01_target_cannot_promote_changed_source_without_new_evidence`; exposed `CHANGED → PRESERVED` promotion defect, then remediated by conserving the weaker source state. Re-executed in #61. | **PASS** | Critical |
| C-02 | Provenance continuity | `test_epm_c02_broken_provenance_dependency_is_detected_by_audit_chain`; mutation of stored FAP-Core provenance breaks the recomputed chain. | **PASS** | Critical |
| C-03 | Adversarial narrowing | T-07 requires first-class constraint provenance, entailment, assumptions, and governance review. FAP/DPIE has context-preservation machinery but no general constraint/narrowing object or enforcement contract. | **NOT IMPLEMENTED / EXCLUDED** | Critical |
| C-04 | Constraint ≠ resolution | No first-class answer-space / constrained / resolved state exists in the FAP/DPIE runtime. The prior set-arithmetic sentinel is not implementation evidence. | **NOT IMPLEMENTED / EXCLUDED** | Critical |
| C-05 | Constraint monotonicity | No general constraint engine exists in the present runtime boundary; the EPM specification remains normative. | **NOT IMPLEMENTED / EXCLUDED** | High |
| C-06 | Constraint entailment | No executable constraint-entailment model exists in FAP/DPIE. | **NOT IMPLEMENTED / EXCLUDED** | High |
| C-07 | Constraint failure preservation | No first-class constraint-failure state exists in FAP/DPIE. | **NOT IMPLEMENTED / EXCLUDED** | High |
| C-08 | Dependency propagation | `test_epm_c08_dependency_propagation_is_explicit`; purpose, scope, and jurisdiction mutations propagate into invalidation/quarantine, while unchanged non-material context preserves. | **PASS** | Critical |
| C-09 | Derivation ≠ closure | FAP/DPIE does not model `DERIVED` versus `CLOSED` epistemic states or closure conditions. Computation therefore cannot be claimed conformant to this invariant in this boundary. | **NOT IMPLEMENTED / EXCLUDED** | Critical |
| C-10 | Discriminator ≠ observation | No first-class discriminator/selector versus observation type exists in the FAP/DPIE runtime. The prior dictionary sentinel is not implementation evidence. | **NOT IMPLEMENTED / EXCLUDED** | Critical |
| C-11 | Circular resolution | The present FAP/DPIE boundary has no justification dependency graph or cycle-detection mechanism. Any AKS/EIE adversary remains outside this implementation boundary and requires its own integration gate. | **NOT IMPLEMENTED / EXCLUDED** | Critical |
| C-12 | Computational discovery ≠ observation | FAP/DPIE does not expose explicit computational-discovery versus observation epistemic typing. | **NOT IMPLEMENTED / EXCLUDED** | High |
| C-13 | Answer-space granularity | No answer-space representation/granularity engine exists in the current FAP/DPIE boundary. | **NOT IMPLEMENTED / EXCLUDED** | High |
| C-14 | Authorization separation | Runtime-path probe through `assess_fap_transition()`: strong verification cannot bypass purpose/governance boundaries; invalid preservation fails closed, valid preservation authorizes. | **PASS** | Critical |
| C-15 | Context preservation | Existing assurance/red-team/runtime tests show purpose/scope/jurisdiction changes require preservation and otherwise invalidate/quarantine or deny. | **PASS** | Critical |
| C-16 | Rule/version preservation | `test_wrong_rule_binding_does_not_count_as_preservation`; changed rule binding without matching proof yields `RULE_MISMATCH`. | **PASS** | High |
| C-17 | Jurisdiction preservation | `test_jurisdiction_change_is_not_tampering` and dependency gate; jurisdiction crossing without preservation yields `JURISDICTION_MISMATCH`. | **PASS** | High |
| C-18 | Temporal preservation | `tests/test_epm_c18_runtime.py`; changed temporal context without proof fails closed, explicit preservation permits crossing, unchanged-time control preserves normal behavior. | **PASS** | Critical |
| C-19 | UNKNOWN preservation | `test_runtime_preserves_unknown_as_defer` and local UNKNOWN test; UNKNOWN remains UNKNOWN and produces DEFER rather than fabricated invalidity. | **PASS** | Critical |
| C-20 | Epistemic inflation through composition | `test_epm_c20_individually_valid_components_do_not_authorize_unrelated_composition`; unrelated preserved components produce `UNKNOWN / COMPOSITION_UNRESOLVED / QUARANTINE`. | **PASS** | Critical |
| C-21 | Temporal non-retroactivity | A focused helper gate exists in `assess_fap_transition()` and passes tests when a trusted `evidence_available_at` value is supplied. However the production `VerifyClaimResponse` path currently calls DPIE with only the verdict and supplies neither evidence-availability provenance nor a validated temporal bridge. The helper therefore does not establish end-to-end production conformance. | **NOT IMPLEMENTED / EXCLUDED** | Critical |
| C-22 | Provenance tamper visibility | `test_epm_c22_compromised_chain_cannot_serve_authoritative_record`; tamper first compromises the hash chain, then authoritative audit reads raise `AuditIntegrityError` rather than serving the altered record. | **PASS** | Critical |
| C-23 | Materiality boundary | Existing assurance test proves non-material transitions preserve without unnecessary proof, while declared material transitions require explicit preservation. | **PASS** | High |
| C-24 | Misapplication without tampering | `test_perfect_artifact_can_be_misapplied_without_tampering`; intact evidence used outside its application context becomes `INVALIDATED / MISAPPLICATION` and fails closed. | **PASS** | Critical |

## Closure accounting

### Executably conformant in the current FAP/DPIE boundary

`C-01, C-02, C-08, C-14, C-15, C-16, C-17, C-18, C-19, C-20, C-22, C-23, C-24`

### Normative EPM invariants intentionally outside the present implementation claim

`C-03, C-04, C-05, C-06, C-07, C-09, C-10, C-11, C-12, C-13, C-21`

These exclusions do **not** weaken, remove, or redefine the EPM invariants. They prevent false claims that FAP/DPIE implements semantic or temporal-provenance machinery it does not currently possess. Future implementations of constraint algebra, answer-space resolution, discriminator typing, derivational closure, circular-justification analysis, or evidence-availability provenance must open a new executable conformance gate before those capabilities enter the claimed implementation boundary.

## Defects and boundaries exposed during closure

The gate produced substantive findings rather than merely confirming source structure:

1. **C-01 status conservation:** a non-material transition with a weaker source state could return the stronger target-declared state. The evaluator now conserves the source state and defers.
2. **C-22 tamper authority:** chain corruption was detectable but a corrupted record could still be returned through authoritative audit reads. Audit reads now fail closed on a compromised chain.
3. **C-21 production integration boundary:** a temporal-admissibility helper was added and tested, but the production response path does not provide a trustworthy evidence-availability timestamp or validated bridge. C-21 is therefore explicitly excluded rather than falsely promoted to PASS.
4. **CI authentication:** the broader CI workflow lacked the test API credential used by authenticated contract tests. A CI-only credential was added without weakening production authentication.

## Lock determination

The v0.1 lock rule permits closure when critical items are either:

- **PASS with executable evidence through the claimed boundary**, or
- **NOT IMPLEMENTED and intentionally excluded from the claimed conformance boundary**.

That condition is now satisfied for every critical row in this matrix.

**VERDICT: FAP/DPIE EPM CONFORMANCE BOUNDARY — LOCKABLE.**

This verdict does **not** claim that every normative EPM semantic subsystem has been implemented. It states that the current implementation boundary is explicitly delimited, every implemented critical invariant in that boundary has fresh executable evidence, and unimplemented or unintegrated domains are named rather than silently treated as conformant.

## Preserved exclusions

- **TVC:** outside this gate; untouched.
- **Variant Hunter:** parked; untouched.
- **C-21 production temporal non-retroactivity:** remains outside the claimed implementation boundary until evidence availability has trustworthy provenance and is carried through the actual API path.
- No new constraint engine, answer-space engine, discriminator subsystem, closure engine, circular-justification subsystem, or fabricated temporal source was introduced merely to satisfy this matrix.

## Evidence anchors

- FAP-Insurance PR #9, branch `recovery/epm-c21-enforcement`
- Production Verification #61: 60 passed, 1 warning
- FAP-Insurance CI/CD #181: success
- `tests/test_epm_c01_status_conservation.py`
- `tests/test_dpie_audit_boundary.py`
- `tests/test_epm_c18_runtime.py`
- `tests/test_epm_c22_tamper_authority.py`
- `tests/test_epm_conformance_gate.py`
- `tests/test_dpie_assurance.py`
- `tests/test_dpie_red_team.py`
- `models.VerifyClaimResponse._evaluate_dpie_and_legacy_fields()` — production path currently forwards only the verdict to DPIE

**Version:** v0.2  
**Gate state:** CRITICAL GATE CLOSED / BOUNDARY LOCKABLE  
**TVC:** OUT OF SCOPE
