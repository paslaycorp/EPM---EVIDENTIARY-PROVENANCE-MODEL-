# Domain-Neutral Evidentiary State v0.1

**Status:** vNext integration specification  
**Depends on:** Generic Evidentiary Envelope, Evidence Availability, Epistemic Source Typing, Constraint Model, Answer-Space Resolution, Justification Graph  
**Historical boundary:** EPM v0.2 closure remains frozen and unchanged

## 1. Purpose

The previous vNext increments deliberately introduced semantic machinery separately so each invariant could be attacked in isolation.

This specification defines the smallest aggregate object that can carry those implemented semantics as one domain-neutral evidentiary state without collapsing them into one score, verdict, or truth flag.

## 2. Aggregate state

```text
EvidentiaryState {
    schema_version
    state_id
    proposition
    assurance_state
    sources[]
    availability[]
    constraints[]
    answer_space?
    justification_graph?
    limitations[]
    unresolved_conditions[]
}
```

### Field roles

- `state_id` — stable identity of this evidentiary-state snapshot.
- `proposition` — the proposition/question-bearing subject to which this state pertains.
- `assurance_state` — existing transition-assurance `State`; preserves context, rule binding, and assurance properties.
- `sources` — typed records describing how information entered the system.
- `availability` — provenance-bearing evidence-availability records. Absence remains unknown.
- `constraints` — first-class immutable constraint records, including failed or invalidated constraints where preservation is required.
- `answer_space` — optional resolution-state snapshot when the proposition is represented as a candidate space.
- `justification_graph` — optional explicit support/dependency graph.
- `limitations` — declared limitations that must survive downstream serialization.
- `unresolved_conditions` — outstanding conditions material to resolution or closure.

These fields now exist because corresponding runtime semantics exist. They were intentionally absent from Generic Evidentiary Envelope v0.1 before those semantics were implemented.

## 3. No master confidence score

The aggregate MUST NOT collapse provenance, source typing, temporal availability, constraint status, answer-space state, graph integrity, applicability, and authorization into a single confidence number.

A caller may receive component assessments, but one component cannot silently override another boundary.

Examples:

- high confidence cannot repair broken provenance;
- a valid constraint cannot authorize an action;
- an acyclic graph cannot promote UNKNOWN;
- trusted availability cannot prove the proposition itself;
- a resolved answer-space cannot bypass applicability or authority checks.

## 4. Inspection report

The stable engine inspection surface returns typed component results rather than a universal true/false verdict:

```text
EvidentiaryStateReport {
    schema_version
    state_id
    structural_issues[]
    source_results[]
    availability_results[]
    constraint_results[]
    answer_space_result?
    graph_cycle_result?
    limitations[]
    unresolved_conditions[]
}
```

Structural validation determines whether the aggregate is well-formed enough to inspect. Semantic failures remain visible as their own typed states.

A failed constraint remains represented as a failed constraint; it is not deleted simply to make the aggregate structurally valid.

## 5. Stable engine façade

The public Python façade for this cycle exposes two primary operations:

1. `assess_transition(envelope)` — evaluate whether assurance survives a proposed source -> target transition;
2. `inspect_state(state)` — inspect the semantic integrity of a domain-neutral evidentiary-state snapshot.

Specialized modules remain available internally, but callers should not need to know FAP/DPIE implementation details.

## 6. FAP compatibility

FAP-Insurance continues to adapt its domain-specific request/context into the generic transition envelope.

FAP does not need to populate constraint, answer-space, source-typing, justification, or trusted-availability objects unless a real integration supplies them.

Absent semantic objects remain absent/unknown; they are never fabricated for completeness.

## 7. Adversarial integration probes

The aggregate/engine gate MUST demonstrate at least:

1. a state can carry a valid source, valid constraint, answer-space, and acyclic justification graph without semantic collapse;
2. an invalid constraint remains visible in the report and does not become effective narrowing;
3. missing availability remains `UNKNOWN` in the temporal report;
4. graph circularity remains visible even when other components are valid;
5. limitations and unresolved conditions survive inspection unchanged;
6. no component report produces an authorization decision unless the separate transition/Governor path is invoked.

## 8. Claim boundary

Passing this gate establishes a coherent domain-neutral state representation and stable engine façade over the implemented vNext semantic components.

It does not claim that every production adapter supplies every component.

It does not promote C-21 to production PASS and does not alter the frozen v0.2 matrix.

TVC and Variant Hunter remain outside this cycle.
