# GO4 Agent Access — Design Spec (Loader + MCP + Pointer)

**Date:** 2026-06-05
**Status:** Draft for review
**Depends on:** CONFLICTS refactor (`2026-06-05-conflicts-refactor-design.md`) — the MCP and loader consume the split conflicts.
**Supersedes:** the plugin design (`2026-06-04-go4-plugin-design.md`) — dropped after the criticism pass (plugin skills can't be made pull-not-push; auto-fire fights the token goal).

---

## 1. Purpose

Three **pull-not-push** ways for an agent to use the GO4 catalog, each loading only what is asked for — honoring the #1 goal: **minimize the consumer's token use**. All three are built over the existing `ingest/` corpus + the split conflicts; they add no pattern content. No auto-fire, no marketplace push — *those who want it can find it.*

## 2. The three access modes (separated by role)

| Mode | File(s) | Role |
|---|---|---|
| **Loader** | `ingest/INGEST.md` (rewritten) | Point your agent at it **once**; it loads the whole catalog into **your** memory format (Karpathy wiki, Obsidian, vector store, `CLAUDE.md`). Active, format-agnostic ingestion assistant. |
| **MCP server** | `mcp/` | Live, precise **pull-query** — `go4_find` / `go4_pattern` / `go4_decision` — for agents that want on-demand lookup, not pre-loaded memory. Works in any MCP client. |
| **Pointer** | root `llms.txt` + `AGENTS.md` snippet | Lightweight "reference GO4 from your project" — for those who just want a link. |

These do **not** overlap: the loader fills *your* memory once; the MCP answers live queries; the pointer is a reference link. (This is the separation you flagged — the ingest file is a loader, not an entry point.)

## 3. Design principles

1. **Token-minimization is the goal.** Pull-not-push; load only what's asked; lean returns.
2. **Dogfooded.** Built with GO4's own patterns — **I3 MCP Server + V13 Tool Budget + K13 Retrieval Bundle** (+ K1-over-K9, S6, K6, I1). The distribution mechanism obeys the catalog it serves (as `ingest/` is itself a clean K12).
3. **Derived from `ingest/`.** The corpus is the lean digests + `ingest.json` + the split `conflicts/`. No new content, no duplication; the server is pure read-logic.
4. **Deterministic.** No build-time or runtime LLM in the server — retrieval is lexical/structured + graph traversal. Reproducible.
5. **Pipelines untouched.** Site/PDF/ingest builds unaffected.

---

## 4. A — Loader + Pointer

### 4.1 Loader — rewrite `ingest/INGEST.md` as an active loader

Today `INGEST.md` is a passive description. Rewrite it as instructions an agent executes to load GO4 into the user's memory:

- **What it loads:** the 94 pattern digests, 12 mechanism digests, 7 decision guides, the conflict map (`patterns/conflicts/*.md` + the edge graph in `ingest.json`), and `references.md`.
- **How to load (adapt to the user's format):** detect or ask the memory system, then create one note/record/chunk per unit —
  - *Karpathy wiki:* one page per pattern, `[[wikilinks]]` for edges, a category index page.
  - *Obsidian:* one note per pattern, frontmatter preserved (Dataview-ready), `[[links]]` resolve.
  - *Vector store:* chunk each digest, carry frontmatter as metadata.
  - *`CLAUDE.md`:* a compact reference section + pointers to the decision guides.
- **Preserve the three things that are the catalog's value:** the **relationship graph** (`requires`/`conflicts_with`/`composes_with`), the **decision guides** (routing logic), and the **conflict map**.
- **Manifest-driven:** `ingest.json` is the index (units + the full edge graph + field glossary) — use it to drive the load.
- **Provenance:** these are derived digests; `patterns/*.md` + `CHAPTER-0.md` are canonical (each unit's `canonical:` points home).

### 4.2 `llms.txt` (repo root, also served on the Pages site)

The standard agent-routing index: the 7 categories, the decision guides, and links (to the site + `ingest/`). A fetch-this-file routing map for agents that discover GO4 on the web.

### 4.3 `AGENTS.md` / `CLAUDE.md` snippet

A copy-paste block (documented in README + the loader) to wire GO4 into a user's own agent context in one line — points at `ingest/INGEST.md` (to load) or the MCP (to query).

---

## 5. B — The MCP server (the dogfooded core)

### 5.1 Vehicle — **I3 MCP Server**
Python **FastMCP**, **stdio** transport, **local** (reads the repo's `ingest/` + `ingest.json` + `patterns/conflicts/`). Multi-client by construction (Claude Code, Cursor, Windsurf, any MCP/SDK agent) — which is the *only* justification I3's decision guide accepts here (standardised multi-client reach, not tool count or credentials). Execution is deterministic (an I1 lookup under the protocol).

### 5.2 Tools — **V13 Tool Budget: 3 lean tools**

| Tool | Input | Returns (bundle) |
|---|---|---|
| `go4_find` | `query: str, limit: int = 5` | ranked candidates `[{id, title, category, when_to_use, decision_guide}]` + a flag if any two candidates conflict. *(tiny)* |
| `go4_pattern` | `id: str` | `{summary, description, key_points, edges{requires, conflicts_with, composes_with, siblings}, conflicts:[{with, type, note}], mechanism_refs, cost, canonical}` — **conflicts folded in here** (no separate tool, per V13). *(one lean digest)* |
| `go4_decision` | `category: str` | the category's decision-guide flowchart. *(one compact guide)* |

Schemas minimal, descriptions compact, results bounded (`limit`).

### 5.3 Retrieval — **K13 shape-correct: structured + graph, no embeddings**
Structured field-search over `ingest.json` (`title`, `summary`, `when_to_use`, `also_known_as`, `category`) with a small relevance ranking, plus **graph traversal** over the edge list for relationships and conflicts. **No vector embeddings** — K13's shape table is explicit that vector search is the wrong primitive for structured + relational data, which is exactly what the catalog is. Deterministic; the server builds an in-memory index from `ingest.json` + the digests at startup.

### 5.4 Returns — **K13 / S6 / K6**
Bundle-shaped, **authority-labeled** (`canonical:` = authoritative full source vs the digest = derived), bounded and lean — never raw file dumps. `go4_find` returns one-liners; `go4_pattern` returns one digest + edges + its conflict notes (pulled from `patterns/conflicts/*.md`).

### 5.5 Token discipline — **V13 good-citizen**
Measure the total `tools/list` schema-token footprint and **publish it in the MCP README** so consumers can budget it ("an unmeasured server is an unowned cost"). 3 tools, lean schemas, bounded returns.

### 5.6 Structure & deps
```
mcp/                          ← one new top-level dir
  server.py                   FastMCP server (3 tools)
  search.py                   lexical field-search + graph traversal over ingest.json
  test_mcp.py                 plain-assert tests over search/retrieval (repo style)
  requirements.txt            the MCP SDK only
  README.md                   one-line client config + the measured schema-token cost
```
Reads `../ingest/`, `../ingest.json`, `../patterns/conflicts/` at runtime. No generation step — pure read-logic.

---

## 6. Pattern grounding (the dogfooding map)

| Pattern | What it dictates here |
|---|---|
| **I3 MCP Server** | The vehicle; justified by multi-client reach; stdio/local; deterministic I1 execution. |
| **V13 Tool Budget** | 3 tools, lean schemas, conflicts folded into `go4_pattern`, **measure + publish** the schema footprint, bound returns. |
| **K13 Retrieval Bundle** | Structured + graph retrieval (no embeddings — shape-correct); bundle-shaped, authority-labeled returns. |
| **K1 over K9** | Retrieve/pull, don't load the whole catalog into context (M2's n² cost). |
| **S6 / K6 / I1 / M2·M9** | Templated structured returns; lean digest payloads; deterministic retrieval; the `ingest/`+manifest "exact-store" tier read cheaply. |

**Conflict check (CONFLICTS.md):** **I3 ⊕ V13 — Critical 6** — resolved by *being* the disciplined small server (3 tools, measured schema, lean returns). No other tensions.

The payoff: GO4-the-MCP is a worked example of **I3 + V13 + K13**, as `ingest/` is of **K12** — the repo demonstrates its own catalog.

---

## 7. Footprint & distribution

- **Footprint:** one new top-level `mcp/` dir + a root `llms.txt`; modified `ingest/INGEST.md` (→ loader) + a README snippet. Reads `ingest/` + `conflicts/`. **Site/PDF/ingest pipelines untouched.**
- **Distribution:** clone the repo, run the MCP server (stdio config block in the MCP README — copy into Claude Code / Cursor settings). `llms.txt` ships on the Pages site. `INGEST.md` is the loader anyone points an agent at. No marketplace, no install step.

## 8. Out of scope (v1)

- Semantic/vector search (lexical is shape-correct *and* leaner — K13).
- Plugin/marketplace packaging (dropped — pull-not-push).
- `pip`-installable MCP package (clone-and-run for v1).
- A 4th conflicts tool (folded into `go4_pattern`).
- Harvesting the full conflict registry into the edge graph (inherited from the `ingest/`/CONFLICTS scope).

## 9. Success criteria

- **Loader:** pointing an agent at `ingest/INGEST.md` loads the catalog into a chosen memory format, preserving the graph + decision guides + conflict map.
- **MCP:** `go4_find` / `go4_pattern` / `go4_decision` work in Claude Code and one other MCP client; retrieval is deterministic; the total `tools/list` footprint is **measured, published, and small**.
- **Token budget:** a "which pattern?" round-trip (`go4_find` → one `go4_pattern`) costs ~hundreds of tokens, not the whole catalog.
- `llms.txt` + the `AGENTS.md` snippet are present and accurate.
- Site/PDF/ingest builds still pass; no top-level footprint beyond `mcp/` + `llms.txt`.
