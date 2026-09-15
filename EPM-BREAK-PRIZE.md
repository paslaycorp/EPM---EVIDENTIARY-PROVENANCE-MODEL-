# EPM Break Prize — v0.1.1

**Prize: US$1,000**

EPM v0.1.1 makes a narrow claim: evidence should not gain applicability, authority, certainty, resolution, or temporal legitimacy that its evidence and governing context do not support.

The Break Prize exists to reward the first independent researcher who produces a complete, reproducible material violation of that boundary against the frozen v0.1.1 runtime.

> Don’t tell me EPM works. Don’t tell me it doesn’t. Make the evidence decide.

## Frozen target

Release: `v0.1.1`

Runtime commit:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

Engine:

`epm-engine/0.1.1`

Later commits on `main` do not replace the prize target.

## Qualifying BREAK

A qualifying BREAK demonstrates that the frozen runtime authorizes, accepts, resolves, closes, or otherwise materially strengthens an evidentiary state in a way that grants evidence something it did not legitimately possess.

Examples include:

- purpose or scope laundering;
- authority laundering;
- jurisdiction laundering;
- rule/version laundering;
- retroactive use of evidence that was not yet available;
- future-effective rules applied to earlier states;
- UNKNOWN promoted without new legitimate evidence;
- computation relabeled as external observation;
- derivation or constraint processing promoted into resolution without legitimate external discrimination;
- circular/shared-origin support treated as independent corroboration;
- materially invalidated upstream evidence leaving dependents current.

The report must identify the violated invariant, not merely an unexpected result.

## Submission requirements

A qualifying report must include:

1. exact EPM commit SHA;
2. Python version and relevant environment information;
3. attack class;
4. minimal executable reproduction;
5. exact input state and governing context;
6. expected invariant;
7. exact observed result;
8. deterministic/non-deterministic status;
9. enough information for another operator to reproduce the finding independently.

Use the structured red-team issue form where practical.

## Verification rule

The organizer or a designated independent verifier must reproduce the claimed material invariant violation against the exact frozen target.

Reports sharing the same underlying root cause are treated as one finding. The first complete qualifying report by GitHub submission timestamp takes priority.

The target does not move during verification.

## Prize

The first independently reproduced qualifying BREAK receives **US$1,000**.

Payment is arranged directly with the verified winner after reproduction and eligibility review. The winner is responsible for any tax or reporting obligations applicable to them.

## Eligibility

The submitter must not have authored the EPM v0.1.1 runtime or this prize harness.

Testing must be performed against code or systems the researcher is authorized to test. The prize does not authorize access to unrelated production systems, accounts, infrastructure, or third-party data.

## Non-qualifying reports

The prize is not awarded for:

- stylistic disagreement;
- a missing feature EPM does not claim;
- universal truth or universal media-origin timestamping;
- domain policy never supplied to EPM;
- disagreement with the deliberate rule that computation is not observation;
- TVC or Variant Hunter behavior;
- duplicate root causes;
- malformed input that is rejected before crossing the claimed boundary.

## Three outcomes

### BREAK

A material invariant violation is reproduced. The prize is awarded if it is the first qualifying root cause.

### EDGE

A legitimate integration ambiguity or boundary weakness is identified without yet proving a runtime invariant violation. It is recorded and investigated but does not automatically qualify for the prize.

### HOLD

A serious attack fails to violate the declared boundary. The attempt and receipt are recorded as bounded external evidence, not as proof of universal correctness.

## Fast path

Run the Blackbox Gauntlet:

```bash
python tools/epm_gauntlet.py --output validation-receipt.json
```

Then try something the gauntlet does not already know how to ask.

Supporting material:

- `EPM-BLACKBOX-GAUNTLET.md`
- `EXTERNAL-RED-TEAM.md`
- `.github/ISSUE_TEMPLATE/epm-red-team.yml`
- `schemas/external-validation-receipt.schema.json`
- `STANDARDS-INTEROP.md`

## Campaign status

The campaign is open until a qualifying BREAK is awarded or a prospective closure is publicly posted. A complete submission received before a posted closure remains eligible under the terms in effect when it was submitted.

## Why this exists

Praise is cheap. Argument is cheaper.

A system about evidentiary integrity should make room for the person who finds the assumption its author missed.

If EPM breaks, preserve the break.

If it holds, preserve the attack.

Either way, make the evidence decide.
