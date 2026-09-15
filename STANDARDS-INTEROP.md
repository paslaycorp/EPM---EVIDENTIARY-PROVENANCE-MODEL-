# EPM standards interoperability map

## Provenance is not permission

EPM is positioned beside provenance standards, not on top of them as a replacement.

The interoperability boundary is:

`verifiable provenance -> evidentiary state -> permitted use decision`

A provenance system can establish what it is designed to establish about an artifact, manifest, build, repository event, or chain of transformations. EPM then asks a different question:

> Does that evidence remain legitimately applicable here, now, under this rule, authority, jurisdiction, purpose, scope, and consequence?

That distinction is the integration surface.

## C2PA 2.4

The current C2PA 2.x line provides standardized Content Credentials for source/history provenance and validation of media/content manifests. EPM does not reimplement C2PA validation.

A C2PA-aware adapter should keep these layers separate:

1. **C2PA validation result** — what the manifest, assertions, trust material, and content binding establish.
2. **EPM evidentiary state** — how that validated result is typed, when it became available to the decision system, its provenance references, and its limitations.
3. **EPM transition assurance** — whether use of that evidentiary state is preserved when purpose, scope, jurisdiction, authority, rule/version, time, or consequence changes.

### Repository receipt boundary

C2PA 2.4 introduces a repository receipt assertion for proof that a C2PA Manifest was ingested by a C2PA Manifest Repository.

That maps naturally to an EPM **bounded availability fact** when the integration can authenticate and bind the receipt to the exact evidentiary reference.

It does **not** automatically prove:

- when the underlying media first existed;
- when a camera captured it;
- that the media was available to an earlier decision system;
- that the media is admissible or authorized for every downstream purpose.

The clean mapping is:

`repository receipt time = evidence of repository ingestion`

not:

`repository receipt time = universal media-origin time`

This is the same temporal separation EPM already enforces between claimed event time, evidence availability time, and decision-state time.

## SLSA 1.2

SLSA 1.2 addresses software supply-chain security through source/build tracks and provenance attestations.

EPM's package pipeline can use SLSA-style provenance for EPM itself while keeping that evidence distinct from EPM's runtime semantics.

The repository workflow `.github/workflows/supply-chain.yml` produces:

- wheel;
- source distribution;
- SHA-256 manifest;
- CycloneDX SBOM;
- GitHub build provenance attestation.

This is **supply-chain evidence**, not a claim that the repository has achieved a particular SLSA level.

A formal SLSA conformance claim would require evaluating the applicable SLSA track requirements independently.

## CycloneDX

The package proof bundle contains a CycloneDX 1.6 SBOM for the EPM distribution identity.

EPM v0.1.1 has zero core runtime dependencies. The SBOM therefore describes the package as a library component without inventing runtime dependency components that do not exist.

Build tooling is not represented as an EPM runtime dependency.

## GitHub build provenance

The supply-chain workflow uses GitHub's artifact attestation mechanism to bind produced artifacts to the workflow execution that generated them.

The attestation answers a build-provenance question. It does not answer whether a downstream system is authorized to use the artifact for a particular purpose.

That gives EPM an intentionally recursive posture:

- provenance evidence can be supplied **to** EPM;
- EPM's own distribution can itself carry provenance evidence;
- neither fact collapses provenance into permitted downstream use.

## Interoperability rule

No external standard input should enter EPM as `AUTHORIZED` merely because that standard's validation succeeded.

Validation should enter as typed evidence with explicit provenance and limitations. Authorization remains a separate EPM transition question.

In short:

`authentic != applicable`

`valid != authorized`

`available now != available then`

`derived != observed`

`provenance proof != permission proof`

## Non-claim

This document is a non-normative interoperability map. It does not claim certification, endorsement, formal C2PA conformance, formal SLSA conformance, or legal admissibility.
