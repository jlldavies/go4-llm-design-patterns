#!/usr/bin/env python3
"""Build the ingest/ artifact from canonical source + ingest-meta.json.
  python3 build/build_ingest.py --bootstrap   # (re)generate ingest-meta.json from source
  python3 build/build_ingest.py                # build ingest/ from source + meta
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ingest_lib as L

BUILD = Path(__file__).parent
ROOT = BUILD.parent
PATTERNS = ROOT / "patterns"
CONTENT = BUILD / "content"
META = BUILD / "ingest-meta.json"
OUT = ROOT / "ingest"

CATEGORY_FILES = {"SIGNAL", "KNOWLEDGE", "REASONING", "ORCHESTRATION",
                  "RELIABILITY", "INTEGRATION", "HUMANIZERS"}


def pattern_files():
    """Canonical pattern files only (exclude overviews/decisions/CONFLICTS/etc.)."""
    for f in sorted(PATTERNS.glob("*.md")):
        if L.ID_RE.match(f.stem):
            yield f


def bootstrap():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    wmap = L.when_to_use_map(readme)
    conflicts = (PATTERNS / "CONFLICTS.md").read_text(encoding="utf-8")
    cedges = L.conflict_edges(conflicts)
    meta = {}
    for f in pattern_files():
        uid = L.unit_id(f.stem)
        text = f.read_text(encoding="utf-8")
        edges = L.related_edges(text, uid)
        intent = L.intent_of(text)
        meta[uid] = {
            "summary": (intent.split(". ")[0].rstrip(".") + ".") if intent else L.title_of(text),
            "when_to_use": wmap.get(uid, ""),
            "cost": "",  # fill during review (decision-guide tables are the source)
            "edges": edges,
        }
    # merge conflict edges (authoritative) into conflicts_with / requires / composes_with
    for a, b, etype in cedges:
        for x, y in ((a, b), (b, a)) if etype == "conflicts_with" else ((a, b),):
            if x in meta:
                meta[x]["edges"].setdefault(etype, [])
                if y not in meta[x]["edges"][etype]:
                    meta[x]["edges"][etype].append(y)
    META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {META} ({len(meta)} patterns) — REVIEW edges before building")


def _filter_edges(edges, valid_ids):
    return {et: [i for i in ids if i in valid_ids] for et, ids in edges.items()}


def id_to_stem_map():
    return {L.unit_id(f.stem): f.stem for f in pattern_files()}


def applicability_points(text):
    """First few 'Use ... when:' bullets as key points."""
    sec = re.search(r'Use .*?when:\s*\n(.*?)\n\n', text, re.S | re.M)
    if not sec:
        return []
    pts = [l.strip("- ").strip() for l in sec.group(1).splitlines() if l.strip().startswith("-")]
    return pts[:4]


def build_patterns(meta, id_to_stem):
    OUT.mkdir(exist_ok=True)
    units = []
    for f in pattern_files():
        uid = L.unit_id(f.stem)
        text = f.read_text(encoding="utf-8")
        m = meta[uid]
        edges = _filter_edges(m["edges"], id_to_stem)
        fields = {
            "id": uid, "title": L.title_of(text), "type": "pattern",
            "category": L.category_of(uid), "summary": m["summary"],
            "when_to_use": m.get("when_to_use", ""), "cost": m.get("cost", ""),
            "also_known_as": L.also_known_as(text),
            **edges,
            "mechanism_refs": L.mechanism_refs(text),
            "canonical": f"patterns/{f.name}", "derived": True,
        }
        unit_md = L.assemble_pattern_unit(
            fields, L.intent_of(text), edges,
            applicability_points(text), id_to_stem)
        (OUT / f.name).write_text(unit_md, encoding="utf-8")
        units.append((uid, fields, f.name))
    return units


def build_mechanisms(chapter0, id_to_stem):
    mechs = L.parse_mechanisms(chapter0)
    units = []
    for me in mechs:
        mid = f"M{me['num']}"
        slug = me["slug"]
        fields = {
            "id": mid, "title": me["title"], "type": "mechanism",
            "summary": me["title"], "grade": me["grade"],
            "canonical": f"build/content/CHAPTER-0.md#m{me['num']}", "derived": True,
        }
        body = [L.emit_frontmatter(fields), "", "## Description",
                f"Mechanism {me['num']} (Grade {me['grade']}): {me['title']}. "
                f"Derived in the Mechanical Foundation; see the canonical file "
                f"(`build/content/CHAPTER-0.md#m{me['num']}`) for the full derivation."]
        (OUT / f"{slug}.md").write_text("\n".join(body) + "\n", encoding="utf-8")
        id_to_stem[mid] = slug
        units.append((mid, fields, f"{slug}.md"))
    return units


def build_decisions():
    units = []
    for cat in sorted(CATEGORY_FILES):
        df = PATTERNS / f"{cat}-DECISION.md"
        if not df.exists():
            continue
        text = df.read_text(encoding="utf-8")
        uid = f"DECISION-{cat.lower()}"
        fname = f"{uid}.md"
        fields = {"id": uid, "title": f"{cat.title()} — Decision Guide",
                  "type": "decision-guide", "summary": f"How to choose among {cat.title()} patterns.",
                  "canonical": f"patterns/{cat}-DECISION.md", "derived": True}
        # keep the decision body verbatim (it is already dense, agent-friendly)
        body = L.emit_frontmatter(fields) + "\n\n" + L.strip_first_h1(text)
        (OUT / fname).write_text(body, encoding="utf-8")
        units.append((uid, fields, fname))
    return units


def build_references():
    refs = (CONTENT / "REFERENCES.md").read_text(encoding="utf-8")
    fname = "references.md"
    fields = {"id": "references", "title": "References", "type": "reference-set",
              "summary": "Full bibliography for the catalog.",
              "canonical": "build/content/REFERENCES.md", "derived": True}
    (OUT / fname).write_text(
        L.emit_frontmatter(fields) + "\n\n" + L.strip_first_h1(refs), encoding="utf-8")
    return [("references", fields, fname)]


FIELD_GLOSSARY = {
    "requires": "Hard dependency: this pattern must be paired with the target.",
    "conflicts_with": "Mutually exclusive or in tension for the same task.",
    "composes_with": "Pairs or nests cleanly with the target.",
    "siblings": "Same-problem alternative with a different trade-off.",
    "mechanism_refs": "Chapter-0 mechanism numbers (1–12) that ground this pattern.",
}


def write_manifest(pattern_units, mech_units, decision_units, ref_units):
    unit_list, edge_list = [], []
    for uid, fields, fname in pattern_units:
        unit_list.append({
            "id": uid, "type": "pattern", "category": fields["category"],
            "title": fields["title"], "summary": fields["summary"],
            "file": f"ingest/{fname}", "canonical": fields["canonical"],
            "edges": {k: fields[k] for k in L.EDGE_ORDER + ["mechanism_refs"] if fields.get(k)},
        })
        for et in L.EDGE_ORDER:
            for tgt in fields.get(et, []):
                edge_list.append({"from": uid, "to": tgt, "type": et})
    for uid, fields, fname in mech_units:
        unit_list.append({
            "id": uid, "type": "mechanism",
            "title": fields["title"], "summary": fields["summary"],
            "file": f"ingest/{fname}", "canonical": fields["canonical"],
        })
    for uid, fields, fname in decision_units:
        unit_list.append({
            "id": uid, "type": "decision-guide", "category": fields["title"].split(" — ")[0],
            "title": fields["title"], "summary": fields["summary"],
            "file": f"ingest/{fname}", "canonical": fields["canonical"],
        })
    for uid, fields, fname in ref_units:
        unit_list.append({
            "id": uid, "type": "reference-set",
            "title": fields["title"], "summary": fields["summary"],
            "file": f"ingest/{fname}", "canonical": fields["canonical"],
        })
    manifest = {
        "schema": "go4-ingest/v1",
        "generated_from": "patterns/*.md + build/content/CHAPTER-0.md",
        "canonical_note": "Units are derived digests. patterns/*.md and CHAPTER-0.md are authoritative.",
        "field_glossary": FIELD_GLOSSARY,
        "units": unit_list,
        "edges": edge_list,
        "stats": {
            "patterns": len(pattern_units),
            "mechanisms": len(mech_units),
            "decision_guides": len(decision_units),
            "references": len(ref_units),
        },
    }
    (OUT / "ingest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
                                     encoding="utf-8")


def write_index(units):
    by_cat = {}
    for uid, fields, fname in units:
        by_cat.setdefault(fields["category"], []).append((uid, fields, fname))
    lines = ["# GO4 Ingest — Index", ""]
    for cat in ["Signal", "Knowledge", "Reasoning", "Orchestration",
                "Reliability", "Integration", "Humanizers"]:
        if cat not in by_cat:
            continue
        lines.append(f"## {cat}")
        for uid, fields, fname in by_cat[cat]:
            lines.append(f"- [[{fname[:-3]}]] — {fields['summary']}")
        lines.append("")
    (OUT / "index.md").write_text("\n".join(lines), encoding="utf-8")


INGEST_MD = """# Ingest GO4 into your agent's memory

