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

from . import __version__
from .lifetime import reconstruct
from .logparse import parse_log
from .report import exposure_days_report, lifetime_report, scan_report


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _emit(lines: list[str]) -> None:
    for line in lines:
        print(line)


def cmd_scan(args: argparse.Namespace) -> int:
    commits = parse_log(_read(args.logfile))
    lines = scan_report(commits)
    _emit(lines)
    return 1 if lines else 0


def cmd_lifetime(args: argparse.Namespace) -> int:
    commits = parse_log(_read(args.logfile))
    lifetimes = reconstruct(commits)
    _emit(lifetime_report(lifetimes))
    return 1 if lifetimes else 0
