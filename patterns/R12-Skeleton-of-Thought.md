# R12 — Skeleton-of-Thought

> Generate an outline of the answer in one call, then expand each outline point in parallel, then aggregate — turning a sequentially-decoded long-form response into a fan-out / fan-in inside a single agent's thinking.

**Also Known As:** SoT, Outline-First Generation, Parallel Decoding via Skeleton. (SoT-R, a router-gated variant, is named in Variants.)

**Classification:** Category III — Reasoning · a *structural* reasoning pattern that shapes the agent's output as outline-then-parallel-expansion; latency-oriented rather than accuracy-oriented.

---

## Intent

Cut end-to-end latency on long-form, structurally separable answers by writing the outline once and expanding every point in parallel, instead of decoding the whole answer token-by-token in a single sequential stream.

## Motivation

Standard LLM generation is strictly sequential: token N depends on token N−1, so a thousand-token answer is a thousand serial decode steps (mechanism 7 — token generation is forward-only stochastic sampling; each emitted token conditions the next). For *short* answers this is fine; for *long-form* answers — reports, essays, technical breakdowns, structured explanations — sequential decoding is the dominant latency cost, and it is wasted work in a specific way: most of the sections in a structured answer do not actually depend on the *content* of the earlier sections, only on the *outline*. A response with sections "definition, history, mechanism, examples, limitations" is five mostly-independent paragraphs concatenated; once the outline is fixed, the model could write them all at once.

Ning et al. (2023) named this: have the model write the skeleton first (one short serial call), then dispatch a parallel call per skeleton point to expand it, then concatenate. The structural decomposition the model would have produced internally is now made explicit, and the slow part — expansion — is parallelised. Across 12 tested LLMs they measured substantial wall-clock speed-ups, and on several question categories the structured outline even nudged quality up because the model is forced to plan before it writes.

