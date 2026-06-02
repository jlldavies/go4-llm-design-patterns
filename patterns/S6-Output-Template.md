# S6 — Output Template

> Provide the skeleton of the expected output — fields, labels, and structure — for the model to complete, so format generation is replaced by format *filling*.

**Also Known As:** Template Filling, Structured Output, Format Forcing, Skeleton Prompting. (Variants: **JSON-mode / schema-constrained decoding**, **Free-text template**, **Few-shot template** — see Variants.)

**Classification:** Category I — Signal · the format-shaping pattern — separates *what to say* from *how to lay it out*, by carrying the layout in the prompt.

---

## Intent

Replace open-ended generation of "content plus format" with the simpler task of filling content into a predefined skeleton, so downstream parsers, chained LLM calls, and human reviewers see a consistent shape every run.

## Motivation

Open-ended generation produces inconsistent formats. The same prompt, asked twice, returns different field orders, different label wording, different nesting depths — and any system that depends on parsing the output breaks the first time the model decides a Markdown bullet list is friendlier than a JSON object. The cost is not the occasional bad run; it is the defensive parsing that every downstream step now has to carry forever.

The fix is to move the format burden out of the model's task. If the prompt *contains* the skeleton — fields, labels, order, types — the model's job collapses from "decide format AND content" to "fill content into format". The first is generative and noisy; the second is closer to extraction and substantially more reliable. Every measured benchmark of structured generation shows the same pattern: skeleton-bearing prompts produce parseable output an order of magnitude more often than free-form prompts, and the gap widens as the schema gets richer. For the JSON-mode / schema-constrained variant, the reason is stronger: schema-constrained decoding (Outlines, Guidance, OpenAI Structured Outputs) masks the logit distribution at each token step so that only tokens valid under the schema grammar can be sampled (mechanism 7). This removes structural sampling variance entirely — the output type, field order, and key spelling are deterministic. The free-text template cannot achieve this because it still relies on stochastic sampling of format tokens. The choice between variants is the same principle that makes tool execution more reliable than in-context computation.

A real boundary lives inside the pattern. When the provider supports **native structured output APIs** — OpenAI's `response_format` with JSON Schema, Anthropic's tool-use schema, schema-constrained decoders like Outlines or Guidance — those are *strictly better* than a free-text template: they constrain the decoder itself, so the output is guaranteed parseable, not merely usually parseable. S6 in free text is the fallback when (a) the provider does not support schema-constrained decoding for the call you are making, (b) the output mixes structured fields with narrative prose, or (c) the schema is too fluid to commit to up front. Treat the API as the default and the free-text skeleton as the explicit fallback — both are the same pattern, applied through different mechanisms.

## Variants

The variants differ in *how the skeleton is enforced* — by the decoder, by prompt content, or by examples:

- **JSON mode / schema-constrained decoding.** The skeleton is a JSON Schema (or grammar) submitted to the API; the decoder constrains generation to valid completions. Provider-native (OpenAI Structured Outputs, Anthropic tool-input schemas) or library-driven (Outlines, Instructor, Guidance). Strongest guarantee; only available where supported.
- **Free-text template.** The skeleton is written into the prompt as labelled placeholders or a partial document; the model completes by analogy. Works with any model and any output shape, including mixed structured-plus-narrative outputs. Probabilistic, not guaranteed.
- **Few-shot template.** The skeleton is taught implicitly by 2–8 worked examples (composition with **S2 Few-Shot**); the model infers format from demonstration rather than from an explicit skeleton. Useful when the format is hard to describe but easy to show.

The three are the same pattern — *carry the output shape so the model does not have to invent it* — differing in the mechanism that carries it. Pick the strongest one the runtime supports.

## Applicability

Use Output Template when:

- output is parsed programmatically, or chained to another LLM call (see **O2 Prompt Chaining**);
- consistent format across runs is a business or display requirement;
- the task is multi-field structured extraction;
- the format is non-obvious, easy to drift on, or has changed before.

Do not use when:

- the output is naturally free prose (an essay, a draft email, a summary for human reading) — a template constrains expression for no gain; use **S1 Zero-Shot** or **S3 Persona**;
- the format is so simple that a single sentence of instruction is clearer than a skeleton ("respond with one word: YES or NO");
- the provider supports schema-constrained decoding for the call — use the API directly rather than a free-text template (still S6, but via the JSON-mode variant);
- the schema is changing every run — the template has to be re-built per call and its value drops; consider **S2 Few-Shot** with diverse examples instead.

## Decision Criteria

S6 is right when the cost of a malformed output is non-trivial and the format is stable enough to write down.

**1. Measure the parse-failure rate.** Run the same prompt N times without a template; count outputs that fail your downstream parser or differ in field order, labelling, or nesting. **> 5% failure** means S6 pays back immediately; **> 20%** means S6 is mandatory before any production use.

