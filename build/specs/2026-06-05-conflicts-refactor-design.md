# CONFLICTS Refactor — Design Spec

**Date:** 2026-06-05
**Status:** Draft for review
**Author:** James Davies (with Claude)

---

## 1. Purpose

`patterns/CONFLICTS.md` is a 481-line / ~8.5K-token monolith. It is loaded **whole** by the PDF (Appendix A), the mdBook site, and parsed by the ingest build — and any agent consumer that "checks the conflict map" pays the full ~8.5K tokens for what is usually a single-pattern question. Split it into a **lean summary + per-category subfiles**, and re-wire every consumer (PDF, site, ingest, and the forthcoming agent-access layer) so a reader/agent loads only the slice it needs.

This is a **structural** refactor: no conflict is added, removed, or reworded. The same content, reorganised, with every existing cross-reference still resolving.

## 2. Design principles

1. **No content change, no broken links.** Every one of the 8 Critical conflicts and 10 Connections is referenced from pattern prose via `linkify` as `CONFLICTS.md#critical-N` / `#connection-x`. Those anchors **must keep resolving** after the split.
2. **Lean summary, deep subfiles.** The top file is an index you can read in seconds; the prose lives one hop away, grouped by category.
3. **Pipelines stay green.** PDF, site, and ingest builds must still pass; the generated `ingest/` artifact must stay **byte-identical** (the refactor moves where conflict edges are read from, it does not change the edge graph).
4. **Derived, not duplicated.** The summary's conflict index is generated from the subfiles so it cannot drift.

## 3. The split

```
patterns/
  CONFLICTS.md                      ← lean SUMMARY (entry point; keeps all anchors)
  conflicts/
    SIGNAL.md
    KNOWLEDGE.md
    REASONING.md
    ORCHESTRATION.md
    RELIABILITY.md
    INTEGRATION.md
    HUMANIZERS.md
```

**`CONFLICTS.md` (summary) contains:**
- The **Conflict Taxonomy** (the 6 types table) — authored, unchanged.
- A **Conflict Index**, in two tiers:
  - **Critical conflicts (8) + Connections (10)** — kept as short *anchored sub-headings*: a `### Critical N — R4 ⊕ R5  {#critical-N}` heading with a ≤2-line gloss and a `full »` link to the subfile. **These headings carry the canonical `#critical-N` / `#connection-x` anchors**, so every existing `linkify`-generated reference still resolves *here* unchanged — only the full prose moved one hop away.
  - **Full registry (the long tail)** — one index line per conflict: type symbol, pattern pair, gloss, link to its subfile entry.
  - The index is *generated* from the subfiles (§6) so it can't drift.
- The **7 Hardest Design Decisions** and the **Conflict Escalation Path** — authored, unchanged (they are already summary-level).

**`conflicts/<CATEGORY>.md` (7 subfiles) contain:**
- The full prose of each Critical conflict, registry entry, and Connection, grouped by **primary category** (the category of the first/most-specific pattern in the pair). Each entry keeps a subfile-local anchor for the summary→subfile link.
- A cross-category conflict (e.g. `I3 ↔ V13`, `H5 → V1`) lives in its primary category's file, with a one-line cross-reference from the partner category's file.

### Anchor-preservation strategy (the load-bearing trick)

Existing pattern prose links resolve to **`CONFLICTS.md#critical-N`**. The summary's index entry for each Critical keeps exactly that `{#critical-N}` anchor — so **every existing link lands on the summary index line, which links onward to the full subfile entry. `linkify.py` needs no change for the critical/connection references.** The reader pays the summary (lean), not the monolith, and clicks through only if they want the full prose.

## 4. Per-category placement

The Full Conflict Registry is already grouped by category-pair, so placement is mostly mechanical. Rule: each conflict goes in the subfile of the **first pattern's category**; if the two patterns are in different categories, the partner category's subfile gets a one-line `see conflicts/<primary>.md#<anchor>` cross-reference. The 8 Criticals and 10 Connections follow the same rule (e.g. Critical 1 `R4⊕R5` → `REASONING.md`; Critical 6 `I3↔V13` → `INTEGRATION.md` with a cross-ref from `RELIABILITY.md`; Connection F `O6→O17` → `ORCHESTRATION.md`).

## 5. Consumer re-wiring

