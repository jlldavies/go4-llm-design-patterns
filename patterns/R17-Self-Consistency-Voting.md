# R17 — Self-Consistency Voting

> Run the same prompt N times with diversity-inducing sampling, then select the answer by majority vote — marginalising over independent reasoning paths instead of trusting any single one.

**Also Known As:** Self-Consistency, Self-Consistency Decoding, Ensemble Sampling, Majority Vote, SC Prompting. (Universal Self-Consistency and weighted-vote variants noted in Variants.)

**Classification:** Category III — Reasoning · Band III-C Iterative refinement · the *parallel-with-voting* pattern — sibling of R7 Reflexion's *sequential-with-memory* and R8 Self-Refine's *sequential-with-critique*.

---

## Intent

Improve the reliability of a reasoning step by sampling N independent attempts at the *same* prompt and selecting the answer they most agree on, instead of trusting a single greedy decode.

## Motivation

A single chain of thought is a *random walk*: temperature, the model's prior, and the order tokens happen to fall in all push the trace one way or another. For a hard reasoning question, any individual trace is noisy — sometimes correct, sometimes derailed by an early misstep that the rest of the chain rationalises. Greedy decoding hides this by returning the single highest-probability path, which is not the same thing as the most likely *answer*; many distinct chains can converge on the same correct answer while individually being low-probability paths.

Wang et al. (2022) made the observation precise: for reasoning tasks, the right object to maximise is not P(path) but P(answer) marginalised over paths. The trick is operational. *Sample* N independent chains-of-thought from the model with temperature > 0; *extract* the final answer from each; *vote*. The correct answer is more likely to be reached by multiple, different reasoning paths than any one wrong answer is — wrong chains are wrong in many different ways, but the correct chain has fewer ways to look right. So agreement across diverse traces is a signal of correctness. The mechanistic basis of why temperature sampling produces diverse paths (rather than near-identical answers) depends on R1/R2 CoT (mechanism 7): without intermediate reasoning tokens, temperature sampling introduces noise only at the final answer token. With CoT, each intermediate reasoning token is stochastically sampled, and the conditional distribution of token N+1 given a wrong token at step k diverges from the correct path — creating genuinely different reasoning paths rather than n-copies of one answer with minor surface variation.

This is structurally distinct from the other reliability patterns in the same band. **R7 Reflexion** repeats *sequentially*, with memory of past failure — each attempt is informed by the last. **R8 Self-Refine** generates once, then critiques and revises in a sequential loop with the same model. **R17 Self-Consistency** repeats *in parallel*, with no memory and no critique — independence is the point. The three patterns share an Intent (reliability through repetition) but resolve it on different axes: sequential-with-memory (R7), sequential-with-critique (R8), parallel-with-voting (R17). Self-Consistency is also distinct from the search patterns R9 Tree of Thoughts and R10 LATS: those *expand, evaluate, prune* a tree of partial thoughts toward a goal; R17 *marginalises* over fully-independent completed samples. Search picks one good path; voting integrates over many.

## Variants

The variants differ in *how votes are counted* and *what counts as agreement*:

- **Vanilla Self-Consistency (Wang et al., 2022).** Sample N CoT chains, extract a literal final answer from each (a number, a label, an option letter), tally by exact match, return the mode. Works when answers are discrete and literally comparable.
- **Universal Self-Consistency / USC (Chen et al., 2023).** When answers are free-form (an explanation, a summary, a code snippet) and cannot be exact-matched, hand the N candidates to the LLM itself and ask it to pick the response most consistent with the rest. The LLM acts as a *cluster judge* over its own samples. Extends self-consistency beyond tasks with extractable literal answers.
- **Weighted Self-Consistency.** Weight each vote by a confidence signal — token-level log-probability, judge score, or evaluator pass — rather than counting one vote per chain. Useful when sampling is cheap but a few chains are clearly stronger than others.

All three share the structural move — *generate N independent traces, integrate, decide*. They differ only in how integration is implemented (literal tally, LLM judge, weighted tally).

## Applicability

Use Self-Consistency Voting when:

- the task has an objectively correct or strongly preferred answer (math, multiple-choice, classification, code with tests, structured extraction);
- the model's accuracy is below its capability ceiling — single-shot is noisy but often nearly right;
- you can afford N× the cost and latency of a single call;
- you need a confidence signal alongside the answer (agreement rate is one).

