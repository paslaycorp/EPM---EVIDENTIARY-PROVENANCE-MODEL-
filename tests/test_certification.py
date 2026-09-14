from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from epm import (
    AssuranceContext,
    AssuranceState,
    AvailabilityAttestation,
    Constraint,
    ConstraintStatus,
    EntailmentStatus,
    EvidenceAvailability,
    EvidentiaryEnvelope,
    EvidentiaryState,
    GitHubActionsRunReceipt,
    PremiseState,
    PreservationProof,
    RuleBinding,
    State,
    TemporalAvailability,
    assess_temporal_availability,
    assess_transition,
    audit_state,
    evaluate_constraint,
    ingest_github_actions_run,
)
from epm.adapters import (
    AdapterInputError,
    InsuranceEvidenceUse,
    LegalEvidenceUse,
    ScientificEvidenceUse,
    insurance_envelope,
    legal_envelope,
    scientific_envelope,
)
from epm.availability import AvailabilityIngestionError
from epm.justification import (
    JustificationGraph,
    JustificationNode,
    JustificationNodeStatus,
    JustificationNodeType,
    SupportEdge,
    SupportRelation,
    add_node,
    add_support_edge,
    assess_independence,
    detect_cycle,
    empty_graph,
    invalidate_node,
)
from epm.resolution import (
    ClosureBasis,
    Discriminator,
    DiscriminatorObservation,
    EpistemicStanding,
    ResolutionState,
    close_answer_space,
    create_answer_space,
    recompute_with_constraints,
    record_derivation,
    resolve_with_observation,
)
from epm.sources import (
    EpistemicSourceRecord,
    EpistemicSourceType,
    observation_reclassification_allowed,
)

AT = datetime(2026, 9, 14, 2, 1, 16, tzinfo=UTC)


def _rule(version: str = "1", authority: str = "authority", jurisdiction: str = "US") -> RuleBinding:
    return RuleBinding("rule", version, authority, jurisdiction, AT)


def _context(purpose: str = "review", scope: str = "record", jurisdiction: str = "US", at: datetime = AT) -> AssuranceContext:
    return AssuranceContext("subject", purpose, scope, jurisdiction, at)


def _envelope(*, source_state: AssuranceState = AssuranceState.PRESERVED, source_context: AssuranceContext | None = None, target_context: AssuranceContext | None = None, source_rule: RuleBinding | None = None, target_rule: RuleBinding | None = None, consequence: str = "standard", proof: PreservationProof | None = None) -> EvidentiaryEnvelope:
    source_context = source_context or _context()
    target_context = target_context or source_context
    source_rule = source_rule or _rule()
    target_rule = target_rule or source_rule
    material = source_context != target_context or source_rule != target_rule
    return EvidentiaryEnvelope(
        transition_id="T-1",
        source=State("E-1", {"applicability": source_state}, source_context, source_rule),
        target=State("E-1:target", {"applicability": AssuranceState.PRESERVED}, target_context, target_rule),
        material_properties=frozenset({"applicability"}) if material else frozenset(),
        preservation={"applicability": proof} if proof else {},
        consequence=consequence,
    )


def _constraint(state: PremiseState = PremiseState.ESTABLISHED) -> Constraint:
    return Constraint(
        constraint_id="C-1",
        proposition="Premise excludes Y.",
        premise_refs=("P-1",),
        premise_states={"P-1": state},
        provenance_refs=("prov:P-1",),
        entailment_basis="P-1 entails exclusion of Y at the declared granularity.",
        entailment_status=EntailmentStatus.ESTABLISHED,
        excluded_candidates=("Y",),
        source_ref="source:P-1",
    )


def _space():
    return create_answer_space(
        question_id="Q-1",
        candidates=("X", "Y"),
        granularity="binary identity",
        granularity_basis="The bounded test question declares exactly X and Y.",
    )


def _observation() -> EpistemicSourceRecord:
    return EpistemicSourceRecord(
        source_id="OBS-1",
        source_type=EpistemicSourceType.OBSERVATION,
        producer="external-sensor",
        provenance_refs=("prov:OBS-1",),
        external_origin=True,
    )


def test_unknown_is_conserved_as_defer():
    result = assess_transition(_envelope(source_state=AssuranceState.UNKNOWN))
    assert result["state"] == "UNKNOWN"
    assert result["decision"] == "DEFER"
    assert result["failure"] == "NONE"


