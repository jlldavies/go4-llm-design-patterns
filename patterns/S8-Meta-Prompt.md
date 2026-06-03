# S8 — Meta-Prompt

> Use the LLM itself to generate or refine the prompts it will run on, driven by an external evaluation signal, so prompt engineering becomes a measured optimisation loop rather than human guesswork.

**Also Known As:** Auto-Prompting, Prompt Optimisation, Self-Generated Prompts, Automatic Prompt Engineering, Recursive Meta Prompting.

**Classification:** Category I — Signal · a *meta-level* pattern — it produces the Signal-layer artefacts (system prompts, instructions, exemplars) that the other S-patterns assume a human wrote.

---

## Intent

Replace hand-crafted prompt engineering with a measured generate-evaluate-select loop, in which an LLM proposes candidate prompts, an evaluator scores them against a task signal, and the best candidate is kept and iterated on.

## Motivation

Every other Signal pattern — S1 zero-shot, S2 few-shot, S3 persona, S4 instruction decomposition, S6 output template — assumes a human sat down and *wrote* the prompt. That human is doing search by intuition: they try a phrasing, run a few examples, eyeball the outputs, change a word, try again. The search space is enormous, the signal is noisy, and the result rarely generalises beyond the inputs the human happened to think of. Two failure modes follow directly:

- **The plateau.** After a few rounds the human stops finding gains, not because the optimum is reached but because the next improvement is non-obvious — a re-ordering of clauses, a different verb, an exemplar the human did not think to include. Manual prompt engineering converges to a local maximum bounded by the engineer's imagination.
- **The generalisation gap.** A prompt tuned on a handful of cases overfits to those cases; production traffic exposes failures the engineer never saw. The "prompt" is really a hand-tuned regression on the test set the engineer happened to look at.

The fix is to make prompt construction a proper optimisation: define a search space (templates, instructions, exemplars), define an objective (a measurable score over a held-out set), and let a machine search. The LLM itself is the natural proposer — it knows what English sentences are well-formed and what instructions are coherent. The evaluator is a separate signal — graded examples, R17 self-consistency, V15 LLM-as-Judge, or a unit-test pass rate. The pattern is the loop that closes between them.

This is a *meta*-pattern. Other S-patterns shape the prompt to the task; S8 shapes the *process that produces* the prompt. Its forces are different: it needs an evaluation signal (without which no candidate can be ranked); it pays a curator-style call budget for every iteration; and its generated prompts can be fragile or overfit in ways human-written prompts are not. It earns its own number because no other pattern has these forces — they are all downstream consumers of the artefact S8 produces.

## Variants

The variants differ in *what is being optimised* and *how the search is run*:

- **APE — Automatic Prompt Engineer.** Instruction-level optimisation: the LLM proposes candidate instructions; each is scored on a graded dataset; the highest-scoring is kept. A black-box random / iterative search over instruction text. (Zhou et al., 2022.)
- **DSPy programs (MIPROv2, COPRO, GEPA, SIMBA).** Module-level optimisation: prompts are not strings but compiled artefacts of a declarative program; the optimiser tunes instructions *and* few-shot demonstrations *and* their composition jointly, using Bayesian optimisation, coordinate ascent, or reflective LLM-driven proposal. The mature production form of the pattern. (Khattab et al., 2023.)
- **Meta Prompting / Recursive Meta Prompting (RMP).** A scaffold-level optimisation: a single example-agnostic meta-prompt guides the LLM to generate task-specific prompts; in the recursive variant, the LLM also refines its own meta-prompt against task feedback. (Zhang et al., 2023.)
- **AutoPDL.** Pattern-level optimisation: the search space is *combinations of prompting patterns* (ReAct, CoT, ReWOO, etc.) plus their demonstrations, expressed as PDL programs; successive halving navigates the space. Source-to-source: input and output are both runnable PDL programs. (Spiess et al., 2025.)

All four share the same core — propose, evaluate, select, iterate — and differ only in the granularity of the search space (instruction string $\to$ module $\to$ scaffold $\to$ pattern composition). They are one pattern, four points on a granularity axis.

## Applicability

Use Meta-Prompt when:

- you have a measurable evaluation signal — graded examples, a verifier, an LLM judge, or unit tests — and can run it cheaply against many candidate prompts;
- the prompt must generalise across a distribution of inputs, not just please a few favourite examples;
- the production task is high-volume enough that a one-off optimisation cost amortises across many calls;
- manual prompt engineering has plateaued and you suspect non-obvious wins remain.

