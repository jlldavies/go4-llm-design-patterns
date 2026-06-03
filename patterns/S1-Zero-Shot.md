# S1 — Zero-Shot

> Ask the model to do the task with nothing but the instruction itself — no examples, no decomposition, no template, no role, no constitution — and rely entirely on its pre-trained instruction-following.

**Also Known As:** Direct Instruction, Vanilla Prompting, Instruction-Only Prompting, Naked Prompt.

**Classification:** Category I — Signal · the *baseline* pattern of the category — every other Signal pattern is defined as "S1 plus a specific addition" (examples, role, constraints, steps, template, samples, principles, density passes).

---

## Intent

State the task and submit it. Nothing else. S1 is the floor against which every other Signal pattern is the upgrade — it names the *do-nothing-extra* default so that adding anything else becomes a conscious decision rather than an unexamined habit.

## Motivation

Every prompt-engineering move costs something — tokens, latency, maintenance, brittleness — and earns its keep only against a clearly understood baseline. Without a named baseline, teams pile on persona, examples, constraints, templates, and chain-of-thought scaffolding from the first prompt onward, never measuring whether any single addition actually helped. Cost and complexity drift upward; the prompt becomes a museum of habits no one can defend.

S1 fixes the floor. It says: *the task description alone, sent to a capable instruction-tuned model, is the baseline you must beat to justify anything more.* Post-instruction-tuning models (Wei et al., 2022) handle a remarkable range of well-defined tasks at this floor. Instruction-tuned models follow zero-shot instructions reliably for in-distribution tasks because the instruction tokens shift the learned Q-K bilinear form (attention metric) toward completions the model has densely covered in training (mechanism 1). The failure mode — inconsistent format on out-of-distribution tasks — occurs because the Q-K inner products do not route confidently to a single completion cluster when the task is novel. Brown et al. (2020) introduced the term "zero-shot" precisely to distinguish *no demonstrations* from one-shot and few-shot; the result was that GPT-3 already solved many tasks at zero-shot, and that result has only strengthened with every subsequent model generation. For well-formed tasks the floor is often high enough that no upgrade is warranted.

The unique contribution of naming S1 is therefore not a *technique* — there is no clever trick — but a *discipline*. Every other Signal pattern decomposes into "S1 + a specific addition": **S2** adds k example pairs; **S3** adds an identity; **S4** adds numbered steps; **S5** adds prohibitions; **S6** adds a template; **S8** adds a meta-level prompt-search loop; **S9** adds a constitution. Two patterns once listed as Signal — **R17 Self-Consistency Voting** (now in Reasoning, since voting over N samples is a thinking-shape choice, not a prompt-shaping move) and **K6's Chain-of-Density variant** (folded into K6 as a summarisation technique) — were relocated because they were not actually prompt-shaping. The category only makes sense if its baseline is named.

## Applicability

Use Zero-Shot when:

- the task is well-defined and unambiguous to a competent reader without examples;
- the output format is common enough to sit inside the model's training distribution (summary, classification, translation, plain answer);
- iteration speed or unit cost dominates the design — every added token is paid on every call;
- you do not yet have measurements that justify any upgrade.

Do not use it when:

- the output format is non-standard and you cannot describe it cleanly in words $\to$ upgrade to **S2 Few-Shot**.
- domain expertise framing materially helps tone or knowledge activation $\to$ add **S3 Persona**.
- the task has a clear multi-step process the model keeps skipping $\to$ add **S4 Instruction Decomposition**.
- known failure modes need explicit prohibition $\to$ add **S5 Constraint Framing**.
- downstream code parses the output $\to$ add **S6 Output Template** (or a structured-output API).
- reasoning reliability is the constraint and a feedback signal exists $\to$ wrap with **R17 Self-Consistency Voting** or **R7 Reflexion**.
- regulated or safety-critical operation $\to$ add **S9 Constitutional Framing**.

## Decision Criteria

