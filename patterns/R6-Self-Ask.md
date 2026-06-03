# R6 — Self-Ask

> Decompose a compositional question into explicit follow-up sub-questions, answer each one (optionally via a tool or retriever), then compose the final answer from the intermediate answers.

**Also Known As:** Follow-Up Question Decomposition, Compositional Decomposition, Self-Ask Prompting. (Self-Ask-with-Search noted in Variants.)

**Classification:** Category III — Reasoning · Band III-A Linear chains · the *question-decomposition* pattern — sibling of R1/R2 CoT (unstructured chain) and R3 Plan-and-Solve (action plan); R6 is structured by sub-questions rather than by reasoning steps or action steps.

---

## Intent

Close the *compositionality gap* — the failure mode in which a model can answer each sub-fact of a multi-hop question individually but cannot combine them — by forcing the model to ask and answer its own follow-up questions before composing the final answer.

## Motivation

Press et al. (2022) named and measured a specific failure: models that know fact A *and* know fact B nonetheless get the question "A combined with B" wrong. They called the ratio of (can solve all sub-problems) to (can solve the whole) the **compositionality gap**, and found it does *not* close as model scale grows — bigger models retrieve facts better but do not compose them better. Scale alone does not fix this.

Why not? Because a single greedy decode of a compositional question commits to producing the final answer in one shot. The compositionality gap is a consequence of autoregressive stochastic sampling (mechanism 7): each token is sampled forward-only; once the answer token is committed, the model cannot revise it even if later reasoning steps contradict it. Naming the sub-questions before answering them forces the answer token to be deferred until all conditioning context is present. The model never explicitly *names* the sub-facts it needs; it tries to weave them into the answer in one pass, and any missed hop becomes a fluent-sounding hallucination. Chain-of-Thought (R1, R2) helps because emitting reasoning tokens creates room to surface intermediate facts — but CoT is unstructured prose, and the model can still skip the hop, restate the question, or rationalise the wrong answer.

Self-Ask's contribution is **structural**: it imposes a rigid Q/A scaffold — `Follow up: …` / `Intermediate answer: …` — that the model fills in turn by turn before emitting `So the final answer is: …`. The structure forces the decomposition to be *named* and *checkable*, and turns each sub-question into a clean point where an external tool (search, retriever, calculator) can substitute for the model's own recall. Press et al. report that this structured decomposition, with or without a tool, measurably narrows the gap where CoT alone does not.

This is distinct from R1/R2 CoT, R3 Plan-and-Solve, and R4 ReAct on three different axes. **CoT** emits free-form reasoning prose with no enforced structure; Self-Ask emits a Q/A tree the operator can parse. **Plan-and-Solve** plans an upfront sequence of *actions* and then executes them; Self-Ask grows a tree of *questions* incrementally, where each next sub-question depends on the answer to the previous one. **ReAct** interleaves `Thought / Action / Observation` around a tool, and the loop is action-shaped; Self-Ask's loop is question-shaped — sub-questions are the unit, tools are optional, and many Self-Ask runs are pure model recall.

## Variants

The pattern has two named members differing in **whether sub-questions are answered by the model alone or by an external tool**:

- **Vanilla Self-Ask (Press et al., 2022).** The same model that produces follow-up questions also produces intermediate answers from its own parametric knowledge. Pure prompting; no external dependencies. Works when the sub-facts are within the model's training data.
- **Self-Ask with Search.** Each `Intermediate answer:` slot is filled by a search-engine call (Google, Bing, Tavily) keyed on the follow-up text. The original paper shows this lift accuracy substantially on time-sensitive and long-tail multi-hop questions. LangChain ships this as `create_self_ask_with_search_agent` with a single tool of name `Intermediate Answer`.

Both share the *structural move* — Q/A scaffold, named follow-ups, composition step. They differ only in who fills the intermediate-answer slots. A third common configuration — **Self-Ask with retrieval** — substitutes a **K1 Vanilla RAG** call for the search engine; treat that as a composition of R6 + K1 rather than a separate variant.

## Applicability

Use Self-Ask when:

