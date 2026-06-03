# GO4 Ingest Layer — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Generate a derived, ingestible `ingest/` folder (one markdown unit per pattern/mechanism/decision-guide, plus `ingest.json`, `index.md`, `INGEST.md`, `references.md`) from the existing canonical source, so anyone can clone the repo and load the whole catalog into an agent memory system.

**Architecture:** A pure-function extraction/assembly library (`build/ingest_lib.py`) tested by `build/test_ingest.py`, driven by an orchestrator (`build/build_ingest.py`) that reads canonical source + a curated `build/ingest-meta.json` and writes the `ingest/` artifact. A `build/validate_ingest.py` gate checks integrity. Mirrors the existing `linkify.py`(lib) + `build_book.py`(orchestrator) + `test_linkify.py`(tests) split. Source files are read-only inputs; `ingest/` is a committed artifact like `GO4.pdf`.

**Tech Stack:** Python 3 stdlib only (`re`, `json`, `pathlib`) — no new dependencies, matching the existing build. Reuses `build/linkify.py`. Tests are plain-assert scripts run with `python3`.

---

## Decisions that refine the spec (flag for reviewer)

1. **Meta file is JSON, not YAML.** The spec wrote `ingest-meta.yaml`; this plan uses `build/ingest-meta.json` so the build stays **stdlib-pure** (no `pyyaml`), consistent with every existing `build/*.py`. The file is bootstrap-generated then hand-reviewed; JSON edits fine for that. Switch back to YAML only if you want nicer hand-editing and accept the dependency.
2. **Plan & spec live in `build/specs/`**, not `docs/superpowers/` (the skill default), because `docs/` is gitignored in this repo.

## File structure

| File | Responsibility | New/Mod |
|---|---|---|
| `build/ingest_lib.py` | Pure extraction + assembly functions (no I/O) | Create |
| `build/test_ingest.py` | Plain-assert tests for `ingest_lib` | Create |
| `build/ingest-meta.json` | Curated per-pattern metadata (edges, cost, summary) — bootstrap-generated, reviewed | Create |
| `build/build_ingest.py` | Orchestrator: read source + meta → write `ingest/` | Create |
| `build/validate_ingest.py` | Integrity gate over generated `ingest/` | Create |
| `ingest/` | Generated artifact (units + manifest + readme) | Create (committed) |
| `README.md` | Add prominent "Ingest" section + Repo Structure + Start Here | Modify |

Pattern-id convention: the leading `[A-Z]+\d+` of a filename (`R4-ReAct.md` → id `R4`, stem `R4-ReAct`). Edge targets and wikilinks use ids/stems.

---

### Task 1: Scaffold the lib, test runner, and output dir

**Files:**
- Create: `build/ingest_lib.py`
- Create: `build/test_ingest.py`

- [ ] **Step 1: Create `build/ingest_lib.py` with header and id helpers**

```python
#!/usr/bin/env python3
"""Pure extraction + assembly functions for the GO4 ingest layer.
No I/O — callers in build_ingest.py read/write files. Run tests: python3 build/test_ingest.py
"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from linkify import _MECH, _NUM  # reuse the mechanism-citation regexes

ID_RE = re.compile(r'^([A-Z]+\d+)\b')
CATEGORY = {  # id-prefix letter -> category name
    "S": "Signal", "K": "Knowledge", "R": "Reasoning", "O": "Orchestration",
    "V": "Reliability", "I": "Integration", "H": "Humanizers",
}


def unit_id(stem: str) -> str:
    """'R4-ReAct' -> 'R4'. Raises if no leading id."""
    m = ID_RE.match(stem)
    if not m:
        raise ValueError(f"no id in {stem!r}")
    return m.group(1)


def category_of(uid: str) -> str:
    return CATEGORY[uid[0]]
```

- [ ] **Step 2: Create `build/test_ingest.py` skeleton (matches `test_linkify.py` style)**

```python
#!/usr/bin/env python3
"""Plain-assert tests for ingest_lib.py. Run: python3 build/test_ingest.py"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from ingest_lib import unit_id, category_of


def eq(got, want):
    assert got == want, f"\n  got:  {got!r}\n  want: {want!r}"


# --- ids ---
eq(unit_id("R4-ReAct"), "R4")
eq(unit_id("K13-Retrieval-Bundle"), "K13")
eq(category_of("R4"), "Reasoning")
eq(category_of("H10"), "Humanizers")

print("ALL INGEST TESTS PASSED")
```

- [ ] **Step 3: Run the tests, verify they pass**

Run: `python3 build/test_ingest.py`
Expected: `ALL INGEST TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add build/ingest_lib.py build/test_ingest.py
git commit -m "feat(ingest): scaffold ingest_lib with id/category helpers"
```

---

### Task 2: Extract `also_known_as`, `title`, and `intent`

**Files:**
- Modify: `build/ingest_lib.py`
- Modify: `build/test_ingest.py`

Real source shapes (from `patterns/R4-ReAct.md`): line 1 `# R4 — ReAct`; an `**Also Known As:** Reason+Act, Reason-and-Act Loop, ...` line; an `## Intent` section whose first paragraph is the digest source.

- [ ] **Step 1: Add the three extractors to `ingest_lib.py`**

