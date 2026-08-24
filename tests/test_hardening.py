import math
import re
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor

from satprep.core.ability import AbilityEstimator, LearnerModel, most_informative
from satprep.core.blueprint import BlueprintModel
from satprep.core.framework import SECTION_MATH, SECTION_RW
from satprep.core.rng import derive_seed
from satprep.engine.mocktest import MockTest
from satprep.engine.session import PracticeSession
from satprep.questions.bank import QuestionBank
from satprep.storage.db import Store


class TestExtremeAbility(unittest.TestCase):
    def test_all_correct_long_streak_bounded_finite(self):
        est = AbilityEstimator()
        items = [(1.5, 2.0)] * 400
        res = est.fit(items, [1] * 400)
        self.assertTrue(math.isfinite(res.theta))
        self.assertTrue(math.isfinite(res.posterior_sd))
        self.assertGreater(res.theta, 3.0)
        self.assertLess(res.theta, 12.0)

    def test_all_wrong_long_streak_bounded_finite(self):
        est = AbilityEstimator()
        items = [(1.5, -2.0)] * 400
        res = est.fit(items, [0] * 400)
        self.assertTrue(math.isfinite(res.theta))
        self.assertLess(res.theta, -3.0)
        self.assertGreater(res.theta, -12.0)

    def test_item_selection_at_extreme_theta_does_not_crash(self):
        items = [(1.0 + 0.01 * i, -1.0 + (i % 20) * 0.2) for i in range(30)]
        for theta in (-10.0, 10.0):
            pick = most_informative(
                [__import__("satprep.core.ability", fromlist=["Item"]).Item(
                    f"i{i}", "s", a, b) for i, (a, b) in enumerate(items)], theta)
            self.assertIsNotNone(pick)

    def test_learner_nan_free_under_alternating_extremes(self):
        lm = LearnerModel()
        for i in range(200):
            lm.respond("sk", a=1.4, b=4.0 if i % 2 else -4.0,
                       correct=i % 2)
        st = lm.state("sk")
        self.assertTrue(math.isfinite(st.theta))
        self.assertTrue(math.isfinite(st.posterior_sd))


class TestSeedReproducibilityRegression(unittest.TestCase):
    def test_same_seed_reproduces_full_pipeline_identically(self):
        def run(seed):
            model = BlueprintModel(kappa=120.0)
            sess = PracticeSession(user_id="repro", section=SECTION_MATH,
                                   length=12, seed=seed, model=model,
                                   bank=QuestionBank(master_seed=derive_seed(seed, "bank")))
            return ([q.question_id for q in sess.questions],
                    [q.prompt for q in sess.questions],
                    [q.answer_index for q in sess.questions])

        a = run("regression-seed-1")
        b = run("regression-seed-1")
        c = run("regression-seed-2")
        self.assertEqual(a, b)
        self.assertNotEqual(a[0], c[0])

    def test_mock_branching_reproduces_given_same_seed_and_answers(self):
        def run():
            mock = MockTest(user_id="m", sections=(SECTION_MATH,), seed="branch-repro")
            for q in mock.module_questions(SECTION_MATH, 1):
                correct = q.answer_index
                mock.answer(q.question_id, correct if len(mock.modules[(SECTION_MATH, 1)].answers) % 2 == 0
                            else (correct + 1) % 4)
            report = mock.report()
            ids = [q.question_id for mod in mock.modules.values() for q in mod.questions]
            profiles = [m.profile for m in mock.modules.values()]
            return ids, profiles, report["sections"][SECTION_MATH]["score_estimate"]

        self.assertEqual(run(), run())


