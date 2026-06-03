# O4 — Parallelization

> Run independent sub-tasks concurrently across distinct LLM calls, then aggregate their outputs programmatically — turning serial wall-clock time into a fan-out / fan-in across agents.

**Also Known As:** Fan-Out / Fan-In, Concurrent LLM Calls, Parallel Execution. (Sectioning and Voting are *variants* of this pattern — see Variants.)

**Classification:** Category IV — Orchestration · Band IV-A Workflow · a *workflow* pattern — deterministic dispatch and aggregation around independent sub-tasks, no dynamic delegation.

---

## Intent

When sub-tasks of a request are genuinely independent of each other, run them simultaneously across distinct LLM calls and aggregate the results programmatically, so wall-clock latency collapses from the sum of the calls to the maximum.

## Motivation

A surprising amount of agent work decomposes into sub-tasks that have no data dependency on each other. A research request that needs five sources scanned; an evaluation pipeline that scores an answer along six rubrics; a code-review pass with security, performance, and style critics; a translation job across ten target languages. In a naive implementation, each of these runs serially — call one, wait, call the next — and the wall-clock cost is the sum of all of them.

Yet none of the sub-tasks needed any of the others to produce its result. The dispatcher could have fired them all at once and waited for the slowest. The scaffold-taxonomy survey of 13 production coding agents (arXiv 2604.03515) named this directly: O4 is *the most commonly missed optimisation in production systems.* Engineers reach for orchestration cleverness when the cheapest win — running independent things concurrently — is sitting unused.

The pattern is a single move: identify independence, fan out, fan in. It is fundamentally distinct from O2 Prompt Chaining (which is *sequential* because steps depend on each other) and from O6 Orchestrator-Workers (which is *dynamic* delegation by an LLM rather than deterministic dispatch by code).

The mechanical win is context bounding (mechanism 6): each worker has its own seq_len. The n² attention cost is paid over the worker's small isolated context, not over a monolithic context carrying all sub-tasks. A single agent doing 5 sub-tasks sequentially pays n² where n grows with each sub-task's output; O4 pays n² five times independently at a fraction of n_combined. This is not just a latency win — it is a quality win, because each worker's attention is concentrated on its own sub-task rather than diluted across all of them. (Mechanisms 2, 6.) O4 is what you reach for when the decomposition is fixed and the sub-tasks are honestly independent. It is also distinct from R12 Skeleton-of-Thought, the sibling at the prompt level: R12 parallelises the expansion of an *outline within one agent's output*; O4 parallelises *sub-tasks across distinct agents*. They are structurally the same fan-out, at different layers of the stack.

## Variants

The variants differ in *what is parallelised* and *how the outputs are combined*:

- **Sectioning.** Decompose one task into independent sub-tasks (different content, different scopes), dispatch each to its own worker, aggregate by concatenation, structured merge, or summary. The classic example: a code-review pipeline with security, performance, and style critics each examining the same diff; their reports are stitched into one review. (Anthropic, *Building Effective Agents*, 2024.)
- **Voting.** Dispatch the *same* prompt N times with different seeds, temperatures, or models; aggregate by majority vote, best-of, or judged selection. Used when a single sample is too unreliable but a small ensemble is cheap. **R17 Self-Consistency Voting** is the canonical case — same prompt, sample N times, majority over extracted answers — and is itself a specialisation of this O4 variant.

Both are the same pattern — fan out independent calls, fan in their results — differing only in whether the calls vary the *task* (Sectioning) or vary the *sample* (Voting). The Aggregator behaves differently in each: concatenating in Sectioning, voting / selecting in Voting.

## Applicability

Use Parallelization when:

- the work decomposes into sub-tasks with no data dependency between them;
- the decomposition is known at design time (no dynamic delegation needed);
- wall-clock latency is a binding constraint, or higher confidence from an ensemble is needed;
- your serving stack and rate-limit budget actually permit concurrent calls.

Do not use when:

- sub-tasks have sequential dependencies — output of step N is input of step N+1. Use **O2 Prompt Chaining**.
- the decomposition itself must be decided by an LLM at runtime (open-ended task, unknown shape). Use **O6 Orchestrator-Workers**.
- the parallel work is *sections of one agent's structured output*, not sub-tasks routed to distinct agents. Use **R12 Skeleton-of-Thought** at the prompt level.
- the goal is to challenge a single answer with adversarial perspectives that *debate* each other across rounds. Use **O12 Debate / Deliberation**.
- per-call cost is the binding constraint and ensemble or parallel work cannot be afforded. Use **O1 Single Agent**.

