from __future__ import annotations

from typing import TYPE_CHECKING

from .models import ScoredMemory
from .scoring import recency_score, strength_score

if TYPE_CHECKING:
    from .store import SQLiteStore


def detect_and_resolve_conflicts(
    scored: list[ScoredMemory],
    store: SQLiteStore,
    now: float | None = None,
) -> list[ScoredMemory]:
    """Scan activated memories for contradicts edges. Demote the weaker side."""
    if len(scored) < 2:
        return scored

    id_set = {s.memory.id for s in scored}
    by_id = {s.memory.id: s for s in scored}
    demoted: set[str] = set()

    for sm in scored:
        edges = store.get_edges(sm.memory.id)
        for edge in edges:
            if edge.rel_type != "contradicts":
                continue
            other_id = edge.target_id if edge.source_id == sm.memory.id else edge.source_id
            if other_id not in id_set or other_id in demoted or sm.memory.id in demoted:
                continue

            # Rank by strength * confidence * recency
            a = sm
            b = by_id[other_id]
            rank_a = a.memory.strength * a.memory.confidence * recency_score(a.memory, now)
            rank_b = b.memory.strength * b.memory.confidence * recency_score(b.memory, now)

            loser_id = b.memory.id if rank_a >= rank_b else a.memory.id
            demoted.add(loser_id)

    # Apply demotion: halve the score of the weaker contradicting memory
    result = []
    for sm in scored:
        if sm.memory.id in demoted:
            result.append(
                ScoredMemory(
                    memory=sm.memory,
                    score=sm.score * 0.3,
                    activation=sm.activation,
                    components={**sm.components, "conflict_demoted": True},
                )
            )
        else:
            result.append(sm)

    result.sort(key=lambda s: s.score, reverse=True)
    return result
