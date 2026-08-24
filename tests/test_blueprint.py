import math
import unittest
from collections import Counter

from satprep.core.blueprint import (
    BlueprintModel,
    largest_remainder,
    sample_dirichlet,
)
from satprep.core.framework import (
    DEFAULT_PROFILE,
    DIFFICULTY_PROFILES,
    SECTION_MATH,
    SECTION_RW,
    leaf_weights,
)
from satprep.core.rng import rng_for


class TestLargestRemainder(unittest.TestCase):
    def test_exact_total(self):
        alloc = largest_remainder([0.2, 0.3, 0.5], 10)
        self.assertEqual(sum(alloc), 10)
        self.assertEqual(alloc, [2, 3, 5])

    def test_irrational_weights_hit_total(self):
        w = [1 / 3, 1 / 3, 1 / 3]
        for n in range(0, 30):
            self.assertEqual(sum(largest_remainder(w, n)), n)

    def test_remainder_goes_to_largest_fraction(self):
        alloc = largest_remainder([0.25, 0.25, 0.50], 5)
        self.assertEqual(alloc, [1, 1, 3])

    def test_tie_broken_by_index_deterministically(self):
        a = largest_remainder([0.5, 0.5], 3)
        b = largest_remainder([0.5, 0.5], 3)
        self.assertEqual(a, b)
        self.assertEqual(sum(a), 3)

    def test_zero_weight_gets_nothing(self):
        alloc = largest_remainder([0.0, 1.0, 0.0], 7)
        self.assertEqual(alloc, [0, 7, 0])

    def test_zero_total(self):
        self.assertEqual(largest_remainder([0.4, 0.6], 0), [0, 0])

    def test_all_zero_weights_rejected_for_positive_total(self):
        with self.assertRaises(ValueError):
            largest_remainder([0.0, 0.0], 4)

    def test_negative_total_rejected(self):
        with self.assertRaises(ValueError):
            largest_remainder([0.5, 0.5], -1)


class TestDirichletSampling(unittest.TestCase):
    def test_sums_to_one_and_reproducible(self):
        alphas = [400 * w for w in (0.28, 0.26, 0.26, 0.20)]
        r1 = rng_for(12345, "d1")
        r2 = rng_for(12345, "d1")
        p1 = sample_dirichlet(alphas, r1)
        p2 = sample_dirichlet(alphas, r2)
        self.assertAlmostEqual(sum(p1), 1.0, places=12)
        self.assertEqual(p1, p2)

    def test_concentrated_prior_draws_near_mean(self):
        alphas = [10000 * 0.7, 10000 * 0.3]
        r = rng_for(999, "conc")
        p = sample_dirichlet(alphas, r)
        self.assertLess(abs(p[0] - 0.7), 0.01)


