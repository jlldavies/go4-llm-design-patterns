# O8 — Loop Agent

> Run a fixed pipeline of distinct, role-specialised agents as one cycle, then repeat the whole cycle until a termination condition fires.

**Also Known As:** Agentic Loop, Iterative Multi-Agent Pipeline, Cyclic Workflow, Generate-Critique-Evolve Loop.

**Classification:** Category IV — Orchestration · Band IV-B Agentic · a *control* pattern — it composes a multi-agent pipeline (O2 / O4 / O5 inside) and wraps it in a cycle with a termination judge.

---

## Intent

Improve a single carried state across rounds by running the same sequence of distinct agents — each with its own role, prompt, and output contract — on the state, until a termination judge says the state is good enough or a hard bound trips.

## Motivation

Some problems are not solved in one pass and are not solved by one agent. They are solved by a *team* of role-specialised agents that take turns on the same artefact, round after round: a generator proposes, a critic finds faults, a ranker prioritises, an evolver refines, and the loop runs again on the refined output. Each round produces a better state than the last; convergence — not a single brilliant call — is what produces the answer.

The obvious alternatives fail in specific ways. **R4 ReAct** is a loop, but it is a *single* agent looping over its own Thought / Action / Observation — one session, one role; it cannot host distinct critique or evolution roles without role-bleed and lost context. **O2 Prompt Chaining** runs a sequence of distinct agents but only *once* — no cycle, no convergence. **O5 Evaluator-Optimizer** is a cycle, but a specific two-role cycle (generator + judge); it cannot accommodate a three- or four-role pipeline like *generate $\to$ debate $\to$ rank $\to$ evolve*. **O6 Orchestrator-Workers** delegates dynamically from a central orchestrator — workers are picked per-task, not run as a fixed cycle.

O8 is the pattern when the loop body is *itself a multi-agent pipeline*. The pipeline shape is fixed (each round runs the same agents in the same order); the *cycle count* is what varies, governed by a termination judge and a hard bound. The defining example — Google's AI co-scientist — runs Generation $\to$ Reflection $\to$ Ranking $\to$ Evolution $\to$ Meta-review, and repeats the whole cycle, with an Elo tournament deciding when hypotheses have stabilised. The cycle is the unit of work; one pass through it is one round of improvement.

## Applicability

Use Loop Agent when:

- the task improves measurably with repeated passes by the same multi-agent pipeline (generate $\to$ critique $\to$ revise; search $\to$ synthesise $\to$ evaluate $\to$ refine);
- distinct roles must do distinct work each round — a single ReAct loop would conflate them;
- termination has a definable signal (criterion met, stagnation detected, budget exhausted), not "the model decides it's done";
- the cycle's state object (draft, hypothesis set, codebase) can be carried and mutated round by round.

Do not use when:

- one agent in one pass suffices — use **O1 Single Agent**;
- the work is sequential but never iterates — use **O2 Prompt Chaining**;
- only two roles are needed (generate + judge) — use **O5 Evaluator-Optimizer**, which is the specialised two-role case;
- the inner loop is within a single agent's reasoning trace — use **R4 ReAct** or **R7 Reflexion**;
- sub-tasks are independent and need not cycle together — use **O4 Parallelization**;
- delegation is dynamic and worker selection changes per task — use **O6 Orchestrator-Workers**;
- the loop cannot be bounded — without **V9 Bounded Execution**, this becomes anti-pattern **A3 Uncontrolled Recursion**.

## Decision Criteria

O8 is right when the unit of work is a *cycle of distinct agents*, the cycle measurably improves a carried state, and termination is principled.

**1. Count the roles inside one round.** If one role does all the work, this is **R4** or **O1** with retries. If two roles (generator + judge), use **O5**. If three or more distinct roles each do distinct work each round (e.g. *generate $\to$ critique $\to$ rank $\to$ evolve*), O8 is the right shape.

**2. Measure round-over-round improvement.** On a held-out test of representative tasks, plot the quality metric per round. If round N+1 is reliably better than round N for at least 3–5 rounds before plateauing, the cycle is doing real work. If round 2 is already at the asymptote, you do not need a loop — one pass suffices.

**3. Define the termination judge.** Name the signal that ends the loop: a quality threshold passed (e.g. Elo > X, judge says PASS), a stagnation detector (improvement < ε for K rounds), or an external success criterion (tests pass, target found). A loop with no judge — only a max-iteration cap — is fragile; the judge is the pattern's brain.

