# V16 — Offline Eval

> Validate agent behaviour against a curated suite of known scenarios and reference outputs **before** production deployment, so regressions, drift, and capability gaps are caught against ground truth rather than discovered by users.

**Also Known As:** Regression Testing, Pre-Production Eval, Validation Suite, Eval Harness, Eval-Driven Development.

**Classification:** Category V — Reliability · Band V-C Observability and Evaluation · the *pre-deployment gate* — a test harness, distinct from V17's live monitoring, that turns "ship-or-don't" into a measured decision against a held-out set.

---

## Intent

Establish a held-out, versioned suite of inputs and expected outputs (or pass criteria), run it against the agent on every change, and gate deployment on the result — so quality, safety, and cost have a numeric baseline that any change must clear before it reaches users.

## Motivation

Production LLM systems fail in a characteristic way: an isolated change — a new prompt, a new model version, a refactored tool, a new MCP server — quietly degrades behaviour on cases nobody thought to recheck. Without a regression suite, the degradation is discovered downstream when a user complains, a customer churns, or a safety incident lands. The Composio AI Agent Report 2025 attributes the 88% production-failure rate primarily to *pilot simplification* (A13) — agents tested informally against a few hand-picked happy paths, then shipped into the messy, adversarial, edge-case-rich reality of real traffic.

**Why offline evaluation is a baseline requirement, not a nice-to-have (mechanism 7).** Token generation is stochastic sampling from a learned probability distribution (mechanism 7). The same prompt, agent, and test case may produce correct output on one run and incorrect output on another. A single "it worked" test proves nothing about the system's actual reliability — it proves only that one sample from the distribution was acceptable. Offline evaluation over a representative benchmark establishes the *distribution* of outputs, not a single sample: it measures pass-rate, failure modes, and the rate of edge-case failures across many inputs. Without this baseline, a code change that shifts the distribution adversely — increasing the rate of a specific failure mode while leaving common cases unchanged — is invisible until it reaches production.

The naive alternative is **vibe-checking** (anti-pattern A6): the engineer prompts the agent with a handful of cases, judges the outputs by eye, and ships. Vibe-checking has no memory. It cannot tell you whether yesterday's known-good case still passes. It cannot tell you whether the new model handles the adversarial cases the old one had been hardened against. It cannot answer the only question a deployment gate needs to answer: *is this change a regression?* That requires a frozen set of cases, a frozen way of scoring them, and a comparison to a frozen baseline.

V16 is that gate. The defining move is the **held-out golden set with deterministic scoring**: inputs you have already decided the agent must handle, expected outputs (or criteria the output must satisfy), and a scoring mechanism that produces a number you can compare to last week's number. Ground truth is the load-bearing element — it is what makes V16 *offline* and distinct from V17 *online* eval, which monitors live traffic without ground truth and therefore cannot tell capability change apart from input-distribution change. V16 catches *known* regressions deterministically; V17 catches *unknown* regressions probabilistically. A production system needs both, and V16 must come first.

## Applicability

Use Offline Eval when:

- a change to prompts, model, tools, or orchestration logic is about to ship;
- the agent has a stable enough specification that "right answer" or "acceptable answer" can be defined per case;
- regressions on previously-handled cases are unacceptable (which is almost always);
- adversarial or compliance-sensitive behaviours must be re-verified on every deploy;
- a new model version is being adopted and the team needs to know what changes.

Do not rely on Offline Eval alone when:

- the agent runs on a fast-shifting input distribution where the golden set goes stale weekly — pair with **V17 Online Eval** for live drift detection;
- the system is multi-agent and emergent behaviour cannot be captured in flat case/answer pairs — pair with **V18 Agent Simulation**;
- the task has no defensible ground truth at all and no rubric a judge can apply consistently — that is a sign the task itself is under-specified, not that V16 is wrong; tighten the spec or use **V1 Human-in-the-Loop** as the gate instead;
- the team will not maintain the golden set — an unmaintained V16 suite degrades into theatre faster than no suite at all.

## Decision Criteria

V16 is right when there is a deploy event to gate, a definition of "correct enough" per case, and a team willing to keep the golden set alive.

