# K10 — Long-Term Memory

> Persist knowledge in an external store that outlives the context window, and retrieve from it in later turns and later sessions, so the agent accumulates and reuses what it learns.

**Also Known As:** Persistent Memory, Cross-Session Memory, External Memory, Agent Memory. (Episodic, Semantic, and Procedural memory are *variants* of this pattern — see Variants.)

**Classification:** Category II — Knowledge · Band II-C Memory · cross-session persistence.

---

## Intent

Give an agent continuity beyond a single context by writing knowledge to an external store and retrieving it when relevant — so the agent improves over time without retraining.

## Motivation

A context window is erased at the end of a session. By default an agent begins every session knowing nothing of the last one: no memory of what the user told it, what it tried, what worked. For one-shot tasks that is fine. For personal assistants, agents on recurring work, and any system expected to *improve*, it is disabling — the agent cannot personalise, cannot avoid repeating mistakes, cannot build expertise. The two within-context patterns, K8 Working Memory and K11 Observational Memory, do not solve this; they live and die with the session.

Long-Term Memory adds the missing layer: an external store, outside the context window, that persists across sessions. The agent writes knowledge to it as it goes, and retrieves the relevant entries — typically by embedding similarity — into the context of a later session. The mechanism is file retrieval, not model learning (mechanism 10). The model's weights are frozen between API calls. All improvement is in the *store* — the quality of what is retrieved and injected into context. A better memory system is one that retrieves higher-quality text into the context window; no capability accrues in the model itself.

The mechanism is uniform — write to an external store, retrieve by similarity, inject — and it is the same mechanism as K1 Vanilla RAG, with one decisive difference: in K1 the corpus is *given*, while here **the agent writes its own corpus from its experience.**

## Variants

The variants differ only in *what is stored*. They map to the cognitive-science memory triad, and they are one pattern — the store / retrieve / inject mechanism is identical — differentiated by content type and retention policy:

- **Episodic** — records of what happened: past runs, decisions, outcomes, failures and their causes. Lets the agent recall "last time I tried X here, Y broke." Tends to *decay* with age.
- **Semantic** — facts, concepts, and user preferences: what the agent knows. Lets it personalise and accumulate domain knowledge. Tends to *accumulate*.
- **Procedural** — verified how-to: code patterns, tool-use sequences, workflows that worked. Lets the agent reuse a proven procedure instead of re-deriving it. Tends to be *verified then reused*, and is often distilled from episodic memory.

A given system may run one, two, or all three stores. They behave differently in retention and retrieval, but the pattern is one.

## Applicability

Use Long-Term Memory when:

- the system is a personal assistant that should remember the user across sessions;
- the agent works recurring task types — a coding agent on a codebase, a research agent in a domain;
- the system is expected to get better over time.

It is unnecessary for stateless, one-shot tasks.

## Decision Criteria

K10 is the right memory pattern when memory means *isolated, fact-shaped items that should survive sessions and be retrieved on demand.*

**1. Inventory what should be remembered.** Are the items short, fact-shaped, independent — user preferences, decisions, isolated facts about entities? Or are they connected knowledge worth organising into pages? If the former, K10 fits. If the latter, **K12 Karpathy Memory** fits better.

**2. Read pattern.** Do reads arrive as queries answerable by similarity to stored items? If yes, K10's vector store is the natural access pattern. If reads need structural navigation (open the X note, follow the link to Y), choose K12.

**3. Write/read balance.** K10 writes are cheap — one Extractor call per exchange. Reads are cheap — one similarity search. Both scale linearly. K10 has no hidden curation cost, which is its advantage over K12 and its limit: it builds no structure.

**4. Cross-session continuity.** Is there continuity worth keeping between sessions? If sessions are independent and forgetting is fine, neither K10 nor K12 is needed — K11 within sessions is enough.

**5. Operator inspection.** If a human needs to read, audit, or correct memory, K10's flat vector store is hard to navigate compared to K12's structured notes. Factor that into the choice.

**Quick test — K10 is the right pattern when:**

- the items are *fact-shaped* (preferences, decisions, isolated facts), *and*
- similarity retrieval is the natural access pattern, *and*
- write and read are roughly balanced (no curation amortisation needed), *and*
- cross-session continuity is required.

