from dataclasses import asdict, dataclass
from fractions import Fraction
from typing import Tuple

# Single prior for all items - difficulty string controls content only, not b-parameter
B_PRIOR_MEAN = 0.0
B_PRIOR_SD = 1.0
A_RANGE = (0.8, 1.2)


def draw_irt_params(rng, difficulty: str) -> Tuple[float, float]:
    """Draw IRT parameters from single prior.
    
    Args:
        rng: Random number generator
        difficulty: Content difficulty tier (controls question content, NOT b-parameter)
    """
    b = rng.gauss(B_PRIOR_MEAN, B_PRIOR_SD)
    a = rng.uniform(*A_RANGE)
    return a, b


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
