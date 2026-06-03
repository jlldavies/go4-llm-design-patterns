# O16 — Hybrid Control Flow

> Stack two or more *different* loop primitives — typically ReAct plus plan-execute plus generate-test-repair plus bounded retry — inside a single agent scaffold, each handling the phase of the task it is best at, with explicit transitions between them.

**Also Known As:** Primitive Stack, Layered Control, Composite Loop Architecture, Stacked-Primitive Scaffold.

**Classification:** Category IV — Orchestration · Band IV-B Agentic · a *composite control* pattern — it is one agent whose scaffold layers multiple loop primitives, not a pipeline of agents.

---

## Intent

Build a single agent that is competent across all phases of a complex task by stacking the loop primitives each phase needs — exploration on a ReAct loop, planning on plan-execute, repair on generate-test-repair, recovery on bounded retry — rather than trying to force every phase through one primitive.

## Motivation

Production coding agents do not run one loop. The scaffold taxonomy (Rombaut, 2026) cracked open 13 open-source coding agents at pinned commit hashes and found that **11 of 13 stack multiple loop primitives** inside a single scaffold rather than relying on a single control structure. Five primitives recur:

1. **ReAct** (R4) — Thought / Action / Observation; the default for *exploration* (read code, list files, search) where the next step depends on what the last action returned.
2. **Plan-execute** (R3) — produce a plan up front, then execute the steps; the default for *structured work* where the decomposition is worth committing to before action.
3. **Generate-test-repair** — generate code, run tests, fix failures; the default for *implementation* where an executable oracle exists.
4. **Multi-attempt retry** — re-run the previous loop with updated context on failure; the default for *recovery* from a single bad attempt.
5. **Tree search** (R10 LATS) — MCTS over candidate paths; the default for *hard decisions* where multiple promising branches must be compared.

No single primitive handles all phases well. A pure ReAct agent over-explores when the path is obvious; a pure plan-execute agent commits to plans that survive contact poorly; a pure generate-test-repair agent has nothing to do until it knows what to write; a pure retry loop fails the same way faster. Real agents address this empirically: ReAct to understand the code, plan-execute to lay out the fix, generate-test-repair to land it, retry to bound the recovery, tree search for the rare decision big enough to deserve it.

O16 is the name for that empirical fact. It is not "use whichever primitive you like" — that would be no pattern. It is a *composition discipline*: identify the task phases, name the right primitive for each, define the transitions explicitly, and bound the whole. The pattern's contribution is making the stack — and the transitions between layers — first-class engineering objects rather than implicit accidents of the scaffold.

This is distinct from **O8 Loop Agent** (a fixed cycle of *agents* — same pipeline, repeated rounds, one termination judge) and from **O6 Orchestrator-Workers** (a central agent dynamically delegating to other agents). O8 and O6 are multi-agent orchestrations. O16 is **one agent** whose internal control flow stacks multiple primitives. The unit of composition is the loop primitive, not the agent.

## Variants

Production stacks differ by which primitives they layer and in what order. Four common shapes:

- **Explore $\to$ Plan $\to$ Implement (the SWE-bench stack).** ReAct exploration, then plan-execute, then generate-test-repair for each plan step, wrapped in bounded retry. The dominant production coding-agent shape; observed in SWE-agent, OpenHands, and several closed agents.
- **Localize $\to$ Repair $\to$ Validate (the Agentless stack).** A three-phase plan-execute pipeline with no ReAct exploration phase — a deliberately *shallower* stack. Demonstrates that stacking does not always mean more layers; sometimes the win is dropping ReAct entirely (Xia et al., 2024).
- **ReAct + Generate-Test-Repair (the pair-programming stack).** No explicit plan phase; the agent reasons step-by-step (ReAct) and uses the test suite as the oracle. Closer to Aider's shape — lighter than the full four-layer stack, suitable for single-file changes.
- **Plan + ReAct (the strategic / tactical stack).** Plan-execute at the outer layer setting goals; ReAct at the inner layer executing each goal. Used in enterprise / supervisory agents where the plan is committee-approved and execution is tactical.

