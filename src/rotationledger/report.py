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
    """Raw hit list: one line per finding per commit that adds it."""

    lines: list[str] = []
    for commit in commits:
        for dl in commit.added:
            for f in scan_line(dl.text):
                lines.append(
                    f"{commit.short} {_fmt_date(commit.date)} "
                    f"{f.rule} {f.fingerprint} {dl.path} "
                    f"len={f.value_len} entropy={f.entropy:.2f}"
                )
