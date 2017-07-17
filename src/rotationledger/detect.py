"""Named detection rules for credential-shaped strings.

Each rule reports a match with a stable ``rule`` name and a ``fingerprint``.
The fingerprint identifies one logical secret across commits without ever
storing the secret value itself: it is a truncated SHA-256 of the raw match.
Lifetime tracking keys on the fingerprint, so the same secret added and later
removed is recognised as one credential, not two.
"""

from __future__ import annotations

