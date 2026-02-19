---
sidebar_position: 1
title: Introduction
slug: /
---

# OpenMem

Deterministic memory engine for AI agents. Retrieves context via BM25 lexical search, graph-based spreading activation, and human-inspired competition scoring. SQLite-backed, zero dependencies.

```mermaid
flowchart LR
    Q[Query] --> BM25[FTS5 / BM25]
    BM25 --> Seed[Seed Activation]
    Seed --> Spread[Spreading Activation]
    Spread --> Score[Competition Scoring]
    Score --> Conflict[Conflict Resolution]
    Conflict --> Pack[Token Packing]
    Pack --> Out[Results]
```

No vectors, no embeddings, no LLM in the retrieval loop. The LLM is the consumer, not the retriever.

## Why OpenMem?

| | |
|---|---|
| **Deterministic** | Same input, same output. No stochastic embedding drift. |
| **Zero dependencies** | Pure Python + SQLite. Nothing to install, nothing to break. |
| **Human-inspired** | Memories decay, get reinforced, compete, and conflict — just like human recall. |
| **Token-budgeted** | Retrieval respects a token budget so you never blow your context window. |

## Install

```bash
pip install openmem-engine
```

Or add to [Claude Code](./claude-code) for persistent memory across coding sessions:

```bash
uvx openmem-engine install
```

Browse your memories in the [Web UI](./web-ui):

```bash
openmem-engine ui
```

## Quick example

```python
from openmem import MemoryEngine

engine = MemoryEngine()

m1 = engine.add("We chose SQLite for simplicity", type="decision", entities=["SQLite"])
m2 = engine.add("Postgres has better concurrent writes", type="fact", entities=["Postgres"])
engine.link(m1.id, m2.id, "supports")

results = engine.recall("Why did we pick SQLite?")
for r in results:
    print(f"{r.score:.3f} | {r.memory.text}")
```
