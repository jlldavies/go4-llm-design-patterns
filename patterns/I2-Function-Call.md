# I2 — Function / Tool Call

> Describe external capabilities as typed, schema-described functions; let the LLM pick which one to invoke and with what parameters; have code execute the actual call and return the result back into the model's context.

**Also Known As:** Tool Use (Anthropic), Function Calling (OpenAI / Gemini), Schema-Wrapped Tool Call, Structured Action Output. (The OpenAI / Anthropic / Gemini variants differ only in protocol surface — see Variants.)

**Classification:** Category VI — Integration · the *LLM-routed* baseline of the category — a thin schema layer that turns an I1 Direct API Call into an LLM-chosen invocation; the entry point for any agent that needs natural-language routing to 1–5 tools.

---

## Intent

Make external actions LLM-routable without giving up typed execution: the LLM reads tool descriptions and picks one with structured arguments; code validates and executes it; the result flows back into the model's context so reasoning continues.

## Motivation

When an agent has more than one possible action and the choice depends on interpreting the user's intent, something has to do that interpretation. Hard-coding the routing in code forces the developer to anticipate every phrasing — a losing game once the surface area grows past a couple of tools. Doing the routing inside the prose of the prompt ("ask me to search if you need to search") leaves the model emitting free-form text that another layer has to parse, which is exactly the place where format drift, hallucinated arguments, and silent malformed calls live.

I2 resolves this by giving the routing decision a *typed surface*. Each tool is described once as a JSON Schema — name, parameters, types, semantics in the description field. The LLM sees the schemas, the user request, and the conversation; it emits a structured `tool_call` object naming one of those tools and supplying parameters that conform to the schema. The application validates the call against the same schema, executes it as plain code (an I1 internally), and returns the result back into the LLM's context as a `tool_result` so the model can reason over what it got. The LLM's contribution is exclusively *routing and argument extraction*; the execution is deterministic. The schema is the contract that keeps both sides honest.

The pattern's unique contribution is that the *contract is the API*. There is no separate parser, no regex over free-form output, no "tool-call interpreter" — providers (OpenAI, Anthropic, Gemini) bake the JSON Schema dispatch into the model API itself, and most enforce schema conformance at decoding time (OpenAI `strict: true`, Anthropic `strict`). That removes the most common failure mode of doing this by hand — malformed arguments — and reduces the integration to: describe the tools once, run a small dispatcher, execute. Brown et al. (2020) framed the original idea; OpenAI's June 2023 function-calling release made it a first-class API primitive; Anthropic tool use (2024) and Gemini function calling (2024) standardised it across the major providers. It is now the default way to give an agent 1–5 tools.

## Variants

The variants differ only in *protocol surface and dispatch semantics*. The pattern — schema-described tools, LLM-chosen invocation, code-executed call, structured result back — is identical:

- **OpenAI Function Calling.** Tools declared on the request as `tools=[{type: "function", function: {name, description, parameters}}]`; the model returns `tool_calls[]` with `name` and JSON-encoded `arguments`. `strict: true` constrains decoding to the schema. The earliest mainstream implementation (June 2023).
- **Anthropic Tool Use.** Tools declared as `tools=[{name, description, input_schema}]`; the model returns content blocks of type `tool_use` with `input` already parsed as an object. Supports `cache_control` per tool (for prefix caching of large tool lists) and an optional `strict` flag.
- **Gemini Function Calling.** Tools declared as `tools=[{functionDeclarations: [...]}]`; the model returns `functionCall` parts with `name` and `args`. Supports parallel and compositional function calling out of the box.

All three are the same pattern. Differences are surface — JSON shape, where the schema lives, whether arguments arrive pre-parsed — and tooling layers (Vercel AI SDK, Instructor, LangChain `bind_tools`) abstract over them so the agent code does not need to care which provider is underneath.

## Applicability

Use I2 when:

- the choice of *which* action to take depends on interpreting natural-language input, and that interpretation is what the LLM is good at;
- the agent has roughly **1–15 tools** (see V13 Tool Budget) — small enough that every schema can sit in the prompt without crowding it out;
- the tool set is **application-specific** and stable at deploy time (not shared across many agents or clients);
- the model provider already supports function / tool calling natively — no need to invent a parsing layer;
- you want typed arguments at the seam, not free-form text that needs post-hoc validation.

