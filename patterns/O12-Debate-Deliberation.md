# O12 — Debate / Deliberation

> Stage two or more agents arguing *opposing* positions on the same question across several rounds, then have a separate synthesiser agent (or human) weigh the exchange and produce the final answer — using adversarial argument as the mechanism that surfaces what a single agent's reasoning hides.

**Also Known As:** Multi-Agent Debate (MAD), Devil's Advocate, Adversarial Deliberation, Self-Play Scientific Debate (Google Co-Scientist's framing). (No formally named sub-variants; the relevant configuration choices — number of debaters, number of rounds, judge vs. tournament aggregation, same-model vs. cross-model debaters — are tuning parameters rather than separate patterns.)

**Classification:** Category IV — Orchestration · Band IV-C Specialised Coordination · the *adversarial multi-agent deliberation* pattern — distinct from O5 Evaluator-Optimizer (one critic on one draft), O9 Multi-Agent Reflection (N independent critics on one draft, no cross-talk), and O11 Blackboard (shared state, cooperative accumulation).

---

## Intent

Use *adversarial argument between agents holding opposing positions* — not independent critique, not iterative self-refinement — to surface the assumptions, counter-evidence, and failure modes a single agent's reasoning would not see, then synthesise the exchange into a more accurate or better-considered final answer.

## Motivation

Single-agent reasoning, even with reflection, shares its own blind spots. Reflexion (R7), Self-Refine (R8), and even Evaluator-Optimizer (O5) all leave the *position* unchallenged: the agent (or critic) starts from somewhere, and the loop refines that starting position rather than contesting it. When the starting position is subtly wrong — a hidden premise, an unjustified causal claim, a missed alternative — refinement polishes the wrong answer.

Multi-Agent Reflection (O9) gets *more eyes* on the output but each pair of eyes operates independently: critic A doesn't see critic B's view, no one is *committed* to a position, and the synthesis combines parallel verdicts rather than weighing a contest. O5 is one judge on one draft; O9 is N judges on one draft; both are *evaluation* topologies — they grade work that already exists.