The variants are not exhaustive — production scaffolds vary. They are the *named recurring stacks* worth distinguishing because the choice of stack drives evaluation metrics, scaffold engineering, and where the agent will fail.

## Applicability

Use O16 when:

- the task has *distinct phases* with different control needs (e.g. explore, plan, implement, verify) and no single primitive serves all of them;
- you have already tried a single-primitive agent (R4 alone, or R3 alone) and observed it fail in specific phases;
- you can name the transitions between phases explicitly (signal, predicate, or judge that ends one layer and starts the next);
- you can bound every loop layer with V9 Bounded Execution — without bounds, a multi-layer scaffold is multiple ways to run forever.

Do not use when:

- the task has *one* phase and is well-served by one primitive — use **R4 ReAct** (exploration), **R3 Plan-and-Solve** (structured), or **O8 Loop Agent** (multi-agent cycles);
- the "phases" are actually role specialisations — that is **O8 Loop Agent** or **O6 Orchestrator-Workers**, not O16;
- a primitive can be skipped — every extra layer is failure surface; never add a layer the agent's evaluation does not need;
- transitions cannot be defined except by "the agent decides" — that is **O6** with dynamic delegation, not O16's principled stack;
- the loops cannot be bounded — without **V9 Bounded Execution** on every layer, you have anti-pattern **A3 Uncontrolled Recursion** in multiples.

## Decision Criteria

O16 is right when one agent must span multiple control regimes within a single coherent task, and the transitions between them are nameable.

**1. Count the distinct phases.** List the phases the task actually has (explore, plan, implement, verify, debug). If the count is one, use the matching single primitive (R4 / R3 / generate-test-repair / retry / R10) directly. If the count is two or more, O16 is a candidate. Production coding agents typically have three to four.

**2. Match each phase to its primitive.** For each phase, name the primitive that fits it best — the test is *"what does this phase's loop body do?"*. Reasoning over partial observations $\to$ R4 ReAct. Decomposing a goal upfront $\to$ R3 Plan-execute. Producing code against tests $\to$ generate-test-repair. Recovering from a bad single attempt $\to$ multi-attempt retry. Choosing between candidate paths $\to$ R10 LATS. If two phases reduce to the same primitive, they are one phase — collapse them.

**3. Define every transition explicitly.** Each layer boundary needs a *named transition signal*: a predicate (`exploration_done()`), a judge call (V15: "is the plan complete?"), or a hard event (tests pass). A scaffold whose layers blend ("the agent will know when to plan") is anti-pattern A1 God Prompt at the control-flow level. Document the transitions before writing the scaffold.

**4. Bound every layer.** Each loop primitive in the stack gets its own V9 cap — max ReAct steps, max plan-execute steps, max test-fix iterations, max retry attempts. The bounds are independent: hitting the ReAct cap should not silently restart plan-execute. Without per-layer bounds, the stack runs in O(product of layer depths) — anti-pattern A3 in multiples.

**5. Cost the stack.** Each layer is real LLM calls. A ReAct-explore phase of 20 steps + a plan of 10 steps + a test-fix loop of 5 rounds $\times$ 3 attempts is ~50–80 calls before counting retries. Compare against the simpler alternative: if a single-primitive agent + a stronger model would get the same result for fewer calls, prefer the simpler agent. O16 must earn its cost on tasks where no single primitive does the job.

**Quick test — O16 is the right pattern when:**

- the task has 2+ distinct phases with materially different control needs, *and*
- you can name the primitive that fits each phase and the transition between them, *and*
- each layer can be independently bounded by V9, *and*
- a single-primitive baseline has been tried and observed to fail in specific phases.

