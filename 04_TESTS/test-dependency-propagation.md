# Dependency Propagation Test

**ID:** T-15

**Attack:** An upstream evidence or assumption changes while downstream constraints and conclusions remain cached.

**Pass:** Dependency propagation marks affected descendants for reevaluation.

**Fail:** Cached conclusions remain trusted without revalidation.
