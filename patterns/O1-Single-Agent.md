# O1 — Single Agent

> One LLM, one system prompt, one bounded tool set, one context window — the model itself plans, decides, acts, and observes until the task is done, with no coordination across agents because there is only one agent.

**Also Known As:** Autonomous Agent, Solo Agent, Monolithic Agent, Single-Loop Agent, Tool-Using Assistant.

**Classification:** Category IV — Orchestration · Band IV-A Workflow patterns · the *baseline* pattern of the category — every other orchestration pattern (O2–O17) is defined as the upgrade introduced when O1 demonstrably fails.

---

## Intent

Run the whole task inside one agent: a single configured LLM with a system prompt, a small tool set, and a ReAct-style inner loop. Use it as the floor against which any multi-step pipeline, router, or multi-agent decomposition must justify its cost.

## Motivation

Every orchestration move costs something — extra LLM calls, context handoffs, coordination logic, more failure surfaces, more code to maintain. Teams reach for multi-agent decompositions on instinct (it *feels* like a "real" agent system) and discover late that the pipeline is slower, more brittle, and harder to debug than one capable model with the right tools and the right prompt would have been. Anthropic's "Building Effective Agents" (2024) opens with precisely this warning: find the simplest solution, and only add complexity when the measurement demands it. The 12-Factor Agents project (Factor 10: Small, Focused Agents) makes the same point from the production side — small agents with 3–20 turn scopes outperform sprawling ones because their context windows stay coherent.

O1 fixes the floor. It says: *one LLM, one system prompt, one bounded tool set, run an inner reasoning loop (typically R4 ReAct) until the task is done* is the architecture you must beat to justify anything more. The pattern is not a clever trick; there is no novel mechanism — the LLM, the system prompt, and the tools already existed. The contribution is naming the baseline so that adding a second agent becomes a conscious decision rather than an unexamined habit.

Every other Category IV pattern decomposes into "O1 plus a specific addition": **O2 Prompt Chaining** adds a fixed sequence of separately-prompted LLM calls; **O3 Routing** adds a classifier in front of N specialised O1s; **O4 Parallelization** runs several O1-shaped calls concurrently and aggregates; **O5 Evaluator-Optimizer** adds a second LLM as judge; **O6 Orchestrator-Workers** adds a planner that dynamically delegates to worker O1s; **O7 Supervisor Hierarchy** stacks O6 recursively; **O17 Agent Isolation** spawns fresh-context O1s as sub-agents. Each is an upgrade against the same floor. The category only makes sense if its baseline is named — which is why O1 earns a numbered pattern even though, mechanically, it is "just one agent doing the task."

## Applicability

Use Single Agent when:

- the task is self-contained within one context window — total input + intermediate scratch + tool outputs + final answer fit comfortably;
- the tool set is small enough that the model can select reliably — typically **≤ 10–15 tools** before selection accuracy degrades, hard-capped by **V13 Tool Budget**;
- the task does not split into roles that are genuinely *distinct in expertise or context* — a "researcher" and a "writer" persona at the same model and same context is not a real split;
- iteration speed and debuggability matter — one agent has one failure domain.

Do not use it when:

- the task decomposes into a known, fixed sequence of steps with quality gates between them → use **O2 Prompt Chaining**.
- distinct input types need genuinely different handling (billing vs. technical vs. cancellation) → use **O3 Routing**.
- independent sub-tasks can run concurrently and the latency saving matters → use **O4 Parallelization**.
- output quality requires evaluation that the generator cannot honestly give itself → use **O5 Evaluator-Optimizer** (or **R8 Self-Refine** for the cheap version).
- the task is open-ended and decomposition is not known upfront → use **O6 Orchestrator-Workers**.
- the working context exceeds what one window can hold without compression, and compression itself loses too much → use **O17 Agent Isolation** to delegate sub-tasks to fresh contexts.
- the tool count exceeds the V13 budget and cannot be trimmed → split by domain (**O14 Single Information Environment**) or route (**O3**).

## Decision Criteria

O1 is right when one capable model can carry the whole task end-to-end inside one context window, with a tool set it can navigate, and nothing in the failure profile justifies the cost of an upgrade yet.

**1. Context-budget check.** Estimate **C** = system prompt + worst-case user input + cumulative tool outputs + intermediate reasoning + final answer, in tokens. If **C ≤ ~50%** of an affordable context window, O1 is viable. **50–75%** is borderline — measure overflow rate on a probe set. **> 75%** → escalate to **O17 Agent Isolation** for sub-tasks, or **K6 Context Compression** to free space, or **O2** to break the task across calls.

