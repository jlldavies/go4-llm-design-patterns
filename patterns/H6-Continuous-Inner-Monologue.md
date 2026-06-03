# H6 — Continuous Inner Monologue

> Run a persistent background reasoning process — distinct from the user-facing responder — that thinks between turns and across sessions, writing its reflections to a shared store the responder reads on its next turn.

**Also Known As:** MIRROR Pattern, Thinker Agent, Inner Monologue, Cognitive Inner Monologue, Vygotskian Inner Speech for LLMs, Background Reasoning Stream.

**Classification:** Category VII — Humanizers · *continuity / self-improvement* role — a between-turn, cross-session background reasoning loop that gives an agent a persistent inner life rather than a per-turn one.

---

## Intent

Maintain a continuous, autonomous inner monologue — a Thinker process separate from the user-facing Responder — that reflects between turns, consolidates across sessions, and writes its conclusions to a shared memory the Responder reads on the next interaction.

## Motivation

Out of the box, an LLM agent has no thoughts between turns. When the user is not speaking, nothing is happening: no reflection on the last exchange, no consolidation of what was learned, no anticipation of what is coming, no monitoring of pending commitments. The agent is a function from input to output and nothing more. For a personal assistant, a coaching agent, a long-running autonomous worker, that flatness shows: every turn starts cold, prior exchanges are revisited only when retrieved, slow realisations never land because there is no slow process for them to land in.

