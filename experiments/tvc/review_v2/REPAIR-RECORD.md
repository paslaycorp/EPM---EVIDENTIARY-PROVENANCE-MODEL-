# PR #31 integrity repair record — 2026-09-24

Parent: `5597b0b5c2130665e69196f3e00c5d75252ee220`.
Core remains at tree `2f8abae49ccf8eef326604963c866084edf793ea`.

## Problem and change

The independent review demonstrated that `close_against_contract()` accepted a
changed payload while validating an old digest/anchor pair. The original five
witnesses changed transition identity, policy identity, issue time, prior
standing, or the stored response surface plus matching later reconstruction.
The repaired verifier recomputes a versioned, unambiguous payload digest before
trusting the payload or executing reconstruction. A sixth probe exposed a
newline field-boundary collision in the old encoding; v2 structured JSON removes
that ambiguity. V1 digests are not interpreted as v2 commitments.

The old closure result's first boundary depended on tuple order, while parallel
graph edges retained only the first provenance reference. Explicit policy
priorities now preserve default diagnostics under permutations. Graph obligations
retain every provenance reference and fail closed with a typed UNKNOWN when
parallel assertions cannot be distinguished by the existing dependency identity.

The previous failing-policy-order and collapsed-provenance tests have been
strengthened to require repaired behavior. Their original forms remain at the
parent commit, and the independent review's raw evidence is in `baseline.json`.
No historical result has been rewritten to report a pass.

## Executed local validation

- The initial 19 repair regressions against the untouched parent produced
  16 failures and 3 passes, including all five original payload-forgery witnesses.
  Some failures deliberately describe the newly specified v2 behavior rather
  than preexisting API requirements.
- The repaired repository's full suite passed: **252 tests**, Python 3.12.14.
  This includes 20 focused integrity regressions and two subprocess review gates.
- The subprocess gate independently compares 114,244 closure cases, 512 generated
  graphs, and 3,211 counterfactual surfaces; it requires byte-identical primary
  results across three fresh hash-seeded processes.
- Prospective issuance is independently reproducible for all 27 two-dependency
  surfaces. Both arms detect all 702 changed surfaces across 729 original/later
  pairs, within equal query budgets. Endpoint-only checks still miss those changes.
- The EPM Blackbox Gauntlet and distribution build passed. Exact unchanged Core
  file hashes are asserted during each independent review run.

The local suite result is not a claim about unobserved remote CI. Remote CI must
be attached to the actual pushed commit, including Python 3.13, before treating
that commit's validation as complete.

## Preserved boundary and remaining limitations

Changes are confined to `experiments/tvc/**` and `tests/test_tvc_*.py`. EPM Core,
public API, version, release tags, deployment authority and production remain
unchanged. This is an experimental correctness repair, not a Core merge request.

The generic controls continue to match TVC on the declared domains. External
trusted time, historical graph completeness, provenance adjudication and
resource-bounded capability separation remain unproved. Frontier compression
still commits the baseline-failure boundary rather than every degraded label,
and complete-surface issuance still uses 2^n reconstruction queries.

The next scientific gate is the frozen, independently challenged comparison in
`PROTOCOL.md`, with equal history, policy semantics, intervention rights and
resource budgets. No strengthened novelty or irreducibility claim follows from
this repair.
