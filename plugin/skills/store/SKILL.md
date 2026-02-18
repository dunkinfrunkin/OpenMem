---
name: store
description: Store important facts, decisions, or preferences as persistent memories
user_invocable: true
arguments:
  - name: content
    description: Optional content to store. If omitted, extract key facts from the conversation.
    required: false
---

# /openmem:store

Store memories from the current conversation into persistent memory.

## Instructions

1. Determine what to store:
   - If the user provided `$ARGUMENTS` content, store that directly.
   - If no content was provided, analyze the current conversation and extract the most important:
     - **Decisions** made (type: `decision`)
     - **Preferences** expressed (type: `preference`)
     - **Key facts** established (type: `fact`)
     - **Constraints** identified (type: `constraint`)
     - **Plans** discussed (type: `plan`)
     - **Incidents** or issues encountered (type: `incident`)

2. For each item to store, call the `memory_store` MCP tool with:
   - `text`: The full content of the memory
   - `type`: One of `fact`, `decision`, `preference`, `incident`, `plan`, `constraint`
   - `entities`: A list of key entities (project names, people, technologies, etc.)
   - `confidence`: How certain we are (0-1, default 1.0)
   - `gist`: A short one-line summary for quick retrieval

3. If you identify relationships between new memories or between new and existing memories, use `memory_link` to connect them.

4. Report back to the user what was stored, showing:
   - The memory text (abbreviated if long)
   - The type and entities
   - The memory ID (so they can reference it later)

5. If you think the new memory supersedes or contradicts an existing one, mention this and offer to use `memory_supersede` or `memory_contradict` to manage the relationship.
