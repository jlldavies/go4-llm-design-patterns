# S2 — Few-Shot

> Put `k` worked input$\to$output examples into the prompt so the model infers the task — its format, style, and decision boundary — from the demonstrations rather than from instruction alone.

**Also Known As:** In-Context Learning, Exemplar Prompting, k-Shot Prompting, One-Shot (when k = 1). (Dynamic / Retrieval-Augmented Few-Shot is a *variant* — see Variants.)

**Classification:** Category I — Signal · the canonical upgrade from S1 Zero-Shot · a *setup* pattern — the work is in choosing and arranging examples once, not in any per-call logic.

---

## Intent

Demonstrate the task with examples in the prompt, so the model learns the desired format and behaviour from the demonstrations themselves rather than from a description of them.

## Motivation

**S1 Zero-Shot** asks the model to perform a task from instruction alone. For well-defined tasks in formats the model has seen during pre-training (summarise this, translate that, return JSON with these fields), instruction is enough. For anything else — a non-standard output shape, a specific tone, an idiosyncratic classification scheme, a domain-specific reasoning style — instruction in isolation produces inconsistent results, because *describing* a format is harder than *showing* it.

Brown et al. (2020) showed that large language models can pick up a task from a handful of examples in their context window, without any weight update. This is **in-context learning**: the model uses the demonstrations as a kind of runtime "training set" that shapes its next-token distribution. The mechanism is fundamentally different from S1 — instead of relying on the instruction-following circuit, it relies on the model's ability to extrapolate the *pattern* implicit in the examples. Subsequent work (Min et al., 2022) showed that what does the heavy lifting is the *format and distribution* of demonstrations — the label space, the input space, the structure of the input$\to$output map — more than the literal correctness of the labels in the examples.

That insight is the pattern's defining force: **the examples are the specification.** Whatever the examples consistently demonstrate is what the model will produce. This makes example *selection* — not example *count* — the pattern's main design lever. A handful of carefully chosen, distribution-covering demonstrations beats a dozen homogeneous ones, and a single misleading example can bias the entire output stream. The pattern is cheap in calls (zero extra LLM calls per request beyond the base generation) and expensive in tokens (every demonstration rides on every call), so the design problem is *which* examples to include and in *what* order — not whether to include any.

## Variants

The variants differ in *how examples are chosen and assembled*:

- **Static k-shot.** A fixed set of 2–8 examples baked into the prompt, the same for every call. Cheapest to maintain; the standard form; what most production systems use. Cache-friendly: the prefix is constant.
- **One-shot.** k = 1. A single demonstration; the lowest-cost upgrade from S1. Often enough when only the *format* matters (the model already knows the task; it just needs the shape). Brown et al. (2020) treated this as a distinct regime worth measuring.
- **Structured few-shot.** Examples are wrapped in explicit delimiters and labelled fields (`<example>…</example>`, `Input: … Output: …`), removing ambiguity about where each example begins and ends. Reduces "example bleed" — the model treating an example field as part of the current query.
- **Dynamic / Retrieval-Augmented Few-Shot.** Examples are selected *per query* from a pool, typically by similarity to the current input (Liu et al. 2022, "KATE"). Higher quality on diverse query streams; loses prefix caching; adds an embedding lookup step. This composes with K1 Vanilla RAG — the retriever fetches *example demonstrations* rather than knowledge chunks. (Note: this remains S2 because the in-prompt structure and in-context-learning mechanism are unchanged; only example selection moves to runtime.)

All four are the same pattern — *examples in the prompt drive in-context learning* — differing in whether the example set is fixed or selected, and how rigidly it is structured.

## Applicability

Use Few-Shot when:

- the output format is non-standard or uncommon, and S1 produces inconsistent shapes;
- the task involves a specific style, tone, or reasoning pattern the model would not produce by default;
- a small set of representative examples covers the input distribution;
- you can spend the token budget on demonstrations on every call.

Do not use when:

- a one-line instruction reliably produces the right shape — use **S1 Zero-Shot**;
- the output is highly structured (JSON, function-call args) and the runtime offers a structured-output mode — use **S6 Output Template** or the API's structured mode;
- the task is multi-step with intermediate gating — use **S4 Instruction Decomposition** or **O2 Prompt Chaining**;
- you have hundreds of labelled examples and the task is stable — fine-tuning will beat any in-prompt arrangement on cost per call.

## Decision Criteria

S2 is right when the task is hard to *describe* but easy to *demonstrate*, and the token cost of carrying examples is acceptable on every call.

**1. Measure S1's failure mode.** Run S1 on a labelled test set:

- **Format-consistency rate** — what % of outputs match the required shape exactly? Below ~90%, S2 will help.
- **Style match** — does a human rater accept the tone? Below acceptance, S2 with style-bearing examples helps directly.

If both are already high, S2 buys nothing. Stay with S1.

**2. Pick k.** Empirically, 3–5 examples capture most of the benefit; returns diminish past 8; very long contexts can tolerate "many-shot" (dozens to hundreds) but the marginal gain per example is small. Start at k = 3 and add only when measurement shows a remaining gap.

**3. Choose static vs dynamic selection.** If the query distribution is narrow, a fixed k-shot prefix is simpler and cache-friendly. If the query distribution is wide and a single fixed set cannot cover it, switch to the **Dynamic / Retrieval-Augmented Few-Shot** variant — accept the loss of prefix caching in exchange for per-query example fit.

**4. Budget the tokens.** Cost per call $\approx$ k $\times$ example_length + base_prompt. If examples push the prompt past the model's caching threshold or the latency budget, reduce k, compress examples, or fine-tune instead (mechanism 5).

**5. Audit the example set.** Examples must (a) span the input distribution, including hard cases, not just easy ones; (b) be internally consistent — no two examples contradict on shape or labelling; (c) be balanced across classes for classification; (d) be ordered so the last example is *not* an outlier (recency bias is real). A mis-chosen example set is worse than no examples — it teaches the wrong pattern.

**Quick test — S2 is the right pattern when:**

- S1 produces inconsistent format or style on the target task, *and*
- 2–8 representative examples can cover the input distribution, *and*
- the per-call token cost of carrying those examples is affordable, *and*
- the task is not better served by a structured-output API (S6) or fine-tuning.

If S1 already produces the right shape, stay with S1. If the runtime supports structured output and the issue is only format, prefer **S6 Output Template** with the structured-output mode. If the task has hundreds of labelled examples and is stable, fine-tune. If a single fixed example set cannot cover the queries, switch to the **Dynamic** variant.

## Structure

