# EPM vNext Conformance Matrix v0.1 — Executable Engine Gate

**Status:** VNEXT ENGINE GATE EXECUTED — REVIEWABLE, NOT MERGED OR RELEASED  
**Date:** 2026-09-14  
**Scope:** Domain-neutral EPM vNext engine as implemented on the FAP-Insurance vNext branch  
**Historical baseline:** `04_TESTS/EPM-CONFORMANCE-MATRIX-v0.2.md` remains frozen and unchanged  
**Explicit exclusions:** production C-21 integration, TVC, Variant Hunter, merge/release/deployment claims

## Governing evidence rule

This matrix is a new vNext evidence record. It does **not** rewrite, supersede, backdate, or reinterpret the frozen EPM v0.2 closure matrix.

A row is marked **PASS** only where executable behavior exists in the vNext runtime boundary and was exercised in the final branch-wide verification gate. Specification text or repository inspection alone is not treated as runtime conformance evidence.

The final executable FAP-Insurance vNext baseline is:

- branch: `vnext/generic-evidentiary-envelope-v0.1`
- commit: `bd1421c485085adbaf8428c0ca1bfb36f5915313`
- Production Verification #83 — run `34797796926` — **SUCCESS**
- final Production Verification pytest — **151 passed, 1 warning**
- FAP-Insurance CI/CD #203 — run `34797797078` — **SUCCESS**
- engine lint — **PASS**
- vNext test correctness lint — **PASS**
- engine compile — **PASS**
- public `epm` import — **PASS**
- legacy API/assurance regression suites — **PASS**
- dedicated EPM vNext semantic gate — **PASS**
- full pytest suite — **PASS**

## Evidence-state vocabulary

- **PASS** — fresh executable evidence demonstrates the invariant in the claimed vNext engine boundary.
- **ENGINE CAPABILITY PRESENT / PRODUCTION INTEGRATION EXCLUDED** — the generic engine abstraction is implemented and executed, but a trustworthy production integration required for the stronger deployment claim does not exist.
- **FAIL** — executable evidence demonstrates a violation.
- **UNVERIFIED** — implementation exists but fresh executable evidence is absent.

## Conformance matrix

