# V17 — Online Eval

> Continuously sample live production traffic, score the sampled outputs with reference-free judges and trace-derived signals, and alert on quality, safety, or cost drift — so degradation that emerges only from real traffic is caught while the system is still running, without waiting for a ground-truth label that will never arrive.

**Also Known As:** Production Monitoring, Live Quality Tracking, Continuous Eval, Reference-Free Eval, Drift Monitoring, Real-Time LLM Observability.

**Classification:** Category V — Reliability · Band V-C Observability and Evaluation · the *runtime* counterpart to V16 — V16 evaluates fixed inputs against known answers before deploy; V17 evaluates open inputs against rubrics while serving.

---

## Intent

Make the deployed system answer the question *"is it still working?"* on its own, continuously, by sampling its live traces, judging them against rubrics that need no ground truth, and surfacing drift as an alert — so quality and safety regressions that only appear in production are detected from the run itself, not from a customer complaint.

## Motivation

V16 Offline Eval catches the regressions you can write a test case for. It runs against a fixed, curated golden set with known expected outputs, and it runs before deployment. That is exactly its strength — and exactly its limit. Three classes of regression are invisible to it:

- **Distributional shift.** Real users do not write the queries the golden set anticipates. New input patterns, new topics, new languages, new edge phrasings emerge constantly. The golden set freezes the world V16 was built in; production keeps moving.
- **Silent model drift.** The same prompt against the same model, six months apart, can drift — provider-side fine-tuning, RLHF updates, model deprecation rotating in a replacement, even temperature-default changes. The provider's release notes rarely surface what changed; the output quality does. The mechanism is that weight updates change the learned attention bilinear forms (mechanism 1); identical prompts produce different probability distributions over output tokens, resulting in different behaviour even when the prompt and context are unchanged.
- **Compounding system drift.** Tools update, retrieval corpora change, downstream agents redeploy, guardrails tune. Each change is small and tested in isolation; the integrated behaviour drifts in ways no single component owner sees.

The reason V16 cannot catch any of these is structural: **V16 requires ground truth**. You cannot regression-test what you have not labelled. Production traffic — millions of queries with no expected output — has no labels and will not get any. Manual labelling at production volume is unaffordable; waiting for user complaints means the regression has already shipped to many users.

The pattern is the move that the broader ML world made a decade earlier under the name **production monitoring**: sample live traffic, score what you sampled with whatever reference-free signal you can compute, track rolling distributions, alert on drift. For LLM systems the reference-free signal is **V15 LLM-as-Judge** applied to sampled outputs against a rubric (faithfulness, safety, helpfulness, format), augmented by **trace-derived metrics** read from V14 (guardrail trigger rate, tool-error rate, V9 termination rate, cost and latency percentiles). The defining claim is that *aggregate behaviour over many sampled traces is observable even when individual outputs are not*; drift in the aggregate signal is what V17 watches for.

This is distinct from V14 and V15. V14 produces the data; V17 *consumes* it. V15 is the scoring primitive; V17 is the *system* that calls V15 against a sample at a chosen cadence, stores the result as a time series, and decides when to alert. It is also distinct from V16: V16 is pre-deployment with ground truth; V17 is post-deployment without ground truth. They are complementary halves of the evaluation story — and a production agent needs both.

## Applicability

Use V17 when:

- the agent is in production with non-trivial traffic (≥ ~1000 requests/day) — below that, sampling produces too few datapoints for drift to be statistically distinguishable from noise;
- the answer to *"is it still working?"* needs to be available faster than the next manual review cycle;
- ground truth at production volume is unavailable or unaffordable, but the team can articulate quality and safety rubrics;
- regulatory or operational commitments require continuous monitoring (financial services, healthcare, EU AI Act Article 15 — accuracy and robustness monitoring through the lifecycle);
- the system is subject to model upgrades, corpus updates, prompt changes, or tool changes that could individually pass V16 but compose into drift.

Do not use when:

- the agent is pre-production with no live traffic — use **V16 Offline Eval** and **V18 Agent Simulation**; V17 has nothing to sample;
- volume is too low (~< few hundred requests/day) for sampling to yield signal — collect for V16's golden set and revisit;
- ground truth *is* available cheaply and at scale (rare; usually a structured-data task with explicit user feedback) — direct accuracy metrics dominate V17's rubric scores;
- the team cannot or will not staff an on-call response — V17 with no one watching becomes alert theatre and pulls budget for no benefit.

