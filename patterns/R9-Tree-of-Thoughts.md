# R9 — Tree of Thoughts

> Search a tree of partial-solution states by having the LLM generate candidate next thoughts, evaluate the promise of each, and explore the most promising branches with backtracking — turning one-shot reasoning into deliberate exploration of a solution space.

**Also Known As:** ToT, Deliberate Problem Solving, Branching Reasoning. (No named sub-variants; the paper itself distinguishes BFS and DFS search strategies and value-vs-vote evaluation, but those are configuration choices rather than separate patterns.)

**Classification:** Category III — Reasoning · Band III-D Search-structured reasoning · the *LLM-as-search-engine* pattern — sibling of R10 LATS (the formal MCTS variant) and R11 Buffer of Thoughts (the template-retrieval shortcut).

---

## Intent

Solve problems where the right reasoning path is not obvious upfront by having the LLM expand a tree of candidate partial solutions, score the promise of each, expand the best, and backtrack from dead ends — substituting *search over a structured space* for a single linear chain of thought.

## Motivation

Chain-of-thought (R1, R2) commits to one line of reasoning at the first step and rides it to the end. For easy problems with a single obvious approach, this is fine — the chain is the answer. For *hard* problems with a large solution space — Game of 24, crosswords, creative writing under constraints, planning under uncertainty — the first plausible thought is often wrong, and CoT has no machinery to recover. The model produces a confident, well-structured trajectory that ends at the wrong place, with no signal it should have tried something else (mechanism 7 — token generation is forward-only stochastic sampling; once an intermediate thought is committed, subsequent tokens condition on it and cannot revise it). Add Self-Consistency (R17) on top and you draw N parallel chains; if the model has the same bias on all N, you vote a wrong answer with high confidence.

The deficit is *deliberation*. Humans solving a hard puzzle do not generate a single chain; they generate candidates, look at each, judge which are promising, expand the promising ones, abandon the dead ends, and sometimes come back to a discarded branch. Yao et al. (2023) made this operational: at each reasoning step, ask the LLM for **k candidate next thoughts**, then ask it (or a separate evaluator) to **score** each candidate, then **search** — BFS keeps the top-b thoughts at each level, DFS expands the most promising depth-first with backtracking on failure. The headline result in the paper is striking on tasks where CoT fails by construction: Game of 24 success rate **4% → 74%** for GPT-4, with comparable gains on Creative Writing and Mini Crosswords. The lift is not a percentage point or two — it is a phase change in what the model can do.

The unique contribution is to give the LLM the *deliberate-thinking machinery* that pure forward generation lacks: branching, evaluation, pruning, backtracking. ToT is structurally distinct from its band-mates. **R10 LATS** subsumes ToT conceptually — it is the same idea executed with Monte Carlo Tree Search, a formal value function, and a reflection step — but it is much more expensive and requires more engineering; ToT is the *lightweight, prompt-only* member of the family. **R11 Buffer of Thoughts** moves the same kind of structure *out of inference time* by retrieving pre-distilled thought-templates from a library; it pays at write-time so reads are cheap, where ToT pays at every read. **R17 Self-Consistency** draws independent samples and votes — no evaluation, no branching, no backtracking — it works without structure but cannot recover from a shared bias across samples. ToT sits at a specific point on the cost-quality curve: more expensive than CoT or Self-Consistency, more capable on search-structured problems; cheaper than LATS, less capable when the search demands a formal value function.

The pay-off is bounded by the *evaluator*. The whole pattern reduces to whether the LLM can usefully score partial states — *this branch looks like it can win; that one is a dead end*. When the evaluator is reliable, the search converges; when it is noisy, the search wanders and the cost runs without quality return. The evaluator is the lever, and the part of the pattern most worth tuning.

## Applicability

Use Tree of Thoughts when:

- the problem has a **large search space** where the first plausible reasoning path is often wrong — Game of 24, mathematical puzzles, mini-crosswords, planning under constraints, creative writing with hard constraints;
- you can write a **reasonable evaluator** for *partial* solutions — "this state can plausibly reach a valid solution" or "this state cannot";
- one-shot CoT (R1/R2) demonstrably fails or saturates well below the model's ceiling;
- you can afford **5–50× the LLM calls of CoT** for the lift in quality;
- the problem decomposes naturally into *thought steps* of comparable granularity (so branching has somewhere to land).

