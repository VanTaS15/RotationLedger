"""Named detection rules for credential-shaped strings.

Each rule reports a match with a stable ``rule`` name and a ``fingerprint``.
The fingerprint identifies one logical secret across commits without ever
storing the secret value itself: it is a truncated SHA-256 of the raw match.
Lifetime tracking keys on the fingerprint, so the same secret added and later
removed is recognised as one credential, not two.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass

from .entropy import looks_random, shannon_entropy

# High-entropy generic assignment thresholds. Recorded here so a reader can
# reproduce every generic finding by hand.
GENERIC_MIN_LEN = 20
GENERIC_MIN_ENTROPY = 3.5


@dataclass(frozen=True)
class Finding:
    """One detected credential-shaped token."""

    rule: str
    fingerprint: str
    value_len: int
    entropy: float


def _fingerprint(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]
