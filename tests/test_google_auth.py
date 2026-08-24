import base64
import hashlib
import json
import random
import time
import unittest

import satprep.api.google_auth as gauth
from satprep.api.google_auth import (
    AuthError,
    stable_user_id,
    verify_google_credential,
    verify_rs256_signature,
)


def is_probable_prime(n, rounds=16):
    if n < 2:
        return False
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    d = n - 1
    r = 0
    while d % 2 == 0:
        d //= 2
        r += 1
    for _ in range(rounds):
        a = random.randrange(2, n - 1)
        x = pow(a, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(r - 1):
            x = pow(x, 2, n)
            if x == n - 1:
                break
        else:
            return False
    return True


def gen_prime(bits):
    while True:
        candidate = random.getrandbits(bits) | (1 << bits - 1) | 1
        if is_probable_prime(candidate):
            return candidate


def generate_rsa_keypair():
    e = 65537
    while True:
        p = gen_prime(256)
        q = gen_prime(256)
        phi = (p - 1) * (q - 1)
        if p != q and phi % e != 0:
            n = p * q
            return {"n": n, "e": e, "d": pow(e, -1, phi)}


def b64url(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def sign_message(key, message: bytes) -> bytes:
    k = (key["n"].bit_length() + 7) // 8
    digest_info = bytes.fromhex("3031300d060960864801650304020105000420")
    digest = hashlib.sha256(message).digest()
    trailer = digest_info + digest
    pad_len = k - len(trailer) - 3
    em = b"\x00\x01" + b"\xff" * pad_len + b"\x00" + trailer
    sig_int = pow(int.from_bytes(em, "big"), key["d"], key["n"])
    return sig_int.to_bytes(k, "big")


def make_token(key, payload, kid="test-kid", alg="RS256"):
    header = {"alg": alg, "typ": "JWT", "kid": kid}
    head_b64 = b64url(json.dumps(header).encode())
    payload_b64 = b64url(json.dumps(payload).encode())
    signing_input = f"{head_b64}.{payload_b64}".encode()
    signature = sign_message(key, signing_input) if alg == "RS256" else b"\x00"
    return f"{head_b64}.{payload_b64}.{b64url(signature)}"


def jwk_for(key, kid="test-kid"):
    n_bytes = key["n"].to_bytes((key["n"].bit_length() + 7) // 8, "big")
    return {"kty": "RSA", "alg": "RS256", "use": "sig", "kid": kid,
            "n": b64url(n_bytes), "e": b64url(key["e"].to_bytes(3, "big"))}


def base_claims(**overrides):
    now = int(time.time())
    claims = {
        "iss": "https://accounts.google.com",
        "aud": "test-client-id",
        "sub": "1234567890",
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "email_verified": True,
        "iat": now,
        "exp": now + 3600,
    }
    claims.update(overrides)
    return claims


class TestRs256Primitive(unittest.TestCase):
    def test_roundtrip_signature(self):
        key = generate_rsa_keypair()
        message = b"header.payload"
        signature = sign_message(key, message)
        self.assertTrue(
            verify_rs256_signature(signature, message, key["n"], key["e"]))

    def test_tampered_message_rejected(self):
        key = generate_rsa_keypair()
        signature = sign_message(key, b"header.payload")
        self.assertFalse(
            verify_rs256_signature(signature, b"header.payloAd",
                                   key["n"], key["e"]))


class TestVerifyGoogleCredential(unittest.TestCase):
    def setUp(self):
        self.key = generate_rsa_keypair()
        gauth.set_jwks([jwk_for(self.key)])

    def tearDown(self):
        gauth.set_jwks(None)

    def test_valid_token_returns_profile(self):
        profile = verify_google_credential(make_token(self.key, base_claims()),
                                           "test-client-id")
        self.assertEqual(profile["provider"], "google")
        self.assertEqual(profile["subject"], "1234567890")
        self.assertEqual(profile["email"], "ada@example.com")

    def test_stable_user_id_deterministic_and_namespaced(self):
        self.assertEqual(stable_user_id("42"), stable_user_id("42"))
        self.assertNotEqual(stable_user_id("42"), stable_user_id("43"))
        self.assertTrue(stable_user_id("42").startswith("g-"))

    def test_bad_signature_rejected(self):
        token = make_token(self.key, base_claims())
        head, body, sig = token.split(".")
        raw_sig = base64.urlsafe_b64decode(sig + "==")
        forged = f"{head}.{body}." + b64url(
            bytes(byte ^ 0xFF for byte in raw_sig))
        with self.assertRaises(AuthError):
            verify_google_credential(forged, "test-client-id")

    def test_wrong_audience_rejected(self):
        with self.assertRaises(AuthError):
            verify_google_credential(
                make_token(self.key, base_claims(aud="other-client")),
                "test-client-id")

    def test_expired_token_rejected(self):
        with self.assertRaises(AuthError):
            verify_google_credential(
                make_token(self.key, base_claims(exp=int(time.time()) - 3600)),
                "test-client-id")

    def test_untrusted_issuer_rejected(self):
        with self.assertRaises(AuthError):
            verify_google_credential(
                make_token(self.key, base_claims(iss="https://evil.example")),
                "test-client-id")

    def test_unknown_kid_rejected(self):
        with self.assertRaises(AuthError):
            verify_google_credential(
                make_token(self.key, base_claims(), kid="rotated-key"),
                "test-client-id")

    def test_malformed_token_rejected(self):
        for bad in ("", "not-a-jwt", "a.b", "x.y.z"):
            with self.assertRaises(AuthError):
                verify_google_credential(bad, "test-client-id")

    def test_alg_none_rejected(self):
        with self.assertRaises(AuthError):
            verify_google_credential(
                make_token(self.key, base_claims(), alg="none"),
                "test-client-id")


class TestAuthEndpoint(unittest.TestCase):
    def setUp(self):
        import re
        import satprep.api.server as srv
        self.srv = srv
        self.state = srv.AppState(db_path=":memory:",
                                  google_client_id="cid-123")
        self.key = generate_rsa_keypair()
        gauth.set_jwks([jwk_for(self.key)])
        self.match = __import__("re").match(
            r"^/api/auth/google$", "/api/auth/google")

    def tearDown(self):
        gauth.set_jwks(None)
        self.state.close()

    def test_login_maps_subject_to_stable_local_account(self):
        status, payload = self.srv.auth_google(
            self.state, self.match,
            {"credential": make_token(
                self.key, base_claims(sub="777", aud="cid-123"))})
        self.assertEqual(status, 200)
        user_id = payload["user"]["user_id"]
        self.assertTrue(user_id.startswith("g-"))
        again_status, again = self.srv.auth_google(
            self.state, self.match,
            {"credential": make_token(
                self.key, base_claims(sub="777", aud="cid-123"))})
        self.assertEqual(again["user"]["user_id"], user_id)
        self.assertIsNotNone(self.state.store.get_user(user_id))

    def test_rejected_when_not_configured(self):
        state = self.srv.AppState(db_path=":memory:", google_client_id=None)
        try:
            from satprep.api.server import ApiError
            with self.assertRaises(ApiError) as ctx:
                self.srv.auth_google(
                    state, self.match,
                    {"credential": make_token(self.key, base_claims())})
            self.assertEqual(ctx.exception.status, 400)
        finally:
            state.close()

    def test_config_endpoint_exposes_client_id_only(self):
        status, config = self.srv.get_config(
            self.state,
            __import__("re").match(r"^/api/meta/config$", "/api/meta/config"),
            {})
        self.assertEqual(config, {"google_client_id": "cid-123"})


class TestAccountLinking(unittest.TestCase):
    def setUp(self):
        import re
        from types import SimpleNamespace
        import satprep.api.server as srv
        self.srv = srv
        self.state = srv.AppState(db_path=":memory:",
                                  google_client_id="cid-123")
        self.key = generate_rsa_keypair()
        gauth.set_jwks([jwk_for(self.key)])
        self.re = re

        self.local_uid = "u-local123"
        self.state.store.create_user(self.local_uid, "Local Student")
        self.state.store.create_session("ls1", self.local_uid, "practice",
                                        "math", 2, "seed")
        for i, correct in ((1, True), (2, False)):
            q = SimpleNamespace(question_id=f"lq{i}", skill_id="probability",
                                difficulty="easy", a=1.1, b=-0.5)
            self.state.store.add_response("ls1", SimpleNamespace(
                question=q, choice_index=0, correct=correct,
                theta_before=0.0, theta_after=0.2 if correct else -0.2))

    def tearDown(self):
        gauth.set_jwks(None)
        self.state.close()

    def _route(self, path):
        return self.re.match(r"^/api/auth/link.*$", path)

    def _cred(self, sub):
        return make_token(self.key, base_claims(sub=sub, aud="cid-123"))

    def test_probe_reports_local_data(self):
        status, payload = self.srv.auth_link_probe(
            self.state, self._route("/api/auth/link/probe"),
            {"local_user_id": self.local_uid})
        self.assertEqual(status, 200)
        self.assertTrue(payload["user_exists"])
        self.assertEqual(payload["sessions"], 1)
        self.assertEqual(payload["responses"], 2)

    def test_link_moves_sessions_and_refits_theta(self):
        status, result = self.srv.auth_link(
            self.state, self._route("/api/auth/link"),
            {"credential": self._cred("777"), "local_user_id": self.local_uid})
        self.assertEqual(status, 200)
        google_id = result["user"]["user_id"]
        self.assertTrue(google_id.startswith("g-"))
        self.assertEqual(result["moved_sessions"], 1)

        sessions = self.state.store.recent_sessions(google_id)
        self.assertEqual(len(sessions), 1)
        moved = self.state.store.get_session("ls1")
        self.assertEqual(moved["user_id"], google_id)

        learner = self.state.learners[google_id]
        prob = learner.state("probability")
        self.assertEqual(prob.attempts, 2)
        self.assertEqual(prob.correct, 1)

        rows = self.state.store.load_theta_snapshot(google_id)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["attempts"], 2)

    def test_second_link_is_noop(self):
        cred = self._cred("777")
        first = self.srv.auth_link(
            self.state, self._route("/api/auth/link"),
            {"credential": cred, "local_user_id": self.local_uid})
        second = self.srv.auth_link(
            self.state, self._route("/api/auth/link"),
            {"credential": cred, "local_user_id": self.local_uid})
        self.assertEqual(first[1]["moved_sessions"], 1)
        self.assertEqual(second[1]["moved_sessions"], 0)

    def test_cannot_claim_with_foreign_google_identity_direction(self):
        self.srv.auth_link(
            self.state, self._route("/api/auth/link"),
            {"credential": self._cred("777"), "local_user_id": self.local_uid})
        google_id = "g-" + stable_user_id("777")[2:]
        attacker_state = self.state
        with self.assertRaises(self.srv.ApiError) as ctx:
            attacker_state and self.srv.auth_link(
                attacker_state, self._route("/api/auth/link"),
                {"credential": self._cred("999"),
                 "local_user_id": google_id})
        self.assertEqual(ctx.exception.status, 400)

    def test_unknown_local_account_404(self):
        with self.assertRaises(self.srv.ApiError) as ctx:
            self.srv.auth_link(
                self.state, self._route("/api/auth/link"),
                {"credential": self._cred("777"), "local_user_id": "u-ghost"})
        self.assertEqual(ctx.exception.status, 404)


if __name__ == "__main__":
    unittest.main()
