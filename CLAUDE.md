# GO4 — AI Engineering Design Patterns

Last reviewed: 2026-07-21

GO4 is a published catalog of 94 LLM-engineering design patterns: a typeset book
(`GO4.pdf`), an online mdBook edition (GitHub Pages), an ingestible projection for loading
into agent memory (`ingest/`), an Agent Skill (`skills/go4`), and a Python MCP server
(`mcp/`). This repo is the source of all of that. See `README.md` for the public-facing
overview.

## Read first

The single rule that governs everything here: **`patterns/`, `research/`, and
`build/content/` are the source; `ingest/`, `GO4.pdf`, the mdBook site, and the conflict
projections are GENERATED.** Never hand-edit a generated artifact — change the source and
regenerate. Editing `ingest/*.md` or `GO4.pdf` directly is lost on the next build and
desyncs the catalog from its projection.

Every pattern is a markdown file in `patterns/` carrying frontmatter (id, category,
`when_to_use`, typed edges such as `conflicts_with` / `composes_with`, cost,
`mechanism_refs`, canonical) plus a description, key points, and `[[wikilinks]]`. The
relationship graph in `ingest/ingest.json` is derived from that frontmatter.

## Start here

Repo layout (full tree in `README.md` → Repo Structure):

- `patterns/` — the catalog: 94 pattern files, the seven category overviews + decision
  guides, and `CONFLICTS.md` (cross-pattern tensions).
- `research/MECHANISMS.md` — the folk-claim → mechanism → evidence mapping (the "why").
- `ingest/` — generated projection: one unit per pattern/mechanism/decision guide, plus
  `ingest.json` (the machine manifest) and `INGEST.md` (load recipes).
- `build/` — everything that builds the PDF, the site, the ingest projection, and the
  conflict map, with validators and tests.
- `mcp/` — a Python MCP server exposing the catalog. `skills/go4` — the Agent Skill.
- `doc-system/DESIGN.md` — how the doc system is designed.

The working loop when you change the catalog: edit the source in `patterns/` (or
`research/` / `build/content/`) → regenerate with the `build/` scripts
(`build_ingest.py`, `build_conflicts.py`, `build_book.py`) → validate
(`build/validate.py`, `build/validate_conflicts.py`) → run the `build/test_*.py` tests.

## Working norms

- Source vs generated: only ever edit under `patterns/`, `research/`, `build/content/`,
  `mcp/`, `skills/`, `doc-system/`. Regenerate `ingest/` and the book/site outputs; do not
  hand-edit them.
- Check `patterns/CONFLICTS.md` before recommending or documenting a combination of
  patterns — that check is not optional (it is the same rule the workspace applies when
  using GO4 for design work).
- Keep frontmatter schema-valid and the `[[wikilinks]]` / typed-edge graph internally
  consistent; `build/validate.py` and `build/validate_conflicts.py` enforce this.
- A new or changed pattern is not done until ingest, conflicts, and the book regenerate
  cleanly and the `build/test_*.py` suite passes.

## Related docs

- `README.md` — public overview, install, repo structure.
- `ingest/INGEST.md` — how to load the catalog into agent memory (Karpathy wiki, Obsidian,
  vector store, Claude Code).
- `patterns/CONFLICTS.md` — the conflict map (must-read before combining patterns).
- `research/MECHANISMS.md` — the mechanical foundation.
- `doc-system/DESIGN.md` — doc-system design. `mcp/README.md` — the MCP server.
- Workspace `working/SESSION-STANDARDS.md` names GO4 as the design basis for multi-step /
  orchestration work.

## MCP servers

This repo PROVIDES a project-scoped MCP server: a Python stdio server under `mcp/`
(`server.py` + `go4_catalog.py`, deps in `mcp/requirements.txt`, tests in
`mcp/test_go4_catalog.py`) that exposes the pattern catalog for query. There is no
committed `.mcp.json` (the registration path is machine-specific); consumers register
`mcp/server.py` via `claude mcp add`. See `mcp/README.md`.

## Session close

This repo has no session-state to hand off. When work changes the catalog, the closing
step is mechanical: regenerate `ingest/` and the book/site from source, run
`build/validate.py` and the `build/test_*.py` suite, and commit source plus regenerated
outputs together so the projection never lags the source.