If only one phase exists, choose the single matching primitive — R4, R3, generate-test-repair, retry, or R10 — rather than stacking. If the phases are different *roles* repeated cyclically, choose **O8 Loop Agent**. If delegation is dynamic per task with no fixed phase structure, choose **O6 Orchestrator-Workers**. If transitions cannot be named, the scaffold is not yet ready to be O16 — name them first.

## Structure

```
   Task ─▶ ┌─────────────────────────────────────────────────────────────┐
           │                  ONE AGENT, ONE CONTEXT                      │
           │                                                              │
           │  ┌───────────────┐  T1   ┌──────────────┐  T2  ┌──────────┐ │
           │  │  Layer 1:     │ ────▶ │  Layer 2:    │ ───▶ │ Layer 3: │ │
           │  │  ReAct        │       │ Plan-execute │      │ Generate │ │
           │  │  (explore)    │       │ (decompose)  │      │ -Test    │ │
           │  │               │       │              │      │ -Repair  │ │
           │  │  V9 cap       │       │  V9 cap      │      │ V9 cap   │ │
           │  └───────────────┘       └──────────────┘      └──────────┘ │
           │       ▲                                              │       │
           │       │            Layer 4: Retry (outer)            │       │
           │       └──────────────────────────────────────────────┘       │
           │                       V9 cap                                 │
           │                                                              │
           │     Transitions T1, T2, … are explicit named signals:        │
           │       predicate, judge call, or hard event.                  │
           │     V14 Trajectory Logging records every layer's events.     │
           └─────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
                                    Result
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Scaffold** | the static composition — which primitives are layered, in what order, and the transitions between them | task type $\to$ layered control structure | be redesigned mid-run. The stack is fixed at build time; runtime adaptation is the **O6** pattern. |
| **Layer Primitive** *(one per layer: R4, R3, generate-test-repair, retry, R10, …)* | the control flow for *its* phase | layer-entry state $\to$ layer-exit state | be the same primitive as its neighbour. If two layers reduce to the same loop, they are one layer — collapse them. |
| **Transition Signal** *(one per layer boundary)* | the named predicate / judge / event that ends one layer and starts the next | layer state $\to$ ADVANCE / STAY / ABORT | be implicit. "The agent decides when to advance" is **O6** dynamic delegation, not O16. |
| **Shared Working Memory** | the state that crosses layer boundaries (artefacts, plan, file edits, test results) | layer outputs $\to$ next layer's inputs | be reconstructed at each boundary. Continuity is what makes the stack a single agent and not a chain of separate agents. |
| **Per-Layer Bound** *(V9)* | the hard cap on each layer's loop independently | layer iteration count $\to$ CONTINUE / EXIT-LAYER | be shared across layers — one global cap is anti-pattern A3 in multiples; per-layer bounds are the discipline. |
| **Trajectory Log** *(V14)* | the per-layer event record (entries, exits, attempts, transitions) | layer events $\to$ durable log | be optional. Without it, debugging a multi-layer scaffold is intractable; the layer that misbehaved cannot be found. |

The scaffold is a single agent — one identity, one context, one user-facing presence. What varies inside it is the control regime per phase. The Transition Signal column is where the pattern earns its keep: every boundary must have a named, testable rule, or the stack is not O16, it is a pile.

## Collaborations

The agent receives the task. Layer 1's primitive begins — typically ReAct, exploring the environment (reading files, listing directories, running queries) under its own V9 cap on steps. The Transition Signal for Layer 1 $\to$ Layer 2 is checked on each step's exit (a predicate, a judge call, or an event such as "enough context gathered"). When it fires, Layer 1 exits and Layer 2 begins on the accumulated Shared Working Memory.

Layer 2 — typically plan-execute — produces a structured plan and walks it. The Transition Signal for Layer 2 $\to$ Layer 3 may be "plan ready" (after the plan emits) or step-by-step ("for each plan step, enter Layer 3"). Layer 3's generate-test-repair loop generates code, runs tests, and repairs failures under its own V9 cap on iterations. If Layer 3 exhausts its cap, Layer 4 (the outer retry wrapper) may re-enter Layer 2 with a revised plan, or Layer 1 with broadened context, under *its* own cap.

The Trajectory Log records every entry, exit, and transition. V9 bounds at each layer guarantee that the stack always terminates, even if one transition signal misfires. The final result is the artefact left in Shared Working Memory when the last layer exits — typically a passing patch, a written document, or a solved task.

## Consequences

**Benefits**
- Matches control flow to phase: exploration uses an exploratory loop; planning uses a structured loop; implementation uses a test-driven loop. No phase pays the wrong loop's overhead.
- Empirically dominant in production coding agents — the scaffold taxonomy found 11/13 are O16-shaped.
- The stack is a maintenance object: layers can be added, replaced, or tuned independently; transitions are named contracts.
- The agent stays *one* agent — single context, single trajectory, single identity to the user — even with three or four control regimes inside.

**Costs**
- Engineering complexity: every layer is a loop with its own state, prompt, model choice, and bound.
- Transition design is real work — wrong transitions mean Layer N fires when the agent should still be in Layer N-1, and quality degrades silently.
- Token cost compounds across layers — a deep stack with shallow layers is often cheaper than a shallow stack with deep ones, but neither is free. The accumulation is mechanical. Because all layers run within one agent (one context window), the KV cache grows with every layer transition: Layer 3 sees the observations from Layers 1 and 2 in its context (mechanism 3). This is why "a deep stack with shallow layers is often cheaper" — shallow layers produce compact working memory that does not dominate Layer 3's context. The Agentless finding (deliberately shallow three-phase stack outperforming deeper agents on SWE-bench) is explained by this: fewer accumulated tokens from earlier layers means Layer 3's attention is not diluted by early-phase scratchpad content. (Mechanisms 2, 3.)
- Harder to test than a single primitive: each layer needs unit-level testing *and* integration tests across transitions.

**Risks and failure modes**
- *Layer bleed* — Layer 2's loop continues to run inside Layer 3 because the transition signal was incomplete; the agent plans while it should be implementing.
- *Stack inflation* — adding layers without measurable benefit. Every extra layer is failure surface; agents with five primitives are not five times better than agents with three.
- *Bound product explosion* — per-layer caps multiply: a ReAct cap of 20 $\times$ plan-execute cap of 10 $\times$ generate-test-repair cap of 5 $\times$ retry cap of 3 = 3,000 worst-case LLM calls. Set per-layer caps as if the others may saturate. The worst-case call count reflects a compounded context growth as well as a compounded call count. At maximum depth across all layers, the context window may be close to full when the last layer fires. Plan layer bounds so that the combined context fits within 70% of the window, leaving room for the final layer's generation. (Mechanisms 2, 3.)
- *Transition oscillation* — Layers 2 and 3 ping-pong because the transition predicates are not monotone (a plan-step "completes" $\to$ Layer 3 $\to$ produces an observation that "re-opens" the plan $\to$ Layer 2 $\to$ …). Transitions must be monotone or have a higher-level damping rule.
- *A3 in multiples* — V9 missing on any one layer makes the entire stack a runaway candidate; per-layer bounds are non-negotiable.
- *Hidden god-prompt* — packing all four layers' instructions into one mega-prompt instead of giving each layer its own session setup; the stack reverts to a single confused loop.

## Implementation Notes

- **Name the phases before naming the primitives.** The right starting question is *"what distinct phases does this task have?"*, not *"which primitives should we use?"*. The phases come first; the primitives follow.
- **Each layer is its own configured session.** Different setup, different model where useful, different output contract. The ReAct layer's session is not the plan-execute layer's session, even when the same base model serves both. Each session's stable setup (role, output contract, constraints) is a candidate for prefix caching (mechanism 5). A Layer 1 ReAct session that starts with the same system prompt on every task pays prefill once per cache TTL on that prefix, then pays only the variable portion. Since the ReAct layer typically runs many more steps than other layers, this caching benefit compounds. Design each layer's system prompt with a stable prefix and variable suffix to maximize cache hit rate. (Mechanism 5.)
- **Bound each layer independently.** A single global wall-clock cap is not enough; each loop's iteration count must be capped at its own scale. ReAct $\to$ max steps; plan-execute $\to$ max plan size; generate-test-repair $\to$ max repair iterations; retry $\to$ max attempts.
- **Make every transition signal a one-line predicate or a named judge call.** If you cannot write the transition in one expression, the transition is not clear enough yet. Document them at the top of the scaffold.
- **Log per-layer.** V14 Trajectory Logging must record layer entries, exits, transitions taken, and final state per layer — not just per LLM call. Otherwise debugging *which layer misbehaved* is intractable.
- **Prefer shallower stacks where they suffice.** The Agentless variant (three sequential phases, no ReAct) outperformed many full-stack agents on SWE-bench. More layers $\neq$ better.
- **Verify the simpler baseline first.** Before O16, try the single-primitive agent. If R4 alone passes the evaluation, O16 is gold-plating; if it fails in specific phases, that failure is the evidence that justifies the layer you add.
- **Pair with O17 Agent Isolation for heavy sub-tasks.** Within a layer, expensive sub-work (web research, long-running code analysis) can be delegated to a sub-agent with a fresh context, without breaking the single-agent shape of the parent.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** O16 layers multiple primitives drawn from the Reasoning category — **R4 ReAct** for exploration, **R3 Plan-and-Solve** for decomposition, generate-test-repair as a code-driven primitive, multi-attempt retry as a wrapper, optionally **R10 LATS** for hard branching decisions — inside a single agent scaffold. Mandatory companions: **V9 Bounded Execution** at every layer, **V14 Trajectory Logging** across the stack. Often pairs with **O17 Agent Isolation** for sub-tasks. Each layer's session is Signal-layer work — role (**S3**), constraints (**S5**), output contract (**S6**).

**The chain (canonical four-layer coding-agent stack):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Layer 1 — ReAct exploration: read code, list files, run queries until "enough context" | `LLM` (looped) | R4 session; V9 cap on steps |
| 2 | Transition T1: judge / predicate — exploration complete? | `LLM` (or rule) | V15-style judge or rule |
| 3 | Layer 2 — Plan-execute: emit plan, then iterate plan steps | `LLM` (looped) | R3 session; V9 cap on plan size |
| 4 | Transition T2: per plan step — enter Layer 3 | `code` | — |
| 5 | Layer 3 — Generate-test-repair: produce code, run tests, repair failures | `LLM` (looped) + `code` (test runner) | Repair session; V9 cap on iterations |
| 6 | Transition T3: tests pass $\to$ advance plan step; cap hit $\to$ escalate to Layer 4 | `code` | — |
| 7 | Layer 4 — Retry: revise plan or broaden exploration, re-enter Layer 2 or Layer 1 | `code` (+ `LLM` for plan revision) | V9 cap on attempts |
| 8 | Trajectory log per layer entry, exit, transition | `code` | V14 |
| 9 | Return final state when terminal transition fires or all bounds exhaust | `code` | — |

**Skeleton** — the wiring only; each `# LLM` line is a configured session (specified below):

