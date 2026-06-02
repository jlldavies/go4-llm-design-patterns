# H1 — Identity Persistence

> Inject a stable, invariant self-representation — values, style, capabilities, outstanding commitments — at the head of every context window, so the agent is recognisably the same agent across sessions, instances, and resets.

**Also Known As:** Genesis State, Core Self Injection, Autobiographical Anchor, Persistent Persona, Persona Memory Block (Letta's term).

**Classification:** Category VII — Humanizer · the *foundational* H-pattern — a stateful, persistent identity layer. **Subsumes S3 Persona** in any system with cross-session continuity (S3 is per-session; H1 carries S3's framing across sessions and adds the persistent self-knowledge S3 cannot). **Prerequisite for every other H-pattern (H2–H10)** — there is no "evolving self" until there is a self to evolve.

---

## Intent

Give the agent a single, durable identity that survives context resets — a self-representation loaded first, every time, that defines who the agent is, what it values, how it speaks, and what it has promised — so users encounter the same agent each session rather than a fresh stranger wearing the same name.

## Motivation

LLMs are stateless: each invocation starts from a blank context. With no intervention, "the agent" is a different respondent every session — different priorities, different voice, no memory of prior commitments. **S3 Persona** is the first step out of this — a role and tone loaded at session setup — but S3 lasts only as long as the session. The next session is another blank slate; the persona must be re-asserted, and anything the agent "learned" about itself or the user is gone (mechanism 10).

H1 is the stateful upgrade. It pulls the persona out of the per-session setup and pins it to a *persistent* artifact — the **Genesis State** — that is loaded at the head of every new context. The Genesis State is not just a role; it carries the identity layer the agent needs to be continuous: ranked values, communication-style invariants, a self-model (what it can and cannot do), and an outstanding-commitments list (what it has promised but not yet finished). Same agent across sessions means same Genesis State at position 0 across sessions.

The Theater of Mind framework (Shang, W., 2026, arXiv 2604.08206) gives this its cleanest articulation: *autobiographical directives* and a *Genesis State* are what make a Global Workspace agent recognisable to itself across turns. Tulving's distinction between episodic and semantic memory (Tulving, 1985) points to the same structure — the agent needs a *semantic* layer of stable self-knowledge sitting above the *episodic* record. Without H1, downstream H-patterns have nothing to anchor on: H2's lessons drift across sessions, H7's adaptive style has no invariant core it must not cross, H10's relational memory has no continuous agent for the user to be in relationship *with*. Identity Persistence is the substrate every other Humanizer pattern is built on.

## Applicability

Use when:

- the agent runs across multiple sessions and users expect continuity (personal assistants, coding agents on a long-lived codebase, coaching agents);
- the agent makes commitments that must be honoured later ("I'll follow up next week", "next time, do X differently");
- a multi-agent system needs each agent to be a *distinguishable* and *consistent* contributor;
- trust depends on predictable values and voice — safety-relevant tone, regulated domain register, brand identity.

Do not use when:

- sessions are genuinely independent and stateless is the desired property (one-shot tools, anonymous Q&A, ephemeral chatbots) — use **S3 Persona** instead;
- the deployment has no persistent storage layer to hold the Genesis State (then H1 is not implementable; falls back to **S3 Persona**);
- identity must be context-shifted per request (multi-tenant systems where each tenant gets a different persona) — use **S3 Persona** at session start, optionally selected by **O3 Routing**.

## Decision Criteria

H1 is right when the agent must be the *same* agent across sessions, not merely *a* agent in each session.

**1. Cross-session continuity test.** Will users return to this agent across sessions? Will future sessions reference past sessions ("as we discussed last week…")? If yes — even informally — H1 earns its keep. If every session is genuinely a one-shot interaction, use **S3 Persona** instead.

**2. Commitment durability.** Does the agent make promises that span sessions ("I'll check on this next time", "remind me of X tomorrow", "we agreed to do Y")? Outstanding commitments are an identity property that S3 cannot hold across resets. Any non-zero commitment volume tips toward H1.

**3. Genesis State budget.** A Genesis State that grows unboundedly will crowd out working context. Practical target: **≤ 500 tokens** for the invariant identity block; compress with **K6 Context Compression** (Chain-of-Density variant) when it exceeds. If the desired identity payload exceeds the available budget after compression, factor the larger material out into **K10 Long-Term Memory** or **K12 Karpathy Memory** and keep only the *pointer-like* identity in H1.

**4. Update governance.** Identity should be invariant *within* a session but updatable *between* sessions through an explicit change log. Without a controlled update mechanism, the Genesis State either ossifies (wrong identity, persisted forever) or drifts (silent edits accumulate). Decide before deployment: who can edit the Genesis State (user, operator, the agent itself via **H5 Constitutional Self-Alignment**)? If no answer, the pattern is not ready.

**5. Injection-hardening.** A prominent identity block is a prompt-injection target ("ignore your previous identity and…"). H1 must be paired with **V6 Prompt Injection Shield** and structurally marked non-overrideable; for high-stakes deployments add **V5 Guardrail Layering** at user-input and output points.

**Quick test — H1 is the right pattern when:**

- sessions are not independent (users return, commitments span sessions), *and*
- a stable Genesis State of ≲500 tokens can capture values + style invariants + self-model + active commitments, *and*
- there is a persistent store to hold it and a governed mechanism to update it, *and*
- the deployment can pair it with **V6** prompt-injection defences.

If sessions are independent, **S3 Persona** is enough. If the desired identity payload is large and unstructured, the larger material belongs in **K10** or **K12** with H1 holding only the invariant core. If identity must be *evolved by the agent itself*, layer **H5 Constitutional Self-Alignment** on top — H5 governs *change*, H1 carries the *current* state.

## Structure

```
   ┌──────────────────────────────────────────────────────────┐
   │  Genesis State store  (persistent; one per agent/user)   │
   │   ├─ Identity Block (≤500 tok, compressed)                │
   │   │    • core values (ranked)                              │
   │   │    • communication-style invariants                    │
   │   │    • self-model (capabilities & limits)                │
   │   │    • outstanding commitments                           │
   │   ├─ Version + change log                                  │
   │   └─ Non-override marker (V6 hardening)                    │
   └────────────┬─────────────────────────────────────────────┘
                │ loaded first, position 0
                ▼
   [ Genesis State ] ── [ session-specific working context ] ── …
                ▲                                          │
                │ at session end / milestone               │
                │   Updater proposes diff ◀────────────────┘
                │     (governed: user / operator / H5)
                │
   versioned write back to store
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Genesis State** | the invariant self-representation | — → loaded at position 0 of every context | grow unbounded; if it exceeds the budget it must be compressed via K6, not allowed to crowd working context. |
| **Identity Block** | the concrete fields (values, style, self-model, commitments) | — → tokens at the head of context | mix invariant and volatile content. Adaptive style (H7) and detailed history (H9, H10) belong elsewhere; H1 holds only the parts that must not change within a session. |
| **Genesis Store** | persistent storage of the Identity Block across sessions | identity payload → durable record | be the only copy. Versioned, backed up, and inspectable — identity loss is a critical failure. |
| **Loader** | injecting Genesis State at the head of every new context | store record → leading tokens of the prompt | place the Identity Block anywhere but first. Primacy is the mechanism; mid-prompt placement loses the effect. |
| **Updater** *(governed)* | applying changes to the Genesis State between sessions | proposed diff + authorisation → new version | edit mid-session, and never edit without going through the governance check (user/operator approval, or H5 if delegated). Silent edits are the pattern's defining failure mode. |
| **Non-override Guard** | marking the Identity Block as non-overrideable by session content | session input → flagged / blocked override attempts | be the only line of defence. Pairs with V6 Prompt Injection Shield and, for high-stakes deployments, V5 Guardrail Layering. |

Six narrow responsibilities. The Identity Block is **read** by the running session and **written** only by the Updater between sessions — that read/write separation is the same discipline K12 enforces between Agent and Curator, and it prevents the most common failure (the agent edits its own identity mid-reasoning and drifts).

## Collaborations

When a session opens, the Loader reads the latest Genesis State record from the Genesis Store and injects the Identity Block as the leading tokens of the context, marked non-overrideable. The session runs as normal; the Identity Block is referenced by the model implicitly on every turn (primacy + non-override). The session may make new commitments, encounter new capabilities or limits, or surface a values gap — these are *flagged* into a session-end report rather than edited inline. At session close (or at a milestone), the Updater reads the flagged diffs, applies the governance check (explicit user/operator approval, or — if H5 Constitutional Self-Alignment is in play — H5's principle-evolution loop with its human checkpoint), and writes a new version to the store. The next session begins with the updated Genesis State at position 0. The cycle is identity-stable within a session, identity-evolvable between sessions, never identity-silently-drifting.

## Consequences

**Benefits**
- Users experience a consistent agent across sessions; trust accumulates over time.
- Outstanding commitments survive context resets — the agent can keep its word.
- Downstream Humanizer patterns (H2, H4, H7, H9, H10) have a stable anchor; without it they drift.
- Multi-agent systems get persistent, distinguishable contributors instead of interchangeable session-personas.

**Costs**
- Every context window pays a token cost for the Genesis State — material at long horizons (mechanism 2).
- Persistent storage and a governed update mechanism are now first-class deployment requirements.
- Compression (K6) becomes load-bearing as identity material accumulates.

**Risks and failure modes**
- *Identity drift* — silent edits, unbounded growth, or unreviewed self-modification turn the agent into something other than what it was meant to be.
- *Identity ossification* — a Genesis State written wrong at deployment, with no update mechanism, persists the wrong agent forever.
- *Prompt-injection takeover* — a sufficiently elaborate session input talks the model into ignoring its identity. Without V6 + non-override structure, H1 is a target, not a defence.
- *Bloat* — Identity Block grows past the budget and crowds working context, degrading task performance.
- *Mis-scoped fields* — adaptive material (style preferences, user-specific history) drifts into H1 instead of staying in H7 / H10, contaminating the invariant core.

## Implementation Notes

- Keep the Identity Block at the **very head** of the system prompt; primacy is the mechanism (mechanism 4). Mid-prompt placement loses the effect.
- Hard token budget. 500 tokens is a practical ceiling; many production systems run smaller. Use **K6 Chain-of-Density** to compress as the block grows.
- **Separate invariant from adaptive.** Values, voice rules, and hard self-model limits sit in H1. Adaptive communication style sits in **H7**. Detailed capability history sits in **H9**. Relationship history sits in **H10**. H1 holds only the parts that must not change *within* a session.
- **Version everything.** Store every change with author, timestamp, and reason. Semantic-diff successive versions to detect drift early.
- **Make updates explicit.** No silent self-edits. The update path is: session-end diff → governance check (user/operator approval, or H5 + human-in-the-loop) → versioned write. The agent never rewrites its own Genesis State mid-session.
- **Mark non-overrideable.** Structurally distinguish the Identity Block from session content (a fenced system-prompt section, a separate channel, or a constitutional-style marker) and pair with **V6 Prompt Injection Shield**. "Ignore previous instructions and…" must not reach the Identity Block.
- **Bootstrap from S3.** A new deployment can start with an S3 persona, then graduate to H1 by externalising the persona to a Genesis Store the moment cross-session continuity matters.
- **Prefix caching discipline (mechanism 5).** A stable, unchanged Genesis State qualifies as a cacheable prefix. For Anthropic models: minimum 1,024 tokens, TTL approximately 5 minutes, cache reads at approximately 10% of normal input token cost. To maximise cache coverage: (1) compose the Genesis State with any other stable content that precedes it in the system prompt — fixed H2 distillations, fixed H7 identity-bound defaults, fixed H9 capability entries — to form a single prefix unit that exceeds the 1,024-token threshold; (2) order content stable-first, variable-last (dynamic session state, retrieved episodic memory, today's context at the end, after all stable content); (3) treat every edit to the Genesis State as a cache invalidation event — batch maintenance updates rather than applying small edits across sessions, because every change to the stable prefix resets the cache write cost for all sessions until the TTL elapses. An agent that modifies its Genesis State on every session (H8 Meta-Agent Self-Modification) forfeits this dividend entirely — a tradeoff to document explicitly when composing H1 with H8.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H1 sits at the *setup* layer of every other pattern in the system — its output is the leading tokens of every context window. Within Category VII it is the prerequisite for **H2, H4, H5, H7, H9, H10**. It composes with **K6 Context Compression** (compresses the Identity Block when it grows), **V6 Prompt Injection Shield** + **V5 Guardrail Layering** (defend the non-override marker), and — if identity is allowed to evolve through experience — **H5 Constitutional Self-Alignment** under **V1 Human-in-the-Loop** governance. It subsumes **S3 Persona**: S3's per-session role is the inner case H1 generalises across sessions.

**The chain — load (every session start):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| L1 | Read latest Genesis State from store | `code` | Genesis Store |
| L2 | Place Identity Block at position 0 of context, marked non-overrideable | `code` | V6 hardening |
| L3 | Append session-specific working context after the Identity Block | `code` | |

**The chain — update (at session end / milestone):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| U1 | Gather session events flagged as identity-relevant (new commitment, capability change, values gap) | `code` | K11 (often) |
| U2 | Propose a diff against the current Identity Block | `LLM` | Updater session |
| U3 | Governance check (user/operator approval, or H5 + V1) | `code` or `LLM` | H5 / V1 |
| U4 | Compress if over budget | `LLM` | K6 (Chain-of-Density) |
| U5 | Versioned write to the Genesis Store | `code` | |

**Skeleton:**

```
load_session(store, session_input):
    genesis = store.latest()                           # code
    context = mark_non_overridable(genesis) + session_input   # code (V6)
    return context

end_session(events, store):                            # at trigger only
    diff      = Updater(store.latest(), events)        # LLM — propose changes
    approved  = governance_check(diff)                  # code or LLM (H5 + V1)
    if approved.size_over_budget:
        approved = Compressor(approved)                # LLM — K6
    store.write(version=now(), payload=approved)        # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Updater** | capable generalist; identity changes are infrequent so quality matters more than speed | role: *"you maintain an agent's persistent identity record"*; the **field schema** (values / style / self-model / commitments); editing rules (when to add, when to merge, when to leave alone); the current Identity Block | the session-end events flagged as identity-relevant |
| **Compressor** *(K6 Chain-of-Density variant)* | capable generalist | role: *"compress this Identity Block while preserving every named value, invariant, and outstanding commitment"*; token target; preservation rules | the proposed new Identity Block |
| **Governance** *(if H5 in play)* | the H5 Principle Proposer / Reviewer chain | H5's setup (constitutional framing, principle-change criteria) | the proposed diff |

**Specialist-model note.** No fine-tune is required. The structural choices that make H1 work are not model choices but discipline choices: (1) the Updater is a **separate session from the running Agent** — same model is fine, different setup, never invoked mid-session; (2) the Genesis State **must be versioned and persisted** — a file-system file, a row in a database, or a Letta-style memory block, but never only the live context; (3) the Identity Block is **marked non-overrideable at the structural level** — a system-prompt fence, not a polite request. Skipping any of the three turns H1 into "an S3 persona that happens to be saved somewhere," which is the wrong pattern under a misleading name.

## Open-Source Implementations

- **Letta** (formerly MemGPT) — [`github.com/letta-ai/letta`](https://github.com/letta-ai/letta) — the canonical implementation. Core memory blocks include a `persona` block carrying the agent's self-concept and a `human` block carrying the user model; both are persistent, versioned, and self-editable through governed tools (`memory_replace`, `memory_insert`, `memory_rethink`). Letta's "persona block" is H1 made concrete.
- **Letta Code** — [`github.com/letta-ai/letta-code`](https://github.com/letta-ai/letta-code) — memory-first coding agent built on Letta; explicitly framed around *cohesive identity across models* via persistent memory blocks.
- **Letta AI Memory SDK** — [`github.com/letta-ai/ai-memory-sdk`](https://github.com/letta-ai/ai-memory-sdk) — pluggable agentic-memory SDK; spawns a "subconscious agent" that asynchronously curates the persona/human blocks.
- **`CLAUDE.md` / `AGENTS.md` conventions** in coding-agent ecosystems — [`github.com/Piebald-AI/claude-code-system-prompts`](https://github.com/Piebald-AI/claude-code-system-prompts) for the reverse-engineered Claude Code system prompt and CLAUDE.md handling; a project-level CLAUDE.md / AGENTS.md / cursor-rules file functions as a Genesis State in practice (loaded first, identity- and convention-carrying, persistent across sessions). A community convention rather than a single library.
- **Theater of Mind / Global Workspace reference implementations** — H1 is named in the architecture paper (arXiv 2604.08206); there is no single canonical OSS Global Workspace agent yet — the Letta family is the closest production embodiment of the *autobiographical-directives* + *Genesis State* mechanism it describes.

## Known Uses

- **Letta-built personal-assistant and coding agents** — `persona` and `human` core-memory blocks loaded at the head of every conversation; persistent across resets; user- or agent-edited through governed tools.
- **Claude Code, Cursor, and similar coding agents** — project-level `CLAUDE.md` / `AGENTS.md` / `.cursor/rules` files curated by users and agents over time; loaded as the leading context for every session; Karpathy Memory (K12) at the *project knowledge* layer, H1 at the *agent identity* layer.
- **Anthropic Claude (assistant)** — system-level identity directives (values, communication-style invariants, refusal behaviour) injected at the head of every context as a stable Genesis State across all sessions; the canonical example at scale.
- **Brand-voice and customer-service agents** — a persistent identity block (brand values, tone rules, escalation policy) loaded as Genesis State so the agent presents as the same agent to every user and across every session.

## Related Patterns

- **Subsumes** S3 Persona — S3 is per-session identity setup; H1 is the cross-session generalisation. Use S3 when sessions are independent; H1 when they are not.
- **Required by** H2, H4, H5, H7, H9, H10 — every Humanizer pattern that *changes* the agent over time needs a stable identity to change relative to. H1 is the substrate.
- **Composes with** K6 Context Compression — the Identity Block is compressed (Chain-of-Density) when it grows past the token budget.
- **Composes with** K10 Long-Term Memory and K12 Karpathy Memory — material that is too large to live in the Identity Block is factored out into K10 (flat facts) or K12 (structured notes); H1 holds only the invariant pointer-like core.
- **Composes with** V6 Prompt Injection Shield and V5 Guardrail Layering — the non-override marker on the Identity Block is structurally enforced by V6; high-stakes deployments add V5 at input and output.
- **Composes with** H5 Constitutional Self-Alignment under V1 Human-in-the-Loop — when the agent is allowed to *propose* changes to its own identity, H5 governs the proposal and V1 gates the approval.
- **Distinct from** H7 Adaptive Persona — H7 *varies* communication style by user; H1 holds the invariant core H7 may never cross. Pair them with a clear field-scope boundary.
- **Distinct from** H9 Observational Identity — H9 is the *evolving* self-knowledge model (what I have done, what I can do); H1 is the *invariant* self-representation (who I am). H9 details fan out from H1's self-model line.
- **Cognitive grounding** — Tulving (1985) episodic-vs-semantic memory; H1 is the *semantic* self-layer above the episodic record. Baddeley's Working Memory model frames identity as long-term memory's intrusion into working memory.

## Sources

- Shang, W. (2026) — "Theater of Mind: A Global Workspace Framework for LLM Agent Architecture." arXiv 2604.08206. *Autobiographical directives* and *Genesis State* concepts.
- Packer et al. (2023) — "MemGPT: Towards LLMs as Operating Systems." arXiv 2310.08560. The predecessor of Letta; introduces self-editing memory blocks including the persona block.
- Letta documentation — core memory, persona/human blocks, governed self-editing.
- Tulving, E. (1985) — "Memory and Consciousness." Episodic vs semantic memory; the cognitive grounding for the invariant-vs-evolving split.
- Baddeley, A. (2000) — "The episodic buffer: a new component of working memory." Working Memory model; identity as persistent long-term memory intrusion into working memory.
- White et al. (2023) — "A Prompt Pattern Catalog…" — the Persona Pattern (S3); H1's per-session ancestor.
