"""Independent generic control. No imports from TVC, candidate tests or adapters."""
from collections import Counter
from hashlib import sha256
from datetime import timezone
import json


def classify(condition):
    if condition is None:
        return "UNRESOLVED"
    status, available, provenance = condition
    # Truth table: historical/provenance failure has priority over unknown status.
    return {
        (True, "SATISFIED"): "ADMISSIBLE",
        (True, "UNRESOLVED"): "UNRESOLVED",
        (True, "FAILED"): "FAILED",
        (False, "SATISFIED"): "FAILED",
        (False, "UNRESOLVED"): "FAILED",
        (False, "FAILED"): "FAILED",
    }[(available and provenance, status)]


def interpret(rules, admissible):
    """DNF clauses in standing priority order; no access to asserted standing."""
    for standing, alternatives in rules:
        for conjunction in alternatives:
            if not set(conjunction).difference(admissible):
                return standing
    return "UNKNOWN"


def closure(payload):
    required = sorted(payload["policy"].get(payload["standing"], []),
                      key=lambda name: (payload["priorities"].get(name, 0), name))
    tags = {name: classify(value) for name, value in payload["conditions"].items()}
    failed = [name for name in required if tags.get(name, "UNRESOLVED") == "FAILED"]
    unresolved = [name for name in required if tags.get(name, "UNRESOLVED") == "UNRESOLVED"]
    available = {name for name, tag in tags.items() if tag == "ADMISSIBLE"}
    if payload["scope"] == "required":
        available.intersection_update(required)
    reproduced = interpret(payload["rules"], available)
    status = ("FAILED" if failed else "UNRESOLVED" if unresolved else
              "DEGRADED" if reproduced != payload["standing"] else "CLOSED")
    boundary = next((name for name in required if name in failed or name in unresolved), None)
    return dict(status=status, reproduced=reproduced, obligations=required,
                failed=failed, unresolved=unresolved, boundary=boundary)


def graph_obligations(payload):
    """Relational least fixed point, rather than the candidate's traversal stack."""
    nodes = payload["nodes"]
    reachable = {payload["target"]} if payload["target"] in nodes else set()
    previous = None
    while previous != reachable:
        previous = reachable.copy()
        reachable |= {
            source for source, target, relation, provenance in payload["edges"]
            if target in reachable and source in nodes
            and nodes[source] not in ("EVIDENCE", "ATTESTATION")
        }
    selected = {}
    for source, target, relation, provenance in payload["edges"]:
        if target in reachable and source in nodes:
            # Group by logical identity while retaining every provenance claim.
            selected.setdefault(f"{relation}:{source}->{target}", set()).add(provenance)
    return sorted((name, tuple(sorted(refs))) for name, refs in selected.items())


def availability(payload, records, when):
    from epm.temporal import assess_temporal_availability
    counts = Counter(item.evidence_id for item in records)
    by_id = {item.evidence_id: item for item in records}
    output = []
    for obligation_id, provenance in graph_obligations(payload):
        if len(provenance) > 1:
            signature = [obligation_id, "UNKNOWN", False, "DEPENDENCY_PROVENANCE_AMBIGUOUS"]
        elif counts[obligation_id] > 1:
            signature = [obligation_id, "UNKNOWN", False, "DEPENDENCY_AVAILABILITY_AMBIGUOUS"]
        else:
            item = assess_temporal_availability(
                evidence_id=obligation_id, state_at=when, availability=by_id.get(obligation_id))
            signature = [item.evidence_id, item.status.value, item.trusted, item.reason_code]
        output.append(signature)
    return output


def boundary(dependencies, oracle):
    """Bitmask truth-table oracle, with independent all-subsets minimality check."""
    names = sorted(set(dependencies))
    full = (1 << len(names)) - 1
    values = {mask: oracle(frozenset(name for i, name in enumerate(names)
                                   if not mask & (1 << i))) for mask in range(full + 1)}
    baseline = values[0]
    failures = {mask for mask, value in values.items() if value != baseline}
    minimal = {mask for mask in failures
               if not any(other != mask and other & mask == other for other in failures)}
    ids = lambda mask: tuple(name for i, name in enumerate(names) if mask & (1 << i))
    rows = sorted(((ids(mask), values[mask]) for mask in minimal), key=lambda row: (len(row[0]), row))
    recovery = []
    for recovered in set(values).difference(failures):
        for i in range(len(names)):
            predecessor = recovered ^ (1 << i)
            if recovered & (1 << i) and predecessor in failures:
                recovery.append((ids(predecessor), values[predecessor], ids(recovered), baseline))
    recovery.sort(key=lambda row: (len(row[2]), row[2], row[0], row[1], row[3]))
    return dict(baseline=baseline, minimal=rows, recoveries=recovery, monotone=not recovery)


def contract_surface(dependencies, oracle):
    names = sorted(set(dependencies))
    masks = sorted(range(1 << len(names)),
                   key=lambda mask: (mask.bit_count(), tuple(n for i, n in enumerate(names) if mask & (1 << i))))
    return tuple((tuple(n for i, n in enumerate(names) if mask & (1 << i)),
                  oracle(frozenset(n for i, n in enumerate(names) if not mask & (1 << i))))
                 for mask in masks)


def contract_digest(contract):
    # Same v2 wire specification, independently encoded without TVC helpers.
    fields = dict(schema=contract.schema, transition_id=contract.transition_id,
                  issued_at=contract.issued_at.astimezone(timezone.utc).isoformat(timespec="microseconds"),
                  policy_id=contract.policy_id, prior_standing=contract.prior_standing,
                  material_dependencies=list(contract.material_dependencies),
                  prospective_surface=[[list(removed), standing] for removed, standing in contract.prospective_surface])
    return sha256(json.dumps(fields,sort_keys=True,separators=(",", ":"),ensure_ascii=True).encode()).hexdigest()


def verify_contract(contract, asserted, oracle, verify_anchor):
    if contract_digest(contract) != contract.contract_digest:
        return False, "PAYLOAD_DIGEST_MISMATCH"
    if not verify_anchor(contract.contract_digest, contract.anchor_ref):
        return False, "ANCHOR_MISMATCH"
    surface = contract_surface(contract.material_dependencies, oracle)
    if surface != contract.prospective_surface:
        return False, "PROSPECTIVE_SURFACE_MISMATCH"
    if oracle(frozenset(contract.material_dependencies)) != asserted:
        return False, "ASSERTED_RESULT_MISMATCH"
    return True, "CLOSED"
