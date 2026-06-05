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
