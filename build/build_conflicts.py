#!/usr/bin/env python3
"""Split patterns/CONFLICTS.md into a summary + per-category subfiles, and (default
mode) regenerate the summary's index from the subfiles.
  python3 build/build_conflicts.py --migrate   # one-time: original CONFLICTS.md -> summary + conflicts/*.md
  python3 build/build_conflicts.py              # regenerate the <!-- INDEX --> block of CONFLICTS.md
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import conflicts_lib as C

BUILD = Path(__file__).parent
ROOT = BUILD.parent
PATTERNS = ROOT / "patterns"
CONFLICTS = PATTERNS / "CONFLICTS.md"
SUBDIR = PATTERNS / "conflicts"
CATS = ["Signal", "Knowledge", "Reasoning", "Orchestration", "Reliability", "Integration", "Humanizers"]
CAT_FILE = {c: c.upper() + ".md" for c in CATS}  # Signal -> SIGNAL.md

# Section titles that stay verbatim in the summary (authored), in order.
SUMMARY_KEEP = ["Conflict Taxonomy", "Cross-Category Dependency Graph",
                "The Seven Hardest Design Decisions", "Conflict Escalation Path"]


def _section_preamble(body):
    """Text before the first '### ' heading in a section body, stripped of trailing ---."""
    import re as _re
    lines = body.splitlines()
    result = []
    for line in lines:
        if _re.match(r'^### ', line):
            break
        result.append(line)
    return "\n".join(result).strip().rstrip("-").strip()


def migrate():
    md = CONFLICTS.read_text(encoding="utf-8")
    sections = C.parse_sections(md)
    # buckets[cat] = list of (heading, body) full entries for that category's subfile
    buckets = {c: [] for c in CATS}
    index = {c: [] for c in CATS}  # (anchor_or_none, heading, gloss, kind)

    def place(heading, body, cat, kind):
        buckets[cat].append((heading, body))
        index[cat].append((C.anchor_of(heading), heading, C.gloss_of(body), kind))

    criticals_body = sections["The Critical Conflicts (Must Know)"]
    connections_body = sections["Mechanistically-Derived Cross-Pattern Connections"]

    for head, body in C.split_entries(criticals_body):
        place(head, body, C.primary_category_of_pair(head), "critical")
    for head, body in C.split_entries(connections_body):
        place(head, body, C.primary_category_of_pair(head), "connection")
    for head, body in C.split_entries(sections["Full Conflict Registry"]):
        # registry 'entries' are the 'X vs Y' table sections
        place(head, body, C.primary_category_of_title(head), "registry")

    SUBDIR.mkdir(exist_ok=True)
    for cat in CATS:
        parts = [f"# Conflicts — {cat}\n",
                 f"*Per-category conflict detail. Summary + index: [CONFLICTS.md](../CONFLICTS.md).*\n"]
        for head, body in buckets[cat]:
            parts.append(f"## {head}\n\n{body}\n")
        (SUBDIR / CAT_FILE[cat]).write_text("\n".join(parts).rstrip() + "\n", encoding="utf-8")

    # Preserve section intro prose (text before first ### in criticals/connections).
    criticals_intro = _section_preamble(criticals_body)
    connections_intro = _section_preamble(connections_body)

    # Build the summary: preamble + taxonomy + generated INDEX + kept sections.
    index_block = "## Conflict Index\n\n"
    if criticals_intro:
        index_block += criticals_intro + "\n\n"
    index_block += "<!-- BEGIN INDEX -->\n" + render_index(index) + "\n<!-- END INDEX -->"
    if connections_intro:
        index_block += "\n\n" + connections_intro

    summary = [sections[""],  # title + intro
               "## Conflict Taxonomy\n\n" + sections["Conflict Taxonomy"],
               index_block]
    for keep in ["Cross-Category Dependency Graph", "The Seven Hardest Design Decisions", "Conflict Escalation Path"]:
        summary.append(f"## {keep}\n\n{sections[keep]}")
    CONFLICTS.write_text("\n\n---\n\n".join(summary).rstrip() + "\n", encoding="utf-8")
    print(f"migrated: {sum(len(b) for b in buckets.values())} entries -> {len(CATS)} subfiles + summary")


def render_index(index):
    """Generate the index markdown. Criticals/Connections keep their #anchor as a
    sub-heading (so linkify links resolve here); registry entries are plain links."""
    out = []
    for cat in CATS:
        rows = index[cat]
        if not rows:
            continue
        out.append(f"### {cat}")
        rel = "conflicts/" + CAT_FILE[cat]
        for anchor, heading, gloss, kind in rows:
            title = heading.split("  {#")[0]
            if kind in ("critical", "connection") and anchor:
                # subfile keeps the same {#anchor}; on the site these are different
                # pages so there is no id collision, and the full-link resolves.
                out.append(f"#### {title}  {{#{anchor}}}\n{gloss} [full »]({rel}#{anchor})\n")
            else:  # registry section
                out.append(f"- **{title}** — see [{rel}](./{rel})")
        out.append("")
    return "\n".join(out).strip()


def regenerate_index():
    """Default mode: re-derive the <!-- INDEX --> block from the subfiles (idempotent)."""
    index = {c: [] for c in CATS}
    for cat in CATS:
        f = SUBDIR / CAT_FILE[cat]
        for head, body in _subfile_entries(f.read_text(encoding="utf-8")):
            anchor = C.anchor_of(head)
            kind = "critical" if anchor and anchor.startswith("critical") else \
                   "connection" if anchor and anchor.startswith("connection") else "registry"
            index[cat].append((anchor, head, C.gloss_of(body), kind))
    md = CONFLICTS.read_text(encoding="utf-8")
    new = md.split("<!-- BEGIN INDEX -->")[0] + "<!-- BEGIN INDEX -->\n" + render_index(index) + \
          "\n<!-- END INDEX -->" + md.split("<!-- END INDEX -->", 1)[1]
    CONFLICTS.write_text(new, encoding="utf-8")
    print("regenerated CONFLICTS.md index block")


def _subfile_entries(text):
    out, head, buf = [], None, []
    for line in text.splitlines():
        m = re.match(r'^## (.+)', line)
        if m:
            if head is not None:
                out.append((head, "\n".join(buf).strip("\n")))
            head, buf = m.group(1).strip(), []
        elif head is not None:
            buf.append(line)
    if head is not None:
        out.append((head, "\n".join(buf).strip("\n")))
    return out


if __name__ == "__main__":
    migrate() if "--migrate" in sys.argv else regenerate_index()
