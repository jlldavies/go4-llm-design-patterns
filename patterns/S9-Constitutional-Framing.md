# S9 — Constitutional Framing

> Embed an explicit set of principles — a *constitution* — in the session setup, and have the model critique and revise its own output against those principles before returning it, so values and judgement live as inspectable text rather than as an implicit prior baked into weights.

**Also Known As:** Constitutional AI (inference-time), Principle-Based Alignment, Runtime Constitution, Self-Critique-and-Revise, CAI-at-Inference.

**Classification:** Category I — Signal · the setup-layer pattern that names *which principles the model applies*; complements **S3 Persona** (who the model is), **S5 Constraint Framing** (what it must not do), and **S6 Output Template** (what its output looks like). The inference-time form of Anthropic's Constitutional AI (Bai et al. 2022, training-time); the soft, in-prompt counterpart to **V7 AgentSpec** (hard, external policy enforcement).

---

## Intent

Make the model's value judgement legible, auditable, and updatable — by stating the principles explicitly in the prompt and inserting a self-critique-and-revise step that checks the draft against them before it is returned.

## Motivation

Every model already has implicit values: behaviours trained in through RLHF, default refusal patterns, a baseline politeness, an aversion to certain content. These are real, but they are *implicit* — the operator cannot inspect them, cannot point to them, cannot version them, and cannot reason about how they will apply in a context the trainer did not anticipate. When the model behaves well, the operator does not know why; when it behaves badly, the operator has no lever short of changing models.

S9 moves judgement out of the weights and into the prompt. The session setup carries a short, numbered list of principles — *"acknowledge uncertainty rather than fabricate; prioritise user safety over task completion; if a request implies medical, legal, or financial advice, recommend a qualified professional"* — and the per-call prompt includes a step that asks the model to draft, then critique that draft against the principles, then revise. The constitution is text: an operator can read it, edit it, version-control it, and audit any output against it. The same operator can compare two systems by comparing their constitutions, which is impossible when the values live only in weights.

This is the inference-time application of Bai et al.'s 2022 "Constitutional AI from AI Feedback." Their result was a *training* technique: use a constitution to generate critique-and-revision data, then fine-tune on it. S9 is the same critique-and-revise move, applied at *runtime* on every output, with the constitution carried in the system prompt rather than distilled into weights. The trade is the obvious one: weights are fast at inference but opaque and fixed; in-prompt is slower and probabilistic (mechanism 7) but inspectable and updatable. S9 earns its number because that trade — *make values legible at the cost of an extra LLM step per output* — is a distinct design move with its own forces, distinct from S3 (which names *identity*, not principles) and distinct from S5 (which enumerates *prohibitions*, not interpretive principles). Persona says who; prohibitions say what-not; the constitution says *how to judge* — interpretive guidance the model applies in cases the operator did not anticipate.

S9 is *soft*. The model applies its constitution through language reasoning: probabilistic, manipulable by adversarial input, not an enforcement boundary. That is the H/S complementarity with V7 (see Critical Conflicts in CONFLICTS.md, CRITICAL 3): S9 broad and interpretive, V7 narrow and deterministic. They layer; they do not substitute.

## Applicability

Use Constitutional Framing when:

- the system operates in a context — safety-critical, regulated, brand-sensitive, ethically charged — where outputs must be explainable against stated values, not just produced;
- the operator needs to **audit** outputs against principles, or to **update** the value framing without retraining;
- the constitution captures *interpretive* judgement (when to refuse vs. clarify, how to weigh helpfulness against caution) that cannot be enumerated as flat prohibitions;
- multiple agents in the system must share a consistent value framing across roles;
- you need a written, inspectable record of "what this system is supposed to believe about its work."

Do not use when:

- the requirement is a deterministic, enumerable rule ("never call `send_email` when the context contains classified data") — use **V7 AgentSpec**, which enforces the rule at runtime regardless of what the model "thinks";
- the requirement is a flat set of prohibitions with no interpretive content — use **S5 Constraint Framing**;
- the requirement is identity / register / voice rather than judgement — use **S3 Persona**;
- the principles themselves must evolve through experience with human oversight — use **H5 Constitutional Self-Alignment**, which extends S9 across sessions with a governed evolution loop (H5 requires V1 Human-in-the-Loop for every change);
- the cost of an extra critique-and-revise pass on every output is unacceptable and the implicit defaults of the model already cover the value space.

