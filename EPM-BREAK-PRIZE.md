# EPM Break Challenge — v0.1.1

EPM makes a narrow claim. Independent reviewers are invited to break it.

This is a **technical falsification challenge, not a cash bounty**. The purpose is to obtain reproducible evidence about the released boundary, whether the result is a break, a meaningful edge case, or a serious attack that the boundary survives.

> **Don’t tell me EPM works. Don’t tell me it doesn’t. Make the evidence decide.**

## Frozen target

Release: `v0.1.1`

Runtime commit:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

Engine:

`epm-engine/0.1.1`

The target does not move during evaluation. Later `main` commits do not replace the frozen challenge target.

## What counts as a BREAK

Produce a reproducible case where EPM **authorizes, accepts, resolves, closes, or materially strengthens** an evidentiary state in a way that lets evidence gain something it did not legitimately possess, including:

- applicability across a changed purpose or scope;
- authority under an unbound authority or rule;
- jurisdictional legitimacy after an unpreserved jurisdiction change;
- temporal legitimacy from evidence unavailable at the historical state time;
- certainty or resolution created only by computation over unchanged evidence;
- observation status manufactured from an internal derivation;
- independence manufactured from circular or shared-origin support;
- a current dependent conclusion surviving a material upstream invalidation.

A useful report identifies the violated invariant, not merely an unexpected output.

## Evidence required

A useful submission should include the exact EPM SHA and Python version, the attack class, a minimal executable reproduction, exact input state and governing context, the expected invariant, the observed result, determinism status, and enough detail for independent reproduction.

## Fast path

```bash
python tools/epm_gauntlet.py --output validation-receipt.json
```

Then go beyond it. The gauntlet is a starting attack deck, not proof of safety.

Relevant material:

- `EPM-BLACKBOX-GAUNTLET.md`
- `EXTERNAL-RED-TEAM.md`
- `.github/ISSUE_TEMPLATE/epm-red-team.yml`
- `schemas/external-validation-receipt.schema.json`
- `STANDARDS-INTEROP.md`

## Three outcomes

### BREAK

A material invariant violation is reproduced against the frozen target. The runtime boundary should reopen only around the demonstrated defect.

### EDGE

A legitimate integration ambiguity or boundary weakness is identified without yet demonstrating a runtime invariant violation. It gets recorded and investigated.

### HOLD

A serious attack is executed and the declared boundary survives. A HOLD is bounded external evidence that the tested attack failed; it is **not** proof that EPM is universally correct.

## Why run the challenge?

Because praise is cheap and argument is cheaper.

A useful evidentiary architecture should make it easy for someone else to show the assumption its author missed.

If EPM breaks, preserve the break, reproduce it, and learn from it. If it holds, preserve the exact attack too.

**Break one boundary. Show your work. Make the evidence decide.**
