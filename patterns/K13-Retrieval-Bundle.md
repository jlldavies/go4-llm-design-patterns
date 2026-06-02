# K13 — Retrieval Bundle

> Before writing any retrieval code for an agent workflow, explicitly specify the complete operational context bundle that workflow always needs — by field, by source, by data shape, by freshness requirement, and by authorization constraint — then build storage and assembly to deliver that bundle reliably.

**Also Known As:** Agent Operating Context, Workflow Context Specification, Typed Memory Contract, Pre-Compiled Context Bundle.

**Classification:** Category II — Knowledge · Band II-A Retrieval strategy · *design-time prerequisite* — K13 is the specification step that precedes K1, K3, K4, and the storage tier decisions in K10/K11/K12. It does not replace them; it tells you which ones to use for which fields.

---

## Intent

Define the exact bundle of operational context a specific agent workflow always needs — not "relevant documents" but precisely *these fields from these sources in these shapes* — and then build assembly to deliver that bundle reliably, rather than letting the agent reconstruct it dynamically from raw search results on every run.

## Motivation

**The rediscovery problem.** Classic RAG was designed for a chatbot era job: a user types a question, the system finds three semantically similar chunks, the model writes a paragraph. That loop works because the answer lives in a few paragraphs and the user asks once.

Agents do not ask questions and stop. They run tasks — open a ticket, check the policy, retrieve the customer record, draft the response. If an agent runs a customer escalation task, it needs the customer record, the applicable plan, the product version, the region, the purchase history, the refund policy, the refund threshold, any prior exceptions for this customer, the current ticket, the approved response language, and whether the agent is authorized to issue the refund or only draft a recommendation. That is not three semantically similar chunks. That is a typed operational bundle assembled from multiple sources.

Classic RAG leaves the agent to assemble that bundle on the fly from raw search results on every run. The consequence, measured at production scale, is severe: **rediscovery can consume up to 85% of agent compute** (PineCone, 2025). Agents refetch the same context every run. They re-summarize documents they summarized last time — correctly or not. They ask users for information the system already has. They blow the token budget before useful work begins.

**Why the rediscovery problem is architectural.** The model's weights do not persist knowledge between API calls (mechanism 10). The KV cache does not persist across sessions. Everything the agent assembled last time is gone unless it was written to external storage and re-loaded. An agent without a specified bundle has no stable definition of what it needs, so it improvises the assembly each time — paying the full cost of discovery on every run.

**Why larger context windows do not fix this.** A larger window gives the model more room to work. It does not decide what belongs in that room. It does not mark which source is authoritative. It does not enforce freshness. It does not distinguish what the agent confirmed from what it inferred. Filling a large window with the raw output of generic search — mixing authoritative, stale, and inferred content — causes **context rot**: the model cannot reliably determine which facts to weight, treats stale alongside current as equal, blends sources it should cite separately, and gives wrong emphasis. Performance degrades not because the right answer is absent but because it is not presented in a form the model can use reliably. This is mechanism 4 (lost-in-middle / U-shaped recall) compounded by provenance ambiguity: a fact buried in the middle of a long mixed-authority context is both statistically under-attended and untrustably attributed.

**Why the retrieval unit must match the data shape.** Vector search finds text that is semantically similar to the query. The learned bilinear form (mechanism 1) captures distributional co-occurrence: tokens that appear in similar contexts are nearby in the embedding space. This is effective for fuzzy prose where meaning lives in word choice and phrasing. It is systematically wrong for three other shapes:

- **Structured documents** (contracts, filings, regulatory documents): a clause can look semantically relevant while a definition 40 pages away completely changes its meaning. A schedule can overwrite a general term. The structure of the document — its section hierarchy, its cross-references, its schedules and annexes — carries meaning that chunking into embedding-sized fragments destroys. Vector search finds text that sounds right; it misses the legal or structural relationships that make it correct.

