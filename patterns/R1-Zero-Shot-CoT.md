# R1 — Zero-Shot CoT

> Append a short reasoning-elicitation trigger (canonically *"Let's think step by step"*) to a zero-shot prompt and let the model write its reasoning out before the final answer — no examples, no decomposition, no scaffold.

**Also Known As:** "Let's think step by step", Zero-Shot Chain-of-Thought, Zero-Shot-CoT, Trigger-Phrase CoT. (Two-stage and instruction-style trigger variants noted in Variants.)

**Classification:** Category III — Reasoning · Band III-A Single-pass reasoning · the *trigger-only* refinement of **S1 Zero-Shot** — the cheapest reasoning pattern in the category and the natural first upgrade from a bare instruction.

---

## Intent

Elicit explicit intermediate reasoning from a capable instruction-tuned model by adding a single short trigger phrase to an otherwise zero-shot prompt, so the model writes its working out before committing to an answer instead of jumping straight to a guess.

## Motivation

A bare zero-shot prompt (**S1**) asks the model to produce the answer directly. For arithmetic, multi-hop reasoning, and symbolic tasks, that direct-answer mode is unreliable: the model commits to an answer token before any deliberation has happened, and whatever reasoning the rest of the completion contains is post-hoc rationalisation of a guess that has already been made (mechanism 7). The failure is not that the model *cannot* reason — it is that the prompt has not invited it to.

Kojima et al. (2022) found that a single appended sentence — *"Let's think step by step"* — is enough to flip this. With no examples, no decomposition, no fine-tune, the trigger biases the model toward emitting a reasoning trace *first* and the answer *last*. The reported lifts are dramatic: MultiArith accuracy went from 17.7% to 78.7%, GSM8K from 10.4% to 40.7%, on the same model with the same task. The mechanism is not magic — instruction-tuned models have learned that prompts of the form "think step by step" are followed by step-by-step solutions in the training distribution. The trigger simply addresses the right region of that distribution.

**Why emitting reasoning tokens helps (mechanism 7 + mechanism 1).** Token generation is autoregressive stochastic sampling: each emitted token conditions the distribution for all subsequent tokens. Emitting reasoning tokens before the answer token shifts the model's KV cache prefix toward a region of learned Q-K space that is geometrically closer to the answer — the intermediate reasoning tokens activate attention patterns associated with the domain and approach, narrowing the probability mass on the final answer token. This is derivable: the reasoning tokens change which K-vectors the answer-position Q attends to, via the learned bilinear form $g_{\mu\nu} = W_Q W_K^T$ (mechanism 1). The answer is not revised by the reasoning — it is conditioned on it.

This is structurally distinct from its siblings in the band. **R2 Few-Shot CoT** (Wei et al., 2022) provides *worked examples* with reasoning traces — it teaches both *what* to reason about and *how* to format the reasoning. R1 supplies no examples; the model invents the format. **R3 Plan-and-Solve** separates a *planning call* from an *execution call*, producing an explicit plan first. R1 is one call with no plan artifact — the reasoning and answer come out together. **S1 Zero-Shot** has no reasoning scaffold at all. R1 sits exactly between S1 and R2: the zero-example refinement of S1 that buys most of R2's reasoning lift without paying R2's example tokens.

The unique contribution is the trigger as a *named upgrade* over S1 — a one-line change that, when measured, often moves accuracy enough on reasoning tasks to be the default first move before any heavier intervention.

## Variants

The variants differ in *how the trigger is phrased* and *whether reasoning and answer are produced in one call or two*:

- **One-stage trigger (Kojima et al., 2022).** Append *"Let's think step by step."* to the prompt; the model emits reasoning followed by the answer in a single completion. The original and most common form.
- **Two-stage Zero-Shot CoT (Kojima et al., 2022 §3.2).** First call generates the reasoning with the trigger; a second short call extracts the answer in a strict format (*"Therefore, the answer is …"*). Used when the answer must be parsed deterministically downstream and the one-stage output is too variable in format. Costs an extra short call; pays for itself when the extractor would otherwise be brittle.
- **Instruction-style triggers.** Variants of the trigger phrase — *"Take a deep breath and work on this problem step by step."* (Yang et al., 2023 / OPRO), *"Let's work this out in a step by step way to be sure we have the right answer."* (the APE-discovered phrase), *"Think carefully step by step."* Different phrasings yield small but measurable differences; the optimal phrasing is model-specific and worth a 20-sample probe.

