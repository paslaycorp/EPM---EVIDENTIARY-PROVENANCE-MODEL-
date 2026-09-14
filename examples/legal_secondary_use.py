from datetime import UTC, datetime

from epm import AssuranceState, assess_transition
from epm.adapters import LegalEvidenceUse, legal_envelope


def run_example():
    at = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)

    item = LegalEvidenceUse(
        matter_id="MAT-001",
        exhibit_id="EX-001",
        source_assurance=AssuranceState.PRESERVED,
        source_use="admission-review",
        target_use="public-disclosure",
        source_record_scope="case-record",
        target_record_scope="case-record",
        source_jurisdiction="US-TX",
        target_jurisdiction="US-TX",
        source_at=at,
        target_at=at,
        source_rule_id="evidence-rule",
        source_rule_version="1",
        source_authority="court",
        target_rule_id="evidence-rule",
        target_rule_version="1",
        target_authority="court",
        consequence="critical",
    )

    return assess_transition(legal_envelope(item))


if __name__ == "__main__":
    print(run_example())
