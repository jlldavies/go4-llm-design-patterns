# GO4 Ingest Layer — Design Spec

**Date:** 2026-06-03
**Status:** Draft for review
**Author:** James Davies (with Claude)

---

## 1. Purpose

Add a third build output to GO4: a derived `ingest/` folder that lets anyone
clone the repo, point a personal memory system or coding agent at it, and absorb
the **entire** catalog — patterns, the mechanical foundation, decision guides,
the conflict graph, and references — as clean, relabelable knowledge.

GO4 documents [K12 Karpathy Memory](../../patterns/K12-Karpathy-Memory.md). The
ingest layer makes GO4 *distribute itself as a K12 artifact*: an LLM-friendly,
interlinked, self-describing knowledge set in the markdown-wiki shape the
ecosystem converged on in 2026 (`agentmemory`, Cognee, Obsidian/Dataview, Claude
Code memory). The catalog becomes an instance of the pattern it teaches.

This is a **derived projection** of the existing source. It adds no new claims
and changes no source content.

```
patterns/*.md + build/content/CHAPTER-0.md + decision guides + CONFLICTS.md + REFERENCES
        │
        ├──→ GitHub Pages (mdBook)     [exists]
        ├──→ GO4.pdf                    [exists]
        └──→ build/build_ingest.py ──→  ingest/   [NEW]
```

## 2. Design principles (non-negotiable)

1. **Neutral / relabel-on-ingest.** We *suggest* labels; we never impose a
   schema. Frontmatter is flat and uses widely-understood field names. Every
   field is documented so a consumer can map ours → theirs in one step. The body
   stays useful even if a consumer discards all frontmatter.
2. **Accurate self-description.** Each unit is a *derived digest*. `patterns/*.md`
   remains canonical. Every unit carries `derived: true` and a `canonical:`
   pointer. No memory-lifecycle fields (confidence, decay, retention) — GO4 is
   authored and stable, and inventing those would be inaccurate.
3. **Completeness — "all of it."** The set includes patterns + mechanisms +
   decision guides + the conflict/relationship graph + references. One ingest
   absorbs the whole catalog, the "why," and the sources.
4. **Provenance.** Every unit links back to its canonical source file (and
   optionally the Pages URL). The manifest records the source commit.
5. **Deterministic & quote-faithful.** The layer is assembled from the source by
   a build script, not paraphrased by a per-build LLM. Descriptions are built
   from the source's own *Intent* text plus curated relationship data — so they
   cannot drift from canonical claims. Regenerating from the same commit yields
   byte-identical output.
6. **Minimal top-level footprint.** `ingest/` is the *only* new top-level
   directory. All machinery — `build_ingest.py`, `ingest-meta.yaml`,
   `validate_ingest.py`, this spec — lives under the existing `build/`. The only
   other touch at the top level is editing the existing `README.md`.

## 3. Deliverables

```
README.md                   # MODIFIED — prominent "ingest into your agent" section (see §11)
ingest/                     # THE ONLY new top-level directory
  INGEST.md                 # honest description + how-to-ingest + relabel guide
  index.md                  # generated catalog by category (one line per unit)
  ingest.json               # manifest: unit index + global edge graph + field glossary
  references.md             # consolidated bibliography unit (anchored sources)
  S1-Zero-Shot.md … H10-Relational-Memory.md   # 94 pattern units
  M1-…-bilinear-form.md … M12-…-rope.md         # 12 mechanism units
  DECISION-reasoning.md … DECISION-signal.md    # 7 decision-guide units
build/
  ingest-meta.yaml          # the curated graph + selection metadata (single source of truth for labels)
  build_ingest.py           # assembles ingest/ from source + ingest-meta.yaml
  validate_ingest.py        # integrity checks (or folded into validate.py)
  specs/2026-06-03-go4-ingest-layer-design.md   # this file
```

