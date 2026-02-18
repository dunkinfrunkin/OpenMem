---
name: status
description: Show memory store statistics and health
user_invocable: true
---

# /openmem:status

Show the current state of the persistent memory store.

## Instructions

1. Call the `memory_stats` MCP tool to retrieve store statistics.

2. Present the results to the user in a clear summary:

   **Memory Store Status**
   - Total memories and breakdown by status (active, superseded, contradicted)
   - Total edges (relationships between memories)
   - Average memory strength (indicates overall health/freshness)

3. Provide brief guidance:
   - If average strength is low (< 0.5), suggest that many memories may be stale and the user might want to review and reinforce important ones.
   - If there are many superseded or contradicted memories, mention that the store has been actively maintained.
   - If the store is empty, suggest using `/openmem:store` to start building the memory base.