```
hybrid_agent(task):
    state = init_state(task)                          # code
    log   = []                                        # code  — V14

    for retry in 1..max_retries:                      # code  — V9 (Layer 4 cap)

        # Layer 1 — ReAct exploration
        for step in 1..max_react_steps:               # code  — V9 (Layer 1 cap)
            obs   = ReActAgent(state) ─────────────── # LLM
            state = state.apply(obs)
            log_layer_event(log, 1, obs)              # V14
            if T1_done(state): break                  # transition T1

        # Layer 2 — Plan-execute
        plan = Planner(state) ───────────────────────  # LLM
        log_layer_event(log, 2, plan)                  # V14

        for plan_step in plan[:max_plan_steps]:        # V9 (Layer 2 cap)

            # Layer 3 — Generate-test-repair
            for it in 1..max_repair_iters:            # V9 (Layer 3 cap)
                edit    = RepairAgent(plan_step, state) # LLM
                state   = state.apply(edit)
                results = run_tests(state)             # code
                log_layer_event(log, 3, results)       # V14
                if results.passed: break               # transition T3 (success)
            else:
                break  # bound hit → escalate to Layer 4 retry

        if all_plan_steps_passed(state):
            return state

        # else: outer retry — revise plan / broaden exploration

    return best_state(log)                             # code (after V9 retry exhaust)
```

