# I3 — MCP Server

> Deploy tools behind a standardised Model Context Protocol server so any compliant client can discover, authenticate, and invoke them — and pay the schema-token cost of that standardisation deliberately, not by accident.

**Also Known As:** Model Context Protocol, MCP, Tool Server, Standardised Tool Discovery, "the npm of AI tools".

**Classification:** Category VI — Integration · the *standardised, shared, multi-client* member of the band — wraps **I1** internally, like **I2**, but lifts tool discovery out of the agent codebase and into a separate protocol-conformant process. Direct tension with **V13 Tool Budget** (see CRITICAL 6).

---

## Intent

Expose a set of tools through a separate protocol-conformant server so multiple agents and clients can discover, authenticate, and invoke those tools without per-agent integration code — accepting the resulting schema-token cost as a first-class budget item.

## Motivation

Before MCP, every agent framework had its own tool-integration shape: a LangChain `Tool` object, a CrewAI tool wrapper, OpenAI function schemas, Claude tool definitions, a custom in-house registry. Adding a new tool meant integrating it N times, once per framework; sharing a tool across teams meant duplicating it or vendoring a framework. The standard interface was missing.

Anthropic's Model Context Protocol — published November 2024 and donated to the Linux Foundation's Agentic AI Foundation in December 2025 — fills exactly that gap. MCP standardises four things over JSON-RPC 2.0: `tools/list` (discovery), `tools/call` (invocation), `resources/*` (data exposure), and `prompts/*` (templated prompts). A server implements those endpoints once; any MCP client — Claude Desktop, Cursor, Claude Code, VS Code Copilot, Windsurf, OpenAI's ChatGPT desktop app, Zed, and the long tail of agent runtimes — can speak to it. The pay-off is real: as of May 2026, PulseMCP lists over 14,000 servers and the SDKs have crossed 97 million cumulative downloads. Build once, invoke from anywhere.

But the cost is also real, and the practitioner backlash through 2025–26 is what makes the pattern interesting rather than obvious. Every connected MCP server contributes its **entire** `tools/list` schema to the client's context window, before the agent has read the user's first message. The GitHub MCP server alone has grown from ~42,000 tokens in early 2025 to ~55,000 tokens across ~93 tool definitions by 2026 — roughly 21% of a 200K-token window paid as a context tax. Four or five servers loaded by reflex, none individually outrageous, will burn 60,000+ tokens before the agent starts work. Anthropic's own Claude Code documentation, GitHub's official server docs, and the September 2025 SEP-1576 proposal ("Mitigating Token Bloat in MCP") all now treat schema overhead as a primary engineering concern. Cursor caps clients at ~40 tools; tool-selection accuracy has been observed to drop from ~43% to ~14% as tool counts climb. The pattern is correct; the failure mode is using it without a token budget. That tension — ecosystem richness against context cost — is what I3 names and forces explicit.

I3 is therefore not "the right answer" because MCP exists. It is the right answer when *credential isolation, multi-client reuse, or process boundaries* justify paying the schema-token cost; and when the agent's V13 Tool Budget has room for that cost. Otherwise its smaller siblings — **I2 Function Call** for an app-local toolset, **I4 CLI Invocation** for zero-schema-overhead — are cheaper. The pattern's unique contribution is the *standardised, shared, discoverable* substrate. The pattern's unique liability is the *schema-token tax* that substrate imposes. Both belong in the design conversation; neither can be assumed.

The cost is not linear in the token count. By mechanism 2, the attention matrix QK^T is O(seq_len²) in compute. Adding 55,000 K vectors from a GitHub MCP schema does not add 55,000 units of cost — it adds 55,000 K vectors that every Q vector in the response must attend over, compounding across every generated token (mechanism 2). Heavy schemas make the model slower at doing *anything*, not just at tasks involving those tools.

## Applicability

Use I3 when:

- 5+ tools must be shared across multiple agents, clients, or developers — the integration cost of doing this per-framework exceeds the schema-token cost of MCP;
- credential isolation matters — the server holds API keys, OAuth tokens, database credentials; the agent's process never sees them;
- tools must run in a different process, language, or trust boundary than the agent — separation is enforced by the protocol;
- a high-quality pre-built server already exists for the integration you need (GitHub, Slack, Postgres, Filesystem, Fetch, Git, Notion, Linear) — taking the ecosystem benefit;
- the agent's V13 Tool Budget has measured headroom for the server's schema cost.

Do not use I3 when:

- 1–5 tools are needed for a single, app-local agent — use **I2 Function Call**; migration to I3 later is cheap, premature adoption is not;
- the tool is high-frequency and a CLI already exists — use **I4 CLI Invocation**; zero schema-token overhead beats standardisation for the hot path;
- the action is fully deterministic and no LLM routing is needed — use **I1 Direct API Call** under code;
- the agent is already at or near its **V13 Tool Budget** ceiling — adding another server breaks tool-selection accuracy;
- the tool would be invoked from exactly one agent and shared by no one — the protocol overhead earns nothing.

## Decision Criteria

I3 is right when standardisation, sharing, or credential isolation justify the schema-token cost — and only then.

**1. Count the clients.** How many distinct agents, frameworks, or processes will invoke these tools?
- 1 — almost certainly **I2** (or **I1** / **I4**); I3 buys you nothing alone.
- 2–3 — borderline; if migration cost from I2 is low and you expect more clients, lean **I3**.
- 4+ — **I3** clearly: per-framework re-integration cost dominates schema cost.

**2. Measure the schema budget.** Run `tools/list` against the candidate server and *count the tokens of the response* in the model's tokenizer.
- < 5,000 tokens — cheap; add freely (a Fetch or Time server).
- 5,000–20,000 tokens — moderate; ensure room remains for the agent's actual context.
- 20,000–55,000 tokens — heavy (GitHub, full Slack); enable only the toolsets used, or use a dynamic-load gateway.
- > 55,000 tokens for one server, or > 60,000 across all loaded servers — over budget; trim by toolset, split into focused servers, or fall back to **I4** for the high-frequency subset.

**3. Hard tool-count ceiling.** Total tools surfaced to the client (across *all* servers).
- ≤ 15 — safe selection accuracy.
- 16–40 — degrading; Cursor's empirical limit is ~40; pair with dynamic injection.
- > 40 — selection accuracy collapses (~43% → ~14% at high counts); **V13 Tool Budget** is now mandatory, not optional.

**4. Credential / trust posture.** Where do the API keys live?
- Acceptable in the agent process → **I2** is fine.
- Must not be reachable by the LLM context or agent code (separation of duties, third-party tool, customer credentials) → **I3** earns its keep; the server holds the secret, the agent only sees the tool name.
- Tool is reachable by adversarial input (untrusted document content, user-pasted prompts) → V3 Lethal Trifecta applies; **I3** must be paired with **V6 Prompt Injection Shield** and **V8 Tool Sandboxing** regardless.

**5. Ecosystem fit.** Does a maintained server already exist (registry.modelcontextprotocol.io, modelcontextprotocol/servers, github/github-mcp-server, vendor-maintained)?
- Yes — large pay-off; you inherit a tested integration, updates, and community fixes.
- No — you are *building* an MCP server, which is more work than an I2 tool; only justified if multi-client use is real.

**Quick test — I3 is the right pattern when:**

- 2+ clients (agents, IDEs, runtimes) will use the same tools, *and*
- credential isolation or process separation is a stated requirement, *and*
- measured `tools/list` token cost fits within the V13 Tool Budget for the target agent, *and*
- total tool count across all loaded servers stays at or below the selection-accuracy ceiling (~40 tools).