## Decision Criteria

S9 is right when value judgement must be legible and auditable, not just present — and when the principles are interpretive enough that no flat rule list could replace them.

**1. Audit requirement.** Will any output ever need to be defended by pointing at the principle that produced it? Compliance reviewers, safety teams, regulators, brand owners all ask this. If yes, the constitution must exist as text — S9 applies. If no one will ever ask "why did the agent decide that way?", the implicit defaults of the model are sufficient and S9 is overhead.

**2. Interpretive vs. enumerable.** Can you write the requirement as a list of forbidden tool calls, forbidden content patterns, or hard data-flow rules? If yes, **V7 AgentSpec** is the right layer — deterministic, surviving prompt manipulation, producing an audit trail. S9 carries the *spirit* of rules ("treat user wellbeing as a higher priority than completing the task"); V7 carries the *letter* ("`send_email` is prohibited when `context.classification == 'restricted'`"). In any safety-critical system you need both — S9 for the cases V7 didn't anticipate, V7 for the cases S9 was talked out of (CONFLICTS.md CRITICAL 3).

**3. Update cadence.** How often will the value framing need to change? Constitutions are text — an operator can edit one in minutes and redeploy with no training run. If the value framing is genuinely fixed forever, the implicit defaults of the model are equivalent. If the framing must evolve quarterly (brand voice, regulatory updates, post-incident learnings), S9's editability is decisive.

**4. Adversarial exposure.** How exposed is the system to prompt injection or user manipulation? S9 alone is *probabilistic* — a sufficiently clever adversarial prompt can talk a model out of its constitution; this is a documented failure mode (jailbreaks targeting the constitution). High-exposure systems must layer V7 (deterministic) under S9 (interpretive). If exposure is low (internal tool, single-trusted-user), S9 alone may suffice; if exposure is open-internet, S9 alone is insufficient on principle.

**5. Cost budget per output.** The self-critique-and-revise loop adds at least one extra LLM step per output (critique) and often two (critique + revise). On a budget-sensitive surface (chat tier, high-volume backend) measure the latency and token cost; if a single capable model already produces principle-aligned output by default, the critique step buys little. The cheapest implementation uses the same model for draft, critique, and revise in one turn; the most reliable uses a separate, sometimes smaller, critic session.

**Quick test — S9 is the right pattern when:**

- outputs may need to be defended by pointing at a stated principle, *and*
- the value framing is interpretive (judgement, weighing trade-offs) rather than enumerable, *and*
- the value framing will need to change without retraining, *and*
- you can afford one extra LLM step per output for self-critique and revision.

If the requirement is enumerable, use **V7 AgentSpec** instead (and pair S9 + V7 in safety-critical systems). If the requirement is identity rather than judgement, use **S3 Persona**. If the requirement is a flat list of prohibitions, use **S5 Constraint Framing** (S9 provides the principles; S5 turns selected principles into hard prohibitions). If you need principles that *evolve* across sessions with human review, use **H5 Constitutional Self-Alignment**.

## Structure

```
  Session setup (once)
       │
       ▼
   Constitution: numbered list of principles loaded into the system prompt
       │
       ▼
   ┌───────────────────────  Per-call loop  ───────────────────────┐
   │                                                                │
   │   User query                                                   │
   │       │                                                        │
   │       ▼                                                        │
   │   1. Draft        — generate a candidate response              │
   │       │                                                        │
   │       ▼                                                        │
   │   2. Critique     — check the draft against each principle     │
   │                     (same model, or a separate critic session) │
   │       │                                                        │
   │       ▼                                                        │
   │   3. Revise       — rewrite the draft to address the critique  │
   │       │                                                        │
   │       ▼                                                        │
   │   Final answer (and, optionally, the critique as audit record) │
   └────────────────────────────────────────────────────────────────┘
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Constitution** | the principles themselves, as inspectable text | — $\to$ numbered list loaded once at setup | be implicit, unversioned, or scattered across prompts. A constitution that lives only in one engineer's head is not a constitution; it is a hope. |
| **Drafter (LLM)** | producing the candidate response | query + role + (constitution visible) $\to$ draft | be told to "self-police" inline. Mixing the draft and the critique in one pass collapses the pattern; the critique is meant to be a *separate* judgement step. |
| **Critic (LLM)** | scoring the draft against each principle and producing a critique | draft + constitution $\to$ critique (per-principle pass/fail with rationale) | revise the draft itself — that is the Reviser's job. Conflating critic and reviser produces lip-service revisions that erase the critique signal. |
| **Reviser (LLM)** | rewriting the draft to address the critique | draft + critique + constitution $\to$ revised answer | introduce new claims unsupported by the draft or the input. The Reviser is bounded to *addressing the critique*, not rewriting from scratch. |
| **Audit Sink** *(optional)* | persisting the critique alongside the output | (draft, critique, revised) $\to$ durable record | be optional in regulated contexts. In compliance settings the critique *is* the audit artefact. |

The Drafter / Critic / Reviser can all be the **same model in three separate sessions** with different setups, or three distinct model choices (often a smaller/cheaper critic). What must not collapse is the *separation of responsibility* — the moment one session does both draft and critique, the model finds reasons its draft was fine. There is also a mechanistic basis for separation: in a separate session, the Critic's Q-K attention computations are performed over the draft text alone, not over the reasoning tokens that generated the draft. The Drafter's generative context does not exist in the Critic's KV cache (mechanism 6, mechanism 3). This is subagent decomposition as context bounding: each agent's seq_len is bounded, the O(n²) cost is isolated, and the probability distribution the Critic samples from is not contaminated by the generative chain. A same-session self-check has the full generation in its attention horizon.

## Collaborations

At session setup, the operator loads the Constitution — a short numbered list of principles — into the system prompt. This is done once; subsequent turns inherit it. When a user query arrives, the Drafter generates a candidate response in the normal way, with the constitution visible (so the draft is already aligned where possible). The Critic then receives the draft along with the constitution and produces a per-principle judgement: for each principle, does the draft honour it, and if not, what is the specific concern? The Reviser receives the draft and the critique and produces a revised answer that addresses the concerns the critique raised — not a rewrite from scratch, just the targeted fix. The revised answer is returned to the user; the critique itself is optionally persisted by the Audit Sink as a record of *why* the system produced what it did.

A bound on the critique-revise cycle (one pass typically, two at most) keeps cost predictable; see V9 Bounded Execution. In a system that also runs V7 AgentSpec, V7's deterministic checks run *after* the Reviser — V7 is the floor, S9 is the interpretive ceiling, and the V7 check catches the case where the model was talked out of its own constitution by adversarial input.

## Consequences

**Benefits**
- Values live as inspectable, editable, version-controllable text.
- Outputs can be defended ("which principle led to that decision?") and audited against a stable artefact.
- The constitution can be updated in minutes — no retraining, no model swap, no waiting for the next foundation-model release.
- The same constitution can be shared across agents, giving a multi-agent system consistent value framing.
- The critique-revise loop catches a meaningful share of would-be policy violations the drafter would otherwise return.

**Costs**
- One extra LLM step per output (critique), often two (critique + revise). Tokens, latency, money.
- The constitution itself occupies prompt budget — short, terse principles matter.
- A poorly written constitution underperforms a well-trained implicit default — the operator now owns a new authoring problem.
- The pattern caches well in steady state (the constitution is stable prefix) but every constitution edit invalidates the cache. For Anthropic deployments: constitutions exceeding 1024 tokens qualify for provider prefix caching (mechanism 5) at ~10% of normal input token cost per cache hit, TTL ~5 minutes. A 10-principle constitution is typically well under 500 tokens — compose with the rest of the stable system prompt (S3, S5) to form a single cacheable prefix unit exceeding the threshold. Every constitution edit invalidates the prefix cache; batch edits at maintenance windows to preserve the caching benefit.

**Risks and failure modes**
- *Probabilistic enforcement.* The model can be talked out of its constitution by adversarial input. Calling an S9 system "aligned" without a V7 deterministic floor is overclaiming.
- *Lip-service critique.* The Critic, when run as the same model in the same turn as the Drafter, often produces a token-rich critique that says nothing — every principle marked "satisfied" — and the Reviser changes nothing. Separating sessions, and asking the critique to find at least one weakness, mitigates this.
- *Principle conflict.* "Be maximally helpful" and "refuse anything that could conceivably cause harm" pull opposite ways; the model resolves by picking one and ignoring the other, often invisibly. Constitutions must explicitly order or trade off the principles.
- *Constitution bloat.* Long constitutions degrade — past ~10 principles the model attends partially due to mid-context under-attendance (mechanism 4). Keep it short, terse, ordered.
- *Drift across edits.* Without version control on the constitution itself, a quarter of unreviewed edits leaves an unrecognisable document. Treat the constitution like code.

## Implementation Notes

- Write the constitution as **short, numbered, terse principles** — five to ten lines, each one sentence. Long-prose constitutions degrade. Anthropic's published constitutions and the LangChain constitutional principles library are good calibration.
- **Order** the principles deliberately — the model attends first and last most strongly. Put the most safety-critical principle first.
- Pair S9 with **S3 Persona** when the persona implies authority the constitution must constrain ("you are a senior security engineer; principle 1: never claim certifications you do not hold").
- Pair S9 with **S5 Constraint Framing** for the subset of principles that *can* be turned into flat prohibitions — S5 enumerates those, S9 covers the interpretive remainder.
- Pair S9 with **V7 AgentSpec** in any safety-critical context — S9 for interpretation, V7 for deterministic floor. **Always both.**
- The **Critic session should be a separate session** from the Drafter, even when using the same model. Different setup, different invocation. Same-session "self-check" produces lip-service.
- Bound the critique-revise loop to one or two passes (V9 Bounded Execution) — diminishing returns past two.
- **Version the constitution.** A change to principle 3 should produce a constitution v1.4.0 with a changelog; outputs should be tagged with the constitution version that produced them.
- For low-latency tiers, consider running the Critic only on outputs that match a triage classifier (a tiny pre-filter LLM-as-Judge) — most outputs do not need the full loop.
- The constitution is **stable prefix** — it caches well across calls. Edits invalidate cache; batch edits at known maintenance windows. For Anthropic deployments: constitutions exceeding 1024 tokens qualify for provider prefix caching (mechanism 5) at ~10% of normal input token cost per cache hit, TTL ~5 minutes. Compose the constitution with the rest of the stable system prompt (S3 persona, S5 constraint block) to form a single cacheable prefix unit exceeding the threshold; editing any component invalidates the full prefix cache.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** S9 chains a Drafter, a Critic, and a Reviser against a shared Constitution loaded at setup. Composes with **S3** (the Drafter's role), **S5** (any principle that is flat enough to enumerate as a hard prohibition), **S6** (output template for the Critic's per-principle verdict), **V9** (bound on the critique-revise loop), **V7** (deterministic post-check independent of S9), and **V14** (persist the critique as audit). Echoes **R7 Reflexion** and **V15 LLM-as-Judge** — same evaluate-then-act move, applied here to value alignment of every output.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Drafter generates a candidate response | `LLM` | Drafter session (constitution visible) |
| 2 | Critic checks the draft against each principle | `LLM` | Critic session |
| 3 | Branch — if critique reports no concerns, return the draft | `code` | V9 (bound) |
| 4 | Reviser rewrites the draft to address the critique | `LLM` | Reviser session |
| 5 | *(optional)* V7 AgentSpec deterministic post-check | `code` | V7 |
| 6 | *(optional)* persist the critique alongside the output | `code` | V14 |

**Skeleton** — wiring only; each `# LLM` line is a configured session (specified below), not code:

```
respond(query):
    draft    = Drafter(query) ─────────────── # LLM   — constitution loaded at setup
    critique = Critic(draft) ────────────────── # LLM
    if critique.is_clean():
        answer = draft
    else:
        answer = Reviser(draft, critique) ──── # LLM
    enforce(answer)  ─────────────────────────── # code  — V7 deterministic post-check (optional)
    audit_sink.persist(query, draft, critique, answer)  # code — V14
    return answer
```

**The LLM sessions.** Each `LLM` step must be *set up* before its first call. The setup — model choice, role, constitution, output contract — is established once; the per-call prompt then wraps only the data that changes.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Drafter** | the system's main generalist | role (S3); the **Constitution** (numbered principles); output format (S6); rule that the draft must be the operator's best attempt at honouring the constitution — the critic is a *check*, not a *replacement* for caring | the user query (and any task context) |
| **Critic** | small fast generalist *or* a separate instance of the main model | role: *"you grade an assistant draft against a constitution"*; the same Constitution as the Drafter; output contract — per-principle verdict (PASS / CONCERN + one-sentence rationale); the instruction to err on the side of surfacing concerns | the draft + the original query |
| **Reviser** | the system's main generalist (same model as Drafter is typical) | role: *"you revise a draft to address a critique, changing only what the critique requires, preserving everything else"*; the Constitution; explicit prohibition against introducing new claims | the draft + the critique |