def test_material_purpose_change_quarantines_standard_consequence():
    result = assess_transition(_envelope(target_context=_context(purpose="secondary-use")))
    assert result["failure"] == "MISAPPLICATION"
    assert result["decision"] == "QUARANTINE"
    assert result["fail_closed"] is True


def test_material_purpose_change_denies_critical_consequence():
    result = assess_transition(
        _envelope(target_context=_context(purpose="secondary-use"), consequence="critical")
    )
    assert result["decision"] == "DENY"


def test_valid_preservation_authorizes_material_transition():
    target = _context(purpose="secondary-use")
    proof = PreservationProof(
        property_name="applicability",
        transition_id="T-1",
        rule_id="rule",
        rule_version="1",
        authority="authority",
        evidence_refs=("prov:bridge",),
        source_purpose="review",
        target_purpose="secondary-use",
        source_scope="record",
        target_scope="record",
        source_jurisdiction="US",
        target_jurisdiction="US",
    )
    result = assess_transition(_envelope(target_context=target, proof=proof))
    assert result["state"] == "PRESERVED"
    assert result["decision"] == "AUTHORIZED"


def test_wrong_preservation_authority_fails_closed():
    target = _context(purpose="secondary-use")
    proof = PreservationProof(
        property_name="applicability",
        transition_id="T-1",
        rule_id="rule",
        rule_version="1",
        authority="wrong-authority",
        evidence_refs=("prov:bridge",),
    )
    result = assess_transition(_envelope(target_context=target, proof=proof))
    assert result["failure"] == "AUTHORITY_MISMATCH"


def test_missing_availability_stays_unknown():
    result = assess_temporal_availability(evidence_id="E-1", state_at=AT, availability=None)
    assert result.status is TemporalAvailability.UNKNOWN
    assert result.trusted is False


def test_unvalidated_availability_stays_unknown():
    record = EvidenceAvailability(
        evidence_id="E-1",
        available_at=AT,
        observed_at=AT,
        source="test",
        provenance_ref="prov:test",
        attestation=AvailabilityAttestation("A-1", "authority", "method", "basis", False),
    )
    result = assess_temporal_availability(evidence_id="E-1", state_at=AT, availability=record)
    assert result.status is TemporalAvailability.UNKNOWN
    assert result.reason_code == "AVAILABILITY_UNTRUSTED"


def test_github_actions_connector_accepts_bounded_real_run_receipt():
    receipt = GitHubActionsRunReceipt(
        evidence_id="ci:FAP-Insurance:83",
        repository="paslaycorp/FAP-Insurance",
        run_id=34797796926,
        created_at=datetime(2026, 9, 14, 2, 1, 16, tzinfo=UTC),
        observed_at=datetime(2026, 9, 14, 2, 1, 32, tzinfo=UTC),
        api_url="https://api.github.com/repos/paslaycorp/FAP-Insurance/actions/runs/34797796926",
        transport_verified=True,
    )
    availability = ingest_github_actions_run(receipt)
    assert availability.attestation.validated is True
    assert availability.available_at == receipt.created_at
    assert availability.provenance_ref == receipt.api_url


def test_github_actions_connector_rejects_unverified_transport():
    receipt = GitHubActionsRunReceipt(
        "E-1",
        "paslaycorp/FAP-Insurance",
        34797796926,
        AT,
        AT,
        "https://api.github.com/repos/paslaycorp/FAP-Insurance/actions/runs/34797796926",
        False,
    )
    with pytest.raises(AvailabilityIngestionError):
        ingest_github_actions_run(receipt)


def test_github_actions_connector_rejects_wrong_host():
    receipt = GitHubActionsRunReceipt(
        "E-1",
        "paslaycorp/FAP-Insurance",
        34797796926,
        AT,
        AT,
        "https://example.com/repos/paslaycorp/FAP-Insurance/actions/runs/34797796926",
        True,
    )
    with pytest.raises(AvailabilityIngestionError):
        ingest_github_actions_run(receipt)


def test_trusted_future_availability_is_unavailable_not_unknown():
    receipt = GitHubActionsRunReceipt(
        "E-1",
        "paslaycorp/FAP-Insurance",
        34797796926,
        AT + timedelta(hours=1),
        AT + timedelta(hours=1, minutes=1),
        "https://api.github.com/repos/paslaycorp/FAP-Insurance/actions/runs/34797796926",
        True,
    )
    result = assess_temporal_availability(
        evidence_id="E-1",
        state_at=AT,
        availability=ingest_github_actions_run(receipt),
    )
    assert result.status is TemporalAvailability.UNAVAILABLE


