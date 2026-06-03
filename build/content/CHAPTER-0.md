# The Mechanical Foundation

> *The patterns in this catalog are not heuristics layered over a black box. Each one is grounded in the mechanical behavior of the transformer at inference time. This chapter establishes that mechanical foundation at the level of precision the patterns require. A reader who internalizes it can derive most of the catalog's recommendations from first principles rather than accepting them on authority.*

---

## Why This Chapter Exists

This chapter derives twelve mechanistic principles from how transformers actually compute — from the attention bilinear form and KV cache structure through to prefix caching economics and subagent context bounding. It is a derivation resource: when a pattern entry cites a mechanism (for example, *mechanism 2 — n² compute cost*), this is where that citation resolves. You do not need to read this chapter to use the catalog. Read it when you want to understand why a pattern's costs are what they are, not just that they are.

Mechanism citations in pattern files take the form **"(mechanism N)"**. That notation refers to the numbered sections below. A reader who needs the derivation for any cited mechanism should find it here.

---

## 0.0 — How a Language Model Computes

The mechanisms in this chapter are precise. Before the formalism, here is the conceptual model they build on — structured so that the mathematical objects introduced in Mechanisms 1 through 3 are immediately recognisable when they appear.

**Tokens.** A language model does not read words. It reads *tokens* — byte-pair encoded substrings that tile any input text. One token is roughly three-quarters of a word in English, though the ratio varies by content type. "context" is one token; "contextualisation" may be three. Every count in this chapter — context window size, KV cache size, input cost — is a token count, not a word count. When a model's context window is 200,000 tokens, that is roughly 150,000 words.

**The context window.** At inference time, the model sees a fixed sequence of tokens: your system prompt, any prior turns, your current message, any retrieved documents. This sequence is the *context*. Every token has a position, and position matters — the model has learned structural priors from training (instructions near the start, user query near the end). The model is stateless between calls: it has no memory of previous requests. The context window is the totality of what it knows for one call.

**Token embeddings.** Each token at position $i$ is immediately converted to a vector of real numbers: $e_i \in \mathbb{R}^{d_\text{model}}$. This is the *embedding* — a list of $d_\text{model}$ floating-point values that encodes the token's identity and its position in context. In current models $d_\text{model}$ is typically 768 to 8,192. All computation in the model — every addition, multiplication, and comparison — operates exclusively on these embedding vectors. A token never appears as a string inside the model; it is always a point in a $d_\text{model}$-dimensional vector space.

**Weight matrices and projections.** The model does not compare token embeddings directly. At each attention head, three learned weight matrices — $W_Q$, $W_K$, $W_V \in \mathbb{R}^{d_\text{head} \times d_\text{model}}$ — project embeddings into smaller spaces purpose-built for comparison. Multiplying an embedding by $W_Q$ produces a *query vector* $Q_i = W_Q e_i \in \mathbb{R}^{d_\text{head}}$; multiplying by $W_K$ produces a *key vector* $K_j = W_K e_j$. These matrices are learned: training discovers which linear transformations make useful comparisons for the tasks the model is trained on. The weight matrices are fixed after training; only the embeddings they are applied to change at inference time.

**The attention score as a bilinear form.** Each attention head computes a scalar score $s_{ij}$ — how much token $i$ should attend to token $j$. The natural measure of alignment between two vectors is a *dot product*: $s_{ij} = Q_i \cdot K_j = \sum_\alpha Q_i^\alpha K_j^\alpha$, where $\alpha$ indexes the $d_\text{head}$ components. This is a *bilinear form* — a function that takes two vectors and returns a scalar, linear in each argument. The standard dot product is the special case where all directions in space are treated equally. A general bilinear form $B(u,v) = \sum_{\mu\nu} u^\mu M_{\mu\nu} v^\nu$ uses a matrix $M$ to define *which* directions matter and *how much*, establishing a geometry on the space. The full attention score — traced back through both projections to the original embeddings $e_i$ and $e_j$ — is exactly such a bilinear form, with the matrix $M = W_Q W_K^T$. Mechanism 1 derives this in full. The matrix is called the *effective metric tensor* $g_{\mu\nu}$, and it is this matrix — not the Euclidean metric — that determines what the model considers "similar." Each of the $H$ heads at each of the $L$ layers defines a different $g_{\mu\nu}$; there are $H \times L$ distinct learned geometries operating simultaneously.

