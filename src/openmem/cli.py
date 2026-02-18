"""OpenMem CLI — install and manage the Claude Code MCP integration."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys


def _claude_env() -> dict[str, str]:
    """Return a clean env that allows calling claude from within Claude Code."""
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


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


def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: openmem-engine <command>")
        print()
        print("Commands:")
        print("  install    Add OpenMem to Claude Code")
        print("  uninstall  Remove OpenMem from Claude Code")
        print("  serve      Start the MCP server (used by Claude Code)")
        sys.exit(0)

    command = sys.argv[1]

    if command == "install":
        install()
    elif command == "uninstall":
        uninstall()
    elif command == "serve":
        from openmem.mcp_server import main as serve
        serve()
    else:
        print(f"Unknown command: {command}")
        print("Run 'openmem-engine' with no arguments for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
