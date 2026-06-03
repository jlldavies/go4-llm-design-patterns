# K11 — Observational Memory

> Treat what the agent has already seen and done within the current session as its primary memory — kept in a stable, compact, immediately available form — rather than re-retrieving it from an external store.

**Also Known As:** Agent-Centric Memory, Seen-First Memory, Session Memory

**Classification:** Category II — Knowledge · Band II-C Memory · in-session persistence. An emerging (2025–26) pattern.

---

## Intent

Maintain coherence across a long agentic session by keeping a running, compact record of the agent's own observations and actions, and prioritising that record over external retrieval.

## Motivation

When agents replaced chatbots, the memory question changed. A chatbot answering questions over a corpus needs RAG: retrieve what the *documents* say. An agent running for hours needs something else — it needs to recall what *it* did: which files it edited, which tools it called, what they returned, what it concluded. That is not in any external corpus; it is the session's own history. Using K1-style retrieval for it is a poor fit — the relevant context is recent agent activity, and re-retrieving it from a vector store is slow, imprecise, and beside the point.

Observational Memory takes the opposite stance: **the agent's own observations are the primary memory.** The session keeps a running, compressed record of what the agent has perceived and done, and that record — not an external corpus — is what the agent reasons over. External retrieval (K1) becomes a secondary source, consulted only when the in-session record is insufficient.

There is a second, structural payoff. A memory built from a stable, append-mostly record of observations changes slowly and predictably. A stable context prefix is a *cacheable* context prefix: KV-cache reuse across the session's many model calls is reported to cut cost by roughly an order of magnitude. The mechanism (mechanism 5 and 3): the provider computes and stores the KV states — a 4D tensor [layers $\times$ seq_len $\times$ kv_heads $\times$ d_head] — for any stable token prefix. On re-submission of the same token sequence, those states are injected directly, bypassing the O(seq_len²) prefill computation (mechanism 2). At Anthropic: minimum 1024 tokens, ~5-minute TTL, reads at ~10% of normal input cost. Any edit to a prior position in the prefix produces a different token ID $\to$ different K vector $\to$ cached state invalid for that position and all subsequent ones. K1-style retrieval, which rewrites the context with different chunks every turn, forfeits that. Observational Memory is partly a pattern *for* cache-friendliness.

This is distinct from K10 Long-Term Memory, which persists across sessions and is corpus-like; K11 is scoped to the current session and is observation-like. It is distinct from K8 Working Memory, which is a scratchpad the model deliberately writes; K11 is the accumulated record of everything the agent has observed, written deliberately or not. And it is distinct from K12 Karpathy Memory, which takes the same observation stream as input but has the LLM digest it into structured curated notes — K11 keeps the raw log cheap and cache-friendly; K12 pays curation cost to make later reads dense and navigable. The two are the **raw-log** and **curated-notes** branches of the same Karpathy framing of agent memory; they are often paired.

## Applicability

Use Observational Memory when:

- the agent runs long sessions — hours, or days;
- the agent's own prior actions are the main relevant context — coding, research, operations agents;
- KV-cache reuse is a material cost lever for the deployment;
- K1 retrieval is too slow or too imprecise for in-session recall.

It is irrelevant to short tasks and single-turn question answering.

## Decision Criteria

K11 is the right memory pattern when the agent's own activity *is* the memory and prompt caching makes the cost work.

**1. Session length.** How long does a typical session run? If sessions are short (a handful of turns), the cache amortisation that justifies K11 does not accrue. Threshold of interest: roughly **$\geq$ 20–30 turns**, or hour-scale sessions.

**2. Provider and model caching.** Does the chosen model and provider expose prompt caching at usable granularity? Without it, K11 is just "keep appending tokens" — costs scale linearly per turn with no offset, and the pattern's main economic argument disappears. Additionally, sessions that pause between agent steps for longer than the TTL (~5 minutes on Anthropic) will re-prefill at full cost on the next step — the cache benefit accrues only within an active session (mechanism 5). For long-idle agents, the economics shift back toward K10 or K12.

