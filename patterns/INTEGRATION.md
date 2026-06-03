# Category VI — Integration Patterns

An **Integration pattern** is a design pattern for how a language model reaches the world outside its prompt — the wiring through which an LLM, or a system of LLMs, invokes tools, calls services, discovers other agents, and delegates work to them. Integration patterns separate *what the model decides* from *how that decision is enacted* on real systems.

## Usage

A model in isolation can only emit tokens. Every consequential agent system must, at some point, leave the prompt: read a database, search a corpus, call an API, run a shell command, hand a sub-task to another agent. The shape of that wiring is not incidental — it determines latency, cost, security posture, debuggability, and which capabilities can be reused. Integration patterns make those decisions explicit, the way Category II makes context decisions explicit and Category IV makes coordination decisions explicit.

The dominant industry shift through 2024–26 was the arrival of standardised protocols at two layers: **MCP** (Model Context Protocol, Anthropic, November 2024) for tool wiring, and **A2A** (Agent-to-Agent, donated by Google to the Linux Foundation in June 2025; the IBM/Red Hat ACP variant merged into A2A under the LF in August/September 2025) for inter-agent delegation. Both sit under the Linux Foundation's **Agentic AI Foundation (AAIF)**, the LF directed fund that also anchors AGENTS.md and Goose. Apply an Integration pattern whenever:

- code (not the LLM) should decide which call to make and how;
- the LLM must select a tool from a typed catalogue and invoke it with structured parameters;
- tools are reused across multiple agents, codebases, or organisations;
- existing CLI tools already encode the capability the agent needs;
- agents from different systems must discover each other and delegate work.

## Forces

Every Integration pattern resolves the same three forces in tension. A pattern is right for a situation when it balances them in the way that situation demands.

1. **Routing has a cost, and it is not free.** Letting the LLM choose a tool adds latency, non-determinism, and tokens. The non-determinism is structural: token generation is stochastic sampling from a learned probability distribution (mechanism 7), which is not eliminable by configuration. The token cost compounds via O(n²) attention scaling (mechanism 2), not linearly — each schema token that enters the context pays a pairwise cost against every other token in the session, not just a flat per-token fee. Tool schemas eat context: a single MCP server like GitHub's now occupies ~40,000–55,000 tokens before the agent has done anything; four or five reflex-loaded servers exceed 60,000 tokens of pure schema overhead. Tool-selection accuracy degrades sharply as catalogues grow — empirically from ~43% to ~14% at high tool counts.

2. **The capability the agent needs already exists somewhere outside the model.** It is an HTTP endpoint, a database, a CLI binary battle-tested for decades, an MCP server published by a vendor, or another agent reachable over the network. Reaching it cleanly — without rewriting it as a function or duplicating it per framework — is the whole point.

3. **Reuse and trust pull in opposite directions.** Standardising tool wiring (MCP) and agent wiring (A2A) makes capabilities composable across teams and vendors; the same standardisation widens the supply-chain attack surface, complicates credential isolation, and turns every added server into a Lethal Trifecta (V3) audit problem.

An Integration pattern is, in each case, a disciplined answer to one question: where does the boundary between LLM reasoning and code execution sit, and what protocol carries the call across it?

## Structure

All Integration patterns share one skeleton. They interpose a **routing decision** between the LLM's reasoning and the external capability:

```
  LLM reasoning ───▶ Routing ───▶ Invocation ───▶ External system ───▶ Result
  (or none —        (code,        (HTTP, JSON-     (API, DB, CLI,          │
   for I1)           function     RPC, subprocess,  MCP server,            │
                     schema,      A2A protocol)     other agent)           │
                     Agent Card)                                            │
         ◀──────────────────────────────────────────────────────────────────┘
         result → KV cache extension (mechanism 3: seq_len grows here;
                  compact results before re-entry to bound O(n²) cost)
```

Patterns differ in *who routes* — code alone (I1), the LLM choosing from a static catalogue (I2), the LLM choosing from a discovered catalogue (I3/I4), or an orchestrator choosing among discovered agents (I5/I6) — and in *what crosses the boundary* — an HTTP call, a typed function invocation, a JSON-RPC tools/call message, a subprocess argv, or an A2A task. The three bands below group the patterns by the boundary they cross: in-agent tool calling (VI-A), standardised tool protocols (VI-B), and inter-agent discovery and delegation (VI-C). They are stages of scale rather than alternatives: a production system typically uses I1 for deterministic ops, I2 or I3 for LLM-routed tools, I4 for shell capability, and I5+I6 once it must talk to agents it does not own.

## Examples

