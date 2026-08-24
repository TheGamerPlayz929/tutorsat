from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Tuple

B_RANGES = {
    "easy": (-2.0, -0.7),
    "medium": (-0.5, 0.6),
    "hard": (0.8, 2.2),
}
A_RANGE = (1.0, 1.6)


def draw_irt_params(rng, difficulty: str) -> Tuple[float, float]:
    lo, hi = B_RANGES[difficulty]
    return rng.uniform(*A_RANGE), rng.uniform(lo, hi)


def fmt_number(value) -> str:
    if isinstance(value, Fraction):
        if value.denominator == 1:
            return str(value.numerator)
        return f"{value.numerator}/{value.denominator}"
    if isinstance(value, int):
        return str(value)
    f = float(value)
    if abs(f - round(f)) < 1e-9:
        return str(int(round(f)))
    text = f"{f:.4f}".rstrip("0").rstrip(".")
    return text


@dataclass(frozen=True)
class Question:
    question_id: str
    section: str
    domain_id: str
    skill_id: str
    difficulty: str
    a: float
    b: float
    prompt: str
    choices: Tuple[str, ...]
    answer_index: int
    explanation: str

    def is_correct(self, choice_index: int) -> bool:
        return choice_index == self.answer_index

    def correct_choice(self) -> str:
        return self.choices[self.answer_index]

    def to_dict(self) -> dict:
        d = asdict(self)
        d["choices"] = list(d["choices"])
        return d


class GenerationError(RuntimeError):
    pass


def build_choices(rng, correct: str, distractors, max_tries: int = 50):
    """Return (shuffled 4-tuple of unique choice strings, index of correct)."""
    seen = [correct]
    pool = list(distractors)
    tries = 0
    while len(seen) < 4:
        if pool:
            cand = str(pool.pop(0))
        else:
            cand = None
        if cand is not None and cand not in seen:
            seen.append(cand)
            continue
        tries += 1
        if tries > max_tries:
            raise GenerationError("could not build 4 unique choices")
        filler = _filler(correct, tries)
        if filler not in seen:
            seen.append(filler)
    rng.shuffle(seen)
    trimmed = tuple(seen[:4])
    return trimmed, list(trimmed).index(correct)


def _filler(correct: str, n: int):
    stripped = correct.rstrip()
    suffix = ["", ".", "?", "!"][n % 4]
    candidate = stripped + suffix
    if candidate == correct or candidate in ("", "."):
        return stripped * 2 + suffix
    return candidate
