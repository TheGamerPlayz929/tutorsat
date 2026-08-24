import unittest

from satprep.core.weakspots import compute_weak_spots


def row(domain, difficulty, correct):
    return {"domain_id": domain, "difficulty": difficulty,
            "correct": correct}


class TestWeakSpots(unittest.TestCase):
    def test_struggling_domain_sorted_first(self):
        rows = []
        for _ in range(6):
            rows.append(row("geometry_trig", "medium", False))
            rows.append(row("algebra", "easy", True))
        for _ in range(2):
            rows.append(row("geometry_trig", "medium", True))
            rows.append(row("algebra", "medium", True))
        out = compute_weak_spots(rows)
        self.assertEqual(out[0]["domain_id"], "geometry_trig")
        self.assertEqual(out[0]["status"], "struggling")
        self.assertEqual(out[0]["tier"], "medium")
        geo = out[0]
        self.assertEqual(geo["attempted"], 8)
        self.assertEqual(geo["correct"], 2)
        alg = next(w for w in out if w["domain_id"] == "algebra")
        self.assertEqual(alg["status"], "strong")

    def test_min_attempts_filters_noise(self):
        rows = [row("algebra", "hard", False)]
        self.assertEqual(compute_weak_spots(rows), [])
        rows.append(row("psda", "easy", True))
        self.assertEqual(compute_weak_spots(rows), [])

    def test_worst_tier_selected_for_label(self):
        rows = ([row("advanced_math", "easy", True)] * 5
                + [row("advanced_math", "hard", False)] * 4
                + [row("advanced_math", "hard", True)])
        out = compute_weak_spots(rows)
        self.assertEqual(out[0]["tier"], "hard")
        self.assertEqual(out[0]["tier_attempted"], 5)
        self.assertEqual(out[0]["tier_correct"], 1)

    def test_developing_band(self):
        rows = [row("craft_structure", "medium", i % 2 == 0)
                for i in range(10)]
        out = compute_weak_spots(rows)
        self.assertEqual(out[0]["status"], "developing")

    def test_section_and_labels_present(self):
        rows = ([row("std_conventions", "easy", False)] * 2
                + [row("std_conventions", "easy", True)] * 2
                + [row("expression_ideas", "easy", True)] * 3)
        out = compute_weak_spots(rows)
        conv = next(w for w in out
                    if w["domain_id"] == "std_conventions")
        self.assertEqual(conv["section"], "rw")
        self.assertEqual(conv["tier_label"], "Foundations")
        expr = next(w for w in out
                    if w["domain_id"] == "expression_ideas")
        self.assertEqual(expr["status"], "strong")


if __name__ == "__main__":
    unittest.main()