```
  ┌── prompt assembled once (static) or per-query (dynamic) ──┐
  │                                                            │
  │  [optional system / persona]                               │
  │  [optional instruction]                                    │
  │                                                            │
  │  Example 1:  Input → Output                                │
  │  Example 2:  Input → Output                                │
  │     …                                                      │
  │  Example k:  Input → Output                                │
  │                                                            │
  │  Query:      Input → ?                                     │
  └────────────────────────────────────────────────────────────┘
                            │
                            ▼
                     Model generation
                            │
                            ▼
                          Output

  Static k-shot:   example block is constant across calls.
  Dynamic k-shot:  Selector retrieves k examples per query
                   from a pool, then assembles the prompt.
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Example pool** | the curated set of vetted input$\to$output demonstrations | curation effort $\to$ reusable examples | contain contradictions or distribution gaps — a bad pool teaches a bad pattern; vet once, hard. |
| **Selector** *(static or dynamic)* | choosing which `k` examples appear in the prompt | (static: nothing per call) / (dynamic: query $\to$ top-k examples) | reorder examples arbitrarily across calls in the static case — that breaks prefix caching; or, in the dynamic case, select on a similarity signal that ignores label coverage. |
| **Prompt assembler** | composing examples + query into a single, delimited prompt | examples + query $\to$ final prompt string | let the query field be confusable with an example field — every example needs an unambiguous boundary or the model treats the query as another example to imitate. |
| **Model** | inferring the task from the demonstrations and completing it | full prompt $\to$ completion | be asked to produce outputs the example set never demonstrated — extrapolation beyond the demonstrated distribution is exactly where in-context learning is least reliable. |
| **Evaluator** *(offline)* | scoring whether the chosen example set actually beats S1 | held-out labelled set $\to$ format / accuracy / style metrics | rubber-stamp the example set on training cases — it must be measured on held-out data, since examples chosen by inspection often overfit. |

The pattern's quality is dominated by the **Example pool** and the **Selector**. The Model does the work the demonstrations imply; the Prompt assembler is mechanical; the Evaluator is what catches a bad example set before it ships.

## Collaborations

A query arrives. In the **static** case, the Prompt assembler concatenates a fixed example block with the query and ships it; the Model completes against the demonstrated pattern. In the **dynamic** case, the Selector first queries the Example pool — typically by embedding similarity — to fetch the top-k most relevant demonstrations, then the Prompt assembler composes the per-query prompt. Either way, the Model never sees the Selector or pool directly; it sees only the final assembled prompt and learns the task from its structure. Offline, the Evaluator runs the static or dynamic configuration against a held-out labelled set and decides whether to keep the chosen examples, swap them, or change k.

## Consequences

**Benefits**

- Strong format and style control with no fine-tuning and no extra LLM calls per query.
- Works across models and providers; portable.
- The example set is a human-readable, version-controllable artefact — easier to audit than a fine-tune.
- A small number of examples (3–5) typically captures most of the achievable gain.

**Costs**

- Every demonstration consumes context tokens on every call — the cost scales linearly with `k` and example length, but each token also participates in O(n²) pairwise attention over the full prompt (mechanism 2).
- Designing and vetting the example pool is real work, even though no model training is involved.
- Dynamic selection adds an embedding-lookup step per query and breaks prefix caching.

**Risks and failure modes**

- *Bad pool* — examples that contradict, skew toward easy cases, or imbalance the label distribution will teach the wrong pattern; the model dutifully extrapolates the bias.
- *Recency bias* — the last example exerts disproportionate influence; an outlier at position k pulls the model toward it.
- *Example bleed* — without clear delimiters, the model can treat the live query as another example to imitate, or carry over irrelevant fragments of the previous example into its output.
- *Cache loss (dynamic variant)* — selecting examples per query means a different prefix every call, defeating prompt caching's economics on high-volume systems. **Cache cascade destruction (mechanism 5).** Dynamic example selection changes the token sequence of the few-shot block on every call. This does not only forfeit the prefix cache for the few-shot examples themselves — it invalidates the entire prefix that precedes them (system prompt, persona, constraint framing, output template) because the cache key is the exact byte sequence up to the cache boundary. If the dynamic examples are inserted after a 2,000-token stable prefix, dynamic selection causes 2,000 tokens of prefix to be re-prefilled on every call at full cost (~10$\times$ the cache-hit price per token). The economic cost of the dynamic variant is therefore the marginal cost of retrieval plus the full prefill cost of the stable prefix — not just the retrieval overhead. Budget this explicitly. The mitigation: place dynamic examples at the end of the context (after all stable content), so the static prefix can still be cached even if the examples change.
- *Drift unmeasured* — the example set is set once and never re-evaluated; as the input distribution shifts, the set silently goes out of date.

## Implementation Notes

- Start at k = 3. Add examples only when held-out measurement shows a remaining gap. Diminishing returns are sharp after 5–8.
- Diversity beats volume. Five examples covering five distinct sub-cases beat ten examples of the same shape.
- Order matters — put the most representative example *last* (recency bias works in your favour if you place it deliberately). **The geometric basis of recency bias (mechanism 12).** RoPE relative positional encoding makes the attention score between query position $i$ and key position $j$ a function of their relative distance: $s_{ij} = Q_i^T R((j-i)\theta) K_j$. The last example immediately before the query has the smallest offset $|j - i|$ and therefore the least-rotated (strongest) inner product. Placing the most representative example last is not a heuristic — it is exploiting a derivable geometric property of the position encoding. The practical consequence: in a 5-shot setup, the ordering of examples matters more than is commonly recognized, and the difference between placing the best example first vs. last can be measurable in output quality.
- For classification, balance examples across classes; an imbalanced set is read by the model as a prior.
- Use unambiguous delimiters between examples and between the example block and the live query (`<example>…</example>`, `### Example`, or `Input: / Output:` pairs).
- The label correctness of the examples matters less than their format and distribution (Min et al. 2022) — but do not exploit this; correct labels still help and incorrect ones invite drift on adjacent tasks.
- If using the dynamic variant, retrieve by **task similarity** (does this example demonstrate the same sub-pattern?), not pure semantic similarity to the query — the latter retrieves near-duplicates that teach the model to copy rather than generalise.
- Compose with **S6 Output Template** when the demonstrated format is structured — the examples show *what* the fields contain; the template shows *what fields exist*. Together they are tighter than either alone.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring. **Note: S2 is mostly about setup — choosing and arranging the example set — not per-call work.** Static S2 adds zero LLM calls beyond the base generation; dynamic S2 adds one cheap retrieval step (typically not an LLM).

