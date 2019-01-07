import unittest

from rotationledger.detect import scan_line


class TestDetect(unittest.TestCase):
    def test_aws_access_key(self):
        findings = scan_line('AWS_ACCESS_KEY_ID = "AKIAEXAMPLE00000FAKE"')