- **Governed tabular data** (ERP tables, CRM records, warehouse metrics, financial models): the source of truth for a revenue number is a governed metric definition tied to a specific table with specific lineage and access controls. Converting a table to prose and asking a language model to reason over it via semantic search is the wrong abstraction. The column relationships, row ordering, aggregation semantics, and data governance cannot be preserved in a vector embedding. Tabular data requires tabular-native retrieval.

- **Relational knowledge** (supplier-to-shipment connections, customer failure patterns, incident root causes): some knowledge is inherently relational — it lives in the edges between entities, not in the entities themselves. Graph-shaped data requires graph-native retrieval (K3 GraphRAG). Chunk retrieval cannot represent edges.

If you pick the wrong retrieval primitive for a given data shape, the model compensates at high context cost — spending tokens reconstructing structure that was available but lost, or inferring relationships that were stored but not retrieved. Better embeddings do not fix this. Higher-quality vector search still cannot retrieve document hierarchy, table semantics, or graph edges — it finds more relevant text. Better text is not the same as the right data shape.

## Applicability

Use Retrieval Bundle when:

- you are designing or debugging an agent that runs a specific, recurring workflow type (support, research, document review, financial analysis, procurement, compliance);
- the agent currently rebuilds context from scratch on every run, re-fetching or re-summarizing material it has assembled before;
- the agent's context window is filling with mixed-authority or mixed-freshness content that degrades output reliability;
- you are choosing between retrieval primitives and are not sure which to use — K13 is the prerequisite that answers that question.

Do not use it as a replacement for retrieval patterns:

- K13 is the specification step; K1, K3, K4, and the memory patterns (K10–K12) are the implementation. K13 tells you which of those to use for which fields; it does not replace them.
- For purely exploratory agents where the workflow varies entirely per run, a fixed bundle specification is not possible — use K5 Adaptive RAG to decide dynamically what to retrieve.
- For simple single-question systems, the overhead of bundle specification is not justified — K1 with good chunking is enough.

## Decision Criteria

K13 is right when the workflow type is stable, the agent has a defined task, and rediscovery is a measurable cost.

**1. Test for workflow type stability.** Can you write down, for a specific class of tasks this agent handles, the same list of information fields every run needs? If yes — this is a bundleable workflow. If the fields vary entirely per task with no common structure: K5 Adaptive RAG or dynamic assembly is more appropriate.

**2. Measure the rediscovery cost.** In your existing agent logs, count: how many retrieval calls happen before useful task work starts? How often does the agent read a source it read in a prior session? How often does it ask a user for something the system has? What fraction of your token budget is context assembly rather than task execution? If context assembly consumes > 30% of your token budget, rediscovery is your largest cost lever.

**3. Identify the data shapes.** For each field in the bundle, classify it:

| Shape | Characteristics | Retrieval primitive |
|---|---|---|
| **Fuzzy prose** | Meaning in word choice; no strict hierarchy; approx. match sufficient | K1 Vanilla RAG, K2 Query Transformation |
| **Structured document** | Meaning in section hierarchy, cross-references, schedules; chunking loses structure | K4 RAPTOR (hierarchical tree), document-tree approaches |
| **Governed tabular** | Business truth in tables, metrics, records; column/row semantics; access controls; lineage | Semantic layer + tabular-native retrieval; not vector search |
| **Relational** | Knowledge lives in edges between entities; dependency reasoning; pattern finding across connections | K3 GraphRAG, knowledge graph retrieval |

Most real agents need more than one shape. This is not a failure — it is the correct diagnosis. The error is assuming one primitive covers all shapes.

**4. Define freshness and authority per field.** For each bundle field, specify:
- **Source**: which system is authoritative (not merely relevant)?
- **Freshness**: how stale is too stale for this field? (customer status: real-time; policy text: daily; historical tickets: session-level)
- **Authorization**: is this agent permitted to see this field for this entity?
- **Missing-field behavior**: what should the agent do if this field cannot be retrieved?