## Decision Criteria

O4 is right when sub-tasks are honestly independent, the decomposition is fixed, and latency or confidence (not raw quality of reasoning) is the lever.

**1. Test independence.** Take a representative request and list the sub-tasks. Ask, for each pair: *could B run without A's output?* If yes for every pair, the work is parallelisable. If any pair fails the test, that edge is a dependency — chain those two with **O2** and parallelise the rest. Practical threshold: $\geq$ 80% of sub-tasks must be pairwise independent before O4 pays.

**2. Quantify the latency win.** Measure serial wall time `T_serial = sum(t_i)` and predicted parallel wall time `T_parallel ≈ max(t_i) + dispatch_overhead`. Speed-up factor `T_serial / T_parallel`. Below ~2$\times$ speed-up the wiring overhead is rarely justified; above ~3$\times$ it almost always is. For Voting variants, the equivalent test is *confidence gain per dollar* — measure error rate at N=1 vs N=5 vs N=10 and pick the knee.

**3. Confirm the serving stack parallelises.** Concurrent API requests, async dispatch, or batched inference must actually run simultaneously. Single-tenant local inference often serialises under the hood; check before adopting. If the stack does not parallelise, O4 saves nothing — drop back to **O2**.

**4. Budget rate limits and peak cost.** O4 multiplies peak QPS by the fan-out factor. A request that was 5 sequential calls becomes 5 concurrent calls — check provider rate limits, retry behaviour, and peak spend. Pair with **V9 Bounded Execution** for a hard cap on fan-out width.

**5. Plan the aggregator.** Decide upfront: concatenate (Sectioning, structured sections), structured merge (Sectioning with overlapping outputs), majority vote (Voting on closed-vocab answers), judged selection (Voting on open-ended outputs — pair with **V15 LLM-as-Judge**). An aggregator that does not match the variant is the pattern's most common silent failure.

**Quick test — O4 is the right pattern when:**

- sub-tasks are pairwise independent (no output of one is input of another), *and*
- the decomposition is known at design time (not LLM-decided per request), *and*
- the serving stack actually runs the calls in parallel, *and*
- expected speed-up or confidence-gain exceeds the wiring and peak-cost overhead.

If any condition fails, choose the right neighbour. Sequential dependencies $\to$ **O2 Prompt Chaining**. Decomposition must be dynamic $\to$ **O6 Orchestrator-Workers**. Parallel sections of *one agent's* output $\to$ **R12 Skeleton-of-Thought**. Voting on the same prompt as a reasoning move $\to$ **R17 Self-Consistency Voting** (a special case of O4 Voting). Adversarial debate rather than independent samples $\to$ **O12 Debate / Deliberation**.

## Structure

