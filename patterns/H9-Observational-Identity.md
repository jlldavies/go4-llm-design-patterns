# H9 — Observational Identity

> Maintain an explicit, evolving model of the agent's own capabilities, knowledge state, and past actions — with confidence and freshness on every entry — so the agent can honestly answer "what do I know?", "what have I done?", and "what can I do?" as first-class reasoning.

**Also Known As:** Self-Knowledge Model, Capability Self-Awareness, Epistemic Self-Model, Metacognitive State, Self-Model.

**Classification:** Category VII — Humanizer · the *evolving self-knowledge* layer that pairs with **H1 Identity Persistence**. Where H1 carries the *invariant* core (who I am), H9 carries the *evolving* record (what I have done, what I can do, with what confidence). H9 reads from **K11 Observational Memory** (session-scoped raw activity) at session end and writes life-span self-knowledge that survives reset.

---

## Intent

Give an agent a persistent, queryable model of its own demonstrated capabilities, attempted tasks, outstanding commitments, and known limitations — each entry timestamped and confidence-scored, each subject to decay — so the agent can route on, communicate about, and reason from its own track record rather than guessing.

## Motivation

Without an explicit self-model, an agent has no honest answer to three questions a competent operator routinely asks itself: *what can I do?*, *what have I tried?*, *what do I know?* The default LLM behaviour on all three is to guess. The agent will confidently attempt tasks it has previously failed, repeat searches that did not work, claim general competence it has never demonstrated, and forget the commitments it made last session. None of this is dishonesty — it is the absence of the relevant data structure.

**K11 Observational Memory** captures this material within a session: the running activity record the agent reasons over. But K11 is session-scoped and lossy at reset. **H1 Identity Persistence** captures *invariant* identity across sessions — values, voice, the headline self-model — but it deliberately holds only the invariant core; the *details* of capability and history would overwhelm the H1 token budget. The gap between them is the evolving, detailed track record: which tasks I have attempted and at what success rate, which tools I have mastered and with what known failure modes, which knowledge domains I have actually engaged versus merely claimed, what I tried in the last session that did not work, what I have committed to but not yet delivered. H9 is that gap, filled.

The Baddeley working memory model (Baddeley, 2000) identifies *self-monitoring* as a core function of the central executive — the component that asks "am I doing this well? have I done this before?" alongside the task. H9 is that function at the agent level: an externalised central-executive record the LLM can read in, reason against, and update. The "Theater of Mind" framing (Shang, arXiv 2604.08206) makes the same architectural claim — epistemic state-tracking is a first-class component of a Global Workspace agent, distinct from both the invariant Genesis State and the episodic log. The defining commitment of H9 is *honesty about the record*: every entry carries a confidence, every confidence carries a date, every date decays. Without that discipline H9 becomes the anti-pattern **HA5 Stale Self-Model** — an agent that confidently claims capabilities it has lost, citing "experience" from a context that no longer holds.

## Applicability

Use when:

- the agent runs across multiple sessions and tasks recur, so a track record is genuinely informative;
- the agent must accurately communicate its own limitations to users or to a router ("I have done X seven times, never Y");
- a multi-agent system needs capability-based routing — **O3 Routing** or **O6 Orchestrator-Workers** with worker selection by demonstrated competence;
- users ask "what do you remember about X?" or "have we tried this before?" as a normal part of the interaction;
- the cost of an agent confidently overreaching its capability exceeds the cost of maintaining the self-model.

Do not use when:

- sessions are independent and one-shot — the track record does not accumulate; use **H1 Identity Persistence** with a static self-model line;
- capability is genuinely uniform across the deployed agent fleet and never changes — there is no signal to record; use **S3 Persona** capability framing;
- you cannot maintain a decay / refresh mechanism — without it the pattern becomes **HA5 Stale Self-Model**; stay on H1 alone;
- the storage / governance budget for per-agent persistent self-knowledge is not available — fall back to **H1** with summary capability fields, or to **K11 Observational Memory** for in-session-only awareness.

## Decision Criteria

H9 is right when an *honest record* of what the agent has done, can do, and is doing changes its behaviour — and when you can afford to keep that record fresh.

