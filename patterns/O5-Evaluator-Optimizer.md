# O5 — Evaluator-Optimizer

> Split generation and evaluation into two distinct agents — a Generator that drafts, and a separate Judge that scores it against criteria — and iterate the Generator on the Judge's feedback until the work passes, capped by a hard loop bound.

**Also Known As:** Generator-Critic, Judge-Optimizer, Separate Evaluator, Two-Agent Refinement. (No named sub-variants; the relevant configuration choices — binary vs scalar verdict, same-model vs cross-model judge, in-band vs out-of-band evaluation — are tuning parameters rather than separate patterns.)

**Classification:** Category IV — Orchestration · Band IV-B Agentic workflows · the *two-agent quality-loop* pattern — the production-grade sibling of R8 Self-Refine (same shape, single model in three roles) and the architectural cousin of R7 Reflexion (sequential retry with external pass/fail, inside one agent).

---

## Intent

Improve output quality by separating the generator and the judge into two distinct agents — different sessions, typically different setups, potentially different models — so the evaluation is genuinely independent of the work it scores, and the generator iterates on a feedback signal it cannot foresee or sandbag.

## Motivation

A single agent that generates and then critiques its own output shares its own blind spots. **R8 Self-Refine** is the lightweight form of this loop — one model, three roles (generator, critic, refiner), all in-context — and it works when the model is strong enough to recognise its own near-misses. R8's load-bearing weakness is exactly the property that makes it cheap: the critic sees the world the same way the generator does, so the failures it cannot see in its own output are the failures it cannot see in anyone else's. When the critic is the same model as the generator, "you wrote this; is it good?" returns a sympathetic verdict more often than it should.

The Evaluator-Optimizer move is to make the separation *architectural*, not just prompt-level. The Judge is a different agent: its own session, its own setup, its own prompts, often a different model entirely. The Generator does not know what the Judge will check, cannot pre-empt its criteria, and cannot rewrite history once the Judge has spoken — the verdict comes from outside the Generator's context. That separation is what buys the independent evaluation. Anthropic's "Building Effective Agents" lists this as one of five canonical workflow patterns precisely because the cross-agent boundary is the structural fact: it is not a prompt-engineering choice on a single model, it is a system-design choice that wires two agents together.

The defining claim of the pattern is *participant cardinality*: **two agents, not one in two roles**. **R8** is one model, in-context, three prompted personas — the lightweight version. **O5** is two agents, separated by infrastructure — the production-grade version that pays for the separation in extra wiring and gets back an evaluation signal the Generator cannot game.

The mechanical reason same-model critique fails is that the Generator and Judge share the same weight matrices W_Q and W_K — the same learned bilinear form Q_α K^α that causes the Generator to under-attend to a class of counter-examples will cause the Judge to under-attend to the same class when it evaluates the output (mechanism 1). Cross-model O5 breaks this by using a different bilinear form — a different set of learned projection matrices — so the Judge's attention geometry is genuinely different from the Generator's. (Mechanism 1.) **R7 Reflexion** sits adjacent: a single Actor agent that retries on an *automated* pass/fail signal (test runner, schema validator, environment) with an in-context verbal critique between attempts; R7's evaluator can be code, R7 is one agent, and the iteration mechanism is retry-with-memory rather than draft-on-feedback. O5 is the right pattern when the evaluation requires an LLM judgment and the quality of that judgment depends on it not coming from the same head that wrote the draft.

## Applicability

Use Evaluator-Optimizer when:

- output quality is the constraint and self-evaluation has measurably shared blind spots — R8 on a labelled sample shows the same-model critic accepting work humans reject;
- the success criteria are concrete enough to write a judge rubric against (correctness, completeness, format, tone, factual support) but not concrete enough for a deterministic check (no test runner, no schema validator);
- you can afford two agent slots and the per-iteration cost of running both;
- the task tolerates 2–5 sequential refinement rounds — the loop is strictly sequential by construction (output N+1 needs feedback N);
- the rubric is stable enough to set once and reuse across many tasks of the same shape (otherwise rubric maintenance overwhelms the gains).

