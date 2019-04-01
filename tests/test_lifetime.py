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
