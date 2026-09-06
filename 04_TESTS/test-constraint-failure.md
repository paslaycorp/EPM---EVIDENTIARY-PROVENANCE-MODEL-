# Constraint Failure Test

**ID:** T-05

**Attack:** A premise supporting a constraint is later invalidated.

**Pass:** The affected constraint and every dependent result become stale, invalid, or explicitly reopened.

**Fail:** The narrowed answer-space survives after its supporting premise is broken.
