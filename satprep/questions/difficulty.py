"""Difficulty validation for TutorSAT.

Implements the conceptual distinction (§7):
    template_difficulty — which generator branch was requested (easy/medium/hard)
    instance_difficulty  — what the resulting item's cognitive demand actually is

Scoring is a deterministic, interpretable gate (§9), not a single opaque
threshold. Every generated item carries a DifficultyProfile (§8) produced by
the generator (which knows what it built). The bank validates the profile;
hard items that fail the minimum gate (§10) are rejected/resampled.

No ML, no College Board content, stdlib only. Deterministic.
"""

from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class DifficultyProfile:
    """Internal cognitive-demand metadata (§8). Not shown to students.

    Fields follow §3 required dimensions. Generators construct this;
    the bank scores it.
    """

    # §3.2 reasoning steps: meaningful transitions, not raw arithmetic
    reasoning_steps: int  # 1, 2, 3, ...
    # §3.5 decision-point count: non-obvious choices the student must make
    decision_points: int  # 0, 1, 2, ...
    # §3.3 representation translation: words→equation, graph→equation, etc.
    representation_translation: bool
    # §3.4 concept interaction: two relevant ideas must interact
    concept_interaction: bool
    # §3.6 distractor quality: 0=bad/nonsense, 1=plausible, 2=error-pathway
    distractor_quality: int  # 0, 1, 2
    # §3.7 information density: additional interpreted information
    information_density: int  # 0, 1, 2
    # §3.8 computational burden: subordinate to reasoning
    computation_burden: int  # 0, 1, 2
    # §3.1 directness: 0=direct operation revealed, 2=non-obvious construction
    directness: int  # 0, 1, 2
    # §4 hard / §10 constraint that must be incorporated
    constraint_complexity: bool


# ---------------------------------------------------------------------------
# Hard rejection rules (§5) — automatic reasons to reject a HARD label
# ---------------------------------------------------------------------------

def _hard_reasons(profile: DifficultyProfile) -> List[str]:
    reasons: List[str] = []
    # Mathematical
    if profile.reasoning_steps <= 1 and not profile.representation_translation \
            and not profile.concept_interaction and not profile.constraint_complexity:
        reasons.append("HARD requires >1 reasoning step or translation/interaction/constraint")
    if profile.decision_points == 0:
        reasons.append("HARD requires at least 2 decision points (has 0)")
    if profile.decision_points == 1:
        reasons.append("HARD requires at least 2 decision points (has 1)")
    if profile.directness == 0:
        reasons.append("HARD: operation is directly revealed (directness=0)")
    if profile.distractor_quality == 0:
        reasons.append("HARD: distractors not plausible (quality=0)")
    # R&W / general
    if profile.reasoning_steps == 1 and profile.directness == 0:
        reasons.append("HARD: single obvious operation, equation already in needed form")
    # §5: "student only needs to take a square root and select ±"
    # Detected via reasoning_steps==1 + directness==0 + no interaction
    # (generators for (x+p)^2=q set reasoning_steps=1; gate above already covers)
    # Computation as primary difficulty (§3.8 / §5)
    if profile.computation_burden == 2 and profile.reasoning_steps <= 2 \
            and not profile.concept_interaction and not profile.representation_translation:
        reasons.append("HARD: difficulty is primarily tedious computation")
    return reasons


def _substantial_characteristic(profile: DifficultyProfile) -> bool:
    """§10: at least one substantial reasoning characteristic."""
    # Direct translation of §10 list: non-obvious model construction,
    # multiple dependent transformations, conditional selection, meaningful
    # parameter interpretation, multi-representation, interaction.
    # Encoded as booleans in the profile.
    return bool(
        profile.representation_translation
        or profile.concept_interaction
        or profile.constraint_complexity
        or (profile.information_density >= 1 and profile.directness >= 1)
    )


# ---------------------------------------------------------------------------
# Categorical gates (§4, §9, §10)
# ---------------------------------------------------------------------------

