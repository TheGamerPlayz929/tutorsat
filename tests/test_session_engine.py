import unittest

from satprep.core.ability import AbilityEstimator, LearnerModel
from satprep.core.blueprint import BlueprintModel
from satprep.core.framework import SECTION_MATH, SECTION_RW
from satprep.engine.mocktest import MockTest, branch_profile
from satprep.engine.session import PracticeSession


class TestPracticeSession(unittest.TestCase):
    def test_session_serves_all_questions(self):
        sess = PracticeSession(user_id="u1", section=SECTION_MATH, length=8,
                               seed="s1")
        served = []
        while True:
            q = sess.next_question()
            if q is None:
                break
            served.append(q)
            sess.answer(0)
        self.assertEqual(len(served), 8)
        self.assertTrue(sess.finished)
        self.assertEqual(len(set(q.question_id for q in served)), 8)

    def test_summary_counts_accuracy(self):
        sess = PracticeSession(user_id="u1", section=SECTION_MATH, length=6,
                               seed="s2")
        for i in range(6):
            q = sess.next_question()
            sess.answer(q.answer_index if i < 4 else (q.answer_index + 1) % 4)
        s = sess.summary()
        self.assertEqual(s["answered"], 6)
        self.assertEqual(s["correct"], 4)
        self.assertAlmostEqual(s["accuracy"], 4 / 6)

    def test_theta_updates_flow_through_session(self):
        learner = LearnerModel(AbilityEstimator())
        sess = PracticeSession(user_id="u2", section=SECTION_MATH, length=5,
                               seed="s3", learner=learner)
        first = sess.next_question()
        rec = sess.answer(first.answer_index)
        st = learner.state(first.skill_id)
        self.assertEqual(rec.theta_after, st.theta)
        skill_state = sess.summary()["per_skill"][first.skill_id]
        self.assertEqual(skill_state["attempts"], 1)

    def test_adaptive_ordering_prefers_informative_items(self):
        sess = PracticeSession(user_id="u3", section=SECTION_MATH, length=12,
                               seed="s4")
        q = sess.next_question()
        remaining_infos = []
        from satprep.core.ability import fisher_information
        theta = 0.0
        for idx in range(12):
            qq = sess.questions[idx]
            remaining_infos.append(fisher_information(qq.a, qq.b,
                                                      sess.theta_for_skill(qq.skill_id)))
        best = max(remaining_infos)
        chosen = fisher_information(q.a, q.b, sess.theta_for_skill(q.skill_id))
        self.assertAlmostEqual(chosen, best, places=10)

    def test_skill_filter_respected(self):
        sess = PracticeSession(user_id="u4", section=SECTION_MATH,
                               skills={"probability"}, length=5, seed="s5")
        while True:
            q = sess.next_question()
            if q is None:
                break
            self.assertEqual(q.skill_id, "probability")
            sess.answer(0)

    def test_reproducible_with_same_seed(self):
        a = PracticeSession(section=SECTION_RW, length=7, seed="dup")
        b = PracticeSession(section=SECTION_RW, length=7, seed="dup")
        qa = [a.questions[i].to_dict() for i in range(7)]
        qb = [b.questions[i].to_dict() for i in range(7)]
        self.assertEqual(qa, qb)


class TestBranching(unittest.TestCase):
    def test_branch_thresholds(self):
        self.assertEqual(branch_profile(0.10), "easy_leaning")
        self.assertEqual(branch_profile(0.49), "easy_leaning")
        self.assertEqual(branch_profile(0.50), "balanced")
        self.assertEqual(branch_profile(0.74), "balanced")
        self.assertEqual(branch_profile(0.75), "hard_leaning")
        self.assertEqual(branch_profile(0.95), "hard_leaning")


class TestMockTest(unittest.TestCase):
    def _answer_all(self, mock, section, index, correct_ratio):
        questions = mock.module_questions(section, index)
        n_correct = int(round(correct_ratio * len(questions)))
        for i, q in enumerate(questions):
            if i < n_correct:
                choice = q.answer_index
            else:
                choice = (q.answer_index + 1) % 4
            mock.answer(q.question_id, choice)

    def test_module_lengths_match_framework(self):
        mock = MockTest(user_id="m", seed="len")
        for sec in (SECTION_RW, SECTION_MATH):
            m1 = mock.module_questions(sec, 1)
            expected = {SECTION_RW: 27, SECTION_MATH: 22}[sec]
            self.assertEqual(len(m1), expected)

    def test_module2_built_after_module1_complete(self):
        mock = MockTest(user_id="m", seed="branch", sections=(SECTION_MATH,))
        with self.assertRaises(KeyError):
            mock.module_questions(SECTION_MATH, 2)
        self._answer_all(mock, SECTION_MATH, 1, correct_ratio=1.0)
        m2 = mock.module_questions(SECTION_MATH, 2)
        self.assertEqual(len(m2), 22)
        result = mock.module_result(SECTION_MATH, 2)
        self.assertEqual(result["profile"], "hard_leaning")

    def test_weak_performance_branches_easy(self):
        mock = MockTest(user_id="m", seed="weak", sections=(SECTION_MATH,))
        self._answer_all(mock, SECTION_MATH, 1, correct_ratio=0.2)
        result = mock.module_result(SECTION_MATH, 2)
        self.assertEqual(result["profile"], "easy_leaning")

    def test_mid_performance_branches_balanced(self):
        mock = MockTest(user_id="m", seed="mid", sections=(SECTION_MATH,))
        self._answer_all(mock, SECTION_MATH, 1, correct_ratio=0.6)
        result = mock.module_result(SECTION_MATH, 2)
        self.assertEqual(result["profile"], "balanced")

    def test_full_mock_completes_and_reports(self):
        mock = MockTest(user_id="m", seed="full",
                        sections=(SECTION_RW, SECTION_MATH))
        for sec in (SECTION_RW, SECTION_MATH):
            self._answer_all(mock, sec, 1, correct_ratio=0.7)
            self._answer_all(mock, sec, 2, correct_ratio=0.7)
        self.assertTrue(mock.complete())
        report = mock.report()
        self.assertTrue(report["complete"])
        est = report["sections"][SECTION_RW]["score_estimate"]
        self.assertIsNotNone(est)
        low, high = est
        self.assertGreaterEqual(low, 200)
        self.assertLessEqual(high, 800)
        self.assertLessEqual(high - low, 160)

    def test_double_answer_ignored(self):
        mock = MockTest(user_id="m", seed="dup-ans", sections=(SECTION_MATH,))
        q = mock.module_questions(SECTION_MATH, 1)[0]
        self.assertTrue(mock.answer(q.question_id, q.answer_index))
        self.assertFalse(mock.answer(q.question_id, (q.answer_index + 1) % 4))

    def test_unknown_question_raises(self):
        mock = MockTest(user_id="m", seed="unk", sections=(SECTION_MATH,))
        with self.assertRaises(KeyError):
            mock.answer("nope", 1)


class TestScoring(unittest.TestCase):
    def test_monotone_mapping(self):
        from satprep.scoring.scale import estimated_score
        scores = [estimated_score(t, n_items=30)[0] for t in (-2, -1, 0, 1, 2)]
        self.assertEqual(scores, sorted(scores))

    def test_band_within_bounds(self):
        from satprep.scoring.scale import estimated_score
        for t in (-3, -1, 0, 0.5, 3):
            low, high = estimated_score(t, n_items=5)
            self.assertGreaterEqual(low, 200)
            self.assertLessEqual(high, 800)
            self.assertLess(low, high)


if __name__ == "__main__":
    unittest.main()
