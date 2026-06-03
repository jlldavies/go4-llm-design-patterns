# K7 — Context Pruning

> Identify spans of the context window that are no longer needed and remove them outright, keeping everything retained at full fidelity.

**Also Known As:** Selective Recall, Context Cleaning, Relevance Filtering, Tool-Result Dropping

**Classification:** Category II — Knowledge · Band II-B Context-window management · a *subtractive* in-flight curation pattern; the lossless counterpart of K6 Context Compression.

---

## Intent

Reclaim context-window space by deleting content that has served its purpose, without summarising or altering what remains.

## Motivation

Not all context bloat needs compression. Much of a full window is not *compressible* content — it is simply *spent* content. A 10,000-token SQL result that the agent read and acted on at step 3 is pure noise at step 9. A retrieved document used in an earlier sub-task. A tool error already handled. These spans are not partially relevant — they are *done*.

Summarising them (K6) still keeps a lossy residue, and still costs a summarisation call. The correct move for spent content is exact removal: identify the span and delete it, leaving every retained token untouched.

Where K6 trades fidelity for space, pruning gives space *for free* on the content that stays — it is lossless on the retained context. Its cost is elsewhere: you must *know* what is spent. That bookkeeping is the pattern's whole difficulty, and it is what makes pruning genuinely distinct from compression rather than a variant of it. Pruning is lossless but requires consumption tracking; compression is lossy but requires no tracking. Two different patterns, because they resolve the forces differently.

## Applicability

Use Context Pruning when:

- the agent produces large tool outputs that get fully consumed — database queries, file reads, API responses;
- retrieved documents have been used and the sub-task that needed them is finished;
- errors have been handled, or intermediate outputs are now redundant.

Prefer pruning *before* compression — it is cheaper and lossless. It does not apply when you cannot determine what is spent; then compress instead.

## Decision Criteria

K7 is right when sizeable portions of context are *spent* — read, used, finished — and you can track which.

**1. Inventory spent content.** In a typical session, what fraction of token usage is content consumed and not referenced again?
- Large tool outputs (DB results, file dumps, API responses): often dominates the budget.
- Retrieved documents from finished sub-tasks: noise after the sub-task ends.
- Handled errors, processed intermediates: spent.

If a significant share (≳ 30%) is consumed-and-done, K7 pays off.

**2. Consumption tracking feasibility.** Can spans be reliably marked as "consumed"?
- Tool calls: easy — wrap the tool, mark output spent after the next turn.
- Sub-task boundaries: easy if the control flow has explicit sub-tasks.
- Free-form conversation: harder — what counts as consumed?

If tracking is impractical, fall back to **K6 Context Compression**.

**3. Trigger choice.** Prune at natural boundaries (end of sub-task, threshold) — not every turn. Frequent pruning thrashes the context and invalidates cached KV states (mechanism 3 and 5). Each prune that rewrites earlier token positions forces re-computation of those K and V vectors — negating the cost benefit of provider-side prefix caching. Prune at sub-task boundaries that preserve the stable prefix; avoid pruning mid-prefix.

**4. Stub vs delete.** Replace bulk with a compact stub ("[tool foo: returned 412 rows, processed]") so the agent remembers the event without the bulk. Pruning to nothing loses event-level context.

**5. Lossless-first principle.** Always pair K7 with K6. Run K7 first (lossless), K6 only on what cannot be pruned. Never reach for K6 on content that can simply be dropped.

**Quick test — K7 is the right pattern when:**

- significant context is consumed-and-done (typically large tool outputs), *and*
- consumption can be tracked reliably (explicit sub-task or tool boundaries), *and*
- lossless reduction is preferable when available.

If consumption cannot be tracked, **K6** is the only option. If the context never approaches the window, neither pattern is needed. For cross-session persistence, K7 does not help — that is **K10 / K11 / K12** territory.

## Structure

