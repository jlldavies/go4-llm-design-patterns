# R10 — Language Agent Tree Search (LATS)

> Run Monte Carlo Tree Search over an agent's reasoning trajectories: select promising branches by UCB, expand with LLM-proposed actions, evaluate with an LLM value function, simulate forward, and backpropagate value through the tree — so the agent searches the solution space the way AlphaGo searches a board.

**Also Known As:** LATS, MCTS for LLM Agents, Monte Carlo Agent Search. (LATS unifies ReAct (R4) + Tree of Thoughts (R9) + Reflexion (R7) under MCTS — see Related Patterns.)

**Classification:** Category III — Reasoning · Band III-B Search-structured · the formal MCTS variant of branching reasoning — sibling of R9 ToT, strictly more powerful and roughly 10$\times$ more expensive.

---

## Intent

Search the solution space of an agentic task with full Monte Carlo Tree Search — selection by UCB, expansion, simulation, and value backpropagation — using the LLM as action generator, value estimator, and verbal critic, so the agent can revisit any node, redirect from any dead end, and converge on high-quality trajectories on problems that defeat single-path patterns.

## Motivation

R4 ReAct walks one trajectory; if a step is wrong, the trajectory limps to a wrong answer or stalls. R7 Reflexion rescues that by *retrying* the whole trajectory with a verbal critique attached — but it still walks one trajectory at a time and only learns between full attempts. R9 Tree of Thoughts adds branching and per-node evaluation, but its search is loose: BFS / DFS with LLM scoring, no statistical accounting of which branches have been tried how many times with what success, and pruning by single-shot LLM judgement.

The move that distinguishes LATS is **value backpropagation** under a principled exploration/exploitation rule. MCTS, the algorithm that powered AlphaGo, maintains for every node a visit count and a running value estimate; at each step it descends the tree by the UCB rule (favour high-value *and* under-explored branches); it expands a leaf, simulates forward to a terminal, observes the outcome, and **propagates that outcome up to every ancestor**. After enough iterations, the value estimates concentrate on the best subtrees and the agent commits to the best-explored action from the root. LATS (Zhou et al., 2023) ports this algorithm onto LLM agent trajectories: each tree node is a state (a prefix of Thought–Action–Observation steps); the LLM proposes actions (mechanism 7 — each proposal is a stochastic sample from the model's distribution), scores states, and — when a simulation fails — emits a Reflexion-style verbal critique that is folded into the value update.

The pay-off is genuinely new behaviour, not just more compute. ToT can prune a bad branch but cannot *learn* across simulations that "this whole region of the tree is unpromising"; LATS does, because backpropagation makes every rollout inform every ancestor. ToT cannot backtrack to a node it already explored and *try the next-best child* — it has no statistics to make that choice; LATS does. The cost is high: 5–20$\times$ more LLM calls than ToT, ~50–100$\times$ more than ReAct. So R10's place in the language is narrow but real — the pattern of last resort, used when correctness on a hard problem is worth the call budget.

## Applicability

Use LATS when:

- the task is hard enough that ReAct (R4), Reflexion (R7), and Tree of Thoughts (R9) have all been tried and demonstrably fail;
- the task admits a useful value signal — a verifier, a test suite, a programmatic correctness check, or at minimum a reliable LLM critic — that can score partial trajectories;
- correctness or quality is worth roughly 10$\times$ ToT's cost (10–100$\times$ ReAct's);
- the task is bounded enough that a tree with depth in the tens and branching factor of 3–5 can plausibly contain a solution.

Do not use when:

- a single trajectory plus light retry (R4 + bounded retries, or R7 Reflexion) already solves the task — LATS is wasted;
- the search space is one path with a known shape — use R3 Plan-and-Solve;
- the task has no usable value signal — MCTS without value estimation degenerates to random search;
- the call budget is tight or latency is user-facing — choose R9 Tree of Thoughts (cheaper search) or R7 Reflexion (cheaper retry);
- the loop is not bounded by V9 Bounded Execution — running MCTS on an LLM with no cap is a guaranteed cost incident.

## Decision Criteria

R10 is right when ToT-class search is genuinely insufficient, a value signal exists, and the budget for ~10$\times$ more LLM calls is justified by the quality of the answer.

**1. Did the simpler pattern already fail?** Run R4, then R7, then R9 on a held-out hard set. If any of them solves the task at acceptable cost, stop — that is the right pattern. Only when all three plateau below the required quality bar does R10 become worth considering. Falling back upward: if R10 is in question and R9 is untested, **test R9 first**.

