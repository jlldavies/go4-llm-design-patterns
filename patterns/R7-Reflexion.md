# R7 — Reflexion

> Retry a failed task with a verbal critique of the previous attempt in context — converting an automated pass/fail signal into linguistic feedback that the next attempt can read and act on.

**Also Known As:** Verbal Reinforcement Learning, Self-Reflection Loop, Episodic Refinement, Reflexion Agent. (No named sub-variants; the paper itself distinguishes binary-feedback and scalar-feedback configurations and three actor flavours — ReAct, CoT, Act — but those are configuration choices rather than separate patterns.)

**Classification:** Category III — Reasoning · Band III-C Iterative refinement · the *sequential-with-memory-of-failure* pattern — sibling of R17 Self-Consistency Voting's *parallel-with-voting* and R8 Self-Refine's *sequential-with-self-critique*.

---

## Intent

Improve the reliability of an agent on a task with an automated pass/fail signal by having it retry, with a verbal critique of why the last attempt failed appended to its context — so each retry learns from a linguistic gradient instead of from weights.

## Motivation

A single agent attempt at a hard task is a one-shot bet. When the attempt fails on an objective check — a unit test, a schema validation, a goal-state assertion in a simulated environment — the cheap fix is to retry. Naive retry, though, is just *another roll of the same dice*: the same model, the same prompt, a fresh sample from the same distribution. On a task where the model has a genuine deficit (a misread of the spec, a faulty plan, a buggy loop), naive retry will reproduce the same failure mode in slightly different words.

Shinn et al. (2023) made the operational move: between the failure and the retry, run a *self-reflection* step. The model reads the trajectory of the failed attempt and the failure signal, and writes a short verbal diagnosis — "the previous attempt assumed X, but the error trace shows X is not true; next time check Y before doing Z." That critique enters an **episodic memory** that prepends to the next attempt's context. The retry is not a fresh roll; it is a continuation that has *seen its own past mistake* and been told what to do differently. The verbal form of the feedback is critical because the model's weights do not change between attempts (mechanism 10); the only mechanism by which a prior failure can influence the next attempt is by being written to external storage and re-read as tokens. The headline numbers in the paper — GPT-4 HumanEval lifting from 80% to 91%, AlfWorld task completion from 73% to 97% — are the cost of one or two reflection rounds buying meaningful reliability gains without any fine-tuning. The model is being reinforced *verbally*: the gradient is text, not parameters.

This is structurally distinct from the other reliability patterns in the same band. **R17 Self-Consistency** repeats *in parallel*, with no memory and no critique — diversity across independent samples is the lever; it works without an external feedback signal but cannot fix a systematic blind spot. **R8 Self-Refine** repeats sequentially, but its critique comes from the model alone with no external check — it works on open-ended tasks (writing, summarising) where there is no automatable pass/fail, but it shares all the generator's blind spots. **R7 Reflexion** sits between them: sequential (like R8), but with *external feedback* (like a test runner or a judge) driving the critique. The three patterns share an Intent — reliability through repetition — but resolve it on different axes: parallel-with-voting (R17), sequential-with-self-critique (R8), sequential-with-external-feedback (R7).

The unique contribution is the *verbal* form of the reinforcement. Earlier work on retry-on-failure used scalar reward signals to fine-tune. Reflexion's claim is that for capable models, *the textual form of the failure analysis* — written by the model itself, in its own internal language — is a more usable correction signal than a number. The model already knows *how* to reason; what it lacks is the observation that its last reasoning was wrong and in what specific way.

## Applicability

Use Reflexion when:

- the task has an **automated, objective success criterion** — unit tests, a schema validator, a code executor, a goal-state assertion, a numeric grader, an LLM judge with high agreement to ground truth;
- one-shot accuracy is below the model's ceiling — failures are *diagnosable* rather than fundamental capability gaps;
- you can afford **2–5 retries** in latency and cost, and each retry is a full task re-execution;
- the failures are diverse enough that a verbal critique can identify *what specifically* went wrong (not just "it was wrong").

Do not use it when:

- there is no automated success signal — without external feedback the critique has nothing to anchor on; prefer **R8 Self-Refine** (no external signal, same-model critique) or **O5 Evaluator-Optimizer** (separate judge);
- the task is open-ended / subjective (creative writing, opinion synthesis) — there is no "passed" state to drive the loop; prefer **R8 Self-Refine**;
- one-shot is *already* unreliable in many different ways — sample diversity will help more than memory; prefer **R17 Self-Consistency Voting**;
- the model has a *systematic* deficit on the task — Reflexion's critique is generated by the same model and inherits its blind spots; prefer **O5 Evaluator-Optimizer** with a stronger judge model, or **R10 LATS** for harder search;
- latency is tight — N sequential retries cannot be parallelised away; each round is a full task execution;
- the failure signal is too coarse — a bare "fail" with no trace gives the reflector nothing to diagnose.

## Decision Criteria

R7 is right when the task has an automated pass/fail signal, single-shot is noisy but the failures are diagnosable, and the budget tolerates a small number of sequential retries.

**1. Confirm the pass/fail signal is real and informative.** Reflexion's quality is bounded by the feedback signal. A *binary* pass/fail (tests pass / tests fail) works; a *scalar* score (test pass-rate, judge score) works better; a *bare* "wrong" with no trace is too coarse. If the signal is just "no" with no error message, log, or counter-example, the Self-Reflection step has nothing to diagnose — fall back to **R17 Self-Consistency** or expand the evaluator's output.

**2. Cap retries — N is the primary tuning lever.** Shinn et al. found gains plateau by **N = 3–5 retries** on most tasks. The first reflection captures most of the gain; the second sometimes adds a meaningful lift; rarely more. Set a hard ceiling and treat any unbounded retry loop as a bug. Pair with **V9 Bounded Execution** — without a cap, a stubbornly-wrong query burns the budget. If N = 1 is enough, the task did not need R7 in the first place.

**3. Check for systematic-bias risk.** The Self-Reflection step is *the same model* that produced the failed attempt. On a task where the model is reliably wrong in the same way, the reflection will rationalise the same wrongness — *refinement theatre*. Test on a labelled set: do failures cluster on the same error type after N reflections, or do they spread? Clustered failures after N rounds means R7 is not breaking through the blind spot — switch to **O5 Evaluator-Optimizer** (different judge model) or **R10 LATS** (search rather than retry).

**4. Cost the retry budget.** Each retry is a *full task execution* — actor call(s), tool calls, evaluator call, plus the reflection call. Total cost is roughly **N $\times$ (per-task cost) + N $\times$ (reflection cost)**. At N = 3 you are paying ~3–4$\times$ one-shot. Compare to **R17 Self-Consistency** at the same N: R17 parallelises (lower wall-clock latency but same dollar cost), R7 does not. If your bottleneck is latency rather than dollars, prefer R17; if it is *quality* on a task with an automated check, R7 wins.

**5. Decide what persists.** Reflexion stores critiques in an *episodic memory buffer* across retries within a task. If you want the critiques to outlive the task — to inform the *next* user's similar task, or the same user's next session — promote the buffer to durable storage. That is the **H2 Episodic Self-Improvement** pattern in Humanizers; R7 is its in-task engine. Without H2, the lessons die at task end.

**Quick test — R7 is the right pattern when:**

- the task has an automated pass/fail or scalar feedback signal that returns an *informative* failure description, *and*
- single-shot accuracy is below the model's ceiling but failures look diagnosable (not all the same mode), *and*
- the budget tolerates 2–5 sequential retries at full task cost, *and*
- a verbal critique can plausibly point at *what* to change for the next attempt.

If there is no automated signal, use **R8 Self-Refine**. If failures are scattered and the model is unbiased, **R17 Self-Consistency** may be cheaper at comparable quality. If the same wrong mode recurs across reflections, the model has a systematic blind spot and you need **O5 Evaluator-Optimizer** with a separate judge or **R10 LATS** with explicit search.

## Structure