Do not use it when:

- a deterministic automated check exists — use **R7 Reflexion**, which leverages the test runner / schema / environment directly and is one agent rather than two;
- the same model in three roles is good enough and a separate judge is over-budget — use **R8 Self-Refine**;
- the work is parallel-sample-able and there is a modal answer to converge on — use **R17 Self-Consistency Voting**, which marginalises over independent samples at lower marginal cost than sequential refinement;
- you need multiple critical lenses on the same output (security, performance, accuracy, style as parallel critics) — use **O9 Multi-Agent Reflection**, which is O5 generalised across N parallel judges;
- the loop is open-ended and there is no plausible stopping condition the Judge can emit — bound a different way or do not loop;
- latency is tight — the loop is strictly sequential and adds the Judge's call to every round.

## Decision Criteria

O5 is right when output quality is the constraint, self-critique has measurable blind spots, no automated success signal exists, and the budget tolerates a separate agent slot.

**1. Test for same-model blind spots before reaching for O5.** Run **R8 Self-Refine** on a labelled sample. Compute the **same-model critic false-positive rate** — outputs the critic accepts that human reviewers reject. If that rate is **> 20%**, the model shares the blind spot and R8 cannot save it: escalate to O5 with a different judge model. If the rate is **< 10%**, R8 is doing the job and O5's extra cost is not paying for itself.

**2. Confirm no deterministic evaluator exists.** If there is a test runner, schema validator, code executor, or environment assertion, use **R7 Reflexion** instead — the automated signal is stronger and cheaper per round than an LLM judge. O5 is for tasks where the verdict requires judgment: drafts, summaries, free-form code review, content with quality rubrics, structured outputs whose quality is more than schema validity.

**3. Cap iterations — N = 2 to N = 4 is the working range.** Like R8, gains plateau quickly. Set the iteration cap at **N = 3** and tune down if early-stop fires often, up only if the Judge consistently identifies remaining issues. Beyond **N = 5** is almost always wasted compute. Pair with **V9 Bounded Execution** — the Judge's "approved" sentinel is a *soft* stop; V9 is the *hard* one. The plateau is an observation, not yet derived from first principles. The likely mechanism is that the refinement space that a fixed-rubric Judge can reach is bounded; after 2–3 iterations the draft has moved to the mode of the Judge's sampling distribution and further iterations — themselves stochastic (mechanism 7) — sample near-identical verdicts. Treat the N=3 cap as empirical; re-validate on your task. (Mechanism 7 — emergent/unproven.)

**4. Pick the Judge model deliberately — cross-model is the default.** If the Generator is a frontier model, the Judge can often be a smaller, cheaper one — the judgment task is narrower than generation. If the Generator and Judge are the *same* model, the architectural separation buys less than its cost; verify the separation is doing real work by ablating the Judge to the same model and measuring the quality delta. Same-model O5 collapses toward R8 in practice if the Judge's prompt does not enforce a genuinely different stance.

**5. Cost the loop honestly.** Each round is **Generator call + Judge call + (on fail) Generator refinement call**. At N = 3 with a frontier Generator and a small Judge, expect **~4–6$\times$ single-shot cost**, dominated by Generator refinements. If the Generator is small, the loop is cheap; if the Generator is large, the Judge being small is the lever that keeps O5 affordable.

**Quick test — O5 is the right pattern when:**

- R8 same-model critique has measurable blind spots on the task (false-positive rate > 20%), *and*
- no automated pass/fail signal exists to use R7 instead, *and*
- a separate Judge — same model or different — is in budget for every iteration, *and*
- the task tolerates 2–5 sequential rounds and the Judge can emit a stable "approved" sentinel.

If a deterministic check exists, use **R7 Reflexion**. If R8's same-model critic catches enough, stay with **R8 Self-Refine** — it is half the wiring. If you need multiple critical lenses in parallel rather than one sequential judge, use **O9 Multi-Agent Reflection**. If the answer space supports a literal mode, **R17 Self-Consistency Voting** may be cheaper at comparable quality.

