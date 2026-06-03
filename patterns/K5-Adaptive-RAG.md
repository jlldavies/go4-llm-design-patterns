# K5 — Adaptive RAG

> Wrap retrieval in an evaluation-and-control loop: decide whether retrieval is needed at all, judge the quality of what comes back, and act on that judgment — skip it, proceed, re-retrieve, or fall back to another source.

**Also Known As:** Self-Reflective RAG, Adaptive Retrieval, Agentic RAG. (Self-RAG and Corrective RAG / CRAG are *variants* of this pattern — see Variants.)

**Classification:** Category II — Knowledge · Band II-A Retrieval · a *control* pattern — it wraps K1, or any of K2–K4, rather than replacing it.

---

## Intent

Make retrieval conditional and self-correcting, so the system retrieves only when retrieval helps and recovers when retrieval fails, instead of retrieving blindly on every query and trusting whatever returns.

## Motivation

K1 Vanilla RAG retrieves on *every* query, unconditionally, and uses whatever returns, uncritically. It is a straight pipeline with no decision points. Two failure modes follow directly from that:

- **Retrieval that should not happen.** For a query the model can answer from its own weights — an arithmetic question, a request to summarise pasted text, a piece of general knowledge — retrieval injects irrelevant chunks that distract the model and cost tokens. K1 has no step that asks *should I retrieve at all?* (Weights-only answers are stochastic samples from the model's learned distribution — mechanism 7 — with no external anchor and no auditability; the Gate's DIRECT branch trades auditability for latency savings, which is appropriate only when the query is genuinely answerable from trained knowledge.)
- **Retrieval that fails silently.** When the corpus does not contain the answer, or the retrieved chunks are off-topic, K1 proceeds regardless: it feeds the generator poor context and produces a confident, well-formatted, wrong answer that *looks* grounded. K1 has no step that asks *is what I got actually any good?*

Both failures have the same cause — the absence of judgment — and the same fix: insert an evaluation step and a control decision that acts on it. Evaluate *before* retrieval ("is retrieval needed?") and *after* it ("is this good enough, and does my answer rest on it?"), and branch on the verdict. That evaluation-and-control loop is the pattern. It is fundamentally distinct from K1: K1 is a straight line; Adaptive RAG is a loop with branches.

## Variants

The variants differ in *where the judgment lives* and *how recovery works*:

- **Self-RAG.** The model itself is trained to emit *reflection tokens*: a decision token (retrieve or not), a relevance token (is this passage relevant), and a support token (is my answer grounded in it). Evaluation is internal to the model; it typically requires a fine-tuned model, though the behaviour can be approximated with prompting. (Asai et al., 2023.)
- **Corrective RAG (CRAG).** A separate, lightweight evaluator scores the retrieved documents. On a low score it triggers a *fallback* — typically web search, sometimes query reformulation or broader retrieval. Evaluation is an external component; recovery is corpus-side. (Yan et al., 2024.)

Both are the same pattern — *judge the retrieval, branch on the verdict* — differing only in implementation. That shared core is why they are one pattern and not two: neither adds a structural element the other lacks; they are two ways to build the same loop.

## Applicability

Use Adaptive RAG when:

- the query stream is mixed — some queries need retrieval, some are answerable from weights;
- the task is factuality-critical and a silent retrieval miss is unacceptable;
- the corpus may be stale or incomplete, so retrieval failure is a realistic event.

Do not bother when:

- every query genuinely needs retrieval and the corpus is known to be complete — the evaluation overhead then buys nothing;
- latency is so tight that no extra evaluation calls can be afforded.

## Decision Criteria

K5 is right when the cost of a silent retrieval failure is high — or when many queries do not need retrieval at all.

**1. Measure the bad outcomes.** On a labelled test set:
- **Skip-rate** — what % of queries are answerable from weights alone? > 30% means the Gate saves real cost and noise.
- **Silent-miss rate** — what % of K1 retrievals fetch *something* that does not actually answer? > 5% means the Quality Evaluator catches them.
- **Ungrounded-answer rate** — what % of K1 answers carry unsupported claims? > 5% means the Support Evaluator catches them.