```
                                            ┌── episodic memory (verbal critiques) ──┐
                                            │                                         │
                                            ▼                                         │
   Task ──▶ Actor ──▶ trajectory ──▶ Evaluator ──pass──▶ Answer                       │
                                         │                                            │
                                         fail (+ signal: trace / score)               │
                                         │                                            │
                                         ▼                                            │
                                  Self-Reflection ──▶ verbal critique ────────────────┘
                                         │
                                         ▼
                                  retry (N < N_max) ───── back to Actor
                                         │
                                  N ≥ N_max ──▶ best-effort Answer (or escalate)
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Actor** | attempting the task end-to-end, possibly via an inner reasoning pattern (R4 ReAct, R1 CoT, R13 CodeAct) | task + episodic memory of past critiques $\to$ completed trajectory + candidate answer | judge its own attempt — that is the Evaluator's job; an Actor that grades itself loses the external signal that distinguishes R7 from R8. |
| **Evaluator** | producing the pass/fail (or scalar) feedback signal that drives the loop | trajectory + candidate answer $\to$ pass / fail (+ failure description) | be the same model session as the Actor; the signal must be external — a test runner, a schema validator, a judge model, an environment, or an LLM-as-Judge (V15) with a separate prompt and ideally a different model. |
| **Self-Reflection (LLM)** | writing the verbal critique that converts the failure signal into actionable text | failed trajectory + failure signal $\to$ short verbal critique ("what went wrong, what to do differently") | rewrite the answer or attempt the task itself — its only output is *diagnosis*. A reflector that solves the task collapses into the Actor. |
| **Episodic memory** | accumulating critiques across retries within the task | sequence of critiques $\to$ text buffer prepended to the Actor's next prompt | grow without bound — keep only the last K critiques (typically 1–3); stale critiques drown out current signal. (Promote to durable storage via **H2** if cross-task persistence is wanted.) |
| **Loop controller** | counting retries, terminating on pass or N_max | (attempt result, retry count) $\to$ continue / stop | hide a non-terminating loop; the cap N_max is mandatory (V9). |

Five narrow responsibilities. The pattern's reliability depends on the Evaluator being *genuinely external* to the Actor — same model is acceptable, but the *signal* must come from outside the Actor's own judgment. Collapse the Evaluator into the Actor and R7 degenerates into R8 with extra steps.

## Collaborations

The Actor attempts the task — composing whatever inner reasoning pattern fits (most often **R4 ReAct** for tool-using agents, **R1 / R2 CoT** for reasoning tasks, **R13 CodeAct** for code-generation tasks). Its trajectory and candidate answer go to the Evaluator, which runs the automated check — executing unit tests, validating a schema, asserting a goal state, scoring with a judge. On *pass*, the loop terminates and the answer is returned. On *fail*, the Evaluator hands the trajectory and the failure description (error trace, failing test, judge critique) to the Self-Reflection session. The reflector reads the failure and writes a short verbal critique aimed at the *next* attempt. The critique is appended to the episodic memory buffer. The Loop controller increments the retry counter; if N < N_max, the Actor runs again with the memory buffer prepended to its prompt; if N $\geq$ N_max, the loop terminates with the best-effort attempt and (optionally) escalates. The episodic memory persists across the loop's iterations but, in vanilla R7, dies at task end; promoting it to durable storage is the **H2 Episodic Self-Improvement** move.

## Consequences

**Benefits**
- Substantial accuracy gains on tasks with automated checks — Shinn et al. report GPT-4 HumanEval 80% $\to$ 91%, AlfWorld 73% $\to$ 97% with a few rounds of reflection; the gain comes essentially free of fine-tuning.
- The verbal critiques are *inspectable* — operators can read why the agent thought it failed, which is valuable for debugging, evaluation, and trust calibration. Compare to an opaque scalar reward.
- Provides a natural log of *what the agent learned* — directly promotable into **H2 Episodic Self-Improvement** for cross-session learning.
- Works with any capable model that supports long-enough context to carry critiques; no fine-tune required.

**Costs**
- **N $\times$ full-task cost** plus N $\times$ reflection cost — the headline price. At N = 3, expect ~3–4$\times$ one-shot cost.
- Latency scales linearly in N: retries are sequential by construction (the next attempt depends on the previous critique). Cannot be parallelised the way R17 can.
- Engineering surface: an external Evaluator is required; without it the pattern collapses. Building a reliable Evaluator is often the hardest part.
- Episodic memory inflates context with each round — for very long actor trajectories, the buffer is non-trivial. The episodic memory buffer is in-context storage (mechanism 9) — the most expensive tier. Each appended critique increases the Actor's prompt length; every subsequent Actor LLM call then pays O(seq_len²) attention cost (mechanism 2) over the entire prefix including all prior critiques. At K=3 critiques with average 100 tokens each, a 300-token buffer prefix imposes ~10% overhead on a 1000-token context but grows super-linearly as context grows. Trim aggressively (last 1–3 critiques) to bound this.

**Risks and failure modes**
- *Refinement theatre.* The Self-Reflection step produces a plausible-sounding critique that does not identify the actual problem; the next attempt fails for the same reason in slightly different words. Symptom: the same error type across rounds. Mitigation: log critiques and review them; if the model's reflection is shallow, switch to **O5 Evaluator-Optimizer** with a stronger external judge.
- *Shared blind spot.* Actor and Reflector are typically the same model; on a task where that model has a systematic weakness, the reflection inherits it. Mitigation: use a *different model* for the Reflection session — the cost is small and the bias-reduction is real.
- *Loop non-termination.* Without N_max the agent can chase its tail on a hard query indefinitely. V9 Bounded Execution is non-optional.
- *Stale memory poisoning.* A wrong critique persisted across retries can steer subsequent attempts further away from the correct answer. Mitigation: keep the buffer short (last 1–3 critiques), and consider letting the reflector explicitly *revise* prior critiques rather than only appending.
- *Evaluator brittleness.* If the automated check is wrong (a flaky test, a permissive validator), the loop terminates on a false pass or grinds on a false fail. The Evaluator is the loop's ground truth — invest in it.

## Implementation Notes

- The single most common composition is **R7 wrapping R4 ReAct** as the Actor — Shinn et al.'s default for agentic tasks. For coding tasks the Actor is more often **R13 CodeAct** (or vanilla code generation); for pure reasoning tasks, **R1 / R2 CoT**.
- The Evaluator is *the loop's ground truth*. For code tasks, a test runner with a real interpreter; for structured-output tasks, a schema validator; for environment tasks, a goal-state assertion; for free-form tasks, an LLM judge (V15 LLM-as-Judge), ideally a *different* model from the Actor. A flaky Evaluator is worse than no R7 at all — it terminates on false passes.
- Keep N_max small — 3 to 5. Most gain is captured in the first reflection; gains plateau quickly. Wire to **V9 Bounded Execution**.
- Trim the episodic memory aggressively. The *last 1–3 critiques* is the working setting; long histories degrade more than they help. The reflector should focus on *this* failure, not the whole history.
- Use a *separate model* for the Self-Reflection session if the Actor's blind spots are a worry — often a small fast generalist with a tight reflection prompt is better than the Actor reflecting on itself.
- Treat the verbal critique as data. Log every reflection to **V14 Trajectory Logging** — the trace *is* the artefact of interest. Critiques that look meaningless on inspection are a sign the pattern is not earning its keep.
- Cap critique length (1–3 sentences is typical) — long reflections drift into restating the task and dilute the signal.
- For cross-session learning, persist the buffer to durable storage and re-inject relevant past critiques into new sessions. That is **H2 Episodic Self-Improvement** — Reflexion is its in-task engine.
- Pair with **R17 Self-Consistency** orthogonally: on the *final* attempt at N_max, draw N samples and vote, in case the issue is sample noise rather than systematic.

## Implementation Sketch

> `LLM = configured session (model + setup + per-call prompt); code = wiring.`

**Composition:** R7 wraps an inner Actor (most often **R4 ReAct**, sometimes **R13 CodeAct** or **R1 / R2 CoT**) in a retry loop driven by an external Evaluator, with a Self-Reflection session between attempts. The pattern composes with **V9 Bounded Execution** (the retry cap is non-optional), **V14 Trajectory Logging** (the loop's value is the inspectable trace), and **V15 LLM-as-Judge** when the Evaluator is itself an LLM. Promotion of the episodic memory to durable storage is the **H2 Episodic Self-Improvement** composition.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Actor attempts the task, prepending episodic memory | `LLM` | Actor session (composes R4 / R13 / R1) |
| 2 | Evaluator runs the automated check | `code` (or `LLM` if V15) | Evaluator (V15 if LLM) |
| 3 | Branch — pass $\to$ return; fail $\to$ continue | `code` | |
| 4 | Self-Reflection writes a verbal critique of the failure | `LLM` | Reflection session |
| 5 | Append critique to episodic memory (trim to last K) | `code` | |
| 6 | Increment retry counter; if N < N_max loop to 1 | `code` | V9 |
| 7 | At N_max: return best-effort answer (or escalate) | `code` | V1 (optional) |

**Skeleton** — the wiring only:

```
reflexion(task, N_max=3):
    memory = []                                       # code  — episodic buffer
    for n in range(N_max):
        attempt = actor(task, memory)                  # LLM   — Actor session (composes R4 / R13 / R1)
        verdict, signal = evaluator(task, attempt)     # code  — or LLM (V15) if judge-based
        if verdict == PASS:
            return attempt                             # success exit
        critique = self_reflect(task, attempt, signal) # LLM   — Reflection session
        memory.append(critique)
        memory = memory[-K:]                            # code  — trim to last K (typically 1–3)
    return attempt                                     # V9-bounded exit; best-effort
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Actor** | the system's main generalist; whatever model the inner reasoning pattern requires (capable enough for the task) | role (S3); inner-pattern setup (R4 ReAct's thought/action/observation format, or R13 CodeAct's code-action format, or R1/R2 CoT trigger); output contract (S6); **and** the instruction *"the following critiques from previous attempts apply — read them before acting: {memory}"* | the task instance + the current episodic memory |
| **Self-Reflection** | a capable generalist; **ideally a different model from the Actor** to reduce shared blind spots — even a smaller fast model works well, the job is diagnosis not generation | role: *"you are given a failed attempt at a task and its failure signal; write a short verbal critique (1–3 sentences) identifying what went wrong and what the next attempt should do differently"*; output contract: bounded length, no restating the task, no producing a new answer | the task + the failed trajectory + the failure signal (error trace / failing test / judge critique) |
| **Evaluator** *(only if LLM-based; V15)* | a *separate* model from the Actor — using the same model collapses the external-signal property | role: *"you grade an attempt at this task against this criterion"*; the criterion / rubric; output contract (PASS / FAIL + one-line justification) | the task + the attempt |

