from __future__ import annotations

import math
import time

from .models import Memory, ScoredMemory

# Recency decay: half-life ~14 days
LAMBDA_RECENCY = 0.05
# Strength natural decay rate
ALPHA_DECAY = 0.01
# Reinforcement factor
BETA_REINFORCE = 0.1

# Default competition weights
DEFAULT_WEIGHTS = {
    "activation": 0.5,
    "recency": 0.2,
    "strength": 0.2,
    "confidence": 0.1,
}

# Status penalties
STATUS_PENALTY = {
    "active": 1.0,
    "superseded": 0.5,
    "contradicted": 0.3,
}


def recency_score(memory: Memory, now: float | None = None) -> float:
    """Exponential recency decay. Uses last_accessed if available, else created_at."""
    if now is None:
        now = time.time()
    t_ref = memory.last_accessed if memory.last_accessed is not None else memory.created_at
    days_elapsed = (now - t_ref) / 86400.0
    return math.exp(-LAMBDA_RECENCY * days_elapsed)


def strength_score(memory: Memory, now: float | None = None) -> float:
    """Strength with reinforcement and natural decay, clamped to [0, 1]."""
    if now is None:
        now = time.time()
    days_since_creation = (now - memory.created_at) / 86400.0
    raw = memory.strength * (1 + memory.access_count) ** BETA_REINFORCE * math.exp(
        -ALPHA_DECAY * days_since_creation
    )
    return max(0.0, min(1.0, raw))


def _normalize(values: dict[str, float]) -> dict[str, float]:
    """Min-max normalize to [0, 1]. If all values are equal, return 1.0 for all."""
    if not values:
        return {}
    max_v = max(values.values())
    min_v = min(values.values())
    span = max_v - min_v
    if span == 0:
        return {k: 1.0 for k in values}
    return {k: (v - min_v) / span for k, v in values.items()}


def compete(
    activations: dict[str, float],
    memories: dict[str, Memory],
    weights: dict[str, float] | None = None,
    now: float | None = None,
) -> list[ScoredMemory]:
    """Score and rank activated memories using the competition model.

    Returns ScoredMemory list sorted by descending score.
    """
    if now is None:
        now = time.time()
    w = weights or DEFAULT_WEIGHTS

    if not activations:
        return []

    # Compute raw component scores
    raw_activation = {mid: activations[mid] for mid in activations if mid in memories}
    raw_recency = {mid: recency_score(memories[mid], now) for mid in raw_activation}
    raw_strength = {mid: strength_score(memories[mid], now) for mid in raw_activation}

    # Normalize activation and strength
    norm_activation = _normalize(raw_activation)
    norm_strength = _normalize(raw_strength)

    results = []
    for mid in raw_activation:
        mem = memories[mid]
        components = {
            "activation": norm_activation[mid],
            "recency": raw_recency[mid],
            "strength": norm_strength[mid],
            "confidence": mem.confidence,
        }
        score = (
            w["activation"] * components["activation"]
            + w["recency"] * components["recency"]
            + w["strength"] * components["strength"]
            + w["confidence"] * components["confidence"]
        )
        # Apply status penalty
        penalty = STATUS_PENALTY.get(mem.status, 1.0)
        score *= penalty

        results.append(
            ScoredMemory(
                memory=mem,
                score=score,
                activation=activations[mid],
                components=components,
            )
        )

    results.sort(key=lambda s: s.score, reverse=True)
    return results
