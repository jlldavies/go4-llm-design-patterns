# V14 — Trajectory Logging

> Emit a complete, structured, OpenTelemetry-compliant trace of every decision, LLM call, tool invocation, policy check, and intermediate output the agent makes during a task — so the run can be replayed, debugged, audited, and evaluated long after it finishes.

**Also Known As:** Agent Trace, OTel for Agents, Audit Log, GenAI Telemetry, Span-Based Observability.

**Classification:** Category V — Reliability · Band V-C Observability and Evaluation · the *substrate* pattern — the raw data source the rest of the band (V15–V18) and several V-A patterns (V1, V2, V7) read from.

---

## Intent

Make every step the agent takes visible as a structured event, in a vendor-neutral format, so that debugging, auditing, evaluation, and monitoring can all read from the same record — instead of each rebuilding the run from fragmentary logs.

## Motivation

Production agents are opaque by default. When one fails — a wrong answer, a runaway loop, a leaked secret, a tool call gone wrong — the operator has to reconstruct what happened from print statements, request logs, and partial outputs. The reconstruction takes hours, often days, and usually misses the actual failure point because the relevant intermediate step was never recorded. The Composio AI Agent Report (2025) cites "no observability" as one of the top causes of agents that ship to production and then quietly die.

**Why multi-agent runs are undebuggable without traces (mechanism 3 + mechanism 7).** The KV cache is session-scoped and does not persist across API calls (mechanism 3). Once an agent's session ends, its complete computational state — the exact token sequence it conditioned on, the context it saw — is gone. If the agent produced a wrong output, the only evidence is the output itself; the context that produced it is unreconstructable without an external log. Compound this with stochastic generation (mechanism 7): the same call made again may produce a different output, making post-hoc reproduction unreliable. A trajectory log is the only mechanism by which the full context, call sequence, and token-level decisions of a multi-agent run are preserved for audit, debugging, or replay.

Naive alternatives all fail at the same thing — *they are written for humans to read in the moment, not for machines to query after the fact.* Free-text logs are unparseable. Per-step stdout is unstructured. Even careful narrative logging gives you a story per run, not a queryable dataset across runs. The 12-Factor Agents distinction is the right one: *"logs are for people, traces are for machines."* V14 is about traces.

The unique contribution is the **shape** of the data. A trace is a tree of *spans* — each span a typed, attributed, timed unit of work, with parent-child relations capturing what called what. Every LLM call, tool invocation, retrieval, policy check, and guardrail decision is a span. The OpenTelemetry GenAI Semantic Conventions (CNCF, 2024–25) standardise the attribute names — `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.tool.name` — so the same trace can be read by Jaeger, Honeycomb, Phoenix, Logfire, Grafana, or any other OTel backend without translation. That standardisation is what turns observability from a per-team bespoke project into a commodity capability. Without V14, every other observability and evaluation pattern (V15 LLM-as-Judge, V16 Offline Eval, V17 Online Eval, V18 Agent Simulation) has nothing to read from.

## Applicability

Use V14 when:

- the agent is heading for production — V14 is universal there, not optional;
- multiple subsystems (debugging, audit, eval, monitoring) need to read the same run record;
- the agent has more than one step, more than one tool, or more than one collaborating component;
- regulated industries (healthcare, finance, legal) require an audit trail by law;
- you intend to run V15/V16/V17/V18 — they all need V14 trace data as input.

Do not bother when:

- the agent is a single throwaway prompt with no tools, no loop, and no collaborators — narrative logging suffices;
- you are still in early prototype with no users and no failures worth diagnosing — add V14 before launch, not on day one of a sketch;
- privacy constraints make trace storage materially harder than the value justifies (rare, but real for some on-device or end-to-end-encrypted contexts; handle with scrubbing rather than skipping V14).

## Decision Criteria

V14 is right whenever an agent will run more than once and someone will need to know later what it did.

**1. Multi-step or multi-component?** If the agent has *any* of: a loop (R4, R7, R9, R10), a tool call, a sub-agent (O6, O7, O17), or a policy/guard step (V5, V7) — V14 is required. A linear single-prompt call can fall back to ordinary application logging. With anything more, narrative logging loses the structure and the trace earns its keep within the first incident.

**2. Production readiness.** If the agent is targeting production: V14 is non-negotiable from day one. Adding tracing after an outage is too late — the outage you needed to debug already happened with no record. *No production agent ships without V14.*

