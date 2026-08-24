import math
import random
import unittest

from satprep.core.ability import (
    PRIOR_MEAN,
    PRIOR_SD,
    AbilityEstimator,
    Item,
    LearnerModel,
    fisher_information,
    logistic,
    log_logistic,
    most_informative,
)


def log_posterior(estimator, ab, u, theta):
    total = -((theta - estimator.mu) ** 2) / (2 * estimator.prior_sd ** 2)
    for (a, b), ui in zip(ab, u):
        p = logistic(a * (theta - b))
        total += ui * math.log(p) + (1 - ui) * math.log(1 - p)
    return total


class TestLogisticHelpers(unittest.TestCase):
    def test_logistic_known_values(self):
        self.assertAlmostEqual(logistic(0.0), 0.5)
        self.assertAlmostEqual(logistic(2.0), 1 / (1 + math.exp(-2)))
        self.assertAlmostEqual(logistic(-3.5), 1 / (1 + math.exp(3.5)))

    def test_log_logistic_consistency(self):
        for z in (-40, -5, -0.5, 0.0, 0.5, 5, 40):
            self.assertAlmostEqual(log_logistic(z), math.log(logistic(z)), places=10)

    def test_extreme_arguments_stay_finite(self):
        self.assertTrue(math.isfinite(logistic(800)))
        self.assertGreater(logistic(800), 0.999999)
        self.assertTrue(math.isfinite(logistic(-800)))
        self.assertTrue(math.isfinite(log_logistic(-800)))
        self.assertTrue(math.isfinite(log_logistic(800)))


class TestAbilityEstimator(unittest.TestCase):
    def setUp(self):
        self.est = AbilityEstimator()

    def test_no_responses_returns_prior(self):
        res = self.est.fit([], [])
        self.assertEqual(res.theta, PRIOR_MEAN)
        self.assertEqual(res.posterior_sd, PRIOR_SD)
        self.assertTrue(res.converged)
        self.assertEqual(res.n_items, 0)

    def test_correct_raises_wrong_lowers_theta(self):
        up = self.est.fit([(1.0, 0.0)], [1])
        down = self.est.fit([(1.0, 0.0)], [0])
        self.assertGreater(up.theta, PRIOR_MEAN)
        self.assertLess(down.theta, PRIOR_MEAN)

    def test_symmetry_of_single_response_around_prior_mean(self):
        up = self.est.fit([(1.0, 0.0)], [1]).theta
        down = self.est.fit([(1.0, 0.0)], [0]).theta
        self.assertAlmostEqual(up, -down, places=10)

    def test_harder_item_gives_stronger_evidence_when_correct(self):
        t_easy = self.est.fit([(1.0, -2.0)], [1]).theta
        t_mid = self.est.fit([(1.0, 0.0)], [1]).theta
        t_hard = self.est.fit([(1.0, 2.0)], [1]).theta
        self.assertGreater(t_hard, t_mid)
        self.assertGreater(t_mid, t_easy)

    def test_order_invariance_of_map(self):
        ab = [(1.2, -0.5), (0.8, 0.3), (1.5, 1.1), (1.0, -1.7), (1.1, 0.9)]
        u = [1, 0, 1, 1, 0]
        base = self.est.fit(ab, u).theta
        rng = random.Random(7)
        for _ in range(10):
            idx = list(range(len(u)))
            rng.shuffle(idx)
            perm_theta = self.est.fit([ab[i] for i in idx], [u[i] for i in idx]).theta
            self.assertAlmostEqual(base, perm_theta, places=10)

    def test_newton_matches_grid_search(self):
        ab = [(1.2, -0.5), (0.8, 0.3), (1.5, 1.1), (1.0, -1.7)]
        u = [1, 0, 1, 1]
        result = self.est.fit(ab, u)
        best_t, best_v = None, -math.inf
        steps = 16001
        for k in range(steps):
            t = -4.0 + 8.0 * k / (steps - 1)
            v = log_posterior(self.est, ab, u, t)
            if v > best_v:
                best_v, best_t = v, t
        self.assertLess(abs(result.theta - best_t), 2e-3)

    def test_posterior_shrinks_with_evidence(self):
        r0 = self.est.fit([], [])
        r3 = self.est.fit([(1.0, 0.0)] * 3, [1, 1, 0])
        r20 = self.est.fit([(1.0, 0.0)] * 20, [1] * 14 + [0] * 6)
        self.assertLess(r3.posterior_sd, r0.posterior_sd)
        self.assertLess(r20.posterior_sd, r3.posterior_sd)

    def test_laplace_sd_matches_closed_form(self):
        ab = [(1.0, 0.2), (1.4, -0.8), (0.9, 0.5)] * 7
        u = ([1, 0, 1] * 7)[: len(ab)]
        res = self.est.fit(ab, u)
        info = sum(fisher_information(a, b, res.theta) for a, b in ab)
        expected_sd = 1.0 / math.sqrt(info + 1.0 / PRIOR_SD ** 2)
        self.assertAlmostEqual(res.posterior_sd, expected_sd, places=10)

    def test_all_correct_is_high_but_bounded_by_prior(self):
        items = [(1.5, 2.5)] * 30
        res = self.est.fit(items, [1] * 30)
        self.assertGreater(res.theta, 2.0)
        self.assertLess(res.theta, 10.0)

    def test_recovery_simulation_known_true_ability(self):
        for truth in (0.8, -0.6):
            with self.subTest(truth=truth):
                rng = random.Random(f"recover-{truth}")
                items, u = [], []
                for _ in range(400):
                    a = rng.uniform(0.8, 1.5)
                    b = rng.gauss(truth, 1.0)
                    p = logistic(a * (truth - b))
                    u.append(1 if rng.random() < p else 0)
                    items.append((a, b))
                est = self.est.fit(items, u)
                self.assertLess(abs(est.theta - truth), 0.3)

    def test_convergence_and_iterations(self):
        ab = [(1.3, 0.4 * i - 1) for i in range(15)]
        u = [1 if i % 3 else 0 for i in range(15)]
        res = self.est.fit(ab, u)
        self.assertTrue(res.converged)
        self.assertLessEqual(res.iterations, 50)

    def test_validation_errors(self):
        with self.assertRaises(ValueError):
            self.est.fit([(1.0, 0.0)], [1, 0])
        with self.assertRaises(ValueError):
            self.est.fit([(0.0, 0.0)], [1])
        with self.assertRaises(ValueError):
            self.est.fit([(-1.0, 0.0)], [1])
        with self.assertRaises(ValueError):
            self.est.fit([(1.0, 0.0)], [2])
        with self.assertRaises(ValueError):
            AbilityEstimator(prior_sd=0)