## Decision Criteria

V17 is right when the system is live, ground truth is missing, the rubrics are articulable, and someone will respond to alerts.

**1. Production volume sufficient for sampling.** Estimate daily requests N and target sample rate p. The judge call count per day is N·p; rolling-window drift detection wants at least ~100 sampled scores per window. Practical threshold: **N·p ≥ 100/window**, with windows ≥ 1 hour for fast-moving signals and ≥ 24 hours for slow drift. If N is too small, lean on **V16** with an expanded golden set drawn from real traces instead.

**2. Rubric definability without ground truth.** Can the team write a faithfulness rubric, a safety rubric, a format rubric — and validate the judge's calibration against a small held-out human-labelled sample? If yes, V17 is viable. If no, V17 produces noise; invest in the rubric (and a V16 baseline) first.

**3. Judge cost budget.** Annualise: N·p · judge_cost_per_call · 365. Compare to (a) the cost of an undetected quality regression reaching users, and (b) the cost of staffing a manual sampling/review process for the same coverage. If the judge cost exceeds the combined alternatives by more than ~3×, lower p (stratified sampling, error-only sampling) or switch the rubric to cheaper trace-derived signals before adopting V17 at full coverage.

**4. Drift-detection method choice.** Pick by signal type:
- **Threshold alarms** — score < absolute threshold (e.g. safety rate < 99.5%) → simplest, blunt.
- **Rolling-window comparison** — current window vs trailing baseline (e.g. mean score this hour vs trailing 7-day mean, alert on > 2σ deviation) → standard choice.
- **Distributional tests** — KS / PSI / Wasserstein on the full score distribution → catches mean-preserving shape drift the rolling-mean misses; needed when the tail matters more than the mean (safety-critical).
- **Embedding drift on inputs** — sentence-embedding distance from a reference corpus distribution → detects input distributional shift even before output drift appears.

**5. On-call commitment and runbook.** Every alert needs a named owner, a response SLA, and a runbook that says what to do (page humans via **V1 Human-in-the-Loop**, switch traffic via **V19 Fallback**, roll back the deploy, open an incident). An alert with no defined response is a monitoring-theatre red flag; the literature names this directly as V17's primary failure mode.

**Quick test — V17 is the right pattern when:**

- the agent is in production at sample-viable volume, *and*
- ground truth is absent at production scale but rubrics are articulable, *and*
- the judge-cost budget closes against the cost of undetected regressions, *and*
- a named owner and runbook are committed for every alert.

If the agent is pre-production, choose **V16** and **V18**. If ground truth is plentiful, use direct accuracy metrics on the live stream rather than V15-judge sampling. If volume is too low for sampling to converge, extend the **V16** golden set with real-traffic examples and run it on a tighter cadence. If the budget for judges or on-call cannot be committed, V17 is the wrong investment — instrument V14 deeply, build dashboards, and revisit when the team can sustain response.

## Structure

