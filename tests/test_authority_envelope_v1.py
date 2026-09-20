import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from epm.assurance import Decision
from epm.authority import (
    AuthorityFailureCode,
    AuthorityGrant,
    AuthorityRequest,
    ValidatedAuthorityBasis,
    establish_authority_basis,
    evaluate_authority_request,
)

NOW = datetime(2026, 9, 20, 12, 0, tzinfo=UTC)
ROOT = Path(__file__).resolve().parents[1]


def _request(**overrides):
    values = {
        "transition_id": "AUTH-T-001",
        "actor": "agent:invoice-worker",
        "action": "database.write",
        "resource": "db:invoice/job_state",
        "purpose": "invoice-processing",
        "scope": "invoice-job",
        "jurisdiction": "US-TX",
        "at": NOW,
        "authority": "ops:payments",
        "policy_id": "payments-runtime",
        "policy_version": "1",
    }
    values.update(overrides)
    return AuthorityRequest(**values)


def _grant(**overrides):
    values = {
        "grant_id": "GRANT-001",
        "subject": "agent:invoice-worker",
        "actions": frozenset({"database.write"}),
        "resources": frozenset({"db:invoice/job_state"}),
        "purposes": frozenset({"invoice-processing"}),
        "scopes": frozenset({"invoice-job"}),
        "jurisdictions": frozenset({"US-TX"}),
        "issuer": "ops:payments",
        "policy_id": "payments-runtime",
        "policy_version": "1",
        "evidence_refs": ("policy:payments-runtime:1", "grant:GRANT-001"),
        "not_before": NOW - timedelta(hours=1),
        "not_after": NOW + timedelta(hours=1),
    }
    values.update(overrides)
    return AuthorityGrant(**values)


def _basis(grant=None, *, validated_at=None):
    return establish_authority_basis(
        grant or _grant(),
        validator_id="boundary:payments-authz/1",
        validation_method="signed-grant+policy-binding",
        validation_evidence_refs=("validation:GRANT-001",),
        validated_at=validated_at or NOW - timedelta(minutes=1),
    )


def test_matching_authority_is_authorized():
    result = evaluate_authority_request(_request(), _basis())

    assert result.decision is Decision.AUTHORIZED
    assert result.failure is AuthorityFailureCode.NONE
    assert result.permitted is True
    assert result.fail_closed is False


def test_constraints_are_conserved_in_authorized_result():
    grant = _grant(constraints=("max_rows=1", "no_schema_change"))
    result = evaluate_authority_request(_request(), _basis(grant))

    assert result.decision is Decision.AUTHORIZED_WITH_CONSTRAINTS
    assert result.permitted is True
    assert result.constraints == ("max_rows=1", "no_schema_change")


def test_missing_authority_never_inherits_from_capability():
    result = evaluate_authority_request(_request(), None)

    assert result.decision is Decision.DEFER
    assert result.failure is AuthorityFailureCode.AUTHORITY_UNESTABLISHED
    assert result.permitted is False
    assert result.fail_closed is True


def test_raw_self_asserted_validation_cannot_authorize():
    hostile = {
        "grant_id": "GRANT-001",
        "boundary_validated": True,
        "validated": True,
        "authority": "ops:payments",
    }

    result = evaluate_authority_request(_request(), hostile)

    assert result.decision is Decision.QUARANTINE
    assert result.failure is AuthorityFailureCode.BOUNDARY_UNVALIDATED
    assert result.permitted is False


def test_validated_basis_cannot_be_constructed_directly():
    with pytest.raises(TypeError, match="establish_authority_basis"):
        ValidatedAuthorityBasis(
            grant=_grant(),
            validator_id="hostile",
            validation_method="trust-me",
            validation_evidence_refs=("self:asserted",),
            validated_at=NOW,
            _seal=object(),
        )


def test_network_reachability_does_not_authorize_connection():
    request = _request(
        action="network.connect",
        resource="tcp:203.0.113.7:22",
        purpose="reverse-tunnel",
    )

    result = evaluate_authority_request(request, _basis())

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.ACTION_MISMATCH


def test_compute_access_does_not_authorize_cryptocurrency_mining():
    grant = _grant(
        actions=frozenset({"compute.execute"}),
        resources=frozenset({"gpu:cluster-a"}),
        purposes=frozenset({"model-training"}),
    )
    request = _request(
        action="compute.execute",
        resource="gpu:cluster-a",
        purpose="cryptocurrency-mining",
    )

    result = evaluate_authority_request(request, _basis(grant))

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.PURPOSE_MISMATCH


