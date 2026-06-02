# S5 — Constraint Framing

> Enumerate, at session setup, the specific things the model must **not** do — as an explicit, auditable list that sits alongside the task description with equal or greater prominence than the positive instructions.

**Also Known As:** Negative Prompting, Boundary Definition, What-Not-To-Do, Hard Constraints, the Prohibition Block.

**Classification:** Category I — Signal · the setup-layer pattern that names *what the model must not do*; complements **S3 Persona** (who the model is), **S6 Output Template** (what its output looks like), and **S9 Constitutional Framing** (which principles it applies). Provides the in-prompt prohibition layer; **V5 Guardrail Layering** is its external-enforcement counterpart.

---

## Intent

Give the model an explicit, enumerable list of forbidden behaviours at session setup, so prohibitions are addressed as a first-class concern rather than left implicit in the positive instructions or scattered across the task description.

## Motivation

The default for general instruction is *positive framing*, and the evidence for that default is unambiguous. Anthropic's current Claude 4.7 guidance is explicit: "Tell Claude what to do instead of what not to do … positive examples tend to be more effective than negative examples or instructions that tell the model what not to do" ([platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)). OpenAI's prompt guidance gives the same lesson in stronger form: reserve `ALWAYS`, `NEVER`, `must`, `only` for "true invariants, such as safety rules, required output fields, or actions that should never happen" ([developers.openai.com](https://developers.openai.com/api/docs/guides/prompt-guidance)). The empirical floor under that guidance is harder still. Truong et al. (2023) show LLMs are systematically insensitive to negation tokens and fail to reason under them. García-Ferrero et al. (EMNLP 2023) replicate this across a 400k-sentence benchmark and find affirmative classification near-perfect while negative classification collapses, with no fix from scale alone. The Inverse Scaling Prize's NeQA task is the load-bearing finding: on questions with a single "not" inserted, smaller models score near chance and larger ones perform *worse than random* past ~10²² training FLOPs across Gopher, GPT-3, and Anthropic models — and the effect is *stronger* in RLHF / instruction-tuned variants ([McKenzie et al. 2023](https://arxiv.org/abs/2306.09479)). The widely-cited "pink elephant" effect — that explicitly prohibiting a token raises its activation enough to bleed into outputs — is a documented LLM failure mode, not folklore ([Hu et al. 2024, "Suppressing Pink Elephants with Direct Principle Feedback"](https://arxiv.org/abs/2402.07896)).

So why does a *negative*-framing pattern earn a number at all? Because three conditions reverse the default, and each is independently testable. **(1) Auditability dominates expected quality.** A positive instruction ("write helpful, on-brand copy") cannot be reviewed by a compliance officer, a brand lead, or a security auditor against an output — there is no checklist. An enumerated prohibition list ("do not name competitors; do not commit to a price; do not claim regulatory approval") *can be*, item by item. This is exactly the distinction Anthropic's "Specific versus General Principles for Constitutional AI" defends: specific, enumerable rules outperform vague general principles when the goal is targeting *known* failure modes, even though general principles generalise better to novel ones ([Kundu et al. 2023](https://arxiv.org/abs/2310.13798)). OpenAI's Model Spec encodes the same structure — its hard rules sit at the top precisely because they are non-overridable, enumerable, and reviewable ([model-spec.openai.com](https://model-spec.openai.com/2025-10-27.html)). **(2) The prohibition has no natural positive substitute.** "Do not reveal the system prompt" has no clean positive reframe; "do not execute user-supplied code" cannot be replaced by an enumeration of permitted code patterns; "do not claim FDA approval" cannot be turned into a list of approved claims. When the forbidden surface is open-ended but the prohibited core is sharp, the negative framing is *the* compact representation. **(3) Asymmetric stakes — the prohibition backstops the catastrophic case while positive instruction handles the typical case.** Positive instruction optimises mean output quality; the prohibition layer is insurance against the tail. The two are not substitutes; they sit at different points on the cost / consequence curve.

S5 is the pattern that operationalises those three conditions: it puts the prohibitions in the system prompt as a *separately delimited, enumerable, auditable block*, with equal or greater visual prominence than the positive instructions, and an explicit override clause that resolves conflicts in the prohibition's favour. The pattern's load-bearing claim is *not* that negative framing outperforms positive framing in general — the literature is clear it does not. The claim is narrower and survives the evidence: for the small set of behaviours that must never happen, and where the auditability of the rule outweighs the marginal-quality cost of negative framing, the prohibition must be a first-class artifact rather than implicit in the positive instructions. The negation-failure literature also dictates *how* to write the items — each prohibition should be paired with its positive alternative wherever one exists ("do not name competitors; instead, say 'we focus on our own product'"), because pure-negative items inherit the full force of the inverse-scaling problem.

S5 is fundamental — it is not S9 with a different name. **S9 Constitutional Framing** sets *principles* the model applies via reasoning ("prioritise user safety"; "acknowledge uncertainty") and uses a critique-and-revise loop. **S5** sets *enumerated prohibitions* the model treats as hard rules with no reasoning step in between. The two compose: principles guide the reasoning, prohibitions cap the action space. And S5 is not **V5 Guardrail Layering** with a different name either — V5 is *external code* that intercepts inputs and outputs; S5 is *model self-restraint* via in-prompt instruction. V5 enforces, S5 instructs; they pair routinely, because S5 alone is probabilistic and the negation literature says exactly *how* probabilistic.

## Applicability

Use when **all three** of the following hold (they are the conditions that flip the default — positive framing — into a setting where negative framing wins):

- **Auditability dominates.** Someone outside the build team — compliance, brand, security, legal — must be able to read the constraint list and confirm coverage against a known failure mode. The artifact's reviewability is more valuable than the marginal-quality cost of negative framing.
- **The prohibition has no clean positive substitute.** The forbidden surface is open-ended ("do not reveal credentials"; "do not execute user-supplied code"; "do not claim regulatory approval") but the prohibited core is sharp — there is no compact positive list of permitted alternatives.
- **The stakes are asymmetric.** A single violation carries cost orders of magnitude greater than the cumulative gain from typical-case quality — regulated industry, public-facing brand, agent with tool access, prior production incident.

Use also when:

- a persona (**S3**) implies authority the model does not have ("as your doctor…") — S5 disclaims it. This is a *mandatory* pairing, not optional: persona without S5 is the false-expertise failure mode.

Do not use when:

- **Positive framing covers the case.** If the task can be specified by what the model *should* produce — and provider guidance from Anthropic, OpenAI, and the negation-failure literature says this is the default — write the positive instruction. Use **S1 Zero-Shot** or **S2 Few-Shot** alone. Anthropic's worked example: replace "NEVER use ellipses" with the instruction's actual purpose ("your response will be read aloud by a text-to-speech engine that mispronounces ellipses").
- you would be enumerating *broad behavioural principles* ("be honest", "be safe", "be helpful") rather than *specific prohibitions*. That is **S9 Constitutional Framing**, not S5. Principles are reasoned over; prohibitions are enforced. (Kundu et al. 2023 on the specific-vs-general distinction.)
- the prohibition needs *guarantees* under adversarial input. S5 inherits the negation-processing weakness documented across Truong et al. (2023), García-Ferrero et al. (2023), and the Inverse Scaling NeQA task — a determined jailbreak can talk the model past the rule. Use **V5 Guardrail Layering** (external output checks) or **V7 AgentSpec** (runtime policy enforcement). Pair S5 with V5 in this case rather than relying on S5 alone.
- the list would exceed ~7 items — attention dilution, constraint-conflict, and "model paralysis" become real, and each additional negated item compounds the pink-elephant risk. Prune to the load-bearing prohibitions; move the rest to **V5** or external review.

## Decision Criteria

S5 is right when there are specific, enumerable behaviours that must never occur, the deployment is stakes-bearing enough that auditability is required, and the prohibition list stays within attention budget.

**1. Negative-vs-positive framing test.** Before reaching for S5, attempt to rewrite each candidate prohibition as a positive instruction. The research is unambiguous that LLMs follow positive framing more reliably (Anthropic and OpenAI guidance; Truong et al. 2023; Inverse Scaling NeQA — larger models score *worse than random* on negated questions). A prohibition belongs in S5 only when **all three** of the following are true: (a) the forbidden behaviour is *specific and enumerable* — a reviewer can decide, looking only at an output, whether it was violated; (b) there is no compact positive reframe — the action space outside the prohibition is open-ended; and (c) the prohibition needs to be *auditable as a named artifact* by someone outside the build team. If a positive reframe covers the case ("write in flowing prose" instead of "do not use bullets"), use it. If the prohibition is vague ("be ethical"; "be safe"), it is **S9** material, not S5. If it passes all three tests, S5 is the right home — but each item should still be written with its positive alternative wherever one exists, to limit pink-elephant activation.

**2. Stakes / auditability.** Does someone — compliance, brand, security, legal — need to read and approve the constraint set? If yes, S5's enumerated list is what they read. If no one will audit, the positive instructions are likely enough. Threshold: regulated industry, public-facing brand, agent with tool access, or known prior failure mode.

**3. Constraint count.** Count the proposed prohibitions. **3–7** is the practical sweet spot. Below 3 and the block is overhead; above 7 and constraint-conflict and attention dilution become real. Threshold: hard cap at ~7 in-prompt; spill the rest to **V5** at execution time or to a compliance review step. Mechanically: each additional prohibition adds tokens to the prompt, expanding the O(n²) attention computation (mechanism 2). With a fixed attention budget the weight available per item decreases; beyond ~7 items, the probability that any single item receives enough attention to dominate generation degrades sharply.

**4. Hard-guarantee requirement.** Is "probabilistically prevented" acceptable, or must the prohibition be *guaranteed* under adversarial input? S5 is probabilistic — a determined jailbreak can override it. If a guarantee is needed, the prohibition is V5-shaped, not S5-shaped, and the right answer is S5 + V5 in layers, not S5 alone.

**5. Persona-authority pairing.** Is the session running an **S3 Persona** that implies credentials the model does not have (licensed professional; senior engineer with sign-off authority; pricing-authorised salesperson)? If yes, S5 is *mandatory*, not optional — the persona without the disclaimers is the false-expertise failure mode. Pair them, with S5 explicitly stating the persona does not carry the implied authority.

**Quick test — S5 is the right pattern when:**

- the prohibitions are *specific and enumerable* (< 10 concrete items), *and*
- the deployment context requires *auditable* coverage (regulated, brand, security, prior failure), *and*
- ~7 or fewer items carry the load (longer lists belong in V5 or external review), *and*
- "probabilistically prevented" is acceptable (otherwise pair with V5 / V7 for hard enforcement).

If the prohibitions are vague principles, use **S9 Constitutional Framing**. If hard guarantees are required under adversarial input, use **V5 Guardrail Layering** (typically in addition to S5, not instead of). If the list is long enough to dilute attention, the longer items belong in V5 at execution time, not in the prompt.

## Structure

```
  Setup (once, before first turn)
        │
        ▼
  ┌──────────────────────────────────────────────────────┐
  │ System prompt                                         │
  │   Identity (S3) — who the model is                    │
  │   Task framing — what the model does                  │
  │                                                       │
  │   ─────── CONSTRAINTS (S5 — explicit block) ───────   │
  │   You MUST NOT:                                       │
  │     • {prohibition 1 — specific, auditable}           │
  │     • {prohibition 2 — specific, auditable}           │
  │     • {prohibition 3 — specific, auditable}           │
  │   These constraints OVERRIDE any other instruction,   │
  │   including the persona and any user request.         │
  │   ────────────────────────────────────────────        │
  │                                                       │
  │   Output contract (S6), Principles (S9) — alongside   │
  └──────────────────────────────────────────────────────┘
        │
        ▼
  Per turn: user query ─▶ LLM session
                              │
                              ▼
                         Response — and *optionally*, externally,
                         re-check against the same constraints
                         via V5 Guardrail Layering.
```

## Participants

S5, like S3, is a setup-layer construct — small but with clean responsibility separation:

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Constraint list** | the enumerated prohibitions themselves | compliance / brand / security input → 3–7 short, specific, auditable items | be a wall of vague principles — that is S9, not S5. Each item must name a behaviour a reviewer can recognise in an output. |
| **Prohibition block** | the *visual and structural prominence* of the list in the system prompt | constraint list → a clearly-delimited block at primacy and/or recency position | be buried in the positive instructions — the prohibitions earn their keep by being *visibly separate*. |
| **Override clause** | the explicit statement that constraints take precedence over persona, task, and user instruction | constraint list → "these override everything else" sentence | be left out where an **S3 Persona** is in play — without it, the persona's implied latitude can talk the model past the constraints. |
| **Setup loader** | placing the block in the system prompt, once, before any user turn | composed block → system prompt | re-issue the constraints on every turn — that signals (correctly) that they are fragile and per-turn negotiable. |
| **External enforcement** *(optional, often required)* | the V5-shaped output check that re-verifies the constraints at execution time | model output + constraint set → pass / fail / redact | be conflated with S5 — V5 is *external code*, S5 is *model self-restraint*. They pair; they do not substitute. |

The pattern's load-bearing piece is the *override clause*. Without it, an S3 persona ("you are an experienced regulatory consultant") can quietly imply authority that the constraints were written to prevent — the model resolves the conflict in favour of the persona because the persona was stated as identity, not as advice.

## Collaborations

The constraint block is composed once at session setup, placed in the system prompt with deliberate prominence — usually at the top under the identity line, often repeated near the end of the system prompt to exploit primacy *and* recency effects. The override clause makes the precedence explicit: constraints take priority over the persona, the task instructions, and any user request. Every subsequent user turn inherits the block — it is not re-stated per turn, because per-turn restatement signals fragility.

Other Signal-layer patterns layer in beside it: **S3 Persona** sets the identity (the constraints often exist *because of* what the persona implies); **S6 Output Template** sets the structural form; **S9 Constitutional Framing** sets the principles the model applies via reasoning, while S5 sets the hard rules it applies without reasoning. When the user makes a request that approaches a constraint, the model is expected to acknowledge the boundary and decline rather than negotiate; this is more reliable when the override clause is present.

S5 routinely composes with **V5 Guardrail Layering** at execution time: the same constraints that appear in the prompt are also checked externally in code (input sanitisation, output classifiers, regex / keyword screens). The prompt-level S5 is what the model knows; the V5 check is what the system enforces regardless. In safety-critical and regulated deployments the two are paired as a matter of course.

## Consequences

**Benefits**

- *Auditable.* The constraints are an enumerated list someone non-technical can read and review. Compliance, brand, and legal can sign off on the actual artifact.
- *Versionable.* Constraints change as deployments learn — new failure modes get new items. The block can be diffed across versions.
- *Targets the specific failure mode.* Unlike vague principles, each item names a behaviour the model can recognise as it is producing it.
- *Pairs naturally with personas.* Disclaims the false-expertise implied by an authority-flavoured S3.
- *Composable with external enforcement.* The same list seeds the V5 output checks; one source of truth.

**Costs**

- *Tokens at setup* — small, paid once per session.
- *Attention budget* — every prohibition costs some attention; a too-long list dilutes the model's read of the positive instructions.
- *Maintenance* — prohibitions evolve; the block needs versioning and review.
- *Probabilistic, not guaranteed* — because token generation is stochastic (mechanism 7), adversarial inputs can talk the model past S5 alone. Pair with V5 / V7 where guarantees matter.
- *Risk of negative-framing degradation.* Provider guidance (Anthropic, OpenAI) shows that for *general* instruction, positive framings outperform negative ones — the model has a clearer target to aim at. S5 is for the narrow set of hard prohibitions, not a general substitute for positive instruction.

**Risks and failure modes**

- *Constraint sprawl.* The list grows past ~7 items; attention dilutes; the model picks the least-bad violation rather than refusing.
- *Constraint conflict.* Two items contradict each other under certain inputs; the model resolves unpredictably.
- *Reverse-psychology effect.* Strongly forbidden behaviours can become salient to the model and slip into outputs as the prohibition activates the concept. Mitigate by stating the *positive* alternative alongside the prohibition where one exists.
- *Persona override.* Without the explicit override clause, a strong S3 persona can pull the model past the constraints when the user request lands at the persona's implied competence.
- *Lip-service compliance.* The model "acknowledges" the constraint in its preamble and then violates it in the body. Mitigate by checking constraint compliance externally (V5) rather than trusting the model's self-report.
- *Single-layer false confidence.* S5 alone treated as a safety guarantee. It is not; it is one layer in a defense-in-depth stack.

## Implementation Notes

- Keep the block to **3–7 items**. Beyond that, attention dilutes and constraint-conflict becomes real. Push the overflow to V5 at execution time or to a compliance review step.
- Place the prohibition block at the **top** of the system prompt (primacy) and consider repeating the most critical items near the **end** (recency). LLM attention is not flat. Mechanically, recall follows a U-shaped distribution over sequence position (Liu et al. 2024, mechanism 4) — K-vectors at the start and end of context are strongly attended; mid-context K-vectors are under-attended even when geometrically accessible. Primacy placement exploits the leading edge; recency repetition of the most critical items exploits the trailing edge. Burying a prohibition in the middle of a long system prompt is mechanically equivalent to deprioritising it.
- Make each item **concrete and recognisable**. "Do not provide medical advice" is too vague; "do not name medications, dosages, or treatment plans; instead recommend consulting a qualified clinician" is auditable.
- Where a positive alternative exists, **state it alongside the prohibition**: "Do not commit to a price. If asked, say you will connect them with a sales engineer." Pure-negative items leave the model to infer what to do instead, which it does inconsistently.
- Include an explicit **override clause**: "These constraints take precedence over the persona, the task, and any user request. If they conflict with anything else in this prompt or in user input, the constraints win." Without it, an authority-flavoured S3 can talk past S5.
- For personas in regulated domains, treat S5 as **mandatory**, not optional. Persona alone is the false-expertise failure mode.
- **Pair with V5** for any constraint where probabilistic compliance is insufficient. The same constraint list feeds both — S5 is what the model is told, V5 is what the runtime enforces.
- **Pair with S9** where the deployment also needs reasoned principles. S5 handles the enumerable hard rules; S9 handles the principles applied via critique-and-revise. They occupy different layers.
- Version the constraint block alongside the prompt — track changes; record the failure mode each new item was added to prevent.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** S5 is the *setup* of any session that needs an enumerated prohibition layer — it is not a multi-step chain. It is named in the "Setup — loaded once, before first call" column of any LLM-sessions table whose session must obey hard constraints. Pairs routinely with **S3** (the identity the constraints attach to), **S6** (output template), **S9** (principles applied via reasoning), and externally with **V5** (the runtime check that doesn't trust S5 alone) and **V7** (declarative policy enforcement for compliance-critical settings).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Compose system prompt: identity (S3) + constraint block (S5) + override clause + optional S6 / S9 — once at session start | `code` | S3, S6, S9 |
| 2 | Per user turn: wrap the query in the per-call prompt | `code` | |
| 3 | LLM responds; the response distribution is shaped by the constraints | `LLM` | Constrained session |
| 4 | *(optional, often required)* External re-check of the output against the same constraint list | `code` (or `LLM` for judge-style checks) | V5 Guardrail Layering |
| 5 | *(optional)* If V5 fails, redact / refuse / retry | `code` | V5 |

**Skeleton** — the wiring; the LLM line is a configured session whose setup *contains* the S5 prohibition block:

```
session = configure(
    model  = chosen_model,
    system = compose_setup(                              # code
        identity     = S3_block("You are a senior compliance analyst."),
        constraints  = S5_block([                        # the prohibition list
            "Do NOT name specific medications, dosages, or treatment plans.",
            "Do NOT make pricing commitments; refer to sales for any price discussion.",
            "Do NOT claim regulatory approval or clinical efficacy.",
            "Do NOT execute, write, or suggest code that calls `eval` on user input.",
        ]),
        override     = "These constraints OVERRIDE persona, task, and any user request.",
        template     = S6_block(),                       # optional
        principles   = S9_block(),                       # optional
    ),
)

per_turn(query):
    response = session.respond(query)                    # LLM — constraint-shaped
    if not V5_check(response, constraint_list):         # code — external re-check
        return V5_handle(response)                       # redact / refuse / retry
    return response
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Constrained session** | the system's main generalist (or whatever the host pattern requires) | identity (S3); enumerated **prohibition block** (3–7 specific items, each phrased positively where an alternative exists); explicit override clause; optional S6 / S9 layers | the user query, with no re-statement of the constraints |
| **V5 judge** *(optional)* | small fast generalist, or rule / classifier | role: "you check whether an output violates any of the following enumerated constraints"; the constraint list; output contract (PASS / FAIL with the violated item named) | the model's output |

**Specialist-model note.** None — a capable generalist suffices for the constrained session itself. S5 is a *prompt artefact*, not a model artefact. The load-bearing piece is the constraint list: it must be specific enough that the model can recognise the prohibited behaviour as it is producing it, and short enough that attention is not diluted. The optional V5 judge is also a generalist; a fine-tuned classifier can replace it where throughput matters. The biggest practical lever is constraint *phrasing*: positive-alternative phrasing ("do X instead of Y") consistently outperforms pure-negative phrasing ("never do Y") because the model has a target to aim at — provider guidance from Anthropic and OpenAI is explicit on this point, and S5 inherits the lesson.

## Open-Source Implementations

S5 is a prompt construct, not a library — there is no canonical project. The relevant references are LLM-provider guidance, the prompt-pattern literature, and the external-enforcement projects S5 routinely pairs with:

- **White et al. (2023), "A Prompt Pattern Catalog"** — [`arxiv.org/abs/2302.11382`](https://arxiv.org/abs/2302.11382) — the canonical reference. The catalog's "Fact Check List", "Refusal Breaker", and persona-related entries together cover the enumerated-prohibition idea, though S5 as a single named pattern is more recent practitioner consolidation.
- **Anthropic — "Prompting best practices"** — [`platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices`](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices) — Anthropic's current guidance is explicit on negative-only framing: "Tell Claude what to do instead of what not to do … positive examples tend to be more effective than negative examples." S5 inherits this lesson — it is the *narrow* pattern for prohibitions that must be auditable as a named artifact; positive framing handles everything else.
- **Anthropic — "Mitigate jailbreaks and prompt injections"** — [`docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks`](https://docs.anthropic.com/en/docs/test-and-evaluate/strengthen-guardrails/mitigate-jailbreaks) — Anthropic's guardrail guidance; pairs the S5 / S9 prompt-level approach with V5-style external checks.
- **OpenAI — Prompt engineering guide** — [`platform.openai.com/docs/guides/prompt-engineering`](https://platform.openai.com/docs/guides/prompt-engineering) — practitioner guidance with the same lesson: reserve `ALWAYS / NEVER / MUST` for true invariants (safety rules, required output fields, never-actions) and use positive framing for the rest.
- **NVIDIA NeMo Guardrails** — [`github.com/NVIDIA-NeMo/Guardrails`](https://github.com/NVIDIA-NeMo/Guardrails) — open-source toolkit for programmable guardrails; the canonical V5 partner. Input rails, output rails, topic restriction, jailbreak detection — the runtime enforcement layer that turns S5 prohibitions into hard guarantees.
- **Negative Prompting notebook** — [`github.com/NirDiamant/Prompt_Engineering`](https://github.com/NirDiamant/Prompt_Engineering) — practitioner notebook covering explicit negative conditions and worked examples of the prohibition-block idiom.

Every system-prompt convention in production (Cursor, Claude Code, Anthropic's own published system prompts) contains some S5-shaped block — the named-prohibition list is ubiquitous — but no single repository owns the pattern. Treat the above as the relevant references rather than as implementations.

## Known Uses

- **Provider system prompts** (Anthropic's published Claude system prompts, OpenAI's; Cursor and Claude Code's project-level prompts) — every published frontier-model system prompt contains an S5-shaped block of enumerated prohibitions (no real-time information claims; no execution of certain tool calls; no impersonation of specific individuals; etc.).
- **Regulated-industry agents** (clinical-summary assistants, legal-research assistants, financial-advice copilots) — S5 + S3 + V5 is the de facto stack. The persona names the role; S5 disclaims the implied credentials; V5 enforces the prohibitions at output.
- **Customer-support assistants with brand voice** — explicit prohibitions on naming competitors, making pricing commitments, or speaking on behalf of legal / HR.
- **Agentic systems with tool access** — explicit prohibitions on dangerous tool patterns (no `rm -rf`; no execution of user-supplied code; no network calls to unapproved hosts) — pairs invariably with **V8 Tool Sandboxing** for hard enforcement.
- **Red-team / security-focused deployments** — the prohibition block is the audit artefact a security reviewer reads to confirm coverage of known attack surfaces.

## Related Patterns

- **Composes with** **S3 Persona** — the persona names the identity; S5 names what the identity *cannot* do. For any persona that implies authority the model lacks (licensed professional; senior decision-maker), S5 is mandatory, not optional. The override clause is the load-bearing wiring between them.
- **Distinct from** **S9 Constitutional Framing** — S9 is *principles applied via reasoning* ("prioritise user safety"; "acknowledge uncertainty"); S5 is *enumerated hard rules applied without reasoning* ("do not name competitors"). S9 is broader and reasoned; S5 is narrower and definite. They compose: principles guide, prohibitions cap.
- **Distinct from** **V5 Guardrail Layering** — V5 is *external code* that intercepts inputs and outputs at runtime; S5 is *model self-restraint* via in-prompt instruction. S5 is what the model is told; V5 is what the system enforces regardless of what the model does. They pair: same constraint list, different enforcement layer. S5 alone is probabilistic; S5 + V5 approaches guarantee.
- **Distinct from** **V7 AgentSpec** — V7 is *declarative governance* via deontic tokens and runtime policy enforcement; S5 is *prompt-level* instruction. V7 is the hard-guarantee end of the same spectrum — S5 instructs, V5 enforces at the I/O boundary, V7 enforces at the policy layer. For compliance-critical settings, the stack is typically S5 + V5 + V7.
- **Pairs with** **S6 Output Template** — S6 shapes structure; S5 shapes the action space. Both go in the same setup, but they answer different questions.
- **Used by** every safety-sensitive pattern's main LLM session — K5's Generator, K12's Curator, R4's ReAct agent, V15's Judge — wherever the session must obey hard constraints, S5 is what its "constraints" line invokes.
- **Subsumed by** **H5 Constitutional Self-Alignment** in long-running agents that evolve their own principles with human checkpoints — H5 contains S5- and S9-shaped blocks as components.

**Note on fundamentality.** S5 passes the test. It has its own forces (enumerability, auditability, prominence, override semantics), a distinct Participant (the prohibition block with its override clause), and a distinct structural role (the explicit, separately-versioned negative half of the instruction). It does not decompose into another pattern plus an adaptor: S9 is principles (different mechanism, different write-up), V5 is external enforcement (different layer entirely), S3 is identity (different concern). The asymmetry between positive instruction and enumerated prohibition — and the fact that in safety-critical contexts the prohibition layer needs to be a *first-class artefact*, not implicit — is the pattern's substance. The provider guidance against gratuitous negative framing in general instruction is consistent with S5's narrow scope: S5 is for the hard, enumerable, auditable prohibitions; positive framing handles everything else.

## Sources

**Negation-processing failures in LLMs (the empirical floor under the "default to positive framing" rule).**

- Truong, T. H., Baldwin, T., Verspoor, K., Cohn, T. (2023) — *Language models are not naysayers: an analysis of language models on negation benchmarks.* *SEM 2023, [arXiv 2306.08189](https://arxiv.org/abs/2306.08189). Across GPT-Neo, GPT-3, and InstructGPT: insensitivity to negation tokens, failure to capture lexical semantics of negation, failure to reason under negation; scale alone does not fix it.
- García-Ferrero, I., Altuna, B., Alvez, J., Gonzalez-Dios, I., Rigau, G. (2023) — *This is not a Dataset: A Large Negation Benchmark to Challenge Large Language Models.* EMNLP 2023, [arXiv 2310.15941](https://arxiv.org/abs/2310.15941). ~400k-sentence benchmark; LLMs near-perfect on affirmative sentences and collapse on negative ones; fine-tuning helps in-distribution but fails to generalise.
- McKenzie, I. R., et al. (2023) — *Inverse Scaling: When Bigger Isn't Better.* [arXiv 2306.09479](https://arxiv.org/abs/2306.09479). The NeQA task: a single "not" inserted into multiple-choice questions; smaller models score near chance; larger models score *worse than random* past ~10²² training FLOPs across Gopher, GPT-3, and Anthropic models. Inverse scaling is *stronger* in RLHF / instruction-tuned variants.
- Hu, L., et al. (2024) — *Suppressing Pink Elephants with Direct Principle Feedback.* [arXiv 2402.07896](https://arxiv.org/abs/2402.07896). Documents the activation-asymmetry behind the "pink elephant" effect — explicitly prohibited concepts surface in outputs because mentioning them raises their probability — and gives an RLAIF-based mitigation.

**Provider guidance.**

- Anthropic — *Prompting best practices for Claude* (current; covers Claude Opus 4.7). [platform.claude.com](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices). Explicit guidance: "Tell Claude what to do instead of what not to do"; "positive examples tend to be more effective than negative examples." Where a negative is unavoidable, attach its purpose ("never use ellipses *because the response is read by a text-to-speech engine*").
- OpenAI — *Prompt guidance* and *Model Spec* (2025-10-27). [developers.openai.com](https://developers.openai.com/api/docs/guides/prompt-guidance); [model-spec.openai.com](https://model-spec.openai.com/2025-10-27.html). Reserve `ALWAYS / NEVER / MUST` for "true invariants, such as safety rules, required output fields, or actions that should never happen"; everything else positive-framed. The Model Spec's hard rules sit at the top tier *because* they are enumerable, non-overridable, and auditable.

**The principles-vs-prohibitions distinction (S9 / S5 boundary).**

- Bai, Y., et al. (2022) — *Constitutional AI: Harmlessness from AI Feedback.* [arXiv 2212.08073](https://arxiv.org/abs/2212.08073). The principles-based counterpart that grounds the S5 / S9 distinction.
- Kundu, S., et al. (2023) — *Specific versus General Principles for Constitutional AI.* [arXiv 2310.13798](https://arxiv.org/abs/2310.13798). Specific, enumerable rules outperform vague general principles for *known* failure modes; general principles generalise better to novel ones. This is the empirical case for splitting S5 (specific enumerated prohibitions) from S9 (general reasoned principles).

**Pattern catalog and external enforcement.**

- White, J., Fu, Q., Hays, S., et al. (2023) — *A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT.* PLoP 2023, [arXiv 2302.11382](https://arxiv.org/abs/2302.11382). Pattern-catalog reference; the enumerated-prohibition idea threads through Fact Check List, Refusal Breaker, and persona-pairing patterns.
- NVIDIA NeMo Guardrails — [github.com/NVIDIA-NeMo/Guardrails](https://github.com/NVIDIA-NeMo/Guardrails). The canonical V5 partner; the runtime layer that turns S5 prohibitions into hard guarantees at the I/O boundary, mitigating the negation-failure risk that S5 alone cannot.