```python
def title_of(text: str) -> str:
    """'# R4 — ReAct' -> 'ReAct'."""
    first = text.splitlines()[0].lstrip("# ").strip()
    m = re.match(r'[A-Z]+\d+\s*(?:—\s*)?(.+)', first)
    return m.group(1).strip() if m else first


def also_known_as(text: str) -> list:
    """Parse the '**Also Known As:** a, b, c' line into a list (stops at first sentence/paren)."""
    m = re.search(r'\*\*Also Known As:\*\*\s*(.+)', text)
    if not m:
        return []
    raw = m.group(1)
    raw = re.split(r'\.\s|\s*\(', raw, maxsplit=1)[0]  # drop trailing prose/parenthetical
    return [p.strip().rstrip(".") for p in raw.split(",") if p.strip()]


def intent_of(text: str) -> str:
    """First paragraph under '## Intent' (single line, whitespace-collapsed)."""
    m = re.search(r'^## Intent\s*\n+(.+?)(?:\n\n|\n##)', text, re.S | re.M)
    if not m:
        return ""
    return re.sub(r'\s+', " ", m.group(1)).strip()
```

- [ ] **Step 2: Add tests using real R4 strings**

```python
from ingest_lib import title_of, also_known_as, intent_of

R4_HEAD = "# R4 — ReAct\n"
eq(title_of(R4_HEAD), "ReAct")
eq(also_known_as("**Also Known As:** Reason+Act, Think-Act-Observe, the Agent Loop. (Function-calling agents...)"),
   ["Reason+Act", "Think-Act-Observe", "the Agent Loop"])
eq(intent_of("## Intent\n\nLet an agent make its next decision after seeing the result.\n\n## Motivation"),
   "Let an agent make its next decision after seeing the result.")
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python3 build/test_ingest.py`
Expected: `ALL INGEST TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add build/ingest_lib.py build/test_ingest.py
git commit -m "feat(ingest): extract title, also-known-as, intent"
```

---

### Task 3: Extract `mechanism_refs` (reuse linkify's regex)

**Files:**
- Modify: `build/ingest_lib.py`
- Modify: `build/test_ingest.py`

R4 cites "(mechanism 7)", "mechanism 2", "mechanisms 3 and 5", etc. `_MECH` from `linkify.py` already matches "mechanism(s) <numexpr>"; `_NUM` finds the integers.

- [ ] **Step 1: Add the extractor**

```python
def mechanism_refs(text: str) -> list:
    """Sorted unique mechanism numbers (1–12) cited anywhere in the text."""
    nums = set()
    for m in _MECH.finditer(text):
        for n in _NUM.findall(m.group(2)):
            v = int(n)
            if 1 <= v <= 12:
                nums.add(v)
    return sorted(nums)
```

- [ ] **Step 2: Add tests**

```python
from ingest_lib import mechanism_refs

eq(mechanism_refs("conditions on mechanism 4; see mechanisms 2 and 3, plus (mechanism 12)."), [2, 3, 4, 12])
eq(mechanism_refs("no citations here"), [])
eq(mechanism_refs("mechanism 99 is out of range"), [])
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python3 build/test_ingest.py`
Expected: `ALL INGEST TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add build/ingest_lib.py build/test_ingest.py
git commit -m "feat(ingest): extract mechanism_refs via linkify regex"
```

---

### Task 4: Extract typed edges from the "Related Patterns" section

**Files:**
- Modify: `build/ingest_lib.py`
- Modify: `build/test_ingest.py`

R4's Related Patterns bullets are labelled: `**Sibling of** **R5 ReWOO**`, `**Required by** **V9...**`, `**Pairs with** **V14...**`, `**Composes with** **K8...**`, `**Distinct from** **R3...**`. Map label → edge type; default unknown → `related`.

- [ ] **Step 1: Add the label map and parser**

```python
EDGE_LABELS = [  # (lowercase prefix, edge type) — order matters, first match wins
    ("sibling", "siblings"),
    ("required by", "requires"), ("requires", "requires"), ("depends on", "requires"),
    ("pairs with", "composes_with"), ("composes with", "composes_with"),
    ("inner pattern of", "composes_with"), ("often paired with", "composes_with"),
    ("managed by", "composes_with"), ("uses", "composes_with"),
    ("composes cleanly", "composes_with"), ("tool layer", "composes_with"),
    ("distinct from", "related"), ("not to be confused", "related"),
    ("named after", "related"), ("aligned with", "related"), ("echoes", "related"),
]
_REL_ID = re.compile(r'\b([A-Z]+\d+)\b')


def _edge_type(label: str) -> str:
    low = label.lower().strip()
    for prefix, etype in EDGE_LABELS:
        if low.startswith(prefix):
            return etype
    return "related"


def related_edges(text: str, self_id: str) -> dict:
    """Parse '## Related Patterns' bullets into {edge_type: [ids]} (deduped, no self)."""
    sec = re.search(r'^## Related Patterns\s*\n(.*?)(?:\n## |\Z)', text, re.S | re.M)
    edges = {}
    if not sec:
        return edges
    for line in sec.group(1).splitlines():
        if not line.lstrip().startswith("-"):
            continue
        lbl = re.match(r'\s*-\s*\*\*(.+?)\*\*', line)
        if not lbl:
            continue
        etype = _edge_type(lbl.group(1))
        ids = [i for i in _REL_ID.findall(line) if i != self_id]
        if ids:
            edges.setdefault(etype, [])
            for i in ids:
                if i not in edges[etype]:
                    edges[etype].append(i)
    return edges
```

- [ ] **Step 2: Add tests with real R4 bullets**

