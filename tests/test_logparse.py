import unittest

from rotationledger.logparse import parse_log

LOG = """commit 1111111222222333333444444555555666666000
Author: A Dev <a@example.invalid>
Date:   2026-01-05 09:14:00 +0000

    init commit

diff --git a/config.py b/config.py
--- /dev/null
+++ b/config.py
@@ -0,0 +1,2 @@
+import os
+KEY = "AKIAEXAMPLE00000FAKE"

commit 7777777888888999999000000aaaaaabbbbbb000
Author: B Dev <b@example.invalid>
Date:   2026-02-10 12:00:00 +0000

    remove key

diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,1 @@
 import os
-KEY = "AKIAEXAMPLE00000FAKE"
"""


class TestLogParse(unittest.TestCase):
    def test_parses_two_commits(self):
        commits = parse_log(LOG)
        self.assertEqual(len(commits), 2)

    def test_newest_first_order_preserved(self):
        commits = parse_log(LOG)
        self.assertTrue(commits[0].sha.startswith("1111111"))
        self.assertTrue(commits[1].sha.startswith("7777777"))

    def test_subject_captured(self):
        commits = parse_log(LOG)
        self.assertEqual(commits[0].subject, "init commit")

    def test_date_parsed_iso(self):
        commits = parse_log(LOG)
        self.assertEqual(commits[0].date.year, 2026)
        self.assertEqual(commits[0].date.month, 1)

    def test_added_and_removed_lines(self):
        commits = parse_log(LOG)
        added_texts = [d.text for d in commits[0].added]
        self.assertIn('KEY = "AKIAEXAMPLE00000FAKE"', added_texts)
        removed_texts = [d.text for d in commits[1].removed]
