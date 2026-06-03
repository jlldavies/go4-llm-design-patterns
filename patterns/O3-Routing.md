# O3 — Routing

> Classify the incoming input, then dispatch it to the specialised handler that fits — so each input type runs through a prompt or agent tuned for it instead of through one diluted generalist.

**Also Known As:** Classifier-Dispatcher, Intent Router, Query Router, Triage. (K5 Adaptive RAG's Retrieval Gate is a *specialised O3* applied to the retrieve-or-not decision.)

**Classification:** Category IV — Orchestration · Band IV-A Workflow · a *switching* pattern — it selects which downstream path runs, rather than running a fixed or dynamically-decomposed one.

---

## Intent

Make the choice of handler an explicit, inspectable, swappable step, so each input type meets a handler tuned for it and the routing decision itself becomes a first-class object the system can log, test, and improve.

## Motivation

A single prompt that has to cover every kind of input the system might receive — billing questions, technical support, refund requests, sales enquiries, abuse reports — ends up diluted. Its instructions hedge across cases; its few-shot examples cannot cover all the categories without bloating the context; it underperforms on each category compared with a prompt written for *that* category alone. The God-Prompt anti-pattern (A1) is what this looks like in the wild.

The fix is the same move applied across many engineering disciplines: classify first, then dispatch. A small step decides the input's *type* — by rules, by embedding similarity, or by a small classifier model or LLM call — and routes it to a handler built for that type. The handlers can then be tight, focused, and individually testable. Each one is typically an O1 Single Agent (or sometimes an O2 pipeline) specialised to its category.

At the attention level, a single diluted prompt forces the model's Q vectors to query a K-space that contains schema text and examples for all categories simultaneously. The learned bilinear form (Q_α K^α) that selects which tokens to attend to was not trained for this multi-category mixture; the inner products are spread thinly across all category examples rather than concentrated on the relevant ones (mechanism 1). A specialist prompt concentrates that K-space on one category's vocabulary, tightening the attention similarity computation. (Mechanism 1.)

O3 is *not* O2 Prompt Chaining: O2 follows a fixed sequence; O3 *selects which path runs*. It is not O4 Parallelization: O4 fans out to all branches simultaneously; O3 picks one. It is not O6 Orchestrator-Workers: O6 *dynamically decomposes* a task into worker calls at runtime; O3 selects from an enumerated set of pre-built routes. The distinguishing feature of O3 is the **fixed, enumerable set of routes** plus the **classification step that switches between them**. Routing also enables a deliberate cost-quality split — easy queries go to a small, fast, cheap handler; hard or unusual ones go to a bigger model. The dispatch decision becomes a knob the system can tune.

## Applicability

Use Routing when:

- inputs fall into clearly distinct categories that benefit from category-specific handling (different prompts, different tools, different models);
- a generalist handler measurably underperforms specialists on at least one category;
- you want a deliberate cost split — small models for easy categories, larger for hard ones;
- you need an explicit escalation path (human, specialist team, premium tier) for a defined subset of inputs;
- routing decisions need to be logged and audited (compliance, debugging, drift detection).

Do not use Routing when:

- inputs are uniform — one specialist is no better than another (use **O1 Single Agent**);
- the path is fixed and sequential regardless of input type (use **O2 Prompt Chaining**);
- every branch must run for every input and the outputs combine (use **O4 Parallelization**);
- categories are not enumerable upfront and the system must decompose tasks at runtime (use **O6 Orchestrator-Workers**);
- the only decision is *whether to retrieve* — that specialised case is **K5 Adaptive RAG**'s Retrieval Gate, not a general router.

## Decision Criteria

O3 is right when inputs split into distinct categories, a specialist beats a generalist on at least one, and the routes are enumerable at design time.

**1. Measure category separation.** On a labelled sample of historical inputs, can the categories be labelled with $\geq$ 90% inter-annotator agreement? Below ~80%, the categories are not crisp enough; the classifier will inherit the ambiguity. Fallback: collapse to **O1 Single Agent** with a stronger generalist prompt, or move the resolution into a downstream **O5 Evaluator-Optimizer** pass.

**2. Measure the specialist lift.** For each candidate category, build a category-specific handler and a generalist handler; compare quality on held-out inputs. If the specialist gives a measurable lift (typically $\geq$ 5–10pp on the category's primary metric), the route earns its place. If no category clears the bar, fall back to **O1**.

**3. Pick the classifier.** Three implementations, in increasing flexibility and cost:
- **Rule-based** (regex, keyword, deterministic feature) — sub-millisecond, free, brittle. Good when categories carry obvious surface signals.
- **Embedding similarity to route exemplars** (e.g. semantic-router) — single embedding call, ~10–50ms, cheap, robust to paraphrase. The production default for well-separated categories. Embedding cosine distance approximates the inner-product structure of the model's attention space — it is a cheaper proxy for the same discriminative computation the LLM would perform under its learned bilinear form, making it the right tool when the categories are linearly separable in embedding space (mechanism 1).
- **LLM classifier call** (small fast model with a classification prompt) — 100–500ms, cost-per-call, handles novel inputs and nuanced categories. Use when the categories require understanding.
If the classifier itself is wrong > 5% of the time on held-out data, the routing decision becomes the system's dominant failure mode — fix the classifier before adding more routes.

**4. Always define an `other` route.** A miscategorised input that falls into the wrong specialist handler is a worse failure than one that lands in a deliberate fallback. The `other` / `unknown` route should escalate to a generalist handler, a human, or a clarification prompt — never to the closest-matching specialist by default.

**5. Cost the routing layer.** Total per-request cost $\approx$ classifier cost + chosen handler cost. If the classifier is a large LLM call but the routed handlers are cheap, the router dominates spend and a smaller classifier (embedding or rule-based) likely pays. If routing accuracy matters more than cost, the LLM classifier earns its tokens.

**Quick test — O3 is the right pattern when:**

- inputs are categorisable with $\geq$ 90% inter-annotator agreement, *and*
- at least one category shows $\geq$ 5pp specialist lift over a generalist baseline, *and*
- the route set is enumerable at design time (with an explicit `other` route), *and*
- routing decisions need to be logged or used to control cost.

If categories are too fuzzy, fall back to **O1** with a stronger generalist or layer in **O5 Evaluator-Optimizer**. If the path is fixed regardless of input, use **O2**. If every branch must run, use **O4**. If task decomposition is dynamic and the route set is not enumerable, use **O6**.

## Structure

```
                      ┌── Route A: [Specialist Handler A — O1]
                      │
   Input ─▶ Classifier ──▶ Route B: [Specialist Handler B — O1 or O2]
            (rule /    │
             embedding/├── Route C: [Specialist Handler C — O1]
             LLM)      │
                      └── Route Other: [Generalist / Human escalation]
                                                  │
                                                  ▼
                                          [Logged routing decision → V14]
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Classifier** | the routing decision | raw input $\to$ route label | answer the input or look at handler output; a classifier that can also generate has no incentive to admit uncertainty and will overfit to the `default` route. |
| **Route Registry** | the enumerable set of valid routes and their handlers | — $\to$ `{label: handler}` table | accept new routes silently at runtime; route changes are a deployment event, not a runtime mutation. |
| **Dispatcher** | invoking the handler the Classifier named | route label + input $\to$ handler invocation | reinterpret the label or pick a different route; if the Classifier's label is invalid, it must go to `other`, not be quietly corrected. |
| **Specialist Handler(s)** | producing the answer for a specific input category | input $\to$ answer | handle inputs outside their category; a specialist that tries to be useful on the wrong input erodes the value of routing. Each is typically an **O1** instance. |
| **Fallback / `other` route** | catching inputs that do not fit any defined route | input $\to$ answer or escalation | be the dumping ground for low-confidence routes — that is misuse; the Classifier should send genuinely-ambiguous inputs here, not borderline ones it should have handled. |
| **Routing Logger** *(V14)* | recording each routing decision with its inputs and outcomes | input + label + handler outcome $\to$ audit record | be optional. Without it, misrouting is undebuggable and drift is invisible. |

The Classifier's separation from the Handlers is the pattern's load-bearing wall. Collapsing them — a generalist handler that "also decides what kind of question this is" — recreates the God-Prompt that motivated the pattern.

## Collaborations

An input arrives. The Classifier produces a route label, drawn from the Route Registry's enumerated set, plus (for non-rule classifiers) a confidence signal. The Dispatcher looks up the named handler and invokes it; if the label is invalid or confidence falls below threshold, the Dispatcher invokes the `other` route instead. The Specialist Handler runs — typically an O1 Single Agent with a prompt and tool set tuned to its category — and produces the answer. The Routing Logger (V14) records the input, the chosen route, the confidence, and the final outcome, so misrouting can be detected and the Classifier improved over time. When confidence is consistently low for a class of inputs the route set may need extending; when one route's outcomes are consistently poor the Specialist Handler needs work, not the router.

## Consequences

**Benefits**
- Specialist handlers outperform a single diluted generalist on their own category.
- Routing decisions are inspectable, loggable, and testable as a first-class step.
- Enables a deliberate cost-quality split — cheap handlers for easy categories, expensive ones for hard.
- Explicit escalation path (`other` route) for inputs the system cannot or should not handle.
- Each route is independently swappable; iterating on one specialist does not destabilise the others.

**Costs**
- Adds a classification step on the critical path (latency + cost, both modest with embedding-based routers).
- The Route Registry must be maintained — new categories require deployment, not a prompt tweak.
- Per-route evals must be maintained, not just a single end-to-end eval.

**Risks and failure modes**
- *Classifier drift* — input distribution shifts so the boundaries the Classifier learned no longer fit; quality degrades silently unless V14 logs are reviewed.
- *Overfit fallback* — the `other` route attracts everything ambiguous and quietly becomes the dominant route; the Classifier is effectively bypassed.
- *Specialist on the wrong input* — a Handler that "tries to be helpful" on out-of-category input produces confident wrong answers; specialists must refuse, not improvise.
- *Route explosion* — every new edge case spawns a new route; the registry becomes unmaintainable. Treat routes as expensive; merge before adding.
- *Classifier-Handler coupling* — a Classifier trained on yesterday's Handler outputs locks the system into yesterday's behaviour. Keep the Classifier's training data independent.

## Implementation Notes

- Start with the cheapest classifier that meets accuracy targets — usually embedding similarity to a small set of exemplars per route. Upgrade to an LLM classifier only when the embedding router misclassifies on understood-but-paraphrased inputs.
- Hold the Classifier's evaluation set separate from the Handlers' evaluation sets. A single end-to-end eval hides which component is failing.
- Log the classifier's confidence alongside the chosen route. A route taken at low confidence is the leading indicator of needed retraining or a missing category.
- When a new route is added, run the Classifier on historical data and confirm previously-routed inputs do not get reclassified in regressions; a new route can silently steal from an existing one.
- The `other` route should ideally do something useful — escalate to a generalist, ask a clarifying question, or escalate to a human — not return a generic error.
- Pair routing decisions with **V14 Trajectory Logging** by default. Without that audit trail, misrouting is invisible.
- For cost-driven routing (small model vs large model), make the cost-tier choice explicit in the route label, not hidden inside the Handler. Auditors should be able to see *why* an expensive call was made.
- The Classifier itself can be an **O1 Single Agent** call (a small fast model with a classification prompt). This is recursive but bounded — routers do not route to other routers.

## Implementation Sketch

> LLM = configured session (model + setup + per-call prompt); code = wiring.

**Composition:** O3 chains a *Classifier* (which can be code, embedding similarity, or a small LLM) with one of N *Specialist Handlers* (each typically an **O1 Single Agent**, sometimes an **O2 Prompt Chaining** pipeline). It pairs with **V14 Trajectory Logging** for audit and with **V9 Bounded Execution** when handlers themselves loop. K5 Adaptive RAG's Retrieval Gate is a specialised O3 applied to retrieve-or-not.

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Classify the input $\to$ route label + confidence | `code` *or* `LLM (or rule)` | Classifier session (if LLM) |
| 2 | Look up handler from Route Registry | `code` | |
| 3 | If label invalid or confidence < threshold, switch to `other` | `code` | |
| 4 | Dispatch input to chosen handler | `code` | O1 / O2 |
| 5 | Handler produces answer | `LLM` | Specialist Handler session |
| 6 | Log (input, label, confidence, handler, outcome) | `code` | V14 |

**Skeleton** — wiring only; the `# LLM` lines are configured sessions specified below:

```
route(input):
    label, conf = Classifier(input)                  # code / LLM — rule, embedding, or small LLM
    if label not in registry or conf < THRESHOLD:    # code
        label = "other"                              # code — explicit fallback
    handler = registry[label]                        # code
    answer = handler(input)                          # LLM — specialist (O1) or pipeline (O2)
    log(input, label, conf, handler.name, answer)    # code — V14 Trajectory Logging
    return answer
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Classifier** *(only if LLM-based)* | small fast generalist, or a fine-tuned classifier | role (*"you classify customer support messages into one of the following categories: BILLING, TECHNICAL, REFUND, ABUSE, OTHER"*); the category list with one-line definitions; output contract (*"reply with exactly one category name"*); calibration examples | the input |
| **Specialist Handler (per route)** | chosen per route — small model for cheap/easy categories, larger for nuanced | role specific to the category (S3); category-specific tools, constraints (S5), output template (S6), any domain context | the input |

For rule-based or embedding-based classifiers, no LLM session is required for the routing step — the classifier is pure code or a vector lookup against route exemplars.

**Specialist-model note.** A capable generalist suffices for the LLM-classifier variant; no fine-tuning is required, though a small fine-tuned classifier (DistilBERT-class) gives the lowest-latency and lowest-cost routing layer for high-volume systems. The *handlers* may individually require specialists — a code-handler route running a fine-tuned coding model, a legal-handler route running a long-context model — but those choices are local to each route, not to the routing pattern. The prompt artefact doing the heavy lifting on the routing step is the *category definitions* — terse, mutually-exclusive, exhaustive (with `OTHER` as the catch-all).

## Open-Source Implementations

- **Anthropic claude-cookbooks** — [`github.com/anthropics/claude-cookbooks`](https://github.com/anthropics/claude-cookbooks/tree/main/patterns/agents) — `basic_workflows.ipynb` contains the canonical reference implementation of the Routing workflow from "Building Effective Agents."
- **aurelio-labs semantic-router** — [`github.com/aurelio-labs/semantic-router`](https://github.com/aurelio-labs/semantic-router) — embedding-similarity routing layer; classify by cosine distance to per-route exemplar utterances; sub-LLM latency. The production default for embedding-based O3.
- **vllm-project semantic-router** — [`github.com/vllm-project/semantic-router`](https://github.com/vllm-project/semantic-router) — system-level intelligent router for Mixture-of-Models; BERT-classifier dispatch by cost, latency, safety, and modality across local, private, and frontier models. O3 applied to model selection.
- **LangGraph** — [`github.com/langchain-ai/langgraph`](https://github.com/langchain-ai/langgraph) — conditional edges and router functions are the framework's native expression of O3; the documentation's routing tutorials are runnable references.

## Known Uses

- **Customer support assistants** — billing, technical, refund, abuse, and general categories routed to different prompts, tool sets, and (often) different models.
- **Cost-tier routers** — easy queries to small fast models (e.g. Claude Haiku), hard or unusual to larger models (e.g. Claude Sonnet/Opus); a routine configuration in production cost-sensitive deployments. Large models are required for complex reasoning but simple classification tasks do not require large model capacity; routing to a small model for these cases is mechanically correct resource allocation (mechanism 8). (Mechanism 8.)
- **Triage systems** — automatable / needs specialist / needs human routing in clinical, legal, and financial support contexts.
- **Multi-domain assistants** — coding vs analysis vs creative routes inside developer-tool and productivity products.
- **K5 Adaptive RAG retrieve-or-not gate** — a specialised O3 where the "routes" are RETRIEVE and DIRECT.

## Related Patterns

- **Composes with** O1 Single Agent — each route's handler is typically an O1 instance specialised for that category.
- **Composes with** O2 Prompt Chaining — a route can terminate in an O2 pipeline rather than a single handler.
- **Composes with** V14 Trajectory Logging — routing decisions are first-class audit events; pair by default.
- **Composes with** V9 Bounded Execution — when handlers loop (R4 ReAct, R7 Reflexion), the loop cap belongs inside the handler, not at the router.
- **Distinct from** O2 Prompt Chaining — O2 follows a fixed sequence; O3 *selects which path runs*.
- **Distinct from** O4 Parallelization — O4 fans out to all branches; O3 picks one.
- **Distinct from** O6 Orchestrator-Workers — O6 dynamically decomposes tasks into worker calls at runtime; O3 dispatches to a fixed, enumerated route set.
- **Specialised by** K5 Adaptive RAG's Retrieval Gate — K5's retrieve-or-not decision is O3 narrowed to one specific routing question.
- **Pairs with** V15 LLM-as-Judge — when the Classifier is itself an LLM call, V15 techniques (rubric, calibration set) are the right way to evaluate it.
- **Mitigates** A1 God Prompt — Routing is the principled decomposition the God Prompt fails to do.

## Sources

- Anthropic (2024) — "Building Effective Agents" (Schluntz & Zhang) — lists Routing as one of five canonical workflow patterns.
- Anthropic claude-cookbooks — `patterns/agents/basic_workflows.ipynb` reference implementation.
- aurelio-labs semantic-router documentation — embedding-similarity routing as a production pattern.
- vllm-project semantic-router and the "vLLM Semantic Router" paper (arXiv 2603.04444) — routing applied to model selection in Mixture-of-Models.
- AWS Prescriptive Guidance — agent design patterns, routing variant.
- LangGraph documentation — conditional edges and router functions.
