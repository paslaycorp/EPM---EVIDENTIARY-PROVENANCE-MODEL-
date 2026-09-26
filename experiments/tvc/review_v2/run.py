#!/usr/bin/env python3
"""Run isolated TVC reduction and correctness review. Python 3.12+, stdlib only.

Exit 0 means the bounded integrity and reduction checks pass. This does not
establish irreducibility or authorize production. No network operations.
"""
import argparse
import ast
from collections import Counter
from dataclasses import replace
from datetime import datetime, timezone, timedelta
from hashlib import sha256
import importlib.util
from itertools import product, permutations
import json
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
SOURCE = ROOT
sys.path.insert(0, str(SOURCE / "src"))
import reference
from epm import (AssuranceContext, AssuranceState, AvailabilityAttestation,
                 EvidenceAvailability, EvidentiaryState, RuleBinding, State, inspect_state)
from epm.justification import (JustificationGraph, JustificationNode,
                               JustificationNodeType, SupportEdge, SupportRelation)

def load(name):
    spec = importlib.util.spec_from_file_location("candidate_" + name, SOURCE / "experiments" / "tvc" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module

tvc, dynamic, frontier, prospective = map(load, ("tvc", "dynamic", "selective_surface", "prospective_closure_contract"))
NAMES = ("support", "provenance", "entailment", "contradictions")
POLICY = {"EVIDENCED": list(NAMES[:2]), "INFERRED": list(NAMES)}
RULES = [["INFERRED", [list(NAMES)]], ["EVIDENCED", [list(NAMES[:2])]]]
NOW = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)
SEED = 3109232026

def canonical(obj):
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

def digest(obj):
    return sha256(canonical(obj).encode()).hexdigest()

def detached(obj):
    return json.loads(canonical(obj))

def candidate_rules(rules, active):
    # Separate interpreter from reference.interpret; no access to assertion.
    return next((standing for standing, clauses in rules
                 if any(all(name in active for name in clause) for clause in clauses)), "UNKNOWN")

def candidate_closure(payload):
    conditions = {name: tvc.HistoricalCondition(name, tvc.ObligationStatus(value[0]), value[1], value[2])
                  for name, value in payload["conditions"].items() if value is not None}
    snapshot = tvc.EpistemicSnapshot("uniform", "X", payload["standing"], NOW.isoformat(), conditions)
    policy = {standing: tuple(tvc.Obligation(name, name, standing, priority=payload["priorities"].get(name, 0)) for name in required)
              for standing, required in payload["policy"].items()}
    def reconstruct(s, admissible):
        if payload["scope"] == "all":
            admissible = frozenset(name for name, c in s.conditions.items()
                                  if c.status is tvc.ObligationStatus.SATISFIED
                                  and c.available_at_claim_time and c.provenance_valid)
        return candidate_rules(payload["rules"], admissible)
    result = tvc.evaluate_closure(snapshot, policy, reconstruct)
    return dict(status=result.status.value, reproduced=result.reproduced_standing,
                obligations=[o.obligation_id for o in result.obligations],
                failed=list(result.failed), unresolved=list(result.unresolved), boundary=result.closure_boundary)

def payload(standing="INFERRED", conditions=None, scope="required"):
    return dict(standing=standing, conditions=conditions if conditions is not None else
                {name: ["SATISFIED", True, True] for name in NAMES},
                scope=scope, policy=POLICY, rules=RULES,
                priorities={name:(index+1)*10 for index,name in enumerate(NAMES)})

def epm_record(unresolved=()):
    # Mechanically compiled obligations remain a caller composition, not Core.
    att = AvailabilityAttestation("att", "fixture", "local", "synthetic", True)
    assurance = State("primary", {"evidence": AssuranceState.VALID}, AssuranceContext(at=NOW),
                      RuleBinding("fixture", "1", "local", effective_at=NOW))
    return EvidentiaryState("state", "X", assurance,
             availability=(EvidenceAvailability("primary", NOW, NOW, "fixture", "prov", att),),
             unresolved_conditions=tuple(unresolved))