**3. Compliance load.** Does the deployment domain require an audit trail (EU AI Act Article 12 record-keeping; HIPAA; SOX; financial-services regulation)? Then V14 is not just useful, it is the compliance mechanism. The trace **must** be tamper-evident and retained per regulatory schedule.

**4. Downstream patterns committed?** If V15 (LLM-as-Judge), V16 (Offline Eval), V17 (Online Eval), or V18 (Agent Simulation) are on the roadmap — V14 is their feedstock. They cannot be built later without V14 data accumulating from now.

**5. Multi-agent system?** Any agent that talks to other agents — O6 Orchestrator-Workers, O7 Supervisor Hierarchy, O11 Blackboard, O17 Agent Isolation — must propagate trace context across the boundary, or each agent's spans become orphaned and the cross-agent flow is unreconstructable. V14 with **distributed context propagation** is mandatory.

**Quick test — V14 is the right pattern when:**

- the agent will run in production *or* in any context where someone will later ask "what did it do, and why?", *and*
- the agent has more than one step, tool, or component, *and*
- a downstream consumer exists or is planned (debugging, audit, V15/V16/V17/V18), *and*
- the operational maturity of the team can sustain "instrument, ship, alert" — not just "instrument".

If none of these hold — a one-off script, a hand-driven prototype — narrative `print` or structured application logs suffice. If they hold and you ship without V14, you are accepting **A15 Untraced Agent** as a known liability; expect debugging to take hours per incident rather than minutes, and expect no compliance story when asked.

## Structure