**1. Multi-session capability variance.** Across sessions, does the agent's effective capability vary by task type? Measure success rate by task-type bucket over a labelled period. If buckets diverge — > 20-point spread between best- and worst-performing task types — a self-model lets the agent route, escalate, or warn instead of guessing. If buckets converge, H9 buys little; H1's static self-model line suffices.

**2. Capability-routing pay-off.** In a multi-agent system, would routing on demonstrated competence (rather than declared capability) improve outcomes? Measure the *mis-routing rate* under **O3 Routing** with static capability declarations versus a track-record-driven router. If mis-routing > 10%, H9 is the upgrade path; if < 5%, static declarations are fine.

**3. Commitment-tracking volume.** Count outstanding commitments per agent at any time — promises made, follow-ups owed, "next session we will…" markers. If consistently $\geq$ 3 open commitments, H9's commitment-tracker block earns its keep; under 1, H1's commitments line is enough.

**4. Decay discipline.** A self-model without decay degrades into **HA5 Stale Self-Model**. Practical thresholds: success counts older than 90 days lose half their weight; entries untouched for 180 days are flagged for refresh; entries untouched for 365 days are archived. If you cannot operate this discipline, do not build H9.

**5. Budget envelope.** Loaded H9 payload should sit at ≲ 1–2k tokens. Above that, compress with **K6 Context Compression** or push the detailed history to **K12 Karpathy Memory** (structured notes the H9 entries reference) and keep only the index in H9. If neither is available, drop to H1. This budget reflects the O(n²) attention cost that every loaded H9 token adds to the session: a 2k-token H9 payload on a 4k working context adds 50% to pairwise attention computation for every turn (mechanism 2). The Selector's role is to enforce the storage-hierarchy discipline (mechanism 9): bulk capability data lives in the Self-Knowledge Store (cold storage or a vector index, retrieved at O(1) cost per query); only the task-relevant subset enters the expensive in-context tier. Selector budget enforcement is context-budget enforcement.

**Quick test — H9 is the right pattern when:**

- multi-session capability variance is real (> 20-point spread by task type), *and*
- an honest track record would change routing, escalation, or user communication, *and*
- a decay / refresh discipline is in place to prevent staleness, *and*
- the token budget supports a 1–2k-token self-model alongside H1.

If sessions are independent, **H1**'s static self-model line is enough. If the variance is real but staleness cannot be controlled, stay on H1 — H9 without decay becomes **HA5**. If the self-knowledge payload exceeds budget, factor detail out to **K12 Karpathy Memory** and keep H9 as an index of references.

## Structure

