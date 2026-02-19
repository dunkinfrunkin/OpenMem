"""OpenMem CLI — install and manage the Claude Code MCP integration."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_DB = os.path.join(Path.home(), ".openmem", "memories.db")


def _claude_env() -> dict[str, str]:
    """Return a clean env that allows calling claude from within Claude Code."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def _get_db_path() -> str:
    return os.environ.get("OPENMEM_DB", DEFAULT_DB)


def install() -> None:
    """Install OpenMem as a Claude Code MCP server."""
    claude = shutil.which("claude")
    if not claude:
        print("Error: 'claude' CLI not found. Install Claude Code first:")
        print("  https://docs.anthropic.com/en/docs/claude-code")
        sys.exit(1)

    # Add the MCP server
    print("Adding OpenMem to Claude Code...")
    result = subprocess.run(
        [claude, "mcp", "add", "-s", "user", "openmem", "--", "uvx", "openmem-engine", "serve"],
        capture_output=True,
        text=True,
        env=_claude_env(),
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "already exists" in stderr:
            print("OpenMem is already installed in Claude Code.")
            print("To reinstall, first run: uvx openmem-engine uninstall")
            return
        print(f"Error: {stderr}")
        sys.exit(1)

    print("Done! OpenMem is now available in Claude Code.")
    print()
    print("Start a new Claude Code session and Claude will have access to:")
    print("  memory_store, memory_recall, memory_link,")
    print("  memory_reinforce, memory_supersede, memory_contradict,")
    print("  memory_stats")
    print()
    print(f"Memories are stored in ~/.openmem/memories.db")


def uninstall() -> None:
    """Remove OpenMem from Claude Code."""
    claude = shutil.which("claude")
    if not claude:
        print("Error: 'claude' CLI not found.")
        sys.exit(1)

    print("Removing OpenMem from Claude Code...")
    result = subprocess.run(
        [claude, "mcp", "remove", "-s", "user", "openmem"],
        capture_output=True,
        text=True,
        env=_claude_env(),
    )
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}")
        sys.exit(1)

    print("Done. OpenMem has been removed from Claude Code.")


def status() -> None:
    """Show memory store status and statistics."""
    from openmem import MemoryEngine

    db_path = _get_db_path()
    if not os.path.exists(db_path):
        print(f"No memory store found at {db_path}")
        print("Store memories via Claude Code or the Python API to get started.")
        return

    engine = MemoryEngine(db_path=db_path)
    stats = engine.stats()

    print(f"Database: {db_path}")
    size_kb = os.path.getsize(db_path) / 1024
    if size_kb < 1024:
        print(f"Size:     {size_kb:.0f} KB")
    else:
        print(f"Size:     {size_kb / 1024:.1f} MB")
    print()
    print(f"Memories: {stats['memory_count']}")
    print(f"  Active:       {stats['active_count']}")
    print(f"  Superseded:   {stats['superseded_count']}")
    print(f"  Contradicted: {stats['contradicted_count']}")
    print(f"Edges:    {stats['edge_count']}")
    print(f"Avg strength: {stats['avg_strength']:.2f}")


def list_memories() -> None:
    """List all memories in the store."""
    from datetime import datetime

    from openmem import MemoryEngine

    db_path = _get_db_path()
    if not os.path.exists(db_path):
        print(f"No memory store found at {db_path}")
        return

    engine = MemoryEngine(db_path=db_path)
    memories = engine.store.all_memories()

    if not memories:
        print("No memories stored yet.")
        return

    # Parse optional flags
    show_all = "--all" in sys.argv
    limit = 20
    for i, arg in enumerate(sys.argv):
        if arg in ("-n", "--limit") and i + 1 < len(sys.argv):
            limit = int(sys.argv[i + 1])

    # Sort by creation time, newest first
    memories.sort(key=lambda m: m.created_at, reverse=True)

    if not show_all:
        total = len(memories)
        memories = memories[:limit]

    for mem in memories:
        created = datetime.fromtimestamp(mem.created_at).strftime("%Y-%m-%d %H:%M")
        text = mem.text if len(mem.text) <= 80 else mem.text[:77] + "..."
        status_tag = "" if mem.status == "active" else f" [{mem.status}]"
        print(f"  {mem.id[:8]}  {created}  ({mem.type}){status_tag}  {text}")

    if not show_all and total > limit:
        print(f"\n  ... and {total - limit} more. Use --all to see everything.")

    print(f"\n{total if not show_all else len(memories)} memories total.")


