#!/usr/bin/env python3
"""Pure parse/route/gloss helpers for the CONFLICTS split. No I/O.
Run tests: python3 build/test_conflicts.py"""

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ingest_lib import category_of  # category_of("R4") -> "Reasoning"

# Section-title first word -> category name (matches ingest_lib.CATEGORY values)
TITLE_CATEGORY = {
    "Signal": "Signal", "Knowledge": "Knowledge", "Reasoning": "Reasoning",
    "Orchestration": "Orchestration", "Reliability": "Reliability",
    "Integration": "Integration", "Humanizer": "Humanizers",
}
_FIRST_ID = re.compile(r'\b([SKROVIH]\d+)\b')


def primary_category_of_pair(text):
    """First pattern id in a heading pair -> its category. 'R4 $\\oplus$ R5' -> 'Reasoning'."""
    m = _FIRST_ID.search(text)
    if not m:
        raise ValueError(f"no pattern id in {text!r}")
    return category_of(m.group(1))


def primary_category_of_title(title):
    """Registry section title -> category. 'Reliability vs Orchestration' -> 'Reliability'."""
    first = title.split(" vs ")[0].strip()
    return TITLE_CATEGORY[first]


def parse_sections(md):
    """Split a markdown doc into {h2_title: body} on '## ' headings.
    Preamble (before the first ## ) is keyed ''. Bodies exclude the ## line."""
    out, key, buf = {}, "", []
    for line in md.splitlines():
        m = re.match(r'^## (.+)', line)
        if m:
            out[key] = "\n".join(buf).strip("\n")
            key, buf = m.group(1).strip(), []
        else:
            buf.append(line)
    out[key] = "\n".join(buf).strip("\n")
    return out


def split_entries(section_body):
    """Split a section body on '### ' headings into [(heading, body), ...].
    heading excludes the leading '### '. body excludes the heading line."""
    out, head, buf = [], None, []
    for line in section_body.splitlines():
        m = re.match(r'^### (.+)', line)
        if m:
            if head is not None:
                out.append((head, "\n".join(buf).strip("\n")))
            head, buf = m.group(1).strip(), []
        elif head is not None:
            buf.append(line)
    if head is not None:
        out.append((head, "\n".join(buf).strip("\n")))
    return out


def anchor_of(heading):
    """Extract the {#anchor} from a heading, or None. '… {#critical-1}' -> 'critical-1'."""
    m = re.search(r'\{#([\w-]+)\}', heading)
    return m.group(1) if m else None


def gloss_of(body):
    """First sentence of a conflict body, skipping a leading '**Type:** …' line.
    Used for the summary index entry."""
    lines = [l for l in body.splitlines() if l.strip() and not l.startswith("**Type:**")]
    if not lines:
        return ""
    first = lines[0].strip()
    # first sentence: up to the first '. ' (keep it short)
    sentence = re.split(r'(?<=\.)\s', first, maxsplit=1)[0]
    return sentence.strip()
