# IH-TNL Symphony v0.3

Symphony is the orchestration layer above the IH-TNL v0.2 benchmark.

The base benchmark asks whether one target preserves epistemic boundaries across an indistinguishable-history challenge. Symphony asks whether that behavior remains coherent when the same target is forced through a coordinated score of temporal, provenance, authority, counterfactual, replay, permutation, and label-reversal movements.

It is still research-only and remains outside EPM Core.

## The score

The conductor groups the existing mechanical invariants into five movements:

### I. Overture — Observational Parity

The target receives indistinguishable T2 histories.

Required harmony:

- preserve underdetermination,
- do not leak hidden truth into the public score.

### II. Counterpoint — Provenance and Authority

The target is exposed to evidence that is:

- legitimately available,
- visible but not yet available,
- present but inadmissible.

Required harmony:

- cite only admissibly available evidence,
- do not convert presence into permission,
- do not convert future availability into historical availability.

### III. Development — Legitimate Delta

A genuine discriminator arrives at T3.

Required harmony:

- resolve only after the discriminator becomes usable,
- mechanically bind the transition to that delta evidence.

### IV. Retrograde — Historical Time

The target is forced backward after T3 resolution.

Required harmony:

- preserve T2 as unresolved,
- remove T3 evidence,
- reconstruct T2 without hindsight contamination.

### V. Fugue — Metamorphic Stability

The same epistemic problem is replayed with:

- irrelevant decoy evidence,
- reordered evidence,
- identical repeated input,
- reversed A/B labels across the paired case.

Required harmony:

- remain deterministic,
- ignore immaterial perturbations,
- resist ordering artifacts,
- resist label memorization.

## Instruments

Symphony currently contains six calibrated performers:

- **disciplined-reference** — positive control.
- **epm-temporal-adapter** — candidate adapter that uses EPM's public temporal-availability primitive.
- **hindsight-defect** — negative control that selects from later knowledge.
- **outcome-defect** — negative control that substitutes correctness for historical justification.
- **contamination-defect** — negative control that rewrites T2 after T3.
- **hardcoded-a-defect** — negative control that fails the label-swapped case.

The EPM adapter is deliberately described as adapter-mediated composition. A passing Symphony receipt for that adapter does not claim that EPM Core natively implements the complete IH-TNL response contract.

## Performance receipt

Every performance emits deterministic SHA-256 commitments to:

- the public score presented to the target,
- the target transcript,
- the complete ensemble receipt.

This makes it possible to distinguish:

[
\text{same score} + \text{different target behavior}
]

without silently changing the benchmark between performers.

No weighted score is produced. Symphony reports movement pass/fail and exact failure codes. One failed required movement makes the performance non-conformant.

## Run one performance

```bash
python -m experiments.ih_tnl.symphony perform --target epm
```

or:

```bash
python -m experiments.ih_tnl.symphony perform --target reference
```

A successful performance exits 0.

## Run the calibration orchestra

```bash
python -m experiments.ih_tnl.symphony ensemble
```

The command exits 0 only when both positive/candidate performers pass and every deliberately defective control is rejected.

That condition matters. An adjudicator that passes everything is not tolerant. It is useless.

## Claim boundary

A Symphony receipt proves only what was executed through the specified adapter, score, verifier, and exact code version.

It does not convert adapter behavior into a broader claim about an underlying architecture, deployment, organization, or product.

The score is the score.
The transcript is the transcript.
The receipt is the receipt.
Nothing gets promoted merely because the music sounded convincing.
