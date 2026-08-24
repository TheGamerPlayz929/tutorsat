import math

ANCHORS = [
    (-2.5, 300),
    (-1.0, 430),
    (0.0, 530),
    (1.0, 630),
    (2.5, 740),
]
MIN_SCORE = 200
MAX_SCORE = 800


def _interpolate(theta: float) -> float:
    if theta <= ANCHORS[0][0]:
        return float(ANCHORS[0][1])
    if theta >= ANCHORS[-1][0]:
        return float(ANCHORS[-1][1])
    for (t0, s0), (t1, s1) in zip(ANCHORS, ANCHORS[1:]):
        if t0 <= theta <= t1:
            frac = (theta - t0) / (t1 - t0)
            return s0 + frac * (s1 - s0)
    return 500.0


def estimated_score(theta: float, n_items: int = 10):
    """Map a section-level mean theta to an estimated score band.

    Heuristic calibration (documented in README): piecewise-linear anchors on
    the IRT scale, with band width shrinking like 60/sqrt(n_items), clamped to
    [15, 80] points. This is NOT College Board equating.
    """
    center = _interpolate(theta)
    half = max(15.0, min(80.0, 60.0 / math.sqrt(max(1, n_items))))
    low = max(MIN_SCORE, int(round(center - half / 2.0)))
    high = min(MAX_SCORE, int(round(center + half / 2.0)))
    return low, high
