#!/usr/bin/env python3
"""Assemble GO4 standalone files into one master book.md, then pandoc → PDF."""

from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "site"))
from linkify import linkify_mechanisms, linkify_conflicts

PDF_SRC = Path(__file__).parent          # pdf-source/ — book source markdown
ROOT = PDF_SRC.parent                    # repo root — patterns/, GO4.pdf, book.md
PATTERNS = ROOT / "patterns"
OUT_MD = ROOT / "book.md"
OUT_PDF = ROOT / "GO4.pdf"

# Category map: (chapter title, intro file, standalone order)
CATEGORIES = [
    ("Category I — Signal Patterns", "SIGNAL.md",
     ["S1-Zero-Shot", "S2-Few-Shot", "S3-Persona", "S4-Instruction-Decomposition",
      "S5-Constraint-Framing", "S6-Output-Template", "S8-Meta-Prompt",
      "S9-Constitutional-Framing"]),
    ("Category II — Knowledge Patterns", "KNOWLEDGE.md",
     [f"K{i}-" for i in range(1, 14)]),
    ("Category III — Reasoning Patterns", "REASONING.md",
     ["R1-Zero-Shot-CoT", "R2-Few-Shot-CoT", "R3-Plan-and-Solve", "R4-ReAct",
      "R5-ReWOO", "R6-Self-Ask", "R7-Reflexion", "R8-Self-Refine",
      "R9-Tree-of-Thoughts", "R10-LATS", "R11-Buffer-of-Thoughts",
      "R12-Skeleton-of-Thought", "R13-CodeAct", "R14-Program-of-Thoughts",
      "R16-Talker-Reasoner", "R17-Self-Consistency-Voting",
      "R18-Graph-of-Thoughts", "R19-Step-Back-Prompting",
      "R20-Chain-of-Verification"]),
    ("Category IV — Orchestration Patterns", "ORCHESTRATION.md",
     [f"O{i}-" for i in range(1, 19)]),
    ("Category V — Reliability Patterns", "RELIABILITY.md",
     [f"V{i}-" for i in range(1, 21)]),
    ("Category VI — Integration Patterns", "INTEGRATION.md",
     [f"I{i}-" for i in range(1, 7)]),
    ("Category VII — Humanizer Patterns", "HUMANIZERS.md",
     [f"H{i}-" for i in range(1, 11)]),
]


def resolve(prefix: str) -> Path:
    """Find the actual file matching a prefix like 'K3-'."""
    if (PATTERNS / f"{prefix}.md").exists():
        return PATTERNS / f"{prefix}.md"
    matches = sorted(PATTERNS.glob(f"{prefix}*.md"))
    if not matches:
        raise FileNotFoundError(prefix)
    return matches[0]


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def strip_first_h1(text: str) -> str:
    """Remove the first '# ...' line and any leading blank lines after it."""
    lines = text.splitlines()
    out = []
    stripped = False
    for line in lines:
        if not stripped and line.startswith("# ") and not line.startswith("## "):
            stripped = True
            continue
        if stripped and not out and not line.strip():
            continue
        out.append(line)
    return "\n".join(out)


_PATTERN_STUB = re.compile(r"^## [A-Z]\d+\b")
_NEXT_STEPS = re.compile(r"^## Next Steps", re.IGNORECASE)


def strip_planning(text: str) -> str:
    """Strip any '## Next Steps' section and everything after it."""
    out = []
    for line in text.splitlines():
        if _NEXT_STEPS.match(line):
            break
        out.append(line)
    while out and (out[-1].strip() in ("", "---")):
        out.pop()
    return "\n".join(out) + "\n"


def strip_category_stubs(text: str) -> str:
    """Keep category file intro (Usage/Forces/Structure/Examples/See also)
    and drop the per-pattern stub blocks — the full standalones follow."""
    out = []
    for line in text.splitlines():
        if _PATTERN_STUB.match(line):
            break
        out.append(line)
    # Trim trailing horizontal rules / blank lines.
    while out and (out[-1].strip() in ("", "---")):
        out.pop()
    return "\n".join(out) + "\n"


def shift_headings(text: str, by: int = 1) -> str:
    """Shift markdown headings down by N levels. Caps at H6."""
    def shift(match):
        hashes = match.group(1)
        new_level = min(len(hashes) + by, 6)
        return "#" * new_level + " "
    out_lines = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if not in_fence:
            line = re.sub(r"^(#{1,6}) ", shift, line)
        out_lines.append(line)
    return "\n".join(out_lines)


def pattern_label(path: Path) -> str:
    """Return 'K7 — Context Pruning' from the first H1 of a pattern file."""
    first_line = path.read_text(encoding="utf-8").splitlines()[0]
    title = first_line.lstrip("# ").strip()
    m = re.match(r"([A-Z]\d+)\s+(?:—\s*)?(.+)", title)
    if m:
        return f"{m.group(1)} — {m.group(2)}"
    return title


# Escape literal backslash-letter sequences ("\n", "\t" etc) outside code
# spans/fences and outside math spans so XeLaTeX doesn't see them as
# undefined control sequences.
_BACKSLASH_LETTER = re.compile(r"\\([a-zA-Z])")

# Matches inline code spans OR inline math spans — both must pass through
# unmodified so LaTeX commands inside math (e.g. \alpha, \mu, \text{}) are
# preserved.  Display math lines (starting with $$) are handled separately.
_PROTECTED_SPAN = re.compile(r"(`[^`\n]*`|\$[^$\n]+\$)")


