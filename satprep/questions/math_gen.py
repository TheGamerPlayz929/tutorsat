import math
from fractions import Fraction

from .base import GenerationError, build_choices, fmt_number
from .difficulty import DifficultyProfile

TRIPLES = [(3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25), (9, 40, 41)]


def _poly(coeffs, var="x"):
    parts = []
    power = len(coeffs) - 1
    for c in coeffs:
        if c != 0:
            mag = abs(c)
            piece = f"{var}^{power}" if power > 1 else (var if power == 1 else "")
            if not parts:
                lead = f"-{piece}" if c < 0 else (f"{mag}{piece}" if piece else str(mag))
                if c < 0 and not piece:
                    lead = str(-mag)
                elif c < 0:
                    lead = f"-{mag}{piece}"
                else:
                    lead = f"{mag}{piece}" if piece else str(mag)
                parts.append(lead)
            else:
                op = "-" if c < 0 else "+"
                body = f"{mag}{piece}" if piece else str(mag)
                parts.append(f" {op} {body}")
        power -= 1
    return "".join(parts) if parts else "0"


def _pick(rng, lo, hi, exclude=()):
    while True:
        v = rng.randint(lo, hi)
        if v not in exclude:
            return v


def gen_linear_eq_1v(rng, difficulty):
    x = _pick(rng, -6, 8, exclude=(0,))
    if difficulty == "easy":
        a = _pick(rng, 2, 9)
        b = _pick(rng, -9, 9)
        c = a * x + b
        prompt = f"If {a}x + {b} = {c}, what is the value of x?"
        steps = f"Subtract {b}: {a}x = {c - b}. Divide by {a}: x = {x}."
    elif difficulty == "medium":
        p = _pick(rng, 2, 6)
        q = _pick(rng, -8, 8)
        r = p * (x + q)
        prompt = f"If {p}(x + {q}) = {r}, what is the value of x?"
        steps = f"Divide both sides by {p}: x + {q} = {x + q}. Subtract {q}: x = {x}."
    else:
        a = _pick(rng, 2, 9)
        c = _pick(rng, 2, 9, exclude=(a,))
        b = _pick(rng, -9, 9)
        d = a * x + b - c * x
        prompt = f"If {a}x + {b} = {c}x + {d}, what is the value of x?"
        steps = (f"Subtract {c}x from both sides: {a - c}x + {b} = {d}. Subtract {b}: "
                 f"{a - c}x = {(a - c) * x}. Divide by {a - c}: x = {x}.")
    correct = str(x)
    distract = [x + 1, x - 1, -x, x + 2]
    choices, idx = build_choices(rng, correct, [fmt_number(v) for v in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": steps}


def gen_linear_functions(rng, difficulty):
    fname = rng.choice(["f", "g", "h"])
    if difficulty == "easy":
        m = _pick(rng, -6, 6, exclude=(0,))
        b = _pick(rng, -8, 8)
        k = _pick(rng, -4, 5)
        val = m * k + b
        prompt = f"Let {fname}(x) = {_poly([m, b])}. What is {fname}({k})?"
        correct = fmt_number(val)
        distract = [fmt_number(m * b + k), fmt_number(m * k - b), fmt_number(k * (m + b))]
        expl = (f"Substitute x = {k}: {fname}({k}) = {m}({k}) + ({b}) = {val}.")
    elif difficulty == "medium":
        x1 = _pick(rng, -5, 5)
        x2 = x1 + _pick(rng, 1, 5)
        m = _pick(rng, -4, 4, exclude=(0,))
        y1 = _pick(rng, -6, 6)
        y2 = y1 + m * (x2 - x1)
        prompt = (f"A line passes through ({x1}, {y1}) and ({x2}, {y2}). "
                  f"What is the slope of the line?")
        correct = fmt_number(m)
        distract = [fmt_number(-m), fmt_number(Fraction(x2 - x1, y2 - y1)) if y2 != y1 else "-1",
                    fmt_number(y2 - y1)]
        expl = f"Slope = ({y2} − ({y1})) / ({x2} − ({x1})) = {y2 - y1} / {x2 - x1} = {m}."
    else:
        # Extrapolate: given f at two inputs, find f at a third
        x1 = _pick(rng, -4, 3)
        x2 = x1 + _pick(rng, 1, 4)
        x3 = x2 + _pick(rng, 1, 4)
        m = _pick(rng, -5, 5, exclude=(0,))
        b = _pick(rng, -8, 8)
        y1, y2, y3 = m * x1 + b, m * x2 + b, m * x3 + b
        prompt = (f"The function {fname} is linear. If {fname}({x1}) = {y1} and "
                  f"{fname}({x2}) = {y2}, what is {fname}({x3})?")
        correct = fmt_number(y3)
        distract = [fmt_number(y2 + (x3 - x2)), fmt_number(y2 - m * (x3 - x2)),
                    fmt_number(y1 + m * x3), fmt_number(y3 + 2 * m)]
        expl = (f"Slope = ({y2} − {y1}) / ({x2} − {x1}) = {m}. Then "
                f"{fname}({x3}) = {y2} + {m}({x3} − {x2}) = {y3}.")
    choices, idx = build_choices(rng, correct, [d for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_systems_linear(rng, difficulty):
    if difficulty == "hard":
        # Ask for a combination (x + y or similar), not the ordered pair
        span = 5
        xs = _pick(rng, -span, span, exclude=(0,))
        ys = _pick(rng, -span, span, exclude=(0, xs))
        while True:
            a, b = _pick(rng, -5, 5, exclude=(0,)), _pick(rng, -5, 5, exclude=(0,))
            c, d = _pick(rng, -5, 5, exclude=(0,)), _pick(rng, -5, 5, exclude=(0,))
            if a * d - b * c != 0:
                break
        e1, e2 = a * xs + b * ys, c * xs + d * ys
        line1 = f"{a}x {'+' if b >= 0 else '-'} {abs(b)}y = {e1}"
        line2 = f"{c}x {'+' if d >= 0 else '-'} {abs(d)}y = {e2}"
        target = rng.choice([("x + y", xs + ys), ("x − y", xs - ys)])
        prompt = (f"In the system {line1} and {line2}, what is the value of "
                  f"{target[0]}?")
        correct = str(target[1])
        distract = [str(xs), str(ys), str(xs * ys), str(-(target[1]))]
        expl = (f"Solving simultaneously gives x = {xs} and y = {ys}, so "
                f"{target[0]} = {target[1]}.")
    else:
        span = 4 if difficulty == "easy" else 6
        xs = _pick(rng, -span, span, exclude=(0,))
        ys = _pick(rng, -span, span, exclude=(0,))
        while True:
            a, b = _pick(rng, -4, 4, exclude=(0,)), _pick(rng, -4, 4, exclude=(0,))
            c, d = _pick(rng, -4, 4, exclude=(0,)), _pick(rng, -4, 4, exclude=(0,))
            if a * d - b * c != 0:
                break
        e1, e2 = a * xs + b * ys, c * xs + d * ys
        line1 = f"{a}x {'+' if b >= 0 else '-'} {abs(b)}y = {e1}"
        line2 = f"{c}x {'+' if d >= 0 else '-'} {abs(d)}y = {e2}"
        prompt = (f"The system of equations {line1} and {line2} is graphed in the "
                  f"xy-plane. What is the (x, y) solution to the system?")
        correct = f"({xs}, {ys})"
        distract = [f"({ys}, {xs})", f"({-xs}, {ys})", f"({xs}, {-ys})", f"({-xs}, {-ys})"]
        expl = (f"Solving simultaneously gives x = {xs} and y = {ys}; "
                f"checking: {a}({xs}) {'+' if b >= 0 else '-'} {abs(b)}({ys}) = {e1}.")
    choices, idx = build_choices(rng, correct, distract)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_linear_inequalities(rng, difficulty):
    if difficulty == "hard":
        a = _pick(rng, 2, 6)
        num = _pick(rng, -9, 9)
        den = _pick(rng, 2, 5)
        b = den * _pick(rng, -6, 6)
        c = a * num + b
        op = rng.choice(["<", ">"])
        frac = Fraction(num, den)
        prompt = f"Which inequality represents the solution to {a}x + {b} {op} {c}?"
        correct = f"x {op} {frac.numerator}/{frac.denominator}"
        flipped = f"x {'>' if op == '<' else '<'} {frac.numerator}/{frac.denominator}"
        distract = [flipped, f"x {op} {num}", f"x {'>' if op == '<' else '<'} {c}",
                    f"x {op} {num + 1}"]
        expl = (f"Subtract {b}: {a}x {op} {c - b}. Divide by {a}: "
                f"x {op} {frac.numerator}/{frac.denominator}.")
    else:
        a = _pick(rng, 2, 8)
        if difficulty == "medium" and rng.random() < 0.5:
            a = -a
        x = _pick(rng, -6, 6, exclude=(0,))
        b = _pick(rng, -8, 8)
        c = a * x + b
        op = rng.choice(["\u2264", "\u2265"])
        oop = "\u2264" if a > 0 else "\u2265"
        iop = "\u2264" if a < 0 else "\u2265"
        prompt = f"Which inequality represents the solution to {a}x + {b} {op} {c}?"
        correct = f"x {oop} {x}"
        distract = [f"x {iop} {x}", f"x {oop} {x + 1}", f"x {'>' if oop == '\u2264' else '<'} {x}",
                    f"x {oop} {-x}"]
        expl = (f"Subtract {b}: {a}x {op} {c - b}. Dividing by {a}"
                + (" flips" if a < 0 else " keeps") + f" the sign: x {oop} {x}.")
    choices, idx = build_choices(rng, correct, distract)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_linear_word_problems(rng, difficulty):
    fee = _pick(rng, 10, 60, exclude=(0,))
    rate = _pick(rng, 3, 12)
    units = rng.choice(["dollars", "credits"])
    sym = "$" if units == "dollars" else ""
    if difficulty == "easy":
        n = _pick(rng, 2, 10)
        total = fee + rate * n
        prompt = (f"A studio charges a one-time fee of {sym}{fee} plus {sym}{rate} "
                  f"per class. If a student pays a total of {sym}{total}, how many "
                  f"classes did the student take?")
        ans = str(n)
        distract = [n + 1, n - 1, round(total / rate), n + 2]
        expl = (f"Total cost = {fee} + {rate}n = {total}, so {rate}n = {total - fee} "
                f"and n = {ans}.")
        correct = ans
        profile = DifficultyProfile(
            reasoning_steps=1, decision_points=0,
            representation_translation=False, concept_interaction=False,
            distractor_quality=1, information_density=0, computation_burden=0,
            directness=0, constraint_complexity=False,
        )
    elif difficulty == "medium":
        # §3.1-3.5: requires translating offset model (free sessions) and
        # incorporating constraint: first k classes included.
        k_free = _pick(rng, 2, 4)
        n_total = _pick(rng, 6, 14)
        n_paid = n_total - k_free
        total = fee + rate * n_paid
        prompt = (f"A studio charges a one-time fee of {sym}{fee}. The first "
                  f"{k_free} classes are included, and each additional class costs "
                  f"{sym}{rate}. A student pays a total of {sym}{total}. How many "
                  f"classes did the student attend in total?")
        correct = str(n_total)
        distract = [str(n_paid), str(n_total - 1), str(n_total + 1), str(round(total / rate))]
        expl = (f"Paid classes m: {fee}+{rate}m={total} → {rate}m={total - fee} → m={n_paid}. "
                f"Total classes = m+{k_free}={n_total}.")
        profile = DifficultyProfile(
            reasoning_steps=2, decision_points=1,
            representation_translation=True, concept_interaction=False,
            distractor_quality=2, information_density=1, computation_burden=0,
            directness=1, constraint_complexity=True,
        )
    else:
        # Two-plan comparison: after how many sessions do plans cost the same?
        # Hard: non-obvious model construction for both plans + break-even reasoning
        rate_a = _pick(rng, 6, 12)
        rate_b = _pick(rng, 3, rate_a - 2)
        n_eq = _pick(rng, 4, 12)
        fee_a = _pick(rng, 10, 40)
        fee_b = fee_a + (rate_a - rate_b) * n_eq
        prompt = (f"Plan A charges a {sym}{fee_a} signup fee plus {sym}{rate_a} per "
                  f"session. Plan B charges a {sym}{fee_b} signup fee plus "
                  f"{sym}{rate_b} per session. After how many sessions do the two "
                  f"plans cost the same amount?")
        correct = f"{n_eq} sessions"
        distract = [n_eq - 1, n_eq + 1, n_eq + 2, max(2, n_eq - 2)]
        distract = [str(d) + " sessions" for d in distract]
        expl = (f"{fee_a} + {rate_a}n = {fee_b} + {rate_b}n gives "
                f"{rate_a - rate_b}n = {fee_b - fee_a}, so n = {fee_b - fee_a} ÷ "
                f"{rate_a - rate_b} = {n_eq}.")
        profile = DifficultyProfile(
            reasoning_steps=3, decision_points=2,
            representation_translation=True, concept_interaction=True,
            distractor_quality=2, information_density=1, computation_burden=0,
            directness=2, constraint_complexity=True,
        )
    choices, idx = build_choices(rng, correct, distract)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl, "difficulty_profile": profile.__dict__}


def gen_equivalent_expressions(rng, difficulty):
    if difficulty == "easy":
        a = _pick(rng, -6, 6, exclude=(0,))
        b = _pick(rng, -6, 6, exclude=(0,))
        prompt = f"Which expression is equivalent to (x + {a})(x + {b})?"
        coeffs = [1, a + b, a * b]
        correct = _poly(coeffs)
        distract = [_poly([1, a * b, a + b]), _poly([1, a + b, -a * b]),
                    _poly([1, a - b, a * b])]
        expl = (f"FOIL: x^2 + ({b}x) + ({a}x) + ({a})({b}) = {correct}.")
    elif difficulty == "medium":
        ea = _pick(rng, 2, 7)
        eb = _pick(rng, 2, 7)
        ec = _pick(rng, 1, min(ea + eb - 1, 9))
        exp = ea + eb - ec
        prompt = f"Which expression is equivalent to (x^{ea} \u00b7 x^{eb}) / x^{ec}?"
        correct = f"x^{exp}"
        distract = [f"x^{ea * eb - ec}", f"x^{ea + eb + ec}", f"x^{ea - eb - ec}",
                    f"x^{exp + 1}"]
        expl = (f"Add exponents in the numerator: x^{ea + eb}. Then subtract: "
                f"x^{ea + eb} \u00f7 x^{ec} = x^{exp}.")
    else:
        family = rng.choice(["diff_squares", "binomial_square", "product_power"])
        if family == "diff_squares":
            a = _pick(rng, 2, 12)
            prompt = f"Which expression is equivalent to (x + {a})(x - {a})?"
            correct = _poly([1, 0, -(a * a)])
            distract = [_poly([1, 0, a * a]), _poly([1, 2 * a, a * a]),
                        _poly([1, -2 * a, a * a])]
            expl = f"Difference of squares: (x + {a})(x - {a}) = x^2 - {a * a}."
        elif family == "binomial_square":
            a = _pick(rng, 2, 9)
            negated = rng.random() < 0.5
            term = f"x - {a}" if negated else f"x + {a}"
            b = -a if negated else a
            prompt = f"Which expression is equivalent to ({term})^2?"
            correct = _poly([1, 2 * b, b * b])
            distract = [_poly([1, 0, b * b]), _poly([1, b, b * b]),
                        _poly([1, 2 * b, 2 * b * b])]
            expl = (f"Square the binomial: ({term})^2 = x^2 {'+' if b >= 0 else '-'} "
                    f"{abs(2 * b)}x {'+' if b * b >= 0 else '-'} "
                    f"{abs(b * b)} = {correct}.")
        else:
            ea = _pick(rng, 2, 8)
            eb = _pick(rng, 2, 8)
            prompt = f"Which expression is equivalent to (x^{ea})^{eb}?"
            exp_val = ea * eb
            correct = f"x^{exp_val}"
            distract = [f"x^{ea + eb}", f"{exp_val}x",
                        f"x^{exp_val + 1}", f"{ea * eb}\u00b7x^{eb}"]
            expl = (f"Raise a power to a power by multiplying exponents: "
                    f"(x^{ea})^{eb} = x^{exp_val}.")
    choices, idx = build_choices(rng, correct, distract)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_nonlinear_equations(rng, difficulty):
    if difficulty == "easy":
        r1 = _pick(rng, 1, 6)
        r2 = _pick(rng, -6, 6, exclude=(r1,))
        p = -(r1 + r2)
        q = r1 * r2
        prompt = f"If x^2 + {p}x + {q} = 0, what is the larger solution?"
        correct = str(max(r1, r2))
        distract = [min(r1, r2), -max(r1, r2), max(r1, r2) + 1, p]
        expl = (f"Factor: (x - {r1})(x - {r2}) = 0, so x = {r1} or x = {r2}; "
                f"the larger is {max(r1, r2)}.")
        profile = DifficultyProfile(
            reasoning_steps=1, decision_points=0,
            representation_translation=False, concept_interaction=False,
            distractor_quality=1, information_density=0, computation_burden=0,
            directness=0, constraint_complexity=False,
        )
    elif difficulty == "medium":
        variant = rng.choice(["radical", "leading_coeff"])
        if variant == "radical":
            k = _pick(rng, 2, 6)
            m = _pick(rng, -8, 8)
            n = _pick(rng, 1, 5)
            rem = n * n - m
            while k <= 0 or rem % k != 0:
                k = _pick(rng, 2, 6)
                m = _pick(rng, -8, 8)
                rem = n * n - m
            x = rem // k
            prompt = f"If \u221a({k}x + {m}) = {n}, what is the value of x?"
            correct = str(x)
            distract = [x + 1, n * n - m, x // k if k != 1 and x % k == 0 else x - 1,
                        n * n]
            expl = (f"Square both sides: {k}x + {m} = {n * n}. So {k}x = {rem} and "
                    f"x = {x}. Check: \u221a({k}\u00b7{x} + {m}) = {n}.")
            profile = DifficultyProfile(
                reasoning_steps=2, decision_points=1,
                representation_translation=False, concept_interaction=False,
                distractor_quality=1, information_density=0, computation_burden=0,
                directness=1, constraint_complexity=False,
            )
        else:  # leading_coeff
            r1 = _pick(rng, -5, 5, exclude=(0,))
            r2 = _pick(rng, -5, 5, exclude=(r1, 0))
            a = _pick(rng, 2, 4)
            b = -a * (r1 + r2)
            c = a * r1 * r2
            prompt = f"What is the larger solution to {_poly([a, b, c])} = 0?"
            correct = str(max(r1, r2))
            distract = [min(r1, r2), -max(r1, r2), max(r1, r2) + 1, a]
            expl = (f"Divide by {a} and factor: (x - {r1})(x - {r2}) = 0, giving "
                    f"x = {r1} or x = {r2}. The larger solution is {max(r1, r2)}.")
            profile = DifficultyProfile(
                reasoning_steps=2, decision_points=1,
                representation_translation=False, concept_interaction=False,
                distractor_quality=1, information_density=0, computation_burden=1,
                directness=0, constraint_complexity=False,
            )
    else:
        # Hard: ONLY genuinely hard variants — trivial (x+p)^2=q removed (§5, Ex C)
        variant = rng.choice(["quadratic_formula", "contextual", "u_substitution"])
        if variant == "quadratic_formula":
            # Bare quadratic with irrational roots — direct, not hard; will be demoted by gate
            while True:
                a = _pick(rng, 1, 5)
                b = _pick(rng, -8, 8)
                c = _pick(rng, -8, 8)
                disc = b * b - 4 * a * c
                if disc > 0 and int(disc ** 0.5) ** 2 != disc:
                    break
            import math
            r1 = (-b + math.sqrt(disc)) / (2 * a)
            r2 = (-b - math.sqrt(disc)) / (2 * a)
            correct = fmt_number(max(r1, r2))
            wrong1 = fmt_number(min(r1, r2))
            wrong2 = fmt_number((-b + math.sqrt(abs(disc))) / (2 * a)) if disc > 0 else fmt_number(-b / (2 * a))
            wrong3 = fmt_number(-b / a)
            prompt = f"What is the larger solution to {_poly([a, b, c])} = 0?"
            distract = [wrong1, wrong2, wrong3]
            expl = (f"Quadratic formula: x = ({-b} \u00b1 \u221a({disc})) / {2*a}. "
                    f"The larger root is {correct}.")
            profile = DifficultyProfile(
                reasoning_steps=2, decision_points=1,
                representation_translation=False, concept_interaction=False,
                distractor_quality=1, information_density=0, computation_burden=1,
                directness=0, constraint_complexity=False,
            )
        elif variant == "contextual":
            # Rectangle area with length = mult*width + k, area given — requires
            # words→equation translation, constraint (positive root), interaction geometry+algebra
            mult = rng.choice([2, 3])
            k = _pick(rng, 1, 5)
            w = _pick(rng, 3, 9)
            area = w * (mult * w + k)
            length = mult * w + k
            prompt = (f"A rectangle has length {k} feet more than {mult} times its width. "
                      f"Its area is {area} square feet. What is the width of the rectangle, in feet?")
            correct = str(w)
            distract = [str(length), str(w + 1), str(area // w if w != 0 else w + 2), str(-w)]
            expl = (f"Let width = w, length = {mult}w+{k}. Area: w({mult}w+{k})={area} → "
                    f"{mult}w²+{k}w-{area}=0 → w={w} (positive root; negative root rejected).")
            profile = DifficultyProfile(
                reasoning_steps=3, decision_points=2,
                representation_translation=True, concept_interaction=True,
                distractor_quality=2, information_density=1, computation_burden=0,
                directness=2, constraint_complexity=True,
            )
        else:  # u_substitution
            # x^4 + bx^2 + c = 0 form
            u1 = _pick(rng, 1, 9)
            u2 = _pick(rng, 1, 9)
            while u1 == u2:
                u2 = _pick(rng, 1, 9)
            b = -(u1 + u2)
            c = u1 * u2
            import math
            r1 = math.sqrt(max(u1, u2))
            r2 = -math.sqrt(max(u1, u2))
            correct = fmt_number(max(r1, r2))
            wrong1 = fmt_number(min(r1, r2))
            wrong2 = fmt_number(math.sqrt(min(u1, u2)))
            wrong3 = fmt_number(max(u1, u2))
            prompt = f"What is the largest real solution to x\u2074 + {b}x\u00b2 + {c} = 0?"
            distract = [wrong1, wrong2, wrong3]
            expl = (f"Substitute u = x\u00b2: u\u00b2 + {b}u + {c} = 0. "
                    f"Roots: u = {u1}, {u2}. Real x = \u00b1\u221a{max(u1, u2)}. "
                    f"Largest: {correct}.")
            profile = DifficultyProfile(
                reasoning_steps=3, decision_points=2,
                representation_translation=True, concept_interaction=True,
                distractor_quality=2, information_density=1, computation_burden=0,
                directness=2, constraint_complexity=True,
            )
    choices, idx = build_choices(rng, correct, [str(d) if isinstance(d, (int, float)) else d
                                                for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl, "difficulty_profile": profile.__dict__}


def gen_nonlinear_systems(rng, difficulty):
    if difficulty == "easy":
        t1 = _pick(rng, -2, 1)
        t2 = t1 + _pick(rng, 1, 3)
        c = _pick(rng, -3, 3)
        m = t1 + t2
        k = c - t1 * t2
        y1, y2 = t1 * t1 + c, t2 * t2 + c
        prompt = (f"The equations y = x\u00b2 + {c} and y = {m}x {'+' if k >= 0 else '-'} "
                  f"{abs(k)} are graphed in the xy-plane. The graphs intersect at two "
                  f"points. What is the y-coordinate of the point of intersection with "
                  f"the greater x-coordinate?")
        correct = str(y2)
        distract = [y1, t2, y2 - y1 if y2 != y1 else y2 + 1, t2 * t2 - c]
        expl = (f"Set x\u00b2 + {c} = {m}x {'+' if k >= 0 else '-'} {abs(k)}, which factors "
                f"as (x - {t1})(x - {t2}) = 0. At x = {t2}: y = {t2}\u00b2 + {c} = {y2}.")
    elif difficulty == "medium":
        t1 = _pick(rng, -4, 2)
        t2 = t1 + _pick(rng, 1, 5)
        c = _pick(rng, -5, 5)
        m = t1 + t2
        k = c - t1 * t2
        y1, y2 = t1 * t1 + c, t2 * t2 + c
        prompt = (f"The equations y = x\u00b2 + {c} and y = {m}x {'+' if k >= 0 else '-'} "
                  f"{abs(k)} are graphed in the xy-plane. The graphs intersect at two "
                  f"points. What is the y-coordinate of the point of intersection with "
                  f"the greater x-coordinate?")
        correct = str(y2)
        distract = [y1, t2, y2 - y1 if y2 != y1 else y2 + 1, t2 * t2 - c]
        expl = (f"Set x\u00b2 + {c} = {m}x {'+' if k >= 0 else '-'} {abs(k)}, which factors "
                f"as (x - {t1})(x - {t2}) = 0. At x = {t2}: y = {t2}\u00b2 + {c} = {y2}.")
    else:
        # Sum of both y-coordinates: requires finding both intersections
        t1 = _pick(rng, -4, 2)
        t2 = t1 + _pick(rng, 2, 5)
        c = _pick(rng, -5, 5)
        m = t1 + t2
        k = c - t1 * t2
        y1, y2 = t1 * t1 + c, t2 * t2 + c
        total_y = y1 + y2
        prompt = (f"The equations y = x\u00b2 + {c} and y = {m}x {'+' if k >= 0 else '-'} "
                  f"{abs(k)} are graphed in the xy-plane. The graphs intersect at two "
                  f"points. What is the sum of the y-coordinates of the two points of "
                  f"intersection?")
        correct = str(total_y)
        distract = [y2, y1, t1 + t2, total_y - c]
        expl = (f"Set x\u00b2 + {c} = {m}x {'+' if k >= 0 else '-'} {abs(k)}, which factors "
                f"as (x - {t1})(x - {t2}) = 0, so x = {t1} or {t2}. The y-values are "
                f"{y1} and {y2}, and their sum is {total_y}.")
    choices, idx = build_choices(rng, correct, [str(d) for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_nonlinear_functions(rng, difficulty):
    if difficulty == "easy":
        b = _pick(rng, -5, 5)
        c = _pick(rng, -6, 6)
        k = _pick(rng, -3, 3)
        val = k * k + b * k + c
        prompt = f"If f(x) = x\u00b2 + {b}x + {c}, what is f({k})?"
        correct = fmt_number(val)
        distract = [fmt_number(k * k + b + c), fmt_number(k * (k + b)), fmt_number(val + 2),
                    fmt_number(-(val))]
        expl = (f"f({k}) = ({k})\u00b2 + ({b})({k}) + {c} = {k * k} + {b * k} + {c} = {val}.")
    elif difficulty == "medium":
        h = _pick(rng, -5, 5, exclude=(0,))
        kk = _pick(rng, -6, 6)
        a = _pick(rng, 1, 3)
        prompt = (f"The function f(x) = {'' if a == 1 else a}(x {'-' if h > 0 else '+'} "
                  f"{abs(h)})\u00b2 {'+' if kk >= 0 else '-'} {abs(kk)} is graphed in the "
                  f"xy-plane. What is the vertex of the graph?")
        correct = f"({h}, {kk})"
        distract = [f"({-h}, {kk})", f"({h}, {-kk})", f"({kk}, {h})", f"({-h}, {-kk})"]
        expl = (f"For f(x) = a(x - h)\u00b2 + k the vertex is (h, k), here "
                f"({h}, {kk}).")
    else:
        # Vertex from standard form: requires x = -b/(2a)
        a = _pick(rng, 1, 3)
        h = _pick(rng, -5, 5, exclude=(0,))
        b = -2 * a * h
        kk = _pick(rng, -6, 6)
        prompt = (f"The function f(x) = {a}x\u00b2 {'+' if b >= 0 else '-'} "
                  f"{abs(b)}x {'+' if kk >= 0 else '-'} {abs(kk)} is graphed in the "
                  f"xy-plane. What is the vertex of the graph?")
        correct = f"({h}, {kk})"
        distract = [f"({-h}, {kk})", f"({h}, {-kk})", f"({-h}, {-kk})", f"({kk}, {h})"]
        expl = (f"The x-coordinate of the vertex is -b/(2a) = {-b}/{2 * a} = {h}. "
                f"Then f({h}) = {a}({h})\u00b2 {'+' if b >= 0 else '-'} {abs(b)}({h}) "
                f"{'+' if kk >= 0 else '-'} {abs(kk)} = {kk}, so the vertex is "
                f"({h}, {kk}).")
    choices, idx = build_choices(rng, correct, [d for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_ratios_rates(rng, difficulty):
    if difficulty == "easy":
        a = _pick(rng, 2, 7)
        b = _pick(rng, 2, 7, exclude=(a,))
        scale = _pick(rng, 2, 6)
        amt_a = a * scale
        amt_b = b * scale
        ing_a, ing_b = rng.sample(["flour", "sugar", "oats", "honey", "milk"], 2)
        prompt = (f"A recipe uses {a} cups of {ing_a} for every {b} cups of {ing_b}. "
                  f"If a baker uses {amt_a} cups of {ing_a}, how many cups of {ing_b} "
                  f"are needed?")
        correct = str(amt_b)
        distract = [amt_a, amt_b + b, scale, amt_b + 2]
        expl = (f"{amt_a} \u00f7 {a} = {scale} batches, so {ing_b} needed = {b} \u00d7 "
                f"{scale} = {amt_b}.")
        profile = DifficultyProfile(
            reasoning_steps=1, decision_points=0,
            representation_translation=False, concept_interaction=False,
            distractor_quality=1, information_density=0, computation_burden=0,
            directness=0, constraint_complexity=False,
        )
    elif difficulty == "medium":
        # Constant rate: find distance at a second quantity
        mpg = _pick(rng, 15, 40, exclude=(0,))
        g1 = _pick(rng, 4, 8)
        g2 = g1 + _pick(rng, 2, 5)
        miles1 = mpg * g1
        miles2 = mpg * g2
        prompt = (f"A car travels {miles1} miles on {g1} gallons of gasoline. At the "
                  f"same rate, how many miles can the car travel on {g2} gallons?")
        correct = str(miles2)
        distract = [miles1, miles2 + mpg, miles2 - mpg, mpg * g1 * g2 // max(g1 + g2, 1)]
        expl = (f"Rate = {miles1} \u00f7 {g1} = {mpg} miles per gallon. On {g2} "
                f"gallons: {mpg} \u00d7 {g2} = {miles2} miles.")
        profile = DifficultyProfile(
            reasoning_steps=2, decision_points=1,
            representation_translation=True, concept_interaction=False,
            distractor_quality=1, information_density=0, computation_burden=0,
            directness=1, constraint_complexity=False,
        )
    else:
        # Combined work rates — requires both rates, sum, then scale
        r_a = _pick(rng, 15, 40)
        r_b = _pick(rng, 15, 40)
        t_a = _pick(rng, 3, 6)
        t_b = _pick(rng, 4, 8)
        parts_a, parts_b = r_a * t_a, r_b * t_b
        t_tot = _pick(rng, 5, 9)
        combined = r_a + r_b
        total = combined * t_tot
        unit = rng.choice(["widgets", "parts", "cards"])
        prompt = (f"Machine A assembles {parts_a} {unit} in {t_a} minutes, and "
                  f"Machine B assembles {parts_b} {unit} in {t_b} minutes. Working "
                  f"together at these rates, how many {unit} can the two machines "
                  f"assemble in {t_tot} minutes?")
        correct = str(total)
        distract = [parts_a + parts_b, r_a * t_tot, r_b * t_tot, total + combined]
        expl = (f"Machine A: {parts_a} \u00f7 {t_a} = {r_a} per minute; Machine B: "
                f"{parts_b} \u00f7 {t_b} = {r_b} per minute. Together: {combined} per "
                f"minute \u00d7 {t_tot} minutes = {total}.")
        profile = DifficultyProfile(
            reasoning_steps=3, decision_points=2,
            representation_translation=True, concept_interaction=True,
            distractor_quality=2, information_density=1, computation_burden=0,
            directness=2, constraint_complexity=True,
        )
    choices, idx = build_choices(rng, correct, [str(d) for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl, "difficulty_profile": profile.__dict__}


def gen_percentages(rng, difficulty):
    if difficulty == "easy":
        p = rng.choice([10, 20, 25, 50])
        n = rng.randint(2, 40) * (100 // math.gcd(p, 100))
        part = n * p / 100
        prompt = f"What is {p}% of {int(n)}?"
        correct = fmt_number(part)
        distract = [fmt_number(part * 2), fmt_number(part / 2), fmt_number(n - part),
                    fmt_number(part + 10)]
        expl = f"{p}% of {int(n)} = {p}/100 \u00d7 {int(n)} = {fmt_number(part)}."
    elif difficulty == "medium":
        p = rng.choice([10, 20, 25, 50])
        price = rng.randint(2, 30) * (100 // math.gcd(p, 100))
        new_price = price * (1 - p / 100)
        prompt = (f"A jacket priced at ${int(price)} is discounted by {p}%. "
                  f"What is the sale price of the jacket?")
        correct = f"${fmt_number(new_price)}"
        distract = [f"${fmt_number(price * p / 100)}",
                    f"${fmt_number(price * (1 + p / 100))}",
                    f"${fmt_number(new_price * 2)}",
                    f"${fmt_number(price - p)}"]
        expl = (f"Discount = {p}% of {price} = {fmt_number(price * p / 100)}. "
                f"Sale price = {price} - {fmt_number(price * p / 100)} = "
                f"{fmt_number(new_price)}.")
    else:
        p = rng.choice([25, 50, 100])
        orig = rng.randint(2, 30) * (100 // math.gcd(p, 100))
        after = orig * (1 + p / 100)
        prompt = (f"After a {p}% increase, the price of a laptop bag is "
                  f"${fmt_number(after)}. What was the original price?")
        correct = f"${fmt_number(orig)}"
        distract = [f"${fmt_number(after * (1 - p / 100))}",
                    f"${fmt_number(after - p)}",
                    f"${fmt_number(orig * 2)}",
                    f"${fmt_number(after / (1 + p / 200))}"]
        expl = (f"Original \u00d7 (1 + {p}/100) = {fmt_number(after)}, so original = "
                f"{fmt_number(after)} \u00f7 {fmt_number(1 + p / 100)} = {orig}.")
    choices, idx = build_choices(rng, correct, [d for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_one_variable_data(rng, difficulty):
    if difficulty == "easy":
        n = 5
        vals = [_pick(rng, 1, 20) for _ in range(n - 1)]
        target_mean = _pick(rng, 4, 15)
        total = target_mean * n
        missing = total - sum(vals)
        data = sorted(vals + [missing])
        prompt = (f"The list {data[0]}, {data[1]}, {data[2]}, {data[3]}, and m has a "
                  f"mean of {target_mean}. What is the value of m?")
        correct = str(missing)
        distract = [target_mean, missing + 1, missing - 1, total - missing]
        expl = (f"Sum = mean \u00d7 count = {target_mean} \u00d7 {n} = {total}. "
                f"Missing value = {total} - {sum(vals)} = {missing}.")
    else:
        n = 7 if difficulty == "medium" else 9
        vals = sorted(_pick(rng, 1, 40) for _ in range(n))
        med = vals[n // 2]
        word = "median"
        if difficulty == "hard":
            mean = sum(vals) / n
            word = rng.choice(["median", "mean"])
            med = fmt_number(med) if word == "median" else fmt_number(round(mean, 2))
            correct = str(med)
            prompt = f"What is the {word} of the list {vals}?"
            if word == "mean":
                distract = [fmt_number(vals[n // 2]),
                            fmt_number(round(mean + 0.5, 2)),
                            fmt_number(vals[-1] - vals[0]),
                            fmt_number(round(sum(vals) / (n - 1), 2))]
                expl = (f"Mean = sum \u00f7 count = {sum(vals)} \u00f7 {n} = "
                        f"{fmt_number(round(mean, 2))}.")
            else:
                distract = [str(vals[0]), str(vals[-1]), str(vals[1]), str(vals[n // 2] + 1)]
                expl = (f"With {n} sorted values the median is the {n // 2 + 1}th "
                        f"value: {vals[n // 2]}.")
        else:
            correct = str(med)
            prompt = f"What is the median of the list {vals}?"
            distract = [str(vals[0]), str(vals[-1]), str(vals[1]), str(vals[n // 2] + 1)]
            expl = (f"With {n} sorted values the median is the middle ("
                    f"{n // 2 + 1}th) value: {med}.")
    choices, idx = build_choices(rng, correct, [str(d) for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_probability(rng, difficulty):
    red = _pick(rng, 1, 8)
    green = _pick(rng, 1, 8, exclude=(red,))
    blue = _pick(rng, 1, 8)
    total = red + green + blue
    if difficulty == "easy":
        frac = Fraction(red, total)
        prompt = (f"A jar contains {red} red, {green} green, and {blue} blue "
                  f"marbles. If one marble is drawn at random, what is the "
                  f"probability that it is red?")
        correct = f"{frac.numerator}/{frac.denominator}"
        distract = [f"{red}/{total - red}", f"{Fraction(green, total).numerator}/{Fraction(green, total).denominator}",
                    f"{Fraction(blue, total).numerator}/{Fraction(blue, total).denominator}",
                    f"{Fraction(total - red, total).numerator}/{Fraction(total - red, total).denominator}"]
        expl = (f"P(red) = {red} favorable / {total} possible = "
                f"{frac.numerator}/{frac.denominator}.")
    elif difficulty == "medium":
        frac = Fraction(total - blue, total)
        prompt = (f"A jar contains {red} red, {green} green, and {blue} blue "
                  f"marbles. If one marble is drawn at random, what is the "
                  f"probability that it is NOT blue?")
        correct = f"{frac.numerator}/{frac.denominator}"
        nb = Fraction(blue, total)
        distract = [f"{nb.numerator}/{nb.denominator}", f"{blue}/{total - blue}",
                    f"{Fraction(red, total).numerator}/{Fraction(red, total).denominator}",
                    f"{Fraction(total - red, total).numerator}/{Fraction(total - red, total).denominator}"]
        expl = (f"Not-blue marbles = {red} + {green} = {total - blue}. "
                f"P(not blue) = {total - blue}/{total} = "
                f"{frac.numerator}/{frac.denominator}.")
    else:
        denom = total - green
        frac = Fraction(red, denom)
        prompt = (f"A jar contains {red} red, {green} green, and {blue} blue "
                  f"marbles. Given that a drawn marble is not green, what is the "
                  f"probability that it is red?")
        correct = f"{frac.numerator}/{frac.denominator}"
        uncond = Fraction(red, total)
        distract = [f"{uncond.numerator}/{uncond.denominator}",
                    f"{red}/{total}",
                    f"{Fraction(blue, denom).numerator}/{Fraction(blue, denom).denominator}",
                    f"{Fraction(red, total - red).numerator}/{Fraction(red, total - red).denominator}"]
        expl = (f"Not-green outcomes: {total} - {green} = {denom}. Of those, {red} "
                f"are red, so the probability is {red}/{denom} = "
                f"{frac.numerator}/{frac.denominator}.")
    choices, idx = build_choices(rng, correct, [d for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_inference_studies(rng, difficulty):
    pct = rng.randrange(38, 72, 2)
    moe = rng.choice([2, 3, 4])
    if difficulty == "hard":
        # Reverse reasoning: identify the value OUTSIDE the interval
        outside = pct + moe + rng.choice([2, 3, 4])
        prompt = (f"A survey of a random sample of voters in a county found that "
                  f"{pct}% support a proposal, with a margin of error of \u00b1{moe} "
                  f"percentage points. Which of the following is NOT a plausible "
                  f"value for the percentage of all voters in the county who support "
                  f"the proposal?")
        correct = f"{outside}%"
        distract = [f"{pct}%", f"{pct - moe}%", f"{pct + moe}%"]
        expl = (f"The margin of error gives a plausible range of {pct - moe}% to "
                f"{pct + moe}%. The value {outside}% falls outside that range, so it "
                f"is not plausible.")
    else:
        correct = (f"It is plausible that between {pct - moe}% and {pct + moe}% of all "
                   f"voters in the county support the proposal")
        distract = [f"Exactly {pct}% of all voters support the proposal",
                    f"No more than {pct - moe}% of all voters support the proposal",
                    f"At least {pct + moe}% of all voters support the proposal",
                    rng.choice(["The sampling was flawed, so no conclusion can be drawn",
                                "The survey proves that a majority of every age group "
                                "supports the proposal"])]
        prompt = (f"A survey of a random sample of voters in a county found that {pct}% "
                  f"support a proposal, with a margin of error of \u00b1{moe} percentage "
                  f"points. Which conclusion is most supported by the survey results?")
        expl = (f"A margin of error of \u00b1{moe} points means the true population value "
                f"most plausibly lies between {pct - moe}% and {pct + moe}%; sample results "
                f"do not pin down an exact value.")
    choices, idx = build_choices(rng, correct, distract)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_units_conversion(rng, difficulty):
    if difficulty == "easy":
        km = rng.randint(2, 25)
        meters = km * 1000
        prompt = f"A trail is {km} kilometers long. How many meters long is the trail?"
        correct = fmt_number(meters)
        distract = [fmt_number(km * 100), fmt_number(km * 10000), fmt_number(km),
                    fmt_number(meters + 500)]
        expl = f"1 kilometer = 1,000 meters, so {km} km = {km} \u00d7 1000 = {meters:,} m."
    elif difficulty == "medium":
        kmh = rng.randrange(30, 121, 3)
        mpm = kmh * 1000 / 60
        prompt = (f"A train travels at {kmh} kilometers per hour. What is its speed "
                  f"in meters per minute?")
        correct = fmt_number(int(round(mpm)))
        distract = [fmt_number(kmh * 1000), fmt_number(kmh * 50 // 3 if kmh % 6 == 0 else kmh * 60),
                    fmt_number(int(round(mpm / 2))), fmt_number(kmh * 60)]
        expl = (f"{kmh} km/h = {kmh * 1000} meters per hour. Dividing by 60 minutes "
                f"gives {int(round(mpm))} meters per minute.")
    else:
        rate = rng.randrange(6, 61, 3)
        cents_min = rate * 100 / 60
        while abs(cents_min - round(cents_min)) > 1e-9:
            rate = rng.randint(6, 30)
            cents_min = rate * 100 / 60
        prompt = (f"A consultant earns ${rate} per hour, paid in cents. What is the "
                  f"pay rate in cents per minute?")
        correct = fmt_number(int(round(cents_min)))
        distract = [fmt_number(rate * 100), fmt_number(int(round(rate * 100 / 100))),
                    fmt_number(int(round(cents_min / 2))), fmt_number(rate * 60)]
        expl = (f"${rate} = {rate * 100} cents per hour. Dividing by 60 minutes "
                f"gives {int(round(cents_min))} cents per minute.")
    choices, idx = build_choices(rng, correct, [d for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_area_volume(rng, difficulty):
    if difficulty == "easy":
        l = _pick(rng, 3, 15)
        w = _pick(rng, 2, 12)
        area = l * w
        prompt = (f"A rectangle has a length of {l} centimeters and a width of {w} "
                  f"centimeters. What is its area, in square centimeters?")
        correct = str(area)
        distract = [str(2 * (l + w)), str(area + l), str(area - w), str(l + w)]
        expl = f"Area = length \u00d7 width = {l} \u00d7 {w} = {area}."
    elif difficulty == "medium":
        base = 2 * _pick(rng, 2, 10)
        height = _pick(rng, 2, 12)
        area = base * height / 2
        prompt = (f"A triangle has a base of {base} inches and a height of {height} "
                  f"inches. What is its area, in square inches?")
        correct = fmt_number(area)
        distract = [str(base * height), str(base + height), fmt_number(area / 2),
                    str(base * height - height)]
        expl = f"Area = \u00bd \u00d7 base \u00d7 height = \u00bd \u00d7 {base} \u00d7 {height} = {fmt_number(area)}."
    else:
        l = _pick(rng, 2, 6)
        w = _pick(rng, 2, 6)
        h = _pick(rng, 2, 6)
        vol = l * w * h
        prompt = (f"A rectangular prism has a volume of {vol} cubic units. Its "
                  f"length is {l} units and its width is {w} units. What is its "
                  f"height, in units?")
        correct = str(h)
        distract = [str(vol // w if vol % w == 0 else h + 1), str(h + 1), str(h - 1),
                    str(vol - l * w)]
        expl = (f"Volume = l\u00d7w\u00d7h, so {vol} = {l}\u00d7{w}\u00d7h = "
                f"{l * w}h, giving h = {h}.")
    choices, idx = build_choices(rng, correct, [d for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_lines_angles_triangles(rng, difficulty):
    if difficulty == "easy":
        a = _pick(rng, 25, 80)
        b = _pick(rng, 25, 80, exclude=(a,))
        c = 180 - a - b
        prompt = (f"Two angles of a triangle measure {a}\u00b0 and {b}\u00b0. What is "
                  f"the measure, in degrees, of the third angle?")
        correct = str(c)
        distract = [str(abs(a - b)), str(360 - a - b), str(c + 10), str(a + b)]
        expl = f"Angle sum: 180 - {a} - {b} = {c}."
    elif difficulty == "medium":
        trip = rng.choice(TRIPLES)
        k = rng.randint(1, 4)
        a, b, hyp = trip[0] * k, trip[1] * k, trip[2] * k
        if rng.random() < 0.5:
            prompt = (f"A right triangle has legs of lengths {a} and {b}. What is the "
                      f"length of the hypotenuse?")
            correct = str(hyp)
            distract = [str(a + b), str(hyp + 2 * k), str(abs(b - a)), str(hyp - k)]
            expl = (f"a\u00b2 + b\u00b2 = {a * a} + {b * b} = {hyp * hyp}, so the "
                    f"hypotenuse is {hyp}.")
        else:
            prompt = (f"A right triangle has one leg of length {a} and a hypotenuse "
                      f"of length {hyp}. What is the length of the other leg?")
            correct = str(b)
            distract = [str(hyp - a), str(b + 2 * k), str(a + b), str(abs(hyp - b))]
            expl = (f"c\u00b2 \u2212 a\u00b2 = {hyp * hyp} \u2212 {a * a} = "
                    f"{b * b}, so the other leg is {b}.")
    else:
        a = _pick(rng, 30, 70)
        b = _pick(rng, 30, 70, exclude=(a,))
        ext = a + b
        prompt = (f"In a triangle, two interior angles measure {a}\u00b0 and {b}\u00b0. "
                  f"What is the measure of the exterior angle adjacent to the third "
                  f"interior angle, in degrees?")
        correct = str(ext)
        distract = [str(180 - ext), str(180 - a - b), str(ext + 45), str(a + b + 60)]
        expl = (f"The third interior angle is 180 - {a} - {b} = {180 - a - b}; the "
                f"exterior angle is 180 - {180 - a - b} = {ext} (equal to the sum of "
                f"the two remote interior angles).")
    choices, idx = build_choices(rng, correct, [d for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_right_triangles_trig(rng, difficulty):
    if difficulty == "hard":
        # Solve for a side given a trig ratio (reverse SOH-CAH-TOA)
        trip = rng.choice(TRIPLES)
        m = _pick(rng, 2, 6)
        opp, adj, hyp = trip[0] * m, trip[1] * m, trip[2] * m
        name = rng.choice(["sin", "tan"])
        if name == "sin":
            ratio = Fraction(trip[0], trip[2])
            prompt = (f"In a right triangle, sin of one acute angle is "
                      f"{ratio.numerator}/{ratio.denominator}. If the hypotenuse is "
                      f"{hyp}, what is the length of the side opposite that angle?")
            correct = str(opp)
            distract = [str(adj), str(hyp - opp), str(opp + m), str(hyp - adj)]
            expl = (f"sin = opposite/hypotenuse, so opposite = sin \u00d7 hypotenuse = "
                    f"{ratio.numerator}/{ratio.denominator} \u00d7 {hyp} = {opp}.")
        else:
            ratio = Fraction(trip[0], trip[1])
            prompt = (f"In a right triangle, tan of one acute angle is "
                      f"{ratio.numerator}/{ratio.denominator}. If the side adjacent to "
                      f"that angle is {adj}, what is the length of the side opposite "
                      f"the angle?")
            correct = str(opp)
            distract = [str(adj), str(hyp), str(opp + m), str(adj - trip[0])]
            expl = (f"tan = opposite/adjacent, so opposite = tan \u00d7 adjacent = "
                    f"{ratio.numerator}/{ratio.denominator} \u00d7 {adj} = {opp}.")
    else:
        trip = rng.choice(TRIPLES)
        k = rng.randint(1, 3) if difficulty == "easy" else rng.randint(1, 4)
        opp, adj, hyp = trip[0] * k, trip[1] * k, trip[2] * k
        funcs = [("sin", opp, hyp), ("cos", adj, hyp), ("tan", opp, adj)]
        name, side, ref = rng.choice(funcs)
        frac = Fraction(side, ref)
        correct = f"{frac.numerator}/{frac.denominator}"
        prompt = (f"In a right triangle with legs {opp} and {adj} and hypotenuse "
                  f"{hyp}, what is {name} of the angle opposite the leg of length "
                  f"{opp}?")
        if name == "sin":
            distract = [f"{adj}/{hyp}", f"{opp}/{adj}", f"{hyp}/{opp}", f"{adj}/{opp}"]
            expl = f"sin = opposite/hypotenuse = {opp}/{hyp}."
        elif name == "cos":
            distract = [f"{opp}/{hyp}", f"{adj}/{opp}", f"{hyp}/{adj}", f"{opp}/{adj}"]
            expl = f"cos = adjacent/hypotenuse = {adj}/{hyp}."
        else:
            distract = [f"{adj}/{opp}", f"{opp}/{hyp}", f"{hyp}/{adj}", f"{adj}/{hyp}"]
            expl = f"tan = opposite/adjacent = {opp}/{adj}."
        fracs = []
        for d in distract:
            try:
                f = Fraction(d)
                fracs.append(f"{f.numerator}/{f.denominator}")
            except (ValueError, ZeroDivisionError):
                fracs.append(d)
        distract = fracs
    choices, idx = build_choices(rng, correct, distract)
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


def gen_circles(rng, difficulty):
    h = _pick(rng, -5, 5)
    k = _pick(rng, -5, 5, exclude=(h,))
    r = _pick(rng, 2, 12)
    if difficulty == "easy":
        area_coef = r * r
        circ_coef = 2 * r
        want_area = rng.random() < 0.5
        if want_area:
            prompt = f"What is the area of a circle with radius {r}? (in terms of \u03c0)"
            correct = f"{area_coef}\u03c0" if r != 1 else f"\u03c0"
            distract = [f"{circ_coef}\u03c0", f"{area_coef * 2}\u03c0",
                        f"{r}\u03c0", f"{area_coef + r}\u03c0"]
            expl = f"Area = \u03c0r\u00b2 = \u03c0({r})\u00b2 = {area_coef}\u03c0."
        else:
            prompt = f"What is the circumference of a circle with radius {r}? (in terms of \u03c0)"
            correct = f"{circ_coef}\u03c0"
            distract = [f"{area_coef}\u03c0", f"{circ_coef + 2}\u03c0", f"{r}\u03c0",
                        f"{2 * area_coef}\u03c0"]
            expl = f"Circumference = 2\u03c0r = 2\u03c0({r}) = {circ_coef}\u03c0."
    elif difficulty == "medium":
        r2 = r * r
        prompt = (f"The circle (x {'-' if h >= 0 else '+'} {abs(h)})\u00b2 + "
                  f"(y {'-' if k >= 0 else '+'} {abs(k)})\u00b2 = {r2} is graphed in "
                  f"the xy-plane. What is the radius of the circle?")
        correct = str(r)
        distract = [str(r2), str(2 * r), str(r + 1), str(max(abs(h), abs(k)))]
        expl = f"The right-hand side is r\u00b2 = {r2}, so r = \u221a{r2} = {r}."
    else:
        # Radius from expanded equation: requires completing the square
        r2 = r * r
        d_coef = -2 * h
        e_coef = -2 * k
        f_coef = h * h + k * k - r2
        prompt = (f"The circle x\u00b2 + y\u00b2 {'+' if d_coef >= 0 else '-'} "
                  f"{abs(d_coef)}x {'+' if e_coef >= 0 else '-'} {abs(e_coef)}y "
                  f"{'+' if f_coef >= 0 else '-'} {abs(f_coef)} = 0 is graphed in the "
                  f"xy-plane. What is the radius of the circle?")
        correct = str(r)
        distract = [str(r2), str(2 * r), str(abs(d_coef) // 2 or 1), str(r + 1)]
        expl = (f"Complete the square: (x {'-' if h >= 0 else '+'} {abs(h)})\u00b2 + "
                f"(y {'-' if k >= 0 else '+'} {abs(k)})\u00b2 = {r2}, so r = "
                f"\u221a{r2} = {r}.")
    choices, idx = build_choices(rng, correct, [d for d in distract])
    return {"prompt": prompt, "choices": list(choices), "answer_index": idx,
            "explanation": expl}


GENERATORS = {
    "linear_equations_1v": gen_linear_eq_1v,
    "linear_functions": gen_linear_functions,
    "systems_linear": gen_systems_linear,
    "linear_inequalities": gen_linear_inequalities,
    "linear_word_problems": gen_linear_word_problems,
    "equivalent_expressions": gen_equivalent_expressions,
    "nonlinear_equations": gen_nonlinear_equations,
    "nonlinear_systems": gen_nonlinear_systems,
    "nonlinear_functions": gen_nonlinear_functions,
    "ratios_rates": gen_ratios_rates,
    "percentages": gen_percentages,
    "one_variable_data": gen_one_variable_data,
    "probability": gen_probability,
    "inference_studies": gen_inference_studies,
    "units_conversion": gen_units_conversion,
    "area_volume": gen_area_volume,
    "lines_angles_triangles": gen_lines_angles_triangles,
    "right_triangles_trig": gen_right_triangles_trig,
    "circles": gen_circles,
}


def generate(skill_id: str, rng, difficulty: str) -> dict:
    gen = GENERATORS.get(skill_id)
    if gen is None:
        raise GenerationError(f"no generator registered for skill '{skill_id}'")
    return gen(rng, difficulty)