If items are *connected knowledge with structure*, prefer **K12 Karpathy Memory**. If memory is only needed within a session, **K11 Observational Memory**. K10 and K12 are commonly run together — facts in the vector store, structure in the notes.

## Structure

```
  DURING a session                          A LATER session
  ────────────────                          ───────────────
  observe / act                             query
       │                                      │
       ▼                                      ▼
  extract memory-worthy items           retrieve relevant entries
       │                                 (similarity search)
       ▼                                      │
  write to external store ──────────────▶     ▼
  (episodic / semantic / procedural)    inject into context ──▶ proceed
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Memory store** | persistent storage of memories across sessions | memory items $\to$ queryable store | be unbounded — episodic memory must decay, or it accumulates noise. The reason noise is harmful: retrieved items are injected into the context (mechanism 9). Irrelevant injected items consume finite window space, and if they land in mid-context positions they are subject to the lost-in-the-middle geometric under-attention (mechanism 4), simultaneously wasting space and suppressing useful content nearby. |
| **Memory Writer** | extracting what is worth keeping, routing it | session events $\to$ store writes | store everything — write-time selectivity is what keeps retrieval useful, and is the poisoning surface. |
| **Retriever** | surfacing relevant memories | query $\to$ memory items | inject stale or conflicting memories without resolution. |
| **Distiller** *(procedural variant)* | abstracting episodes into reusable procedures | episodes $\to$ procedures | distil unverified episodes — a procedure is a *verified* pattern. |
| **Generator (LLM)** | reasoning with retrieved memory injected | query + memories $\to$ answer | — |

## Collaborations

**Write path.** During a session the Memory Writer watches what the agent observes and does, extracts the items worth keeping, and writes them to the appropriate store. **Read path.** In a later session the Retriever searches the store for entries relevant to the current query and injects them into context. **Distillation path** (procedural). The Distiller periodically abstracts recurring successful episodes from the episodic store into parameterised procedures in the procedural store.

## Consequences

**Benefits**
- Genuine cross-session continuity, personalisation, and improvement over time.
- Expertise accumulates — all without retraining the model (mechanism 10).

**Costs**
- External store infrastructure.
- Write-time extraction cost; retrieval latency.
- Memory management overhead — deciding what to keep and what to expire.

**Risks and failure modes**
- *Stale memory* — the world changed, the memory did not.
- *Conflicting memory* — a new fact contradicts a stored one and both are retained.
- *Memory poisoning* — the agent stores a hallucination as fact and trusts it in every later session. The most dangerous failure of the pattern. The mechanical depth of this risk: a poisoned memory item is embedded and stored as a text vector. When retrieved, it is injected as tokens into the context. The model's attention treats those tokens no differently from ground-truth tokens — there is no architectural mechanism to flag retrieved-from-store content as suspect (mechanism 3). The only defence is write-time selectivity (the Extractor's poisoning guard).
- *Irrelevant retrieval* — surfaced memories mislead rather than help.
- In multi-agent systems, per-agent stores diverge into inconsistent "memories."

## Implementation Notes

- Be selective at write time — store what is reusable, not everything observed.
- Expire or decay episodic memory; it ages.
- Semantic memory needs conflict resolution when a new fact contradicts an old one.
- Procedural memory must be re-validated when the environment changes.
- In multi-agent systems, use a shared memory substrate rather than per-agent stores.
- Gate what gets written — memory poisoning is the failure to design against first.
- Implementations: Mem0, Zep, Letta (MemGPT), or a custom vector database.

## Implementation Sketch

> `LLM` = configured session; `code` = wiring.

**Composition:** Two main paths — a *write* path during a session (Extractor $\to$ Embedder $\to$ store) and a *read* path in later sessions (Embedder $\to$ similarity search $\to$ Generator). The procedural variant adds a periodic *distillation* path.

**The chain — write:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| W1 | At session end (or per turn): hand the exchange to the Extractor | `code` | |
| W2 | Extract durable items worth recalling | `LLM` | Extractor session |
| W3 | Embed each item | `LLM` | K1 Embedder |
| W4 | Write (vector, text, owner tag) to the memory store | `code` | |

**The chain — read:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| R1 | Embed the query | `LLM` | K1 Embedder |
| R2 | Similarity search the store, filtered by owner | `code` | |
| R3 | Inject retrieved memories into the prompt | `code` | |
| R4 | Generate the answer | `LLM` | Generator session |

**The chain — distil (procedural variant):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| D1 | Periodically scan recent episodic items | `code` | |
| D2 | Distil recurring successful trajectories into a parameterised procedure | `LLM` | Distiller session |
| D3 | Write to the procedural store | `code` | |

**Skeleton:**

```
remember(exchange, store, user):
    items = Extractor(exchange)                     # LLM
    for item in items:
        store.add(Embed(item), item, owner=user)    # LLM + code