**4. Cost the cycle.** One round = sum of the per-agent costs in the pipeline. Multiply by expected rounds (often 5–20). If the expected total exceeds the budget for a single high-end model call, O8 must clearly beat that alternative on quality; otherwise prefer **R10 LATS** or **R9 Tree of Thoughts** as the more search-efficient option for hard problems.

**5. Bound it.** Pair with **V9 Bounded Execution** — a hard cap on rounds, total LLM calls, and wall-clock. Without V9 the loop is anti-pattern A3. Also instrument with **V14 Trajectory Logging**: per-round artefacts and judge verdicts are what make convergence visible.

**Quick test — O8 is the right pattern when:**

- the loop body needs 3+ distinct agent roles, *and*
- the carried state measurably improves over multiple rounds before plateauing, *and*
- a definable termination judge exists (threshold, stagnation, success criterion), *and*
- V9 Bounded Execution and V14 Trajectory Logging are in place from the start.

If the loop body is one role, choose **R4** or **R7**. If two roles, choose **O5**. If the pipeline runs once and stops, choose **O2**. If delegation is dynamic per task, choose **O6**. If the goal is to search a solution space rather than refine a single carried state, choose **R9** or **R10**.

## Structure

```
              ┌─────────────────────────────────────────────────────┐
              │                  one cycle (round)                  │
              │                                                     │
   State_n ─▶ │  Agent A ─▶ Agent B ─▶ Agent C ─▶ ... ─▶ Agent K   │ ─▶ State_{n+1}
              │  (e.g. Generate)  (Critique)   (Rank)    (Evolve)  │
              └─────────────────────────────────────────────────────┘
                                       │
                                       ▼
                              ┌──────────────────┐
                              │ Termination judge│
                              │  threshold? /    │
                              │  stagnation? /   │
                              │  bound hit?      │
                              └────────┬─────────┘
                                       │
                          ┌────────────┴────────────┐
                          │ no                       │ yes
                          ▼                          ▼
                   loop back with State_{n+1}      return State_final
                                       ▲
                                       │
                            V9 Bounded Execution caps
                            rounds, calls, wall-clock
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Cycle Pipeline** *(fixed sequence of distinct agents A $\to$ B $\to$ ... $\to$ K)* | the per-round transformation of the carried state | State_n $\to$ State_{n+1} | change agents or order between rounds — that turns O8 into dynamic delegation (O6), and convergence stops being measurable. |
| **Each Cycle Agent** | one role's work for the round (generate, critique, rank, evolve, etc.) | upstream output for this round $\to$ its contribution to State_{n+1} | re-do another agent's job. Role bleed (the Critic also generating, the Evolver also ranking) is O8's most common failure mode. |
| **Carried State** | the artefact under improvement (draft, hypothesis set, candidate ranking, code) | round outputs $\to$ updated artefact | be reconstructed from scratch each round — continuity is what makes the loop work. |
| **Termination Judge** | the verdict that ends the loop | State_n, history of states $\to$ CONTINUE / STOP | be the same session as any Cycle Agent. A judge that also generates has no incentive to ever STOP. |
| **Round Bound** *(V9)* | the hard cap that guarantees termination | round count, total calls, wall-clock $\to$ CONTINUE / ABORT | be replaced by "the judge will catch it" — the judge can fail; the bound must not. |
| **Trajectory Log** *(V14)* | the per-round record of states, agent outputs, and judge verdicts | round events $\to$ durable log | be optional. Without it, convergence is invisible and debugging is impossible. |

The Cycle Pipeline is fixed at design time; the Termination Judge runs *outside* it; the Round Bound is non-negotiable. Each Cycle Agent is its own configured session — separate setup, separate prompt, separate model where useful.

## Collaborations

A task arrives carrying initial State_0 (often empty, a brief, or a seed artefact). Round 1 begins: Agent A reads State_0 and emits its contribution; Agent B reads A's output and the relevant slice of State_0 and emits its own; Agents C through K continue in fixed order. The round closes with State_1 = the integrated outputs of all agents this round. The Termination Judge inspects State_1 against the threshold or stagnation criterion: if the verdict is STOP, State_1 is returned; if CONTINUE, the Round Bound checks rounds-so-far, total-calls, and wall-clock — if any cap is breached the loop ABORTS (returning the best state seen); otherwise round 2 begins on State_1. Every round's agent outputs and the judge verdict are appended to the Trajectory Log. The loop terminates when either the judge says STOP or the bound says ABORT — never on the agents' own initiative.

## Consequences

**Benefits**
- Hosts a multi-agent pipeline (3+ distinct roles) inside a loop without conflating roles — each agent stays a focused session.
- Convergence is measurable: per-round states and judge verdicts produce a quality curve, not a single opaque result.
- Bounded termination is guaranteed when V9 is wired in, eliminating the A3 runaway-loop risk.
- The cycle is the *unit of improvement* — adding a new role means adding an agent to the pipeline, not redesigning the loop.

**Costs**
- LLM calls scale as (agents per cycle $\times$ rounds). A 4-agent pipeline running 10 rounds is 40 calls before the judge fires.
- Latency scales with rounds; parallelism across agents within a round (O4 inside O8) only partially offsets this.
- State management is real engineering — what carries forward, what is regenerated each round, what is logged.
- The Termination Judge is a single point of failure for cycle hygiene; a weak judge lets the loop run too long or stop too early.

**Risks and failure modes**
- *Uncontrolled recursion (A3)* — V9 not wired, or the judge never returns STOP and no bound trips.
- *Role bleed* — Critic starts generating, Evolver starts ranking; per-round outputs lose their crispness and convergence stalls.
- *Pipeline rot* — changing the agent set or order between rounds (drifts toward O6); the loop stops being a cycle.
- *Stagnation undetected* — judge does not include a stagnation rule, so a plateaued state cycles until the round cap; cost burned, quality unchanged.
- *State explosion* — carrying full per-round histories into the next round consumes the context window; pair with **K6 Context Compression** or **K7 Pruning** on the carried state if rounds are many.
- *Judge-Generator drift* — the judge is gradually trained-against by repeated cycles; combine with **V15 LLM-as-Judge** discipline (separate model where possible, rubric versioned, calibrated on held-out items).

## Implementation Notes

- Fix the agent set and order at design time; resist the temptation to "let the loop decide which agent runs next" — that move is O6, and you lose the convergence guarantees of a fixed cycle.
- Each Cycle Agent gets its own session setup: role, criteria, output contract. Different model per agent is fine and often optimal (small fast model for ranking, strong model for generation).
- The Termination Judge belongs in a *separate* session from any Cycle Agent. The same model is acceptable; the prompt and role must be distinct. The mechanical reason to prefer a different model: agents sharing the same weight matrices share the same learned attention geometry (mechanism 1). If the Termination Judge uses the same W_Q and W_K as the Generator, the inner product Q_α K^α that evaluates "is this done?" is shaped by the same biases that shaped the Generator's output. A different model has genuinely different projection matrices and therefore different evaluation geometry. (Mechanism 1.)
- Include a stagnation rule in the judge: if the quality metric improves by less than ε for K consecutive rounds, STOP — regardless of threshold. This catches the "plateau under the bar" case.
- Carry forward only what the next round needs. The full per-round history goes to V14 Trajectory Logging, not into the next round's context. Apply **K6 / K7** to the carried state if it grows. This is mechanical necessity, not just good hygiene. The KV cache grows as [layers $\times$ seq_len $\times$ kv_heads $\times$ d_head] (mechanism 3). If per-round states accumulate in the carried context, by round 10 the context has grown 10-fold; the n² attention cost (mechanism 2) means generation latency and compute scale quadratically with rounds, not linearly. The practical consequence is that a loop agent carrying full history becomes progressively slower and more expensive per round. The design target should be: carried state is O(1) in size relative to round count, with per-round artefacts offloaded to V14. (Mechanisms 2, 3.)
- Where rounds run a pipeline whose agents are independent within a round, use **O4 Parallelization** for that round — but the cycle as a whole is still serial.
- Start with rounds capped at 5–10 and measure the quality curve. Many loops in production converge well before the cap; the cap is a safety net, not a target.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** O8 wires a *fixed pipeline* of distinct agents (drawing on **O2** for the per-round sequencing, optionally **O4** for parallel agents within a round, sometimes **O5** as a two-role pipeline-special-case), wraps it in a cycle, and adds a Termination Judge (drawing on **V15 LLM-as-Judge**). Mandatory companions: **V9 Bounded Execution**, **V14 Trajectory Logging**. The setup of each agent session is Signal-layer work — role (**S3**), constraints (**S5**), an output contract (**S6**).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Initialise State_0 from the task brief | `code` | |
| 2 | Round agent A — produce A's contribution for this round | `LLM` | Agent-A session |
| 3 | Round agent B — produce B's contribution | `LLM` | Agent-B session |
| 4 | ... agents C..K, in fixed order | `LLM` | per-agent sessions; O4 if parallel within a round |
| 5 | Integrate this round's outputs into State_{n+1} | `code` | |
| 6 | Append round artefacts to trajectory log | `code` | V14 |
| 7 | Termination judge — STOP / CONTINUE | `LLM` | Judge session, V15 |
| 8 | Bound check — rounds, calls, wall-clock | `code` | V9 |
| 9 | If CONTINUE and within bounds, loop to 2; else return final state | `code` | |

**Skeleton** — the wiring only; each `# LLM` line is a configured session:

```
loop_agent(task):
    state = init_state(task)                        # code
    history = []                                    # code  — V14
    for round in 1..max_rounds:                     # code  — V9 bound
        out_A = AgentA(state) ─────────────         # LLM
        out_B = AgentB(state, out_A) ──────         # LLM
        out_C = AgentC(state, out_A, out_B) ─       # LLM
        out_K = AgentK(state, out_A..out_C) ─       # LLM
        state = integrate(state, out_A..out_K)      # code
        history.append(round_record(state, ...))    # code  — V14
        verdict = TerminationJudge(state, history)  # LLM   — V15
        if verdict == STOP: return state
        if bound_exceeded(): return best(history)   # code  — V9
    return best(history)                            # code
```

**The LLM sessions.** Each `LLM` step is *set up* before its first call. The setup is established once per session; the per-call prompt then wraps only the data that changes.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent A** *(e.g. Generator)* | strong generalist | role (S3) — *"you produce candidate {hypotheses / drafts / fixes}"*; constraints (S5); output contract (S6) | current state + round number |
| **Agent B** *(e.g. Critic / Reflector)* | strong generalist | role — *"you critique {A's output} against {rubric}"*; rubric; output contract (structured findings) | state + A's output |
| **Agent C** *(e.g. Ranker)* | small fast generalist *or* fine-tuned ranker (specialist) | role — *"you score and order candidates by {criteria}"*; output contract (ordered list with scores) | state + A's and B's outputs |
| **Agent K** *(e.g. Evolver / Refiner)* | strong generalist | role — *"you produce an improved version drawing on {prior round's critique and ranking}"*; output contract | state + this round's prior outputs |
| **Termination Judge** | small fast generalist; ideally a *different* model from the agents (V15 hygiene) | role — *"you decide whether the loop should STOP"*; the threshold rule, the stagnation rule (Δ < ε for K rounds), output contract (STOP / CONTINUE + reason) | current state + the last K rounds' summaries |

