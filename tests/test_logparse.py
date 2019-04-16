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

