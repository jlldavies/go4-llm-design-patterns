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