def _passes_hard(profile: DifficultyProfile) -> Tuple[bool, List[str]]:
    reasons = _hard_reasons(profile)
    if reasons:
        return False, reasons
    # Structural gate (§4 HARD, §10)
    # At least 2 meaningful transitions; 3 preferred, 2 allowed only with translation
    if profile.reasoning_steps < 2:
        return False, ["HARD requires ≥2 reasoning steps (has %d)" % profile.reasoning_steps]
    if profile.reasoning_steps == 2 and not profile.representation_translation:
        return False, ["HARD with 2 steps requires representation translation"]
    if profile.reasoning_steps >= 3 and profile.decision_points < 2:
        # 3+ steps but fewer than 2 decision points → still trivial chain
        return False, ["HARD with ≥3 steps still requires ≥2 decision points"]
    if not _substantial_characteristic(profile):
        return False, ["HARD requires a substantial characteristic (translation/interaction/constraint)"]
    if profile.distractor_quality < 1:
        return False, ["HARD requires distractor_quality ≥1"]
    if profile.directness == 0:
        return False, ["HARD requires directness ≥1"]
    return True, []


def _passes_medium(profile: DifficultyProfile) -> Tuple[bool, List[str]]:
    reasons: List[str] = []
    if profile.reasoning_steps < 2:
        reasons.append("MEDIUM requires ≥2 reasoning steps (has %d)" % profile.reasoning_steps)
    if profile.decision_points < 1:
        reasons.append("MEDIUM requires ≥1 decision point")
    if profile.distractor_quality == 0:
        reasons.append("MEDIUM requires distractor_quality ≥1")
    if not reasons:
        return True, []
    # Additional soft check: directness 0 with 1 step and no translation → easy
    if profile.directness == 0 and not profile.representation_translation \
            and not profile.concept_interaction:
        reasons.append("MEDIUM: direct application with no translation/interaction")
    return (False, reasons) if reasons else (True, [])


def score_difficulty(
    payload: Optional[Dict] = None,
    profile: Optional[DifficultyProfile] = None,
) -> Tuple[str, List[str], DifficultyProfile]:
    """Validate an item's profile and return its instance difficulty.

    Args:
        payload: generator payload (unused today, reserved for future heuristics)
        profile: DifficultyProfile produced by the generator. If None,
                 defaults to an Easy profile (so items without meta cannot
                 be mislabeled Hard).

    Returns:
        (tier in {'easy','medium','hard'}, reasons: list[str], profile used)
    """
    if profile is None:
        # No profile → cannot be Hard. Treat as easy fallback (§9).
        fallback = DifficultyProfile(
            reasoning_steps=1,
            decision_points=0,
            representation_translation=False,
            concept_interaction=False,
            distractor_quality=0,
            information_density=0,
            computation_burden=0,
            directness=0,
            constraint_complexity=False,
        )
        return "easy", ["no difficulty_profile provided → easy fallback"], fallback

    hard_ok, hard_reasons = _passes_hard(profile)
    if hard_ok:
        return "hard", [], profile

    medium_ok, medium_reasons = _passes_medium(profile)
    if medium_ok:
        # Item passed medium but failed hard → medium
        # Include hard rejection reasons for audit visibility
        return "medium", hard_reasons, profile

    # Otherwise easy (even if it was requested as medium/hard, the instance is easy)
    return "easy", hard_reasons + medium_reasons, profile


# Exposed for bank and audit
HARD_REJECTION_RULES = _hard_reasons  # alias for §5 reference


def profile_from_dict(d: Optional[Dict]) -> Optional[DifficultyProfile]:
    """Coerce a plain dict (from generator payload) into a DifficultyProfile."""
    if not d:
        return None
    try:
        return DifficultyProfile(**{k: d[k] for k in DifficultyProfile.__dataclass_fields__})
    except Exception:
        return None


def as_dict(profile: DifficultyProfile) -> Dict:
    return asdict(profile)
