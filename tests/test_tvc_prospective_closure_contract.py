from __future__ import annotations

import importlib.util
import sys
from datetime import datetime, timezone
from pathlib import Path

MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "prospective_closure_contract.py"
spec = importlib.util.spec_from_file_location("tvc_prospective_closure_contract", MODULE)
assert spec and spec.loader
tvc = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tvc
spec.loader.exec_module(tvc)

UTC = timezone.utc
TPRE = datetime(2026, 9, 14, 18, 30, tzinfo=UTC)
DEPS = ("support_a", "support_b", "provenance", "entailment", "contradictions")


def anchor(digest: str) -> str:
    return f"anchor:{digest}"


def verify_anchor(digest: str, ref: str) -> bool:
    return ref == f"anchor:{digest}"


def reconstruct(ids: frozenset[str]) -> str:
    support = bool({"support_a", "support_b"} & ids)
    if support and {"provenance", "entailment", "contradictions"}.issubset(ids):
        return "INFERRED"
    if support and "provenance" in ids:
        return "EVIDENCED"
    return "UNKNOWN"


def reconstruct_drifted(ids: frozenset[str]) -> str:
    support = bool({"support_a", "support_b"} & ids)
    both_supports = {"support_a", "support_b"}.issubset(ids)
    if support and {"provenance", "entailment"}.issubset(ids) and (
        "contradictions" in ids or both_supports
    ):
        return "INFERRED"
    if support and "provenance" in ids:
        return "EVIDENCED"
    return "UNKNOWN"


def issue():
    return tvc.issue_contract(
        transition_id="prospective-X",
        issued_at=TPRE,
        policy_id="policy-v1",
        prior_standing="EVIDENCED",
        material_dependencies=DEPS,
        reconstruct=reconstruct,
        anchor=anchor,
    )


def test_contract_is_outcome_blind_by_api_shape():
    contract = issue()
    assert not hasattr(contract, "asserted_standing")
    assert contract.prior_standing == "EVIDENCED"


def test_valid_later_result_closes_against_pre_outcome_contract():
    result = tvc.close_against_contract(
        issue(),
        asserted_standing="INFERRED",
        reconstruct=reconstruct,
        verify_anchor=verify_anchor,
    )
    assert result.valid
    assert result.reason == "CLOSED"


def test_asserted_result_cannot_select_its_own_obligations():
    contract = issue()
    inferred = tvc.close_against_contract(
        contract,
        asserted_standing="INFERRED",
        reconstruct=reconstruct,
        verify_anchor=verify_anchor,
    )
    evidenced = tvc.close_against_contract(
        contract,
        asserted_standing="EVIDENCED",
        reconstruct=reconstruct,
        verify_anchor=verify_anchor,
    )
    assert inferred.valid
    assert not evidenced.valid
    assert evidenced.reason == "ASSERTED_RESULT_MISMATCH"
    assert inferred.contract_digest == evidenced.contract_digest


def test_later_semantic_drift_fails_even_when_endpoint_is_same():
    contract = issue()
    assert reconstruct(frozenset(DEPS)) == reconstruct_drifted(frozenset(DEPS)) == "INFERRED"
    result = tvc.close_against_contract(
        contract,
        asserted_standing="INFERRED",
        reconstruct=reconstruct_drifted,
        verify_anchor=verify_anchor,
    )
    assert not result.valid
    assert result.reason == "PROSPECTIVE_SURFACE_MISMATCH"


def test_post_hoc_reconstruction_cannot_replace_prospective_contract():
    original = issue()
    later = tvc.issue_contract(
        transition_id="prospective-X",
        issued_at=TPRE,
        policy_id="policy-v1",
        prior_standing="EVIDENCED",
        material_dependencies=DEPS,
        reconstruct=reconstruct_drifted,
        anchor=anchor,
    )
    # Same prior label, same dependency identities, same full-set endpoint.
    assert original.prior_standing == later.prior_standing
    assert original.material_dependencies == later.material_dependencies
    assert reconstruct(frozenset(DEPS)) == reconstruct_drifted(frozenset(DEPS))
    # But the pre-outcome counterfactual contracts are different.
    assert original.contract_digest != later.contract_digest


def test_anchor_tampering_fails_closed():
    result = tvc.close_against_contract(
        issue(),
        asserted_standing="INFERRED",
        reconstruct=reconstruct,
        verify_anchor=lambda digest, ref: False,
    )
    assert not result.valid
    assert result.reason == "ANCHOR_MISMATCH"