This threshold is mechanically grounded: the KV cache grows as [layers × seq_len × kv_heads × d_head] with every token appended to the trajectory. Each generation step reads the full cache; at 70–75% of the window, attention is distributed over a context where relevant tokens are increasingly diluted by accumulated observations. The n² compute cost also becomes material — every new token added pays pairwise attention against all prior tokens. U-shaped recall (Liu et al. 2024) means mid-trajectory tool outputs are statistically under-attended even when technically in window, making overflow a soft failure before it is a hard one. (Mechanisms 2, 3, 4.)

**2. Tool-budget check (V13).** Count distinct tools the agent will be exposed to. **≤ 10 tools** → O1 is safe. **10–15** → measure tool-selection accuracy (Anthropic and others have observed selection accuracy degrading from ~87% to ~54% as tools proliferate). **> 15** → escalate: **O3 Routing** to split by intent, **O14 SIE** to split by data domain, or **I3 MCP** + dynamic discovery. The 4–5 MCP-server / 60k-token threshold from RELIABILITY V13 applies here.

**3. Decomposition test.** Can you enumerate the task's steps at design time? If **yes**, **O2 Prompt Chaining** is cheaper and more testable than O1's free-form loop. If **no — the path is open-ended and the model must decide** — O1's ReAct loop is the right shape. O1 wins exactly when the work is exploratory.

**4. Role-distinctness test.** Would the proposed sub-agents genuinely differ in *model, system prompt, or context* — or are they the same model with different role labels? Same model + same context with two personas is not a real split; collapse to one O1. Different models, isolated contexts, or genuinely specialised tools → **O6 Orchestrator-Workers**.

**5. Reliability budget.** Is a runaway agent acceptable? Never. O1 must be paired with **V9 Bounded Execution** (cap on tool calls, iterations, cost, wall-clock time) and **V14 Trajectory Logging** (so failures can be diagnosed without re-running). These are not orchestration; they are the cost of running any agent. The pattern's most common production failure is "agent ran for 200 tool calls and burned the budget on a task that should have been bounded at 20."

**Quick test — O1 is the right pattern when:**

- the working context fits one window with room to spare, *and*
- the tool set is within V13 budget (~10–15 tools), *and*
- the task path is not known in advance — the model must explore, *and*
- no sub-task needs a genuinely different model, prompt, or isolated context, *and*
- V9 Bounded Execution and V14 Trajectory Logging are in place.

If the path *is* known in advance, choose **O2 Prompt Chaining**. If input types branch, choose **O3 Routing**. If sub-tasks are independent and parallelisable, choose **O4 Parallelization**. If decomposition must be dynamic, choose **O6 Orchestrator-Workers**. If quality cannot be self-evaluated, layer **O5 Evaluator-Optimizer** on top. O1 alone is the default; upgrades are deliberate, measured, and named.

## Structure

```
  ┌─────────────────────────────────────────────────────────┐
  │   System Prompt: role · task framing · tool catalogue · │
  │   constraints · stop conditions (S3 · S5 · V9)          │
  └────────────────────────────┬────────────────────────────┘
                               │
   User request ──▶ ───────────┴───────────┐
                               │           │
                               ▼           │
                    ┌──────────────────┐   │
                    │  LLM (one        │   │
                    │  configured      │◀──┘  inner loop:
                    │  session)        │       reason → act → observe
                    └────────┬─────────┘       (R4 ReAct)
                             │
                  ┌──────────┼──────────┐
                  ▼          ▼          ▼
              Tool A     Tool B  …  Tool N   (I2 / I3 / I4)
                  │          │          │
                  └──────────┼──────────┘
                             │
                       observation
                             │
                             ▼
                    (loop until done OR
                     V9 bound reached)
                             │
                             ▼
                          Answer
```

One model. One system prompt. One context. One inner loop. Tools fan out and observations fan back in to the *same* agent.

## Participants

Four participants — the minimum any agentic system can have. The discipline of O1 is that the list does *not* grow.

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **System Prompt** | the agent's role, task framing, tool catalogue, stop conditions, and any constraints | task spec → instruction block loaded once into the session | smuggle in a second persona, a hidden evaluator, or a chain of "now do step 2" instructions — those are O2/O5 upgrades and must be named as such, not buried inside the system prompt. |
| **Agent (LLM)** | the un-augmented reason-act-observe loop over the tools | system prompt + user request + accumulating tool observations → next action or final answer | be silently swapped between calls; spawn or call another agent (that is O6/O17); persist state outside the context (that is K10/K11/K12). |
| **Tool Set** | the bounded set of actions the Agent can call | tool invocation → tool result | exceed the V13 budget — once tool count drives selection accuracy down, the pattern has failed and the system needs O3, O14, or I3. Tools must not silently mutate (idempotency makes V10 checkpointing work). |
| **Caller** | the wiring that submits the request, runs the inner loop, executes tool calls, and enforces the V9 bound | user request → final answer (or bounded failure) | hand-massage intermediate outputs to nurse the agent past failures — that masks an O1 failure that should be an honest escalation to O2 or O5. The Caller's only judgement is the V9 stop. |

