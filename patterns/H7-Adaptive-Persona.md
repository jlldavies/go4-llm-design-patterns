# H7 — Adaptive Persona

> Treat communication style — detail level, technical depth, format, length, tone — as a continuously-estimated per-user parameter, inferred from explicit feedback and implicit interaction signals, and applied at generation time without ever crossing into the agent's invariant identity core.

**Also Known As:** User-Calibrated Style, Preference-Driven Voice, Dynamic Persona, User Style Model.

**Classification:** Category VII — Humanizer · the *expression-surface* counterpart to **H1 Identity Persistence**. H1 holds the invariant identity core (values, principles, hard self-model limits); H7 governs the *variable surface* (how that identity expresses itself to this particular user). H7 has no meaning without H1 — without a fixed core to vary against, "adaptive persona" collapses into the anti-pattern **HA3 Identity Drift**.

---

## Intent

Close the style gap between agent and user: infer how this user prefers to be communicated with — from explicit corrections, implicit engagement signals, and their own register — and apply those parameters at generation time, while explicitly preserving the identity invariants H1 holds constant.

## Motivation

**S3 Persona** assigns one persona at deployment, the same persona for every user. **H1 Identity Persistence** carries that persona across sessions but does not vary it by interlocutor. Both produce the same failure on a multi-user system: a single voice that fits some users well, others poorly, and shifts the burden of accommodation onto the user.

The personalisation literature is consistent on what this costs. The primary cause of user disengagement in long-term agent interaction is *style mismatch*, not capability gap — an expert user given beginner explanations disengages; a novice user buried in jargon disengages; a user who writes terse messages and receives long bulleted responses disengages. Salemi et al.'s **LaMP** benchmark (arXiv 2304.11406) showed that conditioning generation on a user's own profile materially changes the *acceptability* of an otherwise-correct answer. The model's knowledge was never the bottleneck; the *fit* was.

H7's move is to treat communication style as a small, structured, per-user model — five or six parameters, not a free-form persona — that the agent both *reads* (at generation time) and *updates* (from observed signals). The cognitive grounding is **Theory of Mind** (Premack & Woodruff, 1978): an agent that can act effectively in conversation imputes mental states to its interlocutor — what they already know, what register they speak in, how much detail they want — and adjusts its own production accordingly. H7 is Theory of Mind operationalised at the style layer: an explicit user model that lets the agent communicate *to this user*, not to a generic average user.

The tension with H1 is structural and load-bearing. H1 defines what must never change; H7 defines what may change per user. If the boundary is left implicit, gradual style adaptations leak into the identity core — the agent becomes "whoever the user wants it to be," losing the consistent contributor H1 was built to be. That failure has a name (**HA3 Identity Drift**) precisely because it is the predictable consequence of running H7 without explicit field-scope discipline. The pattern earns its number on the partition: *variable surface above an invariant core, with an enforced boundary between them*. Without that boundary, H7 is dangerous; with it, H7 is how an agent stops being everyone's average and starts being usefully theirs.

## Applicability

Use Adaptive Persona when:

- the agent serves *individual users* over time (personal assistants, coding assistants, coaches, educational agents);
- the user base is heterogeneous in expertise, register, or format preference (a single persona will misfit a meaningful fraction);
- explicit style corrections ("be more concise", "stop the jargon", "more detail next time") appear in the interaction logs — these are unambiguous signals the static persona is mispriced;
- a stable identity core already exists (**H1** in place) that the adaptation surface can vary against.

Do not use when:

- there is no **H1 Identity Persistence** — adapting style without an invariant core produces **HA3 Identity Drift**; install H1 first, or stay on **S3 Persona**;
- the system is single-session or anonymous — there is no "this user over time" to adapt to; use **S3 Persona** for the deployment-wide voice;
- a single regulated register is required by domain (legal, medical, safety-critical disclosures) — varying style by user is a compliance liability; use **S3** plus **S5 Constraint Framing** plus **V7 AgentSpec** to lock the register;
- the user count is so large per agent that no useful signal accumulates per user — fall back to coarse cohort-level personas chosen via **O3 Routing**.