class TestBlueprintModel(unittest.TestCase):
    def setUp(self):
        self.model = BlueprintModel(kappa=400.0)

    def _draw_many(self, total, section=None, skill_ids=None, profile=DEFAULT_PROFILE,
                   seeds=range(20)):
        agg = Counter()
        for s in seeds:
            bp = self.model.draw(total, section=section, skill_ids=skill_ids,
                                 profile=profile, seed=s)
            agg.update(bp.by_cell())
        return agg

    def test_exact_lengths_rw_and_math(self):
        for sec, per_mod in ((SECTION_RW, 27), (SECTION_MATH, 22)):
            bp = self.model.draw(per_mod, section=sec, seed=derive_seed_test(sec))
            self.assertEqual(bp.total, per_mod)
            self.assertEqual(bp.by_cell().total(), per_mod)
        mixed = self.model.draw(13, section=SECTION_MATH, seed=7)
        self.assertEqual(mixed.by_cell().total(), 13)
        zero = self.model.draw(0, section=SECTION_RW, seed=1)
        self.assertEqual(zero.by_cell().total(), 0)

    def test_counts_are_nonnegative_integers(self):
        bp = self.model.draw(27, section=SECTION_RW, seed=42)
        for cell, n in bp.counts:
            self.assertIsInstance(n, int)
            self.assertGreaterEqual(n, 0)

    def test_reproducible_given_same_seed(self):
        a = self.model.draw(27, section=SECTION_RW, seed="fixed-seed")
        b = self.model.draw(27, section=SECTION_RW, seed="fixed-seed")
        self.assertEqual(a.counts, b.counts)
        c = self.model.draw(27, section=SECTION_RW, seed="other-seed")
        self.assertNotEqual(a.counts, c.counts)

    def test_auto_seed_is_stable_for_same_inputs(self):
        a = self.model.draw(10, section=SECTION_MATH)
        b = self.model.draw(10, section=SECTION_MATH)
        self.assertEqual(a.counts, b.counts)

    def test_respects_skill_filter(self):
        skills = {"words_in_context", "transitions"}
        bp = self.model.draw(15, section=SECTION_RW, skill_ids=skills, seed=11)
        for (dom, sk, dif) in bp.by_cell():
            self.assertIn(sk, skills)

    def test_difficulty_profile_changes_mix(self):
        easy_agg = Counter()
        hard_agg = Counter()
        for s in range(12):
            easy_agg.update(self.model.draw(
                22, section=SECTION_MATH, profile="easy_leaning", seed=s).by_difficulty())
            hard_agg.update(self.model.draw(
                22, section=SECTION_MATH, profile="hard_leaning", seed=s).by_difficulty())
        e_share = easy_agg["easy"] / sum(easy_agg.values())
        h_share = hard_agg["hard"] / sum(hard_agg.values())
        self.assertGreater(e_share, 0.40)
        self.assertGreater(h_share, 0.45)

    def test_prior_fidelity_to_framework(self):
        weights = leaf_weights(section=SECTION_RW)
        agg = self._draw_many(300, section=SECTION_RW, seeds=range(30))
        grand = sum(agg.values())
        by_cell = {cell: n / grand for cell, n in agg.items()}
        worst = max(abs(by_cell.get(c, 0.0) - w) for c, w in weights.items())
        self.assertLess(worst, 0.02,
                        f"empirical proportions deviate from prior: {worst:.4f}")

    def test_posterior_shifts_toward_observed_skill(self):
        target = ("expression_ideas", "transitions", "medium")
        baseline_agg = self._draw_many(200, section=SECTION_RW, seeds=range(30))
        base_share = baseline_agg[target] / sum(baseline_agg.values())

        shifted_model = BlueprintModel(
            kappa=400.0, observations={c: 0 for c in []} | {target: 500})
        shifted_agg = Counter()
        for s in range(30):
            shifted_agg.update(
                shifted_model.draw(200, section=SECTION_RW, seed=s).by_cell())
        shifted_share = shifted_agg[target] / sum(shifted_agg.values())
        self.assertGreater(shifted_share, base_share + 0.03)

    def test_invalid_inputs_raise(self):
        with self.assertRaises(ValueError):
            BlueprintModel(kappa=0)
        with self.assertRaises(ValueError):
            BlueprintModel(kappa=-5)
        with self.assertRaises(ValueError):
            self.model.draw(5, section="nope", seed=1)
        with self.assertRaises(ValueError):
            self.model.draw(-1, seed=1)
        with self.assertRaises(ValueError):
            self.model.draw(5, profile="extreme", seed=1)
        with self.assertRaises(KeyError):
            self.model.draw(5, skill_ids={"not_a_skill"}, seed=1)
        with self.assertRaises(ValueError):
            self.model.draw(5, section=SECTION_MATH, skill_ids={"words_in_context"},
                            seed=1)


def derive_seed_test(name):
    from satprep.core.rng import derive_seed
    return derive_seed("test", name)


if __name__ == "__main__":
    unittest.main()
