# K6 — Context Compression

> When the context window fills, replace stretches of it with shorter summaries — trading fidelity for space so the task can continue.

**Also Known As:** Conversation Compression, History Summarisation, Context Summarisation, Compaction

**Classification:** Category II — Knowledge · Band II-B Context-window management · a *subtractive* in-flight curation pattern; the lossy counterpart of K7 Context Pruning.

---

## Intent

Keep a long-running task within the context window by summarising older or bulky content into a denser form, preserving as much of its information as the reclaimed space allows.

## Motivation

Any task that runs long enough — a multi-turn conversation, an agent loop, a document pass — accumulates context. The window is finite, cost is linear in tokens, and quality degrades non-linearly as the window fills. Sooner or later the accumulated context will not fit, or fits but degrades the model. Something must be removed.

**The mechanistic account (mechanism 4 + mechanism 2).** Quality degrades non-linearly because: (1) the $O(n^2)$ attention compute spreads probability mass over more K-vectors as $n$ grows, diluting the signal from any individual token; and (2) the learned Q-K projection matrices (mechanism 1) have a U-shaped recall bias — content placed in the middle of long contexts is geometrically accessible but statistically under-attended (Liu et al., 2024). Compression works not because it 'organises' information — the model has no concept of organisation — but because it reduces $n$, concentrating the available attention budget on fewer K-vectors, and removes mid-context content that would be under-attended anyway.

The naive removal is truncation: drop the oldest tokens. That loses their information completely, including anything still relevant. Compression is the less-lossy alternative. Instead of discarding old content, summarise it: a 4,000-token stretch of early conversation becomes a 400-token summary that keeps the gist, the decisions, the named entities. The task continues with its early context still present, in compressed form.

The pattern's defining trade is explicit and unavoidable: **it spends fidelity to buy space.** Compression is lossy by design — that is the mechanism, not a failure mode. Why not simply use a bigger window (K9 Long Context)? Because cost still scales with the window, and past some length quality degrades regardless of the model's nominal limit. Compression is what you do when the working set genuinely exceeds what a window can hold *well*.

## Variants

The variants are increasing in cost and in fidelity:

- **Hard truncation** — drop the oldest N tokens. The degenerate baseline; included for contrast. Fast, and loses information outright.
- **Sliding window** — keep the most recent N tokens, drop the rest. Better, but still loses early context entirely.
- **LLM summarisation** — generate a dense summary of the dropped span. The core variant.
- **Chain-of-Density summarisation** *(Adams et al., 2023 — "From Sparse to Dense", arXiv 2309.04269)* — iteratively rewrite the summary to pull in missing entities at constant length. Best fidelity per token for fact-dense content, at the cost of N rounds of LLM calls per compression event. *(Previously listed as a standalone Signal pattern S10; folded here after fundamentality review found it is a K6 variant, not a distinct pattern.)*
- **Recursive summarisation** — summarise summaries as the session keeps growing.

## Applicability

Use Context Compression when:

- the task is a long-running agent session — at scale this is mandatory, not optional;
- a multi-turn conversation has grown past roughly half the window;
- the agent produces bulky tool outputs (SQL results, file contents, API dumps) that accumulate.

Do not bother for short tasks that never approach the window.

## Decision Criteria

K6 is right when sessions reach the context-window threshold and you cannot afford to drop content losslessly.

**1. Measure session token growth.** Profile real sessions for tokens-per-turn (T_avg) and max-turns (N_max). Estimated peak $\approx$ T_avg $\times$ N_max + tool outputs. If peak > ~50% of usable window, K6 is in play. If peak < 30%, you do not need it yet.

**2. Set the trigger.** Compression should fire *before* quality degrades, not when the window is full. A common setting: trigger at ~70% of nominal window.

**3. Try K7 first.** Before compressing (lossy), check whether content is *prunable* (lossless). Tool outputs that have been read, finished sub-task context, redundant intermediates $\to$ **K7 Context Pruning**. Always K7 first; K6 only on what cannot be pruned.

**4. Compressibility check.** Can older content be summarised without losing what later turns will need? Conversational sessions usually yes — decisions, facts, entities are extractable. Highly technical step-by-step work is harder — small details may matter later. Sample-test the Compactor prompt before relying on it.

**5. Compactor cost.** Each compression triggers an LLM call. For long sessions with many compression events, this adds up. Use a small fast model — strong models on summarisation are wasted here.

**Quick test — K6 is the right pattern when:**

- session length pushes peak token usage past ~50% of usable window, *and*
- old content can be safely summarised, *and*
- K7 pruning alone is insufficient, *and*
- summarisation cost in the loop is acceptable.

If sessions do not approach the window, K6 is overhead. If everything in context is consumed-and-done, **K7** alone is lossless and cheaper. If the working set fits a much bigger window comfortably, **K9 Long Context** sidesteps both.

## Structure