**Composition:** S2 sits inside the *Setup* slot of any LLM session (S1, S3, S6, K1's generator, K5's gates and evaluators, R-category reasoners). The examples become part of the session's setup string. The dynamic variant composes with **K1 Vanilla RAG** — the retriever fetches *examples*, not knowledge chunks — and shares the Selector role with that pattern.

**The chain — static k-shot (per request):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Assemble final prompt = fixed example block + query | `code` | — |
| 2 | Generate | `LLM` | base session |

**The chain — dynamic k-shot (per request):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Embed the query | `code` (or tiny `LLM`) | — |
| 2 | Selector retrieves top-k examples from pool | `code` | K1 (Selector role) |
| 3 | Assemble final prompt = retrieved examples + query | `code` | — |
| 4 | Generate | `LLM` | base session |

**The chain — offline (one-time setup, then on a cadence):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| S1 | Curate example pool from labelled data | `code` (human) | — |
| S2 | Pick k and select / order examples | `code` | — |
| S3 | Evaluate on held-out set vs S1 baseline | `LLM` + `code` | V15 (LLM-as-Judge) optional |
| S4 | Ship the example set; re-evaluate periodically | `code` | — |

**Skeleton:**

```
# Static k-shot — setup-once
EXAMPLES = load_curated_examples(pool, k=4)           # code, one-time
PROMPT_PREFIX = render(EXAMPLES, delimiters)          # code, one-time

answer(query):
    prompt = PROMPT_PREFIX + render_query(query)      # code
    return generate(prompt)                            # LLM — base session

# Dynamic k-shot — per-call selection
answer_dynamic(query, pool):
    q_emb   = embed(query)                             # code (tiny model)
    chosen  = pool.top_k_by_similarity(q_emb, k=4)     # code — Selector
    prompt  = render(chosen, delimiters) + render_query(query)  # code
    return generate(prompt)                            # LLM — base session
```

**The LLM sessions.** S2 itself does not own an LLM session — it provides *example content* that lives in the Setup of whichever session is doing the real work. The table below records this honestly.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Host session (any)** | whatever the host pattern (S1, S3, S6, K1-generator, …) uses | role + instruction + **the k-shot example block** (static case) | the live query (static) — or the live query plus the dynamically retrieved examples (dynamic case) |
| **Evaluator** *(offline only)* | small fast generalist, or V15 LLM-as-Judge | role: *"compare two outputs against a labelled target; score format and content"*; the scoring rubric | the held-out item + the candidate output |

**Specialist-model note.** None — a capable generalist suffices. The pattern's quality lives in the **example pool**, not in any specialist model. Two specialist *dependencies* may appear at the edges: (a) an **embedding model** in the dynamic variant for similarity-based selection, and (b) optionally an **LLM-as-Judge** (V15) for offline evaluation of the chosen example set. Neither is required for the core pattern; the artefact that does the heavy lifting is the curated example block itself.

## Open-Source Implementations

Few-Shot is a primitive of every LLM framework — there is no single canonical project to point to, but the projects below are the standard references for *managing* few-shot examples (selection, storage, optimisation) rather than just stuffing them into a string.

