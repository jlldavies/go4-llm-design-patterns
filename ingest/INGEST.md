# Load GO4 into your agent's memory

You are helping a developer load the **GO4 LLM-engineering pattern catalog** into their
own agent memory / knowledge base. Point your agent at this file and it will ingest the
whole catalog into whatever format the user runs.

## What you're loading (all in this `ingest/` folder + `../patterns/`)
- **94 pattern digests** (`*.md` here) — frontmatter (id, category, when_to_use, typed
  edges, cost, mechanism_refs, canonical) + a dense description + key points + `[[wikilinks]]`.
- **12 mechanism digests** (`M*.md`) — the "why" (transformer-level rationale).
- **7 decision guides** (`DECISION-*.md`) — how to choose a pattern per category.
- **The conflict map** — `../patterns/conflicts/*.md` (full prose) + the typed
  `conflicts_with` edges in every digest and in `ingest.json`.
- **`references.md`** — the bibliography.
- **`ingest.json`** — the machine index: every unit + the full relationship graph +
  a `field_glossary`. **Drive the load from this.**

## How to load it — adapt to the user's memory format
1. Detect or ask the user's system: Karpathy LLM-wiki, Obsidian, a vector store, a
   `CLAUDE.md`/`AGENTS.md`, or something else.
2. For each unit, create one note / record / chunk in that format:
   - **Karpathy wiki / Obsidian:** one page per pattern; preserve frontmatter; turn the
     `[[wikilinks]]` and typed edges into your link format; add a category index page.
   - **Vector store:** chunk each digest; carry the frontmatter as metadata (id, category,
     edges, cost) so filters and graph queries still work.
   - **`CLAUDE.md`:** a compact reference section + the 7 decision guides inline.
3. **Preserve the three things that are the catalog's value:** the **relationship graph**
   (`requires` / `conflicts_with` / `composes_with`), the **decision guides**, and the
   **conflict map**. A flat list of 94 patterns loses most of the value.
4. **Relabel freely** — the field names are suggestions; map them onto your schema
   (`ingest.json` → `field_glossary` documents each one).

## Provenance
These are **derived digests**. The authoritative sources are `../patterns/*.md` and
`../build/content/CHAPTER-0.md` — each unit's `canonical:` field points home. Load the
digests for working memory; follow `canonical:` when you need the full treatment.

*Prefer live queries over loading everything? Run the MCP server in `../mcp/` instead.*
