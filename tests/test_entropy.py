import unittest

from rotationledger.entropy import classify, looks_random, shannon_entropy


class TestEntropy(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(shannon_entropy(""), 0.0)

    def test_single_repeated_char_is_zero(self):
