# Category V — Reliability Patterns

A **Reliability pattern** is a design pattern for keeping an LLM system *safe, recoverable, and evaluable* under failure. Reliability patterns separate *the capability the agent has* from *the conditions under which it is allowed to exercise that capability* — and from *the evidence that it did so correctly*.

## Usage

A capable LLM, given a tool and a task, will eventually do something irreversible, expensive, unbounded, ungrounded, or unobservable. The failure modes are not exotic: the loop that never terminates, the prompt-injection that exfiltrates a secret, the hallucinated function call, the silent quality regression no one notices for a month. Capability patterns (Signal, Knowledge, Reasoning, Orchestration) do nothing to stop any of these — that is not what they are for.

Reliability patterns are how the system keeps running anyway. They insert *bounds* (around loops, around tool sets, around action space), *gates* (human or programmatic, before irreversible acts), *fallbacks* (a cheaper degraded path when the primary one fails), and *evidence* (logs, evals, judges) so that when a capability pattern misbehaves the blast radius is contained and the failure is visible. They are cross-cutting — every category above this one needs them — and they are the prerequisite for production, not an optimisation applied after. Apply a Reliability pattern whenever:

- an action is irreversible, externally visible, or expensive enough that a single wrong call matters;
- a loop, a tool call count, or a token spend could grow without explicit bound;
- a tool, a corpus, or a piece of content the agent reads is not fully trusted;
- a deployment must produce evidence — for debugging, audit, regression detection, or regulator — that it behaved as intended.

## Forces

Every Reliability pattern resolves the same three forces in tension. A pattern is the right choice for a situation when it balances them in the way that situation demands.

1. **The LLM is the least trustworthy component in the system.** It will hallucinate tool calls, follow instructions embedded in untrusted content, loop on plausible-but-wrong reasoning, and confidently emit malformed output. Anything the LLM touches must be treated as a possibly-hostile, possibly-broken input by whatever runs next. All four failure modes share the same mechanistic root: token generation is stochastic sampling from a learned probability distribution (Mechanism 7). The model does not "decide" to hallucinate or loop; it samples from a distribution that, in the relevant input region, assigns non-trivial probability mass to incorrect tokens. This is what distinguishes the LLM as an untrusted component from, say, a flaky network call — the failure mode is distributional, not deterministic, which is why deterministic external enforcement (V7, V5, V9 as code) is the correct response pattern.

2. **Safety has a cost, and it is paid in latency, throughput, and capability.** Every gate, every guardrail, every validator, every judge, every checkpoint is a step that does not happen in a one-shot call. The wrong dial setting either ships an unsafe agent or ships nothing at all because the workflow has too many hoops. The mechanistic cost compounds geometrically: each additional step that involves an LLM call adds O(n²) attention computation (Mechanism 2) and context growth (Mechanism 3). The safety/capability trade-off is not just wallclock latency — it is a geometric increase in the computational cost of each subsequent reasoning step within the same session.

3. **Failure modes only surface in evidence.** Without traces you cannot debug, without offline evals you cannot detect regressions, without online evals you cannot see drift, without judges you cannot score outputs at scale. A system without observability is not *unreliable* — it is *not knowably reliable*, which is operationally the same thing.

A Reliability pattern is, in each case, a disciplined answer to one question: how to let the agent do its work, while guaranteeing that what it does is bounded, recoverable, and inspectable.

## Structure

All Reliability patterns share one skeleton. They wrap a capability — an LLM call, a tool call, a loop, a whole agent — in an *envelope* of policy, monitoring, and evidence:

```
                  ┌──────── Policy ────────┐
                  │ (gates, bounds, rules) │
   Input ────▶    │                        │   ────▶ Output
                  │   Capability (LLM,     │
                  │   tool, loop, agent)   │
                  │                        │
                  └──────── Evidence ──────┘
                    (traces, evals, judges)
```

Patterns differ in *which envelope they tighten* — the human gate around an irreversible action (V1, V2), the architectural split that prevents capability and adversarial input co-existing (V3, V4), the input/output filters around a single call (V5, V6, V20), the sandbox around a tool (V7, V8), the bound around a loop (V9), the externalised state around a session (V10, V11, V12), the cap on tool count (V13), the fallback for when any of these trips (V19), the trace and judge that capture what happened (V14–V18). The three sub-bands below group the patterns by the question they answer: how to *prevent* harm at the architecture layer (V-A), how to *contain and recover* from failure at the operational layer (V-B), and how to *see and score* what the system is actually doing (V-C). They are not alternatives. A production system instantiates a pattern from each band at once — V-A so the worst outcomes are unreachable, V-B so the recoverable ones are recovered from, V-C so anything else is at least visible.

