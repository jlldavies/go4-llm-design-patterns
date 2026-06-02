# V13 — Tool Budget

> Cap the number and total schema footprint of tools any single agent can see at once — typically below fifteen, never above forty — so the model can actually choose the right tool, and the context window is not consumed by tool definitions before the work begins.

**Also Known As:** Tool Scope Limit, Tool Inventory Cap, Capability Pruning, Tool Catalogue Discipline, MCP Tax Mitigation.

**Classification:** Category V — Reliability · Band V-B Operational Reliability · a *resource-discipline* pattern — it constrains *what the agent can see*, not what it can do, and so reduces the failure mode in which an agent can no longer reliably pick from an oversized menu.

---

## Intent

Keep the per-agent tool catalogue small enough that the model's tool-selection accuracy stays in the usable range and the tool schemas do not consume the context budget the actual task needs — by enforcing a hard cap on tool count, a measured cap on schema-token cost, and a discipline of dynamic-load-only-what-the-task-requires.

## Motivation

The empirical picture is sharper than it looks. Anthropic's Tool Search documentation gives the headline number: tool-selection accuracy drops from **43% at small tool counts to roughly 14% once the catalogue exceeds the model's working capacity** — a 3× collapse on the very capability the tools were added to support. The Berkeley Function-Calling Leaderboard finds worse: accuracy on calendar-scheduling tasks fell from 43% to 2% as the tool count rose from 4 to 51. The mechanism is not mysterious. Tool schemas live in the context window; at scale they crowd out the task; and at scale the model can no longer tell similar tools apart. A 93-tool GitHub MCP server costs ~55,000 tokens of schema before the agent does anything; three MCP servers (GitHub + Slack + Sentry) can burn 143,000 of a 200K window on definitions alone (Layered, 2026; OnlyCLI, 2026).

This is why MCP, which makes tool addition almost frictionless, makes the problem worse rather than better. The original I3 MCP Server pattern's strength — *standardised discovery, easy reuse, the same tool available to many clients* — is also its danger: every new server is a deposit into a context-budget account no one is reconciling. Cursor's hard-cap of 40 active tools, raised under user pressure but kept at all, is the industry's most public acknowledgement that the empirical limit is *somewhere below the model's nominal capacity*. Above that ceiling, the IDE silently drops tools rather than degrade. Claude Code v2.1.7+ shipped Tool Search precisely to lazy-load schemas when MCP definitions would exceed 10% of context, cutting a 77K-token tool load to ~8.7K — an 85% reduction without losing capability (Anthropic, 2026).

V13 is the explicit *discipline* that turns these scattered limits into a design constraint. The pattern is not about being clever with MCP gateways or lazy loaders — those are *implementations* of V13. The pattern itself is the cap, the measurement, and the policy: every agent has a tool budget, the budget is measured in both *count* (cardinality) and *schema tokens* (footprint), and the budget is enforced at design time and on every integration change. Without that discipline, A12 (Tool Proliferation) is what happens by default — and the result is an agent that *looks* powerful and is, on the actual selection task, worse than one with five tools and a clear menu.

**Why schema token costs compound (mechanism 2 + mechanism 3).** Tool schemas live in the KV cache for the entire request — they are not dynamically loaded when a tool is called; they are always present (mechanism 3). Every generated Q vector performs a full similarity search over all cached K vectors, including all schema tokens, at every generation step. Adding 5,000 schema tokens to the prompt adds 5,000 K-vector comparisons per generated token across the entire response (mechanism 2: O(n²) attention means schema cost compounds with response length, not just prompt length). Furthermore, similar tool descriptions produce nearby K-vectors in the learned attention bilinear form (mechanism 1), making routing signals ambiguous when the catalogue is large — the Q-K similarity scores converge toward uniform, degrading tool selection accuracy.

## Applicability

Use a Tool Budget when:

- the agent has more than five tools, *or* will plausibly acquire more (any MCP-using agent qualifies);
- one or more MCP servers are configured, or are likely to be added — schema costs scale with server count, not just tool count;
- the agent runs on a model where the working context is also where reasoning happens (so schema tokens compete with the task);
- tool-selection accuracy is observable as a quality lever (i.e. the agent must reliably pick the right tool, not just have access to a wide set);
- the same agent is used across multiple task types, where some tasks need only a subset of the catalogue.

