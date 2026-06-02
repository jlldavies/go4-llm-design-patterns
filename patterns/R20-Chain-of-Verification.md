# R20 — Chain-of-Verification

> Have a model draft an answer, generate verification questions targeted at its own factual claims, answer each question independently so the answers do not lean on the draft, and revise the draft from those answers — turning hallucination into a thing the model checks against itself.

**Also Known As:** CoVe, Verify-Then-Revise, Question-Driven Self-Verification. (Joint, 2-Step, Factored, and Factor+Revise are *variants* of this pattern — see Variants.)

**Classification:** Category III — Reasoning · Band III-C Iterative refinement · the *question-driven* self-verification pattern — sibling of R8 Self-Refine's *general-critique* form and R7 Reflexion's *external-signal* form.

---

## Intent

Reduce hallucination in a single-shot answer by interrogating it: surface the factual claims the answer rests on as explicit verification questions, answer each one independently of the draft, and rewrite the draft from those answers.

## Motivation

A model that produces a fluent answer is not, by that fluency, producing a true one. Hallucinated dates, fabricated citations, invented attributes, plausible-but-wrong names — these are the dominant failure modes when a language model speaks confidently outside its weights. The naive responses are familiar and unsatisfying: retry and hope (no improvement guarantee), add retrieval (changes the problem to grounding), or run a generic self-critique (R8 — the critic shares the generator's blind spots in vague ways).

Dhuliawala et al. (2023) made a sharper move. Rather than ask the model to *critique* its output, ask it to *interrogate* it. Take the draft, *generate verification questions* that target each load-bearing factual claim ("When was X born? Who founded Y? Which city hosts Z?"), and then — crucially — *answer each verification question in a fresh context that does not see the draft*. The independence is the load-bearing structural choice: when the verifier cannot see the draft's claims, it cannot anchor on them, so its answers reveal where the draft was wrong. The mechanistic basis of independence is attention architecture (mechanism 1): when the Verifier receives only the isolated question, its attention Q vectors have no draft tokens to contract against; the model samples exclusively from parametric knowledge (mechanism 7 — stochastic distribution over its weights, which do not change between calls, mechanism 10). When the draft is present, Q vectors over the question tokens also attend to the draft's factual claims via the learned Q-K bilinear form (mechanism 1), anchoring the Verifier's response to the draft's framing. The independence boundary is a KV-isolation measure: the Factored variant's fresh session per question ensures the verification K vectors are drawn solely from the question tokens (mechanism 3 — the KV cache does not persist across API calls; each fresh session starts with an empty cache). Finally, rewrite the draft from the verification answers, keeping the parts the verification supported and correcting the parts it contradicted.

The defining claim is that **specific factual questions, answered independently, surface hallucinations that general self-critique does not.** This is what separates R20 from the rest of the iterative-refinement band. R8 Self-Refine asks "what is wrong with this?" — a broad question that lets the critic share the generator's framing. R7 Reflexion needs an external pass/fail signal — code that ran, a test that failed — and uses that to drive retries. R20 sits between them: no external signal needed, but the critique step is decomposed into atomic factual sub-questions whose independent answers function as the signal. The verifier's blind spots are still the model's blind spots, but by re-asking each fact afresh, the pattern uses the model's prior probability over isolated facts as a check on its prior probability over fluent compositions of those facts. Empirically, Dhuliawala et al. report consistent reductions in hallucination on Wikidata list questions, MultiSpanQA, and long-form biography generation — with the Factor+Revise variant the strongest on long-form.

## Variants

The four variants from the original paper differ in **how steps 2–4 (plan questions / answer questions / revise) are wired**, and trade verifier independence against simplicity:

- **Joint.** Verification questions *and* their answers are generated together in one prompt that also sees the draft. Simplest; weakest, because the answers can anchor on the draft. (Dhuliawala et al. 2023; reported as the baseline-but-worst CoVe variant.)
- **2-Step.** One LLM call plans the questions; a second LLM call answers all of them in a single batch. Cleaner separation than Joint; answers can still bias each other within the batch.
- **Factored.** One call plans the questions; *each question is answered in its own independent call*, with no draft and no sibling answers in context. The strongest independence; most calls.
- **Factor+Revise.** Factored plus an explicit cross-check step: after the independent answers come back, an extra LLM call compares each verification answer against the draft and flags inconsistencies *before* the final revision step. Dhuliawala et al. report this as the strongest variant for long-form generation.

All four are the same pattern — *draft, surface factual claims as questions, answer them, revise* — differing only in where the independence boundary is drawn and whether a cross-check step is added. **Factored** is the canonical recommendation for short-form questions where call cost is acceptable; **Factor+Revise** for long-form generation where inconsistencies need to be enumerated before rewriting.

## Applicability

Use Chain-of-Verification when:

- the task produces a **fluent factual answer** (biographies, list questions, entity descriptions, summaries with named entities, long-form factual writing) and hallucination of names, dates, or attributes is the dominant failure;
- there is **no automated pass/fail signal** — if there were, **R7 Reflexion** is stronger and cheaper per round;
- you cannot or do not want to add retrieval — **K1 Vanilla RAG** or **K5 Adaptive RAG** are usually a better fix when a corpus exists, but they are infrastructure CoVe does not require;
- the budget tolerates **2–5× the single-shot cost** (one extra plan call, one batch or N independent answer calls, one revision call);
- the model is strong enough that its **prior over isolated facts is more reliable than its prior over fluent compositions of facts** — this is the load-bearing assumption.

Do not use it when:

- an automated criterion exists (tests, schema, executor) — use **R7 Reflexion**;
- the hallucinations are not factual but structural / stylistic / logical — use **R8 Self-Refine** (general critique catches those; verification questions do not);
- a corpus of ground-truth documents is available — use **K1 / K5** to ground the draft rather than interrogating the model against itself;
- you can afford a different judge model — use **O5 Evaluator-Optimizer**, whose model-separation catches blind spots a same-model verifier cannot;
- the answer space is one where independent samples *vote* cleanly (a literal mode exists) — use **R17 Self-Consistency Voting** at lower marginal cost;
- latency budget cannot tolerate the question-planning round-trip plus the answer-batch round-trip.

## Decision Criteria

R20 is right when the failure mode is *fluent-but-fabricated facts*, no external signal exists, and a corpus to ground against is unavailable or undesired.

**1. Measure the hallucination rate on a labelled sample.** Score single-shot outputs for factual claims; mark each claim correct / wrong / unverifiable. If the **hallucinated-claim rate exceeds ~10%** of named facts and matters to the user, CoVe earns its calls. Below ~5% the loop usually does not pay; reach for **S6 Output Template** (cite-or-omit contract) or accept single-shot.

**2. Pick a variant from the task shape.**
- Short-form (list questions, single-sentence factuals, closed-book QA) — **Factored**: cheap enough per question, strongest independence.
- Long-form (biographies, multi-paragraph factual writing) — **Factor+Revise**: the explicit consistency-check step is what Dhuliawala et al. found made the difference on long-form.
- Cost-constrained / latency-critical — **2-Step**: one plan call, one batched answer call; weaker independence but cheaper.
- Prototype / quickest deploy — **Joint**: one call, weakest variant; useful only to demonstrate the pattern before committing to the stronger forms.

**3. Cost the loop honestly.** Factored at K verification questions = 1 draft + 1 plan + K answer + 1 revise = **K+3 LLM calls**. Long-form with K=8 questions → **11 calls** for what was one. Factor+Revise adds one more cross-check call. The economically defensible move is often Factored on a strong generalist rather than Joint on a cheaper model — *the independence is the lift, not the iteration count*.

**4. Cap the verification questions.** Set a hard ceiling on questions per draft (typical: **K ≤ 10**) and prompt the planner to focus on load-bearing claims. Without a cap the planner enumerates every minor entity and the loop's cost explodes. Pair with **V9 Bounded Execution** for the overall loop bound.

**5. Test the independence assumption.** On a labelled sample, compare the **Joint** variant against **Factored** on the same drafts. If Factored does not measurably outperform Joint, the model is not anchoring on the draft when it sees it — and CoVe is doing nothing R8 could not do more cheaply. The independence has to be paying for itself or the pattern is not the right choice.

**Quick test — R20 is the right pattern when:**

- the dominant failure mode on this task is **fluent factual hallucination** (names, dates, attributes), *and*
- no automated pass/fail signal is available (otherwise **R7**), *and*
- a corpus to ground against is unavailable or not worth the build (otherwise **K1 / K5**), *and*
- a separate judge model is not warranted or affordable (otherwise **O5**), *and*
- the latency and cost budgets tolerate K+3 sequential calls per output.

If the hallucinations are structural or stylistic rather than factual, use **R8 Self-Refine**. If an automated criterion exists, use **R7 Reflexion**. If a corpus exists, use **K1 Vanilla RAG** or **K5 Adaptive RAG** to ground the draft. If independent samples vote cleanly, use **R17 Self-Consistency Voting**.

## Structure

```
  Task ─▶ Drafter (LLM) ─▶ draft
                            │
                            ▼
                  Planner (LLM, sees draft) ─▶ verification questions [Q1..Qk]
                            │
                            ▼
              ┌─── for each Qi (no draft in context) ───┐
              │                                          │
              ▼                                          ▼
        Verifier (LLM) ─▶ A1     ...     Verifier (LLM) ─▶ Ak
              │                                          │
              └─────────────────┬────────────────────────┘
                                ▼
                  (Factor+Revise only)
                  Cross-check (LLM) ─▶ inconsistencies
                                ▼
                       Reviser (LLM) ─▶ revised answer
                                ▼
                          Final output

  Independence boundary: the Verifier(s) MUST NOT see the draft.
  Bound the question count and overall loop with V9.
```

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Drafter (LLM)** | producing the initial fluent answer | task → draft | be skipped or replaced with retrieval — the pattern interrogates *the draft*; without one there is nothing to verify. |
| **Planner (LLM)** | surfacing the draft's load-bearing factual claims as verification questions | task + draft → list of atomic factual questions | emit composite or leading questions ("Isn't it true that X was born in Y?"); each question must be **atomic, factual, and neutrally phrased**, or the verifier will reproduce the draft's errors. |
| **Verifier (LLM)** | answering each verification question independently of the draft | verification question (alone, no draft, no sibling answers in Factored) → answer | see the draft, or see other verification answers (in Factored). The independence boundary is the pattern's only structural defence against shared bias; collapsing it collapses the pattern. |
| **Cross-checker (LLM)** *(Factor+Revise only)* | comparing each verification answer against the corresponding claim in the draft and listing inconsistencies | draft + {(Qi, Ai)} → inconsistencies | rewrite the draft itself; that is the Reviser's job. The cross-checker only *flags*. |
| **Reviser (LLM)** | rewriting the draft using the verification answers (and the cross-check, if present) | draft + {(Qi, Ai)} (+ inconsistencies) → revised answer | invent new claims not supported by either the draft or the verification answers; revision must be a reconciliation, not a regeneration. |
| **Loop controller** | enforcing the question cap and overall bound | question count, iteration count → continue / stop | run unbounded — a planner that enumerates every entity needs a hard cap (**V9 Bounded Execution**). |

Six narrow responsibilities, of which one is variant-conditional. The four roles **Drafter / Planner / Verifier / Reviser** are present in every variant; the **Cross-checker** is the structural addition that defines Factor+Revise. The same model can fill every LLM role — what matters is that the Verifier's *session* receives no draft in its context. **Different sessions, same model** is the canonical configuration.

## Collaborations

The Drafter answers the task and emits a draft. The Planner reads the task and the draft and writes K verification questions, each targeting a single factual claim. The Loop controller caps K. Each verification question is then sent to the Verifier — in the **Factored** variant, in its own independent call with no draft and no sibling answers; in **2-Step**, in a batched call with the other questions but no draft; in **Joint**, in the same call as planning, with the draft. The Verifier answers, returning a set {(Qi, Ai)}. In **Factor+Revise**, the Cross-checker now reads the draft and the {(Qi, Ai)} pairs and emits a list of inconsistencies. The Reviser receives the draft, the verification answers, and (when present) the inconsistencies, and rewrites the draft so that every retained claim is consistent with a verification answer. The revised answer is returned. Each LLM role is a separate session of the same model; their setups (role, output contract) differ, their model identity does not.

## Consequences

**Benefits**
- Reduces *fluent factual hallucination* on tasks where the model's prior over isolated facts is better calibrated than its prior over compositions — the empirical case Dhuliawala et al. document.
- Needs no external signal (unlike R7) and no second model (unlike O5) — works wherever single-shot CoVe-able.
- The verification questions and their answers are **inspectable artifacts** — a user can read *why* the revision changed what it did. Operationally valuable in factual workflows.
- Factor+Revise's explicit inconsistency list is a checkable audit trail; pair with **V14 Trajectory Logging**.
- Composes cleanly with **S6 Output Template** (question-and-answer format contracts) and **K1 Vanilla RAG** (verification questions can also be sent to a retriever, turning CoVe into a retrieval-augmented self-check).

**Costs**
- **K+3 LLM calls** in Factored at K questions; **K+4** in Factor+Revise. At K=8 that is **~3–5× the single-shot cost** for one revision.
- Sequential dependencies on the critical path (draft → plan → verify → revise) mean wall-clock latency adds up; verifier calls can parallelise within a round but the rounds themselves are serial.
- Planner quality caps the pattern's value. A planner that asks the wrong questions verifies the wrong things.

**Risks and failure modes**
- *Verifier anchoring* — the most common failure: the Verifier sees the draft (Joint variant, or accidental context leakage in 2-Step) and confidently re-confirms the draft's hallucinations. The independence boundary is load-bearing; protect it. The mechanistic failure path: the draft in context adds O(draft_length) extra K vectors; the Verifier's Q vectors over the fact question produce high inner products with K vectors from the draft's factual claims (mechanism 1), effectively conditioning the Verifier's answer on the claim it is verifying. Joint variant failure is thus not a heuristic observation but a predictable consequence of attention geometry.
- *Leading questions* — the Planner phrases verification questions in a way that presupposes the draft's claims ("How old was X when she founded Y?" presupposes X founded Y). Symptom: verification rates are suspiciously high. Fix: prompt the Planner to neutralise framing and decompose presuppositions.
- *Shared blind spots* — when the model's prior over the isolated fact is *also* wrong, the Verifier confidently confirms a hallucination. CoVe cannot fix what the model itself does not know; in that regime, **K1 / K5** (retrieve against an external corpus) is the right move, not more self-verification.
- *Missed claims* — the Planner skips a load-bearing factual claim, the Reviser leaves it untouched, and the final answer still hallucinates. Reduce by prompting the Planner to enumerate all named entities and dates explicitly, and by capping K at a level that allows full coverage.
- *Reviser regeneration* — the Reviser rewrites the answer from scratch instead of reconciling claims, introducing new hallucinations. Symptom: revised output contains claims neither in the draft nor in any verification answer. Mitigate with a strict Reviser prompt: *"only keep claims supported by a verification answer or unchallenged in the draft"*.
- *Unbounded planner* — without a question cap, the loop's cost is unpredictable.

## Implementation Notes

- **The Verifier prompt sees only the question.** No draft, no other answers, no chain-of-thought from the planner. This is the single most important implementation detail in the pattern. In code, this typically means a fresh session per question (Factored) or at minimum a prompt with the draft scrubbed out (2-Step).
- **The Planner prompt should explicitly ask for atomic, neutrally-phrased, factual questions.** Provide one or two few-shot examples (**S2 Few-Shot**) showing decomposition of a composite claim into multiple atomic questions. Without this, planners default to leading or composite questions.
- **Cap K — 5 to 10 verification questions is the working range.** For very long drafts, run CoVe paragraph-by-paragraph rather than blowing K out.
- **Verifier answer contract.** Constrain the Verifier to short, declarative answers with an "unknown" sentinel. *"Answer in one short sentence. Reply UNKNOWN if you are not confident."* The Reviser handles UNKNOWN as "do not keep this claim".
- **Same model, different sessions.** Generator, Planner, Verifier, (Cross-checker), Reviser are typically the same model with separate setups. Using a different (often weaker) model as the Verifier defeats the pattern: the Verifier's prior is the check, so the Verifier should be the strongest available.
- **Compose with retrieval where a corpus exists.** A natural extension is to send each verification question to a retriever (**K1**) and feed the retrieved snippet to the Verifier as grounding. This converts CoVe from a closed-book self-check into a fact-checking pipeline.
- **Pair with V9 Bounded Execution** — cap K (the question count) and bound any outer loop that re-runs CoVe on the revised answer.
- **Log the (question, answer) pairs** (**V14 Trajectory Logging**) — they are a high-value audit artifact and a source of error analysis when the pattern misses.
- **Multi-round CoVe is usually waste.** Running CoVe on the revised output rarely lifts further; the verifier's information was already extracted in round 1. If quality remains poor after one round, the failure is structural (planner missed a claim, verifier shared the blind spot) and another round will not fix it.

## Implementation Sketch

> `LLM = configured session (model + setup + per-call prompt); code = wiring.`

**Composition:** R20 chains four (or five, in Factor+Revise) sessions of *the same model* — Drafter, Planner, Verifier, (Cross-checker), Reviser — under a code-driven loop controller. It draws on **S2 Few-Shot** for the Planner's question-decomposition examples, **S6 Output Template** for the structured question/answer contracts, **V9 Bounded Execution** for the question cap, and **V14 Trajectory Logging** for the audit trail. R20 composes upward into **O6 Orchestrator-Workers** as a quality step applied to a worker's factual output, and laterally with **K1 Vanilla RAG** (verification questions sent to a retriever).

**The chain (Factor+Revise, the strongest long-form variant):**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Drafter writes the initial answer | `LLM` | Drafter session |
| 2 | Planner generates K verification questions | `LLM` | Planner session (S2, S6) |
| 3 | Cap K and dispatch | `code` | V9 |
| 4 | For each Qi, Verifier answers independently (no draft) | `LLM` (×K) | Verifier session |
| 5 | Cross-checker compares answers to draft, lists inconsistencies | `LLM` | Cross-checker session *(Factor+Revise only)* |
| 6 | Reviser rewrites draft from {(Qi, Ai)} and inconsistencies | `LLM` | Reviser session |
| 7 | Return revised answer | `code` | |

**Skeleton** — the wiring only; each `# LLM` line is a configured session of the same model:

```
chain_of_verification(task, max_questions=8):
    draft     = Drafter(task)                                # LLM — model M
    questions = Planner(task, draft)[:max_questions]         # LLM — model M, Planner session; V9 cap
    answers   = [Verifier(q) for q in questions]             # LLM ×K — model M, Verifier session
                                                             #          NO draft in context (Factored)
    issues    = CrossChecker(draft, zip(questions, answers)) # LLM — model M (Factor+Revise only)
    return Reviser(task, draft, zip(questions, answers), issues)   # LLM — model M, Reviser session
```

In the **Factored** variant, drop step 5 (no Cross-checker) and pass `issues=None` to the Reviser. In **2-Step**, replace the per-question Verifier loop with a single batched call (`answers = Verifier(questions)`). In **Joint**, fold steps 2 and 4 into one call (`questions_and_answers = JointPlanner(task, draft)`); this is the simplest and weakest variant.

**The LLM sessions.** All sessions use *the same model*. They differ in setup (role, criteria, output contract); the per-call prompt wraps only the changing data.

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Drafter** | the system's main generalist (must be strong enough that its *prior over isolated facts* is more reliable than its prior over fluent compositions — this is the pattern's load-bearing assumption) | role (S3); output contract for the task (S6); any domain context | the task instance |
| **Planner** (same model) | role: *"you read an answer and surface its load-bearing factual claims as atomic, neutrally-phrased verification questions; do not presuppose the answer's claims; one fact per question"*; one or two few-shot examples (S2) showing decomposition of a composite claim; output contract — a numbered list of K questions, one per line | the task + the draft |
| **Verifier** (same model, **fresh session per question** in Factored) | role: *"answer the following factual question in one short sentence; reply UNKNOWN if you are not confident; do not speculate"*; output contract — single-sentence answer or UNKNOWN; **no draft, no sibling answers, no chain-of-thought from the planner** | a single verification question |
| **Cross-checker** *(Factor+Revise only, same model)* | role: *"compare each verification answer to the corresponding claim in the draft and list any inconsistencies"*; output contract — a list of `(claim, verification answer, consistent? yes/no, note)` | the draft + the {(Qi, Ai)} list |
| **Reviser** (same model) | role: *"rewrite the answer so that every retained claim is supported by a verification answer or is unchallenged in the draft; do not invent new claims; preserve the draft's structure and style"*; the original task and success criteria | the task + the draft + the {(Qi, Ai)} list (+ inconsistencies, in Factor+Revise) |