```python
from ingest_lib import related_edges, _edge_type

eq(_edge_type("Sibling of"), "siblings")
eq(_edge_type("Required by"), "requires")
eq(_edge_type("Pairs with"), "composes_with")
eq(_edge_type("Distinct from"), "related")
eq(_edge_type("Totally novel label"), "related")

rp = (
    "## Related Patterns\n"
    "- **Sibling of** **R5 ReWOO** — same problem, opposite trade-off.\n"
    "- **Required by** **V9 Bounded Execution** — never run R4 unbounded.\n"
    "- **Composes with** **K8 Working Memory** — the trajectory is the scratchpad.\n"
    "## Sources\n"
)
e = related_edges(rp, "R4")
eq(e["siblings"], ["R5"])
eq(e["requires"], ["V9"])
eq(e["composes_with"], ["K8"])
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python3 build/test_ingest.py`
Expected: `ALL INGEST TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add build/ingest_lib.py build/test_ingest.py
git commit -m "feat(ingest): parse typed edges from Related Patterns"
```

---

### Task 5: Extract conflict edges from CONFLICTS.md

**Files:**
- Modify: `build/ingest_lib.py`
- Modify: `build/test_ingest.py`

CONFLICTS headings look like `### Critical 1 — R4 $\oplus$ R5  {#critical-1}` and `### Critical 3 — S9 H/S V7  {#critical-3}`. The symbol picks the edge type: `$\oplus$`/`$\leftrightarrow$` → `conflicts_with`; `$\to$` → `requires`; `$\sim$`/`H/S`/`$\uparrow$` → `composes_with`.

- [ ] **Step 1: Add the conflict parser**

```python
CONFLICT_SYMBOLS = [
    (r'\\oplus', "conflicts_with"), (r'\\leftrightarrow', "conflicts_with"),
    (r'\\to\b', "requires"), (r'\\sim', "composes_with"),
    (r'\\uparrow', "composes_with"), (r'\bH/S\b', "composes_with"),
]
_CONF_HEAD = re.compile(r'^###\s+Critical\s+\d+\s+—\s+(.+?)\s*\{#', re.M)


def conflict_edges(conflicts_md: str) -> list:
    """Parse CONFLICTS.md headings into [(a, b, edge_type), ...] (a,b are ids)."""
    out = []
    for head in _CONF_HEAD.finditer(conflicts_md):
        title = head.group(1)
        ids = re.findall(r'\b([A-Z]+\d+)\b', title)
        if len(ids) < 2:
            continue
        etype = "conflicts_with"
        for pat, t in CONFLICT_SYMBOLS:
            if re.search(pat, title):
                etype = t
                break
        a, b = ids[0], ids[1]
        out.append((a, b, etype))
    return out
```

- [ ] **Step 2: Add tests with real CONFLICTS headings**

```python
from ingest_lib import conflict_edges

cm = (
    "### Critical 1 — R4 $\\oplus$ R5  {#critical-1}\n"
    "### Critical 2 — V1 $\\leftrightarrow$ V2  {#critical-2}\n"
    "### Critical 3 — S9 H/S V7  {#critical-3}\n"
)
eq(conflict_edges(cm), [("R4", "R5", "conflicts_with"),
                        ("V1", "V2", "conflicts_with"),
                        ("S9", "V7", "composes_with")])
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python3 build/test_ingest.py`
Expected: `ALL INGEST TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add build/ingest_lib.py build/test_ingest.py
git commit -m "feat(ingest): parse conflict edges from CONFLICTS.md"
```

---

### Task 6: Extract `when_to_use` from the README index tables

**Files:**
- Modify: `build/ingest_lib.py`
- Modify: `build/test_ingest.py`

README rows look like: `| [S1 Zero-Shot](patterns/S1-Zero-Shot.md) | Direct Instruction | Simple, well-defined tasks within model priors |`. Column 3 is the curated when-to-use one-liner.

- [ ] **Step 1: Add the table parser**

```python
_README_ROW = re.compile(
    r'^\|\s*\[([A-Z]+\d+)[^\]]*\]\([^)]+\)\s*\|[^|]*\|\s*([^|]+?)\s*\|', re.M)


def when_to_use_map(readme: str) -> dict:
    """{id: when_to_use} from README pattern-index tables. Strips bold/markdown emphasis."""
    out = {}
    for m in _README_ROW.finditer(readme):
        uid, when = m.group(1), m.group(2).strip()
        when = re.sub(r'\*\*([^*]+)\*\*', r'\1', when)  # drop **bold**
        out[uid] = when
    return out
```

- [ ] **Step 2: Add tests with real README rows**

```python
from ingest_lib import when_to_use_map

rows = (
    "| [S1 Zero-Shot](patterns/S1-Zero-Shot.md) | Direct Instruction | Simple, well-defined tasks within model priors |\n"
    "| [R4 ReAct](patterns/R4-ReAct.md) | Reason+Act, Agent Loop | Adaptive tool use; each action informs the next |\n"
)
w = when_to_use_map(rows)
eq(w["S1"], "Simple, well-defined tasks within model priors")
eq(w["R4"], "Adaptive tool use; each action informs the next")
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python3 build/test_ingest.py`
Expected: `ALL INGEST TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add build/ingest_lib.py build/test_ingest.py
git commit -m "feat(ingest): extract when_to_use from README index"
```

---

### Task 7: Parse CHAPTER-0 into 12 mechanism units

**Files:**
- Modify: `build/ingest_lib.py`
- Modify: `build/test_ingest.py`

CHAPTER-0 mechanisms are delimited by `### M2 — n² Compute and KV Cache Memory Cost  {#m2}` followed by `#### Grade A` (or "Grade B" / "Grade B — ..."). The body runs until the next `### M` or `---`/section.

- [ ] **Step 1: Add the mechanism splitter**

