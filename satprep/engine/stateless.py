import hashlib
import hmac
import json
import time

from ..core.ability import AbilityEstimator, LearnerModel, SkillState
from ..core.blueprint import BlueprintModel
from ..core.framework import (
    DEFAULT_PROFILE,
    SECTION_MATH,
    SECTION_RW,
    SECTIONS,
    get_skill,
)
from ..core.rng import derive_seed
from ..questions.bank import QuestionBank
from .mocktest import MockTest
from .session import AnswerRecord, PracticeSession

BLOB_VERSION = 1
MAX_SESSIONS = 300
MAX_RESPONSES = 5000


class StateError(ValueError):
    pass


def canonical_json(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False).encode("utf-8")


def sign_state(state: dict, secret: str) -> dict:
    body = {k: v for k, v in state.items() if k != "sig"}
    mac = hmac.new(secret.encode("utf-8"), canonical_json(body),
                   hashlib.sha256).hexdigest()
    return {**body, "sig": mac}


def verify_and_prepare(state: dict, secret) -> tuple:
    if not isinstance(state, dict):
        raise StateError("state must be an object")
    clean = {k: v for k, v in state.items() if k != "sig"}
    tampered = False
    if secret:
        expected = hmac.new(secret.encode("utf-8"), canonical_json(clean),
                            hashlib.sha256).hexdigest()
        provided = state.get("sig") or ""
        tampered = not hmac.compare_digest(expected, provided)
    if clean.get("v") != BLOB_VERSION:
        raise StateError(f"unsupported state version: {clean.get('v')}")
    sessions = clean.get("sessions", [])
    if not isinstance(sessions, list):
        raise StateError("sessions must be a list")
    total_responses = sum(len(s.get("responses", [])) for s in sessions)
    if len(sessions) > MAX_SESSIONS:
        raise StateError("too many sessions in state")
    if total_responses > MAX_RESPONSES:
        raise StateError("too many responses in state")
    clean["sessions"] = sessions
    return clean, tampered


def new_state(user_id="anon") -> dict:
    return {"v": BLOB_VERSION, "user_id": user_id, "sessions": [],
            "theta": {}}


def _fit_learner(responses_by_skill) -> LearnerModel:
    estimator = AbilityEstimator()
    learner = LearnerModel(estimator)
    for skill_id, log in responses_by_skill.items():
        ab = [(a, b) for a, b, _u in log]
        u = [u for _a, _b, u in log]
        if not ab:
            continue
        result = estimator.fit(ab, u)
        attempts = len(u)
        correct = sum(u)
        learner.states[skill_id] = SkillState(
            skill_id=skill_id, theta=result.theta,
            posterior_sd=result.posterior_sd, attempts=attempts,
            correct=correct, history=[])
        learner._responses[skill_id] = [(a, b, ui) for a, b, ui in log]
    return learner


def learner_from_state(state: dict) -> LearnerModel:
    by_skill = {}
    for entry in sorted(state.get("sessions", []),
                        key=lambda s: (s.get("started_at") or 0,
                                       s.get("session_id") or "")):
        for r in entry.get("responses", []):
            by_skill.setdefault(r["skill"], []).append(
                (float(r["a"]), float(r["b"]), int(bool(r["correct"]))))
    return _fit_learner(by_skill)


def refresh_theta_cache(state: dict, learner: LearnerModel) -> None:
    theta = {}
    for skill_id, st in learner.states.items():
        prev = (state.get("theta") or {}).get(skill_id) or {}
        history = prev.get("history") or []
        if history and len(history) >= st.attempts:
            history = history[-st.attempts:]
        elif st.attempts:
            history = history + [st.theta]
        theta[skill_id] = {"est": round(st.theta, 6),
                           "sd": round(st.posterior_sd, 6),
                           "n": st.attempts,
                           "correct": st.correct,
                           "history": history}
    state["theta"] = theta


def _practice_bank(entry):
    return QuestionBank(master_seed=derive_seed(entry["seed"], "practice"))


def reconstruct_practice(entry: dict, learner: LearnerModel) -> PracticeSession:
    cfg = entry.get("config") or {}
    session = PracticeSession(
        user_id=entry.get("user_id", "anon"),
        section=cfg.get("section"),
        length=int(cfg.get("length", 10)),
        skills=set(cfg["skills"]) if cfg.get("skills") else None,
        seed=entry["seed"],
        learner=learner,
        model=BlueprintModel(),
        bank=_practice_bank(entry),
        profile=cfg.get("profile", DEFAULT_PROFILE))
    by_id = {q.question_id: q for q in session.questions}
    records = []
    for idx, r in enumerate(entry.get("responses", [])):
        q = by_id.get(r["item_id"])
        if q is None:
            continue
        records.append(AnswerRecord(
            question=q, choice_index=int(r["choice_index"]),
            correct=bool(r["correct"]),
            theta_before=float(r.get("tb", 0.0)),
            theta_after=float(r.get("ta", 0.0))))
    session.records = records
    answered = {r["item_id"] for r in entry.get("responses", [])}
    session._remaining = [i for i, q in enumerate(session.questions)
                          if q.question_id not in answered]
    pending = entry.get("pending_item_id")
    if pending:
        for i, q in enumerate(session.questions):
            if q.question_id == pending and i in session._remaining:
                session._remaining.remove(i)
                session._pending_index = i
                break
    return session


