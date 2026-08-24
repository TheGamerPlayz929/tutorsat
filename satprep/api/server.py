import json
import os
import re
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace
from urllib.parse import urlparse

from ..core.ability import LearnerModel
from ..core.blueprint import BlueprintModel
from ..core.framework import (
    DEFAULT_PROFILE,
    DIFFICULTY_PROFILES,
    DOMAINS,
    SECTIONS,
    get_skill,
)
from ..core.rng import derive_seed
from ..core.weakspots import compute_weak_spots
from ..engine.mocktest import MockTest
from ..engine.session import PracticeSession
from ..engine import stateless as xs
from ..questions.bank import QuestionBank
from ..questions.base import GenerationError
from ..scoring.scale import estimated_score
from ..storage.db import Store
from .google_auth import AuthError, stable_user_id, verify_google_credential

WEB_DIR = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "web"))

STATIC_FILES = {
    "/": "index.html",
    "/index.html": "index.html",
    "/app.js": "app.js",
    "/styles.css": "styles.css",
    "/config.js": "config.js",
    "/privacy.html": "privacy.html",
}

CONTENT_TYPES = {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
}


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.message = message


class AppState:
    def __init__(self, db_path="satprep.db", google_client_id=None,
                 allowed_origins=frozenset(), stateless_secret=None):
        self.store = Store(db_path)
        self.google_client_id = google_client_id
        self.allowed_origins = frozenset(allowed_origins)
        self.stateless_secret = stateless_secret
        self.lock = threading.RLock()
        self.sessions = {}
        self.mocks = {}
        self.learners = {}

    def close(self):
        self.store.close()


def resolve_route(method, path):
    for route_method, rx, fn in ROUTES:
        if route_method != method:
            continue
        match = rx.match(path)
        if match:
            return fn, match
    return None, None


def parse_json_body(raw: bytes) -> dict:
    if not raw:
        return {}
    try:
        parsed = json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        raise ApiError(400, "invalid JSON body")
    if not isinstance(parsed, dict):
        raise ApiError(400, "JSON object expected")
    return parsed


def handle_http_request(app: AppState, method: str, path: str,
                        body: bytes, origin: str = ""):
    """Shared entrypoint for every transport (http.server, WSGI, ...).

    Returns (status, extra_headers, payload_bytes) for /api/* requests.
    """
    if method == "OPTIONS":
        if origin in app.allowed_origins:
            return 204, [
                ("Access-Control-Allow-Origin", origin),
                ("Vary", "Origin"),
                ("Access-Control-Allow-Methods", "GET, POST, OPTIONS"),
                ("Access-Control-Allow-Headers", "Content-Type"),
                ("Access-Control-Max-Age", "600"),
            ], b""
        return 404, [], json.dumps(
            {"error": "origin not allowed"}).encode("utf-8")

    fn, match = resolve_route(method, path)
    if fn is None:
        raise ApiError(404, f"no route for {method} {path}")
    parsed_body = parse_json_body(body) if method == "POST" else {}
    try:
        status, obj = fn(app, match, parsed_body)
    except ApiError:
        raise
    except (KeyError, ValueError, RuntimeError) as e:
        raise ApiError(400, str(e))
    except BrokenPipeError:
        raise
    except Exception as e:
        raise ApiError(500, f"internal error: {e}")

    headers = [("Content-Type", "application/json; charset=utf-8")]
    if origin in app.allowed_origins:
        headers.append(("Access-Control-Allow-Origin", origin))
        headers.append(("Vary", "Origin"))
    payload = json.dumps(obj).encode("utf-8")
    headers.append(("Content-Length", str(len(payload))))
    return status, headers, payload


def _learner_for(state: AppState, user_id: str) -> LearnerModel:
    """Rebuild (or fetch cached) learner by replaying the stored response log."""
    with state.lock:
        lm = state.learners.get(user_id)
        if lm is None:
            lm = LearnerModel()
            for skill_id, a, b, correct in state.store.user_response_log(user_id):
                lm.respond(skill_id, a, b, correct)
            state.learners[user_id] = lm
        return lm


def sanitize(question_dict: dict) -> dict:
    return {k: v for k, v in question_dict.items()
            if k not in ("answer_index", "explanation")}


def _require_session(state: AppState, session_id: str) -> PracticeSession:
    session = state.sessions.get(session_id)
    if not isinstance(session, PracticeSession):
        raise ApiError(404, f"practice session '{session_id}' not found")
    return session