**Tensors and index notation.** A *tensor* is a multi-dimensional array; a vector $v \in \mathbb{R}^n$ is a rank-1 tensor (one index), a matrix $M \in \mathbb{R}^{m \times n}$ is a rank-2 tensor (two indices). The KV cache is a rank-4 tensor of shape $L \times n \times n_\text{kv} \times d_\text{head}$ (layers $\times$ sequence positions $\times$ KV heads $\times$ head dimension). In the mechanism derivations, expressions like $g_{\mu\nu}$ name a rank-2 tensor by its indices; a repeated index appearing once as a subscript and once as a superscript (as in $Q_\alpha K^\alpha$) means sum over that index — this is *Einstein summation notation*. $Q_\alpha K^\alpha$ is therefore $\sum_\alpha Q_\alpha K^\alpha$, the dot product written compactly. The covector/vector distinction ($Q_\alpha$ vs $K^\alpha$) tracks which space each lives in; for the practical consequences of this chapter, what matters is that a repeated paired index is always a sum, and the result is a scalar.

**A forward pass.** When you send a prompt, the model runs a single forward pass over all input token embeddings simultaneously. At each layer, each attention head computes query, key, and value projections for every position; scores every token pair with the bilinear form; softmax-normalises the scores; and produces a weighted sum of value vectors. The result feeds the next layer. The final layer's output is a probability distribution over the vocabulary; one token is sampled and appended to the sequence. Generation is a loop of single-token predictions, each conditioned on everything before it.

**The KV cache.** Running a full forward pass over the growing sequence on every step would be prohibitively slow — by step 500, you would recompute attention over 500 tokens 500 times. Each layer avoids this by caching the *key* and *value* vectors it computed for prior tokens. On the next step, only the new token needs fresh computation; the cached K and V vectors for all prior tokens are reused. This is the KV cache. It grows monotonically — one entry per layer per token, never removed or reordered — which is why its structure appears in the cost reasoning for almost every pattern in this catalog.

**The n² intuition.** During the initial *prefill* — processing all input tokens before generation begins — the model computes the attention score between every pair of tokens. A prompt twice as long has four times as many pairs: prefill cost scales with the square of sequence length. A 2,000-token prompt costs four times as much to prefill as a 1,000-token prompt. A 4,000-token prompt costs sixteen times as much. Engineers who model token costs as linear are systematically underestimating the cost of long contexts. This quadratic relationship is the mechanical basis for the entire Knowledge category and for the subagent isolation imperative in Orchestration patterns.

---

## 0.1 — The Inference Primitives (Mechanisms 1–7)

### M1 — Attention as a Learned Bilinear Form  {#m1}

#### Grade A
*The bilinear form is algebraically derived from the QK^T computation; the result follows from the matrix operations and requires no empirical inference.*

At each attention head, the core computation contracts a query against a key. Writing the query as $Q_\alpha \in \mathbb{R}^{d_\text{head}}$ (naturally a covector — a linear functional acting on the key space) and the key as $K^\alpha \in \mathbb{R}^{d_\text{head}}$ (a vector), the raw attention score is:

$$s = Q_\alpha K^\alpha$$

When both Q and K are represented as elements of $\mathbb{R}^{d_\text{head}}$ with the Euclidean metric $\delta_{\alpha\beta}$ providing an implicit identification of tangent and cotangent spaces, the contraction becomes the familiar dot product. But the weight matrices $W_Q$ and $W_K$ project from the same token embedding into Q-space and K-space via different learned maps. The full attention bilinear form in token-embedding space $\mathbb{R}^{d_\text{model}}$ is therefore:

$$Q_i^\alpha K_{j\alpha} = e_i^\mu\,(W_Q)_\mu^{\;\alpha}\,\delta_{\alpha\beta}\,(W_K^T)^\beta_{\;\nu}\,e_j^\nu = e_i^\mu\,g_{\mu\nu}\,e_j^\nu$$

where the **effective metric tensor** on embedding space is:

$$g_{\mu\nu} = (W_Q W_K^T)_{\mu\nu}$$

This is a learned non-symmetric $(0,2)$ tensor on $d_\text{model}$-space. It is not a Riemannian metric — it is neither symmetric nor positive-definite — but it plays the structural role of one: it defines what constitutes similarity between token embeddings at each head. Because $W_Q \neq W_K$, this similarity is directional: $s(e_i \to e_j) \neq s(e_j \to e_i)$. The query attends to the key; the reverse is not the same operation.

Every head defines a different $g_{\mu\nu}$. Multi-head attention runs $H$ such bilinear forms in parallel, each carving out a different learned notion of token relevance. There is no single Euclidean geometry on the embedding space; there are $H \times L$ distinct learned geometries (one per head per layer).

**Practical consequence:** What a model attends to is not Euclidean distance in embedding space — it is a head-specific, layer-specific, learned asymmetric structure. "Semantic similarity" is shorthand for proximity under this learned metric, which is why the same two tokens can be similar under one head and dissimilar under another.

**What this grounds:** K-series retrieval pattern rationale (why embedding-space retrieval is head-specific); S2 few-shot ordering; K1 hybrid retrieval; the entire rationale for why prompt phrasing affects attention routing.

---

### M2 — n² Compute and KV Cache Memory Cost  {#m2}

#### Grade A
*Quadratic scaling of the attention matrix is an algebraic consequence of computing pairwise token interactions; the cost bound is exact.*

The attention matrix $QK^T \in \mathbb{R}^{n \times n}$ (where $n$ = sequence length) is computed at every layer for every head. The compute cost of prefill — processing all $n$ input tokens in one forward pass — is $O(n^2 d_\text{model})$ in FLOPs. Doubling the context quadruples the prefill cost.

Token generation (the decode phase) is structurally different. At each step, only one new Q vector is computed; it is contracted against all $n$ cached K vectors. This is a matrix-vector product (not matrix-matrix), and is bounded by **memory bandwidth**, not FLOP count. The bottleneck is reading the KV cache from DRAM, not computing the attention. Generation latency scales with $n$, not $n^2$, but is dominated by memory bandwidth to the KV cache rather than arithmetic throughput.

**The n² compounding is non-linear in cost.** Adding 100 tokens to a 1,000-token prompt costs more than adding 100 tokens to a 100-token prompt — not proportionally more, but quadratically more in prefill attention compute. Practitioners who model token costs as linear are systematically underestimating the cost of long prompts.

**What this grounds:** Every pattern rationale that mentions "token cost," "context budget," or "sequence length limit." The n² fact is the mechanical basis for the entire K-series (context engineering) and for the subagent decomposition imperative in O-series patterns.

---

### M3 — The KV Cache as a Growing 4D Tensor  {#m3}

#### Grade A
*Cache structure and monotonic growth follow directly from causal masking applied to autoregressive decoding; the tensor shape is exact.*

The key-value cache at inference time is a 4-dimensional tensor of shape:

$$\mathcal{C} \in \mathbb{R}^{L \times n \times n_\text{kv} \times d_\text{head}}$$

where $L$ = number of layers, $n$ = tokens in context, $n_\text{kv}$ = number of KV heads (with grouped-query attention, $n_\text{kv} < n_\text{heads}$), and $d_\text{head}$ = head dimension. The cache grows monotonically during a session — tokens are appended, never removed or reordered. Causal masking makes the attention matrix lower-triangular: token $i$ can only attend to tokens $j \leq i$.

At generation step $t$, the model computes a new Q for position $t$ and contrasts it against all $n+t-1$ cached K vectors across all $L$ layers. This is the full similarity search described under Mechanism 1, executed against the entire history on every generation step.

