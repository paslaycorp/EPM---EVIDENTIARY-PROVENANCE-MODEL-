"""Prospective, outcome-blind closure contract experiment.

The contract is generated before the claimed epistemic transition result exists.
It binds prior state, policy, material dependencies, and a counterfactual response
surface without receiving the later asserted standing as an input.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from itertools import combinations
from typing import Callable, Iterable


Reconstruct = Callable[[frozenset[str]], str]


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


@dataclass(frozen=True)
class ContractClosureResult:
    valid: bool
    reason: str
    asserted_standing: str
    reproduced_standing: str
    contract_digest: str


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
    dependencies, surface = _surface(material_dependencies, reconstruct)
    lines = [
        transition_id,
        issued_at.isoformat(),
        policy_id,
        prior_standing,
        ",".join(dependencies),
    ]
    lines.extend(f"{','.join(removed)}=>{standing}" for removed, standing in surface)
    digest = sha256("\n".join(lines).encode("utf-8")).hexdigest()
    return ProspectiveClosureContract(
        transition_id=transition_id,
        issued_at=issued_at,
        policy_id=policy_id,
        prior_standing=prior_standing,
        material_dependencies=dependencies,
        prospective_surface=surface,
        contract_digest=digest,
        anchor_ref=anchor(digest),
    )


def close_against_contract(
    contract: ProspectiveClosureContract,
    *,
    asserted_standing: str,
    reconstruct: Reconstruct,
    verify_anchor: Callable[[str, str], bool],
) -> ContractClosureResult:
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