| Consumer | File(s) | Change |
|---|---|---|
| **PDF** | `build/build_book.py:245` | Appendix A now assembles `CONFLICTS.md` (summary) **+ all `conflicts/*.md`** in category order, under the existing `{#appendix-conflicts}` heading. Anchors resolve within the single PDF; `linkify_pdf`'s `#critical-N` targets are unchanged. |
| **Site** | `build/prepare.py` | Copy `CONFLICTS.md` **and** `conflicts/*.md` into `build/src/patterns/` (mirroring the `conflicts/` subdir). `linkify_conflicts` is **unchanged** (its `CONFLICTS.md#critical-N` output still resolves to the summary). |
| **Site nav** | `build/src/SUMMARY.md` | Under "Appendix A — Conflicts", list the summary + the 7 subfiles as nested entries. |
| **Site validate** | `build/validate.py` | `source_of()` must resolve `patterns/conflicts/<cat>.md` refs from SUMMARY; extend the path mapping. |
| **Ingest** | `build/build_ingest.py` (`bootstrap`) | `conflict_edges` now reads **`patterns/conflicts/*.md`** (glob) instead of `CONFLICTS.md`. The same 8 Critical headings are found (now distributed across subfiles) → **the same edge set → `ingest/` regenerates byte-identically.** |
| **Ingest lib** | `build/ingest_lib.py` (`conflict_edges`) | No logic change — it still matches `### Critical N — … {#…}` headings; only the caller's file set changes. (Harvesting the *full registry* for more edges is a deliberate **non-goal** here — see §8 — to keep the artifact identical.) |

> Note: the agent-access layer (MCP + loader, Spec 2) will consume the subfiles + the edge graph for per-pattern conflict serving. That wiring is specified there, not here.

## 6. Generation & validation

- **`build/build_conflicts.py`** (new, parallel to `build_ingest.py`): reads the 7 subfiles, extracts each conflict's heading (type symbol + pattern pair + anchor), and regenerates the **Conflict Index** section of `CONFLICTS.md` between `<!-- BEGIN INDEX -->` / `<!-- END INDEX -->` markers. The taxonomy, 7-decisions, and escalation sections are authored and left untouched. Deterministic; committed artifact.
- **`build/validate_conflicts.py`** (or fold into the build): every conflict in a subfile appears in the index and vice-versa; every `#critical-N` (N=1..8) and `#connection-x` (a..j) anchor exists in the summary; every cross-reference target resolves; no conflict appears in two subfiles' *primary* position.
- **Determinism gate:** after the refactor, `python3 build/build_ingest.py && git diff --stat ingest/` must be **empty** — proof the edge graph is unchanged.

## 7. Migration (one-time content move)

The split is a one-time reorganisation of existing prose: a helper script (or careful manual pass) distributes the 8 Criticals, the registry sections, and the 10 Connections into the 7 subfiles by §4's rule, preserving wording exactly. The summary's taxonomy/decisions/escalation are lifted verbatim from the current file. After the move, `build_conflicts.py` generates the index. A diff of *concatenated* `CONFLICTS.md` + `conflicts/*.md` against the original (modulo headings/anchors) confirms no prose was lost.

## 8. Out of scope

- **Harvesting the Full Registry / Connections into the ingest edge graph** — valuable (more `conflicts_with`/`composes_with` edges), but it changes the `ingest/` artifact and belongs in its own change; this refactor holds the edge set constant.
- The MCP/loader's consumption of the split (Spec 2).
- Re-wording or re-categorising any conflict.

## 9. Footprint

New: `patterns/conflicts/` (7 files, under `patterns/` — not a top-level dir), `build/build_conflicts.py`, `build/validate_conflicts.py`, this spec. Modified: `patterns/CONFLICTS.md` (→ summary), `build/build_book.py`, `build/prepare.py`, `build/validate.py`, `build/src/SUMMARY.md`, `build/build_ingest.py` (caller only). `ingest/` regenerates byte-identically.

## 10. Success criteria

- `CONFLICTS.md` is a lean summary (~1.5–2K tokens) with a complete, generated conflict index; the 7 subfiles hold the full prose.
- Every existing `CONFLICTS.md#critical-N` / `#connection-x` reference from pattern prose still resolves (site + PDF).
- PDF builds (Appendix A = summary + subfiles); `validate.py` + `prepare.py` pass; `mdbook build` clean.
- `python3 build/build_ingest.py` → `ingest/` **byte-identical** to pre-refactor (determinism gate).
- No conflict prose lost (concatenation diff); index ↔ subfiles consistent (validator).
