# GO4 MCP Server

Pull-not-push access to the GO4 LLM-engineering pattern catalog. Three tools —
`go4_find`, `go4_pattern`, `go4_decision` — over the repo's `ingest/` corpus.
No auto-fire, no embeddings; the agent loads only what it asks for.

## Idle cost

The three tool schemas total **~169 tokens** (measured) in a client's tool listing —
the only always-on cost. Everything else loads on demand per call.

## Install & run

    pip install -r mcp/requirements.txt   # requires Python 3.10+
    python3 mcp/server.py                 # stdio transport

## Claude Code / Cursor config

    {"mcpServers": {"go4": {"command": "python3", "args": ["/ABS/PATH/GO4/mcp/server.py"]}}}

Replace `/ABS/PATH/GO4` with the absolute path to your clone of this repo.

## Tools

- `go4_find(query, limit=5)` — ranked candidates: id, title, category, when-to-use.
  Use to locate patterns matching a task or concern, then call `go4_pattern` for the full
  bundle.
- `go4_pattern(id)` — full bundle for one pattern: summary, when-to-use, cost, typed
  edges (requires / conflicts_with / composes_with / siblings), mechanism refs, dense
  description + key points, conflict notes, and the canonical source path.
- `go4_decision(category)` — the category's decision-guide flowchart for picking a
  pattern. category in: Signal, Knowledge, Reasoning, Orchestration, Reliability,
  Integration, Humanizers.
