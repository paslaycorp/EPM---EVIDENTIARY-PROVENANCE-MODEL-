#!/usr/bin/env python3
"""Independent issuance and matched history-retention experiment."""
from itertools import product
from types import SimpleNamespace
from hashlib import sha256
import json
import sys
import argparse
from pathlib import Path
sys.dont_write_bytecode = True
from run import HERE, NOW, Oracle, canonical, prospective, reference, source_integrity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,default=Path("/tmp/tvc-prospective-factorial.json"))
    args = parser.parse_args()
    before = source_integrity()
    dependencies = ("a", "b")
    surfaces = [("INFERRED",)+row for row in product(("INFERRED", "EVIDENCED", "UNKNOWN"), repeat=3)]
    registry = {}
    def anchor(value):
        # Registry receives a digest from each arm; no candidate output supplied
        # to generic issuance. A content-addressed receipt is deterministic here.
        ref = "receipt:" + value
        registry[ref] = value
        return ref
    def verify(value, ref):
        return registry.get(ref) == value
    rows = []
    drift_count = 0
    original_contracts = 0
    for original in surfaces:
        tvc_oracle, generic_oracle = Oracle(dependencies, original), Oracle(dependencies, original)
        candidate = prospective.issue_contract(
            transition_id="same-claim", issued_at=NOW, policy_id="fixed-policy", prior_standing="EVIDENCED",
            material_dependencies=dependencies, reconstruct=tvc_oracle, anchor=anchor)
        generic = SimpleNamespace(
            schema="tvc.prospective-closure/v2",
            transition_id="same-claim", issued_at=NOW, policy_id="fixed-policy", prior_standing="EVIDENCED",
            material_dependencies=dependencies,
            prospective_surface=reference.contract_surface(dependencies, generic_oracle))
        generic.contract_digest = reference.contract_digest(generic)
        generic.anchor_ref = anchor(generic.contract_digest)
        assert vars(candidate) == vars(generic)
        assert tvc_oracle.calls == generic_oracle.calls == 4
        original_contracts += 1
        for later in surfaces:
            tvc_later, generic_later = Oracle(dependencies, later), Oracle(dependencies, later)
            result = prospective.close_against_contract(candidate, asserted_standing="INFERRED",
                       reconstruct=tvc_later, verify_anchor=verify)
            control = reference.verify_contract(generic, "INFERRED", generic_later, verify)
            changed = original != later
            assert result.valid == control[0] == (not changed)
            # On drift the generic checker returns early, while TVC also queries
            # the full-set endpoint for its diagnostic. Both stay within five.
            assert tvc_later.calls <= 5 and generic_later.calls <= 5
            endpoint_detects = original[0] != later[0]
            assert not endpoint_detects
            rows.append(dict(original=original, later=later, changed=changed,
                             tvc_endpoint_detects=endpoint_detects, generic_endpoint_detects=endpoint_detects,
                             tvc_history_detects=not result.valid, generic_history_detects=not control[0],
                             tvc_queries=tvc_later.calls, generic_queries=generic_later.calls))
            drift_count += changed
    assert source_integrity() == before
    results = {
        "protocol_sha256":sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),
        "independently_issued_identical_contracts":original_contracts,
        "original_later_pairs":len(rows), "changed_surfaces":drift_count,
        "unchanged_surfaces":len(rows)-drift_count,
        "issuance_budget_per_arm":4, "verification_budget_per_arm":5,
        "tvc_endpoint_only_detected":0, "generic_endpoint_only_detected":0,
        "tvc_full_history_detected":drift_count, "generic_full_history_detected":drift_count,
        "full_history_false_positives_each":0,
        "equal_information_within_each_regime":True,
        "between_regime_contrast_is_information_retention_not_unique_capability":True,
        "all_pairs_sha256":sha256(canonical(rows).encode()).hexdigest(),
        "source_unchanged":True,
        "timestamp_trust":"local simulation only",
    }
    target = args.out
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(json.dumps(results,indent=2,sort_keys=True)+'\n')
    target.with_suffix('.jsonl').write_text(''.join(canonical(row)+'\n' for row in rows))
    print(json.dumps(results,indent=2))


if __name__ == '__main__':
    main()
