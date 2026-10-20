import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(*args):
    return subprocess.run([sys.executable, "-m", "rotationledger", *args], cwd=str(ROOT),
                          capture_output=True, text=True,
                          env={**__import__("os").environ, "PYTHONPATH": "src"})


class CliContractTests(unittest.TestCase):
    def test_missing_logfile_exits_2(self):
        r = run("scan", "does-not-exist.txt")
        self.assertEqual(r.returncode, 2, r.stderr)
        self.assertIn("error:", r.stderr)

    def test_version_prints(self):
        r = run("version")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.startswith("rotationledger "))


if __name__ == "__main__":
    unittest.main()
