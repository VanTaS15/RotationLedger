"""Command line interface for rotationledger.

Subcommands:
  scan      list every credential-shaped finding in the export
  lifetime  reconstruct each secret's introduce/rotate/still-live state
  report    the exposure-days report, the headline artifact
  version   print the package version

Exit codes: 0 clean (no findings), 1 findings present, 2 usage error.
"""

from __future__ import annotations

import argparse
import sys

