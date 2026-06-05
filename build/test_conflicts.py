#!/usr/bin/env python3
"""Plain-assert tests for conflicts_lib.py. Run: python3 build/test_conflicts.py"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from conflicts_lib import primary_category_of_pair, primary_category_of_title, parse_sections


def eq(got, want):
    assert got == want, f"\n  got:  {got!r}\n  want: {want!r}"


eq(primary_category_of_pair("R4 $\\oplus$ R5"), "Reasoning")
eq(primary_category_of_pair("S9 H/S V7"), "Signal")
eq(primary_category_of_pair("K6/K7 $\\sim$ K11"), "Knowledge")
eq(primary_category_of_pair("V4/V15/V6"), "Reliability")
eq(primary_category_of_title("Signal vs Reasoning"), "Signal")
eq(primary_category_of_title("Reliability vs Signal/Reasoning"), "Reliability")
eq(primary_category_of_title("Humanizer vs Other Categories"), "Humanizers")

s = parse_sections("intro\n## A\na body\n## B\nb body")
eq(s[""], "intro")
eq(s["A"], "a body")
eq(s["B"], "b body")

print("ALL CONFLICTS TESTS PASSED")
