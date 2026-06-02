# O9 — Multi-Agent Reflection

> Have several distinct critic agents — different personas, often different models or knowledge bases — independently review the same output, then synthesise their critiques into one verdict the generator can act on.

**Also Known As:** Ensemble Critique, Parallel Critique, Devil's Advocate Ensemble, Multi-Critic Review, Reviewer Ensemble.

**Classification:** Category IV — Orchestration · Band IV-B Agentic workflows · the *ensemble-of-independent-judges* pattern — O5 Evaluator-Optimizer generalised across N parallel critics with a synthesis step.

---

## Intent

Get genuinely independent evaluation of an output by running several differently-configured critic agents in parallel against it, then synthesising their critiques — so the verdict reflects multiple lenses no single critic (or self-critique) would produce.

## Motivation

Single-agent reflection patterns share blind spots with generation. **R8 Self-Refine** uses one model in three roles: a critic that thinks the way the generator thinks accepts work humans reject. **O5 Evaluator-Optimizer** moves the judge to a separate agent — independent of the generator — but it is still *one* judge with *one* rubric. Many real review tasks need multiple lenses applied at once: a code change wants a security review *and* a performance review *and* a maintainability review; a strategy memo wants a quantitative critic *and* a legal critic *and* a market critic. Asking a single judge to hold all those lenses at once dilutes each one — and gives the generator a single voice it can learn to satisfy without satisfying the underlying concerns.

The Multi-Agent Reflection move is to run **N separate critic agents in parallel**, each configured with a distinct persona (security reviewer, performance reviewer, accuracy reviewer, style reviewer), often distinct models, and sometimes distinct knowledge bases. Each critic sees only the output and its own brief. None can see the others' critiques while writing. After they finish, a Synthesis Agent reads all N critiques and produces a single consolidated verdict — surfacing agreement, flagging contradictions, prioritising the most consequential issues. The Generator then iterates against that synthesised feedback.

The defining claim is *participant cardinality on the judge side*: where R8 collapses generation and critique into one model, and O5 separates them into two agents, O9 fans the judge out into **N independent agents plus a synthesiser**. Independence is structural: separate sessions, separate setups, ideally separate models. That fan-out is what catches what any single judge would miss — including a sympathetic same-model judge in O5.