If all three are low, you do not need K5.

**2. Pick a variant.**
- **Self-RAG** — reflection tokens from a fine-tuned model; specialist build dependency; tightest integration.
- **Corrective RAG** — external evaluator + web-search fallback; works with off-the-shelf models; the easier deploy.

**3. Cost the loop.** K5 adds 1–3 LLM calls per query (gate, quality, support). Small fast models keep the overhead modest. Web-search fallback adds external cost on misses.

**4. Reliability budget.** Is this a task where confidently wrong is unacceptable (medical, legal, financial, safety)? Then K5 is mandatory regardless of measured miss rate — the Support Evaluator pays for itself the first time it catches a hallucination.

**5. Loop-bound discipline.** Pair with **V9 Bounded Execution** — set a hard cap on recovery rounds. Otherwise a hard query can cascade fallbacks indefinitely.

**Quick test — K5 is the right pattern when:**

- skip-rate, silent-miss-rate, or ungrounded-answer-rate exceeds your reliability budget, *and*
- evaluation latency is acceptable, *and*
- the cost of a silent wrong answer materially exceeds the cost of a corrective check.

If retrieval is always needed and the corpus is always sufficient, K1 alone suffices. If retrieval always fails for corpus reasons, expand the corpus — do not wrap it. If only the web-search fallback matters, the **Corrective RAG** variant is simpler than full **Self-RAG**.

## Structure

```
  Query ──▶ [ Retrieve? ] ──no──▶ answer from weights ──────────────────────▶ Answer
                 │
                yes
                 ▼
            Retrieve ──▶ [ Quality OK? ] ──no──▶ Fallback ──┐
                              │                  (web search,│
                             yes                  reformulate,│
                              │                   re-retrieve)│
                              ▼                               │
                          Generate ◀───────────────────────────┘
                              │
                              ▼
                      [ Answer supported? ] ──no──▶ revise / retry
                              │
                             yes
                              ▼
                            Answer
```

## Participants

Each participant owns exactly one decision and nothing else — the pattern's reliability comes from that separation of responsibility.

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Retrieval Gate** | the retrieve-or-not decision | raw query $\to$ boolean | answer the query, or look at documents — it sees none. A gate that can also generate has no incentive to ever say "no". |
| **Retriever** | fetching candidate context | query $\to$ chunk set | judge its own sufficiency. It is an inner pattern (K1, or K2–K4), invoked unchanged. |
| **Quality Evaluator** | the verdict on retrieved context | query + chunks $\to$ pass/fail | see the final answer (it grades *inputs*), or fetch anything itself. |
| **Fallback Retriever** | recovery when quality fails | query + failure signal $\to$ fresh context | be trusted more than the primary — its output re-enters the same Quality gate. |
| **Support Evaluator** | the verdict on the answer's grounding | answer + context $\to$ supported/not | re-judge relevance (that was Quality's call); it asks only "does the answer rest on this context". |
| **Generator** | producing the answer | query + approved context $\to$ answer | retrieve, or decide whether its own answer is grounded. |

Six narrow responsibilities, each independently testable and swappable. The Self-RAG variant collapses the Gate and both Evaluators *into the model* via trained reflection tokens; the CRAG variant keeps the Quality Evaluator as an external component. Either way the six responsibilities are the same — only their packaging differs.

## Collaborations

A query arrives. The Retrieval Gate decides whether retrieval is warranted; if not, the Generator answers from the model's weights and the loop ends. If retrieval proceeds, the Retriever runs and the Quality Evaluator scores the result. On a passing score, the Generator produces an answer. On a failing score, the Fallback Retriever is invoked — web search, reformulation, or broader retrieval — and its result re-enters the same Quality gate. After generation, the Support Evaluator checks that the answer rests on the retrieved context; if it does not, the answer is revised or the loop retries. A bound on the number of recovery rounds (V9 Bounded Execution) keeps the loop terminating.