All three share the structural move — *one zero-shot call with an appended reasoning-elicitation phrase* — differing only in trigger wording or whether answer extraction is split out as a second call.

## Applicability

Use Zero-Shot CoT when:

- the task involves arithmetic, multi-step inference, symbolic reasoning, or commonsense composition, and a bare S1 call returns the wrong answer or skips the reasoning;
- you have no curated examples to put in the prompt — or the cost of curating them is not yet justified;
- you want the cheapest possible reasoning lift over S1 (one extra sentence in the prompt, one call);
- the model is large and instruction-tuned enough to follow the trigger (small models often ignore it).

Do not use it when:

- the task is well-defined and S1 already returns correct answers with a stable format — the reasoning trace is then pure overhead $\to$ **S1 Zero-Shot**.
- the model is small or weakly instruction-tuned and does not follow the trigger reliably $\to$ use **R2 Few-Shot CoT** instead, where worked examples teach the format explicitly.
- the reasoning format itself matters (specific intermediate steps, a domain-standard layout, a citation pattern) and R1's free-form reasoning is too variable $\to$ **R2 Few-Shot CoT**.
- the task needs an *inspectable plan before execution* (regulated workflow, multi-tool orchestration, human review checkpoint) $\to$ **R3 Plan-and-Solve**.
- the task is open-ended and needs *exploration* or *adaptation* mid-run $\to$ **R4 ReAct**.
- the task is numerical or computational and the model hallucinates arithmetic even with CoT $\to$ **R14 Program of Thoughts** (offload computation to an executor).
- single-shot CoT is right but its output is noisy and you need a reliability lift $\to$ wrap with **R17 Self-Consistency Voting** (R1 $\times$ N + vote is the canonical composition).

## Decision Criteria

R1 is right when S1 underperforms on a reasoning task, the model is capable enough to follow a trigger, and you want the cheapest possible reasoning upgrade before paying for examples or multi-call patterns.

**1. Measure the S1 gap.** On a labelled set of ~50 reasoning items, run S1 and R1 head-to-head with identical model and decoding. If R1 lifts accuracy by **$\geq$ 5 percentage points**, R1 has earned its sentence. If the lift is **< 2 points**, S1 alone is fine. The middle band (2–5 points) is a judgement call about how much the failures cost downstream.

**2. Check that the model actually reasons.** Inspect 10 R1 completions. The trace should be substantive — multiple short steps, intermediate values, an explicit final answer. If the model emits *"Let's think step by step. The answer is 42."* (trigger acknowledged, no actual reasoning), the model is too small or too weakly tuned for R1. Escalate to **R2 Few-Shot CoT** where worked examples demonstrate the depth expected.

**3. Pick the trigger phrasing.** *"Let's think step by step."* is the default. Run a 20-sample probe with two or three candidate phrases (the OPRO and APE phrasings above) on a representative slice; the differences are usually small but model-specific. Lock the phrasing once chosen — switching mid-deployment invalidates the baseline.

**4. Decide one-stage vs two-stage.** If downstream code needs to parse the answer deterministically and one-stage R1 produces variable answer phrasings, use the **two-stage variant**: first call generates the reasoning; second short call extracts the answer in a strict format (S6 Output Template on the second call). The extra call is cheap and removes a class of parsing failures.

**5. Cost vs the next upgrade.** R1 adds *one sentence* to the prompt — effectively free. R2 adds *k worked examples* — typically 200–1000 tokens depending on task. R3 splits into *two calls*. R17 multiplies cost by *N* (mechanism 2 for the total token cost). Walk up the ladder only when measurement shows R1 is insufficient: most reasoning lifts that R2 achieves are partially captured by R1 alone, at a fraction of the prompt budget.

**Quick test — R1 is the right pattern when:**

- the task involves explicit reasoning (arithmetic, multi-hop, symbolic, commonsense composition), *and*
- S1 underperforms on a labelled probe by $\geq$ 5 points, *and*
- the model is capable enough that the trigger produces a substantive trace, *and*
- the reasoning format does not need to be controlled tightly enough to require examples.