## Decision Criteria

H7 is right when style mismatch is a measurable cost in this deployment, **H1** is in place to hold the invariant core, and per-user signal accumulates fast enough to be useful.

**1. Measure the style-mismatch cost.** Over a labelled period:
- **Explicit-correction rate** — what % of sessions contain an explicit style instruction ("be more concise", "more detail", "stop using jargon")? **> 5%** means a single persona is systematically mispriced and H7 earns its keep.
- **Rewrite-after-output rate** — what % of agent outputs the user materially rewrites? **> 10%** is a style-fit signal, not a content-correctness signal.
- **Disengagement-after-style-shift rate** — does engagement drop after long / short / formal / casual outputs? Any consistent pattern is an H7 lever.

If all three are low, **S3 Persona** alone is sufficient and H7 is overhead.

**2. Confirm H1 is in place.** H7 *requires* **H1 Identity Persistence** as substrate. Without H1, there is no invariant core for adaptation to vary against, and the adaptation gradually rewrites everything — **HA3 Identity Drift**. If H1 is absent, install it before H7; do not bolt H7 onto a stateless **S3 Persona** and call it adaptive.

**3. Enumerate the style fields explicitly.** H7 is not "the persona adapts." It is "**these specific fields** adapt, **these other fields** never do." Practical style fields: *detail level* (1–5), *technical depth* (1–5), *format preference* (bullets / prose / code / tables), *response length* (short / medium / long), *tone* (formal / casual / collaborative). Identity-core fields that **H7 may not touch**: values, refusal behaviour, safety register, capability claims, domain-truth statements, brand-voice invariants. If the field list cannot be written down before deployment, the partition will not survive operation.

**4. Per-user signal budget.** H7 needs enough per-user data to estimate parameters above noise. Practical floor: **≥ 5–10 interactions per user** before adapting beyond the deployment default. Below that, run S3's static persona and let signal accumulate. Above that, bound adaptation step size so a single unusual exchange does not jump the model. The style overlay is injected into every session context and remains in-context for all turns. It contributes to seq_len for the duration of the session, compounding the O(n²) attention cost on every turn (mechanism 2). Keep the overlay compact — the 5-field schema keeps this contribution to ~20–50 tokens, negligible. Free-form style expansions beyond the schema are a budget risk, not just a governance risk.

**5. Style-reset mechanism.** Users must be able to *explicitly reset* style preferences ("go back to defaults"). Without a reset path, a noisy or mis-inferred adaptation persists and the user has no recourse. Treat the reset as a first-class user-facing operation, not a hidden admin tool.

**Quick test — H7 is the right pattern when:**

- style mismatch is measurable in the deployment (explicit-correction or rewrite-rate exceeds threshold), *and*
- **H1 Identity Persistence** is already in place with an enumerated invariant core, *and*
- the style fields that may adapt — and those that may not — are written down before deployment, *and*
- per-user interaction volume is sufficient to estimate style parameters above noise, *and*
- an explicit reset mechanism is exposed to the user.

If any condition fails, **S3 Persona** is the right pattern. If H1 is missing, install H1 first or stop at S3. If multiple users share one persona by design (brand voice, regulated register), prefer **S3 + V7 AgentSpec** and route different users via **O3 Routing** rather than adapt.

## Structure