Do not use when:

- there is no evaluation signal — without R17 self-consistency, V15 LLM-as-Judge, or graded data you cannot rank candidates, and the pattern degenerates to "the LLM wrote a prompt, we hope it is good";
- the task is one-off or low-volume — a careful S2 / S4 / S6 prompt by a human is cheaper than the optimisation budget;
- the latency budget is real-time and the optimisation must happen per query — S8 is an *offline* pattern that produces a *deployed* prompt;
- the task definition itself is unstable — optimising a prompt against a moving target produces brittle artefacts.

## Decision Criteria

S8 is right when you have an evaluation signal and a task volume that justifies an offline optimisation budget.

**1. Confirm the evaluation signal.** You need a function `score(prompt, dataset) → number`. The score can come from:
- graded examples (gold labels, BLEU / accuracy / exact-match) — strongest signal;
- **R17 Self-Consistency Voting** (consensus rate as proxy);
- **V15 LLM-as-Judge** with a stable rubric;
- a downstream verifier (unit tests, type checks, sandboxed execution).

If you cannot produce *any* of these, stop. S8 cannot function — pick the best prompt by hand using S2 / S4 / S6 and revisit when a signal exists.

**2. Cost the optimisation budget.** A typical S8 run is **20–200 candidate prompts $\times$ N evaluation cases $\times$ evaluator-call cost**. Cap before starting: hours of LLM time, dollar budget, or candidate count. Pair with **V9 Bounded Execution** — an unbounded optimisation loop is the canonical waste. Note that the cost compounds super-linearly: the O(n²) attention computation (mechanism 2) means a candidate prompt of length p evaluated against an input of length q costs O((p+q)²) per call, not O(p+q). Verbose candidates — which the optimiser tends to generate — are penalised geometrically in the evaluation pass. Set a maximum candidate token length as a constraint on the Proposer, not just as a quality concern.

**3. Estimate amortisation.** Optimisation cost C, per-call savings or quality gain Δ, expected calls N. Run S8 only if `C ≪ Δ × N` — i.e. the deployed prompt will be used many times. Rule of thumb: N $\geq$ 10,000 calls of the optimised prompt for the budget to break even on a typical reasoning task.

**4. Pick the granularity.**
- Instruction text only $\to$ **APE** (simplest, off-the-shelf).
- Instructions + few-shot demonstrations in a multi-step program $\to$ **DSPy** (production-grade; the default if the system is non-trivial).
- A reusable scaffold for a family of tasks $\to$ **Meta Prompting / RMP**.
- A combination of prompting patterns (which Reasoning pattern to use, with what demonstrations) $\to$ **AutoPDL**.

**5. Overfit risk.** Hold out an evaluation set the optimiser never sees. Score the final prompt on it. If held-out performance is materially below the optimisation score, the candidate is overfit — discard and either expand the optimisation set or coarsen the search space.

**Quick test — S8 is the right pattern when:**

- an evaluation signal exists and is cheap enough to run against many candidates, *and*
- the deployed prompt will be called enough times to amortise the optimisation budget, *and*
- a held-out set can validate that the optimised prompt generalises, *and*
- manual prompt engineering has either plateaued or is too costly to scale to the surface area.

If no evaluation signal exists, stay manual — write the prompt with S2 / S4 / S6 / S9. If volume is low, stay manual — the optimisation budget will never amortise. If the search space is small (one or two parameters), grid-search by hand rather than building the loop. If the underlying issue is that the *task* is ill-defined, fix the task before optimising the prompt.

## Structure

