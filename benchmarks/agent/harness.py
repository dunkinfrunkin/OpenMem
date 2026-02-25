"""LLM agent harness using OpenAI function calling.

Gives the agent a `memory_recall` tool and lets it search iteratively
until it produces a final answer.
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field

from benchmarks.adapters.base import MemoryAdapter

MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "memory_recall",
            "description": (
                "Search your memory for relevant information. "
                "Returns memories ranked by relevance score. "
                "You can call this multiple times with different queries "
                "to find all the information you need."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language search query",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Max number of results (default 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        },
    },
]

SYSTEM_PROMPT = """\
You are an assistant that answers questions using ONLY information from your memory system.

You have access to a `memory_recall` tool that searches a knowledge base and returns relevant memories.

Rules:
- ALWAYS search your memory before answering. Never guess or use prior knowledge.
- You may call memory_recall multiple times with different queries to gather all needed info.
- If you find conflicting information, prefer the one that appears more authoritative or recent.
- Base your answer strictly on what you find in memory. If the information isn't there, say so.
- Be specific and include exact details (numbers, names, versions) when available.
- Once you have enough information, provide a clear, concise answer.
"""


@dataclass
class AgentResult:
    """Result of an agent run on a single scenario."""
    answer: str
    tool_calls: int = 0
    recall_calls: int = 0
    recall_latencies_ms: list[float] = field(default_factory=list)
    total_latency_ms: float = 0.0
    llm_latency_ms: float = 0.0
    memory_latency_ms: float = 0.0
    messages: list[dict] = field(default_factory=list)
    error: str | None = None


class AgentHarness:
    """Drives an OpenAI model through a memory-recall loop."""

    def __init__(
        self,
        model: str = "gpt-4o-mini",
        max_turns: int = 10,
        temperature: float = 0.0,
    ) -> None:
        self.model = model
        self.max_turns = max_turns
        self.temperature = temperature
        self._client = None

    def _get_client(self):
        if self._client is None:
            from openai import OpenAI
            self._client = OpenAI()
        return self._client

    def run(self, adapter: MemoryAdapter, task: str) -> AgentResult:
        client = self._get_client()
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task},
        ]

        tool_calls_count = 0
        recall_calls_count = 0
        recall_latencies: list[float] = []
        total_llm_ms = 0.0
        total_mem_ms = 0.0
        total_start = time.perf_counter()

        for _turn in range(self.max_turns):
            llm_start = time.perf_counter()
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=MEMORY_TOOLS,
                    tool_choice="auto",
                    temperature=self.temperature,
                )
            except Exception as e:
                return AgentResult(
                    answer="",
                    error=f"OpenAI API error: {e}",
                    total_latency_ms=(time.perf_counter() - total_start) * 1000,
                )
            llm_elapsed = (time.perf_counter() - llm_start) * 1000
            total_llm_ms += llm_elapsed

            msg = response.choices[0].message

            # Serialize assistant message for the log
            assistant_msg: dict = {"role": "assistant", "content": msg.content}
            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            messages.append(assistant_msg)

            if not msg.tool_calls:
                # Agent gave a final answer
                total_elapsed = (time.perf_counter() - total_start) * 1000
                return AgentResult(
                    answer=msg.content or "",
                    tool_calls=tool_calls_count,
                    recall_calls=recall_calls_count,
                    recall_latencies_ms=recall_latencies,
                    total_latency_ms=total_elapsed,
                    llm_latency_ms=total_llm_ms,
                    memory_latency_ms=total_mem_ms,
                    messages=messages,
                )

            # Execute tool calls
            for tc in msg.tool_calls:
                tool_calls_count += 1
                fn_name = tc.function.name
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": "Error: invalid JSON arguments",
                    })
                    continue

                if fn_name == "memory_recall":
                    recall_calls_count += 1
                    query = args.get("query", "")
                    top_k = args.get("top_k", 5)

                    mem_start = time.perf_counter()
                    results = adapter.recall(query, top_k=top_k)
                    mem_elapsed = (time.perf_counter() - mem_start) * 1000
                    recall_latencies.append(mem_elapsed)
                    total_mem_ms += mem_elapsed

                    # Format results for the agent
                    if results:
                        lines = [f'Results for "{query}":']
                        for i, r in enumerate(results, 1):
                            lines.append(f"  {i}. [score={r.score:.3f}] {_get_memory_text(adapter, r.id)}")
                        tool_output = "\n".join(lines)
                    else:
                        tool_output = f'No results found for "{query}"'
                else:
                    tool_output = f"Unknown tool: {fn_name}"

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": tool_output,
                })

        # Max turns exhausted
        total_elapsed = (time.perf_counter() - total_start) * 1000
        last_content = ""
        for m in reversed(messages):
            if m.get("role") == "assistant" and m.get("content"):
                last_content = m["content"]
                break

        return AgentResult(
            answer=last_content,
            tool_calls=tool_calls_count,
            recall_calls=recall_calls_count,
            recall_latencies_ms=recall_latencies,
            total_latency_ms=total_elapsed,
            llm_latency_ms=total_llm_ms,
            memory_latency_ms=total_mem_ms,
            messages=messages,
            error="Max turns exhausted" if not last_content else None,
        )


def _get_memory_text(adapter: MemoryAdapter, memory_id: str) -> str:
    """Retrieve the original text for a memory ID.

    Falls back to just returning the ID if the adapter doesn't expose stored text.
    """
    # For adapters that store text in a dict
    if hasattr(adapter, "_memories") and isinstance(adapter._memories, dict):
        return adapter._memories.get(memory_id, memory_id)

    # For OpenMem-based adapters with an engine
    if hasattr(adapter, "_engine") and adapter._engine is not None:
        id_map = getattr(adapter, "_id_map", {})
        internal_id = id_map.get(memory_id)
        if not internal_id:
            # Try reverse: memory_id might already be internal
            internal_id = memory_id
        try:
            mem = adapter._engine.store.get_memory(internal_id)
            if mem:
                return mem.text
        except Exception:
            pass

    # For ChromaDB adapter
    if hasattr(adapter, "_collection") and adapter._collection is not None:
        try:
            result = adapter._collection.get(ids=[memory_id])
            if result and result.get("documents") and result["documents"][0]:
                return result["documents"][0]
        except Exception:
            pass

    return f"[memory:{memory_id}]"
