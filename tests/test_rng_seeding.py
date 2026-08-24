import random
import unittest

from satprep.core.rng import derive_seed, rng_for


class TestSeedDerivation(unittest.TestCase):
    def test_deterministic(self):
        self.assertEqual(derive_seed("a", 1, "x"), derive_seed("a", 1, "x"))

    def test_order_and_type_sensitive(self):
        self.assertNotEqual(derive_seed("a", "b"), derive_seed("b", "a"))
        self.assertNotEqual(derive_seed("12"), derive_seed(1, 2))

    def test_in_range(self):
        for parts in [("u1", "session", 3), ("", ""), (None, True)]:
            seed = derive_seed(*parts)
            self.assertTrue(0 <= seed < (1 << 63))

    def test_streams_independent_but_reproducible(self):
        master = derive_seed("master")
        r1 = rng_for(master, "slot", 0)
        r2 = rng_for(master, "slot", 0)
        r3 = rng_for(master, "slot", 1)
        seq1 = [r1.random() for _ in range(20)]
        seq2 = [r2.random() for _ in range(20)]
        seq3 = [r3.random() for _ in range(20)]
        self.assertEqual(seq1, seq2)
        self.assertNotEqual(seq1, seq3)

    def test_rng_isolated_from_global_random(self):
        master = derive_seed("m")
        r = rng_for(master, "x")
        vals = [r.random() for _ in range(5)]
        fresh = rng_for(master, "x")
        self.assertEqual([fresh.random() for _ in range(5)], vals)
        self.assertNotEqual(vals[0], vals[1])


if __name__ == "__main__":
    unittest.main()