def _require_mock(state: AppState, mock_id: str) -> MockTest:
    mock = state.mocks.get(mock_id)
    if not isinstance(mock, MockTest):
        raise ApiError(404, f"mock '{mock_id}' not found")
    return mock


def framework_tree() -> dict:
    out = []
    for sec in SECTIONS.values():
        out.append({
            "section_id": sec.section_id,
            "name": sec.name,
            "questions_per_module": sec.questions_per_module,
            "modules_in_test": sec.modules_in_test,
            "minutes_per_module": sec.minutes_per_module,
            "domains": [
                {"domain_id": d.domain_id, "name": d.name,
                 "skills": [{"skill_id": s.skill_id, "name": s.name}
                            for s in d.skills]}
                for d in sec.domains],
        })
    return {"sections": out, "difficulty_profiles": DIFFICULTY_PROFILES,
            "default_profile": DEFAULT_PROFILE}


def section_scores(state: AppState, learner: LearnerModel) -> dict:
    out = {}
    for sec_id, sec in SECTIONS.items():
        skill_ids = {s.skill_id for d in sec.domains for s in d.skills}
        weighted = 0.0
        attempts = 0
        for sid in skill_ids:
            st = learner.state(sid)
            if st.attempts:
                weighted += st.theta * st.attempts
                attempts += st.attempts
        if attempts:
            low, high = estimated_score(weighted / attempts, n_items=attempts)
            out[sec_id] = {"low": low, "high": high}
    return out


ROUTES = []


def route(method, pattern):
    compiled = re.compile(pattern)

    def decorator(fn):
        ROUTES.append((method, compiled, fn))
        return fn

    return decorator


@route("GET", r"^/api/meta/framework$")
def get_framework(state, m, body):
    return 200, framework_tree()


@route("GET", r"^/api/health$")
def health(state, m, body):
    return 200, {"status": "ok"}


@route("GET", r"^/api/meta/config$")
def get_config(state, m, body):
    return 200, {"google_client_id": state.google_client_id}


@route("POST", r"^/api/auth/google$")
def auth_google(state, m, body):
    credential = str(body.get("credential") or "")
    if not credential:
        raise ApiError(400, "credential required")
    if not state.google_client_id:
        raise ApiError(400,
                       "Google sign-in is not configured on this server")
    try:
        profile = verify_google_credential(credential, state.google_client_id)
    except AuthError as e:
        raise ApiError(401, f"Google sign-in rejected: {e}")
    user_id = stable_user_id(profile["subject"])
    name = profile["name"] or (profile["email"].split("@")[0]
                               if profile["email"] else "Google User")
    user = state.store.create_user(user_id, name[:80])
    _learner_for(state, user_id)
    return 200, {"user": {**user, "provider": "google"}}


@route("POST", r"^/api/auth/link/probe$")
def auth_link_probe(state, m, body):
    local_user_id = str(body.get("local_user_id") or "")
    if not local_user_id.startswith("u-"):
        raise ApiError(400, "local_user_id must be an anonymous u-* account")
    if not state.store.get_user(local_user_id):
        return 200, {"user_exists": False, "sessions": 0, "responses": 0}
    summary = state.store.local_data_summary(local_user_id)
    return 200, {"user_exists": True, **summary}


@route("POST", r"^/api/auth/link$")
def auth_link(state, m, body):
    credential = str(body.get("credential") or "")
    local_user_id = str(body.get("local_user_id") or "")
    if not credential:
        raise ApiError(400, "credential required")
    if not state.google_client_id:
        raise ApiError(400, "Google sign-in is not configured on this server")
    try:
        profile = verify_google_credential(credential, state.google_client_id)
    except AuthError as e:
        raise ApiError(401, f"Google sign-in rejected: {e}")
    google_user_id = stable_user_id(profile["subject"])
    if local_user_id == google_user_id:
        return 200, {"user": {"user_id": google_user_id}, "moved_sessions": 0}
    if not local_user_id.startswith("u-"):
        raise ApiError(400, "only anonymous u-* accounts can be linked")
    if not state.store.get_user(local_user_id):
        raise ApiError(404, f"local account '{local_user_id}' not found")

    with state.lock:
        moved = state.store.move_sessions(local_user_id, google_user_id)
        name = profile["name"] or (profile["email"].split("@")[0]
                                   if profile["email"] else "Google User")
        user = state.store.create_user(google_user_id, name[:80])
        from ..core.ability import LearnerModel
        learner = LearnerModel()
        for skill_id, a, b, correct in state.store.user_response_log(google_user_id):
            learner.respond(skill_id, a, b, correct)
        state.store.save_theta(google_user_id, learner)
        state.learners[google_user_id] = learner
        state.learners.pop(local_user_id, None)
    return 200, {"user": {**user, "provider": "google"},
                 "moved_sessions": moved}


