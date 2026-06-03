# Category IV — Orchestration Patterns

An **Orchestration pattern** is a design pattern for *coordinating* multiple inferences, agents, and tools — chains, routers, parallel fan-outs, hierarchies, ensembles, and shared substrates — so that what no single LLM call can do well, a structured arrangement of calls can.

## Usage

A single LLM call has a fixed window, a fixed tool budget, and a single reasoning trace. Many real tasks exceed all three: too much input to fit, too many tools to wield reliably, too many sub-problems to resolve in one pass without entanglement. The response is not to make one agent larger but to compose several smaller ones — each focused, each testable — into a system whose behaviour is the *interaction*.

Orchestration patterns specify those interactions. They name the canonical shapes — pipeline, router, fan-out, supervisor/worker tree, debate, blackboard — and the discipline each shape requires (when steps must be fixed vs dynamic, where state is owned, how termination is bounded). This is the systems-design layer of GO4: Category III governs what happens *inside* one agent's head; Category IV governs how multiple heads add up to a working system. Apply an Orchestration pattern whenever:

- the task exceeds one agent's reliable context or tool count;
- distinct sub-tasks benefit from specialised prompts, models, or roles;
- independent sub-tasks could run in parallel and shorten wall-clock time;
- output quality requires an evaluator that did not write the output;
- state must be shared, handed off, or isolated across multiple inferences.

## Forces

Every Orchestration pattern resolves the same four forces in tension. A pattern is the right choice for a situation when it balances them as that situation demands.

1. **Decomposition is bought, not free.** Every additional agent boundary adds latency, cost, hand-off surface, and a new place errors can hide. The cheapest correct system has the *fewest* coordinated parts — but not fewer. Mechanically: the KV cache does not persist across API calls (mechanism 3) — each new agent session pays full prefill. If prefix caching (mechanism 5) were perfect and free, the latency cost of decomposition would fall sharply; in practice, prefix caching amortises the stable-setup portion but not the task-specific portion of each agent's context.

2. **Determinism trades against adaptivity.** Fixed pipelines are cheap, predictable, and testable but cannot react to surprise. Dynamic delegation adapts but pays in unpredictable cost and harder debugging. Each pattern picks a point on this axis.

3. **Independence is a claim about state, not a property of agents.** Parallel only beats sequential when sub-tasks truly do not share state or ordering. Misjudging independence is the most common source of subtle multi-agent bugs. At the mechanical level, "independence" means the sub-tasks' required context is disjoint. When two sub-tasks share context (e.g. both need the same retrieved document), running them in isolated contexts (O17) means each pays the shared content's prefill independently. This is the tension between context isolation (mechanism 6 benefit: bounded n² per agent) and shared-prefix caching (mechanism 5 benefit: amortised prefill for common content): isolation is optimal for attention quality; shared prefix caching is optimal for cost. The right answer is to make the shared content a stable cacheable prefix and partition only the task-specific content.

4. **Coordination needs boundedness.** Any loop, retry, debate, or hierarchy can run forever absent an explicit termination condition. Reliability patterns — V9 Bounded Execution, V14 Trajectory Logging — are not optional companions; they are co-required.

An Orchestration pattern is, in each case, a disciplined answer to one question: how to combine multiple inferences into a system that is more capable than any single one *without* paying so much in coordination overhead that the gain is lost.

## Structure

All Orchestration patterns share one skeleton. They interpose a **coordination layer** between a task and one or more LLM inferences:

```
  Task ────▶ Coordination ────▶ Inference(s) ────▶ Aggregation ────▶ Result
            (sequence,         (one or many       (combine,
             route,             agents, each       gate,
             fan-out,           with its own       hand-off,
             delegate,          context and        synthesise)
             share)             tools)
```

Patterns differ in *how the coordination layer is shaped* — fixed pipeline, classifier, parallel fan-out, dynamic delegator, hierarchical tree, peer mesh, shared blackboard — and in *what the aggregation does* — concatenate, vote, judge, synthesise, hand off. The three bands below group the patterns by the kind of coordination they impose: deterministic workflows (IV-A), dynamic agentic structures (IV-B), and specialised coordination mechanisms (IV-C). Production systems typically instantiate one pattern from IV-A or IV-B as the spine, and one or more IV-C patterns as supporting structure.

