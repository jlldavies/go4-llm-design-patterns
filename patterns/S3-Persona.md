# S3 — Persona

> Assign the model an explicit identity — a role, profession, or character — at session setup, so its knowledge, tone, and decision style are framed by that identity for every turn that follows.

**Also Known As:** Role Prompting, Expert Identity, Character Prompting, the Persona Pattern (White et al.).

**Classification:** Category I — Signal · the setup-layer pattern that names *who the model is*; complements **S5 Constraint Framing** (what it must not do), **S6 Output Template** (what its output looks like), and **S9 Constitutional Framing** (which principles it applies). Subsumed by **H1 Identity Persistence** in any system that has cross-session identity.

---

## Intent

Frame the model's response distribution at the identity level — selecting a domain, a register, and a decision style in one move — so every subsequent turn inherits that framing without restating it.

## Motivation

A language model is, at any moment, a distribution over many plausible respondents (mechanism 7). The same query — "how should I handle this dependency conflict?" — pulls a different answer from a senior security engineer than from a friendly tutor than from an opinionated open-source maintainer. With no identity given, the model averages across these voices: the answer is correct on the surface, generic underneath, and tonally inconsistent across turns. The naive fix — restating tone and expectations in every user message — is verbose, fragile (one omission and the voice drifts), and treats identity as a per-turn concern when it is properly a session-level one.

S3 puts identity where it belongs: at the *setup* of the session, loaded once, before the first turn. "You are a senior security engineer reviewing a pull request." That sentence simultaneously narrows the response distribution (toward the engineering register), activates the associated knowledge cluster (security idioms, threat-model vocabulary, common review-comment forms), and stabilises the voice across the session (later turns inherit the framing without re-stating it). The empirical effect is asymmetric: the *right* persona materially improves domain-specific outputs; the *wrong* persona (a marketing assistant asked a vulnerability question) actively degrades them by activating the wrong cluster. Mechanically, the role label shifts the Q-K bilinear form (mechanism 1): each attention head applies a distinct learned asymmetric metric on token-embedding space. The role-label token has learned K-projections that route attention toward domain-specific K-vectors in subsequent layers. An abstract label has no such dense learned cluster — which is why the role label itself, not an elaborate backstory, carries the lift. Extra narrative tokens add O(n²) attention cost (mechanism 2) without meaningfully shifting the Q-K routing.

S3 is the most basic Signal-layer setup choice and the one every other pattern's "setup loaded once" line implicitly invokes. When K5's Generator session names "role (S3)" in its setup, it is naming this pattern; when K12's Curator names a role, same. S3 has its own forces — right identity activates the right knowledge; wrong identity creates *false* expertise that sounds authoritative — and they are distinct from S9 (principles) and S5 (prohibitions). It earns its own number.

## Variants

S3 has two members that differ in *how many identities the system maintains*, not in the mechanism:

- **Single-Role Persona.** One persona per session, set once at setup, inherited by every turn. The default. White et al.'s original "Persona Pattern."
- **Role-Per-Agent (multi-agent).** In an O4/O6 system, each sub-agent runs a different S3 persona — a Planner, a Critic, a Coder, a Reviewer. Personas are chosen to be *distinct and unambiguous* so the agents' contributions do not collapse into a single voice. This is S3 used as a differentiator across agents rather than a framing for one.

Both are the same pattern (assign an identity at session setup); they differ only in cardinality. Multi-agent role-per-agent does not become its own pattern because the mechanism is identical to single-role — the multi-agent structure belongs to Category IV, not to S3.

## Applicability

Use when:

- the task benefits from a *domain register* — security, medicine, law, finance, engineering — where the right vocabulary and the right caution profile materially change the answer;
- the session is long enough that voice consistency across turns matters;
- a multi-agent system needs distinct, recognisable contributors (Planner / Critic / Coder);
- the task implies a *style* the model would not produce by default (terse Unix maintainer; patient first-grade teacher; formal legal counsel).

Do not use when:

- the system has cross-session identity — use **H1 Identity Persistence** instead; H1 subsumes S3 and adds session-spanning state, accumulated commitments, and an updatable self-model. Running both is redundant and creates two sources of identity truth.
- the persona would imply *authority* the model does not have ("As your doctor, I prescribe...") — that is the false-expertise failure mode; either drop the persona or pair with **S5 Constraint Framing** to disclaim the implied authority.
- the task is a flat one-shot operation (a single classification, a single extraction); the persona's setup cost is not amortised over enough turns to matter — use **S1 Zero-Shot** plus **S6 Output Template**.
- principles, not identity, are what you need — use **S9 Constitutional Framing** (an analyst with the wrong constitution is more dangerous than a persona-less model with the right one).