```python
_MECH_HEAD = re.compile(
    r'^###\s+M(\d+)\s+—\s+(.+?)\s*\{#m\d+\}\s*\n+#{3,4}\s+Grade\s+([AB])', re.M)


def parse_mechanisms(chapter0: str) -> list:
    """Return [{'num':int,'title':str,'grade':'A'|'B','slug':str}] for M1..M12."""
    heads = list(_MECH_HEAD.finditer(chapter0))
    out = []
    for h in heads:
        num, title, grade = int(h.group(1)), h.group(2).strip(), h.group(3)
        slug = re.sub(r'[^a-z0-9]+', "-", title.lower()).strip("-")
        out.append({"num": num, "title": title, "grade": grade,
                    "slug": f"M{num}-{slug}"})
    return out
```

- [ ] **Step 2: Add tests with real CHAPTER-0 headings**

```python
from ingest_lib import parse_mechanisms

c0 = (
    "### M1 — Attention as a Learned Bilinear Form  {#m1}\n\n#### Grade A\n*text*\n"
    "### M2 — n² Compute and KV Cache Memory Cost  {#m2}\n\n#### Grade A\n*text*\n"
    "### M4 — Lost-in-the-Middle as Q-K Space Geometry  {#m4}\n\n#### Grade B — empirically strong\n*text*\n"
)
ms = parse_mechanisms(c0)
eq(len(ms), 3)
eq(ms[0]["num"], 1)
eq(ms[1]["grade"], "A")
eq(ms[2]["grade"], "B")
eq(ms[0]["slug"], "M1-attention-as-a-learned-bilinear-form")
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python3 build/test_ingest.py`
Expected: `ALL INGEST TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add build/ingest_lib.py build/test_ingest.py
git commit -m "feat(ingest): split CHAPTER-0 into mechanism units"
```

---

### Task 8: Assemble a pattern unit (frontmatter + Description + wikilinks)

**Files:**
- Modify: `build/ingest_lib.py`
- Modify: `build/test_ingest.py`

This is the core projection. Given extracted fields + an id→stem map, produce the full unit markdown. Frontmatter values are simple scalars/lists (manual emit — no yaml dependency).

- [ ] **Step 1: Add frontmatter emitter and unit assembler**

```python
EDGE_ORDER = ["requires", "conflicts_with", "composes_with", "siblings", "related"]
EDGE_PHRASE = {
    "requires": "Requires", "conflicts_with": "In tension with",
    "composes_with": "Composes with", "siblings": "Sibling of",
}


def _yaml_scalar(v) -> str:
    s = str(v)
    return f'"{s}"' if re.search(r'[:#\[\]{}",]', s) else s


def emit_frontmatter(fields: dict) -> str:
    """Emit flat YAML frontmatter. Lists -> [a, b]; skip empty values."""
    lines = ["---"]
    for k, v in fields.items():
        if v in (None, "", [], {}):
            continue
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(x) for x in v)}]")
        elif isinstance(v, bool):
            lines.append(f"{k}: {'true' if v else 'false'}")
        else:
            lines.append(f"{k}: {_yaml_scalar(v)}")
    lines.append("---")
    return "\n".join(lines)


def relationship_sentence(edges: dict) -> str:
    """Deterministic prose summary of the edge graph for the Description."""
    parts = []
    for et in EDGE_ORDER:
        ids = edges.get(et)
        if ids and et in EDGE_PHRASE:
            parts.append(f"{EDGE_PHRASE[et]} {', '.join(ids)}")
    return (". ".join(parts) + ".") if parts else ""


def wikilink_line(edges: dict, id_to_stem: dict) -> str:
    seen, links = set(), []
    for et in EDGE_ORDER:
        for i in edges.get(et, []):
            if i in id_to_stem and i not in seen:
                seen.add(i)
                links.append(f"[[{id_to_stem[i]}]]")
    return "Related: " + " · ".join(links) if links else ""


def assemble_pattern_unit(uid, title, fields, intent, edges, key_points, id_to_stem):
    fm = emit_frontmatter(fields)
    rel = relationship_sentence(edges)
    canonical = fields["canonical"]
    desc = f"{intent} {rel} This is a condensed digest; the canonical file " \
           f"(`{canonical}`) carries the full decision criteria, failure modes, " \
           f"and implementation.".replace("  ", " ").strip()
    body = [fm, "", "## Description", desc]
    if key_points:
        body += ["", "## Key points"] + [f"- {p}" for p in key_points]
    wl = wikilink_line(edges, id_to_stem)
    if wl:
        body += ["", wl]
    return "\n".join(body) + "\n"
```

- [ ] **Step 2: Add tests**

```python
from ingest_lib import emit_frontmatter, relationship_sentence, wikilink_line, assemble_pattern_unit

eq(emit_frontmatter({"id": "R4", "cost": "medium-high", "requires": ["V9", "V14"], "derived": True}),
   "---\nid: R4\ncost: medium-high\nrequires: [V9, V14]\nderived: true\n---")
eq(relationship_sentence({"requires": ["V9", "V14"], "siblings": ["R5"]}),
   "Requires V9, V14. Sibling of R5.")
eq(wikilink_line({"requires": ["V9"], "siblings": ["R5"]}, {"V9": "V9-Bounded-Execution", "R5": "R5-ReWOO"}),
   "Related: [[V9-Bounded-Execution]] · [[R5-ReWOO]]")

unit = assemble_pattern_unit(
    "R4", "ReAct",
    {"id": "R4", "title": "ReAct", "canonical": "patterns/R4-ReAct.md", "derived": True},
    "ReAct interleaves Thought, Action, Observation.",
    {"requires": ["V9"], "siblings": ["R5"]},
    ["Use when the next call depends on the last result"],
    {"V9": "V9-Bounded-Execution", "R5": "R5-ReWOO"},
)
assert "## Description" in unit and "[[V9-Bounded-Execution]]" in unit, unit
assert "patterns/R4-ReAct.md" in unit, unit
```

