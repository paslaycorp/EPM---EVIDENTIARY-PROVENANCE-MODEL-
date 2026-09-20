# EPM — Evidentiary Provenance Model

**Domain-neutral evidentiary provenance, integrity, and transition-assurance engine**

**Current released runtime: v0.1.2**

EPM preserves boundaries between evidence, inference, applicability, authority, time, and permitted action. It is designed to prevent a downstream system from acquiring certainty or authority that its evidence and governing context do not support.

EPM is not a universal truth engine, a centralized trust score, or a substitute for domain authority.

## Released boundary

Current corrective release:

- release: `v0.1.2`
- exact release commit: `bb0559ddb8eff7f78acc432c0334ce7596c1045c`
- engine identity: `epm-engine/0.1.2`
- certified Python targets: 3.12 and 3.13

Historical v0.1.1 remains preserved at:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

The v0.1.2 release corrected the applicability/materiality boundary without rewriting the v0.1.1 history.

Post-release work on `main` may add governance, interoperability contracts, supply-chain proof, documentation, and adversarial validation. Those changes do not retroactively alter an earlier tagged release.

## Core question

> Even if this evidence is valid, may it legitimately be used here, now, under this rule, for this purpose, by this authority, with this consequence?

## Install the released runtime exactly

```bash
python -m pip install "git+https://github.com/paslaycorp/EPM---EVIDENTIARY-PROVENANCE-MODEL-.git@bb0559ddb8eff7f78acc432c0334ce7596c1045c"
```

Verify runtime identity:

```bash
python -c "import epm; print(epm.EPM_ENGINE_VERSION)"
```

Expected:

```text
epm-engine/0.1.2
```

## Decision vocabulary

EPM returns explicit decision states rather than a scalar truth score:

- `AUTHORIZED`
- `AUTHORIZED_WITH_CONSTRAINTS`
- `DEFER`
- `QUARANTINE`
- `DENY`

Typical failure boundaries include purpose, scope, jurisdiction, temporal mismatch, rule/version mismatch, authority mismatch, unresolved composition, unavailable evidence, preservation failure, and contradiction.

## Epistemic boundaries

EPM preserves distinctions such as:

```text
valid evidence != authorized use
later evidence != evidence available earlier
more computation != new external observation
constraint != resolution
provenance != truth
verification != authority
```

Unknowns and contradictions remain representable instead of being silently normalized into confidence.

## EPM ↔ FAP Assurance Contract

Current `main` contains the bounded EPM/FAP Assurance Contract v1.

The contract keeps responsibilities separate:

- **EPM** owns assurance semantics and decision-boundary vocabulary.
- **FAP-Core** remains an evidence producer / verification component.
- **FAP-Insurance** remains a domain adapter and EPM runtime consumer.

FAP scores, confidence values, or verdicts do not automatically become EPM authority.

## Authority Envelope v1 — vNext research

Post-release `main` carries staged work for a domain-neutral authority contract that generalizes the existing evidence/use boundary into consequential action control.

Its central invariant is:

```text
capability != authority
```

A proposed action is explicitly bound to actor, action, resource, purpose, scope, jurisdiction, time, governing authority and policy. Raw caller claims cannot self-assert boundary validation. Non-authorized outcomes are execution-blocking, and explicit constraints remain attached to constrained authorization.

This is vNext research, not part of the frozen v0.1.1 or released v0.1.2 runtime and not a production deployment claim.

See `AUTHORITY-ENVELOPE-v1.md`.

## Supply-chain proof

EPM's hardened supply-chain workflow can verify an immutable release target without rewriting it. The current v0.1.2 proof chain includes controlled build identity, SBOM generation, artifact digests, machine-readable evidence receipts, independent verification, and GitHub/Sigstore attestation.

Supply-chain proof establishes provenance of the built artifact. It does not prove universal correctness.

## Release attestation

A separate post-release governance contract is being developed for a common machine-readable chain across EPM, FAP-Core, and FAP-Insurance:

```text
proposal → exact source → required checks → artifacts → dependencies
→ deployment evidence → runtime identity → rollback target
```

The attestation is evidence, not deployment authority.

## Adversarial validation

The repository includes the EPM Blackbox Gauntlet and the EPM Break Challenge.

The active public challenge target is:

- release: `v0.1.2`
- exact commit: `bb0559ddb8eff7f78acc432c0334ce7596c1045c`

The challenge is a technical falsification exercise, not a cash bounty.

See:

- `QUICKSTART.md`
- `RUNTIME.md`
- `EPM-BLACKBOX-GAUNTLET.md`
- `EPM-BREAK-CHALLENGE.md`
- `SUPPLY-CHAIN.md`
- `STANDARDS-INTEROP.md`

## License

MIT.
