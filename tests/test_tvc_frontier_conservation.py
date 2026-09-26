from datetime import datetime, timedelta, timezone
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys


P = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "frontier_conservation.py"
S = spec_from_file_location("tvc_frontier_conservation", P)
assert S is not None and S.loader is not None
M = module_from_spec(S)
sys.modules[S.name] = M
S.loader.exec_module(M)

Snapshot = M.FrontierSnapshot
Evidence = M.FrontierMutationEvidence
Status = M.FrontierTransitionStatus
evaluate = M.evaluate_frontier_transition

T0 = datetime(2026, 9, 6, 20, 56, tzinfo=timezone.utc)
T1 = T0 + timedelta(hours=1)
T2 = T1 + timedelta(hours=1)


def snap(t, digest, authority="A", policy="P"):
    return Snapshot(t, "INFERRED", digest, authority, policy)


def evidence(**kw):
    base = dict(
        evidence_id="rev-1",
        available_at=T1,
        effective_at=T1,
        incorporated_at=T1,
        provenance_valid=True,
        authority_id="A",
        policy_id="P",
        permits_from_digest="F0",
        permits_to_digest="F1",
    )
    base.update(kw)
    return Evidence(**base)


def test_unchanged_frontier_is_preserved_without_revision_evidence():
    r = evaluate(snap(T0, "F0"), snap(T1, "F0"), [])
    assert r.status is Status.PRESERVED


def test_silent_frontier_mutation_is_unresolved_even_with_same_endpoint():
    r = evaluate(snap(T0, "F0"), snap(T1, "F1"), [])
    assert r.status is Status.UNRESOLVED
    assert r.reason == "FRONTIER_MUTATION_WITHOUT_ADMISSIBLE_EVIDENCE"


def test_legitimate_revision_requires_exact_from_to_binding():
    r = evaluate(snap(T0, "F0"), snap(T1, "F1"), [evidence()])
    assert r.status is Status.REVISED
    assert r.evidence_ids == ("rev-1",)


def test_later_evidence_cannot_launder_earlier_frontier_mutation():
    late = evidence(available_at=T2, effective_at=T2, incorporated_at=T2)
    r = evaluate(snap(T0, "F0"), snap(T1, "F1"), [late])
    assert r.status is Status.UNRESOLVED


def test_bad_provenance_cannot_authorize_frontier_mutation():
    r = evaluate(snap(T0, "F0"), snap(T1, "F1"), [evidence(provenance_valid=False)])
    assert r.status is Status.UNRESOLVED


def test_authority_substitution_fails_closed():
    wrong = evidence(authority_id="B")
    r = evaluate(snap(T0, "F0"), snap(T1, "F1", authority="A"), [wrong])
    assert r.status is Status.FAILED
    assert r.reason == "FRONTIER_MUTATION_AUTHORITY_OR_POLICY_MISMATCH"


def test_policy_substitution_fails_closed():
    wrong = evidence(policy_id="P2")
    r = evaluate(snap(T0, "F0"), snap(T1, "F1", policy="P"), [wrong])
    assert r.status is Status.FAILED


def test_revision_evidence_for_another_transition_does_not_transfer():
    wrong = evidence(permits_from_digest="OTHER", permits_to_digest="F1")
    r = evaluate(snap(T0, "F0"), snap(T1, "F1"), [wrong])
    assert r.status is Status.UNRESOLVED


def test_temporal_reversal_fails():
    r = evaluate(snap(T1, "F0"), snap(T0, "F1"), [evidence()])
    assert r.status is Status.FAILED
    assert r.reason == "TEMPORAL_REVERSAL"


def test_certificate_is_deterministic_under_evidence_order():
    a = evidence(evidence_id="a")
    b = evidence(evidence_id="b")
    r1 = evaluate(snap(T0, "F0"), snap(T1, "F1"), [a, b])
    r2 = evaluate(snap(T0, "F0"), snap(T1, "F1"), [b, a])
    assert r1 == r2
