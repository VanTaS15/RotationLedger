import unittest

from rotationledger.entropy import classify, looks_random, shannon_entropy


class TestEntropy(unittest.TestCase):
    def test_empty_is_zero(self):
        self.assertEqual(shannon_entropy(""), 0.0)

    def test_single_repeated_char_is_zero(self):
        self.assertEqual(shannon_entropy("aaaaaa"), 0.0)

    def test_uniform_two_symbols_is_one_bit(self):
        self.assertAlmostEqual(shannon_entropy("abab"), 1.0, places=9)

    def test_uniform_four_symbols_is_two_bits(self):
        self.assertAlmostEqual(shannon_entropy("abcd"), 2.0, places=9)

    def test_classify_counts_families(self):
        c = classify("aB3$")
        self.assertTrue(c.lower and c.upper and c.digit and c.symbol)
        self.assertEqual(c.count, 4)

    def test_looks_random_rejects_short(self):
        self.assertFalse(looks_random("aB3xY", min_len=20))

