from dataclasses import dataclass

EASY = "easy"
MEDIUM = "medium"
HARD = "hard"
DIFFICULTIES = (EASY, MEDIUM, HARD)

SECTION_RW = "rw"
SECTION_MATH = "math"


@dataclass(frozen=True)
class Skill:
    skill_id: str
    name: str
    weight: float


@dataclass(frozen=True)
class Domain:
    domain_id: str
    name: str
    section: str
    weight: float
    skills: tuple


@dataclass(frozen=True)
class Section:
    section_id: str
    name: str
    questions_per_module: int
    modules_in_test: int
    minutes_per_module: float
    domains: tuple


DOMAINS = (
    Domain(
        domain_id="craft_structure",
        name="Craft and Structure",
        section=SECTION_RW,
        weight=0.28,
        skills=(
            Skill("words_in_context", "Words in Context", 0.50),
            Skill("text_structure_purpose", "Text Structure and Purpose", 0.30),
            Skill("cross_text_connections", "Cross-Text Connections", 0.20),
        ),
    ),
    Domain(
        domain_id="info_ideas",
        name="Information and Ideas",
        section=SECTION_RW,
        weight=0.26,
        skills=(
            Skill("central_ideas_details", "Central Ideas and Details", 0.45),
            Skill("command_of_evidence", "Command of Evidence", 0.30),
            Skill("inferences", "Inferences", 0.25),
        ),
    ),
    Domain(
        domain_id="std_conventions",
        name="Standard English Conventions",
        section=SECTION_RW,
        weight=0.26,
        skills=(
            Skill("sentence_boundaries", "Boundaries", 0.50),
            Skill("form_structure_sense", "Form, Structure, and Sense", 0.50),
        ),
    ),
    Domain(
        domain_id="expression_ideas",
        name="Expression of Ideas",
        section=SECTION_RW,
        weight=0.20,
        skills=(
            Skill("transitions", "Transitions", 0.45),
            Skill("rhetorical_synthesis", "Rhetorical Synthesis", 0.55),
        ),
    ),
    Domain(
        domain_id="algebra",
        name="Algebra",
        section=SECTION_MATH,
        weight=0.35,
        skills=(
            Skill("linear_equations_1v", "Linear Equations in One Variable", 0.25),
            Skill("linear_functions", "Linear Functions", 0.20),
            Skill("systems_linear", "Systems of Two Linear Equations", 0.20),
            Skill("linear_inequalities", "Linear Inequalities", 0.10),
            Skill("linear_word_problems", "Linear Word Problems", 0.25),
        ),
    ),
    Domain(
        domain_id="advanced_math",
        name="Advanced Math",
        section=SECTION_MATH,
        weight=0.35,
        skills=(
            Skill("equivalent_expressions", "Equivalent Expressions", 0.30),
            Skill("nonlinear_equations", "Nonlinear Equations in One Variable", 0.40),
            Skill("nonlinear_systems", "Nonlinear Systems of Equations", 0.15),
            Skill("nonlinear_functions", "Nonlinear Functions", 0.15),
        ),
    ),
    Domain(
        domain_id="psda",
        name="Problem-Solving and Data Analysis",
        section=SECTION_MATH,
        weight=0.15,
        skills=(
            Skill("ratios_rates", "Ratios, Rates, and Proportional Relationships", 0.25),
            Skill("percentages", "Percentages", 0.20),
            Skill("one_variable_data", "One-Variable Data: Measures of Center and Spread", 0.20),
            Skill("probability", "Probability and Conditional Probability", 0.15),
            Skill("inference_studies", "Inference from Sample Statistics and Evaluating Claims", 0.10),
            Skill("units_conversion", "Units and Unit Conversion", 0.10),
        ),
    ),
    Domain(
        domain_id="geometry_trig",
        name="Geometry and Trigonometry",
        section=SECTION_MATH,
        weight=0.15,
        skills=(
            Skill("area_volume", "Area and Volume", 0.30),
            Skill("lines_angles_triangles", "Lines, Angles, and Triangles", 0.25),
            Skill("right_triangles_trig", "Right Triangles and Trigonometry", 0.25),
            Skill("circles", "Circles", 0.20),
        ),
    ),
)

SECTIONS = {
    SECTION_RW: Section(
        section_id=SECTION_RW,
        name="Reading and Writing",
        questions_per_module=27,
        modules_in_test=2,
        minutes_per_module=32,
        domains=tuple(d for d in DOMAINS if d.section == SECTION_RW),
    ),
    SECTION_MATH: Section(
        section_id=SECTION_MATH,
        name="Math",
        questions_per_module=22,
        modules_in_test=2,
        minutes_per_module=35,
        domains=tuple(d for d in DOMAINS if d.section == SECTION_MATH),
    ),
}

DIFFICULTY_PROFILES = {
    "balanced": {EASY: 0.30, MEDIUM: 0.45, HARD: 0.25},
    "easy_leaning": {EASY: 0.55, MEDIUM: 0.40, HARD: 0.05},
    "hard_leaning": {EASY: 0.05, MEDIUM: 0.35, HARD: 0.60},
    "expert": {EASY: 0.0, MEDIUM: 0.0, HARD: 1.0},
}
DEFAULT_PROFILE = "balanced"

BRANCH_THRESHOLDS = {"easy_leaning": 0.50, "hard_leaning": 0.75}


def _validate():
    for sec in SECTIONS.values():
        total = sum(d.weight for d in sec.domains)
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"section {sec.section_id} domain weights sum to {total}")
        for dom in sec.domains:
            stotal = sum(s.weight for s in dom.skills)
            if abs(stotal - 1.0) > 1e-9:
                raise ValueError(f"domain {dom.domain_id} skill weights sum to {stotal}")
    for name, prof in DIFFICULTY_PROFILES.items():
        ptotal = sum(prof[d] for d in DIFFICULTIES)
        if abs(ptotal - 1.0) > 1e-9:
            raise ValueError(f"profile {name} sums to {ptotal}")


_validate()


def get_domain(domain_id):
    return next(d for d in DOMAINS if d.domain_id == domain_id)


def get_skill(skill_id):
    for d in DOMAINS:
        for s in d.skills:
            if s.skill_id == skill_id:
                return s
    raise KeyError(skill_id)


def leaf_weights(section=None, skill_ids=None, profile=DEFAULT_PROFILE):
    """Joint weights over (domain_id, skill_id, difficulty) leaves.

    Normalized over the selected subset so filtered sessions still sum to 1.
    """
    if profile not in DIFFICULTY_PROFILES:
        raise ValueError(f"unknown difficulty profile: {profile}")
    if section is not None and section not in SECTIONS:
        raise ValueError(f"unknown section: {section}")
    diff = DIFFICULTY_PROFILES[profile]
    weights = {}
    for dom in DOMAINS:
        if section is not None and dom.section != section:
            continue
        for sk in dom.skills:
            if skill_ids is not None and sk.skill_id not in skill_ids:
                continue
            base = dom.weight * sk.weight
            for dif in DIFFICULTIES:
                key = (dom.domain_id, sk.skill_id, dif)
                weights[key] = base * diff[dif]
    if not weights:
        raise ValueError("no framework cells match the requested filters")
    z = sum(weights.values())
    return {k: v / z for k, v in weights.items()}
