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
