#!/usr/bin/env python3
"""Mechanical quality gate for rotationledger.

Standard library only. Run from the project root:

    python scripts/verify.py

Exit code is the claim of correctness: 0 when every check passes, 1 when any
check fails. One line is printed per check so the result is readable in CI.

Each check corresponds to a defect that actually occurred in this tree and is
recorded in ../_standards/LESSONS.md. The checks are deliberately conservative:
they parse structure rather than eyeball it, because several of these defects
were invisible on inspection and only a script found them.
"""

from __future__ import annotations

import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
README = ROOT / "README.md"

SVG_NS = "{http://www.w3.org/2000/svg}"

# Banned filter primitives (decoration, not information; Lesson 9).
BANNED_FILTERS = ("feGaussianBlur", "feDropShadow", "feTurbulence")

# Marketing terms a technical README should not lean on. Kept small and
# specific so the check does not fire on ordinary prose.
BANNED_MARKETING = (
    "blazing", "blazingly", "seamless", "seamlessly", "cutting-edge",
    "cutting edge", "state-of-the-art", "state of the art", "revolutionary",
    "game-changing", "game changing", "world-class", "world class",
    "next-generation", "next generation", "supercharge", "turbocharge",
    "effortless", "effortlessly", "unleash", "unlock the power",
    "leverage synergies", "best-in-class", "best in class",
)

# The em dash in all three of its disguises (Lesson 1). The two HTML forms are
# assembled from parts so this source file does not itself contain the literal
# strings it searches for, which would make the check flag its own text.
EM_DASH_FORMS = (
    "\u2014",
    "&#" + "8212;",
    "&m" + "dash;",
)

# Text file extensions to scan for the em dash. Byte-for-byte, no rendering.
TEXT_SUFFIXES = {
    ".py", ".md", ".txt", ".svg", ".toml", ".cff", ".yml", ".yaml",
    ".cfg", ".ini", ".gitignore", ".gitattributes", ".editorconfig",
    ".gitlog", "",
}

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "build", "dist"}


def _iter_files() -> list[Path]:
    out: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        if path.name.endswith(".egg-info"):
            continue
        out.append(path)
    return out

