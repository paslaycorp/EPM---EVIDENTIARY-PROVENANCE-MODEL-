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

Final release branch:

`release/epm-v0.1.1-2026-09-14`

The runtime is certified on Python 3.12 and 3.13. FAP-Insurance consumes this exact commit in production.

v0.1.1 is a narrow corrective patch over the frozen v0.1.0 release. It adds explicit rejection of governing rules whose `effective_at` occurs after the historical epistemic state being inspected. It does not reopen the epistemic ladder, answer-space semantics, transition authorization model, or connector claims.

Historical v0.1.0 remains preserved at its own release branch and is not rewritten.

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
- `legal_secondary_use.py` — intact evidence can still be denied for unauthorized secondary use.

## External validation

The recommended red-team target is deliberately narrow:

> Make EPM authorize or accept a state where evidence gains applicability, authority, certainty, or temporal legitimacy that it did not possess.

See [`EXTERNAL-RED-TEAM.md`](EXTERNAL-RED-TEAM.md) for the attack contract and reporting format.

## Repository map

- `src/epm/` — standalone runtime
- `tests/` — certification and adversarial tests
- `examples/` — executable reference demonstrations
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
- TVC implementation;
- Variant Hunter implementation.

## License

MIT. See [`LICENSE`](LICENSE).