## Examples

**V-A — Safety and Security.** Architecture-level prevention: keep dangerous combinations from existing in the first place.
- **V1 Human-in-the-Loop** — block before an irreversible action until a human approves.
- **V2 Human-on-the-Loop** — let the agent act; a human watches the trace and can interrupt.
- **V3 Rule of Two (Lethal-Trifecta Prevention)** — flag any agent that holds private data + untrusted input + external comms simultaneously.
- **V4 Dual LLM** — split into a Privileged LLM (data + tools, no untrusted content) and a Quarantined LLM (untrusted content, no tools).
- **V5 Guardrail Layering** — external code-enforced checks at four points: user input, tool call, tool response, final output.
- **V6 Prompt Injection Shield** — sanitise, re-anchor, and constrain the action space so adversarial text cannot hijack goals.
- **V7 AgentSpec / Declarative Governance** — operate the agent under an external policy artefact, enforced outside the LLM.
- **V8 Tool Sandboxing** — run every tool, especially LLM-generated code, in an isolated environment with hard resource limits.

**V-B — Operational Reliability.** Containment and recovery: bounded loops, durable state, validated I/O, declared fallbacks.
- **V9 Bounded Execution** — cap iterations, tool calls, tokens, time, and cost on every loop.
- **V10 Checkpointing** — persist working state at every meaningful step so any failure is resumable.
- **V11 Error Compaction** — replace raw errors in context with compact, dedup-aware summaries.
- **V12 Stateless Reducer** — design the agent as a pure function `(state, input) → (output, state')` with no hidden state.
- **V13 Tool Budget** — cap the number and schema footprint of tools per agent (typically <15, hard ceiling ~40).
- **V19 Fallback / Graceful Degradation** — declare a pre-approved degraded path for every primary-path failure mode.
- **V20 Schema Validation** — validate every model output against a declared schema and re-prompt on failure until conformance or budget exhaustion.

**V-C — Observability and Evaluation.** Evidence: traces, judges, and eval harnesses that make behaviour knowable.
- **V14 Trajectory Logging** — emit a complete, OTel-compliant trace of every decision, call, and intermediate output.
- **V15 LLM-as-Judge** — score outputs with a separate LLM call against an explicit rubric.
- **V16 Offline Evaluation** — validate against a curated suite of known scenarios before deployment.
- **V17 Online Evaluation** — sample live traffic, score with reference-free judges, alert on drift.
- **V18 Agent Simulation** — run the whole agent against synthetic users, tools, and worlds before production.

## See also

- **Categories I–IV** — Signal, Knowledge, Reasoning, Orchestration each define capabilities; this category defines the conditions under which those capabilities are safe to deploy. **S9 Constitutional Framing** (soft, in-prompt) pairs with **V7 AgentSpec** (hard, external) — see CRITICAL 3 in `CONFLICTS.md`.
- **Cross-cutting reach** — every loop needs V9; every CodeAct (R13) needs V8 (CRITICAL 5); every Constitutional Self-Alignment (H5) needs V1 (CRITICAL 7); every MCP deployment (I3) is in tension with V13 (CRITICAL 6). The full map is in `CONFLICTS.md`.

---

## Quick Reference

### V-A — Safety and Security

| # | Pattern | Also Known As | Intent |
|---|---|---|---|
| V1 | **Human-in-the-Loop** | Approval Gate | Block on irreversible, novel, or high-blast-radius actions |
| V2 | **Human-on-the-Loop** | Monitoring Mode | Agent acts autonomously; human monitors and can interrupt |
| V3 | **Rule of Two** | Lethal Trifecta Guard | Flag agents with private data + untrusted content + external comms |
| V4 | **Dual LLM** | Privilege Separation | Quarantined LLM for untrusted data; privileged LLM for actions |
| V5 | **Guardrail Layering** | Defense in Depth | Safety checks at input, pre-call, post-call, and output |
| V6 | **Prompt Injection Shield** | Input Sanitisation | Structural and positional defences against injection |
| V7 | **AgentSpec** | Policy as Code | Declarative, out-of-prompt, deterministic policy enforcement |
| V8 | **Tool Sandboxing** | Isolated Execution | Confine LLM-generated code to restricted environment |

### V-B — Operational Reliability