**The LLM sessions.** Each layer's primitive uses its own configured session. Same base model is often fine; setups differ.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **ReAct Explorer** (Layer 1) | strong generalist with tool use | role (S3) — *"you explore the environment to understand the task"*; available tools and ReAct format (Thought / Action / Observation); termination criterion ("when you have enough context to plan, stop") | task brief + observations so far |
| **Planner** (Layer 2) | strong generalist | role — *"you produce an executable plan as an ordered list of steps"*; plan schema (S6); rule that each plan step is independently testable; constraints (S5) | task brief + Layer 1 findings |
| **Repair Agent** (Layer 3) | strong generalist *or* code-specialist model | role — *"you implement one plan step against a failing test, then revise on observed failure"*; edit format (S6); rule for when to admit the step needs replanning rather than further repair | plan step + current code + test output |
| **Transition Judge** (T1, optionally T2/T3) | small fast generalist | role — *"you decide whether the agent has gathered enough context to plan"*; rubric for *enough context* (files identified, error reproduced, relevant region located); output contract (ADVANCE / STAY + reason) | the recent observations |
| **Plan Reviser** (Layer 4) | strong generalist | role — *"you revise a failed plan given which steps failed and why"*; rule to preserve passing prefix and rewrite from the first failure | original plan + failure trace |

