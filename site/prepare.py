#!/usr/bin/env python3
"""Copy content files into src/ ready for mdBook, injecting on-screen links.
Run before: mdbook build"""

from pathlib import Path
from linkify import linkify_mechanisms, linkify_conflicts

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"


def transform(text: str, dest_subdir: str) -> str:
    """Inject mdBook (relative-path) links. dest_subdir is 'patterns' or 'pdf-source'."""
    if dest_subdir == "patterns":
        mech = lambda n: f"[{n}](../pdf-source/CHAPTER-0.md#m{n})"
        crit = lambda n: f"[Appendix A, Critical {n}](CONFLICTS.md#critical-{n})"
        appx = lambda: "[Appendix A](CONFLICTS.md)"
    else:  # pdf-source
        mech = lambda n: f"[{n}](CHAPTER-0.md#m{n})"
        crit = lambda n: f"[Appendix A, Critical {n}](../patterns/CONFLICTS.md#critical-{n})"
        appx = lambda: "[Appendix A](../patterns/CONFLICTS.md)"
    text = linkify_mechanisms(text, mech)
    text = linkify_conflicts(text, crit, appx)
    return text


def copy_transformed(src: Path, dst: Path, dest_subdir: str) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(transform(src.read_text(encoding="utf-8"), dest_subdir),
                   encoding="utf-8")
    print(f"  {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")


print("Preparing src/...")

# All pattern files
src_patterns = SRC / "patterns"
src_patterns.mkdir(exist_ok=True)
for f in sorted((ROOT / "patterns").glob("*.md")):
    copy_transformed(f, src_patterns / f.name, "patterns")

# Selected pdf-source files
src_pdf = SRC / "pdf-source"
src_pdf.mkdir(exist_ok=True)
for name in ["INTRO.md", "TAXONOMY-DRAFT.md", "CHAPTER-0.md", "REFERENCES.md", "APPENDIX-C.md"]:
    copy_transformed(ROOT / "pdf-source" / name, src_pdf / name, "pdf-source")

print("Done.")