**VI-A — In-agent tool calling.** The LLM (or no LLM) routes within its own deployment.
- **I1 Direct API Call** — code routes deterministically; no LLM in the call path.
- **I2 Function / Tool Call** — LLM selects from a JSON Schema catalogue defined in-agent.

**VI-B — Standardised tool protocols.** The catalogue is discovered over a protocol, not hard-coded.
- **I3 MCP Server** — tools published as MCP servers; discovered, authenticated, and invoked over JSON-RPC; the schema-cost ↔ ecosystem-richness tradeoff (CRITICAL 6 with V13).
- **I4 CLI Invocation** — agent shells out to existing CLI binaries; zero schema tokens; the Unix-philosophy counterpart to I3.

**VI-C — Inter-agent discovery and delegation.** The boundary is between whole agents, not between an agent and a tool.
- **I5 Agent Card** — each agent publishes a machine-readable manifest at `/.well-known/agent-card.json`; the discovery layer for A2A.
- **I6 A2A Delegation** — structured task delegation across system / vendor / organisation boundaries using the unified A2A protocol (post-ACP merger).

## See also

- **Category II — Knowledge patterns** — Integration brings external *capabilities* into the loop; Knowledge brings external *information* into the context.
- **Category III — Reasoning patterns** — R4 ReAct and R13 CodeAct are reasoning patterns built directly on top of I2/I3/I4; the reasoning loop and the tool loop are the same loop.
- **Category IV — Orchestration patterns** — O6 Orchestrator-Workers and O15 Agent Handoff are the in-system counterparts of I6's cross-system delegation; I5 is how O6 discovers workers it doesn't own.
- **Category V — Reliability patterns** — V13 Tool Budget, V8 Tool Sandboxing, V6 Prompt Injection Shield, and V3 Rule of Two all attach directly to the integration layer; CRITICAL 6 (`CONFLICTS.md`) names the I3 ↔ V13 tradeoff as the defining cost question of the category.

*Both protocol layers — MCP and A2A — sit under the Linux Foundation's **Agentic AI Foundation (AAIF)**, the LF directed fund that anchors MCP, AGENTS.md, and Goose, with A2A as a sibling LF project under the same umbrella.*

## Decision aid

The integration decision flowchart:

```
Does LLM reasoning determine the action?
  NO  → I1 (Direct API Call)
  YES → How many tools, and shared with anyone?
          1–15, single agent              → I2 (Function Call)
          existing CLI for this           → I4 (CLI Invocation) — zero schema cost
          5+ tools, shared multi-agent    → I3 (MCP Server) — measure schema cost first
          20+ tools                       → I3 with gateway + dynamic tool discovery

Are agents from different systems coordinating?
  Discovery only      → I5 (Agent Card)
  Task delegation     → I6 (A2A Delegation), using I5 for discovery first
```

The headline cost number: GitHub MCP occupies ~40,000–55,000 tokens of schema in a single client; four or five reflex-loaded MCP servers consume 60,000+ tokens before the agent has done anything. This is why CRITICAL 6 (`CONFLICTS.md`) pairs I3 directly with V13 Tool Budget. The empirical threshold (~15 tools safe, ~40 ceiling) has a mechanistic basis: similar tool descriptions occupy nearby K-vector regions in the attention bilinear form (mechanism 1), making the Q-K inner products for routing ambiguous as the catalogue grows. Beyond the ceiling, the signal that should select the right tool is lost in the noise of near-identical similarity scores. Schema tokens loaded for unused tools are also not idle — they sit in the KV cache (mechanism 3) and are attended over on every generation step, unlike human working memory which can set something aside.

---

## Quick Reference

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| I1 | **Direct API** | Deterministic Call | Synchronous HTTP; no LLM reasoning | Sub-10ms ops; consistency-critical |
| I2 | **Function/Tool Call** | Schema-Wrapped API | LLM selects and invokes typed function | 1–5 tools; app-specific routing |
| I3 | **MCP Server** | Model Context Protocol | Standardised tool discovery; credential isolation | 5+ tools shared across agents |
| I4 | **CLI Invocation** | Shell Tool | Agent uses existing CLI directly | Tools with existing CLIs (git, docker, gh) |
| I5 | **Agent Card** | Agent Manifest | Self-describing JSON for agent discovery | Multi-agent; A2A interoperability |
| I6 | **A2A Delegation** | Agent-to-Agent | Structured cross-agent task delegation | Multi-vendor agent collaboration |

---

## I1 — Direct API Call

Call an external service directly from code without LLM routing — deterministically, synchronously, with full programmatic control over parameters, retries, and error handling. The LLM, if present, sits upstream of the call (deciding *what* to do) rather than inside it. The right pattern when the action is fully determined by code logic and the latency, cost, or determinism of an LLM in the call path is unjustified — financial transactions, structured database writes, sub-10ms operations, anything with audit and compliance requirements.

