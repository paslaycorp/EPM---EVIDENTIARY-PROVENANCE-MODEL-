# EPM Authority Envelope v1 — vNext Research Contract

## Status

This document defines an experimental, domain-neutral authority layer on post-release EPM `main`.

It does **not** rewrite or retag:

- EPM v0.1.1 — `87903f2d53531bf28d97f1271af62b6d9b3e64be`
- EPM v0.1.2 — `bb0559ddb8eff7f78acc432c0334ce7596c1045c`

It does not itself deploy software, open network connections, write databases, send messages, use credentials, allocate compute, or perform any other external action.

## Problem

A system can possess the technical capability to perform an action without possessing authority to perform it.

EPM therefore treats the following as non-equivalent:

```text
capability != authority
reachability != permission
successful execution != authorized execution
valid evidence != authorized use
self-asserted trust != boundary-validated trust
```

The Authority Envelope makes the authority question explicit before a consequential state transition is permitted.

## Request contract

Each proposed transition binds:

```text
actor
action
resource
purpose
scope
jurisdiction
time
governing authority
policy id
policy version
consequence
```

The canonical machine-readable request schema is:

`schemas/epm-authority-request-v1.schema.json`

The request schema deliberately has `additionalProperties: false`. A caller cannot add `validated`, `boundary_validated`, or another trust-bearing boolean to promote its own request.

## Authority basis

An `AuthorityGrant` is only a claim until an external ingestion-boundary validator authenticates the authority evidence it controls.

The EPM kernel separates:

```text
AuthorityGrant
        |
        | external authentication / verification
        v
establish_authority_basis(...)
        |
        v
ValidatedAuthorityBasis
        |
        v
evaluate_authority_request(...)
```

The factory checks structural completeness, explicit evidence references, timezone comparability, validity intervals and revocation evidence. It does not discover external authority by itself.

Boundary adapters remain responsible for authenticating the issuer, signature, credential, policy source, capability token, legal authority, organizational delegation or other domain-specific authority evidence before establishing a typed basis.

A raw mapping, caller boolean, score, verdict, confidence value, successful network connection, available credential or executable capability cannot substitute for that boundary decision.

## Evaluation

For request (R), validated basis (B), and proposed time (t), authorization requires all material dimensions to remain covered:

[
Authorize(R,B,t) =
Actor
\land Action
\land Resource
\land Purpose
\land Scope
\land Jurisdiction
\land Policy
\land Authority
\land Time
\land Evidence
\land \neg Revoked
]

The current decision vocabulary remains:

- `AUTHORIZED`
- `AUTHORIZED_WITH_CONSTRAINTS`
- `DEFER`
- `QUARANTINE`
- `DENY`

Only the first two set `permitted=true`.

Every other result sets `fail_closed=true`.

An executor integrating this contract MUST gate mutation on `result.permitted`. It MUST NOT infer permission from the ability to perform the operation.

## Failure vocabulary

Authority Envelope v1 makes the failure dimension explicit:

- `INVALID_REQUEST`
- `AUTHORITY_UNESTABLISHED`
- `BOUNDARY_UNVALIDATED`
- `EVIDENCE_UNESTABLISHED`
- `ACTOR_MISMATCH`
- `ACTION_MISMATCH`
- `RESOURCE_MISMATCH`
- `PURPOSE_MISMATCH`
- `SCOPE_MISMATCH`
- `JURISDICTION_MISMATCH`
- `POLICY_MISMATCH`
- `AUTHORITY_MISMATCH`
- `TEMPORAL_MISMATCH`
- `AUTHORITY_REVOKED`

## Temporal rules

Authority is time-bound evidence.

Authority Envelope v1 therefore preserves these invariants:

1. a grant cannot authorize use before `not_before`;
2. a grant cannot authorize use after `not_after`;
3. a validation performed later cannot retroactively authorize an earlier action;
4. revocation blocks transitions at and after the revocation time;
5. revocation does not rewrite whether a transition before revocation was authorized;
6. incomparable timezone state is not silently normalized.

