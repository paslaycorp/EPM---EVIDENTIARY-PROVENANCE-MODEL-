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

| ID | EPM invariant / failure mode | Adversarial condition | Existing test/spec | Implementation evidence | Expected failure behavior | Current evidence state | Priority |
|---|---|---|---|---|---|---|---|
| C-01 | Epistemic status conservation | Legitimate derivation is presented as stronger epistemic status without new evidence | EPM principle; executable test required | DPIE assurance primitives preserve explicit assurance state | Reject/contain status promotion; preserve provenance and justification | **INTEGRATION REQUIRED** | Critical |
| C-02 | Provenance continuity | Constraint/answer survives after supporting provenance is broken or unavailable | T-14 `test-provenance-continuity.md` | FAP artifact carries provenance hash/audit trail; DPIE preserves explicit provenance dependencies | Broken/stale dependency must surface; artifact must not remain authoritative | **SPECIFIED / INTEGRATION REQUIRED** | Critical |
| C-03 | Adversarial narrowing | Actor adds constraints to force preferred answer | T-07 `test-adversarial-narrowing.md` | DPIE has explicit applicability/context preservation mechanisms | Preference must not masquerade as valid narrowing | **SPECIFIED / INTEGRATION REQUIRED** | Critical |
| C-04 | Constraint ≠ resolution | Constraint reduces answer space to a candidate without proving exhaustiveness/resolution | T-12 family; constraint tests | EPM decision model distinguishes answer-space constraints from authority | Result remains constrained, not resolved, absent resolution conditions | **SPECIFIED** | Critical |
| C-05 | Constraint monotonicity | Added constraint causes unsupported strengthening of conclusion | `test-constraint-monotonicity.md` | EPM test specification exists | Narrowing cannot silently increase epistemic authority | **SPECIFIED** | High |
| C-06 | Constraint entailment | Constraint is accepted without declared entailment/premises | `test-constraint-entailment.md` | EPM test specification exists | Unsupported constraint is rejected/deferred | **SPECIFIED** | High |
| C-07 | Constraint failure preservation | Invalid constraint is treated as harmless narrowing | `test-constraint-failure.md` | EPM test specification exists | Failure remains explicit; no derived authority from failed constraint | **SPECIFIED** | High |
| C-08 | Dependency propagation | Derived state loses or obscures dependency chain | `test-dependency-propagation.md` | DPIE `AssuranceProperty.dependencies`; FAP audit/provenance structures | Dependencies propagate or result becomes non-authoritative/deferred | **INTEGRATION REQUIRED** | Critical |
| C-09 | Derivation ≠ closure | A derivation is treated as proof that the answer space is closed | `test-derivation-vs-closure.md` | EPM derivational model; no single cross-component executable proof yet | Derivation cannot establish closure without closure conditions | **SPECIFIED** | Critical |
| C-10 | Discriminator ≠ observation | A discriminator or selector is treated as direct observation | `test-discriminator-independence.md`; `test-discriminator-integrity.md` | EPM discriminator model/specification | Identification/selection must not promote to observation | **SPECIFIED** | Critical |
| C-11 | Circular resolution | Output used as its own discriminator/justification | `test-circular-resolution.md` | AKS/EIE contains a `JustificationChainAdversary` for circular-justification attacks | Circular support must be detected or quarantined | **INTEGRATION REQUIRED** | Critical |
| C-12 | Computational discovery ≠ observation | Computationally discovered result is represented as an external observation | `test-computational-discovery.md` | EPM specification | Computational discovery retains derivational provenance | **SPECIFIED** | High |
| C-13 | Answer-space granularity | Representation granularity is mistaken for epistemic fact | T-12 `test-answer-space-granularity.md` | EPM test specification | Granularity must be justified by question/evidence | **SPECIFIED** | High |
| C-14 | Authorization separation | Epistemic validity is treated as authorization | EPM Governor/decision model; executable integration test required | DPIE decisions include AUTHORIZED, CONSTRAINED, DEFER, QUARANTINE, DENY | Authorization requires explicit governance/authority conditions | **INTEGRATION REQUIRED** | Critical |
| C-15 | Context preservation | Same evidence crosses purpose/scope/jurisdiction boundary without preservation proof | DPIE assurance tests | `RequestAssuranceContext`; `PreservationProof`; `evaluate_transition()` | Material context change without proof → INVALIDATED + QUARANTINE/DENY | **UNVERIFIED RUNTIME / STRONG IMPLEMENTATION EVIDENCE** | Critical |
| C-16 | Rule/version preservation | Evidence crosses a changed rule binding without proof | DPIE assurance tests | `RuleBinding`; preservation checks rule id/version/authority | RULE_MISMATCH; invalidate material transition | **UNVERIFIED RUNTIME / STRONG IMPLEMENTATION EVIDENCE** | High |
| C-17 | Jurisdiction preservation | Evidence crosses jurisdiction boundary without explicit determination | DPIE assurance tests | `AssuranceContext.jurisdiction`; preservation checks | JURISDICTION_MISMATCH; quarantine material transition | **UNVERIFIED RUNTIME / STRONG IMPLEMENTATION EVIDENCE** | High |
| C-18 | Temporal preservation | State crosses temporal boundary without valid preservation | DPIE assurance implementation + EPM temporal model | `AssuranceContext.at`; rule effective-time check | TEMPORAL_MISMATCH; no silent temporal carry-forward | **INTEGRATION REQUIRED** | Critical |
| C-19 | UNKNOWN preservation | Missing/unknown evidence is silently converted to false/invalid | DPIE assurance implementation | Explicit `UNKNOWN` and conservative `DEFER` path | UNKNOWN remains UNKNOWN; no fabricated invalidity | **UNVERIFIED RUNTIME / STRONG IMPLEMENTATION EVIDENCE** | Critical |
| C-20 | Epistemic inflation through composition | Individually valid transformations compose into an unjustified stronger result | EPM core failure-mode definition; executable composition test required | DPIE has `COMPOSITION_UNRESOLVED`; FAP state/provenance transitions | Composition must preserve or explicitly justify resulting epistemic status | **INTEGRATION REQUIRED** | **Critical — Gate blocker** |
| C-21 | Temporal non-retroactivity | Evidence available at t2 strengthens what was knowable at t1 | EPM temporal model; executable test required | Temporal evidence model specified; no fresh executable conformance evidence | Later availability cannot silently rewrite earlier epistemic state | **SPECIFIED / NOT YET EXECUTABLE** | **Critical — Gate blocker** |
| C-22 | Provenance tamper visibility | Provenance/hash/audit relationship changes without corresponding state response | FAP artifact provenance/audit implementation | `provenance_hash()`, immutable-style event trail | Tamper/broken chain must become detectable and non-authoritative | **INTEGRATION REQUIRED** | Critical |
| C-23 | Materiality boundary | Non-material transition incorrectly treated as requiring/establishing material preservation, or vice versa | DPIE assurance tests | `Materiality`; `is_material()` | Materiality determines whether explicit preservation proof is required | **UNVERIFIED RUNTIME** | High |
| C-24 | Misapplication without tampering | Perfectly intact artifact is applied outside original purpose/scope | DPIE `perfect_artifact_misapplication_demo()` and assurance tests | `MISAPPLICATION`; INVALIDATED; DENY/QUARANTINE | Integrity of artifact does not imply applicability in new context | **UNVERIFIED RUNTIME / STRONG IMPLEMENTATION EVIDENCE** | Critical |

