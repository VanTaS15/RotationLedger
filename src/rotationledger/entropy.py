"""Shannon entropy and character-class analysis.

The detector in ``detect.py`` uses these helpers to decide whether a candidate
token looks like random key material rather than ordinary source text. Nothing
here touches the network or the clock, so the results are fully deterministic.
"""

