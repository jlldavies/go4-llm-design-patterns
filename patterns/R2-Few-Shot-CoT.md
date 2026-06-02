# R2 — Few-Shot CoT

> Put `k` worked examples in the prompt — each one a complete question *with its reasoning steps* leading to the answer — so the model learns from the demonstrations both how to reason about the task and what the answer should look like.

**Also Known As:** Exemplar Chain-of-Thought, Manual CoT, Demonstration-Based CoT, k-Shot CoT. (Auto-CoT and Complexity-Based CoT are *variants* — see Variants.)

**Classification:** Category III — Reasoning · Band III-A Single-pass elicitation · the *demonstrated* sibling of R1 Zero-Shot CoT — same one-call shape, but the reasoning structure is shown rather than triggered.

---

## Intent

Elicit step-by-step intermediate reasoning by *demonstrating* it in a small set of in-prompt examples — `(question, reasoning trace, answer)` triples — so the model both adopts the reasoning style and produces the answer in the demonstrated form.

## Motivation

**R1 Zero-Shot CoT** triggers reasoning with a phrase ("Let's think step by step") and trusts the model to generate something that looks like a reasoning trace. That works on capable modern models for tasks the model has plenty of pre-training exposure to. It fails — or produces inconsistent, malformed, or shallow reasoning — when the reasoning *shape* the task needs is non-obvious: idiosyncratic domain logic, multi-hop arithmetic with a specific solution form, structured derivations with named intermediate quantities, classification with a justification field. Telling the model to think step by step does not tell it *which* steps.

Wei et al. (2022) made the move that defined the pattern: rather than triggering reasoning with a phrase, *demonstrate* it. Put complete worked examples in the prompt — each example carries the question, the chain of intermediate reasoning steps a competent solver would write down, *and* the final answer. The model treats the demonstrations as a runtime spec for two things at once: the reasoning form (what to think about, in what order, at what granularity) and the answer form (where the answer goes, how it is phrased). The paper's headline result — an 8-shot CoT prompt on a 540B model achieves state-of-the-art on GSM8K, surpassing a fine-tuned GPT-3 with a verifier — was the first clean demonstration that reasoning is an *elicitable* capability of sufficiently large models, and the lever that elicits it is *examples that show the reasoning, not examples that show only the answer*. In-context learning with demonstrations is mechanistically grounded in induction-head circuits (Olsson et al., 2022) — two-step attention patterns that perform match-and-copy via the learned bilinear form (mechanism 1): given [A][B]…[A]→[B], the model learns to complete the pattern by attending to prior instances. Few-shot exemplars supply exactly these prior instances; the model's capability is not instruction-following but circuit activation.

The defining force is sharper than S2's. Plain few-shot (S2) demonstrates `input → output`; the examples *are* the spec for the answer's shape. Few-shot CoT demonstrates `input → reasoning → output`; the examples are the spec for the *reasoning's* shape as well. That changes everything about example design: an example with the right answer but the wrong reasoning trace is now *worse* than no example, because the model will dutifully extrapolate the bad reasoning. The cost-quality knob (how many examples, which examples, how detailed the traces) moves from "format coverage" to "reasoning coverage" — the examples must span the kinds of reasoning the task demands, not just the kinds of inputs. R2 is therefore not "S2 with longer examples"; it is a distinct pattern where the labour moves from selecting inputs to *authoring reasoning traces*, and the failure modes (sycophantic reasoning, copied-but-misapplied templates, plausible-but-wrong intermediate steps) follow from that authorship layer.

## Variants

The variants differ in *how the exemplar reasoning traces are produced and selected*:

- **Manual Few-Shot CoT (Wei et al., 2022).** The canonical form. A small fixed set — typically 4–8 — of hand-authored exemplars, each a complete reasoning trace. Maximally controllable; the artefact is human-curated and human-readable; the standard production form. Cache-friendly: the prefix is constant.
- **Auto-CoT (Zhang et al., 2022).** The exemplar reasoning traces are *generated* by **R1 Zero-Shot CoT** on a clustered, diverse set of training questions, then assembled into the few-shot block. Removes the manual authorship cost; trades some trace quality for scale; uses clustering to ensure diversity across the demonstrations. (arXiv 2210.03493.)
- **Complexity-Based CoT (Fu et al., 2022).** Among candidate exemplars, *prefer those with longer / more-step reasoning traces*. The empirical finding: prompting with complex (high-step-count) demonstrations consistently outperforms prompting with simple ones on multi-step reasoning benchmarks. A selection-policy variant, not an authoring one. (arXiv 2210.00720.)
- **Dynamic / Retrieval-Augmented Few-Shot CoT.** Exemplars are retrieved per query from a pool of `(question, reasoning, answer)` triples — typically by similarity to the current question. Inherits the retrieval mechanism from S2's dynamic variant but applies it over reasoning-bearing exemplars. Loses prefix caching; gains per-query reasoning fit.

All four share the structural move — *examples that include reasoning steps drive in-context elicitation of a matching reasoning style*. They differ in whether the traces are authored or generated, and whether they are fixed or selected per query.

## Applicability

Use Few-Shot CoT when:

- R1 Zero-Shot CoT produces inconsistent reasoning shape or shallow reasoning on the target task;
- the task needs a *specific* reasoning form (a named scratchpad layout, a domain-specific derivation, a particular justification structure) that the model will not produce by default;
- 4–8 representative reasoning traces can cover the kinds of inferences the task demands;
- the per-call token cost of carrying those traces is acceptable.

Do not use it when:

- the model is already a "reasoning model" with built-in deliberation (o1, o3, R1, Claude 3.7+ thinking) — these models generate their own reasoning traces; few-shot CoT often hurts more than it helps. Use **R1** or no CoT at all.
- a one-word trigger reliably elicits the right reasoning — use **R1 Zero-Shot CoT**;
- the task is single-step and the answer needs format control only, not reasoning — use **S2 Few-Shot** (examples without reasoning are cheaper and equally effective);
- the reasoning requires *adaptation* mid-step based on observations or tool outputs — use **R4 ReAct**;
- the reasoning needs an inspectable upfront plan before execution — use **R3 Plan-and-Solve**;
- the task is open-ended and there is no comparable "correct reasoning shape" to demonstrate — use **R8 Self-Refine** or **R7 Reflexion** instead.

## Decision Criteria

R2 is right when the *shape* of the needed reasoning is hard to describe but easy to demonstrate, the task has a small set of reasoning archetypes that examples can span, and the token cost of carrying full reasoning traces on every call is acceptable.

**1. Measure R1's failure mode first.** Run R1 Zero-Shot CoT on a labelled test set:

- **Reasoning-shape consistency** — what % of traces follow a usable structure? Below ~80% means demonstration will help.
- **Reasoning depth** — does the model reach the right number of inference steps, or skip key intermediate steps? If it skips, demonstration of complete traces directly fixes this.
- **Final-answer accuracy** — if R1 already achieves the accuracy you need, do not pay for R2.

If R1's reasoning shape is consistent and the accuracy is sufficient, stay on R1. R2's value is precisely in the gap R1 cannot close.

**2. Pick k.** Wei et al.'s headline results used 4–8 exemplars. Most of the gain is captured by **k = 4–6**; beyond k = 8 the returns are typically small and the prompt gets expensive. Start at k = 4 and add only if a held-out gap remains.

**3. Choose the authoring approach.** If you can write ≤10 high-quality exemplars by hand, do — **Manual Few-Shot CoT** is the standard. If hand authorship is the bottleneck, switch to the **Auto-CoT** variant — generated traces are noisier but scale. If you have a corpus of solved problems with varying complexity, prefer the **Complexity-Based CoT** variant — select the longer-trace exemplars from it.

**4. Audit the reasoning traces, not just the answers.** Every example must (a) reach the right answer *via reasoning steps that are themselves correct*, (b) demonstrate the *same kind of reasoning* you want the model to imitate, and (c) avoid leakage — the trace should not encode the final answer through a shortcut the model can copy. A trace that gets the right answer through wrong reasoning is a poison example: the model imitates the wrong reasoning and gets the wrong answer on every novel input.