def baseline_gap():
    data = payload(conditions={name: ["SATISFIED", True, True] for name in NAMES[:3]})
    before = digest(data)
    a, b = detached(data), detached(data)
    assert digest(a) == digest(b)
    native = inspect_state(epm_record())
    generic = reference.closure(a)
    compiled = inspect_state(epm_record(generic["unresolved"]))
    candidate = candidate_closure(b)
    assert generic == candidate
    assert not native.unresolved_conditions and compiled.unresolved_conditions == ("contradictions",)
    assert digest(data) == before
    return dict(native_explicit_unresolved=list(native.unresolved_conditions),
                native_structural_issues=list(native.structural_issues),
                native_availability=[r.status.value for r in native.availability_results],
                tvc=candidate, generic=generic,
                epm_after_automatic_compilation=list(compiled.unresolved_conditions),
                removed_derivation_control_misses=True, shared_input_sha256=before)

def exhaustive_closure():
    states = [None] + [list(row) for row in product(("SATISFIED", "FAILED", "UNRESOLVED"), (False, True), (False, True))]
    corpus = sha256()
    outcomes = Counter()
    total = 0
    for standing, scope in product(POLICY, ("required", "all")):
        for choices in product(states, repeat=4):
            data = payload(standing, dict(zip(NAMES, choices)), scope)
            raw = canonical(data)
            left, right = json.loads(raw), json.loads(raw)
            expected, actual = reference.closure(left), candidate_closure(right)
            assert expected == actual, (data, expected, actual)
            assert canonical(left) == raw == canonical(right)
            outcomes[actual["status"]] += 1
            corpus.update((raw + "\n" + canonical(actual) + "\n").encode())
            total += 1
    return dict(comparisons=total, mismatches=0, outcomes=dict(sorted(outcomes.items())),
                input_output_sha256=corpus.hexdigest(), condition_states=13,
                reconstruction_scopes=["required", "all"], supported_standings=list(POLICY))

def graph_model(data):
    return JustificationGraph(
        nodes={key: JustificationNode(key, JustificationNodeType(kind), ("prov:"+key,),
                                      kind in ("EVIDENCE", "ATTESTATION")) for key, kind in data["nodes"].items()},
        edges=tuple(SupportEdge(a, b, SupportRelation(r), p) for a, b, r, p in data["edges"]))

def availability_records(raw):
    return tuple(EvidenceAvailability(name, NOW+timedelta(seconds=offset), NOW+timedelta(seconds=max(0, offset)),
                 "fixture", "prov:"+name, AvailabilityAttestation("att:"+name, "fixture", "local", "synthetic", trusted))
                 for name, offset, trusted in raw)

def candidate_graph(data):
    result = dynamic.assess_graph_obligation_availability(graph_model(data), target_id=data["target"],
                         state_at=NOW, availability=availability_records(data["records"]))
    return [[r.evidence_id, r.status.value, r.trusted, r.reason_code] for r in result]

def graph_trials():
    rng = random.Random(SEED)
    rows = []
    for i in range(512):
        names = [f"n{j}" for j in range(rng.randint(4, 12))]
        nodes = {name: rng.choice(("DERIVATION", "CONSTRAINT", "EVIDENCE", "ATTESTATION")) for name in names}
        nodes[names[-1]] = "CLAIM"
        edges = [[a, b, rng.choice(("SUPPORTS", "DERIVATION_INPUT", "ATTESTS")), f"prov:{a}:{b}"]
                 for j, a in enumerate(names) for b in names[j+1:] if rng.random() < .3]
        data = dict(nodes=nodes, edges=edges, target=names[-1], records=[])
        for name, _ in reference.graph_obligations(data):
            state = rng.randrange(5)
            if state == 0:
                continue
            data["records"].append([name, 1 if state == 1 else 0, state != 2])
            if state == 4:
                data["records"].append([name, -1, True])
        # Candidate never sees derived obligations, only the same raw graph/records.
        original_hash = digest(data)
        a, b = detached(data), detached(data)
        expected = reference.availability(a, availability_records(a["records"]), NOW)
        actual = candidate_graph(b)
        assert actual == expected and digest(a) == digest(b) == original_hash
        variants = [data]
        for _ in range(2):
            changed = detached(data)
            rng.shuffle(changed["edges"])
            rng.shuffle(changed["records"])
            changed["nodes"] = dict(reversed(list(changed["nodes"].items())))
            variants.append(changed)
        for variant in variants:
            assert candidate_graph(variant) == expected
        rows.append([original_hash, actual])
    return dict(cases=512, candidate_evaluations=512*3, mismatches=0,
                seed=SEED, input_output_sha256=digest(rows), parallel_provenance_edges="separate integrity probe")

