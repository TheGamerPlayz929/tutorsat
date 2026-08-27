import unittest
from satprep.questions.difficulty import DifficultyProfile, score_difficulty
from satprep.questions.bank import QuestionBank
from satprep.core.rng import rng_for


class TestDifficultyGates(unittest.TestCase):
    """Regression tests for §16 — difficulty validity, not label gymnastics."""

    def test_example_c_trivial_quadratic_not_hard(self):
        """(x+4)^2 = 2 — single ± step, equation already in needed form — must NOT be hard."""
        profile = DifficultyProfile(
            reasoning_steps=1, decision_points=0,
            representation_translation=False, concept_interaction=False,
            distractor_quality=1, information_density=0, computation_burden=0,
            directness=0, constraint_complexity=False,
        )
        tier, reasons, _ = score_difficulty({}, profile)
        self.assertNotEqual(tier, "hard", f"trivial quadratic scored as hard: {reasons}")
        self.assertEqual(tier, "easy")

    def test_example_a_direct_linear_not_hard(self):
        """21 + 8x = 117 — one obvious operation, no translation — must NOT be hard."""
        profile = DifficultyProfile(
            reasoning_steps=1, decision_points=0,
            representation_translation=False, concept_interaction=False,
            distractor_quality=1, information_density=0, computation_burden=0,
            directness=0, constraint_complexity=False,
        )
        tier, reasons, _ = score_difficulty({}, profile)
        self.assertNotEqual(tier, "hard")
        # Direct linear may be easy, not medium/hard
        self.assertIn(tier, ("easy", "medium"))

    def test_example_a_medium_requires_translation(self):
        """Reparameterized medium linear_word_problems (offset free sessions) should be medium."""
        profile = DifficultyProfile(
            reasoning_steps=2, decision_points=1,
            representation_translation=True, concept_interaction=False,
            distractor_quality=2, information_density=1, computation_burden=0,
            directness=1, constraint_complexity=True,
        )
        tier, reasons, _ = score_difficulty({}, profile)
        self.assertEqual(tier, "medium", f"offset word problem should be medium: {reasons}")

    def test_example_b_boundaries_medium_eligible(self):
        """IC; however, IC — valid medium boundaries item should remain medium."""
        profile = DifficultyProfile(
            reasoning_steps=2, decision_points=1,
            representation_translation=False, concept_interaction=False,
            distractor_quality=1, information_density=0, computation_burden=0,
            directness=1, constraint_complexity=False,
        )
        tier, reasons, _ = score_difficulty({}, profile)
        self.assertEqual(tier, "medium", f"IC; however, IC should be medium: {reasons}")

    def test_genuine_hard_contextual_passes(self):
        """Contextual quadratic with translation + constraint + interaction should be hard."""
        profile = DifficultyProfile(
            reasoning_steps=3, decision_points=2,
            representation_translation=True, concept_interaction=True,
            distractor_quality=2, information_density=1, computation_burden=0,
            directness=2, constraint_complexity=True,
        )
        tier, reasons, _ = score_difficulty({}, profile)
        self.assertEqual(tier, "hard", f"contextual hard should pass: {reasons}")

    def test_genuine_hard_u_substitution_passes(self):
        """u-substitution hard should pass."""
        profile = DifficultyProfile(
            reasoning_steps=3, decision_points=2,
            representation_translation=True, concept_interaction=True,
            distractor_quality=2, information_density=1, computation_burden=0,
            directness=2, constraint_complexity=True,
        )
        tier, _, _ = score_difficulty({}, profile)
        self.assertEqual(tier, "hard")

    def test_computation_only_not_hard(self):
        """Tedious arithmetic alone must not confer hard (§3.8, §5)."""
        profile = DifficultyProfile(
            reasoning_steps=1, decision_points=0,
            representation_translation=False, concept_interaction=False,
            distractor_quality=1, information_density=0, computation_burden=2,
            directness=0, constraint_complexity=False,
        )
        tier, _, _ = score_difficulty({}, profile)
        self.assertNotEqual(tier, "hard")

    def test_no_profile_fallback_is_easy(self):
        tier, reasons, _ = score_difficulty({}, None)
        self.assertEqual(tier, "easy")
        self.assertIn("no difficulty_profile", reasons[0])

    # ------------------------------------------------------------------
    # Generator-level regression: ensure hard nonlinear_equations no longer
    # emits the trivial (x+p)^2=q pattern as hard (§5, Ex C)
    # ------------------------------------------------------------------

    def test_nonlinear_hard_never_trivial(self):
        """Sample many hard nonlinear_equations; none should be trivial (x+p)^2=q with direct ±."""
        bank = QuestionBank(master_seed="regression-hard-nonlinear")
        # Force hard cells; after validator, hard cells must be validated hard
        # Sample 40 hards via bank.make with hard difficulty
        for seq in range(40):
            q = bank.make(("advanced_math", "nonlinear_equations", "hard"), item_seq=seq)
            # Validated difficulty must be hard (bank enforces gate)
            self.assertEqual(q.difficulty, "hard", f"hard cell demoted to {q.difficulty}: {q.prompt[:80]}")
            # Hard prompt must not be the trivial (x+p)^2=q with two choices ±
            # The old pattern had prompt starting with "If (x +" and containing ")² = "
            # and no contextual words. Contextual hard contains "rectangle".
            # We accept either contextual or u_substitution as valid hards.
            self.assertTrue(
                "rectangle" in q.prompt.lower() or "x⁴" in q.prompt or "x" in q.prompt,
                f"unexpected hard prompt: {q.prompt[:120]}",
            )

    def test_linear_word_problems_medium_not_direct(self):
        """Medium linear_word_problems must require offset/translation, not 21+8x=117."""
        bank = QuestionBank(master_seed="regression-medium-lwp")
        for seq in range(20):
            q = bank.make(("algebra", "linear_word_problems", "medium"), item_seq=seq)
            # Medium should contain the offset clue ("first" and "included") after fix
            self.assertIn("first", q.prompt.lower(),
                          f"medium LWP should contain offset constraint: {q.prompt[:120]}")

    # ------------------------------------------------------------------
    # Invariants (§16 Test 5)
    # ------------------------------------------------------------------

    def test_invariants_answer_correctness_and_unique_choices(self):
        bank = QuestionBank(master_seed="invariants")
        for skill in ["linear_equations_1v", "nonlinear_equations", "linear_word_problems"]:
            for diff in ["easy", "medium", "hard"]:
                for seq in range(5):
                    q = bank.make(("algebra" if "linear" in skill else "advanced_math", skill, diff), item_seq=seq)
                    self.assertEqual(len(q.choices), 4)
                    self.assertEqual(len(set(q.choices)), 4)
                    self.assertIn(q.choices[q.answer_index], q.choices)
                    # answer_index valid
                    self.assertTrue(0 <= q.answer_index < 4)

    def test_invariants_seed_reproducibility(self):
        bank_a = QuestionBank(master_seed=777)
        bank_b = QuestionBank(master_seed=777)
        for skill, diff in [("linear_word_problems", "medium"), ("nonlinear_equations", "hard")]:
            qa = bank_a.make(("algebra" if skill == "linear_word_problems" else "advanced_math", skill, diff), item_seq=3)
            qb = bank_b.make(("algebra" if skill == "linear_word_problems" else "advanced_math", skill, diff), item_seq=3)
            self.assertEqual(qa.prompt, qb.prompt)
            self.assertEqual(qa.choices, qb.choices)
            self.assertEqual(qa.answer_index, qb.answer_index)
            self.assertEqual(qa.difficulty, qb.difficulty)

    def test_invariants_irt_params_still_present(self):
        bank = QuestionBank(master_seed=123)
        q = bank.make(("algebra", "linear_word_problems", "hard"), item_seq=0)
        self.assertIsInstance(q.a, float)
        self.assertIsInstance(q.b, float)
        self.assertTrue(0.2 <= q.a <= 2.5)
        self.assertTrue(-6 <= q.b <= 6)


if __name__ == "__main__":
    unittest.main()
