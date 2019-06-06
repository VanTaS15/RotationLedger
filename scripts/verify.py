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


def _svgs() -> list[Path]:
    if not ASSETS.is_dir():
        return []
    return sorted(ASSETS.rglob("*.svg"))


def _is_text(path: Path) -> bool:
    return path.suffix.lower() in TEXT_SUFFIXES or path.name.startswith(".")


# --- Check 1: every SVG parses as XML ---------------------------------------
def check_svg_parses() -> tuple[bool, str]:
    failures: list[str] = []
    for svg in _svgs():
        try:
            ET.parse(svg)
        except ET.ParseError as exc:
            failures.append(f"{svg.relative_to(ROOT)}: {exc}")
    if failures:
        return False, "svg parses as XML: " + "; ".join(failures)
    return True, f"svg parses as XML: {len(_svgs())} file(s) ok"


# --- Check 2: no banned filter primitives -----------------------------------
def check_no_banned_filters() -> tuple[bool, str]:
    failures: list[str] = []
    for svg in _svgs():
        text = svg.read_text(encoding="utf-8")
        for term in BANNED_FILTERS:
            if term in text:
                failures.append(f"{svg.relative_to(ROOT)}: {term}")
    if failures:
        return False, "no banned filters: " + "; ".join(failures)
    return True, "no banned filters: none present"


# --- Check 3: no illegal -- inside an XML comment ---------------------------
def check_no_double_hyphen_comment() -> tuple[bool, str]:
    comment_re = re.compile(r"<!--(.*?)-->", re.DOTALL)
    failures: list[str] = []
    for svg in _svgs():
        text = svg.read_text(encoding="utf-8")
        for body in comment_re.findall(text):
            if "--" in body:
                failures.append(str(svg.relative_to(ROOT)))
                break
    if failures:
        return False, "no -- in XML comments: " + "; ".join(failures)
    return True, "no -- in XML comments: clean"


# --- Check 4: no em dash in any tracked text file ---------------------------
def check_no_em_dash() -> tuple[bool, str]:
    failures: list[str] = []
    for path in _iter_files():
        if not _is_text(path):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for form in EM_DASH_FORMS:
            if form in text:
                failures.append(f"{path.relative_to(ROOT)}: {form!r}")
    if failures:
        return False, "no em dash (U+2014/&#8212;/&mdash;): " + "; ".join(failures)
    return True, "no em dash (U+2014/&#8212;/&mdash;): clean"


# --- Check 5: no pandoc image attribute block in README ---------------------
def check_no_pandoc_image_attr() -> tuple[bool, str]:
    if not README.is_file():
        return True, "no pandoc image attr in README: README absent"
    text = README.read_text(encoding="utf-8")
    # Match ){ ... width|height ... } as in ![alt](path){width=200}.
    pat = re.compile(r"\)\{[^}]*(?:width|height)[^}]*\}")
    if pat.search(text):
        return False, "no pandoc image attr in README: found ){...width/height...}"
    return True, "no pandoc image attr in README: clean"


# --- Check 6: no banned marketing terms in README ---------------------------
def check_no_marketing() -> tuple[bool, str]:
    if not README.is_file():
        return True, "no marketing terms in README: README absent"
    text = README.read_text(encoding="utf-8").lower()
    hits = [t for t in BANNED_MARKETING if t in text]
    if hits:
        return False, "no marketing terms in README: " + ", ".join(hits)
    return True, "no marketing terms in README: clean"


# --- Check 7: every SVG has viewBox, role=img, title, desc ------------------
def check_svg_accessibility() -> tuple[bool, str]:
    failures: list[str] = []
    for svg in _svgs():
        try:
            root = ET.parse(svg).getroot()
        except ET.ParseError:
            failures.append(f"{svg.relative_to(ROOT)}: unparseable")
            continue
        missing: list[str] = []
        if not root.get("viewBox"):
            missing.append("viewBox")
        if root.get("role") != "img":
            missing.append('role="img"')
        if root.find(f"{SVG_NS}title") is None:
            missing.append("<title>")
        if root.find(f"{SVG_NS}desc") is None:
            missing.append("<desc>")
        if missing:
            failures.append(f"{svg.relative_to(ROOT)}: {', '.join(missing)}")
    if failures:
        return False, "svg accessibility: " + "; ".join(failures)
    return True, f"svg accessibility: {len(_svgs())} file(s) ok"


# --- Check 8: no two labels on the same baseline overlap --------------------
def _char_width_em(font_family: str) -> float:
    fam = (font_family or "").lower()
    mono_hints = ("mono", "consolas", "courier", "cascadia", "jetbrains")
    return 0.60 if any(h in fam for h in mono_hints) else 0.58


def _text_extent(elem, x: float, size: float, anchor: str) -> tuple[float, float]:
    content = "".join(elem.itertext())
    width = len(content) * _char_width_em(elem.get("font-family", "")) * size