S1 is right when a capable instruction-tuned model can do the task from the instruction alone, and nothing in the failure profile justifies the cost of an upgrade yet.

**1. Task-novelty score.** Is the task plausibly inside the model's pre-training distribution? Summarisation, simple classification, translation, factual Q&A, common formats (markdown, JSON, plain prose) — yes, S1. Bespoke domain output, esoteric format, proprietary tone — no, escalate. *Threshold:* if a competent human reader could do the task from the instruction without examples, the model probably can too.

**2. Format-consistency rate.** Run the prompt N=20 times. What fraction returns the expected shape? If **$\geq$ 95%**, S1 holds. **90–95%** is borderline — measure the cost of failures before upgrading. **< 90%** $\to$ escalate to **S6 Output Template** (or a structured-output API), or **S2 Few-Shot** if the failure is stylistic rather than structural.

**3. Quality-against-upgrade delta.** Compare S1 quality against S2 (few-shot) on the same task. If the lift from 3–5 examples is **< 5 percentage points** on whatever quality metric you care about, S1 wins on cost. If it's **> 10 points**, S2 wins. The middle band is a judgement call about token budget.

**4. Cost / latency budget.** Tokens added by an upgrade are paid on *every* call. At scale, a 200-token persona $\times$ 1M calls/month is not free. Mechanically, every token added to the prompt participates in O(n²) pairwise attention computations and adds ~300KB to the KV cache (mechanism 2, 3). At scale a 200-token addition is not 200 tokens of linear cost — it expands the attention matrix over the full prompt length. S1 minimises this. If unit economics are tight, S1 is the right floor and upgrades must clear a measurable bar.

**5. Reliability budget.** Is this safety-critical, regulated, or load-bearing for downstream automation? If yes, S1 is almost never the final answer — pair with **S5 Constraint Framing**, **S9 Constitutional Framing**, or **V9 Bounded Execution** as needed. S1 is for the long tail of well-defined, low-stakes calls.

**Quick test — S1 is the right pattern when:**

- the task sits inside the model's training distribution, *and*
- format-consistency on a 20-run probe is $\geq$ 95%, *and*
- the lift from few-shot is small enough that the token cost does not pay back, *and*
- the task is not safety-critical.

If format slips, choose **S6 Output Template** (or a structured-output API). If style or tone slips, choose **S2 Few-Shot**. If reasoning quality is the bottleneck, choose **R4 ReAct** or **R17 Self-Consistency Voting**. If safety matters, layer **S5 Constraint Framing** or **S9 Constitutional Framing** on top. S1 alone is the default; upgrades are deliberate.

## Structure

```
  Task description
        │
        ▼
  ┌─────────────────┐
  │   LLM (single   │      no examples
  │   configured    │      no decomposition
  │    session)     │      no template
  └────────┬────────┘      no role required
           │
           ▼
        Output
```

A single configured session. One call. Nothing on either side of the model except the instruction in and the output out.

## Participants

Three participants — the minimum any prompted system can have. The discipline of S1 is that the list does *not* grow.

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Task Instruction** | the single natural-language statement of what to do | task spec $\to$ instruction string | smuggle in examples, role, template, or constraints — each of those is a different Signal pattern and must be named as the upgrade it is. |
| **Model** | the un-augmented instruction-following capability | instruction $\to$ completion | be silently swapped between calls — S1's reliability is bound to the specific model; a downgrade or model swap invalidates the baseline measurement. |
| **Caller** | the surrounding code that submits the call and handles the response | instruction $\to$ completion $\to$ downstream | retry-and-massage the output until it parses — that masks an S1 failure that should be a deliberate upgrade to S6 or S2. |

The whole point of the page is the *Must not* column. S1's failure mode is not technical; it is the slow accretion of unexamined additions until the prompt is no longer S1 and no one remembers when it changed.

## Collaborations

