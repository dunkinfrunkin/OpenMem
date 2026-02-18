---
name: recall
description: Recall memories relevant to the current conversation or a specific query
user_invocable: true
arguments:
  - name: query
    description: Optional search query. If omitted, infer context from the conversation.
    required: false
---

# /openmem:recall

Recall relevant memories from the persistent memory store.

## Instructions

1. Determine the recall query:
   - If the user provided a `$ARGUMENTS` query, use it directly.
   - If no query was provided, analyze the current conversation context and synthesize a focused search query from the key topics, entities, and decisions being discussed.

2. Call the `memory_recall` MCP tool with the query. Use `top_k: 5` and `token_budget: 2000` as defaults unless the user specifies otherwise.

3. Present the results to the user in a clear format:
   - For each memory, show:
     - **Type** and **status**
     - **Content** (the memory text)
     - **Score** (relevance score from 0-1)
     - **Confidence** and **strength**
   - If no memories are found, let the user know and suggest storing relevant information with `/openmem:store`.

4. If any recalled memories seem outdated or contradictory, mention this to the user and suggest using the memory management tools (supersede, contradict) to clean things up.
