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
