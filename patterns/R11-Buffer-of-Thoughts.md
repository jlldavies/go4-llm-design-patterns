# R11 — Buffer of Thoughts

> Maintain a meta-buffer of reusable high-level *thought-templates* distilled from past problems, and for each new problem retrieve the most relevant template and instantiate it — trading expensive per-problem search for amortised reuse of reasoning structure.

**Also Known As:** BoT, Meta-Buffer Reasoning, Template-Augmented Reasoning, Thought-Augmented Reasoning.

**Classification:** Category III — Reasoning · Band III-B Search-structured (sibling of R9 ToT and R10 LATS) · a *reuse* pattern — replaces per-problem search with retrieval of cached reasoning shape.

---

## Intent

Replace re-deriving a reasoning structure on every hard problem with retrieving and instantiating a previously distilled *thought-template*, so the cost of search is paid once across a problem family rather than every problem in it.

## Motivation

R9 Tree of Thoughts and R10 LATS pay for quality with breadth-first or Monte-Carlo search: every new problem incurs a full multi-branch exploration, even when the *shape* of its solution is one the system has solved before. Two failures follow:

- **Reasoning structure is re-derived, not reused.** A problem like "find the value that makes this expression equal to 24" has a recognisable shape — enumerate, combine, check. ToT will re-discover that shape on every instance, branching and pruning from scratch. The *abstract* reasoning skeleton is identical across instances, but ToT has no place to put it.
- **Cost scales with problem count, not problem-family count.** A production system that sees 10,000 Game-of-24 problems pays 10,000 × ToT cost. There is no amortisation: each problem is independent in compute terms.

