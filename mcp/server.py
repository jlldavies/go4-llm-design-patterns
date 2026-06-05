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
    """Find GO4 design patterns matching a task or concern. Returns ranked candidates:
    [{id, title, category, when_to_use}]. Call go4_pattern(id) for a pattern's full
    bundle and go4_decision(category) for the category flowchart."""
    return C.find(query, limit, index=_INDEX)


@mcp.tool()
def go4_pattern(id: str) -> dict:
    """Get one GO4 pattern's bundle: summary, when-to-use, cost, typed edges
    (requires/conflicts_with/composes_with/siblings), mechanism refs, description,
    key points, canonical source path, and conflicts (resolution notes per
    conflicting pattern). Call go4_decision for the category flowchart."""
    p = C.get_pattern(id, index=_INDEX)
    if "error" not in p:
        p["conflicts"] = C.conflict_notes(id)
    return p


@mcp.tool()
def go4_decision(category: str) -> dict:
    """Get a GO4 category's decision guide (the flowchart that picks a pattern).
    category in Signal, Knowledge, Reasoning, Orchestration, Reliability, Integration, Humanizers."""
    return C.get_decision(category)


if __name__ == "__main__":
    mcp.run()