| # | Pattern | Also Known As | Intent |
|---|---|---|---|
| V9 | **Bounded Execution** | Circuit Breaker | Hard caps on steps, cost, wall-time — required for every loop |
| V10 | **Checkpointing** | State Snapshot | Replayable agent state; recovery without restart |
| V11 | **Error Compaction** | Error Summarisation | Compress errors into compact structured signals |
| V12 | **Stateless Reducer** | Pure Agent | Deterministic, replayable summary of accumulated state |
| V13 | **Tool Budget** | Schema Budget | Limit active schema tokens — every schema token costs n² attention |
| V19 | **Fallback** | Graceful Degradation | Cheaper degraded path for every primary-path failure mode |
| V20 | **Schema Validation** | Structured Output | Validate output against schema; re-prompt on failure |

### V-C — Observability and Evaluation

| # | Pattern | Also Known As | Intent |
|---|---|---|---|
| V14 | **Trajectory Logging** | Agent Tracing | OTel-compatible trace of every call, action, observation |
| V15 | **LLM-as-Judge** | AI Evaluator | Second model evaluates quality against defined rubrics |
| V16 | **Offline Eval** | Regression Testing | Batch evaluation against held-out cases before deployment |
| V17 | **Online Eval** | Production Monitoring | Real-time quality metrics in production |
| V18 | **Agent Simulation** | Sandbox Testing | Simulated environment for pre-deployment stress testing |

---

## V1 — Human-in-the-Loop

Insert mandatory human review and approval at defined decision boundaries before the agent proceeds — the agent *blocks* until a human approves, rejects, or modifies the plan.

**Full entry:** [`V1-Human-in-the-Loop.md`](V1-Human-in-the-Loop.md) — *required by H5 Constitutional Self-Alignment for every principle change (see CRITICAL 7 in `CONFLICTS.md`); required by H8 Meta-Agent Self-Modification for any significant behavioural change.*

---

## V2 — Human-on-the-Loop

Let the agent act autonomously within its scope while a human watches the trace in real time, ready to interrupt, redirect, or override — so oversight stays continuous without blocking every step.

**Full entry:** [`V2-Human-on-the-Loop.md`](V2-Human-on-the-Loop.md)

---

## V3 — Rule of Two (Lethal-Trifecta Prevention)

Audit every agent for the simultaneous presence of three capabilities — private-data access, untrusted-content exposure, and external communication — and treat any agent that holds all three as unsafe until at least one is broken by a mitigation.

**Full entry:** [`V3-Rule-of-Two.md`](V3-Rule-of-Two.md) — *detection only; requires V4, V6, or V8 as mitigation.*

---

## V4 — Dual LLM

Split the agent into two LLM sessions — a Privileged LLM that holds private data and tool access but never sees untrusted content, and a Quarantined LLM that processes untrusted content but holds no private data and no tools — so the capability to act never co-exists with the input that might hijack it.

**Full entry:** [`V4-Dual-LLM.md`](V4-Dual-LLM.md)

---

## V5 — Guardrail Layering

Apply external, code-enforced safety and validation checks at four distinct points in the agent's execution — user input, before each tool call, after each tool response, and on the final output — so that no single failure point can compromise the system.

**Full entry:** [`V5-Guardrail-Layering.md`](V5-Guardrail-Layering.md)

---

## V6 — Prompt Injection Shield

Sanitise inputs, constrain the action space, and re-anchor instructions so adversarial text embedded in untrusted content cannot hijack the agent's goals.

**Full entry:** [`V6-Prompt-Injection-Shield.md`](V6-Prompt-Injection-Shield.md)

---

## V7 — AgentSpec / Declarative Governance

Specify the agent's operating rules — its permissions, prohibitions, and obligations — as an external declarative artefact, and enforce them at runtime in a policy engine that runs *outside* the LLM and cannot be overridden by prompt manipulation.

**Full entry:** [`V7-AgentSpec.md`](V7-AgentSpec.md) — *the hard counterpart to S9 Constitutional Framing; see CRITICAL 3 in `CONFLICTS.md`.*

---

## V8 — Tool Sandboxing

Run every agent-invoked tool — especially LLM-generated code — inside an isolated execution environment with hard, explicit limits on filesystem, network, processes, memory, time, and cost, so a reasoning error or a successful prompt injection has nowhere to escape to.

**Full entry:** [`V8-Tool-Sandboxing.md`](V8-Tool-Sandboxing.md) — *required by R13 CodeAct in any production or shared environment (CRITICAL 5).*

---

## V9 — Bounded Execution

Wrap every agent loop in a hard envelope of iteration, tool-call, token, time, and cost caps — so a wrong turn becomes a graceful termination instead of a runaway invoice.

