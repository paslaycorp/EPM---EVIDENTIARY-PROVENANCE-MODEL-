from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class Phase(str, Enum):
    T2 = "T2"
    T3 = "T3"
    COUNTERFACTUAL_T2 = "COUNTERFACTUAL_T2"


class Resolution(str, Enum):
    UNRESOLVED = "UNRESOLVED"
    HISTORY_A = "HISTORY_A"
    HISTORY_B = "HISTORY_B"


class FailureCode(str, Enum):
    F1_UNSUPPORTED_SELECTION = "F1"
    F2_HIDDEN_ORACLE = "F2"
    F3_HISTORICAL_SMUGGLING = "F3"
    F4_OUTCOME_INFERENCE = "F4"
    F5_UNCERTAINTY_COLLAPSE = "F5"
    F6_TEMPORAL_LAUNDERING = "F6"
    F7_PROVENANCE_FREE_DISCRIMINATOR = "F7"
    F8_AVAILABILITY_FREE_PROVENANCE = "F8"
    F9_NARRATIVE_SUBSTITUTION = "F9"
    F10_IRREVERSIBLE_CONTAMINATION = "F10"
    S1_SCHEMA = "S1"
    S2_BASIS_OUTSIDE_STIMULUS = "S2"
    M1_DECOY_SENSITIVITY = "M1"
    M2_ORDER_SENSITIVITY = "M2"
    M3_NONDETERMINISM = "M3"
    M4_LABEL_MEMORIZATION = "M4"


@dataclass(frozen=True)
class Evidence:
    evidence_id: str
    proposition: str
    source: str
    introduced_at: Phase
    available_at: Phase
    admissible: bool = True
    material: bool = True
    authority: str = "ordinary"

    def to_public(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Stimulus:
    benchmark: str
    phase: Phase
    observations: dict[str, Any]
    evidence: tuple[Evidence, ...]
    candidates: tuple[str, str] = ("HISTORY_A", "HISTORY_B")
    request: str = "Return one machine-readable TargetResponse."

    def to_public(self) -> dict[str, Any]:
        return {
            "benchmark": self.benchmark,
            "phase": self.phase.value,
            "observations": self.observations,
            "evidence": [item.to_public() for item in self.evidence],
            "candidates": list(self.candidates),
            "request": self.request,
        }


@dataclass(frozen=True)
class DiscriminatorRequirement:
    kind: str
    predicate: str
    temporal_scope: Phase


@dataclass(frozen=True)
class HiddenCaseTruth:
    legitimate_history: Resolution
    illegitimate_history: Resolution
    t2_missing_discriminator: DiscriminatorRequirement
    t3_discriminator_evidence_id: str
    correct_outcome_history: Resolution


@dataclass(frozen=True)
class CaseBundle:
    case_name: str
    t2: Stimulus
    t3: Stimulus
    counterfactual_t2: Stimulus
    hidden: HiddenCaseTruth
    decoy_t2: Stimulus
    reordered_t2: Stimulus
    future_evidence_t2: Stimulus
    inadmissible_evidence_t2: Stimulus


@dataclass
class TargetResponse:
    resolution: Resolution
    basis_evidence_ids: list[str] = field(default_factory=list)
    claimed_discriminator_ids: list[str] = field(default_factory=list)
    required_discriminator: dict[str, str] | None = None
    historical_state: dict[str, str] = field(default_factory=dict)
    resolution_time: str | None = None
    transition_basis_ids: list[str] = field(default_factory=list)
    explanation: str = ""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "TargetResponse":
        try:
            resolution = Resolution(payload["resolution"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError("response.resolution must be a valid Resolution") from exc
        return cls(
            resolution=resolution,
            basis_evidence_ids=list(payload.get("basis_evidence_ids", [])),
            claimed_discriminator_ids=list(payload.get("claimed_discriminator_ids", [])),
            required_discriminator=payload.get("required_discriminator"),
            historical_state=dict(payload.get("historical_state", {})),
            resolution_time=payload.get("resolution_time"),
            transition_basis_ids=list(payload.get("transition_basis_ids", [])),
            explanation=str(payload.get("explanation", "")),
        )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["resolution"] = self.resolution.value
        return payload


@dataclass(frozen=True)
class Finding:
    code: FailureCode
    phase: str
    message: str


@dataclass(frozen=True)
class VerificationReport:
    passed: bool
    findings: tuple[Finding, ...]
    checks: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "findings": [
                {"code": f.code.value, "phase": f.phase, "message": f.message}
                for f in self.findings
            ],
            "checks": dict(self.checks),
        }
