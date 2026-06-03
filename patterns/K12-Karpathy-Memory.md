# K12 — Karpathy Memory

> Have the LLM itself curate a structured, dense memory — writing, editing, merging, and linking entries — so every read is of pre-digested knowledge rather than a raw observation log or a vector of isolated extractions.

**Also Known As:** Curated Memory, Self-Edited Memory (Letta's term), Agent-Authored Wiki, Structured Notes Memory

**Classification:** Category II — Knowledge · Band II-C Memory · curated persistence; can be in-session or cross-session.

---

## Intent

Give an agent a memory the LLM itself maintains as structured, dense, token-efficient notes — paying more at *write* time so every *read* is cheap, navigable, and useful.

## Motivation

Memory for agents has, until recently, leaned on two strategies, each flawed at a different end:

- **K10 Long-Term Memory** stores short *extracted items* with vectors and retrieves them by similarity. Cheap to write, cheap to read individually — but the items are isolated and brittle, with no structure between them, and similarity retrieval misses anything not phrased like the query.
- **K11 Observational Memory** keeps the raw observation log as primary memory, leaning on prompt caching for cost. Free to write — but verbose at read: the agent rereads everything to remember anything, and any single fact is buried in the noise of the whole session.

Neither captures what a human knowledge worker does, which is to **maintain notes**. They write down what matters, revise their notes when they learn more, link them, prune them. The notes are dense because a human has digested the underlying material *once* and won't redo that work on every read.

Karpathy's framing of agent memory points to the same move: have the LLM build and maintain the memory itself — write structured entries, update them, refactor them — so each read is of pre-digested knowledge, not raw experience. The cost moves to the *curator*: the LLM call that organises the memory. The pay-off is at read time: every subsequent reasoning step over that memory pays only for the dense final form. The foundation: the model's weights do not change between sessions (mechanism 10). All capability that accumulates is in the *files* — the curated notes — that are read into context at each session. Curation is the process of making those files more information-dense per token, so each read obtains more useful knowledge per unit of context-window cost.

This is the third memory strategy. It is not K10's vector store and it is not K11's raw record. It is **an LLM authoring its own knowledge base**.

The defining claim of the pattern is asymmetric: *one* expensive curation buys *many* cheap reads. Where K10 amortises a moderate write against a moderate read, and K11 amortises a free write against a cheap-via-cache read, K12 amortises an expensive write against a *very* cheap, *very* useful read.

## Applicability

Use Karpathy Memory when:

- the same memory will be read many times before it is updated (read frequency far exceeds curation frequency);
- the domain or user has structure worth preserving — entity profiles, project notes, evolving understanding;
- read-time token cost is a material lever (long contexts, many turns over the same memory);
- the memory must be human-readable and editable for operators or downstream agents.

Do not use it when:

- the memory is touched once or twice — curation cost will not amortise;
- the data is naturally a flat list of facts with no structure between them (K10 fits);
- curator-call budget is not affordable, or curation latency is intolerable at the trigger points.

## Decision Criteria

K12 is right when curation amortises against many reads, structure earns its keep, and editability matters.

**1. Estimate read-to-write ratio.** Count expected reads of the memory between curations (R) versus curator calls per cycle (W). Practical threshold: if **R / W $\geq$ 10**, curation amortises clearly; below that, K10 or K11 is usually cheaper.

**2. Score the structure benefit.** Would a human reader of this memory want pages, sections, links? Entity profiles, decision logs, evolving project notes — yes, K12. A bag of independent facts — no, K10.

**3. Cost the curator.** Curation calls dominate the write side. Annualise: curator calls per day $\times$ cost per call. Compare to (a) the K11 cost of re-reading uncurated logs and (b) the K10 cost of similarity calls plus retrieval-miss errors.

**4. Read-time efficiency check.** A curated note is typically 5–20$\times$ denser than the raw observations it digested. This density directly reduces context-window cost (mechanism 9): in-context storage costs O(n²) per step in attention compute (mechanism 2). A 10$\times$ denser note means 10$\times$ fewer tokens in the context, which is not a linear saving — it collapses the per-step attention cost toward the sparser regime of the n² curve. If that compression unlocks the read budget — letting the agent hold its working memory in a small fraction of the window — K12 has paid.

**5. Editability requirement.** Does a human or another agent need to read, audit, or correct the memory? Curated notes are inspectable and editable. Vector-store memory (K10) effectively is not; raw observation logs (K11) are inspectable but not navigable.

**Quick test — K12 is the right pattern when:**

- R / W $\geq$ 10 (curation amortises against many reads), *and*
- the memory has structure worth preserving (entities, projects, linked concepts), *and*
- read-time token efficiency is a material concern, *and*
- inspectability and editability matter to operators or downstream systems.

If R / W is low, choose **K11** — the raw log is already a record and curation overhead is unjustified. If the memory is flat facts with no structure, choose **K10** — a vector store with similarity is simpler. If you need *both* a long activity log to reason from and a small curated overlay, run K11 and K12 together (the curated notes prepended to the cached log).

## Structure

```
  Agent activity (sessions, tasks, exchanges, often K11's record)
         │
         ▼
  Trigger: end of session, milestone, periodic
         │
         ▼
  Curator (LLM) ──▶ reads current notes touched by activity + the activity itself
         │
         ▼
  emits edits: write new entries, update existing, merge duplicates, refactor, link
         │
         ▼
  Memory store: structured notes (pages, blocks, sections, links)
         │
         ▼
  At read: Selector picks relevant notes by name / topic / recency ──▶ Agent
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Memory store** | the structured notes themselves | structured store $\to$ reads/writes | be unstructured — the structure is what makes reading cheap. |
| **Note schema** | what an entry looks like (block? page? section + links?) | — $\to$ editable structure | be over-engineered — the schema must be one the Curator can reliably produce. |
| **Curator (LLM)** | writing, editing, merging, refactoring notes | current notes + recent activity $\to$ updated notes | rewrite notes on every turn — curation must be triggered (end of session, milestone), or the cache and the operator both lose. |
| **Selector** | choosing which notes to load for a given query | query + index of notes $\to$ relevant subset | load everything — that undermines the read-efficiency point. |
| **Agent (LLM)** | reasoning with the loaded notes | query + loaded notes $\to$ answer | edit notes inline; that is the Curator's job. The separation prevents accidental drift. |

The **Curator and the Agent are kept distinct sessions, even when the same model serves both.** The Agent reads; the Curator writes. Mixing them is the pattern's most common failure: an Agent that edits notes mid-reasoning destabilises the memory and erodes the cache. There is a mechanistic reason beyond semantic confusion: if the Agent writes to the note store mid-reasoning, the note tokens change position, invalidating the provider-side KV cache for those positions mid-session (mechanism 3 and 5). The separation is a cache correctness requirement as much as a design principle.

## Collaborations

The Agent runs its task as usual, reading curated notes the Selector loaded. At a defined trigger — end of session, end of milestone, periodic interval — the Curator wakes up. It reads the existing entries touched by the recent activity and the activity log itself, then emits edits: new entries, updates to existing ones, merges of duplicates, links between related notes. The store applies the edits. The next time the Agent runs, the Selector chooses which notes to load and the Agent reasons over the refreshed curated subset.

## Consequences

**Benefits**
- Read-time token cost is small — every read consumes dense, pre-digested content.
- The memory has structure: entries can be named, linked, indexed, navigated.
- Notes are inspectable and editable by humans or other agents.
- Improvement compounds: as understanding grows, the Curator refactors.

**Costs**
- Curator calls are not cheap — every update is at least one LLM call, often several.
- The memory drifts if curator prompts are weak — notes contradict, duplicates accumulate.
- Less cache-friendly than K11 — curation changes the prefix. The mechanism: each curation event modifies note content, producing a different token sequence for modified entries. The provider's KV cache key is the exact token sequence; a changed note entry invalidates the cached state for that position and all subsequent positions (mechanisms 3 and 5). This is why K11 (append-only, never-edit) is more cache-friendly by design — K12 explicitly trades cache stability for write-time structure improvement.
- Schema discipline: a sloppy schema yields unreliable retrieval.

**Risks and failure modes**
- *Curator drift* — repeated curations gradually rewrite history into the Curator's interpretation, not the original facts.
- *Edit storms* — too-frequent curation thrashes the memory and the cache.
- *Schema collapse* — without a stable schema, notes degenerate into free-form prose the Selector cannot index.
- *Stale notes* — without aging or refresh, old notes mislead.
- *Agent-as-Curator confusion* — when the Agent edits the store mid-reasoning, working state and persistent memory blur.

## Implementation Notes

- Treat the Curator as a *separate session* from the Agent, even when using the same model. Different setups, different prompts, different invocations.
- Trigger curation deliberately — session end, milestone, periodic — never every turn.
- Keep the schema simple at first: titled entries with sections, links by entry name. Add structure only when retrieval misses it.
- Version the Curator's prompts; track curator-output diffs over time as a drift signal.
- The Selector can be a small generalist call or a deterministic index — choose by the navigation pattern.
- Pair with **K11** for in-session activity (the Curator reads K11's log to produce K12 entries) and with **K10** if you also need fact-level extraction in a flat vector store.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** K12 chains an *Agent* (reads) with a separate *Curator* (writes) against a structured Memory store. The Curator often reads K11's activity log as its source material. K12 commonly composes with **K11** (activity input) and **K10** (orthogonal vector store for flat facts).

**The chain — read (per Agent step):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| R1 | Selector picks relevant entries by name / topic / recency | `code` (or small `LLM`) | Selector session |
| R2 | Compose prompt: selected notes + the query | `code` | S6 output template |
| R3 | Agent reasons and answers | `LLM` | Agent session |

**The chain — curate (at trigger):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| C1 | Gather recent activity (often K11's log) + entries it touches | `code` | K11 (often) |
| C2 | Curator decides what to write, edit, merge, link | `LLM` | Curator session |
| C3 | Apply edits to the Memory store (replace / insert / rethink) | `code` | |
| C4 | *(optional)* Curator emits a diff / changelog entry | `LLM` | Curator session |

**Skeleton:**

```
read(query, store):
    notes = Selector(query, store.index)              # code (or small LLM)
    return Agent(notes, query)                         # LLM

curate(activity_log, store):                           # at trigger only
    touched = store.entries_touching(activity_log)     # code
    edits   = Curator(touched, activity_log)           # LLM — write/edit/merge/link
    store.apply(edits)                                  # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | the system's main generalist | role; how to use the loaded notes (*"treat as your existing knowledge of this domain or user"*); rule for flagging missing knowledge to be added at the next curation | the selected notes + the query |
| **Curator** | capable generalist — *curation quality caps the value of the whole pattern* | role: *"you maintain a structured knowledge store"*; the **schema** (entry format, links, sections); editing rules (when to merge, when to split, when to leave alone); the existing entries this curation will touch | the new activity since the last curation |
| **Selector** *(optional)* | small fast generalist, *or* a deterministic index | role: choose the entries most relevant to the query; output: list of entry names | the query + the index of available entries |

**Specialist-model note.** No fine-tuned specialist is required, but two structural choices change everything:

- The **Curator must be a separate session from the Agent.** Same model is fine; different setups, different invocations. Mixing them creates the "agent edits memory while reasoning" failure mode.
- A **long-context model** materially helps the Curator, which must hold current notes plus recent activity. The Curator's quality benefits from the strongest available model — paid for in batches at trigger time, not per turn.

## Open-Source Implementations

- **LLM Wiki** (Karpathy, 2026) — [`gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — the reference design. A Gist, not a repo: describes the raw/ + wiki/ + schema architecture, the three operations (ingest / query / lint), and the `index.md` + `log.md` navigation state. The authoritative source for the pattern's mechanism.
- **memoriki** — [`github.com/AyanbekDos/memoriki`](https://github.com/AyanbekDos/memoriki) — the closest direct OSS implementation (Apr 2026, 105 ★, MIT). Lifts Karpathy's raw/ + wiki/ + CLAUDE.md structure verbatim, then adds a MemPalace semantic-search layer on top for queries the wiki alone cannot answer. A template starter rather than a mature library.
- **Letta** (formerly MemGPT) — [`github.com/letta-ai/letta`](https://github.com/letta-ai/letta) — mature production implementation. Core memory blocks are LLM-curated structured notes the agent edits with explicit tools (`memory_replace`, `memory_insert`, `memory_rethink`). Archival memory layers in for scale beyond the core.
- **Cognee** — [`github.com/topoteretes/cognee`](https://github.com/topoteretes/cognee) — memory control plane: builds and persists a knowledge graph from heterogeneous sources, exposes `remember / recall / forget / improve` operations. Apache 2.0.
- **Agent Memory Techniques** — [`github.com/NirDiamant/Agent_Memory_Techniques`](https://github.com/NirDiamant/Agent_Memory_Techniques) — runnable notebooks covering Letta, Mem0, Zep, Graphiti, and the curated-vs-extracted distinction.
- **CLAUDE.md / AGENTS.md conventions** in coding-agent workflows — project-level markdown maintained by the agent across sessions. A community convention rather than a single repo; the pattern in its lightest form.

## Known Uses

- **Letta** production deployments — agents with editable core memory blocks, including a coding-agent variant (`letta-code`).
- **Coding-agent ecosystems** (Claude Code, Cursor) — project-level `CLAUDE.md` and rules files curated by the user or the agent over time.
- **Personal-assistant agents** maintaining user profiles and project notes as structured entries rather than raw histories.
- **karpathy/autoresearch** issue [#179](https://github.com/karpathy/autoresearch/issues/179) — open proposal to add a project-level long-term memory file and a Guidance Agent to autoresearch, applying the same curated-briefing principle to a research-agent loop. Adjacent engineering discussion, not a released implementation.

## Related Patterns

- **Distinct from** K10 Long-Term Memory — K10 stores extracted *facts* in a vector store, retrieved by similarity; K12 stores structured *notes* the LLM authored, retrieved by name / topic / inclusion. Often paired: K10 for fact recall, K12 for the agent's organised understanding.
- **Distinct from** K11 Observational Memory — K11 is the raw activity record; K12 is the *digest* of it. K11 usually feeds K12 — the curator reads the log.
- **Echoes** K6 Context Compression in spirit but differs in scope — K6 compresses *live* context to free space; K12 produces *persistent* structured notes for repeated reads. Same instinct (digest once, use many times), different time scale.
- **Pairs with** S6 Output Template — the note schema is a Signal-layer artifact that constrains the Curator.
- **Pairs with** V14 Trajectory Logging — the activity log feeding the Curator overlaps the Reliability category's logging concern; same raw data, different uses.
- **Named after** Andrej Karpathy, whose framing of agent memory — *"structure memory to be token-friendly; use the LLM to build the data"* — is the clearest articulation of the pattern.

## Sources

- Karpathy, A. (2026) — "LLM Wiki" — [`gist.github.com/karpathy/442a6bf555914893e9891c11519de94f`](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) — primary source for the raw/ + wiki/ + schema architecture and the ingest / query / lint operations.
- Karpathy, A. (2025) — "Context engineering" tweet, June 25 — [`x.com/karpathy/status/1937902205765607626`](https://x.com/karpathy/status/1937902205765607626) — coins the framing; distinguishes context engineering from prompt engineering in industrial-strength LLM applications.
- Karpathy, A. (2025) — YC AI Startup School keynote, June 16–17 — "LLM as OS" framing; context window as RAM; LLMs as having anterograde amnesia without external memory. Summary: [`latent.space/p/s3`](https://www.latent.space/p/s3).
- Packer et al. (2023) — "MemGPT: Towards LLMs as Operating Systems" — arXiv 2310.08560 — predecessor of Letta; the paged-memory model that K12 generalises.
- Letta documentation — core-memory blocks and the self-editing memory model.
- "Anatomy of Agentic Memory" (arXiv) and the Agent Memory Techniques survey for the wider variant landscape.
