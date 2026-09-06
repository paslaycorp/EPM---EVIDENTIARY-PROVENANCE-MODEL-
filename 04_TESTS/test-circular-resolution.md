# Circular Resolution Test

**ID:** T-06

**Attack:** A candidate answer is used to justify the discriminator that supposedly resolves that answer.

**Pass:** Dependency analysis detects the circularity and prevents self-supporting resolution.

**Fail:** The loop is accepted as independent support.
