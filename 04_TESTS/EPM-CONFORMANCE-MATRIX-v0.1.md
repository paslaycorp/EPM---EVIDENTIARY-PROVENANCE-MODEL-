# EPM Conformance Matrix v0.1

**Status:** TESTING GATE — ACTIVE  
**Purpose:** Map EPM invariants to specified attacks, known implementation evidence, executable coverage, expected failure behavior, and current evidence state.  
**Scope:** EPM baseline and its presently identified DPIE/FAP implementation relationships.  
**Exclusion:** Temporal Verification Closure (TVC) is intentionally outside this gate.

## Evidence-state vocabulary

- **PASS** — fresh executable evidence demonstrates the invariant.
- **FAIL** — executable evidence demonstrates a violation.
- **NOT IMPLEMENTED** — the invariant is defined, but the relevant enforcement mechanism is absent.
- **UNVERIFIED** — implementation/specification evidence exists, but fresh executable evidence is not presently available.
- **SPECIFIED** — an adversarial test exists as an EPM specification, but executable conformance has not yet been demonstrated.
- **INTEGRATION REQUIRED** — local mechanisms exist, but cross-boundary behavior has not yet been demonstrated.

> Repository inspection is evidence of implementation structure, not a substitute for executing the tests. No current runtime PASS is asserted unless execution evidence is available.

## Conformance matrix

