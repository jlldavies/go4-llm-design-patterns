# O14 — Single Information Environment

> Partition the corpus by ownership rather than unifying it: each agent owns a single, bounded dataset, and a coordinator routes every query to the agent that owns the data the answer lives in — composing across owners only when the question crosses domains.

**Also Known As:** SIE, Data-Centric Agent Design, Domain-Partitioned Agents, Data-Product Agents.

**Classification:** Category IV — Orchestration · Band IV-C Specialised Coordination · a *data-partitioning* coordination pattern — agents are defined by the corpus they own, not by the behaviour they perform.

---

## Intent

Make data ownership the primary unit of agent specialisation, so the routing question becomes "*which dataset holds the answer?*" rather than "*which capability is needed?*", and each owner agent is tuned to one bounded corpus instead of one shared one.

## Motivation

Enterprise data is rarely one corpus. It is sales data here, HR data there, finance data behind a different access boundary, support tickets in a fourth system — each with its own schema, vocabulary, freshness, and access rules. Two naive responses both fail:

- **One unified corpus (K1 over everything).** Indexing it all together blurs the vocabularies — "owner" in CRM $\neq$ "owner" in HR $\neq$ "owner" in legal — and the retriever returns plausibly-relevant chunks from the wrong domain. Access boundaries are also lost: the index can leak content the requesting user should not see.
- **One generalist agent over all the tools (O6 with worker = "everything").** The worker's context fills with tool schemas and policy text from every domain. Domain-specific prompting and per-corpus tuning are impossible because there is only one prompt.

The right move is to make **ownership** the architectural primitive. Each agent owns *one* dataset: its schema, its retriever, its tuning, its access rules, its system prompt — all scoped to that domain. A coordinator looks at the query, picks the owner whose dataset holds the answer, and delegates. Cross-domain queries decompose into per-owner sub-queries that the coordinator synthesises. The owners are *specialists by data*, not by task.

The mechanical basis is that the retriever's embedding similarity (or the LLM's Q-K inner product) is computed over a K-space that contains tokens from both domains. When "owner" appears in CRM documents and HR documents with different semantic contexts, the K vectors for these tokens cluster in overlapping regions of embedding space — the learned bilinear form cannot discriminate which sense is relevant because it was trained over mixed-domain data rather than the clean partition you want (mechanism 1). Separate Owner agents with domain-specific prompts steer the Q vectors to query from the right region of K-space. (Mechanism 1.)

This is structurally distinct from O3 Routing (which routes by *task type* to handlers that often share data) and from O6 Orchestrator-Workers (which decomposes by *capability* into workers that share the corpus). The defining commitment of O14 is the partition itself: **the corpus does not unify — it stays sharded by owner**, and that shape is what every other element of the pattern is designed around.

## Applicability

Use SIE when:

- the underlying data is genuinely partitioned — distinct schemas, distinct sources, distinct freshness, or distinct access boundaries;
- a unified K1 RAG over the combined corpus produces confused results because vocabularies clash across domains;
- per-domain tuning matters — each dataset benefits from its own retriever, prompt, and policy;
- access control / data-sovereignty constraints require that an agent only ever sees the data it owns.

Do not use when:

- the corpus is genuinely one corpus with one vocabulary — use **K1** with a unified index;
- specialisation is by task, not by data (e.g. summarise vs translate vs code) — use **O3 Routing**;
- the work is open-ended decomposition over a shared corpus — use **O6 Orchestrator-Workers**;
- the shared substrate *is* the architectural commitment (multi-agent reasoning over common memory) — use **O11 Blackboard** or **K10 Long-Term Memory**.

## Decision Criteria

O14 is right when ownership boundaries already exist in the data and you want the agent architecture to mirror them, rather than paper over them with a unified index.

