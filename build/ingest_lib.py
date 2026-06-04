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
    return CATEGORY.get(uid[0], "Unknown")


def title_of(text: str) -> str:
    """'# R4 — ReAct' -> 'ReAct'."""
    first = text.splitlines()[0].lstrip("# ").strip()
    m = re.match(r'[A-Z]+\d+\s*(?:—\s*)?(.+)', first)
    return m.group(1).strip() if m else first


def also_known_as(text: str) -> list:
    """Parse the '**Also Known As:** a, b, c' line into a list (stops at first sentence)."""
    m = re.search(r'\*\*Also Known As:\*\*\s*(.+)', text)
    if not m:
        return []
    raw = m.group(1)
    raw = re.sub(r'\s*\([^)]*\)', '', raw)   # strip inline parentheticals first
    raw = re.split(r'\.\s', raw, 1)[0]       # then cut at sentence end
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
    ("required by", "related"), ("requires", "requires"), ("depends on", "requires"),
    ("pairs with", "composes_with"), ("composes with", "composes_with"),
    ("inner pattern of", "composes_with"), ("often paired with", "composes_with"),
    ("managed by", "composes_with"), ("uses", "composes_with"),
    ("composes cleanly", "composes_with"), ("tool layer", "composes_with"),
    ("distinct from", "related"), ("not to be confused", "related"),
    ("named after", "related"), ("aligned with", "related"), ("echoes", "related"),
]
_REL_ID = re.compile(r'\b([A-Z]+\d+)\b')
_VALID_ID = re.compile(r'^[SKROVIH]\d+$')


def _edge_type(label: str) -> str:
    low = label.lower().strip()
    for prefix, etype in EDGE_LABELS:
        if low.startswith(prefix):
            return etype
    return "related"


def _valid_ids(raw_ids: list, self_id: str) -> list:
    """Filter a list of raw ID strings: keep only valid pattern IDs, no self."""
    seen, out = set(), []
    for i in raw_ids:
        if _VALID_ID.match(i) and i != self_id and i not in seen:
            seen.add(i)
            out.append(i)
    return out


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


def related_edges(text: str, self_id: str) -> dict:
    """Parse '## Related Patterns' bullets into {edge_type: [ids]} (deduped, no self).

    Handles three bullet formats:
      Format A: - **Label** **TargetID Title** — prose…   (targets bold before em-dash)
      Format B: - **Label** — T1, T2 targets…            (targets plain text after em-dash)
      Format C: - **Label** T1 Title — prose…             (plain-text target before em-dash)
    Anti-patterns (A\\d+) and any non-pattern token are excluded via _VALID_ID whitelist.
    """
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
        # Skip editorial "Note on…" bullets
        if lbl.group(1).lower().startswith("note"):
            continue
        etype = _edge_type(lbl.group(1))
        pre, _, post = line.partition("—")
        # Strip the leading bold label span from pre, then collect IDs from the remainder.
        # This captures both Format A (bold targets) and Format C (plain-text targets)
        # that appear before the em-dash.
        pre_body = re.sub(r'^\s*-\s*\*\*[^*]+\*\*', '', pre, count=1)
        raw_pre = re.findall(r'[A-Z]+\d+', pre_body)
        ids = _valid_ids(raw_pre, self_id)
        if not ids and post:
            # Format B fallback: plain-text IDs from the post-em-dash prose
            raw_b = _REL_ID.findall(post)
            ids = _valid_ids(raw_b, self_id)
        if ids:
            edges.setdefault(etype, [])
            for i in ids:
                if i not in edges[etype]:
                    edges[etype].append(i)
    return edges


EDGE_ORDER = ["requires", "conflicts_with", "composes_with", "siblings", "related"]
EDGE_PHRASE = {
    "requires": "Requires", "conflicts_with": "In tension with",
    "composes_with": "Composes with", "siblings": "Sibling of",
}


def _yaml_scalar(v) -> str:
    s = str(v)
    if re.search(r'[:#\[\]{}",]', s):
        return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'
    return s


def emit_frontmatter(fields: dict) -> str:
    """Emit flat YAML frontmatter. Lists -> [a, b]; skip empty values."""
    lines = ["---"]
    for k, v in fields.items():
        if v in (None, "", [], {}):
            continue
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(_yaml_scalar(x) for x in v)}]")
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


def assemble_pattern_unit(fields, intent, edges, key_points, id_to_stem):
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
