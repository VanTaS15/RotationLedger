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


# Ordered named rules. The first structural rule that matches wins for a line,
# so a private key header is never also reported as a generic assignment.
_AWS_KEY_RE = re.compile(r"\b((?:AKIA|ASIA)[0-9A-Z]{16})\b")
_PRIVATE_KEY_RE = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")
_BEARER_RE = re.compile(r"\bBearer\s+([A-Za-z0-9\-._~+/]{20,}=*)")
_CONN_STRING_RE = re.compile(
    r"\b(?:postgres|postgresql|mysql|mongodb(?:\+srv)?|redis|amqp)://"
    r"[^\s:/@]+:([^\s:/@]{6,})@[^\s/]+"
)
_GENERIC_RE = re.compile(
    r"(?:secret|token|api[_-]?key|apikey|password|passwd|access[_-]?key)"
    r"['\"]?\s*[:=]\s*['\"]?([A-Za-z0-9\-._~+/]{%d,})['\"]?" % GENERIC_MIN_LEN,
    re.IGNORECASE,
)


def scan_line(text: str) -> list[Finding]:
    """Return every credential-shaped finding on one line.

    Structural rules (AWS, private key, bearer, connection string) are checked
    first. Only if none of them match on a captured region does the generic
    high-entropy assignment rule apply, which avoids double counting.
    """

    findings: list[Finding] = []
    matched_spans: list[tuple[int, int]] = []

    for m in _AWS_KEY_RE.finditer(text):
        val = m.group(1)
        findings.append(
            Finding("aws-access-key", _fingerprint(val), len(val), shannon_entropy(val))
        )
        matched_spans.append(m.span(1))

    if _PRIVATE_KEY_RE.search(text):
        marker = "-----BEGIN PRIVATE KEY-----"
        findings.append(
            Finding("private-key-header", _fingerprint(marker), len(marker), 0.0)
        )

    for m in _BEARER_RE.finditer(text):
        val = m.group(1)
        findings.append(
            Finding("bearer-token", _fingerprint(val), len(val), shannon_entropy(val))
        )
        matched_spans.append(m.span(1))

    for m in _CONN_STRING_RE.finditer(text):
        val = m.group(1)
        findings.append(
            Finding(
                "connection-string", _fingerprint(val), len(val), shannon_entropy(val)
            )
        )
        matched_spans.append(m.span(1))

    for m in _GENERIC_RE.finditer(text):
        val = m.group(1)
        span = m.span(1)
        if any(span[0] < e and s < span[1] for s, e in matched_spans):
            continue
        if not looks_random(val, GENERIC_MIN_LEN, GENERIC_MIN_ENTROPY):
            continue
        findings.append(
            Finding(
                "generic-high-entropy",
                _fingerprint(val),
                len(val),
                shannon_entropy(val),
            )
        )

    return findings

# draft note 1255