A bundle with unspecified authority and freshness produces context rot. Specifying per-field makes the agent's behavior deterministic when sources disagree or are unavailable.

**5. Cost the assembly.** Pre-assembled bundles have a write cost (assembly call at task start or periodic refresh). Dynamic RAG has a per-run discovery cost. Compare: assembly_cost × assembly_frequency vs. rediscovery_cost × run_frequency. At high run frequency over stable data, pre-assembly wins materially.

## Structure

```
  DESIGN TIME (once per workflow type):
  ┌────────────────────────────────────────────────────────┐
  │  Bundle Specification                                  │
  │  ├── Field: customer_record                           │
  │  │   ├── source: CRM (tabular)                        │
  │  │   ├── freshness: real-time                         │
  │  │   ├── auth: agent role = support                   │
  │  │   └── if missing: halt, request human              │
  │  ├── Field: refund_policy                             │
  │  │   ├── source: policy corpus (structured doc)       │
  │  │   ├── freshness: daily                             │
  │  │   ├── auth: all agents                             │
  │  │   └── if missing: use default policy               │
  │  ├── Field: prior_tickets                             │
  │  │   ├── source: ticket system (relational)           │
  │  │   ├── freshness: session-level                     │
  │  │   └── if missing: proceed with empty history       │
  │  └── ...                                              │
  └────────────────────────────────────────────────────────┘
           │
           ▼
  Storage and retrieval primitives chosen by shape:
  tabular fields → semantic layer / governed table access
  structured doc fields → K4 RAPTOR tree index
  relational fields → K3 graph store
  prose fields → K1/K2 vector index

  RUN TIME (each agent task):
  ┌────────────────────────────────────────────────────────┐
  │  Bundle Assembler                                      │
  │  ├── fetch tabular fields from governed table          │
  │  ├── retrieve structured doc sections via K4          │
  │  ├── retrieve graph neighborhood via K3               │
  │  └── retrieve prose via K1/K2                         │
  └────────────────────────────────────────────────────────┘
           │
           ▼ compact, typed, authoritative bundle
  ┌────────────────────────────────────────────────────────┐
  │  Agent context window                                  │
  │  [bundle — small, high-signal, authoritative]         │
  │  [task instructions]                                   │
  └────────────────────────────────────────────────────────┘
           │
           ▼
  Task execution (no rediscovery)
```

The structural invariant: the agent's context contains the bundle (assembled once, authoritative, correctly shaped) and the task instructions. It does not contain raw search results, re-derived summaries, or content the agent has to evaluate for relevance and authority.

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Bundle specification** (a design artifact, not code) | the exact definition of what this workflow type always needs: fields, sources, shapes, freshness, auth, missing behavior | — | be implicit. An unspecified bundle is indistinguishable from "let the agent figure it out," which is the rediscovery pattern. |
| **Bundle assembler** (code) | assembling the bundle from its constituent sources at task start | task entity ID + bundle spec → assembled bundle | retrieve more than the spec requires. Every token added to context costs O(n²) attention compute (mechanism 2). The assembler's job is to be complete and precise, not comprehensive. |
| **Shape-appropriate retrieval primitives** (one or more, chosen per field type) | delivering each field in the right shape | field spec → field value | substitute a different shape. Retrieving a governed metric via vector search, or a contract section via raw text grep, are shape mismatches that produce wrong or unreliable answers regardless of retrieval quality. |
| **Authority and freshness enforcer** (code) | validating each retrieved field against its spec before injecting into context | raw retrieval results → validated, labeled bundle fields | pass unlabeled content. The agent must know which fields are authoritative (the governed table, the current policy) vs. contextual (prior tickets, historical examples). Mixing them unlabeled produces context rot. |
| **Missing-field handler** (code or policy) | deciding what to do when a required field cannot be retrieved | retrieval failure → halt / substitute / flag | silently omit. A missing required field should be an explicit signal (halt for authorization failures, substitute for optional fields, flag for degraded mode). Silent omission produces a partially-assembled bundle the agent treats as complete. |

