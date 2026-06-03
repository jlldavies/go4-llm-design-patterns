---
name: go4-pdf-restructure
description: Three-phase restructure of GO4 PDF — book order, content reorganisation, and LaTeX pattern card styling
metadata:
  type: project
---

# GO4 PDF Restructure — Design Spec

**Date:** 2026-06-03
**Status:** Approved — ready for implementation planning

---

## Context

The GO4 project has 94 AI engineering design patterns across seven categories. The PDF (1,163 pages) was reviewed and the following structural and content problems identified:

- Chapter 0 (heavy tensor math) sits between the Introduction and the patterns — gatekeeping the useful content behind the hardest material
- The Introduction led with the GoF authority claim rather than the reader's problem, and lacked humility about being a homage
- "How to read" sent readers to Chapter 0 first; no guidance to jump to needed category
- The efficiency message ("use the smallest sufficient pattern") was absent from the front matter
- Decision flows buried in TAXONOMY-DRAFT rather than at the end of each relevant section
- Open Questions and Next Steps in the PDF
- No visual distinction between pages of different patterns
- Intro appears after the TOC rather than before it

---

## Approach

Three sequential phases, each producing a valid PDF for review.

---

## Phase 1 — Skeleton

**Goal:** Correct the book order, fix the introduction, place intro before TOC.

### `build_book.py` — assembly order

Current: Intro → Chapter 0 → Pattern Catalog → 7 Sections → Appendices

New:
1. `\frontmatter` raw LaTeX
2. Introduction (INTRO.md)
3. `\tableofcontents\clearpage` + `\mainmatter` raw LaTeX
4. Pattern Catalog (TAXONOMY-DRAFT — shortened in Phase 2)
5. 7 Category sections
6. Mechanisms chapter (formerly Chapter 0) — as unnumbered back-matter chapter (`\chapter*{}`)
7. Appendix A — Conflicts
8. Appendix B — References
9. Appendix C — Anti-Patterns + Composition Examples (new, from TAXONOMY-DRAFT)

Remove `--toc` from pandoc command args. TOC is now injected manually after the intro.

The Mechanisms chapter preamble comment (`# must precede Pattern Catalog`) is removed — it now follows the patterns.

### `INTRO.md` — rewritten

The introduction has been rewritten (committed). Key changes from original:
- Opens with reader's problem (88% failure rate, specific failure modes) not GoF claim
- GoF introduced as method/homage in paragraph 3, after the problem is established
- Explicit humility: "a homage to the Gang of Four approach, not a claim to their authority"
- New guiding principle paragraph: "use the smallest sufficient pattern"
- Added audience statement (engineers building LLM systems in production)
- "How to read" reversed: patterns are primary reference, Mechanisms is at the back
- Closing paragraph unchanged

### Section page breaks

Already handled by `documentclass=book` + `--top-level-division=chapter`. No change needed.

---

## Phase 2 — Content

**Goal:** Restructure TAXONOMY-DRAFT, add LLM primer to Mechanisms, move decision flows, remove open questions, distribute cognitive science and scaffold content.

### TAXONOMY-DRAFT.md — what survives in the PDF

The "Pattern Catalog" overview chapter shrinks to seven short paragraphs — one per section, just the opening description and the category table (GoF analogy column). Removed from PDF:

| Section | Destination |
|---|---|
| Per-pattern rows (all 7 sections) | Already in section intro files; TAXONOMY-DRAFT version removed |
| Decision flows (Primary/Orchestration, Reasoning, Integration) | Move to section-end companion files |
| Open Questions and Research Gaps | `OPEN-QUESTIONS.md` (repo root, not in PDF) |
| Next Steps | `OPEN-QUESTIONS.md` (already stripped by build script but source cleaned) |
| Scaffold Architecture Dimensions | ORCHESTRATION.md section intro |
| Cognitive Science Grounding | HUMANIZERS.md section intro |
| Anti-Pattern Registry | Appendix C |
| Pattern Composition Examples | Appendix C |

