from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class RecallResult:
    """Normalized result from any adapter's recall method."""

    id: str
    score: float


@dataclass
class AdapterCapabilities:
    """Declares which features an adapter supports."""

    supports_graph: bool = False
    supports_contradiction: bool = False
    supports_supersession: bool = False
    supports_temporal_decay: bool = False
    supports_reinforcement: bool = False
    supports_metadata: bool = False


@runtime_checkable
class MemoryAdapter(Protocol):
    """Common interface all memory systems must implement."""

    name: str
    capabilities: AdapterCapabilities

    def setup(self) -> None: ...
    def teardown(self) -> None: ...
    def store(self, id: str, text: str, metadata: dict | None = None) -> None: ...
    def link(
        self,
        source_id: str,
        target_id: str,
        rel_type: str = "mentions",
        weight: float = 0.5,
    ) -> None: ...
    def supersede(self, old_id: str, new_id: str) -> None: ...
    def contradict(self, id_a: str, id_b: str) -> None: ...
    def reinforce(self, memory_id: str) -> None: ...
    def recall(self, query: str, top_k: int = 10) -> list[RecallResult]: ...