def latex_safe(text: str) -> str:
    out_lines = []
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
            out_lines.append(line)
            continue
        if in_fence:
            out_lines.append(line)
            continue
        # Display-math lines ($$...$$) contain only LaTeX — pass untouched.
        if line.strip().startswith("$$"):
            out_lines.append(line)
            continue
        # Split by code spans and inline math spans; odd-indexed pieces are
        # the protected spans and must not be modified.
        pieces = _PROTECTED_SPAN.split(line)
        for i, piece in enumerate(pieces):
            if i % 2 == 1:  # code span or inline math — untouched
                continue
            pieces[i] = _BACKSLASH_LETTER.sub(r"\\\\\1", piece)
        out_lines.append("".join(pieces))
    return "\n".join(out_lines)


# Raw LaTeX page break using pandoc's fenced raw block — bypasses latex_safe().
PAGE_BREAK = "\n```{=latex}\n\\clearpage\n```\n"
TOC = "\n```{=latex}\n\\tableofcontents\n\\clearpage\n```\n"


def assemble() -> str:
    parts = []

    # YAML front matter
    parts.append(
        "---\n"
        'title: "The Gang of Four for AI Engineering"\n'
        'subtitle: "A Pattern Catalog for LLM Systems"\n'
        'author: "James Davies"\n'
        'date: "May 2026"\n'
        "---\n"
    )

    # Introduction — before the TOC
    intro = read(PDF_SRC / "INTRO.md")
    parts.append("# Introduction\n")
    parts.append(strip_first_h1(intro))
    parts.append("\n")

    # TOC placed after Introduction
    parts.append(TOC)

    # The Pattern Catalog (TAXONOMY-DRAFT) — strip planning sections
    tax = read(PDF_SRC / "TAXONOMY-DRAFT.md")
    parts.append("# The Pattern Catalog\n")
    parts.append(strip_planning(strip_first_h1(tax)))
    parts.append("\n")

    # Categories
    for chapter_title, intro_file, standalones in CATEGORIES:
        parts.append(f"# {chapter_title}\n")
        intro_text = read(PATTERNS / intro_file)
        intro_body = strip_category_stubs(strip_first_h1(intro_text))
        parts.append(intro_body)
        parts.append("\n")

        for prefix in standalones:
            path = resolve(prefix)
            body = read(path)
            first_line = body.splitlines()[0]
            title = first_line.lstrip("# ").strip()
            label = pattern_label(path)
            parts.append(PAGE_BREAK)
            # Stripe: set for this pattern
            parts.append(f"\n```{{=latex}}\n\\setpatternname{{{label}}}\n```\n")
            parts.append(f"## {title}\n")
            rest = strip_first_h1(body)
            parts.append(shift_headings(rest, by=2))
            parts.append("\n")

        # Stripe: clear before decision companion (decision pages have no stripe)
        parts.append("\n```{=latex}\n\\clearpatternname\n```\n")

        # Decision companion file — appended after section's final pattern
        decision_file = PATTERNS / intro_file.replace(".md", "-DECISION.md")
        if decision_file.exists():
            parts.append(PAGE_BREAK)
            parts.append(strip_first_h1(read(decision_file)))
            parts.append("\n")

    # Mechanisms — back-matter reference (formerly Chapter 0)
    parts.append(PAGE_BREAK)
    chapter0 = read(PDF_SRC / "CHAPTER-0.md")
    parts.append("# The Mechanical Foundation\n")
    parts.append(strip_first_h1(chapter0))
    parts.append("\n")

    # Appendix A — Conflicts
    parts.append(PAGE_BREAK)
    parts.append("# Appendix A — Conflicts {#appendix-conflicts}\n")
    parts.append(strip_first_h1(read(PATTERNS / "CONFLICTS.md")))
    parts.append("\n")

    # Appendix B — References
    parts.append(PAGE_BREAK)
    parts.append("# Appendix B — References\n")
    parts.append(strip_first_h1(read(PDF_SRC / "REFERENCES.md")))
    parts.append("\n")

    # Appendix C — Anti-Patterns and Composition Examples
    parts.append(PAGE_BREAK)
    parts.append("# Appendix C — Anti-Patterns and Composition Examples\n")
    parts.append(strip_first_h1(read(PDF_SRC / "APPENDIX-C.md")))
    parts.append("\n")

    return "\n".join(parts)


def linkify_pdf(text: str) -> str:
    """Inject single-document (#anchor) links for the PDF."""
    text = linkify_mechanisms(text, lambda n: f"[{n}](#m{n})")
    text = linkify_conflicts(
        text,
        lambda n: f"[Appendix A, Critical {n}](#critical-{n})",
        lambda: "[Appendix A](#appendix-conflicts)",
    )
    return text


def main():
    OUT_MD.write_text(latex_safe(linkify_pdf(assemble())), encoding="utf-8")
    print(f"wrote {OUT_MD} ({OUT_MD.stat().st_size:,} bytes)")

    cmd = [
        "pandoc", str(OUT_MD), "-o", str(OUT_PDF),
        "--pdf-engine=xelatex",
        "--top-level-division=chapter",
        "-V", "documentclass=book",
        "-V", "classoption=oneside",
        "-V", "geometry:a4paper,top=2.8cm,bottom=2.5cm,left=2.5cm,right=2.5cm",
        "-V", "mainfont=Charter",
        "-V", "sansfont=Avenir Next",
        "-V", "monofont=Menlo",
        "-V", "monofontoptions=Scale=0.82",
        "-V", "fontsize=11pt",
        "-V", "linestretch=1.18",
        "-V", "colorlinks=true",
        "-V", "linkcolor=NavyBlue",
        "-V", "urlcolor=NavyBlue",
        "-V", "toccolor=black",
        "-H", str(PDF_SRC / "header.tex"),
    ]
    print("running:", " ".join(cmd))
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr, file=sys.stderr)
        sys.exit(result.returncode)
    size_mb = OUT_PDF.stat().st_size / 1_048_576
    print(f"wrote {OUT_PDF} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
