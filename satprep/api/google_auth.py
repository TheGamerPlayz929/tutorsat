import base64
import hashlib
import json
import time
import urllib.request

JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"
VALID_ISSUERS = ("accounts.google.com", "https://accounts.google.com")
CLOCK_SKEW = 60
_CACHE_TTL = 3600
_SHA256_DIGEST_INFO = bytes.fromhex("3031300d060960864801650304020105000420")

_jwks_cache = {"keys": None, "fetched_at": 0.0}


class AuthError(ValueError):
    pass


def _b64url_decode(part: str) -> bytes:
    padding = "=" * (-len(part) % 4)
    return base64.urlsafe_b64decode(part + padding)


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _int_from_b64url(part: str) -> int:
    return int.from_bytes(_b64url_decode(part), "big")


def parse_credential(credential: str):
    parts = credential.split(".")
    if len(parts) != 3:
        raise AuthError("malformed credential")
    header_b64, payload_b64, signature_b64 = parts
    try:
        header = json.loads(_b64url_decode(header_b64))
        payload = json.loads(_b64url_decode(payload_b64))
        signature = _b64url_decode(signature_b64)
    except AuthError:
        raise
    except Exception as exc:
        raise AuthError("malformed credential") from exc
    signing_input = f"{header_b64}.{payload_b64}".encode("ascii")
    return header, payload, signature, signing_input


def set_jwks(keys):
    _jwks_cache["keys"] = keys
    _jwks_cache["fetched_at"] = time.time()


def _fetch_jwks():
    now = time.time()
    if _jwks_cache["keys"] and now - _jwks_cache["fetched_at"] < _CACHE_TTL:
        return _jwks_cache["keys"]
    with urllib.request.urlopen(JWKS_URL, timeout=10) as resp:
        document = json.loads(resp.read().decode("utf-8"))
    _jwks_cache["keys"] = document.get("keys", [])
    _jwks_cache["fetched_at"] = now
    return _jwks_cache["keys"]


def _emsa_pkcs1_v15_sha256(message: bytes, k: int) -> bytes:
    digest = hashlib.sha256(message).digest()
    trailer = _SHA256_DIGEST_INFO + digest
    pad_len = k - len(trailer) - 3
    if pad_len < 8:
        raise AuthError("key too small")
    return b"\x00\x01" + b"\xff" * pad_len + b"\x00" + trailer


def verify_rs256_signature(signature: bytes, message: bytes,
                           modulus: int, exponent: int) -> bool:
    k = (modulus.bit_length() + 7) // 8
    if len(signature) != k:
        return False
    recovered = pow(int.from_bytes(signature, "big"), exponent, modulus)
    em = recovered.to_bytes(k, "big")
    try:
        expected = _emsa_pkcs1_v15_sha256(message, k)
    except AuthError:
        return False
    return em == expected


def verify_google_credential(credential: str, client_id: str, jwks=None) -> dict:
    """Verify a Google ID token and return the normalized profile claims."""
    header, payload, signature, signing_input = parse_credential(credential)

    if header.get("alg") != "RS256":
        raise AuthError("unsupported algorithm")
    kid = header.get("kid")
    if not kid:
        raise AuthError("missing key id")

    keys = jwks if jwks is not None else _fetch_jwks()
    jwk = next((k for k in keys if k.get("kid") == kid), None)
    if jwk is None:
        raise AuthError("unknown signing key")
    modulus = _int_from_b64url(jwk["n"])
    exponent = _int_from_b64url(jwk.get("e", "AQAB"))

    if not verify_rs256_signature(signature, signing_input, modulus, exponent):
        raise AuthError("signature verification failed")

    now = time.time()
    if payload.get("iss") not in VALID_ISSUERS:
        raise AuthError("untrusted issuer")
    audience = payload.get("aud")
    audiences = audience if isinstance(audience, list) else [audience]
    if client_id not in audiences:
        raise AuthError("audience mismatch")
    if float(payload.get("exp", 0)) < now - CLOCK_SKEW:
        raise AuthError("token expired")
    subject = payload.get("sub")
    if not subject:
        raise AuthError("missing subject")

    return {
        "provider": "google",
        "subject": str(subject),
        "name": payload.get("name") or "",
        "email": payload.get("email") or "",
        "email_verified": bool(payload.get("email_verified")),
        "picture": payload.get("picture") or "",
    }


def stable_user_id(subject: str) -> str:
    digest = hashlib.sha256(f"google:{subject}".encode("utf-8")).hexdigest()
    return f"g-{digest[:16]}"