def _x_prepare(state, app):
    clean, tampered = xs.verify_and_prepare(state or xs.new_state(),
                                            app.stateless_secret)
    return clean, tampered


def _x_finish(app, blob, tampered, payload):
    out_state = (xs.sign_state(blob, app.stateless_secret)
                 if app.stateless_secret else blob)
    return {**payload, "state": out_state,
            "meta": {"tampered": bool(tampered)}}


def _sanitize(q_dict):
    return sanitize(q_dict)


@route("GET", r"^/api/x/capabilities$")
def x_capabilities(state, m, body):
    return 200, {"stateless": True,
                 "signed": bool(state.stateless_secret)}


@route("POST", r"^/api/x/practice/start$")
def x_practice_start(state, m, body):
    st, tampered = _x_prepare(body.get("state"), state)
    section = body.get("section")
    if section in (None, "", "mixed"):
        section = None
    skills = body.get("skills") or None
    length = max(1, min(54, int(body.get("length", 10))))
    profile = body.get("profile") or DEFAULT_PROFILE
    xs.validate_config(section=section, skills=skills)
    seed = str(body.get("seed") or uuid.uuid4().hex[:10])
    learner = xs.learner_from_state(st)
    entry = xs.new_practice_entry(
        st.get("user_id", "anon"), section, length, skills, profile, seed)
    st.setdefault("sessions", []).append(entry)
    session = xs.reconstruct_practice(entry, learner)
    question = session.next_question()
    xs.sync_practice_entry(entry, session)
    xs.refresh_theta_cache(st, learner)
    payload = {"session_id": entry["session_id"], "seed": entry["seed"],
               "total_questions": len(session.questions),
               "answered": 0,
               "finished": False,
               "question": _sanitize(question.to_dict()) if question else None}
    return 200, _x_finish(state, st, tampered, payload)


def _x_load_practice(st, learner, session_id):
    entry = xs.get_entry(st, session_id, "practice")
    session = xs.reconstruct_practice(entry, learner)
    return entry, session


@route("POST", r"^/api/x/session/next$")
def x_session_next(state, m, body):
    st, tampered = _x_prepare(body.get("state"), state)
    learner = xs.learner_from_state(st)
    entry, session = _x_load_practice(st, learner, str(body.get("session_id")))
    if not session.finished:
        question = session.next_question()
        xs.sync_practice_entry(entry, session)
    else:
        question = None
    payload = {
        "finished": question is None,
        "answered": len(entry.get("responses", [])),
        "total_questions": len(session.questions),
        "question": _sanitize(question.to_dict()) if question else None,
        "summary": session.summary() if question is None else None}
    return 200, _x_finish(state, st, tampered, payload)


@route("POST", r"^/api/x/session/answer$")
def x_session_answer(state, m, body):
    st, tampered = _x_prepare(body.get("state"), state)
    learner = xs.learner_from_state(st)
    entry, session = _x_load_practice(st, learner, str(body.get("session_id")))
    choice_index = int(body.get("choice_index"))
    try:
        rec = session.answer(choice_index)
    except RuntimeError as e:
        raise ApiError(409, str(e))
    xs.sync_practice_entry(entry, session)
    xs.refresh_theta_cache(st, learner)
    finished = session.finished
    summary = session.summary() if finished else None
    payload = {
        "correct": bool(rec.correct),
        "correct_choice": rec.question.correct_choice(),
        "explanation": rec.question.explanation,
        "skill_id": rec.question.skill_id,
        "theta_before": round(rec.theta_before, 4),
        "theta_after": round(rec.theta_after, 4),
        "answered": session.answered_count,
        "total_questions": len(session.questions),
        "finished": finished,
        "summary": summary}
    return 200, _x_finish(state, st, tampered, payload)


@route("POST", r"^/api/x/session/summary$")
def x_session_summary(state, m, body):
    st, tampered = _x_prepare(body.get("state"), state)
    learner = xs.learner_from_state(st)
    entry, session = _x_load_practice(st, learner, str(body.get("session_id")))
    return 200, _x_finish(state, st, tampered,
                          {"summary": session.summary()})


