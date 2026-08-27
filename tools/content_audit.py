import argparse
import statistics
import sys
from collections import Counter, defaultdict

sys.path.insert(0, ".")

from satprep.core.framework import DOMAINS, DIFFICULTIES, get_skill
from satprep.core.rng import derive_seed, rng_for
from satprep.questions.bank import GENERATORS
from satprep.questions.difficulty import profile_from_dict, score_difficulty


def audit(per_skill=40):
    problems = []
    # For difficulty distribution summary
    hard_rejections = Counter()
    instance_tiers = defaultdict(Counter)

    header = (f"{'skill':28} {'diff':6} {'draws':5} {'uniq':5} "
              f"{'uniq%':6} {'hardgate':8} {'rs_med':6} {'dp_med':6} {'RT%':4} {'CI%':4} {'bad':3}")
    print(header)
    print("-" * len(header))
    for skill_id in sorted(GENERATORS):
        dom = next(d for d in DOMAINS if any(s.skill_id == skill_id for s in d.skills))
        for difficulty in DIFFICULTIES:
            prompts = []
            bad = 0
            rs_vals = []
            dp_vals = []
            rt_count = 0
            ci_count = 0
            hard_pass = 0
            hard_total = 0
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
                prompts.append(payload["prompt"])

                # Difficulty scoring (§8-§10)
                prof = profile_from_dict(payload.get("difficulty_profile"))
                instance_tier, reasons, prof_used = score_difficulty(payload, prof)
                instance_tiers[skill_id + ":" + difficulty][instance_tier] += 1
                rs_vals.append(prof_used.reasoning_steps)
                dp_vals.append(prof_used.decision_points)
                if prof_used.representation_translation:
                    rt_count += 1
                if prof_used.concept_interaction:
                    ci_count += 1
                if difficulty == "hard":
                    hard_total += 1
                    if instance_tier == "hard":
                        hard_pass += 1
                    else:
                        hard_rejections[skill_id] += 1

            unique = len(set(prompts))
            rate = unique / max(1, per_skill)
            flag = ""
            if rate < 0.60:
                flag = " <-- low variety"
            if bad:
                flag += " BAD"
            # Hard gate display
            if difficulty == "hard":
                hg = f"{hard_pass}/{hard_total} {hard_pass*100//max(1,hard_total):3d}%" if hard_total else "--"
                if hard_pass < hard_total * 0.5:
                    flag += " HARD->EASY"
            else:
                hg = "--"
            rs_med = statistics.median(rs_vals) if rs_vals else 0
            dp_med = statistics.median(dp_vals) if dp_vals else 0
            rt_pct = rt_count * 100 // max(1, per_skill)
            ci_pct = ci_count * 100 // max(1, per_skill)
            print(f"{skill_id:28} {difficulty:6} {per_skill:<5} {unique:<5} "
                  f"{rate * 100:5.0f}% {hg:8} {rs_med:5.1f} {dp_med:5.1f} {rt_pct:3d}% {ci_pct:3d}% {bad:>2}{flag}")
    print()
    if hard_rejections:
        print(f"HARD rejections (requested hard but instance was easy/medium):")
        for sid, cnt in sorted(hard_rejections.items(), key=lambda x: -x[1]):
            print(f"  {sid:28} {cnt}/{per_skill} rejected")
        print()
    # Instance tier distribution summary
    print("Instance tier distribution (requested -> instance):")
    for key in sorted(instance_tiers):
        ctr = instance_tiers[key]
        total = sum(ctr.values())
        easy = ctr.get("easy", 0)
        med = ctr.get("medium", 0)
        hard = ctr.get("hard", 0)
        print(f"  {key:36} easy {easy:2d} medium {med:2d} hard {hard:2d}  ({hard*100//max(1,total):2d}% hard)")
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
