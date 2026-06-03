# Category III — Reasoning Patterns

A **Reasoning pattern** is a design pattern that governs *how the model processes its context to produce a structured answer* — how it decomposes the problem, what intermediate work it writes down, whether it branches or backtracks, whether it calls tools, and how it checks itself before committing. Reasoning patterns separate *the shape of thought* from the content the model is reasoning over.

## Usage

A language model that answers in one forward pass commits to the first plausible completion it can find. For arithmetic, multi-hop questions, planning, tool use, and any task with a non-obvious solution path, that is precisely where it fails: the answer is fluent, the reasoning behind it is invented after the fact, and there is no internal step at which the model could have caught its own mistake. Reasoning patterns intervene on the *process* — they prescribe what the model writes between the question and its final answer, and what it does with those intermediate writings.

The shift Reasoning patterns embody is from *one-shot generation* to *structured deliberation*. The category covers everything from the smallest such intervention — appending *"Let's think step by step"* — to the most elaborate: Monte Carlo Tree Search over an agent's own action trajectories. Apply a Reasoning pattern whenever:

- the task requires multi-step inference the model will not produce by default;
- the answer must be auditable as well as correct (intermediate steps inspectable);
- the model must interact with the world via tools and adapt to what it observes;
- one-shot generation is empirically unreliable on the task and quality matters more than the saved tokens.

## Forces

Every Reasoning pattern resolves three forces in tension. A pattern fits a situation when it balances them in the way that situation demands.

1. **Tokens are not free, and reasoning is tokens.** Every intermediate step the model writes, every retry, every branch in a tree of thoughts, every verification pass — all of them are tokens billed and latency added. Cost rises at least linearly in call count, and quadratically in attention cost per call as context accumulates (mechanism 2 — O(seq_len²) attention). For looping patterns (ReAct, Reflexion, Self-Refine, Tree-of-Thoughts), each step appends to the accumulated context, so each subsequent LLM call attends over a longer prefix at growing quadratic cost — making the true cost super-linear, not linear, with deliberation depth.

2. **One-shot answers are confident but unreliable.** Left to itself, the model commits to its first plausible completion. On compositional, numerical, multi-hop, or tool-mediated tasks, that completion is wrong often enough that an intervention is required — and the intervention has to be *structural*, because the model cannot self-detect its own failure mode without being asked to.

3. **Adaptability and efficiency trade off directly.** A pattern that decides every next step in light of the previous observation (ReAct) is maximally adaptive but expensive. A pattern that plans everything upfront and executes blind (ReWOO) is cheap but cannot react. Every Reasoning pattern picks a point on this spectrum, explicitly. The mechanistic basis of this trade-off: ReAct's accumulated trajectory context grows with each step, paying O(n²) attention cost (mechanism 2) on every subsequent LLM call; ReWOO's Worker phase is deterministic code execution (mechanism 7) — no LLM calls, no stochastic variance, no KV-cache growth. The adaptability/efficiency spectrum maps directly onto the question of how much in-context stochastic generation versus deterministic computation is on the critical path.

A Reasoning pattern is, in each case, a disciplined answer to one question: what structure of deliberation gives this task the quality it needs at a cost the system can afford?

## Structure

All Reasoning patterns share one skeleton. They interpose a **deliberation stage** between the question and the answer:

```
  Question ────▶ Deliberation ────▶ Answer
                 (decompose,
                  search,
                  tool-use,
                  verify,
                  iterate)
```

Patterns differ in *what the deliberation does* — write a linear chain, branch into a tree, alternate thought and tool call, plan-then-execute, draft-then-verify, retry-with-critique — and in *where the intermediate work lives* — in the prompt itself, across multiple LLM calls, in a sandboxed interpreter, or in an external memory carried across attempts. These four locations correspond to distinct storage tiers with different cost profiles (mechanism 9): in-context storage pays O(n²) attention cost on every call; prefix caching across calls (mechanism 5) pays a one-time write cost then reads at ~10% of normal token cost within a TTL window; external execution environments (deterministic interpreters, tool sandboxes) store intermediate values at near-zero LLM cost (mechanism 7); external stores (vector indices, key-value stores) pay retrieval cost but no attention cost per token (mechanism 10). Choosing where deliberation lives is a cost-architecture decision, not just a structural one. The sub-bands below group patterns by the shape of the deliberation they prescribe.

