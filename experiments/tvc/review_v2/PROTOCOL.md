# TVC integrity repair and repeatable reduction gate

Parent candidate: `5597b0b5c2130665e69196f3e00c5d75252ee220`.
Original independent experiment: 2026-09-23. Repair review: 2026-09-24.
`baseline.json` retains the original counterexamples, result digest and Core
file hashes. Old results are not reclassified or overwritten by this repair.

## Scope

Only `experiments/tvc/**` and `tests/test_tvc_*.py` change. No EPM public API,
Core, authority envelope, release tag, deployment workflow or production action.
Passing this gate permits further sibling research; it proves neither novelty,
irreducibility nor authorization to deploy.

## Explicit experimental contract changes

1. Prospective contracts use `tvc.prospective-closure/v2`: a SHA-256 over compact,
   sorted-key, ASCII-escaped JSON with schema, transition ID, UTC issue time at
   microsecond precision, policy ID, prior standing, canonical dependency tuple
   and complete canonical response surface. Issue time must be timezone-aware.
   The verifier validates shape and recomputes this payload digest before
   checking its anchor or calling reconstruction. V1 digests are not accepted as
   v2; old artifacts remain historical evidence and must not be silently reissued
   with old dates. Digest binding does not establish external trusted time.
2. `Obligation.priority` is shared policy data, default 0. Canonical order is
   `(priority, obligation_id, required_for, description)`. Default policy uses
   explicit priorities 10/20/30/40, preserving existing default diagnostic order.
   Changing a priority changes policy; permuting containers does not.
3. Graph-derived obligations retain all distinct provenance references. When
   multiple references share the existing logical dependency ID, the legacy
   scalar provenance reference is empty and availability returns UNKNOWN with
   `DEPENDENCY_PROVENANCE_AMBIGUOUS`. Exact duplicate assertions are deduplicated.
   This repair does not establish historical graph completeness or adjudicate
   whether two provenance assertions really refer to distinct dependency events.

## Independent repeat of the reduction experiment

`reference.py` imports no TVC helper. The author saw candidate source; this is
implementation independence, not a blinded or independently authored review.
Both arms get identical evidence, policy priorities, reconstruction rules,
intervention rights, history and synthetic anchor registry. No case-ID dispatch.

- 114,244 exhaustive closure comparisons: two standings, 13 states per fact,
  four facts, two reconstruction scopes. Compare all report fields, not only
  verdict. Thirteen states include missingness and every status/time/provenance
  combination. Input mutation is checked.
- 512 seeded graphs; compare candidate traversal against independent relational
  reachability plus EPM temporal primitives, including record ambiguity. Execute
  1,536 candidate checks with order permutations. Parallel provenance receives
  its own adversarial full-output comparison.
- 2,187 complete ternary three-dependency surfaces and 1,024 seeded larger
  surfaces. Compare minimal frontiers, recovery crossings and compression
  rejection with exactly equal 2^n reconstruction calls per audit.
- Nine prospective verification cases, including the original five payload
  mutations. Clean closure passes; real drift, assertion mismatch, false anchor
  and all payload substitutions fail with matching reference reasons.
- 24 obligation permutations and 24 condition permutations: raw full closure
  result must be identical for a fixed policy. Conflicting parallel provenance
  must be retained identically and remain UNKNOWN.
- Three fresh processes with distinct hash seeds must emit byte-identical
  primary results. Core hashes and experimental source hashes are checked before
  and after each execution.
- Independently issue all 27 two-dependency ternary contracts, then compare all
  729 original/later pairs under matched history access. Equal budgets: four
  issuance and at most five verification oracle calls. Complete history should
  expose all 702 changed surfaces in both arms; endpoint-only checks should miss
  all of them. The history-regime contrast is intentionally not information parity.

## Commands

```sh
python experiments/tvc/review_v2/run.py --out /tmp/tvc-review.json
python experiments/tvc/review_v2/prospective_factorial.py --out /tmp/tvc-history.json
PYTHONPATH=src pytest -q tests/test_tvc_integrity_repair.py tests/test_tvc_integrity_review.py
```

The regression suite includes local subprocess replay of the full experiment.
The original closure/replay and frontier results remain bounded reductions.
No disagreement arising from different serialization, hidden historical facts
or omitted policy priorities counts as a capability separation.

## Remaining scientific gate

After integrity passes, freeze both implementations and request separately
authored cases under an explicit operation/memory/query budget. A surviving
material detection difference must be minimized and independently adjudicated;
failure of one generic program is not proof that no generic program can do it.
Equal detections with lower total discovery/issuance/retention/replay cost would
support an efficiency claim. This code's frontier audit still costs 2^n queries.
It preserves baseline-failure topology, not every nonminimal degraded label.

Historical presence, availability, incorporation, permission and graph
completeness remain distinct. Synthetic anchoring establishes no external clock
truth. The generic controls continue to be a live falsification target rather
than a weaker opponent chosen to create a TVC-only result.