def new_practice_entry(user_id, section, length, skills, profile, seed) -> dict:
    return {
        "session_id": f"s-{derive_seed(seed, 'sid'):016x}",
        "mode": "practice",
        "user_id": user_id,
        "seed": str(seed),
        "config": {"section": section, "length": int(length),
                   "skills": sorted(skills) if skills else None,
                   "profile": profile},
        "difficulty_profile": profile,
        "bp_seed": str(seed),
        "responses": [],
        "pending_item_id": None,
        "started_at": time.time(),
        "finished_at": None,
    }


def sync_practice_entry(entry: dict, session: PracticeSession) -> dict:
    entry["responses"] = [
        {"item_id": r.question.question_id, "skill": r.question.skill_id,
         "domain": r.question.domain_id, "difficulty": r.question.difficulty,
         "seq": idx, "a": r.question.a, "b": r.question.b,
         "correct": bool(r.correct), "choice_index": int(r.choice_index),
         "tb": round(r.theta_before, 6), "ta": round(r.theta_after, 6),
         "ts": None}
        for idx, r in enumerate(session.records)]
    entry["pending_item_id"] = (
        session.questions[session._pending_index].question_id
        if session._pending_index is not None else None)
    entry["finished_at"] = time.time() if session.finished else None
    return entry


def reconstruct_mock(entry: dict, learner: LearnerModel) -> MockTest:
    cfg = entry.get("config") or {}
    mock = MockTest(user_id=entry.get("user_id", "anon"),
                    sections=tuple(cfg.get("sections",
                                           [SECTION_RW, SECTION_MATH])),
                    seed=entry["seed"], learner=learner)
    by_key = {}
    for r in entry.get("responses", []):
        by_key.setdefault((r["section"], r["module"]), []).append(r)
    for sec in mock.sections:
        for idx in (1, 2):
            key = (sec, idx)
            if key not in mock.modules:
                if idx == 2 and not mock.module1_complete(sec):
                    continue
            for r in by_key.get(key, []):
                if r["item_id"] in mock.modules[key].answers:
                    continue
                if any(x.question_id == r["item_id"]
                       for x in mock.modules[key].questions):
                    mock.answer(r["item_id"], int(r["choice_index"]))
    return mock


def new_mock_entry(user_id, sections, seed) -> dict:
    return {
        "session_id": f"m-{derive_seed(seed, 'mid'):016x}",
        "mode": "mock",
        "user_id": user_id,
        "seed": str(seed),
        "config": {"sections": list(sections)},
        "difficulty_profile": DEFAULT_PROFILE,
        "bp_seed": str(seed),
        "responses": [],
        "started_at": time.time(),
        "finished_at": None,
    }


def sync_mock_entry(entry: dict, mock: MockTest) -> dict:
    records = []
    seq = 0
    for sec in mock.sections:
        for idx in (1, 2):
            key = (sec, idx)
            if key not in mock.modules:
                continue
            mod = mock.modules[key]
            for q in mod.questions:
                if q.question_id in mod.answers:
                    records.append({
                        "item_id": q.question_id, "skill": q.skill_id,
                        "domain": q.domain_id, "difficulty": q.difficulty,
                        "seq": seq, "a": q.a, "b": q.b,
                        "correct": bool(mod.answers[q.question_id]
                                        == q.answer_index),
                        "choice_index": int(mod.answers[q.question_id]),
                        "section": sec, "module": idx, "ts": None})
                    seq += 1
    entry["responses"] = records
    entry["finished_at"] = time.time() if mock.complete() else None
    return entry


def get_entry(state: dict, session_id: str, mode: str) -> dict:
    for entry in state.get("sessions", []):
        if entry.get("session_id") == session_id \
                and entry.get("mode") == mode:
            return entry
    raise StateError(f"{mode} session '{session_id}' not found in state")


def validate_config(section=None, skills=None, length=None):
    if section is not None and section not in SECTIONS:
        raise StateError(f"unknown section: {section}")
    if skills:
        for sid in skills:
            try:
                get_skill(sid)
            except KeyError:
                raise StateError(f"unknown skill: {sid}")
