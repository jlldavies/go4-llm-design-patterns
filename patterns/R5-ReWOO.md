# R5 — ReWOO

> Plan every tool call upfront in a single LLM pass, execute the plan without any LLM in the loop, then synthesise the answer from the collected evidence — trading mid-run adaptability for ~5× token efficiency.

**Also Known As:** Reasoning Without Observation, Decoupled Reasoning, Plan-Execute-Solve, Foreseeable Reasoning.

**Classification:** Category III — Reasoning · Band III-B Planned reasoning · the *upfront-plan* counterpart to R4 ReAct's *interleaved* loop; defining boundary is whether tool calls are independent (R5) or each step informs the next (R4).

---

## Intent

Separate reasoning from observation so the model plans all tool invocations once, with placeholders for the results, and never re-enters the loop until every external call has completed and the evidence is ready to synthesise.

## Motivation

R4 ReAct calls the LLM once per Thought-Action-Observation step. For an N-step task, that is N LLM invocations, and every invocation re-ingests the entire growing trace — prompt, prior thoughts, prior observations. Token cost grows quadratically: step k pays for context that includes steps 1..k-1. On multi-hop benchmarks this dominates cost long before the answer is reached.

Xu et al. (2023) observed that a large class of tool-augmented tasks does not need mid-run adaptation. When a question decomposes into independent lookups — "find X, find Y, combine them" — the model can foresee the full plan at step zero. The observations would not have changed what comes next; ReAct's per-step re-planning was paying for adaptability the task never asked for. Each step re-reads the trace — O(n²) attention cost in the transformer (mechanism 2): context of length n at step k means the k-th LLM call pays O(k²) attention, making total cost scale super-linearly in N.

ReWOO removes the loop. A Planner emits the *whole* plan in one LLM call, written as a DAG of tool calls with placeholder variables (`#E1`, `#E2`, …) where later steps reference earlier results without knowing their values. A Worker executes the plan deterministically — no LLM in this phase. The Worker phase is deterministic code execution (mechanism 7): same inputs produce the same tool outputs with no stochastic variance and no LLM calls, so it contributes nothing to the O(n²) attention budget. A Solver makes one final LLM call that reads the original question and the populated evidence and produces the answer. Two LLM calls total, regardless of plan length. Result on the paper's HotpotQA evaluation: 5× token efficiency over ReAct *and* 4% accuracy improvement, because the Planner sees the whole task and chooses tools coherently.

The defining claim of the pattern is asymmetric: when sub-tasks are independent, one expensive plan buys many cheap executions. The bet fails when sub-tasks are *not* independent — when step 2's tool choice depends on what step 1 actually returned. That is R4's territory, and the two patterns are mutually exclusive for the same task (see Related Patterns).

## Applicability

Use ReWOO when:

- the task decomposes into tool calls whose *choice* and *arguments* are knowable upfront — typically independent lookups across multiple sources, multi-hop Q&A with a known hop structure, report generation from enumerated data sources;
- token efficiency or latency-via-parallelism is a material lever;
- the tool calls can run in parallel or with simple variable substitution (one tool's output feeds the next as a value, not as a branching decision);
- the working set of tools is small and stable (no need for the model to *discover* tools mid-run).

Do not use when:

- each tool result might change which tool to call next — use **R4 ReAct** (the canonical alternative);
- the task requires exploration of an open solution space — use **R9 Tree of Thoughts** or **R10 LATS**;
- the task is debugging or iterative refinement where failures need diagnosis — use **R7 Reflexion**;
- the plan would have to be re-emitted often because tool outputs are noisy or partial — the planner cost amortises poorly; fall back to **R4 ReAct**.

## Decision Criteria

R5 is right when the tool-call sequence is foreseeable, tool calls are independent (or have only value-substitution dependencies), and per-task token cost matters.

**1. Dependency analysis.** Sketch the tool call DAG for a representative task. Classify each edge:
- *Value substitution* — step 2's argument is step 1's literal output (a city name, a number, an ID). R5 handles this via `#E1` placeholders.
- *Branching decision* — step 2's tool *choice* depends on the *content* of step 1's output. R5 cannot handle this. If any edge is branching → use **R4 ReAct**.

**2. Measure ReAct's overhead.** On a labelled task set, compute steps per task (N) and average input tokens per step. ReAct's token cost grows ~O(N²) because each step re-reads the trace. If N ≥ 5 and the answer is mostly retrieved facts → R5 saves significant cost. If N ≤ 2, the loop overhead is negligible — stay with R4.

**3. Tool catalogue stability.** R5's Planner must see the full tool catalogue in one prompt. If the catalogue is small (≤ ~15 tools) and stable across tasks → R5. If the catalogue is large and the relevant subset is task-dependent, R5's prompt bloats — prefer **R4 ReAct** with dynamic tool selection.

**4. Failure mode tolerance.** When a tool call inside R5's plan fails or returns unexpected content, the Solver receives partial evidence and must either answer with what it has or trigger a replan. If silent failure on partial evidence is unacceptable, wrap R5 in **V9 Bounded Execution** with a replan trigger, or switch to **R4 ReAct** for those task classes.

**5. Latency profile.** R5's Worker phase is deterministic, so independent calls can run in parallel — see **O4 Parallelization**. Net latency can be lower than R4's serial loop. If parallel execution is impossible (one tool, sequential calls), R5 still wins on tokens but not on wall-clock.

**Quick test — R5 is the right pattern when:**

- every edge in the tool DAG is value-substitution, not branching-decision, *and*
- the working tool catalogue is small and stable, *and*
- the task is large enough (N ≥ 5 hops) for the loop overhead to matter, *and*
- partial-evidence failure is tolerable or handled by an explicit replan gate.

If any edge is a branching decision, use **R4 ReAct** — adaptability is worth the cost. If the solution space itself is unknown, use **R9 Tree of Thoughts** or **R10 LATS**. If the failure mode is "agent should learn from a wrong answer", use **R7 Reflexion**. For deterministic, single-tool workflows, plain **R3 Plan-and-Solve** is simpler than R5.

## Structure

```
                              ┌──── tool catalogue ────┐
                              │                         │
  Question ──▶ Planner (LLM) ─┴──▶  Plan = DAG of steps:
                                    #E1 = ToolA["arg"]
                                    #E2 = ToolB["other arg"]
                                    #E3 = ToolC[#E1, #E2]
                                          │
                                          ▼
                                    Worker (code, no LLM)
                                    ─ resolve #E placeholders
                                    ─ execute steps (parallel where the DAG allows)
                                    ─ collect evidence map { #E1: r1, #E2: r2, #E3: r3 }
                                          │
                                          ▼
                                    Solver (LLM)
                                    ─ reads question + full evidence map
                                    ─ produces final answer
                                          │
                                          ▼
                                       Answer
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Planner (LLM)** | the full plan, emitted in one pass | question + tool catalogue → ordered list of `#En = Tool[args]` steps with placeholder references | hedge with branching ("if X then Y") — branching is R4's job; ReWOO assumes the plan is determined by the question alone. |
| **Plan (artefact)** | the DAG of steps with placeholder variables | — → executable plan | contain free text the Worker cannot parse; a malformed plan kills the whole task because there is no LLM in the loop to recover. |
| **Worker** | deterministic execution of the plan | plan + tools → evidence map `{#En → result}` | call the LLM, judge results, or alter the plan — its only job is substitute, dispatch, collect. |
| **Tool registry** | the bound set of callable tools | tool name + args → tool result | be open-ended at runtime — the Planner saw a fixed catalogue; tools appearing afterwards cannot be in any plan. |
| **Solver (LLM)** | the final synthesis | question + populated evidence map → answer | replan, re-fetch, or critique the plan; if evidence is insufficient, it should say so and let an outer loop (V9, or a replan trigger) decide. |

The strict separation of Planner from Solver — same model, *different sessions, different setups* — is what keeps R5 honest. A Planner that can also see the Solver's job is tempted to leave gaps "for later"; a Solver that can replan is tempted to ignore the plan. Two narrow responsibilities.

## Collaborations

A question arrives. The Planner runs once, with the question and the tool catalogue in its setup; it emits a complete plan as a list of `#En = Tool[args]` lines, with later lines free to reference earlier `#En` as placeholder arguments. The Plan is parsed into a DAG. The Worker walks the DAG: every step whose placeholder dependencies are resolved becomes executable; independent steps can fire in parallel (this is where **O4 Parallelization** composes in). As each tool returns, the Worker writes the result into the evidence map and unblocks downstream steps. When every step has either completed or failed, the Worker hands the question and the evidence map to the Solver. The Solver makes one LLM call to synthesise the final answer. There is no loop back to the Planner inside a single task — if the Solver cannot answer, an outer policy (a replan trigger bounded by V9, or fallback to R4 ReAct) handles recovery.

## Consequences

**Benefits**

- ~5× token efficiency vs R4 ReAct on multi-hop benchmarks; gap widens with N.
- Two LLM calls regardless of plan length — predictable cost and latency.
- Parallel tool execution falls out of the DAG structure for free (composes with O4).
- The plan is a single inspectable artefact — easier to audit, log (V14), and test than a ReAct trace.
- Planner has the full task in view, so tool choices are coherent end-to-end rather than locally greedy.

**Costs**

- Zero mid-execution adaptation; the plan is final once emitted.
- A bad plan is silent — there is no LLM in the loop to notice the plan was wrong.
- Planner prompt must include the tool catalogue and any examples, paid in full on every call.
- Solver sees the entire evidence map, so a verbose tool can blow the Solver's context — pair with **K7 Context Pruning** if tool outputs are bulky.

**Risks and failure modes**

- *Hidden dependency* — Planner assumes a value-substitution edge when reality needs a branching decision; downstream steps run on garbage, Solver invents.
- *Tool-output drift* — tool returns a different schema than the Planner imagined; placeholder substitution still "works" but evidence is wrong.
- *Cascade failure* — one tool failure blocks every downstream step in the DAG; without a replan gate, the Solver receives partial evidence.
- *Stale catalogue* — a tool is added after the Planner's setup was loaded; subsequent plans cannot use it until the catalogue is refreshed.
- *R4/R5 confusion* — applying R5 to a task that needed R4 produces a confident-looking wrong answer (the trace looks clean because there is no loop).

## Implementation Notes

- The Planner needs a strong model (mechanism 8 — plan quality caps the value of the whole pattern; a 70B model writes materially better DAGs than a 7B). Small models hallucinate placeholder syntax or skip steps. The Planner's setup — tool catalogue, examples, placeholder syntax — is stable across calls and is the canonical case for provider prefix caching (mechanism 5). At Anthropic pricing, a cached read costs ~10% of a normal input token; a Planner setup of 2000 tokens cached across 1000 calls saves ~90% of the Planner's input cost. Structure the Planner setup as a stable prefix above the per-call question.
- The Solver can usually be a smaller, cheaper model — it does synthesis, not invention.
- Keep the placeholder syntax narrow and parseable (`#E1`, `#E2`, …). Free-form references break the Worker.
- Validate the plan before executing: every `#En` reference must point to an earlier step; every tool must exist in the catalogue; every argument type must match the tool's schema. Failed validation triggers a single replan, not silent execution of a broken plan.
- Execute independent DAG nodes in parallel (O4) — that is where R5's wall-clock gain lives, not just the token gain.
- Pair with **V9 Bounded Execution** to cap replan attempts; otherwise a hard task replans forever.
- Pair with **V14 Trajectory Logging** to record the plan, the evidence map, and the Solver's answer as three separate artefacts — easier to audit than a ReAct trace.
- If tool outputs are long (web pages, large JSON), pre-process or prune (**K7**) before the Solver sees them.
- For the variant where the plan must adapt: do not patch R5; switch to **R4 ReAct**.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** R5 chains a *Planner* LLM session with a deterministic *Worker* and a *Solver* LLM session. It commonly composes with **O4 Parallelization** (independent DAG nodes run in parallel), **V9 Bounded Execution** (cap replans), **V14 Trajectory Logging** (record the plan), and **K7 Context Pruning** (shrink bulky tool outputs before the Solver). The Planner's setup is itself Signal-layer work — a role (**S3**), constraints (**S5**), and a strict output template (**S6**) for the placeholder syntax.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Planner emits the full plan as `#En = Tool[args]` lines | `LLM` | Planner session, S6 template |
| 2 | Parse plan into a DAG; validate references, tool names, schemas | `code` | |
| 3 | On validation failure: one bounded replan; else escalate | `code` (or LLM) | V9 |
| 4 | Worker walks the DAG; executes independent steps in parallel, substitutes `#En` as values | `code` | O4 |
| 5 | Collect evidence map `{#En → result}`; optionally prune bulky outputs | `code` | K7 |
| 6 | Solver synthesises answer from question + evidence map | `LLM` | Solver session |
| 7 | Log plan, evidence, answer as separate artefacts | `code` | V14 |

**Skeleton** — wiring only; `# LLM` markers identify configured sessions:

```
rewoo(question, tools):
    plan_text = Planner(question, tools)            # LLM — one call, full plan
    plan      = parse_and_validate(plan_text, tools) # code — fail closed
    evidence  = {}
    for batch in dag_topological_batches(plan):      # code — O4: parallel where DAG allows
        results = parallel_execute(batch, evidence, tools)  # code — no LLM
        evidence.update(results)
    evidence  = prune_if_large(evidence)             # code — K7
    answer    = Solver(question, evidence)           # LLM — one call, final synthesis
    log(plan, evidence, answer)                      # code — V14
    return answer
```

**The LLM sessions.** Two sessions, each set up once before the first call.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Planner** | strong generalist (plan quality caps the pattern) | role (*"you are a planner; emit a complete tool-use plan in one pass, no execution"*); the **tool catalogue** with names, signatures, and one-line descriptions; the **placeholder syntax spec** (`#E1`, `#E2`, … referenced by later steps); 1–3 few-shot exemplars of valid plans (S2); the strict output template (S6) | the question |
| **Solver** | smaller, cheaper generalist (synthesis, not invention) | role (*"you synthesise an answer from a question and an evidence map; do not call tools, do not replan; if evidence is insufficient, say so"*); answer format and citation rules (S6); any domain or policy context | the question + the populated evidence map |

Concretely, the **Planner** setup includes the tool catalogue rendered as a stable block (e.g. `Search[query] — search the web; returns top-3 snippets.` … `Calculator[expression] — evaluate a math expression.`) and the rule: *"Emit lines of the form #E{n} = Tool[args]. Later steps may reference earlier results as #E{n} inside args. Do not include conditionals, loops, or natural-language commentary. End with a final synthesis step or stop after the last tool."* The per-call prompt then carries only the question. The Solver's setup carries the corresponding rule that it must answer from the evidence map and call out gaps.

**Specialist-model note.** No fine-tuned specialist is required, but two structural choices change everything. First, **the Planner must be a separate session from the Solver**, even when the same model serves both — mixing them lets the Planner skimp on the plan ("the Solver will figure it out") and lets the Solver second-guess the plan ("I'd have chosen different tools"). Second, the Planner benefits materially from a **long-context, strong-reasoning model**: it holds the full tool catalogue, examples, and question in one prompt and must produce a coherent multi-step plan. The Solver does not need either property and can be cheaper. Where R5 is paired with **O4 Parallelization**, the Worker's concurrency is a code concern, not a model concern.

## Open-Source Implementations

- **ReWOO (original)** — [`github.com/billxbf/ReWOO`](https://github.com/billxbf/ReWOO) — Xu et al.'s reference implementation; Planner, Worker, Solver with placeholder variable substitution, evaluation scripts for HotpotQA and TriviaQA.
- **LangGraph ReWOO tutorial** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) (tutorial at `docs/docs/tutorials/rewoo/rewoo.ipynb`) — runnable graph implementation of Planner → Worker → Solver with variable substitution; the closest match to the structure shown above.
- **LangGraph.js ReWOO tutorial** — [`github.com/langchain-ai/langgraphjs`](https://github.com/langchain-ai/langgraphjs) — the TypeScript port of the same tutorial.

## Known Uses

- Multi-source research and report-generation agents that fan out independent lookups (web search + internal docs + structured DBs) and synthesise.
- Cost-constrained production Q&A systems that pre-classify queries into "independent lookups" (route to R5) vs "exploratory" (route to R4) — the routing itself is a Signal/Orchestration concern (O3).
- LangGraph-based assistants that adopt the ReWOO graph as the default for "answer questions that require N independent retrievals."
- Operational workflows with stable tool catalogues (deployment runbooks, compliance checks across enumerated systems) where the plan structure is predictable across tasks.

## Related Patterns

- **Distinct from** R4 ReAct — *the defining boundary*. R4 interleaves Thought-Action-Observation and adapts mid-task; R5 plans every tool call upfront and never re-enters the loop until execution is done. **Mutually exclusive for the same task**: R5 on a branching task gives a confident wrong answer; R4 on independent lookups burns ~5× the tokens for no quality gain. See CONFLICTS §CRITICAL 1.
- **Refines** R3 Plan-and-Solve — R3 plans, then executes step-by-step with possible mid-run replans; R5 hardens R3 into a single-pass plan + deterministic execution + single synthesis, trading R3's adaptability for token efficiency and parallelism.
- **Composes with** O4 Parallelization — independent nodes in R5's DAG are the natural fan-out point; without O4, R5 captures only the token saving, not the latency saving.
- **Composes with** V9 Bounded Execution — caps replan attempts when validation or Solver flags insufficient evidence.
- **Composes with** V14 Trajectory Logging — the plan, evidence map, and answer log as three clean artefacts.
- **Composes with** K7 Context Pruning — shrink bulky tool outputs before the Solver sees them.
- **Distinct from** R7 Reflexion — Reflexion adapts *across* runs by remembering past failures; R5 does not adapt at all within or across runs. Different time scales.
- **Distinct from** R9 Tree of Thoughts / R10 LATS — ToT/LATS explore an *unknown* solution space by branching; R5 assumes the solution path is known and linearisable. Diametrically opposed.
- **Pairs with** O3 Routing — a router that classifies queries as "independent lookups" vs "exploratory" sends the former to R5 and the latter to R4; the routing layer is what makes R5 safe to deploy in mixed workloads.
- **Signal-layer setup** — Planner relies heavily on **S6 Output Template** (placeholder syntax) and **S2 Few-Shot** (exemplar plans); Solver on **S6** (answer format).

## Sources

- Xu, B., Peng, Z., Lei, B., Mukherjee, S., Liu, Y., Xu, D. (2023) — "ReWOO: Decoupling Reasoning from Observations for Efficient Augmented Language Models" (arXiv:2305.18323). Primary source.
- LangGraph documentation — *"Reasoning without Observation"* tutorial (`langchain-ai.github.io/langgraph/tutorials/rewoo/rewoo/`).
- LangGraph.js documentation — TypeScript port of the same tutorial.
- "The AI Engineer" Substack — comparative analysis of single-agent reasoning patterns (R3 / R4 / R5 / R7).
- Nutrient.io — "ReWOO vs ReAct" practitioner analysis.
