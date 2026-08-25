from dataclasses import dataclass, field
from typing import Dict, List, Optional
import random

from ..core.ability import LearnerModel, SkillState, fisher_information
from ..core.blueprint import BlueprintModel
from ..core.framework import DEFAULT_PROFILE
from ..questions.bank import QuestionBank
from ..questions.base import Question


@dataclass
class AnswerRecord:
    question: Question
    choice_index: int
    correct: bool
    theta_before: float
    theta_after: float


class PracticeSession:
    """Adaptive practice: blueprint -> items served by max Fisher information.

    At each step the next question is the unanswered item whose 2PL Fisher
    information at the current per-skill theta is highest (ties broken by
    original blueprint order), which concentrates difficulty near the learner's
    estimated ability - a lightweight computerized-adaptive-testing policy.

    Cold-start exploration: for items with < 30 responses (uncalibrated),
    adds exploration noise to prevent clustering and ensure tail coverage.
    """

    EXPLORATION_RATE = 0.3  # probability of exploring for uncalibrated items
    CALIBRATION_THRESHOLD = 30

    def __init__(self, user_id: str = "anon", section: Optional[str] = None,
                 length: int = 10, skills=None, seed=None,
                 learner: Optional[LearnerModel] = None,
                 model: Optional[BlueprintModel] = None,
                 bank: Optional[QuestionBank] = None,
                 profile: str = DEFAULT_PROFILE,
                 calibration_info: Optional[Dict[str, int]] = None,
                 rng: Optional[random.Random] = None):
        self.user_id = user_id
        self.section = section
        self.length = length
        self.seed = seed if seed is not None else 0
        self.profile = profile
        self.model = model or BlueprintModel()
        self.bank = bank or QuestionBank(master_seed=self.seed)
        self.learner = learner or LearnerModel()

        # calibration_info: {question_id: response_count} for cold-start exploration
        self.calibration_info = calibration_info or {}
        self.rng = rng or random.Random(self.seed)

        self.blueprint = self.model.draw(
            length, section=section, skill_ids=skills, profile=profile, seed=self.seed)
        self.questions: List[Question] = self.bank.fill_blueprint(self.blueprint)
        self._remaining: List[int] = list(range(len(self.questions)))
        self._pending_index: Optional[int] = None
        self.records: List[AnswerRecord] = []
        self.finished = len(self.questions) == 0

    @property
    def answered_count(self) -> int:
        return len(self.records)

    def theta_for_skill(self, skill_id: str) -> float:
        st: SkillState = self.learner.state(skill_id)
        return st.theta

    def _is_calibrated(self, question_id: str) -> bool:
        """Check if an item has reached calibration threshold."""
        return self.calibration_info.get(question_id, 0) >= self.CALIBRATION_THRESHOLD

    def _exploration_score(self, q: Question, theta: float) -> float:
        """Add exploration noise for uncalibrated items to prevent clustering."""
        base_info = fisher_information(q.a, q.b, theta)
        if self._is_calibrated(q.question_id):
            return base_info
        # For uncalibrated items, mix in exploration
        if self.rng.random() < self.EXPLORATION_RATE:
            # Add noise proportional to base info to encourage spread
            noise = self.rng.uniform(0, base_info * 2) if base_info > 0 else self.rng.uniform(0, 1)
            return base_info + noise
        return base_info

    def next_question(self) -> Optional[Question]:
        """Serve the max-information unanswered item given current ability.

        Idempotent: returns the pending question until it is answered.
        Cold-start exploration: uncalibrated items get exploration noise.
        """
        if self._pending_index is not None:
            return self.questions[self._pending_index]
        if not self._remaining:
            return None
        best_pos, best_score = None, None
        for pos, q_idx in enumerate(self._remaining):
            q = self.questions[q_idx]
            info = self._exploration_score(q, self.theta_for_skill(q.skill_id))
            if best_score is None or info > best_score + 1e-12:
                best_pos, best_score = pos, info
        idx = self._remaining.pop(best_pos)
        self._pending_index = idx
        return self.questions[idx]

    def answer(self, choice_index: int) -> AnswerRecord:
        if self._pending_index is None:
            raise RuntimeError("no question is currently served")
        if not 0 <= int(choice_index) < len(
                self.questions[self._pending_index].choices):
            raise ValueError("choice_index out of range")
        q = self.questions[self._pending_index]
        theta_before = self.theta_for_skill(q.skill_id)
        correct = q.is_correct(int(choice_index))
        state = self.learner.respond(q.skill_id, q.a, q.b, int(correct))
        record = AnswerRecord(question=q, choice_index=int(choice_index),
                              correct=correct, theta_before=theta_before,
                              theta_after=state.theta)
        self.records.append(record)
        self._pending_index = None
        if not self._remaining:
            self.finished = True
        return record

    def summary(self) -> dict:
        total = len(self.records)
        correct = sum(1 for r in self.records if r.correct)
        per_skill: Dict[str, dict] = {}
        for r in self.records:
            sid = r.question.skill_id
            slot = per_skill.setdefault(sid, {"attempts": 0, "correct": 0})
            slot["attempts"] += 1
            slot["correct"] += int(r.correct)
        for sid, slot in per_skill.items():
            st = self.learner.state(sid)
            slot["theta"] = round(st.theta, 4)
            slot["posterior_sd"] = round(st.posterior_sd, 4)
        return {
            "user_id": self.user_id,
            "section": self.section,
            "length": self.length,
            "answered": total,
            "total_questions": len(self.questions),
            "correct": correct,
            "accuracy": (correct / total) if total else 0.0,
            "per_skill": per_skill,
            "seed": self.seed,
        }