def test_computational_discovery_cannot_be_relabelled_observation():
    source = EpistemicSourceRecord(
        "COMP-1",
        EpistemicSourceType.COMPUTATIONAL_DISCOVERY,
        "solver",
        ("prov:solver",),
    )
    result = observation_reclassification_allowed(source)
    assert result.valid is False
    assert result.reason_code == "NEW_OBSERVATION_REQUIRED"


def test_valid_constraint_narrows_singleton_but_does_not_resolve():
    result = recompute_with_constraints(_space(), (_constraint(),))
    assert result.snapshot.admissible_candidates == ("X",)
    assert result.snapshot.resolution_state is ResolutionState.CONSTRAINED
    assert result.snapshot.epistemic_standing is EpistemicStanding.DERIVED


def test_invalidated_constraint_reopens_answer_space():
    constrained = recompute_with_constraints(_space(), (_constraint(),)).snapshot
    invalidated = replace(_constraint(), premise_states={"P-1": PremiseState.INVALIDATED})
    result = recompute_with_constraints(constrained, (invalidated,))
    assert result.snapshot.admissible_candidates == ("X", "Y")
    assert result.snapshot.resolution_state is ResolutionState.UNRESOLVED
    assert result.reason_code == "REOPENED"


def test_derivation_does_not_resolve_singleton():
    constrained = recompute_with_constraints(_space(), (_constraint(),)).snapshot
    derived = record_derivation(constrained, candidate="X", derivation_ref="calc:1")
    assert derived.snapshot.resolution_state is ResolutionState.CONSTRAINED
    assert derived.snapshot.epistemic_standing is EpistemicStanding.DERIVED


def test_external_observation_resolves_but_closure_needs_external_basis():
    constrained = recompute_with_constraints(_space(), (_constraint(),)).snapshot
    discriminator = Discriminator(
        "D-1",
        ("X",),
        {"observed-x": ("X",)},
        ("prov:D-1",),
    )
    resolved = resolve_with_observation(
        constrained,
        discriminator,
        DiscriminatorObservation("D-1", "observed-x", _observation()),
    ).snapshot
    assert resolved.resolution_state is ResolutionState.RESOLVED
    denied = close_answer_space(
        resolved,
        ClosureBasis(True, ("basis:domain",), (), ()),
    )
    assert denied.applied is False
    closed = close_answer_space(
        resolved,
        ClosureBasis(True, ("basis:domain",), ("OBS-1",), ()),
    )
    assert closed.snapshot.resolution_state is ResolutionState.CLOSED


def test_raw_circular_graph_is_detected():
    nodes = {
        "A": JustificationNode("A", JustificationNodeType.CLAIM, ("prov:A",)),
        "B": JustificationNode("B", JustificationNodeType.EVIDENCE, ("prov:B",), True),
    }
    graph = JustificationGraph(
        nodes,
        (
            SupportEdge("A", "B", SupportRelation.SUPPORTS, "prov:A-B"),
            SupportEdge("B", "A", SupportRelation.SUPPORTS, "prov:B-A"),
        ),
    )
    assert detect_cycle(graph).cyclic is True


def test_shared_external_origin_is_not_independent_corroboration():
    graph = empty_graph()
    for node in (
        JustificationNode("ROOT", JustificationNodeType.EVIDENCE, ("prov:ROOT",), True),
        JustificationNode("D1", JustificationNodeType.DERIVATION, ("prov:D1",)),
        JustificationNode("D2", JustificationNodeType.DERIVATION, ("prov:D2",)),
        JustificationNode("TARGET", JustificationNodeType.CLAIM, ("prov:TARGET",)),
    ):
        graph = add_node(graph, node).graph
    for edge in (
        SupportEdge("ROOT", "D1", SupportRelation.DERIVATION_INPUT, "prov:1"),
        SupportEdge("ROOT", "D2", SupportRelation.DERIVATION_INPUT, "prov:2"),
        SupportEdge("D1", "TARGET", SupportRelation.SUPPORTS, "prov:3"),
        SupportEdge("D2", "TARGET", SupportRelation.SUPPORTS, "prov:4"),
    ):
        graph = add_support_edge(graph, edge).graph
    result = assess_independence(graph, support_a="D1", support_b="D2", target_id="TARGET")
    assert result.independent is False
    assert result.reason_code == "SHARED_ORIGIN"


