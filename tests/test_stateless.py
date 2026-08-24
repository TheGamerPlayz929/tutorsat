import json
import unittest

import satprep.api.server as srv
from satprep.api.server import ApiError
from satprep.engine import stateless as xs
from satprep.engine.stateless import StateError, canonical_json, verify_and_prepare

SECRET = "test-secret"


def make_state_app(**kwargs):
    kwargs.setdefault("stateless_secret", SECRET)
    return srv.AppState(db_path=":memory:", **kwargs)


class Harness:
    def __init__(self, app):
        self.app = app

    def call(self, path, body=None):
        match = self.app and __import__("re").match(r"^.*$", path)
        fn, m = None, None
        from satprep.api.server import resolve_route
        fn, m = resolve_route("POST", path)
        if fn is None:
            raise AssertionError(f"no route {path}")
        status, payload = fn(self.app, m, body or {})
        return status, payload


class TestSigning(unittest.TestCase):
    def test_sign_and_verify_roundtrip(self):
        state = xs.new_state("u1")
        signed = xs.sign_state(state, SECRET)
        clean, tampered = verify_and_prepare(signed, SECRET)
        self.assertFalse(tampered)
        self.assertEqual(clean["user_id"], "u1")
        self.assertNotIn("sig", clean)

    def test_tamper_detected_not_fatal(self):
        state = xs.sign_state(xs.new_state("u1"), SECRET)
        state["user_id"] = "u-evil"
        clean, tampered = verify_and_prepare(state, SECRET)
        self.assertTrue(tampered)
        self.assertEqual(clean["user_id"], "u-evil")

    def test_unsigned_mode_never_flags(self):
        clean, tampered = verify_and_prepare({"v": 1}, None)
        self.assertFalse(tampered)

    def test_canonical_json_is_order_insensitive(self):
        a = canonical_json({"b": 1, "a": 2})
        b = canonical_json({"a": 2, "b": 1})
        self.assertEqual(a, b)


class TestCaps(unittest.TestCase):
    def _blob_with(self, n_sessions, resp_per=0):
        st = xs.new_state()
        for i in range(n_sessions):
            st["sessions"].append(xs.new_practice_entry(
                "u", "math", 3, None, "balanced", f"cap-{i}"))
            for k in range(resp_per):
                st["sessions"][-1]["responses"].append({
                    "item_id": f"q{i}-{k}", "skill": "probability",
                    "domain": "psda", "difficulty": "easy", "seq": k,
                    "a": 1.0, "b": 0.0, "correct": True, "choice_index": 0,
                    "ts": None})
        return st

    def test_session_cap_413(self):
        app = make_state_app()
        with self.assertRaises(StateError) as ctx:
            verify_and_prepare(self._blob_with(xs.MAX_SESSIONS + 1), SECRET)
        self.assertIn("too many sessions", str(ctx.exception))
        del app

    def test_response_cap_413(self):
        with self.assertRaises(StateError) as ctx:
            verify_and_prepare(
                self._blob_with(2, xs.MAX_RESPONSES), SECRET)
        self.assertIn("too many responses", str(ctx.exception))


class TestPracticeStatelessFlow(unittest.TestCase):
    def setUp(self):
        self.h = Harness(make_state_app())

    def test_start_next_answer_roundtrip(self):
        _, start = self.h.call("/api/x/practice/start",
                               {"section": "math", "length": 3,
                                "seed": "xflow"})
        sid = start["session_id"]
        st = start["state"]
        self.assertEqual(start["total_questions"], 3)
        self.assertIsNotNone(start["question"])
        self.assertNotIn("answer_index", start["question"])

        answered = 0
        result = None
        while True:
            if result is not None and result["finished"]:
                break
            _, nxt = self.h.call("/api/x/session/next",
                                 {"state": st, "session_id": sid})
            st = nxt["state"]
            if nxt["finished"]:
                break
            _, result = self.h.call("/api/x/session/answer",
                                    {"state": st, "session_id": sid,
                                     "choice_index": 0})
            st = result["state"]
            answered += 1
        self.assertEqual(answered, 3)
        self.assertTrue(result["finished"])
        self.assertEqual(result["summary"]["answered"], 3)
        theta_entries = [t for t in st["theta"].values() if t["n"] > 0]
        self.assertGreaterEqual(len(theta_entries), 1)

    def test_reconstruction_equivalence_after_answer(self):
        _, s1 = self.h.call("/api/x/practice/start",
                            {"section": "rw", "length": 4, "seed": "equiv"})
        sid = s1["session_id"]
        _, first = self.h.call("/api/x/session/answer",
                               {"state": s1["state"], "session_id": sid,
                                "choice_index": 0})
        learner_a = xs.learner_from_state(first["state"])
        learner_b = xs.learner_from_state(first["state"])
        entry = xs.get_entry(first["state"], sid, "practice")
        sess_a = xs.reconstruct_practice(entry, learner_a)
        sess_b = xs.reconstruct_practice(entry, learner_b)
        qa = sess_a.next_question().to_dict()
        qb = sess_b.next_question().to_dict()
        self.assertEqual(qa, qb)

    def test_resume_matches_original_flow(self):
        _, start = self.h.call("/api/x/practice/start",
                               {"section": "math", "length": 5,
                                "seed": "resume"})
        sid = start["session_id"]
        st = start["state"]

        def drive(state, upto):
            answered = []
            while len(answered) < upto:
                _, nxt = self.h.call("/api/x/session/next",
                                     {"state": state, "session_id": sid})
                state = nxt["state"]
                qid = nxt["question"]["question_id"]
                _, res = self.h.call("/api/x/session/answer",
                                     {"state": state, "session_id": sid,
                                      "choice_index": 2})
                state = res["state"]
                answered.append((qid, res["correct"]))
            return state, answered

        st_live, live_answers = drive(st, 3)
        st_resumed, resumed_rest = drive(st_live, 2)
        fresh_app = make_state_app()
        h2 = Harness(fresh_app)
        _, replay_start = h2.call("/api/x/practice/start",
                                  {"section": "math", "length": 5,
                                   "seed": "resume"})
        full_state, full_answers = drive(replay_start["state"], 5)
        self.assertEqual([q for q, _ in resumed_rest],
                         [q for q, _ in full_answers[3:]])
        theta_resumed = st_resumed["theta"]
        theta_full = full_state["theta"]
        for skill in theta_full:
            self.assertAlmostEqual(theta_resumed.get(skill, {}).get("est", 0),
                                   theta_full[skill]["est"], places=6)