| ID | Invariant / failure mode | vNext executable evidence / boundary determination | State |
|---|---|---|---|
| C-01 | Epistemic status conservation | Generic envelope and compatibility probes preserve weaker source states; UNKNOWN remains UNKNOWN/DEFER and cannot be promoted by requested target state. | **PASS** |
| C-02 | Provenance continuity | Frozen provenance/audit behavior remains green; vNext source, constraint, availability, graph-node, and support-edge objects add explicit provenance-bearing structure without replacing the prior audit boundary. | **PASS** |
| C-03 | Adversarial narrowing | First-class constraints require identified premises, non-empty provenance, an established entailment basis, source reference, and any required governance review before exclusions become effective. | **PASS** |
| C-04 | Constraint ≠ resolution | Constraint recomputation may narrow to a singleton while the answer-space remains `CONSTRAINED`; only a sufficient discriminator plus a valid external observation can produce `RESOLVED`. | **PASS** |
| C-05 | Constraint monotonicity | Answer-space is recomputed from the declared candidate universe and currently valid constraints; immutable revision/history records narrowing, widening, and reopening instead of silently overwriting history. | **PASS** |
| C-06 | Constraint entailment | Constraint exclusions are ineffective unless entailment status is `ESTABLISHED` and an explicit entailment basis is present. | **PASS** |
| C-07 | Constraint failure preservation | Invalidated or contradicted premises invalidate/contradict the dependent constraint, remove effective exclusions, and permit the answer-space to reopen on recomputation. | **PASS** |
| C-08 | Dependency propagation | Existing FAP dependency propagation remains green; vNext justification-graph invalidation propagates staleness to every reachable dependent node. | **PASS** |
| C-09 | Derivation ≠ closure | `record_derivation()` records `DERIVED` standing without changing resolution state; `CLOSED` requires legitimate resolution, explicit exhaustive-domain basis, external resolution references, and no material unresolved conditions. | **PASS** |
| C-10 | Discriminator ≠ observation | Discriminator definition and sufficiency are distinct from outcome observation; Stage 2 resolution requires a separately typed, externally originated `OBSERVATION`. | **PASS** |
| C-11 | Circular resolution | Direct self-support and cycle-creating edges are rejected; cycle detection prevents circular support from counting as established or independent corroboration. | **PASS** |
| C-12 | Computational discovery ≠ observation | `COMPUTATIONAL_DISCOVERY` and `DERIVATION` are explicit source types; internal outputs cannot be relabeled as observations without new external observation, and new observation does not rewrite old provenance. | **PASS** |
| C-13 | Answer-space granularity | Answer-space construction requires explicit granularity and a justification for that granularity; admissible candidates must remain inside the declared universe. | **PASS** |
| C-14 | Authorization separation | Existing Governor/transition behavior remains green through generic-envelope routing; evidence/assurance evaluation does not itself silently grant unrelated authorization. | **PASS** |
| C-15 | Context preservation | Purpose, scope, jurisdiction, time, rule, and authority context remain typed inputs to materiality/preservation evaluation. | **PASS** |
| C-16 | Rule/version preservation | Existing rule/version mismatch enforcement remains green after generic routing. | **PASS** |
| C-17 | Jurisdiction preservation | Existing jurisdiction mismatch enforcement remains green after generic routing. | **PASS** |
| C-18 | Temporal preservation | Existing transition-time preservation behavior remains green; vNext additionally models trusted evidence availability without conflating it with event/capture/processing time. | **PASS** |
| C-19 | UNKNOWN preservation | Missing or untrusted availability remains `UNKNOWN`; unknown assurance remains UNKNOWN/DEFER rather than being coerced into false availability, false unavailability, or validity. | **PASS** |
| C-20 | Epistemic inflation through composition | Existing composition boundary remains green; vNext aggregate state intentionally returns component assessments instead of a master truth/confidence score that could overwrite weaker states. | **PASS** |
| C-21 | Temporal non-retroactivity | Typed `EvidenceAvailability` plus validated attestation/provenance and AVAILABLE/UNAVAILABLE/UNKNOWN evaluation is implemented and adversarially tested. However, the production FAP request path still does not receive trustworthy end-to-end evidence-availability provenance. `timestamp_claimed`, capture time, and processing time are not substitutes. | **ENGINE CAPABILITY PRESENT / PRODUCTION INTEGRATION EXCLUDED** |
| C-22 | Provenance tamper visibility / authority | Frozen audit/provenance tamper behavior remains green; vNext provenance-bearing semantic records do not weaken the authority boundary. | **PASS** |
| C-23 | Materiality boundary | Generic envelope preserves the executed material/non-material transition distinction and matching-preservation requirement. | **PASS** |
| C-24 | Misapplication without tampering | Material purpose/scope/context misuse remains detectable even where underlying evidence has not been tampered with. | **PASS** |

## Cross-domain execution

The same vNext invariants were exercised without insurance request fields across seven domain contexts:

- insurance
- legal evidence
- scientific evidence
- machine-generated analysis
- financial decision support
- compliance
- intelligence analysis

The cross-domain suite covers fail-closed transition behavior, UNKNOWN conservation, singleton/non-resolution, computational-source typing, temporal UNKNOWN preservation, and circular-support rejection.

## C-21 boundary

C-21 requires a deliberate split between **engine capability** and **production integration**.

The engine can now represent and evaluate trusted availability provenance. That is a real implemented capability. It does not justify a production conformance claim until the production integration supplies a trustworthy provenance-bearing record establishing when evidence actually became available to the relevant epistemic state.

Therefore this matrix does not infer availability from:

- `timestamp_claimed`;
- media capture time;
- request receipt time;
- `processed_at`;
- a bare timestamp without validated provenance.

## Claimed vNext boundary

The executable claim established by this gate is:

> A domain-neutral EPM engine can preserve transition assurance, typed epistemic source origin, trusted temporal-availability uncertainty, premise/entailment-aware constraints, answer-space resolution boundaries, and justification/dependency structure across multiple domain contexts without silently converting derivation into observation, narrowing into resolution, provenance into authority, or uncertainty into certainty.

## Non-claims

This record does not claim:

- that EPM vNext is merged to `main`;
- that EPM vNext is released or deployed to production;
- production C-21 conformance without a trustworthy availability integration;
- that domain adapters automatically possess source/constraint/answer-space/graph data they do not actually emit;
- that graph acyclicity authorizes an action;
- that a confidence score can override typed uncertainty;
- TVC implementation or conformance;
- Variant Hunter implementation or conformance.

The frozen EPM v0.2 closure record remains intact as the historical baseline.