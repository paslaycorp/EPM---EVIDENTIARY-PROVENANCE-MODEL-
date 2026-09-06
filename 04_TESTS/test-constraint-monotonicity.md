# Constraint Monotonicity Test

**ID:** T-09

**Attack:** A later constraint changes the admissible answer-space.

**Pass:** The model records whether the operation narrows, widens, or reopens the space and preserves revision history.

**Fail:** Historical states are silently overwritten or narrowing is assumed irreversible.
