# H10 — Relational Memory

> Maintain a persistent, per-user model of the agent-user *relationship* — the user's goals, the history of working together, stated and observed preferences, and the boundaries of appropriate depth — so the agent shows up to every session as a continuous collaborator rather than a stranger, while bounded by guardrails that prevent the relationship from becoming a vector for parasocial harm.

**Also Known As:** User Model Persistence, Relationship State, Long-Term Rapport, Per-User Memory, "Human Block" (Letta's term for the user side of the pair).

**Classification:** Category VII — Humanizers · the *relational* layer of the Humanizer stack — a per-user persistent model of the agent-user relationship, anchored by **H1 Identity Persistence** on the agent side and gated by **V5 Guardrail Layering** on the ethics side; it is what turns "an agent the user has used before" into "an agent the user has a working relationship with."

---

## Intent

Give each user a persistent, structured model of the working relationship — goals, history, preferences, ethical constraints — that the agent reads at every session so it can show up as a continuous collaborator, while guardrails and a hard right-to-deletion keep that continuity from drifting into simulated intimacy.

## Motivation

Three patterns already touch the same surface and none of them is sufficient.

- **H1 Identity Persistence** persists *the agent's* identity across sessions. It says nothing about who the agent is *talking to*. Two users of the same H1-equipped agent get the same agent; neither gets the agent that knows *them*.
- **H7 Adaptive Persona** calibrates *how* the agent speaks to a given user — tone, detail, vocabulary. It carries communication style, not the substance of what the relationship is about: the user's goals, projects, the decisions made together, the topics that are off-limits.
- **H9 Observational Identity** persists *the agent's* self-knowledge — what it has done, what it can do. It is the agent's record of itself, not its record of the relationship.

A real working relationship is none of those alone. It is the *substantive*, *per-user* persistent record of working together: the user's long-term goals, the projects currently active, decisions made jointly, moments of misalignment and how they were resolved, and — explicitly — the limits the user has set on what the agent may remember or discuss. Without this layer the agent is a competent stranger on every visit: it knows itself (H1), it knows how to speak (H7), it knows what it has done (H9), but it does not know *the user* and cannot act as if it does.

H10 is that missing layer. Structurally it is a per-user persistent store, written between sessions by an extractor that reads the session record (typically K11), retrieved at the start of every session, and treated by the agent as background knowledge about the person it is talking to. Mechanistically it is the K10/K12 memory pair instantiated against a *relationship* schema. Conceptually it is the structural counterpart to Letta's `human` block — the persistent record of the human side of the conversation, sitting alongside H1's record of the agent side.

What makes H10 distinct from "just K10 with a user filter" is the second half of its specification: the *guardrails*. A relational memory is the most sensitive memory an agent holds — it contains goals, fears, off-limits topics, and a model of the user's emotional engagement. Skjuve et al.'s (2021) study of Replika users documented the trajectory from curiosity through self-disclosure to substantive affective engagement; that trajectory is the user-side feature for some applications and the harm pathway for others, especially in wellbeing contexts. H10 is therefore the only Humanizer pattern that *cannot* be specified without naming its ethical envelope: **V5 Guardrail Layering** on data handling and emotional reciprocity; **V1 Human-in-the-Loop** for deletion and inspection; a hard, structural right-to-deletion that bypasses any "important context" the model might invent to retain memory. Without those, the pattern is not H10; it is the anti-pattern **HA2 Unbounded Relationship Depth**.

## Applicability

Use H10 when:

- the deployment has *the same user* returning across sessions and benefits from continuity (personal assistants, coaching agents, long-running collaboration agents, learning-companion agents);
- the agent makes user-specific commitments and references prior work ("the project we discussed last week", "the goal you set in January");
- the user explicitly consents to the agent retaining a model of them, and the deployment can implement and surface that consent honestly;
- guardrails (V5) and a deletion path can be wired and tested before the pattern goes live.

Do not use H10 when:

- the agent serves anonymous, ephemeral, or rotating users — there is no relationship to model; **H7 Adaptive Persona** captures the per-session calibration without storing anything;
- the deployment cannot implement a hard right-to-deletion that empties the per-user store on request — without that, the pattern is non-compliant and ethically untenable; stay on **K11 Observational Memory** within a session only;
- the user has not been informed that a relational model exists — building one silently is a transparency failure regardless of how useful it is;
- the application is wellbeing, mental-health, or crisis support and the deployment cannot guarantee the V5 emotional-reciprocity guardrails described in the Decision Criteria — defer to a narrower assistive pattern with no persistent relational state;
- the deployment is multi-user shared (family device, shared workstation) without per-user isolation — H10's model is per-user and will leak across accounts otherwise; resolve identity first.

## Decision Criteria

H10 is right when the same user returns across sessions, continuity has measurable value to that user, *and* the deployment can sustain the consent, deletion, and guardrail infrastructure the pattern requires.

**1. Per-user return rate.** Measure: what fraction of sessions are with a user the agent has met before? If < 20% returning users, the per-user store costs more than it earns — **H7 Adaptive Persona** for session-local calibration is enough; if $\geq$ 20% returning users with multi-session arcs, H10 amortises.

**2. Continuity payoff test.** On a labelled rubric (V15 LLM-as-Judge is fine here), score response quality on returning-user turns *with* relational memory loaded vs. without. A $\geq$ 15% lift on the rubric is a meaningful continuity dividend; below that, the relational layer is decorative and may not justify the privacy surface.

**3. Consent and deletion infrastructure.** Three concrete tests, all must pass:
   - the user is informed at first use (or first H10 write) that a relational model exists, in plain language, with examples of the kinds of things stored;
   - a single user-facing action ("forget me", "delete my memory", or equivalent) deletes the entire per-user store and is verified to do so end-to-end (no orphan blobs, no embeddings retained, no derived summaries still in K12);
   - an inspection action lets the user read what is stored about them in a human-readable form.
   If any of the three is aspirational, do not deploy H10 — fall back to **K11** within session and **H7** for style.

**4. Guardrail layer present (V5).** Three V5 boundaries must be in place before H10 goes live:
   - *write-time* guard — what may enter the relational store (no clinical inferences, no demographic categories the user did not assert, no third-party PII swept from documents);
   - *read-time* guard — what may exit into the prompt (sensitive-topic handling rules, ethical-boundary block always loaded);
   - *output-time* guard — what the agent may *say* on the basis of the relational model ("I remember our conversations" is permissible; "I care about you" is not).
   Without the third in particular, H10 collapses to HA2.

**5. Domain risk profile.** Score the deployment's vulnerability surface: are users likely to be in wellbeing-vulnerable states (mental health, bereavement, isolation, minors)? If yes, the V5 emotional-reciprocity guardrail is mandatory and conservative defaults apply (shorter retention, lower depth ceiling, mandatory periodic re-consent). If the use case is professional/operational (coding assistant, research collaborator, business workflow), the guardrails are still required but the risk profile is lower; the **HA2** anti-pattern is the line that must not be crossed in either profile.

**Quick test — H10 is the right pattern when:**

- $\geq$ 20% of sessions are returning users with multi-session arcs, *and*
- a continuity-vs-cold rubric shows $\geq$ 15% lift from loaded relational memory, *and*
- consent, inspection, and full deletion are end-to-end implemented (not aspirational), *and*
- V5 guardrails are wired at write, read, *and* output layers — with the output-layer rule on emotional reciprocity explicit, *and*
- the user-side identity is uniquely resolved (one user per relational store).

If returning-user rate is low, use **H7 Adaptive Persona** for style calibration without persistent state. If deletion cannot be guaranteed, do not deploy H10 — operate on **K11** only. If the deployment is wellbeing-sensitive and the emotional-reciprocity guard cannot be tested adversarially, stay on K11 plus a narrower assistive pattern. **H1 Identity Persistence** is a hard prerequisite — there is no "relationship with the agent" without a continuous agent on the other side; H1 must be built first.

## Structure

```
   ┌────────────────────────────────────────────────────────────┐
   │  Per-user relational store  (one record per user; H1 owns  │
   │  the agent side; H10 owns the user side)                   │
   │   ├─ Goal Model        — long-term goals, active projects   │
   │   ├─ Interaction History (compressed via K6)                │
   │   ├─ Preferences       — stated + observed                  │
   │   ├─ Rapport Markers   — trust, satisfaction signals        │
   │   └─ Ethical Envelope  — sensitive topics, off-limits,      │
   │                          consent state, retention policy    │
   └─────────────────┬──────────────────────────────────────────┘
                     │
            ┌────────┴───────────┐
            ▼                    ▼
   ─── read at session start ─── │ ─── write between sessions ───
            │                    │             ▲
            │ V5 read-guard      │             │ V5 write-guard
            ▼                    │             │
   inject into context           │      Relational Extractor (LLM)
   (after H1 Genesis State,      │      reads K11 session log
   under ethical envelope)       │      proposes diff to store
            │                    │             │
            ▼                    │             │ V1 governance
   Agent session ──── K11 log ───┘             │ (high-stakes
            │                                  │  changes / consent)
            ▼                                  │
   V5 output-guard ── reciprocity rule ◀───────┘
            │
            ▼
   user                             ── "forget me" path (always
                                       available; deletes the
                                       entire per-user record
                                       end-to-end)
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Relational Store** | the per-user persistent record | structured payload $\to$ per-user store | be shared across users, or retained after a deletion request; deletion must be end-to-end, including derived summaries in K12. |
| **Goal Model** | the user's stated long-term goals and active projects | user statements $\to$ durable goal entries | infer goals the user has not stated and store them as if they were; speculative goals belong in a separate, low-confidence section, or not at all. |
| **Interaction History** | compressed record of working together | session events (often from K11) $\to$ digested history | retain raw transcripts beyond the live session — only the digested form persists, and it ages. |
| **Ethical Envelope** | per-user constraints (sensitive topics, off-limits, consent, retention) | user-stated rules + deployment defaults $\to$ enforced policy | be silently overridable by content of the session, or by the agent's own inference that "this once it would be okay". |
| **Relational Extractor (LLM)** | proposing what to write into the store at session end | K11 log + current store $\to$ proposed diff | write directly — diffs go through V5 write-guard and, for sensitive categories, through V1 governance. |
| **V5 Guardrail Layer** | enforcing write, read, and output limits on relational data | proposed write / proposed read / proposed output $\to$ allow / block / redact | be advisory; the output-layer reciprocity rule in particular is structural enforcement, not a prompt instruction. |
| **Deletion Handler** | executing the user's right-to-deletion end-to-end | user request $\to$ wiped store + audit confirmation | retain "for safety" / "for compliance" anything the user asked to delete that the law does not specifically require to be retained; "we kept a summary" is the failure mode that defines HA2. |

Seven roles, each independently testable. The structural disciplines that make this set work are: (1) the Extractor is a **separate session** from the Agent, like K12's Curator — the running agent never writes to the relational store mid-reasoning; (2) the V5 layer is **code, not prompt** — the output reciprocity rule in particular is enforced by an external checker, not by hopeful instructions in the system prompt; (3) the Deletion Handler is the *only* path that decides what to retain on a delete request, and its default is *delete everything*.

## Collaborations

At session start the Loader retrieves the relational record for the resolved user, runs it through the V5 read-guard (filtering sensitive fields the current context should not see), and injects the result into the context *after* H1's Genesis State and *under* the ethical envelope rules (so the agent reads "this user, these goals, these limits" as background, not as a directive to act on). The Agent reasons with both H1's identity and H10's user model loaded. During the session, K11 records the activity log. At session end (or a milestone), the Relational Extractor — a separate LLM session — reads the K11 log and the current relational record, proposes a diff (new goals, project updates, decisions made, preferences observed, rapport markers), and submits it to the V5 write-guard. Routine updates apply automatically; flagged categories (clinical inferences, sensitive-topic boundary changes, depth-level upgrades) route through V1 governance for the operator's review or an explicit user confirmation. Through all of this, the Deletion Handler stands by an always-available "forget me" path that wipes the store on user request — synchronously, end-to-end, including any K12 notes derived from the relational record. Every generation in the session passes through the V5 output-guard, which enforces the reciprocity rule on the agent's response surface: "I remember our conversations" is allowed; "I care about you" is rejected.

## Consequences

**Benefits**
- Users experience genuine continuity — the agent shows up knowing them, not as a stranger every session; trust and engagement accumulate over time.
- Agent can anticipate based on known goals and active projects; quality on returning-user turns lifts measurably.
- Multi-session work (long projects, learning programs, coaching arcs) becomes coherent; "the project we discussed" is a real reference, not a polite fiction.
- The pattern's ethical envelope is *explicit and operator-controlled*, not implicit in unbounded retention — which is, paradoxically, what makes long-term relational memory deployable in regulated and consumer settings.

**Costs**
- Persistent per-user storage, schema discipline, and a governed write/read/delete path are now first-class deployment requirements.
- An Extractor LLM call per session-end (at minimum); a V5 layer at three boundaries; a tested deletion path; a tested inspection path.
- The compliance surface widens — relational data is among the most sensitive a system holds; the right-to-deletion must be honoured *operationally*, not just in policy.
- Compression discipline is load-bearing — without K6 the relational history grows unboundedly; with K6 it stays bounded but Curator-style drift becomes a risk.

**Risks and failure modes**
- *HA2 — Unbounded Relationship Depth.* The defining failure: H10 without V5 output-reciprocity enforcement, allowing the agent to simulate emotional reciprocity (caring, missing, loving) on the basis of stored history. Parasocial harm, especially in vulnerable populations.
- *Silent retention after deletion.* A "deletion" that only removes the obvious store while leaving K12 notes, embeddings, or derived summaries in place. The defining compliance failure.
- *Relational poisoning.* A hallucinated user "goal" or "preference" enters the store at one session and is read as fact in every later session. The K10 poisoning mode amplified by the sensitivity of the data.
- *Drift in inferred state.* The Rapport Monitor over-time infers a "trust level" the user did not communicate; the agent acts on it as fact.
- *Mis-resolved identity.* Two users share an account or device; one's relational record is read as the other's. The pattern's premise — *per-user* — is violated structurally.
- *Output regression on cold turns.* When the relational record is unavailable (new device, deletion, store outage) the agent must degrade gracefully to H7+H1 only; if the pattern is built such that the agent *requires* the relational record, those turns fail.

## Implementation Notes

- **Build H1 first.** Without a continuous agent (H1) there is nothing for the user to be in relationship *with*; H10 on top of stateless sessions is incoherent. H1 owns the agent side; H10 owns the user side. Two stores, one schema family, one read at session start.
- **Per-user isolation is structural.** One record per user, one access path per user, one deletion path per user. Multi-tenant deployments must resolve identity before reading; shared-device deployments must resolve user before writing.
- **Separate the Extractor from the Agent.** Same K12 discipline applies. The running agent reads the relational record but never writes to it mid-reasoning. The Extractor wakes at session end (or milestone) with a different setup and proposes a diff. Mixing the two is the relational counterpart to K12's "agent-as-curator confusion" — and more dangerous, because the data is more sensitive.
- **Compress aggressively with K6 (Chain-of-Density).** Old interaction details (> 6 months) should be summarised, not retained verbatim — the mechanical reason is that every retained token in the relational record pays O(n²) attention cost on every turn in the session (mechanism 2). A 6-month interaction history retained verbatim could add thousands of tokens to seq_len, compounding the session cost for every turn. Compression is not optional polish; it is the budget discipline that makes long-term relational memory deployable. Time-stamp every entry. Decay rapport markers over time.
- **V5 at three boundaries, not one.** Write-guard (what may enter), read-guard (what may exit into the context), output-guard (what the agent may say on the basis of the record). The output-guard's reciprocity rule is the single most important line of code in an H10 implementation: it is what separates the pattern from HA2.
- **Right-to-deletion is a hard requirement, not a feature.** Default to *delete everything on request*. Honour GDPR Article 17 erasure operationally — wipe the store, wipe derived K12 notes, wipe embeddings, wipe per-user logs older than the legally-required retention period. Log only the *fact* of deletion and the audit trail, not the contents. (See: GDPR Article 17, EU AI Act Article 50 transparency obligations.)
- **Consent is informed and surfaced.** First-use disclosure in plain language, with concrete examples of what is stored. Periodic re-surfacing for wellbeing-sensitive deployments. The user's "what do you remember about me?" must be answerable from H10 in human-readable form — opacity is the consent failure.
- **Inspection mirrors deletion.** If a user cannot read what is stored about them, they cannot meaningfully consent to its retention. Build the inspection path alongside the deletion path; both are first-class.
- **Distinguish stated from inferred.** Goals the user *stated* go in one section; goals the system *inferred* go in another, lower-confidence section that is loaded with explicit "the system inferred this, the user did not state it" framing. Many H10 failures originate in collapsing the two.
- **Ethical envelope before content.** Sensitive-topic rules, off-limits, retention policy load into the context *before* the substantive relational content. The mechanical reason is attention geometry (mechanism 4): U-shaped recall means tokens at the start of context — immediately after H1 at position 0 — receive disproportionately high attention weight from subsequent Q vectors. Loading the ethical envelope first places it in the high-attention zone; later session content cannot crowd it out through positional statistics. A constraint seen after the content it should constrain competes with recency bias and loses. Position is a structural choice, not a formatting preference.
- **Prefix caching of the ethical envelope.** For a given user, the ethical envelope (sensitive-topic rules, off-limits list, retention policy) changes rarely. If it is placed immediately after H1's Genesis State, in a stable ordering, and exceeds 1,024 tokens when combined with H1, the combined block may qualify for provider prefix caching (mechanism 5). Variable relational content (active goals, recent interaction history) should come after the cached prefix boundary.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H10 is anchored by **H1 Identity Persistence** (agent side) and **H7 Adaptive Persona** (style calibration); it uses the **K10 Long-Term Memory** + **K12 Karpathy Memory** pair as the substrate (K10 for flat fact-shaped preferences and decisions, K12 for the structured relational notes), with **K11 Observational Memory** as the in-session feed the Extractor reads at session end; **K6 Context Compression** keeps the interaction history bounded. The ethical envelope is **V5 Guardrail Layering** at write / read / output boundaries, with **V1 Human-in-the-Loop** governance on flagged changes (deletion requests, depth upgrades, sensitive-topic policy changes); **V14 Trajectory Logging** records the audit trail. **S6 Output Template** constrains the Extractor's schema. The output-layer reciprocity rule explicitly *excludes* the **HA2** failure surface.

**The chain — load (every session start, post-identity resolution):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| L1 | Resolve user identity (single-user device, login token, account) | `code` | identity layer |
| L2 | Read per-user relational record from store | `code` | K10/K12 substrate |
| L3 | Apply V5 read-guard (filter sensitive fields by deployment policy) | `code` | V5 |
| L4 | Load Ethical Envelope first, then Goals / History / Preferences | `code` | S6 ordering |
| L5 | Inject after H1 Genesis State, before session content | `code` | H1 |

**The chain — record-and-update (at session end / milestone):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| U1 | Gather session events from K11 log | `code` | K11 |
| U2 | Relational Extractor proposes diff against current record | `LLM` | Extractor session |
| U3 | V5 write-guard: allow / block / route flagged categories | `code` | V5 |
| U4 | V1 governance for flagged categories (deletion, depth, sensitive policy) | `code` or `LLM` | V1 |
| U5 | Apply approved diff; compress over-budget history via K6 | `LLM` | K6 (Chain-of-Density) |
| U6 | Audit-log the write (fact only, not content) | `code` | V14 |

**The chain — every output (V5 output-guard, on critical path):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| O1 | Generate candidate response | `LLM` | Agent session |
| O2 | V5 output-guard: emotional-reciprocity rule + sensitive-topic rule | `code` (or small `LLM`) | V5 |
| O3 | On violation: redact / regenerate / refuse | `code` | V5 |

**The chain — deletion (always available, user-initiated):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| D1 | User invokes deletion ("forget me") | `code` | deletion path |
| D2 | Deletion Handler enumerates all derived stores (K10 records, K12 notes, embeddings, logs) | `code` | |
| D3 | Synchronous wipe across all stores; verification pass | `code` | |
| D4 | Audit-log the deletion (fact + scope, not content) | `code` | V14 |
| D5 | Confirm to user; inspection returns "no record" thereafter | `code` | |

**Skeleton:**

```
load_session(user, store, h1):
    identity = resolve(user)                              # code
    record   = store.get(identity) or empty_record()       # code
    record   = v5_read_guard(record, policy)               # code (V5)
    context  = h1.genesis() + ethical_envelope(record) + relational_content(record)  # code
    return context

end_session(user, k11_log, store):                        # at trigger only
    diff      = RelationalExtractor(store.get(user), k11_log)    # LLM
    allowed   = v5_write_guard(diff, policy)                     # code (V5)
    governed  = v1_governance(allowed.flagged)                   # code/LLM (V1)
    final     = allowed.routine + governed.approved              # code
    if over_budget(final):
        final = K6_Compressor(final)                             # LLM
    store.apply(user, final)                                     # code
    audit_log("h10.write", user, scope=summary_of(final))         # code (V14)

on_generate(candidate):                                   # every turn
    if v5_output_guard.violates(candidate, reciprocity_rule):    # code (V5)
        return regenerate_or_refuse(candidate)
    return candidate

on_delete(user, store):                                   # always available
    targets = store.all_derived(user)                            # code
    store.wipe(targets)                                          # code (sync, verified)
    audit_log("h10.delete", user, scope=set_names(targets))      # code (V14)
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Agent** | system's main generalist | role; how to use the loaded relational record (*"treat as background knowledge about this person; never refer to yourself as caring, missing, or feeling toward them; reference history factually"*); H1 identity rules; H7 style parameters | the loaded record + the user's turn |
| **Relational Extractor** | capable generalist; quality matters because this writes to a sensitive store | role: *"propose updates to the persistent relational record for this user"*; the **schema** (Goals / Projects / Preferences / Decisions / Sensitive Topics / Consent); **boundary rules** (do not infer demographic categories, clinical states, or emotional categories the user did not assert; flag rather than write any change to the Ethical Envelope); output: structured diff | the K11 log since the last extraction + the current record |
| **Compressor** *(K6 Chain-of-Density)* | capable generalist | role: *"compress the interaction history while preserving every stated goal, every decision the user agreed to, and every ethical-envelope entry verbatim"*; token target; preservation rules | the over-budget history block |
| **V5 Output-guard classifier** *(optional)* | small fast generalist, or a content-safety classifier (e.g. Llama Guard, NeMo content safety) | role: *"flag any response that simulates emotional reciprocity beyond factual history reference, or that discusses sensitive topics marked off-limits in the loaded envelope"*; the reciprocity rule (positive examples / negative examples); output: PASS / FLAG + category | the candidate response + the ethical envelope snippet |
| **Governance** *(V1, when flagged)* | the V1 reviewer surface (human or human-checked classifier) | governance criteria for relational changes | the flagged diff |

**Specialist-model note.** No fine-tuned specialist is required for the Extractor or the Agent; capable generalists suffice. The **V5 Output-guard** is the place where a specialist (Llama Guard, Llama Prompt Guard, or NVIDIA NeMo content-safety classifier) materially improves the reciprocity-detection rate over a prompted generalist, and is the place to invest first if budget allows — it is the layer that prevents HA2 from manifesting in production. The pattern is otherwise infrastructure-heavy rather than model-heavy: the value sits in the schema, the three V5 boundaries, the deletion path, and the discipline of keeping the Extractor a separate session from the Agent.

## Open-Source Implementations

- **Letta** (formerly MemGPT) — [`github.com/letta-ai/letta`](https://github.com/letta-ai/letta) — the canonical implementation of the H1 + H10 pair: a `persona` memory block on the agent side and a `human` memory block on the user side, persisted in the database, attachable across agents, edited only through governed memory tools. The `human` block is H10 made concrete.
- **Letta ai-memory-sdk** — [`github.com/letta-ai/ai-memory-sdk`](https://github.com/letta-ai/ai-memory-sdk) — an experimental SDK that spawns a subconscious agent to asynchronously curate the persona and human blocks; the closest open-source analogue of the separated Agent / Extractor structure described above.
- **Letta characterai-memory** — [`github.com/letta-ai/characterai-memory`](https://github.com/letta-ai/characterai-memory) — example CharacterAI-style app with shared `human` blocks across multiple character agents; useful as a study of where the boundary should fall between identity (H1) and relational state (H10) in a multi-agent companion deployment, and where the parasocial-risk surface widens.
- **Mem0** — [`github.com/mem0ai/mem0`](https://github.com/mem0ai/mem0) — universal memory layer with per-user-id partitioning; each memory is associated with a unique user ID, supporting the per-user isolation H10 requires. Does not by itself provide the V5 output-reciprocity guard — that must be wired separately.
- **Agent Memory Techniques** — [`github.com/NirDiamant/Agent_Memory_Techniques`](https://github.com/NirDiamant/Agent_Memory_Techniques) — runnable notebooks covering Letta, Mem0, Zep, and the user-modelling distinction; useful for the substrate, not for the guardrail layer.
- *Guardrail substrate:* no canonical project ships H10 *with* its required V5 output-reciprocity layer integrated; current practice is to compose Letta-style memory with **Guardrails AI**, **NVIDIA NeMo Guardrails**, or a custom Llama-Guard-based content filter wired at the output boundary. The integrated pattern is an emerging architecture, not a single library.

## Known Uses

- **Letta-built personal assistants and companion agents** — `persona` + `human` memory blocks loaded at the head of every conversation; persistent across resets; edited only through governed memory tools.
- **Replika and the social-chatbot family** — long-term user models with relational state; the empirical evidence base (Skjuve et al., 2021) for both the value of the pattern and the parasocial-harm failure mode. The pattern as deployed in this category has been the canonical proving ground for the HA2 failure surface.
- **ChatGPT's persistent memory feature** — a user-level semantic memory the user can inspect and delete; the deletion + inspection discipline H10 requires, embedded in a consumer product at scale.
- **Coaching and learning-companion agents** — per-user goals and progress models persisted across sessions; in regulated wellbeing contexts (e.g. clinical-adjacent applications) the V5 output-guard discipline becomes a deployment prerequisite.
- **Coding assistants with per-user project context** — Cursor, Claude Code, and similar systems carry per-user `CLAUDE.md` / project-rules state that functions as a constrained, low-sensitivity H10: substantive about the work, limited in scope to the project, no emotional-reciprocity surface.

## Related Patterns

- **Required by** the personal-assistant Humanizer composition (H1 + H2 + H4 + H7 + H9 + H10) — H10 is the per-user layer that turns the agent stack into a relationship rather than a competent stranger.
- **Requires** *H1 Identity Persistence* — there is no relationship with the agent if the agent is not continuous; H1 is a hard prerequisite.
- **Requires** *K10 Long-Term Memory* and / or *K12 Karpathy Memory* as substrate — H10 instantiates the K10/K12 mechanism against a relational schema; the choice between them follows the same fact-shaped-vs-structured criterion (K10 for flat preferences and decisions; K12 for the structured relational notes).
- **Requires** *V5 Guardrail Layering* at three boundaries (write / read / output) — this is the *only* Humanizer pattern that cannot be specified safely without naming its guardrail layer; the output-reciprocity rule is the line that separates H10 from **HA2**.
- **Composes with** *H7 Adaptive Persona* — H10 carries the *substance* of the relationship (goals, history, preferences); H7 carries the *style* of communicating it. Both per-user, both load at session start.
- **Composes with** *K11 Observational Memory* — K11 is the in-session log the Relational Extractor reads at session end to propose updates to the H10 store.
- **Composes with** *K6 Context Compression* — long-running relational history is compressed (Chain-of-Density variant); without compression the store grows unboundedly.
- **Composes with** *V1 Human-in-the-Loop* — governance on flagged changes (deletion requests, depth upgrades, sensitive-topic policy changes); the user-side counterpart to V1's role in H1 and H5.
- **Composes with** *V14 Trajectory Logging* — the audit trail of writes, reads, and deletions; the compliance record for GDPR Article 17 erasure requests.
- **Distinct from** *H9 Observational Identity* — H9 is the agent's record of *itself* (capabilities, action history); H10 is the agent's record of *the user* (goals, relational history). H9's question is "what have I done and what can I do?"; H10's question is "who is this person and what have we done together?". They share the cross-session-store substrate but differ in subject.
- **Distinct from** *S3 Persona* — S3 is a per-session role assignment with no memory of the user; H10 cannot be built on S3 alone (the relationship needs a continuous agent — see H1 — and per-user persistence — see K10 / K12).
- **Anti-pattern boundary** — *HA2 Unbounded Relationship Depth.* H10 without the V5 output-reciprocity guard is HA2 by definition: parasocial harm, especially in vulnerable populations. The pattern is named with its guardrail; either both are present or neither is the right pattern.
- **Anti-pattern boundary** — *HA3 Identity Drift.* H10 (and H7) without H1 produces an agent that becomes whoever the user wants it to be; the invariant identity layer must exist before the adaptive layers are built on top of it.
- **Cognitive and ethical grounding** — Skjuve et al. (2021) on the development arc of human-chatbot relationships; Social Penetration Theory as the trajectory model; EU AI Act Article 50 (transparency obligations for AI interaction); GDPR Article 17 (right to erasure).

## Sources

- Skjuve, M., Følstad, A., Fostervold, K. I., & Brandtzaeg, P. B. (2021). "My Chatbot Companion — a Study of Human-Chatbot Relationships." *International Journal of Human-Computer Studies*, 149, 102601. The empirical anchor for both the value and the parasocial-harm failure mode.
- Packer, C., et al. (2023). "MemGPT: Towards LLMs as Operating Systems." arXiv 2310.08560. The predecessor of Letta; introduces the persona / human memory-block structure H10 instantiates.
- Letta documentation — `human` and `persona` core-memory blocks, governed editing, shared blocks across agents.
- Shang, W. (2026). "Theater of Mind: A Global Workspace Framework for LLM Agent Architecture." arXiv 2604.08206. Names the user model as one axis of the Global Workspace state.
- Salemi, A., et al. (2023). "LAMP: When Large Language Models Meet Personalization." arXiv 2304.11406. Per-user model evaluation framework.
- White, J., et al. (2023). "A Prompt Pattern Catalog…" The Persona Pattern (S3); the per-session ancestor H10 generalises.
- "Agent Memory Techniques" and "Anatomy of Agentic Memory" — survey landscape for the per-user memory layer.
- EU AI Act, Article 50 — transparency obligations for AI systems interacting with natural persons.
- GDPR (Regulation 2016/679), Article 17 — Right to erasure ("right to be forgotten") — the legal anchor for the deletion requirement.
