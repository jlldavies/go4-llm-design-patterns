# R16 — Talker-Reasoner

> Split the agent into a fast, conversational Talker that handles every user turn in real time and a slow, deliberative Reasoner that thinks in the background and injects conclusions when ready — two cognitive speeds running concurrently against a shared memory.

**Also Known As:** System 1 / System 2 Architecture, Fast-Slow Agent, Dual-Process Agent, Thinking Fast and Slow Agent.

**Classification:** Category III — Reasoning · a *dual-latency architectural* pattern — two configured sessions of one model (or two models) wired in parallel, not in series.

---

## Intent

Decouple the latency budget of *responding* from the latency budget of *thinking*, so the agent can answer every turn within a hard real-time bound while still performing arbitrarily deep reasoning whose results land when they are ready.

## Motivation

A single-agent loop forces every turn through one latency budget. If reasoning is cheap, conversation feels alive but quality is shallow. If reasoning is deep, every utterance stalls while the agent thinks. The patterns that try to bridge this — R4 ReAct, R7 Reflexion, R9 Tree of Thoughts — all sit *on the critical path*: the user waits for the chain to finish. For a voice agent, a coaching agent, or any interactive system, that wait is not paid for by quality; the user has already moved on.

Christakopoulou et al. (2024) framed the fix as a direct mapping to Kahneman's dual-process theory. **System 1 (Talker)** is fast, intuitive, and conversational — it always responds, drawing on what is currently believed. **System 2 (Reasoner)** is slow, deliberative, and tool-using — it runs in the background and updates the shared belief state when its deliberation completes. The latency benefit is mechanically grounded in KV cache independence (mechanism 3): each Talker API call creates a fresh KV cache from its prompt; the Reasoner's in-progress deliberation runs in its own independent KV cache (mechanism 3 — the cache does not persist across API calls, so each session's sequence length is bounded to its own context). The Talker's seq_len and O(n²) attention cost (mechanism 2) are bounded by its compact system prompt + latest user turn, independent of how long the Reasoner has been running. The Talker never blocks on the Reasoner; the Reasoner never gets rushed by the Talker. Each turn gets a Talker response; some turns also incorporate freshly arrived Reasoner conclusions.

The defining structural claim is *concurrency, not sequence*. R3 Plan-and-Solve plans then executes; R4 ReAct thinks then acts then thinks; R7 Reflexion runs then reflects then runs. All three serialise reasoning into the response path. R16 *parallelises* them: the Reasoner thinks while the Talker talks, and the two communicate only through a shared memory channel. The architectural unit is no longer "an LLM call" but "two LLMs running on different clocks against the same state."

That is what makes R16 a distinct pattern from H6 Continuous Inner Monologue. H6 keeps a persistent asynchronous *thought stream* within a single agent's loop; R16 splits the agent itself into two sessions with different roles, different models, and different latency targets. The structural participants — Talker, Reasoner, shared memory, sync rule — are not present in H6.

## Applicability

Use when:

- the system is interactive and the per-turn latency budget is hard (sub-second voice, sub-2s chat) yet the task quality requires multi-step reasoning, tool use, or planning;
- workloads are mixed — most turns are conversational, some require deliberation, and the agent cannot tell in advance how many;
- you can afford concurrent inference (two models or two sessions running in parallel);
- the shared state has a natural place to write deliberation outputs (working memory, a plan slot, a recommendation field) without rewriting the Talker's prompt.

Do not use when:

- the workload is uniformly deliberative (every turn needs the full plan) — collapse to **R3 Plan-and-Solve** or **R4 ReAct**, since the Reasoner is on the critical path anyway;
- the workload is uniformly conversational (no turn needs deep reasoning) — a single fast Talker (**O1 Single Agent** with **R1**) is simpler;
- you need only background reflection within a single agent without a fast user-facing thread — use **H6 Continuous Inner Monologue**;
- concurrent inference budget is not available — fall back to **R3** or **R4** with **V9 Bounded Execution** capping the response latency.

## Decision Criteria

R16 is right when interactivity is non-negotiable and quality requires deliberation that does not fit a single turn.

**1. Measure the turn-latency budget.** What is the hard upper bound on response time? Voice agents: ~800ms target, ~1.5s ceiling. Chat: ~2s comfortable. If the budget is generous (>5s) and reasoning fits, **R4 ReAct** with sensible bounds is simpler.

**2. Estimate the deliberation share.** On a labelled sample of turns: what fraction need real reasoning (planning, multi-tool, multi-hop)? **5–40%** is the sweet spot for R16. <5% means a fast Talker alone suffices. >40% means the Reasoner is hot all the time and you should consider **R4** with a fast model instead.

**3. Cost concurrent inference.** R16 typically holds *two* sessions warm. Annualise: (Talker QPS $\times$ Talker cost) + (Reasoner triggers/day $\times$ Reasoner cost). If concurrent inference is unaffordable, fall back to **R4** with **V9** caps.

**4. Pick the sync rule.** How does Reasoner output reach the user? Options: *fire-and-forget* (Reasoner result lands in memory; next Talker turn picks it up), *interrupt* (Reasoner pushes a follow-up message into the stream), *pull* (Talker checks for a result before each response). The wrong choice produces either stale advice or jarring interjections.

**5. Decide the memory channel.** R16 lives or dies by the shared state. A working-memory slot (**K8**) for in-session, a curated note (**K12**) for cross-session — name it before building or the two agents drift.

**6. Bound the Reasoner.** Reasoner runs effectively without a per-turn cap; that is the point. But unbounded *cumulative* runtime burns money. Pair with **V9 Bounded Execution** at the session level (max deliberations / hour, max cost per session).

**Quick test — R16 is the right pattern when:**

- per-turn latency budget is hard (sub-2s typical, sub-second for voice), *and*
- 5–40% of turns benefit from deliberation that exceeds that budget, *and*
- concurrent inference is affordable, *and*
- a clear shared-memory channel exists for Reasoner$\to$Talker handoff, *and*
- a sync rule (fire-and-forget / interrupt / pull) fits the UX.

If the budget is loose, **R4 ReAct** is simpler. If every turn needs deep reasoning, **R3 Plan-and-Solve** keeps planning visible and is cheaper. If you need background reflection within one agent rather than a parallel architecture, **H6 Continuous Inner Monologue**.

## Structure

```
                     ┌──────────────────────────────────────┐
                     │            Shared Memory             │
                     │  (working state, beliefs, plan slot, │
                     │   pending Reasoner conclusions)      │
                     └──────────────────────────────────────┘
                          ▲                       ▲
            reads + writes│         reads + writes│
                          │                       │
   user turn ─────▶ ┌────────────┐         ┌────────────┐
                    │  Talker    │  spawn  │  Reasoner  │
                    │ (System 1) │ ──────▶ │ (System 2) │
                    │  fast,     │         │  slow,     │
                    │  always    │         │  tool-use, │
                    │  responds  │         │  planning  │
                    └────────────┘         └────────────┘
                          │                       │
                  response within            conclusion lands
                  latency budget             when it lands
                          ▼                       ▼
                       user                  Shared Memory
                                          (picked up next turn)
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Talker (System 1)** | producing the user-facing response on every turn within the latency budget | user turn + current shared memory $\to$ reply | block on the Reasoner; plan; call slow tools. The moment the Talker waits on System 2 the pattern degrades to R4 with extra steps. |
| **Reasoner (System 2)** | deep deliberation — multi-step planning, tool use, verification — running in the background | shared memory + (optionally) the triggering turn $\to$ updated plan / belief / recommendation written back to memory | speak to the user directly, hold the response path, or run on every turn. It runs when triggered and writes back when done. |
| **Shared Memory** | the single source of truth both sessions read and write | reads/writes from both $\to$ coherent state | be edited by ad-hoc tool outputs; only the two agents (and their explicit writers) touch it. Drift here breaks everything else. |
| **Trigger / Router** | deciding when to wake the Reasoner | Talker turn or memory event $\to$ spawn-Reasoner or not | wake the Reasoner on every turn (defeats the point) or never (defeats the point). The trigger heuristic is the main tuning lever. |
| **Sync Rule** *(policy, not a process)* | how Reasoner output reaches the user — fire-and-forget, interrupt, or pull | Reasoner result + UX context $\to$ delivery method | smuggle stale conclusions into the response; the sync rule must reject results that arrive after their context has expired. |

The Talker and Reasoner are kept as **distinct configured sessions**, even when the same model serves both — different roles, different setups, different tool budgets. Mixing them is the pattern's most common failure: a Talker that can also "think harder" stalls; a Reasoner that can also reply jumps the rails.

## Collaborations

A user turn arrives. The Talker reads the shared memory — including any conclusion the Reasoner finished since the last turn — and responds within its latency budget. In parallel, the Trigger inspects the turn (and the memory): if deliberation is warranted (a planning request, an unresolved sub-goal, a verification need), it spawns the Reasoner with a copy of the relevant state. The Reasoner runs — possibly for many seconds, possibly using tools — and writes its output (a plan, a recommendation, a corrected belief) back to shared memory. The next time the Talker runs, that conclusion is part of its context. The Sync Rule decides whether the Reasoner's result enters the stream as a follow-up message (interrupt), waits silently for the next user turn (fire-and-forget), or is queried explicitly before the Talker responds (pull). A session-level bound (V9) caps the Reasoner's total cost.

## Consequences

**Benefits**

- The user-facing latency is bounded by the Talker alone, regardless of how deep the Reasoner goes.
- Cost optimises naturally: a small fast model handles the conversational majority; the expensive Reasoner runs only when triggered.
- The two sessions are independently scalable, testable, and tunable.
- Maps cleanly onto inference-time reasoning models (o1, R1) — they slot in as the Reasoner with no behavioural change to the Talker.

**Costs**

- Two warm sessions cost more than one when both fire.
- Concurrency adds engineering complexity — locking, idempotency, write conflicts in shared memory.
- The Sync Rule is a UX problem with no universal answer; getting it wrong feels worse than a slower single agent.

**Risks and failure modes**

- *Stale conclusion injection* — the Reasoner finishes after the conversation has moved on, and its now-irrelevant advice enters the stream.
- *Trigger thrash* — a noisy trigger wakes the Reasoner on every turn; cost collapses while latency benefits stay.
- *Memory race* — Talker and Reasoner write the same slot concurrently and one overwrites the other.
- *Talker bypass* — the Talker, lacking a Reasoner answer, confidently makes one up rather than holding place; the Reasoner's eventual conclusion contradicts what the user was already told.
- *Drift between sessions* — Talker's setup and Reasoner's setup evolve independently and end up referring to different worlds.

## Implementation Notes

- Treat the Talker as a **single fast model** with a tight system prompt: it answers, it never plans, it never calls slow tools. Tool budget (V13) on the Talker should be minimal — short reads, no writes that depend on deliberation.
- Treat the Reasoner as the **strongest available model**, possibly an inference-time reasoning model (o1-class) — model size directly determines per-token compute cost (mechanism 8), and paying for a larger Reasoner is justified when it runs rarely.
- The Trigger can be a small classifier or a rule — *"if the user asks 'plan', 'should I', 'why', or mentions a goal, wake the Reasoner."* Measure and tune; it is the main lever.
- The Sync Rule is UX, not architecture. For chat, fire-and-forget (Reasoner's answer is folded into the next response) feels natural. For coaching / monitoring, an interrupt ("here's something I worked out…") can be appropriate. Pull is rare and forces the Talker to wait — defeats the point unless the question explicitly demands it.
- Shared memory channel: K8 Working Memory for in-session; K12 Karpathy Memory for persistent cross-session beliefs. Pick one before coding. The shared memory channel is necessary because the KV cache does not persist across API calls (mechanism 3) — neither session has memory of the last call unless it is re-injected as tokens. The Reasoner's conclusions written to K8/K12 are the only mechanism by which deliberation survives between turns. This is mechanism 10: all persistence is externalised file/store retrieval, not model state.
- Bound the Reasoner with V9 at the *session* level, not the turn level — the whole point is that no individual turn caps it.
- Log both streams (V14): Talker turns and Reasoner deliberations on a single timeline, otherwise debugging is impossible.
- Inference-time reasoning models (o1, o3, R1, DeepSeek-R1) effectively *are* the Reasoner with built-in System-2 capability; R16 is the natural deployment shape for them.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** R16 runs a *Talker* session and a *Reasoner* session concurrently against a shared memory store. It composes with **K8 Working Memory** (in-session shared state), **K12 Karpathy Memory** (cross-session shared beliefs), **V9 Bounded Execution** (cap Reasoner cumulative cost), **V14 Trajectory Logging** (unified timeline), and **O3 Routing** (the Trigger is a routing decision). The Reasoner itself often runs an inner reasoning pattern — **R3 Plan-and-Solve** or **R4 ReAct** — inside its window.

**The chain — per user turn:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Read shared memory (including any conclusions Reasoner posted since last turn) | `code` | K8 / K12 |
| 2 | Talker generates reply within latency budget | `LLM` | Talker session |
| 3 | Trigger inspects turn + memory: spawn Reasoner? | `code` (or small `LLM`) | O3 Routing |
| 4 | If yes: spawn Reasoner asynchronously (non-blocking) | `code` | |
| 5 | Return Talker reply to user | `code` | |

**The chain — background Reasoner job:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| R1 | Reasoner reads shared memory + triggering context | `code` | K8 / K12 |
| R2 | Reasoner deliberates: plan, multi-tool, verify | `LLM` | Reasoner session; R3 or R4 inside |
| R3 | Apply Sync Rule: write conclusion to memory; emit interrupt iff configured | `code` | |
| R4 | Check session-level bound (cost, deliberations/hour); halt if exceeded | `code` | V9 |

**Skeleton:**

```
on_user_turn(turn, memory):
    state = memory.read()                                  # code — K8/K12
    reply = Talker(turn, state)                            # LLM — fast, bounded
    if Trigger(turn, state):                               # code (or small LLM) — O3
        spawn_async(reason, turn, state)                   # code — non-blocking
    return reply                                           # code

reason(turn, state):                                       # background
    new_state = state.snapshot()
    conclusion = Reasoner(turn, new_state)                 # LLM — R3 or R4 inside
    memory.commit(conclusion, sync_rule)                   # code — fire-and-forget / interrupt / pull
    bound.check()                                          # code — V9 session cap
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Talker** | small fast generalist (latency-optimised; e.g. Haiku-class, GPT-4o-mini, Flash) | role (*"you are the user-facing voice; you respond promptly drawing on the shared memory; you never plan or call slow tools"*); response format (S6); rule for handling pending-deliberation states (*"if a plan is in progress, acknowledge without inventing"*); the shared-memory schema | the user turn + the current shared memory |
| **Reasoner** | strongest available model — often an inference-time reasoning model (o1, o3, R1) | role (*"you are the deliberative planner; you take time, use tools, verify"*); the planning / reasoning protocol (R3 or R4); the tool catalogue; the write-back schema (which memory slot, what shape) | the triggering turn + the memory snapshot |
| **Trigger** *(optional LLM, often a rule)* | small fast classifier or rules | role: decide if deliberation is warranted; output contract (SPAWN / SKIP); the criteria (goal-setting language, ambiguity, multi-step request, verification need) | the latest turn + a thin memory summary |

**Specialist-model note.** No fine-tuned specialist is *required*, but two structural choices change everything:

- The Talker and Reasoner **must be distinct configured sessions**, even if served by the same model. Mixing them collapses the pattern.
- A **reasoning-trained model** (o1, o3, R1, DeepSeek-R1, Claude with extended thinking) is the natural Reasoner; its built-in System-2 behaviour replaces an inner R3/R4 scaffold. Where one is available, R16 is the deployment shape that gets the most out of it — the Talker stays a cheap fast model, the Reasoner pays for thinking time only when triggered.

## Open-Source Implementations

Talker-Reasoner is an emerging architectural pattern, not a library. There is no single canonical project. The closest references are:

- **DPT-Agent** — [`github.com/sjtu-marl/DPT-Agent`](https://github.com/sjtu-marl/DPT-Agent) — official implementation of "Leveraging Dual Process Theory in Language Agent Framework for Real-time Simultaneous Human-AI Collaboration" (ACL 2025). System 1 = FSM + code-as-policy; System 2 = ToM + asynchronous reflection. The most rigorous dual-process agent implementation currently published.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — the state-machine + concurrent-nodes primitives are the natural substrate for a Talker-Reasoner graph; community recipes use it for fast/slow dual-agent topologies.
- **Letta** — [`github.com/letta-ai/letta`](https://github.com/letta-ai/letta) — when paired with a fast voice layer, Letta's curated memory blocks make a serviceable Reasoner + shared-memory channel for voice-agent stacks.
- **VAOS Voice Bridge** (community) — [`github.com/topics/talker-reasoner`](https://github.com/topics/talker-reasoner) — experimental voice-agent projects (e.g. `vaos-voice-bridge`, `super-safe-superintelligence`) tagged `talker-reasoner` that wire a fast voice model to a slower reasoning backbone. Reference-quality, not production libraries.

If your stack already has an inference-time reasoning model (o1, o3, R1) and a concurrent-execution layer, that combination *is* R16 — you do not need a framework.

## Known Uses

- **Voice agents and conversational assistants** that pair a fast voice/chat front-end with a reasoning back-end (the architecture Christakopoulou et al. demonstrated on a sleep-coaching agent).
- **Coding assistants with extended thinking** — Claude Code, Cursor and similar surface a fast Talker for chat-style interaction and route deliberative requests to a reasoning model in the background.
- **Real-time human-AI collaboration in games and simulations** — DPT-Agent's Overcooked benchmarks demonstrate the dual-process split in a hard real-time environment.
- **Production stacks deploying o1/o3/R1-class models** — the Reasoner role is the natural slot for an inference-time reasoning model behind a fast Talker.

## Related Patterns

- **Sibling of** H6 Continuous Inner Monologue — both are dual-process / continuous-reasoning architectures inspired by the same cognitive-science framing. H6 keeps a persistent asynchronous *thought stream* within one agent; R16 splits the agent into two sessions with different roles, different models, and different latency budgets. The structural participants — Talker, Reasoner, shared memory, sync rule — distinguish R16.
- **Distinct from** R3 Plan-and-Solve and R4 ReAct — both serialise reasoning onto the response path. R16 parallelises it.
- **Composes with** K8 Working Memory — the natural in-session shared channel between Talker and Reasoner.
- **Composes with** K12 Karpathy Memory — for cross-session beliefs and plans that persist across conversations.
- **Composes with** O3 Routing — the Trigger is a routing decision (spawn Reasoner or not).
- **Pairs with** V9 Bounded Execution — session-level cap on Reasoner cost; without it deliberation can run unbounded.
- **Pairs with** V14 Trajectory Logging — a unified timeline of Talker turns and Reasoner deliberations is essential to debug the concurrency.
- **Uses inside the Reasoner** R3 Plan-and-Solve, R4 ReAct, or R7 Reflexion — the Reasoner is an inner reasoning pattern; R16 is the architecture that runs it concurrently with a fast Talker.
- **Natural deployment shape for** inference-time reasoning models (o1, o3, R1) — they slot in as the Reasoner without architectural change.

## Sources

- Christakopoulou, K., Mourad, S., & Matarić, M. (2024) — "Agents Thinking Fast and Slow: A Talker-Reasoner Architecture" (arXiv 2410.08328). Google DeepMind. Primary source; direct Kahneman dual-process mapping; sleep-coaching agent case study.
- Kahneman, D. (2011) — *Thinking, Fast and Slow*. The cognitive-science source the architecture maps onto.
- He et al. (2025) — "Leveraging Dual Process Theory in Language Agent Framework for Real-time Simultaneous Human-AI Collaboration" (arXiv 2502.11882, ACL 2025). DPT-Agent paper; rigorous instantiation in a real-time benchmark.
- SAP — "AI Agents: Thinking Fast, Thinking Slow" (industry framing of the pattern).
- The "Something-of-Thought" reasoning family (R1–R14) — patterns the Reasoner can run *inside* its own session.