The mechanical basis for cross-model independence is that each model has its own learned weight matrices W_Q and W_K. The attention score Q_α K^α (mechanism 1) is the inner product under a different bilinear form for each model. What model A systematically under-attends to (because A's projection matrices do not separate that feature class) may be correctly attended to by model B with a different bilinear structure. Same-model critics with different persona prompts narrow the gap in perspective without changing the underlying bilinear form — they are still computing the same inner product, just from a different starting prompt position. Cross-model critics compute genuinely different similarity functions over the same input. (Mechanism 1.) The pattern is the canonical realisation of Andrew Ng's "multi-agent collaboration" reflection move: distinct experts focused on distinct aspects, mirroring how human review teams are built. Compared to its sibling **R17 Self-Consistency Voting**, O9 differs in *how independence is achieved*: R17 samples one model many times and votes; O9 uses *distinct* critics (different personas, often different models) and *synthesises*. R17 marginalises over stochastic variation; O9 marginalises over deliberately-engineered perspective variation.

## Applicability

Use Multi-Agent Reflection when:

- the output needs to clear **multiple distinct lenses** that a single rubric would dilute (security, performance, accuracy, compliance, style, factuality);
- the cost of a missed defect on any one lens is high enough to justify N parallel critic calls plus a synthesiser;
- you can write **N stable, distinct critic personas** with non-overlapping criteria — if the lenses collapse into the same thing, you are paying for redundancy;
- the loop can tolerate at least one synchronous "all critics finish" barrier per round — fan-out latency is the slowest critic, not the average;
- the generator is strong enough to act on multi-dimensional feedback — small models given five conflicting critiques often regress rather than improve.

Do not use it when:

- one rubric handles all the relevant criteria — use **O5 Evaluator-Optimizer**, which is cheaper and simpler;
- the model is strong and the critic only needs to catch near-misses on a single dimension — use **R8 Self-Refine**;
- an automated check covers the failure mode (tests, schema, executor) — use **R7 Reflexion**, which leverages the deterministic signal directly;
- the task has an objectively correct answer with a modal vote across samples — use **R17 Self-Consistency Voting**, which is cheaper and has tighter convergence properties;
- the critics would argue rather than independently review (advocacy-of-opposing-positions, not lens-based critique) — use **O12 Debate / Deliberation**;
- the latency budget cannot absorb N parallel critic calls plus synthesis — a sequential pipeline of two reviewers is cheaper than a synchronised fan-out.

## Decision Criteria

O9 is right when several distinct lenses must be applied to one output and no single judge can hold all of them well.

**1. Count the lenses.** List the *distinct, non-overlapping* review criteria the output must clear. Practical threshold: **N ≥ 3 lenses with materially different rubrics**. If two of the lenses produce the same critique 80%+ of the time, they are one lens — merge or drop. Fewer than three real lenses → **O5** is enough.

**2. Measure the single-judge miss rate.** On a labelled sample, run O5 with a unified rubric and count defects the judge missed that an independent specialist would catch. **Miss rate > 10% on any single lens** is the empirical signal that the unified judge is diluted. Below that, O5 suffices.

**3. Cost the fan-out.** Each round = N critic calls + 1 synthesis call + 1 generator call. With N = 4 critics, that is ~6× the cost of single-shot. Verify the marginal quality lift over O5 justifies the marginal cost. If only one critic is "load-bearing" and the others rarely fire, pull that critic out as O5.

**4. Independence audit.** Critics must be genuinely independent — separate sessions, ideally separate models. If all critics share the generator's model and persona conditioning is the only difference, fan-out gains are smaller than expected; budget for cross-model or cross-vendor critics where the lens matters most (security, factual grounding). Empirically, same-model critics with different persona prompts produce more correlated critiques than cross-model critics (Du et al. 2023). The mechanism is that token generation is stochastic sampling from a model-specific distribution (mechanism 7); same model + different prompt = different sample from the same distribution; cross-model = different distribution. The fan-out gains are bounded by how different the distributions are. (Mechanisms 1, 7.)

**5. Loop-bound discipline.** Pair with **V9 Bounded Execution** — cap the refinement loop. Without a bound, contradictory critics can hold the generator in an infinite revise cycle (security tightens, performance loosens, security tightens again). Log every critique to **V14 Trajectory Logging** so contradictions are inspectable.

**Quick test — O9 is the right pattern when:**

- ≥ 3 distinct lenses with materially different rubrics must be applied to the same output, *and*
- O5's single-judge miss rate on at least one lens exceeds your reliability budget, *and*
- the budget tolerates N critic calls plus synthesis per round, *and*
- the generator can act on multi-dimensional feedback without regressing.

If only one lens dominates, choose **O5**. If the lenses collapse to one rubric, choose **O5**. If a deterministic check exists, choose **R7 Reflexion**. If the task is parallel-sample-able with a modal answer, choose **R17 Self-Consistency Voting** (one model, N samples, vote — cheaper than N distinct critics). If you want critics to argue, not review, choose **O12 Debate / Deliberation**.

## Structure

```
                          ┌──▶ Critic A (security lens)   ──┐
                          │                                  │
   Output ────▶ Fan-out ──┼──▶ Critic B (performance lens) ──┼──▶ Synthesis Agent ──▶ Consolidated feedback
                          │                                  │           │
                          ├──▶ Critic C (accuracy lens)   ──┤           ▼
                          │                                  │      Generator ──▶ Revised output
                          └──▶ Critic D (style lens)      ──┘           │
                                                                         │
                                                  loop (V9-bounded) ◀────┘
```

## Participants

Each critic owns exactly one lens. The Synthesis Agent owns reconciliation. The Generator owns the work. Mixing any of these is the pattern's most common failure.

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Generator** | producing the output and revising it on synthesised feedback | task + (optionally) prior synthesis → output | self-critique inline or pre-empt the critics — that erodes the independence the pattern is paying for. |
| **Fan-out Coordinator** | dispatching the output to all critics in parallel | output → N critic invocations | wait for critics sequentially, share state between critics mid-call, or let one critic's verdict reach another before synthesis. |
| **Critic A … Critic N** | one lens each, applied independently | output + that critic's rubric → structured critique (issues, severity, suggestions) | see other critics' outputs, see the generator's reasoning, or stray outside its assigned lens. A "security reviewer" that also flags style noise dilutes the pattern. |
| **Synthesis Agent** | consolidating N critiques into one actionable verdict | N critiques → ranked issues + revision brief + pass/fail | re-critique the output itself (it grades critiques, not work), or silently drop a critic's input. Conflicts must be surfaced, not smoothed. |
| **Bound** *(V9 Bounded Execution)* | capping rounds | round counter + max rounds → continue/stop | be absent — without a cap, contradictory critics hold the loop open indefinitely. |
| **Trace** *(V14 Trajectory Logging)* | recording every critique and synthesis decision | round events → durable log | be sampled — the log is how contradictory critics are diagnosed after the fact. |

N typically sits at 3–5 critics. Below 3, O5 is enough; above 5, synthesis quality usually degrades faster than coverage improves. Critics must be wired as independent sessions; same model is acceptable for cheap deployments, but a *mixed-model ensemble* (e.g. one critic from a different vendor) is where the pattern earns its full keep on adversarial lenses like security and factuality.

## Collaborations

The Generator produces an output and hands it to the Fan-out Coordinator. The Coordinator dispatches the output, in parallel, to each of the N critics — each running in its own session with its own persona, rubric, and (often) model. No critic sees any other critic's response. Each returns a structured critique: a list of issues, severities, and concrete suggestions, scoped to that critic's lens. When all N critiques are in, the Synthesis Agent reads the bundle and produces a consolidated verdict: ranked issues, surfaced contradictions where critics disagree, an overall pass/fail, and — on a fail — a revision brief. The Generator iterates on that brief and re-enters the loop. A bound (V9) caps the rounds; a trace (V14) records every critique and every synthesis decision, so contradictions and persistent critic disagreements can be inspected after the fact.

## Consequences

**Benefits**
- Genuinely independent evaluation across multiple lenses — each critic's blind spots are different, so coverage is the union.
- Mixed-model ensembles catch failure modes any single model would systematically miss (e.g. one vendor's safety bias, another's hallucination pattern).
- The synthesis step produces a single, prioritised revision brief — the generator does not have to mediate conflicting critics itself.
- Inspectable: per-critic critiques in the trace let operators see *which* lens caught a defect.

**Costs**
- N critic calls + 1 synthesis call + 1 generator call per round — typically 5–7× the cost of single-shot.
- Latency is the slowest critic, not the average; a slow vendor critic dominates wall-clock time.
- Synthesis is itself an LLM judgment — its quality caps the pattern's value, and a weak synthesiser collapses the fan-out's benefit.
- Critic-persona maintenance: N stable rubrics must be authored and versioned.

**Risks and failure modes**
- *Overlapping critics* — two "critics" producing the same critique 80%+ of the time means you are paying twice for one lens. Audit overlap quarterly.
- *Synthesis bias* — a synthesiser that defers to the loudest critic, or that always concludes "pass", silently undoes the pattern.
- *Contradictory critics, no resolution policy* — security says "tighten", performance says "loosen"; without an explicit precedence rule (encoded in the synthesiser's setup) the generator oscillates.
- *Critic capture* — a critic with vague criteria drifts into general style commentary, ceasing to apply its lens.
- *Generator regression* — small generators given five conflicting critiques often degrade rather than improve; size the generator to the feedback dimensionality.

## Implementation Notes

- Author each critic's persona and rubric as a stable Signal-layer artifact (S3 Persona + S5 Constraint Framing + S6 Output Template). The output template should be a structured critique schema (issues, severity, suggestions) — never free prose — or the synthesiser cannot consolidate cleanly.
- The synthesiser's setup is the most consequential prompt in the pattern. Encode the *precedence rule* explicitly: which lens wins when critics contradict (typically safety/security/factuality > correctness > style).
- Cross-vendor critics are the single biggest lever for genuine independence on adversarial lenses. Budget for at least one critic on a different model family than the generator.
- Pair with **O4 Parallelization** for the fan-out — sequential critic calls erase the pattern's latency advantage and have no quality benefit.
- Pair with **V9 Bounded Execution** (a hard round cap is mandatory) and **V14 Trajectory Logging** (per-critic critiques must be inspectable).
- For high-stakes lenses (security, legal, compliance), the corresponding critic can be a human reviewer via **V1 Human-in-the-Loop** — the fan-out then mixes LLM critics and a human gate.
- Track per-critic *contribution rate* — what fraction of synthesis verdicts that critic's input materially changed. A critic with contribution rate near zero over time should be pruned or merged.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** O9 wraps a Generator session in a fan-out-of-critics + synthesis loop. It composes with **O4 Parallelization** for the critic fan-out, **O5 Evaluator-Optimizer** as the single-judge degenerate case, **V9 Bounded Execution** for the loop cap, and **V14 Trajectory Logging** for the per-round trace. Each critic and the synthesiser are themselves built on Signal-layer patterns: **S3 Persona** for the critic's identity, **S5 Constraint Framing** for the lens boundary, **S6 Output Template** for the structured critique schema.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Generator produces (or revises) the output | `LLM` | Generator session |
| 2 | Fan-out: dispatch the output to N critic sessions in parallel | `code` | O4 |
| 3 | Critic A … N each produce a structured critique under its lens | `LLM` (×N, parallel) | Critic sessions (S3, S5, S6) |
| 4 | Collect all N critiques | `code` | |
| 5 | Synthesis Agent consolidates critiques → ranked issues + revision brief + verdict | `LLM` | Synthesis session |
| 6 | Branch — on PASS return; on FAIL loop to step 1 with the revision brief | `code` | V9 (bound), V14 (trace) |

**Skeleton** — the wiring only; each `# LLM` line is a configured session (specified below):

```
multi_agent_reflection(task, max_rounds):
    output = Generator(task, prior_brief=None) ────────────── # LLM
    for round in range(max_rounds):                          # code — V9 bound
        critiques = parallel([                                # code — O4 fan-out
            CriticA(output),                                  # LLM — security lens
            CriticB(output),                                  # LLM — performance lens
            CriticC(output),                                  # LLM — accuracy lens
            CriticD(output),                                  # LLM — style lens
        ])
        log(round, output, critiques)                         # code — V14
        verdict, brief = Synthesis(critiques) ───────────── # LLM
        if verdict == PASS: return output
        output = Generator(task, prior_brief=brief) ──────── # LLM
    return output                                             # bound reached; return best-so-far
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generator** | the system's main generalist | role (S3); the task spec; how to incorporate a prior synthesis brief on revision rounds; output format (S6) | the task, plus (on later rounds) the prior round's revision brief |
| **Critic A — Security** | generalist *or* a security-tuned model; ideally a different model family than the Generator | role: *"you review code/output for security issues only"*; the security rubric (S5: the explicit lens boundary — only security, not style); structured critique schema (S6: issues, severity, suggestions) | the output to review |
| **Critic B — Performance** | small fast generalist, different setup from Critic A | role: *"you review for performance issues only"*; performance rubric; same structured schema | the output to review |
| **Critic C — Accuracy / Factuality** | strong generalist with retrieval, or a different vendor's model for cross-model independence | role: *"you check factual claims against evidence"*; factuality rubric; structured schema; (optionally) retrieval tools | the output to review |
| **Critic D — Style / Maintainability** | small fast generalist | role: *"you review for clarity, structure, maintainability"*; style rubric; structured schema | the output to review |
| **Synthesis** | strong generalist — *synthesis quality caps the pattern* | role: *"you consolidate N independent critiques into one verdict"*; the **precedence rule** (safety > correctness > style); how to surface contradictions; verdict format (PASS / FAIL + ranked issues + revision brief) | the bundle of N critiques |

**Specialist-model note.** No fine-tuned specialist is required for the core pattern, but two structural choices change the economics: (1) a **mixed-model ensemble** is where O9 earns its full keep on adversarial lenses — having at least one critic on a different model family (different vendor, different training data) is the single biggest lever for genuine independence; (2) for high-stakes lenses (security, legal, factuality) a **fine-tuned specialist critic** — or a **human reviewer via V1** — can replace the corresponding LLM critic without changing the pattern's shape. The Synthesis Agent benefits from the strongest available generalist, paid for once per round rather than N times.

## Open-Source Implementations

- **CAMEL-AI** — [`github.com/camel-ai/camel`](https://github.com/camel-ai/camel) — multi-agent framework with role-playing societies; supports critic-ensemble configurations where multiple specialist agents review a target agent's output.
- **Microsoft AutoGen / AG2** — [`github.com/microsoft/autogen`](https://github.com/microsoft/autogen) and [`github.com/ag2ai/ag2`](https://github.com/ag2ai/ag2) — group-chat patterns wire a Writer agent with multiple nested reviewer-critic agents around a coordinating Critic, directly embodying the ensemble-critique structure. (Microsoft AutoGen is in maintenance mode; AG2 is the active community fork.)
- **ChatEval** — [`github.com/chanchimin/ChatEval`](https://github.com/chanchimin/ChatEval) (mirror: [`github.com/thunlp/ChatEval`](https://github.com/thunlp/ChatEval)) — multi-agent referee team with diverse role prompts; the closest research-grade realisation of "distinct critic personas in parallel, synthesised verdict."
- **Multi-Agent Debate (Du et al.)** — [`github.com/composable-models/llm_multiagent_debate`](https://github.com/composable-models/llm_multiagent_debate) — reference implementation of the ICML 2024 multi-agent debate paper; sibling pattern (O12) but the wiring transfers directly to ensemble critique.

Note: Multi-Agent Reflection is more *architecture* than *library*. The canonical realisation is not a single project but a configuration of a general multi-agent framework (CAMEL, AutoGen/AG2, LangGraph, CrewAI) into N parallel critic agents + a synthesiser. The repos above are the closest direct embodiments; production systems typically wire their own.

## Known Uses

- **Code-review assistants in IDE/PR-bot ecosystems** — multiple specialised reviewers (security scanner agent, performance agent, style agent, test-coverage agent) run in parallel on each PR and a synthesiser produces a single review comment. Pattern is convergent across vendor implementations.
- **AutoGen group-chat production deployments** — Writer + nested Critic with multiple reviewer agents is a documented production recipe in the AutoGen examples and in derivative blog-writing and research pipelines.
- **High-stakes content review pipelines** — legal, compliance, and factuality critics fan out over the same draft (regulated industries: finance, healthcare, pharma marketing).
- **ChatEval-style LLM-as-judge ensembles** for benchmark evaluation — multiple critic personas score the same output; synthesis produces the final score. Increasingly standard in eval rigs where single-judge bias is a known confound.

## Related Patterns

- **Refines** O5 Evaluator-Optimizer — O5 is the single-judge case; O9 generalises the judge to N parallel critics + synthesis. The pattern boundary is "one judge or many."
- **Sibling of** R17 Self-Consistency Voting — both achieve reliability through multiple independent assessments. R17 samples *one* model many times and votes (independence via stochastic variation); O9 uses *distinct* critic agents (independence via deliberately-engineered perspective variation) and synthesises. R17 is cheaper; O9 covers multi-lens review R17 cannot.
- **Distinct from** R8 Self-Refine — R8 is *one* model in three roles; O9 is *many* agents with distinct personas, often distinct models. R8 shares blind spots by construction; O9 is built to break them.
- **Distinct from** O12 Debate / Deliberation — O9 critics independently *review* (lens-based critique, no cross-talk); O12 agents *argue* opposing positions and rebut each other before synthesis. O9 marginalises over perspectives; O12 stress-tests through adversarial exchange.
- **Composes with** O4 Parallelization — the critic fan-out is an O4 sectioning move; sequential critics erase the latency benefit with no quality gain.
- **Composes with** V9 Bounded Execution — contradictory critics can hold the loop open indefinitely without a cap.
- **Composes with** V14 Trajectory Logging — per-critic critiques must be inspectable for contradiction diagnosis and contribution-rate audits.
- **Pairs with** V1 Human-in-the-Loop — a high-stakes lens (legal, safety) can be a human critic in the fan-out, mixing LLM and human reviewers without changing the pattern's shape.
- **Pairs with** V15 LLM-as-Judge — every critic in O9 is an LLM-as-Judge instance; O9 is the orchestration that turns N V15 calls into a single verdict.
- **Uses** S3 Persona, S5 Constraint Framing, S6 Output Template — each critic's session is built from Signal-layer artifacts; structured critique schemas (S6) are what make synthesis tractable.

## Sources

- Ng, A. (2024) — "Agentic Design Patterns" series; *Multi-Agent Collaboration* as one of four core patterns. The clearest articulation of distinct critic agents focused on distinct aspects.
- Du, Y. et al. (2023) — "Improving Factuality and Reasoning in Language Models through Multiagent Debate" (arXiv 2305.14325; ICML 2024). Empirical demonstration that multi-agent critique improves accuracy and reasoning over single-agent baselines.
- Chan, C.-M. et al. (2023) — "ChatEval: Towards Better LLM-based Evaluators through Multi-Agent Debate" (arXiv 2308.07201). Diverse role prompts as the operational mechanism for genuine independence.
- Anthropic — "Building Effective Agents" (2024). Frames the evaluator-optimizer / multi-critic axis as a core workflow pattern.
- arXiv 2601.03624 — 46-pattern multi-agent catalog; ensemble-critique and debate variants distinguished.
