"""JANUS-001 subterranean reference kernel.

Research-only. No EPM Core or TVC dependency.

JANUS tracks the nearest admissible epistemic failure shadows and the independent
separation witnesses that keep the current standing from those shadows. It does
not convert fragility into falsity: endpoint standing and structural margin are
separate outputs.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from hashlib import sha256
from itertools import combinations
from typing import Iterable


class MarginEvent(str, Enum):
    STABLE = "STABLE"
    PREFailure_FRAGILITY = "PREFAILURE_FRAGILITY"
    ROBUSTNESS_GAIN = "ROBUSTNESS_GAIN"
    ROBUSTNESS_INFLATION = "ROBUSTNESS_INFLATION"
    FAILED = "FAILED"


@dataclass(frozen=True)
class DependencyClass:
    class_id: str
    member_evidence_ids: tuple[str, ...]


@dataclass(frozen=True)
class SeparationWitness:
    witness_id: str
    shadow_id: str
    dependency_class_id: str
    provenance_valid: bool = True
    active: bool = True


@dataclass(frozen=True)
class Shadow:
    shadow_id: str
    # Independent dependency classes whose simultaneous loss admits this
    # endpoint-changing shadow.
    required_losses: frozenset[str]


@dataclass(frozen=True)
class JanusState:
    state_id: str
    standing: str
    dependency_classes: tuple[DependencyClass, ...]
    shadows: tuple[Shadow, ...]
    witnesses: tuple[SeparationWitness, ...]


@dataclass(frozen=True)
class MarginCertificate:
    state_id: str
    standing: str
    distance: int | None
    nearest_shadows: tuple[str, ...]
    active_class_ids: tuple[str, ...]
    certificate_digest: str


@dataclass(frozen=True)
class MarginTransition:
    prior_distance: int | None
    current_distance: int | None
    endpoint_unchanged: bool
    event: MarginEvent
    explanation_ids: tuple[str, ...]


def _active_classes(state: JanusState) -> frozenset[str]:
    valid_classes = {d.class_id for d in state.dependency_classes}
    return frozenset(
        w.dependency_class_id
        for w in state.witnesses
        if w.active and w.provenance_valid and w.dependency_class_id in valid_classes
    )


def measure_margin(state: JanusState) -> MarginCertificate:
    active = _active_classes(state)
    reachable: list[tuple[int, str]] = []
    for shadow in state.shadows:
        # A required loss is currently separated only while its class has a
        # valid active witness. Missing witnesses mean that part of the shadow
        # is already admissible and therefore costs zero additional losses.
        remaining = shadow.required_losses & active
        reachable.append((len(remaining), shadow.shadow_id))

    if not reachable:
        distance, nearest = None, ()
    else:
        distance = min(n for n, _ in reachable)
        nearest = tuple(sorted(sid for n, sid in reachable if n == distance))

    rows = (
        f"state={state.state_id}",
        f"standing={state.standing}",
        f"distance={distance}",
        "nearest=" + ",".join(nearest),
        "active=" + ",".join(sorted(active)),
    )
    digest = sha256("\n".join(rows).encode()).hexdigest()
    return MarginCertificate(
        state_id=state.state_id,
        standing=state.standing,
        distance=distance,
        nearest_shadows=nearest,
        active_class_ids=tuple(sorted(active)),
        certificate_digest=digest,
    )


def classify_transition(
    prior: MarginCertificate,
    current: MarginCertificate,
    explanation_ids: Iterable[str] = (),
) -> MarginTransition:
    ids = tuple(sorted(set(explanation_ids)))
    same_endpoint = prior.standing == current.standing

    if current.distance == 0:
        event = MarginEvent.FAILED
    elif prior.distance is None or current.distance is None:
        event = MarginEvent.STABLE
    elif current.distance < prior.distance and same_endpoint:
        event = MarginEvent.PREFailure_FRAGILITY
    elif current.distance > prior.distance:
        event = MarginEvent.ROBUSTNESS_GAIN if ids else MarginEvent.ROBUSTNESS_INFLATION
    else:
        event = MarginEvent.STABLE

    return MarginTransition(
        prior_distance=prior.distance,
        current_distance=current.distance,
        endpoint_unchanged=same_endpoint,
        event=event,
        explanation_ids=ids,
    )


def minimal_shadow_basis(state: JanusState) -> tuple[frozenset[str], ...]:
    """Return the antichain of minimal independent loss sets.

    This is intentionally exhaustive before compression. JANUS-001 is small;
    later optimization is forbidden until equivalence is demonstrated.
    """
    classes = tuple(sorted(d.class_id for d in state.dependency_classes))
    failures: list[frozenset[str]] = []
    for n in range(len(classes) + 1):
        for combo in combinations(classes, n):
            lost = frozenset(combo)
            if any(shadow.required_losses <= lost for shadow in state.shadows):
                if not any(existing <= lost for existing in failures):
                    failures.append(lost)
    return tuple(failures)
