# R8 — Self-Refine

> Have one model generate an output, critique its own output, and revise it from that critique — looping until a stopping condition fires, with no external feedback signal and no second model.

**Also Known As:** Generate-Critique-Refine, Iterative Self-Improvement, Self-Feedback Refinement, Self-Editing Loop.

**Classification:** Category III — Reasoning · Band III-C Iterative refinement · the *sequential-with-self-critique* pattern — sibling of R7 Reflexion's *sequential-with-external-signal* and R17 Self-Consistency Voting's *parallel-with-voting*.

---

## Intent

Improve the quality of an output by having the same model that produced it write a critique of it and revise from that critique, iterating until a stopping condition — without any external evaluator, ground-truth signal, or second model.

## Motivation

A single-shot generation is whatever the model wrote on its first pass. That pass is shaped by token-level luck, by the order in which constraints were considered, and by the absence of any look-back step. For tasks where one-shot is *nearly* right but not quite — a draft that misses a constraint, a summary that buries the lede, code that compiles but is brittle — the cheap fix is not to retry or to add a judge model, but to ask the same model to *read what it just wrote and improve it*.

Madaan et al. (2023) made the case operational: take an output, prompt the same model for written feedback on that output ("what is wrong, what could be better"), then prompt it again to produce a revised output that addresses the feedback. Repeat until a stopping condition (a quality threshold, a max iteration count, or the critique reporting "nothing to improve"). Across seven diverse tasks — dialog response, code optimisation, math, sentiment reversal, acronym generation — refined outputs were preferred over one-shot generations by both humans and automatic metrics, with no fine-tuning and no external signal. The pattern works because a model reading its own output in a fresh critic session applies Q-K attention (mechanism 1) over the output as context, activating circuits that can discriminate defects in reasoning chains that the forward generation pass committed to (mechanism 7). It breaks when the same generation-path bias recurs: the critic's learned attention patterns over the generated output may reactivate the same circuits that produced the original answer.