The MIRROR architecture (Hsing, 2025; arXiv 2506.00430) names the move that fixes this: install a *cognitive inner monologue* — a Thinker that runs between conversational turns, generating parallel cognitive threads (goals, reasoning, memory), and a Cognitive Controller that synthesises those threads into a bounded first-person narrative the Responder uses on the next turn. The architecture grounds in four converging cognitive-science strands: Vygotskian inner speech (private language as a tool for thought), Global Workspace Theory (parallel specialised processes synthesised into a unified workspace), reconstructive episodic memory (each turn's narrative is rebuilt, not appended), and complementary learning systems (fast response, slow consolidation). MIRROR's evaluation on the CuRaTe safety benchmark shows up to 156% relative improvement in conflicting-preference safety scenarios — empirical evidence that *between-turn thinking* is not ornamental.

The defining structural claim is **temporal separation**: response time and reflection time live on different clocks. Response time is bounded by the user's tolerance; reflection time is bounded by the next-turn deadline (or by nothing at all, for cross-session consolidation). The Thinker writes its conclusions to a shared memory; the Responder reads them. The two never block on each other.

That is what makes H6 a distinct pattern, not a slightly-bigger prompt. It introduces a new participant (the Thinker), a new schedule (between turns, between sessions), and a new failure mode (Thinker-Responder divergence). No combination of S-, R-, or K-patterns produces those participants without naming them.

The separation is also mechanically motivated. If the Thinker's full reasoning history were concatenated into the Responder's context, the combined sequence length would pay O(n²) attention computation on every user-facing turn — the background reasoning doubles or triples the Responder's effective context (mechanism 2). By running the Thinker in a separate session (mechanism 6 — subagent decomposition as context bounding), each participant operates on a bounded seq_len; only the compact reconstructed narrative crosses the boundary. This is the same context-bounding principle that makes multi-agent architectures mechanically optimal: the orchestrator receives a compact result, not the full reasoning chain.

## Applicability

Use H6 when:

- the agent runs in a persistent session or across sessions and the *between-turn* time is wasted today;
- response quality benefits from reflection that does not fit a single turn's latency budget but is not urgent either;
- the agent must monitor for asynchronous conditions (approaching deadlines, drifting commitments, accumulated context) without the user prompting;
- consolidation across sessions matters — what the agent learned today should change what it does tomorrow without retraining;
- the deployment supports an asynchronous worker (background job, separate process, scheduler) alongside the responder.

Do not use H6 when:

- every turn is purely stateless Q&A — there is no between-turn time worth filling; **O1 Single Agent** with appropriate retrieval suffices;
- the workload is real-time dual-latency *within a single turn* — that is **R16 Talker-Reasoner**, a different pattern (see Related Patterns);
- the agent has no persistent memory channel to write to — H6 requires **K11 Observational Memory** or **K12 Karpathy Memory** as substrate; install one of those first;
- you cannot afford asynchronous inference cost or cannot bound it — without **V9 Bounded Execution** the Thinker burns money silently;
- the agent is autonomous-action-capable and the Thinker's conclusions could trigger side effects — wire **V1 Human-in-the-Loop** or **V2 Human-on-the-Loop** first.

## Decision Criteria

H6 is right when between-turn time is real, reflection earns its keep, and a shared memory channel and a cost bound are both in place.

**1. Measure the between-turn budget.** What is the *expected idle time* between turns on this agent? Voice assistant in active conversation: ~10s typical, not enough. Personal assistant across a workday: minutes-to-hours, plenty. Below ~30s of expected idle, the Thinker rarely finishes useful work; collapse to **R7 Reflexion** inside the next turn instead.

**2. Score the reflection lift.** On a labelled sample, measure quality on turns where the agent has time to reflect first vs. cold turns. If the *reflected* turns score materially better ($\geq$10% on the relevant rubric — V15 LLM-as-Judge is fine for this), H6 is paying. Below 10%, the reflection is decorative.

**3. Cost the Thinker.** The Thinker is an LLM that runs without a user waiting. Annualise: trigger rate $\times$ Thinker cost per run. Compare to the Responder's annual cost and to the V9 cap you intend to enforce. If the Thinker would account for >30% of total inference cost, tighten the trigger or shrink the Thinker's per-run budget — H6 is leverage, not a doubled bill.

**4. Pick the memory channel.** H6 lives or dies by the Thinker$\to$Responder handoff. **K11 Observational Memory** if the natural channel is the activity log itself (Thinker appends reflections; Responder reads cached log). **K12 Karpathy Memory** if the natural channel is structured notes the Thinker curates. Name the channel before building or the two roles drift.

**5. Bound the Thinker.** Wire **V9 Bounded Execution** at the session and the day level (max Thinker runs / session, max cumulative cost / day). H6 without a bound is the canonical runaway-cost failure of this pattern.

**6. Decide the surface rule.** When the Thinker concludes something the Responder has not yet shown the user, how does it land? Three options: *next-turn quiet* (Responder incorporates silently), *next-turn declared* ("I had a moment to think about your earlier point…"), *surface now* (Responder proactively messages the user — requires **V1** or **V2** gate). Wrong choice produces either jarring interjections or invisible thinking.

**Quick test — H6 is the right pattern when:**

- expected between-turn idle $\geq$ ~30s (or cross-session reflection is the goal), *and*
- a labelled reflection-lift study shows $\geq$10% quality gain from between-turn reflection, *and*
- a shared memory channel (K11 or K12) is named and built, *and*
- a V9 bound is in place at session and day level, *and*
- the surface rule for Thinker conclusions is decided and the action gate (V1 / V2) is wired if conclusions can trigger side effects.

If between-turn idle is short, choose **R7 Reflexion** inside the next turn — same instinct, no separate process. If the requirement is real-time dual-latency within a single turn (fast voice front, slow reasoning back), choose **R16 Talker-Reasoner** — same dual-process framing, different time scale. If the only need is to remember what was said, install **K11** or **K12** without the Thinker — H6 is justified only when reflection has work to do.

## Structure

```
   ┌─────────────────────────────────────────────────────────────┐
   │                    Shared Memory                            │
   │  (activity log / curated notes — K11 or K12)                │
   │  Thinker writes reflections; Responder reads them.          │
   └─────────────────────────────────────────────────────────────┘
        ▲                                          ▲
        │ writes reflections,                      │ reads on every turn,
        │ goal updates, consolidations             │ may signal Thinker
        │                                          │
   ┌─────────────┐                          ┌─────────────┐
   │   Thinker   │                          │  Responder  │
   │  (background)                          │  (user-facing)
   │             │                          │             │
   │  loops on:  │                          │  per turn:  │
   │  • reflect  │                          │  • read mem │
   │  • monitor  │                          │  • respond  │
   │  • consolid.│                          │  • signal   │
   │  • predict  │                          │    Thinker  │
   └─────────────┘                          └─────────────┘
        ▲                                          │
        │ scheduled trigger                        │ user turn
        │ (interval, milestone, end-of-session)    │
        │                                          ▼
     Scheduler                                   User
```

The Thinker and the Responder share *only* the memory channel. They never call each other directly.

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Responder** | producing every user-facing turn within the conversational latency budget | user turn + shared memory (including any Thinker reflections since last turn) $\to$ reply | block on the Thinker; perform deep reflection inline (that is the Thinker's job and inflates response latency); write Thinker-class reflections to shared memory itself. |
| **Thinker** | background reflection between turns and consolidation across sessions — generating parallel cognitive threads (goals, reasoning, memory) and synthesising them into a bounded narrative | shared memory + recent activity $\to$ updated reflections / goals / consolidated narrative in shared memory | speak to the user directly (Responder's job); take autonomous side-effectful actions (those must route through V1/V2); run unbounded (V9 caps cumulative cost). |
| **Cognitive Controller** *(MIRROR-specific role; often a Thinker sub-step)* | synthesising the Thinker's parallel threads into a *single bounded* first-person narrative reconstructed each cycle, not accumulated | parallel threads $\to$ one coherent narrative state | let the narrative grow unboundedly across cycles — the reconstruction (not the accumulation) is what makes it tractable. |
| **Shared Memory** | the only channel through which Thinker and Responder communicate | reads/writes from both $\to$ coherent state both can rely on | be edited by anything other than Thinker and Responder; allow concurrent writes without a discipline (last-writer-wins is fine if it is *known* to be last-writer-wins). |
| **Scheduler** | deciding *when* the Thinker runs — interval, milestone, end-of-session, idle-detected | system clock + activity signals $\to$ Thinker invocation | run the Thinker on every turn (collapses to R7 inline) or never (collapses to no H6 at all); the cadence is the main tuning lever. |
| **Action Gate** *(only if Thinker conclusions can trigger side effects)* | enforcing V1 / V2 governance over any Thinker-initiated action surfacing to the user or the world | proposed action + policy $\to$ approved / queued / rejected | be bypassed by the Thinker; without this, H6 becomes an autonomous-action pattern, which it must never be by default. |

The Thinker and Responder are **distinct configured sessions**, even when the same model serves both. Same model is fine; same prompt and same invocation context are not — the roles must be separable or the pattern collapses.

## Collaborations

The Responder handles a user turn the usual way: read shared memory, generate a reply within the latency budget, send. After the reply, the Responder may write a brief activity signal back to memory (what was said, what the user asked for, any flag for the Thinker). Between turns — driven by the Scheduler, not by the Responder — the Thinker wakes. It reads the recent activity, the existing reflections, and whatever cognitive-thread structure the design uses (goals, reasoning, memory). It generates parallel threads in a single LLM call (or a small fan-out), then the Cognitive Controller step synthesises them into one bounded narrative and writes that narrative back to shared memory, replacing the prior narrative rather than appending to it. At session boundaries, the Thinker may do a heavier *consolidation* run — distilling the session's reflections into something the agent will carry forward (this is where H6 composes with **K12 Karpathy Memory**, curating durable notes, or **H2 Episodic Self-Improvement**, harvesting lessons). The next user turn arrives; the Responder reads the updated memory; the cycle continues.

If a Thinker conclusion implies an action — surface a reminder to the user, defer a task, escalate a risk — it does not act. It writes a *proposal* to memory. The Responder picks it up on the next turn and either acts on it under the Action Gate (V1 / V2), or chooses not to. The Thinker proposes; the Responder, gated, disposes.

## Consequences

**Benefits**

- The agent gains a between-turn inner life: realisations land, commitments are tracked, reflections accumulate without retraining (mechanism 10).
- Response latency stays bounded — the Thinker never blocks the Responder.
- Cross-session consolidation becomes a first-class operation, not a happy accident of memory retrieval.
- Empirically validated: MIRROR demonstrates large safety-reasoning gains in multi-turn conflicting-preference scenarios.
- Maps cleanly onto cognitive-science theory (Vygotsky, Global Workspace, complementary learning) — the architectural shape is principled, not ad hoc.

**Costs**

- A second LLM session running on its own schedule — billable inference whether or not a user is present.
- Engineering complexity: scheduling, memory concurrency, surface rules, action gating.
- The reflection cycle adds a write-pressure load on the memory store; pair with appropriate compaction (K6).
- Two configured sessions to keep in sync — Thinker prompt and Responder prompt evolve together or they diverge.

**Risks and failure modes**

- *Thinker-Responder divergence.* Independent sessions drift: the Thinker reaches a conclusion the Responder contradicts on the next turn because their setups have evolved separately.
- *Surface-rule mismatch.* The Thinker concludes; the Responder fails to read; the user never benefits — silent inner monologue with no external effect.
- *Runaway Thinker cost.* No V9 bound, no idle detection, and the Thinker runs forever, burning tokens without proportional value.
- *Narrative accumulation.* The Cognitive Controller is meant to *reconstruct* each turn; if instead it appends, the narrative grows unboundedly and the Thinker chokes on its own history.
- *Autonomous action leak.* The Thinker's proposals reach the user or the world without an Action Gate; H6 turns into uncontrolled autonomous operation. This is the most serious failure mode.
- *Overthinking simple turns.* A Thinker that always runs hard injects nuance the user did not ask for; the Responder's replies feel laboured.

## Implementation Notes

- Start by installing the memory channel — **K11** (activity log + cache) or **K12** (curated notes) — before wiring the Thinker. H6 with no shared store is a pattern with no plumbing.
- Begin small: Thinker version 1 runs only **R7 Reflexion** on the most recent exchange and writes a one-paragraph reflection to memory. Once that earns its keep, add goal-tracking, monitoring, consolidation.
- Schedule deliberately. Triggers worth using: end-of-turn (run once per user turn, post-reply, fire-and-forget); end-of-session (heavier consolidation); idle interval (every N minutes of session activity, capped); explicit signal (Responder flags "needs reflection"). Avoid continuous polling — it collapses cost discipline.
- Enforce **V9 Bounded Execution** at session level and day level. Per-run budget is fine; cumulative bound is the one that saves you.
- Treat the Cognitive Controller's narrative as *bounded and reconstructed*. Cap it (e.g. $\leq$ 500 tokens) and rebuild it from threads each cycle rather than appending. This is the MIRROR-specific discipline that prevents the inner monologue from becoming a runaway log. The mechanical reason reconstruction is mandatory, not appendage: the KV cache does not persist across API calls (mechanism 3). Each Thinker invocation reads the current narrative into context to reason from. If the narrative grows unboundedly by appending, seq_len grows unboundedly with it, and the O(n²) cost of each Thinker invocation grows without bound. Reconstruction caps this at a stable narrative size, keeping each Thinker call's cost bounded.
- **Thinker prefix caching.** The Thinker's setup — role, H1 identity block, reflection protocol, narrative bound — is a stable prefix across invocations. If it exceeds 1,024 tokens it qualifies for provider prefix caching (mechanism 5: ~10% of input token cost on a cache hit). Design the Thinker's system prompt as a stable prefix; session-specific input goes in the per-call prompt only.
- Make divergence detectable: log Thinker conclusions and the Responder turns that follow; surface contradictions via V15 LLM-as-Judge or a simple inconsistency check.
- Gate any Thinker-proposed action through **V1** (approval) or **V2** (monitoring). H6 is a *thinking* pattern by default; it crosses into *acting* only with deliberate wiring.
- Compose with **H1 Identity Persistence** — the Thinker's reflections should refer to the agent's stable self-model, not redefine it each cycle. The Thinker is allowed to update goals and beliefs; it is not allowed to rewrite identity.
- Pair with **V14 Trajectory Logging** so the Thinker's runs are on the same timeline as Responder turns. Debugging H6 without that unified trace is intractable.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** H6 runs a *Responder* session and a *Thinker* session against a shared memory store. The memory channel is **K11 Observational Memory** (activity log) or **K12 Karpathy Memory** (curated notes), one or both. The Thinker often runs **R7 Reflexion** inside its own loop and may emit lessons that feed **H2 Episodic Self-Improvement**. The architecture sits on top of **H1 Identity Persistence** (stable self), bounds via **V9 Bounded Execution**, gates any actions through **V1 / V2**, and is observable via **V14 Trajectory Logging**.

**The chain — per user turn (Responder path):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Read shared memory: current narrative + any reflections since last turn | `code` | K11 / K12 |
| 2 | Responder generates reply within latency budget | `LLM` | Responder session |
| 3 | Write activity signal (turn summary, any flag) to memory | `code` | K11 |
| 4 | Optionally trigger Thinker (end-of-turn schedule) | `code` | Scheduler |

**The chain — Thinker run (background, scheduled):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| T1 | Read shared memory: current narrative, recent activity, prior reflections | `code` | K11 / K12 |
| T2 | Generate parallel cognitive threads (goals, reasoning, memory) | `LLM` | Thinker session; may run R7 |
| T3 | Cognitive Controller synthesises threads into bounded narrative | `LLM` | Thinker session (separate prompt) |
| T4 | Write reconstructed narrative + any action proposals back to memory | `code` | |
| T5 | Check V9 bound (session + day); halt if exceeded | `code` | V9 |
| T6 | *(optional, session boundary)* Consolidate session into K12 notes / H2 lessons | `LLM` | K12 / H2 |

**Skeleton:**

```
on_user_turn(turn, memory):
    state = memory.read()                              # code — K11/K12
    reply = Responder(turn, state)                     # LLM — bounded latency
    memory.append_activity(turn, reply)                # code — K11
    schedule_thinker(after_turn=True)                  # code — Scheduler, async
    return reply                                        # code

thinker_run(memory, schedule_context):                 # background
    if not bound.allow():                              # code — V9 session/day cap
        return
    state = memory.read()                              # code — current narrative + activity
    threads = Thinker(state)                           # LLM — parallel cognitive threads
    narrative = CognitiveController(threads, state)    # LLM — bounded reconstruction
    proposals = extract_action_proposals(narrative)    # code
    memory.write_narrative(narrative)                  # code — replaces prior narrative
    memory.write_proposals(proposals)                  # code — Responder + V1 gate consume
    if schedule_context == "end_of_session":           # code
        Consolidator(state, narrative, lessons_store)  # LLM — K12 notes / H2 lessons
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Responder** | capable generalist, latency-tuned | role (*"you are the user-facing voice; you respond within the latency budget drawing on the shared memory and the Thinker's current narrative; you never block on the Thinker"*); response format (S6); H1 identity block; rule for handling pending Thinker proposals (gate through V1/V2 surface rule) | the user turn + the current shared memory state |
| **Thinker** | capable generalist, *quality-tuned, not latency-tuned* (often the strongest available model) | role (*"you are the agent's inner monologue; you reflect between turns; you do not speak to the user; you write to the shared memory only"*); the cognitive-thread schema (goals / reasoning / memory); reflection protocol (R7 if used); H1 identity block (read-only reference); the narrative bound (e.g. $\leq$500 tokens, reconstruct not append) | the current narrative + recent activity since last Thinker run |
| **Cognitive Controller** *(can be a separate prompt on the same Thinker model, or its own session)* | same model as Thinker | role (*"synthesise the parallel threads into a single first-person narrative; bounded length; reconstructed, not accumulated"*); the bound; the narrative schema | the threads emitted by step T2 + prior narrative for context only |
| **Consolidator** *(optional, session-boundary only)* | capable generalist | role (*"distil the session's reflections into durable notes / lessons"*); K12 schema or H2 lesson format | the session's narrative + activity log |

**Specialist-model note.** No fine-tuned specialist is required. Two structural choices change everything:

- The Responder and Thinker **must be distinct configured sessions**, even when the same model serves both. Same model is fine; same prompt and same invocation context are not. Mixing them is the canonical failure mode — the Responder starts "thinking harder" and stalls, or the Thinker starts replying.
- The Cognitive Controller's *bounded reconstruction* is non-negotiable. Whether it is a separate LLM session or a separate prompt on the Thinker model, the discipline of rebuilding the narrative each cycle (not appending) is what keeps the inner monologue tractable across long sessions and across days.

A long-context model materially helps the Thinker, which carries narrative + activity + identity; the Responder can run on a shorter, faster model if cost matters.

## Open-Source Implementations

- **MIRROR** — [`github.com/arcarae/MIRROR`](https://github.com/arcarae/MIRROR) — official implementation of the MIRROR cognitive inner-monologue architecture from arXiv 2506.00430. Implements the Inner Monologue Manager (parallel threads), Cognitive Controller (bounded reconstructed narrative), and Talker (responder), with the CuRaTe benchmark evaluation harness. CC-BY-4.0. The reference implementation of this pattern.
- **Letta** — [`github.com/letta-ai/letta`](https://github.com/letta-ai/letta) — when paired with a scheduled reflection job and Letta's editable core-memory blocks (K12), provides a serviceable substrate for a Thinker-Responder split. Reference for the memory channel; the inner-monologue scheduling is BYO.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — state-machine + concurrent-node primitives make it natural to wire a Responder graph alongside a scheduled Thinker job sharing a state object. Substrate, not a turnkey H6 implementation.

H6 is an *architecture pattern* more than a library pattern. Outside the MIRROR reference implementation, most production embodiments are bespoke: a scheduled background job (Cron, a queue worker, an idle-detector) running an LLM call against a memory store the responder also reads. The framework question is mostly about the memory channel (Letta for K12; a flat log + cache for K11) and the orchestration layer (LangGraph, a job queue, a workflow engine).

## Known Uses

- **MIRROR**-instrumented dialogue systems — Hsing's evaluation on the CuRaTe benchmark demonstrates large gains in personalised-safety scenarios with conflicting preferences and multi-turn consistency.
- **Letta**-based personal-assistant agents — between-session consolidation jobs that update curated memory blocks, functioning as a Thinker over the K12 channel.
- **Long-running coding agents** (Claude Code-style, Cursor agents) — session-boundary reflection that updates project-level CLAUDE.md / rules files is an H6 instance in practice, with the Thinker as a deliberate end-of-session consolidation step rather than a continuous loop.
- **Monitoring / observability agents** that wake on an interval to scan logs, update a working narrative, and write proposals for the user-facing responder to act on — H6 used as a between-turn surveillance pattern.

## Related Patterns

- **Distinct from R16 Talker-Reasoner.** Both are dual-process architectures grounded in cognitive science, but they operate on different time scales and serve different needs. **R16** is *single-turn fast/slow routing*: within one user-facing interaction, a fast Talker responds while a slow Reasoner deliberates in parallel, with the Reasoner's output landing in the same conversational window. **H6** is *between-turn persistent background reasoning*: the Thinker runs in the gap between turns, across sessions, with reflections written to a durable memory channel for the next turn (or the next day) to pick up. R16's Reasoner is on the clock of the conversation; H6's Thinker is on the clock of the agent's life. Use R16 when real-time interactive latency is the constraint; use H6 when between-turn time is the asset. They compose: a system can be Talker-Reasoner within a turn and Thinker-Responder between turns.
- **Required by** any Humanizer composition that wants between-turn reflection (H2, H4, H9 all benefit but do not require H6; H5 benefits from H6 as the channel through which principle-evolution proposals are formed).
- **Composes with H1 Identity Persistence** — the Thinker reads H1's invariant self-model as reference; its reflections update goals and beliefs but never identity.
- **Composes with K11 Observational Memory** — natural channel when the Thinker reflects over the activity log and writes back into it.
- **Composes with K12 Karpathy Memory** — natural channel when the Thinker curates structured notes the Responder reads.
- **Composes with H2 Episodic Self-Improvement** — the Thinker's end-of-session consolidation is the natural harvesting moment for lessons.
- **Uses inside the Thinker** R7 Reflexion — the Thinker's reflection step is often a Reflexion call over the latest exchange.
- **Pairs with V9 Bounded Execution** — session-level and day-level caps on Thinker cost; without these, H6 leaks money.
- **Pairs with V14 Trajectory Logging** — Thinker runs and Responder turns must share a timeline to be debuggable.
- **Pairs with V1 Human-in-the-Loop / V2 Human-on-the-Loop** — any Thinker-proposed action surfaces through one of these gates; H6 is a thinking pattern, not an acting pattern, unless explicitly wired otherwise.
- **Sibling of H3 Entropy-Driven Curiosity** — both are between-turn autonomous mechanisms; H3 detects stagnation, H6 produces continuous reflection. They can compose: the Thinker can trigger H3 when it notices its own reflections cycling.

## Sources

- Hsing, N. S. (2025) — "MIRROR: Cognitive Inner Monologue Between Conversational Turns for Persistent Reflection and Reasoning in Conversational LLMs" — [arXiv 2506.00430](https://arxiv.org/abs/2506.00430). Primary source. Introduces the Inner Monologue Manager + Cognitive Controller + Talker architecture; grounds the design in Vygotskian inner speech, Global Workspace Theory, reconstructive episodic memory, and complementary learning systems; demonstrates up to 156% relative improvement on the CuRaTe safety benchmark.
- Christakopoulou, K., Mourad, S., & Matarić, M. (2024) — "Agents Thinking Fast and Slow: A Talker-Reasoner Architecture" ([arXiv 2410.08328](https://arxiv.org/abs/2410.08328)). The sibling dual-process pattern (R16); cited here because H6 must be distinguished from it.
- Vygotsky, L. S. (1934/1986) — *Thought and Language*. The inner-speech foundation MIRROR maps onto.
- Baars, B. J. (1988) — *A Cognitive Theory of Consciousness*. Global Workspace Theory; the parallel-threads-into-bounded-narrative move H6's Cognitive Controller implements.
- McClelland, J. L., McNaughton, B. L., & O'Reilly, R. C. (1995) — "Why there are complementary learning systems in the hippocampus and neocortex." *Psychological Review*. The fast-response / slow-consolidation split that motivates the Thinker's between-turn schedule.
- Packer et al. (2023) — "MemGPT: Towards LLMs as Operating Systems" ([arXiv 2310.08560](https://arxiv.org/abs/2310.08560)). The OS-style architecture in which a persistent agent process maintains state across interactions; the deployment substrate H6 typically runs on.
