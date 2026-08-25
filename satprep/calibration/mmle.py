"""Nightly MMLE calibration job for 2PL item parameters.

Runs batch marginal maximum likelihood estimation over accumulated response logs.
Re-estimates (a, b) for items with N >= 30 responses, blending against priors.
"""

import json
import math
import time
import sqlite3
from typing import List, Tuple, Optional
from dataclasses import dataclass

from ..core.ability import logistic, clamp_z, AbilityEstimator, PRIOR_MEAN, PRIOR_SD


@dataclass
class ItemParams:
    question_id: str
    a: float
    b: float
    prior_a: float
    prior_b: float
    prior_weight: float
    response_count: int
    last_calibrated_at: Optional[float] = None


@dataclass
class CalibrationResult:
    question_id: str
    a_new: float
    b_new: float
    n: int
    converged: bool
    iterations: int


def load_calibrated_items(conn: sqlite3.Connection) -> List[ItemParams]:
    """Load all items that have reached calibration threshold."""
    rows = conn.execute(
        "SELECT question_id, a, b, prior_a, prior_b, prior_weight, "
        "response_count, last_calibrated_at "
        "FROM calibrated_items WHERE response_count >= 30"
    ).fetchall()
    return [ItemParams(
        question_id=r["question_id"],
        a=r["a"], b=r["b"],
        prior_a=r["prior_a"], prior_b=r["prior_b"],
        prior_weight=r["prior_weight"],
        response_count=r["response_count"],
        last_calibrated_at=r["last_calibrated_at"]
    ) for r in rows]


def load_responses_for_item(conn: sqlite3.Connection, question_id: str) -> List[Tuple[float, float, int, float]]:
    """Load all responses for an item: (a, b, correct, theta_before)."""
    rows = conn.execute(
        "SELECT a, b, correct, theta_before FROM responses WHERE question_id = ?",
        (question_id,)
    ).fetchall()
    return [(float(r["a"]), float(r["b"]), int(r["correct"]), float(r["theta_before"]))
            for r in rows]


def estimate_b_mle(a: float, responses: List[Tuple[float, float, int, float]]) -> Optional[float]:
    """MLE estimate of b for fixed a, using logistic regression on binary responses."""
    if not responses:
        return None
    
    # Newton-Raphson for b
    b = sum(theta for _, _, _, theta in responses) / len(responses)  # init at mean theta
    for _ in range(20):
        g = 0.0
        h = 0.0
        for a_i, b_i, correct, theta in responses:
            z = clamp_z(a_i * (theta - b))
            p = logistic(z)
            g += a_i * (correct - p)
            h -= a_i * a_i * p * (1 - p)
        if abs(h) < 1e-12:
            break
        step = g / h
        if abs(step) > 5.0:
            step = math.copysign(5.0, step)
        b -= step
        if abs(step) < 1e-6:
            break
    return b


def estimate_a_mle(b: float, responses: List[Tuple[float, float, int, float]]) -> Optional[float]:
    """MLE estimate of a for fixed b."""
    if not responses:
        return None
    
    a = 1.0  # init
    for _ in range(20):
        g = 0.0
        h = 0.0
        for a_i, b_i, correct, theta in responses:
            z = clamp_z(a * (theta - b))
            p = logistic(z)
            g += (theta - b) * (correct - p)
            h -= (theta - b) ** 2 * p * (1 - p)
        if abs(h) < 1e-12:
            break
        step = g / h
        if abs(step) > 0.5:
            step = math.copysign(0.5, step)
        a += step
        a = max(0.2, min(2.5, a))  # clamp a to reasonable range
        if abs(step) < 1e-6:
            break
    return a


def bayesian_update(item: ItemParams, responses: List[Tuple[float, float, int, float]]) -> CalibrationResult:
    """Bayesian update blending prior with empirical estimates.
    
    Uses precision-weighted average of prior and empirical estimates.
    """
    n = len(responses)
    
    # Empirical estimates
    b_emp = estimate_b_mle(item.prior_a, responses)
    if b_emp is None:
        return CalibrationResult(item.question_id, item.a, item.b, n, False, 0)
    
    a_emp = estimate_a_mle(b_emp, responses)
    if a_emp is None:
        a_emp = item.prior_a
    
    # Precision weights
    # Prior precision = prior_weight
    # Empirical precision ~ Fisher information at MLE
    info_b = 0.0
    info_a = 0.0
    for a_i, b_i, correct, theta in responses:
        z = clamp_z(a_i * (theta - b_emp))
        p = logistic(z)
        info_b += a_i * a_i * p * (1 - p)
        info_a += (theta - b_emp) ** 2 * p * (1 - p)
    
    w_prior_b = item.prior_weight
    w_emp_b = info_b
    
    w_prior_a = item.prior_weight
    w_emp_a = info_a
    
    # Blend
    b_new = (w_prior_b * item.prior_b + w_emp_b * b_emp) / (w_prior_b + w_emp_b)
    a_new = (w_prior_a * item.prior_a + w_emp_a * a_emp) / (w_prior_a + w_emp_a)
    
    # Clamp to reasonable ranges
    b_new = max(-6.0, min(6.0, b_new))
    a_new = max(0.2, min(2.5, a_new))
    
    return CalibrationResult(
        question_id=item.question_id,
        a_new=a_new,
        b_new=b_new,
        n=n,
        converged=True,
        iterations=1
    )


def run_nightly_calibration(db_path: str = "satprep.db") -> dict:
    """Run the nightly MMLE calibration job.
    
    Returns a summary of calibration results.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    summary = {
        "started_at": time.time(),
        "items_processed": 0,
        "items_calibrated": 0,
        "errors": []
    }
    
    try:
        items = load_calibrated_items(conn)
        summary["items_processed"] = len(items)
        
        for item in items:
            try:
                responses = load_responses_for_item(conn, item.question_id)
                if len(responses) < 30:
                    continue
                
                result = bayesian_update(item, responses)
                if result.converged:
                    # Update database
                    conn.execute(
                        "UPDATE calibrated_items SET a=?, b=?, response_count=?, "
                        "last_calibrated_at=?, prior_weight=? WHERE question_id=?",
                        (result.a_new, result.b_new, result.n,
                         time.time(), item.prior_weight + result.n,
                         item.question_id)
                    )
                    conn.commit()
                    summary["items_calibrated"] += 1
                    
            except Exception as e:
                summary["errors"].append({"question_id": item.question_id, "error": str(e)})
                
    finally:
        conn.close()
    
    summary["finished_at"] = time.time()
    return summary


if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "satprep.db"
    result = run_nightly_calibration(db_path)
    print(json.dumps(result, indent=2))