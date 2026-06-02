# I1 — Direct API Call

> Call an external service from code on a deterministic path — no LLM decides which endpoint, no LLM picks parameters, no LLM interprets the response — so the call is fast, reproducible, and cheap.

**Also Known As:** Deterministic Integration, Synchronous HTTP, Traditional API Client, Hard-Coded Tool Call.

**Classification:** Category VI — Integration · the *deterministic baseline* of the category — every other Integration pattern (I2 Function Call, I3 MCP Server, I4 CLI Invocation) wraps I1 inside an LLM-routing layer; I1 is the layer with no routing.

---

## Intent

Execute an external action from ordinary code, with parameters fixed by program logic rather than chosen by a language model, so the integration is deterministic, sub-10ms-latency-achievable, and auditable line-for-line.

## Motivation

Treating every integration as a "tool call" routes everything through an LLM that must read a schema, decide what to invoke, and emit structured arguments. That is the right move when the next action genuinely depends on interpreting natural language. It is the wrong move when the next action is already determined by code — and a surprising share of agent integrations sit in that second category.

Three classes of action are deterministic by construction. **Post-decision execution:** the LLM has already decided what to do; the API call that follows is a mechanical consequence of that decision, not a fresh judgment. **Pre-decision data fetch:** the agent needs the current price, the user's record, the order status — there is no ambiguity about which endpoint answers that, only one value to retrieve. **Fixed-shape writes:** logging a trade, inserting an audit row, posting a webhook — the schema is known, the parameters come from typed code variables, the call signature does not change. Routing any of these through an LLM adds 300–2000ms of latency, $0.001–$0.05 of cost per call, and a small but non-zero rate of malformed arguments — in return for no decision the LLM was needed to make.

I1 is what is left after that overhead is stripped out: a regular HTTP client invocation, a database driver call, an SDK method. The LLM may sit elsewhere in the system — deciding *whether* to make this call, or *what to do with the result* — but the call itself is plain code. The pattern's unique contribution is to name this as a first-class architectural choice rather than an absence. Every other Integration pattern (I2, I3, I4) is a layer that adds LLM routing *on top of* I1; choosing I1 directly is choosing to skip that layer when it earns nothing.

The distinction from I2 Function Call is sharp and worth stating: **I2 = LLM chooses; I1 = deterministic.** I2 is appropriate when natural-language interpretation determines which function and which parameters. I1 is appropriate when the function and the parameters are already determined by code or by the LLM's prior output. They are not competitors — I2's execution step *is* I1 internally — but they are different architectural choices that get conflated when every integration is reflexively schema-wrapped.

The small but non-zero rate of malformed arguments from I2 is not a configuration defect — it is a structural consequence of mechanism 7: token generation is stochastic sampling from a learned probability distribution, not a deterministic function. Even at temperature=0 (argmax sampling), the distribution is learned, not computed from a schema. I1 eliminates this variance entirely because code does not sample.

## Applicability

Use I1 when:

- the API to call and its parameters are determined by program logic, by typed variables, or by a structured extraction from prior LLM output — no fresh interpretation needed;
- the call is latency-critical (sub-10ms achievable; LLM routing cannot reach that floor);
- the call is high-frequency and per-call LLM cost would be material at scale;
- the action has compliance, audit, or financial semantics that demand reproducible behaviour for identical inputs;
- the API surface is stable and the parameter mapping is known at build time.

Do not use I1 when:

- the next action genuinely depends on interpreting natural language — use **I2 Function Call** (and let I2 call I1 internally);
- the call set is large and shared across multiple agents or clients — use **I3 MCP Server**;
- the operation already has a battle-tested CLI and you want zero schema overhead — use **I4 CLI Invocation**;
- the action carries authority and could be triggered against an attacker's input — use **V1 Human-in-the-Loop** to gate it, *then* let I1 execute;
- the call writes to a privileged system and may be reached by adversarial content — the deterministic path still needs **V5 Guardrail Layering** point 2 (pre-call guard) and **V6 Prompt Injection Shield** at the parameter extraction step.

## Decision Criteria

