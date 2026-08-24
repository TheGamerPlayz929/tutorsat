import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence, Tuple

PRIOR_MEAN = 0.0
PRIOR_SD = 1.0
_NEWTON_TOL = 1e-10
_GRAD_TOL = 1e-9
_MAX_ITER = 200
_STEP_CLAMP = 10.0
_Z_CLAMP = 35.0


def logistic(x: float) -> float:
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def log_logistic(x: float) -> float:
    if x >= 0:
        return -math.log1p(math.exp(-x))
    return x - math.log1p(math.exp(x))


def clamp_z(z: float) -> float:
    return max(-_Z_CLAMP, min(_Z_CLAMP, z))


def fisher_information(a: float, b: float, theta: float) -> float:
    """I(theta; item) = a^2 * p * (1 - p) for the 2PL model."""
    p = logistic(clamp_z(a * (theta - b)))
    return a * a * p * (1.0 - p)


@dataclass(frozen=True)
class Item:
    item_id: str
    skill_id: str
    a: float
    b: float


@dataclass(frozen=True)
class FitResult:
    theta: float
    posterior_sd: float
    n_items: int
    iterations: int
    converged: bool


class AbilityEstimator:
    """Maximum a posteriori estimation of theta under a 2PL likelihood.

    Log-posterior (up to a constant):
        l(theta) = sum_i [ u_i log p_i + (1-u_i) log(1-p_i) ] - (theta-mu)^2/(2*sd^2)
    Gradient and Hessian have closed forms and l is strictly concave
    (Hessian < 0 everywhere), so Newton-Raphson converges to the unique MAP.
    Posterior sd uses the Laplace approximation 1/sqrt(observed information).
    """

    def __init__(self, mu: float = PRIOR_MEAN, prior_sd: float = PRIOR_SD):
        if prior_sd <= 0:
            raise ValueError("prior_sd must be positive")
        self.mu = float(mu)
        self.prior_sd = float(prior_sd)

    def _log_posterior(self, theta, ab, u):
        total = 0.0
        for (a, b), ui in zip(ab, u):
            z = clamp_z(a * (theta - b))
            lp = log_logistic(z)
            lq = log_logistic(-z)
            total += ui * lp + (1.0 - ui) * lq
        total -= ((theta - self.mu) ** 2) / (2.0 * self.prior_sd ** 2)
        return total

    def fit(self, items: Sequence[Tuple[float, float]],
            responses: Sequence[int], theta_init: Optional[float] = None) -> FitResult:
        if len(items) != len(responses):
            raise ValueError("items and responses must have equal length")
        for a, _b in items:
            if a <= 0:
                raise ValueError("discrimination a must be positive")
        for u in responses:
            if u not in (0, 1):
                raise ValueError("responses must be 0 or 1")
        ab = [(float(a), float(b)) for a, b in items]

        if not ab:
            return FitResult(theta=self.mu, posterior_sd=self.prior_sd,
                             n_items=0, iterations=0, converged=True)

        inv_var = 1.0 / self.prior_sd ** 2
        theta = self.mu if theta_init is None else float(theta_init)
        current = self._log_posterior(theta, ab, responses)
        converged = False
        iterations = 0
        for iterations in range(1, _MAX_ITER + 1):
            g = -(theta - self.mu) * inv_var
            h = -inv_var
            for (a, b), ui in zip(ab, responses):
                z = clamp_z(a * (theta - b))
                p = logistic(z)
                g += a * (ui - p)
                h -= a * a * p * (1.0 - p)
            if abs(g) < _GRAD_TOL:
                converged = True
                break
            raw = g / h
            if abs(raw) > _STEP_CLAMP:
                raw = math.copysign(_STEP_CLAMP, raw)
            accepted = False
            t = 1.0
            while t > 1e-8:
                cand = theta - t * raw
                cll = self._log_posterior(cand, ab, responses)
                if cll >= current - 1e-12:
                    moved = abs(cand - theta)
                    theta, current = cand, cll
                    accepted = True
                    break
                t *= 0.5
            if not accepted:
                converged = True
                break
            if moved < _NEWTON_TOL:
                converged = True
                break

        h_final = -inv_var
        for (a, b), ui in zip(ab, responses):
            p = logistic(clamp_z(a * (theta - b)))
            h_final -= a * a * p * (1.0 - p)
        post_sd = math.sqrt(-1.0 / h_final)
        return FitResult(theta=theta, posterior_sd=post_sd,
                         n_items=len(ab), iterations=iterations,
                         converged=converged)

    def information(self, items: Sequence[Tuple[float, float]], theta: float) -> float:
        return sum(fisher_information(a, b, theta) for a, b in items)


def most_informative(items: Sequence[Item], theta: float) -> Item:
    """Pick the item with maximal Fisher information at theta."""
    best = None
    best_info = -1.0
    for idx, item in enumerate(items):
        info = fisher_information(item.a, item.b, theta)
        if info > best_info + 1e-15:
            best_info = info
            best = item
    if best is None:
        raise ValueError("no items to choose from")
    return best


@dataclass
class SkillState:
    skill_id: str
    theta: float
    posterior_sd: float
    attempts: int = 0
    correct: int = 0
    history: List[float] = field(default_factory=list)


class LearnerModel:
    """Per-skill 2PL tracking: appends graded responses and refits exact MAP."""

    def __init__(self, estimator: Optional[AbilityEstimator] = None):
        self.estimator = estimator or AbilityEstimator()
        self._responses: Dict[str, List[Tuple[float, float, int]]] = {}
        self.states: Dict[str, SkillState] = {}

    def respond(self, skill_id: str, a: float, b: float, correct: int) -> SkillState:
        if correct not in (0, 1):
            raise ValueError("correct must be 0 or 1")
        log = self._responses.setdefault(skill_id, [])
        log.append((float(a), float(b), int(correct)))
        result = self.estimator.fit([(a_, b_) for a_, b_, _ in log],
                                    [u for _, _, u in log])
        st = self.states.get(skill_id)
        if st is None:
            st = SkillState(skill_id=skill_id, theta=result.theta,
                            posterior_sd=result.posterior_sd)
            self.states[skill_id] = st
        else:
            st.theta = result.theta
            st.posterior_sd = result.posterior_sd
        st.attempts += 1
        st.correct += int(correct)
        st.history.append(result.theta)
        return st

    def state(self, skill_id: str) -> SkillState:
        st = self.states.get(skill_id)
        if st is not None:
            return st
        return SkillState(skill_id=skill_id, theta=self.estimator.mu,
                          posterior_sd=self.estimator.prior_sd)

    def has_activity(self, skill_id: str) -> bool:
        return bool(self._responses.get(skill_id))
