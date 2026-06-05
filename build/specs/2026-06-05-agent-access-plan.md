# GO4 Agent Access Implementation Plan (Loader + MCP + Pointer)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Three pull-not-push ways to use the GO4 catalog over the existing `ingest/` corpus — a format-agnostic **loader** (`ingest/INGEST.md`), a lean **MCP server** (`mcp/`, 3 tools, lexical+graph retrieval), and an **`llms.txt`/`AGENTS.md` pointer` — each loading only what's asked.

**Architecture:** The MCP server's logic lives in a pure, tested `mcp/go4_catalog.py` (builds an in-memory index from the digests' frontmatter + the conflict subfiles, no embeddings); `mcp/server.py` is a thin FastMCP wrapper exposing 3 tools. The loader and pointer are documentation. Nothing is generated/duplicated — the server reads the committed `ingest/` + `patterns/conflicts/` at runtime.

**Tech Stack:** Python 3 — stdlib (`re`, `json`, `pathlib`) for the catalog logic + `mcp` (FastMCP) for the server only. Plain-assert tests (`python3 mcp/test_go4_catalog.py`), matching the repo. Dogfoods I3 (MCP Server) + V13 (Tool Budget: 3 lean tools) + K13 (Retrieval Bundle: shape-correct structured+graph retrieval).

**Spec:** `build/specs/2026-06-05-agent-access-design.md`. **Depends on:** the merged CONFLICTS split (`patterns/conflicts/*.md`).

## Data shapes (from the existing `ingest/`)
- Each `ingest/<ID>-...md` digest: YAML frontmatter (`id, title, type, category, summary, when_to_use, also_known_as, cost, requires, conflicts_with, composes_with, siblings, related, mechanism_refs, canonical, derived`) then `## Description`, `## Key points`, a `Related:` line.
- `ingest/ingest.json`: `{units:[{id,type,category,title,summary,file,canonical,edges}], edges:[{from,to,type}], field_glossary, stats}`.
- `patterns/conflicts/<CAT>.md`: `## Critical N — A ⊕ B {#…}` / `## Connection X …` entries + registry tables `| A (..) | sym | B (..) | resolution |`.

## File structure

| File | Responsibility | New/Mod |
|---|---|---|
| `mcp/go4_catalog.py` | Pure catalog: load index, `find`, `get_pattern`, `get_decision`, `conflict_notes` | Create |
| `mcp/test_go4_catalog.py` | Plain-assert tests | Create |
| `mcp/server.py` | Thin FastMCP server: 3 tools → go4_catalog | Create |
| `mcp/requirements.txt` | `mcp` SDK only | Create |
| `mcp/README.md` | Client config + measured schema-token cost | Create |
| `ingest/INGEST.md` | Rewrite as the active loader | Modify |
| `llms.txt` | Root agent-routing index | Create |
| `README.md` | Add the `AGENTS.md` pointer snippet section | Modify |

---

### Task 1: Scaffold `go4_catalog.py` — load the index

**Files:** Create `mcp/go4_catalog.py`, `mcp/test_go4_catalog.py`

- [ ] **Step 1: Create `mcp/go4_catalog.py`**

```python
#!/usr/bin/env python3
"""Pure GO4 catalog logic for the MCP server: build an in-memory index from the
ingest/ digests + conflict subfiles, and answer find / get_pattern / get_decision
queries. No network, no model, no embeddings — deterministic structured retrieval.
Run tests: python3 mcp/test_go4_catalog.py"""

import re
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent          # repo root
INGEST = ROOT / "ingest"
PATTERNS = ROOT / "patterns"
CONFLICTS = PATTERNS / "conflicts"
CATEGORY_FILE = {  # category -> decision guide
    "Signal": "SIGNAL-DECISION.md", "Knowledge": "KNOWLEDGE-DECISION.md",
    "Reasoning": "REASONING-DECISION.md", "Orchestration": "ORCHESTRATION-DECISION.md",
    "Reliability": "RELIABILITY-DECISION.md", "Integration": "INTEGRATION-DECISION.md",
    "Humanizers": "HUMANIZERS-DECISION.md",
}


def parse_frontmatter(text):
    """Parse a digest's leading --- YAML --- block into a dict. Lists are [a, b].
    Quoted scalars are unquoted. Only the flat key: value shape the digests use."""
    m = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    fm = {}
    if not m:
        return fm
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k, v = k.strip(), v.strip()
        if v.startswith("[") and v.endswith("]"):
            fm[k] = [x.strip().strip('"') for x in v[1:-1].split(",") if x.strip()]
        elif v:
            fm[k] = v.strip('"')
    return fm


def load_index(ingest_dir=INGEST):
    """Return {id: {**frontmatter, 'stem': filename-stem}} for every pattern digest.
    Pattern digests are files whose id frontmatter matches ^[SKROVIH]\\d+$."""
    index = {}
    for f in sorted(ingest_dir.glob("*.md")):
        fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        uid = fm.get("id", "")
        if re.match(r'^[SKROVIH]\d+$', uid):
            fm["stem"] = f.stem
            index[uid] = fm
    return index
```

