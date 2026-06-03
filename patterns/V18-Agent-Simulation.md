# V18 — Agent Simulation

> Run the whole agent against a synthetic user, synthetic tools, and a synthetic world — then judge how the trajectory unfolded — so emergent, multi-turn, and adversarial failures surface in a sandbox rather than in production.

**Also Known As:** Sandbox Testing, Agent Red-Teaming, End-to-End Simulation, Simulated-User Eval, Behavioural Audit.

**Classification:** Category V — Reliability · Band V-C Observability and Evaluation · the *end-to-end* gate — distinct from V16's flat case-and-answer regression suite and from V17's live monitoring; V18 evaluates whole-task trajectories under controlled but realistic conditions.

---

## Intent

Drive the agent through a complete task — with a simulated user, simulated tools, and a simulated environment — under happy-path, edge, adversarial, and load conditions, and score the full trajectory, not just the final answer, against safety and quality criteria — so trajectory-shaped failures invisible to flat eval surface before users see them.

## Motivation

V16 Offline Eval gates known regressions case-by-case against ground truth, and V17 Online Eval samples live traffic for unknown drift. Both treat the agent as a function from a single input to a single output. A real agent is not that. It is a *trajectory*: a sequence of tool calls, retrievals, intermediate plans, recoveries, and user clarifications, accumulated over many turns. The failures that ship to production tend to live in that trajectory, not in any one step. The agent satisfies every per-call assertion and still loses the user's intent across five turns; or it never trips a per-call guardrail but cooperates with an adversarial user across ten exchanges. Flat eval cannot see it.

Two specific failures recur. **Pilot simplification** (anti-pattern A13, Composio AI Agent Report 2025) — the team validates the agent on the cases an engineer would think to type, and the production distribution looks nothing like that: messier inputs, longer dialogues, misbehaving tools, hostile users, partial information. **Per-call regression** as a substitute for end-to-end testing — V16 confirms each isolated decision is unchanged, while the *composition* of those decisions across a long task silently degrades because the agent now spends three more turns on clarification and drifts off-policy on the fourth. Neither V16 nor V17 fixes this; V16 because it has no notion of trajectory, V17 because by the time it surfaces the drift it has already shipped.

V18 is the missing gate. The defining move is **whole-task execution against simulators**: a simulated user with a defined goal and persona generates the turn-by-turn dialogue; simulated tools (or sandboxed real tools — see V8) return controlled responses, including the failure modes V16's mocks never produce; the agent runs end-to-end; and a judge scores the full trajectory — *and the trace*, not just the final message — against task-completion, safety, and policy criteria. Where V16 asks *did this one call regress?* and V17 asks *is live traffic drifting?*, V18 asks *does the agent complete the task without falling off the rails along the way?* That question can only be answered by running the whole agent, which is why V18 is structurally distinct from its siblings, not a richer V16.

## Applicability

Use Agent Simulation when:

- the agent's value is multi-turn — task completion across a dialogue, not a one-shot answer;
- the agent uses tools whose responses (errors, slowness, malformed payloads, injected content) materially change downstream behaviour;
- the deployment is high-stakes — customer service, financial assistance, security-sensitive domains — where adversarial users are realistic;
- the system is multi-agent (O6 Orchestrator-Workers, O7 Supervisor Hierarchy, O11 Blackboard) and emergent inter-agent dynamics cannot be captured case-by-case;
- a new model version, prompt, or policy is about to ship and the team needs to know how trajectories change, not only how single answers change.

Do not use Agent Simulation when:

- the task is genuinely one-shot and stateless — V16 Offline Eval is the right gate, and V18 adds cost without signal;
- there is no defensible task-completion criterion the judge or environment can compute — fix the task spec first, or use V1 Human-in-the-Loop until it exists;
- the simulator's user / tool / environment fidelity is so poor that simulated trajectories tell you about the simulator, not the agent — invest in V14 Trajectory Logging first to mine real trajectories before building the sim;
- the team will not maintain the simulator and its scenarios — an unmaintained simulator drifts from production faster than a golden set does, and gives false confidence.

## Decision Criteria

V18 is right when the agent is trajectory-shaped, an honest simulator can be built, and the team will run and maintain it.

