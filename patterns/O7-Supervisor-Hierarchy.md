# O7 — Supervisor Hierarchy

> Decompose the orchestrator's job across a multi-level tree of supervisors — a root supervisor delegates to sub-supervisors, which delegate to workers — so each node coordinates only a bounded set of children instead of the whole fleet.

**Also Known As:** Hierarchical Agents, Multi-Level Delegation, Tree of Agents, Nested Supervisors, Hierarchical Multi-Agent System (Hierarchical MAS).

**Classification:** Category IV — Orchestration · Band IV-B Agentic Patterns · a *recursive composition* of O6 — each non-leaf node is an O6 Orchestrator over its direct children.

---

## Intent

Scale orchestration past the point where a single coordinator can hold all worker context, by stacking O6 Orchestrator-Workers nodes into a tree where every supervisor manages only its direct children.

## Motivation

O6 Orchestrator-Workers works beautifully up to a point: one orchestrator decomposes the goal, dispatches to a handful of workers, and synthesises the results. That point arrives sooner than people expect. Once the orchestrator is juggling more than roughly five to ten concurrent worker specialisations — each with its own tool surface, its own intermediate state, its own progress signal — the orchestrator's context window starts carrying the load of *the whole system*. Decisions get worse, dispatch starts misrouting, synthesis loses the thread.

The naive fixes all fail. Adding tools to the orchestrator hits the V13 tool-budget ceiling (selection accuracy collapses past ~15 tools). Adding workers without changing the topology just makes the orchestrator's job harder. Splitting the task across multiple peer orchestrators — O10 Swarm — loses the very thing O6 was good at: a single point that owns the goal and integrates the answer.

The right move is structural: introduce a *level*. A root supervisor that thinks in workstreams, not tasks; sub-supervisors that each own a workstream and decompose it into tasks; workers that execute tasks.

The O6 bottleneck is mechanical, not just architectural. As the orchestrator accumulates worker outputs, its context length grows. Attention is n² in compute over seq_len — every new token added to the orchestrator's context pays pairwise attention against all prior tokens (mechanism 2) — and U-shaped in recall: worker outputs arriving in the middle of a long context are geometrically under-attended even when technically in window (mechanism 4). A supervisor hierarchy fixes this by bounding each supervisor's context: the root supervisor sees workstream summaries, not raw worker output. Each level pays n² over a bounded length (mechanisms 2, 4). Each node is still an O6 — the same dispatch-and-synthesise machinery — but applied recursively over a smaller, bounded scope. Google's AI co-scientist (Gemini, 2025) exemplifies this: a Supervisor agent at the root, six specialised agents (Generation, Reflection, Ranking, Proximity, Evolution, Meta-Review) underneath, each running over worker queues. The Supervisor never asks "what does this hypothesis say" — that's a Reflection-agent question; it asks "which sub-agent should run next, and with what resources." That is the pattern's defining move: separate the *what-next* decision (each level) from the *how-to-execute* decision (the level below).

## Applicability

Use when:

- O6 is provably bottlenecked — the orchestrator's context fills with worker chatter, or its tool surface exceeds the V13 budget, or coordination latency dominates;
- the domain has natural hierarchical decomposition — project $\to$ workstream $\to$ task, research goal $\to$ strategy $\to$ hypothesis-action, ticket $\to$ triage-class $\to$ resolution-step;
- worker count exceeds the ~5–10 a single orchestrator can coordinate cleanly;
- different sub-tree branches need genuinely different coordination policies (the Generation-branch supervisor in co-scientist runs a tournament; the Reflection-branch supervisor runs a review queue).

Do not use when:

- a single orchestrator can still coordinate the workers — use **O6 Orchestrator-Workers**;
- the task is a fixed pipeline, not dynamic delegation — use **O2 Prompt Chaining**;
- sub-tasks are independent and need only fan-out, not nested coordination — use **O4 Parallelization**;
- coordination should emerge from peer messaging without a central decision point — use **O10 Swarm / Mesh** (rarely the right answer in production);
- the problem is context contamination, not coordination volume — use **O17 Agent Isolation** to spawn fresh sub-contexts under a single O6.

