# K9 — Long Context

> Place the entire working set of documents directly into a large context window and let the model attend over all of it, instead of retrieving a selected subset.

**Also Known As:** Context Stuffing, No-RAG, Full-Context Prompting

**Classification:** Category II — Knowledge · Band II-B Context-window management · the architectural alternative to retrieval (Band II-A).

---

## Intent

Make the model's full working knowledge available by loading it all into the context window, trading per-call token cost for the elimination of a retrieval system.

## Motivation

Band II-A exists to solve one problem: the corpus does not fit in the context window, so a subset must be selected. That premise has weakened. Model context windows have grown from a few thousand tokens to hundreds of thousands and beyond. For a large and growing class of tasks the entire relevant working set — a contract, a codebase module, a research dossier, a day of a user's documents — now simply *fits*. When it fits, retrieval is no longer mandatory. It is a choice, and often the wrong one.

RAG's costs are real and recurring: a chunking strategy to tune, an embedding pipeline to run, a vector store to operate, and an irreducible retrieval-miss rate — the passage that holds the answer is sometimes just not in the top-k. Long Context pays none of these. Everything goes in. There is no chunk boundary to split a fact, no retrieval miss, no embedding infrastructure. The model sees the whole working set and synthesises across all of it freely — including the cross-document connections K1 cannot reach and K3 needs a graph to reach.

The cost is the window itself. Tokens are paid on every call, and at long context lengths quality still degrades — the lost-in-the-middle effect persists even when the model's nominal limit is far higher (mechanism 4). And the working set must genuinely fit; Long Context does not scale to millions of documents.

So Long Context is **not the absence of a pattern.** It is a deliberate architectural choice with its own forces: take it when the working set fits a window you can afford, and when avoiding retrieval infrastructure and retrieval misses is worth the per-call token cost. The choice between K1 and K9 is the primary architectural fork of Category II.

## Applicability

Use Long Context when:

- the working set fits comfortably inside a context window you can afford to pay for;
- the task needs free synthesis across the whole set — whole-document QA, full-file code reasoning, cross-document comparison;
- the scale does not justify building and operating retrieval infrastructure;
- prompt caching can amortise the repeated long prefix across many queries.

Do not use it when:

- the corpus is far larger than any window;
- per-call cost at full context length is prohibitive;
- sub-second latency is required — long prefills are slow.

## Decision Criteria

K9 is mostly a sizing exercise — measure, threshold, decide.

**1. Size the working set.** Tokenize the full set you would need in front of the model, using the *target model's own tokenizer*. Call the result **T**.

**2. Compare T to the model's *usable* window.** Usable is lower than nominal — lost-in-the-middle degrades quality well before the model's stated limit (mechanism 4).

| T vs nominal window | Verdict |
|---|---|
| T > nominal | K9 impossible — use K1 (or K3/K4) |
| T > ~50% of nominal | quality degradation likely; benchmark before committing |
| T < ~25% of nominal | K9 comfortable |

**3. Cost the calls.** Per uncached call: `T × input-token-price`. With prompt caching, repeat calls over the same set typically cost 10–25% of the uncached price after the first (provider-specific). For N queries per session over a stable set, total cost $\approx$ `uncached × 1 + cached × (N − 1)`. If N is small the long prefix is paid in full almost every call — that usually breaks the economics.

**Prefix cache mechanics (mechanism 5).** The provider stores the KV state tensor $[L \times n \times n_{\text{kv}} \times d_{\text{head}}]$ of the stable prefix — the portion of the prompt that does not change across requests. Re-submission within the provider TTL (~5 minutes for Anthropic, minimum 1,024 tokens) injects the cached states directly, skipping prefill entirely and reducing cost to ~10% of the normal input token price for the cached portion. Sessions that pause longer than the TTL re-prefill at full cost. Design implication: Long Context is most economical when queries over the same stable document corpus are batched within the TTL window. A stable corpus that is loaded once and queried many times within 5 minutes pays the prefill cost once; the same corpus queried once per hour pays it every time.

**4. Latency check.** Long-context prefill runs hundreds of milliseconds to seconds. Sub-second deadlines eliminate K9.

**5. Growth check.** If the working set grows during the session (an agent accumulating observations, a chat accumulating context, retrieved content piling up), set a hard upper bound on T. K9 fails the moment T crosses the window with no graceful degradation; plan a K1 fallback above the bound.

**Quick test — K9 is the right pattern when:**

- T $\leq$ ~50% of the nominal window, *and*
- queries per session N $\geq$ 5 (so caching amortises the prefix), *and*
- the latency budget tolerates a long prefill, *and*
- T does not grow unboundedly during the session.

If any condition fails, choose K1 or one of its refinements. If T is large *and* the queries demand cross-document synthesis or relationship-tracing K1 cannot reach, choose **K3 GraphRAG** or **K4 RAPTOR** rather than just stuffing the window.

## Structure