def test_actor_cannot_borrow_another_subjects_authority():
    result = evaluate_authority_request(
        _request(actor="agent:rogue-worker"),
        _basis(),
    )

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.ACTOR_MISMATCH


def test_agent_cannot_self_expand_into_authority_granting():
    request = _request(
        action="authority.grant",
        resource="authority:agent:invoice-worker",
        purpose="self-escalation",
    )

    result = evaluate_authority_request(request, _basis())

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.ACTION_MISMATCH


@pytest.mark.parametrize(
    ("field", "value", "failure"),
    [
        ("purpose", "litigation-discovery", AuthorityFailureCode.PURPOSE_MISMATCH),
        ("scope", "all-customers", AuthorityFailureCode.SCOPE_MISMATCH),
        ("jurisdiction", "US-CA", AuthorityFailureCode.JURISDICTION_MISMATCH),
        ("policy_version", "2", AuthorityFailureCode.POLICY_MISMATCH),
        ("authority", "agent:self", AuthorityFailureCode.AUTHORITY_MISMATCH),
    ],
)
def test_context_cannot_silently_expand(field, value, failure):
    result = evaluate_authority_request(_request(**{field: value}), _basis())

    assert result.decision is Decision.DENY
    assert result.failure is failure


def test_later_validation_cannot_retroactively_authorize_earlier_action():
    result = evaluate_authority_request(
        _request(at=NOW),
        _basis(validated_at=NOW + timedelta(minutes=1)),
    )

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.TEMPORAL_MISMATCH


def test_expired_grant_is_denied():
    grant = _grant(not_after=NOW - timedelta(seconds=1))

    result = evaluate_authority_request(_request(), _basis(grant))

    assert result.decision is Decision.DENY
    assert result.failure is AuthorityFailureCode.TEMPORAL_MISMATCH


def test_revocation_does_not_rewrite_history_but_blocks_later_use():
    revoked_at = NOW + timedelta(minutes=10)
    grant = _grant(
        not_after=NOW + timedelta(hours=2),
        revoked_at=revoked_at,
        revocation_evidence_refs=("revocation:GRANT-001",),
    )
    basis = _basis(grant, validated_at=NOW - timedelta(minutes=5))

    before = evaluate_authority_request(_request(at=NOW), basis)
    after = evaluate_authority_request(
        _request(transition_id="AUTH-T-002", at=NOW + timedelta(minutes=11)),
        basis,
    )

    assert before.decision is Decision.AUTHORIZED
    assert after.decision is Decision.DENY
    assert after.failure is AuthorityFailureCode.AUTHORITY_REVOKED


@pytest.mark.parametrize(
    ("action", "resource", "purpose"),
    [
        ("filesystem.read", "file:/evidence/receipt.json", "verification"),
        ("network.connect", "https:api.example.test", "verification"),
        ("message.send", "mailbox:review@example.test", "case-review"),
        ("deployment.release", "service:claims-api", "production-release"),
        ("database.write", "db:claims/audit", "audit-recording"),
        ("credential.use", "credential:service-a", "service-auth"),
        ("compute.execute", "gpu:cluster-a", "model-training"),
    ],
)
def test_same_contract_is_domain_neutral(action, resource, purpose):
    grant = _grant(
        actions=frozenset({action}),
        resources=frozenset({resource}),
        purposes=frozenset({purpose}),
        scopes=frozenset({"bounded-operation"}),
        jurisdictions=frozenset({"US"}),
        issuer="authority:example",
        policy_id="policy:example",
        policy_version="7",
    )
    request = _request(
        transition_id=f"T-{action}",
        action=action,
        resource=resource,
        purpose=purpose,
        scope="bounded-operation",
        jurisdiction="US",
        authority="authority:example",
        policy_id="policy:example",
        policy_version="7",
    )

    result = evaluate_authority_request(request, _basis(grant))

    assert result.decision is Decision.AUTHORIZED
    assert result.permitted is True


def test_authority_request_schema_rejects_self_asserted_validation():
    schema = json.loads(
        (ROOT / "schemas" / "epm-authority-request-v1.schema.json").read_text()
    )
    payload = _request().to_dict()
    Draft202012Validator(schema).validate(payload)

    hostile = dict(payload)
    hostile["boundary_validated"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(hostile)


def test_authority_decision_receipt_schema_executes():
    schema = json.loads(
        (ROOT / "schemas" / "epm-authority-decision-receipt-v1.schema.json").read_text()
    )
    receipt = evaluate_authority_request(_request(), _basis()).to_receipt()

    Draft202012Validator(schema).validate(receipt)