**Memory cost per token:** approximately $2 \times L \times n_\text{kv} \times d_\text{head} \times \text{bytes\_per\_float}$. For a 70B-class model with GQA: $\approx 2 \times 80 \times 8 \times 128 \times 2 \approx 327$KB per token in context. A 100k-token context requires roughly 32GB of KV cache.

**The KV cache does not persist across API calls.** Each new call to the Anthropic Messages API starts with a fresh KV cache. The only persistence mechanism is re-sending tokens (re-prefill) or using provider-side prefix caching (Mechanism 5). This is the architectural fact that makes all H-series (Humanizer) "memory" patterns file-retrieval operations, not model-state operations.

**What this grounds:** All H-series memory patterns; K8 Working Memory; K9 Long Context; the cost model for all O-series multi-agent patterns; V10 Checkpointing.

---

### M4 — Lost-in-the-Middle as Q-K Space Geometry  {#m4}

#### Grade B — empirically strong, partially derived
*The U-shaped attention weight distribution is robustly observed across models and tasks, but the geometric account is a partial derivation rather than a closed-form proof.*

Liu et al. (2024) documented a U-shaped recall curve over sequence position: recall is strong at the start and end of the context window, materially weaker for content placed in the middle. This is not an arbitrary empirical finding — it has a mechanical substrate, though the substrate is not fully derivable from first principles (hence Grade B).

The Q and K projection matrices $W_Q$ and $W_K$ were trained on natural text. Natural text has strong local dependencies (adjacent and nearby tokens are semantically related) and strong document-boundary conventions (opening sentences state the topic; closing sentences summarize it). The learned projection matrices therefore embed a **recency bias** (small $i-j$ offsets produce stronger Q-K inner products — see Mechanism 12 on RoPE) and a **start-of-context anchoring** (opening position K vectors are densely attended in natural text and the model internalized this pattern).

Middle K vectors are geometrically accessible — the attention computation can reach them — but statistically under-attended because the learned $W_Q$ and $W_K$ do not amplify those positions. The failure mode is not attention blindness; it is low attention weight mass assigned to middle positions relative to start and end.

**Practical consequence:** Content placed in the middle of a long context is systematically less likely to influence the output than the same content placed at the start or end. This is a physical property of the Q-K geometry, not a soft preference. Pattern recommendations to "place critical content at the start or end" are derivable from this mechanism.

**What this grounds:** K1, K6, K7, K9, K10, K11 rationale for context placement; S3 Persona placement advice; V6 Prompt Injection Shield defense rationale.

---

### M5 — Prefix Caching as Cache Engineering  {#m5}

#### Grade A mechanism; Grade B operational specifics
*That caching prefix KV states reduces recomputation follows directly from M2 and M3; the TTL durations and hit-rate figures cited are provider-specific and subject to change.*

Provider-level prefix caching stores the KV cache state (Mechanism 3) for a stable prompt prefix. When a subsequent request sends the same prefix — identical tokens, same byte offsets — the provider injects the stored KV states directly into the generation step, bypassing prefill entirely. The savings follow from Mechanism 2: the $O(n^2)$ prefill cost for the cached prefix is not paid on cache hits.

**Anthropic operational specifics (as of 2026):**
- Minimum cacheable prefix: 1,024 tokens
- Cache TTL: approximately 5 minutes
- Cache write cost: approximately 125% of normal input token cost (a one-time overhead)
- Cache read cost: approximately 10% of normal input token cost
- Net saving on cache hit: approximately 90% of the prefill cost for the cached prefix

**The cache key is the exact token sequence.** A single token difference anywhere in the prefix — a changed word, a reordered sentence, a different whitespace character — invalidates the cache for that position and all subsequent positions. Cache hit requires byte-identical prefix.