@route("POST", r"^/api/x/mocks/start$")
def x_mocks_start(state, m, body):
    st, tampered = _x_prepare(body.get("state"), state)
    sections = body.get("sections") or [SECTION_RW, SECTION_MATH]
    if not isinstance(sections, list) or not sections:
        raise ApiError(400, "sections must be a non-empty list")
    for sec in sections:
        if sec not in SECTIONS:
            raise ApiError(400, f"unknown section: {sec}")
    seed = str(body.get("seed") or uuid.uuid4().hex[:10])
    learner = xs.learner_from_state(st)
    entry = xs.new_mock_entry(st.get("user_id", "anon"),
                              list(dict.fromkeys(sections)), seed)
    st.setdefault("sessions", []).append(entry)
    mock = xs.reconstruct_mock(entry, learner)
    sections_out = {}
    for sec in mock.sections:
        mod = mock.modules[(sec, 1)]
        questions = []
        for q in mod.questions:
            qd = _sanitize(q.to_dict())
            qd["answered"] = False
            qd["module"] = 1
            questions.append(qd)
        sections_out[sec] = {
            "name": SECTIONS[sec].name,
            "minutes_per_module": SECTIONS[sec].minutes_per_module,
            "modules": [{"index": 1, "profile": mod.profile, "unlocked": True,
                         "questions": questions}]}
    xs.refresh_theta_cache(st, learner)
    payload = {"mock_id": entry["session_id"], "seed": entry["seed"],
               "sections": sections_out, "complete": False, "report": None}
    return 200, _x_finish(state, st, tampered, payload)


@route("POST", r"^/api/x/mocks/state$")
def x_mocks_state(state, m, body):
    st, tampered = _x_prepare(body.get("state"), state)
    learner = xs.learner_from_state(st)
    entry = xs.get_entry(st, str(body.get("mock_id")), "mock")
    mock = xs.reconstruct_mock(entry, learner)
    sections_out = {}
    for sec in mock.sections:
        mod_list = []
        for idx in (1, 2):
            key = (sec, idx)
            if key not in mock.modules:
                continue
            mod = mock.modules[key]
            questions = []
            for q in mod.questions:
                qd = _sanitize(q.to_dict())
                qd["answered"] = q.question_id in mod.answers
                qd["module"] = idx
                questions.append(qd)
            mod_list.append({"index": idx, "profile": mod.profile,
                             "unlocked": idx == 1
                             or mock.module1_complete(sec),
                             "questions": questions})
        sections_out[sec] = {
            "name": SECTIONS[sec].name,
            "minutes_per_module": SECTIONS[sec].minutes_per_module,
            "modules": mod_list}
    complete = mock.complete()
    payload = {"mock_id": entry["session_id"], "complete": complete,
               "sections": sections_out,
               "report": mock.report() if complete else None}
    return 200, _x_finish(state, st, tampered, payload)


@route("POST", r"^/api/x/mocks/answer$")
def x_mocks_answer(state, m, body):
    st, tampered = _x_prepare(body.get("state"), state)
    learner = xs.learner_from_state(st)
    entry = xs.get_entry(st, str(body.get("mock_id")), "mock")
    mock = xs.reconstruct_mock(entry, learner)
    question_id = str(body.get("question_id") or "")
    try:
        choice_index = int(body.get("choice_index"))
    except (TypeError, ValueError):
        raise ApiError(400, "choice_index must be an integer")
    question = mock.find_question(question_id)
    if question is None:
        raise ApiError(404, f"question '{question_id}' not in this mock")
    theta_before = mock.learner.state(question.skill_id).theta
    accepted = mock.answer(question_id, choice_index)
    if not accepted:
        raise ApiError(409, "question already answered")
    theta_after = mock.learner.state(question.skill_id).theta
    xs.sync_mock_entry(entry, mock)
    xs.refresh_theta_cache(st, learner)
    complete = mock.complete()
    payload = {
        "correct": bool(question.is_correct(choice_index)),
        "correct_choice": question.correct_choice(),
        "explanation": question.explanation,
        "skill_id": question.skill_id,
        "theta_before": round(theta_before, 4),
        "theta_after": round(theta_after, 4),
        "complete": complete,
        "report": mock.report() if complete else None}
    return 200, _x_finish(state, st, tampered, payload)


@route("DELETE", r"^/api/users/([A-Za-z0-9\-]+)$")
def delete_user_route(state, m, body):
    uid = m.group(1)
    if not state.store.get_user(uid):
        raise ApiError(404, f"user '{uid}' not found")
    removed = state.store.delete_user(uid)
    state.learners.pop(uid, None)
    return 200, {"deleted": True, "sessions_removed": removed}