**1. Count the partitions.** Identify the candidate datasets and the boundary that separates them (schema, source, access rule, owning team). If you cannot draw the boundaries cleanly, the data is not partitioned — use **K1**. Practical threshold: **2–10 distinct, named partitions** is where O14 earns its keep. One partition is K1; more than ~10 is usually a sign the partitions are too granular and want a hierarchy (**O7**).

**2. Measure cross-domain miss rate on a unified K1 baseline.** Build a K1 index over the combined corpus, run a representative query set, label each answer for correctness. If **> 15% of failures** are "retrieved from the wrong domain" or "blended vocabularies from two domains", the unified corpus is hurting you and SIE will fix it. Below that, K1 is still cheaper.

**3. Score the per-domain tuning benefit.** For each candidate partition, ask: does it want its own retriever config, system prompt, or policy? If three or more partitions answer yes, per-domain tuning is a real lever and SIE captures it. If they would all share the same configuration, the partitioning is cosmetic — use **O3**, where handlers can share a retriever.

**4. Check the access-control axis.** If different users / tenants have different visibility across partitions, SIE encodes that in the architecture — an owner agent simply cannot return data outside its partition. If access is uniform, the access-control argument doesn't apply and the choice between O14 and O3 is purely operational.

**5. Cost the coordinator and cross-domain queries.** The coordinator adds one classification call per query. Cross-domain queries add fan-out (one call per relevant owner) and a synthesis step — usually **O4 Parallelization** over the chosen owners plus a final aggregator. Budget for it; without **V9 Bounded Execution** on the fan-out, a broad query can pull every owner.

**Quick test — O14 is the right pattern when:**

- the data has 2–10 well-defined ownership boundaries, *and*
- a unified-corpus K1 baseline shows material cross-domain confusion (> 15% miss rate from wrong-domain retrieval), *and*
- per-domain tuning (retriever, prompt, policy) is a meaningful lever, *and*
- the cost of the coordinator + occasional cross-domain fan-out is acceptable.

If the partitions are imaginary, use **K1**. If the partitions are real but the specialisation is by *behaviour* rather than *data*, use **O3 Routing**. If you need open-ended decomposition over a shared corpus, use **O6**. If you need multi-agent collaboration on a *shared* substrate rather than partitioned ones, use **O11 Blackboard** or **K10 Long-Term Memory**.

## Structure

```
                       Query
                         │
                         ▼
                  ┌─────────────┐
                  │ Coordinator │  ── classifies which dataset(s) own the answer
                  └─────────────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ Owner A │      │ Owner B │      │ Owner C │
   │ (data A,│      │ (data B,│      │ (data C,│
   │  retr A,│      │  retr B,│      │  retr C,│
   │  prompt │      │  prompt │      │  prompt │
   │   A)    │      │   B)    │      │   C)    │
   └─────────┘      └─────────┘      └─────────┘
        │                │                │
        └────────────────┼────────────────┘
                         ▼
                  ┌─────────────┐
                  │ Synthesiser │  ── single-domain: pass through;
                  └─────────────┘     multi-domain: combine answers
                         │
                         ▼
                       Answer
```

## Participants

| Participant | Owns | Input $\to$ Output | Must not |
|---|---|---|---|
| **Coordinator** | the dataset-selection decision | query $\to$ set of owner IDs | answer the query, hold any data, or call any owner's retriever directly. A coordinator that can also retrieve has no incentive to delegate. |
| **Partition Manifest** | the catalogue of owners, their domains, and access rules | — $\to$ routable manifest the Coordinator reads | be inferred at runtime; it must be declared and versioned, or routing decisions become unreproducible. |
| **Owner Agent** *(one per partition)* | one bounded dataset and its retrieval / answer pipeline | sub-query $\to$ answer scoped to its dataset | look outside its partition, even when the query mentions another domain. Crossing the boundary is the Coordinator's call, not the Owner's. |
| **Synthesiser** *(used for multi-domain queries)* | combining answers from multiple owners into one response | per-owner answers + original query $\to$ final answer | re-retrieve, or override an Owner's answer on the Owner's home turf. It composes; it does not adjudicate within a domain. |
| **Access Policy** | the rule that gates which owners a given user / tenant can reach | (user, owners) $\to$ permitted subset | be enforced inside Owner Agents alone — it must gate at the Coordinator, or a misrouted query can leak. |