| ID | EPM invariant / failure mode | Adversarial condition | Existing test/spec | Implementation evidence | Executable gate probe | Expected failure behavior | Current evidence state | Priority |
|---|---|---|---|---|---|---|---|---|
| C-01 | Epistemic status conservation | Legitimate derivation is presented as stronger epistemic status without new evidence | EPM principle; executable test required | DPIE assurance primitives preserve explicit assurance state | `test_epm_c01_status_conservation_blocks_unproved_material_crossing` | Reject/contain status promotion; preserve provenance and justification | **UNVERIFIED RUNTIME / PROBE ADDED** | Critical |
| C-02 | Provenance continuity | Constraint/answer survives after supporting provenance is broken or unavailable | T-14 `test-provenance-continuity.md` | FAP artifact carries provenance hash/audit trail; DPIE preserves explicit provenance dependencies | No implementation-level dependency-break probe yet | Broken/stale dependency must surface; artifact must not remain authoritative | **SPECIFIED / INTEGRATION REQUIRED** | Critical |
| C-03 | Adversarial narrowing | Actor adds constraints to force preferred answer | T-07 `test-adversarial-narrowing.md` | DPIE has explicit applicability/context preservation mechanisms | Semantic sentinel added; implementation probe still required | Preference must not masquerade as valid narrowing | **SPECIFIED / INTEGRATION REQUIRED** | Critical |
| C-04 | Constraint ≠ resolution | Constraint reduces answer space to a candidate without proving exhaustiveness/resolution | T-12 family; constraint tests | EPM decision model distinguishes answer-space constraints from authority | Semantic sentinel added | Result remains constrained, not resolved, absent resolution conditions | **SPECIFIED / PROBE ADDED** | Critical |
| C-05 | Constraint monotonicity | Added constraint causes unsupported strengthening of conclusion | `test-constraint-monotonicity.md` | EPM test specification exists | No implementation probe yet | Narrowing cannot silently increase epistemic authority | **SPECIFIED** | High |
| C-06 | Constraint entailment | Constraint is accepted without declared entailment/premises | `test-constraint-entailment.md` | EPM test specification exists | No implementation probe yet | Unsupported constraint is rejected/deferred | **SPECIFIED** | High |
| C-07 | Constraint failure preservation | Invalid constraint is treated as harmless narrowing | `test-constraint-failure.md` | EPM test specification exists | No implementation probe yet | Failure remains explicit; no derived authority from failed constraint | **SPECIFIED** | High |
| C-08 | Dependency propagation | Derived state loses or obscures dependency chain | `test-dependency-propagation.md` | DPIE `AssuranceProperty.dependencies`; FAP audit/provenance structures | `test_epm_c08_dependency_propagation_is_explicit` | Dependencies propagate or result becomes non-authoritative/deferred | **UNVERIFIED RUNTIME / PROBE ADDED** | Critical |
| C-09 | Derivation ≠ closure | A derivation is treated as proof that the answer space is closed | `test-derivation-vs-closure.md` | EPM derivational model; no single cross-component executable proof yet | No implementation probe yet | Derivation cannot establish closure without closure conditions | **SPECIFIED** | Critical |
| C-10 | Discriminator ≠ observation | A discriminator or selector is treated as direct observation | `test-discriminator-independence.md`; `test-discriminator-integrity.md` | EPM discriminator model/specification | Semantic sentinel added; implementation probe still required | Identification/selection must not promote to observation | **SPECIFIED / PROBE ADDED** | Critical |
| C-11 | Circular resolution | Output used as its own discriminator/justification | `test-circular-resolution.md` | AKS/EIE contains a `JustificationChainAdversary` for circular-justification attacks | No cross-boundary runtime probe yet | Circular support must be detected or quarantined | **INTEGRATION REQUIRED** | Critical |
| C-12 | Computational discovery ≠ observation | Computationally discovered result is represented as an external observation | `test-computational-discovery.md` | EPM specification | No implementation probe yet | Computational discovery retains derivational provenance | **SPECIFIED** | High |
| C-13 | Answer-space granularity | Representation granularity is mistaken for epistemic fact | T-12 `test-answer-space-granularity.md` | EPM test specification | No implementation probe yet | Granularity must be justified by question/evidence | **SPECIFIED** | High |
| C-14 | Authorization separation | Epistemic validity is treated as authorization | EPM Governor/decision model; executable integration test required | DPIE decisions include AUTHORIZED, CONSTRAINED, DEFER, QUARANTINE, DENY | `test_epm_c14_authorization_does_not_follow_epistemic_validity_alone` | Authorization requires explicit governance/authority conditions | **UNVERIFIED RUNTIME / PROBE ADDED** | Critical |
| C-15 | Context preservation | Same evidence crosses purpose/scope/jurisdiction boundary without preservation proof | DPIE assurance tests | `RequestAssuranceContext`; `PreservationProof`; `evaluate_transition()` | Existing DPIE tests + C-01 probe | Material context change without proof → INVALIDATED + QUARANTINE/DENY | **UNVERIFIED RUNTIME** | Critical |
| C-16 | Rule/version preservation | Evidence crosses a changed rule binding without proof | DPIE assurance tests | `RuleBinding`; preservation checks rule id/version/authority | Existing DPIE tests | RULE_MISMATCH; invalidate material transition | **UNVERIFIED RUNTIME** | High |
| C-17 | Jurisdiction preservation | Evidence crosses jurisdiction boundary without explicit determination | DPIE assurance tests | `AssuranceContext.jurisdiction`; preservation checks | Existing DPIE tests | JURISDICTION_MISMATCH; quarantine material transition | **UNVERIFIED RUNTIME** | High |
| C-18 | Temporal preservation | State crosses temporal boundary without valid preservation | DPIE assurance implementation + EPM temporal model | `AssuranceContext.at`; rule effective-time check | `test_epm_c18_temporal_preservation_requires_matching_temporal_context` | TEMPORAL_MISMATCH; no silent temporal carry-forward | **UNVERIFIED RUNTIME / PROBE ADDED** | Critical |
| C-19 | UNKNOWN preservation | Missing/unknown evidence is silently converted to false/invalid | DPIE assurance implementation | Explicit `UNKNOWN` and conservative `DEFER` path | Existing DPIE assurance tests | UNKNOWN remains UNKNOWN; no fabricated invalidity | **UNVERIFIED RUNTIME** | Critical |
| C-20 | Epistemic inflation through composition | Individually valid transformations compose into an unjustified stronger result | EPM core failure-mode definition; executable composition test required | DPIE has `COMPOSITION_UNRESOLVED`; FAP state/provenance transitions | `test_epm_c20_individually_valid_components_do_not_authorize_unrelated_composition` | Composition must preserve or explicitly justify resulting epistemic status | **UNVERIFIED RUNTIME / PROBE ADDED** | **Critical — Gate blocker** |
| C-21 | Temporal non-retroactivity | Evidence available at t2 strengthens what was knowable at t1 | EPM temporal model; executable test required | Temporal evidence model specified; no temporal-availability enforcement in current DPIE API | `test_epm_c21_later_evidence_cannot_strengthen_prior_state_without_temporal_bridge` | Later availability cannot silently rewrite earlier epistemic state | **FAIL EXPECTED / ENFORCEMENT GAP EXPOSED** | **Critical — Gate blocker** |
| C-22 | Provenance tamper visibility | Provenance/hash/audit relationship changes without corresponding state response | FAP artifact provenance/audit implementation | `provenance_hash()`, immutable-style event trail | No implementation-level tamper probe yet | Tamper/broken chain must become detectable and non-authoritative | **INTEGRATION REQUIRED** | Critical |
| C-23 | Materiality boundary | Non-material transition incorrectly treated as requiring/establishing material preservation, or vice versa | DPIE assurance tests | `Materiality`; `is_material()` | Existing DPIE assurance tests | Materiality determines whether explicit preservation proof is required | **UNVERIFIED RUNTIME** | High |
| C-24 | Misapplication without tampering | Perfectly intact artifact is applied outside original purpose/scope | DPIE `perfect_artifact_misapplication_demo()` and assurance tests | `MISAPPLICATION`; INVALIDATED; DENY/QUARANTINE | Existing DPIE assurance tests | Integrity of artifact does not imply applicability in new context | **UNVERIFIED RUNTIME** | Critical |

