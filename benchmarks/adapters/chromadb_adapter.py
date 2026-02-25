from __future__ import annotations

from .base import AdapterCapabilities, RecallResult


class ChromaDBAdapter:
    name = "ChromaDB (Vector)"
    capabilities = AdapterCapabilities(
        supports_graph=False,
        supports_contradiction=False,
        supports_supersession=False,
        supports_temporal_decay=False,
        supports_reinforcement=False,
        supports_metadata=True,
    )

    def __init__(self) -> None:
        self._client = None
        self._collection = None

    def setup(self) -> None:
        import chromadb

        self._client = chromadb.Client()
        self._collection = self._client.create_collection(
            name="benchmark",
            metadata={"hnsw:space": "cosine"},
        )

    def teardown(self) -> None:
        if self._client:
            try:
                self._client.delete_collection("benchmark")
            except Exception:
                pass
            self._client = None
            self._collection = None

    def store(self, id: str, text: str, metadata: dict | None = None) -> None:
        self._collection.add(
            ids=[id],
            documents=[text],
            metadatas=[metadata] if metadata else None,
        )

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
        results = self._collection.query(
            query_texts=[query],
            n_results=top_k,
        )
        output = []
        if results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            distances = results["distances"][0] if results.get("distances") else [0] * len(ids)
            for id_, dist in zip(ids, distances):
                score = max(0.0, 1.0 - dist)
                output.append(RecallResult(id=id_, score=score))
        return output
