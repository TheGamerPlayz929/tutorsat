import math
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Sequence, Tuple

from .framework import (
    DEFAULT_PROFILE,
    DIFFICULTY_PROFILES,
    SECTIONS,
    get_domain,
    get_skill,
    leaf_weights,
)
from .rng import derive_seed

Cell = Tuple[str, str, str]

DEFAULT_KAPPA = 400.0


def largest_remainder(weights: Sequence[float], total: int) -> list:
    """Allocate `total` integer seats proportional to `weights`.

    Deterministic: ties in fractional part are broken by lower index.
    """
    if total < 0:
        raise ValueError("total must be non-negative")
    if not weights:
        if total == 0:
            return []
        raise ValueError("empty weights")
    positives = [(i, w) for i, w in enumerate(weights) if w > 0]
    if not positives:
        if total == 0:
            return [0] * len(weights)
        raise ValueError("all weights are zero")
    weight_sum = sum(w for _, w in positives)
    alloc = [0] * len(weights)
    remainders = []
    used = 0
    for i, w in positives:
        exact = total * w / weight_sum
        floor = int(math.floor(exact + 1e-12))
        alloc[i] += floor
        used += floor
        remainders.append((exact - floor, i))
    remaining = total - used
    if remaining < 0 or remaining > len(remainders):
        raise RuntimeError(f"largest_remainder invariant violated: {remaining}")
    remainders.sort(key=lambda t: (-t[0], t[1]))
    for k in range(remaining):
        alloc[remainders[k][1]] += 1
    return alloc


def sample_dirichlet(alphas, rng):
    samples = [rng.gammavariate(a, 1.0) if a > 0 else 0.0 for a in alphas]
    z = sum(samples)
    return [s / z for s in samples]


@dataclass(frozen=True)
class Blueprint:
    section: Optional[str]
    profile: str
    total: int
    counts: Tuple[Tuple[Cell, int], ...]
    seed: int
    kappa: float

    def by_cell(self) -> Counter:
        return Counter({cell: n for cell, n in self.counts if n > 0})

    def by_skill(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for (dom, sk, dif), n in self.counts:
            out[sk] = out.get(sk, 0) + n
        return out

    def by_domain(self) -> Dict[str, int]:
        out: Dict[str, int] = {}
        for (dom, sk, dif), n in self.counts:
            out[dom] = out.get(dom, 0) + n
        return out

    def by_difficulty(self) -> Dict[str, int]:
        out = {"easy": 0, "medium": 0, "hard": 0}
        for (dom, sk, dif), n in self.counts:
            out[dif] += n
        return out


class BlueprintModel:
    """Dirichlet-multinomial model over framework leaves.

    Prior: Dirichlet(kappa * w) where w are normalized framework leaf weights.
    Posterior after reference/practice-form counts n: Dirichlet(kappa*w + n).
    A draw samples pi ~ posterior, takes N*pi, and largest-remainder rounds
    to an exact integer allocation of N questions.
    """

    def __init__(self, kappa: float = DEFAULT_KAPPA,
                 observations: Optional[Dict[Cell, int]] = None):
        if kappa <= 0:
            raise ValueError("kappa must be positive")
        self.kappa = float(kappa)
        self.observations = {c: int(n) for c, n in (observations or {}).items()}
        if any(n < 0 for n in self.observations.values()):
            raise ValueError("observation counts must be non-negative")

    def alphas(self, section=None, skill_ids=None, profile=DEFAULT_PROFILE):
        weights = leaf_weights(section=section, skill_ids=skill_ids, profile=profile)
        cells = sorted(weights.keys())
        return [
            (cell, self.kappa * weights[cell] + self.observations.get(cell, 0))
            for cell in cells
        ]

    def draw(self, total: int, section=None, skill_ids=None,
             profile=DEFAULT_PROFILE, seed=None) -> Blueprint:
        from random import Random

        if total < 0:
            raise ValueError("total must be non-negative")
        if section is not None and section not in SECTIONS:
            raise ValueError(f"unknown section: {section}")
        if profile not in DIFFICULTY_PROFILES:
            raise ValueError(f"unknown difficulty profile: {profile}")
        if skill_ids is not None:
            skill_ids = frozenset(skill_ids)
            for sid in skill_ids:
                get_skill(sid)
                if section is not None:
                    section_skills = {s.skill_id for d in SECTIONS[section].domains
                                      for s in d.skills}
                    if sid not in section_skills:
                        raise ValueError(f"skill {sid} not in section {section}")
        if seed is None:
            seed = derive_seed("auto", section, tuple(sorted(skill_ids)) if skill_ids else (),
                               profile, total, self.kappa)

        pairs = self.alphas(section=section, skill_ids=skill_ids, profile=profile)
        cells = [c for c, _ in pairs]
        alphas = [a for _, a in pairs]
        rng = Random(seed)
        probs = sample_dirichlet(alphas, rng)
        alloc = largest_remainder(probs, total)
        counts = tuple((cells[i], alloc[i]) for i in range(len(cells)))
        return Blueprint(
            section=section,
            profile=profile,
            total=total,
            counts=tuple((c, n) for c, n in counts if n > 0),
            seed=seed,
            kappa=self.kappa,
        )

    def describe_cell(self, cell: Cell) -> str:
        dom, sk, dif = cell
        return f"{get_domain(dom).name} / {get_skill(sk).name} [{dif}]"