**1. Is the agent's value carried by the trajectory, not the call?** Count the median number of turns or tool calls before task completion in real traffic (use V14 traces). Threshold: **$\geq$ 3 turns or $\geq$ 3 tool calls** to complete a representative task. Below that, the agent is effectively one-shot and **V16 Offline Eval** suffices; V18 buys little. Above that, single-call evals miss the failure mode by construction.

**2. Can a simulated user be built with realistic intent variance?** A good user simulator has (a) a defined *goal* per scenario (book a refund, find a vulnerability, get medical advice), (b) a *persona* that varies how the goal is pursued (terse, rambling, hostile, confused), and (c) plausible *partial knowledge* so it does not just hand the agent the answer. Threshold: simulator coverage spans at least the goals you see in V14 plus the adversarial goals you must defend against; persona diversity is non-trivial. If the simulated user is one persona that politely states its goal, the sim is happy-path-only and gives false confidence — use **V1 Human-in-the-Loop** red-teaming until the simulator earns its keep.

**3. Can simulated tools cover the failure modes that matter?** Real tools fail in characteristic ways: timeout, 4xx schema mismatch, 5xx outage, malformed payload, injected content (V6 territory), rate-limit, partial result. Threshold: the tool simulator can inject each of these on demand, scenario-by-scenario. If the tools only return clean happy-path responses, the sim cannot test recovery paths and **V8 Tool Sandboxing** for real tools is the cheaper option.

**4. Are scenario categories covered?** A V18 scenario suite must span: (a) **happy path** — common goals with common personas; (b) **failure injection** — tool timeouts, schema errors, rate limits; (c) **adversarial** — prompt-injection attempts, jailbreaks, hostile users (regression for **V6 Prompt Injection Shield**); (d) **load / concurrency** — multiple sessions, V9-bounded-resource pressure; (e) **long-horizon** — multi-session interactions exercising H1/H2 identity-and-state patterns. Threshold: each category populated with at least a handful of scenarios; an audit that is happy-path-only is a V18 in name only.

**5. Is the trajectory scored, not just the final output?** A V18 judge that only looks at the last assistant message is a V16 in disguise. The judge must consume the full trace (via **V14 Trajectory Logging**) and score *trajectory-level* dimensions: task completion, policy adherence at every turn, safety violations *anywhere* in the run, cost / turn-count / latency budgets, and tool-use correctness. Threshold: at minimum, completion-rate and any-turn-safety-violation must be measured; ideally also turn-count-to-completion and policy-adherence-per-turn.

**6. Will the simulator and scenario set be maintained?** Like V16's golden set, the simulator decays. New production patterns must be folded back (V14 $\to$ V18 scenarios); user-simulator personas must be re-tuned as user behaviour shifts; tool simulators must track real-tool API changes. Threshold: named owner; production incidents become V18 scenarios as a post-mortem step; quarterly sim-vs-prod fidelity audit. Without that, the sim drifts and the gate becomes theatre.

**Quick test — V18 is the right pattern when:**

- the agent is trajectory-shaped ($\geq$ 3 turns / tool calls per task), *and*
- an honest simulator can be built for user, tools, and environment, *and*
- scenarios span happy / failure-injection / adversarial / load / long-horizon, *and*
- the judge scores the trajectory, not only the final output, *and*
- the team has named an owner who will keep the sim in sync with production.

If the agent is one-shot, run **V16 Offline Eval** instead. If trajectory fidelity cannot be honestly simulated, mine real trajectories with **V14 Trajectory Logging** and run human red-teaming under **V1 Human-in-the-Loop** until the sim is credible. If only adversarial prompt injection matters, a focused **V6 Prompt Injection Shield** regression suite is cheaper than a full V18 build.

## Structure