Five narrow responsibilities. The pattern's reliability comes from the rule that **no Owner ever sees data it does not own**, even on a cross-domain query — the Coordinator decomposes, the Owners answer independently, the Synthesiser composes.

## Collaborations

A query arrives. The Coordinator reads the Partition Manifest, applies the Access Policy for the requesting user, and classifies the query into one or more owner partitions. If the query is single-domain, the matching Owner Agent retrieves from its dataset and answers; the Synthesiser is a pass-through. If the query spans multiple domains, the Coordinator decomposes it into per-owner sub-queries — typically fanned out in parallel via O4 Parallelization — and each Owner answers independently from its own data. The Synthesiser then combines the per-owner answers into a single response, attributing each fragment to its owner. The recovery loop on misrouting (the Coordinator chose the wrong owner, or a chosen owner has no relevant data) is bounded by V9 Bounded Execution: a small number of re-routes, then a graceful "no owner has this" response.

## Consequences

**Benefits**
- Per-domain tuning: each Owner gets its own retriever, prompt, and policy, scoped to one dataset.
- Vocabulary integrity: queries do not blend retrievals across domains where the same word means different things.
- Access control as architecture: an Owner cannot return data outside its partition, so misrouting cannot leak.
- Cleaner governance: adding, removing, or updating a domain affects only its Owner Agent.

**Costs**
- Coordinator + fan-out + synthesis is more infrastructure than a single K1 retriever.
- Cross-domain queries pay N retrievals plus a synthesis call.
- Each Owner is a separately maintained surface (retriever config, prompt, evals).
- The Partition Manifest is a piece of authored configuration that has to stay current with the data.

**Risks and failure modes**
- *Misrouting* — the Coordinator picks the wrong Owner; the Owner answers confidently from the wrong corpus.
- *Boundary leakage* — an Owner reaches outside its partition (via a hidden tool, a stale cached index, or prompt drift); access control breaks silently.
- *Cross-domain blindness* — a question that needs joining across domains gets routed to one Owner and answered as if the rest does not exist.
- *Manifest rot* — the declared partition map drifts from the actual data layout; routing decisions look correct but go to the wrong place.
- *Cascading fan-out* — broad queries route to "all owners" without bound, multiplying cost.

## Implementation Notes

- Make the Partition Manifest a first-class, versioned artefact — declared, not inferred. The Coordinator reads it; the Owners do not.
- The Coordinator should be small and fast (a classifier or a small generalist). The Owners carry the heavyweight prompts and retrievers.
- Owners should be **structurally identical** apart from their dataset and configuration — same pattern (K1 or its refinement), different corpus. Diverging Owner implementations defeats the maintainability win. Structural identity also enables prefix caching: if all Owner agents share a common system-prompt template prefix that differs only in the domain-specific suffix, the shared prefix can be cached at the provider level and served to subsequent calls at ~10% of normal prefill cost (mechanism 5). Each Owner then pays prefill only for its domain-specific suffix, not for the shared instructions — a meaningful cost saving when the Coordinator routes the same query to multiple Owners. (Mechanism 5.)
- A cross-domain query usually decomposes into a parallel fan-out (O4) of single-domain sub-queries, then a synthesis call. Don't reinvent the orchestration here.
- Enforce access control at the Coordinator (gate the candidate owner set) *and* at each Owner (refuse to answer if asked outside its partition). Defence in depth.
- Bound the recovery / re-route loop (V9) — without a cap, a query no Owner can answer cascades indefinitely.
- Log the routing decision in V14 trajectory logs — "wrong owner chosen" is the most common failure and only a log will expose it.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** O14 chains a Coordinator (selects owners) with N Owner Agents (each typically a K1 or K2–K5 retrieval pattern) and a Synthesiser (composes multi-owner answers). Cross-domain queries compose with **O4 Parallelization**; the recovery / re-route loop composes with **V9 Bounded Execution**; routing decisions are logged via **V14 Trajectory Logging**. Each Owner's setup is Signal-layer work — role (**S3**), constraints (**S5**), output contract (**S6**).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Load Partition Manifest, apply Access Policy for the user | `code` | — |
| 2 | Coordinator picks one or more Owner IDs | `LLM` | Coordinator session |
| 3 | Branch — single owner $\to$ step 5; multiple owners $\to$ step 4 | `code` | — |
| 4 | Decompose into per-owner sub-queries; fan out | `code` | O4 |
| 5 | Each chosen Owner retrieves + answers within its partition | `LLM` ($\times$ N) | Owner session(s); inner K1/K2–K5 |
| 6 | Synthesise per-owner answers (pass-through if N=1) | `LLM` (or `code`) | Synthesiser session |
| 7 | Bound any re-route on "no owner could answer" | `code` | V9 |

