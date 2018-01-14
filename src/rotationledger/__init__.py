"""rotationledger: track the lifetime of leaked secrets through git history.

rotationledger reads a committed ``git log -p`` export offline, detects
credential-shaped strings with Shannon entropy plus named rules, then
reconstructs each secret's lifetime: where it was introduced, how many days it
stayed exposed, where it was removed or rotated, and whether it is still present
at HEAD. The headline artifact is an exposure-days report.

Standard library only, Python 3.11+, no network access.
"""

from __future__ import annotations

from .detect import Finding, scan_line
from .entropy import CharClasses, classify, looks_random, shannon_entropy
from .lifetime import Lifetime, reconstruct
from .logparse import Commit, DiffLine, parse_log

__all__ = [
    "Finding",
    "scan_line",
    "CharClasses",
    "classify",
    "looks_random",
