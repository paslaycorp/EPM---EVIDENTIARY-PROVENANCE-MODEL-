from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run_reference():
    path = ROOT / "examples" / "legal_chain_of_custody.py"
    spec = spec_from_file_location("epm_example_legal_chain_of_custody", path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.run_reference()


def test_legal_chain_of_custody_preserves_only_explicitly_authorized_use():
    result = _run_reference()

    preserved = result["custody_preserved"]
    blocked = result["secondary_use_blocked"]

    assert preserved["decision"] == "AUTHORIZED"
    assert preserved["failure"] == "NONE"
    assert preserved["state"] == "PRESERVED"
    assert preserved["fail_closed"] is False

    assert blocked["decision"] == "DENY"
    assert blocked["failure"] == "MISAPPLICATION"
    assert blocked["state"] == "INVALIDATED"
    assert blocked["fail_closed"] is True
