---
sidebar_position: 4
title: Web UI
---

# Web UI

Browse, search, and inspect your memory store in a local web interface.

```bash
openmem-engine ui
```

Opens `http://localhost:3333` in your browser.

## Usage

```bash
# Default port
openmem-engine ui

# Custom port
openmem-engine ui --port 8080
```

The UI reads from the same database as the CLI and MCP server (`~/.openmem/memories.db` by default, or `OPENMEM_DB`).

## Features

- **Stats bar** — total memories, active count, average strength, edge count
- **Search** — live BM25 search with scored results (same pipeline as `engine.recall()`)
- **Filters** — filter by memory type (`fact`, `decision`, etc.) and status (`active`, `superseded`, `contradicted`)
- **Sortable table** — sort by created date, type, status, strength, or confidence
- **Detail panel** — click any row to see full content, entities, edges, timestamps, and score breakdowns
- **Reinforce / Delete** — boost a memory's strength or remove it directly from the UI

## API endpoints

The UI serves a JSON API on the same port. Useful for scripting or debugging.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Memory store statistics |
| `/api/memories` | GET | List all memories |
| `/api/memories/<id>` | GET | Single memory with edges |
| `/api/search?q=...` | GET | BM25 search with scored results |
| `/api/memories/<id>/reinforce` | POST | Reinforce a memory |
| `/api/memories/<id>` | DELETE | Delete a memory |

### Query parameters for `/api/memories`

| Param | Description |
|-------|-------------|
| `type` | Filter by memory type (e.g. `?type=decision`) |
| `status` | Filter by status (e.g. `?status=active`) |
| `sort` | Sort field: `created_at`, `updated_at`, `strength`, `confidence`, `access_count`, `type`, `status` |
| `order` | Sort direction: `asc` or `desc` (default `desc`) |

### Examples

```bash
# Get stats
curl http://localhost:3333/api/stats

# Search memories
curl "http://localhost:3333/api/search?q=authentication"

# List active decisions
curl "http://localhost:3333/api/memories?type=decision&status=active"

# Reinforce a memory
curl -X POST http://localhost:3333/api/memories/<id>/reinforce
```

## Architecture

The UI is a lightweight Flask app serving vanilla HTML/CSS/JS — no build step, no npm, no frameworks. It wraps the same `MemoryEngine` and `SQLiteStore` used by the CLI and MCP server.

```
openmem-engine ui
  → Flask dev server on localhost:3333
  → Static files from src/openmem/ui/static/
  → JSON API wraps MemoryEngine methods
  → Opens browser automatically
```

:::note
The UI runs Flask's development server. It's intended for local use — not production deployment.
:::