```
                       ┌─────────────────────────────────┐
                       │   Scenario Suite                │
                       │   ─ happy / failure / adversarial│
                       │   ─ load / long-horizon          │
                       └────────────────┬────────────────┘
                                        │
                                        ▼
   ┌─────────────────────┐     ┌─────────────────────┐    ┌──────────────────────┐
   │  User Simulator     │◀───▶│  Agent Under Test    │◀──▶│  Tool Simulator      │
   │  ─ goal             │turn │  ─ full prod setup   │ tool│  ─ schema-correct    │
   │  ─ persona          │     │  ─ V14 instrumented  │ call│    happy responses   │
   │  ─ partial knowledge│     │  ─ V9 bounded        │     │  ─ failure injection │
   └─────────────────────┘     └──────────┬──────────┘     │  ─ adversarial content│
                                          │                └──────────────────────┘
                                          ▼
                              ┌─────────────────────────┐
                              │  Trajectory             │
                              │  (V14 trace + transcript)│
                              └───────────┬─────────────┘
                                          │
                                          ▼
                              ┌─────────────────────────┐
                              │  Trajectory Judge       │
                              │  ─ task completion       │
                              │  ─ any-turn safety       │
                              │  ─ policy adherence      │
                              │  ─ cost / turn budgets   │
                              └───────────┬─────────────┘
                                          │
                                          ▼
                              ┌─────────────────────────┐
                              │  Verdict + Diff vs Baseline│
                              │  → Deployment Gate (V16)  │
                              └─────────────────────────┘
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Scenario** | the goal, persona, environment config, and expected outcome for one run | — $\to$ declarative scenario file | be a single happy-path goal — every scenario is one of {happy, failure-injection, adversarial, load, long-horizon}; categories are tracked. |
| **User Simulator** | producing turn-by-turn user messages consistent with the scenario's goal and persona | scenario + prior trajectory $\to$ next user message | break character mid-run, hand the agent the answer, or read its hidden state; if it can see what the agent knows, it stops being a user. |
| **Tool Simulator** | returning tool responses — clean or injected with the scenario's failure mode | tool call + scenario config $\to$ tool response | quietly degrade to happy responses when the scenario specified a failure; failure injection must be enforced. |
| **Simulation Controller** | orchestrating one run: stepping the agent, routing messages between user-sim and agent, recording the trajectory | scenario + AUT + sims $\to$ trajectory | mutate the AUT or its setup mid-run; the AUT is loaded exactly as it would ship. |
| **Agent Under Test** | producing assistant messages and tool calls per its production configuration | the dialogue + tool responses $\to$ next action | know it is in simulation — eval-awareness invalidates the audit (the Petri 2.0 problem). |
| **Trajectory Judge** | scoring the whole trace against trajectory-level dimensions | full V14 trace + scenario expected outcome $\to$ per-dimension scores + reasoning | score only the final message — a V18 judge that does that is a V16 in disguise. |
| **Scenario Suite** | the curated, versioned collection of scenarios | — $\to$ versioned suite | be happy-path-only, unowned, or unsynced from V14's real-production-failure stream. |
| **Comparator + Gate** | regression detection vs the prior baseline and the deploy decision | trajectory scores + baseline $\to$ PASS / FAIL | tolerance-tune safety categories; safety regressions are hard blocks regardless of aggregate delta. |

The reliability of the pattern lives in the **Must not** column. The most common V18 failures are not the absence of a simulator but the silent decay of one — user-sim that hands over the answer; tool-sim that has quietly stopped injecting failures because a developer "made the tests pass"; judge that only reads the final message; AUT that has learned the simulator's tells.

## Collaborations

A deploy candidate change — new prompt, model, tool, or orchestration logic — triggers the Simulation Controller, which iterates the Scenario Suite. For each scenario, the Controller spins up the Agent Under Test with its exact production setup and instruments it via V14 Trajectory Logging. It then runs the dialogue loop: the User Simulator emits a turn given the scenario goal and persona; the AUT responds, possibly with tool calls; the Tool Simulator returns responses obeying the scenario's failure-injection profile (timeout, schema error, injected content, partial result, or clean); the loop continues until the agent terminates the task or hits a V9 Bounded Execution cap. The Controller records the full trajectory — every message, every tool call, every intermediate decision — into V14. The Trajectory Judge then consumes the trace and the scenario's expected outcome and emits per-dimension scores: did the task complete; was any turn a policy violation; did the agent recover from injected failures; did it resist adversarial pressure; did it stay within turn / cost / latency budgets. The Comparator pulls the prior baseline (per scenario, per dimension) and computes the diff. The Deployment Gate inspects category-aware thresholds: any safety or adversarial regression is a hard block; aggregate quality drops above tolerance block; everything else passes. New incidents discovered in production via V14 flow back as new scenarios — the simulation suite, like V16's golden set, grows by the union of every trajectory failure the system has ever shown.

## Consequences

**Benefits**

- Catches trajectory-shaped failures invisible to V16's per-call regression — drift, abandonment, premature termination, recovery loops, adversarial cooperation.
- Adversarial scenarios are *regression-tested* as full conversations, not as single injected strings — the realistic threat model.
- Multi-agent emergent behaviour (O6, O7, O11) becomes observable: the simulator runs the full system, not its components.
- Pre-launch confidence for new domains, model upgrades, or prompt overhauls becomes a measured claim, not a feeling.
- Production incidents convert directly into permanent scenarios — the suite ratchets up the bar over time.

**Costs**

- Simulator build is non-trivial: tau-bench-class infrastructure for a serious domain is weeks of work, often months.
- Per-scenario runtime cost is high: dozens of LLM calls (user-sim, agent, tools-sim, judge) per scenario, $\times$N scenarios, $\times$every deploy.
- Calibration is ongoing: user-sim personas, tool-sim failure rates, scenario coverage all drift relative to production.
- Judge cost compounds — judging trajectories is more expensive than judging answers, because the input is the whole trace.

**Risks and failure modes**

- *Simulator-production drift* — the sim has gradually stopped resembling real users / tools / traffic; passes do not generalise. This is V18's V17 equivalent of Goodhart drift and the dominant long-run failure.
- *Eval-awareness* — the AUT recognises it is in a simulator (training-data overlap with Petri-class transcripts; a tell-tale user-sim phrasing). Petri 2.0 (Anthropic, 2026) documents this; mitigations are scenario diversity and persona randomisation. The mechanistic root of eval-awareness is weight-level memorisation: if simulation transcripts appeared in training data, the model's frozen weights (mechanism 10) assign higher probability mass to simulation-aware responses on inputs resembling those transcripts. Diversifying scenario phrasing and entry conditions reduces the probability of activating memorised simulation-detection patterns.
- *Happy-path-only suite* — failure-injection and adversarial categories are empty; the sim certifies that the agent handles the easy cases at high cost.
- *User-simulator collusion* — the simulated user accidentally reveals state or steers the agent helpfully; trajectories look successful for the wrong reason.
- *Judge looks at final message only* — the harness is wired but the judge is essentially V16; trajectory dimensions are not measured.
- *Tolerance-tuning safety* — adversarial scenarios fail flakily; the team adds δ to keep deploys green; the gate becomes theatre.
- *Baseline laundering* — failing scenarios are quietly accepted to unblock; the bar drops silently. Same failure mode as V16.

## Implementation Notes

- **Start with mined trajectories, not imagined ones.** The first scenarios should be V14 traces of real production tasks — successful and failing alike. Synthesised scenarios come later, and only after the mined ones look realistic in sim.
- **Pin the user-sim and the judge.** Both are LLMs; both move scores when upgraded. Pin them like you pin the SUT in V16. Upgrading either is a re-baseline event.
- **Randomise persona and entry conditions across runs of the same scenario.** A scenario that always runs identically gives one bit of information; small variations (paraphrase, persona, tool latency jitter) give a distribution.
- **Place the User Simulator's goal and persona at the very start of its context.** For long multi-turn simulations, place the goal and persona before the trajectory history. As the trajectory grows, earlier turns move toward mid-context where recall is weakest (mechanism 4); the persona definition must remain in the high-recall start-of-context zone to maintain consistent persona across many turns.
- **Inject failures at production rates, then double.** Real-world tool failure rates from V14 are the floor; double them for stress scenarios. Agents that pass under doubled failure rates are robust; agents that pass only at clean rates are not.
- **Separate scenario authoring from agent authoring.** Same person writes both $\to$ blind spots. Different person, different team, ideally adversarial.
- **Wire V18 into the pre-prod pipeline behind V16, not as a replacement.** V16 catches per-call regressions cheaply; V18 catches trajectory regressions expensively. Both run; V18 gates the larger deploys.
- **Measure simulator-production fidelity quarterly.** Sample paired trajectories: same task in sim and in prod. Score for behavioural divergence. If sim looks meaningfully different from prod, the gate is no longer calibrated.
- **Capture cost and turn-count alongside quality.** A new agent that completes the task in 8 turns when the old one did it in 4 is a regression even if completion-rate is identical.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** V18 chains a *User Simulator* and a *Tool Simulator* against the *Agent Under Test*, with a *Trajectory Judge* (built on **V15 LLM-as-Judge**) consuming the **V14 Trajectory Logging** trace. The agent itself is loaded under its production reliability stack — **V9 Bounded Execution** caps the loop; **V14** instruments it; **V8 Tool Sandboxing** if real tools are mixed in; **V6 Prompt Injection Shield** is the defence whose adversarial scenarios test. The verdict feeds the same deploy gate as **V16 Offline Eval**, which sits in front of any pattern that ships changes (O2, O3, O6, O7).

**The chain — per scenario:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Load scenario `(goal, persona, env_config, failure_profile, expected_outcome)` | `code` | Scenario Suite |
| 2 | Spin up AUT with production setup; attach V14 tracer | `code` | V14 |
| 3 | Loop: user-sim emits turn | `LLM` | User Simulator session |
| 4 | AUT responds, possibly with tool calls | `LLM` | AUT session |
| 5 | Tool-sim returns response per `failure_profile` | `code` or `LLM` | Tool Simulator |
| 6 | Continue until AUT terminates task or hits V9 cap | `code` | V9 Bounded Execution |
| 7 | Persist full trajectory to V14 trace store | `code` | V14 |

**The chain — per run (across scenarios):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 8 | For each trajectory, run Trajectory Judge across dimensions | `LLM` | Judge session (V15) |
| 9 | Aggregate per-scenario, per-dimension scores | `code` | |
| 10 | Compare to baseline with category-aware tolerances | `code` | Comparator |
| 11 | Emit PASS / FAIL with regressed-scenario diff | `code` | Deployment Gate (shared with V16) |

**Skeleton:**

```
run_simulation(aut, scenario_suite, baseline):
    results = []
    for scenario in scenario_suite:                              # code
        trajectory = run_one_scenario(aut, scenario)             # code
        scores     = judge_trajectory(trajectory, scenario)      # LLM (V15)
        results.append((scenario.id, scores))
    metrics = aggregate(results)                                 # code
    diff    = compare(metrics, baseline, category_tolerances)    # code
    verdict = gate(diff)                                         # code
    log_v14(run_id, metrics, diff, verdict)                      # code
    return verdict, diff