**Specialist-model note.** None required — Chain-of-Verification works with any capable generalist; the structurally important choice is that **all sessions use the same model**, the **Verifier session sees no draft**, and the model is **strong enough that its prior over isolated facts is more reliable than its prior over fluent compositions** (the load-bearing assumption). The Planner's prompt (with S2 few-shot examples for question decomposition) and the Verifier's prompt (with the UNKNOWN sentinel) are the prompt artifacts doing the heavy lifting; both deserve careful authoring. A long-context model is *not* required — verification questions are small and the loop's bottleneck is sequential calls, not context length.

## Open-Source Implementations

- **ritun16/chain-of-verification** — [`github.com/ritun16/chain-of-verification`](https://github.com/ritun16/chain-of-verification) — the most-cited community implementation; Python + LangChain + OpenAI, with separate chains for the three question types Dhuliawala et al. benchmarked (Wikidata list, MultiSpanQA, longform).
- **hwchase17/chain-of-verification** — [`github.com/hwchase17/chain-of-verification`](https://github.com/hwchase17/chain-of-verification) — LangChain Expression Language port of the above by LangChain's creator; the closest thing to a reference graph.
- **langchain-chain-of-verification** (PyPI) — [`pypi.org/project/langchain-chain-of-verification`](https://pypi.org/project/langchain-chain-of-verification/) — packaged distribution of the ritun16 CLI for newer LangChain versions.
- **Note on canonicity.** Meta AI (the paper's authors) did not release an official implementation. The community implementations above cover the four variants; treat them as faithful but unofficial references.

## Known Uses

- **Long-form factual writing assistants** — biography generation, encyclopedic summaries, and entity-description workflows where named-entity hallucination is the dominant failure mode; CoVe is documented in practitioner literature as a baseline mitigation when retrieval is not available.
- **Fact-checking pipelines** — verification questions sent to a retriever or web search (composing CoVe with K1) underpins several open-source fact-check prototypes.
- **Closed-book QA evaluators** — Wikidata list questions and MultiSpanQA-style benchmarks are the canonical empirical setting (Dhuliawala et al. 2023).
- **Educational and prompt-engineering tooling** — CoVe is a standard entry in advanced prompting curricula (learnprompting.org, Anthropic / OpenAI cookbook-style content) as the canonical *self-verification* technique distinct from generic self-critique.

## Related Patterns

- **Sibling of R8 Self-Refine** — same band (iterative refinement), same generate-critique-revise *shape*, but R8's critique is *general* ("what is wrong with this output?") while R20's critique is *decomposed into atomic factual verification questions answered independently*. R8 is cheaper and catches structural / stylistic / logical issues; R20 catches *factual* hallucinations R8 misses because its critic shares the generator's fluent framing. **Use R8 for general quality lift; use R20 specifically when the failure mode is fluent factual hallucination.**
- **Sibling of R7 Reflexion** — same band, same iterate-from-critique shape, but R7 requires an **external pass/fail signal** (test execution, schema validation) and R20 generates its own check from independent re-asking of facts. R7 is stronger when an automated signal exists; R20 is the option when it does not.
- **Sibling of R17 Self-Consistency Voting** — both reduce error through repetition without external signal, but R17 samples N *full answers* in parallel and votes, while R20 decomposes a single answer into K *atomic claims* and re-asks each. R17 fits answers with a literal mode; R20 fits open-ended factual outputs that have no mode to vote over.
- **Distinct from O5 Evaluator-Optimizer** — O5 uses a **separate judge model** (architectural separation); R20 uses the **same model** in a separate session with the draft hidden (in-context separation). O5 catches blind spots R20 cannot when the model itself is wrong about the fact; R20 is the lighter weight when independence-by-context-isolation is enough.
- **Composes with K1 Vanilla RAG / K5 Adaptive RAG** — when a corpus exists, route each verification question through a retriever and feed the snippet to the Verifier. This converts CoVe from a closed-book self-check into a retrieval-augmented fact-checking pipeline.
- **Composes with S2 Few-Shot** — the Planner's question-decomposition step benefits materially from one or two few-shot examples; without them, planners default to composite or leading questions.
- **Composes with S6 Output Template** — structured question and answer contracts (numbered list of questions; one-sentence-or-UNKNOWN answers) make the loop controller deterministic.
- **Pairs with V9 Bounded Execution** — cap K (the question count); without a cap the Planner enumerates every entity and the loop's cost explodes.
- **Pairs with V14 Trajectory Logging** — the (question, answer) pairs are a high-value audit artifact.
- **Composes upward into O6 Orchestrator-Workers and R3 Plan-and-Solve** — R20 is a natural verification step applied to a worker's factual output before it returns to the orchestrator.

## Sources

- Dhuliawala, S., Komeili, M., Xu, J., Raileanu, R., Li, X., Celikyilmaz, A., & Weston, J. (2023) — "Chain-of-Verification Reduces Hallucination in Large Language Models" (arXiv [2309.11495](https://arxiv.org/abs/2309.11495); also published in *Findings of the Association for Computational Linguistics: ACL 2024* — [aclanthology.org/2024.findings-acl.212](https://aclanthology.org/2024.findings-acl.212/)). The canonical reference; the four-step draft / plan / verify / revise procedure, the four variants (Joint, 2-Step, Factored, Factor+Revise), and the empirical evaluation on Wikidata list questions, MultiSpanQA, and longform biography generation.
- Learn Prompting — [Chain-of-Verification (CoVe)](https://learnprompting.org/docs/advanced/self_criticism/chain_of_verification) — practitioner-oriented walkthrough of the four variants and prompts.
- ritun16 / chain-of-verification — [`github.com/ritun16/chain-of-verification`](https://github.com/ritun16/chain-of-verification) — the most-cited community implementation, with per-question-type chains.