**1. Is there a deploy event?** V16 is gate-shaped. If the system updates continuously without a deploy boundary (live online-learning agent, prompt edited in production), V16 has nowhere to attach — use **V17 Online Eval** plus **V10 Checkpointing** for safe rollback instead. Threshold: at least one defined "before users see this" moment per change.

**2. Can correctness be specified per case?** For each candidate case, decide what makes an output acceptable. Options, in increasing flexibility: (a) **exact match** or schema match against a reference — best where the format is rigid; (b) **structured criteria** the output must satisfy (`contains_fact_X`, `cites_source`, `refuses_request`) — best for tool-using or structured-extraction tasks; (c) **rubric-based scoring via V15 LLM-as-Judge** — required where many distinct outputs are equally valid. If none of these can be specified for a case, drop it from the golden set; do not paper over with vibe-checking.

**3. Does the golden set cover the failure modes that matter?** Required categories: (a) **positive cases** — representative correct-behaviour examples; (b) **negative cases** — inputs the agent must refuse or escalate; (c) **edge cases** — unusual-but-valid inputs that break naive implementations; (d) **adversarial cases** — injection attempts, jailbreaks, boundary probes (these double as **V6 Prompt Injection Shield** regression tests); (e) **regression cases** — every bug fixed in production becomes a permanent case here. Threshold: if categories (b)–(e) are empty, the suite is happy-path-only and will give false confidence.

**4. Is there a baseline and a regression threshold?** The suite is only meaningful relative to a prior result. Store score-per-case and aggregate metrics from the last accepted baseline; on each run, flag any case whose score drops below `baseline - δ`. Threshold rule-of-thumb: deploy blocks on any **safety/adversarial regression** (δ = 0), and on aggregate quality drops greater than ~2–5% relative to baseline depending on suite noise.