- [ ] **Step 3: Run tests, verify pass**

Run: `python3 build/test_ingest.py`
Expected: `ALL INGEST TESTS PASSED`

- [ ] **Step 4: Commit**

```bash
git add build/ingest_lib.py build/test_ingest.py
git commit -m "feat(ingest): assemble pattern unit markdown"
```

---

### Task 9: Bootstrap & curate `build/ingest-meta.json`

**Files:**
- Create: `build/build_ingest.py` (bootstrap mode first)
- Create: `build/ingest-meta.json` (generated, then reviewed)

The meta file holds, per pattern id: `summary`, `cost`, and the merged edge dict (Related-Patterns edges + CONFLICTS edges). It is generated once, then **human-reviewed** for misclassified edges before the assembly tasks consume it.

- [ ] **Step 1: Write `build/build_ingest.py` with a `--bootstrap` path**

```python
#!/usr/bin/env python3
"""Build the ingest/ artifact from canonical source + ingest-meta.json.
  python3 build/build_ingest.py --bootstrap   # (re)generate ingest-meta.json from source
  python3 build/build_ingest.py                # build ingest/ from source + meta
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ingest_lib as L

BUILD = Path(__file__).parent
ROOT = BUILD.parent
PATTERNS = ROOT / "patterns"
CONTENT = BUILD / "content"
META = BUILD / "ingest-meta.json"
OUT = ROOT / "ingest"

CATEGORY_FILES = {"SIGNAL", "KNOWLEDGE", "REASONING", "ORCHESTRATION",
                  "RELIABILITY", "INTEGRATION", "HUMANIZERS"}


def pattern_files():
    """Canonical pattern files only (exclude overviews/decisions/CONFLICTS/etc.)."""
    for f in sorted(PATTERNS.glob("*.md")):
        if L.ID_RE.match(f.stem):
            yield f


def bootstrap():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    wmap = L.when_to_use_map(readme)
    conflicts = (PATTERNS / "CONFLICTS.md").read_text(encoding="utf-8")
    cedges = L.conflict_edges(conflicts)
    meta = {}
    for f in pattern_files():
        uid = L.unit_id(f.stem)
        text = f.read_text(encoding="utf-8")
        edges = L.related_edges(text, uid)
        intent = L.intent_of(text)
        meta[uid] = {
            "summary": (intent.split(". ")[0] + ".") if intent else L.title_of(text),
            "when_to_use": wmap.get(uid, ""),
            "cost": "",  # fill during review (decision-guide tables are the source)
            "edges": edges,
        }
    # merge conflict edges (authoritative) into conflicts_with / requires / composes_with
    for a, b, etype in cedges:
        for x, y in ((a, b), (b, a)) if etype == "conflicts_with" else ((a, b),):
            if x in meta:
                meta[x]["edges"].setdefault(etype, [])
                if y not in meta[x]["edges"][etype]:
                    meta[x]["edges"][etype].append(y)
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {META} ({len(meta)} patterns) — REVIEW edges before building")


if __name__ == "__main__":
    if "--bootstrap" in sys.argv:
        bootstrap()
```

- [ ] **Step 2: Generate the meta file**

Run: `python3 build/build_ingest.py --bootstrap`
Expected: `wrote .../ingest-meta.json (94 patterns) — REVIEW edges before building`

- [ ] **Step 3: Manually review `build/ingest-meta.json`** (the one human-judgment step)

Open the file and for each pattern confirm: edges point the right way (e.g. R4 `requires` V9/V14, `conflicts_with` R5), and fill `cost` from the decision-guide cost tables (e.g. `patterns/REASONING-DECISION.md` lists R4 = "Medium–High" → `medium-high`). Correct any mislabelled edge from the prose-parsing heuristic. This file is now authoritative for machine edges.

- [ ] **Step 4: Commit the reviewed meta + bootstrap**

```bash
git add build/build_ingest.py build/ingest-meta.json
git commit -m "feat(ingest): bootstrap and curate ingest-meta.json"
```

---

### Task 10: Build the pattern units into `ingest/`

**Files:**
- Modify: `build/build_ingest.py`

- [ ] **Step 1: Add `id_to_stem` map + pattern-unit emission to `build_ingest.py`**

```python
def id_to_stem_map():
    return {L.unit_id(f.stem): f.stem for f in pattern_files()}


def applicability_points(text):
    """First few 'Use ... when:' bullets as key points."""
    sec = re.search(r'Use .*?when:\s*\n(.*?)\n\n', text, re.S | re.M)
    if not sec:
        return []
    pts = [l.strip("- ").strip() for l in sec.group(1).splitlines() if l.strip().startswith("-")]
    return pts[:4]


def build_patterns(meta, id_to_stem):
    OUT.mkdir(exist_ok=True)
    units = []
    for f in pattern_files():
        uid = L.unit_id(f.stem)
        text = f.read_text(encoding="utf-8")
        m = meta[uid]
        fields = {
            "id": uid, "title": L.title_of(text), "type": "pattern",
            "category": L.category_of(uid), "summary": m["summary"],
            "when_to_use": m.get("when_to_use", ""), "cost": m.get("cost", ""),
            "also_known_as": L.also_known_as(text),
            **m["edges"],
            "mechanism_refs": L.mechanism_refs(text),
            "canonical": f"patterns/{f.name}", "derived": True,
        }
        unit_md = L.assemble_pattern_unit(
            uid, fields["title"], fields, L.intent_of(text), m["edges"],
            applicability_points(text), id_to_stem)
        (OUT / f.name).write_text(unit_md, encoding="utf-8")
        units.append((uid, fields, f.name))
    return units
```