```
  Agent invocation ──▶ Trace Emitter (instrumentation)
                            │
                            │ emits spans, with parent–child links
                            ▼
              ┌─────────────────────────────────────────────────┐
              │  Span: agent_invocation                          │
              │    attrs: agent.id, agent.version, task.id       │
              │                                                  │
              │    ├─ Span: llm_call                             │
              │    │     attrs: gen_ai.system, gen_ai.request.   │
              │    │            model, gen_ai.usage.*, latency   │
              │    │     events: prompt, completion              │
              │    │                                              │
              │    ├─ Span: tool_call                             │
              │    │     attrs: tool.name, tool.version,         │
              │    │            params (scrubbed)                │
              │    │     events: result, error                   │
              │    │                                              │
              │    ├─ Span: policy_check  (V7)                   │
              │    │     attrs: rule, decision, waiver?          │
              │    │                                              │
              │    └─ Span: guardrail_check  (V5)                │
              │          attrs: guard_point, decision, reason    │
              └─────────────────────────────────────────────────┘
                            │
                            ▼
                   OTel Collector (scrub PII, batch, route)
                            │
                            ▼
                  Trace Backend (Jaeger / Phoenix / Honeycomb /
                                  Tempo / Logfire / Datadog)
                            │
                            ▼
               Consumers:  V15 judge · V16 regression suite ·
                           V17 monitors · V18 simulation analyser ·
                           human debugger · audit reviewer
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Trace Emitter** | producing spans from inside the agent | agent step → span (typed, attributed, parent-linked) | block or fail the agent step if emission fails — telemetry must degrade silently, never break the host. |
| **Span Schema** | the attribute vocabulary used (OTel GenAI conventions) | — → consistent attribute namespace | invent ad-hoc attribute names. The whole point is that downstream tools recognise the schema; bespoke names defeat it. |
| **Context Propagator** | passing trace identity across boundaries (sub-agent, tool, HTTP, queue) | parent context → child context, on every cross-boundary call | drop the parent on async, sub-agent, or queue handoffs — orphaned spans break the run reconstruction. |
| **OTel Collector** | receiving spans, scrubbing PII, batching, routing | raw span stream → cleaned span stream | leak unredacted prompt or tool-parameter values to the backend; PII scrubbing is the collector's job, not "later". |
| **Trace Backend** | durable storage and query | spans → indexed, queryable history | be the only consumer — if no analyser, dashboard, or alert reads it, the trace is archaeology. |
| **Trace Analyser** | turning stored traces into action | spans → debug answer / eval score / alert / regression test | conflate this role with the emitter; analysis is downstream, not part of the agent. |

Six narrow responsibilities. The **Emitter and Analyser must be separate concerns** — the agent emits without knowing who will read; the analyser reads without depending on agent internals. This separation is what lets the same trace serve a human debugger, the V15 judge, the V17 monitor, and an auditor — without re-instrumenting for each.

## Collaborations

The agent runs. As it executes each step — an LLM call, a tool invocation, a guard check, a policy evaluation — the Trace Emitter opens a span, records its attributes per the OTel GenAI conventions, and closes it on completion (or on error, with the error recorded). Parent-child relations are set automatically by the propagator, which threads context through the call stack and across boundaries (sub-agent calls, async handoffs, queue dispatches, HTTP requests). The Collector receives the span stream, scrubs PII and credentials, batches, and forwards to the Backend, which indexes and stores. Downstream consumers — a human running a query in Jaeger, the V15 judge scoring a sampled output, the V17 monitor checking p99 latency, the V18 simulation harness diffing actual against expected — all read the same store, without coordinating with each other. When V1 (Human-in-the-Loop) pauses for review, the human's UI is itself a Trace Analyser, presenting the open span tree as the context for the approval decision.

## Consequences

**Benefits**
- Post-hoc debugging shrinks from hours to minutes — the run is fully reconstructable.
- One feedstock serves debugging, audit, eval (V16), monitoring (V17), and simulation analysis (V18).
- Vendor-neutral: switching backends is a collector reconfiguration, not a code change.
- Compliance audit trails are produced as a *byproduct* of normal operation.
- Distributed multi-agent flows become visible end-to-end via context propagation.

**Costs**
- Instrumentation effort up front: every step that matters has to emit; missing spans become invisible failures.
- Storage and processing: high-volume agents produce large trace volumes; retention policy and sampling must be designed.
- Latency: emission, propagation, and export add a few ms per step — usually negligible, occasionally not.
- PII handling: prompts and tool parameters often contain sensitive data; scrubbing must be designed, not assumed.

**Risks and failure modes**
- *Traces written but never read* — the most common failure. Dashboards, alerts, and triage workflows must be built alongside the instrumentation, not "later".
- *PII leakage into the backend* — unscrubbed prompts or tool parameters end up in trace storage, creating a new data-exposure surface.
- *Sampling that drops the rare-but-important* — head-based sampling cheap to run; tail-based sampling preserves rare errors. Pick deliberately.
- *Bespoke attribute names* — drift away from OTel GenAI conventions makes downstream tooling unable to recognise the spans.
- *Orphan spans on async boundaries* — context propagation forgotten on a queue, an HTTP hop, or a sub-agent call; the trace fragments silently.
- *Telemetry that breaks the agent* — emitter exceptions propagate into the agent run. Emission must be non-blocking and fail-silent.

## Implementation Notes

- Use the **OpenTelemetry GenAI Semantic Conventions** as the attribute schema. Don't invent your own — the standard names (`gen_ai.*`) are what downstream tools recognise.
- **Scrub at the collector**, not in the agent. Centralising PII redaction in the collector means a single audited code path instead of many sprinkled `redact(...)` calls.
- **Instrument on the way in**, not retrofitted. Wrap LLM-call helpers, tool dispatchers, and sub-agent invocations so emission is structural; ad-hoc per-call instrumentation will be inconsistent.
- **Propagate context across every boundary**: queues, HTTP, sub-process, sub-agent. The propagation library is part of the OTel SDK; use it rather than rolling your own.
- **Design dashboards alongside instrumentation**. The first time you need a trace, the dashboard already exists — don't write it during the outage.
- **Sample with intent.** 100% in dev; head sampling 1–10% in production for routine spans; always 100% on errors, V1 approvals, V7 policy denials, V9 budget terminations.
- **Pair with K11 (Observational Memory)** when the agent itself needs to reason over its own activity — K11's "agent reads the raw record" is reading the V14 trace.
- **Pair with K12 (Karpathy Memory)** when the trace becomes the substrate for an LLM-curator: the Curator reads V14 and writes structured notes (K12) that distil the trajectory into reusable knowledge.
- **Retention policy** drives storage cost more than emission volume. Short retention (7–30 days) for routine traces; longer (≥ regulatory requirement) for compliance-relevant runs, error runs, and approval runs.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V14 is structural infrastructure, not an LLM step in the agent's own logic. It wraps every other pattern's calls and emits spans for them. Composes with **K11** (the trace can be the activity record), **K12** (a Curator reads the trace), **V5** (guards emit spans), **V7** (policy checks emit spans), **V9** (budget terminations emit spans), **V17** (online judge reads spans). The Trace Analyser, downstream, may itself involve `LLM` calls — that's the V15 judge — but the emission pipeline is all `code`.

**The chain — emission (per agent step):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Start span; attach parent context from caller | `code` | OTel SDK |
| 2 | Record start-time attributes (model, tool name, schema, agent.id, task.id) | `code` | GenAI semconv |
| 3 | Execute the wrapped step (LLM call, tool call, guard, policy, sub-agent) | `LLM` *or* `code` | the wrapped pattern |
| 4 | Record outcome attributes (tokens, latency, decision, error) + events | `code` | GenAI semconv |
| 5 | Close span; propagate context to children | `code` | OTel SDK |
| 6 | Async export to Collector | `code` | OTel exporter |

**The chain — consumption (downstream, separate process):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| C1 | Query the Backend for spans matching a run / time-window / filter | `code` | Jaeger / Phoenix / etc. |
| C2 | Reconstruct the span tree | `code` | |
| C3 | Render for human, or feed to V15 judge, or feed to V17 metric pipeline | `code` *or* `LLM` (V15) | V15 / V17 |

**Skeleton** — wiring only; emission is all `code`. The wrapped LLM call inside `with_span` is the agent's own LLM step:

```
# Instrumented LLM call — the wrapper is code; the inner call is the agent's LLM step
def call_llm(prompt, model):
    with tracer.start_as_current_span("llm_call") as span:                # code  — OTel SDK
        span.set_attribute("gen_ai.system", provider)                      # code  — GenAI semconv
        span.set_attribute("gen_ai.request.model", model)
        span.add_event("prompt", attributes={"summary": redact(prompt)})   # code
        try:
            completion = provider.complete(prompt, model)                  # LLM   — the wrapped call
            span.set_attribute("gen_ai.usage.input_tokens", completion.in_tokens)
            span.set_attribute("gen_ai.usage.output_tokens", completion.out_tokens)
            span.add_event("completion", attributes={"summary": redact(completion.text)})
            return completion
        except Exception as e:
            span.record_exception(e); span.set_status(ERROR)               # code
            raise