## Decision Criteria

O7 is right when one orchestrator can no longer cleanly coordinate the workers and the task decomposes hierarchically.

**1. Measure the O6 bottleneck.** Run the system as O6 first. Track:
- **Worker fan-out** — how many distinct worker specialisations does the orchestrator dispatch to? If > ~8, dispatch quality degrades.
- **Orchestrator context occupancy** — what % of the orchestrator's window is worker output it must integrate? If > ~50%, the orchestrator is doing worker work. This is mechanically grounded: worker outputs accumulate in context, and the quadratic attention cost means every additional worker result adds to the compute burden for all subsequent generation steps (mechanism 2); additionally, results from earlier workers are geometrically under-attended due to U-shaped recall when buried in the middle of a long context (mechanism 4).
- **Tool count on the orchestrator** — if > 15, V13 says selection accuracy is collapsing.

If all three are comfortable, stay on **O6**.

**2. Score the hierarchical decomposition.** Can you name two levels of grouping (workstreams under goals, task-classes under workstreams)? If the decomposition is forced — workers grouped only because grouping was required — the hierarchy will not earn its keep; stay on **O6** with **O17 Agent Isolation** for context hygiene instead.

**3. Cost the tree.** Each level adds at least one supervisor LLM call per decomposition step. A 3-level tree multiplies orchestration calls; budget for it. Pair with **V14 Trajectory Logging** so the calls are debuggable across levels.

**4. Sub-tree heterogeneity.** Do different branches need different coordination *policies* (one runs a tournament, one runs a queue, one runs a debate)? If yes, the hierarchy is paying — each sub-supervisor specialises. If every branch coordinates the same way, **O6 + O4 Parallelization** is enough.

**5. Loop and budget discipline.** Pair with **V9 Bounded Execution** at *every* level — runaway recursion across multiple orchestrators is the catastrophic failure mode. Each supervisor needs its own iteration cap and budget.

**Quick test — O7 is the right pattern when:**

- O6 was tried first and demonstrably bottlenecked (worker fan-out, context occupancy, or tool count), *and*
- the domain has a natural two-or-more-level decomposition (workstreams under goals, sub-tasks under workstreams), *and*
- sub-trees need different coordination policies, not just more workers of the same shape, *and*
- V14 logging and V9 bounds are in place at every level before launch.

If any condition fails, fall back. If O6 still copes, stay on **O6**. If the issue is sub-task context noise rather than coordination capacity, add **O17 Agent Isolation**. If sub-tasks are independent and uniform, use **O4 Parallelization**. If the decomposition is fixed and known at design time, use **O2 Prompt Chaining** of O6 blocks rather than a dynamic hierarchy.

## Structure

```
                    ┌─────────────────────┐
                    │   Root Supervisor   │   ← owns the goal
                    │  (O6 over level 1)  │     decomposes into workstreams
                    └──────────┬──────────┘
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
        ┌────────────┐  ┌────────────┐  ┌────────────┐
        │  Sub-Sup A │  │  Sub-Sup B │  │  Sub-Sup C │   ← own workstreams
        │ (O6 lvl 2) │  │ (O6 lvl 2) │  │ (O6 lvl 2) │     decompose into tasks
        └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           ┌───┴───┐        ┌──┴──┐         ┌──┴──┐
           ▼       ▼        ▼     ▼         ▼     ▼
        ┌────┐ ┌────┐    ┌────┐ ┌────┐   ┌────┐ ┌────┐
        │ W1 │ │ W2 │    │ W3 │ │ W4 │   │ W5 │ │ W6 │   ← workers execute tasks
        └────┘ └────┘    └────┘ └────┘   └────┘ └────┘
            ▲              ▲                  ▲
            │              │                  │
        results bubble up; each level synthesises before passing upward
```