- the question is compositional — two to four hops requiring distinct sub-facts;
- the model can plausibly know each sub-fact in isolation but consistently misses the combination;
- you want the decomposition to be *visible* for audit, debug, or operator inspection;
- the sub-questions are answerable by clean recall or a single tool call each (search, RAG, calculator), not by exploratory action.

Do not use it when:

- the question is single-hop — Self-Ask's scaffolding adds tokens with no compositional payoff; use **R1 Zero-Shot CoT** or even direct prompting;
- the task is action-shaped (must touch the world: write a file, send a message, query an API in a stateful way) — use **R4 ReAct**, whose loop is built for tool-driven exploration;
- the full set of sub-tasks is knowable upfront and they are largely independent — use **R3 Plan-and-Solve** (or **R5 ReWOO** for parallelism and token efficiency);
- the task is open-ended creative work without a "correct" composed answer — use **R8 Self-Refine**;
- the sub-question structure cannot be predicted at all and exploration drives the path — use **R9 Tree of Thoughts**.

## Decision Criteria

R6 is right when the question is compositional, the sub-facts are individually retrievable, and you need the decomposition to be visible.

**1. Measure the compositionality gap on your task.** Run a labelled sample of multi-hop questions through (a) direct prompting and (b) Self-Ask. The gap = (% of sub-facts the model can answer in isolation) − (% of compound questions it can answer end-to-end). If the gap exceeds **~10 percentage points**, Self-Ask's structural move is worth its tokens. If the gap is already small, the model is composing fine — keep R1 CoT.

**2. Count the hops.** Self-Ask shines at **2–4 hops**. At 1 hop, the scaffold is overhead. Above ~5 hops the Q/A chain bloats and intermediate-answer errors compound; switch to **R4 ReAct** with explicit state, or **R9 Tree of Thoughts** if the path branches.

**3. Pick a variant by where the sub-facts live.** Sub-facts inside the model's training data $\to$ **Vanilla Self-Ask** (no tool). Sub-facts are time-sensitive, long-tail, or proprietary $\to$ **Self-Ask with Search** (or compose with **K1 Vanilla RAG** against your corpus). The tool choice is the main lever; the scaffold itself is the same.

**4. Cost the chain.** Each hop adds one round-trip — a follow-up + an intermediate answer + (optional) a tool call. Plan-and-Solve and ReWOO can be cheaper when the sub-questions are independent and parallelisable; Self-Ask is inherently *sequential* because hop N+1 depends on hop N's answer. If the hops are genuinely independent, prefer **R5 ReWOO** for the 5$\times$ token efficiency.

**5. Bound the recursion.** Self-Ask is a loop disguised as a Q/A scaffold — `Are there follow-up questions? Yes / No.` A miscalibrated model can say *Yes* indefinitely. Cap the number of follow-ups (typical: **4–6**) via **V9 Bounded Execution**; force a final answer when the cap is hit.

**Quick test — R6 is the right pattern when:**

- the question is compositional and the hop count is 2–4, *and*
- the measured compositionality gap on your task exceeds the scaffold's token cost, *and*
- each sub-question can be answered by clean recall or one tool call (not by exploratory action), *and*
- you want the decomposition visible for audit.

If the hops are independent and parallelisable, choose **R5 ReWOO**. If the task is action-shaped or the path is genuinely unknown, choose **R4 ReAct**. If the question is single-hop, **R1 Zero-Shot CoT** is enough. If the sub-questions need retrieval against your own corpus rather than the web, compose Self-Ask with **K1 Vanilla RAG** instead of with a search engine.

## Structure

