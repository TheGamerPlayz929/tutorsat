from ..core.framework import get_domain
from ..core.rng import derive_seed, rng_for
from .base import GenerationError, Question, draw_irt_params
from . import math_gen, rw_gen

GENERATORS = {}
GENERATORS.update(math_gen.GENERATORS)
GENERATORS.update(rw_gen.RW_GENERATORS)


def supported_skills():
    return set(GENERATORS.keys())


class QuestionBank:
    """Fills blueprint cells with concrete questions via seeded generators."""

    def __init__(self, master_seed=None):
        self.master_seed = master_seed if master_seed is not None else 0

    def make(self, cell, item_seq: int, master_seed=None, salt=None,
             avoid=None) -> Question:
        domain_id, skill_id, difficulty = cell
        seed = self.master_seed if master_seed is None else master_seed
        gen = GENERATORS.get(skill_id)
        if gen is None:
            raise GenerationError(f"no generator for skill '{skill_id}'")
        avoid = avoid if avoid is not None else set()
        payload = None
        chosen_rng = None
        for attempt in range(12):
            rng = rng_for(seed, "item", salt, item_seq, domain_id, skill_id,
                          difficulty, attempt)
            candidate = gen(rng, difficulty)
            if payload is None:
                payload, chosen_rng = candidate, rng
            if candidate["prompt"] not in avoid:
                payload, chosen_rng = candidate, rng
                break
        rng = chosen_rng
        a, b = draw_irt_params(rng, difficulty)
        question_id = f"q-{derive_seed(seed, 'item', salt, item_seq, domain_id, skill_id, difficulty):016x}"
        section = get_domain(domain_id).section
        avoid.add(payload["prompt"])
        return Question(
            question_id=question_id,
            section=section,
            domain_id=domain_id,
            skill_id=skill_id,
            difficulty=difficulty,
            a=round(a, 4),
            b=round(b, 4),
            prompt=payload["prompt"],
            choices=tuple(payload["choices"]),
            answer_index=int(payload["answer_index"]),
            explanation=payload["explanation"],
        )

    def fill_blueprint(self, blueprint, section=None):
        """Expand a Blueprint into an ordered list of Questions.

        Ordering: cells are visited in the order stored in the blueprint; within a
        cell, items are generated with consecutive item_seq values. The blueprint's
        own seed salts the derivation so two blueprints never collide on ids.
        A per-session `avoid` set makes the bank reseed (bounded attempts) rather
        than repeat an identical prompt within one session; if a finite template
        pool is smaller than the requested count, the duplicate falls back through
        deterministically instead of failing.
        """
        questions = []
        seq = 0
        used_prompts = set()
        for cell, count in blueprint.counts:
            for _ in range(count):
                questions.append(self.make(cell, seq, salt=blueprint.seed,
                                           avoid=used_prompts))
                seq += 1
        return questions