**2. Pick the strongest variant the runtime supports.**
- Native schema-constrained decoding available (OpenAI Structured Outputs, Anthropic tool schemas, Outlines / Guidance / Instructor with a local model)? Use it — the **JSON-mode variant** is strictly better than a prompt template.
- Provider has JSON mode but no schema enforcement? JSON-mode-with-schema-in-prompt is a middle ground.
- No structured-output API, or output is mixed structured + narrative? Use the **free-text template** variant.
- Format hard to describe but easy to show? Use the **few-shot template** variant (compose with **S2**).

**3. Schema stability.** Will the format change more than once a sprint? If yes, the maintenance cost of the template starts to bite — keep the skeleton small and parameterised, or move to few-shot.

**4. Mixed content boundary.** If the output is *pure* structured data (a record, a classification, a tool call), prefer the JSON-mode variant — the decoder constraint removes a whole class of failure. If the output mixes a structured envelope with free narrative inside (a report with `summary:`, `findings:`, `recommendation:` sections), the **free-text template** variant is usually the right answer; JSON mode would force you to escape the prose.

**5. Downstream coupling.** Is the output consumed by code (must parse), by another LLM (must be predictable enough for a chained prompt), or by a human (must be scannable)? Code-consumers raise the value of S6 sharply; human-consumers raise it less.

**Quick test — S6 is the right pattern when:**

- output is consumed by code, a chained LLM call, or a display layer that depends on shape, *and*
- the format is stable enough to write down once, *and*
- parse-failure or shape-drift in untemplated runs is non-trivial (> 5%), *and*
- either no schema-constrained API is available for the call, *or* the output mixes structured fields with narrative.

If a schema-constrained API *is* available and the output is purely structured, use the JSON-mode variant rather than a free-text skeleton — same pattern, stronger mechanism. If the output is free prose for a human reader, do not template at all.

## Structure

```
  Task ──▶ Prompt with embedded skeleton ──▶ Model
                  │                            │
                  ▼                            ▼
       fields, labels, order,           completes the skeleton:
       types, placeholders              fills content into shape
                                              │
                                              ▼
                                       Parser / next LLM step / display
                                              │
                                              ▼
                                     (optional) repair on shape failure
```

When the JSON-mode variant is used, the "skeleton" is a JSON Schema submitted alongside the prompt and the decoder enforces it — the parser then operates on a guaranteed-valid object.

## Participants

| Participant | Owns | Input → Output | Must not |
|---|---|---|---|
| **Skeleton** | the shape of the output — fields, labels, order, types | — → format specification | be ambiguous about which fields are required; an under-specified skeleton invites the model to invent fields, and silently breaks the parser. |
| **Prompt** | binding task input to the skeleton | task input + skeleton → model prompt | leave the model guessing whether placeholders are literal or to be replaced; spell the rule out. |
| **Model** | filling content into the shape | prompt → completed structure | invent new fields, reorder them, or "improve" the format; the skeleton is the contract. |
| **Decoder constraint** *(JSON-mode variant)* | enforcing the schema at token-decode time | schema + logits → constrained tokens | be confused with prompt-side instruction; this is a runtime guarantee, not a hint. |
| **Parser** | converting the completed shape into a typed object | model output → typed record (or shape error) | be lenient about silent shape changes — a brittle parser surfaces drift early, a lenient one hides it. |
| **Repair step** *(optional)* | recovering from shape failure | failed output + schema → corrected output | be the primary defence; if it fires often, fix the skeleton. |

The Skeleton and the Parser are the same artefact viewed from two ends: one defines the shape the model must produce, the other reads it. Keeping them in sync (ideally generated from one schema) is the pattern's main maintenance discipline.

## Collaborations

The task is composed by binding inputs to a skeleton inside a prompt. The model receives the prompt and returns its completion. When the JSON-mode variant is active, the decoder enforces the schema at token-decode time, so the output is guaranteed parseable — the parser becomes a typed-load step. In the free-text variant there is no such guarantee: the parser validates the shape and, on failure, an optional repair step re-prompts the model with the bad output and the schema to ask for a correction. If repair fires more than rarely, the failure is in the skeleton (under-specified, ambiguous placeholders, mixed conventions) and the fix belongs upstream.

## Consequences

**Benefits**

- Dramatically improves format consistency — the dominant lever for reliable downstream parsing.
- Makes prompt-chained pipelines (O2) feasible at all; without S6, every step has to guess the previous step's shape.
- Catches schema drift early — when the model deviates, the parser fails fast rather than poisoning a chain.
- The JSON-mode variant removes whole classes of failure (missing fields, wrong types, invalid enums).

**Costs**