Each non-leaf node is an O6 instance: it dispatches downward and synthesises upward. The tree's *shape* is the design choice — depth, branching factor, where the leaves sit.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Root Supervisor** | the top-level goal and the workstream decomposition | user goal $\to$ workstream assignments + final synthesis | execute tasks, or reach past its direct children. If the root is making task-level decisions, the tree has collapsed back to O6 and the levels below are wasted. |
| **Sub-Supervisor** | one workstream — its task decomposition and worker dispatch | workstream brief from parent $\to$ task results synthesised for the parent | reach across to peer sub-supervisors (siblings communicate only through the parent), or escalate trivia. Cross-branch chatter destroys the bounded-scope property. |
| **Worker** | executing one task with its tool set | task brief $\to$ task result | spawn its own sub-tree (only supervisors spawn), or report sideways. A worker that delegates is a sub-supervisor in disguise — promote it explicitly. |
| **Handoff Contract** | the schema for parent $\leftrightarrow$ child messages | structured brief schema; result schema | be free-form prose. Schema drift between levels is the most common failure mode — each handoff loses fidelity. |
| **Trajectory Logger** *(required, not optional)* | full trace across all levels | every supervisor and worker call $\to$ linked, queryable trace | be per-level — a hierarchy without an end-to-end trace is undebuggable. (See V14.) |
| **Budget Governor** *(required, not optional)* | per-level iteration, cost, and time caps | each supervisor's run state $\to$ continue / halt | be set only at the root — every level needs its own cap, or one branch cascades while another sits idle. (See V9.) |

The pattern's load-bearing rule: **a worker that delegates is a sub-supervisor.** If the role grows delegation responsibility, promote it formally — adding a level in the tree — rather than letting workers spawn workers ad hoc.

## Collaborations

A user goal arrives at the Root Supervisor. The Root decomposes it into workstreams and writes a structured brief for each, dispatching to the appropriate Sub-Supervisor (Handoff Contract). Each Sub-Supervisor decomposes its workstream into tasks and dispatches to its Workers — running tasks in parallel (O4) where independence permits. Workers execute, report results back to their Sub-Supervisor, which synthesises them into a workstream-level result. Sub-Supervisor results bubble up to the Root, which synthesises them into the final answer.

At every level, the Budget Governor enforces an iteration cap (V9): a Sub-Supervisor that has not closed its workstream after N rounds escalates to the Root rather than spinning. The Trajectory Logger (V14) writes every supervisor and worker call into one linked trace, so a failure at any level can be located. Siblings never talk to siblings — all cross-branch information flows through the common ancestor — preserving the bounded-scope property that makes the tree easier to reason about than a fully connected mesh.

Google's AI co-scientist runs exactly this shape: Supervisor at the root; specialised agents (Generation, Reflection, Ranking, Proximity, Evolution, Meta-Review) as sub-supervisors over worker queues; iterative bubble-up of hypotheses through tournament-style ranking. The Supervisor never reads a hypothesis — it reads sub-agent outputs and decides which sub-agent to run next.

## Consequences

**Benefits**
- Scales past the single-orchestrator coordination ceiling — each level handles bounded fan-out.
- Sub-trees can specialise in coordination *policy* (tournament, queue, debate), not just worker content.
- Per-level budgets and traces make a large fleet tractable to operate.
- Failures localise — a bad worker fails its sub-supervisor's workstream, not the whole system.
- Composes recursively with O6, O4, O17 at any level.

**Costs**
- Multiplied LLM calls — every level adds at least one supervisor decision per step.
- Increased latency on the critical path through the tree (depth $\times$ supervisor-call time).
- Schema discipline — every Handoff Contract between levels must be maintained as the system evolves.
- Cross-level debugging is hard without first-class V14 trace plumbing.

