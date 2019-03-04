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
