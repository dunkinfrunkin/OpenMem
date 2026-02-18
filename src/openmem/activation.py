from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .store import SQLiteStore


def spread_activation(
    seed_activations: dict[str, float],
    store: SQLiteStore,
    max_hops: int = 2,
    decay_per_hop: float = 0.5,
) -> dict[str, float]:
    """Spreading activation over the memory graph.

    Starting from seed nodes (typically BM25 hits), propagates activation
    along edges with decay per hop. Returns memory_id → activation_score.
    """
    activations = dict(seed_activations)
    frontier = set(seed_activations.keys())

    for hop in range(max_hops):
        next_frontier: dict[str, float] = {}
        for node_id in frontier:
            for edge, neighbor in store.get_neighbors(node_id):
                spread = activations[node_id] * edge.weight * (decay_per_hop ** (hop + 1))
                if spread > activations.get(neighbor.id, 0):
                    next_frontier[neighbor.id] = spread
                    activations[neighbor.id] = spread
        frontier = set(next_frontier.keys())
        if not frontier:
            break

    return activations