The whole point of the page is the *Must not* column. O1's failure mode is not technical; it is the slow accretion of unexamined additions — a second persona here, a critique step there, an extra tool every sprint — until the prompt is no longer O1 and the team has built an undocumented O6 by stealth.

## Collaborations

The Caller composes the request and submits it to the configured Agent session. The Agent reads the System Prompt (loaded once at session setup) and the user request, then enters its inner reason-act-observe loop: it reasons about what to do, selects a tool from the Tool Set, emits a tool call, the Caller executes the call, the Agent observes the result, and it iterates. The loop continues until the Agent emits a final answer or the V9 bound (max tool calls, max wall-clock, max cost) trips. Every step is logged via V14 Trajectory Logging so that failures can be diagnosed post-hoc without replaying the run. There is no second LLM session, no router, no evaluator, no sibling agent — those moves all belong to other patterns. The simplicity of the collaboration *is* the pattern.

## Consequences

**Benefits**

- Lowest coordination cost of any orchestration pattern — no handoff packets, no router, no aggregation.
- Single failure domain — when something breaks, it broke *here*, not in an inter-agent handoff.
- Lowest latency for short tasks — no fan-out wait, no sequential pipeline accumulation.
- Easiest to test, debug, and trace — one trajectory log captures the whole run.
- Highest portability — drop in a different model and re-run; no orchestration code to rewire.
- The honest baseline — every multi-agent upgrade can be measured against this floor.

**Costs**

- Bounded by one context window — long tasks that exceed it cannot be served by O1.
- Bounded by one tool set — past ~10–15 tools, selection accuracy degrades sharply (V13). At the attention level, each tool schema occupies tokens in the system prompt; with 15+ tools, the Q-K inner product space is crowded with schema text, and the model's learned routing circuits degrade because the bilinear form that separates relevant from irrelevant tool keys becomes less discriminating (mechanism 1). Each additional tool schema also grows the KV cache and raises the quadratic attention cost (mechanism 2). (Mechanisms 1, 2.)
- Bounded by one model's capability — no specialist worker can rescue a sub-task the main model is weak at.
- No independent evaluation — the agent cannot honestly grade its own output (use O5 / R8 if that matters).
- No parallelism — independent sub-tasks run sequentially inside the same loop.

**Risks and failure modes**

- *Runaway loop* — the agent keeps reasoning and tool-calling without progress; without **V9 Bounded Execution** the cost is unbounded. O1 without V9 is anti-pattern **A3 Uncontrolled Recursion**.
- *Tool sprawl* — tools accumulate over time until selection accuracy collapses; this is anti-pattern **A12 Tool Proliferation**, mitigated by V13.
- *Context overflow* — the trajectory grows past the window mid-task; the agent stalls or hallucinates. Mitigate with **K6 Context Compression**, **K7 Context Pruning**, or escalate to **O17 Agent Isolation**.
- *Stealth O6* — the system prompt grows to encode roles, sub-tasks, and inter-step protocols; the pattern has secretly become **O6 Orchestrator-Workers** without the structure to support it. The audit signal is a system prompt longer than ~2 pages doing role-switching mid-prompt.
- *Untraced agent* — no V14 logging; failures cannot be debugged without re-running. This is anti-pattern **A15 Untraced Agent**.
- *Silent capability gap* — the single model is weak at one sub-skill the task needs (e.g. precise arithmetic); O1 has no specialist to delegate to. Add **R13 CodeAct** or **R14 Program of Thoughts** for computation-heavy steps before considering O6.

## Implementation Notes

