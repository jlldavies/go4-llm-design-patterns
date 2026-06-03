# Category I — Signal Patterns

A **Signal pattern** is a design pattern for *shaping what you say* to a language model — the instruction, the demonstrations, the role, the constraints, the output skeleton, the principles — so that the response distribution is shifted toward the task you actually want, before any retrieval, reasoning, or orchestration is layered on top.

## Usage

Every interaction with a language model is, at minimum, a Signal-layer choice. The model is a conditional distribution over text; the prompt is the condition. Even "just type the question" is a Signal pattern (S1 Zero-Shot) — a *default* one, which is the point of naming it. Signal patterns make the prompt itself a deliberate design surface rather than an unexamined habit.

A language model arrives pre-trained with broad capability and no specific calibration to your task. The cheapest, lowest-latency, lowest-engineering-overhead way to calibrate it is at the prompt: showing it examples, telling it who to be, telling it what not to do, giving it the output skeleton, embedding the principles it should apply. None of these touch the weights; all of them shift the response distribution at inference time. The weights are fixed across API calls (mechanism 10) — what changes is which K-vectors the Q vectors attend to (mechanism 1), shaped by the prompt content occupying positions in the KV cache (mechanism 3). Signal patterns are the primary lever because they are the only layer between the fixed weights and the per-call attention computation. Apply a Signal pattern whenever:

- a task is well-enough defined that the lever you need is framing, not retrieval or reasoning;
- output format, tone, or value-alignment is inconsistent across runs;
- you are about to add a Knowledge, Reasoning, or Orchestration pattern and want to rule out "fix it with a better prompt" first;
- a downstream system depends on a stable shape of input or output that the model must produce.

## Forces

Every Signal pattern resolves the same three forces in tension. A pattern is the right choice for a situation when it balances them in the way that situation demands.

1. **The model has priors, not knowledge of your task.** It has seen billions of tokens of generic text but nothing about your domain, your tone, or your forbidden behaviours. Left alone it answers from the mode of its training distribution, which is almost never the mode you want.

2. **Tokens in the prompt are not free.** Every example, every line of persona, every constraint, every template field costs context window, latency, and money on every call. The lever exists only because the cost is small relative to retraining — not because it is zero. Mechanically, this cost is O(n²): the attention matrix QK^T is computed over every pair of tokens in the prompt (mechanism 2), so adding tokens to a 1000-token prompt costs ten times more per token than adding the same tokens to a 100-token prompt. "Not free" understates the compounding — the correct framing is that prompt cost is superlinear in length.

3. **Prompt-layer control is probabilistic, not enforced.** A Signal pattern shifts a distribution; it does not guarantee an outcome. A persona can be broken, a constraint can be violated, a template can be ignored under adversarial or unusual input. Anything that must be *guaranteed* belongs at the Reliability layer, not the Signal layer.

A Signal pattern is, in each case, a disciplined answer to one question: how to spend the smallest number of prompt tokens to move the response distribution the largest distance toward the task you actually want.

## Structure

All Signal patterns share one skeleton. They interpose a **framing stage** between the raw user task and the model, populating the system and user messages with material chosen to shift the response distribution:

```
  Raw task ────▶ Framing ────▶ Prompt ────▶ LLM ────▶ Response
 (what the      (instruction,    (system +
  user wants)    examples,        user
                 role,            messages,
                 constraints,     fully
                 template,        composed)
                 principles)
```

Patterns differ in *what the framing stage adds* — nothing (S1), demonstrations (S2), an identity (S3), a step list (S4), a prohibition list (S5), an output skeleton (S6), self-generated prompts (S8), a constitution (S9) — and in *whether the addition is loaded once at session setup or assembled per call*. The five bands below group the patterns by the addition they make: the baseline (I-A), demonstrations (I-B), setup-layer framing of identity / constraints / format / principles (I-C), instruction structure inside a single call (I-D), and meta-level prompt generation (I-E). They are largely orthogonal — a production prompt usually combines a setup-band pattern (S3 + S5 + S6 + S9) with an instruction-band pattern (S4) and possibly a demonstration-band pattern (S2), all sitting on top of the S1 baseline.