```
  Production traffic
        │
        ▼
  V14 Trajectory Logging (substrate — every request produces a trace)
        │
        ▼
  Sampler ──▶ {random p%} ∪ {stratified by segment, task type, cost outlier}
        │              ∪ {always-sample on error / V5 guard / V9 cap / V7 deny}
        ▼
  Online Judge (V15) ──▶ scores per dimension (faithfulness, safety, helpfulness, format)
        │
        ▼
  Trace-derived metrics (read from V14, no LLM call)
        │   ├─ guardrail trigger rate (V5)
        │   ├─ policy-deny rate (V7)
        │   ├─ V9 termination rate
        │   ├─ tool-error rate, latency p50/p95/p99, cost p50/p95/p99
        │   └─ input embedding drift vs reference
        ▼
  Metrics Store (time series; dimension × window × cohort)
        │
        ▼
  Drift Detector ──▶ rolling-window / threshold / distributional test
        │
        ▼
  Alert Manager ──▶ owner + runbook
        │
        ├──▶ V1 Human-in-the-Loop  (manual review queue)
        ├──▶ V19 Fallback           (route degraded → cheaper / cached / rule)
        └──▶ rollback / incident
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Sampler** | choosing which production traces to evaluate | trace stream + sampling policy → sampled subset | sample only the happy path — error, guard-trigger, policy-deny, V9-cap traces must be sampled at 100% or the rare-and-important failure mode never reaches the judge. |
| **Online Judge** (V15 instance) | reference-free scoring of sampled outputs | sampled trace → scores per rubric dimension | be the same model as the agent under test — judge-similar-to-defendant collapses to self-evaluation and inflates scores. |
| **Trace-Derived Metric Computer** | turning V14 spans into numeric series without LLM calls | V14 spans → time-series points | invent novel attribute names — read only **OTel GenAI semconv** fields V14 emits, or the metric pipeline breaks when the schema evolves. |
| **Metrics Store** | durable time-series storage with cohort dimensions | metric stream → queryable history | be a single global counter — drift hides inside segments (task type, user cohort, model version, region); store dimensioned. |
| **Drift Detector** | turning a metric history into a verdict (drift / no drift) | metric series + detection method → drift signal with confidence | use one method blindly — threshold alarms miss distributional drift; rolling means miss tail shifts; pair methods to the signal class. |
| **Alert Manager** | routing drift verdicts to a named owner with a runbook | drift signal → page / ticket / incident | fire without a runbook — alerts without prescribed response train the team to ignore them, which is worse than no monitoring. |
| **Calibration Sample** | the small human-labelled set the judge is validated against | human labels + judge scores → judge calibration verdict | drift into the judge's training data — calibration must be a held-out check, refreshed periodically, or the judge's reliability silently erodes. |

The Sampler, Judge, and Drift Detector are the three load-bearing roles. Cutting corners on the Sampler (random-only, missing error stratification) is the most common silent failure; cutting corners on the Drift Detector (single threshold for everything) is the second.

## Collaborations

Every production request emits a V14 trace. The Sampler reads the trace stream and selects which traces to evaluate — a baseline random fraction, stratified by user segment / task type / model version, plus 100%-sample policies for any trace with an error, a V5 guardrail trigger, a V7 policy deny, or a V9 cap breach. Each sampled trace goes to the Online Judge (a V15 session configured with the rubric), which scores it on the dimensions defined for the deployment; scores are written to the Metrics Store. In parallel, the Trace-Derived Metric Computer reads the same V14 spans for non-LLM signals — guardrail rates, latency and cost percentiles, tool-error rates, input embedding distance — and writes those as time-series points alongside the judge scores. The Drift Detector reads rolling windows from the store and applies the appropriate test per metric class (threshold, rolling-window deviation, distributional). When a test fires, the Alert Manager routes the verdict to the named owner with a runbook that points to **V1** (human review), **V19** (route to fallback path), or **rollback**. Periodically — weekly is common — the Calibration Sample is refreshed: a small batch of judge-scored traces is hand-labelled and compared to the judge's verdicts, confirming the judge's calibration has not eroded.

## Consequences

**Benefits**
- Catches drift the offline suite cannot see — distributional shift, silent model updates, compounding system drift.
- No ground truth required — judges and trace-derived signals carry the eval at production scale.
- The same V14 trace substrate serves debugging, V16, and V17 — no separate instrumentation.
- Continuous: the answer to *"is it still working?"* is on a dashboard at all times, not assembled on demand after a complaint.
- Composes with V19 to close the loop — detection triggers automatic degradation, not just a human page.

**Costs**
- Judge calls at sample rate are an ongoing expense; at high traffic they dominate the eval budget.
- Storage, indexing, and dashboards are real infrastructure investment, not just code.
- Rubrics must be designed, calibrated, and re-validated — a one-off rubric drifts in usefulness as the system and corpus change.
- On-call burden: alerts with no response degrade into monitoring theatre.

**Risks and failure modes**
- *Sampling that misses the tail* — random-only sampling at 1% will rarely catch a 0.1% failure mode that nonetheless matters; stratified and 100%-on-error sampling is the antidote.
- *Judge bias* — position bias, verbosity bias, self-similarity bias documented in V15 judges translate directly into V17's drift signal; calibration sample is the only defence.
- *Threshold flapping* — alerts fire on noise within natural variance, training the team to mute them; drift methods must be matched to the signal's variance profile.
- *Alert without runbook* — the canonical V17 failure mode named in the source literature: a dashboard built, alerts wired, no owner, no response, no value.
- *Calibration erosion* — the judge model itself can drift; a calibration sample that never refreshes silently goes stale.
- *Cohort collapse* — global aggregates hide segment-level drift; a 1% global quality drop can mean 50% on a small but important cohort.

## Implementation Notes

- **Start before the first incident, not after.** V17 instrumented in week one of production gives a baseline to compare drift against; instrumented in month six gives a snapshot with no history.
- **Stratify the sample.** Random-only sampling is the rookie mistake. Sample by task type, by user cohort, by model version, by cost tier — and always sample 100% of errors, guardrail triggers, policy denies, and V9 caps.
- **Use a stronger judge than the agent.** Same-model judge under-detects same-model failure modes; a stronger or differently-trained judge is the recommended setup.
- **Validate the judge.** A small held-out human-labelled set, refreshed quarterly, is what tells you whether the judge's scores still correlate with human judgment. Without it, the entire V17 signal is hope.
- **Match drift method to signal.** Safety and policy-deny rates → threshold alarms. Quality scores → rolling-window deviation. Distributional shifts in score-shape or latency tails → KS / PSI / Wasserstein. Input drift → embedding distance from a reference corpus.
- **Make the runbook part of the alert.** The alert payload itself should link the runbook; the on-call doesn't have to think about what to do.
- **Compose with V19 from the start.** Quality-drift detected → automatic switch to the V19 fallback path (cheaper model, cached, rule, human queue) → human review the next business day. Detection without remediation is half a system.
- **Pair with V14 sampling policy.** V14's own sampling (head-based for routine, 100% on errors) sets the upper bound on V17's reachable traces; mis-aligning them invisibly limits coverage.
- **Cohort the store.** Dimension every metric by task type, user segment, model version, and region. Global aggregates lie about cohort-level drift.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V17 reads from **V14** (the trace substrate), uses **V15** as its judge primitive, completes the eval story with **V16** (V16 pre-deploy, V17 post-deploy), and pairs with **V19** (V17 detects, V19 reroutes) and **V1** (V17 escalates to human). The rubric itself is a Signal-layer artifact (**S5 Constraint Framing** + **S6 Output Template**).

**The chain — sampling & scoring (continuous, per sampled trace):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Read live trace from V14 | `code` | V14 |
| 2 | Sampler decides include / skip (random + stratified + 100%-on-error) | `code` | sampling policy |
| 3 | Judge evaluates the trace against rubric | `LLM` | V15 Judge session |
| 4 | Compute trace-derived metrics (guard rate, latency, cost, embedding drift) | `code` | V14 spans |
| 5 | Write scores + metrics to the time-series store, cohort-dimensioned | `code` | metrics store |

**The chain — drift detection & response (per detection window):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| D1 | Query metric series for the current window vs trailing baseline | `code` | metrics store |
| D2 | Apply detection method (threshold / rolling / distributional / embedding) | `code` | drift detector |
| D3 | If drift: emit alert with runbook link, owner, severity | `code` | alert manager |
| D4 | Route — page V1, switch to V19 fallback, open incident, or rollback | `code` | V1 / V19 / ops |
| D5 | *(optional, periodic)* Refresh calibration sample with new human labels | `code` *or* `LLM` | calibration |

**Skeleton** — sampling loop and detection loop run independently; the judge call is the only LLM step inside V17 itself:

```
# Sampling and scoring — runs on every live trace
def on_trace(trace):
    if not sampler.select(trace):                        # code  — stratified + error-priority
        return
    scores = judge(trace.input, trace.output, rubric)    # LLM   — V15 judge session
    derived = compute_trace_metrics(trace)               # code  — V14 spans → metric points
    store.write(                                          # code
        scores | derived,
        cohort={'task': trace.task_type,
                'segment': trace.user_segment,
                'model': trace.model_version,
                'region': trace.region}
    )