This folder is a **generated, derived projection** of the GO4 catalog, shaped for
ingestion into agent memory systems (Karpathy LLM wiki / agentmemory, Cognee,
Obsidian, or a coding agent's memory). The canonical, authoritative source is
`patterns/*.md` and `build/content/CHAPTER-0.md` in this repo — these are digests
that link back to it.

## What's here
- One markdown unit per pattern (94), mechanism (12), and decision guide (7)
- `references.md` — the full bibliography
- `ingest.json` — machine manifest: unit index + the full relationship graph + a
  field glossary
- `index.md` — human catalog by category

## How to load it
- **Karpathy wiki / agentmemory:** copy `ingest/` into the wiki source dir, run ingest.
- **Cognee:** point the ingestion pipeline at `ingest/*.md`.
- **Obsidian:** drop in — frontmatter is Dataview-ready, `[[links]]` resolve.
- **Claude Code / coding agent:** reference `ingest/` from your `CLAUDE.md`/`AGENTS.md`.
- **Vector store:** chunk `ingest/*.md`, carry frontmatter as metadata.

## Relabel freely
The frontmatter field names (`requires`, `conflicts_with`, `composes_with`,
`siblings`, `mechanism_refs`) are suggestions. See `ingest.json` → `field_glossary`
to map them onto your own schema. The relationships are also stated in each unit's
prose and as `[[wikilinks]]`, so nothing is lost if you strip the frontmatter.

## Provenance & license
Generated by `build/build_ingest.py`. No confidence/decay/lifecycle fields — GO4 is
authored and stable. MIT licensed, like the rest of the repo.
"""


def write_readme():
    (OUT / "INGEST.md").write_text(INGEST_MD, encoding="utf-8")


if __name__ == "__main__":
    if "--bootstrap" in sys.argv:
        bootstrap()
    else:
        meta = json.loads(META.read_text(encoding="utf-8"))
        id_to_stem = id_to_stem_map()
        OUT.mkdir(exist_ok=True)
        chapter0 = (CONTENT / "CHAPTER-0.md").read_text(encoding="utf-8")
        mech_units = build_mechanisms(chapter0, id_to_stem)
        pattern_units = build_patterns(meta, id_to_stem)
        decision_units = build_decisions()
        ref_units = build_references()
        write_manifest(pattern_units, mech_units, decision_units, ref_units)
        write_index(pattern_units)
        write_readme()
        print(f"ingest/: {len(pattern_units)} patterns, {len(mech_units)} mechanisms, "
              f"{len(decision_units)} decisions, {len(ref_units)} references, "
              f"manifest, index, INGEST.md")
