from __future__ import annotations

import math
import time

from .activation import spread_activation
from .conflict import detect_and_resolve_conflicts
from .models import Edge, Memory, ScoredMemory
from .scoring import compete
from .store import SQLiteStore

# Rough token estimate: ~4 chars per token
CHARS_PER_TOKEN = 4


class MemoryEngine:
    """Main entry point for the cognitive memory engine."""

    def __init__(
        self,
        db_path: str = ":memory:",
        max_hops: int = 2,
        decay_per_hop: float = 0.5,
        weights: dict[str, float] | None = None,
    ):
        self.store = SQLiteStore(db_path)
        self.max_hops = max_hops
        self.decay_per_hop = decay_per_hop
        self.weights = weights

    def add(
        self,
        text: str,
        type: str = "fact",
        entities: list[str] | None = None,
        confidence: float = 1.0,
        gist: str | None = None,
    ) -> Memory:
        """Add a new memory."""
        now = time.time()
        mem = Memory(
            type=type,
            text=text,
            gist=gist,
            entities=entities or [],
            created_at=now,
            updated_at=now,
            confidence=confidence,
        )
        return self.store.add_memory(mem)

    def link(
        self,
        source_id: str,
        target_id: str,
        rel_type: str = "mentions",
        weight: float = 0.5,
    ) -> Edge:
        """Create an edge between two memories."""
        edge = Edge(
            source_id=source_id,
            target_id=target_id,
            rel_type=rel_type,
            weight=weight,
        )
        return self.store.add_edge(edge)

    def recall(
        self,
        query: str,
        top_k: int = 5,
        token_budget: int = 2000,
    ) -> list[ScoredMemory]:
        """Recall memories relevant to the query.

        Pipeline: FTS5/BM25 → seed activation → spreading activation →
        scoring competition → conflict resolution → token-budgeted output.
        """
        now = time.time()

        # Step 1: Lexical trigger via BM25
        bm25_hits = self.store.search_bm25(query, limit=top_k * 4)
        if not bm25_hits:
            return []

        # Normalize BM25 scores to [0, 1] for seeding
        max_score = max(s for _, s in bm25_hits) if bm25_hits else 1.0
        if max_score == 0:
            max_score = 1.0
        seed_activations = {mid: score / max_score for mid, score in bm25_hits}

        # Step 2: Spreading activation
        activations = spread_activation(
            seed_activations,
            self.store,
            max_hops=self.max_hops,
            decay_per_hop=self.decay_per_hop,
        )

        # Step 3: Load all activated memories
        memories = {}
        for mid in activations:
            mem = self.store.get_memory(mid)
            if mem:
                memories[mid] = mem

        # Step 4: Competition scoring
        scored = compete(activations, memories, weights=self.weights, now=now)

        # Step 5: Conflict resolution
        scored = detect_and_resolve_conflicts(scored, self.store, now=now)

        # Step 6: Token-budget packing
        char_budget = token_budget * CHARS_PER_TOKEN
        packed: list[ScoredMemory] = []
        used_chars = 0
        for sm in scored:
            text_len = len(sm.memory.text)
            if used_chars + text_len > char_budget and packed:
                break
            packed.append(sm)
            used_chars += text_len
            if len(packed) >= top_k:
                break

        # Step 7: Update access stats for returned memories
        for sm in packed:
            self.store.update_access(sm.memory.id)

        return packed

    def reinforce(self, memory_id: str) -> None:
        """Explicitly boost a memory's strength."""
        mem = self.store.get_memory(memory_id)
        if not mem:
            return
        mem.strength = min(1.0, mem.strength + 0.1)
        mem.access_count += 1
        mem.last_accessed = time.time()
        self.store.update_memory(mem)

    def supersede(self, old_id: str, new_id: str) -> None:
        """Mark old memory as superseded and link to the new one."""
        old = self.store.get_memory(old_id)
        if old:
            old.status = "superseded"
            self.store.update_memory(old)
        self.link(new_id, old_id, rel_type="same_as", weight=0.3)

    def contradict(self, id_a: str, id_b: str) -> None:
        """Mark two memories as contradicting each other."""
        self.link(id_a, id_b, rel_type="contradicts", weight=0.8)

    def decay_all(self) -> None:
        """Run a decay pass over all memories, reducing strength by natural decay."""
        now = time.time()
        for mem in self.store.all_memories():
            days = (now - mem.updated_at) / 86400.0
            if days < 0.01:
                continue
            decay = math.exp(-0.01 * days)
            mem.strength = max(0.0, min(1.0, mem.strength * decay))
            self.store.update_memory(mem)

    def stats(self) -> dict:
        """Return summary statistics about the memory store."""
        memories = self.store.all_memories()
        edges = []
        for m in memories:
            edges.extend(self.store.get_edges(m.id))
        # Deduplicate edges (they appear for both endpoints)
        unique_edges = {e.id: e for e in edges}

        strengths = [m.strength for m in memories]
        return {
            "memory_count": len(memories),
            "edge_count": len(unique_edges),
            "avg_strength": sum(strengths) / len(strengths) if strengths else 0,
            "active_count": sum(1 for m in memories if m.status == "active"),
            "superseded_count": sum(1 for m in memories if m.status == "superseded"),
            "contradicted_count": sum(1 for m in memories if m.status == "contradicted"),
        }