### `OPEN-QUESTIONS.md` (new file, repo root)

Merges "Open Questions and Research Gaps" + "Next Steps" from TAXONOMY-DRAFT. Not included in PDF build. Kept as a living research document.

### Decision flow companion files (new)

Seven files: `patterns/SIGNAL-DECISION.md` through `patterns/HUMANIZERS-DECISION.md`.

Three exist in TAXONOMY-DRAFT (Primary/Orchestration, Reasoning, Integration) and are extracted. Four need writing (Signal, Knowledge, Reliability, Humanizer) — short decision trees, consistent format with the existing three.

`build_book.py` appends each companion file after its section's final pattern, before the next chapter break. Decision flow pages run without the pattern card stripe (Phase 3).

### Section intro files — quick-reference tables

The compact "Also Known As / Intent / When to Use" tables from TAXONOMY-DRAFT are added to each section intro file, placed after the Examples band and before See Also. This gives each section a scannable overview before the full pattern entries.

### HUMANIZERS.md — Cognitive Science Grounding

The Cognitive Science Grounding table (AI Pattern → Cognitive Theory → Source) is added to HUMANIZERS.md, after the Key Distinctions block and before See Also. It documents the theoretical grounding for why Humanizer patterns work.

### ORCHESTRATION.md — Scaffold Architecture Dimensions

The Scaffold Architecture Dimensions section (five loop primitives, LLM-as-navigator vs scaffold-understands-code fault line, no-consensus dimensions) is added to ORCHESTRATION.md, after the Key Distinctions block. Sourced from arXiv 2604.03515.

### Appendix C — Anti-Patterns and Composition Examples

New appendix in `build_book.py`, assembled from the Anti-Pattern Registry and Pattern Composition Examples sections of TAXONOMY-DRAFT. Titled "Appendix C — Anti-Patterns and Composition Examples."

### Chapter 0 — LLM Primer (section 0.0)

New section added before Mechanism 1, titled **"0.0 — How a Language Model Computes"**.

Target reader: uses LLMs daily, can write code, has not read the architecture papers.

Five subsections, one paragraph each:

1. **Tokens** — byte-pair encoding, approximate counts (1 token ≈ ¾ word), why "token" not "word"
2. **The context window** — the sequence of tokens the model can see; why order and position matter; what "sequence length" means
3. **A forward pass** — prompt tokens in, one token out; what inference actually means; why the model is stateless between calls
4. **The KV cache** — why it exists (avoid recomputing on every generation step), what it stores (key and value vectors per token per layer), why it grows monotonically, why it cannot be reordered
5. **The n² intuition** — twice as long = four times as expensive in prefill; plain terms before the math

Target length: ~700 words. Math-free. Makes Mechanism 1's bilinear form legible because the reader already understands what Q and K represent.

### Chapter 0 preamble — tone adjustment

"Why this chapter exists" opening sentence updated from prerequisite framing ("must precede Pattern Catalog") to invitation framing — it is a derivation resource for readers who want the "why" behind pattern costs.

---

## Phase 3 — LaTeX Pattern Card Styling

**Goal:** Pale yellow left stripe with rotated pattern name on every page within a pattern.

### Visual design

- **Stripe fill:** `#FDFAEC` (pale warm yellow)
- **Hairline:** `#333333` at 0.4pt (right edge of stripe, matches existing header rule weight)
- **Text:** Pattern ID + name, `\small\sffamily` (Avenir Next), rotated 90°, centered vertically
- **Color is uniform** across all patterns — one color marks "you are in a pattern," not which section

Stripe sits in the left margin. Text area geometry is unchanged.

### Implementation

