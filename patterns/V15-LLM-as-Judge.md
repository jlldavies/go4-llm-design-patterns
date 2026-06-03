# V15 — LLM-as-Judge

> Use a separate LLM call to score the output of another LLM call against an explicit rubric, producing an automated, ground-truth-free verdict on quality.

**Also Known As:** Model-Based Evaluation, AI Evaluation, Inferential Evaluation, LLM-as-a-Judge.

**Classification:** Category V — Reliability · Band V-C Observability and Evaluation · the *scoring mechanism* — a primitive other reliability and orchestration patterns reuse rather than a free-standing system.

---

## Intent

Turn "is this output any good?" into a deterministic, schema-checkable call against a written rubric, so generative quality can be measured automatically — at scale, without human labels, and on dimensions traditional metrics cannot reach.

## Motivation

Generative outputs resist measurement. Human evaluation is the gold standard but expensive and slow. Traditional NLP metrics — BLEU, ROUGE, exact match, F1 — measure surface overlap with a reference, not semantic correctness, helpfulness, faithfulness, or tone. For most LLM tasks, the reference does not exist, or many distinct answers are equally good, and the metric scores all of them as failures.

Zheng et al. (2023) — MT-Bench and Chatbot Arena — established empirically that a strong LLM, prompted with a written rubric, agrees with human judges at roughly the inter-human rate (around 80%) on chat-quality dimensions. That is the load-bearing finding: a model can substitute for a human on the *scoring* step, not on the *task* step. The judge does not need to be able to produce the output it grades; it only needs to recognise quality reliably against a fixed rubric.

This makes a class of previously infeasible work feasible. **V16 Offline Eval** can run thousands of cases against a regression suite per deploy. **V17 Online Eval** can sample production traffic continuously without ground truth. **O5 Evaluator-Optimizer** can iterate generator outputs against an automated critic. **S8 Meta-Prompt** can choose between candidate prompts on measured quality. All four require an automated scorer; V15 is the scorer. It is therefore not a free-standing system but a *primitive* — a building block whose value is realised inside the patterns that consume it. The discipline of the pattern is the discipline of the rubric: a well-specified rubric makes the judge useful; a vague one makes it noise dressed as numbers.

## Variants

V15 has two structural variants, distinguished by what the judge is shown:

- **Single-output (direct assessment).** The judge sees one output and scores it against absolute criteria (1–5 per dimension, PASS/FAIL, etc.). The output of MT-Bench's single-answer grading mode; the mode RAGAS, G-Eval, DeepEval, and Prometheus use by default. Cheaper, more interpretable, but suffers from absolute-scale drift across runs.
- **Pairwise (preference judgment).** The judge sees two outputs for the same input and picks the better one (A wins / B wins / tie). The mode Chatbot Arena uses for ELO ranking, and the mode RLHF reward modelling relies on. More robust to absolute-scale drift, more sensitive to *position bias* (judges over-prefer the first answer shown) — the canonical mitigation is to run each pair both ways and average.

Both are V15: same participants, same rubric discipline, same biases to police. They differ only in what the per-call prompt wraps — one output, or two. Choose pairwise when ranking matters and absolute scores would drift; choose single-output when you need an interpretable per-output score and a regression baseline.

## Applicability

Use V15 when:

- the output is generative and no exact reference answer exists (or many references are equally valid);
- quality must be measured at production scale, where human labelling is infeasible;
- the quality dimensions can be written down as a rubric a stranger could apply consistently;
- another pattern that needs an automated scorer is in play — V16, V17, O5, S8.

Do not use V15 when:

- the output is verifiable against ground truth (exact match, schema check, unit test pass/fail) — write the deterministic check, not an LLM judge;
- the rubric cannot be made explicit (vague "good vibes" rubrics produce a judge that scores style and confidence, not the thing you care about);
- the task is so adversarial or out-of-distribution that even a strong judge is unreliable — fall back to **V1 Human-in-the-Loop** for the affected slice;
- the cost of the extra LLM call dominates the value of the measurement (low-traffic, low-stakes tasks).

## Decision Criteria