**Full entry:** [`V9-Bounded-Execution.md`](V9-Bounded-Execution.md)

---

## V10 — Checkpointing

Persist the agent's complete working state to an external durable store at every meaningful step, so any failure, interruption, or human pause can be resumed — or rolled back — from the last known-good snapshot rather than restarted from zero.

**Full entry:** [`V10-Checkpointing.md`](V10-Checkpointing.md) — *12-Factor Agents Factor 5 (Unify execution state and business state) and Factor 6 (Launch / pause / resume with simple APIs). Composes with V12 Stateless Reducer by externalising state (CRITICAL 8).*

---

## V11 — Error Compaction

Replace raw errors in the agent's working context with compact, dedup-aware summaries that preserve the diagnostic signal at a fraction of the token cost.

**Full entry:** [`V11-Error-Compaction.md`](V11-Error-Compaction.md) — *operates in-context; pairs with V14 Trajectory Logging, which retains the full error in the audit log.*

---

## V12 — Stateless Reducer

Design the agent as a pure function of its inputs — `(state, input) → (output, state')` — with no hidden internal state, so every invocation is reproducible, retryable, parallelisable, and trivially checkpointable.

**Full entry:** [`V12-Stateless-Reducer.md`](V12-Stateless-Reducer.md) — *composes with V10 Checkpointing once state is explicitly externalised (CRITICAL 8).*

---

## V13 — Tool Budget

Cap the number and total schema footprint of tools any single agent can see at once — typically below fifteen, never above forty — so the model can actually choose the right tool, and the context window is not consumed by tool definitions before the work begins.

**Full entry:** [`V13-Tool-Budget.md`](V13-Tool-Budget.md) — *in direct tension with I3 MCP Server (CRITICAL 6 in `CONFLICTS.md`); MCP's ecosystem richness is what V13 is bounding.*

---

## V14 — Trajectory Logging

Emit a complete, structured, OpenTelemetry-compliant trace of every decision, LLM call, tool invocation, policy check, and intermediate output the agent makes during a task — so the run can be replayed, debugged, audited, and evaluated long after it finishes.

**Full entry:** [`V14-Trajectory-Logging.md`](V14-Trajectory-Logging.md) — *the substrate every other observability and evaluation pattern reads from (V15–V18) and the audit counterpart to V11.*

---

## V15 — LLM-as-Judge

Use a separate LLM call to score the output of another LLM call against an explicit rubric, producing an automated, ground-truth-free verdict on quality.

**Full entry:** [`V15-LLM-as-Judge.md`](V15-LLM-as-Judge.md) — *the evaluator inside V16 Offline Eval, V17 Online Eval, and many R7 Reflexion loops.*

---

## V16 — Offline Evaluation

Validate agent behaviour against a curated suite of known scenarios and reference outputs **before** production deployment, so regressions, drift, and capability gaps are caught against ground truth rather than discovered by users.

**Full entry:** [`V16-Offline-Eval.md`](V16-Offline-Eval.md)

---

## V17 — Online Evaluation

Continuously sample live production traffic, score the sampled outputs with reference-free judges and trace-derived signals, and alert on quality, safety, or cost drift — so degradation that emerges only from real traffic is caught while the system is still running, without waiting for a ground-truth label that will never arrive.

**Full entry:** [`V17-Online-Eval.md`](V17-Online-Eval.md)

---

## V18 — Agent Simulation

Run the whole agent against a synthetic user, synthetic tools, and a synthetic world — then judge how the trajectory unfolded — so emergent, multi-turn, and adversarial failures surface in a sandbox rather than in production.

**Full entry:** [`V18-Agent-Simulation.md`](V18-Agent-Simulation.md)

---

## V19 — Fallback / Graceful Degradation

When the primary execution path fails — a model errors, a circuit breaker trips, a bound is hit, a tool refuses — switch to a pre-declared degraded path (simpler model, cached answer, deterministic rule, or human escalation) instead of returning an error to the user.

**Full entry:** [`V19-Fallback.md`](V19-Fallback.md) — *the recovery action when V9 Bounded Execution, V20 Schema Validation, or any V-A safety gate trips; declared per failure mode at design time.*

---

## V20 — Schema Validation

Validate every model output against a declared schema and, on failure, re-prompt the model with the validation error until the output conforms or a retry budget is exhausted.

**Full entry:** [`V20-Schema-Validation.md`](V20-Schema-Validation.md) — *the structured-output counterpart to V5 Guardrail Layering's output-stage check; falls back via V19 when the retry budget is exhausted.*
