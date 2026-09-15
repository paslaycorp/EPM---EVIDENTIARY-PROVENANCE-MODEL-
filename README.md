# EPM — Evidentiary Provenance Model

**Domain-neutral evidentiary integrity and transition-assurance engine**  
**Current release: v0.1.1 — corrective production release**

EPM prevents evidence, conclusions, and downstream decisions from gaining certainty, applicability, authority, or temporal legitimacy that their evidence and governing context do not support.

Its core question is:

> Even if this evidence is valid, are we legitimately allowed to use it here, now, under this rule, for this purpose, and with this consequence?

EPM is not a universal truth engine and does not emit a master confidence score.

## Current release boundary

The verified v0.1.1 runtime is commit:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

Release tag:

`v0.1.1`

Final release branch:

`release/epm-v0.1.1-2026-09-14`

The runtime is certified on Python 3.12 and 3.13. FAP-Insurance consumes this exact commit in production.

v0.1.1 is a narrow corrective patch over the frozen v0.1.0 release. It adds explicit rejection of governing rules whose `effective_at` occurs after the historical epistemic state being inspected. It does not reopen the epistemic ladder, answer-space semantics, transition authorization model, or connector claims.

Historical v0.1.0 remains preserved at its own release branch and is not rewritten.

Post-release files on `main` add documentation, examples, adversarial validation tooling, governance targets, and supply-chain proof. They do not redefine the v0.1.1 runtime release commit.

## Install

For reproducibility, install the verified release commit directly:

```bash
python -m pip install "git+https://github.com/paslaycorp/EPM---EVIDENTIARY-PROVENANCE-MODEL-.git@87903f2d53531bf28d97f1271af62b6d9b3e64be"
```

Verify the engine identifier:

```bash
python -c "import epm; print(epm.EPM_ENGINE_VERSION)"
```

Expected:

```text
epm-engine/0.1.1
```

## Public API

```python
from epm import assess_transition, inspect_state, audit_state
```

EPM also exposes typed primitives for:

- assurance context and rule binding;
- evidentiary transition envelopes;
- preservation proofs;
- evidence availability and temporal checks;
- source typing;
- constraints and answer-space handling;
- justification graphs and dependency invalidation;
- deterministic audit artifacts.

Reference adapters are included for insurance, legal/evidentiary, and scientific evidence use.

## Decision vocabulary

EPM returns explicit decision states rather than a scalar truth score:

- `AUTHORIZED`
- `AUTHORIZED_WITH_CONSTRAINTS`
- `DEFER`
- `QUARANTINE`
- `DENY`

Typical failure boundaries include:

- misapplication across purpose or scope;
- authority mismatch;
- jurisdiction mismatch;
- temporal mismatch;
- rule/version mismatch;
- unresolved composition;
- unestablished preservation;
- contradictory evidence.

## Temporal integrity

EPM treats these as different facts:

`claimed event time != evidence availability time != decision-state time`

A later receipt does not make evidence available to an earlier decision state. Production FAP proves a bounded authenticated receipt boundary: when FAP actually possessed an exact evidence reference. That does not prove when the underlying media originally came into existence.

v0.1.1 adds a second temporal guard at state inspection:

`rule effective time > historical state time -> RULE_NOT_YET_EFFECTIVE`

A rule cannot silently govern a state that predates the rule itself.

## Epistemic boundary

The runtime preserves the distinction:

`same evidence + more computation != new external observation`

Computation may produce a valid derivation without upgrading that derivation into a new observation.

Likewise:

`constraint != resolution`

A narrowed or even singleton answer-space can remain unresolved until legitimate external observation supplies the missing discriminator outcome.

## Five-minute start

See [`QUICKSTART.md`](QUICKSTART.md).

Executable examples are under [`examples/`](examples/):

- `basic_transition.py` — unchanged context authorizes;
- `temporal_availability.py` — later evidence cannot be used retroactively;
- `future_effective_rule.py` — a future-effective rule cannot govern an earlier state;
- `legal_secondary_use.py` — intact evidence can still be denied for unauthorized secondary use;
- `legal_chain_of_custody.py` — explicit custody/use preservation authorizes one legal use while unauthorized secondary disclosure is denied.