V15 is right when quality is generative, the rubric can be written down, and an automated scorer unlocks a downstream pattern that needs one.

**1. Rubric-writability test.** Can you write the evaluation criteria as 2–6 dimensions, each with a defined scale and one-sentence description, that a competent stranger could apply? If yes, V15 is viable. If you cannot specify what "good" means, V15 will fabricate consistency — and fall back to **V1 Human-in-the-Loop** until you can.

**2. Judge-vs-task capability.** The judge must be *at least as capable as* the generator on the rubric's dimensions. The standard heuristic: evaluate Haiku-tier outputs with Sonnet-tier or stronger; never grade GPT-4-class outputs with a 7B model unless you have measured agreement on a held-out set.

**3. Calibration against humans.** Before trusting V15 at scale, run it on 50–200 human-labelled cases and measure agreement. Target $\geq$ 70% agreement on PASS/FAIL or $\geq$ 0.6 correlation on numeric scores. Below that, the judge is noise; iterate the rubric or change the judge model.

**4. Bias audit — three known failure modes.**
- **Position bias** (pairwise): judges favour the first option shown. *Mitigation:* run each pair in both orders, average.
- **Verbosity bias**: judges favour longer answers. *Mitigation:* include a "concision" dimension; or normalise score by length on a held-out set.
- **Self-preference / self-similarity**: judges score outputs from their own model family higher. *Mitigation:* use a different model family as judge, or pair two judges from different families. The mechanistic root is that models from the same family share similar learned attention bilinear forms (mechanism 1); inputs that match the judge model's training distribution receive higher probability mass on positive score tokens by virtue of distribution overlap, independent of actual quality.

If you have not measured and mitigated all three, the score is suspect.

**5. Cost per evaluation $\times$ evaluation frequency.** V15 adds one (single-output) or two (pairwise with order-flip) LLM calls per evaluation. At V17 sample rates (1–10% of production traffic) this is manageable; at full coverage of high-traffic systems it is not. Sample, don't exhaustively evaluate, unless the value justifies it.

**Quick test — V15 is the right pattern when:**

- the task output is generative and lacks ground truth, *and*
- the rubric can be written down explicitly with per-dimension scales, *and*
- the judge model is at least as capable as the generator on the rubric's dimensions, *and*
- you have measured judge-vs-human agreement on a calibration set and the result is acceptable.

If the output is deterministically verifiable, use the deterministic check. If the rubric cannot be specified, fall back to **V1 Human-in-the-Loop**. If you need *relative voting across N candidates from the same generator* rather than absolute scoring, use **R17 Self-Consistency Voting** — different mechanism, different question.

## Structure

```
            Input (the case)                  Rubric (loaded once at session setup)
                │                              │
                └──────────────┐  ┌────────────┘
                               ▼  ▼
              [ Primary LLM ] ── output ──▶ [ Judge LLM ]
                                                │
                                       per-dimension scores
                                       + reasoning
                                                │
                                                ▼
                                       [ Score Aggregator ] ──▶ verdict
                                                │
                                                ▼
                                   downstream consumer:
                                   V16 / V17 / O5 / S8
```

The judge is a *separate session* from the primary, with its own setup (the rubric) loaded once before its first call. The primary never sees the rubric; the judge never generates the task answer.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Primary LLM** | producing the output to be evaluated | task input $\to$ output | see the rubric, or score itself. A primary that knows the rubric will optimise for the judge instead of the user. |
| **Rubric** | the written evaluation criteria — dimensions, scales, one-sentence descriptions, edge-case rulings | — $\to$ fixed setup artifact | be vague, drift between runs, or live only in the heads of the team that wrote it. A rubric that is not a checked-in artifact is not a rubric. |
| **Judge LLM** | applying the rubric to one (or two) outputs | rubric (setup) + input + output(s) $\to$ per-dimension scores + reasoning | generate the task answer, or rewrite the rubric mid-evaluation. The judge that helps fix the output has stopped being a judge. |
| **Score Aggregator** | combining per-dimension scores into an actionable verdict (pass/fail, weighted total, regression delta) | dimension scores $\to$ single verdict | hide failing dimensions inside a passing average. The aggregator must surface any blocking-dimension failure even when the total looks fine. |
| **Calibration Set** *(prerequisite)* | the human-labelled cases that prove the judge agrees with humans well enough to be trusted | held-out cases + human labels $\to$ judge-vs-human agreement metric | be drawn from the same data as the eval suite — a judge calibrated on the suite cannot detect drift on the suite. |

