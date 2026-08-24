import json
import os
from urllib.parse import urlparse

from satprep.api.server import (
    WEB_DIR,
    CONTENT_TYPES,
    STATIC_FILES,
    ApiError,
    AppState,
    handle_http_request,
)

REASONS = {
    200: "OK",
    204: "No Content",
    400: "Bad Request",
    401: "Unauthorized",
    404: "Not Found",
    409: "Conflict",
    500: "Internal Server Error",
}

_default_app = None


def get_app() -> AppState:
    global _default_app
    if _default_app is None:
        origins = {
            o.strip() for o in
            os.environ.get("SATPREP_ALLOWED_ORIGINS", "").split(",")
            if o.strip()
        }
        _default_app = AppState(
            db_path=os.environ.get("SATPREP_DB", "satprep.db"),
            google_client_id=os.environ.get("GOOGLE_CLIENT_ID"),
            allowed_origins=origins)
    return _default_app


def create_wsgi_application(app: AppState):
    def application(environ, start_response):
        method = environ.get("REQUEST_METHOD", "GET").upper()
        path = urlparse(environ.get("PATH_INFO", "/")).path
        origin = environ.get("HTTP_ORIGIN", "")

        if method == "GET" and not path.startswith("/api"):
            status, headers, payload = _serve_static(path, origin)
        else:
            length = int(environ.get("CONTENT_LENGTH") or 0)
            body = environ["wsgi.input"].read(length) if length else b""
            try:
                status, headers, payload = handle_http_request(
                    app, method, path, body, origin)
            except ApiError as exc:
                status = exc.status
                payload = json.dumps(
                    {"error": exc.message}).encode("utf-8")
                headers = [("Content-Type",
                            "application/json; charset=utf-8")]

        headers = list(headers)
        if not any(name.lower() == "content-length" for name, _ in headers):
            headers.append(("Content-Length", str(len(payload))))
        start_response(f"{status} {REASONS.get(status, 'OK')}", headers)
        return [payload] if method != "OPTIONS" else [b""]

    return application


def _serve_static(path: str, origin: str):
    fname = STATIC_FILES.get(path)
    target = os.path.join(WEB_DIR, fname) if fname else None
    if not fname or not os.path.isfile(target):
        return 404, [("Content-Type",
                      "application/json; charset=utf-8")], \
            b'{"error": "not found"}'
    ext = os.path.splitext(fname)[1]
    with open(target, "rb") as fh:
        data = fh.read()
    headers = [("Content-Type", CONTENT_TYPES.get(ext,
                                                  "application/octet-stream"))]
    if origin in get_app().allowed_origins:
        headers.append(("Access-Control-Allow-Origin", origin))
        headers.append(("Vary", "Origin"))
    return 200, headers, data


def app(environ, start_response):
    return create_wsgi_application(get_app())(environ, start_response)