```
   Task description + graded dataset + scoring function
                       │
                       ▼
   ┌──────────────── Proposer (LLM) ──────────────┐
   │  emits K candidate prompts (instructions,    │
   │  exemplars, scaffolds, or pattern combos)    │
   └──────────────────────┬───────────────────────┘
                          │
                          ▼
                  Evaluator (per candidate)
                  ─ run candidate against eval set
                  ─ score via labels / R17 / V15 / verifier
                          │
                          ▼
                  Selector — keep top-k, optionally
                  refine via LLM critique of failures
                          │
                          ▼
              ┌───── more rounds? ─────┐
             yes                       no
              │                         │
              ▼                         ▼
   feed top-k back to Proposer    Held-out validation
                                         │
                                         ▼
                                  Deployed prompt
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Task spec** | what "good" means | description + graded dataset + scoring function $\to$ optimisation problem | be ambiguous — a fuzzy spec produces fuzzy prompts. If the spec cannot be written, S8 should not be run. |
| **Proposer (LLM)** | generating candidate prompts | spec + (optionally) prior top-k and their failures $\to$ new candidates | score its own outputs. The Proposer that also evaluates has no incentive to admit a candidate is bad. |
| **Evaluator** | scoring each candidate against the dataset | candidate prompt + eval set $\to$ numeric score | propose candidates, and must be stable across runs. A drifting evaluator makes optimisation meaningless. |
| **Selector** | keeping the best, discarding the rest | scored candidates $\to$ top-k carried to next round | invent new candidates (that is the Proposer's job); it only ranks and prunes. |
| **Held-out validator** | guarding against overfit | final candidate + a set the optimiser never saw $\to$ pass/fail | be the same data the Evaluator used. Reusing it collapses the validation. |
| **Optimisation loop** *(code)* | bounding cost and iterations | rounds + budget $\to$ terminate signal | run unbounded — pair with V9 Bounded Execution by construction. |

Six narrow responsibilities. The pattern's central reliability move is the *Proposer–Evaluator separation*: the Proposer generates, the Evaluator scores, and neither can do both. Without that separation the loop reduces to "ask the LLM if its own prompt is good", which is the failure mode the pattern was invented to avoid.

## Collaborations

A task spec arrives: a description, a graded dataset, and a scoring function. The Proposer reads the spec and emits K candidate prompts (initially just from the description; in later rounds, conditioned on the previous round's top performers and the cases they failed). The Evaluator runs each candidate against the eval set and produces a score. The Selector keeps the top-k and discards the rest. If the optimisation budget allows another round and the score is still climbing, the top-k feed back into the Proposer along with their failure cases — the Proposer's next candidates are informed by what did and did not work. When the budget is exhausted or the score plateaus, the best candidate is sent to the Held-out validator. If it passes, that prompt is deployed; if it fails, the candidate is overfit and either the optimisation set is expanded or the search space coarsened. The whole loop is bounded by V9.

## Consequences

**Benefits**
- Finds prompt structures human engineers do not — re-orderings, exemplar choices, scaffolds beyond intuition.
- Produces a measured, defensible artefact: the score on the held-out set is the prompt's spec sheet.
- Scales to surface areas (many tasks, many sub-prompts, many model versions) where human prompt engineering does not.
- The optimised prompt is portable across model versions if re-run on each — keeping pace with model upgrades becomes a process, not an emergency.

**Costs**
- Optimisation budget: 20–200 candidates $\times$ eval-set size $\times$ evaluator-call cost per round.
- Evaluation infrastructure is mandatory — graded data, R17, V15, or a verifier; building this often dominates the project.
- Generated prompts are typically verbose; readability and brand voice are easily sacrificed to score.
- Re-optimisation needed on model upgrades, task drift, or evaluation-rubric changes.

**Risks and failure modes**
- *No-signal collapse.* Run without a real evaluation signal, the loop selects on noise — outputs look optimised but generalise no better than random.
- *Overfit prompts.* The optimiser memorises the evaluation set; held-out performance is materially worse.
- *Evaluator drift.* If the Evaluator is an LLM judge whose rubric drifts mid-run, scores from different rounds are not comparable and the "best" candidate is illusory.
- *Reward hacking.* The Proposer discovers prompt patterns that score well on the evaluator without actually solving the task — e.g. prompts that exploit the judge's biases.
- *Cost runaway.* Without V9, hard problems trigger endless rounds of marginal improvement at material cost.
- *Brittle artefacts.* The final prompt may be unreadable, longer than necessary, or sensitive to model version — paying for one re-optimisation per model upgrade is the price.

## Implementation Notes

- The Evaluator is the load-bearing component. Spend evaluation effort *before* running the loop, not after — a weak Evaluator selects weak prompts confidently.
- For tasks with gold labels, graded accuracy is the strongest signal. For open-ended tasks, V15 LLM-as-Judge with a stable, versioned rubric is the practical fallback.
- Use a different model for the Evaluator than the Proposer when possible — same-model evaluation has correlated blind spots.
- Hold out a validation set the optimiser never sees. Report final performance on that set, not the optimisation score.
- Start with the simplest variant (APE-style instruction search) before reaching for DSPy / AutoPDL. The marginal value of more sophisticated search shrinks if the eval signal is weak.
- Cap rounds and candidates *explicitly* (V9 Bounded Execution). Plateau detection is a useful additional stop: end the loop when the top-k score does not improve over R rounds.
- Track Proposer / Evaluator / model versions alongside the deployed prompt — a prompt optimised against GPT-X is not necessarily good on GPT-Y. Treat prompts as build artefacts with provenance. Design the optimised prompt as a stable cacheable prefix (mechanism 5). For Anthropic deployment: if the fixed portion of the system prompt exceeds 1024 tokens and remains stable across calls, it qualifies for provider prefix caching (~10% of normal input cost per hit, TTL ~5 min). The optimisation loop should evaluate candidate prompts not only on task score but on whether their stable prefix length meets the caching threshold — a lower-scoring but cache-friendly prompt may be more economical at production scale.
- For DSPy-style multi-step programs, optimise each module against its own signal; do not propagate an end-to-end score into a per-module optimiser — credit assignment becomes intractable.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** S8 chains a Proposer LLM with an Evaluator LLM (or verifier) in a code-driven loop, bounded by **V9 Bounded Execution**. The Evaluator is typically **R17 Self-Consistency Voting** or **V15 LLM-as-Judge** — without one, the loop has no signal. The Proposer's own setup is itself Signal-layer work (S3 role, S5 constraint, S6 output template forcing a list of candidate prompts).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Build the task spec: description, eval set, held-out set, scoring function | `code` | |
| 2 | Proposer emits K candidate prompts | `LLM` | Proposer session |
| 3 | For each candidate, run it on the eval set | `code` | |
| 4 | Score each candidate's outputs | `LLM (or rule)` | Evaluator session — R17 or V15 |
| 5 | Selector keeps top-k by score | `code` | |
| 6 | Budget check — another round? | `code` | V9 |
| 7 | If yes: pass top-k + failure cases back to step 2 | `code` | |
| 8 | If no: run the best candidate on the held-out set | `code` | |
| 9 | Validate generalisation gap; deploy or expand optimisation set | `code` | |

**Skeleton** — the wiring only; each `# LLM` line is a configured session, not code:

```
meta_prompt(spec):
    top_k = []
    for round in range(max_rounds):                 # code — V9 bound
        candidates = Proposer(spec, top_k) ──────── # LLM  — K candidates
        scored = []
        for c in candidates:
            outputs = run(c, spec.eval_set)         # code
            score   = Evaluator(c, outputs) ─────── # LLM (or rule) — R17 / V15
            scored.append((c, score))
        top_k = Selector(scored, k)                 # code
        if plateau(top_k): break                    # code
    best = top_k[0]
    holdout_score = run_and_score(best, spec.holdout_set)  # code — R17/V15
    return best if holdout_score >= threshold else FAIL
```

**The LLM sessions.** Each `LLM` step is a configured session whose setup is loaded once, before the first call.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Proposer** | a capable generalist; long-context helps when feeding back failure cases | role: *"you generate candidate prompts for a downstream LLM to solve a task"*; the task description; the candidate-prompt output schema (numbered list, one per line); editing rules (must keep within token budget, must address listed failure modes when given) | the previous round's top-k prompts and the specific eval cases they failed on (or empty on round 1) |
| **Evaluator** | a generalist *different from* the Proposer when feasible; for graded data, no LLM needed — a deterministic scorer suffices | role: *"you score a candidate prompt's output against a rubric"*; the rubric (versioned); the output contract (numeric score 0–10, plus a one-sentence justification); the dataset's reference answers if available | the candidate prompt, the eval input, and the candidate's output |
| **Selector** *(optional LLM)* | small fast generalist, *or* deterministic top-k | role: pick the top-k; optionally cluster near-duplicate candidates to preserve diversity | the scored list |

**Specialist-model note.** No fine-tune is strictly required, but two structural choices change everything. (a) The **Proposer and Evaluator should be different sessions, ideally different models** — shared models share blind spots, and a Proposer that learns the Evaluator's preferences is the reward-hacking failure mode. (b) The **Evaluator is the load-bearing dependency** — if no automated scoring function exists, S8 cannot run; building the eval (often graded data, sometimes a fine-tuned judge) is the actual cost of adopting the pattern. The DSPy variant additionally requires the program-as-code substrate: the prompts being optimised are not free text but compiled artefacts of a declarative program.