The Primary and the Judge **must be distinct sessions** even when the same model serves both — distinct setups, distinct prompts, distinct invocations. Mixing them is the pattern's most common failure: a system that grades its own output with the same context that produced it is not evaluating, it is rationalising.

## Collaborations

The Primary LLM produces an output for some input. The Judge LLM, configured at setup time with the rubric, receives the input and the output (or two outputs, in the pairwise variant). It scores each dimension, with chain-of-thought reasoning, and emits structured scores. The Score Aggregator turns the dimension scores into a verdict — a pass/fail gate, a numeric score for trending, a winner for a tournament. The verdict is consumed by the pattern that called V15: **V16 Offline Eval** uses it to gate deployments; **V17 Online Eval** uses it to monitor production quality; **O5 Evaluator-Optimizer** feeds it back to the generator as a signal to refine; **S8 Meta-Prompt** uses it to choose between candidate prompts.

The Calibration Set sits outside this runtime path but governs whether the runtime is trusted at all. Before V15 goes into production use, the judge is run on the calibration set, agreement with the human labels is measured, and the rubric or judge model is iterated until agreement meets threshold. Without this step, V15 produces numbers without producing measurement.

## Consequences

**Benefits**
- Quality measurement without ground truth, at scales human labelling cannot reach.
- Enables continuous evaluation (V16, V17), iterative refinement (O5), and prompt selection (S8) — all impossible without an automated scorer.
- Rubric-driven evaluation forces the team to write down what "good" means — a forcing function that improves the system itself, not just its measurement.
- Reasoning emitted alongside scores makes judgments inspectable and disputable.

**Costs**
- One (or two) extra LLM calls per evaluation; non-trivial at high volume.
- Strong judge model is a hard requirement — capability ceiling sets the measurement ceiling.
- Rubric authoring and maintenance is real engineering work, not a side task.
- Calibration against humans is a recurring cost — judges and models drift; calibration must be re-checked.