```
  Context window growing ──▶ [ token threshold reached ]
                                      │
                                      ▼
                          select stretch to compress
                                      │
                                      ▼
                               Summariser (LLM)
                                      │
                                      ▼
            splice summary back in place of the original span ──▶ continue
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Context window** | the accumulating context being managed | — | — |
| **Trigger** | firing when token usage crosses a threshold | token count $\to$ fire / idle | fire so late that the summarisation call itself no longer fits. |
| **Selector** | choosing which span to compress | window $\to$ span | select the system prompt or the active task — only old, settled content. |
| **Summariser (LLM)** | condensing the selected span | span $\to$ dense summary | silently drop decisions or entities — it must preserve specifics, not just gist. |

## Collaborations

The Trigger monitors token usage. When it crosses the threshold, the Selector picks a span to compress — usually the oldest content, never the system prompt or the active task. The Summariser condenses that span, and the summary is spliced back into the window in place of the original. The task continues, now within budget.

## Consequences

**Benefits**
- Keeps long-running tasks within the token budget.
- Restores attention quality by shrinking a bloated window.
- Holds cost roughly bounded as a session extends.

**Costs**
- A summarisation LLM call each time compression triggers.
- Information loss is certain — the only question is how much.

**Risks and failure modes**
- A detail compressed away resurfaces as needed later, and is gone.

**Compression loss is non-deterministic (mechanism 7).** LLM summarisation is stochastic sampling, not a deterministic hash. Compressing the same span twice may produce different summaries; compressing it once on a long context may omit details that would be retained on a short context. A compressed span cannot be reliably reconstructed from its summary. Unlike a deterministic compression algorithm (gzip, etc.) where the same input always produces the same output, LLM summarisation introduces sampling variance at every compression step. Systems that rely on compressed context for correctness (rather than for cost reduction) must account for this variance — either by running compression multiple times and comparing (expensive) or by designing the compression prompt to extract structured facts rather than prose summaries (more reliable but still stochastic).

- Summary errors are absorbed as "facts" the model now trusts.
- Over-compression flattens the context into uselessly generic summary.

## Implementation Notes

- Compress oldest-first; keep recent turns verbatim.
- Never compress the system prompt or the active task description.
- Tool outputs are the highest-value compression target — large, and often already spent.
- Use Chain-of-Density summarisation for fact-dense content where entity coverage matters.
- Use recursive summarisation for very long sessions.
- Expect roughly 80% information preservation from good summarisation — plan for the lost 20%, do not assume 100%.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** A trigger + selector + summariser, run as maintenance after each turn. Defers to **K7** (lossless prune) before lossy compression.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | After each turn: check token usage vs threshold | `code` | trigger |
| 2 | Under threshold $\to$ return; over $\to$ continue | `code` | |
| 3 | Select the span to compress (oldest; never the system prompt or active task) | `code` | |
| 4 | Is the span prunable (spent tool output, finished sub-task)? $\to$ call K7 and return | `code` | K7 (lossless first) |
| 5 | Otherwise: compress the span | `LLM` | Compactor session |
| 6 | Splice the summary back in place of the original span | `code` | |

**Skeleton:**

```
maybe_compress(window):
    if window.tokens < threshold: return window         # code
    span = window.oldest(keep_recent=6)                  # code
    if span.prunable: return K7.prune(window, span)      # K7 first — lossless
    summary = Compactor(span)                            # LLM
    return window.replace(span, summary)                 # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once | Per-call prompt wraps |
|---|---|---|---|
| **Compactor** | generalist | role: *"produce a dense summary of a conversation span"*; preservation contract: *every decision made, fact established, named entity, and open question; drop pleasantries, repetition, and resolved digressions*; length budget | the span to compress |

**Specialist-model note.** None — a capable generalist with the preservation contract in setup is sufficient. The Compactor's *prompt* is the artifact: the same preservation contract is reusable wherever conversation history must be condensed (agent loops, long chats, retrieved-context compression after K1).

## Open-Source Implementations

- **LLMLingua** — [`github.com/microsoft/LLMLingua`](https://github.com/microsoft/LLMLingua) — prompt and context compression by dropping low-information tokens; a finer-grained, complementary compression mechanism.
- **LangChain** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — `ConversationSummaryMemory` and summary-buffer memory implement conversation-history compression directly.

## Known Uses

- Agentic coding tools (e.g. Claude Code) — conversation compaction when the window fills.
- ChatGPT and other assistants — long-conversation handling.
- LangChain `ConversationSummaryMemory` and equivalents.
- Effectively every long-running agent framework ships some form of this.

## Related Patterns

- **Opposite face of** K7 Context Pruning — K6 rewrites kept content (lossy), K7 removes spent content (lossless). Both are Band II-B subtractive curation; prune first, compress what cannot be pruned.
- **Composes with** K8 Working Memory — the scratchpad is itself compressible when it grows.
- **Alternative to** K9 Long Context — compress the working set, or enlarge the window to hold it.
- **Shares its operation with** K4 RAPTOR — both summarise; K6 compresses live context to save space, K4 summarises offline to build an index.
- **Distinct from** the memory patterns — K6 manages the *live* context window. For cross-session persistence see K10/K11/K12; K6 does not help there.
- Implements Anthropic's "Compress" context-engineering strategy.

## Sources

- Anthropic context engineering framework (2025) — the "Compress" strategy.
- Adams et al. (2023) — "From Sparse to Dense: GPT-4 Summarization with Chain of Density Prompting."