Unit inventory: 94 patterns + 12 mechanisms + 7 decision guides + 1 references
unit ≈ **114 unit files**, plus `INGEST.md`, `index.md`, `ingest.json`.

> Open default: category-overviews (`SIGNAL.md` … `HUMANIZERS.md`, 7 files) are
> **not** shipped as separate units in v1 — their content is largely covered by
> the decision guides and the per-pattern descriptions. Reconsider if reviewers
> want them.

## 4. Per-unit file schema

Frontmatter (YAML). Required/optional noted per `type`.

| Field | Type | Applies to | Notes |
|---|---|---|---|
| `id` | string | all | `R4`, `M2`, `K13`, `DECISION-reasoning` |
| `title` | string | all | `ReAct` |
| `type` | enum | all | `pattern` \| `mechanism` \| `decision-guide` \| `reference-set` |
| `category` | enum | pattern, decision-guide | `Signal\|Knowledge\|Reasoning\|Orchestration\|Reliability\|Integration\|Humanizers` |
| `summary` | string (1 line) | all | what it *is* — feeds `index.md` and `ingest.json` |
| `when_to_use` | string (1 line) | pattern | trigger condition — sourced from the README index table |
| `also_known_as` | list | pattern | from the "Also Known As:" line |
| `cost` | enum | pattern | `baseline\|low\|medium\|medium-high\|high\|very-high\|highest` (omit if source has none) |
| `requires` | list[id] | pattern | hard dependency (e.g. R4 → V9, V14) |
| `conflicts_with` | list[id] | pattern | mutually exclusive / tension (authoritative from CONFLICTS.md) |
| `composes_with` | list[id] | pattern | pairs/nests cleanly (e.g. R4 → O6, K6, K8, R7) |
| `siblings` | list[id] | pattern | same-problem alternatives (e.g. R4 → R5, R13) |
| `related` | list[id] | pattern | "distinct from" / see-also |
| `mechanism_refs` | list[int] | pattern | from `(mechanism N)` citations, 1–12 |
| `grade` | enum | mechanism | `A\|B\|observed` |
| `grounds` | list[id] | mechanism | patterns this mechanism underwrites (reverse of `mechanism_refs`) |
| `canonical` | path | all | repo-relative source, e.g. `patterns/R4-ReAct.md`; mechanisms point to `build/content/CHAPTER-0.md#m2` |
| `source_url` | url | all | optional Pages URL |
| `derived` | bool | all | always `true` |

Body:

```markdown
## Description
<Intent, quoted from the canonical file> <one generated sentence stating the
relationships in prose — "Requires V9 and V14; mutually exclusive with R5;
commonly nested inside O6 workers."> This is a condensed digest; the canonical
file carries the full decision criteria, failure modes, and implementation.

## Key points
- <Applicability "use when" bullets, compacted>
- <the "Quick test" criteria>

Related: [[R5-ReWOO]] · [[R13-CodeAct]] · [[O6-Orchestrator-Workers]] ·
[[V9-Bounded-Execution]] · [[M2-n-squared]]
```

The relationships appear **three ways** so they survive any consumer: typed
frontmatter edges, prose in `## Description` (survives frontmatter stripping),
and `[[wikilinks]]` (merges into wiki graphs).

## 5. Manifest schema (`ingest.json`)

One object:

```json
{
  "schema": "go4-ingest/v1",
  "generated_from": "patterns/*.md + build/content/CHAPTER-0.md @ <commit-sha>",
  "canonical_note": "Units are derived digests. The patterns/*.md and CHAPTER-0.md files are authoritative.",
  "field_glossary": {
    "requires": "Hard dependency: this pattern must be paired with the target.",
    "conflicts_with": "Mutually exclusive or in tension for the same task.",
    "composes_with": "Pairs or nests cleanly with the target.",
    "siblings": "Same-problem alternative with a different trade-off.",
    "mechanism_refs": "Chapter-0 mechanism numbers (1–12) that ground this pattern."
  },
  "units": [
    {
      "id": "R4", "type": "pattern", "category": "Reasoning", "title": "ReAct",
      "summary": "Adaptive Thought→Action→Observation loop.",
      "file": "ingest/R4-ReAct.md", "canonical": "patterns/R4-ReAct.md",
      "edges": {
        "requires": ["V9", "V14"], "conflicts_with": ["R5"],
        "composes_with": ["O6", "K6", "K8", "R7"], "siblings": ["R5", "R13"],
        "mechanism_refs": [2, 3, 4, 12]
      }
    }
  ],
  "edges": [
    { "from": "R4", "to": "R5", "type": "conflicts_with" },
    { "from": "R4", "to": "V9", "type": "requires" }
  ],
  "stats": { "patterns": 94, "mechanisms": 12, "decision_guides": 7 }
}
```

`field_glossary` is the relabel aid — a consumer reads it to map our keys onto
their own schema. `edges` is the flat global graph (the whole CONFLICTS map plus
pattern→mechanism links) for programmatic/graph consumers.

## 6. `INGEST.md` contents

1. **What GO4 is** — one paragraph.
2. **What this folder is** — honest: derived digests; `patterns/*.md` canonical;
   generated by `build_ingest.py`; no lifecycle/confidence fields.
3. **What's included** — the inventory.
4. **The field schema** — the glossary (or a pointer to `ingest.json`), with the
   explicit note: *these labels are suggestions; relabel on ingest as you see fit.*
5. **How to load it** — short concrete recipes:
   - Karpathy wiki / `agentmemory`: copy `ingest/` into the wiki's source dir; run ingest.
   - Cognee: point the ingest pipeline at `ingest/*.md`.
   - Obsidian vault: drop in; frontmatter is Dataview-ready, `[[links]]` resolve.
   - Claude Code / coding agent: reference `ingest/` from `CLAUDE.md`/`AGENTS.md`.
   - Generic vector store: chunk `ingest/*.md`; carry frontmatter as metadata.
6. **What's authoritative** — links to canonical source + Pages + PDF.
7. **License** — MIT.

## 7. The curated metadata file (`build/ingest-meta.yaml`)

The relationship graph and selection labels (`cost`, `summary`, edges) are the
one part that can't be 100% mechanically extracted — the source states relations
in varied prose ("Sibling of", "Required by", "Inner pattern of"). So they live
in **one curated file**, reviewed once, versioned, and validated:

```yaml
R4:
  summary: "Adaptive Thought→Action→Observation loop."
  cost: medium-high
  requires: [V9, V14]
  conflicts_with: [R5]
  composes_with: [O6, K6, K8, R7]
  siblings: [R5, R13]
  related: [R3, R1, R2]
```

Bootstrapping it (implementation phase): a script seeds `ingest-meta.yaml` by
parsing each pattern's **Related Patterns** section (label → edge-type map) and
**CONFLICTS.md**, plus regex for `(mechanism N)`. The seed is then **reviewed and
corrected once** — this is the only human-judgment step. After that the graph is
data: deterministic, diffable, validated.

Fields extracted **purely mechanically** (no meta file needed): `also_known_as`
(the "Also Known As:" line), `category` (id prefix), `mechanism_refs` (regex),
`when_to_use` (README index table), Intent text (the opening blockquote).

> Source files are **not modified.** All curated labels live in `ingest-meta.yaml`,
> keeping `patterns/*.md` pristine. (Rejected alternative: frontmatter on source
> patterns — churns the canonical prose the user wants kept as-is.)

## 8. Build & validation

`build_ingest.py`:
1. Load source patterns, mechanisms (CHAPTER-0 split on `### Mn`), decision
   guides, REFERENCES, and `ingest-meta.yaml`.
2. For each unit: extract mechanical fields, join curated fields, assemble
   frontmatter + `## Description` (Intent quote + templated relationship sentence
   + provenance) + key points + `Related:` wikilinks.