## Gate blockers

The following items prevent a full EPM lock because they attack the architecture's most consequential seams rather than isolated functions:

1. **C-20 — Epistemic inflation through composition**
2. **C-21 — Temporal non-retroactivity**
3. **C-02 — Provenance continuity across implementation boundaries**
4. **C-08 — Dependency propagation across transformations**
5. **C-14 — Authorization separation**
6. **C-18 — Temporal preservation**

## Current gate verdict

**VERDICT: NOT READY TO LOCK — TESTING GATE REMAINS ACTIVE**

This is not a theory-completion failure. The EPM corpus contains substantive adversarial test specifications, while DPIE contains concrete executable assurance mechanisms for context, purpose, scope, jurisdiction, rule binding, preservation proof, materiality, and conservative handling of unknown/contradictory source states. The unresolved question is whether those protections survive **composition, temporal transformation, and cross-component use**.

## Required next execution set

Create the smallest executable conformance suite necessary to attack the six blockers:

- `test_epistemic_status_inflation_through_composition`
- `test_provenance_continuity_after_dependency_break`
- `test_dependency_propagation_across_derivation`
- `test_authorization_does_not_follow_epistemic_validity`
- `test_temporal_preservation_requires_available_evidence`
- `test_later_evidence_cannot_strengthen_prior_state`

Each test must record:

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
- Previously inspected FAP artifact/provenance implementation: `fap_core/artifact.py`

**Version:** v0.1  
**Gate state:** ACTIVE  
**TVC:** OUT OF SCOPE FOR THIS GATE