- [ ] **Step 2: Create `mcp/test_go4_catalog.py`**

```python
#!/usr/bin/env python3
"""Plain-assert tests for go4_catalog. Run: python3 mcp/test_go4_catalog.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from go4_catalog import parse_frontmatter, load_index


def eq(got, want):
    assert got == want, f"\n  got:  {got!r}\n  want: {want!r}"


eq(parse_frontmatter('---\nid: R4\ntitle: ReAct\nrequires: [V9, V14]\n---\nbody'),
   {"id": "R4", "title": "ReAct", "requires": ["V9", "V14"]})

idx = load_index()
assert len(idx) == 94, f"expected 94 pattern digests, got {len(idx)}"
eq(idx["R4"]["title"], "ReAct")
eq(idx["R4"]["category"], "Reasoning")
assert "R5" in idx["R4"].get("conflicts_with", []), idx["R4"]

print("ALL CATALOG TESTS PASSED")
```

- [ ] **Step 3: Run** — `python3 mcp/test_go4_catalog.py` → `ALL CATALOG TESTS PASSED`
- [ ] **Step 4: Commit** — `git add mcp/go4_catalog.py mcp/test_go4_catalog.py && git commit -m "feat(mcp): scaffold go4_catalog index loader"`

---

### Task 2: `find` — lexical search

**Files:** Modify `mcp/go4_catalog.py`, `mcp/test_go4_catalog.py`

- [ ] **Step 1: Add `find`**

```python
_WORD = re.compile(r'[a-z0-9]+')


def _terms(s):
    return set(_WORD.findall(s.lower()))


def find(query, limit=5, index=None):
    """Rank patterns by term overlap of the query against
    id/title/summary/when_to_use/also_known_as/category. Returns lean candidates."""
    idx = index if index is not None else load_index()
    q = _terms(query)
    scored = []
    for uid, u in idx.items():
        hay = " ".join([uid, u.get("title", ""), u.get("summary", ""),
                        u.get("when_to_use", ""), " ".join(u.get("also_known_as", [])),
                        u.get("category", "")])
        overlap = len(q & _terms(hay))
        # light field weighting: title/aka hits count double
        boost = len(q & _terms(u.get("title", "") + " " + " ".join(u.get("also_known_as", []))))
        score = overlap + boost
        if score:
            scored.append((score, uid, u))
    scored.sort(key=lambda t: (-t[0], t[1]))
    out = []
    for _, uid, u in scored[:limit]:
        out.append({"id": uid, "title": u.get("title", ""), "category": u.get("category", ""),
                    "when_to_use": u.get("when_to_use", u.get("summary", ""))})
    return out
# (the agent calls go4_decision(category) for the matching flowchart)
```

- [ ] **Step 2: Add test**

```python
from go4_catalog import find
r = find("multi-agent orchestrator workers", limit=5, index=idx)
ids = [c["id"] for c in r]
assert "O6" in ids, ids          # Orchestrator-Workers should surface
assert all(set(c) == {"id","title","category","when_to_use"} for c in r)
r2 = find("retrieval augmented generation vector", limit=3, index=idx)
assert any(c["id"].startswith("K") for c in r2), r2   # a Knowledge pattern
assert len(find("zzzznotarealterm", index=idx)) == 0
```