The loaded-once vs. per-call distinction is also a caching boundary (mechanism 5). Setup-layer patterns (S3, S5, S6, S9) placed in a stable system prompt define the cacheable prefix unit: if the prefix is identical across calls and exceeds the provider's minimum cacheable length (1024 tokens for Anthropic, TTL ~5 min, ~10% cost on cache hits), every subsequent call within the TTL reads the KV state from cache rather than recomputing it. Assembling S3 + S5 + S6 + S9 into a single stable prefix is therefore not just good composition — it is cache engineering. A dynamic S2 (retrieval-augmented few-shot) inserted into the prefix breaks this: it changes the prefix per call and forfeits the cache hit for all the setup-layer material that precedes it.

## Examples

**I-A — Baseline.** The do-nothing default against which every other pattern is defined as an upgrade.
- **S1 Zero-Shot** — instruction only; no examples, no role, no template, no constraints.

**I-B — Demonstration.** Teaching the task by showing rather than telling.
- **S2 Few-Shot** — put `k` worked input→output examples into the prompt so the model infers the task from demonstrations.

**I-C — Setup framing.** Loaded once at session setup; configures *who, what-not, how, and why* for every turn that follows.
- **S3 Persona** — assign the model an explicit identity (role, profession, character) framing knowledge and tone.
- **S5 Constraint Framing** — enumerate the specific things the model must *not* do as an explicit prohibition list.
- **S6 Output Template** — provide the skeleton of the expected output (fields, labels, structure) for the model to fill.
- **S9 Constitutional Framing** — embed explicit principles and have the model self-critique-and-revise against them before returning.

**I-D — Instruction structure.** Shaping the task description itself inside a single prompt.
- **S4 Instruction Decomposition** — break the complex instruction into explicit numbered sequential steps the model executes in order.

**I-E — Meta.** Producing Signal-layer artefacts with the model itself rather than by hand.
- **S8 Meta-Prompt** — use the LLM, driven by an evaluation signal, to generate or refine the prompts other Signal patterns assume a human wrote.

## See also

- **Category II — Knowledge patterns** — Signal shapes *what you say*; Knowledge shapes *what the model sees* (retrieved or persisted information). A typical production prompt is a Signal frame around a Knowledge payload.
- **Category III — Reasoning patterns** — govern *what the model does* with the framed prompt; R1 Zero-Shot CoT and R2 Few-Shot CoT are the reasoning-band counterparts of S1 and S2, adding a "think step by step" instruction to the Signal-layer base.
- **Category IV — Orchestration patterns** — S4 Instruction Decomposition is the single-call sibling of **O2 Prompt Chaining** (multi-call ordered execution) and **R3 Plan-and-Solve** (plan-then-execute as two calls); choose by step length and inspection needs.
- **Category V — Reliability patterns** — S5 Constraint Framing is the in-prompt counterpart of **V5 Guardrail Layering** (external enforcement); S9 Constitutional Framing is the soft, in-prompt counterpart of **V7 AgentSpec** (hard, external policy enforcement). Anything that must be guaranteed belongs at the Reliability layer.
- **Category VII — Humanizer patterns** — **H1 Identity Persistence** subsumes S3 Persona in any system that has cross-session identity.

*Former S7 Self-Consistency Voting was reclassified as **R17** (Reasoning, band III-C) — its mechanism is sampling and aggregating reasoning paths, not shaping the prompt. Former S10 Chain of Density was folded into **K6 Context Compression** as a named Variant — it is a summarisation technique, not a Signal-layer choice. S7 and S10 are intentional gaps in the Signal numbering.*

---

## Quick Reference

