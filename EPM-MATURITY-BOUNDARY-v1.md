# EPM Maturity Boundary v1

## Rule

EPM Core currently stops at **definition of admissibility**.

It may determine whether a proposed consequential transition is:

- `AUTHORIZED`
- `AUTHORIZED_WITH_CONSTRAINTS`
- `DEFER`
- `QUARANTINE`
- `DENY`

It may emit evidence-bound decision receipts.

It does not perform the external action it evaluates.

## Permanent architecture

```text
evidence / request
       |
       v
+------------------+
|     EPM CORE     |
|    DEFINITION    |
+------------------+
       |
       | evidence-bound decision
       v
========== EPM CORE BOUNDARY ==========
       |
       v
+------------------+
|   ENFORCEMENT    |
| external adapter |
+------------------+
       |
       v
+------------------+
|    EXECUTION     |
| external actor   |
+------------------+
       |
       v
+------------------+
| EXECUTION EVID.  |
| external record  |
+------------------+
```

The four layers are distinct:

[
Definition \neq Enforcement \neq Execution \neq ExecutionEvidence
]

An integrated future product may package them together. Integration does not erase their boundaries.

## Present maturity

Current stage:

```text
M1 / definition_only
```

EPM Core owns:

- admissibility evaluation;
- evidence and authority binding;
- explicit constraint definition;
- fail-closed decision states;
- decision-receipt emission.

EPM Core does **not** own:

- external mutation;
- credential exercise;
- network action;
- process execution;
- enforcement of constraints in an external runtime;
- proof that an executor obeyed a decision;
- production deployment authority.

The canonical machine-readable contract is:

`contracts/epm-maturity-boundary-v1.json`

Its validation schema is:

`schemas/epm-maturity-boundary-v1.schema.json`

## Maturity gates

### M1 — Definition

Current state.

Required:

- Authority Envelope contract;
- machine-readable decision receipt;
- fail-closed behavior;
- adversarial authority tests;
- no execution capability in the EPM authority path.

### M2 — Reference enforcement

Future, non-production.

An external adapter may translate the EPM decision into enforceable runtime limits.

Required before entering M2:

- adapter is separately versioned;
- adapter cannot mint EPM decisions;
- constraints are translated without silent widening;
- EPM Core still cannot execute;
- bypass attempts are tested.

### M3 — Reference execution

Future, non-production.

A separately identified executor may perform a permitted operation.

Required:

- constrained executor;
- execution receipt;
- proof that an authorized operation can execute;
- proof that a denied operation physically does not execute;
- explicit irreversible-side-effect classification.

Authorization does not imply execution:

[
Authorized(x) \not\Rightarrow Executed(x)
]

### M4 — Independent adversarial validation

Before production claims, the complete chain must withstand independent attacks against:

- direct enforcement bypass;
- executor bypass;
- grant replay;
- decision-receipt substitution;
- revocation races;
- request mutation after decision;
- TOCTOU changes;
- constraint escape;
- identity substitution;
- authority escalation.

### M5 — Integrated distribution

Only after prior stages mature may definition, enforcement, execution, and evidence ship as one integrated distribution.

Even then:

- each layer remains separately identifiable;
- each layer remains independently versioned;
- enforcement remains replaceable;
- the executor remains replaceable;
- execution evidence remains independently inspectable;
- EPM Core does not acquire execution authority merely because the layers share a product boundary.

## Anti-collapse invariants

The following are permanent:

[
Evaluation \neq AuthoritySource
]

[
Definition \neq Enforcement
]

[
Enforcement \neq Execution
]

[
Execution \neq EvidenceOfExecution
]

[
Authorized(x) \not\Rightarrow Executed(x)
]

[
ExecutionEvidence(x) \not\Rightarrow RetroactiveAuthorization(x)
]

A later maturity stage cannot reinterpret what was justified at an earlier stage.

## Integration rule

A future component consuming EPM must treat an EPM decision as a **definition of admissibility**, not as self-executing authority.

A future enforcer must not allow an executor to widen:

- actor;
- action;
- resource;
- purpose;
- scope;
- jurisdiction;
- time;
- authority;
- policy;
- constraints.

A future execution-evidence layer records what occurred. It does not rewrite the prior authorization state.

## Release boundary

This governance contract is post-release work.

It does not alter:

- v0.1.1 — `87903f2d53531bf28d97f1271af62b6d9b3e64be`
- v0.1.2 — `bb0559ddb8eff7f78acc432c0334ce7596c1045c`

No production enforcement, execution, deployment, or runtime-assurance claim is made by this contract.