```
              ┌──▶ Worker A  ─┐
              │               │
  Request ──▶ Dispatcher ──▶ Worker B  ─┤── parallel
              │               │
              └──▶ Worker C  ─┘
                              │
                              ▼
                          Aggregator ──▶ Result
                          (concat / merge /
                           vote / judge)
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Dispatcher** | the fan-out decision and the prepared per-worker inputs | request $\to$ list of (worker, context) pairs | reason about the answer itself, or fold the workers' results back into a synthesis — that is the Aggregator's call. A Dispatcher that also synthesises has collapsed into O6. |
| **Workers** | producing one independent sub-result each | (sub-task, isolated context) $\to$ sub-result | look at sibling workers' outputs — that re-introduces dependency and destroys the parallelism. Workers run in **O17 Agent Isolation** by default. |
| **Aggregator** | combining the workers' outputs into the final result | list of sub-results $\to$ final answer | re-do the workers' reasoning. The aggregator concatenates, merges, votes, or selects — it does not re-derive. For open-ended Voting, the aggregator may invoke a Judge, but the Judge is a participant in its own right. |
| **Judge** *(optional, Voting variant)* | selecting the best candidate when votes are open-ended | request + N candidates $\to$ chosen candidate (+ rationale) | regenerate the candidates or silently merge fragments of multiple candidates — it picks one, or returns "no candidate qualifies." |
| **Bound / Rate Controller** | capping fan-out width and pacing concurrent calls | proposed fan-out $\to$ admitted fan-out | swallow errors silently; a worker dropped by rate-limiting must surface as a partial-failure signal to the Aggregator. |

The Dispatcher, the Workers, and the Aggregator are **structurally distinct sessions**, even if the same model serves all of them. Mixing the Aggregator into the Dispatcher (so the dispatcher also synthesises) is the most common failure mode — the pattern collapses into a single complicated call that is no longer parallel.

## Collaborations

A request arrives at the Dispatcher. The Dispatcher applies the fixed decomposition rule — split by section, by source, by rubric, by language, or by sample — to produce a list of `(worker, context)` pairs. The Bound / Rate Controller caps the list at the configured fan-out width and admits the calls. Each Worker runs in its own isolated context (O17), producing its sub-result. The wiring collects results as they return; on partial failure (rate-limit, timeout, refused output) the unfilled slots are flagged. When the gathered set crosses the configured quorum (often "all," sometimes "best K of N" for Voting), the Aggregator runs: concatenation or structured merge for Sectioning; majority vote or Judge-based selection for Voting. The final result is returned. No worker ever sees another worker's output; aggregation is the only place independent work re-converges.

## Consequences

**Benefits**
- Wall-clock latency drops from `sum(t_i)` toward `max(t_i)` for Sectioning, or toward `t_single` for parallel Voting.
- Voting variants raise confidence on stochastic tasks — small ensembles often beat a single sample on hard reasoning.
- Each Worker runs with a clean, focused context (when paired with O17) — better focus, lower per-call cost than a single monolithic call.
- Deterministic dispatch and aggregation are easy to test, log, and replay — unlike dynamic O6 orchestration.

**Costs**
- Peak API cost and peak QPS scale with the fan-out factor — a budget concern, especially on provider rate limits.
- Total tokens rise modestly: per-worker context is repeated, not shared.
- Aggregation complexity is real work — merge logic for Sectioning, voting / judging logic for Voting must be designed and tested.
- Partial-failure handling is mandatory; some calls will return errors, timeouts, or refusals.

**Risks and failure modes**
- *Hidden dependency* — sub-tasks the team believed were independent in fact share an assumption, and parallel results contradict or duplicate each other.
- *Rate-limit cascade* — fan-out saturates provider limits; some workers retry, others drop; aggregation runs on partial input without realising.
- *Aggregator collapse* — an Aggregator that uses an LLM to "synthesise" the workers often re-derives the answers and the parallel speed-up evaporates into a slow synthesis call.
- *Fan-out runaway* — without a cap, decomposition produces 50 workers when 5 was the design intent; concurrent cost spikes and latency *increases* due to queuing.
- *Voting with correlated samples* — same model, same prompt, same temperature N times produces N correlated samples; the vote is no more reliable than one sample. Diversity (temperature, model, persona) is required for Voting to pay. Token generation is stochastic sampling from a learned distribution, and this stochasticity is the source of sample diversity (mechanism 7). At temperature=0 (greedy decoding), every sample is identical — zero diversity. At temperature>0, samples diverge because each token is drawn from a probability distribution; but if the distribution is very peaked (the model is confident), samples converge anyway. Cross-model or cross-temperature diversity is required because the underlying sampling distribution, not the temperature alone, determines whether the ensemble adds information. (Mechanism 7.)

## Implementation Notes

- Decide the variant first. Sectioning and Voting answer different questions; the Aggregator design follows from that choice, not the other way around.
- Cap the fan-out (typical `max_workers` 3–10). Pair with **V9 Bounded Execution**. An ungated decomposition is the pattern's quickest path to a runaway bill.
- Run Workers in isolated contexts by default (**O17 Agent Isolation**) — siblings should not see each other's prompts or outputs.
- Handle partial failure explicitly. The aggregator must know which slots are filled, which are empty, and what the quorum rule is.
- For Voting on free-form outputs, pair with **V15 LLM-as-Judge** as the Aggregator's selection step. For Voting on closed-vocab outputs, plain majority is enough.
- Log per-worker traces (**V14 Trajectory Logging**). Debugging a parallel pipeline without traces is debugging blind.
- Watch for the temptation to add cross-worker communication "just for coherence" — at that point the pattern has crossed into O11 Blackboard or O6 Orchestrator-Workers. Move it deliberately, not by accident.
- When workers vary by *role* (security critic vs performance critic), use distinct Worker session setups; when workers vary by *sample* (same role, different seed), reuse one Worker session and vary sampling parameters.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** O4 chains a deterministic *Dispatcher* with N parallel *Worker* invocations and a final *Aggregator*. Workers typically run in **O17 Agent Isolation** (fresh contexts). The fan-out is bounded by **V9 Bounded Execution**. The Voting variant often invokes **V15 LLM-as-Judge** as its Aggregator step; **R17 Self-Consistency Voting** is the special case of O4 Voting where the Workers are independent samples of the same prompt and the Aggregator is a majority over extracted answers.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Dispatcher — decompose request into independent sub-tasks; prepare per-worker context | `code` (or rule, or `LLM` for inputs that need parsing) | Dispatcher logic; O17 for context preparation |
| 2 | Bound — cap fan-out width and admit calls | `code` | V9 |
| 3 | Workers ($\times$N) — run sub-task in parallel, each in an isolated context | `LLM` (parallel) | Worker session(s); O17 |
| 4 | Collect — gather results; mark partial failures | `code` | |
| 5 | Aggregator — concatenate / merge / vote / judge | `code` (or `LLM` for Judge-based selection) | Aggregator logic; V15 for Voting variants |

**Skeleton** — the wiring; each `# LLM` line is a configured session, not code:

```
parallelize(request):
    subtasks = Dispatcher(request)              # code — fixed decomposition rule
    subtasks = subtasks[:max_workers]            # code — V9 cap

    results = parallel_map(                       # code — fan-out
        lambda s: Worker(s.context, s.prompt),    # LLM — runs in parallel, O17 isolated
        subtasks
    )

    filled, missing = partition(results)          # code — partial-failure handling
    if quorum_met(filled):
        return Aggregator(filled)                 # code or LLM — variant-dependent
    else:
        return fallback(request, filled, missing) # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Worker (Sectioning)** | the system's main generalist, or a role-specialist per worker type | role for this section (*"you are the security reviewer"* / *"you summarise source X"*); the contract for the section's output format (S6); the isolation rule (*"do not assume access to other workers' outputs"*) | the sub-task, the prepared context, and the section identity |
| **Worker (Voting)** | the system's main generalist; sometimes a mix of models for ensemble diversity | role for the underlying task; the contract for the answer format; *no* role differentiation across siblings — diversity comes from sampling parameters | the request (same for all N siblings); sampling temperature and seed varied per call |
| **Judge** *(Voting variant only)* | small fast generalist, or a stronger model when the choice is hard | role (*"you select the best of N candidate answers against this rubric; return one candidate and a one-line rationale, or return NO\_CANDIDATE"*); the rubric; the output contract | the request + the N candidate outputs |

**Specialist-model note.** O4 itself requires **no fine-tuned specialist** — capable generalists serve all three roles. Two structural choices do material work:

- **Workers must run in isolated sessions.** Same model is fine; different setups per Sectioning role; identical setups but varied sampling parameters per Voting sample. Letting any worker see another worker's output re-introduces dependency and the parallelism collapses.
- **The Aggregator should be `code` when it can be.** Concatenation, structured merge, and majority vote are deterministic and cheap; an LLM Aggregator is justified only for open-ended Voting selection (where a Judge is doing genuine arbitration) or for Sectioning outputs that need natural-language fusion. An LLM Aggregator that "synthesises" five worker outputs into one essay typically re-does the work and erases the latency win — push back hard on that design.

## Open-Source Implementations

- **Anthropic Claude Cookbooks** — [`github.com/anthropics/claude-cookbooks`](https://github.com/anthropics/claude-cookbooks) — the `patterns/agents/` directory contains minimal reference implementations of the workflows from *Building Effective Agents*, including parallelization with Sectioning and Voting examples. The canonical starting point.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — first-class support for fan-out / fan-in via parallel-branch graphs and the `Send` API for dynamic map-reduce-style fan-out. Reducers handle parallel writes to shared state.
- **Microsoft AutoGen (Core API, v0.4+)** — [`github.com/microsoft/autogen`](https://github.com/microsoft/autogen) — the *Concurrent Agents* design pattern in the Core user guide: multiple agents subscribed to the same topic process a message simultaneously; aggregation happens at a downstream sink agent.
- Most production embodiments are bespoke wiring around a chat-completions API and an async runtime — Python `asyncio.gather`, JavaScript `Promise.all`, or any actor framework will do. The pattern is a few dozen lines around any concurrent-request-capable client.

## Known Uses

- **Anthropic Research** (deep-research agents, internal evaluation) — multi-source research agents fan out one sub-query per source and aggregate findings; the *Building Effective Agents* post names parallelization as a recurring pattern in their customer deployments.
- **Code-review agents** (Claude Code, Cursor, Devin) — security, correctness, performance, and style critics often run as parallel workers on the same diff, with a synthesis step producing the unified review.
- **Translation and localisation pipelines** — same source text fanned out to N target-language workers in parallel.
- **LLM evaluation harnesses** — rubric scoring runs N criteria as parallel judges, an O4 Voting / Sectioning hybrid.
- **Search and retrieval orchestration** (Perplexity, You.com) — query fanned to multiple retrievers / sub-corpora concurrently, results merged before generation.

## Related Patterns

- **Sibling of** R12 Skeleton-of-Thought — same fan-out / fan-in shape, different layer. R12 parallelises *sections of one agent's output* at the prompt level (the agent invokes its Expander session S times against its own skeleton); O4 parallelises *sub-tasks across distinct agents or workers* at the orchestration level. The boundary: if the parallel callees are the *same configured session invoked S times for sections of one output*, it is R12; if they are *distinct sub-tasks with distinct roles or distinct inputs*, it is O4.
- **Distinct from** O2 Prompt Chaining — O2 is *sequential* because steps depend on each other; O4 is *parallel* because they don't. They compose: an O2 pipeline can have an O4 stage where one step fans out before the next sequential step.
- **Distinct from** O6 Orchestrator-Workers — O6 has an LLM Orchestrator that *dynamically* decides what to delegate and to whom; O4 has a deterministic Dispatcher with a fixed decomposition rule. O6 is more flexible and more expensive; prefer O4 when the decomposition can be enumerated at design time.
- **Distinct from** O11 Blackboard — O11 has workers reading and writing a shared state and a control unit activating agents based on that state; O4 workers do not share state during execution. Cross-worker communication during execution is the line between O4 and O11.
- **Distinct from** O12 Debate / Deliberation — O12 has multiple agents *argue across rounds*, each round depending on the previous; O4 Voting has independent samples that do not see each other. Sequential debate is O12; parallel sampling is O4.
- **Specialised by** R17 Self-Consistency Voting — R17 is the canonical case of the O4 Voting variant: same prompt, N independent samples, majority over extracted answers. R17 lives in Reasoning because it shapes a single agent's reasoning move; the underlying mechanism is O4.
- **Pairs with** O17 Agent Isolation — workers in O4 should run in fresh, isolated contexts by default. The standard production stack for complex agents is O6 + O4 + O17.
- **Composes with** O2 Prompt Chaining — most production pipelines are O2 at the top level with O4 stages embedded where the decomposition is independent.
- **Composes with** V9 Bounded Execution — cap the fan-out width or one query will saturate the rate-limit budget.
- **Composes with** V14 Trajectory Logging — per-worker traces are mandatory for debugging parallel pipelines.
- **Composes with** V15 LLM-as-Judge — when the Voting variant's Aggregator needs to select among open-ended candidates, the Judge is exactly V15.

## Sources

- Anthropic (2024) — *Building Effective Agents* (Schluntz, E., and Zhang, B.). Parallelization named as one of five core workflow patterns, with Sectioning and Voting sub-variants.
- Wang, X. et al. (2022) — "Self-Consistency Improves Chain of Thought Reasoning in Language Models" (arXiv 2203.11171) — the canonical Voting case (see also R17 Self-Consistency Voting).
- arXiv 2604.03515 — "Inside the Scaffold" — empirical study of 13 production coding agents naming O4 as the most commonly missed optimisation.
- LangGraph documentation — parallel-branch graphs, the `Send` API for dynamic fan-out, and reducer-based aggregation of parallel writes.
- Microsoft AutoGen Core (v0.4+) documentation — *Concurrent Agents* design pattern.
- AWS Prescriptive Guidance — parallelization workflow pattern.