```
  Working set (all documents) ──▶ placed entirely into the context window
                                            │
                                            ▼
            [ system prompt + entire working set + query ] ──▶ LLM ──▶ Response

  No index. No retriever. No embedding pipeline.
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Working set** | every document the task may need, in full | — $\to$ working set | exceed the window — silent overflow drops content with no warning. |
| **Context window** | holding the working set and the exchange | working set + query $\to$ prompt | be assumed free — every uncached token is paid on every call. |
| **Generator (LLM)** | attending over the whole set to answer | prompt $\to$ answer | be trusted equally at all positions — mid-context material is used worse (lost-in-the-middle). |

The pattern's signature is the participants it *removes*: no chunker, no embedding model, no vector store, no retriever.

## Collaborations

The whole working set is assembled into the prompt once. Each query is answered against it directly. Where prompt caching is available, the working-set prefix is cached on first use and reused across subsequent queries, so the large prefix is paid for once rather than on every call — this is what makes the pattern economical for repeated queries over a stable set.

## Consequences

**Benefits**
- No retrieval infrastructure, no chunking strategy, no embedding pipeline.
- No retrieval miss — the answer is always in context if it is in the working set.
- Full cross-document synthesis, with no graph or index needed.
- A far simpler architecture; with caching, cheap repeated queries over a stable set.

**Costs**
- Tokens for the entire working set on every uncached call.
- Long prefill latency.
- A hard ceiling at the window size.
- Quality still degrades at extreme context lengths.

**Why the cost is non-linear (mechanism 2).** The prefill cost of processing $n$ tokens scales as $O(n^2)$ in attention compute. Doubling the context quadruples the prefill cost, not doubles it. The 10–25% caching discount applies to the cached prefix only — variable content (the query, dynamic metadata) is always prefilled at full cost. This means the economic break-even for Long Context vs RAG depends on the ratio of stable to variable content, not just total token count.

**Risks and failure modes**
- *Lost in the middle* — material buried mid-context is used poorly even though it is present.
- *Silent overflow* — the working set grows past the window and content is dropped without warning.
- *Cost surprises* — without caching discipline, the per-call token bill is large.

## Implementation Notes

- Prompt caching is what makes Long Context economical for repeated queries over a stable set — design for it deliberately.
- Place the query, and the most important material, at the start or end of the context — not buried in the middle.
- Measure quality at your *actual* context length; do not trust the model's nominal limit.
- Keep a fallback to K1 for when the working set outgrows the window.
- "Long context versus RAG" is an empirical question for your task and corpus — benchmark both rather than assuming.

## Implementation Sketch

> `LLM` = configured session; `code` = wiring.

**Composition:** Almost nothing — assemble the working set, mark it cacheable, query against it. The interesting engineering is the *cache configuration*, not the chain.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Assemble the entire working set as the prompt prefix | `code` | |
| 2 | Mark the prefix as cacheable (provider-specific) | `code` | prompt caching |
| 3 | Send the query; the Generator attends over the whole set | `LLM` | Generator session |

**Skeleton:**

```
long_context_answer(working_set, query):
    prefix = assemble(working_set)                      # code
    return Generator(prefix, query, cache=True)         # LLM
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generator** | **a long-context model** — model capability is a hard build dependency (Gemini 1M+, Claude 200k+, GPT 128k+) | role; *"answer using only the documents below; cite [source] per claim"*; the **entire working set is loaded into the cacheable prefix** so a session of queries over a stable set pays for the long prefix once, not per call | the query (the working set is the loaded-once part) |

**Specialist-model note.** This pattern *is* a specialist requirement at the model layer: a long-context model paired with a working prompt-cache implementation. Without caching, K9's per-call token cost is its defining weakness. Measure both quality *and* cost at your actual context length before committing; quality degrades long before the nominal context limit.

## Open-Source Implementations

Long Context is an architecture, not a library — there is no canonical "Long Context" project. The relevant references are the provider cookbooks:

- **Anthropic Cookbook** — [`github.com/anthropics/anthropic-cookbook`](https://github.com/anthropics/anthropic-cookbook) — prompt-caching recipes that make the long-prefix approach economical.
- **Google Gemini Cookbook** — [`github.com/google-gemini/cookbook`](https://github.com/google-gemini/cookbook) — long-context (1M+ token) workflow examples.

## Known Uses

- Gemini long-context (1M+ token) document and codebase workflows.
- Claude long-context document and full-repository analysis.
- "Paste the whole file or repo" coding workflows.
- The widely-discussed long-context-versus-RAG benchmarking literature.

## Related Patterns

- **Competes with** K1 Vanilla RAG — the K1-versus-K9 decision is the primary architectural fork of the category.
- **Competes with** K3 GraphRAG and K4 RAPTOR — a large window can synthesise and abstract across documents without a pre-built index, at higher per-call cost.
- **Composes with** K6 Context Compression — compress the working set to make it fit a window.
- **Aligned with** K11 Observational Memory — both favour a stable, cacheable context prefix.
- Pairs with prompt caching, an Integration- and Reliability-layer concern.

## Sources

- Long-context-versus-RAG benchmarking literature (2024–2026).
- Model long-context technical reports (Gemini, Claude).
- Liu et al. (2023) — "Lost in the Middle: How Language Models Use Long Contexts."