class TestConcurrency(unittest.TestCase):
    def test_store_survives_parallel_writes(self):
        store = Store(":memory:")
        store.create_user("cu", "C")

        def write_batch(worker):
            sid = f"s{worker}"
            store.create_session(sid, "cu", "practice", "math", 10, "seed")
            for i in range(25):
                from types import SimpleNamespace
                q = SimpleNamespace(question_id=f"q{worker}-{i}",
                                    skill_id="algebra", difficulty="easy",
                                    a=1.0, b=0.0)
                rec = SimpleNamespace(question=q, choice_index=0,
                                      correct=(i % 2 == 0),
                                      theta_before=0.0, theta_after=0.1)
                store.add_response(sid, rec)

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(write_batch, range(8)))

        log = store.user_response_log("cu")
        self.assertEqual(len(log), 8 * 25)
        sessions = store.recent_sessions("cu", limit=100)
        self.assertEqual(len(sessions), 8)
        store.close()

    def test_double_submit_race_admits_exactly_one(self):
        from types import SimpleNamespace as SN
        import satprep.api.server as srv

        state = srv.AppState(db_path=":memory:")
        try:
            state.store.create_user("ru", "Racer")
            _, payload = srv.create_mock(
                state, re.match(r"^/api/mocks$", "/api/mocks"),
                {"user_id": "ru", "sections": ["math"], "seed": "race"})
            mid = payload["mock_id"]
            q = payload["sections"]["math"]["modules"][0]["questions"][0]

            results = []
            lock = threading.Lock()

            def attempt(idx):
                try:
                    resp = srv.answer_mock_question(
                        state,
                        re.match(r"^/api/mocks/([A-Za-z0-9\-]+)/answer$",
                                 f"/api/mocks/{mid}/answer"),
                        {"question_id": q["question_id"], "choice_index": idx})
                    out = ("ok", resp[1]["correct"])
                except srv.ApiError as e:
                    out = ("rejected", e.status)
                except Exception as e:
                    out = ("error", str(e))
                with lock:
                    results.append(out)

            threads = [threading.Thread(target=attempt, args=(i % 4,))
                       for i in range(6)]
            for t in threads:
                t.start()
            for t in threads:
                t.join()

            statuses = [r[0] for r in results]
            self.assertEqual(statuses.count("ok"), 1, results)
            self.assertEqual(statuses.count("rejected"), 5, results)
            learner_attempts = sum(
                s.attempts for s in state.learners["ru"].states.values())
            self.assertEqual(learner_attempts, 1)
            rows = state.store.user_response_log("ru")
            self.assertEqual(len(rows), 1)
        finally:
            state.close()


class TestPersistenceEdgeCases(unittest.TestCase):
    def test_missed_log_returns_payloads_for_wrong_answers_only(self):
        from types import SimpleNamespace
        store = Store(":memory:")
        store.create_user("mu", "M")
        store.create_session("ms", "mu", "practice", "rw", 2, "sd")
        wrong_q = {"question_id": "qw", "skill_id": "transitions",
                   "domain_id": "expression_ideas", "difficulty": "easy",
                   "a": 1.1, "b": -0.9, "prompt": "P; ______, B.",
                   "choices": ["however", "moreover", "therefore", "likewise"],
                   "answer_index": 0, "explanation": "contrast"}
        right_q = dict(wrong_q, question_id="qr")
        store.store_item("ms", wrong_q)
        store.store_item("ms", right_q)
        for qid, choice, correct in (("qw", 1, False), ("qr", 0, True)):
            q = SimpleNamespace(question_id=qid, skill_id="transitions",
                                difficulty="easy", a=1.1, b=-0.9)
            store.add_response("ms", SimpleNamespace(
                question=q, choice_index=choice, correct=correct,
                theta_before=0.0, theta_after=0.0))
        missed = store.missed_log("mu")
        self.assertEqual(len(missed), 1)
        self.assertEqual(missed[0]["question"]["question_id"], "qw")
        self.assertEqual(missed[0]["choice_index"], 1)
        self.assertIn("explanation", missed[0]["question"])
        store.close()

    def test_domain_breakdown_sums_to_module_totals(self):
        mock = MockTest(user_id="db", sections=(SECTION_MATH,), seed="dom")
        m1 = mock.module_questions(SECTION_MATH, 1)
        for q in m1:
            mock.answer(q.question_id, q.answer_index)
        for q in mock.module_questions(SECTION_MATH, 2):
            mock.answer(q.question_id, (q.answer_index + 1) % 4)
        rep = mock.report()
        doms = rep["sections"][SECTION_MATH]["domains"]
        total = sum(d["total"] for d in doms)
        correct = sum(d["correct"] for d in doms)
        self.assertEqual(total, 44)
        expected = sum(m["correct"] for m in rep["sections"][SECTION_MATH]["modules"])
        self.assertEqual(correct, expected)


class TestBankDedupWithinSession(unittest.TestCase):
    def test_no_duplicate_prompts_when_pool_allows(self):
        model = BlueprintModel(kappa=60.0)
        bp = model.draw(10, section=SECTION_RW,
                        skill_ids={"words_in_context"}, seed="dedup")
        bank = QuestionBank(master_seed="dedup")
        questions = bank.fill_blueprint(bp)
        prompts = [q.prompt for q in questions]
        self.assertEqual(len(prompts), len(set(prompts)))

    def test_duplicate_fallback_is_deterministic(self):
        model = BlueprintModel(kappa=60.0)
        cells = [("craft_structure", "words_in_context", "easy")] * 14
        from satprep.core.blueprint import Blueprint
        bp = Blueprint(section=SECTION_RW, profile="balanced", total=14,
                       counts=tuple((c, 1) for c in cells),
                       seed="forced-dup", kappa=60.0)
        bank = QuestionBank(master_seed="forced-dup")
        qs_a = bank.fill_blueprint(bp)
        qs_b = QuestionBank(master_seed="forced-dup").fill_blueprint(bp)
        self.assertEqual([q.to_dict() for q in qs_a],
                         [q.to_dict() for q in qs_b])
        self.assertEqual(len(qs_a), 14)


if __name__ == "__main__":
    unittest.main()