If any condition fails, drop to a smaller sibling. Single client → **I2 Function Call**. CLI exists for the hot tool → **I4 CLI Invocation**. Deterministic action with no routing needed → **I1 Direct API Call**. Over schema budget but truly need MCP → adopt a tool-search subagent / gateway (Claude Code's tools-via-search mode is the canonical implementation, ~47% reported reduction), split into focused servers, or allow-list a subset of toolsets.

## Structure

```
   ┌──────────────────────────────────────────────┐
   │ Agent process (MCP Client embedded)          │
   │                                              │
   │   on startup:                                │
   │     for each configured server:              │
   │        tools/list ─┐                         │
   │                    │ schemas merged          │
   │                    ▼ into agent's tool set   │
   │     (V13 Tool Budget enforced here)          │
   │                                              │
   │   at invocation:                             │
   │     LLM picks tool ──▶ tools/call ──┐        │
   └────────────────────────────────────│┼────────┘
                                        │
              JSON-RPC 2.0 over stdio / SSE / streamable HTTP
                                        │
   ┌────────────────────────────────────▼────────┐
   │ MCP Server (separate process / remote URL)  │
   │                                             │
   │   tools/list  ──▶ schema catalogue          │
   │   tools/call  ──▶ Auth Manager (creds here) │
   │                 ──▶ Tool Executor (I1 calls │
   │                     external API / DB / FS) │
   │                 ──▶ structured result        │
   │   resources/* (optional: file-like data)    │
   │   prompts/*   (optional: templated prompts) │
   └─────────────────────────────────────────────┘
```

The credential boundary is the dashed line: secrets live inside the server, never crossing back into the agent's context.

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **MCP Server** | implementing the protocol endpoints (`tools/list`, `tools/call`, optional `resources/*`, `prompts/*`) for one logical tool group | JSON-RPC request → JSON-RPC response | leak credentials into responses, return raw transport noise to the agent, or stuff dozens of unrelated tools into one server. One server, one bounded surface area. |
| **MCP Client** | protocol implementation inside the agent framework — connecting to configured servers, merging discovered tools, routing `tools/call` | server URL/command + LLM-chosen tool call → executed result | silently load every tool from every server; this is where **V13 Tool Budget** is enforced before the schemas hit the model context. |
| **Tool Registry / Discovery** | the `tools/list` endpoint — the catalogue the client reads at startup (and re-reads on dynamic refresh) | client request → list of schemas | grow without an owner. Each schema is paid for in tokens on every session; an un-pruned registry is the schema-bloat failure mode in person. |
| **Auth Manager** | credential storage and per-call authentication inside the server | tool invocation → authenticated outbound call | expose credentials in error messages, in `tools/list` descriptions, or anywhere reachable by the agent's context. The agent must never see a secret. |
| **Tool Executor** | the actual outbound work — HTTP, SDK, filesystem, database call | validated parameters → raw external result | embed routing logic ("if user said X then ..."); routing happens in the LLM upstream, not in the executor. The executor is I1 internally. |
| **Result Shaper** | turning raw external results into the structured response the protocol defines | raw result → typed protocol response | leak transport envelopes, debug fields, or unbounded payloads back into the agent's context; the result will be read by the model and counts against its budget. |
| **Tool Budget Policy** *(at client)* | per-agent cap on schema tokens and tool count; selects toolsets, enables dynamic loading, gates over-budget servers | available servers + agent role → loaded subset | be set by gut feel. Thresholds come from **V13 Tool Budget** measurements, not optimism. |

Seven narrow responsibilities split across two processes. The split is the point: the *server* owns credentials, execution, and the external surface; the *client* owns budget enforcement and routing. Confusing the two — e.g. an agent that holds the credential because "it's easier" — collapses the credential-isolation benefit that justifies the pattern.

## Collaborations

At deploy time, the operator configures one or more MCP servers for the agent — by command (stdio transport for a local process), or URL (SSE or streamable-HTTP for remote). At agent startup the MCP Client connects to each server and calls `tools/list`; the returned schemas are merged into the agent's tool catalogue. The **Tool Budget Policy** runs here, *before* the schemas reach the model: it counts schemas, sums tokens, and either passes (within budget), prunes (selects a subset of tools or toolsets), or refuses (over the hard cap). This is the V13 enforcement point.

When the user query arrives, the LLM sees the merged tool catalogue and picks a tool — exactly as in I2; the protocol does not change the LLM's reasoning, only the discovery upstream of it. The Client routes the chosen `tools/call` to the right server over JSON-RPC. Inside the server, the Auth Manager attaches credentials, the Tool Executor performs the outbound work (an I1 call), and the Result Shaper returns a structured response. The Client surfaces the result back into the agent's context for continued reasoning.

I3 typically composes with **V13 Tool Budget** as a hard prerequisite, **V6 Prompt Injection Shield** when any tool reads adversarial content (third-party documents, web pages, issues), **V8 Tool Sandboxing** for any tool that can execute code, and **V3 Lethal Trifecta** as the audit lens applied to *every* added server — a server with read access to private data, write access to outbound channels, and exposure to untrusted input is the canonical exfiltration risk. For high-frequency hot-path tools, **I4 CLI Invocation** sits alongside I3, taking the zero-schema-overhead path; many production agents deliberately run a slim MCP set for shared, credentialed tools plus a CLI for the rest.

## Consequences

**Benefits**
- One protocol, many clients — build a server once; reuse from Claude Desktop, Cursor, Claude Code, VS Code, Windsurf, ChatGPT desktop, and any compliant runtime.
- Credential isolation — secrets stay in the server process; the agent never holds them.
- Process separation — tools can run in different languages, on different hosts, under different trust boundaries.
- Ecosystem leverage — 14,000+ public servers as of mid-2026; pre-built integrations for the long tail of SaaS / dev tools / data stores.
- Discoverability — `tools/list` is a uniform discovery API; tool changes are versioned and inspectable.
- Standardised resources and prompts — beyond tools, `resources/*` and `prompts/*` give the protocol reach into data exposure and templated prompting.

**Costs**
- Schema-token tax — every connected server contributes its full `tools/list` to context; GitHub MCP alone is ~55,000 tokens by 2026.
- Selection accuracy degradation — tool counts above ~15 erode the LLM's tool-selection precision; above ~40 it collapses (~43% → ~14% measured).
- Operational surface — server process management, transport choice (stdio vs SSE vs streamable HTTP), health, restarts.
- Latency floor — a stdio or HTTP round-trip per call; not appropriate for sub-10ms hot paths (use **I1**).
- Supply-chain exposure — every added server is code in the trust boundary; a malicious or compromised server with full credential access is the supply-chain failure mode.

**Risks and failure modes**
- *Schema bloat by reflex* — operators add five servers because they all look useful; 60,000+ tokens of schema land in context; the agent's working room collapses before the user types.
- *Tool-selection collapse* — tool count crosses the accuracy cliff; the agent picks confidently wrong tools; failures look like model regression but are tooling decisions.
- *Credential leak via descriptions / errors* — a server includes secret material in tool descriptions, error messages, or example values; the agent's context now contains the secret.
- *Lethal Trifecta via composition* — Server A reads private data; Server B writes outbound; Server C ingests untrusted input. Each is fine alone; together they are an exfiltration pipeline. **V3** must be applied across the *combined* server set, not per-server.
- *Stale or vendored schemas* — the server changed but cached schemas in the client did not; calls fail with mysterious type errors. Re-run `tools/list` on connection; surface schema versions.
- *Reflexive use over I4* — high-frequency operation on a tool that has a CLI is wrapped in MCP for "consistency"; the agent burns 35× more tokens per call than the CLI equivalent.

## Implementation Notes

- **Measure schema cost before adding.** Run `tools/list` against the candidate server; tokenise the response in the target model's tokenizer; record the number in the agent's V13 budget. An unmeasured server is an unowned cost.
- **Prefer focused servers over kitchen-sink servers.** Five small servers, each with one toolset, are easier to budget, easier to remove, and easier to audit than one large server with five toolsets.
- **Enable only the toolsets you use.** Most large servers (GitHub, Linear, Slack) ship toolset flags or filters; turning off unused toolsets is the cheapest schema reduction.
- **Use dynamic tool injection where possible.** Don't load all tools at startup; load the subset relevant to the current task. Claude Code's tool-search subagent is the canonical implementation; reported ~47% reduction.
- **Drop to I4 for hot paths.** A frequently-called tool that has a CLI (`gh`, `git`, `kubectl`, `aws`, `gcloud`, `jq`, `rg`) should run as I4 even when an MCP equivalent exists. Reserve I3 for the cases where standardisation pays.
- **Audit every new server for V3 Lethal Trifecta** — across the combined loaded set, not per-server in isolation.
- **Pin server versions.** A silent server update can rewrite the schema and break selection accuracy without a code change in the agent.
- **Prefer official / vendor-maintained over community where credentials matter.** github/github-mcp-server (official), Anthropic's reference servers, vendor MCP servers — all are higher-assurance than random community implementations for high-privilege roles.
- **Treat the server as code in your trust boundary.** Review it, watch its CVEs, and isolate its credentials at the OS level (separate user, separate vault).
- **Choose transport deliberately.** Stdio for local same-host servers (lowest latency, simplest); SSE / streamable HTTP for remote (network reliability, auth required).
- **Pair with V13 always.** I3 without V13 enforcement is the documented failure mode in person.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** I3 plugs into the agent's tool-use loop exactly where **I2 Function Call** does — the LLM still chooses a tool by name and parameters, the difference is *where the schemas came from* (a remote `tools/list`) and *where the call goes* (a JSON-RPC `tools/call`). The pattern composes hard with **V13 Tool Budget** (enforces schema/tool caps), **V8 Tool Sandboxing** (for code-executing tools), **V6 Prompt Injection Shield** (for tools that read untrusted content), and **V3 Lethal Trifecta** (audit across the combined server set). The execution step inside the server is **I1 Direct API Call**. For high-frequency hot tools, **I4 CLI Invocation** runs alongside, taking the schema-free path. The agent's tool-use LLM call is itself shaped by Signal-layer setup (**S3 Persona**, **S5 Constraint Framing**, **S6 Output Template**).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Connect to each configured MCP server; call `tools/list` | `code` | MCP client lib |
| 2 | Enforce V13: count schemas/tokens; prune toolsets or refuse over-budget servers | `code` | V13 Tool Budget |
| 3 | Merge surviving schemas into the agent's tool catalogue | `code` | — |
| 4 | LLM reads user query + tool catalogue; selects a tool and parameters | `LLM` | Agent session (I2 mechanics) |
| 5 | Route selected `tools/call` over JSON-RPC to the right server | `code` | MCP client lib |
| 6 | Server: authenticate, execute (an I1 internally), shape result | `code` | I1, Auth Manager |
| 7 | Return structured result into the agent's context | `code` | V11 if error compaction needed |
| 8 | LLM continues reasoning with the result | `LLM` | Agent session |

**Skeleton** — wiring only; the `# LLM` markers are the only steps the model does:

```
agent_with_mcp(query, servers):
    catalogue = []
    for s in servers:                                  # code
        schemas = mcp_client.list_tools(s)             # code — tools/list
        catalogue += v13_budget.admit(schemas, s)      # code — V13 prune / refuse
    while not done:
        action = Agent(query, catalogue)               # LLM — I2-style routing
        if action.kind == "tool_call":
            server = locate(action.tool, servers)      # code
            result = mcp_client.call(                  # code — tools/call (JSON-RPC)
                server, action.tool, action.params)    #   server-side: auth + I1 + shape
            query = inject_result(query, result)       # code
        else:
            return action.answer                       # LLM produced final answer
```

The skeleton inside the server (single-tool view), entirely code:

```
mcp_server.handle_tools_call(name, params):
    validate(params, schema_for(name))                 # code — V5 pre-call guard
    creds = auth_manager.get(name)                     # code — never returned to agent
    raw  = tool_executors[name](params, creds)         # code — I1 outbound
    return shape(raw)                                   # code — strip transport noise
```

**The LLM sessions.** I3 introduces no new LLM session over I2 — the model is doing tool-selection reasoning, not protocol work. The protocol is entirely code. The agent's *one* LLM session is the same Agent session I2 would use:

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | the system's main generalist with tool-use support | role (S3); tool-use rules (S5: when to call, when to answer directly); citation / formatting contract (S6); the *merged tool catalogue* from step 3 — this is where the schema-token cost lands | the user query + accumulated tool results so far |
| **Tool-search subagent** *(optional, recommended when total tools > 15)* | small fast generalist | role: *"given the user's request, return the names of the 3–10 most relevant tools from this catalogue"*; the full catalogue as setup | the user query |

The optional second session — a tool-search subagent — is the canonical mitigation for schema bloat: keep the full catalogue out of the main Agent's context; let a small fast model pre-select the relevant subset and load only those into the Agent's tool field. Claude Code's measured ~47% token reduction comes from exactly this move. This is an instance of mechanism 6 (subagent decomposition as context bounding): each spawned agent has its own seq_len, bounding the n² attention cost per agent. The main agent operates on a small relevant subset; the subagent operates on the full catalogue. Additionally, the full catalogue is always the stable prefix of the subagent session — a canonical prefix-cache target (mechanism 5): catalogue K-states can be pre-computed and reused across calls at ~10% of normal prefill cost.

**Specialist-model note.** No fine-tuned specialist is required for I3 itself — the protocol is plumbing. Two implementation dependencies do matter as build-time choices: (1) the **MCP SDK** for the agent's language (Python: `modelcontextprotocol/python-sdk`; TypeScript: `modelcontextprotocol/typescript-sdk`; official SDKs also exist for Java, Kotlin, C#) — this is the client-side wiring you do not write yourself; (2) for the V13 mitigation, a **small fast generalist** as the tool-search subagent (Haiku-class, Sonnet-class small, or any sub-1B specialist classifier fine-tuned for tool routing) — capable generalist suffices, no fine-tune required. This is mechanism 8: tool routing is a classification task that does not require large model capacity. A smaller model runs a fraction of the inference cost and latency of a frontier model for the same routing quality.

## Open-Source Implementations

- **MCP specification** — [`github.com/modelcontextprotocol/modelcontextprotocol`](https://github.com/modelcontextprotocol/modelcontextprotocol) — the canonical specification and documentation repository; donated to the Linux Foundation's Agentic AI Foundation in December 2025.
- **Python SDK** — [`github.com/modelcontextprotocol/python-sdk`](https://github.com/modelcontextprotocol/python-sdk) — official Python SDK for MCP servers and clients.
- **TypeScript SDK** — [`github.com/modelcontextprotocol/typescript-sdk`](https://github.com/modelcontextprotocol/typescript-sdk) — official TypeScript SDK for MCP servers and clients.
- **Reference servers** — [`github.com/modelcontextprotocol/servers`](https://github.com/modelcontextprotocol/servers) — the maintained reference set: Everything (test server), Fetch, Filesystem, Git, Memory, Sequential Thinking, Time. Educational examples, not production-targeted.
- **MCP Registry** — [`registry.modelcontextprotocol.io`](https://registry.modelcontextprotocol.io) — the official discovery catalogue; the published server registry, with API access via [`github.com/modelcontextprotocol/registry`](https://github.com/modelcontextprotocol/registry).
- **GitHub MCP Server** — [`github.com/github/github-mcp-server`](https://github.com/github/github-mcp-server) — GitHub's official MCP server; the canonical *heavy* server (40,000–55,000 tokens), with toolset flags for partial loading.
- **Archived first-party servers** — [`github.com/modelcontextprotocol/servers-archived`](https://github.com/modelcontextprotocol/servers-archived) — 13 servers (Slack, Postgres, Google Drive, Brave Search, Sentry, SQLite, Puppeteer, EverArt, AWS-KB, Redis, Google Maps, GitLab, plus one more) that moved from Anthropic stewardship to vendor maintenance in 2025; useful as historical references.

## Known Uses

- **Claude Desktop and Claude Code** (Anthropic) — the first major MCP host; ships with built-in MCP client support; the "tool-search subagent" mitigation for schema bloat originated here.
- **OpenAI ChatGPT desktop app** — adopted MCP officially in March 2025; the protocol crossed the original-provider boundary, confirming standardisation.
- **Cursor, Windsurf, VS Code 1.101+ with Copilot, JetBrains IDEs, Xcode, Zed** — broad IDE adoption; ~40-tool empirical limit traces to Cursor's measurements.
- **GitHub Copilot** — uses the official GitHub MCP server as the canonical context provider for repo / issue / PR operations.
- **Enterprise agent deployments** — credential isolation and process separation are the cited drivers for moving from per-framework tool integrations to MCP across the second half of 2025 into 2026.
- **PulseMCP and the open registry** — over 14,000 listed servers as of May 2026; MCP SDKs have crossed 97M cumulative downloads, indicating real production usage well beyond a few flagship clients.

## Related Patterns

- **Refines** I2 Function Call — I3 keeps I2's "LLM chooses, code executes" reasoning loop and lifts *where the tool schemas come from* out of the agent into a shared protocol.
- **Wraps** I1 Direct API Call — every `tools/call` ultimately executes as an I1 inside the server.
- **Sibling of** I4 CLI Invocation — same goal (give the LLM an external action), opposite trade-off on schema overhead. Production agents commonly run both: I3 for shared credentialed tools, I4 for the hot path.
- **Composes with** I5 Agent Card — Agent Cards are agent-level discovery; MCP is tool-level discovery; an agent may serve both, at different granularities.
- **Required by** V13 Tool Budget — I3 without V13 enforcement is the documented failure mode (schema bloat → tool-selection collapse). See **CRITICAL 6**.
- **Pairs with** V6 Prompt Injection Shield — any MCP tool that reads adversarial content (third-party documents, web pages, issues, emails) widens the attack surface; V6 is the mitigation.
- **Pairs with** V8 Tool Sandboxing — for any MCP server whose tools execute code or touch a privileged surface, V8 is the runtime control.
- **Pairs with** V3 Lethal Trifecta — the audit lens applied *across the combined set of loaded servers*, not per-server.
- **Pairs with** V14 Trajectory Logging — every `tools/call` must appear in the trace, or audit breaks.
- **Pairs with** R4 ReAct and R13 CodeAct — both reasoning patterns invoke tools; when the tool inventory is MCP-served, R4 / R13 sit on top of I3.

## Sources

- Anthropic (2024) — *Introducing the Model Context Protocol* — the original specification announcement (November 2024); [`modelcontextprotocol.io`](https://modelcontextprotocol.io).
- MCP Specification, current release — [`modelcontextprotocol.io/specification/2025-11-25`](https://modelcontextprotocol.io/specification/2025-11-25) — the November 2025 spec; 2026-07-28 release candidate covers stateless protocol core, Extensions framework, Tasks, MCP Apps, authorisation hardening.
- Anthropic (December 2025) — *Donating the Model Context Protocol and Establishing the Agentic AI Foundation* — MCP donated to Linux Foundation directed fund.
- *The 2026 MCP Roadmap* — official blog post on the MCP blog ([`blog.modelcontextprotocol.io`](https://blog.modelcontextprotocol.io/)).
- SEP-1576 — *Mitigating Token Bloat in MCP: Reducing Schema Redundancy and Optimizing Tool Selection* — modelcontextprotocol/modelcontextprotocol issue #1576 (September 2025); the canonical articulation of the schema-cost problem from inside the project.
- GitHub Blog (2025) — *Improving token efficiency in GitHub Agentic Workflows* — the official GitHub take on schema cost in their own server.
- *GitHub MCP Token Cost: A 2026 Autopsy and 4 Fixes* — practitioner analysis tracking the 42K → 55K growth and the mitigation ladder (tool-search subagent, allow-listing, CLI fallback, retrieval-out-of-loop).
- *MCP Token Trap: Why Your AI Agent Burns 35× More Tokens Than a CLI* — OnlyCLI benchmark comparing MCP vs CLI per-operation cost.
- HN community discussions on MCP vs API and MCP vs LangChain (2024–25 threads) — the practitioner backlash and consensus.
- Composio *AI Agent Report 2025* — MCP adoption data.
- Wikipedia — *Model Context Protocol* — for adoption timeline (OpenAI March 2025, Linux Foundation December 2025) cross-reference.
