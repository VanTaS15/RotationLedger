#!/usr/bin/env python3
"""Mechanical quality gate for rotationledger.

Standard library only. Run from the project root:

    python scripts/verify.py

Exit code is the claim of correctness: 0 when every check passes, 1 when any
check fails. One line is printed per check so the result is readable in CI.

Each check corresponds to a defect that actually occurred in this tree and is
recorded in ../_standards/LESSONS.md. The checks are deliberately conservative:
they parse structure rather than eyeball it, because several of these defects
were invisible on inspection and only a script found them.
"""

from __future__ import annotations

import math
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "docs" / "assets"
README = ROOT / "README.md"