**Risks and failure modes**
- *Information loss at boundaries* — each handoff is a summarisation; details drop. Mitigation: keep schemas typed and require provenance fields.
- *Cascading recovery* — a failed sub-supervisor escalates, the parent re-dispatches, the new sub-supervisor fails differently, retry storms emerge. Mitigation: V9 caps at every level, not just the root.
- *Sibling backchannels* — once peers start coordinating directly, the tree turns into a mesh and you have O10 by accident. Hold the line: all cross-branch flow through the common ancestor.
- *Premature hierarchy* — splitting O6 into O7 before O6 has demonstrably failed. The tree pays for itself only when O6 is genuinely bottlenecked.
- *Supervisor-as-worker* — a supervisor that starts inspecting raw worker outputs has reverted to doing worker work. Detect via context-occupancy monitoring on the supervisor.

## Implementation Notes

- **Try O6 first, always.** O7 is justified only after measurement, not by anticipation. Many systems that look "obviously hierarchical" run fine as O6 + O4 + O17.
- **Branching factor of three to six per supervisor** is a comfortable target. Higher and the supervisor's context fills; lower and the hierarchy is wasted.
- **Depth of two** is sufficient for most production systems. Three is rare and usually a sign that the decomposition is unnatural.
- **Specialise sub-supervisors by coordination policy**, not just by worker type. If two branches coordinate identically, merge them.
- **Schemas for handoff are the load-bearing artefact.** Define them up front (`S6 Output Template`) and version them. Free-form briefs between levels degrade the system within weeks.
- **Pair with V14 from day 1.** A hierarchy without a linked end-to-end trace is operationally opaque — every incident becomes a multi-day excavation.
- **Per-level V9 budgets.** A root cap is not enough — set caps inside every sub-supervisor too.
- **Composes with O17 Agent Isolation** — each worker (and often each sub-supervisor) should run with a fresh, isolated context, not inherit the parent's full history.
- **Composes with O4 Parallelization** at every level — sub-supervisors should fan out to their workers in parallel when sub-tasks are independent.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** O7 is **O6 applied recursively**. It chains with **O4 Parallelization** (sibling sub-supervisors or sibling workers run in parallel), **O17 Agent Isolation** (each child runs in a fresh context), **V9 Bounded Execution** (per-level iteration and cost caps), **V14 Trajectory Logging** (linked end-to-end trace), and **S6 Output Template** (the Handoff Contract schemas). Each agent inside the tree typically runs **R4 ReAct** internally.

**The chain — per supervisor step (recursive at every level):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Receive structured brief from parent (or initial user goal) | `code` | S6 schema |
| 2 | Decompose: identify children to dispatch to + their briefs | `LLM` | Supervisor session |
| 3 | Dispatch in parallel to children (workers if leaf, sub-supervisors if not) | `code` | O4, O17 |
| 4 | Each child runs: recursive call (sub-supervisor) or worker execution | `LLM` | child session(s) |
| 5 | Collect child results | `code` | |
| 6 | Synthesise into a result for *this* level | `LLM` | Supervisor session |
| 7 | Check budget / iteration cap; loop to step 2 if not done | `code` | V9 |
| 8 | Return structured result up to parent | `code` | S6 schema |

**Skeleton** — `run_node` is recursive; it is a supervisor at non-leaf nodes and a worker at leaves:

```
run_node(node, brief, depth):
    log_open(node, brief)                              # code — V14
    state = init(brief)
    for round in range(node.max_rounds):               # code — V9 per-level cap
        plan = Supervisor(node, state)                 # LLM   — decide which children to invoke
        if plan.done: break
        child_results = parallel_map(                  # code — O4
            lambda c: run_node(c.target,               # recursive: workers or sub-supervisors
                               c.brief,
                               depth + 1),             # each child gets fresh context — O17
            plan.dispatches
        )
        state = Synthesiser(node, state, child_results)  # LLM — synthesise this level's progress
    result = Finaliser(node, state)                    # LLM — produce result for parent
    log_close(node, result)                            # code — V14
    return result                                      # under the Handoff Contract schema

# at leaves, run_node degenerates: no children, no dispatch — just Worker(brief).
```