@route("GET", r"^/api/export/([A-Za-z0-9\-]+)$")
def export_user(state, m, body):
    uid = m.group(1)
    if not state.store.get_user(uid):
        raise ApiError(404, f"user '{uid}' not found")
    bundle = state.store.export_user(uid)
    return 200, {"kind": "satprep-progress", "mode": "db",
                 "exported_at": time.time(), "payload": bundle}


@route("POST", r"^/api/import$")
def import_user(state, m, body):
    kind = body.get("kind")
    payload = body.get("payload")
    if kind != "satprep-progress" or not isinstance(payload, dict):
        raise ApiError(400, "unrecognized progress file")
    try:
        count = state.store.import_user(payload)
    except (KeyError, TypeError) as e:
        raise ApiError(400, f"malformed progress file: {e}")
    uid_rows = payload.get("user") or []
    if uid_rows:
        state.learners.pop(uid_rows[0]["user_id"], None)
    return 200, {"imported_records": count,
                 "user_id": uid_rows[0]["user_id"] if uid_rows else None}


@route("POST", r"^/api/x/dashboard$")
def x_dashboard(state, m, body):
    st, tampered = _x_prepare(body.get("state"), state)
    learner = xs.learner_from_state(st)
    xs.refresh_theta_cache(st, learner)
    skill_names = {}
    for d in DOMAINS:
        for s in d.skills:
            skill_names[s.skill_id] = s.name
    theta_rows = [{"skill_id": sid, "skill_name": skill_names.get(sid, sid),
                   "theta": vals.get("est", 0.0),
                   "posterior_sd": vals.get("sd", 0.0),
                   "attempts": vals.get("n", 0),
                   "correct": vals.get("correct", 0),
                   "history": vals.get("history", [])}
                  for sid, vals in st.get("theta", {}).items()]
    scores = {}
    for sec_id, sec in SECTIONS.items():
        skill_ids = {s.skill_id for d in sec.domains for s in d.skills}
        weighted = sum((st["theta"].get(sid, {}).get("est", 0.0))
                       * st["theta"].get(sid, {}).get("n", 0)
                       for sid in skill_ids)
        attempts = sum(st["theta"].get(sid, {}).get("n", 0)
                       for sid in skill_ids)
        if attempts:
            low, high = estimated_score(weighted / attempts, n_items=attempts)
            scores[sec_id] = {"low": low, "high": high}
    trend_rows = []
    for entry in sorted(st.get("sessions", []),
                        key=lambda s: s.get("started_at") or 0):
        for r in entry.get("responses", []):
            trend_rows.append(r)
    weak_spots = compute_weak_spots(trend_rows)
    buckets = []
    bucket_size = 5
    for i in range(0, len(trend_rows), bucket_size):
        chunk = trend_rows[i:i + bucket_size]
        buckets.append({"through": i + len(chunk),
                        "accuracy": round(sum(1 for r in chunk
                                              if r["correct"]) / len(chunk),
                                          4)})
    bank_by_seed = {}
    missed = []
    for entry in st.get("sessions", []):
        wrong = [r for r in entry.get("responses", []) if not r["correct"]]
        if not wrong:
            continue
        if entry["mode"] == "practice":
            bank = QuestionBank(master_seed=derive_seed(entry["seed"],
                                                        "practice"))
            bp = BlueprintModel().draw(
                int((entry.get("config") or {}).get("length", 10)),
                section=(entry.get("config") or {}).get("section"),
                skill_ids=set(entry["config"]["skills"])
                if entry["config"].get("skills") else None,
                profile=entry["config"].get("profile", DEFAULT_PROFILE),
                seed=entry["seed"])
            questions = bank.fill_blueprint(bp)
            by_id = {q.question_id: q for q in questions}
        else:
            continue
        for r in wrong:
            q = by_id.get(r["item_id"])
            if q is None:
                continue
            missed.append({"choice_index": r["choice_index"],
                           "question": q.to_dict()})
    missed = missed[:25]
    sessions_out = [{"session_id": e["session_id"], "kind": e["mode"],
                     "status": ("complete" if e.get("finished_at")
                                else "active"),
                     "started_at": e.get("started_at"),
                     "answered": len(e.get("responses", []))}
                    for e in st.get("sessions", [])][-20:]
    return 200, _x_finish(state, st, tampered, {
        "theta": theta_rows, "scores": scores, "trend": buckets,
        "missed": missed, "sessions": sessions_out,
        "weak_spots": compute_weak_spots(trend_rows)})