class TestFisherInformation(unittest.TestCase):
    def test_closed_form_at_p_half(self):
        a, b = 1.5, 0.7
        self.assertAlmostEqual(fisher_information(a, b, b), a * a * 0.25, places=12)

    def test_peak_exactly_at_difficulty(self):
        a, b = 3.0, -0.4
        best_t, best_i = None, -1.0
        for k in range(4001):
            t = -3 + 6 * k / 4000
            i = fisher_information(a, b, t)
            if i > best_i:
                best_i, best_t = i, t
        self.assertLess(abs(best_t - b), 2e-3)

    def test_scales_with_squared_discrimination_at_center(self):
        self.assertAlmostEqual(
            fisher_information(2.0, 0.0, 0.0), 4 * fisher_information(1.0, 0.0, 0.0))

    def test_most_informative_selection(self):
        items = [Item("i1", "s", 1.0, -1.0),
                 Item("i2", "s", 1.0, 0.0),
                 Item("i3", "s", 1.0, 1.0)]
        self.assertEqual(most_informative(items, 0.2).item_id, "i2")
        tie = [Item("a", "s", 1.0, -1.0), Item("b", "s", 1.0, 1.0)]
        self.assertEqual(most_informative(tie, 0.0).item_id, "a")
        far = most_informative(items, 0.95)
        self.assertIn(far.item_id, {"i2", "i3"})


class TestLearnerModel(unittest.TestCase):
    def test_unknown_skill_returns_prior_state(self):
        lm = LearnerModel()
        st = lm.state("never_seen")
        self.assertEqual(st.theta, PRIOR_MEAN)
        self.assertEqual(st.posterior_sd, PRIOR_SD)
        self.assertEqual(st.attempts, 0)

    def test_respond_updates_state_and_counters(self):
        lm = LearnerModel()
        st = lm.respond("algebra", a=1.0, b=0.0, correct=1)
        self.assertEqual(st.attempts, 1)
        self.assertEqual(st.correct, 1)
        st = lm.respond("algebra", a=1.0, b=0.0, correct=1)
        self.assertEqual(st.attempts, 2)
        self.assertEqual(st.correct, 2)
        self.assertEqual(len(st.history), 2)
        self.assertEqual(st.history[-1], st.theta)
        self.assertFalse(lm.has_activity("geometry"))
        self.assertTrue(lm.has_activity("algebra"))

    def test_skills_are_independent(self):
        lm = LearnerModel()
        lm.respond("algebra", a=1.0, b=0.0, correct=1)
        solo = LearnerModel()
        solo_st = solo.respond("geometry", a=1.0, b=-0.5, correct=0)
        shared = lm.respond("geometry", a=1.0, b=-0.5, correct=0)
        self.assertAlmostEqual(shared.theta, solo_st.theta, places=12)
        alg = lm.state("algebra")
        self.assertEqual(alg.attempts, 1)
        self.assertEqual(alg.correct, 1)

    def test_matches_direct_estimator_fit(self):
        lm = LearnerModel()
        seq = [(1.2, -0.3, 1), (0.9, 0.5, 0), (1.4, 1.0, 1)]
        for a, b, c in seq:
            lm.respond("sk", a=a, b=b, correct=c)
        direct = AbilityEstimator().fit([(a, b) for a, b, _ in seq],
                                        [c for _, _, c in seq])
        self.assertAlmostEqual(lm.state("sk").theta, direct.theta, places=12)
        self.assertAlmostEqual(lm.state("sk").posterior_sd, direct.posterior_sd,
                               places=12)

    def test_invalid_response_rejected(self):
        lm = LearnerModel()
        with self.assertRaises(ValueError):
            lm.respond("sk", a=1.0, b=0.0, correct=7)


if __name__ == "__main__":
    unittest.main()