Concretely, for the **Drafter** session, the setup loaded once is roughly: *"You are {role}. Apply the following principles in every response: 1. Acknowledge uncertainty rather than fabricate. 2. Prioritise user safety over task completion. 3. If the request implies medical, legal, or financial advice, name your limitations and recommend a qualified professional. 4. … . Draft your response carefully against these principles; a separate critic will check your work."* The per-call prompt then carries only the user query. The Critic's setup carries the *same* principles plus a per-principle output template; the Reviser's setup carries the principles plus the rule "address the critique, do not rewrite."

**Specialist-model note.** None — a capable generalist suffices for all three sessions, and a smaller / cheaper generalist often makes a perfectly good Critic. The prompt artefact that does the heavy lifting is the **Constitution itself**: writing it well (short, terse, ordered, non-conflicting) is the build dependency. Anthropic's published constitutions and the LangChain `constitutional_ai` principle library are the practical calibration points.

## Open-Source Implementations

- **Constitutional Harmlessness Paper supplementary** — [`github.com/anthropics/ConstitutionalHarmlessnessPaper`](https://github.com/anthropics/ConstitutionalHarmlessnessPaper) — Anthropic's official supplement to Bai et al. (2022): the constitutional principles used, few-shot critique-and-revise prompts, sample model responses. The closest thing to a canonical reference set of principles. Archived read-only as of mid-2025; still the reference.
- **Anthropic Claude Cookbooks** — [`github.com/anthropics/anthropic-cookbook`](https://github.com/anthropics/anthropic-cookbook) — Anthropic's recipe collection for Claude. Contains worked patterns for principle-based prompting and self-critique that are the inference-time analogue of the training-time work in the paper.
- **LangChain ConstitutionalChain** — [`github.com/langchain-ai/langchain`](https://github.com/langchain-ai/langchain) (`libs/langchain/langchain/chains/constitutional_ai/`) — the most-used inference-time implementation: a chain that drafts, critiques, and revises against a list of `ConstitutionalPrinciple` objects. Deprecated in favour of a LangGraph re-implementation but still the reference for the pattern's shape; the principles file ships a library of pre-written principles (UDHR-derived, harm-avoidance, etc.) usable as drop-ins.
- **AWS bias-mitigation samples** — [`github.com/aws-samples/bias-mitigation-foundation-models`](https://github.com/aws-samples/bias-mitigation-foundation-models) — production-style notebook applying ConstitutionalChain on Amazon Bedrock for content-policy alignment.
- **Collective Constitutional AI data** — [`github.com/saffronh/ccai`](https://github.com/saffronh/ccai) — data-processing repo for Anthropic $\times$ Collective Intelligence Project's public-input constitution. Useful as an example of constitution authoring at scale.
- **Constitutional AI awesome papers** — [`github.com/minbeomkim/Constitutional-AI-awesome-papers`](https://github.com/minbeomkim/Constitutional-AI-awesome-papers) — curated paper list for the wider CAI / ethics-guided LM literature.

## Known Uses

- **Anthropic Claude** — Claude's RLAIF training pipeline uses a constitution; the inference-time form of the same idea is now standard practice for system-prompt construction by Claude-deploying teams.
- **Enterprise content assistants** — brand-voice constitutions, safety constitutions, and regulatory constitutions are routinely loaded into system prompts for customer-facing assistants; LangChain's `ConstitutionalChain` is a common starting point.
- **Compliance-sensitive deployments** — financial, healthcare, and legal-tech assistants pair an S9 constitution with V7 AgentSpec deterministic enforcement; the constitution is the legible artefact reviewers read, V7 is the enforced floor.
- **Collective Constitutional AI** — Anthropic $\times$ Collective Intelligence Project published a constitution derived from ~1,000 U.S. adults' input and used it for an inference-time deployment, as proof that a constitution can be *democratically* authored.

## Related Patterns

- **Composes with** **S3 Persona** — S3 names *who* the model is; S9 names *which principles* it applies. Both load at setup. *When the persona implies latitude the constitution prohibits, S9 takes precedence* — state this explicitly (CONFLICTS.md S3 ~ S9).
- **Composes with** **S5 Constraint Framing** — S5 enumerates *flat prohibitions*; S9 provides the *interpretive principles* those prohibitions implement. S5 is the subset of S9's principles that can be turned into a hard "do not" list. Use both: S9 for spirit, S5 for letter.
- **Composes with** **S6 Output Template** — the Critic's per-principle verdict is an S6 structured output (per-principle PASS / CONCERN + rationale).
- **Composes with** **V9 Bounded Execution** — the critique-revise loop must be capped; one or two passes is standard.
- **Hard/Soft complement of** **V7 AgentSpec** — *the* critical pairing. S9 is soft, broad, in-prompt (probabilistic, can be manipulated by adversarial input); V7 is hard, specific, external (deterministic, audit-trailed, survives prompt manipulation). They are not alternatives — they layer. In safety-critical systems, both are mandatory: S9 catches the cases V7 did not enumerate; V7 catches the cases S9 was talked out of. Calling an S9-only system "aligned" is overclaiming. See CONFLICTS.md CRITICAL 3.
- **Extended by** **H5 Constitutional Self-Alignment** — H5 lets the constitution *evolve* across sessions through experience, with mandatory human review at every change (H5 $\to$ V1, no exceptions). **H5 evolves principles; S9 applies them.** A system with no need to evolve its values uses S9; a long-running system in an evolving domain pairs S9 (apply) with H5 (evolve, governed).
- **Shares the evaluate-then-act mechanism with** **R7 Reflexion** and **V15 LLM-as-Judge** — same draft / critique / revise move, applied here to *values* rather than to *task quality*. The patterns are distinct because the critique target is different (principles vs. correctness vs. rubric), but the implementation skeleton is the same.
- **Distinct from** **S3 Persona** — identity is not principles. A persona implies a knowledge cluster and a register; a constitution states judgements. Operators conflate them at their cost: a persona without a constitution can have wrong values delivered with confidence; a constitution without a persona has right values delivered with no register.
- **Distinct from** **S5 Constraint Framing** — prohibitions are not principles. S5 says *do not do X*; S9 says *here is how to judge whether X-shaped things are appropriate*. The constitution generates the prohibition list; the prohibitions do not generate the constitution.

## Sources

- Bai et al. (2022) — "Constitutional AI: Harmlessness from AI Feedback" (Anthropic). The foundational paper; established the training-time form of the critique-and-revise loop against a constitution. arXiv 2212.08073.
- Anthropic (2023–2024) — Claude system-prompt practice and published values documents; the inference-time application of the same idea.
- Huang, S. et al. / Anthropic & Collective Intelligence Project (2024) — "Collective Constitutional AI: Aligning a Language Model with Public Input" (arXiv 2406.07814). The democratically-authored constitution case study.
- LangChain documentation — `ConstitutionalChain` and the `constitutional_ai` principles library; the most widely adopted inference-time implementation in the OSS ecosystem.
- White et al. (2023) — "A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT" — the prompt-pattern context in which Constitutional Framing sits at the Signal layer.