```
   ┌──────────────────────────────────────────────────────────┐
   │  H1 Identity Block (invariant — set at H1, frozen here)  │
   │   • values · principles · refusal · capability · brand    │
   └────────────────────────┬─────────────────────────────────┘
                            │ (read only, never written by H7)
                            ▼
   [ Generation context = H1 invariant + H7 style overlay ]
                            ▲
                            │
   ┌────────────────────────┴─────────────────────────────────┐
   │  H7 User Style Model  (per user, persistent, bounded)     │
   │   • detail level (1–5) · technical depth (1–5)            │
   │   • format pref · response length · tone                  │
   │   • reset flag · last-updated timestamp                   │
   └────────────────────────▲─────────────────────────────────┘
                            │ (written by Style Updater only)
                            │
   ┌────────────────────────┴─────────────────────────────────┐
   │  Style Updater  (at session end / on explicit feedback)   │
   │   ▲ explicit corrections   ▲ implicit signals             │
   │   │ ("be concise", ...)    │ (rewrite, length, register) │
   │   └────────────────────────┴──── Boundary Guard ──┐       │
   │                                  (rejects writes  │       │
   │                                   to H1 fields)   │       │
   └────────────────────────────────────────────────────┴──────┘
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **User Style Model** | the per-user style parameters (detail, depth, format, length, tone) | — → bounded numeric/categorical record | hold identity-core fields (values, refusal, brand). The model has a fixed schema; freeform additions are how H7 silently becomes H1. |
| **Style Inferrer** | extracting style signals from user messages and behaviour | recent turns + rewrites + corrections → proposed delta | infer *content* preferences ("user dislikes topic X") — that belongs in H10. H7 reads only *how*, never *what*. |
| **Style Updater** | applying a bounded delta to the User Style Model at the trigger | proposed delta + current model → updated model | edit mid-session; updates apply between sessions or on explicit feedback, never per turn. Continuous editing destabilises both the model and the cache. |
| **Boundary Guard** | refusing any write that touches an H1 invariant field | proposed delta → permitted delta (or rejection) | be advisory. The Guard is structural — a field-scope allowlist, not a soft warning. A delta that names an H1 field is dropped, not negotiated. |
| **Style Applier** | injecting the active style parameters into the generation context | User Style Model + H1 invariant block → composed setup | override H1 fields. The H1 block is read-only at this layer; the Applier composes them with the style overlay, never replaces them. |
| **Reset Handler** *(user-facing)* | restoring the User Style Model to deployment defaults on explicit request | user reset signal → defaulted model | be hidden. The reset path must be visible and reachable; a hidden reset is operationally absent. |

Six narrow responsibilities. The discipline is the **read/write asymmetry across the H1↔H7 boundary**: the Style Applier *reads* H1's invariant block to compose the generation context; the Style Updater *writes only* to the H7 User Style Model, never to H1. The Boundary Guard enforces that asymmetry at the structural level. The same separation discipline K12 enforces between Curator and Agent — and that **H1 enforces between session and Updater** — prevents the H7-rewrites-identity failure mode (**HA3**).

## Collaborations

A session opens. The Loader (an H1 mechanism) places the H1 invariant Identity Block at position 0. The Style Applier reads the user's User Style Model and composes a *style overlay* — detail level, depth, format, length, tone — beneath the invariant block, completing the setup. The Agent runs as normal; every turn the model produces is shaped by the composed setup (invariant identity + variable style). Within the session, the Style Inferrer watches for signals: an explicit correction ("be more concise"), a user-rewrite of an agent output, the user's own register and length. These accumulate as *proposed deltas* — but no write happens. At session end (or on receipt of an unambiguous explicit signal, e.g. "stop using jargon"), the Style Updater takes the proposed delta, the Boundary Guard checks that no field on the delta touches an H1 invariant (any attempt is dropped and logged), and the Updater applies a bounded step to the User Style Model. The next session loads the updated model. If the user invokes the Reset Handler, the User Style Model returns to deployment defaults; H1's invariant core is untouched throughout.

## Consequences

**Benefits**
- Users feel communicated *to*, not at — engagement and retention improve where they otherwise leak through style mismatch.
- Explicit "be more concise / give me more detail" instructions become rarer as the model converges.
- H1's invariant core stays clean — the partition makes "what about the agent has changed?" a question with a precise answer.
- Multi-user systems serve heterogeneous users from a single deployment without forking personas.

**Costs**
- Per-user state — every user adds a small persistent record; storage and privacy concerns scale with user count.
- Inference and update calls add latency and tokens; the style overlay also costs prompt-cache friendliness if it lives ahead of the cached portion. **Prefix cache architecture:** the H7 style overlay is per-user and therefore variable — it must be positioned *after* the stable cached prefix, not before it. The stable cacheable tier is: H1 Genesis State → fixed tool descriptions → fixed few-shot examples. The per-user variable tier is: H7 style overlay → H10 relational content → session input. Placing the style overlay before the stable tier invalidates the H1 prefix cache for every user, eliminating the session-cost reduction mechanism 5 provides. Providers that support prompt caching (mechanism 5) cache from the beginning of the prompt; any token that varies per user before the cache boundary forces a cache miss.
- A schema must be designed and maintained — adding a sixth field later is non-trivial across already-populated user models.

**Risks and failure modes**
- *Identity Drift (HA3)* — the defining failure: H7 writes seep into H1 fields (values, refusal, capability claims), and the agent gradually becomes whoever the user prefers. **Field-scope discipline + Boundary Guard mitigate.**
- *Single-interaction overfit* — one unusual exchange triggers a large adaptation. Mitigate by bounded step size and minimum interaction count before adapting.
- *Stale style* — user's preferences shifted (new context, new role); the model still applies the old style. Mitigate with periodic decay and a visible Reset path.
- *Over-confident depth inference* — agent infers "expert" from one piece of vocabulary, then pitches everything above the user's actual level. Cap depth at *demonstrated* expertise, not *inferred*; require multiple signals before increasing depth.
- *Cross-user leakage* — a per-user model accidentally consulted for the wrong user. Treat the User Style Model as PII; partition strictly by user ID.

## Implementation Notes

- **Bootstrap from S3 defaults.** A new user's User Style Model = deployment defaults (the S3 persona's implied style). H7 begins to vary only after the per-user signal budget threshold is reached.
- **Bound the step size.** Each update may move a numeric field by at most ±1 on a 1–5 scale, change at most one categorical field. Larger jumps require an *explicit* user correction.
- **Schema is fixed.** No free-form fields. If a sixth style field is genuinely needed, ship a schema migration, do not let the Style Inferrer invent one.
- **Field-scope allowlist.** The Boundary Guard's allowlist is the canonical artefact of the H1↔H7 partition. Review it whenever H1's invariant fields are amended; never amend it implicitly.
- **Distinguish style from content.** H7 affects *how* the agent communicates. *What* the agent communicates about a particular user — goals, projects, history — belongs in **H10 Relational Memory**. The boundary matters: leakage in either direction creates the wrong pattern under the wrong name.
- **Make the Reset visible.** "Reset style preferences" is a first-class user operation, surfaced in the UI or as a command.
- **Decay slowly.** Older signals matter less than recent; apply a gentle exponential decay (half-life ~30 days) rather than a hard cutoff.
- **Privacy.** Treat the User Style Model as personal data. Right-to-deletion, encryption at rest, audit-logged access — the same obligations H10 carries.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H7 sits at the *setup-composition* layer of every user-facing generation, *requiring* **H1** as the invariant substrate and *pairing with* **K10 Long-Term Memory** (semantic-variant store for per-user records) or **K12 Karpathy Memory** (if the style model coexists with curated user notes). It draws on **S3 Persona** as the bootstrap default, on **S6 Output Template** for the User Style Model schema, and on **R7 Reflexion** as one signal source (rewrites are reflective signals). For high-stakes contexts the Boundary Guard composes with **V5 Guardrail Layering**.

**The chain — read & apply (every session start / every turn):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| R1 | Read H1 invariant Identity Block at position 0 | `code` | H1 |
| R2 | Read User Style Model for this user | `code` | K10 (semantic-variant) |
| R3 | Compose generation setup: H1 invariant + H7 style overlay | `code` | S3, S6 |
| R4 | Generate the response | `LLM` | Generator session |

**The chain — infer & update (within session / at trigger):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| U1 | Watch for explicit corrections in user input | `code` | |
| U2 | Watch for implicit signals (rewrites, length match, register) | `code` (or small `LLM`) | Style Inferrer session |
| U3 | Propose a bounded delta to the User Style Model | `LLM` | Style Updater session |
| U4 | Boundary Guard checks no field touches H1 invariants | `code` | field-scope allowlist |
| U5 | Apply the permitted delta; write back to store | `code` | K10 (write) |
| U6 | *(on reset signal)* restore User Style Model to defaults | `code` | Reset Handler |

**Skeleton:**

```
load_session(user_id, store):
    h1_block   = h1_store.latest()                     # code — H1 invariant
    style      = h7_store.read(user_id)                # code — User Style Model
    setup      = compose(h1_block, style_overlay(style))   # code — read-only H1
    return setup