- Tokens consumed by the skeleton on every call (free-text variant); negligible for short schemas, real for rich ones — every skeleton token participates in the O(n²) pairwise attention over the prompt (mechanism 2).
- Maintenance burden — the skeleton and the parser must stay in sync.
- The skeleton can over-constrain — the model fills a "Risk Level" field with `Medium` because the template demanded a value, when the right answer was "insufficient evidence".

**Risks and failure modes**

- *Under-specified skeleton* — the model fills with placeholder text (`[insert title]`), or invents fields the parser does not know about.
- *Schema drift* — the skeleton and the downstream parser diverge over time; outputs validate against the wrong shape.
- *Forced field syndrome* — the model produces low-confidence values to fill mandatory fields rather than admit absence; mitigate with explicit `nullable` / `unknown` enums.
- *Mixed-content breakage* — using JSON mode for an output that should carry narrative forces ugly escaping and degrades quality; use the free-text variant for genuinely mixed outputs.
- *Repair-loop dependence* — relying on the repair step to fix systematic failures rather than fixing the skeleton; hides the cost and degrades latency.

## Implementation Notes

- **Use the API where available.** OpenAI Structured Outputs (`response_format` with JSON Schema), Anthropic tool-use schemas, Outlines and Guidance for self-hosted models — these are strictly better than a free-text template. Reach for the free-text variant only when the API does not support the call or the output is mixed structured + narrative.
- **Provide the schema, not example JSON.** When using JSON mode, give the schema directly; it is shorter and harder to misread than a worked example. The schema *is* the skeleton. Design the prompt + skeleton as a stable, cacheable prefix unit (mechanism 5). For calls where the schema is fixed across queries, the system prompt + skeleton qualifies for provider prefix caching (Anthropic: TTL ~5 min, min 1024 tokens, ~10% cost on cache hit). The skeleton's token cost on subsequent calls within the TTL is a tenth of the listed price. Changing the schema invalidates the cache.
- **For free-text templates, label placeholders unambiguously.** `[TITLE]` is clearer than `<title>` or `{title}`; pick one convention and use it everywhere. State explicitly that placeholders are to be replaced, not echoed.
- **Allow `null` / `unknown` / `n/a` for fields the model may legitimately not have evidence for.** Forced-field syndrome is the main quality cost of S6.
- **Keep skeletons small.** A long template eats context and dilutes attention — recall degrades for mid-context fields (mechanism 4); if the schema has more than ~10 fields, decompose into chained calls (compose with **O2 Prompt Chaining**) rather than one mega-template.
- **Compose with S2 Few-Shot for rare or hard-to-describe formats.** A single worked example often clarifies what three paragraphs of skeleton cannot.
- **Validate on every output, even with JSON mode.** Schema-constrained decoding guarantees syntactic validity, not semantic correctness — a value of the right type can still be wrong.
- **Generate the skeleton and the parser from one source of truth** (Pydantic, Zod, dataclass, JSON Schema file). The most common production failure is the skeleton and parser drifting independently.

## Implementation Sketch

> `LLM` = configured session (model + setup + per-call prompt); `code` = wiring.

**Composition:** S6 sits inside almost every other pattern's *Generator* session — it specifies the shape the generation must take. It composes naturally with **O2 Prompt Chaining** (each step's output shape is a template), **S2 Few-Shot** (examples teach the template implicitly), **S4 Instruction Decomposition** (a template names the output structure of the final step), and **V15 LLM-as-Judge** (judges read more reliably when their verdict shape is templated).

**The chain:**

| # | Step | Kind | Draws on |
|---|---|---|---|
| 1 | Define the schema (Pydantic / JSON Schema / Zod) | `code` | single source of truth |
| 2 | Render the prompt — bind task input + render skeleton (or attach JSON Schema for API variant) | `code` | S5 constraint framing for "must not invent fields" |
| 3 | Model call — generate, decoder-constrained if JSON mode is in play | `LLM` | Generator session |
| 4 | Parse — load the output into the typed object | `code` | the same schema as step 1 |
| 5 | On parse failure (free-text variant only): repair-prompt the model with the bad output and the schema | `LLM` (optional) | Repair session |

**Skeleton** — the wiring only; each `# LLM` line is a configured session:

```
generate_structured(task_input, schema):
    prompt = render_prompt(task_input, schema)        # code
    if api_supports_json_mode:
        output = Model(prompt, response_format=schema) # LLM (decoder-constrained)
    else:
        output = Model(prompt)                         # LLM (free-text template)
    try:
        return parse(output, schema)                   # code
    except ShapeError as e:
        return Repair(output, schema, e)               # LLM — optional, free-text variant only
```

**The LLM sessions:**

