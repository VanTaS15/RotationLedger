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
    lines.sort()
    return lines


def lifetime_report(lifetimes: list[Lifetime]) -> list[str]:
    """One line per credential lifetime, with the exposure window."""

    lines: list[str] = []
    for life in lifetimes:
        removed = life.removed_sha if life.removed_sha else "-"
        removed_date = _fmt_date(life.removed_at) if life.removed_at else "-"
        lines.append(
            f"{life.fingerprint} {life.rule} "
            f"introduced={life.introduced_sha}@{_fmt_date(life.introduced_at)} "
            f"removed={removed}@{removed_date} "
            f"state={life.state} exposure_days={life.exposure_days}"
        )
    return lines


def exposure_days_report(lifetimes: list[Lifetime]) -> list[str]:
    """Headline artifact: exposure days, worst first, with a summary footer."""

    ordered = sorted(
        lifetimes, key=lambda l: (-l.exposure_days, l.fingerprint)
    )
    lines: list[str] = ["EXPOSURE DAYS REPORT", ""]
    if not ordered:
        lines.append("no credentials detected")
        return lines

    for life in ordered:
        tail = " (open, measured to newest commit)" if life.still_live else ""
        lines.append(
            f"{life.exposure_days:>4}d  {life.rule:<22} {life.fingerprint} "