The pattern is fundamentally *latency-shaped*, not accuracy-shaped. It does not unlock harder reasoning; ToT and LATS do that. SoT trades a small amount of coherence-risk (sections cannot reference each other's expansions) for a wall-clock win that scales with the number of skeleton points. It belongs in Reasoning because the skeleton-then-expand is a single agent's thinking structure expressed at the prompt level — not a multi-agent orchestration. The sibling at the orchestration level is **O4 Parallelization**; see Related Patterns.

**Why parallel section generation works (mechanism 7 + mechanism 6).** Token generation is forward-only stochastic sampling — each section's content is a function of its preceding tokens, not of other sections being generated in parallel (mechanism 7). When section dependencies are absent (each section is independently specified by the skeleton), parallel generation produces the same result as sequential generation, because each section's token stream conditions only on its own skeleton prompt. Parallel generation achieves the same output as sequential at the wall-clock time of the *slowest* section rather than the *sum* of all sections. Each section is processed in its own bounded LLM call (mechanism 6), preventing cross-contamination between sections while achieving latency reduction proportional to the number of parallel sections.

## Variants

- **Vanilla SoT.** Apply the skeleton-then-parallel-expand template to every query. Universal latency reduction on structurally separable answers; pays the outline-call overhead even on queries that would not have benefited. (Ning et al., 2023.)
- **SoT-R (Router-Gated SoT).** A lightweight router — a fine-tuned RoBERTa classifier in the original work, or a small LLM gate — decides per query whether SoT applies. Queries that genuinely decompose go through the skeleton path; tightly-coupled or short queries skip straight to standard generation. Adds gate overhead but avoids the SoT-on-unsuitable-queries failure mode. (Ning et al., 2023, §SoT-R.)

Both are the same pattern — outline, then parallel expansion — differing only in whether the decision to apply it is universal or per-query.

## Applicability

Use Skeleton-of-Thought when:

- the expected answer is long-form and naturally decomposes into 3+ roughly-independent sections;
- wall-clock latency matters more than incremental accuracy;
- parallel-call budget is available (either parallel API requests or batched decoding on a hosted model);
- coherence *between* sections is not load-bearing — each section can stand on its own given the outline.

Do not use when:

- the answer is short — outline overhead exceeds the savings (use **R1 Zero-Shot CoT** or no reasoning scaffold);
- sections genuinely depend on each other's content, not just the outline — parallel expansion will produce contradictions (use **R3 Plan-and-Solve** for serial planned execution, or **R4 ReAct** for adaptive step-by-step);
- the goal is higher-quality reasoning on a hard problem, not faster decoding of a structured answer (use **R9 Tree of Thoughts** or **R10 LATS**);
- the parallel work is across *independent sub-tasks routed to different agents* rather than sections of one agent's output (use **O4 Parallelization**).

## Decision Criteria

R12 is right when an answer's *outline* fully determines its sections' shape and the latency budget is the binding constraint.

**1. Measure answer length and structure.** On a sample of expected queries, count: average output tokens (T) and average natural section count (S). Practical threshold: **T ≥ ~400 tokens and S ≥ 3** before SoT pays. Below either, the outline-call overhead dominates; use **R1** or no scaffold.

**2. Score inter-section independence.** Take 10 representative answers and ask: could each section be written knowing only the outline and the question? If yes for ≥ 80% of sections, SoT is safe. If sections frequently reference each other's content ("as discussed in section 2, …"), use **R3 Plan-and-Solve** — serial planned execution preserves the cross-references.

**3. Cost the parallelism.** SoT adds: 1 outline call + S parallel expansion calls vs 1 sequential call. Total *tokens* rise modestly (the outline is repeated as context in each expansion). Total *wall time* drops to roughly `outline_time + max(expansion_times)` instead of `sum(expansion_times)`. The win exists only if your serving stack actually parallelises — check before adopting.

**4. Decide on a router.** If your query distribution is mixed (some long-form, some short, some tightly-coupled), the vanilla variant wastes the outline call on the wrong queries. Use the **SoT-R** variant: a small classifier or LLM gate that opts queries in. Threshold: if measured fraction of SoT-suitable queries < ~60%, the router pays.

**5. Bound the expansion fan-out.** Set a cap on skeleton points (`max_points ≈ 5–8`). An ungated skeleton can produce 20+ points and saturate the parallel-call budget. Pair with **V9 Bounded Execution** for the cap and **V13 Tool Budget** if expansions call tools.

**Quick test — R12 is the right pattern when:**

- expected output is long-form (≥ ~400 tokens) and naturally sections into 3+ blocks, *and*
- sections are independent given the outline (no inter-section content dependencies), *and*
- wall-clock latency is the binding constraint, not answer quality, *and*
- the serving stack actually runs the expansion calls in parallel.

If the answer is short or tightly-coupled, choose **R1** or **R3**. If the goal is reasoning quality on a hard problem, choose **R9** or **R10**, not R12 — SoT does not deepen reasoning. If the parallel work is across independent *sub-tasks for different specialists*, lift it to **O4 Parallelization** at the orchestration layer.

## Structure

```
  Query
    │
    ▼
  Outliner (LLM) ──▶ skeleton = [Point 1, Point 2, …, Point S]
    │
    ▼
  Fan-out ──▶ Expander(Point 1)  ┐
              Expander(Point 2)  │  parallel
              Expander(Point 3)  ├──▶ expansions
                  …              │
              Expander(Point S)  ┘
    │
    ▼
  Aggregator ──▶ stitched answer (outline order preserved)
    │
    ▼
  Answer
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Router** *(optional, SoT-R only)* | the per-query decision to apply SoT | query → SoT / DIRECT | answer the query — a router that can also generate has no incentive to ever say "use SoT" honestly. |
| **Outliner** | producing the skeleton | query → ordered list of section headings / point-stubs | expand any point — its job is structure, not content. An outliner that writes prose has already paid the sequential-decode cost the pattern exists to avoid. |
| **Expander** | producing the prose for one point | (outline, point) → section body | look at sibling sections' expansions — that re-introduces sequential dependency and destroys the parallelism. |
| **Aggregator** | stitching the expansions in outline order | ordered expansions → final answer | re-write sections or arbitrate contradictions silently — surface conflicts back to a coherence pass if needed. |
| **Coherence Pass** *(optional)* | smoothing transitions and resolving cross-references | stitched answer → polished answer | expand the content (that was the Expander's call); only adjust seams between sections. |

The Outliner and the Expander are the same model, configured as two distinct sessions. Keeping them separate is what makes the pattern honest — an Outliner allowed to write prose is just a normal generator, and the parallel speed-up evaporates.

## Collaborations

A query arrives. If a Router is configured, it classifies the query; on DIRECT it bypasses SoT and falls through to standard generation. On SoT, the Outliner emits a short ordered list of section points (typically 3–8). The wiring fans out one Expander call per point — same model, expansion-shaped session, given the original query, the full outline (so the Expander knows what its siblings will cover), and the specific point it owns. The expanders run in parallel; their outputs are collected in outline order; the Aggregator concatenates them. An optional Coherence Pass — a single short serial call — smooths transitions and resolves any "as mentioned above" references the expanders could not satisfy in isolation. The bound on `max_points` (V9) keeps the fan-out from running away.

## Consequences

**Benefits**
- Wall-clock latency drops from `O(total tokens)` toward `O(longest section)` plus the outline call.
- Forces the model to plan structure before writing — on some question categories this nudges quality upward as a side-effect.
- Works across many models without fine-tuning; the original paper measured speed-ups across 12 LLMs.
- Cleanly separates structure from content — outlines are inspectable before any expansion runs.

**Costs**
- Total *tokens* rise modestly: the outline is repeated in each expansion's context.
- The Outliner call sits on the critical path before any parallel work can start.
- Requires a serving stack that actually parallelises calls — single-tenant local inference may see no benefit.
- The optional Coherence Pass is a second serial call that erodes part of the saved latency.

**Risks and failure modes**
- *Inter-section incoherence* — Expanders cannot see each other, so cross-references drift or contradict.
- *Over-decomposition* — an ungated Outliner emits 15+ points, saturating parallel budget and producing thin, repetitive sections.
- *Wrong-tool application* — SoT applied to short or tightly-coupled queries pays overhead for nothing.
- *Skeleton hallucination* — the Outliner invents structure ("§4: Recent legal challenges") that the model cannot then fill, producing weak or fabricated sections.
- *Coherence-pass overreach* — a polish pass that rewrites content silently re-introduces sequential dependency and reasoning shifts unaccountably.

## Implementation Notes

- Cap skeleton points (`max_points` 5–8). Outline templates should explicitly request "between 3 and 7 points." Pair with **V9 Bounded Execution**.
- Pass the *full outline* to each Expander, not just its point — siblings' headings give context and reduce overlap.
- Keep Expander sessions short and tightly scoped — "Write ONLY the section for point N. Do not summarise other points." The cleaner the contract, the better the parallelism holds.
- Use SoT-R when query distribution is mixed; a fine-tuned small classifier (the original paper's RoBERTa) is cheap to run and avoids paying the outline cost on unsuitable queries.
- For coherence-critical outputs (legal briefs, academic prose), add the Coherence Pass — but treat it as a *seam smoother*, not a rewriter. Constrain its output contract to "edit transitions only."
- Track per-section token counts; wildly uneven expansions are a signal the outline is poorly balanced and should be regenerated.
- Pair with **K8 Working Memory** if expansions need to share intermediate computation — but be aware that shared state re-introduces dependency and partly defeats the pattern.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** R12 chains an *Outliner* with N parallel *Expander* invocations of the same Expander session, optionally gated by a *Router* (SoT-R variant) and optionally followed by a serial *Coherence Pass*. The fan-out is conceptually similar to O4 Parallelization, but lives inside one agent's reasoning rather than across distinct agents. Pair with **V9** for the points cap and **S6** for the skeleton output template.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Router — should this query use SoT? | `LLM (or rule)` | Router session (SoT-R variant only) |
| 2 | Branch — DIRECT → fall through to plain generation, return | `code` | |
| 3 | Outliner — emit ordered list of skeleton points | `LLM` | Outliner session, S6 output template |
| 4 | Fan-out — dispatch one Expander call per point in parallel | `code` | V9 cap on points |
| 5 | Expander (×S) — produce section body for each point | `LLM` (parallel) | Expander session |
| 6 | Aggregate — concatenate expansions in outline order | `code` | |
| 7 | Coherence Pass — smooth transitions *(optional)* | `LLM` | Coherence session |

**Skeleton** — the wiring; each `# LLM` line is a configured session, not code:

```
skeleton_of_thought(query):
    if Router(query) == DIRECT:           # LLM (or rule) — SoT-R only
        return Generator(query)            # LLM — fall through

    skeleton = Outliner(query)             # LLM — short, serial
    points = parse_points(skeleton)        # code
    points = points[:max_points]           # code — V9 cap

    expansions = parallel_map(             # code — fan-out
        lambda p: Expander(query, skeleton, p),  # LLM — runs in parallel
        points
    )

    stitched = aggregate(skeleton, expansions)   # code — preserve order
    return Coherence(stitched) if needs_polish else stitched  # LLM (optional)
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Router** *(SoT-R only)* | small fine-tuned classifier (RoBERTa in original work) *or* small fast generalist | role ("you decide whether a query produces a long, structurally-separable answer"); criteria; output contract (SoT / DIRECT) | the query |
| **Outliner** | the system's main generalist; small fast models often suffice | role ("you write a short ordered outline; do not write any prose"); output contract (numbered list, 3–7 short points, one phrase each); constraint ("do not expand any point") | the query |
| **Expander** | the system's main generalist | role ("you write one section of an outlined answer"); rule ("you are given the full outline and ONE point; expand ONLY that point; do not restate other points; do not reference siblings by content, only by outline position if needed"); format / length contract | the query + full skeleton + the specific point |
| **Coherence Pass** *(optional)* | small fast generalist | role ("you smooth transitions between sections without rewriting content"); strict edit-only contract | the stitched answer |

**Specialist-model note.** No fine-tuned specialist is required for vanilla SoT — a capable generalist suffices for both Outliner and Expander, and the same model can serve both roles in different sessions. The **SoT-R variant** does benefit from a fine-tuned router (a small classifier such as the RoBERTa router used in the original work) trained on labelled SoT-suitable / unsuitable queries; this can be approximated by a prompted small generalist at lower fidelity. The structural artefact that does the heavy lifting in vanilla SoT is the **Outliner's output template** (S6) — a strict numbered-list contract is what prevents the Outliner from drifting into prose and re-collapsing the pattern back into sequential generation.

## Open-Source Implementations

- **Skeleton-of-Thought (official)** — [`github.com/imagination-research/sot`](https://github.com/imagination-research/sot) — Ning et al.'s reference implementation. Includes the core SoT prompting templates for multiple LLMs, the SoT-R RoBERTa router, evaluation scripts on Vicuna-style benchmarks, and a Gradio demo. MIT licensed.
- **LangChain / LangGraph** — outline-then-expand templates appear in community tutorials and graph examples; the closest match in LangGraph is a parallel-branch graph that fans out from an outline node — not a named "SoT" primitive but the same shape.
- Most production embodiments are bespoke: the pattern is a few hundred lines of fan-out wiring around any chat-completions API that supports concurrent requests. Provider cookbooks (OpenAI, Anthropic) demonstrate the parallel-call mechanics without naming SoT explicitly.

## Known Uses

- **Long-form answer engines** that need sub-second perceived latency on multi-paragraph responses — the outline streams first to the user (giving the impression of immediate structure), and expansions fill in.
- **Report-generation pipelines** in agentic systems — a planning step emits sections; each section is expanded in parallel by the same or different models; the assembled draft enters a review stage.
- **Tutoring / explanation systems** where the outline is shown to the learner as a roadmap before each section is generated.
- **Batched-decoding deployments** of open-source models — SoT exploits per-batch parallelism that single-stream decoding leaves on the table.

## Related Patterns

- **Sibling of** O4 Parallelization — same fan-out / fan-in shape, different layer. O4 parallelises *sub-tasks across distinct agents or specialists*; R12 parallelises *sections of one agent's output*. If the parallel work is independent enough to route to different agents (with different roles, different tools), lift it to O4. If it is one agent expanding sections of its own structured answer, R12 is correct.
- **Distinct from** R3 Plan-and-Solve — both plan first, then execute. R3 executes steps *sequentially* because steps depend on each other's results; R12 executes sections *in parallel* because sections depend only on the outline. R3 for tool-use and action sequences; R12 for long-form text.
- **Distinct from** R9 Tree of Thoughts — ToT explores branching reasoning paths and prunes; SoT commits to one outline and parallelises its expansion. ToT is accuracy-shaped, SoT is latency-shaped.
- **Distinct from** S4 Instruction Decomposition — S4 numbers the steps the model should perform internally; R12 makes the decomposition a runtime fan-out across calls.
- **Composes with** V9 Bounded Execution — cap `max_points` so the Outliner cannot saturate the parallel budget.
- **Composes with** S6 Output Template — the skeleton's strict output contract is what keeps the Outliner from drifting into prose.
- **Pairs with** V15 LLM-as-Judge — a judge can score the stitched output for inter-section coherence, feeding back into the decision to apply the optional Coherence Pass.
- **Note on category placement** — SoT sits in Reasoning because the skeleton-then-parallel-expand is one agent's thinking structure expressed at the prompt level. The line against Orchestration (O4) is thin: if the expansions are routed to different specialists or models, the pattern has crossed into O4. The decision criterion is whether the parallel callees are *the same configured Expander invoked S times* (R12) or *distinct agents with distinct roles* (O4).

## Sources

- Ning, X., Lin, Z., Zhou, Z., Wang, Z., Yang, H., Wang, Y. (2023) — "Skeleton-of-Thought: Large Language Models Can Do Parallel Decoding" (arXiv 2307.15337). Updated and published as "Skeleton-of-Thought: Prompting LLMs for Efficient Parallel Generation" at ICLR 2024.
- Project page and reference implementation — `github.com/imagination-research/sot`.
- Portkey blog summary — "Skeleton-of-Thought: Large Language Models Can Do Parallel Decoding" — short practitioner overview of the speed-up and the SoT-R router.