Debate is structurally different. Two or more agents are *assigned opposing positions* and must defend them across multiple rounds, each round reading what the other side has just said and being required to respond to it. The mechanism is **commitment and rebuttal**: an agent assigned the contrarian position must find the strongest objection to the consensus view and the consensus agent must reply to it specifically. Du et al. (2023) showed empirically that this surfaces errors single-agent chains miss — on arithmetic, MMLU, and biographical factuality — and that the gains come specifically from the *cross-talk*, not from sampling more answers (which is R17 Self-Consistency Voting's mechanism).

The pattern was elevated by Google DeepMind's AI Co-Scientist (2026 *Nature* paper), where "self-play scientific debate" is the core hypothesis-improvement loop: a Generation agent proposes a hypothesis, debater agents argue for and against, and a Reflection / Meta-review agent synthesises. The hypotheses that emerge are measurably stronger than single-agent generations against the same literature — the adversarial structure is the load-bearing element.

The defining claim is *adversarial assignment*: **two or more agents must hold and defend opposing positions across multiple rounds, with cross-reading**. Strip any of those — same position, single round, no requirement to engage the other's argument — and you no longer have O12; you have O9, O5, or R17. The pattern earns its number on the structural fact that adversarial argument surfaces what consensus reasoning conceals.

## Applicability

Use Debate / Deliberation when:

- a single agent or a same-direction ensemble produces *confidently wrong* answers on the task — failure mode is over-confidence, not under-confidence;
- the question admits genuinely contested positions where the right answer depends on weighing evidence (factual claims under uncertainty, strategic decisions, hypothesis evaluation, risk assessment, ambiguous interpretation);
- you can afford 2 $\times$ R $\times$ N LLM calls (R debaters $\times$ N rounds + synthesis), typically 6–15 calls per question;
- the synthesis step has a meaningful judgment to make — i.e., a coherent synthesiser agent (or human) exists to weigh the exchange;
- the question is *substantive enough* to support multi-round argument; trivial questions degenerate to "agree" by round 2.

Do not use it when:

- a deterministic check exists — use **R7 Reflexion** instead; the test runner is a stronger signal than two agents disagreeing;
- the goal is to combine *independent* critical lenses (security, performance, style) without cross-talk — use **O9 Multi-Agent Reflection**, which is parallel critique, not debate;
- the goal is to converge on a modal answer across independent samples — use **R17 Self-Consistency Voting**, which marginalises over samples at lower marginal cost than staged debate;
- the goal is one judge scoring one draft for refinement — use **O5 Evaluator-Optimizer**;
- the goal is cooperative accumulation of contributions toward a shared solution — use **O11 Blackboard**;
- latency is tight — debate is multi-round and sequential by construction; wall-clock scales with rounds;
- debaters share training distribution so completely that they fall into immediate agreement — the adversarial assignment must produce *real* disagreement, not staged agreement.

## Decision Criteria

O12 is right when over-confidence is the binding failure mode, the question is contested enough to support real argument, and the budget tolerates the round-by-round cost.

**1. Test for over-confident wrong answers before reaching for O12.** On a labelled sample, run single-agent (or O9) on the task. Compute the **confident-wrong rate** — answers given with high stated confidence that humans judge wrong. If that rate is **> 15%** *and* the wrong answers cluster around a particular kind of mistaken premise (a missed counter-example, a wrong causal direction, a confused definition), O12 will catch them; the adversarial side is built to find exactly that. If wrong answers are scattered noise rather than systematic over-confidence, O12 will not help — use **R17 Self-Consistency Voting** to marginalise the noise instead.

**2. Confirm the question supports contested positions.** Some questions have a single correct answer no amount of debate will change (10 $\times$ 7 = 70). Others have an evidentially-supported answer where the wrong-but-plausible alternative is a real position someone could defend (the medical differential, the strategic call, the historical attribution, the scientific hypothesis). O12 only earns its cost on the second kind. Audit a sample: if the contrarian role keeps trivially capitulating in round 2, the question is not contested enough.

**3. Pick R debaters and N rounds.** Standard configurations: **R = 2 debaters, N = 2–3 rounds** (the Du et al. setup; minimum viable). **R = 3+ debaters** for multi-position questions (Co-Scientist tournament-style). Beyond **N = 4 rounds** is almost always wasted — debaters either converge or harden into restatement. The judge fires once at the end (or after each round in tournament configurations).

**4. Pick the synthesiser model deliberately.** The synthesiser is doing the load-bearing judgment work. A cheaper model can be a *debater* (the position constrains the role), but the synthesiser must be at least as capable as the strongest debater — typically the system's main frontier model, set up explicitly as a meta-reasoner ("weigh the strongest argument from each side; identify what the debate established and what remains contested; produce the final answer with a stated confidence"). Tournament configurations (Co-Scientist) replace the single synthesiser with Elo-style pairwise comparisons across many hypotheses.

**5. Cost the loop honestly.** Per question: **R $\times$ N debater calls + 1 synthesiser call**, typically **6–15 LLM calls** at R = 2, N = 2–3. At frontier-model rates this is 6–15$\times$ single-shot cost. Pair with **V9 Bounded Execution** for hard caps on rounds; the synthesiser's stopping signal is *soft*. For tournament configurations, costs multiply by the hypothesis count — Co-Scientist runs hundreds to thousands of pairwise debates per session.

**Quick test — O12 is the right pattern when:**

- the failure mode is confident-wrong answers from systematic premise errors (rate > 15% on labelled sample), *and*
- the question admits a genuinely defensible contrarian position (the debate doesn't collapse to immediate agreement), *and*
- 6–15$\times$ single-shot cost is affordable for the question's stakes, *and*
- a capable synthesiser exists to weigh the exchange (human or strong LLM), *and*
- multi-round latency is acceptable.

If the failure mode is scattered noise rather than confident wrong, use **R17 Self-Consistency Voting**. If you need independent critical lenses without cross-talk, use **O9 Multi-Agent Reflection**. If you have an automated check, use **R7 Reflexion**. If the task is cooperative accumulation, use **O11 Blackboard**. If one judge on one draft is the topology, use **O5 Evaluator-Optimizer**.

## Structure

```
                        Question
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        Debater A      Debater B      (Debater C …)
        (position α)   (position β)   (position γ)
              │             │             │
              ▼             ▼             ▼
            round 1 opening statements  ←─────────┐
              │             │             │       │
              └─────► cross-read ◄────────┘       │
                            │                     │
                            ▼                     │ V9-
                       round 2: rebuttals ────────┤ bounded
                            │                     │ rounds
                            ▼                     │
                       round 3: closing ──────────┘
                            │
                            ▼
                    Synthesiser (Agent S)
                    reads the full exchange
                            │
                            ▼
                  Final answer + rationale
                  (what the debate established,
                   what remains contested)

  Stop: V9 round cap reached  OR  debaters converge  OR  synthesiser fires.
  Debaters and synthesiser are distinct agents — separate sessions, separate setups.
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Debater agents (A, B, …)** | defending an *assigned position* across rounds; reading the other side's last move and responding to it specifically | question + assigned position + transcript so far $\to$ next-round argument | switch positions mid-debate, refuse the assigned position, or ignore the other side's argument. The pattern's claim ("adversarial argument") collapses if debaters capitulate early or talk past each other. Each debater is set up *for its position*, not for the question in general. |
| **Position assigner** | mapping the question to the set of opposing positions before debate starts (consensus vs contrarian; multiple competing hypotheses; pro vs con) | question $\to$ {position_a, position_b, …} | leak its own verdict into the assignment. The assigner sets up the *frame*; it does not pre-judge the outcome. In simple binary debates this can be a deterministic rule; in hypothesis tournaments (Co-Scientist) this is the Generation agent's job. |
| **Debate moderator** *(optional, code)* | sequencing the rounds, threading transcripts to each debater, enforcing the round cap | round state $\to$ next debater's call | rewrite or summarise debater arguments — debaters must read each other's *actual* words. A moderator that paraphrases is editorialising the debate. |
| **Synthesiser agent (S)** | reading the full exchange and producing the final answer with rationale, stated confidence, and explicit notes on what remains contested | question + full debate transcript $\to$ final answer + rationale | be one of the debaters. The synthesiser must be a *separate session* with no assigned position; otherwise it is a debater in judge's clothing and the synthesis collapses to advocacy. |
| **Iteration log** *(V14)* | the full transcript of (round, debater, argument) across rounds plus the synthesiser's final | sequence of rounds $\to$ V14 trajectory record | be hidden or summarised away. The transcript is the pattern's primary audit artefact — operators distinguish genuine adversarial reasoning from staged agreement *only* by reading it. |

Three structural invariants make the pattern work:

- **Debaters hold assigned positions; the synthesiser holds none.** This is the rule that buys the adversarial structure. A debater who can "decide for itself" mid-debate is a same-side ensemble.
- **Debaters cross-read.** Every round after the first carries the *other side's last move* into the prompt and explicitly demands a response to it. Debaters who do not read each other are running in parallel, not debating.
- **Synthesiser is a distinct session.** Same model is fine; different setup, different prompt, no assigned position. Mixing a debater session with the synthesiser destroys the independence claim.

## Collaborations

The Position assigner reads the question and decides the frame: consensus vs contrarian on a factual claim, two competing hypotheses on a scientific question, optimistic vs pessimistic on a risk assessment, multiple candidate plans on a strategic choice. The Debate moderator (typically code) instantiates one Debater agent per position. In round 1, each debater opens with its case — its strongest argument for the assigned position, given the question. The moderator collects the round-1 transcripts and threads them into the next round's prompt: each debater now sees what every other debater said and must produce a *rebuttal* — engage the strongest counter-argument, defend the position against it. Rounds continue under the V9-bounded cap; debaters may concede points but must not switch positions. When the round cap is hit (or debaters explicitly converge), the moderator hands the full transcript to the Synthesiser agent — a fresh session with no assigned position, set up as a meta-reasoner. The Synthesiser produces the final answer with rationale, explicitly noting what the debate established, what remains contested, and the confidence with which the answer is given. The full transcript and the synthesis are logged via **V14 Trajectory Logging** as the audit artefact. In tournament variants (Co-Scientist), the synthesiser is replaced by pairwise Elo comparison across many parallel debates, and the strongest hypothesis emerges from the ranking rather than from a single meta-call.

## Consequences

**Benefits**

- Surfaces confident-wrong answers single-agent and same-direction-ensemble approaches miss — the adversarial assignment forces engagement with the strongest objection.
- Empirically improves factuality and reasoning on hard tasks (Du et al. 2023: gains on arithmetic, MMLU, biographies over single-agent and over self-consistency).
- The transcript itself is an explanatory artefact: operators can read *why* the answer is what it is, not just what it is — useful for trust calibration in high-stakes domains.
- Tournament variants (Co-Scientist) scale to large hypothesis spaces where pairwise comparison is tractable but full evaluation is not.
- Composes cleanly with **V15 LLM-as-Judge** (the synthesiser is V15's canonical use case in tournament configurations), **V9 Bounded Execution** (round cap), and **V14 Trajectory Logging** (the transcript is the artefact).

**Costs**

- **6–15$\times$ single-shot cost** at R = 2, N = 2–3; tournaments are an order of magnitude beyond that.
- Strictly sequential within a debate — wall-clock latency scales with rounds; parallelism only exists across debates, not within one. Each debater call is a fresh API invocation; the KV cache does not persist across API calls (mechanism 3). Each round therefore pays full prefill on the accumulated transcript. The per-round cost grows with transcript length: by round 3, each debater is prefilling round 1 + round 2 transcript before generating its response. Prefix caching (mechanism 5) helps for the stable system-prompt portion but not for the growing debate transcript. (Mechanisms 3, 5.)
- Setup complexity: position assignment, per-round transcript threading, synthesiser prompt all need careful design.
- Debater setup is per-position prompt-engineering work — adding a position is non-trivial.

**Risks and failure modes**

- *Staged agreement* — debaters fall into immediate consensus in round 1 because the assigned positions are not genuinely defensible or the prompt does not enforce commitment. Symptom: round-2 transcripts are restatements with "I agree." Mitigation: stronger position-commitment framing in debater setup ("you must defend this position; if you find it indefensible, state the strongest available defence and the conditions under which it would hold"); calibrate against samples where the contrarian view is known to be right.
- *Shared-bias convergence* — debaters trained on the same data converge on the same wrong answer because both sides share the underlying bias. Symptom: O12 produces the same confident-wrong answer single-agent does, just with more text. Mitigation: cross-model debaters (different providers, different training distributions); explicit "steel-man the contrarian view from these specific sources" framing. The mechanism is shared attention geometry. Two instances of the same model compute Q_α K^α under identical W_Q and W_K matrices (mechanism 1). Any feature class that the model's bilinear form assigns low inner product to — e.g. a class of counter-examples systematically under-represented in training — will receive low attention scores from both debaters, regardless of which position they are assigned. Cross-model debaters use different bilinear forms; the under-attended feature class for model A may be correctly attended to by model B because B's projection matrices define different token-similarity geometry. (Mechanism 1.)
- *Synthesiser bias toward consensus* — the synthesiser defaults to whichever side spoke last or whichever had more words. Symptom: final answers track surface features rather than argument quality. Mitigation: synthesiser setup requires *naming the strongest argument from each side* before producing the verdict; structured output contract (S6) makes this auditable.
- *Hardening into restatement* — debaters stop engaging by round 3 and just restate. Symptom: round-N transcript is nearly identical to round-(N-1). Mitigation: round cap at N = 3–4 with progress detection; if rounds 2 and 3 do not introduce new arguments, the moderator stops the debate.
- *Adversarial drift* — debaters get progressively more uncharitable (straw-manning, ad hominem-style framing). Symptom: the debate stops being about the question. Mitigation: explicit "engage the strongest version of the opposing argument" framing in debater setup; calibrate against samples.
- *Synthesiser captured by a debater* — when the synthesiser uses the same model as one debater and reads that debater's framing, the synthesis tracks that side. Mitigation: cross-model synthesiser; or rotate debater model assignments across the run.
- *Unbounded debate* — without **V9 Bounded Execution**, a stubborn pair can argue indefinitely. The synthesiser's stopping signal is soft; V9 is the hard cap.

## Implementation Notes

- **The position assigner is the load-bearing first step.** A weak frame ("consider both sides") produces weak debates. A strong frame ("Position A: claim X is true because of Y; Position B: claim X is false because of Z") produces real argument. Spend prompt-engineering time here.
- **Cross-model debaters are the high-quality default.** Same-model debate (often used in the Du et al. paper for tractability) works, but shared training distribution is the pattern's single biggest threat. When the stakes warrant it, deploy debaters on different providers or different model families.
- **Synthesiser must be a separate session.** Same model is fine; different setup, different prompt, *no assigned position*. The synthesiser is set up as a meta-reasoner — its job is to weigh the exchange, not to advocate.
- **Use structured output for the synthesis.** A V15/S6-style contract: `{ "answer": ..., "confidence": ..., "established": [...], "contested": [...], "key_argument_a": ..., "key_argument_b": ... }`. Free-form prose synthesis is hard to audit and hard to consume programmatically.
- **Start at R = 2 debaters, N = 2 rounds.** Tune up only if quality data shows gains. Round 3 helps occasionally; round 4 almost never.
- **Pair with V14 Trajectory Logging — non-negotiable.** The transcript is the artefact. Without it, you cannot tell adversarial reasoning from staged agreement.
- **Pair with V9 Bounded Execution.** Cap rounds and total LLM calls per debate. The cap is the hard stop; convergence is the soft one.
- **For hypothesis-generation domains, consider the tournament variant** — replace the single synthesiser with Elo-style pairwise comparisons across many candidate hypotheses, as in Google's Co-Scientist. This is O12 scaled across a candidate set; each pairwise comparison is one O12 debate.
- **Composes upward into O6 Orchestrator-Workers** — O12 is a natural sub-task an orchestrator delegates when a question needs adversarial deliberation rather than direct generation.
- **Compose with V1 Human-in-the-Loop** for the synthesiser role on high-stakes decisions — humans are excellent synthesisers of LLM debates.

## Implementation Sketch

> `LLM = configured session (model + setup + per-call prompt); code = wiring.`

**Composition:** O12 chains R debaters (each its own session, each with an assigned position) with a separate Synthesiser session, under a code-driven debate moderator. It draws on **V15 LLM-as-Judge** as the synthesiser's mechanism, **S3 Persona** for assigning positions to debaters, **S6 Output Template** for the synthesiser's structured verdict, **V9 Bounded Execution** for the round cap, and **V14 Trajectory Logging** for the full transcript. O12 commonly composes upward into **O6 Orchestrator-Workers** (orchestrator delegates contested questions to a debate sub-task) and pairs with **V1 Human-in-the-Loop** for synthesis on high-stakes work.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Position assigner maps question to {position_a, position_b, …} | `code` (or `LLM`) | Optional Assigner session |
| 2 | Each Debater agent produces round-1 opening statement | `LLM` ($\times$ R) | Debater A, B, … sessions (S3) |
| 3 | Moderator threads transcripts; each Debater produces round-r rebuttal engaging the others | `LLM` ($\times$ R per round) | Debater sessions |
| 4 | Branch — if round cap, convergence, or no-progress, exit loop | `code` | V9 |
| 5 | Log full transcript per round | `code` | V14 |
| 6 | Synthesiser reads full transcript and produces final answer with structured rationale | `LLM` | Synthesiser session (V15, S6) |
| 7 | *(tournament variant)* Pairwise Elo comparison across N candidate debates | `LLM` ($\times$ many) | Comparator session |

**Skeleton** — the wiring only; each `# LLM` line is a configured session on its own agent:

```
debate(question, n_debaters=2, max_rounds=3):
    positions = assign_positions(question, n_debaters)         # code (or LLM)
    transcript = []
    for r in range(max_rounds):                                # code — V9-bounded loop
        round_args = []
        for i in range(n_debaters):
            arg = Debater_i(question, positions[i], transcript)  # LLM — debater i
            round_args.append(arg)
        transcript.append(round_args)
        log(r, round_args)                                      # code — V14
        if converged(round_args) or no_progress(transcript):    # code — soft stops
            break
    return Synthesiser(question, transcript)                    # LLM — Synthesiser (V15)
```

**The LLM sessions.** R + 1 distinct agents (R debaters + 1 synthesiser); same model is acceptable, different setups are mandatory.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Debater A** *(and B, C, …)* | capable generalist per side; **cross-model preferred** when shared-bias convergence is a risk | role (S3): *"you are an advocate for position {α}. You must defend this position with the strongest available arguments, engage the other side's strongest objections directly, and concede sub-points where honest while maintaining your position. If the position is genuinely indefensible, state the strongest available defence and the conditions under which it would hold."*; the **assigned position** (concrete claim, key supporting evidence); the rules of engagement (round count, expected length, "engage the other side's last argument specifically"); output format. **The other side's position is described, but not advocated for.** | the question + the transcript of all prior rounds + an explicit "respond to {other debater}'s round-{r-1} argument" instruction |
| **Synthesiser** | the system's strongest generalist, or a *different* model from the debaters when cross-model coverage matters | role: *"you read a multi-round debate and produce the considered final answer. Name the strongest argument from each side, identify what the debate established and what remains contested, then produce the answer with stated confidence."*; output contract (S6) — structured `{ answer, confidence, established[], contested[], key_arg_a, key_arg_b }`; explicit "do not default to whichever side spoke last; weigh argument quality, not surface features" framing. **No assigned position.** | the question + the full debate transcript |
| **Position assigner** *(optional, LLM)* | small fast generalist | role: *"given a question, identify the strongest opposing positions that should be debated. Return them as concrete claims with key supporting evidence."*; output contract — `{ positions: [{name, claim, key_evidence}] }`. **Does not produce a verdict.** | the question |

Concretely, for a factual-claim debate (the Du et al. setup): the Debater-A setup loaded once is *"You are an advocate for position α: 'X is true'. In each round, defend α with the strongest available evidence and engage the most recent counter-argument from your opponent specifically. Concede sub-points where honest, but do not abandon α unless logically forced. End each turn with the single sentence stating the position you currently hold."* The per-call prompt wraps only *"Question: {question}. Transcript so far: {transcript}. Respond to your opponent's round-{r-1} argument."*

**Specialist-model note.** No fine-tuned specialist is required, but two structural choices change everything:

- **Debaters and Synthesiser must be distinct sessions.** Same model is acceptable for cost reasons; different setup, different prompt, no shared session. Same-session O12 collapses to multi-prompt single-agent reasoning.
- **Cross-model debaters are the high-quality configuration.** When debaters share training distribution, they share blind spots — the load-bearing claim ("argument surfaces what consensus reasoning conceals") weakens. The cheapest meaningful upgrade from same-model O12 is to put one debater on a different provider's frontier model. For research-grade deployments (Co-Scientist), debater diversity is treated as a system requirement.

## Open-Source Implementations

- **`llm_multiagent_debate`** — [`github.com/composable-models/llm_multiagent_debate`](https://github.com/composable-models/llm_multiagent_debate) — official Du et al. (2023) implementation; ICML 2024. Reference code across arithmetic, GSM, biographies, and MMLU. The canonical academic implementation.
- **MAD — Multi-Agents Debate** — [`github.com/Skytliang/Multi-Agents-Debate`](https://github.com/Skytliang/Multi-Agents-Debate) — Liang et al. (2023) "Encouraging Divergent Thinking" implementation. Two-debater + judge architecture explicitly designed to prevent the "Degeneration of Thoughts" failure mode in single-agent reflection. Often cited alongside the Du et al. work.
- **MALLM (Multi-Agent Large Language Models Framework)** — [`github.com/Multi-Agent-LLMs/mallm`](https://github.com/Multi-Agent-LLMs/mallm) — research framework (2025) for configurable debate paradigms, personas, response generators, and decision protocols; integrated evaluation. The most general-purpose debate harness.
- **`mad_llm`** — [`github.com/rajeshkochi444/mad_llm`](https://github.com/rajeshkochi444/mad_llm) — CrewAI-based community implementation of Multi-Agent Debate; useful as a minimal worked example rather than a production framework.
- **Tournament-style variant (Co-Scientist)** — no public reference implementation; the architecture is described in Google DeepMind's 2026 *Nature* paper and blog posts, but the production system is not open-source. The closest public approximations build on `llm_multiagent_debate` with Elo-style ranking layered on top.

## Known Uses

- **Google DeepMind AI Co-Scientist** (2026 *Nature* paper) — "self-play scientific debate" is the core hypothesis-improvement mechanism. Generation agent proposes hypotheses; debater agents argue for and against; a Ranking agent runs a tournament of pairwise debates with Elo scoring; the Evolution agent refines top-ranked hypotheses. Deployed via Gemini for Science.
- **Du et al. (2023) experimental deployments** — improved factuality on arithmetic, MMLU, and biographical generation tasks over single-agent and self-consistency baselines.
- **Hypothesis-evaluation pipelines in pharma and drug discovery** — small but growing class of deployments using Co-Scientist-style debate to triage candidate hypotheses before expensive wet-lab follow-up.
- **Adversarial red-team / blue-team agentic systems** — security and policy domains where one agent argues a proposed action is safe and another argues it is unsafe, with synthesis (often human) determining whether to proceed.
- **MALLM framework deployments** — research and educational uses of configurable multi-agent debate for evaluation studies on bias, factuality, and cultural alignment.

## Related Patterns

- **Distinct from O9 Multi-Agent Reflection** — same multi-agent surface, different mechanism. O9 is **N independent critics** on one output, each operating without cross-talk; the synthesis combines parallel verdicts. O12 is **agents assigned opposing positions** who must read and respond to each other across rounds; the synthesis weighs an *argued exchange*. O9 catches what one critic misses by covering more dimensions in parallel; O12 catches what consensus conceals by forcing adversarial engagement. O12 is *not* O9 with more critics — the adversarial assignment and cross-reading are the structural difference.
- **Distinct from O5 Evaluator-Optimizer** — O5 is **one judge on one draft**, iterating refinement of the draft. O12 is **multiple agents arguing positions**, with synthesis at the end. O5's loop refines a single trajectory; O12's loop generates a contested transcript.
- **Distinct from R17 Self-Consistency Voting** — same "multiple samples" surface, different mechanism. R17 samples the *same agent* N times and takes the modal answer — it marginalises noise, but cannot escape shared bias because every sample comes from the same head. O12 samples *different positions* on the same question and forces engagement — it can escape shared bias when debaters are cross-model. Du et al. (2023) showed debate gains over self-consistency on the same tasks.
- **Distinct from O11 Blackboard** — O11 is *cooperative accumulation* (agents contribute to a shared state toward a joint solution); O12 is *adversarial argument* (agents commit to opposing positions and contest them). Different mechanism, different topology.
- **Pairs with V15 LLM-as-Judge** — V15 is the canonical synthesiser mechanism. The synthesiser fires once at the end of debate; in tournament variants, V15 fires once per pairwise comparison.
- **Pairs with V9 Bounded Execution** — mandatory. The round cap is the hard stop.
- **Pairs with V14 Trajectory Logging** — the full transcript is the pattern's primary audit artefact. Without the log, staged agreement is indistinguishable from adversarial reasoning.
- **Pairs with V1 Human-in-the-Loop** — for the synthesiser role on high-stakes work; humans synthesise LLM debates well.
- **Composes with S3 Persona** — position assignment is a Signal-layer persona move applied to the debater's setup.
- **Composes with S6 Output Template** — the synthesiser's structured verdict contract.
- **Composes upward into O6 Orchestrator-Workers** — an orchestrator can delegate a contested question to an O12 debate sub-task when direct generation would be over-confident.
- **Tournament variant** — when scaled across a candidate set with pairwise Elo ranking (Co-Scientist), O12 becomes the unit of comparison in a larger evaluation tournament.

## Sources

- Du, Y., Li, S., Torralba, A., Tenenbaum, J., Mordatch, I. (2023) — "Improving Factuality and Reasoning in Language Models through Multiagent Debate" — [arXiv:2305.14325](https://arxiv.org/abs/2305.14325) — ICML 2024. The canonical paper; introduces the cross-talk + multi-round + synthesis structure and demonstrates empirical gains on arithmetic, MMLU, and biographies.
- Liang, T. et al. (2023) — "Encouraging Divergent Thinking in Large Language Models through Multi-Agent Debate" — [arXiv:2305.19118](https://arxiv.org/abs/2305.19118). Introduces the MAD framework explicitly designed to prevent the "Degeneration of Thoughts" failure mode in single-agent reflection.
- Google DeepMind (2026) — "Co-Scientist: A multi-agent AI partner to accelerate research" — [deepmind.google/blog/co-scientist](https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/) and the accompanying 2026 *Nature* paper. Describes the self-play scientific debate architecture: Generation + Reflection + Ranking (tournament) + Evolution + Meta-review.
- Anthropic (2024) — "Building Effective Agents" — [anthropic.com/research/building-effective-agents](https://www.anthropic.com/research/building-effective-agents). Discusses adversarial multi-agent patterns alongside the five canonical workflow patterns.
- 46-Pattern Catalog — arXiv:2601.03624 — "Debate / Deliberation" entry in the broader multi-agent pattern survey.
- MALLM (2025) — "Multi-Agent Large Language Models Framework" — arXiv:2509.11656 — a configurable framework for multi-agent debate as research infrastructure.