class Oracle:
    def __init__(self, names, table):
        self.names = names
        self.table = tuple(table)
        self.calls = 0
    def __call__(self, active):
        self.calls += 1
        mask = sum(1 << i for i, name in enumerate(self.names) if name not in active)
        return self.table[mask]

def frontier_signature(audit):
    return dict(baseline=audit.baseline_standing, minimal=list(audit.minimal_failure_interventions),
                recoveries=[(r.failed_intervention, r.failed_outcome, r.recovered_intervention, r.recovered_outcome)
                            for r in audit.recovery_crossings], monotone=audit.baseline_failure_monotone)

def frontier_trials():
    labels = ("INFERRED", "EVIDENCED", "UNKNOWN")
    rng = random.Random(SEED + 1)
    cases = [(tuple("abc"), ("INFERRED",)+tail) for tail in product(labels, repeat=7)]
    for _ in range(1024):
        names = tuple("abcdef"[:rng.randint(4, 6)])
        cases.append((names, ("INFERRED",)+tuple(rng.choice(labels) for _ in range((1 << len(names))-1))))
    corpus = sha256()
    counts = Counter()
    for names, table in cases:
        left, right = Oracle(names, table), Oracle(names, table)
        generic = reference.boundary(names, left)
        actual = frontier.analyze_counterfactual_boundary(names, right)
        assert generic == frontier_signature(actual), (names, table, generic, actual)
        assert left.calls == right.calls == 1 << len(names)
        third = Oracle(names, table)
        try:
            compressed = frontier.material_counterfactual_frontier(list(reversed(names)), third)
            assert generic["monotone"]
            assert list(compressed.minimal_failure_interventions) == generic["minimal"]
            counts["compressible"] += 1
        except frontier.NonMonotonicFrontierError as exc:
            assert not generic["monotone"]
            assert exc.audit == actual
            counts["nonmonotone_rejected"] += 1
        assert third.calls == 1 << len(names)
        corpus.update((canonical([names, table, generic])+"\n").encode())
    return dict(cases=len(cases), exhaustive_ternary_three_dependency=3**7,
                seeded_larger_surfaces=1024, mismatches=0, equal_oracle_budgets=True,
                input_output_sha256=corpus.hexdigest(), **dict(counts))