**Specialist-model note.** No single specialist is mandatory; the pattern works with a capable generalist across all layers. But two structural choices matter:

- **Code-specialist for Layer 3 (Repair).** Where the implementation phase dominates (coding agents), a code-tuned model materially outperforms a generalist at the repair loop. Treat that as a build dependency.
- **Tools, not model size, decide Layer 1.** ReAct exploration's quality is dominated by the available tool set (file read, ripgrep, test runner, language server) far more than by the model. Agent-Computer Interface design (SWE-agent's ACI) is the lever, not just the LLM.

## Open-Source Implementations

- **SWE-agent** — [`github.com/SWE-agent/SWE-agent`](https://github.com/SWE-agent/SWE-agent) — academic coding agent (Princeton / Stanford) with an Agent-Computer Interface and a scaffold that explicitly stacks ReAct over a structured action language. NeurIPS 2024. The reference implementation of the explore-plan-implement stack.
- **OpenHands** (formerly OpenDevin) — [`github.com/All-Hands-AI/OpenHands`](https://github.com/All-Hands-AI/OpenHands) — open platform for software-development agents built on the CodeAct paradigm; event-driven execution loop layered with planning and test-fix sub-loops; the leading open-source production-style coding agent.
- **Aider** — [`github.com/Aider-AI/aider`](https://github.com/Aider-AI/aider) — terminal-based AI pair programmer; lints and runs tests on each change, with a repair loop on failures; a lighter ReAct + generate-test-repair variant (no explicit plan layer).
- **Agentless** — [`github.com/OpenAutoCoder/Agentless`](https://github.com/OpenAutoCoder/Agentless) — a deliberately *shallower* O16 stack: localization $\to$ repair $\to$ patch validation, with no ReAct exploration layer. Demonstrates the "shallow O16 beats deep O16" finding on SWE-bench Lite (Xia et al., 2024).
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — general-purpose cyclic graph runtime that hosts O16 stacks as composable subgraphs (a ReAct subgraph, a plan-execute subgraph, a test-fix subgraph, wired through transition edges). The closest general-purpose host.

## Known Uses

- **SWE-agent / SWE-agent 2.0** — academic SOTA on SWE-bench when released; the canonical published example of stacking ReAct + plan-execute + repair under an Agent-Computer Interface.
- **OpenHands** production deployments — the leading open-source coding agent at scale; CodeAct paradigm with layered planning and test-driven repair loops.
- **Devin (Cognition AI)** — proprietary autonomous software engineer; widely described as a stacked-primitive scaffold (plan $\to$ execute with tool use $\to$ test $\to$ revise).
- **Claude Code, Cursor agent mode, Aider** — production coding tools whose internal loops, where visible, exhibit the O16 stack: a ReAct-style outer loop, an inline planning step on harder tasks, an inner test-fix loop.
- **Agentless** — open implementation showing that a *three-phase plan-execute stack with no ReAct* achieves SWE-bench Lite SOTA at low cost (32% at about 0.70 USD per task as published); evidence that the right O16 stack is task-specific, not maximally layered.

## Related Patterns

- **Uses** R4 ReAct, R3 Plan-and-Solve, R10 LATS — these are the loop primitives O16 stacks. None are pattern-rivals; they are O16's building blocks.
- **Distinct from** O8 Loop Agent — O8 is a *fixed cycle of distinct agents*, repeating; O16 is *one agent* whose internal control flow stacks distinct primitives. O8's unit of composition is the agent; O16's is the loop primitive.
- **Distinct from** O6 Orchestrator-Workers — O6 dynamically delegates to other agents per task; O16's stack is fixed at build time and the same agent stays "in role" across all layers.
- **Distinct from** O2 Prompt Chaining — O2 is a single linear pass through fixed steps; O16's layers are *loops* with their own exit conditions and transitions, not steps.
- **Composes with** O17 Agent Isolation — within a layer, expensive sub-work can be delegated to a sub-agent with a fresh context. O17 is the standard pairing for heavy Layer 1 or Layer 3 sub-tasks.
- **Composes with** O4 Parallelization — independent sub-tasks inside a layer (e.g. running tests in parallel) use O4 without changing the stack shape.
- **Required by** V9 Bounded Execution — every layer must be bounded; an unbounded layer makes the stack anti-pattern A3 in multiples.
- **Pairs with** V14 Trajectory Logging — per-layer events must be durable, or debugging the stack is intractable.
- **Pairs with** V15 LLM-as-Judge — the transition signals between layers are typically V15 calls ("is exploration complete?", "is the plan ready?").
- **Note on fundamentality** — O16 names a composition, but the *composition discipline* (named transitions, per-layer bounds, fixed stack at build time) is what earns the pattern number. Without that discipline, "use multiple primitives" is not a pattern, it is permission. The empirical case — 11/13 production coding agents are O16-shaped — anchors the pattern as real architecture, not editorial.

## Sources

- Rombaut, B. (2026) — *Inside the Scaffold: A Source-Code Taxonomy of Coding Agent Architectures*. arXiv 2604.03515. The primary empirical source: 13 open-source coding agents analysed at pinned commit hashes; 11 of 13 stack multiple loop primitives; five primitives identified (ReAct, generate-test-repair, plan-execute, multi-attempt retry, tree search).
- Yang, J., Jimenez, C. E., Wettig, A., Lieret, K., Yao, S., Narasimhan, K., Press, O. (2024) — *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*. NeurIPS 2024. The reference stacked-primitive coding agent.
- Xia, C. S., Deng, Y., Dunn, S., Zhang, L. (2024) — *Agentless: Demystifying LLM-based Software Engineering Agents*. arXiv 2407.01489. Evidence that a deliberately shallower three-phase stack beats deeper agents on SWE-bench Lite at lower cost.
- Anthropic (2024) — *Building Effective Agents*. Foundational catalog of agentic primitives and composition.
- 12-Factor Agents — Factor 10 (Small, Focused Agents) — discipline that informs the per-layer bounding and single-agent shape of O16.