- [ ] **Step 2: Wire a temporary `__main__` build path to exercise it**

In `build_ingest.py`, extend `__main__`:

```python
    else:
        meta = json.loads(META.read_text(encoding="utf-8"))
        id_to_stem = id_to_stem_map()
        units = build_patterns(meta, id_to_stem)
        print(f"wrote {len(units)} pattern units to {OUT}")
```

- [ ] **Step 3: Run and spot-check R4**

Run: `python3 build/build_ingest.py && head -20 ingest/R4-ReAct.md`
Expected: `wrote 94 pattern units to .../ingest`, and `ingest/R4-ReAct.md` shows frontmatter with `id: R4`, `conflicts_with: [R5]`, a `## Description`, and a `Related:` wikilink line.

- [ ] **Step 4: Commit**

```bash
git add build/build_ingest.py ingest/
git commit -m "feat(ingest): generate pattern units"
```

---

### Task 11: Build mechanism units, decision-guide units, references.md

**Files:**
- Modify: `build/build_ingest.py`
- Modify: `build/ingest_lib.py` (a slug helper for decision guides)

- [ ] **Step 1: Add mechanism + decision + references emission to `build_ingest.py`**

```python
def build_mechanisms(chapter0, id_to_stem):
    mechs = L.parse_mechanisms(chapter0)
    for me in mechs:
        fields = {
            "id": f"M{me['num']}", "title": me["title"], "type": "mechanism",
            "summary": me["title"], "grade": me["grade"],
            "canonical": f"build/content/CHAPTER-0.md#m{me['num']}", "derived": True,
        }
        body = [L.emit_frontmatter(fields), "", "## Description",
                f"Mechanism {me['num']} (Grade {me['grade']}): {me['title']}. "
                f"Derived in the Mechanical Foundation; see the canonical file "
                f"(`build/content/CHAPTER-0.md#m{me['num']}`) for the full derivation."]
        (OUT / f"{me['slug']}.md").write_text("\n".join(body) + "\n", encoding="utf-8")
        id_to_stem[f"M{me['num']}"] = me["slug"]
    return mechs


def build_decisions():
    out = []
    for cat in sorted(CATEGORY_FILES):
        df = PATTERNS / f"{cat}-DECISION.md"
        if not df.exists():
            continue
        text = df.read_text(encoding="utf-8")
        uid = f"DECISION-{cat.lower()}"
        fields = {"id": uid, "title": f"{cat.title()} — Decision Guide",
                  "type": "decision-guide", "summary": f"How to choose among {cat.title()} patterns.",
                  "canonical": f"patterns/{cat}-DECISION.md", "derived": True}
        # keep the decision body verbatim (it is already dense, agent-friendly)
        body = L.emit_frontmatter(fields) + "\n\n" + L.strip_first_h1(text)
        (OUT / f"{uid}.md").write_text(body, encoding="utf-8")
        out.append((uid, fields))
    return out


def build_references():
    refs = (CONTENT / "REFERENCES.md").read_text(encoding="utf-8")
    fields = {"id": "references", "title": "References", "type": "reference-set",
              "summary": "Full bibliography for the catalog.",
              "canonical": "build/content/REFERENCES.md", "derived": True}
    (OUT / "references.md").write_text(
        L.emit_frontmatter(fields) + "\n\n" + L.strip_first_h1(refs), encoding="utf-8")
```

- [ ] **Step 2: Add `strip_first_h1` to `ingest_lib.py`** (reused from build_book.py logic)

```python
def strip_first_h1(text: str) -> str:
    out, stripped = [], False
    for line in text.splitlines():
        if not stripped and line.startswith("# ") and not line.startswith("## "):
            stripped = True
            continue
        if stripped and not out and not line.strip():
            continue
        out.append(line)
    return "\n".join(out)
```

- [ ] **Step 3: Add a quick test for `strip_first_h1`**

```python
from ingest_lib import strip_first_h1
eq(strip_first_h1("# Title\n\nBody line"), "Body line")
```

- [ ] **Step 4: Run tests + build, verify mechanism/decision/reference files appear**

Run: `python3 build/test_ingest.py && python3 build/build_ingest.py && ls ingest/ | grep -E 'M1-|DECISION-|references'`
Expected: tests pass; listing shows mechanism units, `DECISION-*` units, and `references.md`.

- [ ] **Step 5: Commit**

```bash
git add build/ingest_lib.py build/build_ingest.py ingest/
git commit -m "feat(ingest): generate mechanism, decision, reference units"
```

---

### Task 12: Build `ingest.json` manifest, `index.md`, `INGEST.md`

**Files:**
- Modify: `build/build_ingest.py`

- [ ] **Step 1: Add manifest + index + readme emission**

```python
FIELD_GLOSSARY = {
    "requires": "Hard dependency: this pattern must be paired with the target.",
    "conflicts_with": "Mutually exclusive or in tension for the same task.",
    "composes_with": "Pairs or nests cleanly with the target.",
    "siblings": "Same-problem alternative with a different trade-off.",
    "mechanism_refs": "Chapter-0 mechanism numbers (1–12) that ground this pattern.",
}


