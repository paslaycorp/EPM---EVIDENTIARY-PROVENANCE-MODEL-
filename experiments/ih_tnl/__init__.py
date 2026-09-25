"""Executable IH-TNL benchmark research harness.

This package is deliberately isolated from EPM Core. It is a black-box benchmark
for temporal epistemic discipline, not an EPM runtime dependency.
"""

from .fixtures import canonical_case
from .verifier import verify_transcript

__all__ = ["canonical_case", "verify_transcript"]