The defining claim of the pattern is *self-containment*: one model, three roles (generator, critic, refiner), no ground-truth oracle. This is what separates R8 from the rest of the band. **R7 Reflexion** also iterates with critique, but requires an external pass/fail signal — code that executes, a schema that validates, a test suite that runs. **O5 Evaluator-Optimizer** also loops generate-then-critique, but uses a *separate* judge model (and often a separate generator), enforcing the separation as an architectural property. **R17 Self-Consistency** repeats in parallel and votes, with no critique step at all. R8 is the strictly lightest of the four: no external signal, no second agent, no fan-out — just a model reading its own work. That lightness is the trade: when single-shot is genuinely far off, R8 cannot save it (the critic shares the generator's blind spots); when single-shot is close, R8 is the cheapest upgrade available.

## Applicability

Use Self-Refine when:

- single-shot output is *close* but consistently misses a constraint, a polish step, or a structural improvement the model would recognise if asked;
- there is **no automated pass/fail signal** (no tests, no schema, no executor) — if there were, **R7 Reflexion** is stronger and cheaper per round;
- the task is open-ended enough that voting across samples (R17) does not apply — there is no "modal answer" to converge on (creative writing, structured drafting, summarisation, code review);
- the budget tolerates 2–5× the single-shot cost for a measurable quality lift;
- the model is strong enough to *both* generate the output and critique it — small models often generate fine but critique poorly.

Do not use it when:

- an automated success criterion exists (tests, schema, executor) — use **R7 Reflexion**, which leverages the signal directly and stops as soon as the criterion passes;
- you can afford a separate judge model (and the model's blind spots matter) — use **O5 Evaluator-Optimizer**, whose separation catches what self-critique misses;
- the task has an objectively correct answer with a literal mode across samples — use **R17 Self-Consistency Voting**, which marginalises over independent attempts at lower marginal cost than sequential refinement;
- the model is too weak to produce useful self-critique — its critiques will be vague ("could be better") or wrong; either upgrade the model or fall back to **O5**;
- latency budget cannot tolerate sequential extra calls — refinement is strictly sequential (output N+1 depends on critique N).

## Decision Criteria

R8 is right when single-shot is close, there is no external signal to use, and the model is strong enough to critique its own work.

**1. Measure the lift on one round of refinement.** Run a labelled sample at N=1 (single-shot) and N=2 (one critique-refine round). If the **preference rate** of N=2 over N=1 is **≥ 60%**, R8 buys real quality. Below 55%, the critic is not actually catching anything — stop and reach for **O5** (separate judge) or accept single-shot.

**2. Cap iterations — N=2 to N=4 is the working range.** Madaan et al. showed diminishing returns after the second or third refinement; many tasks plateau at N=2. Start at **N=3** and tune down if early stopping fires often, up only if the critique consistently identifies remaining issues. Beyond N=5 is almost always wasted compute.

**3. Define the stopping condition explicitly.** Three workable forms: (a) **max-iterations** — hard cap, simplest; (b) **critic-says-done** — the critique step is prompted to emit a sentinel ("no further improvements needed") and the loop exits on it; (c) **quality-threshold** — a scalar score reaches a target. Form (b) is the canonical Self-Refine form; pair with **V9 Bounded Execution** on form (a) and form (c) to guarantee termination.

**4. Test for critic-blindspot before deploying.** The pattern's load-bearing assumption is that the model *can* recognise its own mistakes when asked. If a labelled sample shows the critic accepting outputs that humans reject (a false-positive rate **> 20%**), the model shares the blindspot — R8 will not help. Switch to **O5** with a different judge model, or to **R7** if an automated criterion exists.

**5. Cost the loop honestly.** Each round is one generation + one critique + one refinement = **~3 LLM calls**. At N=3 that is **~9 calls** for what was one call. If those calls are on a frontier model, the cost is real. The economically defensible move is often **same-model R8 on a strong generalist** rather than a cheaper model run with more rounds — the critique quality caps the value of the loop.

**Quick test — R8 is the right pattern when:**

- single-shot output is consistently *close but not quite* on this task type, *and*
- no automated pass/fail signal is available (otherwise R7), *and*
- a separate judge model is not affordable or not warranted (otherwise O5), *and*
- the model is strong enough that its critiques add information (verify on a labelled sample), *and*
- the latency budget tolerates 2–5 sequential calls per output.

If an automated criterion exists, use **R7 Reflexion**. If you can afford a second model and blindspots matter, use **O5 Evaluator-Optimizer**. If answers have a literal mode and can be sampled independently, use **R17 Self-Consistency Voting**. If single-shot is already good enough, do nothing.

## Structure

```
                    ┌─────────────────────────────────────┐
                    │                                     │
                    ▼                                     │
  Task ─▶ Generate (LLM) ─▶ output_n                      │
                    │                                     │
                    ▼                                     │
            Critique (LLM, same model) ─▶ feedback_n      │
                    │                                     │
                    ▼                                     │
           [ stop? ]  ──no──▶ Refine (LLM, same model) ──┘
              │              (output_{n+1} = refine(output_n, feedback_n))
             yes
              │
              ▼
            Final output

  Stop condition: max iterations  OR  critic emits "done"  OR  quality threshold
  Same model fills all three roles (Generate / Critique / Refine);
  bound with V9.
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Generator (LLM)** | producing the initial output and each refined version | task (+ prior output + feedback on iterations ≥ 1) → output_n | be a different model on different iterations — the pattern's identity claim ("same model") is what distinguishes R8 from O5. |
| **Critic (LLM, same model)** | written feedback on the current output, with an explicit "done" sentinel | task + output_n → feedback_n (or DONE) | fabricate a positive verdict to end the loop early; the critic must *try* to find faults, and it must be prompted to do so. A critic that defaults to "looks good" silently collapses the pattern to single-shot. |
| **Refiner (LLM, same model)** | revising the output using the critique | task + output_n + feedback_n → output_{n+1} | rewrite the output from scratch ignoring the critique — that is a second generation, not a refinement, and breaks the iterative quality argument. |
| **Loop controller** | enforcing the stopping condition (max iterations / DONE sentinel / threshold) | iteration count + last critique → continue / stop | run unbounded — without a hard cap (**V9 Bounded Execution**), a critic that never says DONE will loop forever. |

Four narrow responsibilities. Two structural invariants make the pattern work:

- **Same model fills Generator, Critic, and Refiner.** Same weights, same provider, same model ID. (Different *sessions* — different setups and prompts — is fine and normal; the model identity is what matters.) Switching the Critic to a different model is the move that turns R8 into **O5 Evaluator-Optimizer**.
- **The Critic must be prompted to find faults.** A neutral "evaluate this output" prompt produces sycophantic critiques; an explicit "what is wrong, what could be better, return DONE only if nothing remains" prompt produces useful ones.

## Collaborations

The Generator produces output_0 from the task. The Critic — same model, different session — reads output_0 against the task and emits written feedback (or the DONE sentinel). The Loop controller checks the stopping condition: if DONE, or if the iteration cap is reached, the current output is returned. Otherwise the Refiner — same model, different session — takes the task, the current output, and the feedback, and produces output_1. Control returns to the Critic, which now reads output_1. The cycle continues until the Loop controller stops it. Each role is one *session* of the model with its own setup and per-call prompt; the model is the same in all three but the prompts that wrap it are not.

## Consequences

**Benefits**
- Quality lift over single-shot on tasks where one-shot is close — Madaan et al. report human preference for refined outputs across 7 diverse tasks.
- No external signal required — works where R7 cannot (no tests, no schema, no executor).
- No second model required — works where O5 is over-budget.
- The critique trace is *inspectable* — operators can read why the model changed the output. Often a useful artifact in its own right.
- Composes cleanly with **S6 Output Template** (constraint the critic checks against) and **R1 / R2 CoT** (explicit reasoning in both generation and critique).

**Costs**
- **2–5× the single-shot cost** at typical N=2 to N=4. Each round is roughly three LLM calls.
- Strictly sequential — no parallel speed-up like R17 — so wall-clock latency scales with N.
- Critique quality caps the lift. A weak critic spends compute without improving the output.

**Risks and failure modes**
- *Refinement theatre* — the Critic produces plausible-sounding feedback that does not identify the real problem; the Refiner addresses the surface complaint and leaves the real defect untouched. Visible as: refined output differs in wording but not in substance.
- *Shared blind spots* — when the underlying issue is something the model itself cannot see (a domain misconception, a missing fact, a sycophantic framing), no number of self-critique rounds will surface it. R8 *cannot fix* what the model cannot see; O5 with a different judge can.
- *Sycophantic critic* — without an explicit prompt to find faults, the Critic defaults to "looks good" and the loop collapses to single-shot with extra cost.
- *Drift on long loops* — at high N, refinements drift away from the task as each round responds to the previous critique rather than the original goal. This is a lost-in-the-middle effect (mechanism 4): the original task, stated earliest in the prompt, occupies the beginning of the context and is geometrically under-attended relative to the most recent critique. The Refiner attends most strongly to the last critique in the accumulated context, drifting from the original goal. Mitigate by restating the original task at the top of every Refiner call (placing it in an attended position) rather than only in the initial setup. Bound with **V9** and re-anchor every round by including the original task in the Refiner's prompt.
- *Unbounded loop* — a Critic that never emits DONE without a hard iteration cap (V9) runs forever.

## Implementation Notes

- The Critic prompt is the load-bearing artifact. *"List concrete problems with this output. Return DONE only if no improvement is possible."* outperforms *"evaluate this output"* by a wide margin. Specifying *what dimensions to critique on* (factuality, structure, style, completeness) is worth the prompt-engineering time.
- The Refiner prompt should include the **original task**, **the current output**, and **the critique** — not just the critique. Refiners that see only the critique drift; refiners that see the full triple stay anchored.
- Use **structured critique** (a list of issues, each with severity) over prose critique when downstream code needs to act on it. **S6 Output Template** is the natural composition.
- Start with **N=3** as the iteration cap and tune from data. Many tasks plateau at N=2; some benefit from N=4. Beyond N=5 is almost always waste.
- **Same model, different sessions** — the Generator, Critic, and Refiner each have their own setup (role, criteria, output contract). Confusing this with "same prompt three times" produces worse critiques and worse refinements.
- The pattern composes with **R1 Zero-Shot CoT** in the Critic role — "*think step by step about what is wrong with this output*" produces more useful feedback than direct critique. The composition is essentially free.
- **Pair with V9 Bounded Execution** — every refinement loop needs a hard cap, and R8 is no exception. The Critic's DONE sentinel is a *soft* stop; V9 is the *hard* one.
- For comparable outputs (code, structured data), keep an automated check alongside the self-critique — when the check exists, escalate to **R7 Reflexion** to use it directly.

## Implementation Sketch

> `LLM = configured session (model + setup + per-call prompt); code = wiring.`

**Composition:** R8 chains three sessions of *the same model* — Generator, Critic, Refiner — under a code-driven loop controller, drawing on **S6 Output Template** for structured critiques, **R1 / R2 CoT** for explicit reasoning in critique, and **V9 Bounded Execution** for the hard iteration cap. R8 commonly composes upward into **O6 Orchestrator-Workers** or **R3 Plan-and-Solve** as the quality step on a worker's output.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Initial generation | `LLM` | Generator session |
| 2 | Critique current output (with DONE sentinel) | `LLM` | Critic session (R1 / S6) |
| 3 | Branch — if DONE or iteration cap, exit; else continue | `code` | V9 |
| 4 | Refine current output from critique | `LLM` | Refiner session |
| 5 | Loop to step 2 | `code` | |

**Skeleton** — the wiring only; each `# LLM` line is a configured session of the same model:

```
self_refine(task, max_rounds=3):
    output = Generator(task)                          # LLM — same model M
    for n in range(max_rounds):                       # code — V9-bounded loop
        feedback = Critic(task, output)               # LLM — model M, Critic session
        if feedback.is_done():                        # code — sentinel check
            break
        output = Refiner(task, output, feedback)      # LLM — model M, Refiner session
    return output
```

**The LLM sessions.** All three sessions use *the same model*. They differ in setup (role, criteria, output contract); the per-call prompt wraps only the changing data.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generator** | the system's main generalist (must be strong enough that its critiques are useful — critique quality caps the loop's value) | role (S3); the task's success criteria and output contract (S6); any domain context | the task instance |
| **Critic** (same model as Generator) | role: *"you read the output and list concrete problems against the criteria; you return DONE only if no improvement is possible"*; the **same** success criteria the Generator was given (so critique is against the same bar); critique output contract — a structured list of issues with severity, or the DONE sentinel; explicit "do not be lenient" framing | the task + the current output |
| **Refiner** (same model as Generator) | role: *"you revise the output to address each issue in the critique while preserving what is correct"*; the original task and success criteria; instruction to *not* rewrite from scratch — address the critique, keep the rest | the task + the current output + the critique |

**Specialist-model note.** None required — Self-Refine works with any capable generalist; the structurally important choice is that **all three sessions use the same model**. Switching the Critic to a different (typically stronger, or differently-trained) model is the move that turns R8 into **O5 Evaluator-Optimizer** — a related but different pattern. The model must be strong enough to produce useful self-critique: small models often generate fine but critique poorly, and below a quality threshold R8 spends compute without lift. The S6 output contract on the Critic (structured issue list with DONE sentinel) is the prompt artifact doing the heavy lifting — making the loop controller's job deterministic depends on it.

## Open-Source Implementations

- **Self-Refine (official)** — [`github.com/madaan/self-refine`](https://github.com/madaan/self-refine) — the canonical implementation from the paper's authors. Task-specific FEEDBACK and REFINE modules across the 7 benchmarked tasks; reference prompts for critique and refinement.
- **DSPy `Refine`** — [`github.com/stanfordnlp/dspy`](https://github.com/stanfordnlp/dspy) — Refine module ([`dspy/predict/refine.py`](https://github.com/stanfordnlp/dspy/blob/main/dspy/predict/refine.py)) extending BestOfN with an automatic feedback loop: after each failed attempt, generates feedback and uses it as a hint for the next run. The closest thing to a framework primitive.
- **LangGraph reflection tutorials** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — runnable reference graphs for the draft → critique → improve loop; LangGraph's stateful-graph model maps directly onto the R8 cycle.
- **Project website** — [selfrefine.info](https://selfrefine.info/) — paper authors' demo and per-task results.

## Known Uses

- **Code-generation pipelines** — Self-Refine is a documented baseline in code-quality tooling where no test suite is available; the model critiques its own code for readability, edge-case handling, and structure before returning.
- **Long-form writing assistants** — draft-critique-revise loops are standard in production writing tools (essay drafting, marketing copy, executive summaries); the pattern is sometimes called "iterative drafting" in product copy but is structurally R8.
- **Structured data extraction** — the Critic checks the extracted JSON against the schema and the source text; the Refiner fills missed fields or corrects misreads.
- **DSPy production programs** — `dspy.Refine` is applied automatically by the DSPy compiler as a quality lift step on selected modules.
- **Acronym, sentiment-reversal, and dialog-response benchmarks** in the original Madaan et al. paper — the canonical empirical demonstration.

## Related Patterns

- **Sibling of R7 Reflexion** — same band, same generate-critique-refine shape, but R7 requires an **external pass/fail signal** (test execution, schema validation, automated evaluator) while R8 generates its own critique from the same model. R7 is stronger when the signal exists; R8 is the only option when it does not.
- **Sibling of R17 Self-Consistency Voting** — same band, same goal (reliability through repetition), but R17 is *parallel-then-vote* with no critique step and R8 is *sequential-with-self-critique*. R17 needs a comparable answer space; R8 works on open-ended outputs.
- **Distinct from O5 Evaluator-Optimizer** — same generate-critique-refine *shape*, different participant cardinality. O5 uses a **separate judge model** (and often a separate generator), enforcing the separation as an architectural property; R8 uses the **same model** for all three roles. O5 catches blind spots R8 cannot; R8 is the lighter weight when blind spots are not the binding constraint. **The choice between R8 and O5 is the choice between "one model, three roles, in-context" and "two agents, separated by infrastructure".**
- **Composes with S6 Output Template** — a structured critique contract (issue list with severity, plus DONE sentinel) is what makes the loop controller deterministic. Without S6 the Critic's output is prose that the loop controller must parse heuristically.
- **Composes with R1 Zero-Shot CoT** — "*think step by step about what is wrong*" in the Critic role produces more useful feedback than direct critique. Essentially free composition.
- **Pairs with V9 Bounded Execution** — every refinement loop needs a hard cap; the Critic's DONE sentinel is a *soft* stop, V9 is the *hard* one.
- **Pairs with V14 Trajectory Logging** — the chain of (output, critique, refined output) across rounds is a high-value audit artifact; log it.
- **Composes upward into O6 Orchestrator-Workers and R3 Plan-and-Solve** — R8 is a natural quality step applied to a worker's output before it returns to the orchestrator, or to a plan step's output before execution proceeds.

## Sources

- Madaan et al. (2023) — "Self-Refine: Iterative Refinement with Self-Feedback" (arXiv [2303.17651](https://arxiv.org/abs/2303.17651)). The canonical reference; the FEEDBACK → REFINE loop, the 7-task evaluation, and the ~20% preference lift over one-shot generation.
- Project website — [selfrefine.info](https://selfrefine.info/) — per-task results and reference prompts from the authors.
- DSPy documentation — `dspy.Refine` and `dspy.BestOfN` as framework primitives ([source](https://github.com/stanfordnlp/dspy/blob/main/dspy/predict/refine.py)).
- LangGraph reflection tutorials — runnable reference graphs for the draft-critique-improve loop.
- Anthropic agent-pattern catalog — Evaluator-Optimizer (O5) entry, which contrasts the *separate-judge* form against the *same-model* Self-Refine form.