## Structure

```
                                ┌──────────── feedback ────────────┐
                                │                                  │
                                ▼                                  │
   Task ──▶ Generator (Agent G) ──▶ draft_n ──▶ Judge (Agent J) ──▶ verdict_n
                                                       │
                                                       │
                                                approved? ──yes──▶ Final output
                                                       │
                                                       no
                                                       │
                                                       ▼
                                            refine_request to G
                                            (draft_n + feedback_n)
                                                       │
                                                       ▼
                                            Generator produces draft_{n+1}
                                                       │
                                                       └──── back to Judge

  Stop: Judge approves  OR  iteration cap (V9)  OR  no-progress detector
  Generator and Judge are distinct agents — separate sessions, often different models.
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Generator agent (G)** | producing the initial draft and each refinement | task (+ prior draft + Judge feedback on iterations $\geq$ 1) $\to$ draft_n | see the Judge's rubric in its setup. If G is trained to satisfy the rubric directly, the Judge becomes a rubber stamp — the independence collapses. G should be set up for the *task*; the rubric is the Judge's possession. |
| **Judge agent (J)** | scoring drafts against the rubric and emitting an APPROVED sentinel or actionable feedback | task + draft_n $\to$ verdict (APPROVED / NEEDS-WORK + feedback) | be the same session as G. The pattern's identity claim ("two agents, not one in two roles") rests here. Different model is preferred; same model with a different session is acceptable; same session is the failure. J must also not rewrite the draft — its output is *verdict + feedback*, not a new draft. |
| **Refinement controller** | wiring G's next call from the Judge's feedback; enforcing the loop bound | (draft, verdict, iteration count) $\to$ next G call or final output | hide a non-terminating loop. The cap N_max is mandatory (**V9 Bounded Execution**). The controller is also responsible for detecting *no-progress* — if draft_{n+1} differs only superficially from draft_n, stop. |
| **Rubric / criteria artifact** | the standard the Judge applies | written rubric $\to$ Judge setup | live in the Generator's setup. The rubric belongs to the Judge alone; if G knows the rubric, G optimises for the rubric and not the task — a classic Goodhart-style failure. |
| **Iteration log** *(optional)* | the trace of (draft, verdict, feedback) across rounds | sequence of rounds $\to$ V14 trajectory record | be hidden. The chain of drafts and verdicts is the pattern's primary audit artefact; suppressing it kills the operator's ability to tell genuine improvement from refinement theatre. |

Three structural invariants make the pattern work:

- **G and J are distinct agents.** Different sessions; ideally different model IDs. Same session collapses O5 into R8.
- **J holds the rubric; G does not.** G is set up for the task in general; J is set up with the criteria the work must meet. Mixing these defeats the independence claim.
- **J's verdict is contractually structured.** APPROVED ends the loop; NEEDS-WORK carries actionable feedback. Free-form prose verdicts make the controller's job ambiguous and the loop unstable.

## Collaborations

The Generator agent G receives the task and produces draft_0 — a normal generation against the task, with no rubric in its setup. The Refinement controller hands draft_0 to the Judge agent J, which is set up with the rubric and produces a verdict: either APPROVED (loop ends, draft_0 is returned) or NEEDS-WORK with structured feedback. On NEEDS-WORK, the controller composes a refinement request — the original task, the current draft, and the Judge's feedback — and calls G again. G produces draft_1, which goes back to J under the same setup. The cycle continues until J approves, the iteration cap N_max is reached, or the controller detects no-progress (draft_{n+1} differs from draft_n only superficially). At the cap, the controller returns the last draft (best-effort) and optionally escalates to **V1 Human-in-the-Loop**. Each round writes (draft, verdict, feedback) to **V14 Trajectory Logging** — the chain is the audit artefact.

The Judge runs on its own model and its own setup. The pattern's value depends on J not seeing the world the way G does — that is what the architectural separation is for. Same-model O5 (G and J on the same model, different sessions) is permitted and often the cheapest configuration, but the prompts must enforce a genuinely critical stance on J; otherwise the loop collapses toward R8 and the extra wiring buys nothing.

## Consequences

**Benefits**
- Independent evaluation catches blind spots the same-model critic in R8 cannot see — the architectural separation is what buys it.
- The Judge can be a *cheaper* model than the Generator, since judgment is often narrower than generation — same-model R8 cannot exploit this.
- Clear quality gate: APPROVED / NEEDS-WORK is a binary signal the controller can act on without heuristic parsing.
- The Judge's rubric is reusable across many tasks of the same shape — write once, apply to many drafts.
- The iteration log (drafts + verdicts + feedback) is a high-value audit artefact for operators, debuggers, and trust-calibration consumers.
- Composes cleanly with **V15 LLM-as-Judge** (the Judge is V15's canonical use case), **V9 Bounded Execution** (loop cap), and **V14 Trajectory Logging** (the chain is the artefact).

**Costs**
- **Two agent slots, not one** — separate setup, separate prompts, separate model choice. More wiring than R8.
- **4–6$\times$ single-shot cost** at N = 3 with Generator + Judge + refinement calls per round.
- Strictly sequential — no parallel speed-up; wall-clock latency scales with N. Each iteration requires a full fresh prefill on the Generator and Judge calls. The KV cache does not persist across API calls (mechanism 3); each round re-pays the prefill cost. For a stable Judge setup, prefix caching (mechanism 5) amortises the Judge's system prompt across iterations, but the draft and feedback tokens re-enter each time. (Mechanisms 3, 5.)
- Rubric maintenance: the Judge is only as good as its rubric, and rubrics drift as tasks evolve.
- The Judge can become a bottleneck on cross-model calls (rate limits, provider availability) when the Generator and Judge are on different providers.

**Risks and failure modes**
- *Rubber-stamp Judge* — J defaults to APPROVED when its prompt does not enforce a critical stance. Symptom: most drafts pass on round 1, but human reviewers find issues. Mitigation: explicit "find faults; APPROVE only if none remain" framing in J's setup; periodic calibration against human-graded samples.
- *Hostile Judge* — J never approves, the loop always hits N_max. Symptom: cap-bounded exits dominate; final drafts are over-revised and worse than draft_0. Mitigation: tune the rubric, calibrate against a labelled sample, accept the highest-scoring draft on cap-exit rather than the last one.
- *Generator gaming the Judge* — over time, if the Judge's feedback patterns leak into the Generator's setup (via prompt iteration, examples, or fine-tuning), G learns to satisfy J specifically rather than the task. The independence collapses and quality regresses on unseen rubric dimensions. Mitigation: keep G's setup task-focused; never put J's rubric in G's prompt.
- *Refinement theatre* — drafts change in wording across rounds but not in substance; J keeps complaining about adjacent issues. Symptom: J's feedback shifts attention from one surface concern to another while the real defect remains. Mitigation: no-progress detector in the controller; reset to draft_0 with a different model on G if drift is detected.
- *Shared-model blind spots when G = J model* — same-model O5 with insufficiently differentiated prompts collapses to R8. Mitigation: ablate J against a different model; if quality drops, the separation was load-bearing.
- *Unbounded loop* — J that never emits APPROVED without a hard iteration cap (V9) runs forever; controller is also responsible for cap.
- *Rubric leakage to the wider system* — J's rubric, written for one task type, gets reused on tasks where it does not fit; the loop trains drafts in the wrong direction. Mitigation: version rubrics per task type; treat the rubric as a maintained artefact.

## Implementation Notes

- **The Judge's rubric is the load-bearing artefact.** Generic "evaluate this output" prompts produce generic verdicts. Concrete rubrics — "score on (a) factual correctness against the source, (b) completeness against the spec, (c) tone alignment to the brand guide; APPROVE only if all three are PASS" — produce useful verdicts. Spend prompt-engineering time on the Judge, not the Generator.
- **Default to a different model for the Judge.** Cross-model O5 (e.g., Sonnet-class Generator, Haiku-class Judge with a tuned rubric) is the typical production configuration. Same-model O5 is permitted but should be ablated against a different model to verify the separation is doing work.
- **Generator setup must not contain the rubric.** That is the rule that protects the independence claim. G is set up for the *task*; J is set up with the *criteria*. The refinement call carries J's feedback into G's per-call prompt, but never J's rubric into G's setup.
- **Use structured verdicts.** V15-style output contract: `{ "verdict": "APPROVED" | "NEEDS_WORK", "feedback": [ {issue, severity, suggestion} ] }`. Compose with **S6 Output Template**. Free-form prose verdicts make the controller's branching ambiguous.
- **Start with N = 3 as the iteration cap.** Tune from data. Many tasks plateau at N = 2; some benefit from N = 4. Beyond N = 5 is almost always wasted.
- **Include the original task in every refinement call.** The Generator needs the task, the current draft, and the feedback — not just the feedback. Refiners that see only the feedback drift away from the task across rounds.
- **Log everything via V14.** The (draft, verdict, feedback) sequence is the artefact that lets operators distinguish learning from refinement theatre. Without the log, you cannot tell which is which.
- **Calibrate the Judge against humans periodically.** A drifting Judge silently degrades the whole loop. Sample N drafts a week, have humans grade them, compare to J's verdicts; retune the rubric when agreement falls below the threshold.
- **Pair with V9 Bounded Execution** — non-optional. Pair with **V1 Human-in-the-Loop** for cap-exit escalation when the work is high-stakes.
- **Compose upward into O6 Orchestrator-Workers** — O5 is a natural quality step on a worker's output before it returns to the orchestrator.

## Implementation Sketch

> `LLM = configured session (model + setup + per-call prompt); code = wiring.`

**Composition:** O5 chains two distinct agents — a Generator and a Judge — under a code-driven refinement controller, drawing on **V15 LLM-as-Judge** as the Judge's mechanism, **S6 Output Template** for structured verdicts, **V9 Bounded Execution** for the iteration cap, and **V14 Trajectory Logging** for the round-by-round artefact. O5 commonly composes upward into **O6 Orchestrator-Workers** (quality gate on worker output) and pairs with **V1 Human-in-the-Loop** for cap-exit escalation on high-stakes work.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Generator produces initial draft from the task | `LLM` | Generator session |
| 2 | Judge scores the draft against the rubric; emits APPROVED or NEEDS-WORK + structured feedback | `LLM` | Judge session (V15, S6) |
| 3 | Branch — if APPROVED or iteration cap or no-progress, exit | `code` | V9 |
| 4 | Compose refinement request: task + current draft + Judge feedback | `code` | |
| 5 | Generator produces refined draft | `LLM` | Generator session |
| 6 | Loop to step 2 | `code` | |
| 7 | On cap-exit: return best-scoring draft; optionally escalate | `code` | V1 (optional) |

**Skeleton** — the wiring only; each `# LLM` line is a configured session on its own agent:

```
evaluator_optimizer(task, max_rounds=3):
    draft = Generator(task)                              # LLM — Agent G
    for n in range(max_rounds):                           # code — V9-bounded loop
        verdict = Judge(task, draft)                      # LLM — Agent J (V15)
        log(draft, verdict)                                # code — V14
        if verdict.is_approved():
            return draft                                   # APPROVED exit
        if no_progress(draft, prior_draft):                # code — refinement-theatre guard
            return best_so_far()
        draft = Generator(task, draft, verdict.feedback)   # LLM — Agent G, refinement call
    return best_so_far()                                   # V9-bounded cap exit
```

**The LLM sessions.** Two distinct agents, often on different models. They differ structurally — the Judge holds the rubric the Generator never sees.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generator** | the system's main generalist; chosen for the *task*, not the rubric | role (S3); the *task's* success criteria and output format (S6); domain context; instruction to *address the provided feedback* while preserving correct parts of prior drafts on refinement calls. **The Judge's rubric is not in this setup.** | iteration 0: the task. iteration $\geq$ 1: the task + the current draft + the Judge's structured feedback. |
| **Judge** | a *different* model from the Generator (preferred); when same-model, must use a different session with explicitly critical prompting | role: *"you score drafts against this rubric and emit APPROVED only if every criterion passes"*; the **rubric** (concrete criteria with PASS/FAIL definitions); output contract — structured `{ verdict, feedback[] }` (S6); explicit "find faults; do not be lenient" framing. **The task itself is also given so the Judge knows what the work was meant to do.** | the task + the current draft |

