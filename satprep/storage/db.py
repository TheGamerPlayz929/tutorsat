import json
import sqlite3
import threading
import time
from typing import List, Dict

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    section TEXT,
    length INTEGER,
    seed TEXT,
    status TEXT NOT NULL,
    summary_json TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);

CREATE TABLE IF NOT EXISTS items (
    question_id TEXT NOT NULL,
    session_id TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    PRIMARY KEY (question_id, session_id)
);

CREATE TABLE IF NOT EXISTS calibrated_items (
    question_id TEXT PRIMARY KEY,
    a REAL NOT NULL,
    b REAL NOT NULL,
    response_count INTEGER NOT NULL DEFAULT 0,
    last_calibrated_at REAL,
    prior_a REAL NOT NULL,
    prior_b REAL NOT NULL,
    prior_weight REAL NOT NULL DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS responses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    question_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    choice_index INTEGER NOT NULL,
    correct INTEGER NOT NULL,
    a REAL NOT NULL,
    b REAL NOT NULL,
    theta_before REAL NOT NULL,
    theta_after REAL NOT NULL,
    answered_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_responses_session ON responses(session_id);

CREATE TABLE IF NOT EXISTS theta_state (
    user_id TEXT NOT NULL,
    skill_id TEXT NOT NULL,
    attempts INTEGER NOT NULL DEFAULT 0,
    correct INTEGER NOT NULL DEFAULT 0,
    theta REAL NOT NULL,
    posterior_sd REAL NOT NULL,
    history_json TEXT NOT NULL,
    PRIMARY KEY (user_id, skill_id)
);
"""


class Store:
    """Thin SQLite DAO. One connection guarded by a lock (single-process v1)."""

    def __init__(self, path="satprep.db"):
        if path != ":memory:":
            import os
            os.makedirs(os.path.dirname(os.path.abspath(path)) or ".", exist_ok=True)
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def close(self):
        with self._lock:
            self._conn.close()

    def _execute(self, sql, params=()):
        cur = self._conn.execute(sql, params)
        rows = cur.fetchall()
        self._conn.commit()
        return rows

    def create_user(self, user_id: str, name: str) -> dict:
        with self._lock:
            existing = self._conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            if existing:
                return dict(existing)
            now = time.time()
            self._conn.execute(
                "INSERT INTO users (user_id, name, created_at) VALUES (?, ?, ?)",
                (user_id, name, now))
            self._conn.commit()
            return {"user_id": user_id, "name": name, "created_at": now}

    def get_user(self, user_id: str):
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)).fetchone()
            return dict(row) if row else None

    def create_session(self, session_id: str, user_id: str, kind: str,
                       section, length, seed) -> None:
        now = time.time()
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO sessions (session_id, user_id, kind, section,"
                " length, seed, status, created_at, updated_at)"
                " VALUES (?, ?, ?, ?, ?, ?, 'active', ?, ?)",
                (session_id, user_id, kind, section, length, seed, now, now))
            self._conn.commit()

    def finish_session(self, session_id: str, summary: dict) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE sessions SET status='complete', summary_json=?, updated_at=?"
                " WHERE session_id=?",
                (json.dumps(summary), time.time(), session_id))
            self._conn.commit()

    def get_session(self, session_id: str):
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
            return dict(row) if row else None

    def store_item(self, session_id: str, question_dict: dict) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR REPLACE INTO items (question_id, session_id, payload_json)"
                " VALUES (?, ?, ?)",
                (question_dict["question_id"], session_id,
                 json.dumps(question_dict)))
            # Register prior for calibration
            self._conn.execute(
                "INSERT INTO calibrated_items (question_id, a, b, prior_a, prior_b, prior_weight, "
                "response_count, last_calibrated_at) VALUES (?, ?, ?, ?, ?, 1.0, 0, NULL) "
                "ON CONFLICT(question_id) DO UPDATE SET a=excluded.a, b=excluded.b, "
                "prior_a=excluded.prior_a, prior_b=excluded.prior_b, "
                "prior_weight=excluded.prior_weight",
                (question_dict["question_id"], question_dict["a"], question_dict["b"],
                 question_dict["a"], question_dict["b"]))
            self._conn.commit()

    def add_response(self, session_id: str, rec, user_id: str = None) -> None:
        """Add a response. If user_id not provided, look it up from the session."""
        q = rec.question
        with self._lock:
            if user_id is None:
                try:
                    row = self._conn.execute(
                        "SELECT user_id FROM sessions WHERE session_id = ?", (session_id,)).fetchone()
                    user_id = row["user_id"] if row else "unknown"
                except Exception:
                    user_id = "unknown"
            self._conn.execute(
                "INSERT INTO responses (session_id, user_id, question_id, skill_id, difficulty,"
                " choice_index, correct, a, b, theta_before, theta_after, answered_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, user_id, q.question_id, q.skill_id, q.difficulty,
                 int(rec.choice_index), int(rec.correct), float(q.a), float(q.b),
                 float(rec.theta_before), float(rec.theta_after), time.time()))
            self._conn.commit()

    # --- Calibrated items ---

    def get_calibrated_item(self, question_id: str):
        """Get calibrated item parameters, or None if not yet calibrated."""
        with self._lock:
            row = self._conn.execute(
                "SELECT a, b, response_count, prior_a, prior_b, prior_weight "
                "FROM calibrated_items WHERE question_id = ?",
                (question_id,)).fetchone()
            return dict(row) if row else None

    def get_calibration_info(self, question_ids: List[str]) -> Dict[str, int]:
        """Get response counts for a list of question IDs."""
        if not question_ids:
            return {}
        placeholders = ",".join("?" * len(question_ids))
        with self._lock:
            rows = self._conn.execute(
                f"SELECT question_id, response_count FROM calibrated_items "
                f"WHERE question_id IN ({placeholders})",
                question_ids).fetchall()
            return {row["question_id"]: row["response_count"] for row in rows}

    def upsert_calibrated_item(self, question_id: str, a: float, b: float,
                                prior_weight: float = 1.0) -> None:
        """Insert or update a calibrated item with its prior parameters.
        
        Called when a new item is first seen to record its prior (a, b).
        """
        with self._lock:
            self._conn.execute(
                "INSERT INTO calibrated_items (question_id, a, b, prior_a, prior_b, prior_weight, "
                "response_count, last_calibrated_at) VALUES (?, ?, ?, ?, ?, ?, 0, NULL) "
                "ON CONFLICT(question_id) DO UPDATE SET a=excluded.a, b=excluded.b, "
                "prior_a=excluded.prior_a, prior_b=excluded.prior_b, "
                "prior_weight=excluded.prior_weight",
                (question_id, a, b, a, b, prior_weight))
            self._conn.commit()

    def _maybe_calibrate(self, question_id: str) -> None:
        """Check if item has N>=30 responses and run Bayesian recalibration if so."""
        with self._lock:
            row = self._conn.execute(
                "SELECT response_count, prior_a, prior_b, prior_weight, a, b "
                "FROM calibrated_items WHERE question_id = ?",
                (question_id,)).fetchone()
            if not row or row["response_count"] < 30:
                return
            # Run Bayesian update: blend prior with empirical MLE
            self._bayesian_update(question_id, row)

    def _bayesian_update(self, question_id: str, row: dict) -> None:
        """Bayesian update of (a, b) using precision-weighted average of prior and empirical.
        
        For 2PL, we approximate: empirical b from response log, empirical a from 
        discrimination of responses. Prior weight is treated as pseudo-count.
        """
        # Get empirical estimates from responses
        emp = self._conn.execute(
            "SELECT AVG(CASE WHEN correct=1 THEN 1.0 ELSE 0.0 END) AS p_correct, "
            "       AVG(theta_before) AS mean_theta, "
            "       COUNT(*) AS n "
            "FROM responses WHERE question_id = ?",
            (question_id,)).fetchone()
        
        n = emp["n"]
        if n < 30:
            return
        
        # Empirical b: solve p = logistic(a*(theta - b)) for b
        # Using mean theta and observed p_correct
        # With fixed a (use prior a as anchor), b = theta - logit(p)/a
        import math
        
        p_correct = emp["p_correct"] or 0.5
        p_correct = max(0.01, min(0.99, p_correct))  # clamp
        mean_theta = emp["mean_theta"] or 0.0
        prior_a = row["prior_a"]
        prior_b = row["prior_b"]
        prior_weight = row["prior_weight"]
        
        # Precision-weighted average for b
        # Prior variance ≈ 1.0 (from B_PRIOR_SD)
        # Empirical variance ≈ 1 / (n * a^2 * p * (1-p))  (Fisher info)
        p = p_correct
        info_emp = n * prior_a * prior_a * p * (1 - p)
        var_emp = 1.0 / info_emp if info_emp > 0 else 1.0
        var_prior = 1.0 / prior_weight if prior_weight > 0 else 1.0
        
        # Empirical b from MLE: b = theta - logit(p)/a
        logit_p = math.log(p / (1 - p))
        b_emp = mean_theta - logit_p / prior_a if prior_a > 0 else mean_theta
        
        # Blend: precision-weighted
        w_prior = 1.0 / var_prior
        w_emp = 1.0 / var_emp
        b_new = (w_prior * prior_b + w_emp * b_emp) / (w_prior + w_emp)
        
        # Update a with shrinkage toward prior
        a_new = (prior_weight * prior_a + w_emp * prior_a) / (prior_weight + w_emp)
        
        # Update in database
        self._conn.execute(
            "UPDATE calibrated_items SET a=?, b=?, response_count=?, "
            "last_calibrated_at=?, prior_weight=? WHERE question_id=?",
            (a_new, b_new, n, time.time(), prior_weight + n, question_id))
        self._conn.commit()

    def record_response(self, session_id: str, user_id: str, rec) -> None:
        """Record a response and update calibrated item if N>=30."""
        q = rec.question
        qid = q.question_id
        with self._lock:
            # Insert response with user_id
            self._conn.execute(
                "INSERT INTO responses (session_id, user_id, question_id, skill_id, difficulty,"
                " choice_index, correct, a, b, theta_before, theta_after, answered_at)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (session_id, user_id, qid, q.skill_id, q.difficulty,
                 int(rec.choice_index), int(rec.correct), float(q.a), float(q.b),
                 float(rec.theta_before), float(rec.theta_after), time.time()))
            
            # Upsert calibrated item with prior if new
            self._conn.execute(
                "INSERT INTO calibrated_items (question_id, a, b, prior_a, prior_b, prior_weight, "
                "response_count, last_calibrated_at) VALUES (?, ?, ?, ?, ?, 1.0, 0, NULL) "
                "ON CONFLICT(question_id) DO UPDATE SET "
                "response_count = response_count + 1",
                (qid, float(q.a), float(q.b), float(q.a), float(q.b)))
            
            # Check if we should calibrate
            row = self._conn.execute(
                "SELECT response_count FROM calibrated_items WHERE question_id = ?",
                (qid,)).fetchone()
            if row and row["response_count"] >= 30:
                # Run calibration inline (or could defer to nightly job)
                self._bayesian_update(qid, dict(row))
            
            self._conn.commit()

    def save_theta(self, user_id: str, learner) -> None:
        rows = []
        for sid in learner.states:
            st = learner.state(sid)
            rows.append((user_id, sid, st.attempts, st.correct, st.theta,
                         st.posterior_sd, json.dumps(st.history)))
        with self._lock:
            for r in rows:
                self._conn.execute(
                    "INSERT OR REPLACE INTO theta_state (user_id, skill_id, attempts,"
                    " correct, theta, posterior_sd, history_json)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?)", r)
            self._conn.commit()

    def load_theta_snapshot(self, user_id: str) -> list:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM theta_state WHERE user_id=? ORDER BY skill_id",
                (user_id,)).fetchall()
            out = []
            for row in rows:
                d = dict(row)
                d["history"] = json.loads(d.pop("history_json"))
                out.append(d)
            return out

    def user_response_log(self, user_id: str, limit=20000) -> list:
        """Ordered (skill_id, a, b, correct) tuples used to replay a learner."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT r.skill_id AS skill_id, r.a AS a, r.b AS b,"
                " r.correct AS correct FROM responses r"
                " JOIN sessions s ON r.session_id = s.session_id"
                " WHERE s.user_id=? ORDER BY r.id ASC LIMIT ?",
                (user_id, limit)).fetchall()
            return [(r["skill_id"], float(r["a"]), float(r["b"]), int(r["correct"]))
                    for r in rows]

    def move_sessions(self, from_user_id: str, to_user_id: str) -> int:
        with self._lock:
            cur = self._conn.execute(
                "UPDATE sessions SET user_id=? WHERE user_id=?",
                (to_user_id, from_user_id))
            self._conn.commit()
            return cur.rowcount

    def local_data_summary(self, user_id: str) -> dict:
        with self._lock:
            sessions = self._conn.execute(
                "SELECT COUNT(*) AS n FROM sessions WHERE user_id=?",
                (user_id,)).fetchone()["n"]
            responses = self._conn.execute(
                "SELECT COUNT(*) AS n FROM responses"
                " JOIN sessions ON responses.session_id = sessions.session_id"
                " WHERE sessions.user_id=?",
                (user_id,)).fetchone()["n"]
            return {"sessions": sessions, "responses": responses}

    def delete_user(self, user_id: str) -> int:
        with self._lock:
            sids = [r["session_id"] for r in self._conn.execute(
                "SELECT session_id FROM sessions WHERE user_id=?",
                (user_id,)).fetchall()]
            for sid in sids:
                self._conn.execute(
                    "DELETE FROM items WHERE session_id=?", (sid,))
            self._conn.execute(
                "DELETE FROM responses WHERE session_id IN"
                " (SELECT session_id FROM sessions WHERE user_id=?)",
                (user_id,))
            self._conn.execute(
                "DELETE FROM sessions WHERE user_id=?", (user_id,))
            self._conn.execute(
                "DELETE FROM theta_state WHERE user_id=?", (user_id,))
            self._conn.execute(
                "DELETE FROM users WHERE user_id=?", (user_id,))
            self._conn.commit()
            return len(sids)

    def export_user(self, user_id: str):
        with self._lock:
            def rows(sql, params=()):
                return [dict(r) for r in
                        self._conn.execute(sql, params).fetchall()]
            user = rows("SELECT * FROM users WHERE user_id=?",
                        (user_id,))
            sessions = rows("SELECT * FROM sessions WHERE user_id=?"
                            " ORDER BY created_at", (user_id,))
            responses = rows(
                "SELECT r.* FROM responses r JOIN sessions s"
                " ON r.session_id = s.session_id WHERE s.user_id=?"
                " ORDER BY r.id", (user_id,))
            items = rows(
                "SELECT i.* FROM items i JOIN sessions s"
                " ON i.session_id = s.session_id WHERE s.user_id=?",
                (user_id,))
            theta = rows("SELECT * FROM theta_state WHERE user_id=?",
                         (user_id,))
        for s in sessions:
            if s.get("summary_json"):
                s["summary"] = json.loads(s.pop("summary_json"))
        return {"user": user, "sessions": sessions, "responses": responses,
                "items": items, "theta_state": theta}

    def import_user(self, bundle: dict) -> int:
        with self._lock:
            count = 0
            for u in bundle.get("user", []):
                self._conn.execute(
                    "INSERT OR REPLACE INTO users (user_id,name,created_at)"
                    " VALUES (?,?,?)",
                    (u["user_id"], u["name"], u.get("created_at",
                                                    time.time())))
            for s in bundle.get("sessions", []):
                self._conn.execute(
                    "INSERT OR REPLACE INTO sessions (session_id,user_id,"
                    "kind,section,length,seed,status,summary_json,"
                    "created_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (s["session_id"], s["user_id"], s["kind"], s.get("section"),
                     s.get("length"), s.get("seed"), s["status"],
                     json.dumps(s["summary"]) if s.get("summary") else None,
                     s.get("created_at", time.time()),
                     s.get("updated_at", time.time())))
                count += 1
            for i in bundle.get("items", []):
                payload = i.get("payload_json") or json.dumps(i.get("payload"))
                self._conn.execute(
                    "INSERT OR REPLACE INTO items (question_id,session_id,"
                    "payload_json) VALUES (?,?,?)",
                    (i["question_id"], i["session_id"], payload))
            for s in bundle.get("sessions", []):
                self._conn.execute(
                    "DELETE FROM responses WHERE session_id=?",
                    (s["session_id"],))
            for r in bundle.get("responses", []):
                self._conn.execute(
                    "INSERT INTO responses (session_id, question_id,"
                    " skill_id, difficulty, choice_index, correct, a, b,"
                    " theta_before, theta_after, answered_at)"
                    " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (r["session_id"], r["question_id"], r["skill_id"],
                     r["difficulty"], r["choice_index"], r["correct"],
                     r["a"], r["b"], r["theta_before"], r["theta_after"],
                     r.get("answered_at", time.time())))
                count += 1
            for t in bundle.get("theta_state", []):
                history = t.get("history")
                if not isinstance(history, str):
                    history = json.dumps(history or [])
                self._conn.execute(
                    "INSERT OR REPLACE INTO theta_state (user_id,skill_id,"
                    " attempts, correct, theta, posterior_sd, history_json)"
                    " VALUES (?,?,?,?,?,?,?)",
                    (t["user_id"], t["skill_id"], t["attempts"],
                     t["correct"], t["theta"], t["posterior_sd"], history))
            self._conn.commit()
            return count

    def recent_sessions(self, user_id: str, limit=20) -> list:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sessions WHERE user_id=? ORDER BY created_at DESC"
                " LIMIT ?", (user_id, limit)).fetchall()
            out = []
            for row in rows:
                d = dict(row)
                if d.get("summary_json"):
                    d["summary"] = json.loads(d.pop("summary_json"))
                else:
                    d.pop("summary_json", None)
                out.append(d)
            return out

    def response_trend(self, user_id: str, limit=200) -> list:
        with self._lock:
            rows = self._conn.execute(
                "SELECT r.answered_at, r.correct, r.skill_id FROM responses r"
                " JOIN sessions s ON r.session_id = s.session_id"
                " WHERE s.user_id=? ORDER BY r.id ASC LIMIT ?",
                (user_id, limit)).fetchall()
            return [dict(r) for r in rows]

    def weak_rows(self, user_id: str) -> list:
        with self._lock:
            rows = self._conn.execute(
                "SELECT r.skill_id AS skill_id, r.difficulty AS difficulty,"
                " r.correct AS correct FROM responses r"
                " JOIN sessions s ON r.session_id = s.session_id"
                " WHERE s.user_id=?",
                (user_id,)).fetchall()
            return [dict(r) for r in rows]

    def missed_log(self, user_id: str, limit=40) -> list:
        """Incorrect answers joined with their stored question payloads."""
        with self._lock:
            rows = self._conn.execute(
                "SELECT r.choice_index AS choice_index,"
                " r.answered_at AS answered_at,"
                " i.payload_json AS payload_json"
                " FROM responses r"
                " JOIN sessions s ON r.session_id = s.session_id"
                " JOIN items i ON i.session_id = r.session_id"
                "  AND i.question_id = r.question_id"
                " WHERE s.user_id=? AND r.correct=0"
                " ORDER BY r.id DESC LIMIT ?",
                (user_id, limit)).fetchall()
            out = []
            for row in rows:
                d = dict(row)
                d["question"] = json.loads(d.pop("payload_json"))
                out.append(d)
            return out
