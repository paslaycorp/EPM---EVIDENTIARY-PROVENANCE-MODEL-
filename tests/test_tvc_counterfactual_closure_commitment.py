from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "counterfactual_closure_commitment.py"
spec = importlib.util.spec_from_file_location("tvc_counterfactual_closure_commitment", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)

UTC = timezone.utc
T0 = datetime(2026, 9, 14, 18, 0, tzinfo=UTC)
T1 = T0 + timedelta(minutes=1)
DEPS = ("support_a", "support_b", "provenance", "entailment", "contradictions")


def anchor(digest: str) -> str:
    return f"anchor:{digest}"


def verify_anchor(digest: str, ref: str) -> bool:
    return ref == f"anchor:{digest}"


def reconstruct_original(ids: frozenset[str]) -> str:
    support = bool({"support_a", "support_b"} & ids)
    if support and {"provenance", "entailment", "contradictions"}.issubset(ids):
        return "INFERRED"
    if support and "provenance" in ids:
        return "EVIDENCED"
    return "UNKNOWN"


def reconstruct_mutated(ids: frozenset[str]) -> str:
    # Same baseline endpoint with all dependencies present, but semantics of the
    # failure surface changed: contradictions are no longer material once both
    # independent supports are present.
    both_supports = {"support_a", "support_b"}.issubset(ids)
    any_support = bool({"support_a", "support_b"} & ids)
    if any_support and {"provenance", "entailment"}.issubset(ids) and (
        "contradictions" in ids or both_supports
    ):
        return "INFERRED"
    if any_support and "provenance" in ids:
        return "EVIDENCED"
    return "UNKNOWN"


def issue(reconstruct=reconstruct_original):
    return tvc.issue_commitment(
        transition_id="claim-X",
        claim_time=T1,
        committed_at=T1,
        policy_id="policy-v1",
        material_dependencies=DEPS,
        reconstruct=reconstruct,
        anchor=anchor,
    )


def test_commitment_verifies_when_counterfactual_surface_is_reproduced():
    commitment = issue()
    result = tvc.verify_commitment(
        commitment,
        reconstruct=reconstruct_original,
        verify_anchor=verify_anchor,
    )
    assert result.valid
    assert result.reason == "VERIFIED"


def test_same_endpoint_does_not_hide_counterfactual_semantic_drift():
    commitment = issue()
    assert reconstruct_original(frozenset(DEPS)) == "INFERRED"
    assert reconstruct_mutated(frozenset(DEPS)) == "INFERRED"

    result = tvc.verify_commitment(
        commitment,
        reconstruct=reconstruct_mutated,
        verify_anchor=verify_anchor,
    )
    assert not result.valid
    assert result.reason == "COUNTERFACTUAL_SURFACE_MISMATCH"


def test_commitment_is_information_not_recoverable_from_endpoint_alone():
    a = issue(reconstruct_original)
    b = issue(reconstruct_mutated)

    # Both contemporaneous systems assert the same endpoint from the same full
    # dependency set, but they commit to different failure behavior under
    # interventions. A later endpoint-only replay cannot distinguish them.
    assert a.baseline_standing == b.baseline_standing == "INFERRED"
    assert a.material_dependencies == b.material_dependencies
    assert a.surface_digest != b.surface_digest


def test_late_commitment_is_rejected_at_issue_time():
    try:
        tvc.issue_commitment(
            transition_id="late",
            claim_time=T0,
            committed_at=T1,
            policy_id="policy-v1",
            material_dependencies=DEPS,
            reconstruct=reconstruct_original,
            anchor=anchor,
        )
    except ValueError as exc:
        assert "must not post-date" in str(exc)
    else:
        raise AssertionError("late commitment must fail closed")


def test_anchor_tampering_is_rejected():
    commitment = issue()
    result = tvc.verify_commitment(
        commitment,
        reconstruct=reconstruct_original,
        verify_anchor=lambda digest, ref: False,
    )
    assert not result.valid
    assert result.reason == "ANCHOR_MISMATCH"


def test_generic_verifier_can_validate_but_cannot_recreate_original_surface_without_commitment():
    commitment = issue()

    # A generic checker that receives the commitment can validate it. That is
    # interoperability, not a falsification: the novel candidate object is the
    # contemporaneously committed counterfactual surface itself.
    generic = tvc.verify_commitment(
        commitment,
        reconstruct=reconstruct_original,
        verify_anchor=verify_anchor,
    )
    assert generic.valid

    # Remove the commitment and retain only the endpoint, dependency identities,
    # and later semantics. There is no datum that selects the original surface
    # over the mutated one; both reproduce the same endpoint.
    endpoint = reconstruct_mutated(frozenset(DEPS))
    assert endpoint == commitment.baseline_standing
    assert reconstruct_original(frozenset(DEPS)) == endpoint


def test_surface_is_deterministic_across_dependency_order():
    a = tvc.issue_commitment(
        transition_id="order",
        claim_time=T1,
        committed_at=T1,
        policy_id="policy-v1",
        material_dependencies=DEPS,
        reconstruct=reconstruct_original,
        anchor=anchor,
    )
    b = tvc.issue_commitment(
        transition_id="order",
        claim_time=T1,
        committed_at=T1,
        policy_id="policy-v1",
        material_dependencies=reversed(DEPS),
        reconstruct=reconstruct_original,
        anchor=anchor,
    )
    assert a.response_surface == b.response_surface
    assert a.surface_digest == b.surface_digest
