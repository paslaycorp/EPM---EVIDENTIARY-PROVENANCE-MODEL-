# EPM Release Attestation v1

## Purpose

This contract makes the release chain machine-readable across EPM, FAP-Core, and FAP-Insurance.

A release attestation records what was proposed, what exact source revision was reviewed, which checks ran, which artifacts were produced, which dependency identities were verified, what was deployed, what runtime identity was observed, and what rollback target remains available.

The attestation is evidence. It is **not** itself deployment authority, decision authority, or proof that a component is correct.

## Canonical chain

```text
proposal / pull request
        ↓
exact source and merge identity
        ↓
required checks and evidence references
        ↓
artifact digests
        ↓
dependency identities
        ↓
deployment authority and deployed SHA
        ↓
runtime-observed SHA
        ↓
rollback target
```

Each step remains separately inspectable. Missing evidence is represented explicitly rather than inferred from neighboring fields.

## Cross-repository use

- **EPM** uses the contract for normative releases and for any published runtime artifact.
- **FAP-Core** uses the same contract for component releases and production deployments.
- **FAP-Insurance** uses the same contract for production releases and runtime verification.

Repositories may add separate domain-specific evidence records, but must not silently reinterpret the fields in this schema.

## Authority boundary

The record may state which workflow or operator performed deployment, but possession of a valid attestation does not grant that actor future deployment authority.

Likewise:

- a green check is not a release by itself;
- a release tag is not proof that a runtime is serving that revision;
- a runtime health response is not proof of source provenance unless bound to an exact revision;
- an artifact digest is not proof that deployment occurred;
- dependency verification does not transfer dependency authority into the consuming component.

## Failure semantics

Consumers must not fabricate absent evidence. Use explicit nulls or `performed: false` where the schema permits them.

A contradictory chain—for example, a deployed SHA that differs from the runtime-observed SHA—must remain visible as a contradiction. Consumers must not normalize those values into apparent agreement.

## Versioning

Schema identity:

`epm-release-attestation/1.0`

Breaking semantic changes require a new schema identity. Additive repository-specific evidence belongs outside this canonical object unless incorporated through a future versioned contract.