def test_dependency_invalidation_propagates_staleness():
    graph = empty_graph()
    for node in (
        JustificationNode("ROOT", JustificationNodeType.EVIDENCE, ("prov:R",), True),
        JustificationNode("DER", JustificationNodeType.DERIVATION, ("prov:D",)),
        JustificationNode("TARGET", JustificationNodeType.CLAIM, ("prov:T",)),
    ):
        graph = add_node(graph, node).graph
    graph = add_support_edge(graph, SupportEdge("ROOT", "DER", SupportRelation.DERIVATION_INPUT, "p1")).graph
    graph = add_support_edge(graph, SupportEdge("DER", "TARGET", SupportRelation.SUPPORTS, "p2")).graph
    updated = invalidate_node(graph, node_id="ROOT", reason="source withdrawn").graph
    assert updated.nodes["ROOT"].status is JustificationNodeStatus.INVALIDATED
    assert updated.nodes["DER"].status is JustificationNodeStatus.STALE
    assert updated.nodes["TARGET"].status is JustificationNodeStatus.STALE


def test_insurance_adapter_unchanged_context_authorizes():
    item = InsuranceEvidenceUse(
        "CLM-1", "E-1", AssuranceState.PRESERVED,
        "claim-review", "claim-review", "claim", "claim", "US-TX", "US-TX",
        AT, AT, "carrier", "1", "carrier", "carrier", "1", "carrier",
    )
    assert assess_transition(insurance_envelope(item))["decision"] == "AUTHORIZED"


def test_legal_adapter_blocks_unpreserved_secondary_use_critically():
    item = LegalEvidenceUse(
        "MAT-1", "EX-1", AssuranceState.PRESERVED,
        "admission", "public-disclosure", "case-record", "case-record",
        "US-TX", "US-TX", AT, AT,
        "evidence-rule", "1", "court", "evidence-rule", "1", "court",
    )
    result = assess_transition(legal_envelope(item))
    assert result["failure"] == "MISAPPLICATION"
    assert result["decision"] == "DENY"


def test_scientific_adapter_blocks_unpreserved_rule_version_drift():
    item = ScientificEvidenceUse(
        "STUDY-1", "DATA-1", AssuranceState.PRESERVED,
        "primary-analysis", "primary-analysis", "protocol-A", "protocol-A",
        "LAB", "LAB", AT, AT,
        "protocol", "1", "irb", "protocol", "2", "irb",
    )
    result = assess_transition(scientific_envelope(item))
    assert result["failure"] == "RULE_MISMATCH"
    assert result["decision"] == "QUARANTINE"


def test_adapter_rejects_missing_material_context():
    item = InsuranceEvidenceUse(
        "CLM-1", "E-1", AssuranceState.PRESERVED,
        "claim-review", "claim-review", "", "claim", "US-TX", "US-TX",
        AT, AT, "carrier", "1", "carrier", "carrier", "1", "carrier",
    )
    with pytest.raises(AdapterInputError):
        insurance_envelope(item)


def test_audit_artifact_preserves_unresolved_conditions_and_has_no_master_score():
    assurance_state = State("E-1", {"applicability": AssuranceState.UNKNOWN}, _context(), _rule())
    state = EvidentiaryState(
        state_id="S-1",
        proposition="Whether evidence is currently applicable.",
        assurance_state=assurance_state,
        unresolved_conditions=("trusted domain availability not supplied",),
        limitations=("bounded test state",),
    )
    artifact = audit_state(state, issued_at=AT)
    payload = artifact.to_dict()
    assert "confidence" not in payload
    assert "score" not in payload
    assert payload["unresolved_conditions"] == ["trusted domain availability not supplied"]
    assert "UNKNOWN" in artifact.to_markdown()


def test_audit_issue_time_must_be_timezone_aware():
    state = EvidentiaryState(
        "S-1",
        "p",
        State("E-1", {"applicability": AssuranceState.UNKNOWN}, _context(), _rule()),
    )
    with pytest.raises(ValueError):
        audit_state(state, issued_at=datetime(2026, 9, 14, 2, 1, 16))


def test_transition_evaluation_is_deterministic_on_replay():
    envelope = _envelope(target_context=_context(purpose="secondary-use"))
    assert assess_transition(envelope) == assess_transition(envelope)


def test_constraint_unknown_premise_is_not_valid():
    result = evaluate_constraint(_constraint(PremiseState.UNKNOWN))
    assert result.status is ConstraintStatus.UNSUPPORTED
