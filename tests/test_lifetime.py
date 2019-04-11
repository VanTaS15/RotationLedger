import os
import unittest

from rotationledger.lifetime import reconstruct
from rotationledger.logparse import parse_log
from rotationledger.report import exposure_days_report, lifetime_report

SAMPLE = os.path.join(
    os.path.dirname(__file__), "..", "samples", "history.gitlog"
)


def load_sample():
    with open(SAMPLE, "r", encoding="utf-8") as fh:
        return reconstruct(parse_log(fh.read()))


class TestLifetime(unittest.TestCase):
    def test_three_credentials_tracked(self):
        self.assertEqual(len(load_sample()), 3)

    def test_one_still_live(self):
        live = [l for l in load_sample() if l.still_live]
        self.assertEqual(len(live), 1)
        self.assertEqual(live[0].rule, "generic-high-entropy")

    def test_two_rotated(self):
        rotated = [l for l in load_sample() if not l.still_live]
        self.assertEqual(len(rotated), 2)

    def test_aws_key_exposure_window(self):
        # Introduced 2026-01-05, removed 2026-03-20 => 74 days.
        aws = [l for l in load_sample() if l.rule == "aws-access-key"][0]
        self.assertFalse(aws.still_live)
        self.assertEqual(aws.exposure_days, 74)

    def test_bearer_exposure_window(self):
        # Introduced 2026-01-05, removed 2026-04-02 => 87 days.
        bearer = [l for l in load_sample() if l.rule == "bearer-token"][0]
        self.assertEqual(bearer.exposure_days, 87)

    def test_reports_are_line_lists(self):
        lifetimes = load_sample()
