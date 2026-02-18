# OpenMem

Deterministic memory engine for AI agents. Retrieves context via BM25 lexical search, graph-based spreading activation, and human-inspired competition scoring. SQLite-backed, zero dependencies.

## How it works

```
Query → FTS5/BM25 (lexical trigger)
      → Seed Activation
      → Spreading Activation (graph edges, max 2 hops)
      → Recency + Strength + Confidence weighting
      → Competition (score-based ranking)
      → Context Pack (token-budgeted output)
```

No vectors, no embeddings, no LLM in the retrieval loop. The LLM is the consumer, not the retriever.

## Install

```bash
pip install openmem
```

Or from source:

```bash
git clone https://github.com/yourorg/openmem.git
cd openmem
pip install -e ".[dev]"
```

## Quick start

```python
from openmem import MemoryEngine

engine = MemoryEngine()  # in-memory, or MemoryEngine("memories.db") for persistence

# Store memories
m1 = engine.add("We chose SQLite over Postgres for simplicity", type="decision", entities=["SQLite", "Postgres"])
m2 = engine.add("Postgres has better concurrent write support", type="fact", entities=["Postgres"])

# Link related memories
engine.link(m1.id, m2.id, "supports")

# Recall
results = engine.recall("Why did we pick SQLite?")
for r in results:
    print(f"{r.score:.3f} | {r.memory.text}")
# 0.800 | We chose SQLite over Postgres for simplicity
# 0.500 | Postgres has better concurrent write support
```

## Claude Code plugin

Install OpenMem as a Claude Code plugin to get persistent memory across sessions:

```bash
pip install openmem "mcp>=1.0"
claude plugin install --path ./plugin
```

Once installed, you get three slash commands:

| Command | Description |
|---------|-------------|
| `/openmem:recall` | Recall memories relevant to the current conversation |
| `/openmem:store` | Store key facts, decisions, and preferences from the conversation |
| `/openmem:status` | Show memory store statistics |

The plugin also registers an MCP server with 7 tools (`memory_store`, `memory_recall`, `memory_link`, `memory_reinforce`, `memory_supersede`, `memory_contradict`, `memory_stats`) that Claude can call automatically.

Memories persist in `~/.openmem/memories.db` by default (override with the `OPENMEM_DB` env var).

## Usage with an LLM agent

```python
engine = MemoryEngine("project.db")

# Agent stores what it learns
engine.add("User prefers TypeScript over JavaScript", type="preference", entities=["TypeScript", "JavaScript"])
engine.add("Auth system uses JWT with 24h expiry", type="decision", entities=["JWT", "auth"])
engine.add("The /api/users endpoint returns 500 on empty payload", type="incident", entities=["/api/users"])

# Before each LLM call, recall relevant context
results = engine.recall("set up authentication", top_k=5, token_budget=2000)
context = "\n".join(r.memory.text for r in results)

prompt = f"""Relevant context from previous work:
{context}

User request: {user_message}"""
```

## API

### `MemoryEngine(db_path=":memory:", **config)`

| Method | Description |
|--------|-------------|
| `add(text, type="fact", entities=None, confidence=1.0, gist=None)` | Store a memory |
| `link(source_id, target_id, rel_type, weight=0.5)` | Create an edge between memories |
| `recall(query, top_k=5, token_budget=2000)` | Retrieve relevant memories |
| `reinforce(memory_id)` | Boost a memory's strength |
| `supersede(old_id, new_id)` | Mark a memory as outdated |
| `contradict(id_a, id_b)` | Flag two memories as contradicting |
| `decay_all()` | Run decay pass over all memories |
| `stats()` | Get summary statistics |

### Memory types

`fact` · `decision` · `preference` · `incident` · `plan` · `constraint`

### Edge types

`mentions` · `supports` · `contradicts` · `depends_on` · `same_as`

## Retrieval model

**Recency** — Exponential decay with ~14-day half-life. Recently accessed memories surface first.

**Strength** — Reinforced on access, decays naturally over time. Frequently recalled memories persist.

**Spreading activation** — Memories linked by edges activate their neighbors. A query hitting one memory pulls in related context up to 2 hops away.

**Competition** — Final score combines activation (50%), recency (20%), strength (20%), and confidence (10%). Superseded memories are penalized 50%, contradicted ones 70%.

**Conflict resolution** — When two contradicting memories both activate, the weaker one (by strength × confidence × recency) gets demoted.

## Tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
