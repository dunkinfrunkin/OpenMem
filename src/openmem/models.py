from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field


@dataclass
class Memory:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    type: str = "fact"  # decision | fact | preference | incident | plan | constraint
    text: str = ""
    gist: str | None = None
    entities: list[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    strength: float = 1.0  # 0–1, decays over time, reinforced on access
    confidence: float = 1.0  # 0–1, set at creation
    access_count: int = 0
    last_accessed: float | None = None
    status: str = "active"  # active | superseded | contradicted


@dataclass
class Edge:
    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    source_id: str = ""
    target_id: str = ""
    rel_type: str = "mentions"  # mentions | supports | contradicts | depends_on | same_as
    weight: float = 0.5  # 0–1
    created_at: float = field(default_factory=time.time)


@dataclass
class ScoredMemory:
    memory: Memory
    score: float  # final competition score
    activation: float  # raw activation (seed + spread)
    components: dict = field(default_factory=dict)
    # breakdown: {activation, recency, strength, confidence}