**5. Test against the inference-time reasoning baseline.** On a frontier reasoning model (o-series, R1, Claude thinking), measure R2 against *no CoT at all*. These models often regress when given few-shot reasoning exemplars — their internal reasoning is stronger than what the exemplars demonstrate, and the exemplars constrain it. If the reasoning model wins without R2, do not use R2.

**Quick test — R2 is the right pattern when:**

- R1 Zero-Shot CoT produces inconsistent or shallow reasoning on this task, *and*
- 4–8 worked exemplars can cover the reasoning archetypes the task needs, *and*
- the per-call token cost of those exemplars is affordable, *and*
- the host model is *not* an inference-time reasoning model whose internal CoT already exceeds the exemplars.

If R1 already produces consistent reasoning, stay on R1. If the host model is a reasoning model, drop CoT exemplars entirely. If the task needs reasoning that *adapts* to tool outputs, switch to **R4 ReAct**. If you need reliability through marginalisation rather than a richer single trace, compose with **R17 Self-Consistency Voting** — sample N R2 chains at temperature > 0 and vote (Wang et al.'s canonical composition).

## Structure

```
  ┌── prompt (static k-shot or per-query dynamic) ───────────────┐
  │                                                               │
  │  Example 1:                                                   │
  │     Q: …                                                      │
  │     A: <reasoning step 1> <reasoning step 2> …                │
  │        The answer is <a₁>.                                    │
  │                                                               │
  │  Example 2:                                                   │
  │     Q: …                                                      │
  │     A: <reasoning steps …> The answer is <a₂>.                │
  │     ⋮                                                          │
  │  Example k:                                                   │
  │     Q: …                                                      │
  │     A: <reasoning steps …> The answer is <aₖ>.                │
  │                                                               │
  │  Q: <live question>                                           │
  │  A:                                                           │
  └───────────────────────────────────────────────────────────────┘
                            │
                            ▼
                  Model generates reasoning + answer
                  (one LLM call, one decode)
                            │
                            ▼
                  Answer extractor pulls the final answer

  The model is expected to imitate the demonstrated reasoning
  shape on the live question before emitting its answer.
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Exemplar pool** | the curated set of `(question, reasoning trace, answer)` triples | curation effort → reusable reasoning exemplars | contain traces that reach the right answer through wrong reasoning — that is the pattern's worst failure mode; the model imitates the bad reasoning and breaks on every novel input. |
| **Trace author** *(human or R1)* | producing the reasoning steps inside each exemplar | a solved question → a correct, step-by-step trace toward its answer | skip steps a human solver would actually write down — the trace must demonstrate the granularity the model should imitate, not a compressed expert shortcut. |
| **Selector** *(static or dynamic)* | choosing which `k` exemplars appear in the prompt for this call | (static: nothing per call) / (dynamic: query → top-k exemplars by similarity / complexity) | shuffle exemplars arbitrarily across calls in the static case (breaks prefix caching); or, in the dynamic case, retrieve by surface similarity that ignores reasoning-archetype coverage. |
| **Prompt assembler** | composing exemplars + the live query into a delimited prompt | exemplars + query → final prompt | confuse the live query with another exemplar — every exemplar needs an unambiguous boundary so the model treats the query as the *new* question to reason about, not one more demonstration to imitate. |
| **Model** | producing a reasoning trace and a final answer in the demonstrated style | full prompt → reasoning + answer | be asked to reason about problems whose archetype the exemplars never demonstrated — extrapolation beyond the demonstrated reasoning forms is where R2 fails silently with plausible-but-wrong traces. |
| **Answer extractor** | pulling the final answer from the generated trace | one completion → one comparable answer | match loosely — the exemplars must end with a structured marker ("The answer is X") so the extractor is a deterministic regex / parser, not a guess. |
| **Evaluator** *(offline)* | scoring whether this exemplar set actually beats R1 (and pure S2) on held-out reasoning | held-out labelled set → accuracy / reasoning-shape metrics | grade only the final answer — must also check whether the *intermediate reasoning* in generated traces matches the demonstrated form, since that is what R2 buys. |

The pattern's quality is dominated by the **Trace author** and the **Exemplar pool**. The Model dutifully imitates whatever reasoning style the exemplars demonstrate; the Selector decides which archetypes are shown; the Answer extractor needs a marker the exemplars must establish. Mis-author the traces and the whole pattern misfires.

## Collaborations

A query arrives. In the **static** case, the Prompt assembler concatenates a fixed block of `(question, reasoning, answer)` exemplars with the live query and ships one prompt; the Model generates a reasoning trace in the demonstrated shape, ending with the final answer; the Answer extractor parses the trace and returns the answer. In the **dynamic** case, the Selector queries the Exemplar pool — by embedding similarity, by reasoning complexity, or both — to fetch the top-k most relevant `(Q, reasoning, A)` triples, then the Prompt assembler composes the per-query prompt; the Model and Answer extractor run as before. Offline, the Trace author (a human or an R1-driven loop in the Auto-CoT variant) maintains the Exemplar pool; the Evaluator runs the current pool against a held-out labelled set and decides whether to keep, rewrite, swap, or expand the exemplars.

R2 composes one level up: **R17 Self-Consistency Voting** wraps the whole assembly — the Prompt assembler builds the R2 prompt once, the Sampler draws N parallel completions at temperature > 0, the Aggregator votes over their extracted answers. That is the canonical Wang et al. 2022 composition.

## Consequences

**Benefits**

- Substantially outperforms standard few-shot (S2) and R1 Zero-Shot CoT on multi-step reasoning when the demonstrated reasoning shape is genuinely informative — the headline finding of Wei et al. 2022.
- Controls both reasoning shape *and* answer format in one prompt; no extra LLM call per query beyond the base generation.
- The exemplar pool is a human-readable, version-controllable artefact — auditable, editable, easier to govern than a fine-tune.
- Composes cleanly with R17 Self-Consistency, S3 Persona, S6 Output Template, and any downstream reasoning pattern that needs a richer single-pass reasoning step.

**Costs**

- Every exemplar consumes context tokens on every call — the prompt is longer than S2's and much longer than R1's. Cost scales linearly with k × trace length; attending over all exemplar K vectors adds to the O(n²) attention cost at each generation step (mechanism 2).
- *Authoring high-quality reasoning traces is real labour*. Unlike S2, where examples are usually direct from labelled data, R2 exemplars must demonstrate *correct intermediate reasoning*, which often requires hand authorship.
- Dynamic selection adds an embedding-lookup step per query and breaks prefix caching — the static exemplar block, held constant across calls, qualifies for provider-level prefix caching (Anthropic: 5-min TTL, minimum 1024 tokens, cache reads at ~10% of normal input token cost, mechanism 5). Dynamic per-query selection means a different prefix on every call, eliminating this cost reduction entirely (mechanism 5 — cache boundary is invalidated by any change to the prefix). On high-volume systems this is a 10× input-token cost increase, not merely a latency increase.

**Risks and failure modes**

- *Poison exemplars* — a trace that reaches the right answer via wrong reasoning teaches the model the wrong reasoning. This is the pattern's worst failure mode: high-confidence wrong reasoning that looks well-formed.
- *Sycophantic reasoning* — the model generates a plausible-looking trace that supports a wrong final answer; the trace's authority comes from the exemplars' form, not from correctness. Surface symptom: confident traces that "show their work" but the work is fabricated.
- *Reasoning template overfit* — the model copies the exemplars' surface form (same scratchpad layout, same numeric variable names) on problems the form does not actually apply to.
- *Reasoning-model regression* — on inference-time reasoning models (o1, o3, R1, Claude thinking), few-shot CoT exemplars often *hurt* — they constrain the model's stronger internal reasoning. Always A/B against no-CoT on these models.
- *Cache loss (dynamic variant)* — selecting exemplars per query means a different prefix on every call, defeating prompt caching's economics on high-volume systems.
- *Drift unmeasured* — the exemplar pool is set once; as inputs shift, the pool silently goes out of date.

## Implementation Notes

- Start at k = 4. Add exemplars only when held-out measurement shows a remaining reasoning-shape gap. Diminishing returns are sharp past k = 6–8.
- Diversity of *reasoning archetypes* matters more than diversity of surface inputs. Five exemplars covering five distinct reasoning patterns beat ten that all reason the same way.
- End every exemplar with the same answer marker ("The answer is X" or `Answer: X`) so the Answer extractor is a deterministic regex. Without this, R2's downstream composition (especially with R17) breaks.
- Prefer **complex** exemplars over simple ones (Fu et al. 2022): traces with more steps consistently outperform terse traces on multi-step benchmarks.
- Author traces at the granularity you want the model to imitate. Expert shortcuts ("by inspection, x = 7") teach the model to assert without working. Pedagogical granularity ("first compute …, then …, therefore x = 7") teaches the model to show work.
- Audit traces *as reasoning*, not just by final answer. A trace that lands on the right answer with a wrong step is a poison example.
- On inference-time reasoning models (o1, o3, R1, Claude thinking), measure R2 against no-CoT *before* deploying. These models often regress under exemplar constraints; if so, use R1 or no CoT.
- For the canonical reliability composition, pair with **R17 Self-Consistency Voting** — sample N R2 chains at temperature 0.7–0.9 and vote.
- For numerical or symbolic tasks, **R14 Program of Thoughts** dominates R2 — delegate computation to an interpreter rather than reasoning about it in natural language.
- Compose with **S6 Output Template** to lock the final-answer field's shape; compose with **S3 Persona** to lock the reasoning *voice* (e.g. "as a careful arithmetic tutor").
- Bound any loop R2 sits inside with **V9 Bounded Execution**; while R2 itself is one call, callers using R2 inside a retry / refine loop need a cap.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring. R2 is one LLM call per query; the work is in the exemplar block that lives in the session's setup.

**Composition:** R2 sits inside the *Setup* slot of a single LLM session — the exemplar block becomes part of the session's setup string. R2 *refines* **R1 Zero-Shot CoT** (R1 triggers reasoning; R2 demonstrates it) and *specialises* **S2 Few-Shot** (S2 demonstrates I/O; R2 demonstrates I→reasoning→O). R2's canonical upward composition is with **R17 Self-Consistency Voting** — Wang et al.'s "CoT × N + vote". For computation-heavy tasks, **R14 Program of Thoughts** displaces R2's natural-language reasoning with code. The **Auto-CoT** variant uses **R1** as the Trace author offline.

**The chain — static k-shot (per request):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Assemble final prompt = fixed exemplar block + live question | `code` | — |
| 2 | Generate reasoning trace + answer | `LLM` | Solver session |
| 3 | Extract final answer from trace | `code` | answer marker contract |

**The chain — dynamic k-shot (per request):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Embed the live question | `code` (or tiny `LLM`) | — |
| 2 | Selector retrieves top-k exemplars from pool | `code` | S2 (dynamic Selector role) |
| 3 | Assemble final prompt = retrieved exemplars + live question | `code` | — |
| 4 | Generate reasoning trace + answer | `LLM` | Solver session |
| 5 | Extract final answer from trace | `code` | answer marker contract |

**The chain — offline (one-time, then on a cadence):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| O1 | Curate or generate `(Q, reasoning, A)` triples | `code` (human) *or* `LLM` | R1 (Auto-CoT) |
| O2 | Pick k and select / order exemplars (favour complex traces) | `code` | Complexity-Based variant |
| O3 | Evaluate on held-out reasoning set against R1 baseline | `LLM` + `code` | V15 LLM-as-Judge optional |
| O4 | Ship the exemplar block; re-evaluate periodically | `code` | — |

**Skeleton:**

```
# Static k-shot CoT — setup-once
EXEMPLARS = load_curated_reasoning_traces(pool, k=4)        # code, one-time
PROMPT_PREFIX = render_cot_block(EXEMPLARS, delimiters,
                                 answer_marker="The answer is")  # code

solve(question):
    prompt = PROMPT_PREFIX + render_query(question)          # code
    completion = generate(prompt)                             # LLM — Solver session
    answer = extract_answer(completion, marker="The answer is")  # code — deterministic regex
    return answer, completion                                  # return trace for audit

# Dynamic k-shot CoT — per-call selection
solve_dynamic(question, pool):
    q_emb     = embed(question)                               # code
    exemplars = pool.top_k(q_emb, k=4,
                           policy="similarity+complexity")    # code — Selector
    prompt    = render_cot_block(exemplars, delimiters,
                                 answer_marker="The answer is") + render_query(question)
    completion = generate(prompt)                             # LLM — Solver session
    return extract_answer(completion, marker="The answer is"), completion

# Auto-CoT trace authoring (offline) — uses R1 to author traces
def author_traces(seed_questions, k=4):
    clusters = cluster_by_embedding(seed_questions)           # code
    picked   = pick_one_per_cluster(clusters)                  # code — diversity
    traces   = [zero_shot_cot_solve(q) for q in picked]        # LLM × |picked| — R1
    return [(q, t.reasoning, t.answer) for q, t in zip(picked, traces)]
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Solver** | any capable generalist (avoid inference-time reasoning models — they often regress under R2; use R1 or no CoT there) | optional role (S3, e.g. *"you are a careful step-by-step problem-solver"*); the curated `k`-shot exemplar block — each exemplar carrying a complete `(Q, reasoning trace, "The answer is X")`; the answer-marker contract; sampling parameters (temperature 0 for single decode; temperature 0.7–0.9 when composing with **R17 Self-Consistency**) | the live question |
| **Auto-CoT Trace author** *(offline only, Auto-CoT variant)* | a capable generalist; an R1 session — *"Let's think step by step"* | role: solver; the R1 trigger phrase; output contract: reasoning + final answer marker | one seed question per call |
| **Evaluator** *(offline only)* | small fast generalist, or **V15 LLM-as-Judge** | role: *"compare the candidate's reasoning trace and final answer to the labelled solution; score reasoning-shape match and final-answer correctness separately"* | the held-out item + the candidate completion |

**Specialist-model note.** No fine-tuned specialist is required — a capable generalist suffices. The pattern's quality lives in the **exemplar block**, not in any model choice. Two specialist *dependencies* may appear at the edges: (a) an **embedding model** in the dynamic variant for similarity-based exemplar selection; (b) optionally **V15 LLM-as-Judge** for offline evaluation of the chosen exemplar set; (c) in the Auto-CoT variant, an **R1 session** acts as the Trace author. The artefact that does the heavy lifting is the curated reasoning-trace block itself, and the authoring effort behind it.

## Open-Source Implementations

Few-Shot CoT is a primitive of every prompting framework — there is no "Wei et al. official CoT repo" because the technique is a prompt convention, not a library. The projects below are the standard references for *managing* CoT exemplars (selection, generation, optimisation) rather than just stuffing them into a string.

- **Auto-CoT** — [`github.com/amazon-science/auto-cot`](https://github.com/amazon-science/auto-cot) — the canonical implementation of the Auto-CoT variant (Zhang et al. 2022); diversity-based exemplar clustering plus R1-driven trace generation.
- **DSPy** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — Stanford's framework. `dspy.ChainOfThought` is the few-shot CoT primitive; `BootstrapFewShot` and `MIPROv2` *compile* CoT exemplar sets from a training signal — the de facto open-source toolkit for engineered R2 prompts.
- **Chain-of-Thought Hub** — [`github.com/FranxYao/chain-of-thought-hub`](https://github.com/FranxYao/chain-of-thought-hub) — Fu et al.'s benchmarking suite for CoT prompting across reasoning tasks; the reference comparison for complexity-based exemplar selection.
- **Chain-of-Thoughts Papers** — [`github.com/Timothyxxx/Chain-of-ThoughtsPapers`](https://github.com/Timothyxxx/Chain-of-ThoughtsPapers) — the canonical reading list and reference index for CoT-family papers and reproductions.
- **Provider cookbooks** — [Anthropic Prompt Engineering — Chain-of-Thought](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/chain-of-thought) and the OpenAI Cookbook reasoning examples ([`github.com/openai/openai-cookbook`](https://github.com/openai/openai-cookbook)) — the practitioner references for how the frontier vendors recommend structuring CoT exemplars on their own models.

## Known Uses

- **GSM8K, MATH, SVAMP, AQuA benchmarks** — Few-Shot CoT is the canonical baseline reported in every multi-step-reasoning paper since Wei et al. 2022; the 8-shot CoT prompt on PaLM-540B was the first state-of-the-art entry on GSM8K to surpass fine-tuning.
- **Production extractors and classifiers with justifications** — when the output must include both a label and a reasoned explanation, 3–6 worked exemplars carrying the explanation form are the standard production approach.
- **DSPy programs in deployment** — `ChainOfThought` modules with `BootstrapFewShot`-compiled exemplars are a default building block.
- **Coding-task evaluation prompts** — few-shot CoT exemplars carrying step-by-step problem-decomposition traces are standard in code-generation benchmarks (HumanEval, MBPP variants) and in production code-assistant prompts.
- **Provider prompt-engineering guides** — Anthropic, OpenAI, and Google all document Few-Shot CoT as a recommended technique; CoT exemplars are the documented default for reasoning-heavy tasks on their respective platforms.

## Related Patterns

- **Refines** R1 Zero-Shot CoT — R1 *triggers* the reasoning via an instruction; R2 *demonstrates* it via exemplars. Same band, same one-call shape; R2 is the controllable upgrade when R1's reasoning shape is inadequate.
- **Refines** S2 Few-Shot — S2 demonstrates `input → output`; R2 demonstrates `input → reasoning → output`. R2 is the reasoning-bearing specialisation of S2; the example artefact is materially different (carries a reasoning trace) and the failure modes (poison reasoning) follow from that.
- **Composes with** R17 Self-Consistency Voting — the canonical Wang et al. 2022 composition: assemble the R2 prompt, sample N completions at temperature > 0, vote over extracted answers. R2 controls *what* to generate; R17 marginalises over *N* attempts at generating it.
- **Composes with** S3 Persona and S6 Output Template — S3 sets the reasoning voice; S6 locks the final-answer shape; R2 supplies the reasoning trace structure. These three Signal-and-Reasoning patterns commonly stack in production prompts.
- **Distinct from** R3 Plan-and-Solve — R3 generates an explicit plan upfront from the prompt itself, then executes; R2 demonstrates a reasoning style via exemplars and produces the reasoning in one decode. R3's plan is an inspectable artefact between two calls; R2's reasoning is generated alongside the answer in a single call.
- **Distinct from** R4 ReAct — R2 reasons in one shot with no observations; R4 interleaves reasoning with tool calls and adapts to their outputs. R2 cannot adapt mid-trace; R4 can.
- **Distinct from** R14 Program of Thoughts — R14 delegates computation to an interpreter; R2 reasons in natural language. On numerical tasks R14 dominates R2 — natural-language arithmetic is unreliable at scale.
- **Competes with** "reasoning-model" zero-shot — on inference-time reasoning models (o1, o3, R1, Claude thinking), R2's exemplars often constrain the model's stronger internal reasoning; on those models, drop R2 in favour of R1 or no CoT at all.
- **Uses** R1 Zero-Shot CoT (in the **Auto-CoT** variant) — R1 acts as the offline Trace author that produces the exemplars R2 then consumes.

## Sources

- Wei et al. (2022) — *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models* (arXiv [2201.11903](https://arxiv.org/abs/2201.11903), NeurIPS 2022). The canonical reference; introduces few-shot CoT and shows the 8-shot PaLM-540B state-of-the-art on GSM8K.
- Zhang et al. (2022) — *Automatic Chain of Thought Prompting in Large Language Models* (arXiv [2210.03493](https://arxiv.org/abs/2210.03493)). The Auto-CoT variant — diversity-based clustering plus R1-driven trace generation.
- Fu et al. (2022) — *Complexity-Based Prompting for Multi-Step Reasoning* (arXiv [2210.00720](https://arxiv.org/abs/2210.00720)). The Complexity-Based CoT variant — prefer longer-trace exemplars.
- Kojima et al. (2022) — *Large Language Models are Zero-Shot Reasoners* (arXiv [2205.11916](https://arxiv.org/abs/2205.11916)). The companion R1 paper; together with Wei et al. it defines the CoT family.
- Wang et al. (2022) — *Self-Consistency Improves Chain of Thought Reasoning in Language Models* (arXiv [2203.11171](https://arxiv.org/abs/2203.11171)). The canonical R2 + R17 composition (CoT × N + vote).
- Anthropic and OpenAI prompt-engineering guides — current vendor-side practitioner references for chain-of-thought prompting on their respective models.