per_turn(setup, user_msg):
    return Generator(setup, user_msg)                  # LLM

end_session(events, user_id, h7_store):                # at trigger only
    signals  = StyleInferrer(events)                   # code or small LLM
    delta    = StyleUpdater(h7_store.read(user_id),    # LLM — propose delta
                            signals)
    safe     = BoundaryGuard(delta, h1_field_allowlist)  # code — drop H1 writes
    h7_store.write(user_id, apply_step(h7_store.read(user_id), safe))   # code

on_reset(user_id, h7_store):
    h7_store.write(user_id, defaults())                # code — Reset Handler
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generator** | the system's main generalist | the **H1 invariant Identity Block** (read-only) + the **H7 style overlay** (rendered from the User Style Model: *"use detail level {n}/5, technical depth {n}/5, prefer {format}, target {length}, register {tone}"*); plus task-specific role/constraints (S3/S5/S6 as the inner task needs) | the user query (and any retrieved context) |
| **Style Inferrer** *(optional)* | small fast generalist; deterministic rules cover the obvious cases (explicit instructions), the LLM handles the implicit ones | role: *"you extract communication-style signals from a user's recent messages and rewrites — never content preferences, never identity-relevant claims"*; output schema: the same fixed fields the User Style Model uses; explicit list of fields you must **not** touch (H1 invariants) | the recent session turns + any rewrites |
| **Style Updater** | capable generalist; updates are infrequent so quality > speed | role: *"you propose bounded updates to a user's communication-style model"*; the **field schema** (the five style fields, their ranges, the bounded step size); the **H1 field-scope allowlist** the Boundary Guard will enforce, named explicitly in the setup; rule that any proposed change to an H1 field invalidates the entire proposal | the current User Style Model + the inferred signals |