@route("POST", r"^/api/users$")
def create_user(state, m, body):
    name = str(body.get("name") or "Student").strip()[:80] or "Student"
    user_id = "u-" + uuid.uuid4().hex[:10]
    user = state.store.create_user(user_id, name)
    _learner_for(state, user_id)
    return 200, {"user": user}


@route("GET", r"^/api/users/([A-Za-z0-9\-]+)$")
def get_user(state, m, body):
    uid = m.group(1)
    user = state.store.get_user(uid)
    if not user:
        raise ApiError(404, f"user '{uid}' not found")
    return 200, {"user": user,
                 "theta": state.store.load_theta_snapshot(uid),
                 "scores": section_scores(state, _learner_for(state, uid))}


@route("POST", r"^/api/practice$")
def start_practice(state, m, body):
    user_id = body.get("user_id")
    if not user_id:
        raise ApiError(400, "user_id required")
    user_id = str(user_id)
    if not state.store.get_user(user_id):
        raise ApiError(404, f"user '{user_id}' not found")

    section = body.get("section")
    if section in (None, "", "mixed"):
        section = None
    elif section not in SECTIONS:
        raise ApiError(400, f"unknown section: {section}")

    skills = body.get("skills")
    if skills is not None:
        if not isinstance(skills, list) or not skills:
            skills = None
        else:
            for sid in skills:
                try:
                    get_skill(sid)
                except KeyError:
                    raise ApiError(400, f"unknown skill: {sid}")

    try:
        length = max(1, min(54, int(body.get("length", 10))))
    except (TypeError, ValueError):
        raise ApiError(400, "length must be an integer")

    seed = body.get("seed")
    seed = str(seed) if seed not in (None, "") else uuid.uuid4().hex[:10]

    learner = _learner_for(state, user_id)
    try:
        session = PracticeSession(user_id=user_id, section=section, length=length,
                                  skills=skills, seed=seed, learner=learner)
    except GenerationError as e:
        raise ApiError(500, f"question generation failed: {e}")
    except ValueError as e:
        raise ApiError(400, str(e))

    session_id = "p-" + uuid.uuid4().hex[:12]
    with state.lock:
        state.sessions[session_id] = session
    state.store.create_session(session_id, user_id, "practice",
                               section, length, seed)
    for q in session.questions:
        state.store.store_item(session_id, q.to_dict())

    first = session.next_question()
    return 200, {
        "session_id": session_id,
        "seed": seed,
        "total_questions": len(session.questions),
        "answered": 0,
        "finished": first is None,
        "question": sanitize(first.to_dict()) if first else None,
    }


@route("GET", r"^/api/sessions/([A-Za-z0-9\-]+)/next$")
def next_question(state, m, body):
    session = _require_session(state, m.group(1))
    with state.lock:
        question = session.next_question()
    if question is None:
        return 200, {"finished": True, "summary": session.summary()}
    return 200, {
        "finished": False,
        "answered": session.answered_count,
        "total_questions": len(session.questions),
        "question": sanitize(question.to_dict()),
    }


@route("POST", r"^/api/sessions/([A-Za-z0-9\-]+)/answer$")
def answer_question(state, m, body):
    session = _require_session(state, m.group(1))
    try:
        choice_index = int(body.get("choice_index"))
    except (TypeError, ValueError):
        raise ApiError(400, "choice_index must be an integer")
    with state.lock:
        try:
            rec = session.answer(choice_index)
        except RuntimeError as e:
            raise ApiError(409, str(e))
        state.store.add_response(m.group(1), rec)
        state.store.save_theta(session.user_id, session.learner)
    out = {
        "correct": bool(rec.correct),
        "correct_choice": rec.question.correct_choice(),
        "explanation": rec.question.explanation,
        "skill_id": rec.question.skill_id,
        "theta_before": round(rec.theta_before, 4),
        "theta_after": round(rec.theta_after, 4),
        "answered": session.answered_count,
        "total_questions": len(session.questions),
        "finished": session.finished,
        "summary": session.summary() if session.finished else None,
    }
    return 200, out


@route("GET", r"^/api/sessions/([A-Za-z0-9\-]+)/summary$")
def session_summary(state, m, body):
    session = _require_session(state, m.group(1))
    summary = session.summary()
    status = "complete" if session.finished else "active"
    if session.finished:
        state.store.finish_session(m.group(1), summary)
    return 200, {"status": status, "summary": summary}


