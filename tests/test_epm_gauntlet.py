from tools.epm_gauntlet import GAUNTLET_SCHEMA, RELEASE_SHA, run_gauntlet


def test_blackbox_gauntlet_passes_every_declared_invariant():
    receipt = run_gauntlet()

    assert receipt.schema_version == GAUNTLET_SCHEMA
    assert receipt.release_sha == RELEASE_SHA
    assert receipt.engine_version == "epm-engine/0.1.1"
    assert receipt.total_cases >= 12
    assert receipt.failed_cases == 0
    assert receipt.passed_cases == receipt.total_cases
    assert receipt.result == "PASS"


def test_blackbox_gauntlet_case_ids_are_unique():
    receipt = run_gauntlet()
    case_ids = [case.case_id for case in receipt.cases]
    assert len(case_ids) == len(set(case_ids))