**Specialist-model note.** No fine-tuned specialist is required by the pattern itself — Shinn et al.'s headline numbers are on stock GPT-4. Two structural choices change everything:

- **The Evaluator must be genuinely external.** For code tasks this is *a real test runner with a real interpreter* (not an LLM guessing whether tests pass); for environments it is *the environment's own goal-state assertion*; for free-form outputs it is an **LLM-as-Judge (V15)** session running on a *different model* from the Actor. An Evaluator that shares the Actor's blind spots is not an evaluator.
- **The Reflection session is best run on a different model from the Actor.** Cost is small (the reflection is short); the bias reduction is real. The prompt artefact doing the heavy lifting is the *bounded-length, diagnosis-only* output contract — long reflections drift into refinement theatre.

## Open-Source Implementations

- **Reflexion (official)** — [`github.com/noahshinn/reflexion`](https://github.com/noahshinn/reflexion) — Noah Shinn et al.'s reference implementation for the NeurIPS 2023 paper. Includes runnable experiments on HotPotQA (reasoning), AlfWorld (decision-making), and LeetcodeHardGym (programming), with the full set of agent / reflexion-strategy combinations evaluated in the paper. MIT licensed.
- **LangGraph Reflexion example** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the framework's canonical tutorial implementation of the Reflexion graph (actor $\to$ evaluator $\to$ reflector $\to$ loop) is one of the most-cited reference graphs; the closest match to the chain shown above for production reuse.
- **langgraph-reflection** — [`github.com/langchain-ai/langgraph-reflection`](https://github.com/langchain-ai/langgraph-reflection) — a prebuilt LangGraph package wrapping the reflection-style architecture (main agent + critique agent + loop) for direct reuse.
- **DSPy** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — reflection / refine modules can be composed to build Reflexion-shaped programs; the framework treats the loop as a compilable structure rather than a primitive.

## Known Uses

- **Code-generation agents with test-driven loops** — Reflexion's HumanEval setup (generate $\to$ run tests $\to$ reflect on failures $\to$ regenerate) is now a standard architecture in coding-agent stacks. Variants appear in Claude Code, Devin-style systems, and other test-driven agent frameworks where unit tests are the Evaluator.
- **Environment-based agent benchmarks** — AlfWorld, WebArena, and similar agentic benchmarks have Reflexion-shaped baselines where the environment provides the pass/fail signal and the agent reflects between episodes.
- **LangGraph production agents** — Reflexion-style graphs (actor + critic + retry loop) are a common LangGraph deployment shape, especially for tool-using agents with downstream validators.
- **Research-agent reflection loops** — agents that draft $\to$ critique $\to$ revise with an external citation-checker or fact-checker as the Evaluator follow the R7 shape.
- **Episodic-memory agents (H2 promotion)** — long-running personal-assistant and process-automation agents that persist Reflexion critiques across sessions to learn from recurring failure modes.

## Related Patterns

- **Sibling of R17 Self-Consistency Voting** — same goal (reliability through repetition), opposite axis. R7 is *sequential-with-memory-of-failure* (each retry informed by a verbal critique of the last); R17 is *parallel-with-voting* (each sample independent, voted). R7 requires an automated pass/fail signal; R17 needs only temperature > 0. They are complementary: on hard tasks, R7 with R17 on the final attempt (vote across N samples after N_max reflections) covers both axes.
- **Sibling of R8 Self-Refine** — both iterate sequentially with a critique step; the difference is the signal source. R7's critique is anchored by an *external* Evaluator (test runner, judge, environment); R8's critique comes from the same model with no external check. R8 fits open-ended tasks where there is no pass/fail; R7 fits tasks where there is.
- **Composes with R4 ReAct** — the most common Actor inside R7. ReAct provides the per-attempt reasoning loop; Reflexion provides the across-attempt learning loop. Shinn et al.'s default agentic configuration.
- **Composes with R13 CodeAct** — for code-generation tasks the Actor writes code, the Evaluator is a test runner, the Reflection reads stack traces. The natural pairing for test-driven agents.
- **Composes with R1 / R2 CoT** — for pure reasoning tasks (HotPotQA, math) the Actor is a CoT chain and the Evaluator is an answer-checker.
- **Required by H2 Episodic Self-Improvement** — H2 is Reflexion's verbal critiques *persisted across sessions* as durable episodic memory. R7 is the in-task engine that produces what H2 stores. Without R7 (or an equivalent reflection mechanism), H2 has no critiques to persist. The mechanistic reason to promote critiques to durable storage (mechanism 9/10) is that in-context storage pays O(n²) cost on every Actor call; external storage (vector index or exact KV store) pays retrieval cost only once per session and then injects only the relevant entries into context. The model's weights do not change between sessions (mechanism 10) — the only way critiques survive a session boundary is by being written to external storage and read back.
- **Pairs with V9 Bounded Execution** — N_max is non-optional. Any R7 loop without an explicit retry cap is a bug.
- **Pairs with V14 Trajectory Logging** — the verbal critiques and full trajectories are the pattern's inspectable artefact; logging them is what lets operators tell *learning* from *refinement theatre*.
- **Composes with V15 LLM-as-Judge** — when the Evaluator is itself an LLM (free-form outputs, no test runner), V15 supplies it. The judge must be a *different* session from the Actor.
- **Composes with K10 Long-Term Memory (episodic variant)** — the episodic-memory buffer can be promoted to K10's persistent store; the Karpathy-framing version is K12 if the critiques are curated into structured notes.
- **Distinct from O5 Evaluator-Optimizer** — O5 is an architectural pattern (separate optimiser and evaluator *agents*, possibly different models); R7 is a reasoning pattern (one agent retries with verbal memory). O5 catches systematic bias R7 cannot; R7 is lighter-weight and self-contained.
- **Distinct from R10 LATS** — LATS *searches* a tree of partial trajectories with MCTS; R7 *retries* complete trajectories sequentially. LATS subsumes R7 conceptually but is much more expensive — use R7 first; escalate to LATS only when R7 plateaus.

## Sources

- Shinn et al. (2023) — "Reflexion: Language Agents with Verbal Reinforcement Learning" (arXiv [2303.11366](https://arxiv.org/abs/2303.11366); NeurIPS 2023). The canonical reference. Key results: GPT-4 HumanEval 80% $\to$ 91%, AlfWorld 73% $\to$ 97%, HotPotQA gains over ReAct.
- Yao et al. (2022) — "ReAct: Synergizing Reasoning and Acting in Language Models" (arXiv [2210.03629](https://arxiv.org/abs/2210.03629)). The Actor's most common inner pattern.
- Madaan et al. (2023) — "Self-Refine: Iterative Refinement with Self-Feedback" (arXiv [2303.17651](https://arxiv.org/abs/2303.17651)). The sibling sequential-refinement pattern without an external signal.
- Wang et al. (2022) — "Self-Consistency Improves Chain of Thought Reasoning" (arXiv [2203.11171](https://arxiv.org/abs/2203.11171)). The sibling parallel-sampling pattern.
- LangGraph Reflexion documentation and reference implementation — the production realisation of the loop.
- Lilian Weng — "LLM Powered Autonomous Agents" (the self-reflection section).
