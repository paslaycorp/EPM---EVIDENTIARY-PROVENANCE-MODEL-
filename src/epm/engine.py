"""Stable public engine façade for EPM."""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime

from .audit import AuditArtifact, build_audit_artifact
from .envelope import EvidentiaryEnvelope, evaluate_evidentiary_envelope
from .state import EvidentiaryState, EvidentiaryStateReport, inspect_evidentiary_state

EPM_ENGINE_VERSION = "epm-engine/0.1.1"


def assess_transition(envelope: EvidentiaryEnvelope) -> Mapping[str, object]:
    return evaluate_evidentiary_envelope(envelope)


def inspect_state(state: EvidentiaryState) -> EvidentiaryStateReport:
    return inspect_evidentiary_state(state)


def audit_state(
    state: EvidentiaryState,
    *,
    issued_at: datetime,
    transition: Mapping[str, object] | None = None,
) -> AuditArtifact:
    return build_audit_artifact(state, issued_at=issued_at, transition=transition)