```
  Compositional question Q
         │
         ▼
  ┌──────────────────────────────────────────────┐
  │ Decomposer (LLM)                              │
  │   "Are follow-up questions needed? Yes."      │
  │   "Follow up: <sub-question 1>"               │
  └──────────────────────────────────────────────┘
         │
         ▼
  ┌──────────────────────────────────────────────┐
  │ Sub-question answerer                         │
  │   model recall    (Vanilla)                   │
  │   search engine   (Self-Ask with Search)      │
  │   K1 retriever    (Self-Ask + RAG)            │
  │   → "Intermediate answer: <a₁>"               │
  └──────────────────────────────────────────────┘
         │
         ▼
  ┌──── more follow-ups? ────┐
  │  yes → loop (bounded V9) │
  │  no  ↓                   │
  └──────────────────────────┘
         │
         ▼
  Composer (LLM) ──▶ "So the final answer is: <A>"
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Decomposer (LLM)** | producing the next follow-up question given the original question and the intermediate answers so far | Q + (Q₁, a₁) … (Qₖ, aₖ) $\to$ next sub-question Qₖ₊₁ *or* terminate signal | answer its own follow-up in the same step; the structural value is *naming* the sub-question before answering it. Conflating the two collapses Self-Ask back into CoT. |
| **Sub-question answerer** | producing the intermediate answer to one sub-question | Qₖ $\to$ aₖ | be the same call as the Decomposer; even when the same model serves both roles, the prompt must shift so the model is *only* answering Qₖ, not extending the chain. |
| **Tool (search / retriever / calculator)** *(optional)* | sourcing the sub-fact from outside the model | Qₖ $\to$ factual span | be invoked when the answer is already in the model's parametric knowledge with high confidence; calling out for every hop on a single-hop-knowable question wastes budget. |
| **Termination check** | deciding when no more follow-ups are needed | full Q/A history $\to$ continue / stop | hand control back to the Decomposer indefinitely; this is where **V9 Bounded Execution** caps the loop. |
| **Composer (LLM)** | producing the final answer from the intermediate answers | Q + all (Qᵢ, aᵢ) $\to$ A | reopen sub-questions or add unsupported claims; its job is composition, not re-decomposition. |

Five narrow responsibilities. The pattern's reliability comes from the **Decomposer / answerer separation**: when the same call both grows the chain *and* fills it in, the model takes shortcuts — guessing the composed answer before all sub-facts are surfaced. Self-Ask's scaffold (`Follow up:` / `Intermediate answer:`) is the mechanism that enforces the separation even when one model plays both roles.

## Collaborations

The Decomposer receives the compositional question Q and emits the first follow-up Qᵢ under the scaffold `Are follow-up questions needed? Yes. Follow up: …`. The Sub-question answerer fills the corresponding `Intermediate answer:` slot — either by the model's own recall (Vanilla variant), by an external search engine (Self-Ask with Search), or by a **K1** retrieval call (Self-Ask + RAG). Control returns to the Decomposer, which inspects Q together with the accumulated (Qᵢ, aᵢ) pairs and emits the next follow-up or signals termination by switching to `So the final answer is:`. The Termination check enforces a hard cap (typically 4–6 hops, via **V9**) so a miscalibrated Decomposer cannot loop forever. When termination fires, the Composer reads Q and the full sub-Q/A trace and produces the final answer A. The trace itself is the audit artefact — every hop is named, inspectable, and individually re-runnable.

## Consequences

**Benefits**
- Measurably narrows the compositionality gap that scale and CoT alone do not close (Press et al., 2022).
- Sub-questions and intermediate answers are *visible* — operators can inspect, audit, and re-run any single hop.
- Each sub-question is a clean injection point for a tool, a retriever, or a fact-checker; the scaffold is *the* canonical pattern for adding search to a multi-hop chain.
- The structure is model-agnostic and tool-agnostic — works with any capable generalist and any "give me the fact for this question" tool.

**Costs**
- Token cost grows with the number of hops — each hop appends to the accumulated context, growing the KV cache (mechanism 3) so each subsequent LLM call attends over a longer prefix at O(seq_len²) cost (mechanism 2). The growth is super-linear, not linear, once context is substantial. Self-Ask with Search partially mitigates this: the tool returns a compact answer that replaces a long retrieved document.
- Inherently sequential — hop N+1 depends on hop N's answer; cannot be parallelised the way **R5 ReWOO** can.
- Adds output structure the consumer must parse; downstream code must extract the final answer from the scaffold reliably.

**Risks and failure modes**
- *Wrong decomposition.* If the first follow-up names the wrong sub-fact, every later hop inherits the error. The Composer then produces a fluent answer to the wrong question.
- *Intermediate-answer hallucination.* In the Vanilla variant, the same model that decomposed the question also fills in its own intermediate answers — and may hallucinate them with the same confidence as the original wrong answer. Self-Ask narrows the gap; it does not eliminate it.
- *Unbounded recursion.* A miscalibrated Decomposer can keep saying `Yes` and growing the chain. Without **V9 Bounded Execution**, easy questions can spin out into ten-hop traces.
- *Format drift.* The scaffold depends on exact tokens (`Follow up:`, `Intermediate answer:`, `So the final answer is:`). Stronger models sometimes paraphrase; the parser must tolerate small variation or the pipeline silently breaks.
- *Tool mismatch.* Self-Ask with Search assumes the search engine returns short factual answers. Routing the follow-up to a tool that returns documents (rather than answers) requires an extra extraction step or the scaffold collapses.

## Implementation Notes

- The exemplars in the prompt do the heavy lifting — use Press et al.'s original four-exemplar template as a starting point; the scaffolding tokens must appear *literally* in the exemplars or the model will paraphrase them. The canonical Press et al. exemplar block is static across all queries in a domain — the canonical case for provider prefix caching (mechanism 5): a stable prefix above the variable question qualifies for the provider's KV-cache hit at ~10% of normal input token cost. Place the exemplar block at the top of the setup; under Anthropic caching rules a 1024+ token stable prefix reads at ~10% of normal input token cost.
- Use **Few-Shot CoT (R2)** style exemplars showing the full Q/A scaffold including the `Are follow-up questions needed?` opener — Zero-Shot Self-Ask exists but is noticeably less reliable than the few-shot version.
- For the Self-Ask with Search variant, choose a tool that returns *answers* not *documents* — Tavily's `TavilyAnswer`, Google's answer-box API, or a small wrapper that summarises top results. LangChain's `create_self_ask_with_search_agent` requires the tool to be named exactly `Intermediate Answer`.
- Cap the number of follow-ups (typical 4–6) via **V9 Bounded Execution**; when the cap is hit, force the model into the Composer role with an explicit `So the final answer is:` continuation.
- The Composer can be the same model and session as the Decomposer; the scaffold itself enforces the role switch. There is no need for a separate model unless the Composer needs domain knowledge the Decomposer lacks.
- When sub-facts live in your own corpus rather than on the web, compose with **K1 Vanilla RAG** at each hop — Self-Ask becomes the *outer* control loop around per-hop retrieval.
- Log the (Qᵢ, aᵢ) trace via **V14 Trajectory Logging**. The structured trace is far more useful than CoT prose for debugging compositional failures.

## Implementation Sketch

> `LLM = configured session (model + setup + per-call prompt); code = wiring.`

**Composition:** R6 chains a single Self-Ask session over a bounded loop. It composes with **R2 Few-Shot CoT** for the exemplar scaffold, with **K1 Vanilla RAG** or an external search tool to fill `Intermediate answer:` slots (the Self-Ask-with-Search variant), with **V9 Bounded Execution** to cap the follow-up loop, and with **V14 Trajectory Logging** to capture the per-hop trace. Signal-layer setup is **S6 Output Template** — the scaffold tokens are an output contract.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Build prompt P with Self-Ask exemplars + the question Q | `code` | R2, S6 |
| 2 | Decomposer emits `Follow up: Qₖ` *or* `So the final answer is: …` | `LLM` | Self-Ask session |
| 3 | Branch — if final-answer prefix detected, jump to step 6 | `code` | |
| 4 | Answer Qₖ — model recall *or* tool call *or* K1 retrieval | `LLM (or code)` | K1 / search tool |
| 5 | Append `Intermediate answer: aₖ` to the running prompt; check bound; loop to 2 | `code` | V9 |
| 6 | Extract the final answer from the `So the final answer is:` line | `code` | |
| 7 | Log the full (Qᵢ, aᵢ) trace | `code` | V14 |

**Skeleton** — the wiring only; each `# LLM` line is a configured session:

```
self_ask(question, max_hops=6):
    prompt = build_with_exemplars(question)                 # code  — R2 exemplars, S6 scaffold
    for hop in range(max_hops):                              # code  — V9 bound
        step = SelfAskSession(prompt)                        # LLM   — Decomposer or Composer
        if "So the final answer is:" in step:
            return extract_final(step), log_trace()          # code
        followup = parse_followup(step)                      # code
        answer = tool(followup) if use_search else SelfAskSession(answer_only_prompt(followup))
                                                             # LLM or code — sub-question answerer
        prompt += f"\nIntermediate answer: {answer}\n"       # code
    return force_compose(prompt), log_trace()                # LLM (forced Composer call)
```

**The LLM sessions.** Each `LLM` step must be *set up* before its first call.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Self-Ask** | capable generalist; same model serves Decomposer, Sub-question answerer (Vanilla variant), and Composer — the scaffold enforces the role switch | role ("you answer compositional questions by asking follow-ups"); the **four canonical exemplars** from Press et al. showing the full `Are follow-up questions needed? / Follow up: / Intermediate answer: / So the final answer is:` scaffold; output contract (S6) — must emit one of those four prefix tokens | the question Q, then progressively the accumulated `Follow up:` / `Intermediate answer:` history |
| **Sub-question answerer** *(only if separated from Self-Ask session)* | small fast generalist, or a search/retrieval tool — not an LLM at all in the Self-Ask-with-Search variant | role: *"answer the following short question with one factual sentence"*; output contract: one sentence, no scaffolding | the single sub-question Qₖ |