3. Write `ingest/*.md`, `ingest/index.md`, `ingest/references.md`.
4. Emit `ingest/ingest.json` (units + flat edge list + glossary + stats + commit).

`validate_ingest.py` (CI gate, mirrors existing `build/validate.py`):
- Every unit has required frontmatter for its `type`.
- Every edge target id exists (no dangling links).
- `conflicts_with` is **symmetric** (R4↔R5) — warn on asymmetry.
- Every `mechanism_refs` ∈ 1–12; every `canonical` path resolves.
- `ingest.json` units ↔ files are 1:1.
- `ingest-meta.yaml` conflict edges agree with CONFLICTS.md (drift check).

`ingest/` is a **committed artifact, exactly like `GO4.pdf`** — generated locally
by running `build_ingest.py`, then committed. **The existing `deploy-pages.yml`
workflow is NOT modified.** It reads only `patterns/*.md` and named
`build/content/` files (verified: `prepare.py`, `validate.py`, `build_book.py`
all read scoped inputs, never the repo root), so it never sees `ingest/` and
cannot be affected by it. Staleness is guarded *optionally* by a separate,
**non-deploying** CI check that regenerates to a temp dir and diffs against the
committed `ingest/`, failing only if they drift — it touches neither the site nor
the PDF pipeline.

**Source dependencies & regeneration discipline.** `ingest/` is *derived from*,
and therefore coupled to, its upstream inputs: **every `patterns/*.md` file**,
`build/content/CHAPTER-0.md` (mechanisms), the seven decision guides,
`CONFLICTS.md`, `REFERENCES.md`, and `build/ingest-meta.yaml`. Editing any one of
them makes the committed `ingest/` stale. So the authoring workflow for *any*
content change becomes: edit the canonical source → run `build_ingest.py` →
commit the source edit **and** the regenerated `ingest/` in the same change —
identical to how editing a pattern then rebuilding `GO4.pdf` works today. The
staleness guard regenerates from this full input set and fails CI if a source
edit landed without a matching ingest regen. The coupling is strictly
one-directional — source → ingest; `ingest/` is output-only and nothing ever
reads it back, so the canonical files remain the single source of truth.

## 9. Out of scope (later skins, build on this substrate)

- **Claude Code Skill/Plugin** wrapping `ingest/` for `/plugin install` auto-serve.
- **llms.txt** routing pointer at the Pages site.
- **MCP server** serving units on query.
- Memory-lifecycle metadata (confidence/decay/retention) — deliberately excluded.
- Category-overview units (see §3 open default).

## 10. Success criteria

- A developer clones the repo, points a memory system at `ingest/`, and the agent
  thereafter surfaces the right pattern *with its conflicts, cost, and mechanism*
  for a relevant design question.
- `ingest/` regenerates deterministically from source; no manual edits to
  generated files.
- A consumer can discard our frontmatter and relabel from the glossary without
  losing the relationship graph (it's also in prose).
- Nothing in `ingest/` asserts anything not traceable to a canonical source file.

## 11. README updates (prominent)

The ingest layer is the **third way to consume GO4** — book, site, **ingest** —
so it gets first-class placement, not a footnote.

- **New section near the top**, directly after "📖 Get the Book": *"🧠 Ingest
  GO4 into your agent's memory."* One paragraph on what it is, then the workflow:
  clone the repo → point your personal memory system or coding agent at the
  top-level `ingest/` folder → it absorbs the **whole** catalog (patterns,
  mechanisms, decision graph, references). State that the labels are suggestions
  you relabel on ingest, and link to `ingest/INGEST.md`.
- **"Repo Structure"** — add the top-level `ingest/` folder to the tree with a
  one-line note: a generated, ingestible projection of the catalog.
- **"Start Here"** — add a fourth entry: *"Ingest the whole catalog into your
  agent — see `ingest/INGEST.md`."*
- **Accuracy:** describe `ingest/` as a generated, derived projection;
  `patterns/*.md` remain canonical. No overclaiming.
