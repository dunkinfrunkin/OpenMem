"""OpenMem MCP server — persistent memory tools for Claude Code.

Exposes 7 tools via FastMCP (stdio transport):
  memory_store, memory_recall, memory_link,
  memory_reinforce, memory_supersede, memory_contradict,
  memory_stats
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Ensure openmem is importable — handle both installed and dev setups
_repo_root = Path(__file__).resolve().parent.parent.parent
_src_dir = _repo_root / "src"
if _src_dir.is_dir() and str(_src_dir) not in sys.path:
    sys.path.insert(0, str(_src_dir))

from openmem import MemoryEngine  # noqa: E402

from formatting import format_memory, format_recall_results, format_stats  # noqa: E402

# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------

DEFAULT_DB = os.path.join(Path.home(), ".openmem", "memories.db")
db_path = os.environ.get("OPENMEM_DB", DEFAULT_DB)

# Ensure the DB directory exists
os.makedirs(os.path.dirname(db_path), exist_ok=True)

engine = MemoryEngine(db_path=db_path)

# Run decay pass on startup so stale memories lose strength naturally
engine.decay_all()

mcp = FastMCP(
    "openmem",
    description="Persistent cognitive memory for Claude Code",
)

# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------


@mcp.tool()
def memory_store(
    text: str,
    type: str = "fact",
    entities: list[str] | None = None,
    confidence: float = 1.0,
    gist: str | None = None,
) -> str:
    """Store a new memory.

    Args:
        text: The content of the memory to store.
        type: Memory type — one of: fact, decision, preference, incident, plan, constraint.
        entities: Key entities mentioned (project names, people, technologies).
        confidence: How certain this memory is, from 0.0 to 1.0.
        gist: Optional one-line summary for quick retrieval.

    Returns:
        Confirmation with the stored memory's ID and details.
    """
    mem = engine.add(
        text=text,
        type=type,
        entities=entities,
        confidence=confidence,
        gist=gist,
    )
    return f"Stored memory:\n{format_memory(mem)}"


@mcp.tool()
def memory_recall(
    query: str,
    top_k: int = 5,
    token_budget: int = 2000,
) -> str:
    """Recall memories relevant to a query.

    Uses BM25 lexical search, spreading activation through the memory graph,
    competition scoring, and conflict resolution to find the most relevant memories.

    Args:
        query: The search query — what you want to remember.
        top_k: Maximum number of memories to return.
        token_budget: Approximate token budget for returned memories.

    Returns:
        Formatted list of matching memories ranked by relevance.
    """
    results = engine.recall(query=query, top_k=top_k, token_budget=token_budget)
    return format_recall_results(results)


@mcp.tool()
def memory_link(
    source_id: str,
    target_id: str,
    rel_type: str = "mentions",
    weight: float = 0.5,
) -> str:
    """Create a relationship between two memories.

    Links enable spreading activation — related memories boost each other during recall.

    Args:
        source_id: ID of the source memory.
        target_id: ID of the target memory.
        rel_type: Relationship type — one of: mentions, supports, contradicts, depends_on, same_as.
        weight: Edge weight from 0.0 to 1.0, controls activation spread strength.

    Returns:
        Confirmation with the edge details.
    """
    edge = engine.link(
        source_id=source_id,
        target_id=target_id,
        rel_type=rel_type,
        weight=weight,
    )
    return f"Linked memories:\n  edge_id: {edge.id}\n  {source_id} --[{rel_type}, w={weight}]--> {target_id}"


@mcp.tool()
def memory_reinforce(memory_id: str) -> str:
    """Reinforce a memory, boosting its strength.

    Call this when a memory proves useful — it increases strength by 0.1 (up to 1.0)
    and updates access stats. Reinforced memories rank higher in future recalls.

    Args:
        memory_id: ID of the memory to reinforce.

    Returns:
        Confirmation of the reinforcement.
    """
    engine.reinforce(memory_id)
    mem = engine.store.get_memory(memory_id)
    if mem:
        return f"Reinforced memory:\n{format_memory(mem)}"
    return f"Memory {memory_id} not found."


@mcp.tool()
def memory_supersede(old_id: str, new_id: str) -> str:
    """Mark an old memory as superseded by a newer one.

    The old memory receives a 50% score penalty in future recalls.
    A 'same_as' link is created from the new memory to the old one.

    Args:
        old_id: ID of the outdated memory.
        new_id: ID of the replacement memory.

    Returns:
        Confirmation of the supersession.
    """
    engine.supersede(old_id=old_id, new_id=new_id)
    return f"Memory {old_id} superseded by {new_id}."


@mcp.tool()
def memory_contradict(id_a: str, id_b: str) -> str:
    """Mark two memories as contradicting each other.

    Creates a 'contradicts' edge. During recall, the weaker memory
    (by strength x confidence x recency) is demoted to 30% of its score.

    Args:
        id_a: ID of the first memory.
        id_b: ID of the second memory.

    Returns:
        Confirmation of the contradiction.
    """
    engine.contradict(id_a=id_a, id_b=id_b)
    return f"Memories {id_a} and {id_b} marked as contradicting."


@mcp.tool()
def memory_stats() -> str:
    """Get summary statistics about the memory store.

    Returns counts of total, active, superseded, and contradicted memories,
    the number of edges, and average memory strength.

    Returns:
        Formatted statistics summary.
    """
    stats = engine.stats()
    return format_stats(stats)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run(transport="stdio")
