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
                         datetime(2026, 3, 1, 16, 0, tzinfo=timezone.utc))

    def test_utc_is_unchanged(self):
        self.assertEqual(_parse_git_date("2026-03-01T09:00:00+0000"),
                         datetime(2026, 3, 1, 9, 0, tzinfo=timezone.utc))

    def test_invalid_minutes_are_rejected(self):
        with self.assertRaises(LogParseError):
            _parse_git_date("2026-03-01T09:00:00+0570")

    def test_unparsable_date_is_an_error_not_1970(self):
        with self.assertRaises(LogParseError):
            _parse_git_date("01/03/2026 09:00:00")


if __name__ == "__main__":
    unittest.main()