## Consequences

**Benefits**
- Avoids the noise and cost of retrieving when retrieval is not needed.
- Catches retrieval failures instead of passing them silently to the generator.
- Degrades gracefully on out-of-corpus queries — the fallback keeps the system answering.

**Costs**
- Evaluation adds LLM calls, a trained model, or extra components.
- Latency: each gate and evaluator sits on the critical path.
- The web-search fallback adds external cost and further latency.

**Risks and failure modes**
- *Miscalibrated gate* — skips retrieval on a query that needed it, or retrieves on one that did not.
- *False-negative evaluator* — rejects good retrieval, triggering needless and possibly worse fallbacks.
- *Cascading fallback* — one fallback fails its own quality check and triggers another, compounding cost and latency. The compounding is non-linear: each recovery round adds context (retrieved chunks, reformulated queries, tool outputs) to the session, and each subsequent LLM call pays an n² attention cost over that growing context (mechanism 2). This is the mechanistic reason V9 Bounded Execution is not optional — without a hard cap, a hard query causes a super-linear cost spiral.

## Implementation Notes

- The Gate decides RETRIEVE or DIRECT — a binary classification task, not reasoning. The Quality Evaluator decides PASS or FAIL — likewise a classification. Binary classification does not require frontier model capacity (mechanism 8); a small fast model or trained classifier is mechanically correct and cuts the per-query overhead. The same applies to the Support Evaluator.
- The Self-RAG variant needs a fine-tuned model for true reflection tokens; a strong prompt can approximate it at lower fidelity.
- For the CRAG variant, set the quality threshold from measured data, not a guess — it is the pattern's main tuning lever.
- A web-search fallback should feed its results back through the normal retrieval-and-evaluation path, not straight into the generator.
- Query reformulation as a fallback move is K2 Query Transformation invoked inside the loop.
- Bound the recovery loop (V9 Bounded Execution); without a cap, a hard query can cascade fallbacks indefinitely.

## Implementation Sketch

> An LLM pattern is mostly abstract chaining, not runnable code. Steps marked `LLM` are judgment or generation: they cannot be reduced to code, and they are never bare calls — each is a *configured session* with a chosen model, a **setup loaded once before its first execution** (role, criteria, examples, reference context), and a per-call prompt that wraps the changing data. Steps marked `code` are the deterministic wiring the developer writes. The value of the sketch is the chain: which patterns connect, in what order, and where the LLM does the un-codeable work.

**Composition:** K5 wraps an inner retriever (K1, or K2–K4) in a control loop, drawing on **K2** for query reformulation during recovery and **V9** to bound it. The setup of each LLM session is itself Signal-layer work — a role (S3), constraints (S5), an output contract (S6).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Gate — does this query need retrieval? | `LLM` | Gate session |
| 2 | Branch — if not, skip to step 6 | `code` | |
| 3 | Retrieve candidate context | `code` | K1 / K2–K4 |
| 4 | Quality — is the context good enough? | `LLM` | Quality session |
| 5 | Branch — pass $\to$ 6; fail $\to$ recover (reformulate via K2, then web search), loop to 3 | `code` | K2, V9 |
| 6 | Generate the answer | `LLM` | Generator session |
| 7 | Support — is the answer grounded? | `LLM` | Support session |
| 8 | Branch — revise once if not grounded | `code` | |

**Skeleton** — the wiring only; each `# LLM` line is a configured session (specified below), not code:

```
adaptive_rag(query):
    Gate(query) ───────────────── # LLM   → if DIRECT: answer from weights, return
    loop up to max_rounds:         # code  — V9-bounded recovery loop
        retrieve(query) ─────────── # code  — inner pattern: K1
        Quality(query, context) ─── # LLM   → PASS breaks the loop
        on FAIL → rewrite via K2, else web_search ── # code — recovery
    answer = Generator(query, context) ───────────── # LLM
    Support(answer, context) ───── # LLM   → if UNSUPPORTED: revise once
```