Concretely, for the **Self-Ask** session the setup loaded once is: the four Press et al. exemplars (each showing a compositional question worked through 2–3 follow-ups to a `So the final answer is:` line), plus the instruction *"Continue the same format for the new question below."* The per-call prompt then carries the question Q and any accumulated (Qᵢ, aᵢ) pairs.

**Specialist-model note.** None — Self-Ask is pure prompting; any capable generalist suffices. The build dependency is the **exemplar set**, not a fine-tuned model: the four canonical exemplars from Press et al. (or domain-specific replacements) are the prompt artifact that does the heavy lifting. The Self-Ask-with-Search variant adds a build dependency on an *answer-returning* search tool (e.g., Tavily, Bing answer box, Google CSE with answer extraction) — not a documents-returning retriever. If your tool returns documents, wrap it with a one-line summariser or compose with **K1 Vanilla RAG** instead.

## Open-Source Implementations

- **ofirpress/self-ask** — [`github.com/ofirpress/self-ask`](https://github.com/ofirpress/self-ask) — the original code and data from Press et al. (2022); includes the canonical prompt with exemplars, the Compositional Celebrities and Bamboogle benchmarks, and a search-engine demo notebook (`self-ask_plus_search-engine_demo.ipynb`).
- **LangChain `create_self_ask_with_search_agent`** — [`python.langchain.com/api_reference/langchain/agents/langchain.agents.self_ask_with_search.base.create_self_ask_with_search_agent.html`](https://python.langchain.com/api_reference/langchain/agents/langchain.agents.self_ask_with_search.base.create_self_ask_with_search_agent.html) — the production-grade reference implementation; an LLM + a single tool named `Intermediate Answer` (Tavily, Google Serper, etc.). The legacy `SelfAskWithSearchChain` class is deprecated in favour of this constructor.
- **LangChain docs — Self-ask with search** — [`python.langchain.com/v0.1/docs/modules/agents/agent_types/self_ask_with_search/`](https://python.langchain.com/v0.1/docs/modules/agents/agent_types/self_ask_with_search/) — the canonical tutorial; the simplest end-to-end Self-Ask-with-Search example in any framework.
- **Provider prompt-engineering guides** — Google, Anthropic, and OpenAI cookbooks include Self-Ask as a worked example for multi-hop QA; the prompt template is short enough that most production uses are inline rather than library-imported.

## Known Uses

- **Multi-hop QA benchmarks** — Self-Ask is a standard baseline alongside CoT and ReAct on HotpotQA, 2WikiMultiHopQA, Musique, Bamboogle, and Compositional Celebrities (the benchmark Press et al. introduced with the paper).
- **Search-augmented assistants** — Self-Ask with Search is one of the canonical architectures behind early answer-engine prototypes; the `Follow up: / Intermediate answer:` scaffold is visible (sometimes literally) in trace logs from systems that decompose a user query into web lookups before composing.
- **Enterprise RAG over compositional questions** — Self-Ask + **K1** is a common pattern when a single retrieval call cannot return all the sub-facts a compound question needs, but each sub-question retrieves cleanly on its own.
- **LangChain production agents** — the `create_self_ask_with_search_agent` constructor is widely used as the default scaffold for multi-hop factual QA with a single search tool.

## Related Patterns

- **Distinct from R1 Zero-Shot CoT and R2 Few-Shot CoT** — CoT emits free-form reasoning prose; Self-Ask emits a structured Q/A scaffold (`Follow up:` / `Intermediate answer:`) that names each sub-question explicitly. Self-Ask narrows the *compositionality gap* CoT alone leaves open.
- **Distinct from R3 Plan-and-Solve** — R3 plans a sequence of *actions* upfront before executing any of them; R6 grows a tree of *questions* incrementally, where each next sub-question depends on the answer to the previous one. R3 is action-shaped; R6 is question-shaped.
- **Distinct from R4 ReAct** — R4's loop is `Thought / Action / Observation` around a tool, with the loop structure built for exploratory action; R6's loop is `Follow up / Intermediate answer` around a sub-question, with tools optional. Many Self-Ask runs are pure recall with no tool at all; ReAct without tools is not ReAct.
- **Distinct from R5 ReWOO** — R5 plans *all* sub-tool-calls upfront with placeholder variables and executes them in parallel; R6 is inherently sequential because hop N+1 depends on hop N's answer. If the sub-questions are independent, R5 wins on token efficiency (5$\times$) and latency.
- **Composes with K1 Vanilla RAG** — each `Intermediate answer:` slot is a clean injection point for a retrieval call against the operator's corpus. Self-Ask + K1 is the canonical pattern for compositional questions over a private knowledge base.
- **Composes with R2 Few-Shot CoT** — the Self-Ask exemplars *are* a Few-Shot CoT prompt with a stricter output contract. Zero-Shot Self-Ask exists but is noticeably less reliable than the few-shot version.
- **Pairs with R4 ReAct at scale** — when each sub-question itself requires multi-step tool use rather than a single lookup, the sub-question slot becomes a small ReAct sub-loop. The outer pattern is still R6 (question decomposition); the inner pattern is R4 (action loop).
- **Pairs with V9 Bounded Execution** — the follow-up loop must be capped or a miscalibrated Decomposer will recurse on easy questions indefinitely.
- **Pairs with V14 Trajectory Logging** — the structured (Qᵢ, aᵢ) trace is a high-value audit artefact; log it.
- **Pairs with S6 Output Template** — the `Follow up:` / `Intermediate answer:` / `So the final answer is:` scaffold is a Signal-layer output contract that the Decomposer must honour exactly for the parser to work.

## Sources

- Press et al. (2022) — "Measuring and Narrowing the Compositionality Gap in Language Models" (arXiv [2210.03350](https://arxiv.org/abs/2210.03350); Findings of EMNLP 2023). The canonical reference; introduces both the compositionality-gap measurement and the Self-Ask method.
- ofirpress/self-ask GitHub repository — code, data, prompts, and the Compositional Celebrities + Bamboogle benchmarks ([`github.com/ofirpress/self-ask`](https://github.com/ofirpress/self-ask)).
- LangChain documentation — "Self-ask with search" agent type and the `create_self_ask_with_search_agent` constructor (the production reference implementation).
- Wei et al. (2022) — "Chain-of-Thought Prompting Elicits Reasoning in Large Language Models" (arXiv 2201.11903). The CoT baseline against which Self-Ask is measured.
- Yao et al. (2022) — "ReAct: Synergizing Reasoning and Acting in Language Models" (arXiv 2210.03629). The sibling action-loop pattern.