If the model ignores the trigger or the trace is shallow, use **R2 Few-Shot CoT**. If the reasoning needs to be an inspectable artifact separate from execution, use **R3 Plan-and-Solve**. If the task is numerical and arithmetic hallucination is the failure mode, use **R14 Program of Thoughts**. If R1 works but is noisy, wrap with **R17 Self-Consistency Voting**.

## Structure

```
   Task prompt
        │
        │  + trigger ("Let's think step by step.")
        ▼
   ┌─────────────────┐
   │   LLM (single   │
   │   configured    │      no examples
   │    session)     │      no decomposition
   └────────┬────────┘      no plan call
            │
            ▼
   Reasoning trace ──▶ Final answer
   (model writes        (last span of the
    its working          same completion)
    out first)
```

A single call. One prompt, one completion. The trigger sits at the end of the user message; the model emits reasoning then answer in the same response. The two-stage variant adds one short extraction call after the trace.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Prompt builder** | composing the task prompt and appending the reasoning trigger | task spec + input $\to$ instruction string ending in the trigger phrase | smuggle in worked examples (that is **R2**), numbered step lists (that is **S4**), a persona (that is **S3**), or a plan template — any of those moves the pattern off R1 and must be named as the upgrade it is. |
| **Trigger** | the short elicitation phrase that biases the completion toward reasoning-then-answer | — $\to$ a fixed sentence appended after the task | be silently reworded between calls — the trigger is part of the baseline; A/B different phrasings deliberately, not accidentally. |
| **Model** | producing a single completion containing reasoning followed by the answer | trigger-augmented prompt $\to$ completion (trace + answer) | be a small or weakly-tuned model that ignores the trigger; if 10-sample inspection shows shallow or absent traces, the model is wrong for R1 — escalate to R2 or change model. |
| **Answer extractor** | pulling the final answer out of the completion for downstream code | completion $\to$ answer token / value / class | rely on free-form text matching; use a strict regex, a final-line convention, or a two-stage extraction call (R1 two-stage variant). Brittle extraction silently degrades the pattern. |

Four narrow responsibilities. The discipline of R1 is in the *Must not* column: every addition (examples, role, steps, plan) moves the pattern off R1 onto a heavier sibling. R1 is the trigger and nothing else.

## Collaborations

