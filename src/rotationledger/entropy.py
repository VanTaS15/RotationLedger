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

    if not text:
        return 0.0
    counts: dict[str, int] = {}
    for ch in text:
        counts[ch] = counts.get(ch, 0) + 1
    length = len(text)
    total = 0.0
    for n in counts.values():
        p = n / length
        total -= p * math.log2(p)
    return total


def classify(text: str) -> CharClasses:
    """Report which character classes appear in ``text``."""

    lower = upper = digit = symbol = False
    for ch in text:
        if ch.islower():
            lower = True
        elif ch.isupper():
            upper = True
        elif ch.isdigit():
            digit = True
        else:
            symbol = True
    return CharClasses(lower=lower, upper=upper, digit=digit, symbol=symbol)


def looks_random(text: str, min_len: int = 20, min_entropy: float = 3.5) -> bool:
    """Heuristic gate for a high-entropy secret candidate.

    A token is treated as random-looking when it is long enough, mixes at least
    two character classes, and has entropy at or above ``min_entropy`` bits per
    character. The defaults are tuned for base64 and hex secrets in
    ``detect.py`` and are recorded there so results stay reproducible.
    """

    if len(text) < min_len:
        return False
    if classify(text).count < 2:
        return False
    return shannon_entropy(text) >= min_entropy

# draft note 1252
