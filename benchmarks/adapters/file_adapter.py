from __future__ import annotations

import re

from .base import AdapterCapabilities, RecallResult


class FileAdapter:
    """Simulates CLAUDE.md-style memory: flat text + naive keyword search."""

    name = "File-Based"
    capabilities = AdapterCapabilities(
        supports_graph=False,
        supports_contradiction=False,
        supports_supersession=False,
        supports_temporal_decay=False,
        supports_reinforcement=False,
        supports_metadata=False,
    )

    def __init__(self) -> None:
        self._memories: dict[str, str] = {}

    def setup(self) -> None:
        self._memories = {}

    def teardown(self) -> None:
        self._memories = {}

    def store(self, id: str, text: str, metadata: dict | None = None) -> None:
        self._memories[id] = text

    def link(self, source_id: str, target_id: str, rel_type: str = "mentions",
             weight: float = 0.5) -> None:
        pass

    def supersede(self, old_id: str, new_id: str) -> None:
        pass

    def contradict(self, id_a: str, id_b: str) -> None:
        pass

    def reinforce(self, memory_id: str) -> None:
        pass

    def recall(self, query: str, top_k: int = 10) -> list[RecallResult]:
        query_tokens = set(re.findall(r"\w+", query.lower()))
        if not query_tokens:
            return []

        scored = []
        for id_, text in self._memories.items():
            text_tokens = re.findall(r"\w+", text.lower())
            if not text_tokens:
                continue
            hits = sum(1 for t in text_tokens if t in query_tokens)
            score = hits / len(text_tokens) if text_tokens else 0.0
            if score > 0:
                scored.append(RecallResult(id=id_, score=score))

        scored.sort(key=lambda r: r.score, reverse=True)
        return scored[:top_k]