I1 is right when the action is fully determined by code — no LLM judgment is needed to decide what to call or with what.

**1. Locate the decision.** Where does the choice of API + parameters actually get made?
- Made entirely by code logic, or by deterministic extraction from a prior LLM output → **I1**.
- Made by the LLM at the moment of calling (it reads the user's request and picks the tool) → **I2** (which calls I1 internally).
- Made by the LLM but among 10+ shared tools across agents → **I3**.
- The right call is a shell command and a CLI already exists → **I4**.

**2. Latency floor.** What is the target per-call latency?
- < 10ms (HFT, real-time pricing, sub-second UX) → **I1** mandatory; any LLM routing breaks the budget.
- 50–500ms → **I1** preferred; I2 acceptable.
- > 500ms tolerable → I2/I3 fine.

**3. Determinism requirement.** Must identical inputs produce byte-identical calls (audit, compliance, financial reconciliation)?
- Yes → **I1**. LLM routing introduces a small non-zero rate of parameter variance even at temperature 0.
- No → I2 is fine.

**4. Call frequency × LLM cost.** At expected QPS, what would routing-LLM cost run to annually? If it exceeds the engineering cost of writing the deterministic mapping (a few hours to a few days), **I1** wins on raw economics regardless of other factors.

**5. Schema stability.** How often does the API contract change?
- Stable (versioned, deprecation cycles, OpenAPI spec) → **I1** safe; hard-coded mapping holds.
- Volatile (internal API in flux, schema-as-code regenerated weekly) → consider **I2** so the schema description carries the change, or invest in code-generation from the spec for I1.

**Quick test — I1 is the right pattern when:**

- the action and its parameters are determined by code or by a prior structured output, *and*
- latency, cost, or determinism makes LLM routing a net loss, *and*
- the API surface is stable enough that a hard-coded mapping will not churn.

If the choice of action genuinely requires interpreting natural language, choose **I2 Function Call** — and remember that I2's execution step is I1 internally, so the question is only where the LLM sits, not whether the HTTP call exists. If the call set is shared and large, **I3 MCP Server**. If a CLI already does the job, **I4 CLI Invocation**.

## Structure

```
   (upstream decision: LLM output, rule, condition, or code logic)
                              │
                              ▼
                      Parameter Extractor  ── strict typing / regex / structured-output parse
                              │
                              ▼
                         Validator         ── schema check, range check, deny-list, V5 pre-call guard
                              │
                       (fail) │ (pass)
                       ▼      ▼
                   refuse / log     API Client     ── HTTP / SDK / DB driver
                                       │
                                       ▼
                                  Error Handler   ── retry, backoff, circuit breaker, V11 compaction
                                       │
                                       ▼
                                    Result        ── returned to caller (often back into the LLM context)

   No LLM in this path. The LLM may sit upstream (deciding to call) or downstream (consuming the result),
   never inside the call itself.
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Parameter Extractor** | turning upstream signal into typed call parameters | LLM output / rule / variables → typed parameter object | re-interpret the upstream intent — it parses; it does not decide. If it has to "figure out what the user meant", that's I2 territory, not I1. |
| **Validator** | gatekeeping the call before it leaves the process | parameter object → pass / fail | be skipped on the assumption that the upstream code "already validated" — the validator is where compliance and security live, and it must run even on internal callers. |
| **API Client** | executing the call against the external service | validated parameters → raw response | embed business logic — it is a transport. Auth handling, headers, serialisation: yes. Branching on response content: no, that belongs in the caller or Error Handler. |
| **Error Handler** | retry, backoff, circuit breaker, and the decision to surface or swallow | raw response / exception → retried result, surfaced error, or open circuit | hide errors from the audit log; every retry and every circuit-open event must be traceable (V14). |
| **Result Returner** | shaping the response for the caller (and for any LLM downstream) | raw response → typed result | leak transport details (raw headers, full HTTP envelopes) into an LLM's context — that bloats tokens and exposes implementation. |

Five narrow responsibilities, all in code, none of them an LLM. The pattern's reliability comes from that absence: the call path is testable end-to-end with unit tests and replay fixtures, not with eval sets.

## Collaborations

Upstream, something has decided this call should happen — an LLM has emitted a structured action, a rule has matched, or code has reached a branch that always calls this endpoint. The Parameter Extractor reads that signal and produces a typed parameter object. The Validator runs schema, range, and policy checks; this is the same checkpoint as V5 Guardrail Layering's pre-call guard, and on a privileged action it is also where V1 Human-in-the-Loop can interpose. The API Client makes the call. The Error Handler decides whether a non-success response is retried (with backoff and jitter), surfaced to the caller, or escalated to an open circuit. The Result Returner shapes the response — and if the result will be fed back into an LLM's context, it strips transport noise before doing so. Every step writes to the V14 Trajectory Logging trace so the call is auditable after the fact.

The most common composition is as the execution layer of I2: the LLM chooses, in natural language, which function to invoke and with what arguments; once the structured tool call lands, the actual HTTP request is an I1. The LLM's contribution ends at parameter selection; I1 handles the wire. When that whole loop is unnecessary — when code already knows which endpoint to hit — using I1 directly skips the routing layer.

## Consequences

**Benefits**
- Lowest latency available — bounded by network + service, not by an LLM call on the critical path.
- Cheapest per call — no model inference cost.
- Fully deterministic — identical inputs produce identical calls, byte-for-byte.
- Auditable by ordinary code-review and trace inspection; no "why did the model pick that parameter" mystery.
- Testable with standard unit tests, contract tests, and replay fixtures — no eval set required.

**Costs**
- Every parameter mapping must be coded explicitly; there is no LLM to absorb format drift.
- Loss of natural-language flexibility — the call cannot adapt to a phrasing the code did not anticipate.
- Schema changes in the external API require code changes; no schema-description layer to update centrally.
- Risk of premature optimisation: teams reach for I1 because it is fast and cheap, then discover too late that the interpretation work they avoided actually mattered.

**Risks and failure modes**
- *False economy* — choosing I1 to "avoid the LLM cost" on a path where LLM interpretation would have caught a class of user-input variance the hard-coded extractor will silently mishandle.
- *Schema drift* — the external API's contract changes; the deterministic extractor passes the wrong parameter name or omits a newly required field; failures are syntactic and loud, but only in production.
- *Validator skipping* — internal callers are trusted "because they're internal"; the day an external input reaches an internal caller, the missing validation is exploited.
- *Audit gap* — error retries silently swallow failures; the V14 trace shows only the eventual success and the operator cannot see how many attempts it took.
- *Hidden LLM dependency* — the parameter extractor "just regex-parses the LLM output", but the LLM upstream is non-deterministic; the integration is presented as deterministic but the seam above it is not. Trace the determinism boundary explicitly.

## Implementation Notes

- Place the determinism boundary explicitly: document where LLM judgment ends and the deterministic path begins. Most I1 bugs sit on that seam.
- Parse upstream LLM output with **strict structured output** (JSON Schema with `strict: true`, or a typed parsing library) — never with regex or string fishing. A malformed extraction is the most common I1 failure.
- Validate parameters against the API contract *in your code*, not just by hoping the server returns 400. Range, type, enum, deny-list, business-rule — all before the wire.
- Implement retries with exponential backoff + jitter; cap them. Pair with **V9 Bounded Execution** so a retry storm cannot indefinitely re-hit a failing service.
- Add a circuit breaker for high-frequency calls; one bad downstream should not amplify into a thundering herd.
- Log every call to the **V14 Trajectory Logging** trace, including retried attempts and open-circuit events. An I1 call that does not appear in the trace is invisible to audit.
- When the result feeds back into an LLM's context, strip transport noise (headers, envelopes, debug fields) — leave only the semantic payload. This is also where **V11 Error Compaction** belongs if the API errored. The mechanistic reason to strip aggressively is mechanisms 2 and 3: every byte of result that enters the LLM context extends seq_len, contributes O(n²) to the attention computation, and adds to the KV cache that grows for the remainder of the session. A result that is 50 tokens instead of 5,000 tokens is not just cheaper on the input token count — it reduces every subsequent generation step in the session.
- For credential management, do not pass credentials through the LLM's context at any point; the API Client holds them.
- If the call writes data that an attacker could influence upstream, **V5 Guardrail Layering** point 2 and **V6 Prompt Injection Shield** apply to the parameter extraction even though the call itself is "just code".
- Generate the parameter mapping from the API's OpenAPI / gRPC spec where possible — turns a schema change from a silent break into a build-time error.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring. I1 is special: in the canonical case, **there is no `LLM` step inside the pattern.** The LLM may sit upstream as the source of the structured action, but the call path itself is pure code.

**Composition:** I1 chains downstream of whatever produced the structured action — most often **I2 Function Call** (where I1 is I2's execution step), sometimes **R4 ReAct** (where I1 executes the Act), sometimes plain code logic with no LLM at all. It pairs with **V9 Bounded Execution** (retry caps), **V14 Trajectory Logging** (audit), **V5 Guardrail Layering** (pre-call guard), and where relevant **V1 Human-in-the-Loop** (approval gate on privileged calls). On the result side it can feed back into an LLM session, in which case **V11 Error Compaction** shapes any error payload before it enters the context.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Receive upstream signal (LLM structured output, rule, code condition) | `code` | — |
| 2 | Extract typed parameters from the signal | `code` | strict structured-output parsing |
| 3 | Validate parameters (schema, range, policy) | `code` | V5 pre-call guard, V6 if upstream is adversarial-reachable |
| 4 | *(optional)* Human approval for privileged actions | `code` (gates an out-of-band human ack) | V1 Human-in-the-Loop |
| 5 | Make the API call (HTTP / SDK / DB) | `code` | — |
| 6 | Handle errors (retry with backoff, circuit breaker, surface) | `code` | V9 Bounded Execution |
| 7 | Log the call (request, response, retries, latency) | `code` | V14 Trajectory Logging |
| 8 | Shape result for the caller (strip transport noise) | `code` | V11 if returning an error to an LLM context |

**Skeleton** — the wiring; note the absence of `# LLM` markers, which is the point of the pattern:

```
direct_api_call(structured_action):
    params  = extract(structured_action)              # code — strict typed parse
    validate(params)                                  # code — V5 pre-call guard; raises on fail
    if requires_approval(params):                     # code
        await human_ack(params)                       # code — V1 gate
    for attempt in bounded(max_attempts):             # code — V9 bound
        try:
            response = api_client.call(params)        # code — HTTP/SDK/DB
            log(params, response, attempt)            # code — V14
            return shape(response)                    # code
        except RetryableError as e:
            backoff(attempt); continue
        except FatalError as e:
            log_failure(params, e); raise
    raise CircuitOpen()
```

**The LLM sessions:** *None inside I1.* The LLM, if present, is upstream — emitting the structured action that feeds step 1, or downstream — consuming the result returned by step 8. The point of choosing I1 over I2/I3 is precisely that this column is empty.

**Specialist-model note.** None — no model is loaded by this pattern. The build dependency is *strict structured-output parsing* at the seam between any upstream LLM and step 2: a typed parser (Pydantic, Zod, JSON Schema with `strict: true`) is what makes the deterministic path actually deterministic. A regex fishing through free-form LLM text is the most common way I1 quietly stops being I1. If the API contract is available as an OpenAPI / gRPC spec, generate the client from it — turns silent schema drift into a build error.

## Open-Source Implementations

I1 is an architectural choice, not a library — *any* HTTP client or SDK call from agent code is an instance of it. The relevant "implementations" are the client libraries and structured-output tools that make the determinism boundary clean:

- **HTTPX** — [`github.com/encode/httpx`](https://github.com/encode/httpx) — modern Python HTTP client with sync + async, HTTP/2, and connection pooling. The default choice for I1 in Python agent code.
- **Requests** — [`github.com/psf/requests`](https://github.com/psf/requests) — the long-standing Python HTTP client; still the most common I1 substrate in production agents.
- **Axios** — [`github.com/axios/axios`](https://github.com/axios/axios) — the standard JavaScript/TypeScript HTTP client for agent code in the Node / browser stack.
- **Pydantic** — [`github.com/pydantic/pydantic`](https://github.com/pydantic/pydantic) — typed parsing of LLM structured output before it crosses the seam into I1. The build dependency that keeps the path deterministic.
- **Instructor** — [`github.com/instructor-ai/instructor`](https://github.com/instructor-ai/instructor) — Pydantic-backed structured output extraction from LLM calls; the canonical way to land typed parameters into an I1 path.
- **OpenAPI Generator** — [`github.com/OpenAPITools/openapi-generator`](https://github.com/OpenAPITools/openapi-generator) — generates typed API clients from OpenAPI specs across languages; turns schema drift into a build-time error.

There is no single "I1 framework" because I1 is *the absence* of the routing layer that I2/I3/I4 add.

## Known Uses

- **Financial and trading agents** — order placement, position queries, and risk checks call exchange and broker APIs directly from code; LLM routing on the order path is unacceptable on both latency and determinism grounds.
- **Compliance and audit pipelines** — log writes, audit-trail inserts, regulatory submissions all go through I1 paths so that identical inputs produce byte-identical externally-visible behaviour.
- **Claude Code, Cursor, and other coding agents** — most filesystem operations, git invocations, and process control happen as I4 (CLI) or I1 (direct subprocess / API), not as schema-wrapped tool calls — the choice is consistent with the "LLM where language understanding adds value" principle.
- **High-throughput RAG ingestion pipelines** — vector DB writes, embedding API calls, and document chunking are all I1 from worker code; the LLM is upstream (in chunking decisions) or downstream (in answering), not on the hot path.
- **Webhook handlers and event-driven agent paths** — when an external event triggers a known action, the action runs as I1; LLM reasoning is reserved for cases where the event's *meaning* is ambiguous.

## Related Patterns

- **Distinct from** I2 Function Call — I2 has the LLM choose which tool and what parameters; I1 has code choose. I2's execution step *is* I1 internally; the architectural choice is whether the LLM-routing layer earns its keep.
- **Distinct from** I3 MCP Server — I3 is the shared, multi-client version of I2's routing. If routing is not needed, I1 skips both.
- **Distinct from** I4 CLI Invocation — I4 is LLM-chosen invocation of a CLI tool; I1 is code-chosen invocation of an API. Both are zero-schema-token but they differ in who chooses the call.
- **Underlies** I2, I3, I4 — every routed integration eventually calls *something*; that something is an I1.
- **Pairs with** V5 Guardrail Layering — the pre-call guard (point 2 of V5) is the Validator in this pattern.
- **Pairs with** V9 Bounded Execution — retry and circuit-breaker logic must be bounded; without that, a failing downstream cascades.
- **Pairs with** V14 Trajectory Logging — every I1 call must appear in the trace, including retries and open-circuit events, or audit breaks.
- **Pairs with** V1 Human-in-the-Loop — when an I1 call is privileged (financial, irreversible, externally-visible), V1 gates it; I1 still executes the action, V1 just decides whether to.
- **Composes with** R4 ReAct — when an Act step is fully determined (no fresh interpretation needed), it executes as I1 rather than as a schema-wrapped tool call.

## Sources

- REST / HTTP semantics — RFC 9110 (HTTP) and RFC 7231 (predecessor); the foundational specification under any I1 call.
- 12-Factor Agents — Factor 8, *Own Your Control Flow* — argues for deterministic execution over agentic loops where the choice is already made.
- Karpathy, A. (2025) — public commentary on agent architecture and "context engineering"; "use the LLM only where language understanding adds value" frames the I1 / I2 boundary.
- AWS prescriptive guidance on agent architectures — the deterministic-execution vs. LLM-routing distinction as an explicit design decision.
- OpenAPI Specification (3.x) — the contract format that makes I1 mappings generable and refactor-safe.
- Anthropic and OpenAI cookbook materials on tool use — implicitly: every tool *executes* via I1, regardless of how it was *chosen*.
