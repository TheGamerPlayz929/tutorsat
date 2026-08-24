import argparse
import statistics
import sys
from collections import Counter

sys.path.insert(0, ".")

from satprep.core.framework import DOMAINS, DIFFICULTIES, get_skill
from satprep.core.rng import derive_seed, rng_for
from satprep.questions.bank import GENERATORS
from satprep.questions.base import B_RANGES


def audit(per_skill=40):
    problems = []
    print(f"{'skill':28} {'diff':6} {'draws':5} {'uniq':5} "
          f"{'uniq%':6} {'b-mean':7} {'bad':3}")
    for skill_id in sorted(GENERATORS):
        dom = next(d for d in DOMAINS if any(s.skill_id == skill_id
                                             for s in d.skills))
        for difficulty in DIFFICULTIES:
            prompts = []
            bad = 0
            bs = []
            for k in range(per_skill):
                rng = rng_for("audit", skill_id, difficulty, k)
                try:
                    payload = GENERATORS[skill_id](rng, difficulty)
                except Exception as e:
                    bad += 1
                    problems.append((skill_id, difficulty, k, f"EXC {e}"))
                    continue
                choices = payload["choices"]
                idx = payload["answer_index"]
                if len(choices) != 4 or len(set(choices)) != 4:
                    bad += 1
                    problems.append((skill_id, difficulty, k, "dup/short choices"))
                if not 0 <= idx < 4:
                    bad += 1
                    problems.append((skill_id, difficulty, k, "bad answer_index"))
                if not str(choices[idx]).strip():
                    bad += 1
                    problems.append((skill_id, difficulty, k, "empty correct"))
                filler_hits = [c for c in choices if c.rstrip().endswith((".", "?", "!"))
                               and not c.endswith(("?", ".!")) ]
                if any(c.rstrip() != c for c in choices):
                    pass
                prompts.append(payload["prompt"])
            unique = len(set(prompts))
            lo, hi = B_RANGES[difficulty]
            b_mid = (lo + hi) / 2
            flag = ""
            rate = unique / max(1, per_skill)
            if rate < 0.60:
                flag = " <-- low variety"
            if bad:
                flag += " BAD"
            print(f"{skill_id:28} {difficulty:6} {per_skill:<5} {unique:<5} "
                  f"{rate * 100:5.0f}% {'':7} ~{b_mid:+.2f} {bad:>2}{flag}")
    print()
    if problems:
        print(f"PROBLEMS ({len(problems)}):")
        for p in problems[:20]:
            print(" ", p)
    else:
        print("No structural problems detected.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=40)
    args = parser.parse_args()
    audit(args.n)
