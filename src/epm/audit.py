"""Deterministic operator-facing audit artifacts for EPM."""
from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime

from .state import EvidentiaryState, inspect_evidentiary_state

AUDIT_SCHEMA = "epm.audit-artifact/0.1"


@dataclass(frozen=True)
class AuditArtifact:
    schema_version: str
    issued_at: datetime
    state_id: str
    proposition: str
    structural_issues: tuple[str, ...]
    source_assessments: tuple[Mapping[str, object], ...]
    temporal_assessments: tuple[Mapping[str, object], ...]
    constraint_assessments: tuple[Mapping[str, object], ...]
    answer_space: Mapping[str, object] | None
    graph_integrity: Mapping[str, object] | None
    limitations: tuple[str, ...]
    unresolved_conditions: tuple[str, ...]
    transition: Mapping[str, object] | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "issued_at": self.issued_at.isoformat(),
            "state_id": self.state_id,
            "proposition": self.proposition,
            "structural_issues": list(self.structural_issues),
            "source_assessments": [dict(item) for item in self.source_assessments],
            "temporal_assessments": [dict(item) for item in self.temporal_assessments],
            "constraint_assessments": [dict(item) for item in self.constraint_assessments],
            "answer_space": dict(self.answer_space) if self.answer_space else None,
            "graph_integrity": dict(self.graph_integrity) if self.graph_integrity else None,
            "limitations": list(self.limitations),
            "unresolved_conditions": list(self.unresolved_conditions),
            "transition": dict(self.transition) if self.transition else None,
        }

    def to_markdown(self) -> str:
        lines = [
            "# EPM Audit Artifact",
            "",
            f"- Schema: `{self.schema_version}`",
            f"- Issued at: `{self.issued_at.isoformat()}`",
            f"- State: `{self.state_id}`",
            f"- Proposition: {self.proposition}",
            "",
            "## Structural integrity",
        ]
        lines.extend(f"- {item}" for item in self.structural_issues or ("No structural issues recorded.",))
        lines.extend(["", "## Sources"])
        for item in self.source_assessments:
            lines.append(f"- `{item['reason_code']}` — {item['reason']}")
        lines.extend(["", "## Temporal availability"])
        for item in self.temporal_assessments:
            lines.append(
                f"- `{item['evidence_id']}`: **{item['status']}** "
                f"(`{item['reason_code']}`) — {item['reason']}"
            )
        lines.extend(["", "## Constraints"])
        for item in self.constraint_assessments:
            lines.append(
                f"- `{item['constraint_id']}`: **{item['status']}** "
                f"(`{item['reason_code']}`) — {item['reason']}"
            )
        lines.extend(["", "## Answer space"])
        if self.answer_space:
            lines.append(
                f"- State: **{self.answer_space['resolution_state']}**, "
                f"epistemic standing: **{self.answer_space['epistemic_standing']}**"
            )
            lines.append(f"- Admissible: {', '.join(self.answer_space['admissible_candidates'])}")
        else:
            lines.append("- Not represented in this state.")
        lines.extend(["", "## Dependency graph"])
        if self.graph_integrity:
            lines.append(
                "- Cycle detected: " + ("YES" if self.graph_integrity["cyclic"] else "NO")
            )
        else:
            lines.append("- Not represented in this state.")
        lines.extend(["", "## Limitations"])
        lines.extend(f"- {item}" for item in self.limitations or ("None declared.",))
        lines.extend(["", "## Unresolved conditions"])
        lines.extend(f"- {item}" for item in self.unresolved_conditions or ("None declared.",))
        if self.transition:
            lines.extend(["", "## Transition assurance"])
            for key in ("state", "decision", "failure", "reason", "rule_id", "rule_version"):
                if key in self.transition:
                    lines.append(f"- {key}: `{self.transition[key]}`")
        return "\n".join(lines) + "\n"


def build_audit_artifact(
    state: EvidentiaryState,
    *,
    issued_at: datetime,
    transition: Mapping[str, object] | None = None,
) -> AuditArtifact:
    """Build a deterministic audit record from explicit state and issue time."""
    if issued_at.tzinfo is None or issued_at.utcoffset() is None:
        raise ValueError("issued_at must be timezone-aware")
    report = inspect_evidentiary_state(state)
    source_assessments = tuple(
        {
            "valid": item.valid,
            "reason_code": item.reason_code,
            "reason": item.reason,
        }
        for item in report.source_results
    )
    temporal_assessments = tuple(
        {
            "evidence_id": item.evidence_id,
            "status": item.status.value,
            "trusted": item.trusted,
            "reason_code": item.reason_code,
            "reason": item.reason,
            "available_at": item.available_at.isoformat() if item.available_at else None,
            "provenance_ref": item.provenance_ref,
        }
        for item in report.availability_results
    )
    constraint_assessments = tuple(
        {
            "constraint_id": item.constraint_id,
            "status": item.status.value,
            "reason_code": item.reason_code,
            "reason": item.reason,
        }
        for item in report.constraint_results
    )
    answer_space = None
    if state.answer_space is not None:
        answer_space = {
            "question_id": state.answer_space.question_id,
            "resolution_state": state.answer_space.resolution_state.value,
            "epistemic_standing": state.answer_space.epistemic_standing.value,
            "admissible_candidates": state.answer_space.admissible_candidates,
            "active_constraint_refs": state.answer_space.active_constraint_refs,
            "discriminator_refs": state.answer_space.discriminator_refs,
            "granularity": state.answer_space.granularity,
        }
    graph_integrity = None
    if report.graph_cycle_result is not None:
        graph_integrity = {
            "cyclic": report.graph_cycle_result.cyclic,
            "cycle_nodes": report.graph_cycle_result.cycle_nodes,
        }
    return AuditArtifact(
        schema_version=AUDIT_SCHEMA,
        issued_at=issued_at,
        state_id=state.state_id,
        proposition=state.proposition,
        structural_issues=report.structural_issues,
        source_assessments=source_assessments,
        temporal_assessments=temporal_assessments,
        constraint_assessments=constraint_assessments,
        answer_space=answer_space,
        graph_integrity=graph_integrity,
        limitations=report.limitations,
        unresolved_conditions=report.unresolved_conditions,
        transition=transition,
    )
