"""Output formatting helpers for the OpenMem MCP server."""

from __future__ import annotations

from openmem.models import Memory, ScoredMemory


def format_memory(mem: Memory) -> str:
    """Format a single Memory as structured plain text."""
    lines = [
        f"[{mem.id}]",
        f"  type: {mem.type}",
        f"  status: {mem.status}",
        f"  text: {mem.text}",
    ]
    if mem.gist:
        lines.append(f"  gist: {mem.gist}")
    if mem.entities:
        lines.append(f"  entities: {', '.join(mem.entities)}")
    lines.append(f"  strength: {mem.strength:.2f}")
    lines.append(f"  confidence: {mem.confidence:.2f}")
    lines.append(f"  access_count: {mem.access_count}")
    return "\n".join(lines)


def format_scored_memory(sm: ScoredMemory) -> str:
    """Format a ScoredMemory with its score and components."""
    lines = [
        f"[{sm.memory.id}]",
        f"  score: {sm.score:.4f}",
        f"  type: {sm.memory.type}",
        f"  status: {sm.memory.status}",
        f"  text: {sm.memory.text}",
    ]
    if sm.memory.gist:
        lines.append(f"  gist: {sm.memory.gist}")
    if sm.memory.entities:
        lines.append(f"  entities: {', '.join(sm.memory.entities)}")
    lines.append(f"  strength: {sm.memory.strength:.2f}")
    lines.append(f"  confidence: {sm.memory.confidence:.2f}")
    if sm.components:
        parts = ", ".join(f"{k}={v:.3f}" for k, v in sm.components.items())
        lines.append(f"  components: {parts}")
    return "\n".join(lines)


def format_recall_results(results: list[ScoredMemory]) -> str:
    """Format a list of recall results."""
    if not results:
        return "No memories found."
    sections = [f"Found {len(results)} memories:\n"]
    for i, sm in enumerate(results, 1):
        sections.append(f"--- Result {i} ---")
        sections.append(format_scored_memory(sm))
        sections.append("")
    return "\n".join(sections)


def format_stats(stats: dict) -> str:
    """Format memory store statistics."""
    return "\n".join([
        "Memory Store Statistics:",
        f"  Total memories: {stats['memory_count']}",
        f"  Active: {stats['active_count']}",
        f"  Superseded: {stats['superseded_count']}",
        f"  Contradicted: {stats['contradicted_count']}",
        f"  Total edges: {stats['edge_count']}",
        f"  Average strength: {stats['avg_strength']:.2f}",
    ])
