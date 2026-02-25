from __future__ import annotations

from .base import AdapterCapabilities, RecallResult


class BM25OnlyAdapter:
    """OpenMem with spreading activation disabled (max_hops=0)."""

    name = "BM25-Only"
    capabilities = AdapterCapabilities(
        supports_graph=False,
        supports_contradiction=False,
        supports_supersession=False,
        supports_temporal_decay=True,
        supports_reinforcement=True,
        supports_metadata=True,
    )

    def __init__(self) -> None:
        self._engine = None
        self._id_map: dict[str, str] = {}

    def setup(self) -> None:
        from openmem.engine import MemoryEngine

        self._engine = MemoryEngine(db_path=":memory:", max_hops=0)
        self._id_map = {}

    def teardown(self) -> None:
        self._engine = None
        self._id_map = {}

    def store(self, id: str, text: str, metadata: dict | None = None) -> None:
        meta = metadata or {}
        mem = self._engine.add(
            text=text,
            type=meta.get("type", "fact"),
            entities=meta.get("entities"),
            confidence=meta.get("confidence", 1.0),
            gist=meta.get("gist"),
        )
        self._id_map[id] = mem.id

    def link(self, source_id: str, target_id: str, rel_type: str = "mentions",
             weight: float = 0.5) -> None:
        pass

    def supersede(self, old_id: str, new_id: str) -> None:
        pass

    def contradict(self, id_a: str, id_b: str) -> None:
        pass

    def reinforce(self, memory_id: str) -> None:
        self._engine.reinforce(self._id_map[memory_id])

    def recall(self, query: str, top_k: int = 10) -> list[RecallResult]:
        results = self._engine.recall(query, top_k=top_k, token_budget=50000)
        reverse_map = {v: k for k, v in self._id_map.items()}
        return [
            RecallResult(id=reverse_map.get(sm.memory.id, sm.memory.id), score=sm.score)
            for sm in results
        ]
