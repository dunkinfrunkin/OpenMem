---
sidebar_position: 3
title: Claude Code
---

# Claude Code

Add persistent memory to Claude Code with a single command.

```mermaid
flowchart LR
    CC[Claude Code] -->|MCP tools| Server[openmem-server]
    Server --> DB[(~/.openmem/memories.db)]
```

## Installation

```bash
uvx openmem-engine install
```

That's it. Restart Claude Code and the 7 memory tools are available immediately.

:::tip
`uvx` runs the package in an isolated environment — no need to install anything globally. It comes with [uv](https://docs.astral.sh/uv/).
:::

### Uninstall

```bash
uvx openmem-engine uninstall
```

## MCP tools

Once added, Claude has 7 memory tools it can call automatically:

| Tool | Description |
|------|-------------|
| `memory_store` | Store a new memory with type, entities, confidence, and gist |
| `memory_recall` | Recall memories via BM25 search + spreading activation + competition |
| `memory_link` | Create a relationship between two memories |
| `memory_reinforce` | Boost a memory's strength when it proves useful |
| `memory_supersede` | Mark an old memory as replaced by a newer one |
| `memory_contradict` | Flag two memories as contradicting each other |
| `memory_stats` | Get summary statistics about the memory store |

### `memory_store`

```
text: string        — The content to store
type: string        — fact | decision | preference | incident | plan | constraint
entities: string[]  — Key entities (project names, people, technologies)
confidence: float   — How certain (0.0–1.0, default 1.0)
gist: string        — Optional one-line summary
```

### `memory_recall`

```
query: string        — What you want to remember
top_k: int           — Max results (default 5)
token_budget: int    — Approximate token budget (default 2000)
```

### `memory_link`

```
source_id: string    — Source memory ID
target_id: string    — Target memory ID
rel_type: string     — mentions | supports | contradicts | depends_on | same_as
weight: float        — Edge weight 0.0–1.0 (default 0.5)
```

### `memory_reinforce`

```
memory_id: string    — ID of the memory to boost
```

### `memory_supersede`

```
old_id: string       — ID of the outdated memory
new_id: string       — ID of the replacement memory
```

### `memory_contradict`

```
id_a: string         — First memory ID
id_b: string         — Second memory ID
```

### `memory_stats`

No parameters. Returns counts and average strength.

## Configuration

### Database location

By default, memories are stored in `~/.openmem/memories.db`. Override with the `OPENMEM_DB` environment variable:

```bash
claude mcp add openmem -e OPENMEM_DB=/path/to/custom/memories.db -- uvx openmem-engine serve
```

### Startup behavior

The MCP server runs `decay_all()` once on startup, so stale memories naturally lose strength between sessions. No cron jobs needed.

## How it works under the hood

The MCP server wraps the `MemoryEngine` class:

1. **Store** — calls `engine.add()` and returns the memory ID
2. **Recall** — runs the full retrieval pipeline (BM25 → spreading activation → competition → conflict resolution → token packing)
3. **Link/Reinforce/Supersede/Contradict** — graph management operations that improve recall quality over time
4. **Stats** — returns aggregate metrics from the store

All data stays local in your SQLite database. Nothing is sent to external services.

## Verification

After installation, start a new Claude Code session and ask Claude to check the memory store. It should call `memory_stats` and report 0 memories if fresh. Then try asking it to remember something — it will call `memory_store` automatically.