```
                            (H1 — invariant identity, position 0 of every context)
                                          │
                                          │ headline self-model line points at H9
                                          ▼
   ┌────────────────────────────────────────────────────────────────────────────┐
   │  Self-Knowledge Store  (persistent; one per agent)                         │
   │    Capability Map     [task_type, attempts, success_rate, last_seen, conf] │
   │    Tool Proficiency   [tool_id, uses, failure_modes, last_used, conf]      │
   │    Knowledge Domains  [domain, depth, last_engaged, conf]                  │
   │    Action History     [session_id, tasks_done, key_decisions]   (compressed)│
   │    Commitments        [commitment, deadline, status]                       │
   │    Current State      [active_task, hypotheses_open, blocked_on]           │
   └────────────────────────────┬───────────────────────────────────────────────┘
                                │ Selector: load relevant subset for this session
                                ▼
   [ session opens ] ── Selector picks task-relevant entries ── injected after H1
                                │
                                ▼
       session runs (reasoning consults self-model as needed)
                                │
                                ▼
   [ session ends ] ── Updater reads K11 activity log + current entries
                                │
                                ▼
       Decay function ages confidence on untouched entries
                                │
                                ▼
       versioned write back to store
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Self-Knowledge Store** | the persistent record (capabilities, tools, domains, history, commitments, current state) | — $\to$ durable, versioned, per-agent record | be the only copy; identity-data loss is a critical failure. Versioned, backed up, inspectable. |
| **Capability Map** | demonstrated competence by task type, with attempts, success rate, last-seen date, confidence | task outcomes $\to$ calibrated competence record | claim capability the agent has not demonstrated. Declared-but-untested capability belongs in H1's self-model line, not here. |
| **Action History** | the compressed record of past sessions: what was done, what was decided | K11 logs (often) $\to$ compressed life-span trace | grow unbounded; compress with K6 or archive to K12. |
| **Commitment Tracker** | active promises and follow-ups | session events $\to$ live commitment list | drop a commitment silently. Closing a commitment is an explicit event, not an omission. |
| **Selector** | choosing which self-knowledge entries to load for the current session / task | session context + index $\to$ relevant subset | load the whole store; defeating the budget defeats the pattern. |
| **Updater** *(separate session)* | writing self-model changes between sessions | K11 activity + current entries $\to$ proposed updates | run mid-session, or write to fields that belong in H1. Same session-end discipline as H1's Updater. |
| **Decay function** | ageing the confidence and freshness of entries over time | entry + elapsed time $\to$ adjusted confidence | be optional. Without decay, H9 becomes **HA5 Stale Self-Model**. |
| **Self-Query Handler** | answering "what do I know about X?" / "have I done Y?" from the store | query $\to$ grounded self-report | fabricate. If the store has no entry, the answer is "I have no record of doing X" — never "yes, I have." |

The Self-Knowledge Store is **read by the running session and written only by the Updater between sessions** — the same read/write separation H1 and K12 enforce, for the same reason: an agent that edits its own track record mid-task can produce self-flattering drift no operator can detect.

## Collaborations

When a session opens, **H1 Identity Persistence** loads at position 0 carrying the invariant identity and a *headline* self-model line that points at H9. The Selector then loads task-relevant entries from the Self-Knowledge Store — capability map slice for the current task type, recent action history, open commitments, knowledge-domain entries the task will touch — and injects them after H1, before the working context. The session runs. **K11 Observational Memory** accumulates the raw activity log within the session. When the agent must answer a self-referential question ("have I done this before?", "what do I know about X?"), the Self-Query Handler reads from the loaded H9 subset, returning grounded answers with confidence and last-seen dates rather than guesses. At session close, the Updater reads K11's session log and the current entries it touches, proposes additions (new task-types attempted, new commitments, capability evidence) and revisions (success-rate updates, freshness stamps); the Decay function ages every entry by elapsed time; the result is written, versioned, back to the store. **H2 Episodic Self-Improvement** consumes H9's failure entries as a source of lessons; **H4 Procedural Skill Accumulation** writes its skill library entries against the demonstrated capabilities H9 records; **O3 Routing** in a multi-agent system reads the Capability Map to route work to the agent best demonstrated to handle it.

## Consequences

**Benefits**
- The agent reports its capabilities honestly — "I have done X seven times with 6 successes, last attempt 11 days ago" — rather than guessing.
- Routing and escalation decisions are grounded in track record, not declared capability.
- Outstanding commitments survive context resets and surface in the next session.
- "Have I done this before?" becomes a valid question with a real answer.
- Reduces confident overreach into tasks the agent has not previously handled.
- Pairs with H2 (failure lessons) and H4 (successful skills) for a complete experience-driven Humanizer stack.

**Costs**
- Persistent storage + governed update mechanism become first-class deployment requirements.
- The loaded H9 subset adds tokens to every context (target ≲ 1–2k).
- Updater calls at session end add to the cost envelope (paid in batches, not per turn).
- A decay / freshness discipline must be maintained operationally — not just specified.

**Risks and failure modes**
- *Stale self-model* (**HA5**) — without decay, the agent confidently claims capability it has lost; the central failure mode of the pattern.
- *Self-flattery drift* — if the Updater runs without separation from the Agent session, the agent can write self-flattering entries it then reads as evidence.
- *Capability cherry-picking* — entries written only when the agent succeeds, missing the denominator of attempts; success rate ceases to mean anything.
- *Commitment loss* — a closed commitment quietly dropped instead of explicitly marked complete; the next session has no record.
- *Field-scope creep* — adaptive style (H7), values (H1), relationship history (H10) drift into H9; H9 ends up holding what other patterns own.
- *Budget overrun* — the Selector loads too much; the self-model crowds working context.

## Implementation Notes

- **Bootstrap honestly.** First-session H9 is *empty* except for the headline capability claims inherited from H1's self-model line. Capability evidence is earned by attempts, not declared.
- **Confidence + last-seen on every entry.** A capability claim without `attempts=N, successes=M, last_seen=YYYY-MM-DD, confidence=c` is a guess in a structured field. Reject it at the Updater.
- **Decay schedule.** A reasonable default: half-life of 90 days on success counts; flag entries untouched for 180 days for refresh; archive at 365 days. Tune to the domain — fast-moving APIs need faster decay than stable domains.
- **Record attempts, not just successes.** Every attempt updates the denominator. Without this, success-rate is meaningless. This is the discipline that distinguishes H9 from a marketing brochure.
- **Updater is a separate session from the Agent.** Same model is fine, different setup, never invoked mid-session — the same discipline K12 and H1 enforce.
- **Selector load budget.** Load entries relevant to the task at hand, not the whole store. The Capability Map slice for the current task type, recent action history, open commitments, and any knowledge-domain entries the task touches. Target ≲ 1–2k tokens loaded.
- **Mechanistic grounding for decay.** The model's weights do not change between sessions — there is no learning from prior capability demonstrations at the weight level (mechanism 10). The Self-Knowledge Store is the only place capability evidence lives. Without the decay function, the store accumulates stale entries that the model will read and act on as if current, because it has no other source of capability information. Decay is not optional refinement; it is the correction mechanism for the mismatch between a static model and a changing operational environment.
- **Prefix caching of stable capability entries.** For task types where the Selector consistently returns the same capability-map entries, those entries form a stable post-H1 prefix across sessions. If they exceed 1,024 tokens, they may qualify for provider prefix caching (mechanism 5). Design the Selector to return stable entries before session-specific entries to maximise the cacheable prefix length.
- **Surface to users on request.** "What do you remember about X?" should be answerable from H9 + H2. The Self-Query Handler must return *grounded* answers — citing entries with dates and confidences — or admit "I have no record."
- **Compose with K12 for large stores.** Once H9 detail exceeds the budget, push action history and knowledge-domain detail to **K12 Karpathy Memory** as structured notes; keep H9 as an index that references them.
- **Compose with H1, do not subsume it.** H9 details fan out from H1's headline self-model line, but H1 stays invariant within a session — H9 is the layer that *evolves*. Do not let H9 rewrite H1.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H9 sits beside **H1 Identity Persistence** at session start (H1 invariant, H9 evolving) and consumes **K11 Observational Memory** at session end. It feeds **H2 Episodic Self-Improvement** with failure entries and **H4 Procedural Skill Accumulation** with success entries; in multi-agent systems it feeds **O3 Routing** the demonstrated-capability data. Bulk detail factors out to **K12 Karpathy Memory** when budget bites; the Updater is bounded by **V9 Bounded Execution** and audited via **V14 Trajectory Logging**.

**The chain — load (every session start):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| L1 | Load H1 (invariant identity) at position 0 | `code` | H1 |
| L2 | Selector picks task-relevant entries from Self-Knowledge Store | `code` (or small `LLM`) | Selector session |
| L3 | Inject selected entries after H1, before working context | `code` | |

**The chain — self-query (per agent step, on demand):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| Q1 | Detect a self-referential question / capability-estimate need | `code` | |
| Q2 | Self-Query Handler returns grounded answer from loaded entries | `LLM` (or `code` if templated) | Self-Query session |

**The chain — update (at session end / milestone):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| U1 | Gather K11 activity log + entries it touched | `code` | K11 |
| U2 | Updater proposes additions and revisions, with confidence + dates | `LLM` | Updater session |
| U3 | Decay function ages every entry by elapsed time | `code` | |
| U4 | Compress / archive if over budget | `LLM` | K6 / K12 |
| U5 | Versioned write to the Self-Knowledge Store | `code` | V14 (logged) |

**Skeleton:**

```
load_session(query, store, identity):
    context = identity.load()                          # code — H1 at position 0
    entries = Selector(store.index, query)              # code or LLM
    return context + entries                            # injected after H1

