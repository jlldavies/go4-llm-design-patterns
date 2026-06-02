# R4 — ReAct

> Interleave a free-text *Thought*, a structured *Action* (tool call), and the returning *Observation* in a single loop, so each next reasoning step is conditioned on what the previous action actually returned rather than on a plan made before the world was seen.

**Also Known As:** Reason+Act, Reason-and-Act Loop, Think-Act-Observe, Standard Agent Loop, the Agent Loop. (Function-calling agents and tool-using agents in modern frameworks are nearly always R4 underneath.)

**Classification:** Category III — Reasoning · Band III-B Tool-using loops · the *adaptive, observation-conditioned* loop — sibling of R5 ReWOO (plan-then-execute, no observation) and R13 CodeAct (same loop, code instead of JSON as the action language).

---

## Intent

Let an agent make its next decision *after* seeing the result of its last action, by interleaving short reasoning traces with tool calls and feeding each tool's return back into the model — so the trajectory adapts to what the environment actually says, instead of executing a plan written before any of it was known.

## Motivation

A naive tool-using agent has two halves to glue together: a model that can reason, and a set of tools that can act on the world. The question is *in what order, and with what coupling between them*.

Two strategies fail on opposite ends. **Pure chain-of-thought** (R1/R2) reasons in natural language but cannot consult anything outside the model — it hallucinates facts it cannot verify and confabulates calculations it cannot execute. **Pure plan-then-execute** (R3, R5 ReWOO) plans all tool calls up front, then runs them — efficient when the plan is right, but blind: if the first tool returns something unexpected (an empty result, an error, a fact that contradicts the plan), every later step was conceived in ignorance of it. The plan-then-execute agent has no place to *update* on what it just learned.