## Blackbox Gauntlet

The repository includes a machine-readable adversarial harness:

[`EPM-BLACKBOX-GAUNTLET.md`](EPM-BLACKBOX-GAUNTLET.md)

Run it with:

```bash
python tools/epm_gauntlet.py --output validation-receipt.json
```

The gauntlet attacks purpose, scope, jurisdiction, time, rule/version, authority, UNKNOWN inflation, future-rule leakage, evidence-availability leakage, computation-to-observation laundering, and derivation-to-resolution laundering.

It emits an `epm.external-validation-receipt/1.0` artifact instead of a confidence score. A failed invariant makes the process exit non-zero.

## $1,000 EPM Break Prize

The frozen v0.1.1 boundary is now under an open adversarial research prize.

The first independent researcher to produce a complete, reproducible **material invariant violation** against the exact v0.1.1 runtime receives **US$1,000** after the finding is independently reproduced and eligibility is verified.

The target does not move:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

See [`EPM-BREAK-PRIZE.md`](EPM-BREAK-PRIZE.md) for the formal rules and [`BREAK-PRIZE-ANNOUNCEMENT.md`](BREAK-PRIZE-ANNOUNCEMENT.md) for the concise public challenge.

> Don’t tell me EPM works. Don’t tell me it doesn’t. Make the evidence decide.

## External validation

The recommended red-team target remains deliberately narrow:

> Make EPM authorize or accept a state where evidence gains applicability, authority, certainty, or temporal legitimacy that it did not possess.

See [`EXTERNAL-RED-TEAM.md`](EXTERNAL-RED-TEAM.md) for the attack contract and reporting format.

The Blackbox Gauntlet does not replace independent review. It gives an independent reviewer a common attack deck and a reproducible receipt format.

## Supply-chain proof

See [`SUPPLY-CHAIN.md`](SUPPLY-CHAIN.md).

The post-release supply-chain workflow can build an exact target ref and produce:

- wheel and source distribution;
- SHA-256 manifest;
- CycloneDX 1.6 SBOM;
- GitHub build provenance attestations.

The v0.1.1 tag remains immutable; newer workflow machinery checks out that exact target instead of moving the tag.

## Standards interoperability

See [`STANDARDS-INTEROP.md`](STANDARDS-INTEROP.md).

The central interoperability rule is:

`provenance proof != permission proof`

EPM can consume validated provenance evidence from systems such as C2PA while separately governing whether that evidence may support a particular action under the current purpose, scope, authority, jurisdiction, rule, time, and consequence.

## Governance

The exact intended `main` ruleset is committed under:

- [`08_GOVERNANCE/main-ruleset-target.json`](08_GOVERNANCE/main-ruleset-target.json)
- [`08_GOVERNANCE/main-ruleset-application.md`](08_GOVERNANCE/main-ruleset-application.md)

The ruleset requires the PR path, both Python 3.12/3.13 EPM Runtime CI checks, strict up-to-date branches, force-push blocking, deletion blocking, and a named PR-only emergency bypass. Applying the repository-admin control remains a GitHub administration boundary.

## Repository map

- `src/epm/` — standalone runtime
- `tests/` — certification and adversarial tests
- `examples/` — executable reference demonstrations
- `tools/` — external validation tooling
- `schemas/` — machine-readable interoperability/validation schemas
- `01_CANONICAL/` — canonical architecture material
- `03_SPEC/` — adversarial specification
- `04_TESTS/` — conformance records
- `05_COUNTEREXAMPLES/` — failure cases
- `07_DECISION_LOG/` — provenance and release decisions
- `08_GOVERNANCE/` — change-control rules

Historical research artifacts remain preserved. They are not rewritten to manufacture a cleaner chronology.

## Non-claims

EPM v0.1.1 does **not** claim:

- universal truth determination;
- universal domain completeness;
- that confidence overrides typed uncertainty;
- that capture time proves evidence availability;
- that a valid artifact is automatically applicable to a new purpose;
- that computation becomes observation;
- formal C2PA certification or endorsement;
- formal SLSA level conformance;
- universal legal admissibility;
- TVC implementation;
- Variant Hunter implementation.

## License

MIT. See [`LICENSE`](LICENSE).