## Collaborations

At design time, the engineer writes the bundle specification for each workflow type. This drives all subsequent infrastructure choices: which retrieval primitives are needed, which storage tiers are required, which authorization systems must be integrated.

At run time, the Bundle Assembler fires at task start, collecting each field via its specified primitive. The assembled bundle is injected into the agent's context window as a compact, typed, authoritative unit — before any task reasoning begins. The agent then executes its task against the bundle without further retrieval calls (for the specified fields).

For fields with high freshness requirements (real-time customer status), the Assembler retrieves fresh on every run. For fields that are stable across many runs (policy text, product definitions), the Assembler checks a local cache or uses K9 Long Context with prefix caching (mechanism 5) to amortize the retrieval cost.

When a task discovers it needs a field not in the bundle specification, that discovery is a signal to update the specification — not to add ad-hoc retrieval inside the task logic. Ad-hoc retrieval inside the task is the rediscovery pattern re-entering through the back door.

## Consequences

**Benefits**

- Eliminates rediscovery: the agent receives its complete operating context at task start, assembled once, from authoritative sources. No per-run re-fetching, re-summarizing, or user re-questioning.
- Eliminates context rot: each field is labeled with its source and freshness; the agent knows what is authoritative and what is contextual.
- Shape-correct retrieval: each field is delivered by the primitive appropriate for its data shape, not approximated by the nearest available primitive.
- Predictable, auditable agent behavior: the bundle specification is an explicit contract; every agent run against the same entity with the same specification produces the same input structure.
- Token efficiency: a pre-assembled, compact bundle is smaller and higher-signal than the raw search results the agent would otherwise assemble dynamically. Less context waste = more attention budget for task reasoning (mechanisms 2, 6).

**Costs**

- Design-time investment: the bundle specification must be written explicitly for each workflow type. This requires understanding the data landscape before writing retrieval code.
- Multiple primitives: most real bundles need more than one retrieval primitive. This means more infrastructure components to maintain.
- Specification drift: as the workflow evolves, the bundle spec must be kept current. An outdated spec produces a bundle that no longer matches the workflow's actual information needs.
- Assembly latency: collecting fields from multiple systems adds task startup latency vs. a single search call.

**Risks and failure modes**

- *Vendor-first design* — picking a database before writing the bundle spec constrains the agent to the database's shape strengths. The database becomes the frame that defines what the agent can retrieve, rather than the agent's information needs defining what database to use.
- *Ad-hoc bundle expansion* — engineers add retrieval calls inside task logic when they notice missing context, rather than updating the spec. The bundle silently diverges from the specification. Eventually every run has ad-hoc retrieval and rediscovery re-enters through the task code.
- *Authority ambiguity* — bundle includes fields without source labeling; the agent blends a governed metric with a retrieved paragraph and cannot distinguish which is authoritative. Context rot.
- *Shape mismatch* — using vector search for structured documents (finds relevant-sounding clauses, misses controlling definitions 40 pages away) or tabular data (approximates numeric relationships as semantic similarity). The error is systematic, not random — it consistently misses the structurally important content.
- *Stale bundle cache* — pre-compiled bundles for high-freshness fields cached past their TTL. Agent reasons from stale customer status or expired policy. Freshness enforcement must be per-field, not per-bundle.
- *Over-engineering* — building graph + document tree + semantic layer + vector search + tabular model for a simple FAQ agent. K13 is a diagnostic tool; the output of the specification is often "K1 is enough for this workflow."

## Implementation Notes