@route("POST", r"^/api/sessions/([A-Za-z0-9\-]+)/finish$")
def finish_session(state, m, body):
    session_id = m.group(1)
    session = _require_session(state, session_id)
    summary = session.summary()
    state.store.finish_session(session_id, summary)
    return 200, {"status": "complete", "summary": summary}


def _mock_state_payload(mock_id, mock):
    sections_out = {}
    for sec in mock.sections:
        mod_list = []
        for idx in (1, 2):
            key = (sec, idx)
            if key not in mock.modules:
                continue
            mod = mock.modules[key]
            questions = []
            for q in mod.questions:
                qd = sanitize(q.to_dict())
                qd["answered"] = q.question_id in mod.answers
                qd["module"] = idx
                questions.append(qd)
            mod_list.append({
                "index": idx,
                "profile": mod.profile,
                "unlocked": idx == 1 or mock.module1_complete(sec),
                "questions": questions,
            })
        sections_out[sec] = {
            "name": SECTIONS[sec].name,
            "minutes_per_module": SECTIONS[sec].minutes_per_module,
            "modules": mod_list,
        }
    complete = mock.complete()
    return {
        "mock_id": mock_id,
        "user_id": mock.user_id,
        "complete": complete,
        "sections": sections_out,
        "report": mock.report() if complete else None,
    }


@route("POST", r"^/api/mocks$")
def create_mock(state, m, body):
    user_id = body.get("user_id")
    if not user_id:
        raise ApiError(400, "user_id required")
    user_id = str(user_id)
    if not state.store.get_user(user_id):
        raise ApiError(404, f"user '{user_id}' not found")

    raw_sections = body.get("sections") or list(SECTIONS.keys())
    if not isinstance(raw_sections, list) or not raw_sections:
        raise ApiError(400, "sections must be a non-empty list")
    for sec in raw_sections:
        if sec not in SECTIONS:
            raise ApiError(400, f"unknown section: {sec}")
    raw_sections = list(dict.fromkeys(raw_sections))

    seed = body.get("seed")
    seed = str(seed) if seed not in (None, "") else uuid.uuid4().hex[:10]

    learner = _learner_for(state, user_id)
    mock = MockTest(user_id=user_id, sections=tuple(raw_sections), seed=seed,
                    learner=learner)
    mock_id = "m-" + uuid.uuid4().hex[:12]
    with state.lock:
        state.mocks[mock_id] = mock

    total = sum(len(mock.module_questions(sec, 1)) for sec in mock.sections)
    state.store.create_session(mock_id, user_id, "mock", None, total, seed)
    for sec in mock.sections:
        for q in mock.module_questions(sec, 1):
            state.store.store_item(mock_id, q.to_dict())

    payload = _mock_state_payload(mock_id, mock)
    payload["seed"] = seed
    return 200, payload


@route("GET", r"^/api/mocks/([A-Za-z0-9\-]+)$")
def get_mock(state, m, body):
    mock = _require_mock(state, m.group(1))
    return 200, _mock_state_payload(m.group(1), mock)


@route("POST", r"^/api/mocks/([A-Za-z0-9\-]+)/answer$")
def answer_mock_question(state, m, body):
    mock = _require_mock(state, m.group(1))
    mock_id = m.group(1)
    question_id = str(body.get("question_id") or "")
    try:
        choice_index = int(body.get("choice_index"))
    except (TypeError, ValueError):
        raise ApiError(400, "choice_index must be an integer")

    question = mock.find_question(question_id)
    if question is None:
        raise ApiError(404, f"question '{question_id}' not in this mock")

    before_modules = set(mock.modules.keys())
    theta_before = mock.learner.state(question.skill_id).theta
    with state.lock:
        accepted = mock.answer(question_id, choice_index)
        if not accepted:
            raise ApiError(409, "question already answered")
        theta_after = mock.learner.state(question.skill_id).theta

        record = SimpleNamespace(
            question=question, choice_index=choice_index,
            correct=bool(question.is_correct(choice_index)),
            theta_before=theta_before, theta_after=theta_after)
        state.store.add_response(mock_id, record)
        state.store.save_theta(mock.user_id, mock.learner)

        new_modules = set(mock.modules.keys()) - before_modules
        for key in new_modules:
            for q in mock.modules[key].questions:
                state.store.store_item(mock_id, q.to_dict())

    out = {
        "correct": bool(question.is_correct(choice_index)),
        "correct_choice": question.correct_choice(),
        "explanation": question.explanation,
        "skill_id": question.skill_id,
        "theta_before": round(theta_before, 4),
        "theta_after": round(theta_after, 4),
    }
    payload = _mock_state_payload(mock_id, mock)
    out["complete"] = payload["complete"]
    out["report"] = payload["report"]
    return 200, out