Concretely, for a content-quality Judge: setup loaded once is *"You score drafts against the rubric below. APPROVE only if every criterion is PASS. Return `{verdict: APPROVED | NEEDS_WORK, feedback: [{criterion, status, issue, suggestion}]}`. Rubric: (1) factual support — every claim cites the source; (2) completeness — every required section present; (3) tone — matches the brand voice guide below. Do not be lenient; if any criterion is ambiguous, return NEEDS_WORK."* The per-call prompt wraps only *"Task: {task}. Draft: {draft}"*.

**Specialist-model note.** No fine-tuned specialist is required, but two structural choices change everything:

- **Generator and Judge must be distinct agents.** Different sessions, ideally different model IDs. Cross-model (Generator = strong frontier model; Judge = cheaper specialist or differently-trained model) is the typical production configuration and the cheapest way to keep the architectural separation real. Same-model with same-session is the failure that collapses O5 to R8.
- **The rubric is the prompt artefact doing the heavy lifting.** Concrete, criterion-by-criterion, with explicit PASS/FAIL definitions and "do not be lenient" framing. A Judge with a weak rubric is a rubber stamp; the loop then produces motion without progress.

A small fine-tuned classifier can substitute for the Judge LLM on tasks where the rubric reduces to categorical labels — but the typical O5 deployment uses a capable generalist on both ends, distinguished only by setup.

