import random
import unittest

from satprep.core.blueprint import BlueprintModel
from satprep.core.framework import (
    DIFFICULTIES,
    DOMAINS,
    SECTION_MATH,
    SECTION_RW,
)
from satprep.core.rng import rng_for
from satprep.questions.bank import GENERATORS, QuestionBank, supported_skills
from satprep.questions.base import Question


class TestGeneratorCoverage(unittest.TestCase):
    def test_every_framework_skill_has_a_generator(self):
        all_skills = {s.skill_id for d in DOMAINS for s in d.skills}
        self.assertEqual(all_skills, supported_skills())


class TestGeneratedQuestions(unittest.TestCase):
    def check_question(self, q: Question):
        self.assertIsInstance(q.prompt, str)
        self.assertGreater(len(q.prompt), 10)
        self.assertEqual(len(q.choices), 4, f"bad choices for {q.skill_id}: {q.choices}")
        self.assertEqual(len(set(q.choices)), 4, f"duplicate choices in {q.skill_id}")
        self.assertTrue(0 <= q.answer_index <= 3)
        self.assertIsInstance(q.explanation, str)
        self.assertGreater(len(q.explanation), 5)

    def test_all_generators_all_difficulties_many_seeds(self):
        bank = QuestionBank(master_seed=1234)
        seq = 0
        for skill_id in sorted(supported_skills()):
            domain = next(d for d in DOMAINS if any(s.skill_id == skill_id
                                                    for s in d.skills))
            for difficulty in DIFFICULTIES:
                for k in range(6):
                    with self.subTest(skill=skill_id, diff=difficulty, k=k):
                        cell = (domain.domain_id, skill_id, difficulty)
                        q = bank.make(cell, item_seq=seq)
                        seq += 1
                        self.check_question(q)

    def test_deterministic_given_same_seed(self):
        bank_a = QuestionBank(master_seed=777)
        bank_b = QuestionBank(master_seed=777)
        cell = ("algebra", "linear_equations_1v", "medium")
        qa = bank_a.make(cell, item_seq=5)
        qb = bank_b.make(cell, item_seq=5)
        self.assertEqual(qa.to_dict(), qb.to_dict())
        other = QuestionBank(master_seed=778).make(cell, item_seq=5)
        self.assertNotEqual(qa.prompt + qa.choices[0], other.prompt + other.choices[0])

    def test_difficulty_bands_map_to_b_values(self):
        from satprep.questions.base import B_RANGES
        bank = QuestionBank(master_seed=99)
        seq = 0
        seen = {}
        for difficulty in DIFFICULTIES:
            lo, hi = B_RANGES[difficulty]
            for _ in range(30):
                cell = ("algebra", "linear_functions", difficulty)
                q = bank.make(cell, item_seq=seq)
                seq += 1
                self.assertGreaterEqual(q.b, lo - 1e-9)
                self.assertLessEqual(q.b, hi + 1e-9)
                self.assertGreaterEqual(q.a, 0.5)
                seen[difficulty] = True
        self.assertEqual(set(seen), set(DIFFICULTIES))


class TestBankFillsBlueprints(unittest.TestCase):
    def test_fill_matches_blueprint_counts(self):
        model = BlueprintModel(kappa=50.0)
        bp = model.draw(27, section=SECTION_RW, seed="fill-test")
        bank = QuestionBank(master_seed="fill-test")
        questions = bank.fill_blueprint(bp)
        self.assertEqual(len(questions), bp.total)
        by_skill = {}
        for q in questions:
            by_skill[q.skill_id] = by_skill.get(q.skill_id, 0) + 1
        self.assertEqual(by_skill, bp.by_skill())

    def test_fill_math_blueprint(self):
        model = BlueprintModel(kappa=80.0)
        bp = model.draw(22, section=SECTION_MATH, seed="math-fill")
        bank = QuestionBank(master_seed="math-fill")
        questions = bank.fill_blueprint(bp)
        self.assertEqual(len(questions), 22)
        for q in questions:
            self.assertEqual(q.section, SECTION_MATH)


if __name__ == "__main__":
    unittest.main()