- **Pair with V9 Bounded Execution from day one.** Cap tool calls, iterations, cost, and wall-clock. Make the bound visible to the agent in the system prompt — "you have ≤ N tool calls" focuses the loop.
- **Pair with V14 Trajectory Logging from day one.** OTel-compliant traces with tool args, tool results, and reasoning tokens. If a failure cannot be diagnosed from the log, the log is incomplete.
- **R4 ReAct is the standard inner loop.** Most production single agents are O1 with R4 inside; for tool-heavy or computation-heavy tasks, **R13 CodeAct** trades JSON tool-calls for executed Python and often improves accuracy 10–20 pp at similar cost.
- **Keep the system prompt to ≤ 1–2 pages.** Beyond that, decomposition (O2) or role-splitting (O6) is almost always cheaper than one giant prompt — that drift is **A1 God Prompt**.
- **Cap tools at ~10–15** (V13). Beyond that, group by domain and route (O3) or split by dataset (O14). MCP servers (I3) help with discovery but do not raise the per-agent ceiling.
- **Idempotent tools** make V10 Checkpointing and retry-on-failure tractable. Mutating tools without idempotency lock you out of recovery patterns.
- **Stop conditions in the system prompt** matter as much as the V9 bound — "stop and ask the user when X" is a Signal-layer instruction that prevents many runaway loops without needing V1 Human-in-the-Loop wiring.
- **Measure first, escalate second.** Run the task on O1 with a logged probe set. Only when measured failure modes name a specific upgrade (overflow → O17, selection collapse → O3, sequential latency → O4) does the upgrade pay back.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** O1 chains exactly one LLM session with a tool-execution loop. It composes intimately with **R4 ReAct** (the standard inner reasoning shape), **I2 Function Call** or **I3 MCP Server** (tool surface), **V9 Bounded Execution** (the loop bound), and **V14 Trajectory Logging** (the observability layer). The setup of the single LLM session is Signal-layer work — **S3 Persona**, **S5 Constraint Framing**, **S6 Output Template** for any structured final answer. O1 is the inner step that almost every other O-pattern *wraps* — O3 routes to several O1s, O4 runs several in parallel, O6 delegates to many of them.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Compose request and load the configured Agent session | `code` | — |
| 2 | Agent reasons about next action (final answer? tool call?) | `LLM` | Agent session, R4 |
| 3 | Branch — if final answer: return; else: extract tool call | `code` | — |
| 4 | Execute the tool, capture observation | `code` | I2 / I3 / I4 |
| 5 | Append observation to conversation, check V9 bound | `code` | V9 |
| 6 | Loop to step 2 (or stop on bound) | `code` | V9 |
| 7 | Log every step | `code` | V14 |

**Skeleton** — wiring only; each `# LLM` line is the *same* configured session, not a fresh one:

```
single_agent(user_request, tools, max_steps):                # V9 bound
    session = setup(system_prompt, tools)                    # code — load once
    convo   = [user_request]
    for step in range(max_steps):                            # V9
        action = Agent(session, convo)                       # LLM — R4 reason+act
        log(step, action)                                    # V14
        if action.is_final:
            return action.answer
        result = execute(action.tool, action.args)           # code — I2/I3/I4
        convo.append(action); convo.append(result)
    return bounded_failure(convo)                            # V9 stop
```