# Instrumented tool call
def call_tool(name, params):
    with tracer.start_as_current_span("tool_call") as span:               # code
        span.set_attribute("tool.name", name)
        span.set_attribute("tool.params_schema", schema_of(params))        # schema, not values
        result = tools[name](**params)                                     # code  — the actual tool
        span.add_event("result", attributes={"summary": summarise(result)})
        return result

# Top-level agent invocation — opens the root span; all child calls inherit context
def run_agent(task):
    with tracer.start_as_current_span("agent_invocation") as root:
        root.set_attribute("agent.id", AGENT_ID)
        root.set_attribute("agent.version", AGENT_VERSION)
        root.set_attribute("task.id", task.id)
        return agent.step(task)                                            # LLM/code mixed; all spans nest under root
```

**The LLM sessions.** V14's emission pipeline has **no LLM sessions of its own** — it is pure instrumentation. The `LLM` markers above refer to the agent's *own* LLM calls, which V14 wraps; V14 itself does not call any model. If a downstream Trace Analyser uses V15 (LLM-as-Judge) to score sampled traces, that judge session is documented in V15's page, not here.

**Specialist-model note.** No model required. V14's build dependencies are *infrastructure*, not model choices: an OTel SDK appropriate to your stack, a Collector (`opentelemetry-collector-contrib` or a vendor agent), and a Backend (Jaeger, Tempo, Phoenix, Honeycomb, Logfire, Datadog APM, or equivalent). The choice of OTel GenAI Semantic Conventions as the attribute schema is the single decisive build choice — every other choice (which backend, which sampler, which exporter) is reconfigurable.

## Open-Source Implementations

- **OpenTelemetry GenAI Semantic Conventions** — [`github.com/open-telemetry/semantic-conventions`](https://github.com/open-telemetry/semantic-conventions/tree/main/docs/gen-ai) — the canonical specification (`gen_ai.*` attributes for LLM calls, tool calls, agents). Referenced by every implementation below.
- **OpenLLMetry** — [`github.com/traceloop/openllmetry`](https://github.com/traceloop/openllmetry) — Apache-2.0 OTel-native instrumentation for LLM applications (Python, with JS / Go / Ruby siblings); auto-instruments OpenAI, Anthropic, vector DBs, frameworks; exports to any OTel backend.
- **OpenLIT** — [`github.com/openlit/openlit`](https://github.com/openlit/openlit) — Apache-2.0 OTel-native observability platform for GenAI; one-line auto-instrumentation across 50+ providers, frameworks, vector DBs, GPUs; built-in evaluations.
- **Arize Phoenix** — [`github.com/Arize-ai/phoenix`](https://github.com/Arize-ai/phoenix) — open-source AI observability platform (tracing, evals, datasets, experiments); built on OTel + OpenInference; runs locally or self-hosted.
- **OpenInference** — [`github.com/Arize-ai/openinference`](https://github.com/Arize-ai/openinference) — complementary semantic-convention spec and instrumentation set (the substrate Phoenix uses); standardises LLM-specific attribute naming on top of OTel.
- **Pydantic Logfire** — [`github.com/pydantic/logfire`](https://github.com/pydantic/logfire) — Python SDK (MIT-licensed) wrapping OpenTelemetry with Python-centric ergonomics; sends to the Logfire backend or any OTel-compatible store; rich agent and Pydantic AI integration.
- **LangSmith SDK** — [`github.com/langchain-ai/langsmith-sdk`](https://github.com/langchain-ai/langsmith-sdk) — client SDK for the LangSmith platform; framework-agnostic tracing (OpenAI, Anthropic, LangChain, LlamaIndex). Backend is proprietary; SDK is open-source.

## Known Uses

- **LangGraph / LangChain production deployments** — trace agent runs to LangSmith for debugging and evaluation as a default.
- **Anthropic and OpenAI customers using Phoenix / Logfire / Honeycomb** — OTel-based tracing across SDK-direct and framework-mediated agent calls.
- **Enterprise multi-agent systems** — OTel context propagation across A2A (I6) and MCP (I3) boundaries gives end-to-end visibility through orchestrator-worker hierarchies.
- **Regulated deployments (healthcare, finance, legal)** — V14 traces serve as the EU AI Act Article 12 record-keeping artifact and as evidence for incident investigations.
- **Coding agents (Claude Code, Cursor, Devin)** — emit structured traces of tool calls, file reads, and edits; the trace is what the developer reads when an action surprises them.

## Related Patterns

- **Required by** all of V1, V2, V5, V7, V9, V15, V16, V17, V18 — each of these either *emits into* V14 (V1 approvals, V5 guard decisions, V7 policy outcomes, V9 budget terminations) or *reads from* it (V15 judges sampled outputs from the trace; V16/V17 use traces as data; V18 analyses simulation traces).
- **Pairs with** K11 Observational Memory — K11 is "the agent's own activity record"; V14 is the system-level trace of that activity. Often the same underlying data, used by two different consumers (the agent's reasoning loop reads K11; humans and analysers read V14).
- **Pairs with** K12 Karpathy Memory — the Curator reads V14 traces and writes structured notes; the trace is the curation substrate.
- **Composes with** O6 / O7 / O17 — multi-agent orchestration requires V14 with distributed context propagation, or each sub-agent's spans float orphaned.
- **Distinct from** narrative logging — application logs are for humans reading in the moment; V14 traces are for machines querying after the fact. They coexist; they do not substitute.
- **Distinct from** V10 Checkpointing — V10 captures agent *state* (so the run can resume); V14 captures agent *history* (so the run can be understood). State vs. story.
- **Distinct from** V11 Error Compaction — V11 compresses errors for the active *context window*; V14 stores the full raw error in the trace. V11 is for the agent's working memory; V14 is for everyone else.
- **Mitigates** A15 Untraced Agent — the canonical anti-pattern V14 exists to prevent.
- **Mitigates** A4 Agent Sprawl and A10 Silent Failure — both are detectable via V14 trace inspection.

## Sources

- OpenTelemetry GenAI Semantic Conventions — [opentelemetry.io/docs/specs/semconv/gen-ai/](https://opentelemetry.io/docs/specs/semconv/gen-ai/) (CNCF, 2024–25).
- 12-Factor Agents — Factor 10 ("Small, focused agents") and the "logs are for people, traces are for machines" principle (Dex Horthy, HumanLayer).
- Anthropic — "Building Effective Agents" (2024) — observability guidance for production agents.
- Composio AI Agent Report 2025 — 88% production-failure analysis; cites lack of observability as a top root cause.
- EU AI Act — Article 12 (record-keeping) and Article 13 (transparency) requirements that V14 satisfies.
- Honeycomb, Grafana Tempo, Datadog APM, Jaeger — pre-LLM tracing infrastructure repurposed for agents; the operational model that V14 extends.
- Zheng et al. (2023) — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (arXiv 2306.05685) — V15, the downstream pattern that consumes V14 data.