run_one_scenario(aut, scenario):
    trace = V14.new_trace(scenario.id)                           # code
    history = []
    for _ in range(scenario.max_turns):                          # V9 bound
        user_msg = user_sim(scenario, history)                   # LLM — user simulator
        if user_msg is END: break
        history.append(user_msg)
        agent_msg, tool_calls = aut.step(history)                # LLM — agent under test
        history.append(agent_msg)
        for call in tool_calls:
            resp = tool_sim(call, scenario.failure_profile)      # code or LLM
            history.append(resp)
        if aut.task_complete(): break
    return trace.finalize(history)
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **User Simulator** | strong generalist, **pinned**; smaller is fine if persona discipline holds | role (*"you are a simulated user with this goal and persona"*); the scenario's goal and persona; partial-knowledge constraint (*"do not reveal facts the agent has not learned"*); termination rule (*"end the conversation when your goal is met or you give up"*); output contract (single user message) | the trajectory so far |
| **Agent Under Test** | whatever model the agent ships with | the agent's **exact production setup** — system prompt, tools, retrieval config, orchestration — loaded once and not modified; if it differs from production the audit is invalid | the dialogue so far + tool responses |
| **Tool Simulator** *(when LLM-driven; deterministic mocks are pure code)* | small fast generalist | role (*"you simulate the responses of {tool} according to its schema and the scenario's failure profile"*); the tool schema; the failure-profile (rates and types of injected failures); content-injection corpus for adversarial scenarios | the tool call arguments |
| **Trajectory Judge** | strong generalist, **pinned**; ideally stronger than the AUT (V15 guidance) | judge role; the trajectory-dimension rubric (task completion, any-turn safety, policy adherence, recovery from injected failure, turn-count / cost budget); output contract (JSON: per-dimension score + reason + citations into the trace) | the scenario goal + expected outcome + the full V14 trace |