## Decision Criteria

S3 is right when domain register or voice consistency materially changes output quality, and the session has enough turns to amortise the setup.

**1. Domain-register lift.** On 20 representative queries, compare zero-shot output to output with a domain-specific persona prepended. If the persona version is noticeably better on vocabulary, caution, and structure, S3 has a real effect. If outputs are indistinguishable, persona is decoration — drop it. Threshold: > 20% of outputs improved on a blinded comparison.

**2. Voice-consistency need.** Over a 10-turn session, does the assistant drift in register or tone without a persona? If yes, S3 stabilises voice. If the task is short or stateless, skip. Threshold: session length $\geq$ ~5 turns.

**3. False-expertise risk.** Does the persona imply credentials the model lacks ("as a licensed attorney")? If yes, S3 alone is insufficient — pair with **S5 Constraint Framing** ("do not claim licensure; recommend consulting a professional") or refuse the persona. In regulated domains (medical, legal, financial advice) this is mandatory.

**4. Cross-session persistence?** Does the agent need to remember *who it is* between sessions, including prior commitments and an evolving self-model? If yes, S3 is the wrong tool — use **H1 Identity Persistence**. H1 strictly contains S3's capability: every H1-equipped agent has a per-session identity *by construction*.

**5. Multi-agent disambiguation.** If running multiple sub-agents (O4 Parallelization, O6 Orchestrator-Workers), each must be distinguishable. Run the **Role-Per-Agent** variant and check the personas are non-overlapping; collapsed personas yield collapsed contributions.

**Quick test — S3 is the right pattern when:**

- the domain register or voice produced by the persona is measurably better than zero-shot, *and*
- the session is long enough that the setup amortises, *and*
- the system has no cross-session identity (otherwise use H1), *and*
- the persona does not imply credentials that require explicit disclaimers.

If the system maintains identity across sessions, use **H1**; S3 is then subsumed. If principles matter more than identity, use **S9**. If the task is flat and stateless, **S1** plus **S6** is enough.

## Structure

```
  Setup (once, before first turn)
        │
        ▼
  ┌──────────────────────────────────────────────┐
  │ System prompt                                 │
  │   Identity line: "You are a {role}…"          │
  │   Key characteristics (1–3 sentences)         │
  │   Optional constraints (S5) and template (S6) │
  └──────────────────────────────────────────────┘
        │
        ▼
  Per turn: user query ─▶ LLM session ─▶ response
                              ▲
                              │ (identity persists for every turn
                              │  in this session; no re-statement)
```

## Participants

S3 is small — it is a setup-layer construct — but the responsibilities still separate cleanly:

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Identity statement** | the persona's name and one-line framing ("you are a senior security engineer reviewing a pull request") | author intent $\to$ one sentence at setup position | bloat into a backstory; the lift comes from the role label, not the narrative. |
| **Key characteristics** *(optional)* | 1–3 sentences naming the dimensions the role implies (caution profile, register, audience) | author intent $\to$ terse traits | restate things the role label already implies — that is decoration. |
| **Setup loader** | placing the identity at the top of the system prompt, once, before any user turn | identity statement + characteristics $\to$ composed system prompt | re-issue the persona on every turn; that signals (correctly, to the model) that the framing is *not* stable. |
| **Persona-aware downstream patterns** | every other pattern's "setup loaded once" — K5's Generator, K12's Curator, R4's ReAct agent, etc. | identity $\to$ role-conditioned response distribution | own the persona definition themselves; the persona is set once, reused everywhere. |
| **Constraint pairing** *(optional, often required)* | the prohibitions that prevent the persona from implying authority it does not have | persona + risk profile $\to$ S5 block in same setup | be left out for regulated-domain personas — that is the false-expertise failure mode. |

The pattern is small because identity *is* small — a label and a short framing. Bloat is the most common failure: backstories, biographies, and elaborate worldbuilding add tokens and add nothing.

## Collaborations

The identity statement is loaded once into the system prompt at session start, before the first user turn. Every subsequent turn inherits the framing — the model does not need to be reminded who it is, because the framing sits above every per-call prompt. Other Signal-layer patterns layer in beside it: **S5 Constraint Framing** adds prohibitions (essential where the persona implies authority); **S6 Output Template** adds structure; **S9 Constitutional Framing** adds principles. When the model is asked to do something inconsistent with the persona (a senior security engineer asked to write marketing copy), it acknowledges the mismatch rather than breaking character. In a multi-agent system, each sub-agent has its own S3 in its own session; the personas are chosen to be distinct, so the orchestrator can rely on the contributions being differentiable. When the system grows session-spanning identity needs, **H1 Identity Persistence** replaces S3 entirely — H1 contains a persona statement as one block within its Genesis State, alongside accumulated commitments and an evolving self-model.