## Gate blockers

The following items prevent a full EPM lock because they attack the architecture's most consequential seams rather than isolated functions:

1. **C-20 — Epistemic inflation through composition** — executable probe now exists; runtime execution still required.
2. **C-21 — Temporal non-retroactivity** — executable probe now exposes an enforcement gap in the current API design.
3. **C-02 — Provenance continuity across implementation boundaries**
4. **C-08 — Dependency propagation across transformations** — local dependency declaration is present; cross-transformation propagation remains unverified.
5. **C-14 — Authorization separation** — local Governor behavior is testable; runtime evidence remains absent.
6. **C-18 — Temporal preservation** — local temporal boundary exists; availability semantics remain unverified.

## Current gate verdict

**VERDICT: NOT READY TO LOCK — TESTING GATE REMAINS ACTIVE**

The gate has now moved from a purely documentary posture to an executable adversarial probe layer in FAP-Insurance. The new probes deliberately include one expected failure: C-21 demonstrates that the present assurance API has temporal context but does not model evidence availability time or an explicit retrospective bridge. That is a substantive implementation gap, not a test failure to be papered over.

No runtime PASS is claimed because the available environment has not executed the repository's pytest suite. GitHub source inspection confirms the probe and existing implementation structure; it does not substitute for execution.

## Required next execution set

The smallest remaining execution set is:

- `test_epm_c01_status_conservation_blocks_unproved_material_crossing`
- `test_epm_c02` implementation-level constraint/resolution probe
- `test_epm_c08_dependency_propagation_is_explicit`
- `test_epm_c14_authorization_does_not_follow_epistemic_validity_alone`
- `test_epm_c18_temporal_preservation_requires_matching_temporal_context`
- `test_epm_c20_individually_valid_components_do_not_authorize_unrelated_composition`
- `test_epm_c21_later_evidence_cannot_strengthen_prior_state_without_temporal_bridge`
- C-02 provenance continuity probe

Each executable test should record:

`initial_state → transformation(s) → adversarial manipulation → observed state → expected state → decision → reason code → provenance/dependency trace`

## Lock condition

EPM may advance from **TESTING GATE — ACTIVE** only when every critical blocker is either:

- **PASS** with executable evidence, or
- explicitly classified as **NOT IMPLEMENTED** and intentionally excluded from the claimed conformance boundary.

`UNVERIFIED` is not PASS.

`SPECIFIED` is not PASS.

Documentation is not execution evidence.

## Source anchors inspected during matrix construction

- EPM T-07 adversarial narrowing: `04_TESTS/test-adversarial-narrowing.md`
- EPM T-12 answer-space granularity: `04_TESTS/test-answer-space-granularity.md`
- EPM T-14 provenance continuity: `04_TESTS/test-provenance-continuity.md`
- FAP-Insurance DPIE assurance implementation: `dpie_assurance.py`
- FAP-Insurance DPIE composition implementation: `dpie_composition.py`
- FAP-Insurance Governor: `governor.py`
- Previously inspected FAP artifact/provenance implementation: `fap_core/artifact.py`

**Version:** v0.1  
**Gate state:** ACTIVE  
**TVC:** OUT OF SCOPE FOR THIS GATE