| # | Pattern | Also Known As | Intent | When to Use |
|---|---|---|---|---|
| S1 | **Zero-Shot** | Direct Instruction | Task with no examples; rely on model priors | Simple, well-defined tasks where model knowledge is sufficient |
| S2 | **Few-Shot** | In-Context Learning | Provide examples to demonstrate desired format or behaviour | Format control, style matching, novel task types |
| S3 | **Persona** | Role Prompting | Assign the model an identity to frame knowledge and tone | Expert framing, domain-specific tasks, tone alignment |
| S4 | **Instruction Decomposition** | Step Prompting | Break complex instruction into numbered sequential steps | Multi-step tasks with clear ordering |
| S5 | **Constraint Framing** | Negative Prompting | Define what model must NOT do as prominently as what it should | Safety-sensitive, compliance, avoiding known failure modes |
| S6 | **Output Template** | Template Filling | Provide skeleton of expected output for model to complete | Structured data extraction, consistent formatting |
| S8 | **Meta-Prompt** | Auto-Prompting | Model generates or refines its own prompt | Self-optimising workflows; experimental; cost intensive |
| S9 | **Constitutional Framing** | Constitutional AI | Embed principles the model applies to self-critique | Alignment enforcement, safety-critical contexts |

*S7 (Self-Consistency Voting) relocated to R17 (Reasoning). S10 (Chain of Density) folded into K6 (Context Compression). Both are intentional gaps.*

---

## S1 — Zero-Shot

Ask the model to do the task with nothing but the instruction itself — no examples, no decomposition, no template, no role, no constitution — and rely entirely on its pre-trained instruction-following. The baseline against which every other Signal pattern is defined as an upgrade.

**Full entry:** [`S1-Zero-Shot.md`](S1-Zero-Shot.md)

---

## S2 — Few-Shot

Put `k` worked input→output examples into the prompt so the model infers the task — its format, style, and decision boundary — from the demonstrations rather than from instruction alone. Dynamic / Retrieval-Augmented Few-Shot is a variant.

**Full entry:** [`S2-Few-Shot.md`](S2-Few-Shot.md)

---

## S3 — Persona

Assign the model an explicit identity — a role, profession, or character — at session setup, so its knowledge, tone, and decision style are framed by that identity for every turn that follows.

**Full entry:** [`S3-Persona.md`](S3-Persona.md) — *subsumed by **H1 Identity Persistence** in any system that has cross-session identity.*

---

## S4 — Instruction Decomposition

Break a complex instruction into explicit, numbered, sequential steps inside a single prompt, so the model executes them in order rather than collapsing a dense paragraph of requirements into a single best-effort pass. The cheapest rung of the ordered-execution ladder that climbs to **O2 Prompt Chaining** and **R3 Plan-and-Solve**.

**Full entry:** [`S4-Instruction-Decomposition.md`](S4-Instruction-Decomposition.md)

---

## S5 — Constraint Framing

Enumerate, at session setup, the specific things the model must *not* do — as an explicit, auditable list that sits alongside the task description with equal or greater prominence than the positive instructions. The in-prompt prohibition layer; **V5 Guardrail Layering** is its external-enforcement counterpart.

**Full entry:** [`S5-Constraint-Framing.md`](S5-Constraint-Framing.md)

---

## S6 — Output Template

Provide the skeleton of the expected output — fields, labels, and structure — for the model to complete, so format generation is replaced by format *filling*. JSON-mode / schema-constrained decoding, free-text template, and few-shot template are variants.

**Full entry:** [`S6-Output-Template.md`](S6-Output-Template.md)

---

## S8 — Meta-Prompt

Use the LLM itself to generate or refine the prompts it will run on, driven by an external evaluation signal, so prompt engineering becomes a measured optimisation loop rather than human guesswork. Requires an evaluator (typically **V15 LLM-as-Judge** or **R17 Self-Consistency Voting**) to provide the score.

**Full entry:** [`S8-Meta-Prompt.md`](S8-Meta-Prompt.md)

---

## S9 — Constitutional Framing

Embed an explicit set of principles — a *constitution* — in the session setup, and have the model critique and revise its own output against those principles before returning it, so values and judgement live as inspectable text rather than as an implicit prior baked into weights. The inference-time form of Anthropic's Constitutional AI; the soft, in-prompt counterpart to **V7 AgentSpec** (hard, external enforcement).

**Full entry:** [`S9-Constitutional-Framing.md`](S9-Constitutional-Framing.md)

---

*Former S7 Self-Consistency Voting has moved to Category III — Reasoning as **R17**. Former S10 Chain of Density has been folded into **K6 Context Compression** as a named Variant. See `TAXONOMY-DRAFT.md` and the section-review notes for the reclassification rationale.*
