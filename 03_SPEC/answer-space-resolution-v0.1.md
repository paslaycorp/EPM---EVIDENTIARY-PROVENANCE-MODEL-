# Answer-Space and Resolution State v0.1

**Status:** vNext implementation specification  
**Depends on:** First-Class Constraint Model v0.1 and Epistemic Source Typing v0.1  
**Targets:** implementation foundation for C-04, C-09, C-13 and executable Two-Stage Trust Architecture  
**Historical boundary:** EPM v0.2 closure remains frozen and unchanged

## 1. Purpose

EPM must distinguish narrowing an answer-space from resolving an answer and must distinguish resolution from closure.

The resolution state is intentionally orthogonal to epistemic standing.

## 2. Resolution state

The executable vocabulary is:

- `UNRESOLVED` — no effective narrowing or resolution has been established;
- `CONSTRAINED` — valid constraints have changed the admissible answer-space, but no answer is yet established as resolved;
- `RESOLVED` — legitimate discriminating evidence has selected an admissible answer;
- `CLOSED` — resolution exists and explicit closure conditions establish that the declared answer domain and resolution basis are sufficient for closure.

`DERIVED` is deliberately NOT a resolution state. It remains an epistemic standing.

## 3. Epistemic standing

The resolution layer records standing separately:

- `UNKNOWN`
- `OBSERVED`
- `EVIDENCED`
- `DERIVED`
- `INFERRED`
- `PREDICTED`

Computation over existing evidence may produce `DERIVED`; it does not by itself move resolution to `RESOLVED` or `CLOSED`.

## 4. Answer-space snapshot

```text
AnswerSpaceSnapshot {
    question_id
    candidate_universe[]
    admissible_candidates[]
    resolution_state
    epistemic_standing
    active_constraint_refs[]
    discriminator_refs[]
    granularity
    granularity_basis
    history[]
}
```

The candidate universe is preserved so invalidated constraints can reopen previously excluded possibilities.

## 5. Constraint application

Only constraints whose current evaluation is `VALID` may exclude candidates.

Recomputation is performed from the preserved candidate universe and the currently valid constraint set.

The resulting history event records one of:

- `NARROWED`
- `WIDENED`
- `REOPENED`
- `UNCHANGED`

A singleton produced only by valid exclusions remains `CONSTRAINED` unless independent resolution evidence establishes the remaining answer.

## 6. Discriminator

A discriminator specifies how possible observations partition the current alternatives.

```text
Discriminator {
    discriminator_id
    alternatives[]
    observation_partition{}
    provenance_refs[]
}
```

A discriminator is sufficient for a current answer-space only if its declared partition covers the relevant alternatives and can distinguish them at the granularity required by the question.

The discriminator is not itself the later observation.

## 7. Stage 2 observation

Resolution requires an actual source-typed `OBSERVATION` entering after the discriminator has been defined, or equivalent legitimate evidence with an explicit resolution contract.

A model output, derivation, prediction, assertion, or discriminator definition cannot masquerade as the Stage 2 observation.

## 8. Closure

Closure is stronger than resolution.

A resolved answer may become `CLOSED` only when an explicit closure basis establishes at least:

- the declared candidate domain is exhaustive for the question at the stated granularity;
- closure basis/provenance references are non-empty;
- the resolution was not manufactured solely by computation over unchanged evidence;
- no active unresolved condition remains material to the closure claim.

Cardinality one is not a closure condition.

## 9. Granularity

The answer-space MUST identify its representation granularity and why that granularity fits the question/evidence.

A coarse or over-refined representation cannot be mistaken for an epistemic fact merely because it changes cardinality.

## 10. Adversarial probes

The executable gate MUST demonstrate at least:

1. `{X,Y} -> {X}` by constraint remains `CONSTRAINED`, not `RESOLVED`;
2. stronger computation over the same evidence remains `DERIVED` and does not close the answer-space;
3. an insufficient discriminator cannot resolve the current alternatives;
4. a discriminator definition cannot serve as its own observation;
5. a valid external observation plus a sufficient discriminator can produce `RESOLVED`;
6. resolution does not become `CLOSED` without explicit exhaustive closure basis;
7. invalidating a constraint can widen/reopen the answer-space from preserved history;
8. missing granularity basis prevents a valid answer-space claim.

## 11. Claim boundary

Passing this gate creates executable machinery for the C-04/C-09/C-13 distinctions and for Stage 1 -> Stage 2 resolution.

It does not yet establish circular-support detection; that requires the justification graph gate.

It does not change the historical v0.2 matrix or claim production conformance for FAP traffic that does not carry these semantic objects.