self_query(question, loaded_entries):
    return SelfQuery(question, loaded_entries)          # LLM — grounded report

end_session(activity_log, store):                       # at trigger only
    touched   = store.entries_touching(activity_log)    # code
    proposals = Updater(touched, activity_log)          # LLM — additions + revisions
    store.apply(proposals)                              # code
    store.decay_all(now())                              # code — half-life ageing
    if store.size_over_budget():
        store = Compressor(store)                       # LLM — K6 / push detail to K12
    store.write(version=now())                          # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Updater** | capable generalist; updates are infrequent so quality matters more than speed | role: *"you maintain an agent's evolving self-knowledge record"*; the **field schema** (capability map / tool proficiency / domains / action history / commitments / current state); editing rules (record attempts not just successes; never claim untested capability; close commitments explicitly); confidence-and-date contract; the current entries this update will touch | the session's K11 activity log |
| **Selector** *(optional LLM)* | small fast generalist *or* a deterministic index | role: *"choose the self-knowledge entries relevant to the upcoming task"*; output: list of entry IDs; budget cap (≲ 1–2k tokens loaded) | the task framing + the store's index |
| **Self-Query Handler** *(optional LLM)* | small fast generalist | role: *"answer self-referential questions strictly from the loaded entries; cite confidence and last-seen date; if no entry exists, say so"*; output contract (grounded response with citations or explicit no-record) | the self-referential question + the loaded entries |

