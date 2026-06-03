#!/usr/bin/env python3
"""
Build-time linkifiers shared by build_book.py (PDF) and prepare.py (mdBook).
Output-agnostic: callers pass link-target callbacks.

Guards: never modify text inside fenced code blocks, inline code spans,
inline math ($...$), markdown headings, or existing markdown links.
"""

import re

# Spans that must never be touched: existing md links, inline code, inline math.
_PROTECTED = re.compile(r'(\[[^\]\n]*\]\([^)\n]*\)|`[^`\n]*`|\$[^$\n]+\$)')

# "mechanism(s) <numexpr>" where numexpr = ints joined by , / and / – / &
_NUMEXPR = r'\d+(?:\s*(?:,|and|–|&)\s*\d+)*'
_MECH = re.compile(r'\b(mechanisms?)\s+(' + _NUMEXPR + r')', re.IGNORECASE)
_NUM = re.compile(r'\d+')

# "CONFLICTS.md" optionally followed by ", CRITICAL N" / " CRITICAL N"
_CONF = re.compile(r'CONFLICTS\.md(?:,?\s+CRITICAL\s+(\d+))?')


def _on_segments(line, fn):
    """Apply fn only to the non-protected text segments of a single line."""
    parts = _PROTECTED.split(line)
    for i in range(0, len(parts), 2):  # even indices are unprotected text
        parts[i] = fn(parts[i])
    return ''.join(parts)


def _on_lines(text, fn):
    """Apply fn to each line that is not fenced code and not a heading."""
    out, in_fence = [], False
    for line in text.split('\n'):
        if line.lstrip().startswith('```'):
            in_fence = not in_fence
            out.append(line)
            continue
        if in_fence or re.match(r'^#{1,6}\s', line):
            out.append(line)
            continue
        out.append(_on_segments(line, fn))
    return '\n'.join(out)


def linkify_mechanisms(text, link_for):
    """link_for(n: int) -> markdown link string for mechanism n."""
    def repl(m):
        word, nums = m.group(1), m.group(2)
        linked = _NUM.sub(lambda x: link_for(int(x.group())), nums)
        return f'{word} {linked}'
    return _on_lines(text, lambda seg: _MECH.sub(repl, seg))


def linkify_conflicts(text, link_critical, link_appendix):
    """link_critical(n: int) -> str ; link_appendix() -> str (full md links)."""
    def repl(m):
        n = m.group(1)
        return link_critical(int(n)) if n else link_appendix()
    return _on_lines(text, lambda seg: _CONF.sub(repl, seg))
