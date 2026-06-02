# R3 — Plan-and-Solve

> Split reasoning into two distinct LLM calls — first a *Plan* call that produces an explicit, inspectable step list from the full task in view, then an *Execute* call (or chain) that carries the plan out — so plan quality and execution efficiency are tuned independently.

**Also Known As:** Plan-and-Execute, Explicit Planning, Plan-then-Execute, Upfront Planning.

**Classification:** Category III — Reasoning · the *agent-level* instance of ordered execution — two or more LLM calls, with the step list **generated at runtime** by a Planner call rather than authored at design time; the planning-cousin of **S4 Instruction Decomposition** and the planning-counterpoint to **R4 ReAct**.

---

## Intent

Separate the act of *deciding what to do* from the act of *doing it* by putting them in different LLM calls, so the Planner sees the whole task before committing to an order, the Executor runs efficiently against a stable plan, and the plan itself is an inspectable artifact a human or a downstream component can read, edit, or gate on before any step runs.

## Motivation

Single-call reasoning patterns — R1/R2 chain-of-thought, S4 instruction decomposition — interleave planning and execution inside one model turn. The model decides the next step and produces its output in the same forward pass. For short, well-rehearsed procedures that is enough. For tasks where the *order* of steps matters and is non-obvious, it is not: the model commits to step 1 before it has surveyed the full task, and discovers the bad ordering only by failing downstream. Wei et al.'s CoT helps the model think, but it does not give the model a separate moment to *plan*.

ReAct (**R4**) goes the other way: every step is its own LLM call, with a fresh Thought-Action-Observation triplet. That is maximally adaptive but maximally expensive — N model calls for N steps, each carrying the full conversation context, and each making its decisions myopically with only the last observation as immediate input. Long horizons compound the cost, and the lack of a global plan means ReAct can wander.

Plan-and-Solve resolves the tension with a single structural move: lift planning into its own call. Wang et al. (2023) showed that prompting a model to "devise a plan to divide the entire task into smaller subtasks, then carry out the subtasks according to the plan" beats Zero-Shot CoT on arithmetic, symbolic, and commonsense reasoning — the same model, the same task, with the planning step separated. The plan is a first-class artifact: it can be inspected before execution, edited by a human, validated by a checker, or replanned if execution fails. Execution becomes cheap (a smaller model, a tighter prompt) because the hard reasoning was done once, upfront.

The defining claim is asymmetric in time: *one expensive planning call buys many cheap execution calls.* That asymmetry — and the separability of the plan as an artifact — is what makes R3 a distinct pattern, not a configuration of CoT or ReAct. This asymmetry is mechanically grounded in model size (mechanism 8): a 70B Planner and a 7B Executor have a ~10× per-token compute cost difference; the Planner runs once while the Executor runs O(steps) times, so the total cost is dominated by the cheaper session. Each Executor call operates on its own bounded context rather than on the full accumulated history (mechanism 6), which keeps each step's attention cost independent of prior steps.

## Applicability

Use Plan-and-Solve when:

- the task is multi-step and the *order* of steps matters, but the order is not obvious from the input alone — the model needs to survey the whole task before committing;
- a plan written before execution would be useful to inspect, log, gate on, or hand to a human reviewer;
- planning is harder than execution — the steps themselves are individually tractable, the challenge is choosing and sequencing them;
- you want to use a strong (expensive) model for planning and a cheap model — or deterministic code — for execution;
- ReAct (**R4**) is burning too many tokens on a task whose step sequence could be determined upfront.

Do not use when:

- the task is one-step or two-step and a single prompt suffices — stay with **S1 Zero-Shot** or **R1 Zero-Shot CoT**;
- the step list is fixed and authorable at design time — use **S4 Instruction Decomposition** for a single call, or **O2 Prompt Chaining** for a fixed multi-call chain;
- the environment is genuinely unpredictable and each step's choice depends on the last observation — use **R4 ReAct**;
- steps are independent and could run in parallel — use **O4 Parallelization** (R3's plan can also fan out to O4 for parallel execution, but if there is no dependency at all, you do not need the Planner);
- the search space is large enough that one plan is unlikely to be the right one — use **R9 Tree of Thoughts** or **R10 LATS** to search over plans.

## Decision Criteria

R3 is right when planning is harder than execution, the step list cannot be authored at design time, and the plan is worth inspecting before any step runs.

**1. Plan-vs-execute asymmetry.** Estimate the cognitive load of *choosing the steps* versus the cognitive load of *running each step*. R3 pays off when planning is materially harder — the Planner can use a strong model (slow, expensive) and the Executor a cheap one (fast, cheap). If planning and execution are equally hard, the two-call structure buys little; consider **R4 ReAct** instead.

**2. Step-count and predictability.** R3 fits roughly 3–15 steps that are *predictable* once the task is surveyed. Below 3 steps, **S4** in one prompt suffices. Above ~15 steps, plan reliability degrades and you should either decompose hierarchically (Planner emits sub-tasks, each sub-task is its own R3) or move to **R4 ReAct** with mid-run adaptation.

**3. Inspectability requirement.** Does anyone — a human reviewer, a policy checker, an audit log, a downstream component — need to *see the plan before it runs*? Yes → R3 (the plan is a discrete artifact). No → consider **R4** or **R5 ReWOO**. R3 is the natural pattern for high-stakes or regulated workflows because the plan can be gated by **V1 Human-in-the-Loop**.

**4. Adaptation budget.** Count how often, on a labelled test set, the plan needs to change mid-execution because reality diverged. **Replan rate ≤ ~20%** → R3 is efficient (most runs execute the plan as-is). **Replan rate ≥ ~50%** → planning is wasted work; choose **R4 ReAct**, where every step is already adaptive.

**5. Loop discipline.** When replanning is enabled, it is a loop — Plan → Execute → Detect failure → Replan → Execute. Pair with **V9 Bounded Execution** to cap replans (3 is a common ceiling). Without a bound, a hard task can cascade replans indefinitely. Pair with **V14 Trajectory Logging** to record both the plans and the deltas between them — the diff is the diagnostic.

**Quick test — R3 is the right pattern when:**

- the step list is non-trivial and cannot be written at design time, *and*
- planning is materially harder than executing individual steps, *and*
- the plan is worth inspecting before execution (audit, gate, or cost), *and*
- the expected replan rate is low (< ~20% of runs).

If the step list *is* fixed at design time, drop to **S4 Instruction Decomposition** (one call) or **O2 Prompt Chaining** (fixed multi-call). If the environment forces frequent replanning, lift to **R4 ReAct**. If planning *plus* searching over alternative plans is what's needed, lift to **R9 Tree of Thoughts** or **R10 LATS**. If the task is orchestrating workers, **O6 Orchestrator-Workers** uses R3 as its canonical inner pattern — the orchestrator plans, the workers execute.

## Structure

```
            Task
              │
              ▼
       ┌─────────────┐
       │   Planner   │  ◀── strong model; sees the whole task once
       └──────┬──────┘
              │
              ▼
        Plan (artifact: ordered step list)
              │
              ▼
      ┌─────────────────┐
      │   (optional)    │
      │  Plan Reviewer  │  ◀── V1 human / rule check / V15 LLM-judge
      └────────┬────────┘
               │ approved
               ▼
       ┌──────────────┐
       │   Executor   │  ◀── cheap model or chain; one call per step
       └──────┬───────┘
              │
       per-step results
              │
              ▼
     ┌─────────────────┐
     │  Failure?       │── no ──▶  Final answer
     └────────┬────────┘
              │ yes
              ▼
       ┌──────────────┐
       │   Replanner  │ ── V9-bounded ──▶ back to Executor
       └──────────────┘
```

The two-call minimum is Planner → Executor. The full pattern adds an optional Plan Reviewer (gate) before execution and a Replanner (recovery) after a step fails. The Executor is "one call per step" in the default form; the executor can also be a chain (**O2**), a parallel fan-out (**O4**), or a delegation to workers (**O6**).

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Planner (LLM)** | producing the ordered plan from the full task | task description → ordered step list | execute the steps it plans — a Planner that also executes loses the asymmetry the pattern depends on, and is incentivised to write plans it can run rather than plans that are right. |
| **Plan** *(artifact, not a process)* | the inspectable step list itself | — → ordered steps | be implicit or buried in the Planner's free-form output. The plan must be a structured, parseable artifact (numbered list, JSON, etc.) so the Executor and any reviewer can read it. |
| **Plan Reviewer** *(optional)* | gating the plan before execution | plan → approve / revise / reject | rewrite the plan inline — review is approve/reject; revisions go back to the Planner so the Planner's behaviour can be tracked and improved. |
| **Executor (LLM or chain)** | running each step of an approved plan | plan + step index → step result | rewrite the plan to suit itself. An Executor that edits the plan mid-run undoes the inspectability the Planner produced and silently shifts where decisions are made. |
| **State / Scratchpad** | carrying step results forward across executions | step *n* result → step *n+1* input | grow unboundedly — a long plan must compact or summarise old step results (**K6**) before the Executor's context overflows. Typically a **K8 Working Memory** entry. |
| **Replanner (LLM)** *(optional)* | producing a revised plan when execution fails | original plan + failure signal + state → new plan | retry the failed step verbatim — that is the Executor's retry. The Replanner's job is structural: re-order, drop, or add steps in light of what was learned. |

The pattern's discipline is the separation of Planner and Executor. They are *different sessions*, even when they use the same model — different setups, different prompts, different success criteria. Mixing them is the pattern's most common failure: a Planner that drifts into executing produces vague plans; an Executor that drifts into replanning produces inconsistent runs.

## Collaborations

A task arrives. The Planner sees the whole task at once and emits a structured plan — typically a numbered list of steps in JSON or similar machine-readable form. The Plan is now a discrete artifact: it can be logged, displayed, gated, or edited. An optional Plan Reviewer (human via **V1**, a rule, or an **V15 LLM-as-Judge** call) approves or rejects the plan before any step runs; on rejection, the plan returns to the Planner with the reviewer's notes.

Once approved, the Executor runs steps in order. Each step is a separate LLM call (or a chain of calls, or a tool invocation) reading the current step from the plan and the relevant state from the scratchpad. After each step the scratchpad updates with the result. If a step fails — a tool error, a constraint violation, a quality-evaluator rejection — control passes to the Replanner with the original plan, the failure signal, and the state so far. The Replanner emits a revised plan; execution resumes from the relevant step. **V9 Bounded Execution** caps the number of replans; without it, a hard task can cascade replans indefinitely. **V14 Trajectory Logging** records every plan, every step, and the diff between successive plans — that diff is the pattern's primary diagnostic signal when something goes wrong.

## Consequences

**Benefits**
- Plan quality and execution efficiency tune independently — strong model for planning, cheap model (or deterministic code) for execution.
- The plan is an inspectable artifact: humans, policy checks, and audit logs can read it before any step runs.
- 5–10× fewer LLM calls than **R4 ReAct** on tasks whose step sequence holds up — the bulk of reasoning happens once, in the Planner, not at every step.
- Failure localises to a step, with the surrounding plan visible — debugging is straightforward.
- Composes cleanly with **O6 Orchestrator-Workers** (R3 is the orchestrator's inner pattern), **O4 Parallelization** (an executor that runs independent steps in parallel), and **K8 Working Memory** (the plan and step results live in the scratchpad).

**Costs**
- Two LLM calls minimum, even for tasks where one would do — overhead is wasted on simple work.
- The plan is committed before execution sees anything; if reality diverges, the cost of the plan is sunk before adaptation begins.
- Authoring two prompts (Planner and Executor) is more work than authoring one.
- Less cache-friendly than a single-call pattern — the Planner output changes the Executor's prefix. The Executor's prefix (plan + all prior step results) grows with each step — O(n²) attention cost (mechanism 2) — and cannot hit the provider prefix cache because the prefix changes every step. Keep step results in a scratchpad (K8) and pass only the current step + the plan to the Executor to bound context growth.

**Risks and failure modes**
- *Bad-plan-followed-faithfully* — the Executor runs an incorrect plan to completion, producing a confidently wrong answer that *looks* well-structured because it followed an explicit plan. The Plan Reviewer exists to catch this.
- *Plan-step impossible-in-context* — the Planner writes a step that cannot be executed with the available tools or state. Detected at execution; cost of detection is sunk planning effort.
- *Executor drift* — the Executor reinterprets the plan, skipping or merging steps. Pair the Executor's prompt with a strict "execute exactly step N as written; do not skip, merge, or reorder" instruction.
- *Replan storm* — without a hard cap, a hard task triggers replan after replan, each one slightly different, never converging. **V9** is mandatory when replanning is enabled.
- *Plan rot mid-run* — long executions accumulate state that contradicts an early step of the plan; the Executor either notices and stalls or doesn't notice and produces nonsense. Mitigation: a lightweight checkpoint after each step (**V10**) that revalidates the next step against current state.
- *Planner/Executor session blur* — using one prompt for both, or one LLM session for both, lets the model decide implicitly how much to plan vs. execute on each call. The pattern's discipline depends on the two being structurally separate.

## Implementation Notes

- The Plan must be a *structured artifact*, not free-form prose. Use a numbered list, JSON array of step objects, or YAML — anything the Executor can parse step-by-step. Free-form plans force the Executor to re-plan implicitly on every step.
- The Planner's prompt should explicitly say "do not execute the steps; only plan them." Without this, capable models will start to answer immediately, conflating R3 with R1/R2.
- The Executor's prompt should name the *single* step it is running and say "execute exactly this step; do not advance to or summarise other steps." This blocks Executor drift.
- Use a strong model for the Planner and a cheaper one for the Executor — that asymmetry is half the cost benefit. The Planner runs once; the Executor runs many times.
- Always pair with **V9 Bounded Execution** when replanning is enabled. A common ceiling is 3 replans; one is often enough.
- Log both plans and the diffs between them (**V14**). The plan-diff is the most informative debugging signal R3 offers.
- For inspectability, render the plan to the user (or operator) between Planner and Executor. The first time a plan is rendered, half the bugs in the Planner's prompt become visible.
- When the Executor's steps may be independent, fan out with **O4 Parallelization** — R3 + O4 is a common production composition.
- When the executor delegates to specialist workers, lift to **O6 Orchestrator-Workers** — R3 *is* the orchestrator's inner pattern. The Planner becomes the orchestrator's planning step; the Executor becomes the orchestrator's delegation step.
- The plan is a natural **K8 Working Memory** entry — write it to the scratchpad once and let every step read from there rather than re-passing it. When executions are long, the growing scratchpad accumulates tokens that every subsequent Executor call must attend over at O(n²) cost (mechanism 2). Use K6 Context Compression on old step results to bound this.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** R3 chains a *Planner* session with an *Executor* session (or chain) against a shared scratchpad. The Planner's prompt typically composes **S3 Persona** (planner role) + **S5 Constraint Framing** (planning constraints) + **S6 Output Template** (the plan schema). The Executor composes **S3** + **S6** for each step's output. R3 pairs with **K8 Working Memory** for the plan/state scratchpad, **V9 Bounded Execution** for replan caps, **V14 Trajectory Logging** for the plan-diff signal, and optionally **V1 Human-in-the-Loop** or **V15 LLM-as-Judge** for the Plan Reviewer.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Planner — produce a structured ordered plan from the task | `LLM` | Planner session, S3, S5, S6 |
| 2 | *(optional)* Plan Reviewer — approve / revise / reject before execution | `LLM (or rule)` | V1, V15 |
| 3 | Write plan to scratchpad | `code` | K8 Working Memory |
| 4 | For each step in plan: Executor — run step *n* | `LLM` | Executor session, S6 |
| 5 | Append step result to scratchpad | `code` | K8 |
| 6 | Branch — step failed? → Replanner; else next step | `code` | V9 |
| 7 | Replanner — produce a revised plan from failure + state | `LLM` | Replanner session |
| 8 | Loop to step 3 with the new plan; cap by V9 | `code` | V9 |

**Skeleton** — the wiring; each `# LLM` line is a configured session, not a bare call:

```
plan_and_solve(task):
    plan = Planner(task) ──────────────────────────── # LLM
    if reviewer_enabled:
        verdict = PlanReviewer(plan) ───────────────── # LLM (or rule)
        if verdict.rejected: return revise_with_planner(plan, verdict)
    scratchpad.write("plan", plan)                     # code — K8

    for replan_round in range(MAX_REPLANS):            # V9-bounded
        for step in plan.steps_from(current_index):
            result = Executor(step, scratchpad.read()) ─# LLM
            scratchpad.append(step.id, result)         # code
            if step_failed(result):
                plan = Replanner(plan, result, scratchpad) ─ # LLM
                scratchpad.write("plan", plan)         # code
                break                                  # restart inner loop
        else:
            return scratchpad.final_answer()           # all steps succeeded
    raise ReplanBudgetExceeded                         # V9 fired
```

**The LLM sessions.** Each `LLM` step must be *set up* before its first call. Setup is loaded once; the per-call prompt then wraps only the data that changes.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Planner** | strong generalist (or a reasoning model) — *plan quality caps the value of the whole pattern* | role: *"you produce ordered, executable plans; you do not execute them"*; the **plan schema** (numbered list with `{id, action, depends_on, expected_output}` per step); planning constraints (S5); the available tools / executor capabilities; *"output only the plan as JSON; do not solve any step"* | the task description |
| **Plan Reviewer** *(optional)* | small generalist, or a deterministic rule, or a human via V1 | role: *"you approve, revise, or reject plans"*; the policy or rubric the plan must satisfy; output contract (APPROVE / REJECT + notes) | the plan + the task |
| **Executor** | cheap fast generalist — runs many times | role: *"you execute exactly one step of a larger plan"*; how to read step inputs from the scratchpad; output contract (S6) for a step result; *"do not advance, summarise, or revise other steps"* | the current step + the scratchpad slice it needs |
| **Replanner** | the same strong model as the Planner; same setup with an addendum | Planner setup + addendum: *"you are revising a plan that failed; given the original plan, the failure, and the state so far, produce a new plan that completes the task; reuse completed steps"* | the original plan + the failure signal + the scratchpad |

Concretely, for the **Planner** the setup says *"You produce ordered, executable plans. Output a JSON array of step objects with fields {id, action, depends_on, expected_output}. Do not solve the task — produce only the plan. The available executor can call the following tools: …"* and the per-call prompt carries only *"Task: {task}"*.

**Specialist-model note.** No fine-tuned specialist is required. Two structural choices change everything:

- **Planner and Executor are separate sessions, even when the same model serves both.** Same model is fine; different setups, different invocations. Mixing them is the pattern's most common failure mode. The Planner's setup forbids execution; the Executor's setup forbids planning.
- **Asymmetric model choice is the pattern's primary cost lever.** Use the strongest available model (or a reasoning model: o-series, R-series) for the Planner — it runs once. Use a cheap fast model for the Executor — it runs many times. The cost difference compounds over plan length.

A capable generalist suffices for both. The artifact that does the heavy lifting is the **plan schema** in the Planner's setup — a strict, parseable structure (JSON array of step objects with explicit dependency edges) is what makes the Executor cheap and the plan inspectable. A free-form plan undoes most of the pattern's benefit.

## Open-Source Implementations

- **Plan-and-Solve Prompting** — [`github.com/AGI-Edgerunners/Plan-and-Solve-Prompting`](https://github.com/AGI-Edgerunners/Plan-and-Solve-Prompting) — Wang et al.'s original ACL 2023 implementation; prompt templates (IDs 101–307 for PS and PS+ variants), datasets, runners. The canonical reference for the single-prompt Plan-and-Solve formulation.
- **LangGraph plan-and-execute tutorial** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — production-grade reference implementation of the two-call / replan-on-failure form (`docs/tutorials/plan-and-execute/`). The closest match to the structure diagrammed above. JavaScript twin at [`github.com/langchain-ai/langgraphjs`](https://github.com/langchain-ai/langgraphjs) under `examples/plan-and-execute/`.
- **LangChain Plan-and-Execute agents** — the original Plan-and-Solve prompts were upstreamed into LangChain as the "Plan-and-Execute" agent (now superseded by the LangGraph tutorial above for new builds).
- **Together AI cookbook** — [`github.com/togethercomputer/together-cookbook`](https://github.com/togethercomputer/together-cookbook) — `Agents/LangGraph/LangGraph_Planning_Agent.ipynb` runs the LangGraph plan-and-execute graph on Together's hosted models; a useful second reference for the wiring.

## Known Uses

- **AutoGPT / BabyAGI lineage** — early autonomous-agent prototypes used an explicit task-list planner feeding a worker loop; structurally R3 (often with R3 + R7 Reflexion).
- **LangGraph-based production agents** — the plan-and-execute reference graph is a common starting point for agents whose tasks have predictable step structure (research, report generation, structured workflows).
- **Coding agents with a planning phase** (Devin, Cursor "Agent Mode", Claude Code's plan mode) — emit a plan for user review before touching the codebase; the user's approval is the **V1** gate on the plan.
- **Deep-research products** (Perplexity Pro Research, OpenAI/Anthropic deep-research modes) — a planning step produces a research outline that the executor then fills out; the outline is shown to the user.
- **Enterprise workflow agents in regulated domains** — the plan is the audit artifact; **V1 Human-in-the-Loop** approves it before any step touches a system of record.

## Related Patterns

- **Refines** **R1 Zero-Shot CoT** and **R2 Few-Shot CoT** — CoT thinks step-by-step inside one call; R3 lifts the "plan" out into its own call so the plan is a separable artifact. R3 is what CoT becomes when planning quality matters enough to pay an extra call.
- **Sibling of** **S4 Instruction Decomposition** at agent scope — S4 is the *prompt-level* instance of ordered execution (one call carrying an authored step list); R3 is the *agent-level* instance (two or more calls, with the step list generated at runtime by a Planner). S4 ↑ R3 is the upgrade path when the step list cannot be authored at design time.
- **Distinct from** **R4 ReAct** — R4 makes decisions step-by-step with full observation feedback; R3 commits to a plan upfront and replans only on failure. R3 trades adaptability for efficiency and inspectability; R4 trades efficiency for adaptability. Production systems often use **R3 as the outer loop with R4 inside individual execution steps** when a step itself needs to be exploratory.
- **Distinct from** **R5 ReWOO** — ReWOO is plan + parallel tool execution + solver, with placeholder variables flowing between them; R3 is plan + sequential (or fan-out) execution against a state scratchpad. ReWOO is more token-efficient when steps are independent; R3 is more flexible when steps depend on prior results.
- **Distinct from** **R9 Tree of Thoughts** / **R10 LATS** — ToT and LATS search over alternative plans; R3 commits to one plan and replans only on failure. Use ToT / LATS when the right plan is unknown and worth searching for; use R3 when a competent Planner can produce a workable plan first-try.
- **Required by** **O6 Orchestrator-Workers** — R3 is the canonical inner pattern for an orchestrator: the orchestrator's planning step *is* the R3 Planner; the delegation step *is* the R3 Executor (with workers as the per-step callee). An orchestrator without R3 is a Loop Agent (**O8**).
- **Composes with** **O4 Parallelization** — the Executor can fan out independent plan steps to parallel calls; the plan's dependency edges (`depends_on`) tell the wiring which steps can parallelise.
- **Composes with** **K8 Working Memory** — the plan and per-step results are the canonical contents of a scratchpad; an R3 system without K8 ends up re-passing the plan in every Executor call (wasted tokens).
- **Composes with** **V1 Human-in-the-Loop** — the Plan Reviewer is the natural place for human approval; the plan is the artifact a human can read in seconds, where a ReAct trajectory cannot.
- **Composes with** **V9 Bounded Execution** — replan caps; mandatory when replanning is enabled.
- **Composes with** **V14 Trajectory Logging** — log both plans and their diffs; the diff is the diagnostic signal.
- **Composes with** **R7 Reflexion** — after a run fails, Reflexion's verbal critique can feed the Replanner; R3 + R7 is the canonical "learn from failure across plans" loop.

## Sources

- Wang, L., Xu, W., Lan, Y., Hu, Z., Lan, Y., Lee, R. K.-W., Lim, E.-P. (2023) — "Plan-and-Solve Prompting: Improving Zero-Shot Chain-of-Thought Reasoning by Large Language Models" (arXiv 2305.04091, ACL 2023). The primary reference; introduces the Plan-and-Solve (PS) and PS+ prompt formulations and shows zero-shot reasoning gains over Zero-Shot CoT on arithmetic, symbolic, and commonsense benchmarks.
- Wei, J., Wang, X., Schuurmans, D., et al. (2022) — "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models." The single-call antecedent that R3 lifts apart.
- Yao, S., Zhao, J., Yu, D., et al. (2022) — "ReAct: Synergizing Reasoning and Acting in Language Models" (arXiv 2210.03629). The adaptive counterpoint; R3 trades ReAct's per-step adaptation for upfront planning and inspectability.
- LangChain / LangGraph documentation — "Plan-and-Execute" agent tutorial and runnable reference graph; production-grade embodiment of the two-call + replan-on-failure form.
- Anthropic — "Building effective agents" (2024); names "Orchestrator-Workers" with an explicit Planner as a primary multi-step pattern, with R3 as its inner reasoning shape.
- *Architecting Resilient LLM Agents: A Guide to Secure Plan-then-Execute* — arXiv 2509.08646 — security analysis of the plan-then-execute architecture, motivating the Plan Reviewer / V1 gate.