@route("GET", r"^/api/mocks/([A-Za-z0-9\-]+)/report$")
def mock_report(state, m, body):
    mock = _require_mock(state, m.group(1))
    report = mock.report()
    if mock.complete():
        state.store.finish_session(m.group(1), report)
    return 200, report


@route("GET", r"^/api/dashboard/([A-Za-z0-9\-]+)$")
def dashboard(state, m, body):
    uid = m.group(1)
    user = state.store.get_user(uid)
    if not user:
        raise ApiError(404, f"user '{uid}' not found")
    learner = _learner_for(state, uid)
    scores = section_scores(state, learner)
    skill_names = {}
    for d in DOMAINS:
        for s in d.skills:
            skill_names[s.skill_id] = s.name
    theta_rows = []
    for row in state.store.load_theta_snapshot(uid):
        row["skill_name"] = skill_names.get(row["skill_id"], row["skill_id"])
        theta_rows.append(row)
    trend_rows = state.store.response_trend(uid)
    buckets = []
    bucket_size = 5
    for i in range(0, len(trend_rows), bucket_size):
        chunk = trend_rows[i:i + bucket_size]
        buckets.append({
            "through": i + len(chunk),
            "accuracy": round(sum(r["correct"] for r in chunk) / len(chunk), 4)})
    skill_to_domain = {}
    for d in DOMAINS:
        for s in d.skills:
            skill_to_domain[s.skill_id] = d.domain_id
    weak_rows = state.store.weak_rows(uid)
    for row in weak_rows:
        row["domain_id"] = skill_to_domain.get(row["skill_id"], "algebra")
    weak_spots = compute_weak_spots(weak_rows)
    return 200, {
        "user": user,
        "theta": theta_rows,
        "scores": scores,
        "sessions": state.store.recent_sessions(uid),
        "trend": buckets,
        "missed": state.store.missed_log(uid),
        "weak_spots": weak_spots,
    }


class Handler(BaseHTTPRequestHandler):
    app: AppState = None
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        pass

    def _send_json(self, status, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self) -> bytes:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return b""
        return self.rfile.read(length)

    def _serve_static(self, path):
        fname = STATIC_FILES.get(path)
        if fname is None:
            self._send_json(404, {"error": "not found"})
            return
        full_path = os.path.join(WEB_DIR, fname)
        if not os.path.isfile(full_path):
            self._send_json(404, {"error": "static file missing"})
            return
        ext = os.path.splitext(fname)[1]
        with open(full_path, "rb") as fh:
            data = fh.read()
        self.send_response(200)
        self.send_header("Content-Type",
                         CONTENT_TYPES.get(ext, "application/octet-stream"))
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _dispatch(self, method):
        path = urlparse(self.path).path
        if method == "GET" and not path.startswith("/api"):
            return self._serve_static(path)
        origin = self.headers.get("Origin") or ""
        try:
            status, headers, payload = handle_http_request(
                self.app, method, path, self._read_body(), origin)
            reason = {204: "No Content"}.get(status, "OK")
            self.send_response(status, reason)
            for name, value in headers:
                self.send_header(name, value)
            if not any(n.lower() == "content-length" for n, _ in headers):
                self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            if method != "OPTIONS":
                self.wfile.write(payload)
        except ApiError as e:
            self._send_json(e.status, {"error": e.message})

    def do_GET(self):
        self._dispatch("GET")

    def do_POST(self):
        self._dispatch("POST")

    def do_DELETE(self):
        self._dispatch("DELETE")

    def do_OPTIONS(self):
        self._dispatch("OPTIONS")


def serve(host="127.0.0.1", port=8765, db_path="satprep.db",
          google_client_id=None, allowed_origins="",
          stateless_secret=None):
    import signal

    origins = {o.strip() for o in (allowed_origins or "").split(",") if o.strip()}
    app = AppState(db_path=db_path, google_client_id=google_client_id,
                   allowed_origins=origins, stateless_secret=stateless_secret)
    Handler.app = app
    server = ThreadingHTTPServer((host, port), Handler)

    def _terminate(signum, frame):
        raise KeyboardInterrupt

    try:
        signal.signal(signal.SIGTERM, _terminate)
    except (ValueError, OSError):
        pass

    url = f"http://{host}:{port}"
    print(f"TutorSat running at {url}  (db: {db_path})")
    print("Independent project - not affiliated with or endorsed by College Board.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()
