# EPM Blackbox Gauntlet

## Break the boundary or produce the receipt

The EPM Blackbox Gauntlet turns external red-teaming into a reproducible protocol.

The challenge is simple:

> Make EPM authorize or accept a state where evidence gains applicability, authority, certainty, or temporal legitimacy that it did not possess.

If you can do that with valid typed input against the stated release, you have found a defect worth reproducing.

If you cannot, produce the validation receipt that shows exactly which attacks were attempted and which invariant blocked each one.

This is deliberately not a benchmark score. EPM does not collapse epistemic integrity into a number.

## Frozen semantic target

Release tag:

`v0.1.1`

Release runtime commit:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

Engine:

`epm-engine/0.1.1`

The gauntlet itself lives on post-release `main` and exercises the frozen runtime semantics without changing them.

## One-command run

From a repository checkout with EPM installed:

```bash
python tools/epm_gauntlet.py --output validation-receipt.json
```

A successful run exits `0` and writes a receipt using:

`epm.external-validation-receipt/1.0`

The JSON schema is:

[`schemas/external-validation-receipt.schema.json`](schemas/external-validation-receipt.schema.json)

## Current attack deck

The gauntlet contains a control plus adversarial cases for:

- purpose laundering;
- scope laundering;
- jurisdiction laundering;
- temporal context laundering;
- rule/version laundering;
- authority laundering;
- UNKNOWN inflation;
- future-effective rule leakage;
- evidence-availability leakage;
- computation-to-observation laundering;
- derivation-to-resolution laundering.

Each case records:

- attack class;
- invariant under attack;
- expected observable result;
- actual observable result;
- pass/fail status.

A failure is intentionally loud. The process exits non-zero instead of averaging the breakage into a score.

## How to beat it

Do not merely alter an expected value in the gauntlet. That proves nothing.

A successful external attack must provide a smaller or equally clear reproduction that causes the released runtime to violate the invariant while the input remains within the documented semantic boundary.

Examples:

- a purpose changes but EPM authorizes without valid preservation;
- a future-effective rule silently governs a historical state;
- evidence becomes available after the state but is treated as available before it;
- internal computation becomes an observation without new external origin;
- a derivation becomes RESOLVED solely because the answer-space narrowed.

If you find one, open the repository's **EPM red-team finding** issue form and attach the receipt or minimal reproduction.

## Why the receipt matters

External validation often fails because the report cannot answer basic questions later:

- Which release was actually tested?
- Which invariant was attacked?
- What exact outcome was expected?
- What exact outcome occurred?
- Was the behavior deterministic?

The receipt makes those questions part of the artifact rather than part of somebody's memory.

That changes the game from:

`I tried it and it looked fine`

into:

`Here is the exact runtime, attack deck, observable result, and machine-readable evidence of what happened.`

## Passing does not mean proven safe

A PASS means only that the declared attack deck did not falsify the declared invariants on that run.

It does not establish universal correctness, universal domain completeness, legal admissibility, media-origin authenticity, or immunity to attacks not represented in the deck.

The right next move after a clean run is to add a harder attack, not to declare victory.
