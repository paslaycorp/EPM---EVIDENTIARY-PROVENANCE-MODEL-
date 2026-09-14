# Epistemic Source Typing v0.1

**Status:** vNext implementation specification  
**Depends on:** Generic Evidentiary Envelope v0.1  
**Targets:** implementation foundation for C-10 and C-12  
**Historical boundary:** EPM v0.2 closure remains frozen and unchanged

## 1. Purpose

EPM must represent how information entered the evidentiary system without confusing origin with truth, confidence, or epistemic status.

Source type is therefore orthogonal to the existing epistemic ladder:

`OBSERVED -> EVIDENCED -> DERIVED -> INFERRED -> PREDICTED`

A source may be computational, asserted, attested, constrained, or observational while its epistemic state is tracked separately.

## 2. Source types

The first executable vocabulary is:

- `OBSERVATION` — information produced by an external observation path rather than by internal selection or computation;
- `DERIVATION` — a result logically derived from identified inputs;
- `DISCRIMINATOR` — information specification capable of distinguishing alternatives; not the observation of its outcome;
- `CONSTRAINT` — a narrowing relation over admissible possibilities; not evidence merely because it narrows;
- `ASSERTION` — a proposition supplied without EPM treating its truth as established by the act of assertion;
- `EXTERNAL_ATTESTATION` — an externally produced attestation whose provenance and authority remain explicit;
- `COMPUTATIONAL_DISCOVERY` — a consequence or pattern exposed through computation over existing inputs.

## 3. Minimal source record

```text
EpistemicSourceRecord {
    source_id
    source_type
    producer
    provenance_refs[]
    input_refs[]
    external_origin
}
```

Every typed source MUST retain enough provenance to reconstruct how it entered the system.

`external_origin` identifies whether the source originated outside the current computational/derivational boundary. It does not itself establish validity or authority.

## 4. Non-promotion rules

1. A `DISCRIMINATOR` MUST NOT be reclassified as `OBSERVATION` merely because it selects or distinguishes a candidate.
2. A `COMPUTATIONAL_DISCOVERY` MUST NOT become `OBSERVATION` without genuinely new externally originated evidence supporting that reclassification.
3. A `DERIVATION`, `CONSTRAINT`, or `ASSERTION` MUST NOT become `OBSERVATION` by repeated processing, confidence scoring, majority vote, or model selection.
4. An `OBSERVATION` MUST identify an external origin and provenance reference.
5. `EXTERNAL_ATTESTATION` remains an attestation; it is not silently relabeled as direct observation.
6. Source-type preservation does not itself prove the proposition carried by the source.

## 5. Computational discovery

More computation over the same evidence may reveal a consequence already entailed by the inputs. That output remains derivational/computational in provenance.

Computation is not a new external evidentiary event merely because the consequence was previously unknown to the operator.

## 6. Discriminator boundary

A discriminator identifies what information could distinguish remaining alternatives.

The discriminator definition is not the later observation of that information and is not a prediction of which outcome will occur.

This preserves the Two-Stage Trust Architecture boundary:

- Stage 1 may identify discriminator `D`;
- Stage 2 may later receive an actual observation associated with `D`;
- `D` itself never becomes that observation.

## 7. Adversarial probes

The executable gate MUST demonstrate at least:

1. discriminator -> observation relabeling is rejected without new external evidence;
2. computational discovery -> observation relabeling is rejected without new external evidence;
3. repeated/model-selected derivation preserves derivational source type;
4. an observation lacking external origin/provenance is not accepted as a valid observation source record;
5. an external attestation remains distinguishable from direct observation;
6. source classification never upgrades epistemic assurance by itself.

## 8. Claim boundary

Passing this gate provides runtime source typing sufficient to represent the C-10 and C-12 distinctions.

It does not by itself claim full C-10/C-12 production conformance until the relevant production paths actually carry these typed source records end to end.

It does not implement the constraint engine, answer-space resolution, or circular-justification graph.
