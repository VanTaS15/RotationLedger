"""Reconstruct each secret's lifetime from parsed commits.

For every distinct credential fingerprint the state machine walks the commit
history from oldest to newest and records:

- introduced_at: the commit and date where the secret was first added
- removed_at: the commit and date where the secret line was deleted, if any
- still_live: whether the secret is present in the tree at HEAD
- exposure_days: the window in days the secret was live

A secret can be removed and then re-added; this is modelled as separate
lifetimes so a rotation that reuses a value is not silently merged. State
transitions are: absent -> live (introduce), live -> removed (rotate/remove).
The headline number the report cares about is exposure_days.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from .detect import scan_line
from .logparse import Commit


@dataclass
class Lifetime:
    """The tracked life of one credential occurrence."""

    fingerprint: str
    rule: str
    introduced_sha: str
    introduced_at: datetime
    removed_sha: str | None = None
    removed_at: datetime | None = None
    still_live: bool = True

    @property
    def exposure_days(self) -> int:
        """Whole days between introduction and removal.

        For a still-live secret this is measured against the newest commit in
        the analysed history, since the tool is offline and has no later
        reference point. The report labels this case as open ended.
        """

        end = self.removed_at if self.removed_at is not None else self._head_date
        if end is None:
            return 0
        delta = end - self.introduced_at
        return max(delta.days, 0)

    # Set by the reconstructor for still-live secrets.
    _head_date: datetime | None = field(default=None, repr=False)

    @property
    def state(self) -> str:
        return "live" if self.still_live else "rotated"


def _findings_by_fingerprint(lines) -> dict[str, str]:
    """Map fingerprint -> rule name for a set of diff lines."""

    out: dict[str, str] = {}
    for dl in lines:
        for f in scan_line(dl.text):
            out.setdefault(f.fingerprint, f.rule)
    return out


def reconstruct(commits: list[Commit]) -> list[Lifetime]:
    """Build lifetimes from commits.

    ``commits`` is expected newest-first (as git prints). The walk runs oldest
    first so introduction precedes removal in time.
    """

    if not commits:
        return []

    oldest_first = list(reversed(commits))
    head_date = oldest_first[-1].date

    # fingerprint -> currently open Lifetime, if any.
    open_life: dict[str, Lifetime] = {}
    lifetimes: list[Lifetime] = []

    for commit in oldest_first:
        added = _findings_by_fingerprint(commit.added)
        removed = _findings_by_fingerprint(commit.removed)

        # Removals first: a line changed in one commit shows as del then add,
        # but for distinct fingerprints order does not matter within a commit.
        for fp, _rule in removed.items():
            life = open_life.get(fp)
            if life is not None and fp not in added:
                life.removed_sha = commit.short
                life.removed_at = commit.date
                life.still_live = False
                lifetimes.append(life)
                del open_life[fp]

        for fp, rule in added.items():