Do not use it when:

- a single chain of thought already works — **R1 Zero-Shot CoT** or **R2 Few-Shot CoT** is cheaper and sufficient;
- the failures look like sample noise rather than systematic wrong-path commitments — **R17 Self-Consistency Voting** is cheaper and addresses the right problem;
- the problem is open-ended with no evaluable partial states (free-form essay writing without hard constraints) — **R8 Self-Refine** iterates without needing a partial-state evaluator;
- you need *adaptive tool use during execution* rather than search over reasoning paths — **R4 ReAct** is the right shape;
- you need the highest quality reasoning and can pay for it — **R10 LATS** is strictly more capable on hard search problems;
- the reasoning structure recurs across tasks and a library of templates is feasible — **R11 Buffer of Thoughts** delivers comparable quality at ~12% of ToT's cost;
- token budget is tight — the branching factor multiplies cost and ToT has no mechanism to compress it.

## Decision Criteria

R9 is right when one-shot CoT fails on a search-structured problem, you can score partial states usefully, and you can afford 5–50× CoT's compute for a phase-change in quality.

**1. Confirm CoT actually fails.** Measure single-chain CoT success rate on a labelled set. If R1/R2 already clears your bar, do not pay for ToT. The ToT lift is *huge* on problems where CoT is near zero (Game of 24: 4% → 74%) and *small* on problems where CoT already works. If CoT scores > 60%, the gain may not justify the cost — try **R17 Self-Consistency** first; it is 1/k the price.

**2. Test the evaluator independently.** Before building the loop, write the value/vote prompt and score it on a labelled set of *partial* states ("can this state still reach a valid solution?"). If the evaluator's accuracy is below ~70%, the search will wander and cost will run without quality return — fix the evaluator first, or fall back to **R17**. The evaluator is the pattern's bottleneck.

**3. Set branching factor (k) and beam width (b) — these are the cost knobs.** Yao et al.'s defaults: generate **k = 3–5** candidate thoughts per state, keep **b = 1–5** at each BFS level, search to **depth d = 3–10** steps. Total LLM calls scale roughly as `k × b × d` for generation plus `k × b × d` for evaluation. At k=5, b=5, d=4 you are paying ~200 LLM calls per problem. Pick the smallest k, b, d that achieves the lift on your eval set — bigger trees rarely repay their cost.

**4. Choose BFS or DFS by problem shape.** **BFS** (keep top-b at each level) suits problems where good solutions are at a known depth and you want breadth — Game of 24, structured planning. **DFS** (expand most promising, backtrack on failure) suits problems with variable solution depth and a strong "this state is dead" signal — crosswords, constraint-satisfaction. Both share the same Participants; the Loop controller differs.

**5. Bound the search hard.** Pair with **V9 Bounded Execution** — cap total LLM calls, total expanded nodes, and wall-clock. Unbounded tree search is the pattern's failure mode; a poorly-tuned evaluator on a hard problem will burn the budget. The cap is non-optional. For long searches, also pair with **V10 Checkpointing** so a failed run can be resumed.

**Quick test — R9 is the right pattern when:**

- one-shot CoT (R1/R2) demonstrably fails or saturates well below the model's ceiling on the task, *and*
- the LLM can score partial states with > ~70% accuracy on a labelled probe set, *and*
- the budget tolerates 5–50× CoT cost per problem for the quality lift, *and*
- the problem decomposes into thought-steps of comparable granularity (so branching has somewhere to land).

If CoT already works, choose **R1/R2**. If failures look like sample noise rather than systematic commitments, choose **R17 Self-Consistency Voting**. If you need the strongest possible search and can pay for it, escalate to **R10 LATS**. If the reasoning structures recur across many problems, **R11 Buffer of Thoughts** delivers comparable quality at a fraction of the cost. If the task needs interactive tool use rather than reasoning-path search, the pattern you want is **R4 ReAct**, not R9.

## Structure