Do not use it when:

- the agent has 1–5 stable tools registered in code (I2 Function Call), where the schema cost is trivial and selection is not pressured — the budget is implicit and below threshold;
- the system is a fixed pipeline with no LLM-driven tool selection (a sequence of API calls, with no choice point) — V13 governs *selection surface*, not *integration surface*. Use **I1 Direct API Call** thinking;
- the agent is a code-execution agent whose "tool" is one sandbox plus the language standard library (R13 CodeAct + V8 Tool Sandboxing) — the catalogue collapses to one; budget is satisfied trivially.

## Decision Criteria

V13 applies the moment the per-agent tool catalogue would benefit from being smaller than the catalogue happens to be — and the moment any integration can expand the catalogue dynamically.

**1. Count the tools the agent can see at start of turn.** Sum every function, every MCP-exposed tool, every sub-agent capability invoked as a tool. Practical thresholds (empirical, model-dependent):
- **≤ 15 tools** — comfort zone; selection accuracy typically near ceiling. No special action; document the budget.
- **15–30 tools** — caution; selection accuracy begins to degrade; require **V14 Trajectory Logging** to measure tool-selection error rate.
- **30–40 tools** — danger; you are at Cursor's hard cap; you must apply dynamic-load (subset the catalogue per task) or split the agent.
- **> 40 tools** — block. Either dynamic-load is mandatory, or use **O17 Agent Isolation** to split the catalogue across specialist sub-agents, or move high-overhead tools to **I4 CLI Invocation** (zero schema cost).

**2. Measure the schema-token footprint, not just the count.** A "small" set of tools with verbose JSON schemas can equal a large set of compact ones. Run `tools/list` on every active MCP server; sum the resulting bytes; convert to tokens. Thresholds:
- **< 5% of context window** — fine.
- **5–10% of context window** — acceptable for short tasks; degraded for long ones.
- **> 10% of context window** — Anthropic's published trigger for Tool Search lazy-loading. Treat this as the V13 hard threshold for schema footprint, even if tool count is under 40.

**3. Pick a strategy.** The three real strategies, in order of effort:
- **Static prune.** Switch off tools that are not actively used. This is the Cursor / Claude Code Settings-page move: cheap, immediate, recovers the budget in minutes. Always do this first.
- **Dynamic load.** Inject only the tools relevant to the current task. Implementations: Anthropic Tool Search (BM25 or regex over a name-only index), MCP gateway with semantic retrieval (StackOne, MCP Gateway), or a task-routing classifier upstream of the agent that picks the toolset. This is the production answer at scale.
- **Split the agent.** Compose with **O17 Agent Isolation**: one agent per tool family, each with its own narrow budget; an orchestrator routes. This is the architectural answer when the catalogue is irreducibly large and dynamic load is not enough.

**4. Re-audit on every integration change.** Adding an MCP server, a new function, a new sub-agent capability — each is a V13 event. The most common failure (see §Failure modes) is "V13 was checked at deployment and never again." Tie the re-check to change management: any PR that touches the tool manifest cannot merge without an updated count + schema-token measurement.

