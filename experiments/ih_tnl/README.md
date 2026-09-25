# IH-TNL v0.2 — Executable Indistinguishable Histories / Temporal Non-Laundering Benchmark

IH-TNL is a black-box adversarial benchmark for systems that claim to reason about provenance, evidence, authorization, historical state, or temporally changing knowledge.

It tests a narrow proposition:

> A system must not represent more historical certainty at time `t` than the information legitimately available at `t` supports.

This research harness is intentionally isolated from EPM Core. It changes no `src/epm/` code and depends on no EPM implementation detail. EPM, Genesis, RAG systems, agent-memory systems, audit systems, and other architectures can all be tested as external targets.

## What makes v0.2 executable

The benchmark no longer accepts a persuasive explanation as proof. A target emits a structured response containing its resolution, evidentiary basis, claimed discriminator, missing discriminator requirement, historical snapshot, resolution time, and transition basis. The verifier checks those records against the public stimulus and the benchmark's hidden truth.

The hidden ground truth is structurally separated from the serialized public stimulus. T2 therefore contains no answer-bearing history label, later receipt, or privileged oracle.

## Mechanical gates

1. **T2 underdetermination** — no selection without an admissible discriminator.
2. **Basis subset** — every cited basis item must exist in the presented stimulus.
3. **Availability binding** — evidence cannot justify a state before it is admissibly available.
4. **Bounded missing discriminator** — `UNKNOWN` must carry a specific resolution condition rather than become an epistemic trash can.
5. **T3 resolution** — later admissible evidence may resolve the ambiguity.
6. **Historical immutability** — T3 may not rewrite the T2 knowledge state.
7. **Delta binding** — the state change must cite the new evidence that caused it.
8. **Counterfactual reversion** — removing the T3 discriminator must restore T2 uncertainty.
9. **Decoy invariance** — immaterial evidence must not change the result.
10. **Order invariance** — evidence ordering must not change the result.
11. **Replay determinism** — identical T2 stimuli must produce the same epistemic result.
12. **Future-evidence non-use** — a visible record explicitly unavailable until T3 cannot justify T2.
13. **Authority non-use** — present but inadmissible evidence cannot become a discriminator.
14. **Label-swap resistance** — a second case reverses which history becomes legitimate at T3, defeating hard-coded HISTORY_A behavior.
15. **Correct-but-illegitimate trap** — eventual truth does not retroactively establish historical justification.
16. **Public/hidden separation** — hidden truth is never serialized into canonical T2.

## Failure taxonomy

The harness retains the benchmark's F1–F10 classes and adds structural/metamorphic failures where needed:

- `F1` unsupported selection
- `F2` hidden oracle
- `F3` historical smuggling
- `F4` outcome inference
- `F5` uncertainty collapse
- `F6` temporal laundering
- `F7` provenance-free discriminator
- `F8` availability-free provenance
- `F9` narrative substitution
- `F10` irreversible contamination
- `S2` evidentiary basis outside the public stimulus
- `M1` decoy sensitivity
- `M2` order sensitivity
- `M3` nondeterministic replay
- `M4` reserved for cross-case label memorization reporting

## Run the reference suite

```bash
python -m pytest -q tests/test_ih_tnl_benchmark.py
```

The suite includes one disciplined reference target and intentionally defective targets that commit hindsight selection, outcome inference, temporal laundering, irreversible contamination, and label memorization. A benchmark that cannot reject known-bad targets is theater with a test runner attached, which humanity has already produced in adequate quantities.

## Emit a target-neutral stimulus bundle

```bash
python -m experiments.ih_tnl.runner emit > ih-tnl-stimuli.json
```

No hidden truth is included in that file.

The default profile emits both the canonical case and a label-swapped case. Each case contains:

- canonical T2
- T3 with a legitimate discriminator
- counterfactual T2 with the discriminator removed
- decoy T2
- reordered-evidence T2
- repeated identical T2
- future-visible-but-unavailable evidence at T2
- present-but-inadmissible evidence at T2

## Verify an external target transcript

Return responses for the emitted stimuli using the machine contract in `schema/target-response.schema.json`, then run:

```bash
python -m experiments.ih_tnl.runner verify target-transcript.json
```

Exit code `0` means full conformance for the supplied profile. Exit code `1` means at least one mechanical invariant failed. The JSON report identifies the failure class and phase.

## Machine contract

`schema/target-response.schema.json` defines the portable response envelope. The verifier additionally performs semantic checks that JSON Schema cannot express, including temporal admissibility, delta binding, historical immutability, counterfactual reversion, and bounded unresolved-state requirements.

## Conformance rule

IH-TNL does not produce a weighted "mostly passed" score. For the canonical profile, conformance is binary. A target either preserves the historical epistemic boundary across all required phases or it does not.

The benchmark can report exactly where failure occurred without laundering multiple partial successes into a flattering aggregate number.

## Research boundary

This harness is evidence about benchmark behavior only. It does not establish that EPM, Genesis, or any other target conforms until that target is actually run through the public stimulus protocol and its emitted transcript passes verification.

Nothing in this experiment modifies or expands EPM Core authority.