**2. Does a value signal exist?** MCTS needs to score trajectories — partial and complete.
- *Strong signal* (executable verifier: test suite, type check, simulator) $\to$ LATS is appropriate.
- *Medium signal* (LLM-as-judge against a rubric, V15) $\to$ LATS works but is noisier; calibrate the critic carefully.
- *No signal* (no verifier, no rubric) $\to$ LATS degenerates to UCB over random; fall back to R9 with heuristic pruning, or R7 if a retry signal exists.

**3. Cost the call budget.** Typical LATS uses $\approx$ (depth $\times$ branching $\times$ rollouts) LLM calls per task; in published reports that is 50–300 calls per problem. Compare against R9 (~20–50) and R4 (~5–15). If the per-task budget is < ~50 LLM calls, LATS is out of scope — use R9.

**4. Search space shape.** LATS suits trees with branching factor 3–8 and depth 5–30. Below that, exhaustive enumeration is cheaper. Above that, even MCTS will not concentrate value estimates within the budget — re-frame the task or apply R11 Buffer of Thoughts to seed templates.

**5. Loop-bound discipline.** Pair with **V9 Bounded Execution** non-negotiably. Cap: total LLM calls, total tree nodes, wall time, and *no-improvement plateau* (terminate if best-value path has not improved for K rollouts). MCTS with no bound is a cost incident waiting to happen — surface this as a Red Flag in any review.

**Quick test — R10 is the right pattern when:**

- R4 / R7 / R9 have been tried and demonstrably plateau below the quality bar, *and*
- a usable value signal exists (verifier, test suite, or calibrated LLM judge), *and*
- the per-task call budget can absorb ~10$\times$ R9's cost, *and*
- the search tree is shaped for MCTS (branching 3–8, depth 5–30), *and*
- V9 bounds are in place.

If any condition fails, choose the cheaper sibling: **R9 ToT** when branching helps but the budget cannot stretch; **R7 Reflexion** when one trajectory + verbal critique is enough; **R3 Plan-and-Solve** when the path is actually predictable. If no value signal exists at all, no amount of search will help — invest in the verifier first, then revisit.

## Structure

```
                          ┌───────── root state ─────────┐
                          │  (initial task / prompt)     │
                          └──────────────┬───────────────┘
                                         │
                  ┌──────── 1. SELECT (UCB descent) ────────┐
                  │  pick child maximising                  │
                  │   value(child) + c·√(ln N / n(child))   │
                  └──────────────────┬──────────────────────┘
                                     ▼
                  ┌────────── 2. EXPAND (LLM) ─────────────┐
                  │  propose k candidate actions from this │
                  │  state; add them as child nodes        │
                  └──────────────────┬──────────────────────┘
                                     ▼
                  ┌──── 3. SIMULATE / EVALUATE (LLM) ──────┐
                  │  roll forward (greedy or sampled) to a │
                  │  terminal; score with value function   │
                  │  or external verifier                  │
                  └──────────────────┬──────────────────────┘
                                     ▼
                  ┌── 4. REFLECT (LLM, on failure) ────────┐
                  │  emit verbal critique; fold into value │
                  └──────────────────┬──────────────────────┘
                                     ▼
                  ┌──── 5. BACKPROPAGATE (code) ───────────┐
                  │  push value & visit count up to root,  │
                  │  through every ancestor                │
                  └──────────────────┬──────────────────────┘
                                     │
                       loop bounded by V9 (calls, nodes,
                       wall time, no-improvement plateau)
                                     │
                                     ▼
                  ┌──── 6. COMMIT (code) ──────────────────┐
                  │  return best-value path from root      │
                  └─────────────────────────────────────────┘
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Tree Store** | the search tree: nodes, edges, visit counts, value estimates | reads/writes from the controller | persist beyond one task; LATS state is per-task scratch, not memory (that is K10 / K12). |
| **UCB Selector** | the descent decision at each iteration | tree + UCB constant `c` $\to$ next leaf to expand | use raw value alone (collapses to greedy) or raw visits alone (collapses to BFS); the UCB *combination* is the pattern. |
| **Action Generator (LLM)** | proposing candidate next actions at an expansion node | current state (prefix of thoughts/actions/observations) $\to$ k candidate actions | propose the same action across siblings (kills diversity); the prompt must enforce variation. |
| **Value Estimator (LLM)** | scoring a state's promise (and rolled-out trajectory's outcome) | state or trajectory $\to$ scalar value in `[0, 1]` | be the same session as the Action Generator — value estimation must be a separate setup or the scorer rationalises its own proposal. |
| **Simulator** | rolling forward from an expanded node to a terminal | state + policy $\to$ terminal trajectory + outcome | exceed the per-rollout step cap (V9) — an unbounded simulation defeats the budget. |
| **Reflection Critic (LLM, optional)** | verbal post-mortem on a failed rollout | failed trajectory + outcome $\to$ verbal critique folded into the value update | rewrite the tree structure; reflections inform values, they do not edit branches. |
| **Backpropagator** | propagating the rollout outcome up to root | leaf outcome $\to$ updated values & visits on every ancestor | re-evaluate any node with the LLM during the update; backprop is pure arithmetic over already-collected signals. |
| **Controller / Bound (code, V9)** | the outer loop: iterate, terminate, commit | configured budget $\to$ final answer trajectory | run without a hard cap — every dimension (calls, nodes, time, plateau) must be bounded. |

Eight responsibilities, three of them LLM-backed. The split between Action Generator and Value Estimator is the structural move that separates LATS from R9 ToT — ToT collapses both into a single "judge the next thoughts" prompt; LATS keeps them as different sessions so that value cannot be inflated by the proposer.

## Collaborations

The Controller initialises the Tree Store with the root state and enters the bounded loop. Each iteration: the UCB Selector walks from the root by repeatedly choosing the child maximising the UCB score, until it reaches a leaf. The Action Generator is invoked on that leaf to propose k candidate actions, which become new child nodes. The Simulator picks one (typically the most promising by Value Estimator) and rolls forward — applying actions, calling tools, observing results — until it reaches a terminal state or hits the per-rollout step cap. The Value Estimator scores the resulting trajectory; on failure, the Reflection Critic emits a verbal critique that is concatenated into the value signal. The Backpropagator pushes the score up the tree, incrementing visit counts and updating running value estimates on every ancestor. The Controller checks the V9 bounds: if any cap is hit (call count, node count, wall time, or K rollouts with no improvement), the loop terminates and the best-value path from root is committed and returned. Otherwise it iterates.

## Consequences

**Benefits**
- Highest quality reasoning available among prompting/search patterns when a value signal exists; SOTA on HumanEval and WebShop in the original LATS paper.
- Genuine cross-rollout learning: every simulation informs the value of every ancestor, so unpromising regions are demoted automatically.
- Backtracking is principled — the agent can return to any earlier decision and try the next-best child, with statistics to support the choice.
- Reflection (R7-style) folds in cleanly as a value signal, unifying three reasoning patterns under one search.

**Costs**
- 5–20$\times$ more LLM calls than R9 ToT, 50–100$\times$ more than ReAct.
- Latency is heavy: even with parallel expansion, depth $\times$ rollouts dominates.
- Implementation complexity: tree management, UCB tuning, parallel simulation, bound enforcement — much more code than R4 / R7 / R9.

**Risks and failure modes**
- *Value-estimator collapse* — if the LLM scorer is poorly calibrated, UCB descends into the wrong subtree and the search converges on a false optimum.
- *Proposer–scorer leakage* — if the Action Generator and Value Estimator share a session, the scorer inflates its own proposals; the tree becomes self-confirming.
- *Unbounded cost* — MCTS without strict V9 bounds is the most expensive single failure mode in the catalogue; a single hard problem can burn through a daily budget.
- *Shallow simulation* — if the per-rollout cap is too low, the Simulator never reaches a state the verifier can score, and every leaf returns the same flat signal.
- *Wrong granularity* — if a "node" is too fine-grained (every token a branch), the tree explodes; too coarse (whole plans), and the search has nothing to discriminate.

## Implementation Notes

- Pick the node granularity deliberately: a node should be a state at which the LLM has *real choices*, typically one ReAct step (one Thought–Action pair) or one ToT-style "thought".
- Tune the UCB exploration constant `c` empirically — too low and search becomes greedy; too high and it becomes random. Start at √2 (the textbook default) and adjust by measuring how much of the budget lands on the top-value subtree at termination.
- Run expansion in parallel: the k child candidates from one node can be generated and value-estimated concurrently. This is the only practical way to keep latency tolerable.
- Prefix caching (mechanism 5) is the single largest LATS cost lever. LATS trajectories share prefixes naturally: all paths from root share at least the root state; siblings at the same depth share the full path to their parent. At Anthropic pricing (5-min TTL, ~10% of normal input cost on cache hit, minimum 1024 tokens), a 2000-token shared prefix read 50 times across a single LATS run saves ~90% of that prefix's input cost per call. Structure prompts so the stable path-to-current-node appears as a single contiguous prefix before any variable content.
- Use the strongest available model for the Value Estimator (mechanism 8 — per-token compute differs roughly 10$\times$ between 7B and 70B models; value-estimation accuracy caps search quality and a stronger model here compounds over every subsequent UCB decision). The Action Generator can be smaller — diversity matters more than depth there.
- Add a *no-improvement plateau* bound: terminate after K rollouts without the best-value path changing. Often half the budget is wasted polishing an already-converged answer.
- If a verifier exists (test suite, type-checker, simulator), prefer it over LLM scoring at the leaves. LATS's quality cap is the value signal's quality.
- Log every rollout (V14 Trajectory Logging) — replaying the tree is the only practical way to debug a misbehaving LATS run.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** R10 builds on the inner step of **R4 ReAct** (one node = one ReAct step), borrows verbal critique from **R7 Reflexion** (as a value signal), and is the formal MCTS sibling of **R9 ToT** (which uses simpler BFS/DFS over the same kind of tree). Mandatory pair with **V9 Bounded Execution**; **V14 Trajectory Logging** is strongly recommended; **V15 LLM-as-Judge** typically supplies the Value Estimator when no programmatic verifier exists.

**The chain (one iteration of the MCTS loop):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Select leaf via UCB descent from root | `code` | Tree Store, UCB Selector |
| 2 | Propose k candidate actions at the leaf | `LLM` | Action Generator session, R4 step shape |
| 3 | Score each candidate (cheap, optional) | `LLM` | Value Estimator session |
| 4 | Add candidates as child nodes | `code` | Tree Store |
| 5 | Pick a child and simulate forward to terminal | `LLM` (loop) | Simulator, R4 inner step |
| 6 | Evaluate the terminal trajectory | `LLM` (or verifier) | Value Estimator / external verifier (V15) |
| 7 | On failure: reflect — emit verbal critique | `LLM` | Reflection Critic session (R7) |
| 8 | Backpropagate value & visits to root | `code` | Backpropagator |
| 9 | Check V9 bounds; loop or commit best path | `code` | Controller, V9 |

**Skeleton** — wiring only; each `# LLM` line is a configured session:

```
lats(task, budget):
    tree = TreeStore(root=task)                        # code
    while not budget.exhausted() and not plateau(tree):  # code — V9-bounded
        leaf  = ucb_descend(tree)                       # code
        actions = ActionGenerator(leaf.state, k)        # LLM — propose k children
        for a in actions:                               # code — parallelisable
            tree.add_child(leaf, a)
        child = pick_best(leaf.children, ValueEstimator)   # LLM — quick score
        outcome = simulate(child, max_steps)            # LLM loop — R4 inner step
        score = ValueEstimator(outcome) or verifier(outcome)  # LLM or code (V15)
        if score < threshold:
            critique = ReflectionCritic(outcome)        # LLM — R7-style
            score = fold(score, critique)
        backprop(child, score, tree)                    # code
    return tree.best_path_from_root()                   # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Action Generator** | the system's main generalist; diversity matters more than ceiling | role (*"you propose candidate next actions from this state"*); the action grammar (ReAct Thought / Action / Action-input); instruction to produce **k diverse** candidates (S5 constraint framing); output contract (a list of k action proposals, S6) | the current trajectory prefix + `k` |
| **Value Estimator** | the strongest available model — value calibration caps the search's quality | role (*"you score how promising a trajectory is for solving the task"*); the scoring rubric (criteria, examples of low / mid / high scores); output contract (a scalar in [0,1] plus one-line justification) | the trajectory (partial or terminal) |
| **Simulator step** | the same generalist as Action Generator | a ReAct setup (R4): tool list, Thought / Action / Observation grammar, stop criteria | the trajectory prefix + last observation |
| **Reflection Critic** | strong generalist | role (*"you analyse failed trajectories and produce a verbal critique of what went wrong"*); a critique schema (root cause; the decision point that mattered; what to try instead) | the failed trajectory + the outcome |

The Action Generator and Value Estimator **must be separate sessions**, even when the same model serves both — distinct setups, distinct invocations. Sharing them is the proposer–scorer leakage failure mode.

**Specialist-model note.** No fine-tuned specialist is required for LATS — capable generalists serve every role, and the original paper uses GPT-3.5 and GPT-4. But two structural needs change the build: (a) the Value Estimator benefits materially from the strongest model available, because the search's quality cap is the value signal's quality; (b) parallel expansion (k children concurrently) is required for tolerable latency, so the infrastructure needs concurrent LLM calls and prompt caching on shared prefixes. Where a programmatic verifier exists (test suite, type checker, simulator), prefer it to the LLM Value Estimator at the leaves — it is cheaper, faster, and not subject to proposer–scorer leakage. The Reflection Critic is genuinely optional: the basic LATS algorithm works without it; folding it in is the integration with R7 that the original paper emphasises.

## Open-Source Implementations

- **LanguageAgentTreeSearch** — [`github.com/lapisrocks/LanguageAgentTreeSearch`](https://github.com/lapisrocks/LanguageAgentTreeSearch) — the official implementation from Zhou et al. (ICML 2024); covers HumanEval, HotpotQA, and WebShop benchmarks; the reference for what "vanilla LATS" means.
- **LangGraph LATS tutorial** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) (tutorial: `docs/docs/tutorials/lats/lats.ipynb`) — runnable notebook implementing LATS as a LangGraph state machine; the closest production-shaped reference.
- **AutoGen LATS notebook** — [`autogenhub.github.io/autogen/docs/notebooks/lats_search`](https://autogenhub.github.io/autogen/docs/notebooks/lats_search/) — LATS implemented over the AutoGen multi-agent framework; useful for the action-generator-as-agent framing.

## Known Uses

- **Code-generation agents** that report HumanEval / SWE-Bench scores at the frontier — research-grade systems frequently cite LATS-style search as the path from ~85% pass@1 to ~92%+.
- **Web-navigation agents** (WebShop, WebArena research lines) — MCTS-driven exploration over browser actions; LATS-class search consistently improves over ReAct + Reflexion baselines on multi-step navigation benchmarks.
- **Research / advanced-reasoning settings** — LATS is the search algorithm of choice when the task admits a verifier (theorem-proving sketches, formalised math, complex planning benchmarks); rare in user-facing production due to cost.
- **Inference-time reasoning models** (the o-series and equivalents) effectively implement internalised search closer to LATS than to ToT, with built-in value estimation via test-time compute — when those models are available, prefer them to building LATS at the orchestration layer.

## Related Patterns

- **Sibling of** R9 Tree of Thoughts — both branch and evaluate; LATS adds visit-count statistics, UCB selection, and full value backpropagation. R10 is strictly more powerful and roughly 10$\times$ more expensive. Default to R9; escalate to R10 only when R9 plateaus.
- **Unifies** R4 ReAct + R7 Reflexion + R9 Tree of Thoughts — the original LATS paper's framing. The inner step is R4; the verbal critique on failure is R7; the tree shape is R9. R10's contribution is the MCTS algorithm that ties them together.
- **Required by** V9 Bounded Execution — non-negotiable. MCTS on an LLM without strict bounds is the catalogue's most expensive single failure mode.
- **Pairs with** V14 Trajectory Logging — the only practical way to debug a misbehaving LATS run is to replay the tree.
- **Uses** V15 LLM-as-Judge — when no programmatic verifier exists, V15 supplies the Value Estimator at the leaves. Calibrate carefully; LATS's quality cap is the value signal's quality.
- **Distinct from** R7 Reflexion — Reflexion retries the same single trajectory with verbal memory of past failures; LATS searches a tree where every rollout updates value estimates for every ancestor. Reflexion is sequential and memory-driven; LATS is branching and statistics-driven.
- **Distinct from** R3 Plan-and-Solve — R3 commits to one plan and replans on failure; R10 maintains a tree of partial plans and lets statistics pick the winner. If the path is genuinely predictable, R3 wins on cost by orders of magnitude.
- **Composes with** R11 Buffer of Thoughts — BoT can supply LATS's root-level action templates from past solved problems, reducing the search depth needed.
- **Pairs with** O17 Agent Isolation — each LATS rollout can run in an isolated sub-agent so the outer trace stays clean and parallel rollouts do not contaminate each other.
- **Note on fundamentality** — R10 is a sibling of R9, not a variant. The Backpropagator is a participant absent from R9; UCB selection with visit counts is a structural move absent from R9; both are load-bearing for LATS's behaviour. They are two patterns at very different points on the cost-quality curve, not one pattern with a parameter knob.

## Sources

- Zhou et al. (2023) — "Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models" (arXiv 2310.04406, ICML 2024).
- Yao et al. (2023) — "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (arXiv 2305.10601) — the sibling pattern.
- Yao et al. (2022) — "ReAct: Synergizing Reasoning and Acting in Language Models" (arXiv 2210.03629) — the inner step.
- Shinn et al. (2023) — "Reflexion: Language Agents with Verbal Reinforcement Learning" (arXiv 2303.11366) — the reflection move folded into the value update.
- Koh et al. (2024) — "Tree Search for Language Model Agents" (arXiv 2407.01476) — follow-on analysis of MCTS-class search for LLM agents.
- LangGraph LATS tutorial — `langchain-ai/langgraph/docs/docs/tutorials/lats/lats.ipynb`.