Do not use it when:

- the task is open-ended and subjective (creative writing, opinion synthesis) — there is no "correct" mode to vote toward; prefer **R8 Self-Refine**;
- the model has a *systematic bias* on the task — all N samples will be wrong in the same direction, and voting cannot fix that; prefer **R7 Reflexion** (which can use external feedback) or **O5 Evaluator-Optimizer** (separate judge model);
- you have an automated success criterion (tests, schema, executor) — **R7 Reflexion** uses that signal directly and is cheaper than N parallel rolls;
- the latency budget cannot tolerate parallel-N fan-out (a single sequential refine via **R8** may be cheaper at the same quality on easy tasks);
- the search space is so large that the correct answer is rarely reached even once in N samples — switch to **R9 Tree of Thoughts** or **R10 LATS**, which *search*.

## Decision Criteria

R17 is right when single-shot output is noisy but often nearly right, the answer space is comparable across samples, and you can spend N× to buy a measurable reliability gain.

**1. Pick N — the primary tuning lever.** N controls the cost / reliability curve directly. Wang et al. measured diminishing returns: most of the achievable gain is captured by **N = 5–10**; gains beyond N = 20 are small. Start at N = 10 and tune down if the agreement rate is high (the task is easy), tune up only if disagreement is split between two close candidates.