recall(query, store, user, k=5):
    memories = store.search(Embed(query),           # LLM + code
                             owner=user, k=k)
    return Generator(query, memories)                # LLM
```

**The LLM sessions:**

| Session | Model | Setup — loaded once | Per-call prompt wraps |
|---|---|---|---|
| **Extractor** | generalist | role: *"extract durable items worth recalling across sessions — preferences, decisions, stable facts; ignore the transient"*; output: one item per line, or NONE; **poisoning guard**: *"do not store any item the user did not assert or you did not verify"* | the exchange |
| **Embedder** | specialist text-embedding model (as K1) | model choice is the setup | one item |
| **Generator** | main generalist | role; rule for using retrieved memories (*"treat as background knowledge about this user"*); reconciliation rule when memories conflict | query + retrieved memories |
| **Distiller** *(procedural variant)* | generalist | role: *"abstract repeated successful trajectories into a parameterised procedure; reject one-offs and unverified episodes"* | a window of recent episodes |

**Specialist-model note.** No session is itself a specialist, but the Embedder is (as K1). The dedicated memory layers — Mem0, Zep, Letta — are *infrastructure* specialists rather than LLMs: they ship the store, write/read paths, and conflict-resolution logic, leaving the developer to wire only the prompts.

## Open-Source Implementations

- **Mem0** — [`github.com/mem0ai/mem0`](https://github.com/mem0ai/mem0) — a universal memory layer for agents: extraction, storage, and cross-session retrieval.
- **Agent Memory Techniques** — [`github.com/NirDiamant/Agent_Memory_Techniques`](https://github.com/NirDiamant/Agent_Memory_Techniques) — 30 runnable notebooks covering episodic, semantic, and procedural memory and the major systems.
- **Zep** and **Letta** (formerly MemGPT) — production memory systems built on temporal knowledge graphs and self-editing memory respectively; both are surveyed, with code, in the repository above.

## Known Uses

- Mem0, Zep, Letta (MemGPT) — dedicated agent memory layers.
- ChatGPT's memory feature — a user-facing semantic memory.
- Coding agents that persist verified procedural patterns across sessions.
- The agent-memory survey literature.

## Related Patterns

- **Same mechanism as** K1 Vanilla RAG — store, retrieve, inject — but the agent authors its own corpus from experience. The shared mechanism is the bilinear similarity search (mechanism 1): both K1 and K10 embed a query vector and find the nearest stored K vectors in the learned similarity space. The difference is authorship — K1 retrieves from a human-curated corpus, K10 from an agent-authored one.
- **Often paired with** K12 Karpathy Memory — K10 holds *flat fact-shaped items* in a vector store; K12 holds *structured curated notes*. Together they cover both "what does the agent know about this user/entity?" (K10) and "how does the agent understand this domain/project?" (K12).
- **Completes the memory hierarchy with** K8 Working Memory (in-window), K11 Observational Memory (in-session), and K12 Karpathy Memory (curated): in-window / in-session / cross-session-flat / cross-session-structured.
- **Internal dependency** — the procedural variant is distilled from the episodic variant.
- **Required by** the Humanizer patterns — H2 Episodic Self-Improvement, H4 Procedural Skill Accumulation, and H10 Relational Memory all build on this pattern; H2 shares its poisoning risk.
- **Note on fundamentality** — episodic, semantic, and procedural memory were merged into one pattern because the store / retrieve / inject mechanism is identical across all three. They differ in content and retention policy, which makes them variants, not separate patterns.

## Sources

- Agent-memory survey literature — "Anatomy of Agentic Memory" and related surveys.
- Shinn et al. (2023) — Reflexion (the episodic-memory origin).
- Mem0 and Zep documentation.
- Cognitive-science memory triad — Tulving (episodic/semantic), Baddeley (working/long-term).
