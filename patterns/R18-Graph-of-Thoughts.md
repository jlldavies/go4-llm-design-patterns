# R18 — Graph of Thoughts

> Represent reasoning as a directed graph whose vertices are LLM-generated thoughts and whose edges are *generate*, *refine*, and — uniquely — *aggregate* operations, so partial results from different branches can be merged into a single composite thought that no tree-shaped search can produce.

**Also Known As:** GoT, Graph-of-Thought Reasoning, Graph of Operations (GoO), Thought-Graph Search.

**Classification:** Category III — Reasoning · Band III-D Search-structured reasoning · the *DAG-with-aggregation* member of the search family — generalises **R9 Tree of Thoughts** by adding merge operators that combine sibling thoughts.

---

## Intent

Solve problems whose natural decomposition is not a tree by reasoning over a directed acyclic graph of thoughts in which sub-results can be *aggregated* — merged, sorted, deduplicated, combined — and not only expanded and pruned.

## Motivation

R9 Tree of Thoughts unlocked search over reasoning: branch the next step, score each branch, expand the promising ones, backtrack on dead ends. The structure is a tree, and trees have a hard limitation — a node has exactly one parent. Once two branches have explored partial solutions in parallel, there is no shape in the tree that lets the model take both and combine them. The best ToT can do is pick one branch and discard the other.

For a large class of real problems that is the wrong move. Sorting a long list naturally decomposes into "sort halves, then merge" — the merge is an aggregation of two sub-results, not a child of either. Document summarisation across many sources benefits from drafting several partial summaries in parallel and then *fusing* them. Set operations, multi-source synthesis, voting over candidate answers, code-from-fragments — all of these are graphs, not trees, because the high-value step is combining sibling work, not extending a single line of it. Besta et al. (2023) made the observation precise: model the reasoning trace as an arbitrary directed graph in which *thoughts* are vertices and the *transformations* between them — generate, refine, aggregate — are edges. The graph need not be a tree; in the cases that matter, it must not be.

The unique contribution is the **aggregation operator**: an edge with multiple parents and a single child, executed by an LLM call that consumes the parent thoughts and emits one synthesised thought (mechanism 7 — each aggregator LLM call is a fresh stochastic generation over the combined parent context; the synthesis is not deterministic). ToT cannot represent this edge; R8 Self-Refine has self-loops but no multi-parent merges; R17 Self-Consistency votes over independent samples but does not combine them constructively. Adding aggregation reorganises the search space: the Besta paper reports sorting quality 62% above ToT at >31% lower cost, because divide-and-conquer-with-merge is achievable as a graph and not as a tree. Once aggregation is in the language, the *Graph of Operations* it produces becomes the controller, and the LLM is the engine that executes its vertices.

## Applicability

Use when:

- the problem decomposes into sub-problems whose **sub-results must be combined**, not just chosen between (sort-merge, multi-source synthesis, set operations, multi-shard summarisation);
- a tree-shaped search (R9 ToT, R10 LATS) keeps discarding work that could have been merged;
- the quality gain from fusing partials clearly exceeds the extra LLM cost of running the aggregator;
- you have a way to validate aggregated thoughts (an LLM-judge, a deterministic check, or a structural constraint) so a bad merge does not silently poison the graph;
- the problem is novel enough that no reusable template from **R11 Buffer of Thoughts** applies.

Do not use when:

- the problem is small or linear — use **R1 Zero-Shot CoT** or **R3 Plan-and-Solve**;
- the search shape is genuinely a tree, with no useful merge of sibling thoughts — use **R9 Tree of Thoughts** (simpler) or **R10 LATS** (when MCTS-style value estimation pays);
- the reasoning structure recurs across problems — use **R11 Buffer of Thoughts** (12% of ToT/GoT cost on templated tasks);
- you only need reliability over a single reasoning step — use **R17 Self-Consistency Voting** (parallel samples, vote, much cheaper);
- the answer is a long-form artifact you can outline-and-expand in parallel — use **R12 Skeleton-of-Thought**;
- the budget is tight and a tree-only run hits target quality — the aggregation operator is paid in extra LLM calls.

## Decision Criteria

R18 is right when the natural structure of the problem includes *merging* sibling sub-results, and a tree-only search demonstrably leaves quality on the table.

**1. Test for an aggregation gain.** Run R9 ToT on a small set of problems and inspect the discarded siblings: are there cases where two partial solutions, *combined*, would beat the winner? If yes for **$\geq$ 20%** of cases, aggregation is paying. If almost never, stay on R9.

**2. Quantify the structure.** Sketch the ideal solution shape. Count the operators it needs: *generate* (G), *refine* (R), *aggregate* (A). If A = 0, it is a tree — use R9. If A is small but central (e.g. sort-merge, fuse-summaries), R18 is the right fit. If A dominates and the topology is fixed, consider hand-coding a deterministic Graph of Operations and only calling the LLM at the vertices.

**3. Cost the graph.** Per-problem LLM calls scale roughly as `|V| + |E_LLM|`, where `|E_LLM|` counts aggregate and refine edges (each one LLM call). Aggregator calls are typically the most expensive (long context). Budget upper-bound: **5–15$\times$ a single R1 call** is normal; **>30$\times$** without a clear quality win means the graph is over-engineered.

**4. Pick a controller.** The Graph of Operations can be (a) **author-written** — a deterministic recipe like "split, sort, merge" — or (b) **LLM-planned** — an upstream planning step emits the graph. Author-written is more reliable and the published Besta GoT framework defaults to it; LLM-planned is more flexible but adds a planning failure mode. Default to author-written until you have evidence the topology must vary per input.

**5. Bound the graph (V9).** Hard caps on vertex count, depth, aggregate-edge count, and total LLM cost. Without **V9 Bounded Execution**, an LLM-planned graph can expand without limit. The Besta repo's `Controller` carries these limits explicitly — treat them as required, not optional.

**6. Validate aggregated thoughts.** Aggregation is the new failure surface: a bad merge produces a confident, well-formed wrong thought that downstream operators trust. Pair every aggregator with a validator — a deterministic check where possible (sortedness, set membership, length bound), an **R17** vote over the merge, or **V15 LLM-as-Judge**.

**Quick test — R18 is the right pattern when:**

- the problem decomposes into sub-problems whose **sub-results must be merged**, not chosen between, *and*
- a tree-shaped search (R9) measurably loses to a graph by $\geq$ 20% on quality or cost, *and*
- aggregated thoughts can be validated, *and*
- the per-problem LLM budget tolerates a roughly 5–15$\times$ multiplier over single-shot reasoning.

If sub-results never need to merge, R9 ToT (or R10 LATS for the hardest tree searches) is simpler and cheaper. If the reasoning topology recurs across problems, **R11 Buffer of Thoughts** retrieves a template at ~12% of GoT cost. If you only want robustness over a single CoT step, **R17 Self-Consistency Voting** is the right tool. If the problem is parallel outline-and-expand long-form generation, **R12 Skeleton-of-Thought** is more direct.

## Structure