```
  Context window ──▶ identify spent spans ──▶ delete spans ──▶ smaller window,
                     (consumed tool outputs,                   retained content
                      finished sub-task context)               intact at full fidelity
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Context window** | the context being managed | — | — |
| **Consumption Tracker** | recording which spans are spent | span events $\to$ consumed set | guess — a span marked spent that is later referenced is the pattern's main failure. |
| **Pruner** | deleting flagged spans | window + consumed set $\to$ smaller window | alter retained content; pruning is lossless on everything it keeps. |

## Collaborations

As the task runs, the Consumption Tracker marks spans as consumed — a tool output once the agent has read and acted on it, a sub-task's context once the sub-task completes. At a trigger (a token threshold, or a sub-task boundary) the Pruner removes the flagged spans. Everything retained is left exactly as it was.

## Consequences

**Benefits**
- Lossless for all retained content — no summarisation artefacts.
- Cheaper than K6 — no LLM call is involved.
- Frees space without degrading anything that stays. Mechanically: removing spent tokens reduces the length of the K vector sequence the model must attend over. In the attention softmax (mechanism 2), the retained tokens each receive a proportionally larger weight — mid-context content that was being under-attended due to the lost-in-the-middle effect (mechanism 4) becomes relatively more salient after pruning.

**Costs**
- Requires explicit tracking of what has been consumed — the real cost of the pattern is this bookkeeping.

**Risks and failure modes**
- Pruning a span that is referenced again later — the "spent" judgement was wrong.
- Aggressive pruning removes context an unforeseen later step needed.

## Implementation Notes

- Tool results are the prime target — large, and usually fully consumed the moment the agent has read them.
- Prune at sub-task boundaries: when a sub-task finishes, its context becomes prunable as a block.
- Leave a compact reference in place of deleted bulk — e.g. "SQL query X returned 412 rows, processed" — so the agent still knows the event happened. Mechanically: a zero-token deletion removes the K vector for that event from the attention computation entirely — the model has no signal that something happened there. A compact stub keeps a K vector in the sequence that preserves the event-level signal, at minimal token cost (mechanism 3).
- The empirical scaffold study found selective tool-result dropping to be a distinct, common production technique — this pattern is observed practice, not theory.

## Implementation Sketch

> `LLM` = configured session; `code` = wiring. K7 is almost entirely `code` — its cost is bookkeeping, not LLM calls.

**Composition:** A consumption tracker plus a pruner. Runs at sub-task boundaries or on a threshold. The complementary lossy fallback is **K6**, which K7 defers to only when a span cannot simply be dropped.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | When a tool/result is produced: register the span with the Consumption Tracker | `code` | |
| 2 | After the agent has read and acted on it: mark the span consumed | `code` | |
| 3 | At trigger (sub-task boundary or threshold): collect consumed spans | `code` | |
| 4 | For each consumed span, build a compact reference stub | `code` (or `LLM` for prose stubs) | optional Stub-summariser |
| 5 | Replace the bulk span with its stub in the window | `code` | |

**Skeleton:**

```
on_tool_output(name, result, window, tracker):
    span = window.append(f"[tool {name}] {result}")     # code
    tracker.mark_after_next_turn(span)                  # code

maybe_prune(window, tracker):
    for span in tracker.consumed_spans(window):         # code
        stub = f"[{span.label}: {span.one_line} — pruned]"
        window = window.replace(span, stub)              # code
    return window
```

**The LLM sessions:** in the strict form, **none** — the pattern is bookkeeping plus a string substitution. An *optional* small generalist (a "Stub-summariser" session) can produce a one-line prose stub for spans that need more than a programmatic label:

| Session | Model | Setup — loaded once | Per-call prompt wraps |
|---|---|---|---|
| **Stub-summariser** *(optional)* | small fast generalist | role: *"in one short line, describe what this span was and that it has been processed"*; length contract: one sentence | the span to summarise |

**Specialist-model note.** None. K7 is the most code-heavy pattern in the category, and that is the point: the absence of LLM steps is *why* it is lossless on what remains, and *why* it is cheaper than K6.

## Open-Source Implementations

- **OpenProvence** — [`github.com/hotchpotch/open_provence`](https://github.com/hotchpotch/open_provence) — an open implementation of Provence-style context pruning: a reranker-pruner that drops irrelevant sentences from retrieved context.
- **LangChain** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) — the `ContextualCompressionRetriever` prunes retrieved documents down to their relevant spans before they reach the prompt.

## Known Uses

- Production coding agents — selective tool-result dropping, observed across multiple systems in the scaffold study.
- Anthropic's "Select" context-engineering strategy.
- JetBrains and other agent context-management implementations.

## Related Patterns

- **Lossless counterpart of** K6 Context Compression — prune first, compress what cannot be pruned. Both are Band II-B subtractive curation.
- **Composes with** K8 Working Memory — the scratchpad can be pruned of finished entries.
- **Related to** K11 Observational Memory — deciding what stays visible to the agent is the shared concern.
- Implements Anthropic's "Select" / clean-context strategy.

## Sources

- "Inside the Scaffold" empirical study of production coding agents (arXiv) — selective tool-result dropping.
- Anthropic context engineering framework (2025) — the "Select" strategy.