The Caller composes the Task Instruction — one sentence to a short paragraph naming what the model should produce. It submits the instruction to the Model as a single call. The Model returns a completion. The Caller passes the completion to whatever consumes it. There is no second call, no evaluation step, no retry on bad parse — those moves all belong to other patterns (R17 voting, V15 judging, S6 templating, S4 decomposing). The simplicity of the collaboration *is* the pattern.

## Consequences

**Benefits**

- Lowest token cost of any prompting pattern — only the instruction and the input ride in context.
- Lowest latency — one call, no scaffolding, no aggregation.
- Easiest to maintain — fewer moving parts; no example curation, no template drift, no constitution to keep current.
- Highest portability across models — no model-specific tricks baked in; a model swap is a single regression test.
- The honest baseline — every upgrade can be measured against this floor.

**Costs**

- No format guarantee — output structure depends entirely on the model's defaults; token generation is stochastic, so the same prompt produces different shapes across runs (mechanism 7).
- No style guarantee — tone and register drift with model and decoding parameters.
- No reasoning scaffold — complex multi-step tasks degrade because the model produces them in one pass.
- No safety scaffold — nothing constrains adversarial or off-policy completions.

**Risks and failure modes**

- *Silent format drift* — outputs parse most of the time and break occasionally; the failure surfaces in downstream code rather than at the prompt.
- *Capability degradation under model swap* — what worked on a strong model may fail on a smaller or quantised one; S1 has no scaffolding to soak up the difference.
- *Accretion creep* — the prompt slowly grows persona, examples, constraints, templates, until it is no longer S1 but is still treated as the baseline. The team loses the actual baseline.
- *Misclassification as S1* — any prompt with examples is S2, with role is S3, with steps is S4, with template is S6. Calling those "zero-shot" because there is "only one prompt" is the most common audit failure.

## Implementation Notes

- **Keep it one sentence to a short paragraph.** If the instruction needs more than that, the task probably needs decomposition (S4) or a template (S6).
- **Measure first, upgrade second.** Run the format-consistency probe (criterion 2 above) before adding anything. Most failures are diagnosable from 20 runs.
- **Set the model and decoding once, document them.** Temperature, top-p, and model choice are part of the baseline — changing them silently destroys the comparison.
- **Use structured-output APIs in preference to S6 when format is the issue.** If JSON mode or schema-constrained decoding is available, that beats both S1 and S6 free-text templating.
- **Do not chain S1 with itself.** Multi-call workflows belong to the Orchestration category (O6 Orchestrator-Workers and friends), not to S1.
- **Treat S1 as the start of the upgrade ladder, not the destination.** When you find yourself adding "just one example" or "just a role," you have left S1 — name the new pattern and own the upgrade.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** S1 is, by definition, the pattern with no composition — one configured LLM session, called once. It is the inner step many other patterns wrap: **R17** wraps it with N samples and a vote; **R7 Reflexion** wraps it with a retry-with-memory loop; every **O-category** orchestration pattern uses one or more S1 calls as worker steps. S1 itself composes with nothing inside its own boundary.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Compose the instruction string from the task and input | `code` | — |
| 2 | Submit instruction to the configured Model session | `LLM` | Task session |
| 3 | Return the completion to the caller | `code` | — |

**Skeleton** — wiring only; the `# LLM` line is a configured session, not bare code:

```
zero_shot(task_description, input_data):
    prompt = format(task_description, input_data)   # code
    completion = Model(prompt)                       # LLM — single configured session
    return completion                                # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Task** | a capable instruction-tuned generalist (the system's default model) | nothing beyond the model defaults — that absence is what makes this S1 rather than S3 / S5 / S9. Document the model ID, temperature, and top-p. Any setup beyond defaults moves the pattern to S3 (persona) or S5 (constraints). | the instruction + the input |

**Specialist-model note.** None — a capable instruction-tuned generalist is the entire requirement. The pattern artifact that does the heavy lifting is the *instruction itself*: a clear, complete, unambiguous task statement. The model is generic; the discipline is in the writing of the task line.

## Open-Source Implementations

S1 is the degenerate case of prompting — there is no library to install and no canonical project, because the pattern *is* "call the model with the instruction." The relevant references are documentation, guides, and the original paper:

- **Anthropic — Prompt engineering overview** — [`docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview`](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview) — Claude prompting docs; zero-shot is the implicit baseline before "multishot prompting" and the rest.
- **OpenAI — Prompt engineering guide** — [`platform.openai.com/docs/guides/prompt-engineering`](https://platform.openai.com/docs/guides/prompt-engineering) — the OpenAI platform guide; zero-shot is the default mode before the techniques sections.
- **DAIR.AI Prompt Engineering Guide** — [`github.com/dair-ai/Prompt-Engineering-Guide`](https://github.com/dair-ai/Prompt-Engineering-Guide) — the community-maintained guide; the [zero-shot page](https://www.promptingguide.ai/techniques/zeroshot) is the canonical written explanation of the pattern.
- **NirDiamant — Prompt Engineering notebooks** — [`github.com/NirDiamant/Prompt_Engineering`](https://github.com/NirDiamant/Prompt_Engineering) — runnable notebooks; the `zero-shot-prompting.ipynb` is a minimal, working illustration.

These are documentation references, not implementations — exactly as expected for a baseline pattern.

## Known Uses

- **Every LLM application in production** uses S1 somewhere — it is the underlying call inside every wrapper. Most ChatGPT, Claude.ai, and Gemini user turns are zero-shot from the user's side.
- **Classification and summarisation pipelines** that escaped fine-tuning between 2022 and 2024 — many enterprise teams replaced labelled-data fine-tuning with S1 against a frontier model.
- **First drafts of any prompted feature** — the standard engineering practice is to ship S1, measure, and upgrade only when measurements demand it.
- **Eval baselines in benchmark reports** — model evaluations (MMLU, HumanEval, GPQA) report zero-shot scores as the default; few-shot scores are reported as upgrades against that baseline.

## Related Patterns

- **Baseline for** every other Signal pattern — S2, S3, S4, S5, S6, S8, S9 are each "S1 plus a specific addition" (examples, role, steps, prohibitions, template, meta-prompt loop, constitution). S7 and S10 used to belong here but have moved (to R17 and K6 respectively).
- **Wrapped by** R17 Self-Consistency Voting — R17 calls S1 N times and votes; the inner call is exactly S1.
- **Wrapped by** R7 Reflexion — R7 retries an S1 call with a memory of prior failures; the per-attempt call is S1.
- **Used by** every O-category orchestration pattern — O6 Orchestrator-Workers and the others compose multiple S1 calls; the worker step is typically S1.
- **Distinct from** S2 Few-Shot — the presence of even one demonstration moves the pattern to S2. Calling a one-shot prompt "zero-shot" is the most common misclassification.
- **Distinct from** S4 Instruction Decomposition — numbered steps inside one prompt are S4, not S1. The line is the explicit ordering: a paragraph of requirements is S1; a numbered list of steps the model must follow is S4.
- **Note on fundamentality** — S1 is the *degenerate case* of prompting and earns its number as the baseline against which every other Signal pattern is measured, the same role **K1 Vanilla RAG** plays for Knowledge. Removing it would leave the rest of the category without a defined floor.

## Sources

- Brown et al. (2020) — "Language Models are Few-Shot Learners" (GPT-3 paper, arXiv 2005.14165). Introduced the zero-shot / one-shot / few-shot distinction.
- Wei et al. (2022) — "Finetuned Language Models Are Zero-Shot Learners" (FLAN, arXiv 2109.01652). Established instruction tuning as the mechanism that makes zero-shot work.
- Anthropic — Prompt engineering documentation (Claude API docs).
- OpenAI — Prompt engineering guide (platform docs).
- DAIR.AI — Prompt Engineering Guide, zero-shot section.
- White et al. (2023) — "A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT" — establishes the baseline / refinement framing the GO4 Signal category formalises.