```
              ┌───────────── Graph of Operations (controller, deterministic) ─────────────┐
              │                                                                            │
              │   Generate                Generate                Generate                 │
   problem ─▶ │  ┌────────┐              ┌────────┐              ┌────────┐                │
              │  │ t1 (G) │              │ t2 (G) │              │ t3 (G) │                │
              │  └───┬────┘              └───┬────┘              └───┬────┘                │
              │      │ Refine               │ Refine                 │                     │
              │      ▼                       ▼                        ▼                    │
              │  ┌────────┐              ┌────────┐              ┌────────┐                │
              │  │ t1'(R) │              │ t2'(R) │              │ t3 (G) │                │
              │  └───┬────┘              └───┬────┘              └───┬────┘                │
              │      └──────┐         ┌──────┘                       │                     │
              │             ▼         ▼                              │                     │
              │           ┌─────────────┐         Aggregate          │                     │
              │           │  t12 (A)    │ ◀───────────────────────────┘ Aggregate          │
              │           └──────┬──────┘                                                   │
              │                  │                                                          │
              │                  ▼                                                          │
              │           ┌──────────────┐                                                  │
              │           │  t123 (A)    │ ◀── final synthesis vertex                       │
              │           └──────┬───────┘                                                  │
              └──────────────────┼──────────────────────────────────────────────────────────┘
                                 ▼
                              answer

   Edges: G = Generate (one LLM call per child)
          R = Refine   (one LLM call; self-improving a thought)
          A = Aggregate (one LLM call; multi-parent → one child)
   The Controller schedules vertex execution, enforces V9 budgets, and routes outputs to a Validator before they feed downstream.
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Graph of Operations (Controller)** | the topology and the schedule | problem + recipe $\to$ DAG of vertices to execute, in dependency order | mix scheduling with thinking — it is deterministic plumbing, never an LLM call itself. |
| **Thought (Vertex)** | one unit of LLM-generated content | parents' content $\to$ this vertex's content | be the controller — it does not decide what comes next; the Graph does. |
| **Generate operator** | producing fresh thoughts from a parent (1 $\to$ k children) | parent thought + instruction $\to$ k new thoughts | aggregate — that is a different edge type. |
| **Refine operator** | improving a thought in place (1 $\to$ 1, self-loop) | thought $\to$ improved thought | merge two siblings — that is Aggregate. |
| **Aggregate operator** | merging multiple parents into one child (m $\to$ 1) | parent thoughts $\to$ one synthesised thought | be invoked without a validator — a bad merge poisons every downstream vertex. |
| **Scorer / Validator** | judging each thought and gating merges | thought (+ context) $\to$ score / pass-fail | rewrite the thought — its job is verdict, not generation. |
| **Budget Guard (V9)** | hard caps on vertices, depth, aggregator calls, total cost | running graph state $\to$ continue / halt | be optional — without it an LLM-planned graph can expand without limit. |

The single feature that distinguishes R18 from every other reasoning pattern is the **Aggregate operator**. Take it out and you have ToT.

## Collaborations

A problem arrives. The Controller instantiates the Graph of Operations — either an author-written recipe (sort: split $\to$ sort chunks $\to$ merge pairs $\to$ final merge) or one emitted by an upstream planner. It walks the graph in dependency order. For each vertex it dispatches the right operator: *Generate* expands a parent into k candidate children with k LLM calls; *Refine* runs one LLM call against a single parent; *Aggregate* gathers the contents of multiple parent vertices into one LLM call that emits a single synthesised child. After every LLM call the Scorer / Validator runs — a deterministic check, an LLM-judge, or an R17 vote — and the Controller marks vertices passed, pruned, or pending re-execution. The Budget Guard counts vertices, aggregator calls, and cost; when any cap trips, the Controller stops expansion and returns the best terminal vertex. The final answer is the content of the graph's sink vertex (or the best-scoring terminal if the topology has multiple sinks).

## Consequences

**Benefits**

- Represents reasoning shapes that trees cannot: merge-style decomposition, multi-source synthesis, sort-and-combine, fan-in.
- Empirically large gains on aggregable tasks — Besta et al. report sorting quality 62% above ToT at >31% lower cost.
- Decouples controller from engine: the Graph of Operations is inspectable, testable, and replayable; the LLM is interchangeable.
- Composes naturally with **V9** (budgets), **V14** (each vertex is a trace point), and **V15** (per-vertex judging).

**Costs**

- More LLM calls than a tree, often substantially more — aggregator vertices are typically long-context. Aggregator calls are expensive because their input context is m parent thoughts concatenated — if each parent is P tokens, the aggregator's prompt is O(m $\times$ P) tokens, and its internal attention computes over O(m $\times$ P)² pairs (mechanism 2). Aggregating 5 thoughts of 200 tokens each means a 1000-token context with O(1M) attention pairs, compared to O(40K) for a 200-token single-parent call. Use the strongest available model for aggregation (mechanism 8) but compress parent thoughts before aggregation.
- Designing or planning a good Graph of Operations is harder than designing a tree-search heuristic.
- Aggregator outputs can hide errors that propagate downstream; validation overhead is real.
- Less cache-friendly than linear or fixed-fan-out patterns — graph branches diverge. Graph branching destroys prefix caching (mechanism 5): two thoughts at the same depth that branched from a common ancestor share the ancestor's prefix but diverge thereafter. Provider caches key on exact prefix match; a diverged prefix is a cache miss. Author-written GoT topologies can preserve a shared stable system prompt prefix above all variable content, capturing partial caching on the stable portion.

**Risks and failure modes**

- *Bad merge cascade* — an unvalidated aggregator silently corrupts every downstream vertex. The dominant failure mode.
- *Topology drift* — an LLM-planned graph expands into shapes the validator and budget were not sized for.
- *Cost runaway* — without V9 budgets, large aggregators chained late in the graph blow the per-problem cost.
- *Over-engineering* — R18 deployed on problems where R9, R11, or R17 would have been adequate, paying many-$\times$ cost for a small win.
- *Validator gap* — no deterministic check exists and the LLM-judge is itself the bottleneck.

## Implementation Notes

- Start author-written. The Besta `graph-of-thoughts` framework expresses the Graph of Operations in code (a `GraphOfOperations` object built from `Generate`, `Improve`, `Aggregate`, `Score`, `ValidateAndImprove`, `KeepBestN` operators). Hand-authored topologies are reliable and cheap to debug.
- Move to LLM-planned graphs only when the topology genuinely varies per input and you have telemetry showing the planning failures are rarer than the gain.
- Validators are not optional on aggregators. Pair every `Aggregate` with a deterministic check, an R17 vote over the merge, or an `LLM-as-Judge` (**V15**) call. Treat unvalidated aggregations as a bug.
- Score every terminal candidate before picking — `KeepBestN(1)` at the sink is the standard last step.
- Use small, fast models for Score/Validate and the strongest available model for Aggregate (long context, complex synthesis).
- Cache aggressively at vertices whose parents have stable content — graph replay is a real cost saver during prompt iteration.
- Log the whole graph (**V14 Trajectory Logging**): vertices, edges, operator type, inputs, outputs, scores. The graph *is* the trace.
- Bound everything (**V9 Bounded Execution**): max vertices, max depth, max aggregator calls, total cost ceiling. Without this an LLM-planned graph can run away.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** R18 wraps an inner reasoning engine (per-vertex prompts are often **R1/R2 CoT**) in a **Graph of Operations** controller; pairs with **V9 Bounded Execution** for budget caps, **V15 LLM-as-Judge** (or **R17 Self-Consistency Voting**) for aggregator validation, and **V14 Trajectory Logging** for per-vertex traces. The vertex prompts are Signal-layer artifacts: a role (S3), the per-operator instruction set (S5), an output contract (S6).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Build (or plan) the Graph of Operations | `code` (or `LLM` if planned) | Planner session (optional) |
| 2 | Topological walk: pick next ready vertex | `code` | |
| 3 | Dispatch by operator type | `code` | |
| 3a | Generate — expand a parent into k children | `LLM` ($\times$ k) | Generate session |
| 3b | Refine — improve a single thought | `LLM` | Refine session |
| 3c | Aggregate — merge multiple parents into one child | `LLM` | Aggregate session |
| 4 | Score / validate the new thought | `LLM` (or rule) | Score session, V15 |
| 5 | Budget check; halt or continue | `code` | V9 |
| 6 | Log vertex and edge | `code` | V14 |
| 7 | When graph drains, pick best sink and return | `code` | |

**Skeleton** — wiring only; each `# LLM` line is a configured session:

```
solve(problem):
    graph = build_graph(problem)              # code — author-written recipe
    # graph = Planner(problem)                # LLM — optional, LLM-planned topology
    budget = V9.budget(max_vertices, max_aggregates, max_cost)
    for v in graph.topological_order():
        parents = graph.parents(v)
        match v.op:
            case GENERATE:
                v.content = [Generate(p, k) for p in parents]   # LLM × k
            case REFINE:
                v.content = Refine(parents[0])                   # LLM
            case AGGREGATE:
                v.content = Aggregate(parents)                   # LLM — multi-parent merge
        v.score = Score(v.content)                              # LLM (or rule) — V15
        V14.log(v)                                              # code
        if not budget.allows(): break                           # code — V9
    return KeepBestN(graph.sinks(), 1)                          # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generate** | strong generalist (the system's main model) | role ("you produce candidate thoughts for the next step"); the problem definition; output contract (one thought per response, format) | the parent thought + the generation instruction |
| **Refine** | strong generalist | role ("you improve a single thought without changing its goal"); rules for what an "improvement" is for this task | the thought to refine |
| **Aggregate** | strongest available, ideally long-context | role ("you merge multiple thoughts into one synthesised thought"); merge rules for this task (sort-merge, fuse summaries, set union, etc.); output contract | the list of parent thoughts |
| **Score / Validate** | small fast generalist *or* a fine-tuned judge | role ("you score a thought against the task criteria"); the rubric; output contract (numeric score or PASS/FAIL) | the thought + context |
| **Planner** *(optional, only if LLM-planned graph)* | strong generalist | role ("you produce a Graph of Operations for this problem"); the operator vocabulary (Generate / Refine / Aggregate / Score); examples; budget ceiling | the problem |

**Specialist-model note.** No fine-tuned specialist is *required* — the Besta reference implementation runs on stock GPT-class models — but two structural choices matter. (a) The **Aggregator benefits materially from a long-context, capable model**: merge quality caps the whole graph's quality. (b) The **Score / Validate session should be a small fast model** so the per-vertex validation does not dominate cost; for stronger validation pair with **R17 Self-Consistency Voting** over the aggregator's output, or swap in **V15 LLM-as-Judge** with a stronger judge model. The aggregation operator is where the pattern earns its keep — under-invest in it and R9 ToT would have been the better choice.

## Open-Source Implementations

- **Graph of Thoughts (official)** — [`github.com/spcl/graph-of-thoughts`](https://github.com/spcl/graph-of-thoughts) — the canonical implementation accompanying Besta et al. (2023); ships a `GraphOfOperations` controller, the `Generate / Improve / Aggregate / Score / ValidateAndImprove / KeepBestN` operator set, the sorting / set-intersection / keyword-counting / document-merging examples from the paper, and pluggable LLM backends. Maintained by ETH SPCL; the AAAI 2024 paper sits in `paper/`.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — general-purpose graph runtime for LLM workflows; not GoT-specific but the natural substrate for hand-authored Graphs of Operations, including cycles, conditional edges, and persistence.
- **Got4ML / community ports** — several community re-implementations on GitHub track the Besta reference; verify activity before adopting. The Besta repo is the authoritative reference.

## Known Uses

- **ETH SPCL benchmarks** — sorting (62% quality over ToT at lower cost), keyword counting, set intersection, document merging — the worked examples in the Besta paper and repo.
- **Multi-source synthesis pipelines** — production RAG/research systems use a GoT-style fan-in/aggregate stage to fuse partial summaries from many retrieved sources before final answer generation.
- **LangGraph production graphs** — author-written DAGs with explicit aggregation nodes are widely used in agentic workflows; the structural pattern is GoT even when the term is not.
- **Research surveys** — Besta et al.'s follow-up "Demystifying Chains, Trees, and Graphs of Thoughts" (arXiv 2401.14295) treats CoT/ToT/GoT as a single family and is the standard reference for choosing between them.

## Related Patterns

- **Sibling of** R9 Tree of Thoughts — the tree-restricted member of the same search family; R18 generalises R9 by adding aggregation edges.
- **Sibling of** R10 LATS — both are search patterns; LATS adds MCTS + value estimation over a tree, R18 adds aggregation over a graph. Pick R10 when value estimation pays; pick R18 when sibling sub-results need merging.
- **Sibling of** R11 Buffer of Thoughts — BoT retrieves a *reusable template* of the reasoning structure (often itself a small graph) at ~12% of GoT cost; R18 builds the graph from scratch per problem. Use BoT when topology recurs.
- **Sibling of** R12 Skeleton-of-Thought — SoT is a fixed two-layer fan-out/fan-in graph (outline $\to$ parallel expansions); R18 is the general DAG.
- **Distinct from** R17 Self-Consistency Voting — R17 votes over independent end-to-end samples; R18 constructs partial thoughts and *merges* them. The merge is the difference.
- **Pairs with** V9 Bounded Execution — required, not optional; without budgets an LLM-planned graph can expand without limit.
- **Pairs with** V15 LLM-as-Judge — the natural validator for aggregator outputs.
- **Pairs with** V14 Trajectory Logging — the graph *is* the trace; log every vertex and edge.
- **Composes with** R1 / R2 Chain of Thought — per-vertex reasoning is typically a CoT prompt.
- **Note on fundamentality** — R18 earns its number because the **aggregation edge** is a structural element no other reasoning pattern represents. ToT (tree) cannot merge siblings; Self-Refine has self-loops only; Self-Consistency votes but does not combine constructively. Remove aggregation from R18 and it collapses into R9.

## Sources

- Besta, M., Blach, N., Kubicek, A., Gerstenberger, R., Podstawski, M., Gianinazzi, L., Gajda, J., Lehmann, T., Niewiadomski, H., Nyczyk, P., Hoefler, T. (2023) — "Graph of Thoughts: Solving Elaborate Problems with Large Language Models." arXiv 2308.09687. Published as AAAI 2024.
- Besta, M. et al. (2024) — "Demystifying Chains, Trees, and Graphs of Thoughts" (arXiv 2401.14295) — the family-level survey covering CoT, ToT, and GoT under one framework.
- spcl/graph-of-thoughts repository documentation — operator semantics (`Generate`, `Improve`, `Aggregate`, `Score`, `ValidateAndImprove`, `KeepBestN`) and the worked sorting / set / document examples.
- Yao et al. (2023) — "Tree of Thoughts: Deliberate Problem Solving with Large Language Models" (arXiv 2305.10601) — the tree predecessor R18 generalises.
