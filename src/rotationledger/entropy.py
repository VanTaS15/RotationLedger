"""Shannon entropy and character-class analysis.

The detector in ``detect.py`` uses these helpers to decide whether a candidate
token looks like random key material rather than ordinary source text. Nothing
here touches the network or the clock, so the results are fully deterministic.
"""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class CharClasses:
    """Which character families a token draws from."""

    lower: bool
    upper: bool
    digit: bool
    symbol: bool

    @property
    def count(self) -> int:
        return sum((self.lower, self.upper, self.digit, self.symbol))


def shannon_entropy(text: str) -> float:
    """Return the Shannon entropy of ``text`` in bits per character.

    An empty string has zero entropy. A string of one repeated character also
    has zero entropy. A perfectly uniform string over N symbols approaches
    log2(N).
    """

