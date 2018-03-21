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


def cmd_report(args: argparse.Namespace) -> int:
    commits = parse_log(_read(args.logfile))
    lifetimes = reconstruct(commits)
    _emit(exposure_days_report(lifetimes))
    return 1 if lifetimes else 0


def cmd_version(_args: argparse.Namespace) -> int:
    print(f"rotationledger {__version__}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rotationledger",
        description="Track the lifetime of leaked secrets through git history.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_scan = sub.add_parser("scan", help="list every credential-shaped finding")
    p_scan.add_argument("logfile", help="path to a git log -p export")
    p_scan.set_defaults(func=cmd_scan)

    p_life = sub.add_parser("lifetime", help="reconstruct secret lifetimes")
    p_life.add_argument("logfile", help="path to a git log -p export")
    p_life.set_defaults(func=cmd_lifetime)

    p_report = sub.add_parser("report", help="exposure-days report")
    p_report.add_argument("logfile", help="path to a git log -p export")
    p_report.set_defaults(func=cmd_report)

    p_version = sub.add_parser("version", help="print the version")
    p_version.set_defaults(func=cmd_version)

