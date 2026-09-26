"""Prospective, outcome-blind closure contract experiment.

The contract is generated before the claimed epistemic transition result exists.
It binds prior state, policy, material dependencies, and a counterfactual response
surface without receiving the later asserted standing as an input.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
from itertools import combinations
import json
from typing import Callable, Iterable


Reconstruct = Callable[[frozenset[str]], str]
CONTRACT_SCHEMA = "tvc.prospective-closure/v2"


@dataclass(frozen=True)
class ProspectiveClosureContract:
    transition_id: str
    issued_at: datetime
    policy_id: str
    prior_standing: str
    material_dependencies: tuple[str, ...]
    prospective_surface: tuple[tuple[tuple[str, ...], str], ...]
    contract_digest: str
    anchor_ref: str
    schema: str = CONTRACT_SCHEMA


@dataclass(frozen=True)
class ContractClosureResult:
    valid: bool
    reason: str
    asserted_standing: str
    reproduced_standing: str
    contract_digest: str


def _text(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("contract identifiers and standings must be nonempty strings")
    return value


def _utc(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("contract issue time must be timezone-aware")
    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _payload_bytes(contract: ProspectiveClosureContract) -> bytes:
    """Typed, domain-separated encoding; never trust the supplied digest alone.

    V2 rejects legacy digests rather than silently reinterpreting old receipts.
    The anchor authenticates this payload, not external timestamp truth or
    completeness of the caller-supplied dependency universe.
    """
    if contract.schema != CONTRACT_SCHEMA:
        raise ValueError("unsupported contract schema")
    deps = contract.material_dependencies
    if not isinstance(deps, tuple) or any(not isinstance(name, str) or not name.strip() for name in deps):
        raise ValueError("dependencies must be a canonical tuple of identifiers")
    if deps != tuple(sorted(set(deps))):
        raise ValueError("dependencies must be sorted and unique")
    expected = tuple(removed for size in range(len(deps) + 1) for removed in combinations(deps, size))
    surface = contract.prospective_surface
    if not isinstance(surface, tuple) or len(surface) != len(expected):
        raise ValueError("contract must contain the complete canonical surface")
    for row, removed in zip(surface, expected, strict=True):
        if not isinstance(row, tuple) or len(row) != 2 or row[0] != removed:
            raise ValueError("contract surface is not canonical")
        _text(row[1])
    payload = {
        "schema": contract.schema,
        "transition_id": _text(contract.transition_id),
        "issued_at": _utc(contract.issued_at),
        "policy_id": _text(contract.policy_id),
        "prior_standing": _text(contract.prior_standing),
        "material_dependencies": deps,
        "prospective_surface": surface,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def _surface(dependencies: Iterable[str], reconstruct: Reconstruct):
    deps = tuple(sorted(set(dependencies)))
    full = frozenset(deps)
    rows = []
    for size in range(len(deps) + 1):
        for removed in combinations(deps, size):
            rows.append((tuple(removed), reconstruct(full - frozenset(removed))))
    return deps, tuple(rows)


def issue_contract(
    *,
    transition_id: str,
    issued_at: datetime,
    policy_id: str,
    prior_standing: str,
    material_dependencies: Iterable[str],
    reconstruct: Reconstruct,
    anchor: Callable[[str], str],
) -> ProspectiveClosureContract:
    # Reject invalid metadata before invoking either caller-supplied callback.
    _utc(issued_at)
    for field in (transition_id, policy_id, prior_standing):
        _text(field)
    material_dependencies = tuple(material_dependencies)
    for dependency in material_dependencies:
        _text(dependency)
    dependencies, surface = _surface(material_dependencies, reconstruct)
    contract = ProspectiveClosureContract(
        transition_id=transition_id,
        issued_at=issued_at,
        policy_id=policy_id,
        prior_standing=prior_standing,
        material_dependencies=dependencies,
        prospective_surface=surface,
        contract_digest="",
        anchor_ref="",
    )
    digest = sha256(_payload_bytes(contract)).hexdigest()
    return replace(contract, contract_digest=digest, anchor_ref=anchor(digest))


def close_against_contract(
    contract: ProspectiveClosureContract,
    *,
    asserted_standing: str,
    reconstruct: Reconstruct,
    verify_anchor: Callable[[str, str], bool],
) -> ContractClosureResult:
    if contract.schema != CONTRACT_SCHEMA:
        return ContractClosureResult(False, "CONTRACT_SCHEMA_UNSUPPORTED", asserted_standing, "UNKNOWN", contract.contract_digest)
    try:
        expected_digest = sha256(_payload_bytes(contract)).hexdigest()
    except (TypeError, ValueError, OverflowError):
        return ContractClosureResult(False, "CONTRACT_PAYLOAD_INVALID", asserted_standing, "UNKNOWN", contract.contract_digest)
    if expected_digest != contract.contract_digest:
        return ContractClosureResult(False, "PAYLOAD_DIGEST_MISMATCH", asserted_standing, "UNKNOWN", contract.contract_digest)
    if not verify_anchor(contract.contract_digest, contract.anchor_ref):
        return ContractClosureResult(
            False, "ANCHOR_MISMATCH", asserted_standing, "UNKNOWN", contract.contract_digest
        )
    _, reproduced_surface = _surface(contract.material_dependencies, reconstruct)
    if reproduced_surface != contract.prospective_surface:
        return ContractClosureResult(
            False,
            "PROSPECTIVE_SURFACE_MISMATCH",
            asserted_standing,
            reconstruct(frozenset(contract.material_dependencies)),
            contract.contract_digest,
        )
    reproduced = reconstruct(frozenset(contract.material_dependencies))
    if reproduced != asserted_standing:
        return ContractClosureResult(
            False, "ASSERTED_RESULT_MISMATCH", asserted_standing, reproduced, contract.contract_digest
        )
    return ContractClosureResult(True, "CLOSED", asserted_standing, reproduced, contract.contract_digest)
