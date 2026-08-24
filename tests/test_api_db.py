import json
import threading
import unittest
import urllib.request

from satprep.api.server import AppState, Handler, serve
from satprep.storage.db import Store


def make_state(tmp_name=":memory:"):
    return AppState(db_path=tmp_name)


class TestStore(unittest.TestCase):
    def test_user_roundtrip(self):
        store = Store(":memory:")
        user = store.create_user("u1", "Alice")
        self.assertEqual(user["name"], "Alice")
        again = store.create_user("u1", "Alice")
        self.assertEqual(again["user_id"], "u1")
        self.assertIsNotNone(store.get_user("u1"))
        self.assertIsNone(store.get_user("nope"))
        store.close()

    def test_session_and_response_roundtrip(self):
        from types import SimpleNamespace
        store = Store(":memory:")
        store.create_user("u1", "A")
        store.create_session("s1", "u1", "practice", "math", 10, "seed-1")
        sess = store.get_session("s1")
        self.assertEqual(sess["status"], "active")

        q = SimpleNamespace(question_id="q1", skill_id="algebra", difficulty="easy",
                            a=1.2, b=-0.5)
        rec = SimpleNamespace(question=q, choice_index=2, correct=True,
                              theta_before=0.0, theta_after=0.3)
        store.add_response("s1", rec)
        log = store.user_response_log("u1")
        self.assertEqual(log, [("algebra", 1.2, -0.5, 1)])

        store.finish_session("s1", {"accuracy": 1.0})
        self.assertEqual(store.get_session("s1")["status"], "complete")
        trend = store.response_trend("u1")
        self.assertEqual(len(trend), 1)
        self.assertEqual(trend[0]["correct"], 1)
        store.close()

    def test_theta_snapshot(self):
        from types import SimpleNamespace
        store = Store(":memory:")
        store.create_user("u9", "T")
        st = SimpleNamespace(skill_id="probability", attempts=4, correct=3,
                             theta=0.42, posterior_sd=0.55,
                             history=[0.1, 0.2, 0.33, 0.42])

        class FakeLearner:
            states = {"probability": None}

            def state(self, skill_id):
                return st

        store.save_theta("u9", FakeLearner())
        snap = store.load_theta_snapshot("u9")
        self.assertEqual(len(snap), 1)
        self.assertAlmostEqual(snap[0]["theta"], 0.42)
        self.assertEqual(snap[0]["history"][-1], 0.42)
        store.close()

    def test_persistence_across_reopen(self):
        import os
        import tempfile
        path = os.path.join(tempfile.gettempdir(), "satprep_test_db.sqlite")
        if os.path.exists(path):
            os.remove(path)
        s1 = Store(path)
        s1.create_user("keep", "Persisted")
        s1.close()
        s2 = Store(path)
        self.assertIsNotNone(s2.get_user("keep"))
        s2.close()
        os.remove(path)


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import socket
        sock = socket.socket()
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        cls.port = port
        cls.app = AppState(db_path=":memory:")
        Handler.app = cls.app
        from http.server import ThreadingHTTPServer
        cls.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = f"http://127.0.0.1:{port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.app.close()

    def request(self, method, path, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base + path, data=data, method=method)
        if data:
            req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode())

    def _make_user(self):
        status, payload = self.request("POST", "/api/users", {"name": "Tester"})
        self.assertEqual(status, 200)
        return payload["user"]["user_id"]

    def test_framework_endpoint(self):
        status, payload = self.request("GET", "/api/meta/framework")
        self.assertEqual(status, 200)
        ids = {s["section_id"] for s in payload["sections"]}
        self.assertEqual(ids, {"rw", "math"})

    def test_health_endpoint(self):
        status, payload = self.request("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(payload, {"status": "ok"})

    def test_practice_flow_end_to_end(self):
        uid = self._make_user()
        status, start = self.request("POST", "/api/practice", {
            "user_id": uid, "section": "math", "length": 5, "seed": "e2e"})
        self.assertEqual(status, 200)
        sid = start["session_id"]
        self.assertEqual(start["total_questions"], 5)
        q = start["question"]
        self.assertNotIn("answer_index", q)
        self.assertNotIn("explanation", q)

        for i in range(5):
            status, nxt = self.request(
                "GET", f"/api/sessions/{sid}/next"
                ) if i else (status, None)
            if i:
                q = nxt["question"]
                self.assertFalse(nxt["finished"])
                self.assertNotIn("answer_index", q)
            status, result = self.request(
                "POST", f"/api/sessions/{sid}/answer", {"choice_index": 0})
            self.assertEqual(status, 200)
            self.assertIn("correct_choice", result)
            self.assertIn("explanation", result)
        self.assertTrue(result["finished"])
        self.assertIn("summary", result)

        status, summary = self.request("GET", f"/api/sessions/{sid}/summary")
        self.assertEqual(summary["status"], "complete")
        self.assertEqual(summary["summary"]["answered"], 5)

        dash = self.request("GET", f"/api/dashboard/{uid}")[1]
        self.assertGreaterEqual(len(dash["sessions"]), 1)
        self.assertIn("scores", dash)

    def test_double_answer_rejected(self):
        uid = self._make_user()
        _, start = self.request("POST", "/api/practice",
                                {"user_id": uid, "length": 3})
        sid = start["session_id"]
        status, _ = self.request("POST", f"/api/sessions/{sid}/answer",
                                 {"choice_index": 0})
        self.assertEqual(status, 200)
        status, _ = self.request("POST", f"/api/sessions/{sid}/answer",
                                 {"choice_index": 1})
        self.assertEqual(status, 409)

    def test_mock_flow_end_to_end_math_only(self):
        uid = self._make_user()
        status, mock = self.request("POST", "/api/mocks",
                                    {"user_id": uid, "sections": ["math"],
                                     "seed": "mock-e2e"})
        self.assertEqual(status, 200)
        mid = mock["mock_id"]
        modules = mock["sections"]["math"]["modules"]
        self.assertEqual(len(modules), 1)
        self.assertEqual(modules[0]["index"], 1)
        self.assertEqual(len(modules[0]["questions"]), 22)

        questions = modules[0]["questions"]
        for q in questions[:11]:
            self.request("POST", f"/api/mocks/{mid}/answer",
                         {"question_id": q["question_id"], "choice_index": 0})
        state = self.request("GET", f"/api/mocks/{mid}")[1]
        self.assertFalse(state["complete"])

        for q in questions[11:]:
            self.request("POST", f"/api/mocks/{mid}/answer",
                         {"question_id": q["question_id"], "choice_index": 0})
        state = self.request("GET", f"/api/mocks/{mid}")[1]
        mods = state["sections"]["math"]["modules"]
        self.assertEqual(len(mods), 2)
        self.assertEqual(mods[1]["index"], 2)
        self.assertIn(mods[1]["profile"],
                      ("easy_leaning", "balanced", "hard_leaning"))

        for mod in mods[1:]:
            for q in mod["questions"]:
                self.request("POST", f"/api/mocks/{mid}/answer",
                             {"question_id": q["question_id"], "choice_index": 0})
        final = self.request("GET", f"/api/mocks/{mid}")[1]
        self.assertTrue(final["complete"])
        self.assertIsNotNone(final["report"])
        est = final["report"]["sections"]["math"]["score_estimate"]
        low, high = est
        self.assertGreaterEqual(low, 200)
        self.assertLessEqual(high, 800)

    def test_unknown_routes_and_validation(self):
        status, _ = self.request("GET", "/api/does/not/exist")
        self.assertEqual(status, 404)
        status, err = self.request("POST", "/api/practice", {"length": 5})
        self.assertEqual(status, 400)
        uid = self._make_user()
        status, err = self.request("POST", "/api/practice",
                                   {"user_id": uid, "section": "bogus"})
        self.assertEqual(status, 400)
        status, err = self.request("GET", "/api/users/ghost")
        self.assertEqual(status, 404)

    def test_static_serving(self):
        with urllib.request.urlopen(self.base + "/", timeout=10) as resp:
            html = resp.read().decode()
        self.assertIn("<!DOCTYPE html>", html)


if __name__ == "__main__":
    unittest.main()
