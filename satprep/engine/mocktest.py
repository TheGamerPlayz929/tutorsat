from dataclasses import dataclass, field
from typing import Dict, List, Optional, Sequence

from ..core.ability import LearnerModel
from ..core.blueprint import BlueprintModel
from ..core.framework import (
    BRANCH_THRESHOLDS,
    SECTION_MATH,
    SECTION_RW,
    SECTIONS,
    DEFAULT_PROFILE,
)
from ..questions.bank import QuestionBank
from ..questions.base import Question
from ..scoring.scale import estimated_score


def branch_profile(pct_correct: float) -> str:
    """Map module-1 performance to a module-2 difficulty profile.

    Mirrors the digital SAT design where module 2's difficulty depends on
    module-1 results; thresholds are documented assumptions.
    """
    if pct_correct < BRANCH_THRESHOLDS["easy_leaning"]:
        return "easy_leaning"
    if pct_correct < BRANCH_THRESHOLDS["hard_leaning"]:
        return "balanced"
    return "hard_leaning"


@dataclass
class ModuleState:
    section: str
    module_index: int
    profile: str
    questions: List[Question]
    answers: Dict[str, int] = field(default_factory=dict)
    built: bool = True


class MockTest:
    """Full-length timed mock with adaptive second modules.

    Module 1 for each section is drawn from the balanced profile. Once every
    module-1 question in a section is answered, module 2 is assembled using the
    difficulty profile selected by branch_profile(module-1 percent correct).
    """

    def __init__(self, user_id: str = "anon",
                 sections: Sequence[str] = (SECTION_RW, SECTION_MATH),
                 seed=None,
                 learner: Optional[LearnerModel] = None,
                 model: Optional[BlueprintModel] = None,
                 bank: Optional[QuestionBank] = None):
        self.user_id = user_id
        self.sections = tuple(sections)
        self.seed = seed if seed is not None else 0
        self.model = model or BlueprintModel()
        from ..core.rng import derive_seed
        self.bank = bank or QuestionBank(master_seed=derive_seed(seed, "mock-bank"))
        self.learner = learner or LearnerModel()
        self.modules: Dict[tuple, ModuleState] = {}
        for sec in self.sections:
            self._build_module(sec, 1)

    def _build_module(self, section: str, index: int):
        profile = DEFAULT_PROFILE if index == 1 else None
        if index == 2:
            m1 = self.modules[(section, 1)]
            pct = (sum(1 for q in m1.questions
                       if m1.answers.get(q.question_id) == q.answer_index)
                   / max(1, len(m1.questions)))
            profile = branch_profile(pct)
        bp = self.model.draw(
            SECTIONS[section].questions_per_module, section=section,
            profile=profile, seed=self._module_seed(section, index))
        questions = self.bank.fill_blueprint(bp)
        self.modules[(section, index)] = ModuleState(
            section=section, module_index=index, profile=profile,
            questions=questions)

    def _module_seed(self, section, index):
        from ..core.rng import derive_seed
        return derive_seed(self.seed, "mock", section, index)

    def visible_questions(self, section: str) -> List[Question]:
        out = []
        for idx in (1, 2):
            mod = self.modules.get((section, idx))
            if mod and mod.built and (idx == 1 or self.module1_complete(section)):
                out.extend(mod.questions)
        return out

    def find_question(self, question_id: str) -> Optional[Question]:
        for mod in self.modules.values():
            for q in mod.questions:
                if q.question_id == question_id:
                    return q
        return None

    def answer(self, question_id: str, choice_index: int) -> bool:
        q = self.find_question(question_id)
        if q is None:
            raise KeyError(question_id)
        mod = next(m for m in self.modules.values()
                   if any(x.question_id == question_id for x in m.questions))
        if question_id in mod.answers:
            return False
        mod.answers[question_id] = int(choice_index)
        correct = int(q.is_correct(choice_index))
        self.learner.respond(q.skill_id, q.a, q.b, correct)
        if mod.module_index == 1 and self.module1_complete(mod.section) \
                and (mod.section, 2) not in self.modules:
            self._build_module(mod.section, 2)
        return True

    def module_questions(self, section: str, index: int) -> List[Question]:
        return list(self.modules[(section, index)].questions)

    def answered_in_module(self, section: str, index: int) -> int:
        return len(self.modules[(section, index)].answers)

    def module1_complete(self, section: str) -> bool:
        m1 = self.modules.get((section, 1))
        if m1 is None:
            return False
        return all(q.question_id in m1.answers for q in m1.questions)

    def module_result(self, section: str, index: int) -> dict:
        mod = self.modules[(section, index)]
        total = len(mod.questions)
        correct = sum(1 for q in mod.questions
                      if mod.answers.get(q.question_id) == q.answer_index)
        return {"section": section, "module": index, "profile": mod.profile,
                "answered": len(mod.answers), "total": total, "correct": correct}

    def domain_results(self, section: str) -> list:
        """Per-domain correct/total across both modules of a section."""
        from ..core.framework import get_domain
        agg = {}
        for idx in (1, 2):
            mod = self.modules.get((section, idx))
            if not mod:
                continue
            for q in mod.questions:
                if q.question_id not in mod.answers:
                    continue
                slot = agg.setdefault(q.domain_id, {"correct": 0, "total": 0})
                slot["total"] += 1
                if mod.answers[q.question_id] == q.answer_index:
                    slot["correct"] += 1
        return [{"domain_id": dom_id, "name": get_domain(dom_id).name, **stats}
                for dom_id, stats in sorted(agg.items())]

    def complete(self) -> bool:
        for sec in self.sections:
            for idx in (1, 2):
                if (sec, idx) not in self.modules:
                    return False
                mod = self.modules[(sec, idx)]
                if len(mod.answers) != len(mod.questions):
                    return False
        return True

    def section_score_estimate(self, section: str):
        weights = {}
        n_items = 0
        for idx in (1, 2):
            mod = self.modules.get((section, idx))
            if not mod:
                continue
            for q in mod.questions:
                if q.question_id in mod.answers:
                    weights[q.skill_id] = weights.get(q.skill_id, 0.0) + 1.0
                    n_items += 1
        if not n_items:
            return None
        theta_sum = sum(self.learner.state(sid).theta * count
                        for sid, count in weights.items())
        mean_theta = theta_sum / n_items
        return estimated_score(mean_theta, n_items=n_items)

    def report(self) -> dict:
        sections_report = {}
        for sec in self.sections:
            rep = {"modules": [self.module_result(sec, i) for i in (1, 2)],
                   "domains": self.domain_results(sec),
                   "score_estimate": self.section_score_estimate(sec)}
            sections_report[sec] = rep
        return {"user_id": self.user_id, "complete": self.complete(),
                "seed": self.seed, "sections": sections_report}
