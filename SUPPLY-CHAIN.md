# EPM supply-chain proof

EPM separates the immutable runtime release boundary from the workflow that later proves that release.

## Preserved release boundaries

The historical v0.1.1 runtime remains frozen at:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

The current corrective v0.1.2 runtime remains bound to:

`bb0559ddb8eff7f78acc432c0334ce7596c1045c`

Neither tag is moved to capture later workflow improvements.

## Workflow

`.github/workflows/supply-chain.yml`

The workflow supports:

- future `v*` tag pushes; and
- manual dispatch from `main` for an explicit ref, tag, branch, or SHA.

For the current corrective release, manually dispatch the workflow from `main` with:

`v0.1.2`

A manual release proof started from any branch other than `main` fails closed.

## Supply Chain Proof v2

EPM-SCP-V2 strengthens the proof boundary without changing EPM runtime semantics.

The producer job:

1. checks out the exact requested target;
2. requires Python 3.12.14;
3. uses the known-good build toolchain:
   - pip 26.2.1;
   - build 1.6.1;
   - packaging 26.3;
   - pyproject-hooks 1.3.3;
   - setuptools 84.0.0;
   - wheel 0.48.0;
4. builds with `python -m build --no-isolation`, preventing the build backend from silently resolving newer setuptools or wheel versions;
5. binds `SOURCE_DATE_EPOCH` to the target commit timestamp;
6. refuses to emit an incomplete dependency graph if runtime dependencies exist but have not been resolved;
7. generates a CycloneDX 1.6 SBOM that explicitly records the zero-runtime-dependency state and the build toolchain;
8. emits `EPM-RELEASE-EVIDENCE.json`, binding the target ref and SHA to the workflow SHA, package identity, runner context, toolchain, SBOM, and artifact digests;
9. generates `SHA256SUMS`;
10. uploads the proof bundle; and
11. creates GitHub/Sigstore build-provenance attestations over every file in the bundle.

The separate verifier job:

1. downloads the producer artifact on a second GitHub-hosted runner;
2. verifies every SHA-256 manifest entry;
3. re-evaluates the EPM release-evidence contract;
4. verifies the package and SBOM identity;
5. verifies each GitHub artifact attestation against:
   - the EPM repository;
   - `.github/workflows/supply-chain.yml`;
   - the exact workflow-source SHA;
   - the exact workflow-source ref; and
   - a policy that rejects self-hosted runners;
6. emits `EPM-VERIFICATION-RESULT.json`;
7. uploads that verification receipt; and
8. attests the verification receipt itself.

Receipt schemas:

- `schemas/release-evidence-v1.schema.json`
- `schemas/release-verification-v1.schema.json`

## Produced proof objects

The package proof bundle contains:

- Python wheel;
- source distribution;
- `epm-v<version>.cdx.json` CycloneDX 1.6 SBOM;
- `EPM-RELEASE-EVIDENCE.json`;
- `SHA256SUMS`;
- GitHub/Sigstore build-provenance attestations.

The verifier additionally produces:

- `EPM-VERIFICATION-RESULT.json`;
- a retained GitHub Actions verification artifact; and
- a provenance attestation for the verification receipt.

## Verification intent

The proof chain is designed to answer:

- which source ref and exact commit were packaged;
- which workflow commit performed the proof;
- which interpreter and build tools were used;
- which artifact bytes were produced;
- what runtime dependency state the SBOM represents;
- whether the proof bundle hashes are internally consistent;
- whether GitHub/Sigstore recognizes the expected signer workflow and source identity; and
- whether a separate verifier execution accepted the bundle under EPM-SCP-V2.

It deliberately does **not** claim that build provenance grants permission to use EPM in every downstream context.

That is self-application of EPM's own boundary:

`provenance != authorization`

## C2PA boundary

This workflow does not define or alter a C2PA Manifest, assertion, Manifest Repository contract, authorization rule, or permitted-action semantic.

C2PA interoperability remains an external interface question. EPM supply-chain receipts may later reference C2PA evidence, but this hardening pass does not assign C2PA semantics to EPM-native receipts.

## Remaining durability boundary

GitHub Actions proof artifacts are retained for 90 days. The attestations and transparency evidence remain separately addressable, but durable preservation of the proof bytes should be implemented as a separate publication policy rather than silently expanding this workflow's repository-write authority.