def write_manifest(units, mechs):
    unit_list, edge_list = [], []
    for uid, fields, fname in units:
        unit_list.append({
            "id": uid, "type": "pattern", "category": fields["category"],
            "title": fields["title"], "summary": fields["summary"],
            "file": f"ingest/{fname}", "canonical": fields["canonical"],
            "edges": {k: fields[k] for k in L.EDGE_ORDER + ["mechanism_refs"] if fields.get(k)},
        })
        for et in L.EDGE_ORDER:
            for tgt in fields.get(et, []):
                edge_list.append({"from": uid, "to": tgt, "type": et})
    manifest = {
        "schema": "go4-ingest/v1",
        "generated_from": "patterns/*.md + build/content/CHAPTER-0.md",
        "canonical_note": "Units are derived digests. patterns/*.md and CHAPTER-0.md are authoritative.",
        "field_glossary": FIELD_GLOSSARY,
        "units": unit_list,
        "edges": edge_list,
        "stats": {"patterns": len(units), "mechanisms": len(mechs),
                  "decision_guides": len(list(CATEGORY_FILES))},
    }
    (OUT / "ingest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")


def write_index(units):
    by_cat = {}
    for uid, fields, fname in units:
        by_cat.setdefault(fields["category"], []).append((uid, fields, fname))
    lines = ["# GO4 Ingest — Index", ""]
    for cat in ["Signal", "Knowledge", "Reasoning", "Orchestration",
                "Reliability", "Integration", "Humanizers"]:
        if cat not in by_cat:
            continue
        lines.append(f"## {cat}")
        for uid, fields, fname in by_cat[cat]:
            lines.append(f"- [[{fname[:-3]}]] — {fields['summary']}")
        lines.append("")
    (OUT / "index.md").write_text("\n".join(lines), encoding="utf-8")


INGEST_MD = """# Ingest GO4 into your agent's memory

This folder is a **generated, derived projection** of the GO4 catalog, shaped for
ingestion into agent memory systems (Karpathy LLM wiki / agentmemory, Cognee,
Obsidian, or a coding agent's memory). The canonical, authoritative source is
`patterns/*.md` and `build/content/CHAPTER-0.md` in this repo — these are digests
that link back to it.

## What's here
- One markdown unit per pattern (94), mechanism (12), and decision guide (7)
- `references.md` — the full bibliography
- `ingest.json` — machine manifest: unit index + the full relationship graph + a
  field glossary
- `index.md` — human catalog by category

## How to load it
- **Karpathy wiki / agentmemory:** copy `ingest/` into the wiki source dir, run ingest.
- **Cognee:** point the ingestion pipeline at `ingest/*.md`.
- **Obsidian:** drop in — frontmatter is Dataview-ready, `[[links]]` resolve.
- **Claude Code / coding agent:** reference `ingest/` from your `CLAUDE.md`/`AGENTS.md`.
- **Vector store:** chunk `ingest/*.md`, carry frontmatter as metadata.

## Relabel freely
The frontmatter field names (`requires`, `conflicts_with`, `composes_with`,
`siblings`, `mechanism_refs`) are suggestions. See `ingest.json` → `field_glossary`
to map them onto your own schema. The relationships are also stated in each unit's
prose and as `[[wikilinks]]`, so nothing is lost if you strip the frontmatter.

## Provenance & license
Generated by `build/build_ingest.py`. No confidence/decay/lifecycle fields — GO4 is
authored and stable. MIT licensed, like the rest of the repo.
"""


def write_readme():
    (OUT / "INGEST.md").write_text(INGEST_MD, encoding="utf-8")
```

- [ ] **Step 2: Wire all writers into `__main__`**

Replace the `else:` branch in `build_ingest.py`:

```python
    else:
        meta = json.loads(META.read_text(encoding="utf-8"))
        id_to_stem = id_to_stem_map()
        chapter0 = (CONTENT / "CHAPTER-0.md").read_text(encoding="utf-8")
        mechs = build_mechanisms(chapter0, id_to_stem)
        units = build_patterns(meta, id_to_stem)
        build_decisions()
        build_references()
        write_manifest(units, mechs)
        write_index(units)
        write_readme()
        print(f"ingest/: {len(units)} patterns, {len(mechs)} mechanisms, "
              f"+ decisions, references, manifest, index, INGEST.md")
