# Integration Pattern Selection

## Decision Flow

```
Does LLM reasoning determine which action to take?
  NO → I1 (Direct API Call): synchronous HTTP, no model involvement

  YES:
    Does a CLI already exist for this tool?
      YES → I4 (CLI Invocation) first — zero schema overhead

    How many tools, and are they shared across agents?
      1–5 tools, single agent → I2 (Function/Tool Call)
      5–20 tools shared across agents → I2 + I3 hybrid
      20+ tools → I3 (MCP Server) with gateway + dynamic discovery

    Do multiple agents from different vendors need to coordinate?
      YES → I5 (Agent Card) for discovery + I6 (A2A Delegation) for execution
```

## Cost Reality

| Pattern | Context overhead | Notes |
|---|---|---|
| I1 Direct API | None | Model not involved; deterministic |
| I2 Function Call | Schema tokens (per tool) | Each tool schema costs attention budget |
| I3 MCP Server | High | GitHub MCP alone: 40,000–55,000 tokens/request |
| I4 CLI Invocation | Near zero | Existing CLI; command string only |
| I5 Agent Card | Minimal (JSON descriptor) | Discovery only; no execution cost |
| I6 A2A Delegation | Per sub-task | Full task delegation; cost of the delegated agent |

**Design tool budgets before choosing integration patterns.** 4–5 MCP servers = 60,000+ context tokens on schemas alone. Apply V13 (Tool Budget) before adding I3 servers.