def integrity_probes():
    findings = {}
    data = payload(conditions={name: ["SATISFIED", True, True] for name in NAMES})
    data["conditions"]["entailment"] = ["FAILED", False, True]
    data["conditions"]["contradictions"] = ["UNRESOLVED", True, True]
    raw_results = []
    semantic = set()
    for order in permutations(NAMES):
        permuted = detached(data)
        permuted["policy"]["INFERRED"] = list(order)
        actual = candidate_closure(permuted)
        assert actual == reference.closure(permuted)
        semantic.add(canonical([actual["status"], actual["reproduced"], sorted(actual["failed"]), sorted(actual["unresolved"])]))
        raw_results.append(actual)
    assert len(semantic) == 1
    assert all(row == raw_results[0] for row in raw_results)
    findings["policy_order"] = dict(permutations=24, verdict_stable=True,
                closure_boundaries=sorted({r["boundary"] for r in raw_results}),
                raw_full_certificate_invariant=True,
                disposition="Explicit priority is shared policy data; arbitrary tuple ordering has no effect.")
    # Condition mapping order is irrelevant under a fixed policy.
    fixed = candidate_closure(data)
    for order in permutations(NAMES):
        permuted = detached(data)
        permuted["conditions"] = {name: data["conditions"][name] for name in order}
        assert candidate_closure(permuted) == fixed
    findings["condition_order"] = dict(permutations=24, raw_result_invariant=True)

    graph = dict(nodes={"e":"EVIDENCE", "d":"DERIVATION", "x":"CLAIM"}, target="x", records=[],
                 edges=[["e","d","DERIVATION_INPUT","prov-A"], ["e","d","DERIVATION_INPUT","prov-B"],
                        ["d","x","SUPPORTS","prov-X"]])
    representations = []
    for edges in (graph["edges"], list(reversed(graph["edges"]))):
        variant = {**graph, "edges": edges}
        obligations = dynamic.derive_graph_obligations(graph_model(variant), target_id="x")
        representations.append([(r.obligation_id, r.provenance_ref, r.provenance_refs) for r in obligations])
    assert representations[0] == representations[1]
    graph_results = candidate_graph(graph)
    assert graph_results == reference.availability(graph, (), NOW)
    assert any(r[-1] == "DEPENDENCY_PROVENANCE_AMBIGUOUS" for r in graph_results)
    findings["parallel_provenance"] = dict(forward=representations[0], reverse=representations[1],
                disposition="All provenance retained; conflicting assertions remain explicitly UNKNOWN.")

    # Strong independent payload-binding check, same immutable anchor registry.
    deps = ("a", "b")
    original = lambda active: "INFERRED" if "a" in active else "EVIDENCED"
    drifted = lambda active: "INFERRED" if "b" in active else "EVIDENCED"
    registry = {}
    def anchor(value):
        ref = "receipt:" + str(len(registry))
        registry[ref] = value
        return ref
    def verify(value, ref):
        return registry.get(ref) == value
    contract = prospective.issue_contract(transition_id="claim-X", issued_at=NOW, policy_id="p1",
               prior_standing="EVIDENCED", material_dependencies=deps, reconstruct=original, anchor=anchor)
    assert reference.contract_digest(contract) == contract.contract_digest
    assert reference.contract_surface(deps, original) == contract.prospective_surface
    cases = [
        ("clean", contract, original, "INFERRED"),
        ("semantic-drift", contract, drifted, "INFERRED"),
        ("wrong-assertion", contract, original, "UNKNOWN"),
        ("wrong-anchor", replace(contract, anchor_ref="absent"), original, "INFERRED"),
        ("changed-transition-id", replace(contract, transition_id="another-claim"), original, "INFERRED"),
        ("changed-policy-id", replace(contract, policy_id="p2"), original, "INFERRED"),
        ("changed-issued-at", replace(contract, issued_at=NOW+timedelta(days=1)), original, "INFERRED"),
        ("changed-prior-standing", replace(contract, prior_standing="UNKNOWN"), original, "INFERRED"),
        ("replaced-surface-plus-drift", replace(contract, prospective_surface=reference.contract_surface(deps, drifted)), drifted, "INFERRED"),
    ]
    rows = []
    for label, artifact, oracle, assertion in cases:
        actual = prospective.close_against_contract(artifact, asserted_standing=assertion, reconstruct=oracle, verify_anchor=verify)
        expected = reference.verify_contract(artifact, assertion, oracle, verify)
        rows.append(dict(case=label, tvc_valid=actual.valid, tvc_reason=actual.reason,
                         reference_valid=expected[0], reference_reason=expected[1]))
    assert all(r["tvc_valid"] == r["reference_valid"] for r in rows[:4])
    assert all(not r["tvc_valid"] and not r["reference_valid"] for r in rows[4:])
    assert all(r["tvc_reason"] == r["reference_reason"] for r in rows)
    findings["prospective_payload_binding"] = dict(cases=rows, mismatches=0, original_five_witnesses_rejected=5,
        disposition="Full v2 payload is rebound to the authenticated digest before reconstruction.",
        anchor_scope="Local immutable digest registry only; not external trusted time.")

    # Compression only commits baseline-change topology, not every degraded label.
    two = ("a", "b")
    s1 = ["INFERRED", "EVIDENCED", "INFERRED", "EVIDENCED"]
    s2 = ["INFERRED", "EVIDENCED", "INFERRED", "UNKNOWN"]
    f1 = frontier.material_counterfactual_frontier(two, Oracle(two, s1))
    f2 = frontier.material_counterfactual_frontier(two, Oracle(two, s2))
    assert f1 == f2 and s1 != s2
    findings["frontier_scope"] = dict(surface_a=s1, surface_b=s2, same_frontier_digest=f1.digest,
        disposition="Sound for baseline-change membership; not a lossless commitment to all non-baseline standings.")

    model = lambda active: "INFERRED" if {"a","b"} <= active or {"c","d"} <= active else "EVIDENCED"
    ref = reference.boundary(tuple("abcd"), model)
    assert len(ref["minimal"]) == 4 and all(len(row[0]) == 2 for row in ref["minimal"])
    findings["singleton_negative_control"] = dict(singleton_failures=0, joint_minimal_failures=4,
        generic_full_frontier_matches=True)
    assert original(frozenset(deps)) == drifted(frozenset(deps))
    findings["endpoint_negative_control"] = dict(endpoint_equal=True, full_surface_drift_detected_by_both=True)
    return findings