def get_memory() -> None:
    """Get full details of a memory by ID (or prefix)."""
    from datetime import datetime

    from openmem import MemoryEngine

    memory_id = sys.argv[2] if len(sys.argv) > 2 else None
    if not memory_id:
        print("Usage: openmem-engine get <memory_id>")
        print("  Accepts full IDs or short prefixes (e.g. e89f139b)")
        sys.exit(1)

    db_path = _get_db_path()
    if not os.path.exists(db_path):
        print(f"No memory store found at {db_path}")
        return

    engine = MemoryEngine(db_path=db_path)

    # Try exact match first, then prefix match
    mem = engine.store.get_memory(memory_id)
    if not mem:
        for m in engine.store.all_memories():
            if m.id.startswith(memory_id):
                mem = m
                break

    if not mem:
        print(f"Memory not found: {memory_id}")
        sys.exit(1)

    created = datetime.fromtimestamp(mem.created_at).strftime("%Y-%m-%d %H:%M:%S")
    updated = datetime.fromtimestamp(mem.updated_at).strftime("%Y-%m-%d %H:%M:%S")
    accessed = datetime.fromtimestamp(mem.last_accessed).strftime("%Y-%m-%d %H:%M:%S") if mem.last_accessed else "never"

    print(f"ID:           {mem.id}")
    print(f"Type:         {mem.type}")
    print(f"Status:       {mem.status}")
    print(f"Strength:     {mem.strength:.2f}")
    print(f"Confidence:   {mem.confidence:.2f}")
    print(f"Access count: {mem.access_count}")
    print(f"Created:      {created}")
    print(f"Updated:      {updated}")
    print(f"Last accessed: {accessed}")
    if mem.gist:
        print(f"Gist:         {mem.gist}")
    if mem.entities:
        print(f"Entities:     {', '.join(mem.entities)}")
    print()
    print(f"Content:\n  {mem.text}")

    # Show edges
    edges = engine.store.get_edges(mem.id)
    if edges:
        # Deduplicate (edges appear from both sides)
        seen = set()
        print(f"\nEdges:")
        for e in edges:
            if e.id in seen:
                continue
            seen.add(e.id)
            other_id = e.target_id if e.source_id == mem.id else e.source_id
            direction = "->" if e.source_id == mem.id else "<-"
            print(f"  {direction} {other_id[:8]}  ({e.rel_type}, w={e.weight})")


def ui() -> None:
    """Launch the web UI for browsing memories."""
    import webbrowser

    from openmem.ui.app import create_app

    port = 3333
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    app = create_app()
    print(f"Starting OpenMem UI at http://localhost:{port}")
    webbrowser.open(f"http://localhost:{port}")
    app.run(host="127.0.0.1", port=port)


def search() -> None:
    """Search memories by query."""
    from openmem import MemoryEngine
    from openmem._formatting import format_scored_memory

    query = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else None
    if not query:
        print("Usage: openmem-engine search <query>")
        sys.exit(1)

    db_path = _get_db_path()
    if not os.path.exists(db_path):
        print(f"No memory store found at {db_path}")
        return

    engine = MemoryEngine(db_path=db_path)
    results = engine.recall(query, top_k=10, token_budget=4000)

    if not results:
        print(f'No memories found for "{query}"')
        return

    print(f'Found {len(results)} memories for "{query}":\n')
    for i, sm in enumerate(results, 1):
        print(f"--- {i} ---")
        print(format_scored_memory(sm))
        print()


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: openmem-engine <command>")
        print()
        print("Commands:")
        print("  install    Add OpenMem to Claude Code")
        print("  uninstall  Remove OpenMem from Claude Code")
        print("  status     Show memory store statistics")
        print("  list       List stored memories")
        print("  get        Get full details of a memory by ID")
        print("  search     Search memories by query")
        print("  ui         Launch web UI for browsing memories")
        print("  serve      Start the MCP server (used by Claude Code)")
        sys.exit(0)

    command = sys.argv[1]

    if command == "install":
        install()
    elif command == "uninstall":
        uninstall()
    elif command == "status":
        status()
    elif command == "list":
        list_memories()
    elif command == "get":
        get_memory()
    elif command == "search":
        search()
    elif command == "ui":
        ui()
    elif command == "serve":
        from openmem.mcp_server import main as serve
        serve()
    else:
        print(f"Unknown command: {command}")
        print("Run 'openmem-engine' with no arguments for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
