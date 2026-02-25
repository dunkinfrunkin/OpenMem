from __future__ import annotations

import shutil
import tempfile

from .base import AdapterCapabilities, RecallResult


class Mem0Adapter:
    """Mem0 memory layer (requires LLM for fact extraction + vector embeddings)."""

    name = "Mem0"
    capabilities = AdapterCapabilities(
        supports_graph=False,
        supports_contradiction=False,
        supports_supersession=False,
        supports_temporal_decay=False,
        supports_reinforcement=False,
        supports_metadata=True,
    )

    def __init__(self) -> None:
        self._memory = None
        self._tmpdir = None

    def setup(self) -> None:
        from mem0 import Memory

        self._tmpdir = tempfile.mkdtemp(prefix="mem0_bench_")
        config = {
            "embedder": {
                "provider": "huggingface",
                "config": {"model": "sentence-transformers/all-MiniLM-L6-v2"},
            },
            "vector_store": {
                "provider": "qdrant",
                "config": {
                    "collection_name": "benchmark",
                    "embedding_model_dims": 384,
                    "path": self._tmpdir,
                },
            },
            "version": "v1.1",
        }
        self._memory = Memory.from_config(config)

    def teardown(self) -> None:
        self._memory = None
        if self._tmpdir:
            shutil.rmtree(self._tmpdir, ignore_errors=True)
            self._tmpdir = None

    def store(self, id: str, text: str, metadata: dict | None = None) -> None:
        # mem0.add() uses an LLM to extract facts. We use it as-is to represent
        # mem0's actual behavior. The LLM extracts and reformulates memories.
        self._memory.add(text, user_id="bench", metadata=metadata or {})

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
        results = self._memory.search(query, user_id="bench", limit=top_k)
        output = []
        if isinstance(results, dict) and "results" in results:
            entries = results["results"]
        elif isinstance(results, list):
            entries = results
        else:
            return []

        for i, entry in enumerate(entries):
            score = entry.get("score", 1.0 - i * 0.1) if isinstance(entry, dict) else 0.5
            mem_id = entry.get("id", f"mem0_{i}") if isinstance(entry, dict) else f"mem0_{i}"
            output.append(RecallResult(id=str(mem_id), score=float(score)))
        return output[:top_k]