This is the authority equivalent of EPM temporal non-retroactivity.

## Revocation

Revocation is not a mutable boolean that rewrites history.

The grant records:

```text
revoked_at
revocation_evidence_refs
```

A request before `revoked_at` is evaluated against the authority state that existed then.

A request at or after `revoked_at` is denied.

## Constraints

A valid grant may preserve explicit constraints.

For example:

```text
max_rows=1
no_schema_change
destination=approved-domain-only
monthly_cost_ceiling=50USD
human_approval_before_send
```

If constraints exist, a matching request returns:

`AUTHORIZED_WITH_CONSTRAINTS`

The constraints are copied into the decision receipt. They are not silently collapsed into ordinary authorization.

## Domain neutrality

The authority vocabulary uses strings so domains can define action and resource namespaces without changing the kernel.

Examples:

| Domain | Action | Resource |
| --- | --- | --- |
| Filesystem | `filesystem.read` | `file:/evidence/receipt.json` |
| Network | `network.connect` | `tcp:203.0.113.7:22` |
| Messaging | `message.send` | `mailbox:review@example.test` |
| Deployment | `deployment.release` | `service:claims-api` |
| Database | `database.write` | `db:claims/audit` |
| Credentials | `credential.use` | `credential:service-a` |
| Compute | `compute.execute` | `gpu:cluster-a` |
| Authority | `authority.grant` | `authority:agent-x` |

The kernel does not claim that those strings prove real-world identity. Adapters bind them to domain-native identities and evidence.

## Explicit wildcard

The literal `*` is the only universal match.

It is never inferred.

A blank set does not mean unrestricted authority. Every grant dimension must contain an explicit value.

This keeps least-authority behavior visible and reviewable.

## Adversarial requirements

The certification suite must demonstrate at least:

1. no basis → no permission;
2. raw self-asserted boundary validation → no permission;
3. network reachability → no network authority;
4. compute capability → no cryptocurrency-mining authority unless explicitly granted;
5. one actor cannot borrow another actor's grant;
6. a source-code grant cannot self-expand into `authority.grant`;
7. purpose, scope, jurisdiction, policy and authority cannot silently change;
8. future validation cannot authorize a past transition;
9. expired grants are denied;
10. revocation blocks future use without rewriting earlier state;
11. constraints survive the decision;
12. the same kernel evaluates multiple action domains without embedding their business logic.

## Decision receipt

The canonical receipt schema is:

`schemas/epm-authority-decision-receipt-v1.schema.json`

A receipt binds:

```text
transition id
decision
failure code
reason
permitted
fail-closed state
grant id
boundary validator id
constraints
evidence references
```

A receipt is evidence of the EPM authority evaluation. It is not proof that an external executor obeyed the result.

## Execution boundary

Recommended integration:

```text
proposed action
    |
    v
Authority Request
    |
    v
authenticated authority evidence
    |
    v
boundary validator
    |
    v
ValidatedAuthorityBasis
    |
    v
EPM Authority evaluation
    |
    +---- permitted=false ---> stop / record / escalate
    |
    +---- permitted=true ----> constrained executor
                                  |
                                  v
                             execution receipt
```

The executor SHOULD separately record what actually happened, including the exact decision receipt, action identity, runtime identity, result, side effects and rollback state.

That downstream execution receipt is intentionally not claimed by this v1 contract.

## Production proof still required

Repository correctness is not runtime proof.

Before claiming a production implementation of Authority Envelope v1, an integration must demonstrate, at minimum:

1. exact EPM source revision;
2. exact adapter and executor revisions;
3. authenticated runtime identities;
4. real boundary-validation evidence;
5. a permitted transition that executes only after authorization;
6. a non-permitted transition that demonstrably does not execute;
7. revocation behavior;
8. decision and execution receipts;
9. rollback or irreversible-side-effect classification;
10. independent adversarial reproduction.

Until those exist, this remains a tested vNext authority contract, not a production assurance claim.