## Examples

**III-A — Chain-of-Thought family.** Linear, in-context reasoning traces.
- **R1 Zero-Shot CoT** — append a trigger phrase; let the model write the chain.
- **R2 Few-Shot CoT** — supply worked examples with reasoning steps.
- **R19 Step-Back Prompting** — abstract the question first, derive the principle, then specialise back.

**III-B — Plan-and-Act.** Separate planning from execution.
- **R3 Plan-and-Solve** — produce an inspectable plan upfront, then execute it.
- **R5 ReWOO** — plan every tool call with placeholders, execute without an LLM in the loop, synthesise once.

**III-C — Tool-Use loops.** Interleave reasoning with actions against the world.
- **R4 ReAct** — Thought $\to$ Action $\to$ Observation, repeat; each next step conditioned on what came back.
- **R13 CodeAct** — emit executable Python as the action language, with stdout / errors returning as the Observation.
- **R14 Program of Thoughts** — delegate the *computation* (not the orchestration) to a deterministic interpreter.

**III-D — Decomposition.** Break the question apart before answering it.
- **R6 Self-Ask** — explicit follow-up sub-questions, each answered, then composed.
- **R12 Skeleton-of-Thought** — outline first, then expand each outline point in parallel.

**III-E — Search.** Explore a space of partial solutions rather than committing to one path.
- **R9 Tree of Thoughts** — branching search with LLM-evaluated nodes and backtracking.
- **R10 LATS** — Monte Carlo Tree Search unifying ReAct, ToT, and Reflexion under UCB selection.
- **R18 Graph of Thoughts** — directed graph of thoughts with *aggregate* edges that merge branches no tree can.
- **R11 Buffer of Thoughts** — retrieve a thought-template from past problems instead of re-searching.

**III-F — Reflection and Verification.** Generate, then check or improve.
- **R7 Reflexion** — verbal critique of a failed attempt carried into the retry.
- **R8 Self-Refine** — generate, self-critique, revise, loop — single model, no external signal.
- **R17 Self-Consistency Voting** — sample N independent reasoning paths and take the majority.
- **R20 Chain-of-Verification** — draft, generate verification questions, answer them independently, revise.

**III-G — Multi-Mode.** Run two distinct reasoning modes side by side.
- **R16 Talker-Reasoner** — a fast conversational Talker and a slow deliberative Reasoner running concurrently against a shared memory.

## See also

- **Category I — Signal patterns** — shape *what you say* to the model; Reasoning shapes *what it does next*.
- **Category II — Knowledge patterns** — assemble the context Reasoning patterns then operate on; **K8 Working Memory** is the in-context scratchpad most Reasoning patterns write into.
- **Category IV — Orchestration patterns** — Reasoning patterns govern one agent's thinking; Orchestration governs how multiple agents and workflows compose. **O5 Evaluator-Optimizer** is the multi-agent counterpart of **R8 Self-Refine**.
- **Category V — Reliability patterns** — **V9 Bounded Execution** caps the loop in every iterative Reasoning pattern; **V15 LLM-as-Judge** is the external evaluator that **R7 Reflexion** depends on; **V14 Trajectory Logging** captures the deliberation trace.
- **Category VII — Humanizer patterns** — **H6 Continuous Inner Monologue** carries a persistent background reasoning substrate; **R16 Talker-Reasoner** is the structured deliberation architecture that consumes it.

---

## Quick Reference

