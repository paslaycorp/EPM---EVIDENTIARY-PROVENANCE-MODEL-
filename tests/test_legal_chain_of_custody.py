from examples.legal_chain_of_custody import run_reference


def test_legal_chain_of_custody_preserves_only_explicitly_authorized_use():
    result = run_reference()

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
