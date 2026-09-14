# First-Class Constraint Model v0.1

**Status:** vNext implementation specification  
**Depends on:** Epistemic Source Typing v0.1  
**Targets:** implementation foundation for C-03, C-05, C-06, C-07  
**Historical boundary:** EPM v0.2 closure remains frozen and unchanged

## 1. Purpose

A constraint is an evidentiary-semantic object that narrows admissible possibilities only when its supporting premises, provenance, assumptions, and entailment are established.

A constraint is not a boolean and is not evidence merely because applying it narrows an answer-space.

## 2. Minimal object

```text
Constraint {
    constraint_id
    proposition
    premise_refs[]
    premise_states{}
    provenance_refs[]
    entailment_basis
    entailment_status
    dependency_refs[]
    assumptions[]
    excluded_candidates[]
    source_ref
    review_status
    revision_of
}
```

Constraint objects are immutable. Revision creates a new constraint with a new identifier and an explicit `revision_of` link; historical states are not overwritten.

## 3. Premise state

A premise has one of these states:

- `ESTABLISHED`
- `UNKNOWN`
- `INVALIDATED`
- `CONTRADICTED`

A constraint cannot be effective as a valid narrowing operation when any required premise is `UNKNOWN`, `INVALIDATED`, or `CONTRADICTED`.

## 4. Entailment state

Entailment has one of these states:

- `ESTABLISHED`
- `UNESTABLISHED`
- `CONTRADICTED`

A plausible exclusion is not sufficient. The declared premise set and assumptions must support an explicit entailment basis.

## 5. Constraint evaluation states

Evaluation produces one of:

- `VALID` — premises, provenance, entailment, and required review are established;
- `UNSUPPORTED` — the constraint lacks established premises, provenance, entailment, or required review;
- `INVALIDATED` — a supporting premise has been invalidated;
- `CONTRADICTED` — a supporting premise or entailment relation is contradicted;
- `REJECTED` — required governance review explicitly rejected the constraint.

The evaluator MUST report why a constraint is not valid; it must not reduce all failure modes to false.

## 6. Adversarial narrowing

A preference, desired outcome, model prediction, or actor assertion MUST NOT become a valid constraint merely because it excludes unwanted candidates.

Where governance marks a constraint as requiring independent review, the constraint remains unsupported until review is explicitly approved.

Review approval does not repair missing entailment or provenance.

## 7. Failure propagation

If a premise supporting a valid constraint is later invalidated or contradicted, a newly evaluated revision MUST become `INVALIDATED` or `CONTRADICTED` as appropriate.

Any answer-space or conclusion depending on that constraint must later be able to reopen or become stale. The constraint layer exposes the dependency and revision information required for that propagation; it does not silently preserve prior narrowing.

## 8. Monotonicity and revision

Constraint history is append-only in semantic identity:

- new constraints may narrow;
- invalidation may reopen;
- revised assumptions may widen or change the admissible set;
- no historical constraint object is silently rewritten to make the latest state appear inevitable.

Actual answer-space narrowing/widening/reopening is handled by the resolution-state layer, which must retain this history.

## 9. Adversarial probes

The executable gate MUST demonstrate at least:

1. a valid constraint requires established premises, provenance, and entailment;
2. plausible-but-unestablished entailment produces `UNSUPPORTED`;
3. an invalidated premise produces `INVALIDATED`;
4. a contradicted premise/entailment produces `CONTRADICTED`;
5. governance-required but unapproved adversarial narrowing cannot become `VALID`;
6. governance rejection produces `REJECTED`;
7. a revision is a distinct immutable object linked to its predecessor;
8. exclusions on an invalid/unsupported constraint are not treated as effective narrowing.

## 10. Claim boundary

Passing this gate creates executable constraint semantics sufficient for the core C-03/C-05/C-06/C-07 distinctions.

It does not yet claim full production conformance because FAP production traffic does not carry general constraint objects.

It does not itself implement answer-space resolution or circular dependency analysis.