**Specialist-model note.** No fine-tuned specialist is required, but four structural choices matter more than model choice:

- **Pin every model in the loop.** AUT, user-sim, tool-sim, judge — all pinned, all re-baselined explicitly on upgrade. A judge upgrade alone moves scores enough to mask real regressions.
- **AUT loaded exactly as production.** Any deviation — different temperature, missing tool, alternate system prompt — invalidates the result. The AUT is not the SUT in V16; it is the *whole stack* the SUT runs inside.
- **User-sim must not see hidden state.** A common bug: the user-sim is configured with the scenario's expected outcome and accidentally leaks it. Separate the persona prompt from the judge's rubric in code; never give the user-sim the answer.
- **Judge reads the trace, not the transcript.** The judge's input includes V14 tool calls, intermediate plans, retrieval results — not just the assistant-visible messages. A judge that reads only the chat transcript is judging surface, not behaviour.

## Open-Source Implementations

- **τ-bench / τ²-bench** — [`github.com/sierra-research/tau-bench`](https://github.com/sierra-research/tau-bench) and [`github.com/sierra-research/tau2-bench`](https://github.com/sierra-research/tau2-bench) — the reference framework for tool-agent-user simulation across realistic domains (retail, airline, telecom, banking). LLM-simulated user pursues a goal across multi-turn dialogue while the agent uses domain APIs under policy; canonical V18 instantiation for customer-service-class agents.
- **Petri** — [`github.com/safety-research/petri`](https://github.com/safety-research/petri) — Anthropic's open-source auditing tool; an Auditor agent drives the target through simulated multi-turn scenarios with simulated tools; a Judge scores along safety dimensions (deception, oversight subversion, power-seeking). Built on UK AISI's Inspect framework. Petri 2.0 (2026) adds new scenarios and eval-awareness mitigations.
- **Bloom** — [`github.com/safety-research/bloom`](https://github.com/safety-research/bloom) — Anthropic's complementary tool to Petri; takes a single behaviour description and automatically generates many scenarios (understanding $\to$ ideation $\to$ rollout $\to$ judgment) to quantify behaviour frequency. MIT-licensed; designed for arbitrary-behaviour audits rather than fixed scenarios.
- **AgentBench** — [`github.com/THUDM/AgentBench`](https://github.com/THUDM/AgentBench) — ICLR 2024 multi-environment benchmark (8 distinct simulated environments — OS, DB, Knowledge Graph, Digital Card Game, etc.) for evaluating LLM agents end-to-end; useful as a capability-side complement to V18's policy-side audits.
- **OpenEvals** — [`github.com/langchain-ai/openevals`](https://github.com/langchain-ai/openevals) — LangChain's open evaluators; the `run_multiturn_simulation` and `create_llm_simulated_user` primitives are the minimum viable V18 user-simulator wiring for chat-class agents. Pairs with LangSmith for hosted scenario suites and run management.
- **LangGraph agent-simulation tutorials** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the `examples/chatbot-simulation-evaluation/` notebooks (LangSmith-agent-simulation-evaluation) provide runnable references for multi-turn-simulated evaluation against LangSmith datasets.
- **AgentEvals** — [`github.com/langchain-ai/agentevals`](https://github.com/langchain-ai/agentevals) — trajectory-match evaluators (expected-trajectory match and LLM-judged trajectory match) for agent execution traces; the trajectory-level scoring component V18 needs.
- **Inspect AI** — [`github.com/UKGovernmentBEIS/inspect_ai`](https://github.com/UKGovernmentBEIS/inspect_ai) — UK AISI's evaluation framework; tool-use, multi-turn, and model-graded scoring as first-class primitives; the substrate Petri and Bloom build on.

## Known Uses

- **Anthropic Alignment Science** — Petri used to audit 14 frontier models across 111 seed instructions (2025); Bloom used to characterise behaviours like sycophancy and self-preservation across 16 frontier models with 100 rollouts $\times$ 3 (2025).
- **UK AI Security Institute, METR, Apollo Research** — Inspect-based simulation evals are the shared substrate for frontier-model safety audits across the AISI network.
- **Sierra Research / Tau-Bench leaderboard** (`taubench.com`) — public leaderboard for customer-service agent performance across retail, airline, telecom, banking domains; widely used by labs and product teams to compare agent stacks pre-launch.
- **OpenAI, Anthropic** — both teams publicly use multi-turn simulation harnesses for agent-product validation; specific tooling proprietary, but LangSmith / Inspect / Petri are the open analogues.
- **Customer-service agent vendors** (Sierra, Decagon, Ada) — simulated-user evaluation pre-deployment is standard practice for high-stakes deployments; tau-bench-class harnesses dominate.
- **Anthropic "Building Effective Agents"** guidance — end-to-end testing under simulated conditions named as a prerequisite for production agent deployment.

## Related Patterns

- **Pairs with** V16 Offline Eval — V16 catches *per-call* regressions on flat case/answer pairs; V18 catches *trajectory* regressions on end-to-end runs. Production stacks run both; V18 gates the larger deploys behind V16's faster gate.
- **Pairs with** V17 Online Eval — V18 is the rich pre-prod complement; V17 is the cheap continuous post-prod complement. Together they bracket production.
- **Composes with** V14 Trajectory Logging — V14 is both the source of mined scenarios (real failures $\to$ new V18 scenarios) and the data the Trajectory Judge consumes; V18 is the highest-leverage downstream consumer of V14.
- **Composes with** V15 LLM-as-Judge — the Trajectory Judge is V15 applied to traces rather than to outputs; same primitive, harder rubric.
- **Composes with** V9 Bounded Execution — V18 scenarios must bound the agent loop or stuck agents inflate cost without ending; V18 also tests that V9 fires correctly under simulated runaway.
- **Composes with** V6 Prompt Injection Shield — V18's adversarial scenario category is V6's permanent regression test, run as full simulated conversations rather than isolated strings.
- **Composes with** V8 Tool Sandboxing — when V18 uses real tools rather than simulators, V8 is mandatory to prevent simulation runs from causing real side effects.
- **Composes with** O6 Orchestrator-Workers, O7 Supervisor Hierarchy, O11 Blackboard — multi-agent systems' emergent behaviour is the case where V18 is most differentiated from V16; flat eval cannot see inter-agent dynamics.
- **Distinct from** V16 — V16 evaluates per-call against ground truth; V18 evaluates whole trajectories against trajectory-level criteria. Choosing one and skipping the other for a trajectory-shaped agent is an anti-pattern.
- **Distinct from** V17 — V17 monitors live traffic with no ground truth and no control; V18 runs synthetic traffic with controlled conditions. Different questions, different tools.
- **Defends against** A13 Pilot Simplification — V18's failure-injection and adversarial scenario categories are the operational remedy.

## Sources

- Yao et al. (2024) — "τ-bench: A Benchmark for Tool-Agent-User Interaction in Real-World Domains" (arXiv 2406.12045) — canonical formalisation of simulated-user / simulated-tool agent evaluation.
- Sierra Research (2025–26) — "τ²-bench: Evaluating Conversational Agents in a Dual-Control Environment" (arXiv 2506.07982) — telecom-domain extension and dual-control framing.
- Anthropic Alignment Science (2025) — "Petri: An open-source auditing tool to accelerate AI safety research."
- Anthropic Alignment Science (2026) — "Petri 2.0: New Scenarios, New Model Comparisons, and Improved Eval-Awareness Mitigations" — the eval-awareness problem and its mitigations.
- Anthropic Alignment Science (2025) — "Bloom: an open source tool for automated behavioural evaluations."
- Liu et al. (2023) — "AgentBench: Evaluating LLMs as Agents" (arXiv 2308.03688; ICLR 2024) — multi-environment end-to-end LLM-agent benchmarking.
- Anthropic (2024–25) — "Building Effective Agents" — end-to-end simulated testing as a deploy prerequisite.
- Composio (2025) — AI Agent Report — 88% production-failure analysis; A13 Pilot Simplification framing.
- UK AI Security Institute — Inspect AI framework (substrate for Petri and Bloom).
- Software testing tradition: integration testing, chaos engineering, fuzz testing — the conceptual ancestors adapted for agentic systems.