**`header.tex` additions:**
```latex
\usepackage{eso-pic}
\usepackage{tikz}
\usepackage{xcolor}

\definecolor{patternbg}{HTML}{FDFAEC}
\definecolor{patternsep}{HTML}{333333}

\newcommand{\currentpatternname}{}
\newcommand{\setpatternname}[1]{\renewcommand{\currentpatternname}{#1}}
\newcommand{\clearpatternname}{\renewcommand{\currentpatternname}{}}

\AddToShipoutPictureBG{%
  \ifx\currentpatternname\empty\else
    \begin{tikzpicture}[remember picture, overlay]
      % Stripe fill
      \fill[patternbg]
        ([xshift=-1.8cm]current page text area.north west)
        rectangle
        ([xshift=-0.3cm]current page text area.south west);
      % Hairline
      \draw[patternsep, line width=0.4pt]
        ([xshift=-0.3cm]current page text area.north west)
        --
        ([xshift=-0.3cm]current page text area.south west);
      % Rotated pattern name
      \node[rotate=90, anchor=center, text=patternsep,
            font=\small\sffamily]
        at ([xshift=-1.05cm]current page.center)
        {\currentpatternname};
    \end{tikzpicture}
  \fi
}
```

**`build_book.py` injection:**

After each pattern's `PAGE_BREAK`:
```
```{=latex}
\setpatternname{K7 — Context Pruning}
```
```

After the final pattern in each section (before decision flow content):
```
```{=latex}
\clearpatternname
```
```

The pattern name is extracted from the pattern file's first `# ` heading in `assemble()`.

---

## Files Changed

| File | Change |
|---|---|
| `INTRO.md` | Rewritten (Phase 1 — done) |
| `build_book.py` | Assembly order, TOC injection, decision flow injection, stripe injection, Appendix C (Phases 1–3) |
| `header.tex` | Add eso-pic/tikz/xcolor, stripe definition (Phase 3) |
| `CHAPTER-0.md` | Add 0.0 LLM primer, update preamble tone (Phase 2) |
| `TAXONOMY-DRAFT.md` | Strip to section introductions only (Phase 2) |
| `OPEN-QUESTIONS.md` | New file — merged open questions + next steps (Phase 2) |
| `patterns/HUMANIZERS.md` | Add cognitive science grounding (Phase 2) |
| `patterns/ORCHESTRATION.md` | Add scaffold architecture dimensions (Phase 2) |
| `patterns/SIGNAL-DECISION.md` | New — decision flow for Signal section (Phase 2) |
| `patterns/KNOWLEDGE-DECISION.md` | New — decision flow for Knowledge section (Phase 2) |
| `patterns/REASONING-DECISION.md` | New — extracted from TAXONOMY-DRAFT (Phase 2) |
| `patterns/ORCHESTRATION-DECISION.md` | New — extracted from TAXONOMY-DRAFT (Phase 2) |
| `patterns/RELIABILITY-DECISION.md` | New — decision flow for Reliability section (Phase 2) |
| `patterns/INTEGRATION-DECISION.md` | New — extracted from TAXONOMY-DRAFT (Phase 2) |
| `patterns/HUMANIZERS-DECISION.md` | New — decision flow for Humanizer section (Phase 2) |
| `patterns/SIGNAL.md` | Add quick-reference table after Examples band (Phase 2) |
| `patterns/KNOWLEDGE.md` | Add quick-reference table after Examples band (Phase 2) |
| `patterns/REASONING.md` | Add quick-reference table after Examples band (Phase 2) |
| `patterns/ORCHESTRATION.md` | Add quick-reference table + scaffold dimensions (Phase 2) |
| `patterns/RELIABILITY.md` | Add quick-reference table after Examples band (Phase 2) |
| `patterns/INTEGRATION.md` | Add quick-reference table after Examples band (Phase 2) |
| `patterns/HUMANIZERS.md` | Add quick-reference table + cognitive science grounding (Phase 2) |

---

## Out of Scope

- GitHub README restructuring (separate effort)
- Pattern card colors per section (all patterns use same pale yellow)
- Individual pattern content edits
- New patterns
- Code examples
