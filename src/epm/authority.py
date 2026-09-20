"""Domain-neutral capability-to-authority transition control for EPM vNext.

The module is intentionally separate from the released v0.1.2 transition engine.
It models whether a consequential action is authorized; it does not execute the
action and it does not allow capability, reachability, scores, or raw caller
claims to manufacture authority.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .assurance import Decision

AUTHORITY_REQUEST_SCHEMA_VERSION = "epm.authority-request/1.0"
AUTHORITY_DECISION_SCHEMA_VERSION = "epm.authority-decision-receipt/1.0"

_VALIDATED_BASIS_SEAL = object()


class AuthorityFailureCode(str, Enum):
    NONE = "NONE"
    INVALID_REQUEST = "INVALID_REQUEST"
    AUTHORITY_UNESTABLISHED = "AUTHORITY_UNESTABLISHED"
    BOUNDARY_UNVALIDATED = "BOUNDARY_UNVALIDATED"
    EVIDENCE_UNESTABLISHED = "EVIDENCE_UNESTABLISHED"
    ACTOR_MISMATCH = "ACTOR_MISMATCH"
    ACTION_MISMATCH = "ACTION_MISMATCH"
    RESOURCE_MISMATCH = "RESOURCE_MISMATCH"
    PURPOSE_MISMATCH = "PURPOSE_MISMATCH"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    JURISDICTION_MISMATCH = "JURISDICTION_MISMATCH"
    POLICY_MISMATCH = "POLICY_MISMATCH"
    AUTHORITY_MISMATCH = "AUTHORITY_MISMATCH"
    TEMPORAL_MISMATCH = "TEMPORAL_MISMATCH"
    AUTHORITY_REVOKED = "AUTHORITY_REVOKED"


@dataclass(frozen=True, slots=True)
class AuthorityRequest:
    """One proposed consequential transition.

    Strings are deliberately domain-neutral. Applications may use vocabularies
    such as network.connect, database.write, message.send, deployment.release,
    credential.use or compute.execute.
    """

    transition_id: str
    actor: str
    action: str
    resource: str
    purpose: str
    scope: str
    jurisdiction: str
    at: datetime
    authority: str
    policy_id: str
    policy_version: str
    consequence: str = "standard"
    schema_version: str = AUTHORITY_REQUEST_SCHEMA_VERSION

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "transition_id": self.transition_id,
            "actor": self.actor,
            "action": self.action,
            "resource": self.resource,
            "purpose": self.purpose,
            "scope": self.scope,
            "jurisdiction": self.jurisdiction,
            "at": self.at.isoformat(),
            "authority": self.authority,
            "policy_id": self.policy_id,
            "policy_version": self.policy_version,
            "consequence": self.consequence,
        }


@dataclass(frozen=True, slots=True)
class AuthorityGrant:
    """A raw authority claim.

    This object is not sufficient to authorize anything. It must be converted
    into a ValidatedAuthorityBasis by a legitimate ingestion-boundary validator
    before evaluation. The literal "*" is the only wildcard and must be granted
    explicitly.
    """

    grant_id: str
    subject: str
    actions: frozenset[str]
    resources: frozenset[str]
    purposes: frozenset[str]
    scopes: frozenset[str]
    jurisdictions: frozenset[str]
    issuer: str
    policy_id: str
    policy_version: str
    evidence_refs: tuple[str, ...]
    not_before: datetime | None = None
    not_after: datetime | None = None
    constraints: tuple[str, ...] = ()
    revoked_at: datetime | None = None
    revocation_evidence_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidatedAuthorityBasis:
    """Typed boundary-validation result.

    Direct construction is rejected. Boundary adapters establish this type only
    after validating the external authority evidence they control.
    """

    grant: AuthorityGrant
    validator_id: str
    validation_method: str
    validation_evidence_refs: tuple[str, ...]
    validated_at: datetime
    _seal: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._seal is not _VALIDATED_BASIS_SEAL:
            raise TypeError(
                "ValidatedAuthorityBasis must be established through "
                "establish_authority_basis()."
            )


@dataclass(frozen=True, slots=True)
class AuthorityResult:
    transition_id: str
    decision: Decision
    failure: AuthorityFailureCode
    reason: str
    permitted: bool
    fail_closed: bool
    grant_id: str | None = None
    validator_id: str | None = None
    constraints: tuple[str, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    schema_version: str = AUTHORITY_DECISION_SCHEMA_VERSION

    def to_receipt(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "transition_id": self.transition_id,
            "decision": self.decision.value,
            "failure": self.failure.value,
            "reason": self.reason,
            "permitted": self.permitted,
            "fail_closed": self.fail_closed,
            "grant_id": self.grant_id,
            "validator_id": self.validator_id,
            "constraints": list(self.constraints),
            "evidence_refs": list(self.evidence_refs),
        }


def _aware(value: datetime | None) -> bool:
    return value is not None and value.tzinfo is not None and value.utcoffset() is not None


def _nonempty(value: str) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _allows(values: frozenset[str], requested: str) -> bool:
    return requested in values or "*" in values


def _result(
    request: AuthorityRequest,
    decision: Decision,
    failure: AuthorityFailureCode,
    reason: str,
    *,
    basis: ValidatedAuthorityBasis | None = None,
) -> AuthorityResult:
    permitted = decision in {Decision.AUTHORIZED, Decision.AUTHORIZED_WITH_CONSTRAINTS}
    evidence_refs: tuple[str, ...] = ()
    constraints: tuple[str, ...] = ()
    validator_id: str | None = None
    grant_id: str | None = None
    if basis is not None:
        grant = basis.grant
        grant_id = grant.grant_id
        validator_id = basis.validator_id
        constraints = grant.constraints
        evidence_refs = tuple(
            dict.fromkeys(
                (
                    *grant.evidence_refs,
                    *basis.validation_evidence_refs,
                    *grant.revocation_evidence_refs,
                )
            )
        )
    return AuthorityResult(
        transition_id=request.transition_id,
        decision=decision,
        failure=failure,
        reason=reason,
        permitted=permitted,
        fail_closed=not permitted,
        grant_id=grant_id,
        validator_id=validator_id,
        constraints=constraints,
        evidence_refs=evidence_refs,
    )


def establish_authority_basis(
    grant: AuthorityGrant,
    *,
    validator_id: str,
    validation_method: str,
    validation_evidence_refs: tuple[str, ...],
    validated_at: datetime,
) -> ValidatedAuthorityBasis:
    """Record a legitimate boundary validator's successful authority check.

    This function validates structure and temporal comparability. It does not
    discover external authority by itself. The calling boundary adapter remains
    responsible for authenticating the issuer, evidence and validation method.
    """
    required_text = (
        grant.grant_id,
        grant.subject,
        grant.issuer,
        grant.policy_id,
        grant.policy_version,
        validator_id,
        validation_method,
    )
    if not all(_nonempty(value) for value in required_text):
        raise ValueError("Authority basis identifiers must be non-empty strings.")

    dimensions = (
        grant.actions,
        grant.resources,
        grant.purposes,
        grant.scopes,
        grant.jurisdictions,
    )
    if any(not values or any(not _nonempty(value) for value in values) for values in dimensions):
        raise ValueError("Every authority dimension must contain an explicit value.")

    if not grant.evidence_refs or any(not _nonempty(ref) for ref in grant.evidence_refs):
        raise ValueError("Authority grant requires explicit evidence_refs.")
    if not validation_evidence_refs or any(
        not _nonempty(ref) for ref in validation_evidence_refs
    ):
        raise ValueError("Boundary validation requires explicit evidence refs.")

    if not _aware(validated_at):
        raise ValueError("validated_at must be timezone-aware.")
    if grant.not_before is not None and not _aware(grant.not_before):
        raise ValueError("not_before must be timezone-aware when present.")
    if grant.not_after is not None and not _aware(grant.not_after):
        raise ValueError("not_after must be timezone-aware when present.")
    if grant.revoked_at is not None:
        if not _aware(grant.revoked_at):
            raise ValueError("revoked_at must be timezone-aware when present.")
        if not grant.revocation_evidence_refs:
            raise ValueError("Revocation requires explicit revocation evidence.")
    if (
        grant.not_before is not None
        and grant.not_after is not None
        and grant.not_before > grant.not_after
    ):
        raise ValueError("Authority validity interval is inverted.")

    return ValidatedAuthorityBasis(
        grant=grant,
        validator_id=validator_id,
        validation_method=validation_method,
        validation_evidence_refs=validation_evidence_refs,
        validated_at=validated_at,
        _seal=_VALIDATED_BASIS_SEAL,
    )


def evaluate_authority_request(
    request: AuthorityRequest,
    basis: object | None = None,
) -> AuthorityResult:
    """Evaluate whether a consequential transition has sufficient authority.

    All outcomes other than AUTHORIZED or AUTHORIZED_WITH_CONSTRAINTS are
    execution-blocking. Executors MUST check result.permitted rather than
    treating reachability or a successful operation attempt as permission.
    """
    required_request = (
        request.transition_id,
        request.actor,
        request.action,
        request.resource,
        request.purpose,
        request.scope,
        request.jurisdiction,
        request.authority,
        request.policy_id,
        request.policy_version,
    )
    if not all(_nonempty(value) for value in required_request):
        return _result(
            request,
            Decision.DEFER,
            AuthorityFailureCode.INVALID_REQUEST,
            "Authority request is structurally incomplete; execution is not permitted.",
        )
    if not _aware(request.at):
        return _result(
            request,
            Decision.DEFER,
            AuthorityFailureCode.TEMPORAL_MISMATCH,
            "Authority request time is not timezone-comparable.",
        )
    if request.schema_version != AUTHORITY_REQUEST_SCHEMA_VERSION:
        return _result(
            request,
            Decision.DEFER,
            AuthorityFailureCode.INVALID_REQUEST,
            "Authority request schema version is not recognized.",
        )
    if basis is None:
        return _result(
            request,
            Decision.DEFER,
            AuthorityFailureCode.AUTHORITY_UNESTABLISHED,
            "No validated authority basis was supplied; capability does not imply permission.",
        )
    if not isinstance(basis, ValidatedAuthorityBasis):
        return _result(
            request,
            Decision.QUARANTINE,
            AuthorityFailureCode.BOUNDARY_UNVALIDATED,
            "Raw or caller-asserted authority claims cannot establish boundary validation.",
        )

    grant = basis.grant
    if not grant.evidence_refs or not basis.validation_evidence_refs:
        return _result(
            request,
            Decision.DEFER,
            AuthorityFailureCode.EVIDENCE_UNESTABLISHED,
            "Authority or boundary-validation evidence is missing.",
            basis=basis,
        )

    if basis.validated_at > request.at:
        return _result(
            request,
            Decision.DENY,
            AuthorityFailureCode.TEMPORAL_MISMATCH,
            "Authority was validated after the proposed transition time.",
            basis=basis,
        )
    if grant.not_before is not None and request.at < grant.not_before:
        return _result(
            request,
            Decision.DENY,
            AuthorityFailureCode.TEMPORAL_MISMATCH,
            "Authority grant is not yet effective.",
            basis=basis,
        )
    if grant.not_after is not None and request.at > grant.not_after:
        return _result(
            request,
            Decision.DENY,
            AuthorityFailureCode.TEMPORAL_MISMATCH,
            "Authority grant has expired.",
            basis=basis,
        )
    if grant.revoked_at is not None and request.at >= grant.revoked_at:
        return _result(
            request,
            Decision.DENY,
            AuthorityFailureCode.AUTHORITY_REVOKED,
            "Authority was revoked before the proposed transition.",
            basis=basis,
        )

    checks = (
        (grant.subject == request.actor, AuthorityFailureCode.ACTOR_MISMATCH, "actor"),
        (_allows(grant.actions, request.action), AuthorityFailureCode.ACTION_MISMATCH, "action"),
        (
            _allows(grant.resources, request.resource),
            AuthorityFailureCode.RESOURCE_MISMATCH,
            "resource",
        ),
        (
            _allows(grant.purposes, request.purpose),
            AuthorityFailureCode.PURPOSE_MISMATCH,
            "purpose",
        ),
        (_allows(grant.scopes, request.scope), AuthorityFailureCode.SCOPE_MISMATCH, "scope"),
        (
            _allows(grant.jurisdictions, request.jurisdiction),
            AuthorityFailureCode.JURISDICTION_MISMATCH,
            "jurisdiction",
        ),
        (
            grant.policy_id == request.policy_id
            and grant.policy_version == request.policy_version,
            AuthorityFailureCode.POLICY_MISMATCH,
            "policy binding",
        ),
        (
            grant.issuer == request.authority,
            AuthorityFailureCode.AUTHORITY_MISMATCH,
            "governing authority",
        ),
    )
    for passed, failure, dimension in checks:
        if not passed:
            return _result(
                request,
                Decision.DENY,
                failure,
                f"Validated authority basis does not cover the requested {dimension}.",
                basis=basis,
            )

    if grant.constraints:
        return _result(
            request,
            Decision.AUTHORIZED_WITH_CONSTRAINTS,
            AuthorityFailureCode.NONE,
            "Authority is established only under the recorded constraints.",
            basis=basis,
        )
    return _result(
        request,
        Decision.AUTHORIZED,
        AuthorityFailureCode.NONE,
        "Authority is explicitly established for this actor, action, resource and context.",
        basis=basis,
    )