```

(Note: `build_mechanisms` runs before `build_patterns` so mechanism stems exist in `id_to_stem` for any cross-links.)

- [ ] **Step 3: Run the full build**

Run: `python3 build/build_ingest.py && ls ingest/ && python3 -c "import json; d=json.load(open('ingest/ingest.json')); print(d['stats'], len(d['edges']), 'edges')"`
Expected: full listing; stats show `{'patterns': 94, 'mechanisms': 12, 'decision_guides': 7}` and a non-zero edge count.

- [ ] **Step 4: Commit**

```bash
git add build/build_ingest.py ingest/
git commit -m "feat(ingest): manifest, index, and INGEST.md"
```

---

### Task 13: Integrity validator `build/validate_ingest.py`

**Files:**
- Create: `build/validate_ingest.py`

- [ ] **Step 1: Write the validator**

```python
#!/usr/bin/env python3
"""Validate the generated ingest/ artifact. EXIT 1 on any error.
Run: python3 build/validate_ingest.py"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "ingest"
errors, warnings = [], []

manifest = json.loads((OUT / "ingest.json").read_text(encoding="utf-8"))
ids = {u["id"] for u in manifest["units"]}

# 1. every unit file referenced in the manifest exists
for u in manifest["units"]:
    if not (ROOT / u["file"]).exists():
        errors.append(f"missing unit file: {u['file']}")

# 2. every edge target exists as a unit (patterns) — mechanism refs checked separately
for e in manifest["edges"]:
    if e["to"] not in ids:
        warnings.append(f"edge target not a pattern unit: {e['from']} -> {e['to']} ({e['type']})")

# 3. conflict edges are symmetric
conf = {(e["from"], e["to"]) for e in manifest["edges"] if e["type"] == "conflicts_with"}
for a, b in conf:
    if (b, a) not in conf:
        warnings.append(f"asymmetric conflict: {a} conflicts_with {b} but not reverse")

# 4. canonical paths resolve
for u in manifest["units"]:
    can = u["canonical"].split("#")[0]
    if not (ROOT / can).exists():
        errors.append(f"canonical missing: {u['canonical']}")

# 5. mechanism_refs in range
for u in manifest["units"]:
    for n in u["edges"].get("mechanism_refs", []):
        if not (1 <= n <= 12):
            errors.append(f"{u['id']}: mechanism_ref out of range: {n}")

# 6. files-vs-manifest 1:1 for pattern units
unit_files = {u["file"].split("/")[-1] for u in manifest["units"]}
disk_pattern_files = {f.name for f in OUT.glob("*.md")
                      if re.match(r'^[A-Z]+\d+-', f.name)}
for extra in disk_pattern_files - unit_files:
    warnings.append(f"pattern file on disk not in manifest: {extra}")

for w in warnings:
    print(f"WARNING: {w}")
if errors:
    print(f"ERROR: {len(errors)} integrity error(s):")
    for e in errors:
        print(f"  {e}")
    sys.exit(1)
print(f"OK — {len(manifest['units'])} units validated, {len(manifest['edges'])} edges.")
```

- [ ] **Step 2: Run it against the generated artifact**

Run: `python3 build/validate_ingest.py`
Expected: `OK — N units validated, M edges.` (warnings about non-pattern edge targets like V9/M2 are acceptable; there must be zero ERRORs)

- [ ] **Step 3: Commit**

```bash
git add build/validate_ingest.py
git commit -m "feat(ingest): integrity validator for ingest/"
```

---

### Task 14: README — prominent ingest section + Repo Structure + Start Here

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add the ingest section after the "📖 Get the Book" block**

Insert directly after the `[![Deploy mdBook]...` badge line and its following `---`:

```markdown
## 🧠 Ingest GO4 into your agent's memory

Beyond reading it, you can load the **whole catalog** into an agent. The
[`ingest/`](ingest/) folder is a generated, ingestible projection — one markdown
unit per pattern, mechanism, and decision guide, plus a machine manifest
(`ingest.json`) carrying the full relationship graph.

**Workflow:** clone the repo → point your personal memory system or coding agent at
the top-level `ingest/` folder → it absorbs all of it (patterns, the mechanical
foundation, the conflict graph, references). The labels are suggestions you can
relabel on ingest. See [`ingest/INGEST.md`](ingest/INGEST.md) for load recipes
(Karpathy wiki / agentmemory, Cognee, Obsidian, Claude Code).

---
```

- [ ] **Step 2: Add `ingest/` to the "Repo Structure" tree**

In the Repo Structure code block, after the `research/` entry, add:

```
├── ingest/                   ← generated, ingestible projection of the catalog
│   ├── ingest.json           ← manifest: unit index + relationship graph + glossary
│   ├── INGEST.md             ← how to load it into agent memory
│   └── [pattern/mechanism/decision units]
```

- [ ] **Step 3: Add a fourth "Start Here" entry**

In the "Start Here" ordered list, append:

```markdown
5. **[Ingest the whole catalog into your agent](ingest/INGEST.md)** — load every pattern, mechanism, and the conflict graph into your memory system
```

- [ ] **Step 4: Verify the site build is unaffected**

Run: `python3 build/validate.py && python3 build/prepare.py`
Expected: `OK — N references validated.` and `Done.` (README is not part of the mdBook tree, so this confirms nothing broke).

- [ ] **Step 5: Commit**

```bash
git add README.md
git commit -m "docs: add prominent ingest section to README"
```

---

### Task 15: Full regeneration + final verification + commit the artifact

**Files:** (no new files — verification + the committed `ingest/`)

- [ ] **Step 1: Clean regenerate from scratch**

Run: `rm -rf ingest && python3 build/build_ingest.py && python3 build/validate_ingest.py`
Expected: build prints the unit counts; validator prints `OK` with zero ERRORs.

- [ ] **Step 2: Confirm determinism (regenerate twice, diff is empty)**

Run: `python3 build/build_ingest.py && git stash -u --keep-index 2>/dev/null; python3 build/build_ingest.py && git diff --stat ingest/`
Expected: no diff from a second consecutive build (byte-identical output).

- [ ] **Step 3: Confirm both existing builds still pass**

Run: `python3 build/validate.py && python3 build/prepare.py && python3 build/test_linkify.py`
Expected: all pass — the existing site pipeline and linkify tests are untouched.

- [ ] **Step 4: Final commit of the regenerated artifact**

```bash
git add ingest/ build/
git commit -m "feat(ingest): regenerate complete ingest/ artifact"
```

---

## Self-review checklist (run after writing, before execution)

- **Spec coverage:** patterns ✓(T10) mechanisms ✓(T11) decision guides ✓(T11) references ✓(T11) conflict graph ✓(T5,T12) `ingest.json` ✓(T12) `INGEST.md` ✓(T12) `index.md` ✓(T12) frontmatter+`summary`+`## Description` ✓(T8) relabel glossary ✓(T12) provenance/`derived`/`canonical` ✓(T8,T11) validation ✓(T13) README ✓(T14) only-one-top-level-folder ✓(everything else under `build/`) builds-untouched ✓(T14,T15).
- **No build-time LLM** — all assembly is deterministic string work ✓.
- **Determinism** verified in T15 ✓.