**The LLM sessions** — every supervisor is the same *kind* of session, differing only in the level's policy:

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Root Supervisor** | strong generalist (the system's best reasoning model) | role: *"you decompose a goal into workstreams and dispatch to sub-supervisors"*; the list of sub-supervisors and their capabilities; the Handoff Contract schema for outgoing briefs (S6); termination criteria | the user goal + the current state (workstreams in-flight, results so far) |
| **Sub-Supervisor** *(one configured session per sub-supervisor role — Generation, Reflection, …)* | capable generalist; can be smaller than Root | role specific to its workstream (*"you run the hypothesis-generation queue"*); the list of workers it dispatches to; coordination policy (queue / tournament / debate); the Handoff Contract schema | the workstream brief from the parent + current sub-workstream state |
| **Worker** | model fit to the task (small fast for narrow ops; strong for hard sub-tasks) | role specific to the task; tool definitions; output schema | the task brief |
| **Synthesiser** *(per supervisor)* | same model as that supervisor | role: *"integrate child results into a result for your parent"*; output schema | the children's returned results |

In the co-scientist concrete example: the **Root Supervisor** session has setup *"You orchestrate scientific reasoning. You dispatch to: Generation (proposes hypotheses), Reflection (critiques), Ranking (tournament), Proximity (deduplicates), Evolution (refines), Meta-Review (synthesises). Reply with a JSON dispatch plan."* The per-call prompt then wraps the current hypothesis pool and recent sub-agent outputs.

**Specialist-model note.** No fine-tuned specialist is structurally required. However, two pragmatic notes: (a) **Supervisors benefit from the strongest available model** — bad supervisor decisions cost more than bad worker decisions, because they shape what every worker below does; (b) **A long-context model materially helps the Root**, which must hold workstream state across many rounds. However, a long-context model does not eliminate the U-shaped recall problem (mechanism 4) — it merely pushes the failure point further out. Structure the root's context so that the most recently updated workstream state appears near the beginning or end of its context window, not buried in the middle. Workers can usually be small fast models. The standard production stack is *strong* model at root, *capable* model at sub-supervisor, *fit-to-task* model at workers — a model-tier hierarchy mirroring the agent hierarchy. Supervisors at each level benefit from stronger models because their task (decomposition and synthesis over accumulated workstream state) is more complex than individual workers' narrowly scoped tasks — this is model-size matching, where the architectural hierarchy mirrors the required reasoning complexity (mechanism 8). And even with a long-context model at root, the U-shaped recall problem means mid-context workstream entries are statistically under-attended (mechanism 4). (Mechanisms 4, 8.)

## Open-Source Implementations

- **LangGraph Supervisor (Python)** — [`github.com/langchain-ai/langgraph-supervisor-py`](https://github.com/langchain-ai/langgraph-supervisor-py) — the canonical library for building hierarchical multi-agent systems on LangGraph; supports multi-level supervisor-of-supervisors composition.
- **LangGraph Hierarchical Agent Teams tutorial** — [`github.com/langchain-ai/langgraphjs`](https://github.com/langchain-ai/langgraphjs/blob/main/examples/multi_agent/hierarchical_agent_teams.ipynb) — runnable reference graph showing a root supervisor dispatching to team-supervisors, each managing worker agents.
- **CrewAI** — [`github.com/crewAIInc/crewAI`](https://github.com/crewAIInc/crewAI) — the `Process.hierarchical` mode wires a manager agent over a crew; a manager-of-managers configuration extends to multi-level. Note: the manager-delegation path has known sharp edges (see issue tracker), so audit the trace path in your stack.
- **Microsoft AutoGen — Nested GroupChat** — [`github.com/microsoft/autogen`](https://github.com/microsoft/autogen) — nested `GroupChat` lets a participant in an outer chat be itself a GroupChat, giving the hierarchical-supervisor shape via group nesting.
- **AI Co-Scientist (community implementation)** — [`github.com/The-Swarm-Corporation/AI-CoScientist`](https://github.com/The-Swarm-Corporation/AI-CoScientist) — open implementation of the Google "Towards an AI co-scientist" architecture; a worked O7 in code.

## Known Uses

- **Google AI Co-Scientist** (Gemini 2.0, 2025) — Supervisor agent over six specialised agents (Generation, Reflection, Ranking, Proximity, Evolution, Meta-Review), each running worker queues; the canonical O7 deployment in published research.
- **AWS Bedrock multi-agent collaboration** — supervisor-of-agents and supervisor-routing modes documented in AWS prescriptive guidance for enterprise agent deployments.
- **LangGraph production assistants** — multi-team configurations (research team + writing team + review team, each with its own supervisor) are a common production starting point.
- **CrewAI production crews** — hierarchical-process crews with manager agents are widely used for content-pipeline and research-pipeline automations.
- **Enterprise coding-agent fleets** — long-running coding agents that decompose a feature into sub-features (each with its own sub-supervisor and worker pool) commonly run an O7 over O6 + R4 inside each worker.

## Related Patterns

- **Refines** O6 Orchestrator-Workers — O7 is O6 applied recursively; the unit of composition is unchanged, the depth changes.
- **Composes with** O4 Parallelization — sibling sub-supervisors and sibling workers under one supervisor run in parallel.
- **Composes with** O17 Agent Isolation — each child runs in a fresh context, not the parent's full history.
- **Required by** V9 Bounded Execution — every level needs its own iteration / cost / time cap; a root-only cap is unsafe.
- **Required by** V14 Trajectory Logging — a hierarchy without an end-to-end linked trace is operationally opaque.
- **Pairs with** S6 Output Template — the Handoff Contract between levels is a Signal-layer schema artefact.
- **Pairs with** R4 ReAct — each agent inside the tree typically runs ReAct internally.
- **Distinct from** O6 Orchestrator-Workers — O6 is one level (flat workers); O7 is multi-level (orchestrators delegate to orchestrators). Choose O7 only after O6 is provably bottlenecked.
- **Distinct from** O10 Swarm / Mesh — O10 has no central decision point; O7 keeps a single root that owns the goal. Most "swarm" production claims are actually O7.
- **Distinct from** O11 Blackboard System — O11 has emergent agent activation against shared state; O7 has explicit top-down dispatch. They can compose (a sub-supervisor running over a blackboard) but answer different questions.
- **Competes with** O16 Hybrid Control Flow — O16 stacks loop primitives within one agent; O7 stacks agents within a tree. For coordination-heavy tasks O7 wins; for execution-heavy single-agent tasks O16 wins.

## Sources

- Gottweis et al. (2025) — "Towards an AI co-scientist." arXiv 2502.18864. The clearest published O7 deployment: Supervisor agent over six specialised sub-agents over worker queues.
- Anthropic (2024) — "Building Effective Agents." Orchestrator-workers pattern that O7 extends recursively.
- arXiv 2601.03328 — empirical multi-agent system study; documents "Hierarchical MAS" as one of the production network configurations.
- arXiv 2604.03515 — "Inside the Scaffold" empirical scaffold taxonomy; situates hierarchical orchestration among the loop-primitive choices in production agents.
- LangGraph documentation — Hierarchical Agent Teams tutorial and `langgraph-supervisor` library reference.
- AWS Prescriptive Guidance — hierarchical agent pattern in the multi-agent collaboration reference.
- CrewAI documentation — `Process.hierarchical` and manager-agent reference.
- Microsoft AutoGen documentation — nested GroupChat as the hierarchical-conversation building block.
