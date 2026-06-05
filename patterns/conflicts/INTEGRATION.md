# Conflicts — Integration

*Per-category conflict detail. Summary + index: [CONFLICTS.md](../CONFLICTS.md).*

## Critical 6 — I3 $\leftrightarrow$ V13  {#critical-6}

**Type:** Direct Tension

MCP makes it easy to add tool servers. Each server contributes its full schema to the context window. The empirical data:
- Tool selection accuracy: 43% $\to$ 14% at high tool counts (3× degradation)
- GitHub MCP alone: 40,000–55,000 tokens of schema overhead
- 4–5 MCP servers: 60,000+ tokens consumed by schemas before the agent has done anything

The tension: MCP's value proposition is ecosystem richness (many tools, standardised discovery); its cost is the token budget impact of that richness.

**Resolution rule:**
- Measure schema token cost before adding any MCP server (call tools/list; count tokens)
- Apply V13 (Tool Budget) as a hard constraint; never exceed 40 tools per agent (Cursor's empirical limit)
- Dynamic tool injection: load only the tools relevant to the current task, not all tools from all servers
- Prefer I4 (CLI Invocation) for high-frequency tools — zero schema overhead

---

## Connection H — I3 $\sim$ I6  {#connection-h}

**Type:** Composability Tension ($\sim$)

I3 (MCP Server) routes the main agent's tool-selection overhead to a search subagent with its own bounded context. I6 (A2A Delegation) routes execution to a separate executor agent with its own bounded context. The underlying mechanism is identical (mechanism 6: subagent decomposition as context bounding); only the scale and the thing being bounded differ.

**Consequence for system design:** when a system uses both I3 and I6, it has two independent mechanism 6 boundaries. Practitioners who understand this can compose them: the I3 search subagent finds the tool; the I6 executor runs it; the main agent never accumulates either the full tool catalogue or the execution trajectory. Budget model capacity accordingly (mechanism 8: search and routing require less capacity than execution).

---

## Integration vs Integration

| Pattern A | Conflict Type | Pattern B | Resolution |
|:------------|:--:|:------------|:------------------------|
| I1 (Direct API) | $\uparrow$ | I2 (Function Call) | I1 is the execution layer; I2 is LLM routing layer on top. When LLM routing adds no value (deterministic action), skip I2 and use I1 directly. |
| I2 (Function Call) | $\uparrow$ | I3 (MCP Server) | I2 for small, stable, single-agent tool sets. I3 when tools must be shared across agents or tool count exceeds V13 limits. Migration from I2 to I3 is low-cost — start with I2. |
| I3 (MCP Server) | $\leftrightarrow$ | I4 (CLI Invocation) | I3: typed schemas, structured output, high token cost. I4: zero schema overhead, unstructured text output. For any tool with an existing CLI, prefer I4. Use I3 when: credential isolation is required, or tool output must be typed and validated, or the tool has no CLI. |
| I5 (Agent Card) | $\sim$ | I3 (MCP Server) | Agent Cards are agent-level discovery; MCP is tool-level discovery. An agent may serve both: an Agent Card describing its high-level capabilities and an MCP server describing its specific tools. They are complementary, different granularity levels. |
| I6 (A2A Delegation) | $\leftrightarrow$ | O15 (Agent Handoff) | I6 for cross-system delegation (different codebases/organisations). O15 for intra-system context transfer (same codebase, different agent contexts). |