```
                                    ┌─ V9 budget: max_nodes, max_calls ─┐
                                    │                                    │
                                    ▼                                    │
   Problem ──▶ Root state                                                │
                  │                                                       │
                  ▼                                                       │
            Thought Generator ──▶ k candidate next thoughts               │
                                       │                                  │
                                       ▼                                  │
                              State Evaluator ──▶ score per candidate    │
                                       │                                  │
                                       ▼                                  │
                              Search controller (BFS keep top-b,          │
                                                  or DFS expand best,    │
                                                  backtrack on fail) ─────┘
                                       │
                       ┌───────────────┴────────────────┐
                       ▼                                ▼
                  expand promising                 prune dead ends
                       │
                       ▼
                  depth d reached?  ──no──▶ loop back to Thought Generator
                       │
                      yes
                       ▼
                  Best leaf ──▶ Final answer
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **State** | the representation of a partial solution at a given tree node | parent state + applied thought → child state | be opaque — the evaluator and the generator both read it, so it must be a textual / structured form the LLM can reason about. A state the LLM cannot inspect breaks the loop. |
| **Thought Generator (LLM)** | producing k candidate next thoughts from a given state | state → k candidate thoughts | judge its own candidates — that is the Evaluator's job. A generator that pre-prunes loses the search's diversity and collapses into a CoT chain. |
| **State Evaluator (LLM)** | scoring the promise of each candidate state — value-style ("can this still win?") or vote-style ("which of these k is best?") | candidate state(s) + problem → score / ranking | generate new thoughts or commit to a final answer; it only judges. The Evaluator is the pattern's bottleneck — its accuracy bounds the search's quality. |
| **Search controller** | the search policy: BFS keep top-b, or DFS expand-best with backtracking | scored frontier + visited set → next state to expand | run unbounded — `V9` budget on nodes / calls / depth / wall-clock is mandatory. A controller without a cap is a runaway tree. |
| **Frontier / visited store** | the search state: open states to expand, closed states already evaluated | reads/writes from controller | drop visited states without recording them — repeated re-evaluation of the same state is the most common silent cost leak. |
| **Solution extractor** | picking the best leaf (or path) when the search terminates | terminal states + scores → final answer + path | rescore states; it returns the best-already-found, not a new judgment. The path back to root is the inspectable trace. |

Six narrow responsibilities. The Generator and the Evaluator are *the same model* in most ToT deployments — the pattern's value comes from using the LLM in *two distinct modes* (proposing vs judging) on the *same problem*, not from having two different models. Keep them as separate sessions even when the model is shared: the proposer prompt asks for diversity, the evaluator prompt asks for discrimination, and mixing them creates the "generator that pre-prunes" failure.

## Collaborations

A problem arrives and becomes the root state. The Search controller takes the root from the frontier and asks the Thought Generator for k candidate next thoughts; the Generator emits them as small textual continuations (a candidate next move, a partial sentence, a branch of the plan). Each candidate yields a child state. The State Evaluator scores each child — either by value (a numeric promise score per state) or by vote (a ranking across the k children). The Search controller applies its policy: in BFS, keep the top-b children and put them on the frontier for the next depth level; in DFS, push children onto a stack, expand the most promising first, and backtrack to the next-best sibling when a branch hits a dead-end signal or depth cap. The frontier / visited store records what has been expanded so the search does not loop. The cycle repeats — generate, evaluate, expand, prune — until the target depth d is reached, a terminal state with a passing evaluator score appears, or the V9 budget (max nodes, max LLM calls, max wall-clock) trips. The Solution extractor returns the best terminal state and the path back to root as the inspectable trace. If the budget tripped without a passing terminal, the extractor returns the best-effort leaf and surfaces the budget event for the caller.

## Consequences

**Benefits**
- Phase-change quality lifts on search-structured problems where CoT is near zero — Yao et al. report Game of 24 GPT-4 success **4% → 74%**, with comparable gains on Creative Writing (coherence by judge) and Mini Crosswords (letter/word success).
- Backtracking *recovers from wrong first steps*, which CoT and Self-Consistency cannot. A pattern that *can* abandon a branch is qualitatively different from one that *commits*.
- The whole tree is *inspectable* — every node has a state, a score, an expansion history. For debugging, evaluation, and trust calibration this is a much richer artefact than a single chain.
- Prompt-only and model-agnostic — no fine-tune required, works with any capable model. The official paper uses GPT-4 stock.
- Tunable on a clear cost axis (k, b, d) — operators can dial cost against quality without changing the pattern.

**Costs**
- **5–50× CoT cost per problem** as a working envelope. At k=5, b=5, d=4 the call count is ~200 per problem (generation + evaluation). The cost is the most-cited reason ToT does not appear in production despite the headline numbers. The cost per call grows with depth, not just call count (mechanism 2 / 3): a node at depth d carries a root-to-node path of d steps as context; the LLM call at depth d pays O(d²) attention cost over that prefix. Total cost scales as k × b × Σᵢ O(i²) over depth, making deep trees disproportionately expensive relative to shallow ones. Budget depth (d) more conservatively than breadth (k) and width (b).
- Latency scales with depth — each level is a sequential step (the next level's candidates depend on the previous level's selected states). Within a level, generation and evaluation across siblings can be parallelised, but depth is on the critical path.
- Engineering surface: the search controller, the frontier/visited store, the budget enforcement, and the evaluator prompt are all real engineering — the pattern is not a one-prompt drop-in.
- Evaluator-bound — if the LLM cannot score partial states reliably, the whole pattern wanders. Many tasks fail this prerequisite quietly.

**Risks and failure modes**
- *Evaluator noise.* The State Evaluator's accuracy bounds the search's quality. A noisy evaluator prunes good branches and expands dead ones; the search wanders and the budget burns without quality return. Symptom: ToT cost is paid but quality matches CoT. Mitigation: probe the evaluator on labelled partial states before building the loop; use a stronger model for the evaluator than the generator if affordable; switch from value-style to vote-style scoring (or vice versa) — Yao et al. found one wins on some tasks, the other on others.
- *Branching collapse.* The Generator's k candidates are paraphrases of the same idea — no real diversity. Symptom: low variance in evaluator scores across siblings. Mitigation: raise generation temperature; explicitly prompt for *distinct* approaches; use Few-Shot demonstrations of diverse candidate sets.
- *Unbounded tree.* Without a hard V9 cap, a hard problem with a noisy evaluator expands a combinatorial tree. The cap is the difference between an expensive pattern and a runaway one.
- *Depth too shallow.* The search reaches max depth before any branch achieves a terminal state. Solution extractor returns a best-effort leaf that is no better than CoT. Tune d on the eval set, not by guess.
- *Visited-set thrashing.* In DFS without a proper visited store, the controller re-expands states it has already evaluated. Silent cost leak — easy to miss in metrics.
- *Wrong pattern for the problem.* ToT is for search-structured problems with a meaningful partial-state evaluator. Applied to free-form generation (essay writing without hard constraints), the evaluator has no useful signal and the cost is wasted; **R8 Self-Refine** is the right shape there.

## Implementation Notes

- The single most-cited deployment is **BFS with k = 3–5, b = 1–5, d = 3–10** — the Game of 24 default. Start there and tune to your task.
- **DFS** suits problems with a strong "this state is dead" signal (constraint violation, hard impossibility) — crosswords, scheduling, Sudoku-like puzzles. BFS suits problems where the solution is at a known depth and pruning by score is the lever.
- Yao et al.'s most actionable tuning result: **vote-style evaluators** (compare k siblings, pick the best) often outperform **value-style evaluators** (score each state in isolation 0–10) on tasks where the absolute score is hard to calibrate but the relative ranking is easy. Try both on a probe set.
- The Generator and the Evaluator are the same model with *different setups*. The Generator's setup asks for diversity ("propose 5 *distinct* next moves"); the Evaluator's asks for discrimination ("rank these 5; explain in one line"). Mixing the prompts is the most common implementation error.
- For latency, parallelise generation and evaluation *across siblings within a level*. Levels themselves are sequential — the next level depends on this level's selection. Within a BFS level, all nodes share the same path-to-root prefix; the only difference in their prompts is the node's own content. This is a prefix-caching opportunity (mechanism 5): a provider like Anthropic can cache the shared stable prefix and re-use its KV state across the entire level's calls, reducing per-call cost by ~90% on the cached portion (mechanism 5 — cache reads at ~10% of normal input token cost). Arrange node prompts so the stable path-prefix appears before the variable node content.
- For cost, an *adaptive* k is a useful win: ask for fewer candidates when the current state's evaluator confidence is high, more when it is low. Not in the original paper, but a common production tweak.
- Always log the full tree — V14 Trajectory Logging is non-optional for ToT, both for debugging the evaluator and for retrospectively diagnosing failed runs.
- Pair with **V9 Bounded Execution** at four levels: max nodes expanded, max LLM calls, max depth, max wall-clock. Any single bound is insufficient; a noisy evaluator can saturate any one of them.
- Consider **V10 Checkpointing** for long searches — a half-built tree is expensive to lose to a transient error.
- If you have a library of past solved problems with their reasoning paths, the cheaper pattern is **R11 Buffer of Thoughts** — retrieve a template rather than searching from scratch. ToT is the pattern that *builds* the templates BoT later reuses.
- For the very hardest problems where ToT still saturates, escalate to **R10 LATS** — formal MCTS, explicit value function, and a Reflexion-style critique on failed trajectories.

## Implementation Sketch

> `LLM = configured session (model + setup + per-call prompt); code = wiring.`

**Composition:** R9 chains a *Thought Generator* (per-state expansion) and a *State Evaluator* (per-state or per-frontier scoring) inside a Search controller (BFS or DFS). The pattern composes with **V9 Bounded Execution** (the budget cap is non-optional), **V14 Trajectory Logging** (the tree *is* the inspectable artefact), **O4 Parallelization** (siblings within a level can be expanded and evaluated in parallel), and optionally **S2 Few-Shot** in the Generator's setup to demonstrate diverse candidate sets. The Solution extractor's path-back-to-root is what downstream systems consume; **S6 Output Template** constrains its shape.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Pop next state from frontier (BFS level / DFS top-of-stack) | `code` | |
| 2 | Generator proposes k candidate thoughts from this state | `LLM` | Generator session |
| 3 | Apply each thought to the state → k child states | `code` | |
| 4 | Evaluator scores each child (value-style or vote-style) | `LLM` | Evaluator session |
| 5 | Search controller picks which to keep (BFS top-b / DFS push-best) | `code` | |
| 6 | Record expansions in frontier / visited store | `code` | V14 |
| 7 | Check budget (V9: max nodes / calls / depth / wall-clock) | `code` | V9 |
| 8 | If terminal state passes evaluator threshold → extract solution | `code` | |
| 9 | Else if budget exhausted → return best-effort leaf | `code` | V9 |
| 10 | Else loop to 1 | `code` | |

**Skeleton** — the wiring only; each `# LLM` line is a configured session (specified below):

