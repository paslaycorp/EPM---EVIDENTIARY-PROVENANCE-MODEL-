# TVC v0.2 Current-Main Parity Record

## Identity

- EPM base: `adb1c31cdb428816c95a3cf98c9a4427c13ec482`
- frozen TVC v0.1 source: `3bf03d1df25361941af042cf23a4559cce374fbe`
- v0.2 forward-port commit: `9f823b5f753e4c35e139491e56eaec20b0587501`
- validation run: `35519465917`
- validation matrix: Python 3.12 / 3.13
- result: SUCCESS on both lanes

## Isolation proof

The initial forward-port is one commit ahead of the EPM base and contains exactly 30 added files:

- `experiments/tvc/**`
- `tests/test_tvc_*.py`

It changes no `src/epm/**` file and makes no production, release, or authority mutation.

## Information-parity result

The decisive parity fixture provides both EPM and TVC:

- the same proposition;
- the same asserted `INFERRED` standing;
- established support;
- established provenance;
- established entailment;
- the same claim time;
- the same absence of a contradiction-disposition record.

No hidden contradiction fact is provided to TVC.

Observed bounded result:

```text
EPM inspect_state:
  failures = 0
  asserted standing remains INFERRED

TVC evaluate_closure:
  status = UNRESOLVED
  closure_boundary = contradictions
  reproduced_standing = EVIDENCED

incremental detection delta = 1
```

The difference arises because TVC derives obligations intrinsic to the asserted standing and demands historical closure over those obligations.

## Differential controls

The differential matrix also verifies:

- clean closure produces no TVC-only delta;
- explicit contradiction is detected by both systems;
- missing entailment is detected by both systems;
- an `EVIDENCED` standing does not inherit an inference-only contradiction obligation.

The current evidence therefore does not support a claim that TVC simply generates more failures. Its bounded delta is conclusion-conditioned.

## Material Counterfactual Frontier

The v0.2 suite preserves these properties:

- compositional failures hidden from single-dependency ablation are captured;
- inclusion-minimal failure interventions are canonical;
- the material frontier can be smaller than the complete powerset;
- identical endpoint standings may retain different frontier digests;
- dependency input ordering does not alter the result;
- non-monotonic recovery is detected and fails closed instead of being compressed unsafely;
- exhaustive three-dependency surfaces validate the compression gate.

## Important limitation

TVC's dynamic dependency-availability behavior is not claimed as an irreducible new primitive.

The equal-information control test reconstructs the same dynamic availability result by independently traversing the same graph and applying EPM's existing temporal-availability primitive.

Therefore the present claim is narrower:

> TVC currently demonstrates incremental assurance behavior as a conclusion-conditioned closure architecture relative to EPM's inspection surface, while some constituent operations remain reproducible from existing EPM primitives.

## Boundary

TVC remains:

- experimental;
- outside EPM Core;
- non-authoritative;
- non-executing;
- unable to rewrite historical EPM decisions;
- a verifier/challenger rather than a governor.

This record is evidence for continued TVC research, not a production-readiness, novelty, patentability, or universal-security claim.