**Full entry:** [`I1-Direct-API.md`](I1-Direct-API.md)

---

## I2 — Function / Tool Call

Describe external capabilities as typed, JSON-Schema-wrapped functions; let the LLM pick which one to invoke and with what parameters; have code execute the actual call. The standard pattern for enabling LLM agents to act, native to every major model API (OpenAI function calling, Anthropic tool use, Gemini function declarations). The LLM's role is exclusively routing and parameter extraction — execution is I1 underneath. Best for 1–15 tools owned by a single agent; selection accuracy degrades sharply past that.

**Full entry:** [`I2-Function-Call.md`](I2-Function-Call.md)

---

## I3 — MCP Server

Deploy tools as standardised, discoverable Model Context Protocol servers — JSON-RPC 2.0 over stdio, SSE, or HTTP — so any compliant client can discover, authenticate, and invoke them without per-framework integration. Pays the **schema-cost ↔ ecosystem-richness** tradeoff explicitly: every connected server contributes its full `tools/list` schema to the context window before the agent has read the user's first message (GitHub MCP alone occupies ~40,000–55,000 tokens by 2026), so V13 Tool Budget becomes a hard constraint rather than a guideline. This is the defining cost tension of the category — CRITICAL 6 in `CONFLICTS.md` — and the reason the SEP-1576 proposal ("Mitigating Token Bloat in MCP") exists.

**Full entry:** [`I3-MCP-Server.md`](I3-MCP-Server.md)

---

## I4 — CLI Invocation

Have the agent invoke existing command-line tools directly — `git`, `docker`, `kubectl`, `gh`, `rg`, `jq`, `aws`, `gcloud` — as its primary integration mechanism, leveraging tools already documented in the model's training data without wrapping them in JSON Schema. Zero schema-token overhead; access to the entire Unix/Linux ecosystem; unstructured text output the agent must parse. Requires V8 Tool Sandboxing and careful argument handling — `subprocess(shell=True, args=llm_output)` is a direct shell injection. The Claude Code architecture is built on this pattern.

**Full entry:** [`I4-CLI-Invocation.md`](I4-CLI-Invocation.md)

---

## I5 — Agent Card

Publish a standardised, machine-readable description of an agent's identity, skills, endpoints, and authentication at the well-known URL `/.well-known/agent-card.json`, so other agents and orchestrators can discover and verify it without out-of-band configuration. The discovery layer that A2A delegation (I6) reads before invoking. Modelled on IETF RFC 8615 (the `/.well-known/` URI convention) and analogous to DNS: identity resolution without per-relationship setup. Architecturally sound, ecosystem adoption still emerging through 2026.

**Full entry:** [`I5-Agent-Card.md`](I5-Agent-Card.md)

---

## I6 — A2A Delegation

Delegate a task from one agent to another across a system, vendor, or organisational boundary using the unified A2A wire protocol — task submission, streaming status updates (SSE or polling), structured result, defined cancellation semantics. A2A was announced by Google in April 2025 and donated to the Linux Foundation in June 2025; the IBM/Red Hat ACP variant **merged into A2A under the LF in August/September 2025**, so A2A is now the single live standard and ACP is a historical-only variant. The decentralised W3C-DID alternative (ANP) targets open agent networks where no central authority should mediate trust.

**Full entry:** [`I6-A2A-Delegation.md`](I6-A2A-Delegation.md)

---

## Notes on naming and provenance

- **Agent Card path.** The current canonical well-known URL is `/.well-known/agent-card.json`. Older A2A drafts used `/.well-known/agent.json`; that path is deprecated and should not be relied upon in new implementations.
- **AAIF.** "AAIF" in this category always refers to the Linux Foundation's **Agentic AI Foundation** — the LF directed fund that anchors MCP, AGENTS.md, and Goose, with A2A as a sibling LF project under the same umbrella. It is not the "Agentic AI Interoperability Framework" — that expansion appeared in some 2025 drafts and is incorrect.
- **ACP → A2A.** The IBM/Red Hat Agent Communication Protocol was a competing variant in early 2025; it **merged into A2A under the Linux Foundation in August/September 2025**. New deployments target A2A; ACP is listed only for historical context.

*Common integration anti-patterns: MCP-first without cost analysis, `shell=True` with LLM output, I2 overloading past V13, undiscovered agent dependencies, delegate-and-forget. The defining cost tension of the category — I3 ↔ V13 — is Appendix A (Conflicts) CRITICAL 6.*