The Prompt builder composes the task instruction — exactly as it would for S1 — and appends the Trigger as the final sentence of the user message. The Model receives the trigger-augmented prompt and produces a single completion whose body is a step-by-step reasoning trace and whose final span is the answer. The Answer extractor reduces the completion to the comparable form downstream code expects: a number, a class label, a JSON value, an option letter. In the two-stage variant, a second short call wraps the reasoning trace and asks for the answer in a strict format — used when one-stage extraction is too brittle. R1 itself contains no evaluator, no retry, no critique, no fan-out; those moves belong to the wrappers (R17 voting around R1, R7 Reflexion retrying R1, R8 Self-Refine critiquing R1's output).

## Consequences

**Benefits**
- **Free upgrade over S1** — one extra sentence in the prompt; no examples, no extra calls, no fine-tune.
- Substantial accuracy lifts reported on arithmetic, symbolic, and commonsense reasoning benchmarks against capable instruction-tuned models.
- Easiest reasoning pattern to deploy and to roll back — the trigger is a one-line change, the comparison against S1 is one A/B.
- Composes cleanly with **R17 Self-Consistency Voting** — R1 $\times$ N + vote is the canonical reliability composition.
- Model-agnostic — any capable instruction-tuned generalist follows a reasoning trigger; no specialist build dependency.

**Costs**
- **Longer completions** — the reasoning trace inflates output tokens, growing the KV cache for that session (mechanism 3). On long-context billing the cost is non-trivial; on per-token output pricing it can dominate.
- **Higher latency** — more tokens generated means more time-to-final-answer; matters for interactive use.
- The reasoning *format is free-form* — every completion looks slightly different, complicating downstream parsing.

**Risks and failure modes**
- *Sycophantic reasoning* — the model emits a plausible-looking trace that supports a wrong answer (Turpin et al., 2023). The trace looks like deliberation; it is post-hoc rationalisation. R1 alone does not catch this; pair with **R17** (voting), **R7** (external evaluator), or **R8** (critique) where stakes warrant.

**The mechanism of sycophantic reasoning (mechanism 7).** Token generation is forward-only: once a token is sampled and appended, all subsequent tokens are conditioned on it. The model cannot revise a committed intermediate conclusion — it can only elaborate on it. A reasoning chain that drifts toward a plausible-sounding but incorrect conclusion will produce answer tokens that extend that conclusion, not correct it. This is not a model quality failure — it is an architectural property of autoregressive generation. The mitigation patterns (R7 Reflexion, R8 Self-Refine, R17 Self-Consistency) work precisely because they interrupt the forward-only commitment by generating alternative chains and selecting among them, rather than letting a single chain commit.
- *Trigger ignored* — small or weakly instruction-tuned models acknowledge the trigger (*"Let's think step by step. The answer is …"*) without actually reasoning. The lift over S1 collapses. Diagnose with 10-sample inspection; if the trace is shallow, the model is wrong for R1.
- *Format drift in the answer* — different completions place the answer in different positions or phrasings, breaking strict extractors. Mitigate with the **two-stage variant** or a strict final-line convention in the prompt.
- *Misclassification as R1* — a prompt that includes *one* worked example with reasoning is **R2 Few-Shot CoT**, not R1. *"Let's think step by step"* alongside a single demo is R2-with-one-shot, not R1. The defining property is *no examples*.
- *Reasoning lift plateaus on hard problems* — for problems requiring search through a structured space (combinatorial puzzles, multi-step planning), one trace is not enough. Escalate to **R9 Tree of Thoughts**, **R10 LATS**, or wrap with **R17**.

## Implementation Notes

- **Default trigger:** *"Let's think step by step."* — Kojima et al.'s original phrasing and still the most-cited default. Test alternatives only if you have a measurement budget.
- **Place the trigger at the end of the user message**, immediately before the model's turn. Earlier placement (mid-prompt) is less reliable across models.
- **Run the S1 vs R1 A/B before deploying.** If S1 is already correct on the task, R1's tokens are pure overhead. The pattern earns its keep on tasks where the gap is measurable.
- **Lock model and decoding parameters** when comparing S1 to R1 — temperature, top-p, model ID. A model swap is a regression test.
- **Strict answer extraction is worth it.** Either a final-line convention (*"Answer: X"* in the prompt) or the two-stage variant. Free-form parsing is a silent-bug factory.
- **Compose with R17, not replace it.** R17 wraps R1 (N samples of R1 + vote) and is the canonical reliability lift for reasoning tasks. R1 alone is fast and cheap; R1 $\times$ N is reliable and N$\times$ costly. Choose by the failure profile.
- **Watch for sycophantic reasoning.** Where the cost of a confident-wrong answer is high, never rely on a single R1 trace; wrap with R17 or **V15 LLM-as-Judge**.
- **Do not stack R1 inside R2.** R2's worked examples already contain reasoning traces — adding the R1 trigger to a few-shot prompt is redundant on capable models and confuses small ones. Pick one.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** R1 is a near-degenerate composition — it is **S1 Zero-Shot** plus a single appended trigger phrase. R1 is itself the inner step of several heavier patterns: **R17 Self-Consistency Voting** wraps R1 with N samples and a vote (the canonical *CoT $\times$ N + vote*); **R7 Reflexion** wraps R1 with retry-with-memory; **R8 Self-Refine** wraps R1 with critique-and-revise. The Prompt builder may compose with **S6 Output Template** to fix the answer's final-line format for the extractor.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Compose the task prompt | `code` | — (S1 baseline) |
| 2 | Append the reasoning trigger | `code` | — (the R1 move) |
| 3 | Submit to the Reasoner session | `LLM` | Reasoner session |
| 4 | Extract the final answer | `code` (or `LLM` in two-stage variant) | Extractor session *(optional)* |

**Skeleton** — wiring only; each `# LLM` line is a configured session:

```
zero_shot_cot(task, input, trigger="Let's think step by step."):
    prompt = format_task(task, input)                  # code  — the S1 prompt
    prompt = prompt + "\n\n" + trigger                  # code  — the R1 move
    completion = Reasoner(prompt)                       # LLM   — Reasoner session
    answer = extract_answer(completion)                 # code  — strict regex / final line
    return answer, completion                           # caller may want the trace too

# Two-stage variant (when one-stage extraction is brittle):
zero_shot_cot_two_stage(task, input, trigger="Let's think step by step."):
    trace = Reasoner(format_task(task, input) + "\n\n" + trigger)  # LLM
    answer = Extractor(trace + "\n\nTherefore, the answer is:")    # LLM — short call
    return answer, trace
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Reasoner** | a capable instruction-tuned generalist — the system's default model; small or weakly-tuned models often ignore the trigger | nothing beyond model defaults — that absence is the point; any added persona / constraints / examples moves the pattern off R1 to S3 / S5 / R2. Document model ID, temperature (typically 0 for deterministic R1; 0.7–0.9 when wrapped by R17), and top-p. | the task instruction + the input + the appended trigger |
| **Extractor** *(two-stage variant only)* | small fast generalist — extraction is mechanical, not reasoning | role: *"you extract the final answer from a reasoning trace and emit it in the strict format specified"*; the answer format (S6 Output Template) | the trace + the extraction prompt |

**Specialist-model note.** None — R1 works on any capable instruction-tuned generalist. There is no fine-tune, no classifier, no long-context requirement. The artifact doing the heavy lifting is the *trigger phrase itself*: a single sentence that, against a model trained on instruction-following corpora, addresses the region of the distribution where step-by-step solutions live. The only structural requirement is that the model be large and tuned enough to follow the trigger substantively — verify with 10-sample inspection before relying on R1 in production.

## Open-Source Implementations

R1 is the canonical *prompt-engineering-only* pattern — there is no library to install, because the pattern *is* appending a sentence to the prompt. The relevant references are the original paper's code, framework primitives that ship CoT as a built-in module, and documentation:

- **Kojima et al. — `zero_shot_cot`** — [`github.com/kojima-takeshi188/zero_shot_cot`](https://github.com/kojima-takeshi188/zero_shot_cot) — the official implementation accompanying *Large Language Models are Zero-Shot Reasoners* (NeurIPS 2022). The canonical reference; the `main.py` shows the trigger phrase and the two-stage extractor used in the paper.
- **DSPy — `ChainOfThought`** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — ships zero-shot CoT as a first-class module: swapping `dspy.Predict` for `dspy.ChainOfThought` injects a reasoning field before the output. The closest thing to a framework primitive.
- **Amazon Science — `auto-cot`** — [`github.com/amazon-science/auto-cot`](https://github.com/amazon-science/auto-cot) — Zhang et al. (2022); uses Zero-Shot CoT as the inner step to *automatically* generate the demonstrations for an R2 Few-Shot CoT prompt. Useful as a reference for how R1 is used as a building block.
- **DAIR.AI Prompt Engineering Guide — Zero-Shot CoT page** — [`promptingguide.ai/techniques/zero-shot-cot`](https://www.promptingguide.ai/techniques/zero-shot-cot) and the source repo [`github.com/dair-ai/Prompt-Engineering-Guide`](https://github.com/dair-ai/Prompt-Engineering-Guide) — the community-maintained canonical written explanation; the most cited tutorial reference.

> R1 is an architecture / prompt-engineering pattern realised in a single appended sentence; there is no canonical library to install. The references above are the paper's code, framework primitives, and tutorial sources.

## Known Uses

- **Every reasoning benchmark report since 2022** quotes a "Zero-Shot CoT" baseline as the trigger-only comparison against bare zero-shot and few-shot CoT (GSM8K, MultiArith, MATH, SVAMP, CommonsenseQA, StrategyQA, Last Letter Concatenation).
- **DSPy programs** default to `ChainOfThought` for any signature where reasoning is expected to help — Zero-Shot CoT is the framework's implicit default.
- **Provider cookbooks** — Anthropic, OpenAI, and Google all include zero-shot CoT in their prompt-engineering guides as the first reasoning upgrade above bare instruction prompting.
- **Inference-time reasoning models** (o1, o3, DeepSeek-R1, Gemini Thinking) effectively *internalise* the R1 pattern: the trigger is no longer needed because the model is trained to emit reasoning tokens before the answer by default. R1 is what those models do natively; on non-reasoning models R1 is the prompt-side substitute.
- **Production LLM pipelines** routinely append a reasoning trigger to prompts for arithmetic, classification with rationale, and multi-hop Q&A — the cheapest reliability lift available.

## Related Patterns

- **Refines S1 Zero-Shot** — R1 is S1 plus a single appended trigger sentence. The promotion from a Signal-layer pattern (S1) to a Reasoning-layer pattern (R1) is the trigger: S1 produces an answer directly, R1 produces reasoning then answer.
- **Sibling of R2 Few-Shot CoT** — same band, same intent (elicit explicit reasoning), opposite axis: R1 supplies *no examples* (the model invents the format); R2 supplies *worked examples* (teaches both content and format). R1 is cheaper; R2 controls format better. Use R1 by default; escalate to R2 when the trace format is unstable or the model is too small to follow the trigger.
- **Distinct from R3 Plan-and-Solve** — R3 produces an *explicit plan artifact* in a first call before any execution; R1 produces reasoning and answer together in one call with no separable plan. R3 is for inspectable workflows; R1 is for single-shot reasoning.
- **Distinct from R4 ReAct** — R4 interleaves reasoning with *tool calls and observations* in a loop; R1 is a single completion with no tools. Use R4 when external information must enter the trace mid-reasoning.
- **Distinct from R14 Program of Thoughts** — R14 generates *code* that an executor runs; R1 generates *natural-language reasoning* that the model itself produces. For numerical tasks where arithmetic hallucination is the failure, R14 strictly dominates R1.
- **Wrapped by R17 Self-Consistency Voting** — R17's canonical composition is *R1 $\times$ N + vote* (Wang et al., 2022); the explicit chain-of-thought that R1 elicits is what gives sampling diversity room to express itself, and without R1 the samples lack the variation that makes voting informative.
- **Wrapped by R7 Reflexion** — R7 retries R1 (or another reasoning pattern) with a memory of prior failures from an external evaluator; the per-attempt call is typically R1.
- **Wrapped by R8 Self-Refine** — R8 generates with R1, critiques, and revises in a sequential loop with the same model.
- **Composes with S6 Output Template** — fixing the answer's final-line format ("Answer: X") makes the deterministic extractor reliable and removes most parsing failures without forcing the two-stage variant.
- **Used by O-category orchestration patterns** — the worker step inside O6 Orchestrator-Workers and the per-branch reasoning inside O4 Parallelization is often R1.
- **Note on fundamentality** — R1 earns its number as the *zero-example* version of CoT, structurally distinct from R2 (which adds worked examples as participants in the prompt). The trigger-vs-examples axis is the band's primary distinction; both ends are fundamental. R1 is *not* a degenerate variant of R2 — it is the prior pattern R2 refines by adding demonstrations.

## Sources

- Kojima, Gu, Reid, Matsuo, Iwasawa (2022) — *Large Language Models are Zero-Shot Reasoners* (arXiv [2205.11916](https://arxiv.org/abs/2205.11916), NeurIPS 2022). The canonical reference; introduces *"Let's think step by step"* and the one-stage / two-stage variants.
- Wei et al. (2022) — *Chain-of-Thought Prompting Elicits Reasoning in Large Language Models* (arXiv [2201.11903](https://arxiv.org/abs/2201.11903)). The few-shot CoT paper R1 is the zero-example counterpart of.
- Wang et al. (2022) — *Self-Consistency Improves Chain of Thought Reasoning in Language Models* (arXiv [2203.11171](https://arxiv.org/abs/2203.11171)). The canonical *R1 $\times$ N + vote* composition.
- Turpin et al. (2023) — *Language Models Don't Always Say What They Think* (arXiv 2305.04388). Documents sycophantic / unfaithful CoT — the trace-supports-wrong-answer failure mode.
- Yang et al. (2023) — *Large Language Models as Optimizers* (OPRO, arXiv 2309.03409). Discovered the *"Take a deep breath and work on this problem step-by-step"* trigger phrasing.
- Zhang et al. (2022) — *Automatic Chain of Thought Prompting in Large Language Models* (Auto-CoT, arXiv 2210.03493). Uses Zero-Shot CoT as the inner step to generate demonstrations for Few-Shot CoT.
- DAIR.AI Prompt Engineering Guide — *Zero-Shot CoT* section (canonical tutorial reference).
- Lilian Weng — *Prompt Engineering* survey (Chain-of-Thought section).
