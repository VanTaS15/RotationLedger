"""Parse a committed ``git log -p`` export into commits and diff hunks.

This module never invokes git. It reads a text export that a user produced with
``git log -p --date=iso`` (or similar) and turns it into structured commits.
Each commit carries its added and removed lines with the file they touched, so
``lifetime.py`` can reconstruct when a secret entered and left the tree.

The parser is intentionally small and tolerant. It recognises the fields git
prints by default and ignores anything it does not need, rather than trying to
model the full diff grammar.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone


COMMIT_RE = re.compile(r"^commit ([0-9a-f]{7,40})\b")
AUTHOR_RE = re.compile(r"^Author:\s*(.*)$")
DATE_RE = re.compile(r"^Date:\s*(.*)$")
DIFF_GIT_RE = re.compile(r"^diff --git a/(.+?) b/(.+?)\s*$")
PLUS_FILE_RE = re.compile(r"^\+\+\+ b/(.+?)\s*$")
HUNK_RE = re.compile(r"^@@ .*@@")


@dataclass
class DiffLine:
    """A single added or removed line within a commit."""

    path: str
    kind: str  # "add" or "del"
    text: str


@dataclass
class Commit:
    """One commit from the log export."""

    sha: str
    author: str
    date: datetime
    subject: str
    added: list[DiffLine] = field(default_factory=list)
    removed: list[DiffLine] = field(default_factory=list)

    @property
    def short(self) -> str:
        return self.sha[:10]


def _parse_git_date(raw: str) -> datetime:
    """Parse the date formats git prints.

    Handles the ISO form ``2026-01-05 09:14:00 +0000`` and the default form
    ``Mon Jan 5 09:14:00 2026 +0000``. Falls back to a fixed epoch only if both
    fail, keeping the parser total.
    """
