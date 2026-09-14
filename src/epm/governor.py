"""Decision governor for consequential EPM outcomes."""
from __future__ import annotations

from .assurance import AssuranceState, Decision, FailureCode


def govern(
    *,
    assurance_state: AssuranceState,
    failure: FailureCode,
    consequence: str,
) -> Decision:
    """Map an evaluated assurance result to an admissibility decision."""
    if assurance_state is AssuranceState.UNKNOWN:
        return Decision.DEFER
    if failure is FailureCode.NONE and assurance_state is AssuranceState.PRESERVED:
        return Decision.AUTHORIZED
    if consequence.lower() == "critical":
        return Decision.DENY
    return Decision.QUARANTINE
