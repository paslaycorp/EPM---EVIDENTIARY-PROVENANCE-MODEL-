from __future__ import annotations

import importlib.util
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

from epm import (
    AssuranceContext,
    AssuranceState,
    AvailabilityAttestation,
    EvidenceAvailability,
    EvidentiaryState,
    RuleBinding,
    State,
    TemporalAvailability,
    inspect_state,
)
from epm.justification import (
    JustificationGraph,
    JustificationNode,
    JustificationNodeType,
    SupportEdge,
    SupportRelation,
)


MODULE = Path(__file__).resolve().parents[1] / "experiments" / "tvc" / "dynamic.py"
spec = importlib.util.spec_from_file_location("tvc_dynamic_availability_parity", MODULE)
assert spec and spec.loader
dynamic = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dynamic
spec.loader.exec_module(dynamic)

CLAIM_AT = datetime(2026, 9, 6, 20, 56, tzinfo=UTC)


def _node(node_id: str, node_type: JustificationNodeType, *, external: bool = False):
    return JustificationNode(
        node_id=node_id,
        node_type=node_type,
        provenance_refs=(f"prov:{node_id}",),
        external_origin=external,
    )


def _graph() -> JustificationGraph:
    return JustificationGraph(
        nodes={
            "claim-X": _node("claim-X", JustificationNodeType.CLAIM),
            "derive-X": _node("derive-X", JustificationNodeType.DERIVATION),
            "sensor-E": _node("sensor-E", JustificationNodeType.EVIDENCE, external=True),
        },
        edges=(
            SupportEdge(
                "derive-X",
                "claim-X",
                SupportRelation.SUPPORTS,
                "prov:derive-claim",
            ),
            SupportEdge(
                "sensor-E",
                "derive-X",
                SupportRelation.DERIVATION_INPUT,
                "prov:sensor-derive",
            ),
        ),
    )


def _availability(evidence_id: str, available_at: datetime) -> EvidenceAvailability:
    return EvidenceAvailability(
        evidence_id=evidence_id,
        available_at=available_at,
        observed_at=max(available_at, CLAIM_AT),
        source="canonical-dependency-history",
        provenance_ref=f"availability:{evidence_id}",
        attestation=AvailabilityAttestation(
            attestation_id=f"att:{evidence_id}",
            authority="fixture-authority",
            method="signed-dependency-history",
            basis="same availability fact supplied to EPM and TVC",
            validated=True,
        ),
    )


def _epm_state(*dependency_availability: EvidenceAvailability) -> EvidentiaryState:
    assurance = State(
        state_id="primary-E",
        properties={"evidence": AssuranceState.VALID},
        context=AssuranceContext(at=CLAIM_AT),
        rule=RuleBinding(
            rule_id="rule-X",
            version="1",
            authority="fixture-authority",
            effective_at=CLAIM_AT,
        ),
    )
    return EvidentiaryState(
        state_id="state-X",
        proposition="X",
        assurance_state=assurance,
        availability=(_availability("primary-E", CLAIM_AT),) + dependency_availability,
        justification_graph=_graph(),
    )


def _obligation_ids() -> tuple[str, ...]:
    return tuple(
        obligation.obligation_id
        for obligation in dynamic.derive_graph_obligations(_graph(), target_id="claim-X")
    )


def test_missing_graph_dependency_availability_is_candidate_incremental_delta():
    """Same graph, same absence: EPM does not currently derive the missing duties."""
    state = _epm_state()
    epm_report = inspect_state(state)

    assert epm_report.structural_issues == ()
    assert epm_report.graph_cycle_result is not None
    assert epm_report.graph_cycle_result.cyclic is False
    assert all(
        result.status is TemporalAvailability.AVAILABLE
        for result in epm_report.availability_results
    )

    dynamic_results = dynamic.assess_graph_obligation_availability(
        state.justification_graph,
        target_id="claim-X",
        state_at=CLAIM_AT,
        availability=(),
    )
    assert {result.evidence_id for result in dynamic_results} == set(_obligation_ids())
    assert all(
        result.status is TemporalAvailability.UNKNOWN
        and result.reason_code == "AVAILABILITY_UNKNOWN"
        for result in dynamic_results
    )


def test_explicit_future_dependency_availability_is_overlap_not_unique_value():
    obligation_ids = _obligation_ids()
    records = tuple(
        _availability(
            obligation_id,
            CLAIM_AT + timedelta(hours=1)
            if obligation_id.startswith("DERIVATION_INPUT:")
            else CLAIM_AT,
        )
        for obligation_id in obligation_ids
    )
    state = _epm_state(*records)
    epm_report = inspect_state(state)

    assert any(
        result.status is TemporalAvailability.UNAVAILABLE
        and result.reason_code == "EVIDENCE_NOT_YET_AVAILABLE"
        for result in epm_report.availability_results
    )

    dynamic_results = dynamic.assess_graph_obligation_availability(
        state.justification_graph,
        target_id="claim-X",
        state_at=CLAIM_AT,
        availability=records,
    )
    assert any(
        result.status is TemporalAvailability.UNAVAILABLE
        and result.reason_code == "EVIDENCE_NOT_YET_AVAILABLE"
        for result in dynamic_results
    )


def test_complete_historical_dependency_set_closes_without_fabricated_failure():
    records = tuple(
        _availability(obligation_id, CLAIM_AT)
        for obligation_id in _obligation_ids()
    )
    state = _epm_state(*records)
    epm_report = inspect_state(state)
    dynamic_results = dynamic.assess_graph_obligation_availability(
        state.justification_graph,
        target_id="claim-X",
        state_at=CLAIM_AT,
        availability=records,
    )

    assert all(
        result.status is TemporalAvailability.AVAILABLE
        for result in epm_report.availability_results
    )
    assert all(
        result.status is TemporalAvailability.AVAILABLE and result.trusted
        for result in dynamic_results
    )
