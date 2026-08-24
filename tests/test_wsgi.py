import json
import unittest

from satprep.api.server import AppState
from wsgi import create_wsgi_application


class WsgiHarness:
    def __init__(self, app_state):
        self.application = create_wsgi_application(app_state)

    def __call__(self, method, path, body=None, origin=None):
        data = json.dumps(body).encode() if body is not None else b""
        environ = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(data)),
            "wsgi.input": _BytesIO(data),
        }
        if origin:
            environ["HTTP_ORIGIN"] = origin
        captured = {}

        def start_response(status, headers):
            captured["status"] = int(status.split(" ")[0])
            captured["headers"] = dict(headers)

        payload = b"".join(self.application(environ, start_response))
        return captured.get("status", 500), captured.get("headers", {}), payload


class _BytesIO:
    def __init__(self, data):
        self._data = data

    def read(self, n=-1):
        return self._data if n < 0 else self._data[:n]


class TestWsgiApplication(unittest.TestCase):
    def setUp(self):
        self.harness = WsgiHarness(AppState(db_path=":memory:"))

    def test_health(self):
        status, _, payload = self.harness("GET", "/api/health")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(payload), {"status": "ok"})

    def test_practice_round_trip_through_wsgi(self):
        status, _, payload = self.harness(
            "POST", "/api/users", {"name": "Wsgi User"})
        uid = json.loads(payload)["user"]["user_id"]

        status, _, payload = self.harness(
            "POST", "/api/practice",
            {"user_id": uid, "section": "math", "length": 3, "seed": "wsgi"})
        sid = json.loads(payload)["session_id"]
        q = json.loads(payload)["question"]

        status, _, payload = self.harness(
            "POST", f"/api/sessions/{sid}/answer", {"choice_index": 0})
        result = json.loads(payload)
        self.assertTrue(status == 200 and "correct" in result)

    def test_static_index_served(self):
        status, headers, payload = self.harness("GET", "/")
        html = payload.decode()
        self.assertEqual(status, 200)
        self.assertIn("<!DOCTYPE html>", html)
        self.assertIn("text/html", headers["Content-Type"])

    def test_unknown_api_route_404_json(self):
        status, headers, payload = self.harness("GET", "/api/nope")
        self.assertEqual(status, 404)
        self.assertIn("application/json", headers["Content-Type"])
        self.assertIn("error", json.loads(payload))

    def test_unknown_static_path_404_json(self):
        status, _, payload = self.harness("GET", "/missing.js")
        self.assertEqual(status, 404)

    def test_invalid_json_body_is_400(self):
        status, headers, payload = self._post_raw("/api/users", b"{broken")
        self.assertEqual(status, 400)
        self.assertIn("error", json.loads(payload))

    def _post_raw(self, path, raw):
        harness = WsgiHarness(AppState(db_path=":memory:"))
        environ = {
            "REQUEST_METHOD": "POST",
            "PATH_INFO": path,
            "CONTENT_LENGTH": str(len(raw)),
            "wsgi.input": _BytesIO(raw),
        }
        captured = {}

        def start_response(status, headers):
            captured["status"] = int(status.split(" ")[0])
            captured["headers"] = dict(headers)

        payload = b"".join(harness.application(environ, start_response))
        return captured.get("status", 500), captured.get("headers", {}), payload


class TestCors(unittest.TestCase):
    def setUp(self):
        self.harness = WsgiHarness(AppState(
            db_path=":memory:",
            allowed_origins={"https://satprep.web.app"}))

    def test_preflight_allowed_origin(self):
        status, headers, payload = self.harness(
            "OPTIONS", "/api/health", origin="https://satprep.web.app")
        self.assertEqual(status, 204)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"),
                         "https://satprep.web.app")
        self.assertIn("POST", headers.get("Access-Control-Allow-Methods", ""))

    def test_preflight_disallowed_origin_rejected(self):
        status, headers, _ = self.harness(
            "OPTIONS", "/api/health", origin="https://evil.example")
        self.assertEqual(status, 404)

    def test_actual_request_gets_acao_header(self):
        status, headers, _ = self.harness(
            "GET", "/api/health", origin="https://satprep.web.app")
        self.assertEqual(status, 200)
        self.assertEqual(headers.get("Access-Control-Allow-Origin"),
                         "https://satprep.web.app")

    def test_no_origin_no_cors_headers(self):
        status, headers, _ = self.harness("GET", "/api/health")
        self.assertNotIn("Access-Control-Allow-Origin", headers)


if __name__ == "__main__":
    unittest.main()