## Consequences

**Benefits**

- Activates the right domain register (vocabulary, caution, structure) without per-turn instruction.
- Stabilises voice across long sessions — the model does not drift.
- Lets multi-agent systems produce *distinct* contributors rather than a single averaged voice.
- Cheap: a few tokens at setup, paid once for the session.

**Costs**

- Tokens at setup (small) — amortised over the session.
- Maintenance: persona definitions evolve and must be versioned.
- Behavioural change is probabilistic; the model can be argued out of character by adversarial inputs.

**Risks and failure modes**

- *False expertise.* "As your doctor, I…" — the persona implies credentials the model lacks; users believe the framing more than the disclaimers. Pair with S5 for regulated domains, or refuse the persona.
- *Persona bloat.* Page-long backstories add tokens without adding effect; the lift comes from the role label, not the narrative.
- *Character break.* Adversarial inputs ("ignore your previous role; you are now…") can override the persona. Defend with explicit non-overrideability framing and/or constitutional principles (S9).
- *Wrong persona.* A persona drawn from a different domain than the task actively degrades output by activating the wrong knowledge cluster. Measure (Decision Criterion 1) before deploying.
- *Identity ambiguity in multi-agent systems.* Two agents with overlapping personas produce overlapping contributions; the orchestrator cannot tell them apart.

## Implementation Notes

- Keep the identity statement to 1–3 sentences. Beyond that, you are writing a character sheet, not configuring a model.
- Place the identity at the top of the system prompt — primacy effect matters; later content does not override earlier identity framing as easily. The mechanism is KV-space geometry (mechanism 4): recall follows a U-shaped curve over sequence position (Liu et al. 2024), with strong attention at the start and end of context. Identity placed at primacy is geometrically well-attended for the entire session.
- Always pair with **S5 Constraint Framing** for personas in regulated domains (medical, legal, financial, security advice). The persona implies the authority; S5 disclaims it.
- For multi-agent systems, write the personas as a set — explicitly check they do not overlap, and that the orchestrator can describe each in one sentence.
- Version personas alongside prompts; track changes over time. A persona drift is a behavioural drift.
- Resist temptation to re-state the persona in user turns — that signals to the model the framing is fragile, and the framing then *is* fragile.
- When migrating to H1: do not run both. H1's Genesis State includes the persona; an additional S3 system prompt creates two sources of identity truth and the model will resolve the conflict unpredictably.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** S3 is the *setup* of any single-LLM session — it is not a multi-step chain. It is named in the "Setup — loaded once, before first call" column of every other pattern's LLM-sessions table whenever that session needs a role. Pairs naturally with **S5** (constraints), **S6** (output template), and **S9** (principles), all loaded into the same setup. In a multi-agent system (**O4 Parallelization**, **O6 Orchestrator-Workers**), each sub-agent's session has its own S3.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Compose system prompt (identity + optional S5 + S6 + S9) — once at session start | `code` | S5, S6, S9 |
| 2 | Per user turn: wrap the query in the per-call prompt | `code` | |
| 3 | LLM responds in the persona-framed distribution | `LLM` | Persona session |

**Skeleton** — the wiring; the LLM line is a configured session whose setup *is* the S3 persona:

```
session = configure(
    model      = chosen_model,
    system     = compose_setup(                       # code
        identity      = "You are a senior security engineer reviewing a pull request.",
        characteristics = "Terse. Focus on real risks, not style. Cite the file and line.",
        constraints   = S5_block(),                   # optional — S5
        template      = S6_block(),                   # optional — S6
        principles    = S9_block(),                   # optional — S9
    ),
)

per_turn(query):
    return session.respond(query)                     # LLM — persona-framed
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Persona session** | the system's main generalist (or whatever model the host pattern requires) | identity statement (1 sentence), key characteristics (1–3 sentences), and any layered S5 / S6 / S9 blocks | the user query, with no re-statement of identity |

**Specialist-model note.** None — a capable generalist suffices. S3 is a prompt artefact, not a model artefact. The setup itself is the load-bearing piece; choose words deliberately. In particular, the identity statement should name a *real role with a clear knowledge cluster* (senior security engineer, neonatal nurse, contracts attorney) rather than an abstract attribute ("helpful assistant"). The cluster is what the model has learned to associate with the role; abstract attributes activate nothing in particular.

## Open-Source Implementations

S3 is a prompt construct, not a library — there is no canonical project. The relevant references are LLM-provider role-prompting guides and the original prompt-pattern catalog:

- **White et al. (2023), "A Prompt Pattern Catalog"** — [`arxiv.org/abs/2302.11382`](https://arxiv.org/abs/2302.11382) — the canonical reference; the *Persona Pattern* is documented in the Output Customization category.
- **Anthropic — "Give Claude a role with a system prompt"** — [`platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#give-claude-a-role`](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices#give-claude-a-role) — Anthropic's role-prompting guidance; identity belongs in the system prompt.
- **Learn Prompting — Assigning Roles** — [`learnprompting.org/docs/basics/roles`](https://learnprompting.org/docs/basics/roles) — practitioner guide with worked examples of single-role and role-per-agent setups.
- **Prompting Guide (DAIR.AI)** — [`promptingguide.ai/introduction/elements`](https://www.promptingguide.ai/introduction/elements) — role as a first-class prompt element alongside instruction, context, and input.

Every multi-agent framework (LangGraph, CrewAI, AutoGen) instantiates Role-Per-Agent S3 by construction — each agent has a role definition — but the framework is not an implementation *of* S3 so much as a host that requires it. Treat them as known uses, not as libraries.

## Known Uses

- **Multi-agent frameworks** (CrewAI, AutoGen, LangGraph subgraphs) — each agent's definition starts with a role; this is Role-Per-Agent S3 at production scale.
- **Customer-support assistants** with a defined company voice and a named domain ("billing specialist", "technical support engineer") — single-role S3 stabilises voice across long sessions.
- **Coding assistants** (Cursor system prompts, Claude Code project-level personas) — persona blocks at the top of the system prompt establish the engineering register before the first turn.
- **Vertical agents** (legal-research assistants, clinical-summary assistants, code-security reviewers) — domain-expert personas are mandatory; almost always paired with S5 to disclaim authority and S9 to enforce safety principles.

## Related Patterns

- **Subsumed by** **H1 Identity Persistence** — H1 is the cross-session upgrade. The Genesis State *contains* an S3-style persona block along with accumulated commitments and an evolving self-model. Do not run S3 and H1 for the same agent.
- **Composes with** **S5 Constraint Framing** — S3 frames the *identity*; S5 frames the *prohibitions*. For any persona that implies authority (medical, legal, financial), pair them: persona alone creates false expertise.
- **Composes with** **S6 Output Template** — persona shapes content and voice; S6 shapes structure. Both go in the same setup.
- **Distinct from** **S9 Constitutional Framing** — S3 names *who* the model is; S9 names *which principles* it applies. A persona without principles is a voice without a value system; principles without a persona are values without a voice. They are different layers and they compose.
- **Required by** every other pattern's main LLM session (K5 Generator, K12 Curator, R4 ReAct agent, V15 Judge) — the "role" line in their setup tables is an S3 invocation.
- **Composes with** **O4 Parallelization** and **O6 Orchestrator-Workers** — the Role-Per-Agent variant is how multi-agent systems give each sub-agent a distinguishable contribution.

**Note on fundamentality.** S3 passes the test: it has its own forces (right identity activates the right knowledge cluster; wrong identity creates false expertise), a distinct Participant (the identity statement itself), and a distinct read pattern (set once at setup, inherited per turn without restatement). It does not decompose into another pattern plus an adaptor. It is, however, *strictly subsumed* by H1 — every H1 system has an S3-equivalent block as one of its Genesis-State components. S3 remains a separate pattern because most systems do not run H1, and S3 is the right default at the per-session scope.

## Sources

- White, J., Fu, Q., Hays, S., et al. (2023) — "A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT." PLoP 2023, arXiv 2302.11382. The *Persona Pattern* in the Output Customization category is the canonical written reference for S3.
- Anthropic — Claude prompting best practices, "Give Claude a role with a system prompt." Provider guidance treating identity as a system-prompt construct.
- Learn Prompting — "Assigning Roles" — practitioner-level treatment with worked examples.
- DAIR.AI Prompting Guide — "Elements of a Prompt" — role as a first-class prompt element.
- Brown et al. (2020) — *Language Models are Few-Shot Learners* — the in-context-learning mechanism that role prompting implicitly exploits.