**3. Cache hit rate target.** Measure expected and actual cache hit rate. Below ~70% the pattern is misconfigured — something is rewriting prior entries, or the recorder is not truly append-only. Above ~90% is where the reported ~10$\times$ cost reduction lands.

**4. Read pattern.** Is the agent reading the whole record (which K11 makes cheap via cache) or only specific entries (which K12 makes cheap via structure)? *Whole record matters* $\to$ K11. *Specific entries matter* $\to$ K12.

**5. Cross-session continuity.** K11 is session-scoped. If continuity is needed beyond the session, pair with **K10** (facts in a vector store) or **K12** (curated notes) — usually both.

**Quick test — K11 is the right pattern when:**

- session length supports cache amortisation ($\geq$ ~20 turns, or hour-scale), *and*
- the provider supports prompt caching at appropriate granularity, *and*
- cost — not only quality — is the lever you are optimising, *and*
- the agent benefits from reading the *whole record* rather than specific entries.

If sessions are short, drop K11 — it has no benefit. If you need structured, navigable memory rather than the whole record, choose **K12 Karpathy Memory**. If memory must persist across sessions, pair with **K10** or **K12** (usually both).

## Structure

```
  agent observes / acts
        │
        ▼
  append observation to the running record (compressed)
        │
        ▼
  record forms the stable context the agent reasons over ──▶ KV-cache reuse
        │                                                     (stable prefix)
        ▼
  external retrieval (K1) consulted only as a fallback
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Observation record** | the running log of what the agent has seen and done | observations $\to$ reasoning substrate | be rewritten each turn — a stable, append-mostly prefix is what enables caching. |
| **Recorder** | appending each observation or action | event $\to$ record entry | reorder or edit prior entries — that breaks the cacheable prefix. Mechanically: the provider's cache key is the exact token sequence of the prefix. A rewritten token at position i produces a different K vector for that position, invalidating the cached KV state for position i and all subsequent positions (mechanism 3 and 5). The append-only constraint is not a style rule — it is a cache correctness requirement. |
| **Agent (LLM)** | reasoning over the record | record $\to$ next action | reach for external retrieval first — the record is the primary memory. |
| **KV-cache** | serving the stable prefix cheaply | stable prefix $\to$ cached compute | — |
| **External retrieval** | the secondary fallback source | query $\to$ external facts | be the default — it is consulted only when the record is insufficient. |

## Collaborations

At each step the Recorder appends the latest observation or action to the running record. The agent reasons over the record as its primary memory. Because the record is append-mostly, its prefix is stable across calls and is served from the KV-cache rather than recomputed. Only when the record lacks something the agent needs does it fall back to external retrieval.

## Consequences

**Benefits**
- Coherent behaviour across long sessions — the agent reliably recalls its own history.
- Large cost reduction through KV-cache reuse (reported around 10$\times$).
- Simpler than operating an external retrieval layer for in-session recall.
- The record doubles as a natural execution trace.

**Costs**
- The record still consumes window space — it needs K6 and K7 to stay bounded.
- Scoped to one session: no cross-session continuity (that is K10's job).

**Risks and failure modes**
- External knowledge the agent has not "seen" is missing from the record entirely.
- Record growth, if unmanaged, crowds the window.
- If the record is compressed badly, the agent loses access to its own history.

## Implementation Notes

- Keep the record append-mostly and the prefix stable — that stability is what unlocks caching.
- Compress with K6 and prune with K7, but in ways that preserve the cacheable prefix where possible.
- Pair with K10 for cross-session continuity, and with K1 as the fallback for external facts.
- This is an emerging pattern; expect implementation details to keep moving.

## Implementation Sketch

> `LLM` = configured session; `code` = wiring.

**Composition:** Append observations to a stable, append-mostly record; reason over that record as primary context; cache its prefix; fall back to **K1** only on a gap. Managed by **K6/K7** when it outgrows the window — *carefully*, to preserve the cacheable prefix.

**The chain (per agent step):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Append the latest observation/action to the record | `code` | |
| 2 | Compose prompt: stable record prefix + new query; mark prefix cacheable | `code` | prompt caching |
| 3 | Reason over the record to produce the next action or answer | `LLM` | Agent session |
| 4 | If the response signals a knowledge gap: fall back to K1 retrieval and re-prompt | `code` | K1 |
| 5 | Append the new exchange (query + answer) to the record | `code` | |
| 6 | If the record exceeds threshold: K6 compress or K7 prune — preserving the cacheable prefix where possible | `code` | K6, K7 |

**Skeleton:**

```
agent_step(query, mem):
    answer = Agent(mem.context(), query, cache_prefix=True)     # LLM
    if needs_external(answer):
        answer = Agent(mem.context() + K1.retrieve(query),
                       query, cache_prefix=True)                  # LLM + K1
    mem.observe(f"Q: {query}\nA: {answer}")                       # code — append-only
    return answer
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | the system's main generalist, **on a provider that supports prompt caching** | role and operating instructions; rule: *"reason over your observation record below; if you need external facts not present in it, request retrieval explicitly"*; the **observation record itself** is the (growing) cacheable prefix that follows — appended to, never rewritten | the new query |