- **Write the bundle spec as a schema, not prose.** Each field should be a row: name, source, data shape, freshness TTL, authorization rule, missing-field behavior. A prose description of what the agent needs is not a specification.
- **Start from the failure logs.** The pattern is in your existing agent runs: how many retrieval calls before useful work starts? How often is the agent re-reading the same sources? How many user clarification requests are for information the system has? These numbers tell you the size of the rediscovery problem before you commit to an architecture.
- **Match shape before optimizing retrieval quality.** A well-tuned vector search over a contract corpus will still miss the controlling schedule. Fix the shape match first; optimize retrieval quality second.
- **Mark the authority boundary explicitly in the bundle.** Each field in the context should carry metadata: authoritative (the governed metric, the current policy) vs. contextual (prior agent runs, historical examples, background reference). The agent's system prompt should include a rule: "rely on authoritative fields for task decisions; use contextual fields for background only."
- **Version the bundle spec alongside the agent.** When the workflow requirements change, update the spec and the assembly in the same change. Spec and implementation that drift apart produce the rediscovery pattern.
- **Use prefix caching for stable fields (mechanism 5).** Bundle fields that are stable across many runs within a session (policy text, product definitions, authorization rules) can be placed in the stable prefix and cached. Variable fields (the specific customer record, the current ticket) come after the cache boundary. This is K13 composing with O18 (Cache-Warmed Worker Pool) for batched workflows.

## Implementation Sketch

**Design-time: write the bundle specification**

```
workflow_type: customer_escalation

fields:
  - name: customer_record
    source: CRM (governed table)
    shape: tabular
    retrieval: semantic_layer.get_customer(entity_id)
    freshness_ttl: 0  # real-time, always fresh
    auth: role IN [support, supervisor]
    if_missing: halt → "customer record required"

  - name: applicable_plan
    source: product catalogue (governed table)
    shape: tabular
    retrieval: semantic_layer.get_plan(customer.plan_id)
    freshness_ttl: 86400  # daily
    auth: role IN [support, supervisor, agent]
    if_missing: substitute with default_plan

  - name: refund_policy
    source: policy corpus (structured document)
    shape: structured_doc
    retrieval: raptor_index.get_section("refund", customer.region)
    freshness_ttl: 86400
    auth: all
    if_missing: substitute with global_policy

  - name: prior_tickets
    source: ticketing system (relational)
    shape: relational
    retrieval: graph.get_customer_history(entity_id, limit=5)
    freshness_ttl: 3600
    auth: role IN [support, supervisor]
    if_missing: proceed with empty history

  - name: approved_response_language
    source: response template corpus (prose)
    shape: prose
    retrieval: vector_index.retrieve(query=task.issue_type, k=3)
    freshness_ttl: 86400
    auth: all
    if_missing: use unconstrained language with V1 approval gate
```

**Run-time: assembly and injection**

| # | Step | Kind | Notes |
|---|---|---|---|
| 1 | Receive task entity ID and workflow type | `code` | |
| 2 | Load bundle spec for workflow type | `code` | Versioned; checked into source control |
| 3 | For each field: retrieve via specified primitive | `code` | Shape-appropriate primitive per field |
| 4 | Validate each field: freshness, authorization, completeness | `code` | Per-field, not per-bundle |
| 5 | Handle missing fields per spec | `code` | Halt / substitute / flag — never silent omit |
| 6 | Label each field with authority metadata | `code` | authoritative / contextual / inferred |
| 7 | Assemble into compact structured bundle | `code` | JSON or structured markdown; not raw prose dump |
| 8 | Inject bundle into agent context (stable fields first for caching) | `code` | Mechanism 5: stable fields in cacheable prefix |
| 9 | Agent executes task against bundle | `LLM` | No further ad-hoc retrieval for specified fields |

## Known Uses