| Session | Model | Setup — loaded once, before first call | Per-call prompt wraps |
|---|---|---|---|
| **Generator** | any capable generalist; the smaller, the more S6 helps | role (S3 if relevant); the skeleton / schema; the rule that placeholders are to be replaced and no extra fields invented; in JSON mode, the schema is attached out-of-band rather than in the prompt | the task input |
| **Repair** *(optional, free-text only)* | small fast generalist | role: *"correct this output to match the schema; change as little as possible"*; the schema; the parser's error message | the bad output |

**Specialist-model note.** None — a capable generalist suffices. The artefact that does the work is the **schema** (in JSON mode) or the **skeleton** (in free-text mode), not a specialist model. The one runtime dependency that *does* matter is whether the provider supports schema-constrained decoding for the call you are making — if it does, use it; that is a build-time choice about which variant to deploy, not a model choice.

## Open-Source Implementations

- **Outlines** — [`github.com/dottxt-ai/outlines`](https://github.com/dottxt-ai/outlines) — Python library for structured generation against JSON Schema, Pydantic models, regex, and grammars; constrains the decoder so output is guaranteed valid. Works with OpenAI, vLLM, Ollama, and local transformers.
- **Instructor** — [`github.com/567-labs/instructor`](https://github.com/567-labs/instructor) — Pydantic-first structured output across OpenAI, Anthropic, Google, Groq, and Ollama; automatic validation, retry-on-failure, streaming partial objects. (Previously hosted at `jxnl/instructor`; current canonical home is `567-labs/instructor`.)
- **Guidance** — [`github.com/guidance-ai/guidance`](https://github.com/guidance-ai/guidance) — guidance language for constrained generation with JSON Schema, regex, grammars, and token fast-forwarding; supports Transformers, llama.cpp, OpenAI.
- **OpenAI Structured Outputs** — [`platform.openai.com/docs/guides/structured-outputs`](https://platform.openai.com/docs/guides/structured-outputs) — provider-native JSON Schema enforcement via `response_format`; the canonical JSON-mode-variant implementation.
- **Anthropic tool-use schemas** — `tools[].input_schema` with JSON Schema in the Messages API — the equivalent JSON-mode pathway for Claude models.

## Known Uses

- **Production extraction pipelines** — invoice, contract, and form parsers built on OpenAI Structured Outputs or Instructor, where a malformed record breaks the pipeline.
- **LLM-as-Judge evaluators** — V15 verdicts almost universally use a JSON-mode template (verdict, score, rationale) so the judge's output can be aggregated mechanically.
- **Tool-calling agents** — every function-call API is S6 in disguise: the function's input schema is the template the model fills.
- **Chained-prompt pipelines** (O2) — every internal handoff is templated; without S6 the chain does not survive a model upgrade.
- **Karpathy Memory (K12) curators** — the Curator's note schema is an S6 artefact; the structure is what makes the memory navigable.

## Related Patterns

- **Pairs with** S2 Few-Shot — examples can teach a template implicitly when describing it explicitly is hard; the two compose cleanly (template names the shape, examples show its texture).
- **Pairs with** S4 Instruction Decomposition — a template is one way to specify the *output* structure of a multi-step prompt, where S4 specifies the *process*.
- **Pairs with** S5 Constraint Framing — the "do not invent fields, do not echo placeholders" rule is a constraint that belongs next to the template.
- **Pairs with** V15 LLM-as-Judge — judges need structured verdicts (verdict, score, rationale); S6 is the standard mechanism.
- **Required by** O2 Prompt Chaining — chained calls only survive if each step's output shape is templated; otherwise the chain breaks the first time the model rephrases.
- **Required by** I2 Function / Tool Call — every function schema is an S6 template enforced by the provider.
- **Distinct from** S1 Zero-Shot and S3 Persona — those shape *what* the model says; S6 shapes *how* it lays the answer out.
- **Note on the API boundary** — when a provider's structured-output API supports the call, that is the **JSON-mode variant** of S6, not a separate pattern. Use it in preference to a free-text skeleton; reach for the free-text variant only when the API does not support the call or the output is mixed structured + narrative.

## Sources

- White et al. (2023) — "A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT" — *Output Template* / *Output Customization* category.
- OpenAI (2024) — "Introducing Structured Outputs in the API" and the Structured Outputs guide ([`platform.openai.com/docs/guides/structured-outputs`](https://platform.openai.com/docs/guides/structured-outputs)).
- Anthropic — Tool use documentation, `input_schema` for Claude tool definitions.
- Willard & Louf (2023) — "Efficient Guided Generation for Large Language Models" (arXiv 2307.09702) — the Outlines paper; basis for schema-constrained decoding.
- Lundberg & Ribeiro — Guidance project documentation; constrained generation with grammars.
- Instructor documentation — Pydantic-first structured output across providers.