**Specialist-model note.** The hard dependency is **prompt caching** at the model and provider layer — the reported ~10$\times$ cost reduction comes from KV-cache reuse of the stable record prefix. Without caching, the pattern still works but loses its main economic advantage. Measure cache hit rate as a first-class metric, alongside answer quality.

## Open-Source Implementations

Observational Memory is an emerging (2025–26) pattern with no single canonical project yet. The closest references:

- **Agent Memory Techniques** — [`github.com/NirDiamant/Agent_Memory_Techniques`](https://github.com/NirDiamant/Agent_Memory_Techniques) — covers session and observational memory alongside the cross-session variants.
- **Letta** (formerly MemGPT) — [`github.com/letta-ai/letta`](https://github.com/letta-ai/letta) — its *archival* memory layer is the closest production embodiment of the K11 raw-record idea; note that Letta's *core memory blocks* belong to K12 (the curated branch), so Letta sits at the K11/K12 boundary by design.

## Known Uses

- 2025–26 practitioner work on cutting agent costs through observational memory plus caching.
- Agent frameworks that deliberately favour stable, cacheable contexts.
- Long-session coding agents (Claude Code and similar) lean toward this approach.

## Related Patterns

- **Often paired with** K12 Karpathy Memory — K11 keeps the raw activity record; K12 is the LLM-curated *digest* of it. The Curator in K12 typically reads K11's log as its source. K11 and K12 are the *raw-log* and *curated-notes* halves of the same Karpathy framing of agent memory.
- **Distinct from** K10 Long-Term Memory — in-session versus cross-session; usually paired, K11 for intra-session coherence and K10 for inter-session continuity.
- **Distinct from** K8 Working Memory — an accumulated observation record versus a deliberately written scratchpad.
- **Managed by** K6 Context Compression and K7 Context Pruning.
- **Uses** K1 Vanilla RAG as a fallback source on external-knowledge gaps.
- **Aligned with** K9 Long Context — both want a stable, cacheable context prefix.
- Not to be confused with the Humanizer pattern H6 Continuous Inner Monologue, which concerns background deliberation, not memory.

## Sources

- Karpathy, A. — 2025 public talks and writing on agent architecture and "context engineering"; the *raw-log + caching* cost argument is the relevant claim. (See K12 for the *curated-notes* branch of the same framing.)
- Context-engineering and KV-cache reuse literature, 2025–26.
- Provider documentation on prompt caching (Anthropic, OpenAI, Google) — the structural dependency of the pattern.