**The LLM sessions.** The pattern's defining property is that there is exactly one:

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | a capable instruction-tuned generalist with strong tool-use (the system's main model) | role / persona (**S3**); task framing; tool catalogue with schemas (**I2/I3**); constraints and prohibitions (**S5**); output contract for the final answer (**S6**); explicit stop conditions; the V9 bound stated in natural language ("you have ≤ N tool calls") | the accumulating conversation: user request + every prior (action, observation) pair |

**Specialist-model note.** None — a capable tool-using generalist is the entire requirement. That is what makes O1 the baseline. The pattern artifact that does the heavy lifting is the *system prompt* together with the *tool schemas*: a well-scoped role, a tight tool catalogue, clear stop conditions, and an explicit bound. Any move that requires a specialist (a fine-tuned router, a separate evaluator model, a long-context model for the orchestrator) is by definition a different pattern — O3, O5, O6, O7. When O1 starts demanding a specialist, the system has outgrown O1.

## Open-Source Implementations

O1 is the degenerate case of orchestration — there is no library to install whose sole purpose is "one agent," because every agent framework's *simplest* configuration is O1. The relevant references are the canonical write-ups and the minimal-agent libraries that explicitly resist multi-agent sprawl:

- **Anthropic — Building Effective Agents** — [`anthropic.com/news/building-effective-agents`](https://www.anthropic.com/news/building-effective-agents) — the canonical 2024 write-up. Establishes the augmented-LLM baseline and the "find the simplest solution" discipline that O1 formalises.
- **12-Factor Agents** — [`github.com/humanlayer/12-factor-agents`](https://github.com/humanlayer/12-factor-agents) — production principles for LLM-powered software. Factor 10 ([Small, Focused Agents](https://github.com/humanlayer/12-factor-agents/blob/main/content/factor-10-small-focused-agents.md)) is the explicit case for O1 as default.
- **smolagents (Hugging Face)** — [`github.com/huggingface/smolagents`](https://github.com/huggingface/smolagents) — a ~1k-LoC library for tool-using agents; `CodeAgent` and `ToolCallingAgent` are O1 by design, with R13 CodeAct or R4 ReAct inside.
- **OpenAI Agents SDK** — [`github.com/openai/openai-agents-python`](https://github.com/openai/openai-agents-python) — the `Agent` primitive is O1 (LLM + instructions + tools + guardrails); multi-agent is opt-in via handoffs.
- **LangGraph — ReAct agent template** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the prebuilt `create_react_agent` is O1 with R4 inside; the minimal LangGraph runnable.

## Known Uses

- **Claude.ai with tools, ChatGPT with tools, Gemini with tools** — the consumer assistants are O1 at the user-turn level: one LLM, a bounded tool set (web, code, files), a single context per conversation.
- **Cursor Agent, Claude Code, Windsurf** in their single-agent modes — when not delegating to sub-agents, the coding agents run O1 with R4/R13 inside and a curated tool set (filesystem, shell, search) under a V13 budget.
- **Most production "AI assistant" features** ship as O1 — customer-support copilots, sales-research assistants, in-app helpers. Multi-agent appears only where a measured O1 failure justified it.
- **The 12-Factor Agents production examples** at HumanLayer — small, focused agents bounded to 3–20 turns are the recommended default.
- **First-iteration agents at every team that has read Anthropic's piece** — the published guidance has made O1 the de facto starting point across the industry since late 2024.

## Related Patterns

- **Baseline for** every other Orchestration pattern — **O2** (sequence of O1s), **O3** (router to specialised O1s), **O4** (parallel O1s), **O5** (O1 + judge), **O6** (planner over worker O1s), **O7** (recursive O6), **O17** (O1 with fresh isolated context). Each is "O1 plus a specific addition." The category exists because the floor is named.
- **Uses** **R4 ReAct** — the standard inner reasoning loop. Most O1 agents are O1 + R4. **R13 CodeAct** is the common upgrade when the task is tool-heavy or computation-heavy.
- **Uses** **I2 Function Call** or **I3 MCP Server** — the tool surface. **I4 CLI Invocation** is the lowest-overhead variant when CLIs already exist.
- **Required by** **V9 Bounded Execution** and **V14 Trajectory Logging** — O1 without V9 is anti-pattern **A3**; O1 without V14 is **A15**. These are not orchestration upgrades; they are the cost of running any agent.
- **Pairs with** **K8 Working Memory / Scratchpad** for multi-step reasoning state; **K11 Observational Memory** for cache-friendly long sessions; **S3 / S5 / S6** for system-prompt construction.
- **Distinct from** **O2 Prompt Chaining** — O2 is a fixed sequence of separately-prompted LLM calls with code between; O1 is one prompt and one model running an inner loop. Calling a chain of LLM calls "a single agent" is the most common misclassification.
- **Distinct from** **O6 Orchestrator-Workers** — O6 has a planner that dynamically delegates to worker agents with their own contexts and prompts; O1 has one context and one prompt. A "manager persona" inside one system prompt is still O1, not O6.
- **Competes with** **O2** when the task path can be enumerated at design time — O2 is cheaper and more testable; O1 wins on open-ended exploration.
- **Note on fundamentality** — O1 is the *degenerate case* of orchestration and earns its number as the baseline against which every other Orchestration pattern is measured, the same role **S1 Zero-Shot** plays for Signal and **K1 Vanilla RAG** plays for Knowledge. Removing it would leave the rest of the category without a defined floor; every multi-agent upgrade would be measured against an unnamed default.

## Sources

- Anthropic (2024) — *Building Effective Agents.* The canonical guidance to start with the augmented LLM and add complexity only when measurement demands it.
- HumanLayer (2024–2025) — *12-Factor Agents*, Factor 10: Small, Focused Agents. The production-principles case for O1 as the default.
- Yao et al. (2022) — *ReAct: Synergizing Reasoning and Acting in Language Models* (arXiv 2210.03629). The standard inner-loop reasoning pattern O1 typically runs.
- Schick et al. (2023) — *Toolformer: Language Models Can Teach Themselves to Use Tools.* Early formalisation of the tool-using single agent.
- Wang et al. (2024) — *Executable Code Actions Elicit Better LLM Agents* (CodeAct / R13). Tool-use upgrade frequently paired with O1.
- AWS Prescriptive Guidance — *Agentic AI patterns* (single-agent pattern as the foundation).
- Scaffold taxonomy (arXiv 2604.03515) — empirical study of 13 production coding agents; the LLM-as-navigator branch (8/13 agents) is O1 + stacked loop primitives.