## Examples

**IV-A — Workflow patterns.** Deterministic, testable, lower complexity.
- **O1 Single Agent** — one LLM with tools handles the whole task; the baseline before any multi-agent move.
- **O2 Prompt Chaining** — a fixed sequence of LLM calls, each step's output the next step's input.
- **O3 Routing** — classify the input, dispatch to the specialised handler for that class.
- **O4 Parallelization** — run independent sub-tasks simultaneously and aggregate; sectioning and voting variants.

**IV-B — Agentic patterns.** Dynamic, higher complexity, looped or delegated.
- **O5 Evaluator-Optimizer** — separate generator and evaluator agents; iterate until the evaluator passes.
- **O6 Orchestrator-Workers** — a central orchestrator decomposes a goal at runtime and delegates to workers.
- **O7 Supervisor Hierarchy** — O6 applied recursively; a tree of supervisors each managing bounded scope.
- **O8 Loop Agent** — a sequence of sub-agents repeats until a termination condition fires.
- **O9 Multi-Agent Reflection** — several critics, each with a distinct lens, critique one output in parallel.
- **O10 Swarm / Mesh** — peer agents coordinate without a central hub; emergent rather than directed.

**IV-C — Specialised coordination.** Mechanisms that supplement a spine pattern.
- **O11 Blackboard System** — a shared memory all agents read and write; a control unit activates whichever agent fits the current state.
- **O12 Debate / Deliberation** — agents argue opposing positions; a synthesis step produces the considered conclusion.
- **O13 Negotiation** — agents representing competing objectives negotiate to a mutually acceptable outcome.
- **O14 Single Information Environment** — data-centric: each agent owns a dataset; the coordinator routes by data domain.
- **O15 Agent Handoff** — structured transfer of context between agents mid-task so continuity is preserved.
- **O16 Hybrid Control Flow** — stack multiple loop primitives (ReAct + plan-execute + retry + tree search) within one scaffold; the empirically observed production reality.
- **O17 Agent Isolation** — delegate a sub-task to a fresh, minimal context; the orchestration-side of context hygiene.

## See also

- **Category I — Signal patterns** — shape what each individual agent in an orchestration is told.
- **Category II — Knowledge patterns** — supply each agent with the right information; O17 Agent Isolation was formerly K13 here.
- **Category III — Reasoning patterns** — govern what happens *inside* one agent (ReAct, Plan-and-Solve, Reflexion); Orchestration governs how multiple such agents combine.
- **Category V — Reliability patterns** — V9 Bounded Execution is required by every loop or delegation; V14 Trajectory Logging by every multi-agent system; V15 LLM-as-Judge is the inference inside O5 and O9.
- **Category VI — Integration patterns** — I5 Agent Card and I6 A2A Delegation are the wire format multi-vendor orchestrations run over.

*The production composition law: most real systems are **O6 + O4 + R4-inside-workers + O17 for context isolation**, with V9 / V14 as required companions. This law is mechanically derived: (a) n² attention cost requires bounded contexts per agent (mechanisms 2, 6); (b) no KV persistence across API calls means each agent pays its own prefill (mechanism 3); (c) parallel execution is safe only when sub-tasks are genuinely independent — when the same token generation process (mechanism 7) applied to the same context would produce the same answer, parallelism adds no information. O17 is mechanically necessary for the O6 quality win, not merely a nice-to-have: if workers inherit the orchestrator's context, the context-bounding benefit (mechanism 6) is defeated.*

---

## Quick Reference

### IV-A — Workflow Patterns

| # | Pattern | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O1 | **Single Agent** | Autonomous Agent | One LLM + tools + system prompt | Low |
| O2 | **Prompt Chaining** | Pipeline | Output of one call feeds the next in fixed order | Low |
| O3 | **Routing** | Classifier-Dispatcher | Classify input $\to$ specialist handler | Medium |
| O4 | **Parallelization** | Fan-out Fan-in | Simultaneous independent LLM calls | Medium |

### IV-B — Agentic Patterns

| # | Pattern | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O5 | **Evaluator-Optimizer** | Generator-Critic | Separate generator and judge; iterative improvement | Medium |
| O6 | **Orchestrator-Workers** | Hub-and-Spoke | Central LLM dynamically delegates to workers | High |
| O7 | **Supervisor Hierarchy** | Hierarchical Agents | Multi-level tree of orchestrators | High |
| O8 | **Loop Agent** | Agentic Loop | Sequence repeats until termination condition | Medium |
| O9 | **Multi-Agent Reflection** | Ensemble Critique | Multiple agents independently critique one output | High |
| O10 | **Swarm** | Peer-to-Peer Agents | No central coordinator; emergent coordination | Very High |

### IV-C — Specialised Coordination

| # | Pattern | Also Known As | Intent | Complexity |
|---|---|---|---|---|
| O11 | **Blackboard** | Shared Workspace | Central shared memory; agents post and consume | High |
| O12 | **Debate and Deliberation** | Devil's Advocate | Agents argue opposing positions before synthesis | High |
| O13 | **Negotiation** | Multi-Party Consensus | Agents with conflicting objectives negotiate | Very High |
| O14 | **SIE** | Single Information Environment | Agents own specific datasets; coordinator routes | Medium |
| O15 | **Agent Handoff** | Context Transfer | Structured state transfer mid-task | Medium |
| O16 | **Hybrid Control Flow** | Primitive Stack | Stacked loop primitives; most real agents | Varies |
| O17 | **Agent Isolation** | Clean Context | Fresh context per sub-task — required companion to O6 | Low overhead |
| O18 | **Cache-Warmed Worker Pool** | Primed Agent Pool | Shared prefix cached before worker fan-out | Low overhead |

---

## Scaffold Architecture Dimensions

*From empirical study of 13 coding agents (arXiv 2604.03515).*

**Five stackable loop primitives:**
1. ReAct loop
2. Generate-test-repair
3. Plan-execute
4. Multi-attempt retry
5. Tree search (MCTS)

Most production agents (11/13 studied) use O16 — multiple primitives stacked, not a single pattern.

**The major architectural fault line:**

- **LLM-as-navigator** (8/13 agents): general tools; LLM decides navigation; simpler but less precise
- **Scaffold-understands-code** (5/13 agents): repository maps, AST indexing, knowledge graphs; more powerful but complex

**Active research frontier (no consensus):** context compaction strategy, state representation format, safety mechanisms for interactive agents.

---

## O1 — Single Agent

One LLM with a defined tool set and system prompt autonomously handles the complete request, using its own reasoning loop to plan, act, and respond. The baseline that any multi-agent move must out-perform.

**Full entry:** [`O1-Single-Agent.md`](O1-Single-Agent.md)

---

## O2 — Prompt Chaining

Structure a task as a fixed sequence of LLM calls, with programmatic logic and validation gates between steps; the output of each step is the input of the next.

**Full entry:** [`O2-Prompt-Chaining.md`](O2-Prompt-Chaining.md)

---

## O3 — Routing

Classify the incoming input and dispatch it to the specialised downstream handler — prompt, agent, or pipeline — best suited to that class. The classifier may be an LLM, an embedding similarity check, or a rule.

**Full entry:** [`O3-Routing.md`](O3-Routing.md)

---

## O4 — Parallelization

Run multiple LLM calls simultaneously for sub-tasks judged independent, then aggregate. *Sectioning* (different chunks of one task) and *voting* (same prompt N times for consensus) are the two sub-variants.

**Full entry:** [`O4-Parallelization.md`](O4-Parallelization.md)

---

## O5 — Evaluator-Optimizer

One agent generates output; a separate, independent agent evaluates against criteria; the generator revises on the evaluator's feedback; iterate until a quality threshold is met. The production-grade counterpart to R8 Self-Refine.