## Open-Source Implementations

- **Anthropic Cookbook — Evaluator-Optimizer notebook** — [`github.com/anthropics/claude-cookbooks`](https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/evaluator_optimizer.ipynb) — the canonical reference notebook accompanying "Building Effective Agents." Implements the two-agent generate-evaluate-refine loop with a stopping condition. The closest thing to an official implementation.
- **Spring AI — EvaluatorOptimizerWorkflow** — [`github.com/spring-projects/spring-ai-examples`](https://github.com/spring-projects/spring-ai-examples/tree/main/agentic-patterns/evaluator-optimizer) — JVM-framework implementation of the pattern as a first-class workflow class with a `loop(task)` method and chain-of-thought capture. The most framework-y embodiment.
- **LangGraph reference graphs** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — runnable reference graphs for the generator-evaluator loop; LangGraph's stateful-graph model maps directly onto the O5 cycle, and the evaluator-optimizer pattern is a common tutorial example.
- **Pydantic AI — Building Effective Agents port** — [`github.com/intellectronica/building-effective-agents-with-pydantic-ai`](https://github.com/intellectronica/building-effective-agents-with-pydantic-ai) — code examples porting Anthropic's five workflow patterns to Pydantic AI, including an Evaluator-Optimizer notebook with explicit Generator and Fixer agents.
- **DSPy `Refine` and `BestOfN`** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — the framework treats generator-evaluator loops as compilable structures; `Refine` can be configured with a separate judge module to realise O5 (as distinct from its same-model R8 default).

## Known Uses

- **Anthropic's "3-Agent Architecture" deployments** — Planner + Generator + Evaluator triads in agentic systems, where the Evaluator is the O5 Judge wrapping the Generator's worker output.
- **Production content-generation pipelines** — marketing copy, legal clauses, technical documentation — where a Generator drafts and a separate Judge agent scores against a brand guide, compliance rubric, or accuracy criteria. The pattern appears under "evaluator-optimizer" branding in Spring AI shops and "generator-critic" framing in LangGraph deployments.
- **Translation quality loops** — Generator translates, Judge scores nuance and fluency against criteria, Generator refines. Documented in Anthropic's "Building Effective Agents" as a canonical use case.
- **Code review and code generation pipelines** where no test suite is available — Generator writes code, Judge reviews for readability, edge cases, and structural quality against a rubric, Generator revises. (When tests exist, **R7 Reflexion** is preferred.)
- **API documentation generators** — Generator agent reads code and drafts documentation; Judge agent validates the documentation against the actual implementation; the loop iterates until alignment passes.
- **Claude Code's inline evaluator-optimizer skills** — community pattern where one model generates content and a separate model evaluates every claim against evidence before approval.

## Related Patterns

- **Distinct from R8 Self-Refine** — same generate-critique-refine *shape*, different participant cardinality. R8 is one model in three roles (Generator, Critic, Refiner) all in-context; O5 is **two distinct agents** (Generator, Judge), separated by infrastructure — different sessions, ideally different models. R8 is the lightweight in-context version; O5 is the production-grade architectural version. The choice between them is whether the same-model critic's blind spots are the binding constraint.
- **Distinct from R7 Reflexion** — same sequential-refinement *band*, different evaluator type and agent cardinality. R7's evaluator is an **automated pass/fail signal** (test runner, schema validator, environment assertion) and the loop is one agent retrying with verbal memory of failures. O5's evaluator is **always an LLM judge** and the loop is two agents drafting and judging. R7 fits tasks with deterministic checks; O5 fits tasks where the verdict requires judgment.
- **Generalised by O9 Multi-Agent Reflection** — O9 is O5 with N parallel critics across distinct lenses (security, performance, accuracy, style) feeding a synthesis step. Upgrade from O5 to O9 when one Judge's rubric cannot capture the dimensions that matter and parallel specialist critics buy real coverage.
- **Pairs with V15 LLM-as-Judge** — V15 is the canonical Judge mechanism O5 uses for its evaluator role. V15 is the *building block*; O5 is the *loop that calls V15 once per round*.
- **Pairs with V9 Bounded Execution** — mandatory. The Judge's APPROVED sentinel is a soft stop; V9 is the hard one. Every refinement loop without a cap is a bug.
- **Pairs with V14 Trajectory Logging** — the chain of (draft, verdict, feedback) across rounds is the pattern's primary audit artefact; log it.
- **Composes with S6 Output Template** — the Judge's structured verdict contract (verdict + feedback array) is what makes the controller's branching deterministic.
- **Composes upward into O6 Orchestrator-Workers** — O5 is a natural quality gate applied to a worker's output before it returns to the orchestrator.
- **Composes with V1 Human-in-the-Loop** — cap-exit escalation when the loop fails to converge on high-stakes work.
- **Competes with R8** on cost — R8 is half the wiring; O5 is the upgrade when R8's same-model critic provably misses things.

## Sources

- Anthropic (2024) — "Building Effective Agents" — [anthropic.com/research/building-effective-agents](https://www.anthropic.com/research/building-effective-agents). The canonical reference; lists Evaluator-Optimizer as one of five workflow patterns.
- Anthropic Cookbook — Evaluator-Optimizer notebook — [github.com/anthropics/claude-cookbooks](https://github.com/anthropics/claude-cookbooks/blob/main/patterns/agents/evaluator_optimizer.ipynb). Reference implementation.
- Madaan et al. (2023) — "Self-Refine: Iterative Refinement with Self-Feedback" (arXiv [2303.17651](https://arxiv.org/abs/2303.17651)). The single-agent sibling (R8) that O5 separates architecturally.
- Shinn et al. (2023) — "Reflexion: Language Agents with Verbal Reinforcement Learning" (arXiv [2303.11366](https://arxiv.org/abs/2303.11366)). The single-agent retry-with-automated-signal sibling (R7).
- Spring AI documentation — EvaluatorOptimizerWorkflow class reference — [docs.spring.io/spring-ai](https://docs.spring.io/spring-ai/reference/api/effective-agents.html).
- LangGraph documentation and reference graphs — evaluator-optimizer tutorials as canonical realisations of the cycle.
