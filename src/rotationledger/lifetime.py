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