```
tree_of_thoughts(problem, k=5, b=5, d=4, max_nodes=200):
    root = State(problem)
    frontier = [root]                                       # code  — BFS-flavoured; DFS swaps to a stack
    best = root
    nodes_expanded = 0
    for depth in range(d):                                  # V9 — depth bound
        next_frontier = []
        for state in frontier:
            thoughts = Generator(state)                     # LLM   — Generator session, returns k thoughts
            children = [state.apply(t) for t in thoughts]   # code
            scores   = Evaluator(state, children)           # LLM   — Evaluator session (value or vote)
            next_frontier += zip(children, scores)
            nodes_expanded += len(children)
            if nodes_expanded >= max_nodes: break           # V9 — node-count bound
        next_frontier.sort(by_score, descending=True)
        frontier = [s for s, _ in next_frontier[:b]]        # keep top-b
        best = max(best, frontier[0], key=score)
        if best.is_terminal_pass(): return best.path        # success exit
    return best.path                                        # V9-bounded best-effort
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generator** | capable generalist; same model as Evaluator works, *higher temperature* than the Evaluator | role: *"you propose k distinct candidate next thoughts from the given partial solution; each candidate is a small, self-contained continuation; do not solve the whole problem"*; output contract (numbered list, one thought per line); few-shot demonstrations of *diverse* candidate sets where available (S2) | the current state + the problem statement |
| **Evaluator** | capable generalist; **ideally the same model used for Generator but in a separate session at lower temperature**, or a stronger model if the evaluator is the bottleneck | role: *"you score the promise of partial solutions"*; the **scoring rubric** (value-style: "0–10, can this state still reach a valid solution?"; vote-style: "given these k siblings, pick the most promising and explain in one line"); output contract (score or rank, terse justification) | the parent state + the candidate child state(s) + the problem statement |
| **Solution extractor** *(optional `LLM`; often `code`)* | small fast generalist *or* deterministic code | role: *"return the final answer derived from this path"*; output contract (S6) | the terminal state + the path back to root |

**Specialist-model note.** No fine-tuned specialist is required by the pattern itself — Yao et al.'s headline numbers are on stock GPT-4 for both the Generator and the Evaluator. Two structural choices change everything:

- **Generator and Evaluator are separate sessions, even when the same model serves both.** The Generator's setup asks for diversity (high temperature, "propose distinct candidates"); the Evaluator's asks for discrimination (low temperature, "rank these and justify"). Collapsing the two prompts into one — "propose and score" — is the most common implementation error and silently collapses ToT into Self-Consistency with extra steps.
- **The Evaluator is the bottleneck.** If you can only afford one stronger model in the loop, spend it on the Evaluator, not the Generator. Yao et al.'s ablations show evaluator quality dominates; a noisy evaluator wastes any generation gain. The prompt artefact doing the heavy lifting is the **scoring rubric** — vote-style vs value-style is a real choice, not a stylistic one; probe both on a labelled set before committing.

## Open-Source Implementations

- **Tree of Thoughts (official)** — [`github.com/princeton-nlp/tree-of-thought-llm`](https://github.com/princeton-nlp/tree-of-thought-llm) — Yao et al.'s NeurIPS 2023 reference implementation (also accessible at `ysymyth/tree-of-thought-llm`). Runnable code for Game of 24, Creative Writing, and Mini Crosswords with BFS, DFS, value-style and vote-style evaluators. The source of every reported number. MIT licensed.
- **Plug-and-play ToT** — [`github.com/kyegomez/tree-of-thoughts`](https://github.com/kyegomez/tree-of-thoughts) — a widely-used (4.6k+ stars) generalised implementation: pluggable models, BFS/DFS search algorithms, `TotAgent` / `ToTDFSAgent` classes. Less faithful to the paper than the Princeton repo but easier to drop into a new task.
- **Tree-of-Thought prompting** — [`github.com/dave1010/tree-of-thought-prompting`](https://github.com/dave1010/tree-of-thought-prompting) — a *pure-prompting* approximation: a single prompt asks the model to simulate the multi-expert deliberation rather than running an actual tree. Much cheaper, much less powerful — useful for cases where the full ToT cost is unaffordable but CoT is too weak.
- **Tree-of-Thought puzzle solver** — [`github.com/jieyilong/tree-of-thought-puzzle-solver`](https://github.com/jieyilong/tree-of-thought-puzzle-solver) — a Sudoku-style ToT implementation with a prompter agent, checker module, memory module, and ToT controller; a clean reference for the controller / store / evaluator split when adapting ToT to a constraint-satisfaction task.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — tutorial-level Tree-of-Thoughts graphs appear in the LangGraph ecosystem (the framework's Send-API map-reduce pattern is the natural fit for the per-level expansion). A common production starting point for ToT-shaped agents.

## Known Uses

- **Game of 24, Creative Writing, Mini Crosswords** (the paper benchmarks) — the canonical demonstrations and the source of every reported quality lift.
- **Mathematical reasoning agents** — research and educational systems on problems where CoT plateaus and a partial-state evaluator can be written (proof search, equation manipulation).
- **Constraint-satisfaction agents** — puzzle solvers (Sudoku-style, scheduling, routing) where DFS with backtracking on hard infeasibility is the natural fit.
- **Creative-writing agents under hard constraints** — long-form generation where each paragraph is a thought node, the evaluator scores coherence and constraint-satisfaction, and the search keeps the best branch.
- **LangGraph and LangChain tutorial agents** — ToT-shaped reference graphs in framework documentation; common starting point when teams need search-structured reasoning without committing to LATS-level engineering.

## Related Patterns

- **Sibling of R10 LATS** — same family (search-structured reasoning), strictly more capable, much more expensive. LATS executes the same idea with Monte Carlo Tree Search, a formal value function, and a Reflexion-style critique on failed trajectories. R9 is the *prompt-only* member; R10 is the *MCTS-with-reflection* member. Escalate from R9 to R10 when R9 saturates on a hard problem and the budget allows; do not start at R10.
- **Sibling of R11 Buffer of Thoughts** — same family, different time-cost axis. BoT pays once at write time to distil thought-templates into a buffer; R9 pays every time at read time. BoT achieves comparable quality at ~12% of R9's cost *on tasks where templates recur*; R9 wins on novel problems with no prior template. R9 produces what BoT later reuses.
- **Distinct from R17 Self-Consistency Voting** — R17 draws N *independent* samples and votes; R9 *searches* a structured space with evaluation and backtracking. R17 has no evaluator and no memory across samples; R9 has both. R17 is cheaper and addresses sample noise; R9 is more expensive and addresses systematic wrong-path commitments. Different deficits, different fixes — they can compose (vote over N samples within each ToT leaf), though it is unusual.
- **Distinct from R4 ReAct** — R4 interleaves reasoning and *tool use* with a single forward chain; R9 searches *reasoning paths* without tool use as a primitive. ReAct is for exploratory tool-using agents; ToT is for deliberate reasoning over a structured solution space. They compose: ToT's nodes can themselves be ReAct loops when the per-step expansion needs a tool call.
- **Distinct from R3 Plan-and-Solve** — R3 generates *one* plan and executes it (with replan on failure); R9 generates *many* candidate plans at each step and searches over them. R3 commits early; R9 deliberates.
- **Composes with R1 / R2 CoT** — the Generator's per-state output is itself a small chain-of-thought. The thoughts are the unit of branching; CoT-style reasoning lives inside each thought.
- **Composes with O4 Parallelization** — siblings within a search level can be generated and evaluated in parallel. This is the main latency lever for ToT in production.
- **Pairs with V9 Bounded Execution** — non-optional. Cap nodes, calls, depth, and wall-clock; any single bound is insufficient. Without V9, ToT is a runaway tree.
- **Pairs with V14 Trajectory Logging** — the tree *is* the inspectable artefact; every node, score, and pruning decision should be logged. This is also how you diagnose evaluator noise after the fact.
- **Pairs with V10 Checkpointing** — for long searches a half-built tree is expensive to lose to a transient error.
- **Composes with V15 LLM-as-Judge** — the State Evaluator is a V15 judge specialised to partial states. The judge's quality bounds the search.
- **Lineage** — the "Something-of-Thought" family runs CoT (R1/R2) → ToT (R9) → GoT (R18 Graph of Thoughts) → BoT (R11) → SoT (R12). Each adds either structure or efficiency to the reasoning chain; ToT is the first that introduces *search and backtracking*.

## Sources

- Yao et al. (2023) — "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (arXiv [2305.10601](https://arxiv.org/abs/2305.10601); NeurIPS 2023). The canonical reference. Key results: Game of 24 GPT-4 4% → 74%; comparable lifts on Creative Writing and Mini Crosswords.
- Long (2023) — "Large Language Model Guided Tree-of-Thought" (arXiv [2305.08291](https://arxiv.org/abs/2305.08291)). A near-contemporaneous, independent formulation; useful as a cross-check on the core idea.
- Besta et al. (2024) — "Demystifying Chains, Trees, and Graphs of Thoughts" (arXiv [2401.14295](https://arxiv.org/abs/2401.14295)). The survey that situates ToT in the wider Something-of-Thought family; the source for the BoT/GoT/SoT cost comparisons.
- Zhou et al. (2023) — "Language Agent Tree Search Unifies Reasoning, Acting, and Planning in Language Models" (arXiv [2310.04406](https://arxiv.org/abs/2310.04406); ICML 2024). The R10 LATS paper; the formal MCTS-plus-reflection extension of ToT.
- Yang et al. (2024) — "Buffer of Thoughts: Thought-Augmented Reasoning with Large Language Models" (arXiv [2406.04271](https://arxiv.org/abs/2406.04271)). The R11 BoT paper; the template-retrieval shortcut on the same family.
- Princeton NLP — `tree-of-thought-llm` repository documentation and the official BFS/DFS, value/vote configurations referenced in the paper.