- **DSPy** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — Stanford's framework for programming (not prompting) LLMs; its `LabeledFewShot`, `BootstrapFewShot`, and `KNNFewShot` optimisers are the de facto open-source toolkit for static, bootstrapped, and dynamic example selection.
- **PromptSource** — [`github.com/bigscience-workshop/promptsource`](https://github.com/bigscience-workshop/promptsource) — BigScience's templating toolkit and shared repository of 2,000+ prompts across ~170 datasets; the canonical artefact for *curating* few-shot example sets at scale.
- **LangChain `FewShotPromptTemplate` and `ExampleSelector`** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — production-style abstractions: a few-shot template plus pluggable selectors (length-based, semantic-similarity, MMR) for the dynamic variant.
- **Provider cookbooks** — [Anthropic Prompt Engineering — Multishot Prompting](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/multishot-prompting) and the OpenAI Cookbook examples ([`github.com/openai/openai-cookbook`](https://github.com/openai/openai-cookbook)) — the practitioner references for how a frontier-lab vendor recommends structuring few-shot prompts on its own models.

## Known Uses

- **Production classifiers and extractors** built on commercial APIs almost universally use 3–8 in-prompt examples to lock format and label vocabulary.
- **Anthropic, OpenAI, and Google prompt-engineering guides** all recommend multi-shot prompting as the first upgrade from zero-shot — the pattern is the documented default for non-trivial format tasks across all three.
- **DSPy programs** in deployed systems lean on `BootstrapFewShot` to compile high-quality example sets from a training signal, then ship the compiled few-shot prompt.
- **Coding assistants** (Cursor, Claude Code, Copilot) use few-shot examples of code style and convention — sometimes static, sometimes dynamically retrieved from the user's repo — to align generated code with the local codebase.
- **The dynamic variant** is the standard implementation for support-bot intent classification and for code-completion systems that retrieve similar snippets from the local project as in-context demonstrations.

## Related Patterns

- **Refines** S1 Zero-Shot — Few-Shot is the canonical upgrade from S1 when instruction alone underspecifies the task. S1 is the default; S2 is the first thing to try when S1's output is inconsistent.
- **Pairs with** S3 Persona — persona sets *who* is answering; examples set *how* the answer looks. They compose cleanly.
- **Pairs with** S6 Output Template — the template defines the field skeleton; the examples show realistic content within it. Tighter together than either alone.
- **Composes with** R17 Self-Consistency Voting — S2 controls the format; R17 improves the answer's reliability through sampling and majority vote. Orthogonal: S2 sets *what* to produce; R17 votes over *N* attempts at producing it. Where they touch: R17 may show different answers across samples even when the format is locked by S2 — exactly the point.
- **Competes with** S6 Output Template (structured-output mode) — when the runtime offers a structured-output API, that API beats S2's format-by-demonstration on cost and reliability. Use S2 only for format aspects the API cannot express (style, tone, reasoning shape).
- **Composes with** K1 Vanilla RAG (in the **Dynamic / Retrieval-Augmented Few-Shot** variant) — the same retrieval mechanism, fetching example demonstrations instead of knowledge chunks.
- **Distinct from** fine-tuning — fine-tuning updates weights; S2 updates the prompt. Fine-tuning wins on per-call cost when example sets get large and stable; S2 wins on iteration speed and portability.

## Sources

- Brown et al. (2020) — *Language Models are Few-Shot Learners* (arXiv 2005.14165). The GPT-3 paper that established in-context learning as the foundational mechanism.
- Min et al. (2022) — *Rethinking the Role of Demonstrations: What Makes In-Context Learning Work?* (arXiv 2202.12837). Shows that format and distribution, not label correctness, drive few-shot performance.
- Liu et al. (2022) — *What Makes Good In-Context Examples for GPT-3?* (arXiv 2101.06804). The "KATE" method — retrieval-based selection of in-context examples; the basis for the Dynamic variant.
- Bach et al. (2022) — *PromptSource: An Integrated Development Environment and Repository for Natural Language Prompts* (arXiv 2202.01279).
- White et al. (2023) — *A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT*. The PLoP catalog; few-shot is in the Input Semantics category.
- Anthropic and OpenAI prompt-engineering guides — current vendor-side practitioner references for multi-shot prompting.
