# EPM supply-chain proof

EPM's runtime release boundary and its post-release repository state are intentionally separate.

The v0.1.1 runtime remains frozen at:

`87903f2d53531bf28d97f1271af62b6d9b3e64be`

The supply-chain workflow on current `main` can package and attest an explicit target ref without retargeting that release.

## Workflow

`.github/workflows/supply-chain.yml`

The workflow supports:

- future `v*` tag pushes; and
- manual dispatch for an exact ref, tag, branch, or SHA.

For the current release, dispatch it with:

`v0.1.1`

## Produced proof bundle

The workflow generates:

- Python wheel;
- source distribution;
- `epm-v0.1.1.cdx.json` CycloneDX 1.6 SBOM;
- `SHA256SUMS` over the built package artifacts and SBOM;
- GitHub build provenance attestations;
- a retained GitHub Actions artifact containing the proof bundle.

## Verification intent

The proof bundle is designed to answer:

- what source ref was checked out;
- what package identity/version was built;
- what exact artifact bytes were produced;
- what software component identity the SBOM declares;
- which GitHub workflow generated and attested the artifacts.

It deliberately does not claim that build provenance grants permission to use EPM in every downstream context.

That distinction is self-application of EPM's own boundary:

`provenance != authorization`

## Release handling

Do not move the `v0.1.1` tag to capture later workflow files.

The correct pattern is the inverse:

1. keep the release tag immutable;
2. run the newer supply-chain workflow from `main`;
3. tell the workflow to check out the immutable release target;
4. generate attestations over artifacts built from that exact target.

This preserves chronology instead of rewriting it.
