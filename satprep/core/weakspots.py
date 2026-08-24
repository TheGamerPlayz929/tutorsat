from collections import defaultdict

from ..core.framework import DIFFICULTIES, get_domain

MIN_ATTEMPTS = 3
STRONG_THRESHOLD = 0.80
STRUGGLE_THRESHOLD = 0.50

TIER_LABELS = {"easy": "Foundations", "medium": "Medium", "hard": "Advanced"}

_STATUS_ORDER = {"struggling": 0, "developing": 1, "strong": 2}


def _status(accuracy: float) -> str:
    if accuracy < STRUGGLE_THRESHOLD:
        return "struggling"
    if accuracy < STRONG_THRESHOLD:
        return "developing"
    return "strong"


def _worst_tier(cells):
    worst_tier, worst_rate = None, 2.0
    for tier, stats in cells.items():
        if stats["attempted"] == 0:
            continue
        rate = stats["correct"] / stats["attempted"]
        if rate < worst_rate:
            worst_tier, worst_rate = tier, rate
    return worst_tier


def compute_weak_spots(rows):
    """rows: iterable of dicts with domain_id, difficulty, correct.

    Returns domain-level verdicts sorted worst-first. Cells with fewer than
    MIN_ATTEMPTS attempts are excluded; domains with no qualifying cells are
    omitted entirely.
    """
    agg = defaultdict(lambda: defaultdict(
        lambda: {"attempted": 0, "correct": 0}))
    totals = defaultdict(lambda: {"attempted": 0, "correct": 0})
    for row in rows:
        domain_id = row.get("domain_id") or row.get("domain")
        if not domain_id:
            continue
        difficulty = row["difficulty"]
        if difficulty not in DIFFICULTIES:
            continue
        correct = int(bool(row["correct"]))
        cell = agg[domain_id][difficulty]
        cell["attempted"] += 1
        cell["correct"] += correct
        totals[domain_id]["attempted"] += 1
        totals[domain_id]["correct"] += correct

    out = []
    for domain_id, cells in agg.items():
        total = totals[domain_id]
        if total["attempted"] < MIN_ATTEMPTS:
            continue
        tier = _worst_tier(cells)
        tier_stats = cells[tier]
        attempted = total["attempted"]
        correct = total["correct"]
        accuracy = correct / attempted
        out.append({
            "domain_id": domain_id,
            "domain_name": get_domain(domain_id).name,
            "section": get_domain(domain_id).section,
            "tier": tier,
            "tier_label": TIER_LABELS[tier],
            "tier_attempted": tier_stats["attempted"],
            "tier_correct": tier_stats["correct"],
            "tier_accuracy": round(tier_stats["correct"]
                                   / tier_stats["attempted"], 4),
            "attempted": attempted,
            "correct": correct,
            "accuracy": round(accuracy, 4),
            "status": _status(accuracy),
        })
    out.sort(key=lambda w: (_STATUS_ORDER[w["status"]],
                            w["accuracy"],
                            -w["attempted"]))
    return out
