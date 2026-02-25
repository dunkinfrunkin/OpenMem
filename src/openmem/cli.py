"""OpenMem CLI — install and manage the Claude Code MCP integration."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_DB = os.path.join(Path.home(), ".openmem", "memories.db")
SETTINGS_PATH = os.path.join(Path.home(), ".claude", "settings.json")


def _claude_env() -> dict[str, str]:
    """Return a clean env that allows calling claude from within Claude Code."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def _get_db_path() -> str:
    return os.environ.get("OPENMEM_DB", DEFAULT_DB)


def _find_project_root() -> str | None:
    """If running from a local source tree, return the project root path."""
    pkg_dir = Path(__file__).resolve().parent  # src/openmem/
    for parent in pkg_dir.parents:
        if (parent / "pyproject.toml").exists():
            return str(parent)
    return None


def _install_cli_tool() -> None:
    """Persistently install the openmem-engine CLI via uv tool or pipx."""
    project_root = _find_project_root()

    uv = shutil.which("uv")
    if uv:
        if project_root:
            cmd = [uv, "tool", "install", "--force", "--editable", project_root]
        else:
            if shutil.which("openmem-engine"):
                return  # already available
            cmd = [uv, "tool", "install", "openmem-engine"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return

    pipx = shutil.which("pipx")
    if pipx:
        if project_root:
            cmd = [pipx, "install", "--force", "--editable", project_root]
        else:
            if shutil.which("openmem-engine"):
                return
            cmd = [pipx, "install", "openmem-engine"]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            return

    print()
    print("Note: Could not install the openmem-engine CLI globally.")
    print("You can still use it via: uvx openmem-engine <command>")
    print("Or install manually: uv tool install openmem-engine")


def _uninstall_cli_tool() -> None:
    """Remove the persistently installed openmem-engine CLI."""
    uv = shutil.which("uv")
    if uv:
        subprocess.run(
            [uv, "tool", "uninstall", "openmem-engine"],
            capture_output=True,
            text=True,
        )
        return

    pipx = shutil.which("pipx")
    if pipx:
        subprocess.run(
            [pipx, "uninstall", "openmem-engine"],
            capture_output=True,
            text=True,
        )


def _read_settings() -> dict:
    """Read ~/.claude/settings.json, returning empty dict if missing/invalid."""
    if not os.path.exists(SETTINGS_PATH):
        return {}
    try:
        with open(SETTINGS_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def _write_settings(settings: dict) -> None:
    """Write settings back to ~/.claude/settings.json."""
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    with open(SETTINGS_PATH, "w") as f:
        json.dump(settings, f, indent=2)
        f.write("\n")


def _build_hooks_config() -> dict:
    """Build the hooks configuration dict to merge into settings."""
    return {
        "SessionEnd": [
            {
                "hooks": [
                    {
                        "type": "command",
                        "command": "openmem-engine digest",
                        "timeout": 60,
                    }
                ],
                "_openmem": True,
            }
        ],
    }


def _install_hooks() -> None:
    """Add OpenMem hooks to ~/.claude/settings.json.

    Preserves existing hooks and settings. Replaces any existing
    OpenMem hooks (tagged with ``_openmem``) so reinstall is idempotent.
    """
    settings = _read_settings()
    if "hooks" not in settings:
        settings["hooks"] = {}

    hooks = settings["hooks"]
    openmem_hooks = _build_hooks_config()

    for event_name, matcher_groups in openmem_hooks.items():
        if event_name not in hooks:
            hooks[event_name] = []
        # Remove any existing OpenMem hooks for this event
        hooks[event_name] = [
            mg for mg in hooks[event_name] if not mg.get("_openmem")
        ]
        hooks[event_name].extend(matcher_groups)

    _write_settings(settings)


def _uninstall_hooks() -> None:
    """Remove OpenMem hooks from ~/.claude/settings.json."""
    settings = _read_settings()
    hooks = settings.get("hooks")
    if not hooks:
        return

    for event_name in list(hooks.keys()):
        hooks[event_name] = [
            mg for mg in hooks[event_name] if not mg.get("_openmem")
        ]
        if not hooks[event_name]:
            del hooks[event_name]

    if not hooks:
        del settings["hooks"]

    _write_settings(settings)


def install() -> None:
    """Install OpenMem as a Claude Code MCP server with automatic memory hooks."""
    claude = shutil.which("claude")
    if not claude:
        print("Error: 'claude' CLI not found. Install Claude Code first:")
        print("  https://docs.anthropic.com/en/docs/claude-code")
        sys.exit(1)

    # Add the MCP server
    print("Adding OpenMem to Claude Code...")
    project_root = _find_project_root()
    if project_root:
        serve_cmd = ["uv", "run", "--directory", project_root, "openmem-engine", "serve"]
    else:
        serve_cmd = ["uvx", "openmem-engine", "serve"]
    result = subprocess.run(
        [claude, "mcp", "add", "-s", "user", "openmem", "--", *serve_cmd],
        capture_output=True,
        text=True,
        env=_claude_env(),
    )
    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "already exists" in stderr:
            print("OpenMem MCP server is already installed in Claude Code.")
            print("Updating hooks configuration...")
        else:
            print(f"Error: {stderr}")
            sys.exit(1)

    # Persistently install the CLI so `openmem-engine` works without `uvx`
    _install_cli_tool()

    # Install hooks for automatic memory storage
    _install_hooks()

    print("Done! OpenMem is now available in Claude Code.")
    print()
    print("Start a new Claude Code session and Claude will have access to:")
    print("  memory_store, memory_recall, memory_link,")
    print("  memory_reinforce, memory_supersede, memory_contradict,")
    print("  memory_stats")
    print()
    print("Automatic memory storage is enabled:")
    print("  - Stop hook: stores important facts/decisions during sessions")
    print("  - SessionEnd hook: catches anything missed when sessions end")
    print()
    print("Memories are stored in ~/.openmem/memories.db")


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

    _uninstall_hooks()
    _uninstall_cli_tool()
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


def _parse_transcript(transcript_path: str) -> list[dict]:
    """Parse a Claude Code JSONL transcript into a list of messages.

    Returns list of dicts with keys: role (str), content (str).
    Only includes user and assistant messages with text content.
    """
    messages: list[dict] = []
    with open(transcript_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue

            entry_type = entry.get("type")
            msg = entry.get("message", {})
            role = msg.get("role")

            if entry_type not in ("user", "assistant") or not role:
                continue

            content = msg.get("content", "")
            if isinstance(content, str):
                text = content.strip()
            elif isinstance(content, list):
                text_parts = []
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                text = "\n".join(text_parts).strip()
            else:
                continue

            if text:
                messages.append({"role": role, "content": text})

    return messages


def _condense_transcript(messages: list[dict], max_chars: int = 8000) -> str:
    """Build a condensed version of the transcript for LLM extraction."""
    lines = []
    for msg in messages:
        role = "User" if msg["role"] == "user" else "Assistant"
        content = msg["content"]
        if len(content) > 500:
            content = content[:497] + "..."
        lines.append(f"{role}: {content}")

    result = "\n\n".join(lines)
    if len(result) > max_chars:
        result = result[:max_chars] + "\n...(truncated)"
    return result


def _extract_memories_with_claude(messages: list[dict]) -> list[dict]:
    """Use ``claude -p`` to extract structured memories from conversation.

    Returns list of dicts with keys: text, type, entities, confidence, gist.
    Raises RuntimeError if the claude CLI is unavailable or fails.
    """
    claude = shutil.which("claude")
    if not claude:
        raise RuntimeError("claude CLI not found")

    condensed = _condense_transcript(messages)

    prompt = (
        "Analyze this conversation and extract important memories worth "
        "storing long-term.\n\n"
        "For each memory, output a JSON object on its own line with:\n"
        '- "text": the full content of the memory\n'
        '- "type": one of "fact", "decision", "preference", "incident", '
        '"plan", "constraint"\n'
        '- "entities": list of key entities (project names, technologies)\n'
        '- "confidence": float 0.0-1.0\n'
        '- "gist": one-line summary\n\n'
        "Only extract genuinely important information: technical decisions, "
        "user preferences, project facts, bugs and solutions, architecture "
        "choices. Skip trivial exchanges.\n"
        "If there is nothing worth storing, output nothing.\n\n"
        "Output ONLY the JSON objects, one per line. No other text.\n\n"
        "Conversation:\n" + condensed
    )

    result = subprocess.run(
        [claude, "-p", "--no-session-persistence", prompt],
        capture_output=True,
        text=True,
        timeout=60,
        env=_claude_env(),
    )

    if result.returncode != 0:
        raise RuntimeError(f"claude -p failed: {result.stderr}")

    memories: list[dict] = []
    for line in result.stdout.strip().split("\n"):
        line = line.strip()
        if not line:
            continue
        try:
            mem = json.loads(line)
            if "text" in mem and isinstance(mem["text"], str):
                memories.append(
                    {
                        "text": mem["text"],
                        "type": mem.get("type", "fact"),
                        "entities": mem.get("entities", []),
                        "confidence": mem.get("confidence", 1.0),
                        "gist": mem.get("gist"),
                    }
                )
        except json.JSONDecodeError:
            continue

    return memories


_DECISION_KEYWORDS = [
    "decided",
    "chose",
    "choice",
    "we'll use",
    "going with",
    "prefer",
    "preference",
    "the plan is",
    "approach will be",
    "architecture",
    "convention",
    "constraint",
    "requirement",
]


def _extract_memories_simple(messages: list[dict]) -> list[dict]:
    """Fallback extraction using keyword heuristics."""
    memories: list[dict] = []
    for msg in messages:
        if msg["role"] != "assistant":
            continue
        content = msg["content"]
        lower = content.lower()

        if not any(kw in lower for kw in _DECISION_KEYWORDS):
            continue

        text = content[:500].strip()
        if len(content) > 500:
            text += "..."

        memories.append(
            {
                "text": text,
                "type": "fact",
                "entities": [],
                "confidence": 0.7,
                "gist": None,
            }
        )

    return memories[-5:]


def digest() -> None:
    """Digest a Claude Code session transcript and store extracted memories.

    Reads hook event data from stdin (JSON with transcript_path).
    Designed to be called as a SessionEnd hook command.
    """
    try:
        hook_data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, Exception) as e:
        print(f"openmem digest: failed to read hook data: {e}", file=sys.stderr)
        return

    transcript_path = hook_data.get("transcript_path")
    cwd = hook_data.get("cwd", "")
    if not transcript_path:
        print("openmem digest: no transcript_path in hook data", file=sys.stderr)
        return

    if not os.path.exists(transcript_path):
        print(
            f"openmem digest: transcript not found: {transcript_path}",
            file=sys.stderr,
        )
        return

    messages = _parse_transcript(transcript_path)

    if len(messages) < 4:
        return

    try:
        memories = _extract_memories_with_claude(messages)
    except (RuntimeError, subprocess.TimeoutExpired):
        memories = _extract_memories_simple(messages)

    if not memories:
        return

    from openmem import MemoryEngine

    db_path = _get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    engine = MemoryEngine(db_path=db_path)

    stored = 0
    for mem_data in memories:
        try:
            engine.add(
                text=mem_data["text"],
                type=mem_data.get("type", "fact"),
                entities=mem_data.get("entities", []),
                confidence=mem_data.get("confidence", 1.0),
                gist=mem_data.get("gist"),
                source="claude-code",
                project=cwd,
            )
            stored += 1
        except Exception as e:
            print(
                f"openmem digest: failed to store memory: {e}", file=sys.stderr
            )

    if stored:
        print(
            f"openmem digest: stored {stored} memories from session",
            file=sys.stderr,
        )


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
        print("  digest     Extract and store memories from a session transcript")
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
    elif command == "digest":
        digest()
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