**Design implication:** Prompt engineering is cache engineering. System prompts, tool definitions, persona statements, fixed few-shot examples — any content that is stable across requests — should be structured as the **longest possible stable prefix**, placed before any variable content. Variable content (the user's query, dynamic context) comes last. Every edit to the stable prefix resets the cache write cost.

For multi-agent systems (Mechanism 6), the shared context given to all workers should be designed as a single cacheable prefix exceeding the minimum threshold. All workers should be dispatched within the TTL window so they share the cache write paid by whichever worker fires first.

**What this grounds:** S2 Few-Shot static vs dynamic variant cost difference; S3 Persona placement; H1 Identity Persistence operational discipline; K9 Long Context session economics; the new O18 Cache-Warmed Worker Pool pattern.

---

### M6 — Subagent Decomposition as Context Bounding  {#m6}

#### Grade A
*The cost reduction from independent context windows is a direct arithmetic consequence of n² scaling; the calculation is exact given the quadratic bound from M2.*

Each spawned subagent has its own KV cache, its own sequence length $n$, and its own $O(n^2)$ attention compute budget. This is not a logical property of multi-agent architecture — it is a physical property of how the inference computation is partitioned across API calls.

In a single-agent system handling a complex task, $n$ grows as the agent accumulates tool outputs, intermediate reasoning, and conversation history. The n² attention cost grows with every turn. In a multi-agent system:

- The orchestrator maintains a compact context: task assignments and returned results only.
- Each worker maintains a focused context: its brief, its tools, and its internal reasoning — which is discarded after the worker returns its result.
- The orchestrator's $n$ grows slowly (one compact result per worker, not the full internal trajectory).
- Each worker's $n$ is bounded by the scope of its single sub-task.

The quality win of O6 Orchestrator-Workers over O1 Single Agent is structural, not emergent. Separation of orchestration context from execution context bounds the n² cost per agent and keeps each agent in the regime where its Q-K attention weights are well-distributed over a small, high-signal context rather than diluted over a large, mixed context (Mechanism 4).

**What this grounds:** O4 Parallelization; O6 Orchestrator-Workers; O7 Supervisor Hierarchy; O17 Agent Isolation; the mechanical rationale for why O6 + O17 is mandatory, not optional.

---

### M7 — Stochastic Generation and Autoregressive Commitment  {#m7}

#### Grade A
*Sampling from the output distribution is the defined mechanism of autoregressive generation; the irreversibility of committed tokens is a structural property, not an empirical finding.*

Token generation is sampling from a learned probability distribution over the vocabulary. Given the sequence of tokens $t_1, t_2, \ldots, t_{k-1}$, the model outputs a distribution $P(t_k \mid t_1, \ldots, t_{k-1})$ and samples the next token from it. Generation is **autoregressive**: each sampled token becomes part of the conditioning sequence for the next token.

Two consequences are mechanically unavoidable:

1. **No revision.** Once token $t_k$ is sampled and appended, all subsequent tokens are conditioned on it. The model does not revise $t_k$ — it elaborates on it. A reasoning chain that commits to a wrong intermediate conclusion conditions all subsequent tokens on that conclusion. This is the mechanical basis of **sycophantic reasoning** in chain-of-thought patterns: the model produces tokens that extend the most probable continuation of what it has already emitted, not the most correct answer to the original question.

2. **Determinism requires external enforcement.** Token generation cannot be made deterministic by prompt instruction alone. Routing the same computation to a deterministic system (a tool, a code executor, a database lookup) is the only way to eliminate sampling variance. This is the mechanical basis for the "use tools, not the model" discipline in I-series and V-series patterns.

**What this grounds:** Every R-series reasoning pattern rationale; the determinism argument in I2 Function Call, I3 MCP, R13 CodeAct, R14 Program of Thoughts; V-series reliability patterns that use deterministic enforcement; H6 Inner Monologue caveats.

---

## 0.2 — The Memory and Storage Hierarchy (Mechanisms 8–10)

### M8 — Model Size Matching to Task Complexity  {#m8}

#### Grade A cost; Grade B thresholds
*That smaller models are cheaper per token follows from parameter counts; the capability thresholds at which model tiers are interchangeable are empirical and task-dependent.*

Large model capacity (parameter count) is required for complex, multi-step reasoning that integrates many latent factors. It is not required for routing, classification, format conversion, exact lookup, data loading, or other tasks that require recall and pattern-matching rather than reasoning. The generation cost for the same token count scales with model size; using a 70B-parameter model for a routing decision costs an order of magnitude more in memory bandwidth and FLOPs than a 7B model for the same decision.

Correct multi-agent architecture assigns model capacity to reasoning complexity:
- Orchestrators (which must reason about task decomposition and synthesis): strongest available model.
- Workers handling complex sub-tasks: mid-tier models.
- Workers handling simple lookup/classification: small, fast models.

This is not a preference — it is a cost-structure fact. The practical thresholds for when a task is "complex enough" to require a large model are empirical (hence Grade B on thresholds), but the direction of the principle is Grade A.

**What this grounds:** O3 Routing model selection; O6 Orchestrator model assignment (strongest orchestrator, lighter workers); I2 Function Call schema routing; V4 Dual LLM size assignment.

---

### M9 — Storage Tier Hierarchy  {#m9}

#### Grade A cost structure; Grade B use patterns
*The cost and latency ordering of in-context, retrieval, and fine-tuning tiers follows from their computational structure; which tier is optimal for a given access pattern is empirically determined.*

The KV cache does not persist across API calls (Mechanism 3). All information that must survive a session boundary must be written to external storage and retrieved into context. This creates a hierarchy of storage tiers with distinct cost and access properties:

| Tier | Per-token read cost | Capacity | Appropriate content |
|---|---|---|---|
| **In-context** | $O(n^2)$ attention compute per token present | Session-bounded by context window | Current task working set only — discard after use |
| **Prefix cache** | ~10% of normal input cost on hit | Provider TTL ~5 min (Anthropic) | Stable system prompts, tool schemas, fixed examples |
| **Vector index** | Retrieval quality-bounded | Unbounded | Semantic document retrieval; variable-key lookup |
| **Exact KV store** | Deterministic, low-latency | Unbounded | Config, code artifacts, known-key facts |
| **Cold storage** | High latency | Unbounded | Source of truth, archival, infrequent access |

The critical design axis is **write cost vs. read cost**. In-context storage pays zero write cost (no curation step) but pays $O(n^2)$ on every read (every turn). External storage pays a write cost (a curation LLM call to extract and structure the information) but pays near-zero read cost per token retrieved (only the retrieved chunk enters context). The correct tier for a given piece of information depends on how often it is needed, how stable it is, and how tolerant the task is of retrieval errors.

**Common error:** placing in context what belongs in an exact KV store. A 500-token configuration block that never changes costs $O(n^2)$ attention compute on every turn of every session. Externalising it and retrieving it once costs a small retrieval call. The prefix cache (Mechanism 5) is the middle tier: stable, zero-marginal-cost on hit, but TTL-bounded and minimum-size-gated.

**What this grounds:** K-series memory patterns (K8 Working Memory, K10 Long-Term Memory, K11 Observational Memory, K12 Karpathy Memory); H-series session management; I-series tool result handling.

---

### M10 — No Cross-Session Persistence: All Memory Is Retrieval  {#m10}

#### Grade A
*LLM weights are fixed at inference time; the absence of cross-session state change is a definitional property of the inference API contract, not an empirical observation.*

The model's weights do not change between API calls. There is no mechanism by which a conversation causes the model to "learn" or "remember" anything in its parameters. The KV cache is session-scoped (Mechanism 3) and does not persist across calls.

All apparent inter-session memory is a file-retrieval operation: a document (CLAUDE.md, MEMORY.md, a skills file, a retrieved database record) is read into the context at the start of the new session. The model then conditions on the retrieved content as part of its input. The "memory" is the quality and completeness of the retrieved artefact, not a model capability.

**The compounding of "skills" and "memory" over sessions is entirely a function of retrieval quality.** A skill that "gets smarter over time" does so because the skill file was updated with better instructions, not because the model updated its weights. A memory system that degrades over time does so because retrieved content has become stale or irrelevant, not because the model "forgot." The design lever is the write discipline of the external store and the retrieval quality of the search — not the model itself.

**What this grounds:** All H-series patterns; K10/K11/K12 design rationale; the widely-held but incorrect folk-claim that "skills compound across sessions" (they do not — all compounding is in the retrieved files, not the model weights).

---

## 0.3 — The Positional Architecture (Mechanisms 11–12)

### M11 — Context Compaction for Long-Running Systems  {#m11}

#### Grade A mechanism; Grade B trigger thresholds
*That accumulated context must eventually be managed follows from finite window size and quadratic cost; the optimal compaction trigger depends on workload characteristics that are not derivable from first principles.*

In a long-running agent session (an O8 Loop Agent, or any agentic workflow with many turns), the KV cache grows monotonically (Mechanism 3). Without intervention, $n$ eventually approaches the context window limit. The practical cost grows with $n$ even before the limit is hit: attention quality degrades as the middle of the context fills with superseded reasoning (Mechanism 4), and per-turn cost rises as the $O(n^2)$ factor grows.

Context compaction is the operation of replacing a span of prior context with a compressed summary — a lossy, non-deterministic (Mechanism 7) transformation that reduces $n$ while attempting to preserve the information relevant to future turns. The critical properties:

- **Lossy:** compressed content cannot be fully reconstructed from the summary. A detail compressed away is gone.
- **Non-deterministic:** LLM summarisation of the same span produces different outputs on different runs. Compaction is not a hash — it is another stochastic generation step.
- **Invalidates prefix cache:** any edit to a prior position in the token sequence invalidates the KV cache for that position and all subsequent positions (Mechanism 5). Compaction must be treated as a cache-boundary reset.

The **"early decision" problem** in automated systems is a specialised case. When a system prompt contains option menus, routing conditions, or initialisation decisions, those tokens remain in $n$ for the entire session after the decision is made — paying $O(n^2)$ attention cost for content that has no further informational value. Correct architecture: route with a compact stable cacheable prefix (Mechanism 5), load only the relevant branch, compact prior turns to a decision-and-state summary before re-entering the loop.

**Trigger heuristics (Grade B):** compact when the reasoning trajectory exceeds the last N turns that remain relevant, or when $n$ exceeds a threshold fraction of the context window. The exact threshold is task-dependent.

**What this grounds:** O8 Loop Agent compaction discipline; H-series session management; K7 Context Pruning rationale; K6 Context Compression operational constraints.

---

### M12 — RoPE as an SO(d_head) Lie Group Action  {#m12}

#### Grade A
*The rotary embedding is derived exactly from the requirement that relative position encode as a rotation; the Lie group structure follows from the composition law for rotation matrices.*

Rotary positional encoding applies a rotation matrix $R(i\theta) \in \text{SO}(d_\text{head})$ to each query and key before the attention contraction, where $\theta \in \mathbb{R}^{d_\text{head}/2}$ is a fixed frequency vector and $i$ is the token's absolute position in the sequence. The attention score between positions $i$ and $j$ becomes:

$$s_{ij} = Q_i^T\,R(i\theta)^T\,R(j\theta)\,K_j = Q_i^T\,R\!\left((j-i)\theta\right)K_j$$

The rotation matrices compose: $R(i\theta)^T R(j\theta) = R((j-i)\theta)$. The inner product depends **only on the relative position** $j - i$, not on the absolute positions $i$ or $j$. Absolute position is not stored in any token embedding — only relative displacement is encoded in the attention computation.

This is a Lie group homomorphism $\mathbb{Z} \to \text{SO}(d_\text{head})$: translations in sequence space (moving both $i$ and $j$ by the same offset) map to the identity rotation in $d_\text{head}$-space. The model is translation-equivariant in position by construction.

**Recency bias is a geometric consequence.** Small $|j - i|$ (nearby tokens) produces small rotation angles; the inner product $Q_i^T R((j-i)\theta) K_j$ is less rotated away from the unrotated inner product $Q_i^T K_j$. For tokens far apart, the rotation substantially modifies the inner product. The model's learned $W_Q$ and $W_K$ were trained under this geometry and internalized the bias toward small offsets — producing the empirically observed recency effect via a derivable geometric mechanism.

**Implication for few-shot example ordering:** the last example before the query has the smallest offset and therefore the strongest Q-K inner product alignment, all else equal. "Place the most representative example last" is a geometric recommendation derivable from RoPE, not a heuristic.

**Implication for prompt injection defense:** re-anchoring instructions ("Ignore the above...") placed near the end of a context exploit this recency geometry. They are not magic words — they work because their small offset from the query position gives them higher attention weight than the injected content placed earlier.

**What this grounds:** S2 Few-Shot example ordering; S4 Instruction Decomposition placement advice; V6 Prompt Injection Shield re-anchoring rationale; R17 Self-Consistency timing constraint (all N samples must share the same stable prefix position offsets).

---

## 0.4 — How to Read Mechanism Citations in This Book

Pattern files throughout the catalog cite mechanisms in the form **(mechanism N)** or **[Mechanism N]** where N is one of the twelve entries above. These citations indicate:

1. **The rationale for the recommendation is derivable from this mechanism** — not merely observed empirically. Where the evidence grade is A, the derivation is tight. Where it is B, the direction is mechanistically supported but the magnitude or threshold is empirical.

2. **The cited mechanism overrides intuition when they conflict.** If a recommendation feels counterintuitive but is supported by a Grade A mechanism citation, trust the mechanism. The most common case: practitioners underestimate the n² cost of context (Mechanism 2) because linear cost intuitions are deeply ingrained from other computing domains.

3. **"Observed behaviour" without a mechanism number means the claim is empirical.** The catalog distinguishes between derived claims (mechanism citations) and observed claims (phrased as "empirically, X" or "in practice, X"). Where a mechanism is unknown, the pattern says so rather than inventing one.

The grade key for mechanism citations:

| Grade | Meaning in a pattern |
|---|---|
| **A** | Derivable from transformer architecture or information-theoretic first principles. Use as a design axiom. |
| **B** | Mechanistically supported with strong empirical evidence. Direction is reliable; magnitude or threshold may vary. |
| **⚠ observed** | Empirically consistent but without a published mechanistic account. Do not over-generalize. |

---

## Summary — Mechanisms and Pattern Categories

| Mechanism | Grade | Primary categories underwritten |
|---|---|---|
| 1 — Attention as learned bilinear form $g_{\mu\nu} = W_Q W_K^T$ | A | K (retrieval geometry), S (prompt routing), I (tool schema cost) |
| 2 — n² compute and KV cache memory cost | A | K (context budget), O (decomposition rationale), V (cost accounting) |
| 3 — KV cache as growing 4D tensor; no cross-call persistence | A | H (memory = retrieval), K (working memory), V (checkpointing) |
| 4 — Lost-in-middle as Q-K geometric under-attendance | B | K (content placement), S (prompt ordering), V (injection defense placement) |
| 5 — Prefix caching as cache engineering (provider-level KV reuse) | A/B | S (stable prefix design), H (Genesis State caching), O (worker fan-out timing) |
| 6 — Subagent decomposition as per-agent n bounding | A | O (all multi-agent patterns), the O6+O17 composition law |
| 7 — Stochastic generation and autoregressive commitment | A | R (all reasoning patterns), I (deterministic tools), V (enforcement discipline) |
| 8 — Model size matching to task complexity | A/B | O (model assignment), I (routing model), V (dual-LLM size) |
| 9 — Storage tier hierarchy (write cost vs read cost axis) | A/B | K (memory tier selection), H (session management), I (result handling) |
| 10 — No cross-session persistence; all memory is retrieval | A | H (all memory patterns), K (long-term memory design) |
| 11 — Context compaction; early-decision cost amortization | A/B | O (loop patterns), K (pruning/compression triggers) |
| 12 — RoPE as SO($d_\text{head}$) Lie group action; relative-only position | A | S (example ordering), V (injection re-anchoring), R (timing of parallel samples) |

---

*This chapter is the mechanistic spine. Every pattern that cites a mechanism number is claiming that its recommendation follows from the derivation above. Hold that claim to the evidence grade it carries.*