- **Customer support and escalation agents** (Intercom, Zendesk AI integrations): pre-assembled customer bundles containing customer record, plan, history, and policy — reducing agent startup time from multi-second retrieval chains to sub-second assembly from warmed stores.
- **Enterprise financial analysis agents** (investment banks, asset managers): pre-compiled bundles with governed metric definitions, filing sections (hierarchical tree), and relationship maps of entity ownership — rather than vector search over mixed filing corpora.
- **Legal review agents** (contract analysis): bundles with the specific contract (structured document tree retrieval), the governing law jurisdiction policy, and the definition schedule — ensuring the model reasons from structure, not semantic similarity.
- **Procurement and supply chain agents**: bundles with supplier records (tabular), supplier-to-component graphs (relational), and risk policy (structured document) — assembled from three shape-appropriate sources before any reasoning step.
- **PineCone Nexus / NoQL (2025)**: PineCone's explicit reorientation from "retrieve similar chunks" to "deliver operating context bundles with intent, filters, access policy, provenance, and response shape" reflects independent industry convergence on this pattern.

## Related Patterns

- **Prerequisite for** K1 Vanilla RAG, K3 GraphRAG, K4 RAPTOR, K10 Long-Term Memory, K11 Observational Memory — K13 is the specification that tells you which of these to use for which fields. It does not replace them.
- **Distinct from K12 Karpathy Memory** — K12 is an LLM-curated knowledge base that persists across sessions as structured notes. K13 is the specification of what context a workflow type always needs at task start. They compose: K12 can supply the "curated agent knowledge" field in a bundle; K13 specifies that field alongside all others.
- **Distinct from K5 Adaptive RAG** — K5 decides dynamically what to retrieve. K13 specifies in advance what a workflow type always needs. K13 is right for recurring workflows with stable information requirements; K5 is right for exploratory workflows with unpredictable information needs.
- **Composes with O18 Cache-Warmed Worker Pool** — stable bundle fields (policy, definitions, product catalogue) are ideal cacheable prefix candidates. K13 + O18 makes batched workflow execution economical: assemble bundle once, fire N task workers within the cache TTL.
- **Composes with K9 Long Context** — for workflows where the entire stable reference corpus is small enough to fit in the window and queries are repeated many times per session, K9 + prefix caching can serve as the stable-fields tier of the bundle (mechanism 5).
- **Addresses** the "context rot" failure mode described by Chroma research — a bundle with per-field authority labeling and freshness enforcement prevents the mixed-authority, mixed-freshness context that causes rot.
- **Named by** the "rediscovery problem" (PineCone, 2025) — the observation that up to 85% of agent compute can be consumed by agents re-assembling context they have assembled before.

## Sources

- PineCone (2025) — Nexus launch and NoQL query language. "Agents need operating context, not related text." Rediscovery figure: up to 85% of agent compute on context re-assembly. pinecone.io/blog/nexus.
- PageIndex (2025) — Document tree approach for structured documents. "The retrieval unit must match the work you're doing." financebench accuracy results on hierarchical retrieval.
- SAP (2025) — Dremio acquisition (lakehouse + semantic layer + governed access) and Prior Labs acquisition (tabular foundation models). Articulation of the tabular data shape as requiring tabular-native reasoning.
- Microsoft (2024) — GraphRAG. Relational knowledge retrieval for entity-relationship reasoning. Distinct from prose RAG as a data shape.
- Chroma (2025) — Context rot research. Model performance degradation as context grows more cluttered with mixed-authority content.
- Mechanism 1 (Chapter 0 §0.1) — Bilinear form explains why vector search captures distributional similarity but not document structure, table semantics, or graph edges.
- Mechanism 2 (Chapter 0 §0.1) — n² attention cost; pre-assembled compact bundle vs. dynamic assembly.
- Mechanism 4 (Chapter 0 §0.1) — Lost-in-middle / U-shaped recall; context rot as compound failure.
- Mechanism 9 (Chapter 0 §0.2) — Storage hierarchy; each bundle field maps to a storage tier.
- Mechanism 10 (Chapter 0 §0.2) — No cross-session persistence; mechanical basis of the rediscovery problem.
