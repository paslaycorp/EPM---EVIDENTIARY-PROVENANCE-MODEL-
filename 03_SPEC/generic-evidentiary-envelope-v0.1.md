# Generic Evidentiary Envelope v0.1

**Status:** vNext implementation specification — initial compatibility boundary  
**Baseline:** EPM v0.2 closure remains frozen and unchanged  
**Scope:** smallest domain-neutral transport for the assurance semantics already enforced by the FAP/DPIE runtime

## 1. Purpose

The first EPM vNext increment is not a new constraint engine, answer-space engine, source-typing system, dependency graph, or temporal-provenance system.

It introduces a domain-neutral envelope around the transition semantics that already exist so insurance can become an adapter rather than the architectural center of EPM.

The envelope MUST preserve the existing separation between:

- evidentiary/assurance state;
- source and target application context;
- rule binding and authority;
- materiality;
- preservation proof;
- governance consequence.

It MUST NOT infer new evidence, fabricate provenance, promote UNKNOWN, or create evidence-availability chronology.

## 2. Minimal schema

```text
EvidentiaryEnvelope {
    schema_version
    transition_id
    source: State
    target: State
    material_properties
    preservation
    consequence
}

State {
    state_id
    properties
    context
    rule_binding
}

Context {
    identity
    purpose
    scope
    jurisdiction
    at
}

RuleBinding {
    rule_id
    version
    authority
    jurisdiction
    effective_at
}
```

`State`, `Context`, `RuleBinding`, and `PreservationProof` deliberately reuse the already-executed assurance primitives rather than introducing parallel semantics.

## 3. Why this is the minimum

Every field exists because the current FAP/DPIE boundary already requires it to reproduce an enforced decision.

- `transition_id` binds the decision and any preservation proof to a specific transition.
- `source` carries the current assurance state plus the context and rule under which that state exists.
- `target` carries the proposed use context and governing rule without silently rewriting the source state.
- `material_properties` states which assurance properties require explicit preservation across the transition.
- `preservation` carries the existing proof objects used to establish legitimate preservation.
- `consequence` is required by the Governor to distinguish ordinary quarantine from critical denial.
- `schema_version` is required so later typed semantic additions cannot silently change the meaning of a frozen envelope.

No insurance-specific field belongs in the generic envelope.

## 4. FAP compatibility contract

The existing insurance request remains intact. A FAP adapter MAY construct the generic envelope from the current request-local assurance context and verification result.

For compatibility with the frozen v0.2 runtime, the adapter MUST initially preserve these mappings exactly:

1. `STRICT` or `PROBABLE` source verdict -> `PRESERVED` for the currently modeled assurance properties.
2. Any other source verdict -> `UNKNOWN`; it MUST NOT be converted to invalidity.
3. The target may request `applicability = PRESERVED`, but that declaration MUST NOT strengthen a weaker source state.
4. Purpose, scope, jurisdiction, time, rule id, rule version, or rule authority change -> `applicability` is material.
5. A material transition requires the same preservation-proof checks already enforced by the frozen runtime.
6. Governance remains separate from evidence evaluation and maps evaluated assurance to `AUTHORIZED`, `DEFER`, `QUARANTINE`, or `DENY` according to existing rules.

The first adapter is a compatibility bridge. It does not require rewriting `VerifyClaimRequest` or the existing insurance API.

## 5. Explicitly absent from v0.1

The following future EPM subsystems are intentionally NOT represented as implemented semantics in this envelope version:

- detailed provenance objects;
- epistemic source typing (`OBSERVATION`, `DERIVATION`, `DISCRIMINATOR`, etc.);
- first-class constraints;
- answer-space or closure state;
- justification/dependency graph edges;
- trusted evidence-availability provenance;
- temporal bridges as a generic EPM semantic object.

These capabilities require later typed schema additions, executable adversarial probes, failure behavior, and a new conformance claim.

Opaque catch-all fields such as `metadata`, `extensions`, or arbitrary semantic dictionaries are intentionally excluded from the normative core because they could bypass typed provenance and boundary checks.

## 6. C-21 boundary

`timestamp_claimed`, `capture_time`, and `processed_at` are NOT evidence-availability time.

Generic Evidentiary Envelope v0.1 does not create an `evidence_available_at` field and does not change the frozen C-21 determination.

The existing FAP temporal-admissibility helper remains a compatibility-side precondition when its trusted input is explicitly supplied. Production C-21 conformance remains excluded until evidence availability has trustworthy end-to-end provenance.

## 7. First executable gate

The first vNext gate is semantic parity, not feature expansion.

A FAP -> Generic Envelope adapter must demonstrate, with fresh execution, that the generic path matches the frozen runtime for at least:

- UNKNOWN preservation against a stronger target declaration;
- material purpose/context misapplication;
- valid explicit preservation;
- the existing late-evidence temporal helper boundary.

Only after parity passes may the production FAP path be considered for routing through the generic envelope.

## 8. Claim boundary

Passing this gate establishes only that a domain-neutral envelope can carry the already-enforced transition-assurance semantics without weakening them.

It does NOT claim implementation of C-03 through C-13 or C-21, and it does not modify the EPM v0.2 closure record.