**Specialist-model note.** No single specialist is mandatory, but two structural choices materially change quality:

- **Ranker as specialist.** Where a Cycle Agent is a ranker / scorer / classifier, a small fine-tuned model often outperforms a generalist at a fraction of the cost. Treat that as a build dependency, not a drop-in prompt.
- **Judge as a different model from the agents.** Using the same model for the Termination Judge as for the Generator opens a known **V15** drift mode (the model becomes lenient on its own outputs over rounds). A different provider or a smaller specialised judge model reduces that drift.

## Open-Source Implementations

- **Google ADK — `LoopAgent`** — [`github.com/google/adk-python`](https://github.com/google/adk-python) — code-first Python ADK with a first-class `LoopAgent` workflow primitive that runs sub-agents in a cycle until a termination signal; sub-agents end the loop by raising a custom event or setting a shared-context flag. Documented at [adk-docs](https://google.github.io/adk-docs/agents/workflow-agents/loop-agents/).
- **Google ADK Samples** — [`github.com/google/adk-samples`](https://github.com/google/adk-samples) — reference loop-agent implementations (writer + critic refinement, iterative research) showing the cycle pattern in practice.
- **Open Co-Scientist (Jataware)** — [`github.com/jataware/open-coscientist`](https://github.com/jataware/open-coscientist) — open-source adaptation of Google's AI co-scientist; generates, reviews, ranks, and evolves research hypotheses through the canonical generate-debate-evolve loop.
- **Open Co-Scientist (LLNL)** — [`github.com/llnl/open-ai-co-scientist`](https://github.com/llnl/open-ai-co-scientist) — Lawrence Livermore National Laboratory's open implementation of the same generate-review-rank-evolve cycle.
- **AI-CoScientist (Swarms Framework)** — [`github.com/The-Swarm-Corporation/AI-CoScientist`](https://github.com/The-Swarm-Corporation/AI-CoScientist) — minimal, reliable implementation of the *Towards an AI Co-Scientist* paper using the Swarms multi-agent framework; tournament-based hypothesis evolution.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — cyclic graph runtime; loop bodies of distinct nodes are first-class, with recursion limits and explicit termination conditions; the closest general-purpose host for O8.

## Known Uses

- **Google DeepMind AI Co-Scientist** — Gemini-2.0 multi-agent system that cycles *Generation $\to$ Reflection $\to$ Ranking $\to$ Evolution $\to$ Meta-review* with Elo-tournament termination; the canonical production example of O8.
- **Google ADK production agents** — Vertex AI / Gemini Enterprise deployments using ADK's `LoopAgent` primitive for iterative refinement (writer-critic, test-fix, search-synthesise-evaluate).
- **Coding agents with test-fix loops** — Devin, Cursor's agent mode, Claude Code agents: pipelines of *plan $\to$ implement $\to$ test $\to$ diagnose $\to$ revise* iterating until tests pass; the loop body is multi-agent in practice even when packaged as one product.
- **Research / hypothesis-generation pipelines** — biomedical and materials-science labs using the co-scientist architecture (or open clones above) to iterate on candidate hypotheses with peer-review and evolution stages.

## Related Patterns

- **Refines** O2 Prompt Chaining — O2 is a single pass; O8 is O2 wrapped in a cycle with a termination judge.
- **Distinct from** R4 ReAct — R4 is a *single* agent looping over Thought / Action / Observation; O8 is a *pipeline of distinct agents* looping. Different unit of work.
- **Distinct from** R7 Reflexion — R7 keeps verbal self-critique across attempts within a single agent's lifetime; O8 cycles a multi-agent pipeline. R7 can live *inside* an O8 round as one agent's mechanism.
- **Specialised case of** O5 Evaluator-Optimizer — O5 is the two-role (generator + judge) instance of O8. When the loop body grows beyond two roles, O5 generalises to O8.
- **Distinct from** O6 Orchestrator-Workers — O6 has a central orchestrator picking workers dynamically per task; O8 runs the same agents in the same order every round. If the agent set or order changes round-to-round, you are doing O6, not O8.
- **Composes with** O4 Parallelization — within a single round, independent agents can run in parallel; the cycle as a whole stays serial.
- **Composes with** O9 Multi-Agent Reflection — O9 can serve as the *critique stage* inside an O8 round (multiple critic agents in parallel instead of one).
- **Required by** V9 Bounded Execution — O8 without a hard bound is anti-pattern A3 Uncontrolled Recursion. Non-negotiable.
- **Pairs with** V14 Trajectory Logging — per-round artefacts and judge verdicts must be durable, or convergence is invisible.
- **Pairs with** V15 LLM-as-Judge — the Termination Judge is V15 applied to "is the loop done?".
- **Pairs with** K6 / K7 — the carried state often needs compression or pruning between rounds when rounds are many.

## Sources

- Google Research / DeepMind (2025) — *Towards an AI Co-Scientist*, Nature; multi-agent Gemini architecture with Generation, Reflection, Ranking, Evolution, and Meta-review agents iterating in a cycle.
- Google Agent Development Kit (ADK) documentation — *Loop workflow* (workflow-agents / loop-agents); the LoopAgent primitive and termination semantics.
- AWS Prescriptive Guidance — multi-agent loop pattern in agentic workflows.
- Spring AI — *Agentic Patterns* blog; iterative loop primitive.
- arXiv 2604.03515 — *Inside the Scaffold*; "multi-attempt retry" as one of five loop primitives observed in production coding agents.
- Du et al. (2023) — *Improving Factuality and Reasoning in Language Models through Multiagent Debate*; precursor work on multi-agent iterative refinement.
