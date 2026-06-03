# O6 — Orchestrator-Workers

> A central orchestrator LLM decomposes a goal at runtime, dynamically delegates the resulting sub-tasks to specialised worker LLMs, and synthesises their returns into a final answer — choosing the decomposition each time, instead of following a sequence fixed at design time.

**Also Known As:** Hub-and-Spoke, Lead Agent + Subagents, Orchestrator-Subagent, Lead-Researcher Pattern, Manager-Workers, Dispatcher-Workers. (Anthropic's "Building Effective Agents" calls it *Orchestrator-workers*; its Multi-Agent Research System is the canonical production embodiment.)

**Classification:** Category IV — Orchestration · Band IV-B Agentic patterns · the canonical *dynamic multi-agent* pattern — a single Orchestrator coordinates a flat pool of Workers. Sibling of O7 Supervisor Hierarchy (which is O6 applied recursively).

---

## Intent

Have a central LLM decide *at runtime* how to break a goal into sub-tasks and which worker each sub-task goes to, then collect and synthesise the workers' returns — so the decomposition adapts to the specific input instead of being baked into a pipeline.

## Motivation

Two simpler orchestration patterns sit on either side of O6 and fail on opposite ends.

**O2 Prompt Chaining** fixes the decomposition at design time: step 1 feeds step 2 feeds step 3. This is cheap, testable, and predictable — when the sequence is genuinely the same for every input. But many real tasks resist that. A coding change might touch one file or twenty; a research question might fan out into three subqueries or fifteen; a complex document might need different specialised lenses depending on what it contains. The "right" decomposition is itself a function of the input. O2 cannot make that choice — it has no step that asks *what are the sub-tasks?* It just runs the sub-tasks the developer wrote down.

**O1 Single Agent** can in principle adapt: an R4 ReAct agent with enough tools and a large enough context could decompose-and-execute inside one loop. In practice this collapses at scale. The single agent's context fills with the interleaved details of every sub-task, tool-selection accuracy degrades as the tool catalogue grows, and the trajectory becomes unreadable. Anthropic measured the gain explicitly: an orchestrator (Opus 4) coordinating subagents (Sonnet 4) outperformed a single-agent Opus 4 baseline by ~90% on their internal research evaluation. The reason is structural — separation of *what to do* from *how to do it*, with each side operating on a context tuned to its job.

**Why the quality win is structural, not emergent (mechanism 6).** The improvement is derivable from the cost structure of attention. In a single O1 agent handling a complex task, the KV cache grows as the agent accumulates tool outputs, intermediate reasoning, and conversation history — $n$ grows with every turn, and the $O(n^2)$ attention compute means the model's attention budget is spread across an increasingly diluted context. In O6, the orchestrator's $n$ grows with task assignments and compact worker results only; each worker's $n$ is bounded to its single sub-task and discarded after the worker returns. Each worker operates on a small, high-signal context where the U-shaped attention recall (mechanism 4) has less opportunity to drop critical information. The quality gain is a direct consequence of context bounding (mechanism 6), not a product of model capability differences alone.

Orchestrator-Workers is the pattern that resolves both failures. A central LLM — the Orchestrator — owns one decision: *given this input, what are the sub-tasks, and which worker handles each?* It does not execute them. The Workers — one or many, possibly specialised, often parallel — own the execution: each receives only the context for its sub-task and runs an inner loop (almost always **R4 ReAct**) to completion. A Synthesis step (sometimes a separate agent, sometimes the Orchestrator again) integrates the returns. The decomposition is dynamic; the workers are isolated; the orchestrator is the only place that sees the whole shape. This is the canonical *multi-agent* pattern of the post-2024 production era: every major framework ships it, every survey names it, and the Anthropic Multi-Agent Research System is its reference implementation.

## Applicability

Use Orchestrator-Workers when:

- the decomposition into sub-tasks is *not* the same for every input — the count, type, or ordering of sub-tasks depends on what the input contains;
- sub-tasks benefit from running in isolation (clean contexts, specialised prompts, parallel execution);
- the total work would not fit a single agent's context window or tool budget if attempted as one loop;
- you need a clear coordination point for synthesis, audit, and failure-handling.

Do not use it when:

- the sequence of sub-tasks is fully known and fixed at design time — use **O2 Prompt Chaining**, which is cheaper, more predictable, and easier to test;
- the task is small enough for one agent with a manageable tool set — start with **O1 Single Agent** (the 12-Factor "Factor 10" principle: keep agents small and focused; reach for O6 only when O1 demonstrably fails);
- the sub-tasks are independent *and* enumerable up front — use **O4 Parallelization** directly, no orchestrator required;
- the projected worker count exceeds ~5–10 and they fall into natural groupings — promote to **O7 Supervisor Hierarchy** before the orchestrator's context becomes the bottleneck;
- the loop cannot be bounded — never deploy O6 without **V9 Bounded Execution**; an orchestrator that can spawn workers without a cap is **A3 Uncontrolled Recursion** with multipliers.

## Decision Criteria

O6 is right when the decomposition genuinely varies per input, the worker count stays bounded, and you can afford the orchestration overhead.

**1. Test the decomposition stability.** Sketch ten realistic inputs. For each, write down what the sub-tasks would be. If the lists are essentially the same (same count, same types, same order), the decomposition is *stable* — use **O2 Prompt Chaining** with O4 parallelisation where steps are independent. If the lists differ materially — different sub-task counts, different specialisations, different ordering — the decomposition is *dynamic* and O6 is justified. The honest test: would a developer writing O2 have to leave most of the pipeline as TODOs that the orchestrator fills in?

**2. Bound the worker count.** Count expected workers per run on hard inputs. **N $\leq$ ~5** — O6 with a single flat pool is fine. **N $\approx$ 5–10** — O6 works, but the orchestrator's context is filling fast; consider grouping. **N > 10** — promote to **O7 Supervisor Hierarchy**; one orchestrator coordinating dozens of workers loses track. Anthropic's research system reports orchestrators that spawn excessive subagents on simple queries as the most common early failure — bound the count in the orchestrator's prompt and as a hard cap (**V9**).

**3. Cost the orchestration overhead.** O6 adds at least: one orchestrator call to plan, N worker chains, and one synthesis call. Per-task token cost is typically 3–10$\times$ a single-agent baseline. Pay this when the quality win justifies it. Anthropic measured a 90.2% accuracy gain on multi-step research; whether *your* task earns a 3–10$\times$ cost multiplier depends on the per-task value.

**4. Pick the worker inner pattern.** Workers almost always run **R4 ReAct** internally — the per-step adaptive loop on the worker's tools. If sub-tasks need control flow over multiple tools, **R13 CodeAct** wins ~20pp accuracy. If a sub-task is a single tool call, no loop needed — an **I2 Function Call** is enough. The orchestrator picks the worker; the worker runs its own loop.

**5. Composition stack.** O6 has three near-mandatory companions: **O4 Parallelization** (independent workers run in parallel; sequential workers waste the largest win of the pattern), **O17 Agent Isolation** (each worker gets a fresh context with only its brief; no bleed-through), and **V14 Trajectory Logging** (multi-agent without trace is **A15** with N+1 multipliers). The production composition law: *O6 + O4 + O17 + V9 + V14*. Anything less is a prototype.

**O17 is mechanically required, not optional (mechanism 6).** The quality and cost benefits of O6 depend on each worker having its own bounded seq_len. If workers inherit the orchestrator's context — or share a common context — the $O(n^2)$ attention cost grows as if it were a single agent, and the lost-in-middle degradation (mechanism 4) applies to the full shared context rather than each worker's compact brief. O17 Agent Isolation is the mechanism that enforces the context boundary. Without it, O6 is an organizational pattern that provides orchestration overhead without the structural benefit. The production composition law *O6 + O4 + O17 + V9 + V14* is not a style guide — O17 is load-bearing for the quality claim.

**Quick test — O6 is the right pattern when:**

- the sub-task decomposition varies materially across inputs, *and*
- the worker count per run is bounded (typically $\leq$ ~10), *and*
- the orchestration overhead (3–10$\times$ tokens vs single agent) is justified by the quality gain, *and*
- the loop can be hard-bounded with **V9** and traced with **V14**.

If the decomposition is stable, use **O2 Prompt Chaining**. If the task fits one agent with one tool set, use **O1 Single Agent**. If workers are independent and enumerable, **O4 Parallelization** alone suffices. If worker count exceeds ~10, promote to **O7 Supervisor Hierarchy**. If you cannot bound the loop, do not deploy O6 — the unbounded multi-agent loop is **A3** with multipliers.

## Structure

```
                       Goal
                         │
                         ▼
                  ┌──────────────┐
                  │ Orchestrator │  (one LLM session — plans, delegates, synthesises)
                  └──────┬───────┘
              decompose  │  dispatch  (one brief per worker, no shared context)
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         ┌────────┐ ┌────────┐ ┌────────┐
         │Worker 1│ │Worker 2│ │Worker N│   (fresh isolated context each — O17)
         │  R4    │ │  R4    │ │  R4    │   (R4 ReAct loop on each worker's tools)
         └────┬───┘ └────┬───┘ └────┬───┘   (run in parallel where independent — O4)
              │ result   │ result   │ result
              └──────────┼──────────┘
                         ▼
                  ┌──────────────┐
                  │  Synthesis   │  (Orchestrator again, or separate session)
                  └──────┬───────┘
                         ▼
                       Answer

  Wrapped by V9 Bounded Execution (max workers, max depth, max cost, max time).
  Every Orchestrator call and every Worker trajectory captured by V14 Trajectory Logging.
```

The Orchestrator never executes sub-tasks itself — it only decomposes, dispatches, and synthesises. Workers never see one another or the orchestrator's planning context — they see only their own brief. Synthesis sees the workers' returns but not their internal trajectories.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Orchestrator (LLM)** | the decomposition and dispatch decision | goal + worker catalogue $\to$ list of (worker, sub-task brief) | execute sub-tasks itself, or carry a worker's internal trajectory in its own context. An orchestrator that "helps" a worker by also doing its work has collapsed the separation; the gain over **O1** disappears and the context fills with worker-level detail. |
| **Worker (LLM)** *(one or many; often specialised; usually runs R4 internally)* | executing a single sub-task to completion within its isolated context | sub-task brief + tools $\to$ result | see other workers' contexts, the orchestrator's plan, or the original goal beyond what its brief carries. A worker that reasons about *the whole task* is no longer isolated and **O17** is broken. |
| **Worker catalogue** | the registry of available workers, their specialisations, tools, and contract | — $\to$ structured catalogue passed to Orchestrator | grow unbounded — tool / agent selection accuracy collapses above ~10–15 entries (the same Tool Budget arithmetic as **V13** but applied to *workers*). Above that, promote to **O7**. |
| **Dispatcher** | wiring the orchestrator's decision into actual worker invocations; managing parallel execution and partial failures | (worker, brief) list $\to$ worker results | hide failures from synthesis. A silently-dropped worker return is **A10 Silent Failure**; failed sub-tasks must reach synthesis as errors with their briefs intact. |
| **Synthesis (LLM)** *(often the Orchestrator session reused; sometimes separate)* | integrating worker returns into the final answer | original goal + worker results $\to$ final output | re-run sub-tasks. If synthesis finds a gap, it asks the Orchestrator for another worker round; it does not silently execute the missing work itself. |
| **Bound (V9)** | terminating the loop on max workers / depth / cost / time | run state $\to$ continue / halt | be implicit. An O6 system that "trusts the orchestrator to stop" will, on a hard input, spawn workers indefinitely. The Anthropic team identified this as the most common production failure mode in early multi-agent iterations. |
| **Trajectory logger (V14)** | per-orchestrator and per-worker trace for audit and replay | every LLM call + every dispatch $\to$ log | be optional. Untraced O6 is **A15** with N+1 simultaneous undebuggable agents. |

The defining separation is **Orchestrator $\leftrightarrow$ Worker**: the Orchestrator chooses *what gets done*; the Worker chooses *how to do it*. When that separation collapses — orchestrator executes, worker reasons about the whole task — O6 degrades to a confused **O1** with extra LLM calls.

## Collaborations

A goal arrives at the Orchestrator. It reads the worker catalogue and emits a structured plan: a list of (worker, sub-task brief) pairs. Each brief carries an objective, the relevant context the worker needs, the tools it should use, an output format, and clear boundaries — what's in scope and what isn't. The Dispatcher launches the workers, in parallel where the briefs are independent (the **O4** composition) and with fresh isolated contexts (the **O17** composition). Each Worker runs its own inner loop — typically **R4 ReAct** — over its tools until it emits a final result or the per-worker bound trips. Results return to the Dispatcher; partial failures are surfaced as errors, not hidden. Synthesis then runs: the Orchestrator session is rehydrated with the original goal plus the workers' returns and emits the final answer. If synthesis finds a gap, the loop iterates — another orchestrator round, another worker dispatch — until either the answer is complete or the global bound trips. The Trajectory logger captures every orchestrator call, every dispatch, every worker trajectory.

Two collaboration patterns sit one level up. When the worker count exceeds what one orchestrator can coordinate (~5–10), the pattern promotes to **O7 Supervisor Hierarchy** — the same shape, applied recursively. When a sub-task requires its own multi-agent decomposition, a Worker can itself be an O6 — the recursion is the O6/O7 boundary.

## Consequences

**Benefits**

- Adaptive decomposition: the orchestrator chooses sub-tasks per input, not at design time.
- Specialisation: each worker can have its own model, tools, prompt, and context — fit-to-purpose without polluting other workers.
- Context hygiene: workers see only their briefs; the orchestrator never sees worker-level detail. Solves the "everything in one context" failure mode of large O1 agents.
- Parallelism: independent workers run concurrently (the **O4** composition), cutting wall-clock time substantially.
- The most-deployed multi-agent shape in the post-2024 era: Anthropic, AWS, Microsoft, Google, LangChain, CrewAI all ship it as their canonical multi-agent pattern.
- Measured quality wins: Anthropic reports ~90% improvement over single-agent baselines on multi-step research evaluation.

**Costs**

- Orchestration overhead: at least one orchestrator call to plan, N worker chains, one synthesis call. Typical 3–10$\times$ token cost vs a single-agent baseline. Anthropic estimates multi-agent research consumes ~15$\times$ the tokens of an equivalent single-LLM chat.
- Coordination complexity: dispatching, partial-failure handling, synthesis logic — all code the developer must write and test.
- Context-handoff bugs: the worker brief is the *only* thing the worker sees; if it's under-specified the worker hallucinates assumptions, if it's over-stuffed it carries irrelevant noise. Brief quality is the single largest tuning lever.
- Debugging complexity: a failed run has N+1 trajectories. Without **V14** end-to-end tracing this is hours of guessing.

**Risks and failure modes**

- *Excessive sub-agent spawning* — orchestrator decomposes simple queries into many small workers; cost balloons. Anthropic identified this as the most common early-iteration failure. Fix: bound worker count in the orchestrator's prompt and as a hard **V9** cap.
- *Cascading context handoff* — the orchestrator's brief to a worker omits a critical fact; the worker makes a wrong assumption; synthesis integrates the wrong answer. Mitigate by templating briefs (a structured schema with required fields) and by **V15 LLM-as-Judge** over synthesis.
- *Single point of failure* — orchestrator quality caps the whole system. A weak orchestrator wastes capable workers; a confused orchestrator confuses every worker. Use the strongest available model here (Anthropic uses Opus 4 orchestrator, Sonnet 4 workers).
- *Silent worker failure* — a worker errors and its return is dropped; synthesis runs as if it never existed (**A10**). Dispatcher must surface every worker outcome as either result or explicit error.
- *Unbounded recursion* — orchestrator-of-orchestrators-of-orchestrators without a depth cap. The whole tree must be bounded by **V9**, not just per-worker.
- *Untraced multi-agent run* — **A15** with N+1 multipliers. Production O6 without **V14** is undebuggable.
- *Worker count drift toward O7* — the system grows to 15, 20, 30 workers under one orchestrator; selection accuracy collapses and the orchestrator's context fills with the catalogue. Promote to **O7** before this happens, not after.

## Implementation Notes

- The worker brief is the load-bearing artifact. It must carry: an objective (one sentence), required context (only what the worker needs), available tools, expected output format, and explicit scope boundaries. Anthropic's published guidance is precise: *"Each subagent needs an objective, an output format, guidance on the tools and sources to use, and clear task boundaries."* Treat the brief as a schema, not a prose paragraph.
- Use the strongest model available as the Orchestrator; weaker models as Workers if cost matters. Orchestrator reasoning bounds the whole system; worker reasoning is constrained by its brief and tools.
- Bound aggressively on multiple axes: max workers per round, max rounds, max depth, max wall-time, max total cost. Single-axis bounds eventually trip at the wrong time.
- Run independent workers in parallel by default (the **O4** composition); fresh isolated contexts (the **O17** composition); for 5+ shared tools, expose them via **I3 MCP** rather than wiring tools per-worker.
- Synthesis is its own LLM step, not a string concatenation. The orchestrator (or a synthesis session) reads worker returns *and* the original goal, then produces the final answer. Skipping synthesis is the most common O6 quality regression.
- Trace everything (**V14**): orchestrator plan, every dispatch, every worker trajectory, the synthesis call. OTel-compliant tracing across the agent tree is the production standard.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** O6 chains an Orchestrator session with N Worker sessions (each typically running **R4 ReAct** internally on its own tools) and a Synthesis session. It composes with **O4 Parallelization** for independent workers, **O17 Agent Isolation** for fresh worker contexts, **V9 Bounded Execution** for the global cap, and **V14 Trajectory Logging** for the per-agent trace. The Orchestrator's setup draws on **S3 Persona**, **S5 Constraint Framing**, **S6 Output Template** (the brief schema). Workers expose their tools via **I2** function calls or **I3** MCP servers.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Receive goal; assemble worker catalogue | `code` | |
| 2 | Check global bound (max rounds, max workers, max cost) — halt if tripped | `code` | V9 |
| 3 | Orchestrator emits structured plan: list of (worker, brief) pairs | `LLM` | Orchestrator session, S6 |
| 4 | Validate plan (worker exists, brief schema valid, count under cap) | `code` | V9 |
| 5 | Dispatch workers — in parallel where briefs are independent | `code` | O4 |
| 6 | Each worker runs in fresh isolated context | `LLM` (per worker) | Worker session, R4, O17 |
| 7 | Collect results; preserve errors as explicit outcomes | `code` | |
| 8 | Synthesis: integrate returns into final answer (or decide more rounds needed) | `LLM` | Synthesis session |
| 9 | If synthesis says "incomplete", loop to step 2 with updated state | `code` | V9 |
| 10 | Log orchestrator call, every dispatch, every worker trajectory, synthesis call | `code` | V14 |

**Skeleton** — the wiring; each `# LLM` line is a configured session:

```
orchestrator_workers(goal, workers, max_rounds, max_workers, max_cost):
    state = {goal: goal, results: [], round: 0}
    while not V9.bound_tripped(state, max_rounds, max_workers, max_cost):  # code — V9
        plan = Orchestrator(state, workers.catalogue)                       # LLM
        if plan.done:
            break
        validated = validate_plan(plan, workers, max_workers)               # code — V9 cap
        results = parallel_dispatch(validated, workers)                     # code — O4
            # for each (worker, brief) in validated:
            #     fresh_ctx = isolate(brief)                                # code — O17
            #     result = workers[worker].run(fresh_ctx)                   # LLM (R4 inside)
            #     V14.log(worker, brief, result)                            # code — V14
        state.results.extend(results)
        state.round += 1
    answer = Synthesis(state.goal, state.results)                           # LLM
    V14.log_run(state, answer)                                              # code — V14
    return answer
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Orchestrator** | the system's strongest available generalist (Anthropic uses Opus 4; quality here caps the whole system) | role (**S3**: *"you coordinate specialist workers to accomplish a goal"*); the worker catalogue (names, specialisations, tools, when to use each); the brief schema (**S6**: objective / context / tools / output format / boundaries — required fields); constraints (**S5**: *"never execute sub-tasks yourself; spawn no more than K workers per round; if the answer is complete, return done"*); the bound rationale | the current goal + all prior worker results + current round number |
| **Worker** *(one or many; possibly specialised; almost always runs **R4** internally)* | fit-to-purpose — often a faster model than the orchestrator (Anthropic uses Sonnet 4 workers under Opus 4 orchestrator); specialist if the worker's domain warrants | role (**S3**); the tool catalogue for this worker's specialty (names, schemas); the R4 contract (Thought / Action / Observation, Finish action); output-format contract matching what the orchestrator's brief schema specifies | the single brief the orchestrator dispatched (objective + context + tools + output format + boundaries) — *and nothing else* |
| **Synthesis** *(often the Orchestrator session reused; sometimes a separate session)* | strong generalist — same tier as orchestrator | role (*"you integrate the workers' returns into a final answer against the original goal"*); contract for what "complete" vs "needs another round" looks like; final output format | the original goal + the structured worker results |

**Specialist-model note.** No fine-tuned specialist is *required* for the pattern itself, but two model choices matter:

- The **Orchestrator should be the strongest model you can afford** — its reasoning is the system's bottleneck. The Anthropic Multi-Agent Research System's measured 90.2% gain came from pairing **Opus 4 as orchestrator** with **Sonnet 4 as workers**; running Opus everywhere added cost without adding quality, running Sonnet as orchestrator lost the gain.
- **Workers can be specialised** — by prompt, by tool set, by domain fine-tune, or by being a different model entirely. The pattern accommodates heterogeneous workers; the orchestrator's catalogue is how it knows which worker fits which sub-task. Whenever a worker uses a specialist (fine-tuned or otherwise), it is a build dependency, not a drop-in prompt — the orchestrator's prompt must know about it.

## Open-Source Implementations

- **Anthropic Claude Cookbooks — orchestrator_workers** — [`github.com/anthropics/claude-cookbooks`](https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/orchestrator_workers.ipynb) — the reference notebook from Anthropic's "Building Effective Agents" guide; the canonical worked example for the pattern.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the standard production scaffold for O6 in the LangChain ecosystem; orchestrator-worker graphs are a documented core use case.
- **LangGraph Supervisor** — [`github.com/langchain-ai/langgraph-supervisor-py`](https://github.com/langchain-ai/langgraph-supervisor-py) — Python library for hierarchical multi-agent systems built on LangGraph; the supervisor agent is an O6 orchestrator (and the entry point for promoting to **O7** when the worker pool grows).
- **AWS Agent Squad** (formerly Multi-Agent Orchestrator) — [`github.com/awslabs/multi-agent-orchestrator`](https://github.com/awslabs/multi-agent-orchestrator) — AWS Labs framework for orchestrating multiple AI agents with intent classification, dynamic routing, and conversation context across agents. Python and TypeScript.
- **Microsoft AutoGen** — [`github.com/microsoft/autogen`](https://github.com/microsoft/autogen) — programming framework for agentic AI; GroupChat with admin agent is an O6 pattern (an orchestrator selects the next speaker and dispatches). Now in maintenance mode; Microsoft Agent Framework is the successor.
- **CrewAI** — [`github.com/crewAIInc/crewAI`](https://github.com/crewAIInc/crewAI) — role-based multi-agent framework; the Crew + Process abstraction is an O6 orchestrator coordinating role-defined workers.

Every major agent framework ships an O6 implementation as its canonical multi-agent pattern; the pattern is so universal that "build a multi-agent system" in most frameworks means "configure an orchestrator + workers".

## Known Uses

- **Anthropic Multi-Agent Research System** — the production research agent in Claude.ai; a LeadResearcher orchestrator (Opus 4) decomposes queries into sub-searches delegated to parallel subagents (Sonnet 4), then synthesises returns. Reports ~90.2% accuracy improvement over single-agent baselines on internal evaluation. The reference production embodiment of O6.
- **Claude Code, Cursor, Devin, Aider** — coding agents that delegate sub-tasks (analysis, file edits, test execution) to internal worker sessions with isolated context. The "main agent" + "sub-agent" structure visible in their architectures is O6 + **O17** + **R4** workers.
- **Enterprise research and analyst assistants** built on LangGraph, LangGraph Supervisor, and CrewAI — the production default for multi-step research and reporting agents.
- **AWS Bedrock multi-agent collaboration** and **AWS Agent Squad** deployments — the AWS-prescribed shape for multi-agent applications.
- **Microsoft Agent Framework** and legacy **AutoGen GroupChat** deployments — the Microsoft-side production embodiment.

## Related Patterns

- **Distinct from** **O2 Prompt Chaining** — O2 fixes the decomposition at design time; O6 decides it dynamically at runtime. If the sequence is stable, use O2 (cheaper, more predictable, easier to test). This is the canonical O2 / O6 decision and the most-cited choice in GO4's composition examples.
- **Distinct from** **O7 Supervisor Hierarchy** — O6 is single-level (one orchestrator, flat worker pool); O7 applies O6 recursively (supervisor of supervisors). Promote to O7 when worker count exceeds ~5–10 and natural groupings emerge.
- **Distinct from** **O4 Parallelization** — O4 runs *known* sub-tasks in parallel; O6 *decides* what the sub-tasks are. When the sub-tasks are enumerable up front and independent, O4 alone suffices.
- **Distinct from** **O5 Evaluator-Optimizer** — O5 is generator + judge (two roles, one quality loop); O6 is decomposer + many executors (many roles, one synthesis). They compose: O5 as the inner pattern of a worker, or O5 wrapping the synthesis step.
- **Composes with** **O4 Parallelization** — independent workers run concurrently; this is where the wall-clock win lives.
- **Composes with** **O17 Agent Isolation** — workers get fresh, isolated contexts; the production composition law is *O6 + O4 + O17*.
- **Required by** **V9 Bounded Execution** — O6 must be bounded on worker count, depth, time, and cost; unbounded O6 is **A3** with multipliers.
- **Pairs with** **V14 Trajectory Logging** — multi-agent without trace is **A15** with N+1 simultaneous undebuggable agents.
- **Pairs with** **V15 LLM-as-Judge** — quality gate over synthesis catches orchestration errors that no individual worker can see.
- **Inner pattern of workers** — workers almost always run **R4 ReAct** internally (or **R13 CodeAct** if their sub-task needs control flow over multiple tools). R4 is the canonical worker inner loop.
- **Composition law** — *production O6 = O6 + O4 + O17 + V9 + V14*. This is the most-deployed multi-agent stack in 2025–26 and the shape every major framework converges on independently.

## Sources

- Anthropic (2024) — "Building Effective Agents." Engineering guide naming Orchestrator-workers as one of five core workflow patterns. [anthropic.com/engineering/building-effective-agents](https://www.anthropic.com/research/building-effective-agents).
- Anthropic (2025) — "How we built our Multi-Agent Research System." Engineering write-up of the production reference implementation, including the 90.2% measured gain. [anthropic.com/engineering/multi-agent-research-system](https://www.anthropic.com/engineering/multi-agent-research-system).
- Anthropic Claude Cookbooks — `patterns/agents/orchestrator_workers.ipynb`. The reference worked example.
- LangGraph documentation — orchestrator-worker graphs and the Supervisor library.
- AWS Prescriptive Guidance — multi-agent orchestration patterns (orchestrator-workers, hierarchical agents).
- Microsoft AutoGen and Microsoft Agent Framework documentation — GroupChat and orchestration patterns.
- arXiv 2601.03328 — "Multi-Agent System Design Patterns: An Empirical Study" — orchestrator-workers as one of the most-deployed patterns in surveyed production systems.
- arXiv 2604.03515 — "Inside the Scaffold" — scaffold taxonomy finding that multi-agent coding scaffolds layer R4 workers under O6 orchestrators.
- 12-Factor Agents — Factor 10 (Small, Focused Agents) — the principle that motivates O6 over monolithic O1 once a task outgrows a single agent.