**The LLM sessions.** Each `LLM` step must be *set up* before its first call. The setup — model choice, role, criteria, output contract — is established once; the per-call prompt then wraps only the data that changes.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Gate** | small fast generalist, or a trained binary classifier | role ("you decide whether a query needs retrieval"), the RETRIEVE-vs-DIRECT criteria, output contract (one word) | the query |
| **Quality** | small fast generalist; in CRAG often a fine-tuned evaluator | role ("you grade retrieved context for relevance and sufficiency"), output contract (PASS / FAIL) | the query + retrieved context |
| **Generator** | the system's main generalist | role (S3), answer format and citation rules (S6), any domain or policy context the task requires | the query + approved context |
| **Support** | small fast generalist | role ("you check whether an answer is fully grounded in its context"), output contract (SUPPORTED / UNSUPPORTED) | the answer + its context |

Concretely, for the **Gate** session: the setup loaded once is *"You decide whether a query needs document retrieval. Reply RETRIEVE if it depends on specific, external, private, or current facts; reply DIRECT if a capable model can answer from general knowledge. Reply with one word."* The per-call prompt then carries only *"Query: {query}"*. The other three sessions follow the same setup-once, wrap-data-per-call split.

**Specialist-model note.** The two variants differ exactly here. In **Self-RAG**, there are no separate Gate / Quality / Support sessions — all three are one **specialist model**, fine-tuned to emit reflection tokens inline during generation; its setup *is* the fine-tuning, the judgment trained in rather than prompted. In **CRAG**, the Quality session is typically a small **fine-tuned retrieval evaluator** (a specialist), not a general model. Whenever an LLM step uses a specialist, the sketch must say so — a specialist is a build dependency, not a drop-in prompt.

## Open-Source Implementations

- **Self-RAG** — [`github.com/AkariAsai/self-rag`](https://github.com/AkariAsai/self-rag) — the original implementation; reflection-token training data, fine-tuning, and inference code.
- **Corrective RAG (CRAG)** — [`github.com/HuskyInSalt/CRAG`](https://github.com/HuskyInSalt/CRAG) — the original implementation; retrieval-evaluator training and CRAG inference.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — runnable reference graphs for Adaptive RAG, Self-RAG, and CRAG in its tutorials; the closest match to the control loop shown above.
- **AWS sample** — [`github.com/aws-samples/simplified-corrective-rag`](https://github.com/aws-samples/simplified-corrective-rag) — a simplified CRAG assistant on Amazon Bedrock.

## Known Uses

- **Perplexity** and similar answer engines — gate queries and fall back to web search when the index is insufficient.
- **LangGraph**-based production assistants — the adaptive-RAG and CRAG reference graphs are a common production starting point.
- Enterprise RAG assistants increasingly add a retrieval-quality gate before generation as standard practice.

## Related Patterns

- **Wraps** K1–K4 — Adaptive RAG is a control loop around an inner retriever; any retrieval pattern can be that retriever.
- **Composes with** K2 Query Transformation — reformulation is a natural fallback move inside the loop.
- **Composes with** V9 Bounded Execution — the recovery loop must be capped, or a hard query cascades fallbacks without end.
- **Distinct from** K2 — K2 decides *with what key* to retrieve; K5 decides *whether* to retrieve and *whether it worked*. Different questions; they compose.
- **Shares the judge mechanism with** V15 LLM-as-Judge and the Reasoning pattern Reflexion — the same evaluate-then-act move, applied here to retrieval.
- **Note on fundamentality** — Self-RAG and CRAG were merged into this single pattern because both are precisely "evaluate the retrieval, branch on the verdict"; they differ only in where the evaluator sits and how recovery is done. Two implementations of one pattern, not two patterns.

## Sources

- Asai et al. (2023) — "Self-RAG: Learning to Retrieve, Generate, and Critique through Self-Reflection."
- Yan et al. (2024) — "Corrective Retrieval Augmented Generation" (arXiv 2401.15884).
- LangGraph adaptive-RAG reference documentation.