# Drift detection — runs on a window cadence (e.g. every 5 min for safety, hourly for quality)
def detect_drift(metric_name, method, window, cohort=None):
    current  = store.window(metric_name, window, cohort=cohort)      # code
    baseline = store.baseline(metric_name, trailing='7d', cohort=cohort)
    verdict  = method(current, baseline)                              # code  — threshold / KS / PSI / rolling-σ
    if verdict.is_drift:
        alert_manager.fire(                                            # code
            metric=metric_name, cohort=cohort,
            severity=verdict.severity, runbook=runbook_for(metric_name)
        )

# Calibration refresh — runs weekly / monthly
def refresh_calibration():
    sample   = store.sample_judged_traces(n=100, stratified=True)    # code
    labels   = human_review_queue.label(sample)                       # code (via V1 queue)
    judge_vs_human = compare(judge.scores_on(sample), labels)         # code
    if judge_vs_human.correlation < threshold:
        alert_manager.fire('judge_miscalibrated')                     # code
```

**The LLM sessions.** V17's only LLM step is the Online Judge — a V15 session configured for production sampling. (The agent's own LLM calls are scored *by* V17 but are not V17 sessions; they belong to whatever pattern is being monitored.)

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Online Judge** (V15) | a *capable, differently-positioned* model from the agent under test (different family, different size, or stronger generalist) | role ("you grade live production outputs against the rubric"); the rubric with explicit dimensions (faithfulness, safety, helpfulness, format) and scoring scale; chain-of-thought reasoning required; output contract (JSON with per-dimension scores + reasoning + overall verdict) | the sampled trace's input, retrieved context (if any), and final output |

**Specialist-model note.** No fine-tuned specialist is required, but **the judge must not be the same model as the agent under test** — that is the single decisive choice. The mechanistic reason is shared learned attention geometry: models from the same family assign similar probability mass to similar tokens on similar inputs, making the judge autocorrelated with the agent's own failure modes (mechanism 1). A stronger generalist (e.g. evaluating a Haiku-served agent with Sonnet, or evaluating a GPT-served agent with Claude) is the standard configuration; the judge call cost is amortised across the sample rate. Where calibration matters more than capability, a small **fine-tuned evaluator** (the same kind that powers the K5 CRAG variant) can serve — that is a build dependency, not a drop-in. Trace-derived metrics (guardrail trigger rates, policy-deny rates, V9 cap counts) avoid the judge-calibration problem entirely — they are deterministic code outputs with no stochastic variance, making them the highest-signal, lowest-cost monitoring signals available (mechanism 7). The drift detector, embedding-drift computer, and trace-metric computer are pure `code`; no model required.

## Open-Source Implementations

- **Arize Phoenix** — [`github.com/Arize-ai/phoenix`](https://github.com/Arize-ai/phoenix) — open-source AI observability platform with OTel-native tracing, LLM evaluations (LLM-as-judge and code-based), datasets, and experiments; runs locally, self-hosted, or as Arize Cloud. The closest match to the V17 architecture described above.
- **Langfuse** — [`github.com/langfuse/langfuse`](https://github.com/langfuse/langfuse) — open-source LLM engineering platform (Apache 2.0, YC W23) with observability, LLM-as-judge evals, prompt management, datasets; integrates with OpenTelemetry, LangChain, OpenAI SDK, LiteLLM. Supports custom evaluation pipelines via API for online scoring.
- **Helicone** — [`github.com/Helicone/helicone`](https://github.com/Helicone/helicone) — open-source LLM observability platform (YC W23) with one-line instrumentation, online monitoring, evaluations, experiments, AI gateway. SOC 2 / GDPR compliant.
- **LangSmith SDK** — [`github.com/langchain-ai/langsmith-sdk`](https://github.com/langchain-ai/langsmith-sdk) — client SDK for the LangSmith platform; supports online evaluators that run automatically on production traces (safety checks, format validation, reference-free LLM-as-judge), real-time automated feedback, and algorithmic feedback pipelines. Backend is proprietary; SDK is open-source.
- **OpenLLMetry** — [`github.com/traceloop/openllmetry`](https://github.com/traceloop/openllmetry) — Apache-2.0 OTel-native instrumentation across LLM providers and frameworks; Traceloop's commercial platform layers online evaluations, prompt registry, and drift detection on top.
- **Evidently AI** — [`github.com/evidentlyai/evidently`](https://github.com/evidentlyai/evidently) — open-source ML and LLM observability framework (100+ metrics) covering data drift, embedding drift, and LLM judges; supports both offline reports and live monitoring service; the drift-detection methods (KS, PSI, Wasserstein, embedding distance) the V17 detector slots in are first-class here.
- **OpenLIT** — [`github.com/openlit/openlit`](https://github.com/openlit/openlit) — Apache-2.0 OTel-native observability platform for GenAI with one-line auto-instrumentation across 50+ providers, frameworks, vector DBs, GPUs; built-in evaluations.

## Known Uses

- **Anthropic, OpenAI, and major-provider customers using Phoenix / Logfire / Honeycomb** — online sampling and LLM-judge scoring over OTel traces as the standard production-monitoring pattern.
- **LangChain / LangGraph production deployments via LangSmith** — online evaluators running automatically on production runs, scoring quality and safety in real time.
- **Regulated deployments (financial services, healthcare, legal-tech)** — continuous V17 monitoring is the operational mechanism for **EU AI Act Article 15** (accuracy and robustness through the lifecycle) and **NIST AI RMF** Measure 2.x ongoing-monitoring requirements.
- **Coding-agent platforms (Claude Code, Cursor, Devin)** — telemetry-driven quality monitoring on tool-call success rates, edit acceptance, and user-feedback signals; the system catches regressions from model upgrades before users escalate.
- **Customer-support routers** — the canonical V17 deployment in the taxonomy's Example 4: O3 routing + K1 RAG + V17 continuously sampling and judging assistant responses against faithfulness and policy rubrics.

## Related Patterns

- **Reads from** V14 Trajectory Logging — V14 is the data substrate; V17 is meaningless without it.
- **Uses** V15 LLM-as-Judge — V15 is V17's scoring primitive; V17 is the system that calls V15 against a sample at a cadence.
- **Sibling of** V16 Offline Eval — V16 evaluates fixed inputs against ground truth pre-deploy; V17 evaluates live inputs against rubrics post-deploy. The two together complete the eval story; neither replaces the other.
- **Pairs with** V19 Fallback — V17 detects degradation; V19 reroutes around it. Detection without remediation is half a system.
- **Pairs with** V1 Human-in-the-Loop and V2 Human-on-the-Loop — V17 alerts page V1 for manual review or notify the V2 monitor; the human responder is the runbook target.
- **Composes with** V5 Guardrail Layering — V5 guard triggers become a V17 metric (rate, drift); a rising guard-trigger rate is one of V17's fastest leading indicators.
- **Composes with** V7 AgentSpec — V7 policy-deny decisions are V17 metrics; policy-deny drift is a compliance and prompt-injection leading indicator.
- **Composes with** V9 Bounded Execution — V9 cap breaches are V17 metrics; a rising V9 breach rate is a sign the agent is fighting harder for answers it used to find easily.
- **Distinct from** V14 — V14 *produces* the data; V17 *consumes and analyses* it. Different layers, often confused.
- **Distinct from** V18 Agent Simulation — V18 is pre-deploy synthetic traffic with controlled scenarios; V17 is post-deploy real traffic with whatever the world sends.
- **Mitigates** A6 Vibe-Checking as Testing — the canonical anti-pattern where subjective assessment replaces eval frameworks; V17 (paired with V16) is the antidote at the production layer.
- **Mitigates** A10 Silent Failure — V17 is what surfaces failures the agent itself does not signal.

## Sources

- OpenTelemetry GenAI Semantic Conventions — [opentelemetry.io/docs/specs/semconv/gen-ai/](https://opentelemetry.io/docs/specs/semconv/gen-ai/) (CNCF, 2024–25) — the substrate V17 reads.
- Zheng et al. (2023) — "Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena" (arXiv 2306.05685) — V15, the scoring primitive V17 calls; documents the position / verbosity / self-similarity biases V17's calibration sample must check.
- Anthropic — "Building Effective Agents" (2024) — production monitoring as a first-class concern for shipped agents.
- Composio AI Agent Report 2025 — 88% production-failure root-cause analysis; lack of online monitoring named alongside lack of observability.
- EU AI Act — Article 15 (accuracy, robustness, cybersecurity through the lifecycle) — the regulatory anchor for continuous monitoring of high-risk systems.
- NIST AI Risk Management Framework — Measure 2.x ongoing-monitoring functions.
- Arize Phoenix documentation — [arize.com/docs/phoenix](https://arize.com/docs/phoenix) — canonical reference for the trace-sampling + LLM-evals architecture.
- LangSmith Evaluation documentation — [docs.langchain.com/langsmith/evaluation](https://docs.langchain.com/langsmith/evaluation) — online evaluators on production traces (real-time + algorithmic feedback pipelines).
- Traceloop — "Catching Silent LLM Degradation" — the model-and-data-drift framing as it applies to OpenLLMetry-instrumented systems.
- Evidently AI documentation — drift detection methods (KS, PSI, Wasserstein, embedding-drift) as adapted from classical ML monitoring to LLM systems.
- 12-Factor Agents — Factor 10 and the "logs are for people, traces are for machines" principle (Horthy / HumanLayer) — V17 is what reads the machine-traces side.