class TestMockStatelessFlow(unittest.TestCase):
    def setUp(self):
        self.h = Harness(make_state_app())

    def test_mock_branches_through_blob(self):
        _, start = self.h.call("/api/x/mocks/start",
                               {"sections": ["math"], "seed": "mblob"})
        mid = start["mock_id"]
        st = start["state"]
        questions = start["sections"]["math"]["modules"][0]["questions"]
        for q in questions:
            _, res = self.h.call("/api/x/mocks/answer",
                                 {"state": st, "mock_id": mid,
                                  "question_id": q["question_id"],
                                  "choice_index": 0})
            st = res["state"]
        _, state_now = self.h.call("/api/x/mocks/state",
                                   {"state": st, "mock_id": mid})
        st = state_now["state"]
        mods = state_now["sections"]["math"]["modules"]
        self.assertEqual(len(mods), 2)
        self.assertEqual(mods[0]["index"], 1)
        self.assertEqual(mods[1]["index"], 2)
        for mod in mods:
            for q in mod["questions"]:
                if q["answered"]:
                    continue
                _, res = self.h.call("/api/x/mocks/answer",
                                     {"state": st, "mock_id": mid,
                                      "question_id": q["question_id"],
                                      "choice_index": 0})
                st = res["state"]
        final = self.h.call("/api/x/mocks/state", {"state": st,
                                                   "mock_id": mid})[1]
        self.assertTrue(final["complete"])
        report = final["report"]
        low, high = report["sections"]["math"]["score_estimate"]
        self.assertGreaterEqual(low, 200)
        self.assertLessEqual(high, 800)

    def test_double_answer_via_blob_conflicts(self):
        _, start = self.h.call("/api/x/mocks/start",
                               {"sections": ["math"], "seed": "dup"})
        mid = start["mock_id"]
        q = start["sections"]["math"]["modules"][0]["questions"][0]
        _, r1 = self.h.call("/api/x/mocks/answer",
                            {"state": start["state"], "mock_id": mid,
                             "question_id": q["question_id"],
                             "choice_index": 0})
        with self.assertRaises(ApiError) as ctx:
            self.h.call("/api/x/mocks/answer",
                        {"state": r1["state"], "mock_id": mid,
                         "question_id": q["question_id"],
                         "choice_index": 1})
        self.assertEqual(ctx.exception.status, 409)


class TestStatelessDashboard(unittest.TestCase):
    def test_dashboard_derives_everything_from_blob(self):
        h = Harness(make_state_app())
        _, start = h.call("/api/x/practice/start",
                          {"section": "rw", "length": 4, "seed": "dash"})
        sid = start["session_id"]
        st = start["state"]
        for _ in range(4):
            _, nxt = h.call("/api/x/session/next",
                            {"state": st, "session_id": sid})
            st = nxt["state"]
            if nxt["finished"]:
                break
            _, res = h.call("/api/x/session/answer",
                            {"state": st, "session_id": sid,
                             "choice_index": 1})
            st = res["state"]
        _, dash = h.call("/api/x/dashboard", {"state": st})
        self.assertIn("scores", dash)
        self.assertIn("theta", dash)
        self.assertIn("trend", dash)
        self.assertIn("sessions", dash)
        self.assertTrue(all("skill_name" in t for t in dash["theta"]))


class TestTamperSurfacing(unittest.TestCase):
    def test_tampered_blob_flows_through_with_flag(self):
        h = Harness(make_state_app())
        _, start = h.call("/api/x/practice/start",
                          {"section": "math", "length": 3, "seed": "tamper"})
        st = start["state"]
        st["user_id"] = "u-hacked"
        _, next_payload = h.call("/api/x/session/next",
                                 {"state": st, "session_id":
                                  start["session_id"]})
        self.assertTrue(next_payload["meta"]["tampered"])
        self.assertEqual(next_payload["meta"], {"tampered": True})
        self.assertIn("question", next_payload)


if __name__ == "__main__":
    unittest.main()