**2. Set temperature for diversity.** Sampling must be diverse or the N samples collapse to the same trace. Use **temperature 0.7–0.9** (Wang et al.'s working range); top-p ≈ 0.95 is a reasonable default. Temperature 0 degenerates the pattern — N copies of the greedy decode.

**3. Choose the vote function.** If answers are discrete and literally comparable (numbers, labels, option letters, JSON keys), use **literal majority** — code, no LLM. If answers are free-form, use **Universal Self-Consistency** (an LLM cluster-judge) or define an equivalence classifier. Picking the wrong vote function destroys the pattern: literal voting on free text returns "no majority" even when nine of ten samples agree in meaning.

**4. Test for systematic bias before deploying.** Voting amplifies the model's *modal* answer. If the modal answer is systematically wrong (a known model blind spot, a prompt-induced bias, a misleading framing), voting will return it with high confidence. Run a labelled sample: if errors cluster on the same kind of question rather than spreading randomly, the bias is systematic — Self-Consistency will not save you. Use **R7 Reflexion** with an external evaluator, or **O5 Evaluator-Optimizer** with a separate judge model.

**5. Cost the parallel fan-out.** Self-Consistency is *cheap* only relative to its quality gain. The headline cost is **N × the cost of one sample** — at N = 10 you pay 10× (mechanism 2 applies within each sample's own decoding; the N fan-out multiplies the total but each call's attention cost is bounded by its own seq_len). The economically defensible move is often *N samples on a small / cheap model* rather than 1 sample on the expensive one: small model at N is typically cheaper than large model at 1 because a 7B model at temperature 0.8 costs a fraction of a 70B model per call (mechanism 8 — model size directly determines per-token compute cost). At N=10, a small model is often cost-competitive with a single large-model call while providing voting robustness. Measure on your task before committing.

**Quick test — R17 is the right pattern when:**

- the task has an objectively right answer (or a literal mode), *and*
- the model is not systematically biased on this task (errors are scattered, not clustered), *and*
- the budget tolerates N × the per-call cost at N ≥ 5, *and*
- temperature > 0 sampling is available and the answer space is comparable across samples.

If errors cluster systematically, voting will not help — use **R7 Reflexion** with external feedback or **O5 Evaluator-Optimizer** with a separate judge. If the answer is free-form and equivalence is hard to define, use the **Universal Self-Consistency** variant. If the task needs search through a structured space rather than agreement across complete attempts, use **R9 Tree of Thoughts** or **R10 LATS**.

## Structure

```
                         ┌──▶ Sample 1 (T>0) ──▶ answer₁ ─┐
  Prompt P ──▶ broadcast ├──▶ Sample 2 (T>0) ──▶ answer₂ ─┤
   (composed             │           ⋮                    ├──▶ Aggregate ──▶ Winner
    with R1/R2           ├──▶ Sample N (T>0) ──▶ answerₙ ─┘    (literal
    CoT)                 │                                       majority
                         │                                       or
                         │                                       LLM judge)
                         │
                         └─ same model, same prompt, independent draws
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Prompt builder** | composing the single prompt P that will be sampled N times | task + (optional) CoT trigger / exemplars → finished prompt string | vary the prompt across the N rolls — that destroys the marginalisation argument; diversity must come from sampling, not from prompt edits. |
| **Sampler** | drawing N independent completions at temperature > 0 | prompt P → N completions | sample at temperature 0 or share a seed — N degenerate copies provide no signal. |
| **Answer extractor** | pulling the comparable answer object out of each chain-of-thought | one completion → one answer token / value / class | bias toward any particular chain — must be a pure deterministic function, applied uniformly. |
| **Aggregator** | counting agreement and selecting the winner | N answers → winning answer + confidence | hide ties or partial agreement; if the top-2 are close, surface that — the agreement rate *is* the confidence signal. |
| **Cluster judge (LLM)** *(optional)* | grouping semantically-equivalent free-form answers when literal match fails | N candidate answers → equivalence classes (or direct winner) | rewrite or merge the candidates; it only *clusters*. (Used in the Universal Self-Consistency variant.) |

Five narrow responsibilities. The pattern's reliability depends on the *independence* of the N samples — a leaky Sampler (shared seed, deterministic decode) or a contaminated Prompt builder (varying the prompt) collapses the whole structure into "one call, repeated".

## Collaborations

The Prompt builder constructs P once (most often composing **R1 Zero-Shot CoT** — appending "Let's think step by step" — or **R2 Few-Shot CoT** with exemplars; the explicit CoT is what gives diversity room to express itself). The Sampler fans out N parallel calls to the same model with the same prompt at temperature 0.7–0.9. As each completion returns, the Answer extractor reduces it to its comparable form — the final number, the answer letter, the JSON object, the function signature. The Aggregator tallies and returns the modal answer together with the agreement rate as a confidence signal. When answers are not literally comparable (free-form summaries, explanations, code with stylistic variation), an optional Cluster judge LLM groups the candidates by meaning before the count, or directly picks the response most consistent with the rest — the Universal Self-Consistency move.

## Consequences

**Benefits**
- Substantial accuracy gains on reasoning tasks against single-shot CoT, especially as model capability approaches its ceiling.
- Provides a calibrated confidence signal for free — the agreement rate over N samples.
- Embarrassingly parallel: latency is one sample plus aggregation, not N × one sample, given parallel capacity.
- Composes cleanly with **R1 / R2 CoT** — Self-Consistency = CoT × N + vote is the canonical composition.

**Costs**
- **N × token cost** is the headline price. Even with parallel latency, the dollar / FLOPS cost scales linearly in N.
- Aggregation logic adds engineering surface — vote functions, equivalence checking, cluster judging.
- Memory and rate-limit pressure: N concurrent calls hit provider quotas.

**Risks and failure modes**
- *Systematic bias unfixable* — voting amplifies the modal answer. If the model is reliably wrong on a question type, R17 returns the wrong answer with high agreement (and high reported confidence) — worse than no Self-Consistency, because the operator now trusts it.
- *Diversity collapse* — temperature too low, or shared sampling state, returns N near-identical completions; the agreement rate becomes meaningless.
- *Wrong vote function* — literal voting on free-form text returns "no majority"; semantic voting on numerical answers introduces false equivalences. Pick the function that matches the answer space.
- *Confidence over-trust* — a 9-of-10 agreement rate is *not* a 90% probability of correctness; it is the rate at which independent samples of this model agree, which correlates with correctness only on tasks where the model is unbiased. Calibrate against a labelled set before quoting it.

## Implementation Notes

- The single most useful composition is **R1 (or R2) CoT × N + vote** — Wang et al.'s canonical setup. The explicit chain-of-thought is what makes the samples diverse enough for voting to work; without CoT, sampling collapses to local token-level noise.
- Temperature 0.7–0.9 is the working range; tune within that, not outside. top-p ≈ 0.95 is a reasonable secondary lever.
- For multiple-choice, math, classification: literal majority over an extracted answer field. Use a strict extractor (regex, JSON field) — fuzzy extraction is a frequent silent bug.
- For free-form: pick a clustering rule *before* deployment. The Universal Self-Consistency variant (LLM cluster-judge) is the most general option but introduces a judgement call.
- Run N in parallel where the provider supports it; sequential N gives the same answer at N× the wall-clock.
- The **small-model-with-N** vs **large-model-with-1** trade-off is real and often favours the former. Measure on your task before committing to model size.
- Pair with **V9 Bounded Execution** if Self-Consistency is invoked inside a larger loop — N × loop-rounds escalates fast.
- The agreement rate is a usable signal for **abstention**: if agreement falls below a threshold, return "uncertain" rather than the top vote.

## Implementation Sketch

> `LLM = configured session (model + setup + per-call prompt); code = wiring.`

**Composition:** R17 wraps a single Sample session in code-driven fan-out and aggregation, drawing on **R1 Zero-Shot CoT** or **R2 Few-Shot CoT** for the prompt that elicits diverse reasoning traces. When answers are free-form, an optional **Cluster-judge** session implements the **Universal Self-Consistency** variant. R17 commonly composes upward into **S8 Meta-Prompt** as one of its evaluation signals (alongside **V15 LLM-as-Judge**).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Construct prompt P (CoT-augmented) | `code` | R1 / R2 |
| 2 | Fan out: draw N samples at temperature 0.7–0.9 | `LLM × N` | Sample session |
| 3 | Extract a comparable answer from each chain | `code` | |
| 4a | *Literal-match path:* tally answers by exact match | `code` | |
| 4b | *Free-form path:* LLM cluster-judge groups by meaning | `LLM` | Cluster-judge session (USC) |
| 5 | Select the modal answer; report agreement rate as confidence | `code` | |

**Skeleton** — the wiring only:

```
self_consistency(task, N=10, temperature=0.8):
    prompt = build_cot_prompt(task)                  # code  — R1 / R2 composition
    samples = parallel_sample(prompt, N, temperature)  # LLM × N — Sample session
    answers = [extract_answer(s) for s in samples]   # code  — deterministic extractor
    if literal_comparable(answers):
        winner, agreement = majority_vote(answers)    # code
    else:
        winner = cluster_judge(samples)               # LLM   — Cluster-judge (USC)
        agreement = cluster_judge_confidence(samples)
    return winner, agreement
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Sample** | any capable generalist that supports temperature > 0; often a *cheap / small* model run at high N (the economic case for R17) | role (S3); reasoning instruction — "think step by step before answering" (R1) or worked exemplars (R2); output contract (S6) specifying *where* the final answer goes so the extractor can find it; **sampling parameters: temperature 0.7–0.9, top-p ≈ 0.95** | the task instance |
| **Cluster-judge** *(USC variant only)* | capable generalist (must be strong enough to recognise semantic equivalence) | role: *"you are given N candidate answers to the same question; identify the response most consistent with the others"*; output contract: a single chosen index or a list of equivalence groups | the task + the N candidate completions |

**Specialist-model note.** None required — Self-Consistency works with any model that supports temperature > 0 sampling. There is no fine-tune, no classifier, no long-context dependency. The structurally important choice is *economic*, not architectural: the headline cost is N × per-sample, so the right model is often a small one run at high N rather than a frontier model run at N = 1. Test both on the same task; the small-model-with-N configuration frequently wins on cost-adjusted accuracy. The output contract (S6) doing the heavy lifting is the extractor-friendly answer field — making `extract_answer` deterministic is what keeps the aggregator honest.

## Open-Source Implementations

Self-Consistency is typically **implemented inline** rather than imported — the pattern is a dozen lines of fan-out and vote. There is no single canonical library; the canonical reference is the Wang et al. paper.

- **DSPy** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — ships self-consistency as a primitive (`dspy.MultiChainComparison` and majority-vote utilities); the closest thing to a framework primitive.
- **LangChain `RunnableParallel` / LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — parallel-sample-and-aggregate is a documented graph shape, not a named primitive.
- **Anthropic, OpenAI, Google cookbooks** — all three have canonical Self-Consistency examples in their prompt-engineering documentation; these are the most-cited reference implementations.
- **Wang et al. paper** — [arXiv 2203.11171](https://arxiv.org/abs/2203.11171) — the canonical reference; the pseudocode in §3 is the implementation.

> Self-Consistency is an emerging pattern realised mostly inline in application code, not a library — the relevant references are the Wang et al. paper, DSPy's primitive, and the provider cookbooks above.

## Known Uses

- **Math and reasoning benchmarks** — Self-Consistency is the standard reliability lift reported alongside CoT in GSM8K, MATH, SVAMP, and AQuA evaluations.
- **Production multiple-choice and classification pipelines** — used as a confidence layer where the agreement rate triggers human review below a threshold.
- **DSPy programs** — Self-Consistency is a default optimisation step in many DSPy pipelines, applied automatically by the compiler.
- **Code generation with test execution** — N samples are generated and the one passing the most tests is selected (a test-driven majority vote).
- **S8 Meta-Prompt evaluators** — Self-Consistency rate is a common cheap proxy for prompt quality during automated prompt optimisation.

## Related Patterns

- **Sibling of R7 Reflexion** — same goal (reliability through repetition), opposite axis: R7 is *sequential-with-memory* (each attempt informed by the last); R17 is *parallel-with-voting* (each attempt independent). R7 requires an external evaluator; R17 needs only temperature > 0.
- **Sibling of R8 Self-Refine** — same band, different mechanism: R8 is *sequential generate-critique-refine* with the same model; R17 is *parallel-then-vote* with no critique step. R8 fits open-ended tasks; R17 fits tasks with a comparable answer.
- **Composes with R1 Zero-Shot CoT and R2 Few-Shot CoT** — the canonical composition. *Self-Consistency = CoT × N + vote* (Wang et al.); without explicit CoT the samples lack the diversity that makes voting informative.
- **Distinct from R9 Tree of Thoughts and R10 LATS** — those are *search* algorithms (expand, evaluate, prune partial thoughts); R17 is *marginalisation* over fully-independent completed samples. ToT picks a path; R17 integrates over many.
- **Distinct from O5 Evaluator-Optimizer** — O5 uses a *separate* evaluator model to score outputs; R17 has no evaluator, just a tally. O5 catches systematic bias the generating model cannot see in itself; R17 amplifies it.
- **Required by S8 Meta-Prompt** — S8 needs an evaluation signal to rank candidate prompts; Self-Consistency *agreement rate* is one of the two canonical signals (the other being **V15 LLM-as-Judge**). Without R17 or V15, S8 has no objective to optimise.
- **Distinct from S8 Meta-Prompt** — S8 searches over *prompts* for one task; R17 marginalises over *samples* of one prompt. They sit at different levels of the same loop and often appear together.
- **Pairs with V9 Bounded Execution** — N is itself a budget; when Self-Consistency runs inside a larger loop, V9 caps the multiplicative blow-up.
- **Pairs with V15 LLM-as-Judge** — both produce a quality signal; R17 votes within samples of the same model, V15 has a separate model judge. They cover complementary blind spots and are commonly combined.
- **Mutually exclusive with H3 Entropy-Driven Curiosity** — R17 *reduces* entropy by majority vote across N independent samples; H3 *increases* entropy by raising temperature or injecting novelty cues to escape stagnation. The two are direct opposites and must never be applied to the same task simultaneously: H3 firing during an R17 voting round corrupts the sample-diversity calculation the vote depends on, and R17 collapsing entropy on a task where H3 is needed suppresses the only signal H3 can act on. This is **CRITICAL 4** in CONFLICTS.md. Use R17 on tasks with objectively correct answers where consistency = reliability; use H3 on open-ended tasks where diversity = value; never both on one task.

## Sources

- Wang et al. (2022) — "Self-Consistency Improves Chain of Thought Reasoning in Language Models" (arXiv [2203.11171](https://arxiv.org/abs/2203.11171)). The canonical reference.
- Chen et al. (2023) — "Universal Self-Consistency for Large Language Model Generation" (arXiv [2311.17311](https://arxiv.org/abs/2311.17311)). The USC variant for free-form outputs.
- Wei et al. (2022) — "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" (arXiv 2201.11903). The CoT base R17 composes with.
- Lilian Weng — "Prompt Engineering" survey (Self-Consistency section).
- DSPy documentation — `MultiChainComparison` and self-consistency utilities as a framework primitive.
