from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_example(name: str):
    path = ROOT / "examples" / f"{name}.py"
    spec = spec_from_file_location(f"epm_example_{name}", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_example()


def test_basic_transition_reference_example_authorizes():
    result = _run_example("basic_transition")
    assert result["state"] == "PRESERVED"
    assert result["decision"] == "AUTHORIZED"
    assert result["failure"] == "NONE"
    assert result["fail_closed"] is False


def test_temporal_reference_example_rejects_future_evidence():
    result = _run_example("temporal_availability")
    assert result.status.value == "UNAVAILABLE"
    assert result.trusted is True
    assert result.reason_code == "EVIDENCE_NOT_YET_AVAILABLE"


def test_future_effective_rule_reference_example_is_rejected():
    report = _run_example("future_effective_rule")
    assert "RULE_NOT_YET_EFFECTIVE" in report.structural_issues


def test_legal_secondary_use_reference_example_denies():
    result = _run_example("legal_secondary_use")
    assert result["state"] == "INVALIDATED"
    assert result["decision"] == "DENY"
    assert result["failure"] == "MISAPPLICATION"
    assert result["fail_closed"] is True
