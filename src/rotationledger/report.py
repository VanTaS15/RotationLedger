"""Line-oriented, deterministic reports.

Every function here returns a list of text lines with no trailing whitespace so
output diffs cleanly in git. No wall-clock time is read; all dates come from the
parsed commits.
"""

from __future__ import annotations

from .detect import scan_line
from .lifetime import Lifetime
from .logparse import Commit


def _fmt_date(dt) -> str:
    return dt.strftime("%Y-%m-%d")


def scan_report(commits: list[Commit]) -> list[str]:
