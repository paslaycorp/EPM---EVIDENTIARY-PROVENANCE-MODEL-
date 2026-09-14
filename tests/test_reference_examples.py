from examples.basic_transition import run_example as run_basic_transition
from examples.future_effective_rule import run_example as run_future_effective_rule
from examples.legal_secondary_use import run_example as run_legal_secondary_use
from examples.temporal_availability import run_example as run_temporal_availability


def test_basic_transition_reference_example_authorizes():
    result = run_basic_transition()
    assert result["state"] == "PRESERVED"
    assert result["decision"] == "AUTHORIZED"
    assert result["failure"] == "NONE"
    assert result["fail_closed"] is False


def test_temporal_reference_example_rejects_future_evidence():
    result = run_temporal_availability()
    assert result.status.value == "UNAVAILABLE"
    assert result.trusted is True
    assert result.reason_code == "EVIDENCE_NOT_YET_AVAILABLE"


def test_future_effective_rule_reference_example_is_rejected():
    report = run_future_effective_rule()
    assert "RULE_NOT_YET_EFFECTIVE" in report.structural_issues


def test_legal_secondary_use_reference_example_denies():
    result = run_legal_secondary_use()
    assert result["state"] == "INVALIDATED"
    assert result["decision"] == "DENY"
    assert result["failure"] == "MISAPPLICATION"
    assert result["fail_closed"] is True
