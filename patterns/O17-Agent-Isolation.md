# O17 — Agent Isolation

> Delegate a self-contained sub-task to a sub-agent invocation that runs in a **fresh, isolated context window** containing only the brief and the inputs that sub-task needs — then discard that context once the sub-agent returns, integrating only the result.

**Also Known As:** Clean Context, Context Quarantine, Fresh Context Delegation, Sub-Agent Spawn, Isolate (Anthropic's "Isolate" strategy), Small Focused Agents (12-Factor Agents, Factor 10).

**Classification:** Category IV — Orchestration · Band IV-C Specialised Coordination · a *context-hygiene* pattern — it does not coordinate workers (that is O6) or run them in parallel (that is O4); it specifies how each sub-agent's context is *bounded* at spawn time. Reclassified from the former K13 because its mechanism is sub-agent delegation, not context curation.

---

## Intent

When a sub-task does not need the parent's accumulated context, spawn the sub-agent with a fresh window holding only that sub-task's brief and inputs — so the sub-agent reasons over a tight, on-topic context instead of inheriting whatever the parent happens to be carrying.

## Motivation

**Why isolation is mechanically required (mechanism 6 + mechanism 2).** Each agent invocation has its own KV cache, its own sequence length, and its own $O(n^2)$ attention compute budget (mechanism 2). When a worker is given the orchestrator's full accumulated context rather than an isolated brief, the worker's $n$ includes all the orchestrator's reasoning history — paying $O(n^2)$ over a large mixed context rather than $O(n^2)$ over a small task-specific brief. The quality and cost benefit of multi-agent decomposition depends directly on this context bounding (mechanism 6). O17 is the enforcement mechanism: without it, context is shared, $n$ grows as if single-agent, and the architectural benefit of decomposition is defeated.

A long-running agent session accumulates context: tool returns, partial drafts, retrieved documents, sibling sub-task results, scratchpad reasoning. Almost none of that is relevant to any given sub-task. When a sub-task is then run *in* that parent's context — the natural thing to do if you simply make a tool call or a follow-up prompt — three failure modes appear:

- **Attention dilution.** Modern long-context models do degrade with irrelevant tokens. A focused sub-task processed in a 100k-token accumulated context is empirically less reliable than the same sub-task processed in a clean 5k-token brief — the KV cache grows monotonically with the accumulated history, and each generation step queries all cached K-vectors at O(n²) cost, diluting attention over an increasingly large irrelevant context (mechanism 2, mechanism 3). Anthropic measured this directly: their multi-agent research system, where each sub-agent operates in its own context, outperformed a single-agent baseline by ~90% on internal research evaluations, with the gain "strongly linked to the ability to spread reasoning across multiple independent context windows" — a direct consequence of context bounding (mechanism 6).
- **Context pollution.** Earlier tool returns or sibling sub-task outputs can mislead the sub-agent — irrelevant facts get treated as relevant, prior errors propagate, the sub-task quietly inherits the parent's frame. The sub-agent then optimises for the wrong thing.
- **Cost and latency at scale.** Every token in the prefix is paid for on every call. If the parent has 80k tokens of history and a sub-task only needs a 3k-token brief, running the sub-task in the parent context pays 27× more per call than necessary — because prefill cost is quadratic in sequence length (mechanism 2), not linear.

The obvious response is "compress the context before the sub-task" — that is what **K6 Context Compression** does. But compression keeps a *single shared* context: the parent loses information, every subsequent sub-task still sees the compressed digest, and parallel sub-tasks must share one window. The structural move that resolves all three failure modes at once is different: **don't compress, isolate**. Spawn the sub-agent in a separate context window. Pass it only what it needs. Throw the sub-agent's context away when it returns; keep only the result.

That is the pattern. Anthropic's context-engineering writing names "Sub-agent Architectures" as one of three core techniques for long-horizon tasks (alongside Compaction and Structured Note-Taking); the 12-Factor Agents methodology names it Factor 10 ("Small, Focused Agents"). Both arrive at the same structural answer to the same problem: agents that try to do everything in one context fail; agents that delegate to fresh sub-contexts scale. O17 is the codification of that answer as a stand-alone pattern — distinct from O6 (which says *who* does the work) and O4 (which says *how many* run at once), it specifies *what context each sub-agent starts with*.

## Applicability

Use Agent Isolation when:

- a sub-task is self-contained — its inputs can be enumerated explicitly and do not require the parent's accumulated reasoning;
- the parent's context contains material the sub-agent should *not* see (noise, prior attempts, sensitive data, conflicting frames);
- sub-tasks will run in parallel — each needs its own window anyway (composes naturally with **O4 Parallelization**);
- the parent's context is approaching its window limit and the sub-task's work would push it over;
- security or audit requires that certain operations run in a contained context with restricted tools.

Do not use it when:

- the sub-task genuinely depends on the parent's accumulated reasoning — extracting the relevant subset would lose more than the isolation gains; keep the work in the parent (**O1 Single Agent**) or hand it off explicitly with **O15 Agent Handoff**;
- the same compressed context will serve the parent and several sub-tasks — use **K6 Context Compression** to shrink the shared window instead;
- the sub-task is a single deterministic tool call — wrap it as an **I2 Function Call**, no sub-agent needed;
- you have not bounded the spawning loop — a parent that can spawn sub-agents without a hard cap is **A3 Uncontrolled Recursion** with multipliers; pair with **V9 Bounded Execution** or do not deploy.

## Decision Criteria

O17 is right when the sub-task's required inputs are enumerable, the parent's accumulated context is large or polluted, and the spawn-and-discard overhead is justified.

**1. Enumerability test.** Can you write down the sub-agent's full brief in under ~5k tokens (instructions + inputs + relevant context)? If yes, isolation is cheap and clean. If no — if you find yourself wanting to pass "and also everything the parent knows" — the sub-task is not self-contained; keep it in the parent or restructure into **O15 Agent Handoff** with a structured handoff package. Use as a hard test: if the brief cannot be written down, the sub-task is not isolated.

**2. Context-bloat threshold.** Measure parent context size at the moment of delegation. **Parent ≥ 30% of window** with a sub-task that only needs a small fraction — isolation pays for itself immediately in attention quality and per-call cost. **Parent ≥ 70% of window** — isolation is mandatory; running the sub-task in-context risks overflow.

**3. Parallelism check.** Will two or more sub-tasks run concurrently? Parallel execution *requires* separate contexts — O17 is not optional, it is implied by **O4 Parallelization**. Sequential sub-tasks can in principle share the parent context, but lose the cost and focus benefits of isolation.

**4. Pollution audit.** Does the parent context contain material the sub-agent *should not see* — failed prior attempts, sensitive data, a conflicting frame from a sibling sub-task, an over-confident wrong answer? If yes, isolation is the correct quarantine boundary. (Anthropic note that sub-agents with isolated context "avoided clutter and contradictions, keeping each agent lean and focused.")

**5. Loop-bound discipline.** Pair with **V9 Bounded Execution** — a hard cap on the number of sub-agents the parent can spawn per task. Without it, a misbehaving orchestrator (**O6**) can fan out indefinitely; cost and latency cascade. Set the cap in the orchestrator's prompt *and* as a runtime guard.

**Quick test — O17 is the right pattern when:**

- the sub-task's brief is enumerable in a small, self-contained context, *and*
- the parent's accumulated context is large or contains material the sub-agent should not inherit, *and*
- the sub-agent's result can be integrated by the parent without needing the sub-agent's intermediate reasoning, *and*
- the spawning loop is hard-bounded (**V9**).

If any condition fails, the alternatives are: **O1 Single Agent** if everything fits one context cleanly; **K6 Context Compression** if a single shared but compressed context will do; **O15 Agent Handoff** if the receiver does need much of the sender's state and a structured package is the right surface; **O6 Orchestrator-Workers** if the question is *who* coordinates, not *what context* each worker starts with — O6 typically uses O17 inside it.

## Structure

```
   Parent agent (accumulated context: tool returns, drafts, sibling results, …)
                       │
                       │ 1. Identify isolable sub-task
                       │ 2. Prepare minimal brief: instructions + inputs + relevant facts only
                       ▼
              ┌────────────────────┐
              │  Spawn sub-agent   │  fresh context window — only the brief inside
              │  (separate session)│
              └─────────┬──────────┘
                        │
                        ▼
              ┌────────────────────┐
              │   Sub-agent runs   │  reasons / acts on its tight context (often R4 inside)
              └─────────┬──────────┘
                        │ result (compact: answer, structured payload, citation set)
                        ▼
              ┌────────────────────┐
              │   Sub-agent ends   │  context discarded — intermediate reasoning not returned
              └─────────┬──────────┘
                        │ result only
                        ▼
   Parent agent (integrates result; sub-agent's context is never seen)
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Parent (Spawning) Agent** | the decision to delegate, and what the sub-agent gets | parent context + sub-task → spawn call (brief) | dump its full context into the sub-agent — that re-introduces every failure mode the pattern exists to prevent. |
| **Brief Builder** | constructing the sub-agent's starting context | sub-task spec + selected parent state → minimal, self-contained brief | guess what the sub-agent might need "just in case"; under-isolation is recoverable, over-stuffing destroys the pattern. |
| **Sub-Agent** | executing the sub-task in its fresh context | brief → result (and only the result) | persist anything beyond its lifetime, or rely on parent-visible state not passed in the brief; it sees only what the brief contains. |
| **Result Channel** | the narrow return surface | sub-agent's intermediate work → compact, structured result | leak the sub-agent's full transcript into the parent; only the contracted result returns. The contract is the discipline. |
| **Spawn Guard** *(V9)* | the cap on sub-agent count and depth | spawn requests → admit or deny | be optional. Without it, the pattern is **A3 Uncontrolled Recursion** with multipliers. |

The defining responsibility split is **Brief Builder** vs **Sub-Agent**: the Brief Builder decides *what context exists* for the sub-task; the Sub-Agent reasons over it. That separation is what makes the isolation real — if the sub-agent could pull context from the parent on demand, there is no isolation, only the illusion of it.

## Collaborations

The Parent agent reaches a point in its work where the next sub-task can be specified completely: a search to run, a document to summarise, a piece of code to write, a fact to verify. It hands the sub-task spec to the Brief Builder, which assembles a minimal brief — the instructions, the inputs, and only the slice of parent state the sub-agent actually needs. The Spawn Guard checks the cap (count and depth) and admits the spawn. The Sub-Agent runs in its own fresh context, reasoning over only the brief; it typically runs an **R4 ReAct** inner loop on whatever tools it was given. When it finishes, it returns a single compact result via the Result Channel. The Parent integrates that result into its own context; the Sub-Agent's intermediate reasoning, tool returns, and scratchpad never enter the parent and are discarded with the sub-agent's session.

## Consequences

**Benefits**
- Sub-agent attention is concentrated on the right inputs — empirically a large quality win on complex sub-tasks (Anthropic's 90%+ improvement).
- Per-sub-task token cost is far lower than running the sub-task in a polluted parent context.
- Enables parallelism — independent sub-agents can run concurrently (composes with **O4**).
- Provides a quarantine boundary for sensitive or contaminated context.
- Keeps the parent's context lean — the parent sees only results, not the work that produced them.

**Costs**
- Brief construction is real work — under-specification produces wrong-assumption failures.
- Per-spawn overhead — system prompt and tool-set must be set up for each new session.
- Results-only return means the parent cannot easily debug the sub-agent's reasoning; observability requires explicit logging (**V14**).
- Cross-sub-agent coordination is structurally hard — each is isolated; coordination has to happen in the parent or via a shared store.

**Risks and failure modes**
- *Under-isolation* — the sub-agent's brief is missing context it needed, so it makes wrong assumptions confidently. The most common failure mode; fix by reviewing failures and adjusting the Brief Builder.
- *Over-isolation* — passing too much "just in case" reintroduces the bloat the pattern is meant to remove; the spawn becomes a copy of the parent with extra steps.
- *Spawn storms* — without **V9**, a misbehaving orchestrator fans out indefinitely. Costs and latency cascade.
- *Result-channel ambiguity* — if the contract on what the sub-agent returns is loose, parents and sub-agents drift on what counts as "the result."
- *Lost observability* — if the sub-agent's trajectory is discarded entirely, debugging is impossible; always log it (**V14**) even though the parent does not consume it.

## Implementation Notes

- The Brief Builder is the heart of the pattern. Treat it as a Signal-layer artefact (**S6 Output Template** for the brief's shape; **S5 Constraint Framing** for the "what is in scope" rules). Reviewing failed sub-agent runs is reviewing the Brief Builder.
- Default to **fresh system prompt per sub-agent** — do not inherit the parent's system prompt. The sub-agent should be told what *it* does, not what the parent is in the middle of.
- Restrict the sub-agent's tool set to what its sub-task requires. Smaller tool sets improve selection accuracy and reduce attack surface.
- Define the Result Channel as a **structured contract**, not free text. The parent should know the shape it will receive (a JSON object, a fixed set of fields). Loose results lead to integration bugs.
- Always log the sub-agent's full trajectory (**V14 Trajectory Logging**) even though the parent does not read it — debugging an isolated sub-agent requires the trace.
- Bound the spawning loop hard (**V9**): a per-task cap (e.g. "no more than 6 sub-agents") *and* a depth cap (e.g. "sub-agents may not spawn their own sub-agents") unless hierarchical recursion is explicit (**O7**).
- The classic production composition is **O6 + O4 + O17**: the orchestrator (**O6**) decides sub-tasks, **O4** runs them in parallel, **O17** is *how each worker's context is set up*. Without O17, the workers all share the orchestrator's context and the pattern's quality gain is lost.
- O17 inside O6 is the default; O17 *without* O6 is rarer — a single agent that occasionally delegates a self-contained side-task to a fresh sub-agent is a legitimate use, but most O17 deployments are inside an orchestrator-workers structure.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** O17 is most often a sub-component of **O6 Orchestrator-Workers** (the orchestrator decides *which* sub-tasks, O17 specifies *how each worker's context is built*), and it composes with **O4 Parallelization** (independent isolated sub-agents run concurrently). The Brief Builder draws on **S6 Output Template** for brief shape and **S5 Constraint Framing** for scope rules. The Spawn Guard is an instance of **V9 Bounded Execution**. Each sub-agent typically runs **R4 ReAct** internally on its restricted tool set. **V14 Trajectory Logging** is mandatory.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Identify sub-task as isolable (enumerability test) | `code` (or `LLM`) | parent / orchestrator |
| 2 | Build minimal brief: instructions + inputs + relevant facts only | `LLM (or rule)` | Brief Builder session; S5, S6 |
| 3 | Spawn-cap check: count, depth | `code` | V9 |
| 4 | Spawn sub-agent in fresh context with brief and restricted tool set | `code` | — |
| 5 | Sub-agent runs (typically an R4 loop on its tools) | `LLM` | Sub-Agent session; R4 |
| 6 | Sub-agent returns structured result via Result Channel | `code` | result contract (S6) |
| 7 | Log sub-agent trajectory (not returned to parent) | `code` | V14 |
| 8 | Parent integrates result; sub-agent context is discarded | `code` | — |

**Skeleton** — wiring only; each `# LLM` line is a configured session:

```
delegate(parent_state, subtask_spec):
    if not is_isolable(subtask_spec):                  # code — enumerability test
        return None                                     # fall back to in-parent or O15
    brief = BriefBuilder(parent_state, subtask_spec)    # LLM — minimal brief, S6 shape
    SpawnGuard.admit_or_raise(count, depth)             # code — V9 cap
    sub = new_session(                                  # code — fresh window
        system = subtask_spec.system_prompt,            #        not inherited from parent
        tools  = subtask_spec.tools,                    #        restricted set
    )
    result, trajectory = sub.run(brief)                  # LLM — sub-agent (often R4 inside)
    log_trajectory(trajectory)                           # code — V14, not returned to parent
    return result                                        # code — only the result re-enters parent
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Brief Builder** | small fast generalist; *or* a deterministic templater for known sub-task types | role: *"you build minimal self-contained briefs for sub-agents"*; the brief schema (**S6** template — instructions, inputs, in-scope facts, out-of-scope facts, result contract); the scope rules (**S5**) — what *not* to include | the sub-task spec + relevant parent state |
| **Sub-Agent** | depends on sub-task complexity — often a strong generalist for hard sub-tasks, a small fast model for narrow ones; **must be a separate session, fresh system prompt, restricted tools** | sub-task role; restricted tool descriptions; the result contract it must return | the brief (its entire starting context) |

**Specialist-model note.** No fine-tuned specialist is required. Two structural choices dominate quality:

- **The Sub-Agent must be a separately configured session, not a follow-up call on the parent.** Same model is fine; it must have its own system prompt, fresh context, and restricted tool set. A "sub-agent" that is actually a parent-context call defeats the pattern.
- **The Brief Builder is the lever.** Most O17 failures are Brief Builder failures: too little, the sub-agent hallucinates context; too much, the pattern is undone. Version the Brief Builder's template (**S6**) and review failed sub-agent runs against it.

## Open-Source Implementations

- **Claude Code Task tool / Claude Agent SDK** — [`github.com/anthropics/claude-agent-sdk-demos`](https://github.com/anthropics/claude-agent-sdk-demos) — Anthropic's reference. The Task tool spawns a sub-agent in a fresh, isolated context with a restricted tool set; Claude Code's multi-agent research demo is the canonical production embodiment. Each sub-agent's context is discarded after it returns.
- **OpenAI Agents SDK** — [`github.com/openai/openai-agents-python`](https://github.com/openai/openai-agents-python) — supports two delegation modes: *agents-as-tools* (manager retains control; sub-agents run in isolated context per call) and *handoffs* (peer agents take over; closer to **O15**). The agents-as-tools mode is the O17 pattern; `input_filter` controls what context the sub-agent sees.
- **LangGraph `Send` API** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — `Send` dispatches work to nodes "each with isolated state … no risk of shared state pollution or accidental interference." The map-reduce / fan-out idioms are O17 + O4 in one mechanism.
- **12-Factor Agents (Factor 10)** — [`github.com/humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) — methodology repo. `content/factor-10-small-focused-agents.md` is the canonical articulation of "small, focused agents" chained into deterministic DAGs rather than one monolithic context.