The mechanistic basis of the cost reduction is storage-type hierarchy (mechanism 9): ToT re-derives structure at inference time, paying O(n²) attention cost over a growing in-context search tree (mechanism 2) on every problem. BoT externalises the structure to a vector store; retrieval is a single lookup that injects a compact template into context (mechanism 10 — the model's weights do not update, so all structural knowledge must be re-injected as tokens), bounding the input token count to the template size rather than a full search tree.

Buffer of Thoughts (Yang et al., 2024) resolves this by introducing a *meta-buffer* of **thought-templates**: high-level, abstract reasoning skeletons distilled from problems already solved. On a new problem, a *problem distiller* extracts its abstract structure; the meta-buffer is searched for the matching template; an *instantiator* binds the template to the concrete problem; the agent reasons through it. A *buffer-manager* updates the meta-buffer as new templates emerge. Reported result: comparable or better accuracy than ToT/GoT at ~12% of the cost on the benchmarks studied, with reported gains of 11% on Game-of-24, 20% on Geometric Shapes, and 51% on Checkmate-in-One.

The pattern's defining claim is asymmetric — like K12 in the memory category but applied to reasoning: *one* expensive search produces a template that buys *many* cheap reasonings. BoT is not a memory pattern (K10 procedural would store an *executable* procedure retrieved by query similarity); it is a search pattern that *replaces* search at runtime with retrieval of a *non-executable reasoning skeleton* requiring binding. That distinction is what earns it its own number.

## Applicability

Use Buffer of Thoughts when:

- the problem stream contains recurring abstract structures (mathematical puzzles, code-generation patterns, planning skeletons);
- ToT or LATS quality is desired but per-problem cost is unacceptable;
- a curation / distillation phase across solved problems is affordable;
- problem-shape is a recognisable feature you (or the LLM) can extract.

Do not use it when:

- problems are genuinely novel and no template will match — use **R9 Tree of Thoughts** or **R10 LATS** directly;
- a single-pass reasoning trace suffices — use **R1 Zero-Shot CoT** or **R2 Few-Shot CoT**;
- the template buffer cannot be maintained (no curation budget, no review loop) — drift and template-rot will degrade quality faster than the savings buy;
- you need adaptive mid-run tool use — use **R4 ReAct**, which BoT cannot replace.

## Decision Criteria

R11 is right when problem-shape recurs, ToT-level quality is needed, and template curation is affordable.

**1. Measure structural recurrence.** On a sample of solved problems, can you (or a clustering LLM) identify ≥ 5 recurring reasoning shapes that cover ≥ 50% of traffic? Below that, the meta-buffer is too sparse to amortise — use **R9** or **R10** per problem.

**2. Compare per-problem cost.** Estimate cost(ToT or LATS per problem) × expected problem count vs cost(distillation + template storage + per-problem retrieval + instantiated reasoning). Threshold: BoT pays back when **traffic ≥ ~10× the number of distinct templates** at reported ~12% ToT cost. Below that, R9/R10 directly is simpler.

**3. Score template quality risk.** Templates compress reasoning structure — a bad template silently degrades every downstream problem that matches it. Build a sample-and-grade loop (Reflexion-style — see **R7**) over the buffer or expect quality drift.

**4. Cost the buffer-manager.** The buffer is not static. New problem shapes appear; old ones generalise or split. Annualise: buffer-manager calls per cycle × cost. If you cannot afford a periodic manager pass, the buffer ossifies and R11 becomes a stale template store — use **K10** procedural memory instead, which has lower curation expectations.

**5. Distinguish from procedural memory.** R11 templates are *non-executable reasoning skeletons* that require binding by an Instantiator before they can be reasoned over. K10 procedural stores *executable procedures* retrieved by query similarity. If your "templates" are actually parameterised procedures the agent can run directly, you want **K10 procedural variant**, not R11.

**Quick test — R11 is the right pattern when:**

- ≥ 5 recurring problem-shapes cover ≥ 50% of traffic, *and*
- per-problem cost of R9 / R10 is unacceptable but their quality is required, *and*
- buffer-manager budget exists to curate templates against drift, *and*
- the system can extract abstract problem structure reliably enough to retrieve the right template.

If shapes do not recur, use **R9 Tree of Thoughts** or **R10 LATS** directly. If the "template" you have in mind is in fact an executable procedure, use **K10 Long-Term Memory (procedural variant)** instead. If a single CoT pass suffices, you do not need search-family patterns at all — use **R1** or **R2**.

## Structure

```
  Offline / continuous:
    Solved problem ──▶ Buffer-Manager ──▶ distil thought-template ──▶ Meta-Buffer
                                                                          │
                                                                          │
  Online (per problem):                                                   │
    New problem                                                           │
        │                                                                 │
        ▼                                                                 │
   Problem Distiller ──▶ abstract structure  ◀─── retrieve by similarity ─┤
        │                                                                 │
        ▼                                                                 │
   Template (skeleton)                                                    │
        │                                                                 │
        ▼                                                                 │
   Instantiator ──▶ binds template to concrete problem                    │
        │                                                                 │
        ▼                                                                 │
   Reasoner ──▶ Answer                                                    │
        │                                                                 │
        └──▶ (if novel / improved structure) ─── update ──────────────────┘
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Problem Distiller** | extracting the abstract reasoning structure from a concrete problem | raw problem → structure descriptor | solve the problem, or fetch templates — it produces only the descriptor used as the retrieval key. A Distiller that also reasons collapses the abstraction layer the pattern depends on. |
| **Meta-Buffer** | the store of thought-templates | structure descriptor → template | hold *executable procedures* (that is K10) or *raw solved problems* (that is K11) — templates are *non-executable reasoning skeletons*, intentionally abstract. |
| **Template Retriever** | similarity search over the meta-buffer | structure descriptor → top-k templates | retrieve by surface-level query similarity. The descriptor space is the retrieval space, not the raw-problem space. |
| **Instantiator (LLM)** | binding a retrieved template to the concrete problem | template + problem → instantiated reasoning plan | freelance — if no template matches well, it must signal *no match* and surrender to fallback, not improvise a template silently. |
| **Reasoner (LLM)** | executing the instantiated reasoning plan | instantiated plan + problem → answer | edit the template; that is the Buffer-Manager's job at curation time. |
| **Buffer-Manager (LLM)** | distilling new templates, generalising, merging, retiring | recent solved problems + current buffer → updated buffer | run on every problem — manager calls are triggered (batch, milestone, periodic). Per-problem manager calls thrash the buffer and erase the cost advantage. |

Six narrow responsibilities. The **Instantiator and Buffer-Manager are kept as separate sessions even when the same model serves both** — the Instantiator binds *once* per problem, the Manager curates *across* problems, and mixing them is the pattern's most common failure mode (mid-solve template edits).

## Collaborations

A problem arrives. The Problem Distiller produces an abstract structure descriptor — the *shape* of the problem, stripped of its surface content. The Template Retriever queries the Meta-Buffer with that descriptor and returns the closest matches. The Instantiator binds the top template to the concrete problem, producing a reasoning plan that names the problem's actual variables and constraints. The Reasoner executes the plan and produces an answer. If the descriptor matches no template well (or the Reasoner fails along the instantiated plan), the system falls back — usually to R9 Tree of Thoughts — and the Buffer-Manager, triggered at the next batch/milestone, distils the new trajectory into a fresh template and updates the meta-buffer. Over time the buffer densifies, retrieval hits improve, and the per-problem cost trends toward instantiation-and-reason rather than full search.

## Consequences

**Benefits**
- Per-problem cost is a fraction of R9/R10 once the buffer is warm (~12% of ToT/GoT reported on the original benchmarks).
- Quality matches or exceeds search-based reasoning on problem families with recurring shape.
- Inspectable, editable templates — operators can audit and curate the reasoning structures the system is using.
- Improvement compounds as more problems are solved: the system becomes faster *and* better on its problem distribution.

**Costs**
- Up-front and ongoing distillation cost — the Buffer-Manager is not free, and a sparse or stale buffer kills the advantage.
- Two extra LLM-shaped steps (Distiller + Instantiator) on the critical path of every problem.
- Template schema is a hard design problem: too rigid and templates don't generalise; too loose and retrieval misses or instantiation drifts.
- Less effective on genuinely novel problems — falls back to R9/R10 cost on cold-buffer hits.

**Risks and failure modes**
- *Template rot* — old templates encode obsolete heuristics or domain assumptions; without retirement, they silently degrade quality on shifted problem distributions.
- *Mis-retrieval* — a superficially-similar template is selected for a problem whose structure differs; the Instantiator binds it anyway and the Reasoner follows a wrong plan confidently.
- *Schema collapse* — templates accumulated without a stable schema degenerate into free-form prose the Retriever cannot rank.
- *Instantiator-as-author* — when the Instantiator improvises a template instead of admitting no match, the buffer's quality control is bypassed.
- *Manager thrash* — too-frequent buffer-manager runs rewrite templates against noise, eroding both quality and any prompt caching downstream. Frequent buffer-manager runs also destroy prompt-caching value (mechanism 5): once a thought-template is stable, it qualifies as a cacheable prefix — the same template content, appearing at the top of every Reasoner call for that template type, can be cached by the provider and read at ~10% of normal input token cost. Manager rewrites invalidate the cached KV state, forcing full recomputation.

## Implementation Notes

- Keep the **Distiller, Retriever, Instantiator, and Buffer-Manager as separate sessions**, even on the same underlying model. Different setups, different prompts, different invocations.
- Trigger the Buffer-Manager *in batches* — end of session, milestone, or N-problem interval — never per problem.
- The descriptor schema is the single largest design lever. Start with a small, fixed-vocabulary descriptor (problem type, key operations, constraint shape); expand only when retrieval misses signal a gap.
- Cap the Instantiator's behaviour with an explicit *no-match* output and a fallback path (R9 ToT or R10 LATS) — silent improvisation is the worst failure mode.
- Pair with **R7 Reflexion** at the buffer level: failed instantiations should produce a verbal critique that becomes input to the next Buffer-Manager pass.
- The Meta-Buffer's *substrate* can be a K10 procedural store — but the templates are content distinct from K10 procedural memory; do not conflate.
- Bound any fallback search (R9 / R10) with **V9 Bounded Execution** — a cold-buffer problem can otherwise cascade arbitrary cost.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** R11 chains a *Problem Distiller* with a *Template Retriever* (a K1-style retrieval over a structured store) and an *Instantiator* over a Meta-Buffer maintained by a separate *Buffer-Manager*. R11 composes with **K1** (template retrieval), **K10** (the meta-buffer can be implemented on procedural-memory infrastructure), **R7** (failed instantiations feed Reflexion-style critique back to the Manager), **R9** or **R10** (fallback on cold-buffer hits), and **V9** (bound that fallback).

**The chain — solve (per problem):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Distil problem to abstract structure descriptor | `LLM` | Distiller session |
| 2 | Retrieve top-k templates by descriptor similarity | `code` | K1 retrieval |
| 3 | Branch — match found → 4; no match → R9 / R10 fallback (bounded by V9) | `code` | R9, R10, V9 |
| 4 | Instantiate template against the concrete problem | `LLM` | Instantiator session |
| 5 | Reason through the instantiated plan | `LLM` | Reasoner session |
| 6 | Emit answer; log trajectory for the Manager | `code` | V14 logging |

**The chain — curate (at trigger):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| C1 | Gather recent trajectories (successes, failures, fallbacks) | `code` | V14 |
| C2 | Buffer-Manager distils, generalises, merges, retires templates | `LLM` | Manager session |
| C3 | Apply edits to the Meta-Buffer | `code` | |

**Skeleton:**

```
solve(problem, buffer):
    structure  = Distiller(problem)                       # LLM
    templates  = buffer.retrieve(structure, k=3)          # code — K1
    if not templates or templates[0].score < tau:         # code
        return fallback_tot_or_lats(problem, V9_bound)    # code — R9/R10 + V9
    plan       = Instantiator(templates[0], problem)      # LLM
    return Reasoner(plan, problem)                        # LLM

curate(trajectory_log, buffer):                           # at trigger only
    edits  = BufferManager(trajectory_log, buffer.index)  # LLM — distil/merge/retire
    buffer.apply(edits)                                    # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Distiller** | small fast generalist | role: *"extract the abstract reasoning structure of a problem; output only a structured descriptor in the fixed schema below"*; the descriptor schema (problem type, operations, constraint shape) | the concrete problem |
| **Instantiator** | the system's main generalist | role: *"bind a thought-template to a concrete problem; if no template matches well, output NO_MATCH"*; the template format; an explicit no-match contract | the retrieved template + the concrete problem |
| **Reasoner** | the system's main generalist | role: *"execute the instantiated reasoning plan step by step; stop and report when an answer is reached or the plan fails"*; output contract | the instantiated plan + the problem |
| **Buffer-Manager** | capable generalist — *Manager quality caps the value of the pattern, like K12's Curator* | role: *"you maintain a meta-buffer of thought-templates"*; the template schema; rules for when to distil a new template, when to merge, when to retire; the current buffer index | the trajectory log since the last curation |

**Specialist-model note.** No fine-tuned specialist is required. Two structural choices change everything:

- The **Buffer-Manager must be a separate session from the Instantiator**, mirroring K12's Curator-vs-Agent split. Mixing them creates the "Instantiator silently authors a new template mid-solve" failure mode.
- A **long-context model** materially helps the Buffer-Manager, which must hold the current buffer plus a window of recent trajectories. The Manager benefits from the strongest available model, paid for in batches.
- The Distiller and Reasoner can be ordinary generalists; the heavy lifting is in the *descriptor schema* and the *template format* — the prompt artifacts, not the model.

## Open-Source Implementations

- **Buffer of Thoughts (official)** — [`github.com/YangLing0818/buffer-of-thought-llm`](https://github.com/YangLing0818/buffer-of-thought-llm) — the canonical implementation; NeurIPS 2024 Spotlight; Problem Distiller, Meta-Buffer, Buffer-Manager, and benchmark harnesses for Game-of-24, Geometric Shapes, Checkmate-in-One and others.

Beyond the official repo, BoT is an emerging research pattern rather than a productised library — there is no LangGraph-style reference flow yet. Practitioners adapt the components into custom loops; the official repo remains the authoritative reference.

## Known Uses

- **Research benchmarks** — Game-of-24, Geometric Shapes, Checkmate-in-One, Word Sorting, BIG-Bench Hard tasks reported in Yang et al. (2024).
- **Template-based reasoning systems** in early production at organisations running large volumes of mathematical puzzle or game-solving workloads where ToT cost is intolerable but ToT quality is the target.
- The *"Something-of-Thought" family* (CoT → ToT → GoT → BoT → SoT, per the Towards Data Science taxonomy) positions BoT as the cost-reduction step in the search-structured reasoning lineage.

## Related Patterns

- **Sibling of** R9 Tree of Thoughts and R10 LATS — same family (search-structured reasoning), different cost-quality trade. R9/R10 search every problem; R11 retrieves the shape of past search.
- **Competes with** R9 / R10 on cost — at ~12% of ToT cost on the original benchmarks, R11 dominates *when problem-shape recurs*. R9/R10 dominate on genuinely novel problems where the buffer is cold.
- **Falls back to** R9 or R10 on no-match — the no-match branch is the pattern's escape hatch and must be present.
- **Composes with** K1 Vanilla RAG — the Template Retriever is a K1-shaped retrieval over the meta-buffer.
- **Composes with** K10 Long-Term Memory (procedural variant) — the meta-buffer can be implemented on K10's infrastructure, but the *content* (non-executable thought-templates) is distinct from K10 procedural's executable procedures.
- **Composes with** R7 Reflexion — failed instantiations produce verbal critique that informs the next Buffer-Manager pass.
- **Composes with** V9 Bounded Execution — fallback search must be capped, or a cold-buffer problem cascades arbitrary cost.
- **Composes with** V14 Trajectory Logging — the Manager reads the trajectory log to distil and retire templates.
- **Distinct from** K10 procedural — K10 stores *executable procedures* retrieved by *query similarity*; R11 stores *non-executable reasoning skeletons* retrieved by *abstract structure similarity* and requiring an Instantiator. Different content, different retrieval key, different read-time mechanism.
- **Distinct from** K12 Karpathy Memory — K12 curates structured *notes* for the Agent to *read*; R11 curates *reasoning templates* for the Reasoner to *execute via the Instantiator*. The Curator-vs-Manager analogy is real, but the artefact and the read mechanism differ.
- **Echoes** R2 Few-Shot CoT in spirit (reuse examples) but differs in abstraction level — R2 reuses concrete exemplars verbatim; R11 reuses abstracted reasoning skeletons retrieved by structure-match.

## Sources

- Yang et al. (2024) — "Buffer of Thoughts: Thought-Augmented Reasoning with Large Language Models" (arXiv 2406.04271, NeurIPS 2024 Spotlight).
- Official implementation: [`github.com/YangLing0818/buffer-of-thought-llm`](https://github.com/YangLing0818/buffer-of-thought-llm).
- Towards Data Science — "Understanding Buffer of Thoughts (BoT) — Reasoning with Large Language Models" (Something-of-Thought taxonomy: CoT → ToT → GoT → BoT → SoT).
- emergentmind.com — paper summary and component breakdown for arXiv 2406.04271.