**Skeleton** — the wiring; each `# LLM` line is a configured session (specified below):

```
sie(query, user):
    manifest = load_manifest()                          # code
    allowed  = AccessPolicy(user, manifest)             # code
    owners   = Coordinator(query, allowed) ──────────── # LLM
    loop up to max_reroutes:                            # code — V9 bound
        if len(owners) == 1:
            answer = Owner[owners[0]](query) ────────── # LLM   (inner: K1)
            return answer
        subs    = decompose(query, owners)              # code
        partials = parallel_map(                        # code — O4
                     lambda o: Owner[o](subs[o]),       # LLM   (inner: K1)
                     owners)
        answer  = Synthesiser(query, partials) ──────── # LLM
        if answer is not "no owner can answer":
            return answer
        owners = Coordinator.reroute(query, owners)     # LLM
    return graceful_no_owner_response()                 # code
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Coordinator** | small fast generalist, or a fine-tuned classifier | role (*"you choose which owner agents hold the data needed to answer a query"*); the Partition Manifest summary (one line per owner: name + domain + scope rules); output contract (JSON list of owner IDs); explicit rule that "none" is an allowed answer | the query + the allowed-owner subset for this user |
| **Owner Agent** *(one configured session per partition)* | a capable generalist; per-domain tuning where it earns its keep | role scoped to this partition (*"you answer questions about {domain X} from the {dataset X} corpus only"*); the dataset's schema / vocabulary cues; the retriever interface; output contract; the strict refusal rule for out-of-partition questions | the (sub-)query and the retrieved context from this partition's retriever |
| **Synthesiser** | capable generalist; can be the same model as the Owners | role (*"you combine per-owner answers into one coherent response, attributing fragments to their owner"*); rules for handling contradiction across owners (surface, do not paper over); output template | the original query + the list of (owner, answer) pairs |

**Specialist-model note.** No fine-tuned specialist is *required* — capable generalists serve every session — but two specialisations are common in production: (1) the Coordinator is often a small fine-tuned classifier when partition count is high and latency matters; (2) individual Owner Agents may use domain-tuned models (a finance-tuned model on the finance partition, a legal model on the legal partition) where domain accuracy materially lifts the result. Both are build dependencies, not drop-in prompts, and should be declared as such in the Partition Manifest.

## Open-Source Implementations

SIE is an architectural pattern, not a single library — what teams ship is a configuration of a general multi-agent framework with the partition-by-data discipline applied. The closest canonical references are:

- **LangGraph Supervisor** — [`github.com/langchain-ai/langgraph-supervisor-py`](https://github.com/langchain-ai/langgraph-supervisor-py) — the production-grade supervisor library; partition agents by data domain and the supervisor becomes an SIE Coordinator. The official tutorial's music-store example (music_catalog owner vs invoice_info owner) is SIE in miniature.
- **LangGraph multi-agent tutorials** — [`github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/multi_agent/agent_supervisor.md`](https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/multi_agent/agent_supervisor.md) — runnable supervisor + specialist-agent graphs that map directly onto Coordinator + Owner Agents.
- **Databricks Agent System Design Patterns** — [docs.databricks.com](https://docs.databricks.com/aws/en/generative-ai/guide/agent-system-design-patterns) — vendor reference describing the supervisor + domain-specialist pattern as the recommended shape for partitioned enterprise data.
- **Modern Data 101 — AI Agents & Data Products** — [moderndata101.substack.com](https://moderndata101.substack.com/p/how-ai-agents-and-data-products-work) — the data-mesh framing: each data product is a domain-bounded container; agents are scoped to one data product; cross-domain queries orchestrate across products. Same pattern, named from the data-engineering side.

## Known Uses

- **Enterprise multi-domain assistants** built on LangGraph supervisor — one agent per data system (CRM, HRIS, finance, support), supervisor as Coordinator.
- **Telecommunications security and national heritage asset management** case studies in Renney et al. (2026) — both case studies in the SIE paper use the pattern in production-style pilots.
- **Data-mesh organisations** — each "data product" team exposes a domain-bounded agent; a central coordinator handles cross-product queries.
- **Tenant-isolated SaaS assistants** — each tenant or business unit has its own Owner with strict partition rules; SIE provides the access-control architecture as a side-effect of the data partitioning.

## Related Patterns

- **Distinct from** O3 Routing — O3 routes by *task type* to handlers that may share data; O14 routes by *dataset ownership* to agents that each own a private slice. The classifier step looks similar; the architectural commitment (partition the corpus) is different.
- **Distinct from** O6 Orchestrator-Workers — O6 decomposes a goal by *capability*; O14 routes by *data*. O6 workers share the corpus; O14 owners do not.
- **Distinct from** O11 Blackboard and K10 Long-Term Memory — both rely on a *shared* substrate that multiple agents read and write. O14's commitment is the opposite: substrates do not share; they partition.
- **Composes with** K1 (and K2–K5) — each Owner Agent is internally a retrieval pattern. O14 is the orchestration shell; K1 is what fills each cell.
- **Composes with** O4 Parallelization — cross-domain queries fan out across owners.
- **Composes with** V9 Bounded Execution — bound the re-route / fan-out loop.
- **Composes with** V14 Trajectory Logging — routing decisions must be logged; misrouting is the most common failure.
- **Refined by** O7 Supervisor Hierarchy — when partitions are themselves partitioned (region $\to$ product line $\to$ dataset), O14 nests into O7's tree structure.
- **Note on fundamentality** — O14 sits close to O3 + K1 $\times$ N. It is kept as a distinct pattern because the Forces it resolves (data sovereignty, per-corpus tuning, partition-as-access-boundary) are not the Forces O3 resolves (task specialisation), and because the "must not" rules differ in kind: O3 handlers can share data; O14 Owners cannot. The same logic that keeps K10 distinct from "K1 + write" keeps O14 distinct from "O3 + K1 $\times$ N". See §10 surface in the build report for the borderline call.

## Sources

- Renney, H., Nethercott, M. N., Renney, N., Hayes, P. (2026) — "LLM-Enabled Multi-Agent Systems: Empirical Evaluation and Insights into Emerging Design Patterns & Paradigms." arXiv 2601.03328. Names and evaluates the SIE pattern with case studies in telecoms security, national heritage asset management, and utilities customer service.
- LangGraph documentation — Multi-Agent Supervisor tutorial and `langgraph-supervisor-py` library reference.
- Databricks — Agent System Design Patterns (supervisor + domain-specialist agents).
- Modern Data 101 — "How AI Agents & Data Products Work Together to Support Cross-Domain Queries & Decisions for Businesses" — the data-product / data-mesh framing of the same pattern.
