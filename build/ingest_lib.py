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


def mechanism_refs(text: str) -> list:
    """Sorted unique mechanism numbers (1–12) cited anywhere in the text."""
    nums = set()
    for m in _MECH.finditer(text):
        for n in _NUM.findall(m.group(2)):
            v = int(n)
            if 1 <= v <= 12:
                nums.add(v)
    return sorted(nums)


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
