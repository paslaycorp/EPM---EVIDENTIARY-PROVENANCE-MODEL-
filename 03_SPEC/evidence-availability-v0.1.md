# Evidence Availability Provenance v0.1

**Status:** vNext implementation specification — typed foundation  
**Depends on:** Generic Evidentiary Envelope v0.1  
**Historical boundary:** EPM v0.2 closure remains frozen and unchanged  
**C-21 status after this increment:** NOT YET PRODUCTION-CONFORMANT

## 1. Purpose

This increment introduces a typed representation for the claim that a specific item of evidence was available at a specific time.

Its purpose is to make temporal admissibility depend on provenance-bearing availability information rather than on convenient timestamps already present in an application request.

The model MUST preserve this distinction:

`event time != claimed capture time != processing time != evidence availability time`

No existing timestamp may be silently reused as `available_at`.

## 2. Minimal object

```text
EvidenceAvailability {
    evidence_id
    available_at
    observed_at
    source
    provenance_ref
    attestation
}

AvailabilityAttestation {
    attestation_id
    authority
    method
    basis
    validated
}
```

### Field necessity

- `evidence_id` binds the availability claim to the evidence it concerns.
- `available_at` is the time the evidence is asserted to have become available to the relevant evidentiary system or authority.
- `observed_at` records when this availability fact was itself observed/recorded. It MUST NOT be substituted for `available_at`.
- `source` identifies the system, authority, ledger, archive, or other source making the availability assertion.
- `provenance_ref` links to the provenance record from which the availability assertion can be reconstructed.
- `attestation` records why the availability assertion is admissible as trusted input rather than a naked application assertion.

## 3. Trusted-input rule

An availability record is temporally admissible input only when all of the following are established:

1. `evidence_id` matches the evidence being evaluated;
2. `available_at` and `observed_at` are timezone-aware;
3. `observed_at >= available_at` unless a separately specified attestation method establishes why retrospective availability is valid;
4. `source` is non-empty;
5. `provenance_ref` is non-empty;
6. the attestation has a non-empty identifier, authority, method, and basis;
7. `attestation.validated == true`;
8. the availability object entered through a trusted internal provenance path rather than through an unverified domain request field.

The boolean `validated` is a representation of an upstream validation result. It is not permission for a caller to self-certify trust. Domain adapters MUST control whether a raw external field is allowed to construct this object.

## 4. Temporal admissibility

For an epistemic state scoped to time `T_state`:

- if no trustworthy availability record exists, temporal availability is `UNKNOWN`;
- if `available_at <= T_state`, the evidence is temporally available for this check;
- if `available_at > T_state`, the evidence MUST NOT support that earlier epistemic state unless a separately validated temporal-preservation relation exists;
- lack of availability evidence MUST NOT be converted into proof of unavailability.

This increment therefore distinguishes:

`UNKNOWN availability`

from

`KNOWN unavailable at T_state`.

## 5. Forbidden mappings

The following mappings are explicitly prohibited unless an independent provenance relation establishes equivalence:

- `timestamp_claimed -> available_at`
- `capture_time -> available_at`
- `processed_at -> available_at`
- `request_received_at -> historical available_at`
- model generation time -> external evidence availability time

## 6. FAP compatibility boundary

The existing FAP-Insurance request does not provide trustworthy evidence-availability provenance.

Therefore this increment MUST NOT make C-21 production-conformant merely by adding a field to `VerifyClaimRequest`.

A FAP adapter MAY carry an `EvidenceAvailability` object only when that object was created by a trusted internal provenance integration. The current insurance endpoint remains valid without such an object; in that case availability stays `UNKNOWN` for C-21 purposes.

The older compatibility helper accepting `verification["evidence_available_at"]` remains historical/compatibility behavior until replaced by the typed object. It is not promoted into the generic trust contract.

## 7. Adversarial probes

The executable gate MUST demonstrate at least:

1. claimed event/capture time cannot create an availability record;
2. processed time cannot create historical availability;
3. an unvalidated or provenance-free availability record is rejected as trusted temporal input;
4. a trusted record available after the source epistemic time is classified as temporally inadmissible;
5. absence of a trusted record returns `UNKNOWN`, not `AVAILABLE` or `UNAVAILABLE`;
6. a trusted record available on or before the state time is admissible for the temporal-availability check.

## 8. Claim boundary

Passing this gate establishes only that EPM has a first-class, provenance-bearing availability object and can distinguish known availability, known non-availability at a state time, and unknown availability.

It does NOT establish end-to-end FAP production C-21 conformance until a real production provenance source supplies and validates these records through the API/runtime path.

TVC remains outside this specification.
