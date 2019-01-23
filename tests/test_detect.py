import unittest

from rotationledger.detect import scan_line


class TestDetect(unittest.TestCase):
    def test_aws_access_key(self):
        findings = scan_line('AWS_ACCESS_KEY_ID = "AKIAEXAMPLE00000FAKE"')
        rules = [f.rule for f in findings]
        self.assertIn("aws-access-key", rules)

    def test_private_key_header(self):
        findings = scan_line("-----BEGIN RSA PRIVATE KEY-----")
        self.assertEqual([f.rule for f in findings], ["private-key-header"])

    def test_bearer_token(self):
        findings = scan_line('Authorization: Bearer abcDEF123456ghiJKL7890mnoPQR')
        self.assertIn("bearer-token", [f.rule for f in findings])

    def test_connection_string(self):
        findings = scan_line("postgres://user:s3cretPass99@db.example.invalid/app")
        self.assertIn("connection-string", [f.rule for f in findings])