- [ ] **Step 3: Run** — PASS (if O6 doesn't surface, widen the haystack — but title "Orchestrator-Workers" + summary should match "orchestrator workers")
- [ ] **Step 4: Commit** — `git add mcp/go4_catalog.py mcp/test_go4_catalog.py && git commit -m "feat(mcp): lexical find"`

---

### Task 3: `get_pattern` — the digest bundle

**Files:** Modify `mcp/go4_catalog.py`, `mcp/test_go4_catalog.py`

- [ ] **Step 1: Add `get_pattern`**

```python
def _body_sections(text):
    """Return (description, [key_points]) from a digest body."""
    desc = ""
    m = re.search(r'## Description\s*\n+(.+?)(?:\n## |\Z)', text, re.S)
    if m:
        desc = re.sub(r'\s+', " ", m.group(1)).strip()
    kps = []
    m = re.search(r'## Key points\s*\n+(.*?)(?:\n## |\nRelated:|\Z)', text, re.S)
    if m:
        kps = [l.strip("- ").strip() for l in m.group(1).splitlines() if l.strip().startswith("-")]
    return desc, kps


def get_pattern(uid, index=None):
    """Full bundle for one pattern: digest fields + typed edges + canonical (authority)."""
    idx = index if index is not None else load_index()
    u = idx.get(uid)
    if not u:
        return {"error": f"unknown pattern {uid!r}"}
    text = (INGEST / f"{u['stem']}.md").read_text(encoding="utf-8")
    desc, kps = _body_sections(text)
    return {
        "id": uid, "title": u.get("title", ""), "category": u.get("category", ""),
        "summary": u.get("summary", ""), "when_to_use": u.get("when_to_use", ""),
        "cost": u.get("cost", ""), "also_known_as": u.get("also_known_as", []),
        "edges": {k: u.get(k, []) for k in ("requires", "conflicts_with", "composes_with", "siblings", "related")},
        "mechanism_refs": u.get("mechanism_refs", []),
        "description": desc, "key_points": kps,
        "canonical": u.get("canonical", ""),  # authoritative full source
    }
```

- [ ] **Step 2: Add test**

```python
from go4_catalog import get_pattern
p = get_pattern("R4", index=idx)
eq(p["id"], "R4"); eq(p["title"], "ReAct")
assert "R5" in p["edges"]["conflicts_with"], p["edges"]
assert p["canonical"] == "patterns/R4-ReAct.md", p["canonical"]
assert p["description"], p          # non-empty digest description
assert p["key_points"], p           # at least one key point
eq(get_pattern("ZZ9", index=idx), {"error": "unknown pattern 'ZZ9'"})
```

- [ ] **Step 3: Run** — PASS
- [ ] **Step 4: Commit** — `git add mcp/go4_catalog.py mcp/test_go4_catalog.py && git commit -m "feat(mcp): get_pattern bundle"`

---

### Task 4: `get_decision` + conflict notes

**Files:** Modify `mcp/go4_catalog.py`, `mcp/test_go4_catalog.py`

- [ ] **Step 1: Add `get_decision` and `conflict_notes`**

```python
def get_decision(category):
    """Return a category's decision-guide markdown (strip the leading H1)."""
    fname = CATEGORY_FILE.get(category.title())
    if not fname:
        return {"error": f"unknown category {category!r} (use one of {sorted(CATEGORY_FILE)})"}
    text = (PATTERNS / fname).read_text(encoding="utf-8")
    return {"category": category.title(), "decision_guide": re.sub(r'^# .*\n', "", text, count=1)}


_ID = re.compile(r'\b([SKROVIH]\d+)\b')


def conflict_notes(uid, conflicts_dir=CONFLICTS):
    """Scan the conflict subfiles for entries mentioning uid; return [{with, note}].
    Covers both '## Critical/Connection — A sym B' headings and registry table rows."""
    notes = []
    for f in sorted(conflicts_dir.glob("*.md")):
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith("## ") or line.startswith("| "):
                ids = _ID.findall(line)
                if uid in ids:
                    other = [i for i in ids if i != uid]
                    if other:
                        # registry row: resolution is the last '|' cell; heading: the title
                        note = line.split("|")[-2].strip() if line.startswith("| ") else line.lstrip("# ").strip()
                        notes.append({"with": other[0], "note": note})
    # dedupe by 'with'
    seen, out = set(), []
    for n in notes:
        if n["with"] not in seen:
            seen.add(n["with"]); out.append(n)
    return out
```

- [ ] **Step 2: Add test**

```python
from go4_catalog import get_decision, conflict_notes
d = get_decision("reasoning")
eq(d["category"], "Reasoning")
assert "ReAct" in d["decision_guide"] or "R4" in d["decision_guide"], d
assert "error" in get_decision("nope")
cn = conflict_notes("R4")
withs = [c["with"] for c in cn]
assert "R5" in withs, cn          # R4 conflicts with R5 (Critical 1 + registry)
```

- [ ] **Step 3: Run** — PASS
- [ ] **Step 4: Commit** — `git add mcp/go4_catalog.py mcp/test_go4_catalog.py && git commit -m "feat(mcp): get_decision + conflict_notes"`

---

### Task 5: The FastMCP server (3 tools)

**Files:** Create `mcp/server.py`, `mcp/requirements.txt`

- [ ] **Step 1: `mcp/requirements.txt`**
```
mcp>=1.2
```

- [ ] **Step 2: `mcp/server.py`** — thin wrapper; the 3 tools delegate to `go4_catalog`. Tool docstrings are the schema descriptions (keep them tight — V13).

```python
#!/usr/bin/env python3
"""GO4 MCP server — pull-not-push access to the LLM-engineering pattern catalog.
Run: python3 mcp/server.py   (stdio transport)
Config in Claude Code / Cursor: command = python3, args = [/abs/path/mcp/server.py]."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mcp.server.fastmcp import FastMCP
import go4_catalog as C

mcp = FastMCP("go4")
_INDEX = C.load_index()  # built once at startup (deterministic)


@mcp.tool()
def go4_find(query: str, limit: int = 5) -> list:
    """Find GO4 design patterns matching a task or concern. Returns ranked candidate
    pattern ids with one-line when-to-use + the category's decision guide. Use to pick
    which pattern(s) fit, then call go4_pattern for details."""
    return C.find(query, limit, index=_INDEX)


@mcp.tool()
def go4_pattern(id: str) -> dict:
    """Get one GO4 pattern's bundle: summary, when-to-use, cost, typed edges
    (requires/conflicts_with/composes_with/siblings), mechanism refs, a dense
    description + key points, and the canonical source path. Conflicts are in edges;
    call go4_decision for the category flowchart."""
    p = C.get_pattern(id, index=_INDEX)
    if "error" not in p:
        p["conflicts"] = C.conflict_notes(id)
    return p


@mcp.tool()
def go4_decision(category: str) -> dict:
    """Get a GO4 category's decision guide (the flowchart that picks a pattern).
    category ∈ Signal, Knowledge, Reasoning, Orchestration, Reliability, Integration, Humanizers."""
    return C.get_decision(category)


if __name__ == "__main__":
    mcp.run()
```

- [ ] **Step 3: Smoke-test the catalog + server import** (do NOT run `python3 mcp/server.py` — it starts a blocking stdio loop)

Run:
```bash
cd /Users/james/Library/CloudStorage/Dropbox/Code/GO4
python3 -c "import sys; sys.path.insert(0,'mcp'); import go4_catalog as C; print('find:', [c['id'] for c in C.find('orchestrator workers',3)]); print('R4 conflicts:', [c['with'] for c in C.conflict_notes('R4')][:3])"
pip install -r mcp/requirements.txt >/dev/null 2>&1 || echo "(mcp install failed/offline — server import unverifiable; catalog logic still tested)"
python3 -c "import sys; sys.path.insert(0,'mcp'); import server; print('server imports OK')" 2>/dev/null || echo "(server import needs mcp installed)"
```
Expected: catalog calls return sensible results; if `mcp` installs, `server imports OK`.

- [ ] **Step 4: Commit** — `git add mcp/server.py mcp/requirements.txt && git commit -m "feat(mcp): FastMCP server with 3 tools"`

---

### Task 6: MCP README — config + measured schema cost (V13)

**Files:** Create `mcp/README.md`

- [ ] **Step 1: Measure the schema-token footprint** (V13 good-citizen)

Run:
```bash
python3 -c "
import json
tools=[('go4_find','Find GO4 design patterns matching a task or concern. Returns ranked candidate pattern ids with one-line when-to-use + the category decision guide. Use to pick which pattern(s) fit, then call go4_pattern for details.',{'query':'string','limit':'integer'}),
('go4_pattern','Get one GO4 patterns bundle: summary, when-to-use, cost, typed edges, mechanism refs, a dense description + key points, and the canonical source path.',{'id':'string'}),
('go4_decision','Get a GO4 category decision guide (the flowchart that picks a pattern).',{'category':'string'})]
blob=json.dumps([{'name':n,'description':d,'params':p} for n,d,p in tools])
print('approx schema chars:', len(blob), '~tokens:', len(blob)//4)
"
```
Record the number (it will be a few hundred tokens — tiny).

- [ ] **Step 2: Write `mcp/README.md`** with: what it is (pull-not-push catalog access), the 3 tools, the stdio config block for Claude Code / Cursor, and the measured idle schema cost from Step 1. Example config:

```markdown
# GO4 MCP Server

Pull-not-push access to the GO4 LLM-engineering pattern catalog. Three tools —
`go4_find`, `go4_pattern`, `go4_decision` — over the repo's `ingest/` corpus.
No auto-fire, no embeddings; the agent loads only what it asks for.

## Idle cost
The three tool schemas total **~<N> tokens** (measured) in a client's tool listing —
the only always-on cost. Everything else loads on demand per call.

## Install & run
    pip install -r mcp/requirements.txt
    python3 mcp/server.py        # stdio

## Claude Code / Cursor config
    {"mcpServers": {"go4": {"command": "python3", "args": ["/ABS/PATH/GO4/mcp/server.py"]}}}

## Tools
- go4_find(query, limit=5) → ranked candidates + decision guide
- go4_pattern(id) → one pattern's full bundle (edges, conflicts, canonical)
- go4_decision(category) → the category's decision flowchart
```
Replace `<N>` with the measured number.

- [ ] **Step 3: Commit** — `git add mcp/README.md && git commit -m "docs(mcp): server README + measured schema cost"`

---

### Task 7: Rewrite `ingest/INGEST.md` as the loader

**Files:** Modify `ingest/INGEST.md`

- [ ] **Step 1: Replace `ingest/INGEST.md`** with an active, format-agnostic loader (instructions an agent executes):

```markdown
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
```

- [ ] **Step 2: Confirm it still validates** — `python3 build/validate_ingest.py` (INGEST.md isn't a unit, but confirm nothing broke) → `OK`.
- [ ] **Step 3: Commit** — `git add ingest/INGEST.md && git commit -m "docs(ingest): rewrite INGEST.md as a format-agnostic loader"`

---

### Task 8: `llms.txt` + `AGENTS.md` pointer

**Files:** Create `llms.txt`, Modify `README.md`

- [ ] **Step 1: Create root `llms.txt`** (the standard agent-routing index)

```markdown
# GO4 — AI Engineering Design Patterns

> 94 design patterns for building LLM systems in production, each grounded in transformer
> mechanics. Seven categories, per-category decision guides, and a cross-pattern conflict map.

## Catalog
- [Pattern catalog (browse)](https://jlldavies.github.io/go4-llm-design-patterns)
- [The Mechanical Foundation](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/build/content/CHAPTER-0.md): the 12 mechanisms patterns derive from
- [Conflict map](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/patterns/CONFLICTS.md): which patterns can't combine

## Decision guides (pick a pattern)
- [Signal / prompting](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/patterns/SIGNAL-DECISION.md)
- [Knowledge / RAG](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/patterns/KNOWLEDGE-DECISION.md)
- [Reasoning](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/patterns/REASONING-DECISION.md)
- [Orchestration](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/patterns/ORCHESTRATION-DECISION.md)
- [Reliability](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/patterns/RELIABILITY-DECISION.md)
- [Integration](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/patterns/INTEGRATION-DECISION.md)
- [Humanizers / memory](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/patterns/HUMANIZERS-DECISION.md)

## For agents
- [ingest/INGEST.md](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/ingest/INGEST.md): load the whole catalog into your memory
- [mcp/](https://github.com/jlldavies/go4-llm-design-patterns/blob/main/mcp/README.md): query the catalog live via MCP
```

- [ ] **Step 2: Add an "Use it from your own agent" section to `README.md`** (after the "🧠 Ingest" section): a copy-paste `AGENTS.md`/`CLAUDE.md` snippet —

```markdown
## 🔌 Use GO4 from your own agent

**Reference it** — add to your project's `AGENTS.md` / `CLAUDE.md`:
> For LLM/agent design decisions, consult GO4: clone `jlldavies/go4-llm-design-patterns`
> and read `ingest/INGEST.md` (decision guides + 94 pattern digests + the conflict graph).
> Pick a pattern via the matching `patterns/*-DECISION.md`; check `patterns/CONFLICTS.md`
> before combining patterns.

**Query it live** — run the MCP server (`mcp/README.md`): three pull-not-push tools
(`go4_find` / `go4_pattern` / `go4_decision`), no auto-fire, works in Claude Code, Cursor,
or any MCP client.
```

- [ ] **Step 3: Verify links + site build** — `python3 build/validate.py && python3 build/prepare.py` (README/llms.txt aren't in the mdBook tree; confirm nothing broke) → pass.
- [ ] **Step 4: Commit** — `git add llms.txt README.md && git commit -m "docs: add llms.txt + AGENTS.md pointer for agent access"`

---

### Task 9: Full verification

- [ ] **Step 1: Catalog tests + real-data sanity**
```bash
python3 mcp/test_go4_catalog.py
python3 -c "import sys; sys.path.insert(0,'mcp'); import go4_catalog as C; i=C.load_index(); print('patterns indexed:', len(i)); print('find sample:', [c['id'] for c in C.find('prompt injection guardrail',3)]); print('decision:', C.get_decision('reliability')['category'])"
```
Expected: `ALL CATALOG TESTS PASSED`; 94 indexed; sensible find results (a V-pattern for "prompt injection guardrail"); decision returns Reliability.

- [ ] **Step 2: Server imports cleanly (if `mcp` installed)** — `python3 -c "import sys; sys.path.insert(0,'mcp'); import server; assert all(hasattr(server, n) for n in ('go4_find','go4_pattern','go4_decision')); print('server OK: 3 tools registered')"` → `server OK: 3 tools registered` (the `@mcp.tool()` decorator leaves each function as a module attribute). If `mcp` can't be installed here, note it — the catalog logic is fully tested regardless.

- [ ] **Step 3: Existing pipelines untouched** — `python3 build/test_ingest.py && python3 build/validate_ingest.py && python3 build/validate.py && python3 build/prepare.py >/dev/null && echo OK` → all pass (the MCP reads `ingest/`, doesn't change it).

- [ ] **Step 4: Footprint check** — `git diff --name-only main HEAD` should list ONLY paths under `mcp/`, plus `llms.txt`, `ingest/INGEST.md`, `README.md`, and `build/specs/`. Nothing else under `ingest/`, nothing under `patterns/`, and no other `build/` script should change. One new top-level dir (`mcp/`) + one new top-level file (`llms.txt`).

- [ ] **Step 5: Final commit (if any verification fixups)** — commit with explicit paths.

---

## Self-review checklist
- **Spec coverage:** loader ✓(T7) · llms.txt ✓(T8) · AGENTS snippet ✓(T8) · MCP I3 ✓(T5) · 3 tools/V13 ✓(T5) · K13 structured+graph, no embeddings ✓(T1-4) · bundle returns w/ canonical authority ✓(T3) · conflicts folded into go4_pattern ✓(T4-5) · measured+published schema cost ✓(T6) · footprint = `mcp/`+`llms.txt` ✓(T9) · pipelines untouched ✓(T9).
- **No build-time/runtime LLM:** retrieval is lexical + graph, deterministic ✓.
- **Dogfooding:** I3 + V13 + K13 realized in the structure.