Do not use I2 when:

- the action is fully determined by code and no LLM judgment is needed → use **I1 Direct API Call** (and remember I2's execution step *is* I1 internally);
- the tool set is large (> ~15) or must be **shared across multiple agents or clients** → use **I3 MCP Server** (often I3 + I2 hybrid: MCP for discovery, function-call surface for invocation);
- the tool already has a **battle-tested CLI** and you want zero schema-token overhead → use **I4 CLI Invocation**;
- the agent's action selection needs to interleave with reasoning over tool *outputs* turn by turn — I2 is the *substrate* for that, but the reasoning loop wrapping it is **R4 ReAct** or **R13 CodeAct**;
- the action is privileged (financial, irreversible, externally-visible) and an LLM should not unilaterally trigger it → keep I2 for the *proposal* and gate execution with **V1 Human-in-the-Loop**.

## Decision Criteria

I2 is right when the LLM must interpret natural language to choose the action *and* the tool count is small enough that schemas fit comfortably in the prompt.

**1. Tool count.** How many tools does this agent need?
- **1–5** → **I2** is the obvious choice; native API support, low schema cost, simple wiring.
- **5–15** → **I2** still works; watch the schema-token footprint and selection accuracy.
- **15–20** → boundary zone; consider **I3 MCP Server** with dynamic tool injection, or split into sub-agents via **O17 Agent Isolation**.
- **20+** → **I3** with a gateway / dynamic discovery is mandatory; I2's flat schema list collapses selection accuracy (43% → 14% degradation reported at high counts; see V13).

**2. Schema footprint.** Sum the JSON Schema bytes of every tool description and parameter spec, then measure as a fraction of the model's context window.
- **< 5%** of context → safe, I2 is fine.
- **5–10%** → cap the tool set; tighten descriptions; consider per-tool prompt caching (Anthropic `cache_control`).
- **> 10%** → V13's hard threshold; move to I3 with lazy schema loading, or restructure with O17.

**Schema tokens are in seq_len on every generation step (mechanism 2 + mechanism 3).** Tool schemas are part of the KV cache for the entire request. Unlike human working memory, the model does not selectively activate tool schemas only when relevant — every generated Q vector performs a full similarity search over all cached K vectors, including all schema tokens, on every generation step. A 5,000-token tool schema list adds 5,000 K-vector comparisons per generated token, compounding across the entire response length. This is not a flat 5,000-token cost consumed once — it is a per-generation-step compute overhead that scales with response length. **Tool Budget pattern (V13)** addresses this directly: trim schemas aggressively, expose only the tools relevant to the current task, and use I3 MCP Server with dynamic tool discovery for large catalogues rather than loading all schemas statically. The practical implication: a 20-tool static schema list with 200 tokens each costs 4,000 K-vector comparisons per generated token; a dynamically loaded 3-tool schema costs 600.

**3. Sharing scope.** Will these tools be reused across other agents or other clients?
- **No, one agent owns them** → **I2** — the simpler deploy.
- **Yes, multiple agents or external clients** → **I3 MCP Server** earns its standardisation cost.

**4. Determinism / latency budget.** Is the LLM's judgment actually needed on this call?
- **Yes** (natural-language input drives the choice) → **I2**.
- **No** (code already knows what to call) → **I1 Direct API Call**; routing through I2 just adds latency and a small malformed-argument rate.

**5. Schema conformance discipline.** Are you willing to enable strict decoding (`strict: true` on OpenAI / Anthropic) and treat schema validation failures as bugs, not warnings?
- **Yes** → I2 delivers near-zero malformed-argument rates; pairs cleanly with **V20 Schema Validation**.
- **No** → expect a long tail of subtly wrong arguments and the silent failures that come with them; either commit to strict, or move the routing back into deterministic code.

**Quick test — I2 is the right pattern when:**

- 1–15 tools are app-specific to one agent, *and*
- the schemas comfortably fit (< 10% of context), *and*
- the LLM's interpretation of natural language genuinely determines which tool and what arguments, *and*
- the provider's native function-calling surface (with `strict`) is acceptable as the contract.

If routing is unnecessary, choose **I1 Direct API Call**. If the tool set has outgrown a single agent — shared across clients, > 15 tools, schema footprint > 10% — choose **I3 MCP Server**. If a CLI already does the job, choose **I4 CLI Invocation**. The cost of starting with I2 and graduating to I3 later is low; start small.

## Structure

```
   User request ─────────────────┐
                                 │
                                 ▼
   Tool Registry  ─────▶  Prompt assembly   ── tools[] + user message + history
   (JSON Schemas)                 │
                                  ▼
                          ┌──────────────┐
                          │   LLM call   │   provider's function/tool-calling API
                          └──────┬───────┘
                                 │
                       ┌─────────┴─────────┐
                       │                   │
                  text response       tool_call(s)
                       │                   │
                       │                   ▼
                       │           Schema Validator   ── V20; strict-mode catches at decode
                       │                   │
                       │              (pass) │ (fail) → reject / repair / surface
                       │                   ▼
                       │            Tool Dispatcher   ── name → handler lookup
                       │                   │
                       │                   ▼
                       │             Tool Executor    ── I1 internally (HTTP / SDK / DB)
                       │                   │
                       │                   ▼
                       │           Result Injector   ── tool_result block back into context
                       │                   │
                       └─────────┬─────────┘
                                 ▼
                         (loop, or final answer)
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Tool Schema** | the typed contract for one function (name, description, parameter JSON Schema) | tool definition → API-ready schema | hide ambiguity in the description. The description is the *only* thing the LLM uses to choose between tools; "Searches stuff" is the most common cause of wrong-tool selection. |
| **Tool Registry** | the agent's full set of available tools and the dispatcher mapping name → handler | tool definitions → assembled `tools=[...]` array + handler map | grow without a budget (V13). Tools added on autopilot are A12 Tool Proliferation. |
| **LLM Router** | choosing which tool(s) to invoke and with what arguments | user message + tools[] + history → `tool_call` blocks or plain text | execute the call. Selection only; if a model could also execute, it would have no incentive to ever say "no tool needed". |
| **Schema Validator** | enforcing that every emitted `tool_call` conforms to its declared schema before execution | `tool_call` → validated args, or rejection | trust the provider's claim of `strict` blindly on long-tail parameter shapes; validate again at the seam — providers and SDKs version-skew. |
| **Tool Dispatcher** | routing the validated `tool_call` to the right handler | `tool_call` (name + args) → handler invocation | embed business logic. Lookup and dispatch only; the handler does the work. |
| **Tool Executor** | actually performing the external action (an **I1 Direct API Call** internally) | validated args → raw result or error | re-route. It executes the named action; it does not second-guess the LLM's choice. |
| **Result Injector** | shaping the tool result and returning it to the LLM's context as a `tool_result` block | raw result → token-shaped `tool_result` | leak transport noise into the LLM's context — that bloats tokens, exposes implementation, and (V6) widens the prompt-injection surface. |

Seven narrow responsibilities, all but one in code; the LLM occupies exactly one of them. The pattern's reliability comes from keeping the LLM strictly inside the *Router* role and refusing to let any of the others drift back into prose-and-prayer.

## Collaborations

The agent code assembles the prompt with the user's message, the conversation history, and the `tools[]` array — every tool's schema, pulled from the Tool Registry. The LLM Router receives this and emits either a normal text response (no tool needed) or one or more `tool_call` blocks. The Schema Validator checks each call against its declared schema; with `strict: true` enabled, most provider SDKs catch malformed arguments at decode time, but a second-pass validation at the seam (V20) is still required because providers version-skew. The Tool Dispatcher resolves the name to a registered handler and the Tool Executor runs the call — which, internally, is an **I1 Direct API Call** to the actual external service. The Result Injector wraps the response as a `tool_result` block and returns it to the LLM context. The model now sees the result and either continues reasoning (often re-entering the same loop — that is **R4 ReAct**), or produces the final answer.

Two collaborations matter especially. **With R4 ReAct:** I2 is the action substrate of R4 — every "Act" step in a ReAct loop is an I2 tool call, and every "Observation" is the `tool_result` flowing back. **With V13 Tool Budget:** I2 is the simplest place V13 applies — a hand-written tool list with a number in a config — and the boundary at which V13 forces the move to I3.

## Consequences

**Benefits**
- Native support across every major LLM API — OpenAI, Anthropic, Gemini, plus all open-weights models that emit structured tool calls; no parser to maintain.
- Typed arguments at the seam — with `strict: true`, malformed-argument rates collapse toward zero.
- Schemas are the documentation — the same JSON Schema that constrains decoding also describes the tool to the developer.
- Cheapest LLM-routed integration to stand up; an agent goes from "no tools" to "five tools" in an afternoon.
- Composes upward: I2 is the substrate for R4 ReAct, R13 CodeAct, and the routing layer that I3 MCP Server eventually scales out.

**Costs**
- Every tool's schema consumes context tokens; the footprint grows linearly with tool count and quadratically with selection-error risk (V13).
- Selection accuracy degrades past ~15 tools — the model genuinely cannot distinguish between many similar descriptions.
- Tool descriptions become a quiet maintenance burden — small wording changes shift selection rates.
- The dispatcher is application-specific; nothing about an I2 setup is portable to another agent without rewriting the registry. (That portability is precisely what I3 buys.)

**Risks and failure modes**
- *Tool proliferation (A12).* Without V13 enforcement, the tool list grows; selection accuracy collapses; debugging becomes "why didn't it pick the right tool?" with no good answer.
- *Description ambiguity.* "Use this when the user asks about accounts" loses to "Use `lookup_account` for queries about a *specific* customer account by ID; use `list_accounts` for listings without an ID." Vague descriptions cause systematic wrong-tool selection.
- *Hallucinated arguments.* Without `strict: true`, models invent fields, drop required ones, or supply wrong types. The fix is strict mode plus a Schema Validator that refuses on any deviation.
- *Lethal Trifecta exposure (V3).* The moment a tool can read private data, accept untrusted content, and write externally, the agent inherits the trifecta. I2 makes adding such combinations easy; V3 must be audited per tool.
- *Sycophantic dispatch.* The model invokes a tool because the user asked it to, not because it should — typical when one tool's description matches user phrasing too literally. V5 Guardrail Layering point 2 (pre-call guard) catches this.
- *Schema-version skew.* Provider SDKs and the underlying API drift; a schema that decoded cleanly last quarter starts producing extra fields. Re-validating at the seam (V20) is the only durable fix.

## Implementation Notes

- **Enable strict mode** wherever the provider offers it — OpenAI `strict: true`, Anthropic `strict`. It is the single highest-leverage knob on argument quality.
- **Write tool descriptions from the model's perspective**, not the developer's. State *when to use this tool* and *when not to* — the negative half is what disambiguates against the other tools in the registry.
- **Include a one-line example** in the description for any tool with a non-obvious parameter ("query: a search phrase like 'pricing policy 2024', not a question").
- **Measure schema tokens** before deploying; tokens per tool × count must fit comfortably under V13's footprint threshold (< 10% of context).
- **Cache the tool prefix** where the provider supports it (Anthropic `cache_control`) — tool lists rarely change between calls, so prefix caching is free latency.
- **Validate twice**: enable provider-side strict decoding, *and* run a JSON Schema validator on arrival (V20). Providers version-skew.
- **Do not let a tool return a string the next prompt assumes is structured** — shape the `tool_result` payload deliberately; strip transport noise (V11 Error Compaction on errors).
- **Eval the routing**, not just the answers. A held-out set of "which tool would you pick?" labels is the V16 Offline Eval that catches description regressions before users do.
- **Cap the recovery loop.** When the model invokes a tool, gets an error, and tries again — pair with **V9 Bounded Execution** so a confused agent cannot ping a failing service indefinitely.
- **Treat tool outputs as untrusted text** if any input to the tool came from a user; apply **V6 Prompt Injection Shield** to the `tool_result` before it re-enters the context.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** I2 is the routing layer on top of **I1 Direct API Call** (every tool executes via I1 internally). It chains with **R4 ReAct** (which uses I2 as its action substrate, looping until done), composes with **V13 Tool Budget** (which caps the registry), **V20 Schema Validation** (the seam check), **V9 Bounded Execution** (loop cap), **V14 Trajectory Logging** (every tool call traced), and where the action is privileged, **V1 Human-in-the-Loop** (approval gate before execution). The schemas themselves are Signal-layer artefacts — each tool description is **S5 Constraint Framing** + **S6 Output Template** for the routing decision.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Build the `tools=[...]` array from the Tool Registry | `code` | V13 budget enforced here |
| 2 | Assemble the prompt — user message + history + tools | `code` | S3 / S5 / S6 in the system prompt |
| 3 | Call the model with tools enabled | `LLM` | Router session |
| 4 | Branch — if no `tool_call`, return the text answer | `code` | — |
| 5 | Validate each `tool_call` against its schema | `code` | V20 Schema Validation |
| 6 | *(optional)* Gate privileged calls on human approval | `code` | V1 Human-in-the-Loop |
| 7 | Dispatch to the handler; execute (I1 internally) | `code` | I1 Direct API Call |
| 8 | Wrap the result as a `tool_result` block, strip transport noise | `code` | V11 if error |
| 9 | Append result to the conversation; log the call | `code` | V14 Trajectory Logging |
| 10 | Loop to step 3 if more reasoning is needed (R4 ReAct) | `code` | V9 Bounded Execution caps the loop |

**Skeleton** — the wiring; the only `# LLM` step is the Router:

```
function_call_agent(user_message, registry, history):
    tools = registry.schemas()                          # code — V13 budget here
    for step in bounded(max_steps):                     # code — V9 cap
        response = LLM(history, user_message, tools)    # LLM — Router (strict decoding on)
        if response.tool_calls is empty:
            return response.text                        # final answer
        for call in response.tool_calls:
            validate(call, registry.schema(call.name))  # code — V20 (defence in depth)
            if requires_approval(call):
                await human_ack(call)                   # code — V1
            result = registry.handler(call.name)(**call.args)   # code — I1 inside
            log(call, result)                                    # code — V14
            history.append(tool_result_block(call.id, shape(result)))
    raise BoundedExecutionExceeded()
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Router** | the agent's main generalist (Claude / GPT / Gemini); function-calling capable; **strict decoding enabled** | system prompt (role / S3, constraints / S5, output contract / S6); the `tools=[...]` array assembled from the Tool Registry (often **prefix-cached** via Anthropic `cache_control`); conversation history up to the current turn | the new user message (and, on subsequent loop iterations, the latest `tool_result` block) |

**Specialist-model note.** None — the Router is a capable generalist. Two structural choices do the heavy lifting instead:

- **Strict-mode decoding** on the provider (OpenAI `strict: true`, Anthropic `strict`) — this is what makes the contract real; without it, the LLM emits *approximately* schema-conformant arguments and the seam silently rots.
- **Tool descriptions as the carrying artefact** — they are the prompt's most expensive real estate. Time spent here pays back per invocation; time *not* spent here shows up as wrong-tool selection on the dashboard.

If the agent is multi-provider, a library like **Instructor** (Pydantic-backed) or the **Vercel AI SDK** (TypeScript) abstracts over the per-provider tool-calling shape so the Router code does not branch on which model is underneath.

## Open-Source Implementations

- **OpenAI Python SDK** — [`github.com/openai/openai-python`](https://github.com/openai/openai-python) — the reference function-calling client; supports `tools=[]` and `strict: true` natively against the Chat Completions and Responses APIs.
- **Anthropic Python SDK** — [`github.com/anthropics/anthropic-sdk-python`](https://github.com/anthropics/anthropic-sdk-python) — reference tool-use client for Claude; supports `tools=[]`, `tool_use` / `tool_result` blocks, and `cache_control` for prefix caching of tool definitions.
- **Google Gen AI SDK** — [`github.com/googleapis/python-genai`](https://github.com/googleapis/python-genai) — the official Gemini SDK; supports function calling with parallel and compositional invocation.
- **Vercel AI SDK** — [`github.com/vercel/ai`](https://github.com/vercel/ai) — TypeScript toolkit with a provider-neutral `tool()` primitive and a `ToolLoopAgent` that closes the call → execute → return loop for you; runs against OpenAI, Anthropic, Gemini, and others.
- **Instructor** — [`github.com/567-labs/instructor`](https://github.com/567-labs/instructor) — Pydantic-backed structured output / tool-use across 15+ providers; the cleanest way to land typed arguments from a function-call without provider-specific glue.
- **LangChain `bind_tools`** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — the framework-level abstraction for binding a tool list to any provider; useful if already in LangChain, heavier than necessary if not.
- **JSON Schema (2020-12)** — [`json-schema.org/specification`](https://json-schema.org/specification) — the schema dialect every major provider uses for tool definitions; the underlying contract format.

## Known Uses

- **ChatGPT plugins and GPTs** — the production embodiment of OpenAI function calling; every plugin action is an I2 invocation.
- **Claude.ai and the Claude API tool-use ecosystem** — every Anthropic tool integration (web search, code execution, computer use, custom tools) flows through the `tool_use` / `tool_result` protocol.
- **Gemini-backed assistants** (Google AI Studio, Vertex AI agents) — function-calling is the default integration mechanism, including parallel and compositional calls.
- **Cursor, Windsurf, and IDE assistants** — small fixed tool sets (read file, write file, run command, search) wired as I2 for the editor-side actions; CLI tools (I4) and MCP servers (I3) supplement at scale.
- **Domain agents in production** (customer-support routers, legal/medical assistants, finance copilots) — typical pattern is 5–15 I2 tools per agent, with V1 Human-in-the-Loop on any write operation.
- **Vercel AI SDK demos and the broader TypeScript agent ecosystem** — `streamText` + `tools` is the de-facto starting template for new agentic features.

## Related Patterns

- **Wraps** I1 Direct API Call — every I2 tool *executes* as an I1 internally. I2 is the LLM-routing layer; I1 is the wire.
- **Sibling of** I3 MCP Server — I3 is the multi-client, standardised-discovery scale-up of I2; the upgrade path when tool count or sharing demands it.
- **Sibling of** I4 CLI Invocation — both are LLM-chosen invocations; I2 emits structured JSON args, I4 emits a shell command. I4 saves schema tokens at the cost of unstructured output.
- **Substrate for** R4 ReAct — R4's *Act* step is, almost always, an I2 tool call; R4 wraps I2 in a reason / act / observe loop.
- **Substrate for** R13 CodeAct — CodeAct emits *code* as its action and executes it; structurally a specialised I2 where the "tool" is `python_exec` and the argument is a program.
- **Pairs with** V13 Tool Budget — I2's count and schema-footprint are V13's primary surface; the cap lives here.
- **Pairs with** V20 Schema Validation — the seam check that enforces the schema even when strict decoding is enabled.
- **Pairs with** V9 Bounded Execution — caps the call-and-respond loop so a confused agent cannot thrash a failing service.
- **Pairs with** V1 Human-in-the-Loop — privileged tool calls are *proposed* by I2 and *approved* by V1 before execution.
- **Pairs with** V14 Trajectory Logging — every `tool_call` and `tool_result` must appear in the trace.
- **Pairs with** V6 Prompt Injection Shield — `tool_result` payloads from user-influenced inputs are untrusted text and must be sanitised before re-entering context.
- **Constrained by** V3 Rule of Two — auditing whether a tool's combination (private data + untrusted content + external comms) creates the Lethal Trifecta.
- **Distinct from** I1 — I1 is code-chosen; I2 is LLM-chosen. I2's execution step is I1; the architectural choice is whether the routing layer earns its keep.

## Sources

- OpenAI — [Function calling guide](https://platform.openai.com/docs/guides/function-calling) (Chat Completions and Responses APIs); the original mainstream specification (June 2023) and the `strict: true` structured-outputs extension.
- Anthropic — [Tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview) and [How tool use works](https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works); the `tool_use` / `tool_result` protocol, strict mode, and tool prefix caching.
- Google — [Function calling with the Gemini API](https://ai.google.dev/gemini-api/docs/function-calling); parallel and compositional function calling.
- JSON Schema — [2020-12 specification](https://json-schema.org/specification); the schema dialect underneath every major provider's tool-definition surface.
- Schick et al. (2023) — [*Toolformer: Language Models Can Teach Themselves to Use Tools*](https://arxiv.org/abs/2302.04761) (arXiv 2302.04761); the research framing that LLM-routed tool use is a self-supervisable capability.
- Brown et al. (2020) — *Language Models are Few-Shot Learners* (GPT-3); the foundational few-shot capability that made schema-described tool selection viable at all.
- LangChain — [Tool calling concept](https://python.langchain.com/docs/concepts/tool_calling); the framework-level abstraction across providers.
- Andrew Ng (2024) — "The four agentic patterns"; "Tool Use" as one of the four; the practitioner framing of I2's role.
- 12-Factor Agents — Factor 4 (*Tools are just structured output*); the architectural framing that a tool call is a typed message, not a separate paradigm.