| # | Pattern | Also Known As | LLM Calls | Best For |
|---|---|---|---|---|
| R1 | **Zero-Shot CoT** | "Think step by step" | 1 | Quick reasoning improvement; no examples |
| R2 | **Few-Shot CoT** | Exemplar CoT | 1 | Consistent reasoning format with examples |
| R3 | **Plan-and-Solve** | Explicit Planning | 2 | Well-defined multi-step workflows |
| R4 | **ReAct** | Reason+Act Loop | N per step | Exploratory; adaptive; unpredictable paths |
| R5 | **ReWOO** | Reasoning Without Observation | 2 total | Independent tool calls; 5$\times$ cheaper than R4 |
| R6 | **Self-Ask** | Decomposition | 1 + N follow-ups | Multi-hop factual questions |
| R7 | **Reflexion** | Verbal Reinforcement | N $\times$ retries | Clear pass/fail criteria; retries acceptable |
| R8 | **Self-Refine** | Generate-Critique-Refine | N iterations | General quality improvement; no separate judge |
| R9 | **Tree of Thoughts** | ToT | N (branching) | Hard open-ended; path unknown |
| R10 | **LATS** | Language Agent Tree Search | N (tree search) | Highest quality; highest cost |
| R11 | **Buffer of Thoughts** | BoT | 1 + template | 12% cost of ToT; reusable templates |
| R12 | **Skeleton-of-Thought** | SoT | 1 + N parallel | Parallel generation; latency reduction |
| R13 | **CodeAct** | Executable Code Actions | N (with execution) | Multi-tool; ~20pp accuracy gain over JSON |
| R14 | **Program of Thoughts** | PoT | 1 + execution | Numerical/mathematical tasks |
| R16 | **Talker-Reasoner** | System 1/System 2 | Dual async | Real-time + deliberative combined |
| R17 | **Self-Consistency** | Majority Voting | N samples | Factual tasks; sample and vote |
| R18 | **Graph of Thoughts** | GoT | N (DAG) | Non-linear reasoning; merging thought branches |
| R19 | **Step-Back Prompting** | Abstraction Prompting | 2 | Abstract to principle before answering |
| R20 | **Chain of Verification** | CoVe | 1 + N verifications | Reduce hallucination; verify each claim |

---

## R1 — Zero-Shot CoT

Append a short reasoning-elicitation trigger (canonically *"Let's think step by step"*) to a zero-shot prompt and let the model write its reasoning out before the final answer — no examples, no decomposition, no scaffold.

**Full entry:** [`R1-Zero-Shot-CoT.md`](R1-Zero-Shot-CoT.md)

---

## R2 — Few-Shot CoT

Put `k` worked examples in the prompt — each one a complete question with its reasoning steps leading to the answer — so the model learns from the demonstrations both how to reason about the task and what the answer should look like.

**Full entry:** [`R2-Few-Shot-CoT.md`](R2-Few-Shot-CoT.md)

---

## R3 — Plan-and-Solve

Split reasoning into two distinct LLM calls — first a *Plan* call that produces an explicit, inspectable step list from the full task in view, then an *Execute* call (or chain) that carries the plan out — so plan quality and execution efficiency are tuned independently.

**Full entry:** [`R3-Plan-and-Solve.md`](R3-Plan-and-Solve.md)

---

## R4 — ReAct

Interleave a free-text *Thought*, a structured *Action* (tool call), and the returning *Observation* in a single loop, so each next reasoning step is conditioned on what the previous action actually returned rather than on a plan made before the world was seen.

**Full entry:** [`R4-ReAct.md`](R4-ReAct.md)

---

## R5 — ReWOO

Plan every tool call upfront in a single LLM pass, execute the plan without any LLM in the loop, then synthesise the answer from the collected evidence — trading mid-run adaptability for roughly 5$\times$ token efficiency over R4.

**Full entry:** [`R5-ReWOO.md`](R5-ReWOO.md)

---

## R6 — Self-Ask

Decompose a compositional question into explicit follow-up sub-questions, answer each one (optionally via a tool or retriever), then compose the final answer from the intermediate answers.

**Full entry:** [`R6-Self-Ask.md`](R6-Self-Ask.md)

---

## R7 — Reflexion

Retry a failed task with a verbal critique of the previous attempt in context — converting an automated pass/fail signal into linguistic feedback that the next attempt can read and act on.

**Full entry:** [`R7-Reflexion.md`](R7-Reflexion.md)

---

## R8 — Self-Refine

Have one model generate an output, critique its own output, and revise it from that critique — looping until a stopping condition fires, with no external feedback signal and no second model.

**Full entry:** [`R8-Self-Refine.md`](R8-Self-Refine.md)

---

## R9 — Tree of Thoughts

Search a tree of partial-solution states by having the LLM generate candidate next thoughts, evaluate the promise of each, and explore the most promising branches with backtracking — turning one-shot reasoning into deliberate exploration of a solution space.

**Full entry:** [`R9-Tree-of-Thoughts.md`](R9-Tree-of-Thoughts.md)