**Specialist-model note.** No fine-tune is required. The discipline choices that make H7 work are structural, not model-level: (1) the **User Style Model is a fixed schema**, not free-form — a sloppy schema is how style preferences silently grow into content preferences and identity claims; (2) the **Boundary Guard is code, not prompt** — a system-prompt request to "not touch identity fields" is a polite suggestion to the Updater, while a field-scope allowlist in code is a guarantee; (3) the **Style Applier reads H1 read-only** — H1's block is composed into the setup, never *edited* by the H7 layer. Skipping any of the three turns H7 into "a free-form persona that adapts," which is the failure mode under the misleading-success name.

## Open-Source Implementations

- **Letta** (formerly MemGPT) — [`github.com/letta-ai/letta`](https://github.com/letta-ai/letta) — the canonical implementation. The `human` core memory block is the User Style Model made concrete: a persistent, agent-editable block carrying user facts and preferences alongside Letta's `persona` block (which is H1). The block-level separation is exactly the H1↔H7 partition this pattern requires.
- **Mem0** — [`github.com/mem0ai/mem0`](https://github.com/mem0ai/mem0) — a universal memory layer for AI agents that stores user preferences, traits, and interaction patterns as a self-improving long-term memory layer. Per-user identifiers partition the model; "adaptive personalization with continuous improvement" is the pattern's value proposition stated in product terms.
- **LangMem** — [`github.com/langchain-ai/langmem`](https://github.com/langchain-ai/langmem) — LangChain's user-memory primitives for LangGraph agents; explicit *Memory Manager* and *Prompt Optimizer* abstractions for extracting style signals and updating prompts over time.
- **LaMP Benchmark** — [`github.com/LaMP-Benchmark/LaMP`](https://github.com/LaMP-Benchmark/LaMP) — research codebase for the LaMP paper; not a deployable user-style runtime, but the canonical evaluation harness for personalised-LLM outputs and the cleanest reference for what "style fit" measures.

## Known Uses

- **Letta-built personal assistants** — `human` core-memory blocks accumulating user preferences across sessions, paired with `persona` blocks for the agent's invariant identity; the H1↔H7 partition realised at the data-model level.
- **Coding assistants with rules files** (Cursor, Claude Code) — user- or project-level rules files capturing verbosity, formatting, and tone preferences that the agent honours across sessions; H7 in a coding-assistant register.
- **Customer-service agents with user-tier routing** — adapt formality and detail level to the user's interaction history and self-reported expertise, while holding brand voice (H1) constant.
- **Educational and tutoring agents** — calibrate explanation depth to the learner's demonstrated level (not assumed level), pulling from recent exercise performance and explicit user feedback.

## Related Patterns

- **Requires** H1 Identity Persistence — H7 is the variable surface above H1's invariant core. Without H1, H7 collapses into the anti-pattern **HA3 Identity Drift**. The partition between the two is the pattern's defining structural choice.
- **Pairs with** K10 Long-Term Memory (semantic variant) — the User Style Model is naturally stored as a small per-user semantic record; K10's similarity store handles it cleanly when user count is large.
- **Pairs with** K12 Karpathy Memory — when the system also maintains curated *content* notes about the user, K12 holds them; H7 holds only the *style*.
- **Pairs with** H10 Relational Memory — H10 holds the *content* of the relationship (goals, history, project context); H7 holds the *expression style*. They share the per-user partitioning discipline; do not let one absorb the other.
- **Pairs with** H2 Episodic Self-Improvement — explicit style corrections can also be written as cross-session lessons ("user X dislikes nested bullets"), feeding H2's library; do not double-store.
- **Pairs with** V5 Guardrail Layering — for high-stakes deployments, the Boundary Guard's field-scope rejection composes with V5 to surface and audit attempted H1-field writes.
- **Distinct from** S3 Persona — S3 is one persona for the whole deployment; H7 is one persona *per user*, varied from a static base. H7 generalises S3 in the per-user direction; H1 generalises S3 in the cross-session direction.
- **Distinct from** H9 Observational Identity — H9 is the agent's evolving model of *itself* (what it has done, what it can do); H7 is the agent's model of *how to address this user*. Same shape (an evolving model), opposite subject.
- **Cognitive grounding** — Premack & Woodruff (1978) Theory of Mind: an agent acts effectively by imputing mental states (knowledge, register, preference) to its interlocutor. H7 is Theory of Mind realised as a structured per-user style parameter.
- **Anti-pattern** HA3 Identity Drift — H7 without H1, or H7 without a Boundary Guard, *is* HA3. The pattern's discipline exists to prevent this collapse.

## Sources

- Salemi, A., Mysore, S., Bendersky, M., Zamani, H. (2023) — "LaMP: When Large Language Models Meet Personalization." arXiv 2304.11406. The benchmark establishing per-user output fit as a measurable axis distinct from correctness.
- Premack, D., & Woodruff, G. (1978) — "Does the chimpanzee have a theory of mind?" *Behavioral and Brain Sciences* 1(4):515–526. The cognitive grounding for imputing mental states to an interlocutor.
- Shang, W. (2026) — "Theater of Mind: A Global Workspace Framework for LLM Agent Architecture." arXiv 2604.08206. User model as one axis of the Global Workspace state.
- White et al. (2023) — "A Prompt Pattern Catalog…" The Persona Pattern (S3); H7's static precursor.
- Packer et al. (2023) — "MemGPT: Towards LLMs as Operating Systems." arXiv 2310.08560. Letta's predecessor; core-memory `human` block is H7 made concrete.
- Skjuve et al. (2021) — "My Chatbot Companion" (HCI). User-modelling and personalisation effects on long-term engagement.