## Known Uses

- **Anthropic Multi-Agent Research System** — the lead-researcher / sub-agent architecture. Sub-agents operate in isolated contexts, returning condensed findings to the lead. Reported >90% improvement over single-agent baseline on internal research evaluations.
- **Claude Code** — the Task tool spawns sub-agents with fresh contexts for parallel exploration, code review, and background tasks; each sub-agent's context is discarded after it returns its summary.
- **LangGraph map-reduce production systems** — `Send`-based fan-out is the standard idiom for parallel research, parallel evaluation, and any "process N independent items" workload.
- **OpenAI Agents SDK production deployments** — agents-as-tools for sub-task delegation in customer-support, research, and coding agents.

## Related Patterns

- **Composes with** **O6 Orchestrator-Workers** — the production default: O6 chooses what each worker does; O17 specifies that each worker starts with a fresh, minimal context. The canonical stack is **O6 + O4 + O17**.
- **Composes with** **O4 Parallelization** — parallel sub-agents *must* be in isolated contexts; O4 + O17 is one combined mechanism in most frameworks (LangGraph `Send`, Anthropic Task tool).
- **Required by** **V9 Bounded Execution** — a spawning loop without a hard cap is **A3 Uncontrolled Recursion** with multipliers; never deploy O17 without V9.
- **Pairs with** **V14 Trajectory Logging** — the sub-agent's trajectory is not returned to the parent; it must still be logged or debugging is impossible.
- **Distinct from** **K6 Context Compression** — K6 keeps one shared context and shrinks it; O17 splits into multiple isolated contexts. Compose them: compress the parent context, then spawn sub-agents on top.
- **Distinct from** **O15 Agent Handoff** — O15 *transfers* an in-progress interaction with a structured package; O17 *spawns* a fresh sub-task and discards its context on return. O15 is for continuity; O17 is for isolation.
- **Distinct from** **K10–K12 Memory patterns** — those patterns *persist* state across sessions; O17 creates state that is intentionally *discarded*. Sub-agents may still read from a shared K10 store rather than relying solely on the passed brief; the pass-through and the persistence are independent concerns.
- **Sibling of** **O7 Supervisor Hierarchy** — O7 is recursive O6 + O17: each level spawns the next in fresh contexts. Promote from O17-inside-O6 to O7 when worker count grows past ~10.
- **Note on fundamentality** — O17 was originally K13 (Context Isolation, in the Knowledge category). It was reclassified to Orchestration because the *mechanism* is sub-agent delegation, not context curation. K-band patterns shape what a single agent sees; O17 shapes how multiple agents are spawned and how their contexts relate.

## Sources

- Anthropic (2025) — "Effective context engineering for AI agents" — names Sub-agent Architectures as one of three core techniques for long-horizon tasks (alongside Compaction and Structured Note-Taking).
- Anthropic (2025) — "How we built our multi-agent research system" — production embodiment; the lead-researcher / sub-agent architecture and the >90% improvement over single-agent baseline.
- Anthropic (2025) — "Building agents with the Claude Agent SDK" — the Task tool's sub-agent spawn model.
- HumanLayer — *12-Factor Agents*, Factor 10: "Small, Focused Agents" — the principle that agents should be kept to 3–20 steps in narrow scope rather than one monolithic context.
- OpenAI — *Agents SDK* documentation — "Orchestration and handoffs"; the agents-as-tools delegation mode.
- LangChain — *LangGraph* documentation — the `Send` API and map-reduce idioms for isolated-state fan-out.