---

## R10 — Language Agent Tree Search (LATS)

Run Monte Carlo Tree Search over an agent's reasoning trajectories: select promising branches by UCB, expand with LLM-proposed actions, evaluate with an LLM value function, simulate forward, and backpropagate value through the tree — so the agent searches the solution space the way AlphaGo searches a board. Unifies R4, R7, and R9 under MCTS.

**Full entry:** [`R10-LATS.md`](R10-LATS.md)

---

## R11 — Buffer of Thoughts

Maintain a meta-buffer of reusable high-level *thought-templates* distilled from past problems, and for each new problem retrieve the most relevant template and instantiate it — trading expensive per-problem search for amortised reuse of reasoning structure.

**Full entry:** [`R11-Buffer-of-Thoughts.md`](R11-Buffer-of-Thoughts.md)

---

## R12 — Skeleton-of-Thought

Generate an outline of the answer in one call, then expand each outline point in parallel, then aggregate — turning a sequentially-decoded long-form response into a fan-out / fan-in inside a single agent's thinking.

**Full entry:** [`R12-Skeleton-of-Thought.md`](R12-Skeleton-of-Thought.md)

---

## R13 — CodeAct

Have the agent emit *executable Python code* as its action — calling tools, composing them with control flow, and parking intermediate values in variables — instead of emitting a single structured JSON tool call per step, with the code running in a sandbox and its stdout / errors returning as the Observation.

**Full entry:** [`R13-CodeAct.md`](R13-CodeAct.md)

---

## R14 — Program of Thoughts

Generate a self-contained program that computes the answer, run it in a deterministic interpreter, return the interpreter's output — delegating numerical and symbolic work out of the model's tokens and into code. Distinct from R13: PoT offloads *computation*, CodeAct offloads *orchestration*.

**Full entry:** [`R14-Program-of-Thoughts.md`](R14-Program-of-Thoughts.md)

---

*R15 — Inner Monologue: intentional gap. The MIRROR paper (arXiv:2506.00430) proposed inner monologue as a background reasoning substrate. After review, this was classified as a Humanizer concern — it describes how an agent maintains continuous inner speech across turns and sessions, not a reasoning technique applied within a single turn. Documented as **H6 Continuous Inner Monologue** (Humanizers category). R15 is reserved and will not be reused.*

---

## R16 — Talker-Reasoner

Split the agent into a fast, conversational Talker that handles every user turn in real time and a slow, deliberative Reasoner that thinks in the background and injects conclusions when ready — two cognitive speeds running concurrently against a shared memory.

**Full entry:** [`R16-Talker-Reasoner.md`](R16-Talker-Reasoner.md)

---

## R17 — Self-Consistency Voting

Run the same prompt N times with diversity-inducing sampling, then select the answer by majority vote — marginalising over independent reasoning paths instead of trusting any single one.

**Full entry:** [`R17-Self-Consistency-Voting.md`](R17-Self-Consistency-Voting.md) — *was a Signal pattern (former S7); relocated here because the mechanism is sampling diverse reasoning paths, not shaping the prompt.*

---

## R18 — Graph of Thoughts

Represent reasoning as a directed graph whose vertices are LLM-generated thoughts and whose edges are *generate*, *refine*, and — uniquely — *aggregate* operations, so partial results from different branches can be merged into a single composite thought that no tree-shaped search can produce.

**Full entry:** [`R18-Graph-of-Thoughts.md`](R18-Graph-of-Thoughts.md)

---

## R19 — Step-Back Prompting

Before answering a specific question, ask a more abstract version of it, derive the underlying principle or concept, and then specialise that principle back to the original — so reasoning starts from a level the model handles more reliably than the specific case.

**Full entry:** [`R19-Step-Back-Prompting.md`](R19-Step-Back-Prompting.md) — *the Step-Back-as-retrieval-key move is the Step-Back variant of K2 Query Transformation; same abstraction applied at a different layer.*

---

## R20 — Chain-of-Verification

Have a model draft an answer, generate verification questions targeted at its own factual claims, answer each question independently so the answers do not lean on the draft, and revise the draft from those answers — turning hallucination into a thing the model checks against itself.

**Full entry:** [`R20-Chain-of-Verification.md`](R20-Chain-of-Verification.md)