def source_integrity():
    manifest = json.loads((HERE / "baseline.json").read_text())
    actual_names = {str(p.relative_to(SOURCE)) for p in (SOURCE / "src" / "epm").rglob("*.py")}
    assert actual_names == set(manifest["core_sha256"])
    for name, expected in manifest["core_sha256"].items():
        assert sha256((SOURCE / name).read_bytes()).hexdigest() == expected, name
    experimental_hashes = {str(p.relative_to(SOURCE)):sha256(p.read_bytes()).hexdigest()
                           for p in sorted((SOURCE / "experiments" / "tvc").rglob("*.py"))}
    return dict(core_files_verified=len(manifest["core_sha256"]), baseline_head=manifest["head"],
                base=manifest["base"], core_tree=manifest["core_tree"],
                experimental_sha256=experimental_hashes, source_unchanged=True)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("/tmp/tvc-integrity-results.json"))
    args = parser.parse_args()
    before = source_integrity()
    # Static audit supplements (does not replace) inspection of control independence.
    tree = ast.parse((HERE / "reference.py").read_text())
    imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert imports == ["collections", "hashlib", "datetime", "epm.temporal"]
    output = {"protocol_sha256":sha256((HERE/"PROTOCOL.md").read_bytes()).hexdigest(),
              "reference_sha256":sha256((HERE/"reference.py").read_bytes()).hexdigest(),
              "source":before}
    for name, fn in (("baseline_gap", baseline_gap), ("closure", exhaustive_closure),
                     ("dynamic_graph", graph_trials), ("frontier", frontier_trials),
                     ("integrity_probes", integrity_probes)):
        output[name] = fn()
        print(name + ": completed", flush=True)
    assert source_integrity() == before
    output["gates"] = {
        "bounded_reduction":"REPRODUCED_BY_GENERIC_CONTROL",
        "irreducible_capability":"NOT_ESTABLISHED",
        "fixed_input_determinism":"REQUIRES_SEPARATE_MULTIPROCESS_CHECK",
        "full_output_permutation_invariance":"PASS_EXPLICIT_PRIORITY_AND_PROVENANCE_RETENTION",
        "prospective_artifact_binding":"PASS_FULL_V2_PAYLOAD_BINDING",
        "production_boundary":"PRESERVED",
        "promotion":"RESEARCH_ONLY_IRREDUCIBILITY_NOT_ESTABLISHED"}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True)+"\n")
    print("Result SHA256: " + sha256(args.out.read_bytes()).hexdigest(), flush=True)

if __name__ == "__main__":
    main()