**5. Will the suite be maintained?** V16 is a living artefact. Cases must be added when new behaviours ship, retired when behaviours are deprecated, and audited when scoring drifts. Threshold: name an owner, schedule a quarterly review, and **fold every production incident into a new golden-set case as part of the incident post-mortem**. A V16 suite without an owner becomes a target the agent is over-tuned to (Goodhart's law) within two quarters.

**Quick test — V16 is the right pattern when:**

- there is a deploy event to gate, *and*
- correctness can be specified per case (exact match, structured criteria, or V15 rubric), *and*
- the golden set spans positive, negative, edge, adversarial, and regression cases, *and*
- the team has named an owner who will maintain the suite.

If continuous deploy makes "offline" meaningless, use **V17 Online Eval** as the live complement. If multi-agent emergence dominates and flat case/answer pairs cannot capture it, use **V18 Agent Simulation**. If no defensible correctness criterion exists for any case, the task is under-specified — fix the spec before adding the harness.

## Structure

```
                       ┌──────────────────────────────┐
   Change event ──────▶│  Eval Runner                 │
   (prompt / model /   │  for each case in golden set:│
    tool / config)     │    run agent on input        │
                       │    score output              │──┐
                       └──────────────────────────────┘  │
                              ▲                          │
                              │                          ▼
                  ┌───────────┴────────────┐    ┌───────────────────┐
                  │  Golden Set            │    │  Scorer           │
                  │  ─ positive cases      │    │  ─ exact match    │
                  │  ─ negative cases      │    │  ─ structured     │
                  │  ─ edge cases          │    │  ─ V15 Judge      │
                  │  ─ adversarial cases   │    └─────────┬─────────┘
                  │  ─ regression cases    │              │
                  └────────────────────────┘              ▼
                                                ┌───────────────────┐
                                                │  Comparator       │
                                                │  score vs baseline│
                                                └─────────┬─────────┘
                                                          │
                                                          ▼
                                              ┌──────────────────────┐
                                              │  Deployment Gate     │
                                              │  PASS → deploy       │
                                              │  FAIL → block, diff  │
                                              └──────────────────────┘
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Golden Set** | the curated test cases and their expected outputs / criteria | — $\to$ versioned dataset | be edited mid-run, contain only happy paths, or live without an owner — an unowned set decays into Goodhart bait. |
| **Eval Runner** | executing the System Under Test against each case | golden set + SUT $\to$ per-case outputs | mutate the golden set, retry to make scores look better, or hide failed cases. |
| **Scorer** | producing a verdict per case | input + output + expected $\to$ score / pass-fail + reason | invent its own criteria — every score traces back to a case's declared check (exact match, structured assertion, or V15 rubric). |
| **Baseline Store** | the last-accepted aggregate and per-case scores | accepted run $\to$ durable record | be overwritten silently — a baseline update is a decision, logged. |
| **Comparator** | finding regressions against the baseline | current scores + baseline $\to$ diff + verdict | flag noise as regression (apply a tolerance δ); but must never apply tolerance to safety / adversarial cases. |
| **Deployment Gate** | the ship-or-block decision | comparator verdict $\to$ PASS / FAIL | be bypassed without an explicit, logged override; a bypass without record is theatre. |
| **System Under Test** *(the agent)* | producing outputs to be scored | input $\to$ output | see the golden set during training, prompt-tuning, or fine-tuning — leakage invalidates the gate. |

The discipline of the pattern lives in the **Must not** column: the most common V16 failure is not the absence of a suite but the silent rotting of one — vibey case additions, drifting scoring criteria, baselines updated to "make the diff green," adversarial cases that quietly get tolerance applied because they fail too often.

## Collaborations

A change event — a new prompt, a model upgrade, a tool refactor — triggers the Eval Runner, which iterates the Golden Set, running the System Under Test on each case and handing the (input, output, expected) triple to the Scorer. The Scorer applies the declared check for that case (exact match, structured assertion, or a **V15 LLM-as-Judge** call against a rubric) and emits a per-case score and reason. The Comparator pulls the last-accepted per-case scores from the Baseline Store and computes the diff. The Deployment Gate inspects the diff: any safety or adversarial regression is a hard block; aggregate quality drops above tolerance are blocks; everything else is a pass. On pass, the new run becomes the candidate baseline (promoted on deploy). On fail, the diff is surfaced to the engineer with the specific cases that regressed and their reasons. Every run is logged via **V14 Trajectory Logging** so eval history is queryable. Production incidents discovered later flow back as new golden-set cases — the suite grows by the union of every failure the system has ever seen.

## Consequences

**Benefits**

- Regressions on previously-handled behaviour are caught before users see them.
- The team has a defensible, numeric answer to "is this change safe to ship?"
- New model versions can be evaluated apples-to-apples: same suite, same scoring, two runs.
- Adversarial and safety behaviours are *regression-tested*, not assumed.
- The golden set is institutional memory — every production incident permanently raises the bar.

**Costs**

- Building the initial golden set is non-trivial work (often 1–3 engineer-weeks for a serious suite).
- Scoring via V15 costs LLM calls — a 500-case suite $\times$ 1 judge call each, run on every deploy, is a real budget line.
- Maintenance is forever — cases must be added, retired, and rescored as the system and the world evolve.
- A naively-built suite slows the team's deploy cadence without catching real regressions.

**Risks and failure modes**

- *Goodhart drift* — the agent is over-optimised for the suite, scoring perfectly while degrading on real traffic V17 alone would catch.
- *Happy-path-only suite* — categories (b)–(e) of the Decision Criteria are empty; the gate gives false confidence.
- *Stale golden set* — cases reflect the system as it was, not as it is; the gate blocks legitimate change.
- *Data leakage* — golden-set inputs appear in training, prompt-tuning, or RAG corpora, invalidating the held-out claim.
- *Baseline laundering* — failing baselines are quietly accepted to unblock the deploy; over time the bar moves down silently.
- *Judge drift* — the V15 scorer's model is upgraded; scores shift on cases that didn't change; the team conflates judge change with system change. Pin the judge model, or re-baseline explicitly when changing it.

## Implementation Notes

- **Start small and grow with incidents.** A 30–50 case suite that grows by one case per production incident outperforms a 500-case suite built from a brainstorm.
- **Version the suite.** Treat the golden set as code: source-controlled, reviewed, semantically versioned. A score from suite v1.4 is incomparable to a score from v1.5 without explicit re-baselining.
- **Pin the judge.** If scoring uses V15, pin the judge model and prompt the same way you pin the SUT model. A judge upgrade is a re-baseline event.
- **Never tolerance-tune safety cases.** Quality regressions tolerate small dips; safety regressions do not. The Comparator must apply different δ values to different case categories.
- **Run on CI, not on the developer's laptop.** A V16 suite that only runs when someone remembers to run it is functionally absent. Wire it into the deploy pipeline.
- **Capture cost and latency alongside quality.** A change that holds quality but doubles cost is also a regression — surface it.
- **Promotion is a decision, not an automatic step.** New baseline becomes "accepted" only on deploy; failing-and-still-deploying overrides are logged, with reason.
- **Adversarial cases double as V6 regression tests.** Every prompt-injection vector that has been observed in the wild belongs in the suite, permanently.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V16 chains an *Eval Runner* and a *Scorer* against a held-out *Golden Set*, with the *Scorer* often being a **V15 LLM-as-Judge** call. V16 reads from **V14 Trajectory Logging** to populate cases from real traffic, writes back to V14 to log runs, and feeds its baseline into the **V17 Online Eval** monitor (so live drift is measured against the same yardstick). The Deployment Gate sits in front of any pattern that ships changes — prompt-level, model-level, or orchestration-level (O2, O3, O6).

**The chain — per case:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Load case `(input, expected, check_type, category)` from golden set | `code` | Golden Set |
| 2 | Run System Under Test on `input` | `LLM` | SUT session (the agent being evaluated) |
| 3 | Apply Scorer per `check_type` | `code` or `LLM` | Scorer (V15 Judge for rubric checks) |
| 4 | Emit `(case_id, score, reason)` | `code` | |

**The chain — per run:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 5 | Aggregate per-case scores into run metrics | `code` | |
| 6 | Load baseline from store | `code` | Baseline Store |
| 7 | Compare current vs baseline, apply category-aware δ | `code` | Comparator |
| 8 | Emit PASS / FAIL with diff | `code` | Deployment Gate |
| 9 | Log run to V14 | `code` | V14 Trajectory Logging |

**Skeleton:**

```
run_offline_eval(sut, golden_set, baseline):
    results = []
    for case in golden_set:                                # code
        output = sut.run(case.input)                       # LLM — system under test
        score  = score_case(case, output)                  # code or LLM (V15)
        results.append((case.id, score, score.reason))
    metrics = aggregate(results)                           # code
    diff    = compare(metrics, baseline, tolerances)       # code — category-aware δ
    verdict = gate(diff)                                   # code — PASS / FAIL
    log_v14(run_id, metrics, diff, verdict)                # code
    return verdict, diff

score_case(case, output):
    if case.check_type == "exact":      return exact_match(output, case.expected)        # code
    if case.check_type == "structured": return assert_criteria(output, case.criteria)    # code
    if case.check_type == "rubric":     return v15_judge(case.input, output, case.rubric) # LLM — V15
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **System Under Test** | whatever model the agent ships with | the agent's full production setup — system prompt, tools, retrieval config, orchestration; the SUT setup is *exactly* what would ship | the case input |
| **V15 Judge** *(rubric checks only)* | a strong generalist, **pinned** to a specific version so scores are comparable across runs | judge role, the rubric (dimensions + scale), output contract (JSON: per-dimension score + reasoning), reference answer if the case has one | the case input + the SUT's output + (where present) the reference |

**Specialist-model note.** No fine-tuned specialist is required for V16 itself. Two structural choices matter more than model choice:

- **Pin every model in the loop.** Both the SUT and the V15 Judge must be pinned to specific versions, because a model upgrade on either side moves the scores without the system changing. Upgrading either is a re-baseline event, not a routine bump.
- **Hold the golden set out of training and retrieval.** If the SUT is fine-tuned or augmented with RAG, the golden-set inputs must be confirmed absent from training data and retrieval corpora. Leakage silently inflates scores.

## Open-Source Implementations

- **promptfoo** — [`github.com/promptfoo/promptfoo`](https://github.com/promptfoo/promptfoo) — declarative YAML eval configs, CLI + CI/CD integration, exact-match and LLM-as-judge assertions, regression diffing. The most-cited offline-eval harness in the practitioner community; MIT-licensed.
- **OpenAI Evals** — [`github.com/openai/evals`](https://github.com/openai/evals) — framework and registry of benchmarks for evaluating LLMs and LLM systems against curated datasets; the reference implementation for the "eval registry" model.
- **DeepEval** — [`github.com/confident-ai/deepeval`](https://github.com/confident-ai/deepeval) — pytest-style unit testing for LLM apps with 50+ built-in metrics (G-Eval, faithfulness, answer relevancy, hallucination), single-turn and multi-turn datasets, regression dashboards via Confident AI.
- **Inspect AI** — [`github.com/UKGovernmentBEIS/inspect_ai`](https://github.com/UKGovernmentBEIS/inspect_ai) — UK AI Security Institute's evaluation framework; agentic-task, reasoning, and safety evals with built-in prompt engineering, tool use, multi-turn dialog, and model-graded scoring; adopted by METR, Apollo, and other AISIs.
- **Inspect Evals** — [`github.com/UKGovernmentBEIS/inspect_evals`](https://github.com/UKGovernmentBEIS/inspect_evals) — community-contributed eval suites for Inspect AI; useful as a starting golden set for capability, safety, and agentic-task domains.
- **LangSmith eval datasets** — [`github.com/langchain-ai/langsmith-cookbook`](https://github.com/langchain-ai/langsmith-cookbook) — runnable recipes for dataset-based evaluation, regression tests, and pairwise comparison; pairs with LangSmith's hosted dataset and experiment management.

## Known Uses

- **OpenAI, Anthropic** — both use promptfoo internally for prompt and agent evaluation according to its public docs.
- **UK AI Security Institute, METR, Apollo Research** — Inspect AI is the shared substrate for frontier-model safety evaluations across the AISI network.
- **Claude Code, Cursor, Devin** — coding-agent teams ship offline eval suites that gate every model and prompt update; promptfoo and bespoke harnesses dominate.
- **Anthropic's "Building Effective Agents"** guidance names offline evaluation as a prerequisite for production deployment.
- **Enterprise GenAI deployments** (Salesforce, ServiceNow, Microsoft) report offline-eval-gated deploy as standard practice for LLM features as of 2025.

## Related Patterns

- **Pairs with** V15 LLM-as-Judge — V15 is the scoring primitive V16 most often uses for non-exact-match cases. V15 is the verb; V16 is the harness around it.
- **Pairs with** V17 Online Eval — V16 catches *known* regressions pre-deploy against ground truth; V17 catches *unknown* regressions post-deploy without ground truth. Production systems run both; V17 monitors against the baseline V16 establishes.
- **Composes with** V14 Trajectory Logging — V14 traces are the richest source of new golden-set cases (real production failures); V16 runs are themselves logged via V14.
- **Composes with** V18 Agent Simulation — V18 supplies dynamic, multi-turn, adversarial scenarios that flat case/answer pairs cannot capture; V16 runs the simulation-derived results through the same scoring and gate.
- **Composes with** V6 Prompt Injection Shield — adversarial cases in the V16 golden set are V6's permanent regression tests.
- **Distinct from** V15 — V15 is a *primitive* (score one output against a rubric); V16 is a *system* (run a held-out suite, compare to baseline, gate the deploy).
- **Distinct from** V17 — V16 has ground truth and runs offline; V17 has live traffic and no ground truth. Choosing one and skipping the other is an anti-pattern.
- **Defends against** A6 Vibe-Checking — the canonical anti-pattern V16 replaces. A6 is the absence of V16.
- **Defends against** A13 Pilot Simplification — V16's category-aware golden set (adversarial, edge, negative, regression) is the operational remedy.
- **Required by** any system claiming "production-grade" reliability — the Minimum Viable Reliability stack in `RELIABILITY.md` names V16 alongside V5, V9, V14.

## Sources

- Zheng et al. (2023) — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (arXiv 2306.05685) — the scoring foundation V16 inherits via V15.
- Liu et al. (2023) — "G-Eval: NLG Evaluation using GPT-4 with Better Human Alignment" (arXiv 2303.16634) — rubric-based offline eval methodology.
- Anthropic (2024–25) — "Building Effective Agents" — offline evaluation as a deploy prerequisite.
- Composio (2025) — AI Agent Report — the 88% production failure analysis and A13 Pilot Simplification framing.
- Karpathy (2025) — public commentary on eval-driven LLM development.
- BIG-bench, HELM, MMLU — exemplars of systematic LLM eval suite design.
- NIST AI Risk Management Framework (AI RMF 1.0) — evaluation as a Measure-function requirement.
- OpenAI Evals, promptfoo, DeepEval, Inspect AI — primary open-source references (see Open-Source Implementations).