Yao et al. (2022) identified the missing primitive. Have the model emit, in sequence, three things: a *Thought* (free-text reasoning about what to do next), an *Action* (a structured tool call), and then receive an *Observation* (the tool's actual return value) — and feed that observation back into the next iteration. Thought conditions on Observation; Action is chosen by Thought; Observation is produced by the world. Round and round until the model emits an Action of type *Finish*. The reasoning is no longer a monologue divorced from action, and the action is no longer chosen in ignorance of what the world says back. The loop is the simplest structure that closes the loop between language and environment.

What makes R4 fundamental — and not a special case of something else — is that no other pattern provides this specific coupling. ReWOO has the Action but no Observation feedback. Chain-of-thought has the Thought but no Action. Plan-and-Solve has Plan and Execute as *phases*, not a per-step loop. Self-Ask decomposes a question but does not necessarily touch tools. The single-step Thought → Action → Observation triplet, repeated until termination, is the agent-loop primitive of which most production agents are an instance.

## Applicability

Use ReAct when:

- the task requires tool use, and the *sequence* of tool calls cannot be enumerated up front (each call depends on what the last one returned);
- the environment may surface errors, empty results, or unexpected data that should change the next decision;
- exploratory or open-ended tasks where the path to the answer is unknown (multi-hop question answering, code investigation, web navigation, debugging);
- you want a *visible* reasoning trace per step for inspectability, audit, and debugging.

Do not use it when:

- the full tool-call sequence is independent and can be planned up front — prefer **R5 ReWOO** for 5× token efficiency;
- the task is a single tool call wrapped in reasoning — a plain function-call (I2) is sufficient, no loop needed;
- multi-tool coordination needs control flow (loops, conditionals, intermediate variables) — prefer **R13 CodeAct**, which uses Python as the action language and gains ~20pp accuracy on multi-tool benchmarks;
- the task is pure reasoning with no tools — prefer **R1/R2 Chain-of-Thought**, possibly with **R17 Self-Consistency** for reliability;
- the loop cannot be bounded — never run R4 without **V9 Bounded Execution**; unbounded R4 is anti-pattern **A3 Uncontrolled Recursion**.

## Decision Criteria

R4 is right when the next action genuinely depends on what the last action returned, and a bound on the loop is acceptable.

**1. Test for dependency between tool calls.** Sketch the task. If you can write down all tool calls before running any of them — *and the order doesn't matter, or the order is fixed and known* — the calls are independent and **R5 ReWOO** is 5× cheaper. If at least one call's input depends on a previous call's *content* (not just its existence), the calls are dependent and R4 is justified. The honest test: can you describe step 3 without first imagining the result of step 2? If no, you need R4.

**2. Pick the action language.** R4 uses *structured JSON / function-call* actions — one tool per step, model picks tool and arguments. **R13 CodeAct** uses *Python code* as the action — one block can call many tools with control flow. Wang et al. (2024) measured ~20pp accuracy advantage for CodeAct on multi-tool benchmarks (M3 ToolEval). Use R4 when actions are atomic; use **R13** when a single step naturally chains tools or needs `if`/`for`. Both are the same loop shape; only the action language differs.

**3. Bound the loop hard.** R4 with no termination cap is anti-pattern **A3 Uncontrolled Recursion**. Set, before deploying: max steps (typical 8–20 for hard tasks; rarely > 30), max wall-time, max cost, max tool-call count. Pair with **V9 Bounded Execution** as a mandatory dependency, not a nice-to-have. Production R4 agents that stall almost always stalled because of a missing bound.

**4. Cost the per-step LLM call.** Each Thought → Action → Observation triplet costs *at least* one LLM call, often a second one to parse Observation into the next Thought. A 10-step task is 10–20× the cost of a single call. If the trajectory length is known to be short (≤ 3 steps), R4 is cheap; if it is open-ended, budget accordingly. The Observation tokens accumulate in context too — long Observations (search results, file dumps) saturate the window fast. Compose with **K6 Context Compression** or **K7 Context Pruning** for sessions where Observations are large.

**5. Decide on reasoning visibility.** R4's Thought is *visible* — it sits in the trace. This is a feature (inspectability, **V14 Trajectory Logging**, debugging) but also a cost (tokens, latency). Native function-calling on modern models (post-Sonnet 4 / GPT-4 generation) often produces ReAct behaviour with the Thought hidden inside the model's "thinking" channel. Decide whether you want the trace as user-facing reasoning or as internal scratch. The pattern is the same loop either way.

**Quick test — R4 is the right pattern when:**

- the next tool call genuinely depends on the last one's return, *and*
- the action is a single atomic tool invocation (not code with control flow — that's **R13**), *and*
- the loop can be bounded with a hard step / cost / time cap (**V9**), *and*
- per-step LLM cost is acceptable given expected trajectory length.

If the calls are independent and parallelisable, use **R5 ReWOO** for token efficiency. If actions need control flow or chain tools naturally, use **R13 CodeAct**. If the task is pure reasoning with no tools, use **R1/R2 Chain-of-Thought**. If R4 cannot be bounded, do not deploy it — the unbounded loop is **A3**.

## Structure

```
                        ┌──────────────────────────────────────────┐
                        │                                          │
                        ▼                                          │
  Goal ─▶ [LLM] ─▶ Thought ─▶ Action ─▶ [Tool] ─▶ Observation ─────┘
            │
            └─▶ Thought ─▶ Action(Finish) ─▶ Answer

  step counter / cost guard (V9) wraps the loop;
  trajectory logger (V14) captures every (Thought, Action, Observation) triple;
  context manager (K6 / K7) compresses or prunes accumulated Observations.
```

Each loop iteration is a single LLM call that conditions on the running trajectory `(Thought₁, Action₁, Observation₁, …, Thoughtₙ₋₁, Actionₙ₋₁, Observationₙ₋₁)` and emits the next Thought + Action. The Tool executes the Action and returns the Observation. The loop terminates when the model emits `Action: Finish[answer]` or any V9 bound trips.

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Agent (LLM)** | producing the next *Thought* and *Action* given the trajectory so far | trajectory → (Thought, Action) | execute the Action itself, or fabricate an Observation. If it produces both Action and Observation in the same turn, the loop has collapsed and the agent is now hallucinating tool results. |
| **Tool set** | actually performing actions in the world | structured Action → Observation | reason, plan, or decide what tool to call next. A tool that interprets the agent's intent destroys the separation; tools must do exactly what their Action says and return what they returned. |
| **Trajectory** | the append-only record `[(Thought, Action, Observation), …]` fed back into each LLM call | each completed triple → updated history | be edited or reordered mid-run — that is rewriting history. Compression is allowed; mutation is not (use **K6 / K7** for compression, not in-place edits). |
| **Termination check** | deciding when the loop ends | trajectory + step count + cost → continue / halt | be implicit. Every R4 agent must have an explicit step cap, cost cap, and a recognised `Finish` action. Implicit termination ("the model will know when to stop") is the canonical R4 failure mode and is anti-pattern **A3**. |
| **Output parser** | extracting the structured Action from the model's free-text emission | LLM output → (Thought, Action) or parse error | silently coerce malformed Actions into valid ones. A parse error is a signal — return it as an Observation to the next Thought and let the agent recover. |
| **Trajectory logger** *(V14)* | persistent record of every triple for audit and debugging | each triple → log | be optional. Untraced R4 is **A15 Untraced Agent**; debugging an R4 stall without a trace is hours of guessing. |

The defining separation is **Agent ↔ Tool**: the Agent reasons and chooses; the Tool acts and reports. When that separation collapses — the model imagines a tool result instead of actually calling the tool — R4 degenerates into chain-of-thought-with-citation-roleplay, which is much worse than either pure CoT or pure R4 because it *looks* grounded.

## Collaborations

A goal arrives. The Agent emits the first Thought (a short natural-language plan or sub-goal) and the first Action (a structured tool call: tool name and arguments). The Output parser extracts the Action; the Tool executes it and returns an Observation. The trajectory now holds one complete triple. The next LLM call passes the full trajectory back to the Agent, which produces the next Thought conditioned on the prior Observation, then the next Action. The Tool runs again; another triple lands in the trajectory. The Termination check increments the step counter and checks the cost; if either bound trips, the loop halts with a "bounded-out" answer. Otherwise the loop continues until the Agent emits `Action: Finish[answer]`. The Trajectory logger records every triple as the loop runs, regardless of outcome.

Two collaboration patterns sit one level up. **O6 Orchestrator-Workers** typically runs an R4 loop inside *each* worker — the orchestrator delegates a sub-task; the worker runs R4 to completion; the orchestrator collects the result. **K8 Working Memory / Scratchpad** is structurally equivalent to the Trajectory itself: the running record is *both* the memory and the next prompt.

## Consequences

**Benefits**

- Mid-trajectory adaptation: each step conditions on the prior Observation, so the agent recovers from surprising tool returns instead of executing a stale plan.
- Inspectable reasoning: the Thought is in the trace, so debugging is reading the log, not re-deriving model behaviour.
- Tool calls are deterministic (mechanism 7): the same Action with the same inputs returns the same Observation, introducing no sampling variance; intermediate results live in the tool environment rather than in the LLM context, keeping context compact.
- The simplest tool-using primitive that closes the language ↔ environment loop. Most production agents are R4 or a refinement of it.
- Composes cleanly: works inside **O6** workers, under **V9** bounds, with **V14** logging, with **K8** as its own scratchpad.

**Costs**

- One LLM call per step (often two: one to emit, one to parse) — a 10-step task is 10–20× a single call.
- Observation tokens accumulate in context; long Observations (search results, file contents) saturate the window. Mandatory pairing with **K6 / K7** for sessions where Observations are large. Mechanistically, each ReAct step appends new K vectors to the KV cache (mechanism 3); each subsequent LLM call must attend over the entire accumulated trajectory at O(seq_len²) cost (mechanism 2). A 20-step trajectory is not 20× a single call — it is materially more expensive per step because each step's attention computation scales with the growing prefix. Observations should be compressed (K6) or pruned (K7) specifically because every token added compounds subsequent step costs.
- Latency is sequential by construction — the next step cannot start until the last Observation returns. R4 cannot parallelise the way **R5 ReWOO** can.
- Token-inefficient on tasks where the tool-call sequence *could* have been planned up front — ~5× more tokens than **R5 ReWOO** on independent multi-hop lookups.

**Risks and failure modes**

- *Unbounded loop* — without **V9**, a confused agent will keep emitting Actions; the loop runs until cost or wall-time forces a kill. This is anti-pattern **A3 Uncontrolled Recursion** and is the canonical R4 failure.
- *Hallucinated Observation* — when the model emits an Action *and* the Observation in the same generation, the Tool was never called. Strict parsing must halt the model after the Action; everything after must come from the actual Tool. Models trained on ReAct traces sometimes hallucinate Observations during continuation; the wiring code must enforce the cut.
- *Action loop* — the agent emits the same Action repeatedly because each Observation is the same (a dead tool, an empty search). Catch with a same-action-N-times detector inside the Termination check.
- *Drift* — long trajectories with many Observations push the original goal out of the attention window. The goal token stated at position 0 is subject to the U-shaped recall phenomenon (mechanism 4 — Liu et al. 2024): middle-trajectory tokens are geometrically under-attended relative to recent tokens. This is also compounded by recency bias in the learned positional encoding (mechanism 12): the smallest positional offset is at the most recent token, giving it the strongest Q-K contractions. Restating the goal in the system prompt (position 0) or in every Executor prompt keeps it in an attended region. Compose with **K6** (compress old triples) or restate the goal in every step.
- *Hidden state* — anti-pattern **A9 Stateful Reducer**; if any Tool mutates external state, **V10 Checkpointing** is required to make the run replayable.
- *Untraced* — anti-pattern **A15**; an R4 agent without **V14 Trajectory Logging** is undebuggable.

## Implementation Notes

- The stopping condition must be explicit and multi-axis: step count, cost, wall-time, *and* a recognised `Finish` Action. Any single axis as the sole bound eventually trips at the wrong time.
- The Output parser is load-bearing. Brittle regex parsing breaks on minor format drifts. Modern function-calling (OpenAI tools, Anthropic tool use) shifts the parser into the model's structured output API — strictly preferable to free-text "Action: …" parsing if your provider supports it.
- Limit tools per agent (**V13 Tool Budget**) — tool-selection accuracy collapses above ~15 tools (Cursor caps at 40). For 5+ tools shared across agents, use **I3 MCP**; for 1–5 tools, plain function-call (**I2**) is fine.
- For long-running R4 loops, compress *old* triples (**K6**) but keep the original goal and the *last few* Observations verbatim — recent Observations are what condition the next step.
- The Thought itself is sometimes redundant on the strongest models, which can choose actions well without verbalised reasoning. Measure: run with and without an explicit Thought slot. If accuracy is unchanged, drop it — it's pure cost. Function-calling models often internalise the Thought.
- For multi-tool tasks with natural control flow, switch to **R13 CodeAct**: ~20pp accuracy gain, ~30% fewer steps, and intermediate values stay in Python variables instead of bouncing through the LLM context.
- Replay matters. Persist the trajectory (**V14**), seed any non-determinism, and version the tool set — an R4 agent that ran yesterday must be re-runnable today.
- Combine with **R7 Reflexion** when the task has an objective success signal: R4 is the within-run loop; R7 is the across-run learning loop. They stack cleanly.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** R4 is the *agent loop* primitive. The Agent session draws on **S3 Persona** for role, **S5 Constraint Framing** for tool-use rules, **S6 Output Template** for the Thought / Action contract. The loop is bounded by **V9** and logged by **V14**; long sessions compose with **K6 / K7** for context management. R4 commonly sits inside **O6** workers and uses **I2** function-calls or **I3** MCP servers as its tools. **K8 Working Memory** is the Trajectory itself.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Initialise trajectory with goal | `code` | |
| 2 | Check bounds (steps, cost, wall-time) — halt if tripped | `code` | V9 |
| 3 | LLM emits next Thought + Action | `LLM` | Agent session |
| 4 | Parse Action; on parse error, set Observation = error and goto 6 | `code` | I2 / structured output |
| 5 | If Action == Finish, return answer | `code` | |
| 6 | Execute tool: `Observation = tool[Action.name](Action.args)` | `code` | I2 / I3 tools |
| 7 | Append (Thought, Action, Observation) to trajectory; log triple | `code` | V14 |
| 8 | Loop to step 2 | `code` | |

**Skeleton** — the wiring; each `# LLM` line is a configured session:

```
run(goal, tools, max_steps, max_cost):
    trajectory = [goal]
    while not V9.bound_tripped(trajectory, max_steps, max_cost):   # code — V9
        thought, action = Agent(trajectory)                        # LLM
        if action.name == "Finish":
            return action.args["answer"]
        try:
            obs = tools[action.name](**action.args)                # code — I2 / I3
        except Exception as e:
            obs = f"Error: {e}"                                    # parse / tool errors become Observations
        trajectory.append((thought, action, obs))                  # code
        V14.log(thought, action, obs)                              # code — V14
    return bounded_out(trajectory)                                 # code — V9 halt path
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | the system's main generalist (or a tool-use-tuned model — most modern frontier models are) | role (**S3**); the tool catalogue (names, descriptions, JSON schemas); the Thought / Action output contract (**S6**); behavioural rules (**S5**: *"emit exactly one Action per turn; stop after emitting Action; never invent Observations"*); the `Finish` action and how to call it | the full trajectory so far (goal + all prior triples) |

A second LLM call is sometimes used as the **Output parser** when the provider has no native structured-output / tool-use API and the model emits free-text "Thought: … / Action: …" that must be parsed. Modern function-calling APIs make this redundant — the structured Action is the API's job, not a separate model's.

**Specialist-model note.** No fine-tuned specialist is required, but the choice of base model matters more here than in most patterns: R4 quality is largely a function of *tool-use* capability. Models specifically post-trained for tool use (Claude Sonnet 4/Opus 4, GPT-4-class, Llama 3.1+ instruction tunes) produce R4 trajectories with markedly fewer parse failures and same-action loops than models that were not. The pattern works on any capable generalist; it works *much* better on a tool-use-tuned one. The original Yao et al. paper used PaLM-540B with few-shot prompting; the modern equivalent is native function-calling on a frontier instruction-tuned model with zero few-shot examples.

## Open-Source Implementations

- **ReAct (official)** — [`github.com/ysymyth/ReAct`](https://github.com/ysymyth/ReAct) — Yao et al.'s reference implementation; notebooks for HotpotQA, FEVER, ALFWorld, and WebShop with the original prompts and trajectories.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — `langgraph.prebuilt.create_react_agent` is the canonical modern ReAct implementation: a prebuilt graph with the agent node, tools node, and conditional routing wired to halt on no-tool-call. Most production ReAct deployments now use this rather than the older LangChain `AgentExecutor`.
- **LangGraph ReAct template** — [`github.com/langchain-ai/react-agent`](https://github.com/langchain-ai/react-agent) — LangGraph Studio template for a minimal ReAct agent; the cleanest starting point for new builds.
- **LlamaIndex `ReActAgent`** — [`github.com/run-llama/llama_index`](https://github.com/run-llama/llama_index) — `llama_index.core.agent.workflow.ReActAgent`; supports query-engine tools and `FunctionTool` instances with streaming Thought / Action / Observation.
- **LangChain (classic) `create_react_agent`** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — the legacy `langchain.agents.react.agent.create_react_agent` implementation; still widely deployed but increasingly superseded by the LangGraph version.

Beyond these, every major agent framework (CrewAI, AutoGen, Smolagents, Letta, Pydantic AI) ships a ReAct loop as its default agent primitive. The pattern is so canonical that "build an agent" in most frameworks means "run R4 on these tools".

## Known Uses

- **Claude Code, Cursor, Devin, Aider, OpenAI Codex CLI** — coding agents whose inner loop is ReAct over tool calls (file read/write, shell, search, lint). Step counts run 5–50 per task with V9-style hard caps.
- **Perplexity, You.com, Phind** — answer engines whose retrieval + synthesis loop is a constrained R4 over search and fetch tools.
- **LangGraph-based enterprise assistants** — `create_react_agent` is the production default for new tool-using agents in the LangChain ecosystem.
- **Customer-support and ops agents** built on LlamaIndex, LangChain, and CrewAI — virtually all use R4 as the per-agent reasoning loop.
- **Web-navigation and computer-use agents** (Anthropic Computer Use, Browser-Use) — the screen-read / action / observe loop is R4 with vision as the Observation channel.

## Related Patterns

- **Sibling of** **R5 ReWOO** — same problem (multi-step tool use), opposite trade-off. R4 adapts mid-run; R5 plans up front for 5× token efficiency. Mutually exclusive for the same task (see CONFLICTS.md CRITICAL 1).
- **Sibling of** **R13 CodeAct** — same loop shape, different action language. R4 uses structured JSON / function-call actions (one tool per step); R13 uses Python code (many tools + control flow per step). R13 wins ~20pp accuracy and ~30% fewer steps on multi-tool benchmarks but requires **V8 Tool Sandboxing**.
- **Required by** **V9 Bounded Execution** — never run R4 unbounded; unbounded R4 is anti-pattern **A3**.
- **Pairs with** **V14 Trajectory Logging** — R4 without a trace is undebuggable (**A15**).
- **Inner pattern of** **O6 Orchestrator-Workers** — each worker typically runs R4 internally; the orchestrator coordinates across workers.
- **Composes with** **K8 Working Memory** — the Trajectory *is* the scratchpad; R4's running record is structurally K8.
- **Composes with** **K6 / K7** — long sessions compress or prune accumulated Observations to keep the window tractable.
- **Composes with** **R7 Reflexion** — R4 is the within-run loop; R7 is the across-run learning loop that retries failed R4 trajectories with verbal critique in memory.
- **Distinct from** **R3 Plan-and-Solve** — R3 separates planning and execution into *phases*; R4 interleaves them at every step. R3 replans on failure; R4 reacts on every Observation.
- **Distinct from** **R1 / R2 Chain-of-Thought** — CoT reasons without tools; R4 reasons *with* tools and conditions on tool returns. R4 reduces to CoT if the tool set is empty.
- **Tool layer** — **I2 Function/Tool Call** for 1–5 tools, **I3 MCP Server** for 5+ shared across agents, **I4 CLI Invocation** when a CLI already exists.

## Sources

- Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., & Cao, Y. (2022). "ReAct: Synergizing Reasoning and Acting in Language Models." arXiv 2210.03629. Published at ICLR 2023.
- Wang, X., Li, B., Song, Y., Xu, F. F., Tang, X., Zhuge, M., Pan, J., et al. (2024). "Executable Code Actions Elicit Better LLM Agents." arXiv 2402.01030. ICML 2024. — establishes the R4 / R13 comparison.
- Xu, B., Peng, Z., Lei, B., et al. (2023). "ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models." arXiv 2305.18323. — establishes the R4 / R5 comparison.
- LangGraph documentation — `langgraph.prebuilt.create_react_agent` reference, the modern canonical implementation.
- Lilian Weng (2023). "LLM Powered Autonomous Agents." OpenAI blog — ReAct in the broader agent-architecture context.
