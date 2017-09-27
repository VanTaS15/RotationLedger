import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rotationledger.logparse import LogParseError, _parse_git_date  # noqa: E402


class IsoOffsetTests(unittest.TestCase):
    def test_plus_offset_converts_to_utc(self):
        self.assertEqual(_parse_git_date("2026-03-01T09:00:00+0530"),
                         datetime(2026, 3, 1, 3, 30, tzinfo=timezone.utc))

    def test_minus_offset_converts_to_utc(self):
        self.assertEqual(_parse_git_date("2026-03-01T09:00:00-0700"),