**Specialist-model note.** No fine-tuned specialist is required, but the structural discipline is what makes H9 work and what distinguishes it from anti-pattern HA5: (1) the **Updater is a separate session from the Agent** — same model is fine, never invoked mid-session, or the agent writes its own performance reviews; (2) every entry carries **attempts, successes, last-seen date, and confidence** — without all four, success-rate is a fiction; (3) the **Decay function runs on every update** — un-decayed self-knowledge is the HA5 anti-pattern; (4) the **Self-Query Handler must return "no record" when there is none** — fabricating capability is the failure the pattern exists to prevent. Skipping any of the four turns H9 into "an H1 with extra unverified fields."

## Open-Source Implementations

H9 as an integrated GoF-style pattern is emerging; the closest production embodiments are the Letta family of memory-block frameworks plus recent metacognition / self-awareness research.

- **Letta** (formerly MemGPT) — [`github.com/letta-ai/letta`](https://github.com/letta-ai/letta) — the closest production embodiment. Core memory blocks include capability-and-state material in the `persona` block; archival memory + `memory_replace` / `memory_insert` / `memory_rethink` tools cover the persistent record + governed update. Letta is to H9 what it is to H1 — the canonical concrete substrate.
- **Letta Code** — [`github.com/letta-ai/letta-code`](https://github.com/letta-ai/letta-code) — memory-first coding agent; its `/init` command runs deep research over a codebase and writes capability- and knowledge-domain-shaped memory blocks. This is H9 in practice for the coding-agent case.
- **Letta AI Memory SDK** — [`github.com/letta-ai/ai-memory-sdk`](https://github.com/letta-ai/ai-memory-sdk) — the "subconscious agent" that asynchronously curates the memory blocks corresponds structurally to H9's Updater.
- **KnowSelf (ACL 2025)** — [`github.com/zjunlp/KnowSelf`](https://github.com/zjunlp/KnowSelf) — *agentic knowledgeable self-awareness*: trains agents to recognise when knowledge is needed and emit special tokens marking "fast / slow / knowledgeable" thinking. The closest research embodiment of explicit self-knowledge as a first-class agent capability.
- **MUSE — Metacognition for Unknown Situations and Environments** — [arXiv 2411.13537](https://arxiv.org/abs/2411.13537) — framework integrating metacognitive self-awareness and self-regulation into autonomous agents; agents continuously assess their own competence. Paper-only (HRL Laboratories) — no canonical repo at time of writing; cited as a research reference rather than a deployable project.
- **Agent Memory Techniques** — [`github.com/NirDiamant/Agent_Memory_Techniques`](https://github.com/NirDiamant/Agent_Memory_Techniques) — 30 runnable notebooks covering Letta, Mem0, Zep, Graphiti, episodic and semantic memory; the capability- and history-tracking patterns that compose into H9 are demonstrated across several of these.

## Known Uses

- **Letta-built personal-assistant and coding agents** — `persona` memory blocks that carry capability and history claims; updated by governed self-edits; surface to users as grounded "what do I know" answers.
- **Claude Code, Cursor, and similar coding agents** — project-level `CLAUDE.md` files that accumulate a record of *what has been done in this codebase* alongside conventions; this is H9 at the project layer, paired with H1 at the agent-identity layer.
- **Multi-agent routing systems** — internal track-record databases that record per-agent success rates by task type, used by an O3 Router to assign work to the agent best demonstrated to handle it (rather than by declared capability).
- **Letta `letta-code` `/init`** — explicitly described as forming "memories" about the codebase the agent will work on; an H9-shaped capability and knowledge-domain map written on first contact.

## Related Patterns

- **Pairs with** H1 Identity Persistence — H1 holds the *invariant* identity (who I am); H9 holds the *evolving* self-knowledge (what I have done, what I can do). H1's headline self-model line points at H9; H9 details fan out from it. Use both together — H1 alone goes stale on detail, H9 without H1 has no anchor.
- **Composes with** K11 Observational Memory — K11 is the session-scoped raw activity log; H9 is the life-span self-model. K11 feeds H9 at session end: the Updater reads K11's log to derive H9 entries.
- **Composes with** K12 Karpathy Memory — when H9's detail outgrows the budget, push action history and knowledge-domain detail into K12 as structured notes; H9 retains an index that references them.
- **Composes with** K6 Context Compression — compresses the loaded H9 subset (Chain-of-Density) when it approaches the budget.
- **Feeds** H2 Episodic Self-Improvement — H9's failure entries are the source material for H2's lesson library.
- **Feeds** H4 Procedural Skill Accumulation — H9's successful-capability entries are the demonstrated-skill side of the experience record; H4 writes the parameterised procedure, H9 records the demonstrated competence.
- **Feeds** O3 Routing and O6 Orchestrator-Workers — in multi-agent systems, H9's Capability Map is the data structure capability-based routing reads from.
- **Composes with** V9 Bounded Execution (caps the Updater) and V14 Trajectory Logging (audits every self-model change).
- **Distinct from** H1 — H9 is *not* a more-detailed H1; it is a different field schema (track record, not values + voice) under a different read/write discipline (evolves between sessions vs. invariant within).
- **Distinct from** K10 Long-Term Memory — K10 is a vector store of flat fact-shaped items retrieved by similarity; H9 is a structured per-field self-knowledge record retrieved by name / topic / recency.
- **Anti-pattern guarded against:** **HA5 Stale Self-Model** — H9 without decay functions becomes an agent that confidently claims capabilities it has lost. The Decay function is not optional.
- **Cognitive grounding** — Baddeley (2000) Working Memory model: the *central executive* component handles self-monitoring; H9 is that function externalised at the agent level. Tulving (1985) episodic vs. semantic memory: H9 holds the agent's *semantic self-knowledge*, derived from the *episodic* record K11 keeps.

## Sources

- Shang, W. (2026) — "'Theater of Mind' for LLMs: A Cognitive Architecture Based on Global Workspace Theory." arXiv [2604.08206](https://arxiv.org/abs/2604.08206). Epistemic state tracking as a first-class Global Workspace component.
- Baddeley, A. (2000) — "The episodic buffer: a new component of working memory." *Trends in Cognitive Sciences*. The central-executive / self-monitoring function H9 externalises.
- Tulving, E. (1985) — "Memory and Consciousness." Episodic vs. semantic memory; H9 holds semantic self-knowledge derived from the episodic record.
- Packer et al. (2023) — "MemGPT: Towards LLMs as Operating Systems." arXiv [2310.08560](https://arxiv.org/abs/2310.08560). Operating-system model with explicit self-management; the predecessor of Letta.
- Qiao et al. (2025) — "Agentic Knowledgeable Self-Awareness" (ACL 2025; *KnowSelf*). arXiv [2504.03553](https://arxiv.org/abs/2504.03553). Trained agentic self-awareness as a first-class capability.
- Valiente & Pilly (2024) — "Competence-Aware AI Agents with Metacognition for Unknown Situations and Environments (MUSE)." arXiv [2411.13537](https://arxiv.org/abs/2411.13537). Metacognitive self-awareness and self-regulation for competence estimation.
- 12-Factor Agents Factor 4 — *Own Your State, Separate from Session* — state as a first-class architectural concern; the operational underpinning for any persistent self-model.
