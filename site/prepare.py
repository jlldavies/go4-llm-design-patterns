#!/usr/bin/env python3
"""Copy content files into src/ ready for mdBook. Run before: mdbook build"""

import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"


def copy(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"  {src.relative_to(ROOT)} -> {dst.relative_to(ROOT)}")


print("Preparing src/...")

# All pattern files
src_patterns = SRC / "patterns"
src_patterns.mkdir(exist_ok=True)
for f in sorted((ROOT / "patterns").glob("*.md")):
    copy(f, src_patterns / f.name)

# Selected pdf-source files
src_pdf = SRC / "pdf-source"
src_pdf.mkdir(exist_ok=True)
for name in ["INTRO.md", "TAXONOMY-DRAFT.md", "CHAPTER-0.md", "REFERENCES.md", "APPENDIX-C.md"]:
    copy(ROOT / "pdf-source" / name, src_pdf / name)

print("Done.")