**Risks and failure modes**
- *Position bias* — pairwise judges over-prefer the first option shown; uncontrolled, this inverts rankings.
- *Verbosity bias* — judges over-prefer longer answers regardless of correctness.
- *Self-preference / self-similarity bias* — judges score outputs from their own model family higher.
- *Rubric under-specification* — the judge scores style and confidence instead of the dimension you cared about, with full consistency.
- *Eval-suite over-fitting* — the system is tuned to pass the judge, not to serve users (Goodhart's law applied to LLM evaluation).
- *Judge capability gap* — the judge is weaker than the generator on the rubric's dimensions; scores look fine and mean nothing.

## Implementation Notes

- **Use a stronger or different-family model as judge** wherever possible — measurement ceiling tracks judge capability, and a different family reduces self-similarity bias.
- **Require chain-of-thought reasoning before the score**, not after — reasoning produced after the verdict is rationalisation, reasoning produced before is judgment. The reasoning is more reliable than the number.
- **Run pairwise evaluations in both orders and average** — single most effective mitigation for position bias, costs one extra call per pair.
- **Score each dimension separately, then aggregate** — judges asked for a single "quality score" smush dimensions together; judges asked for faithfulness, helpfulness, format, and safety separately produce signals you can actually act on.
- **Treat the rubric as a checked-in artifact** — versioned, code-reviewed, tested. A rubric that changes silently invalidates every prior measurement.
- **Re-calibrate after every model upgrade** — when the judge model changes (and Anthropic / OpenAI / Google ship constantly), agreement against human labels must be re-measured before trusting prior baselines.
- **Sample, don't always exhaustively evaluate** — V17 at 1–10% sample with stratified selection (by user segment, task type, cost outlier) catches drift without paying for full coverage.
- **Place the rubric before the trajectory when judging long traces.** When judging long trajectories (as in V18), the rubric and scoring instructions should be placed at the very start of the judge's context, not after the trajectory text. As the trace evidence grows, it pushes mid-context content toward the weakest-recall positions (mechanism 4); placing the rubric first ensures it remains in the start-of-context high-recall zone throughout.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V15 is consumed by **V16** (regression gating), **V17** (production monitoring), **O5** (evaluator-optimizer loop), and **S8** (meta-prompt selection). The rubric itself is a Signal-layer artifact — a **S6 Output Template** for structured judge output, with **S5 Constraint Framing** on what the judge must not score on (length, formatting flourish, etc.). The Judge session is set up by **S3 Persona** (the evaluator role) plus the rubric.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Primary LLM produces the output | `LLM` | Primary session |
| 2 | Compose judge prompt: input + output(s) | `code` | S6 (judge output template) |
| 3 | Judge LLM scores against rubric, with reasoning | `LLM` | Judge session |
| 4 | *(pairwise only)* re-run judge with options swapped | `LLM` | Judge session |
| 5 | Aggregate per-dimension scores into verdict | `code` | |
| 6 | Emit verdict to downstream consumer (V16/V17/O5/S8) | `code` | V16, V17, O5, S8 |

**Skeleton** — the wiring; each `# LLM` line is a configured session (specified below), not a bare call:

```
evaluate(case):
    output = Primary(case.input)                    # LLM — the system under test
    scores = Judge(case.input, output)              # LLM — rubric applied to one output
    return Aggregate(scores)                        # code

evaluate_pairwise(case, output_a, output_b):
    s_ab = Judge(case.input, output_a, output_b)    # LLM — A first
    s_ba = Judge(case.input, output_b, output_a)    # LLM — B first; cancels position bias
    return Aggregate(combine(s_ab, s_ba))           # code
```

**The LLM sessions.** Each `LLM` step is set up before its first call. The setup — model, role, rubric, output contract — is loaded once; the per-call prompt wraps only the data that changes.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Primary** | the system's task model — whichever model serves the production workload | the system's normal task setup (role, task definition, format) — *not* the rubric | the task input |
| **Judge** | stronger than or different-family from the Primary; specialist evaluator (e.g. Prometheus) where calibrated | role ("you are a strict evaluator following the rubric below"); the **rubric** (dimensions, scales, one-sentence descriptions, edge-case rulings); output contract (per-dimension score + reasoning, JSON); instruction to produce reasoning *before* scoring | the task input + the output(s) to be evaluated |

Concretely, for the **Judge** session: the setup loaded once is *"You are a strict evaluator. Apply the following rubric to the candidate output. Produce reasoning per dimension before assigning a score. Output JSON: {faithfulness: 1–5, helpfulness: 1–5, format: PASS/FAIL, safety: PASS/FAIL, reasoning: string}. Do not reward length or formatting flourish. \[rubric body\]"*. The per-call prompt then carries only *"Input: {input}\n\nOutput: {output}"* (or two outputs in the pairwise variant).

**Specialist-model note.** No fine-tuned specialist is *required* — a stronger generalist (Sonnet, GPT-4-class, Gemini Pro) suffices for most rubrics, which is the deployment pattern in RAGAS, DeepEval, and MT-Bench by default. Where a specialist *is* used, **Prometheus 2** (Kim et al., 2024) is the canonical open-source evaluator LM — fine-tuned for rubric-based scoring, reaches 72–85% agreement with human judgments, and is cheap to run for high-volume judging. Treat that as a build dependency: a specialist judge changes the calibration story (you calibrate the specialist once, against humans; the generalist must be re-calibrated whenever the model changes). The rubric itself is the heaviest prompt artifact in either case — its quality caps the value of the whole pattern.

## Open-Source Implementations

- **RAGAS** — [`github.com/explodinggradients/ragas`](https://github.com/explodinggradients/ragas) — RAG-focused evaluation framework; provides LLM-as-judge metrics (faithfulness, answer relevancy, context precision/recall) and test-data generation; integrates with CI/CD pipelines.
- **DeepEval** — [`github.com/confident-ai/deepeval`](https://github.com/confident-ai/deepeval) — general LLM evaluation framework, pytest-like; ships G-Eval, hallucination, task-completion, and answer-relevancy metrics, all LLM-as-judge based; broad framework integration (LangChain, OpenAI Agents, CrewAI).
- **FastChat — `llm_judge`** — [`github.com/lm-sys/FastChat`](https://github.com/lm-sys/FastChat/tree/main/fastchat/llm_judge) — the canonical MT-Bench / Chatbot Arena implementation from LMSYS; supports single-output and pairwise judging; ships 3.3K human-judged calibration cases (`lmsys/mt_bench_human_judgments`).
- **Prometheus / Prometheus 2** — [`github.com/prometheus-eval/prometheus-eval`](https://github.com/prometheus-eval/prometheus-eval) — open-source specialist evaluator LM (7B and 8x7B) fine-tuned for rubric-based scoring; supports both direct assessment and pairwise ranking; the open alternative to GPT-4 as judge.

## Known Uses

- **Chatbot Arena (lmarena.ai)** — LMSYS production deployment of pairwise V15 at scale; backs the public ELO leaderboard and serves 10M+ comparisons across 70+ models.
- **MT-Bench** — the original LLM-as-Judge benchmark; 80 multi-turn questions scored by GPT-4 as judge; standard reference for new model evaluations.
- **Anthropic, OpenAI, Google internal eval pipelines** — all major labs use LLM-as-Judge as part of pre-release and continuous evaluation; documented in model cards and system cards (2024–25).
- **Production RAG assistants** — RAGAS / DeepEval embedded in CI/CD as deployment gates (V16) and in production monitoring (V17), now standard practice in enterprise RAG.

## Related Patterns

- **Required by** O5 Evaluator-Optimizer — the Evaluator role *is* V15; O5 wires it into a refine loop with the generator.
- **Required by** V16 Offline Eval — V16 is the test framework, V15 is the scoring mechanism inside it; V16 without V15 reduces to exact-match testing.
- **Required by** V17 Online Eval — production sampling and alerting needs an automated scorer; V15 is that scorer.
- **Required by** S8 Meta-Prompt — selecting between candidate prompts needs measured quality on each; V15 produces the measurement.
- **Composes with** V14 Trajectory Logging — judgments themselves should be logged as V14 spans so judge drift is itself observable.
- **Pairs with** S6 Output Template — the structured judge output (per-dimension scores + reasoning) is a Signal-layer artifact; without S6 discipline, judge output is unparseable.
- **Distinct from** R17 Self-Consistency Voting — R17 votes across multiple samples from the *same generator* to pick the most common answer (relative, internal); V15 scores an output against an *external rubric* with a separate judge (absolute, external). Different question, different mechanism.
- **Distinct from** R7 Reflexion and R8 Self-Refine — those use a critic to *improve* the agent's next attempt; V15 is the evaluation primitive that grades *finished* outputs. Reflexion and Self-Refine typically use V15 as their critic.
- **Shares the judge mechanism with** K5 Adaptive RAG (its Quality and Support Evaluators are domain-specific V15 instances).

## Sources

- Zheng et al. (2023) — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (arXiv 2306.05685). The foundational paper; establishes ~80% judge-vs-human agreement and names the three biases (position, verbosity, self-preference).
- Liu et al. (2023) — "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment" (arXiv 2303.16634). Chain-of-thought rubric application for NLG.
- Dubois et al. (2023) — "AlpacaEval: An Automatic Evaluator of Instruction-Following Models." Pairwise V15 applied to instruction-tuned model ranking.
- Kim et al. (2024) — "Prometheus 2: An Open Source Language Model Specialized in Evaluating Other Language Models" (arXiv 2405.01535). The canonical open-source specialist judge.
- Es et al. (2024) — "RAGAS: Automated Evaluation of Retrieval Augmented Generation" (EACL 2024). RAG-specific V15 metrics.
- LMSYS — Chatbot Arena documentation and methodology notes (lmarena.ai); the largest production V15 deployment.