## Open-Source Implementations

- **DSPy** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — Stanford NLP's declarative LM-programming framework; optimisers include MIPROv2, COPRO, SIMBA, GEPA. The mature, production-grade form of the pattern.
- **APE — Automatic Prompt Engineer** — [`github.com/keirp/automatic_prompt_engineer`](https://github.com/keirp/automatic_prompt_engineer) — the original instruction-level prompt search; treats instructions as programs, optimises by black-box search over candidate strings against a chosen score function (Zhou et al., 2022).
- **Meta Prompting** — [`github.com/meta-prompting/meta-prompting`](https://github.com/meta-prompting/meta-prompting) — official implementation of "Meta Prompting for AI Systems" (arXiv 2311.11482), including the Recursive Meta Prompting variant.
- **AutoPDL** — [`github.com/IBM/prompt-declaration-language`](https://github.com/IBM/prompt-declaration-language) — IBM's Prompt Declaration Language with the AutoPDL optimiser (arXiv 2504.04365); source-to-source optimisation over agentic and non-agentic prompting patterns plus demonstrations.

## Known Uses

- **DSPy in production** — Databricks, JetBlue, and other enterprise teams use DSPy to compile multi-step LLM pipelines, with the optimiser tuning instructions and few-shot exemplars per module.
- **Prompt registries with auto-optimisation** — platforms such as Weights & Biases Weave, LangSmith, and PromptLayer ship offline prompt-optimisation utilities built on the propose-evaluate-select loop.
- **Internal eval-driven prompt CI** — high-volume LLM products (search assistants, code assistants, agentic platforms) increasingly run S8-style sweeps in CI to re-tune prompts against held-out evaluation sets on each model upgrade.
- **Academic benchmarks** — many recent benchmark submissions report results obtained with DSPy / GEPA / MIPROv2-optimised prompts rather than hand-crafted ones.

## Related Patterns

- **Required by** S8 itself — needs **R17 Self-Consistency Voting** or **V15 LLM-as-Judge** (or graded data, or a verifier) as the Evaluator. Without an evaluation signal the loop cannot rank candidates; this is the hard prerequisite.
- **Composes with** V9 Bounded Execution — the optimisation loop must be capped on rounds, candidates, and budget; otherwise marginal improvement runs without end.
- **Produces** the artefacts that S1–S6 and S9 describe — S8 is the *process* whose output is the system prompt and exemplars those patterns assume already exist.
- **Sibling of** R7 Reflexion — both are iterate-with-feedback loops, but operate at different levels: R7 refines an *output* across attempts on a single task; S8 refines a *prompt* across many tasks. Same loop shape; different artefact under optimisation.
- **Pairs with** V14 Trajectory Logging — every candidate, score, and selection should be logged; the optimisation history is the audit trail for the deployed prompt.
- **Pairs with** S3 Persona, S5 Constraint Framing, S6 Output Template — these structure the *Proposer's* own session (what kind of candidates to emit, in what format).
- **Distinct from** K12 Karpathy Memory — both have an LLM authoring its own artefact; K12 authors a *memory store* the same agent reads, S8 authors a *prompt* a different agent will run. Different artefact, different read pattern, different evaluation regime.
- **Distinct from** O5 Evaluator-Optimizer — O5 is an orchestration pattern where one agent generates and another critiques an *output*; S8 is the Signal-layer analogue operating on *prompts*. The mechanism is similar; the artefact is one level higher.

## Sources

- Zhou et al. (2022) — "Large Language Models Are Human-Level Prompt Engineers" (APE; arXiv 2211.01910).
- Khattab et al. (2023) — "DSPy: Compiling Declarative Language Model Calls into Self-Improving Pipelines" (arXiv 2310.03714).
- Opsahl-Ong et al. (2024) — "Optimizing Instructions and Demonstrations for Multi-Stage Language Model Programs" (MIPROv2; arXiv 2406.11695).
- Zhang et al. (2023) — "Meta Prompting for AI Systems" (arXiv 2311.11482).
- Suzgun & Kalai (2024) — "Meta-Prompting: Enhancing Language Models with Task-Agnostic Scaffolding" (arXiv 2401.12954).
- Spiess et al. (2025) — "AutoPDL: Automatic Prompt Optimization for LLM Agents" (arXiv 2504.04365).
- White et al. (2023) — "A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT" — Question Refinement Pattern as a precursor.