**5. Watch the indirect surface.** Tools that *return* tool calls (sub-agent handoffs, R13 CodeAct's `exec`, RAG-MCP-style tool retrieval) hide capability behind a single visible tool. Count these by *post-expansion* surface: an `exec` tool that can call anything in the sandbox is, for V13 purposes, the size of the sandbox's reachable capability set, not 1.

**Quick test — V13 is the right pattern when:**

- the agent has, or might soon have, more than 15 tools, *or* its tool schemas consume more than 5% of the context budget, *and*
- there is an LLM-driven selection step that picks among those tools (i.e. selection accuracy is a real quality lever), *and*
- there is at least one integration surface (MCP, sub-agent, plugin) that can expand the catalogue without a code change, *and*
- the agent runs on a context-window that the rest of the task also wants to use.

If the agent has ≤ 5 hand-wired tools and no plausible expansion path, V13 is unnecessary — the budget is implicit. If the agent's tools are entirely CLI-invoked (**I4**), the schema-token component of the budget collapses; only the count test still applies. If schema footprint alone is the problem and count is fine, the lighter answer is **K6 Context Compression** of returned tool outputs and lazy schema loading — not a hard cap on count.

## Structure

```
                ┌─────────────────────────────────────────────┐
                │  Agent under design / under deployment      │
                └────────────────────┬────────────────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │  Tool Registry            │
                       │  (everything the agent    │
                       │   *could* see)            │
                       └─────────────┬─────────────┘
                                     │
                                     ▼
                       ┌───────────────────────────┐
                       │  Tool Budget Policy       │
                       │   max_tools  (count)      │
                       │   max_schema (tokens)     │
                       │   strategy   (static /    │
                       │                dynamic /  │
                       │                split)     │
                       └─────────────┬─────────────┘
                                     │
                       ┌─────────────┴─────────────┐
                       ▼                           ▼
            ┌────────────────────┐      ┌────────────────────┐
            │ Tool Router        │      │ Budget Enforcer    │
            │ (dynamic):         │      │ (verifies count +  │
            │  picks subset of   │      │  schema tokens at  │
            │  Registry          │      │  load + on change) │
            │  for this task     │      │                    │
            └─────────┬──────────┘      └─────────┬──────────┘
                      │                            │
                      └──────────────┬─────────────┘
                                     ▼
                       ┌───────────────────────────┐
                       │  Agent context for turn   │
                       │  (≤ budget tools loaded)  │
                       └─────────────┬─────────────┘
                                     ▼
                       ┌───────────────────────────┐
                       │  V14 trace                │
                       │  (tool-selection accuracy,│
                       │   tool-call distribution, │
                       │   unused tools)           │
                       └─────────────┬─────────────┘
                                     ▼
                       Feedback into Policy
                       (prune unused; re-tune)
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Tool Registry** | the authoritative list of every tool the agent *could* call, with its schema, owner, and last-used timestamp | integration manifests + MCP servers + function decorators → unified tool catalogue | be the same object as the per-turn loaded set. Conflating "everything available" with "everything loaded" is how the budget silently breaks. |
| **Tool Budget Policy** | the per-agent cap: `max_tools`, `max_schema_tokens`, and the chosen strategy (static / dynamic / split) | agent role + task profile → policy document | be set by gut feel. Thresholds must come from measured selection accuracy and measured schema cost, recorded in the policy. |
| **Budget Enforcer** | the gate that compares the loaded toolset to the policy at agent initialisation and on every integration change | loaded toolset + policy → PASS / FAIL / WARN | fail open. A budget that warns on violation but still loads the catalogue is theatre; the enforcer must be able to block, or at minimum force a routing decision. |
| **Tool Router** *(dynamic-load implementations)* | the per-task selection of *which* subset of the Registry to expose this turn | task hint or current query + Registry index → subset within budget | load everything just because budget allows. The router's quality is judged by *how few tools it can load while still letting the task succeed*. |
| **V14 Tap** | the telemetry that records which tools were loaded, which were called, which were *never* called, and where the model picked the wrong tool | tool-call traces → per-tool utility statistics | be optional. Without the trace, no one knows that 23 of the 40 loaded tools have not been called in a month and could be pruned. |
| **Pruner / Auditor** | the recurring review that uses V14 data to retire unused tools and re-tune the policy | utility statistics + change requests → updated Registry + updated Policy | be a one-shot. Catalogues drift up; pruning must be a recurring cadence (sprint, month, release), tied to the V14 evidence. |

The six responsibilities are deliberately separated. The Registry knows everything; the Policy says what is allowed; the Enforcer is the gate; the Router is the runtime allocator; V14 is the evidence; the Pruner closes the loop. Collapsing the Registry into the Enforcer (which is what "just configure tools/list" does) is the most common implementation error — it means the budget is fixed at startup and never revisited.

## Collaborations

At **design time**, the Tool Budget Policy is set for each agent: a numeric `max_tools`, a `max_schema_tokens` measured against a representative context window, and a strategy choice (static prune, dynamic load, or split). The Tool Registry is built from the agent's integration manifest — function decorators, MCP-server URIs, sub-agent capabilities — and includes every tool *available*, not every tool *loaded*. The Budget Enforcer runs on agent initialisation: it loads tools per strategy, counts, sums schema tokens, and either PASSes (within budget), routes (dynamic-load picks a subset), or BLOCKs (over hard cap, no router configured).

At **runtime**, when dynamic loading is the strategy, the Tool Router examines the incoming task (a user request, a sub-task from O6 Orchestrator-Workers, a step from an O2 chain) and picks the smallest subset of the Registry that lets the task proceed. Implementations vary: Anthropic Tool Search uses BM25 / regex over a name-only index; MCP gateways use FAISS + sentence embeddings; a simple classifier suffices when task types are discrete. The loaded subset enters the agent context for the turn; the rest of the Registry does not.

The **V14 Tap** records, for each turn: which tools were loaded, which were called, which sat unused in the context, and where the model attempted to use a tool that was not loaded (a routing miss). At a recurring cadence — sprint review, monthly maintenance, release gate — the **Pruner / Auditor** reads V14 statistics and proposes Registry changes: retire tools with zero calls in N weeks, split tools that are co-called frequently into their own bundle, fold near-duplicate tools into one. The Policy is re-tuned: budgets that are systematically under-used can shrink; budgets that systematically miss can grow, but only with measured selection-accuracy support.

V13 composes upward into the integration patterns it is constraining. **I2 Function Call** is the simplest substrate — a hand-written tool list — and V13 here is one number in a config. **I3 MCP Server** is where V13 earns its keep: every new server is a re-audit; the gateway, if used, is the Router; the gateway's lazy-load is the dynamic strategy. **I4 CLI Invocation** is the escape valve — moving a tool from MCP to CLI converts schema-token cost to (essentially) zero, at the cost of typing discipline.

## Consequences

**Benefits**

- Selection accuracy stays in the usable range. The headline 43% → 14% collapse is what V13 is preventing; agents that stay inside their budget keep the high-end accuracy the tools were added for.
- Context budget is reclaimed for the task. A 77K-token tool load reduced to 8.7K (Anthropic's published Tool Search number) is roughly 70K tokens of reasoning surface returned to actual work.
- Catalogue drift is bounded. Without V13, MCP servers accumulate; with V13, every addition is a re-decision.
- Sets up clean composition with **O17 Agent Isolation** — splitting an over-budget agent into role-narrow sub-agents is the standard escape when dynamic-load isn't enough.

**Costs**

- Discipline overhead. Someone owns the Pruner cadence; someone owns the policy. Without an owner, the budget ages out.
- Dynamic-load infrastructure (router, index, gateway) is a real build. Static prune is free; dynamic load is a system.
- False-negative routing. A Tool Router that picks too narrowly fails the task; tuning needs eval data (V16).
- "Useful but rarely called" tools become political — the Pruner has to defend retirements against owners who want their tool kept loaded.

**Risks and failure modes**

- *Budget checked once, never again.* The most common failure. Set at deployment, drifted by integration creep, never re-audited. Symptom: agent that worked in week one performs worse in week eight, no one can explain it.
- *MCP gateway loaded everything anyway.* Gateway claims dynamic loading but the underlying client still calls `tools/list` on every server eagerly. Verify the loaded-set at the model boundary, not at the gateway boundary.
- *Tool-of-tools illusion.* One visible tool (an `exec`, a sub-agent handoff, a `mcp_proxy.run_any_tool`) hides the full catalogue behind a single entry; the count is satisfied; the schema is satisfied; the model is still selecting from N capabilities, just opaquely. Count by post-expansion surface.
- *Router misses on out-of-distribution tasks.* The Router's index was trained / tuned on the in-distribution tasks; an edge-case task picks the wrong subset and the agent has no tool to do the job. Surface and re-route to V1 Human-in-the-Loop, then add the missed-task signature to the Router's training data.
- *Schema bloat hidden in tool *responses*.* Budget polices the input schemas; the *response* schemas (output JSON, tool result bodies) can still consume context. Pair with **K6 Context Compression** for verbose tool outputs and **V11 Error Compaction** for tool errors.
- *Optimising count, missing tokens.* 30 small tools and 5 huge ones — the count is fine but the schema tokens are not. Measure both.

## Implementation Notes

- The fast win on any agent that uses MCP is the Settings-page prune. Open each server, turn off the tools the agent does not call (V14 will tell you which). On Cursor, this gets you below 40 in minutes. On Claude Code, MCP Tool Search auto-enables when schemas pass 10% of context.
- Measure schema cost before adding a server. `tools/list` on the server, count tokens, compare to budget. If a single server would consume > 5% of context alone, treat it as an architectural decision — not a "just add it" change.
- Prefer **I4 CLI Invocation** for high-frequency, high-schema-cost tools that have a CLI. The schema collapses to "this tool exists and takes a shell command" — sometimes a 35× cost reduction (OnlyCLI benchmark, 2026).
- For genuinely large catalogues (50+ tools), dynamic-load is the standard production answer. Anthropic Tool Search, the MCP Gateway pattern, StackOne, and Atlassian's mcp-compressor are the current implementations. Choose the one whose query semantics match the agent's task signature.
- When dynamic-load is impractical, **O17 Agent Isolation** is the structural answer: one specialist agent per tool family, an orchestrator that routes by task type. Each specialist has a narrow, comfortable budget; the orchestrator itself has a tiny tool set (the routes).
- Encode the budget in **V7 AgentSpec** if you have it: `PROHIBIT load_tools WHERE count(loaded) > max_tools`. This makes the budget a runtime invariant, not honour-system policy.
- The V14 trace must include *non-events*: tools loaded but never called are the prune candidates. A trace that only logs successful tool calls cannot drive the Pruner.
- Keep the Policy human-readable. The thresholds (`max_tools: 15`, `max_schema_tokens: 10_000`, `strategy: dynamic_load`) live in the agent's spec next to the V3 audit, not buried in framework configuration.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V13 is mostly *policy + wiring*, with an optional LLM step inside the Tool Router (when natural-language task hints select the subset). It composes with **I2 Function Call** (the smallest tool surface), **I3 MCP Server** (the surface it most often disciplines), **I4 CLI Invocation** (the escape valve for schema cost), **O17 Agent Isolation** (the split strategy), **V14 Trajectory Logging** (the evidence), **V7 AgentSpec** (the encoding of the policy as a runtime rule), and **K6 Context Compression** / **V11 Error Compaction** (for the tool-response side of the budget V13 itself doesn't cover).

**The chain — design-time:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Build the Tool Registry from the agent's integration manifest (functions + MCP servers + sub-agent capabilities) | `code` | I2 / I3 / I4 manifests |
| 2 | Measure: count tools, sum schema tokens (`tools/list` per server) | `code` | |
| 3 | Set the Policy: `max_tools`, `max_schema_tokens`, strategy (`static` / `dynamic` / `split`) | `code` (human-authored) | V7 if encoded as policy |
| 4 | Branch: if over budget under `static`, prune the Registry (Settings-page off-switches) and re-measure; if `dynamic`, build the Tool Router index; if `split`, hand off to O17 | `code` | O17 (if split) |
| 5 | Record the audit row in the agent spec next to the V3 audit | `code` | |

**The chain — per-turn (dynamic-load strategy):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| R1 | Receive task / query | `code` | |
| R2 | Tool Router picks the subset (BM25 / regex / semantic search / classifier) within budget | `LLM` *or* `code` | Router session (if LLM) |
| R3 | Budget Enforcer verifies subset.count ≤ max_tools and sum(schema_tokens) ≤ max_schema_tokens | `code` | |
| R4 | Load the subset into the agent context for the turn | `code` | |
| R5 | Agent runs; emits tool calls; V14 records which loaded tools were called and which were not | `LLM` (the Agent) + `code` (the trace) | V14 |
| R6 | At session end: stream the unused-tools list to the Pruner | `code` | |

**The chain — pruner cadence (sprint / month / release):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| P1 | Aggregate V14 stats: per-tool call rate, per-tool error rate, per-tool last-used timestamp | `code` | V14 |
| P2 | Pruner proposes retirements: tools with zero calls in N weeks; tools with high schema cost and low call rate | `code` *or* `LLM` (rules vs. judgement) | Pruner session (if LLM) |
| P3 | Human review of proposed retirements (most teams will keep this step) | `code` | V1 Human-in-the-Loop |
| P4 | Apply: remove from Registry; re-tune Policy if budget was systematically under-used | `code` | |

**Skeleton:**

```
# design time
registry  = build_registry(integration_manifest)            # code
metrics   = measure(registry)                               # code — count + schema tokens
policy    = load_policy(agent_spec)                         # code
strategy  = enforce(policy, metrics)                        # code — static/dynamic/split/BLOCK
if strategy == "split":
    return delegate_to_O17(registry, policy)                # code
if strategy == "dynamic":
    router_index = build_index(registry)                    # code (BM25, embeddings, classifier)

# per turn
subset    = Router(task_hint, router_index, policy)         # LLM (or code)  — Router session
assert within_budget(subset, policy)                        # code — Budget Enforcer
output    = Agent(subset, task)                             # LLM — the agent itself
trace_loaded_vs_called(subset, output.tool_calls)           # code — V14

# pruner cadence
stats     = aggregate(v14_traces, window=N_weeks)           # code
proposed  = Pruner(stats, registry, policy)                 # LLM (or rules)  — Pruner session
approved  = HumanReview(proposed)                           # V1
apply(approved, registry, policy)                           # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Tool Router** *(optional — code routing works for discrete task types)* | small fast generalist *or* fine-tuned classifier; selection is high-volume, low-stakes per call | role: *"you select the minimal set of tools needed to handle the incoming task. You see a name + one-line description of every available tool. Return the names of the tools needed — fewer is better. Never return more than `max_tools`."*; the budget; the Registry index (names + summaries, not full schemas) | the task / query + (optional) a recent-history hint |
| **Pruner** *(optional — most teams use deterministic rules)* | capable generalist; pruning judgement matters more than throughput | role: *"you review tool-utilisation telemetry and propose retirements. A tool is a retirement candidate if it has not been called in the window, or if its schema cost exceeds its measured value. Propose with reasons; humans approve."*; the policy thresholds; the categorisation rules | the V14-derived per-tool statistics for the window |

**Specialist-model note.** No fine-tuned specialist is required for V13 itself — the policy and the enforcer are code, and both LLM sessions are optional. The two places where a specialist *helps*: (1) the Tool Router, when task types are continuous rather than discrete, can be a fine-tuned classifier or a small embedding model (sentence-transformers + FAISS is the common implementation, as in the MCP Gateway Registry and StackOne); (2) the Pruner, when retirement decisions are too nuanced for a rule, is a job for a strong generalist with the full telemetry. Neither is required; the simplest valid V13 is a number in a config and a Settings-page prune.

## Open-Source Implementations

V13 is a *policy / discipline pattern* — there is no single canonical library; instead, there is a small constellation of implementations of the *strategies* (static prune, dynamic load, split):

- **Anthropic Tool Search (Claude Code v2.1.7+ and the Claude Developer Platform)** — [`platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool`](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool) and [`code.claude.com/docs/en/mcp`](https://code.claude.com/docs/en/mcp). The reference *dynamic-load* implementation: when tool definitions exceed ~10% of context, the schemas are lazy-loaded via BM25 / regex search over a name-only index. Reports ~85% token reduction at typical loads.
- **MCP Gateway and Registry (agentic-community)** — [`github.com/agentic-community/mcp-gateway-registry`](https://github.com/agentic-community/mcp-gateway-registry) — open-source MCP gateway with a central registry, FAISS + sentence-transformers semantic tool discovery, and configurable per-agent budgets. The canonical *gateway* implementation.
- **Microsoft MCP Gateway** — [`github.com/microsoft/mcp-gateway`](https://github.com/microsoft/mcp-gateway) — Microsoft's gateway-pattern reference, with dynamic tool exposure and per-session catalogue control.
- **Atlassian mcp-compressor** — [`github.com/atlassian-labs/mcp-compressor`](https://github.com/atlassian-labs/mcp-compressor) — an MCP wrapper that compresses tool schemas and applies usage-driven pruning to reduce token cost on tool/list.
- **Cursor IDE Settings — per-server tool toggles** — [`forum.cursor.com/t/tools-limited-to-40-total/67976`](https://forum.cursor.com/t/tools-limited-to-40-total/67976). The reference *static-prune* implementation: a UI for turning individual MCP tools off, enforced as a hard 40-tool ceiling.
- **Tool Attention (Sadani & Kumar, 2026)** — [`arxiv.org/abs/2604.21816`](https://arxiv.org/abs/2604.21816). Research artifact for dynamic tool gating + lazy schema loading; reports 47.3K → 2.4K per-turn tool tokens on a 120-tool / 6-server benchmark.

## Known Uses

- **Cursor IDE** — production 40-tool hard cap with per-tool Settings-page enable/disable; the public reference for static-prune at scale.
- **Claude Code (Anthropic)** — production dynamic-load via Tool Search from v2.1.7; auto-activates when MCP tool schemas exceed ~10% of context. Documented at [`code.claude.com/docs/en/mcp`](https://code.claude.com/docs/en/mcp).
- **The Claude Developer Platform's Tool Search tool** — server-side API for the same lazy-load pattern in third-party agents.
- **GitHub Agentic Workflows** — explicit token-efficiency work in 2026 reducing GitHub MCP's per-request footprint from ~55K tokens by schema pruning and on-demand schema fetch ([`github.blog/ai-and-ml/github-copilot/improving-token-efficiency-in-github-agentic-workflows/`](https://github.blog/ai-and-ml/github-copilot/improving-token-efficiency-in-github-agentic-workflows/)).
- **StackOne** — production search-first tool discovery across 200+ connectors / 10,000+ actions; demonstrates V13 at "enterprise catalogue" scale via dynamic load.
- **MCP Protocol SEP-1576 (proposed)** — [`github.com/modelcontextprotocol/modelcontextprotocol/issues/1576`](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1576) — protocol-level proposal to add a `minimal` flag for `tools/list` (names + summaries) and a `tools/get_schema` method (full schema on demand). V13 promoted to protocol.
- **The "build small, focused MCP servers" community consensus** (Demiliani, 2025; Layered, 2026; Apigene, 2026) — the prescriptive form of V13 for MCP authors: a server exposing 5–10 well-scoped tools is preferable to a 30-tool mega-server.

## Related Patterns

- **Competes with** I3 MCP Server — see *CONFLICTS.md* CRITICAL 6. MCP's value (rich ecosystem of tools) is exactly what V13 disciplines (the schema cost of that richness). They are not alternatives; V13 is the policy without which I3 is unsafe at scale.
- **Pairs with** I2 Function Call — V13 is trivially satisfied for small hand-wired toolsets, but the *count* discipline applies even there. The pattern formalises what good I2 design already does informally.
- **Composes with** I4 CLI Invocation — moving a high-schema-cost tool from MCP to CLI is the most effective single budget recovery. CLI tools cost ~0 schema tokens; their "schema" is the agent's general knowledge of shell.
- **Composes with** O17 Agent Isolation — when a single agent's catalogue is irreducibly large, split it: each sub-agent has a narrow budget; the orchestrator routes. O17 is V13's "structural" answer where dynamic-load is the "runtime" answer.
- **Pairs with** V14 Trajectory Logging — V13 cannot be tuned without per-tool call statistics; the Pruner is a V14 consumer.
- **Pairs with** V7 AgentSpec — the budget can and should be encoded as deontic policy (`PROHIBIT load_tools WHERE count > max_tools`) so enforcement is runtime, not honour-system.
- **Composes with** K6 Context Compression and V11 Error Compaction — V13 polices the *input* (schema) side of tool context; K6 / V11 police the *output* (response / error) side. Both are needed to keep the full tool-budget envelope.
- **Required by** V3 Rule of Two — V3 explicitly cites V13 as the cap on the dynamic-acquisition surface: an MCP catalogue capped at 40 tools is a much smaller attack surface for compositional trifecta acquisition than an uncapped one.
- **Counters** the anti-pattern A12 Tool Proliferation — A12 is the unmanaged-catalogue failure mode; V13 is the discipline that prevents it. Citing A12 without V13 is diagnosis without treatment.
- **Distinct from** V9 Bounded Execution — V9 caps iterations / cost / time per *run*; V13 caps the tool *catalogue* per *agent*. Both are budgets, but at different layers of the stack; both are required for a runaway-resistant agent.

## Sources

- Anthropic (2026) — "Tool Search tool" — [`platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool`](https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool). The headline 43% → 14% selection-accuracy figure and the 10%-of-context trigger for lazy-loading.
- Anthropic (2026) — "Connect Claude Code to tools via MCP" — [`code.claude.com/docs/en/mcp`](https://code.claude.com/docs/en/mcp). Claude Code v2.1.7+ Tool Search behaviour and the 77K → 8.7K token reduction.
- Anthropic Engineering (2026) — "Introducing advanced tool use on the Claude Developer Platform" — [`anthropic.com/engineering/advanced-tool-use`](https://www.anthropic.com/engineering/advanced-tool-use).
- Berkeley Function-Calling Leaderboard — accuracy collapses from 43% to 2% as tool count grows from 4 to 51 on scheduling tasks. Referenced via [`emergentmind.com/topics/tool-selection-accuracy-ts`](https://www.emergentmind.com/topics/tool-selection-accuracy-ts) and [`tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale`](https://tianpan.co/blog/2026-04-09-tool-selection-problem-agent-tool-routing-at-scale).
- Sadani, A. & Kumar, D. (2026) — "Tool Attention Is All You Need: Dynamic Tool Gating and Lazy Schema Loading for Eliminating the MCP/Tools Tax in Scalable Agentic Workflows" — arXiv 2604.21816 — [`arxiv.org/abs/2604.21816`](https://arxiv.org/abs/2604.21816). Per-turn tool tokens reduced 47.3K → 2.4K (~95%); context utilisation 24% → 91% on 120-tool / 6-server benchmark.
- Cursor Community Forum — "Tools limited to 40 total" — [`forum.cursor.com/t/tools-limited-to-40-total/67976`](https://forum.cursor.com/t/tools-limited-to-40-total/67976). The canonical statement of the 40-tool hard cap and its rationale.
- Layered (2026) — "MCP Tool Schema Bloat: The Hidden Token Tax (and How to Fix It)" — [`layered.dev/mcp-tool-schema-bloat-the-hidden-token-tax-and-how-to-fix-it/`](https://layered.dev/mcp-tool-schema-bloat-the-hidden-token-tax-and-how-to-fix-it/). The GitHub MCP 55K-token measurement and the GitHub+Slack+Sentry 143K combined figure.
- OnlyCLI (2026) — "MCP Token Trap: Why Your AI Agent Burns 35x More Tokens Than a CLI" — [`onlycli.github.io/OnlyCLI/blog/mcp-token-cost-benchmark/`](https://onlycli.github.io/OnlyCLI/blog/mcp-token-cost-benchmark/). The MCP-vs-CLI 35× token ratio that motivates the I4 escape valve.
- Model Context Protocol — SEP-1576 — [`github.com/modelcontextprotocol/modelcontextprotocol/issues/1576`](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1576). Protocol-level proposal for `minimal` `tools/list` and on-demand `tools/get_schema`.
- GitHub Blog (2026) — "Improving token efficiency in GitHub Agentic Workflows" — [`github.blog/ai-and-ml/github-copilot/improving-token-efficiency-in-github-agentic-workflows/`](https://github.blog/ai-and-ml/github-copilot/improving-token-efficiency-in-github-agentic-workflows/).
- Composio (2026) — "MCP Gateways: A Developer's Guide to AI Agent Architecture in 2026" — [`composio.dev/content/mcp-gateways-guide`](https://composio.dev/content/mcp-gateways-guide). 67,300 tokens / 33.7% of 200K context consumed by 7 active MCP servers, before any conversation.