**Full entry:** [`O5-Evaluator-Optimizer.md`](O5-Evaluator-Optimizer.md)

---

## O6 — Orchestrator-Workers

A central orchestrator LLM decomposes a goal at runtime, delegates sub-tasks to specialised worker LLMs, and synthesises the results. The dynamic counterpart to O2 Prompt Chaining: use when the sequence cannot be enumerated at design time.

**Full entry:** [`O6-Orchestrator-Workers.md`](O6-Orchestrator-Workers.md)

---

## O7 — Supervisor Hierarchy

Extend O6 into a multi-level tree: a root supervisor delegates to sub-supervisors, which delegate to worker agents. Each node manages only its direct children, keeping every orchestrator's cognitive load bounded.

**Full entry:** [`O7-Supervisor-Hierarchy.md`](O7-Supervisor-Hierarchy.md)

---

## O8 — Loop Agent

Run a sequence of sub-agents repeatedly until a termination condition is met — either success criteria are satisfied or a bounded iteration limit is reached. Always paired with V9 Bounded Execution.

**Full entry:** [`O8-Loop-Agent.md`](O8-Loop-Agent.md)

---

## O9 — Multi-Agent Reflection

Multiple critic agents, each with a distinct lens (security, performance, accuracy, style), independently critique the same output; a synthesis step combines their critiques. The ensemble counterpart to R8 Self-Refine and O5.

**Full entry:** [`O9-Multi-Agent-Reflection.md`](O9-Multi-Agent-Reflection.md)

---

## O10 — Swarm / Mesh

Multiple peer agents coordinate without a central orchestrator, emergently distributing work via local state and peer messages. Experimental: most production systems claiming O10 in fact degrade to O7.

**Full entry:** [`O10-Swarm.md`](O10-Swarm.md)

---

## O11 — Blackboard System

Maintain a central shared memory all agents read and write; a control unit activates whichever agent is most relevant to the current blackboard state. The classical (Hayes-Roth) coordination structure, now applied to LLM agents.

**Full entry:** [`O11-Blackboard.md`](O11-Blackboard.md)

---

## O12 — Debate / Deliberation

Multiple agents argue opposing or divergent positions on the same question; a synthesis agent (or human) evaluates the debate and produces the considered conclusion. Improves factuality where consensus may be wrong.

**Full entry:** [`O12-Debate-Deliberation.md`](O12-Debate-Deliberation.md)

---

## O13 — Negotiation

Agents representing different stakeholders or objectives negotiate to a mutually acceptable outcome, mediated by explicit negotiation protocols. Emerging; limited production deployment to date.

**Full entry:** [`O13-Negotiation.md`](O13-Negotiation.md)

---

## O14 — Single Information Environment

Each agent specialises in, and owns, a specific dataset or data domain; a coordinator routes queries to the agent whose data domain matches. The data-centric counterpart to O3 Routing.

**Full entry:** [`O14-SIE.md`](O14-SIE.md)

---

## O15 — Agent Handoff

Transfer control of an in-progress interaction from one agent to another with a structured context package — intent, entities, prior actions, trace ID — so the receiving agent continues coherently and the user does not repeat themselves.

**Full entry:** [`O15-Agent-Handoff.md`](O15-Agent-Handoff.md)

---

## O16 — Hybrid Control Flow

Combine multiple loop primitives (ReAct, plan-execute, generate-test-repair, multi-attempt retry, tree search) inside one scaffold so each primitive handles the sub-problem it fits best. The empirically dominant production shape: 11 of 13 coding agents in the scaffold-taxonomy study use stacked primitives, not a single one.

**Full entry:** [`O16-Hybrid-Control-Flow.md`](O16-Hybrid-Control-Flow.md)

---

## O17 — Agent Isolation

Delegate a sub-task to a new agent invocation with a fresh, isolated context window containing only the information that sub-task needs. The orchestration-side mechanism behind context hygiene.

**Full entry:** [`O17-Agent-Isolation.md`](O17-Agent-Isolation.md)
