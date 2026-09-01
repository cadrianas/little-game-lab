"""Independent check of generated days.

Deliberately does NOT use the bitmask index the generator relies on: it scans
the whole dictionary with plain string logic, so a bug in the fast path cannot
hide behind the same bug in the checker.
"""

import json
import sys
from collections import Counter
from pathlib import Path

from corpus import DICTIONARY_FILES, MAX_LEN, MIN_LEN


def brute_force(letters, prices, budget):
    pool = set(letters)
    best_len, best_words = 0, []
    seen = set()
    for path in DICTIONARY_FILES:
        if not path.exists():
            continue
        with open(path) as fh:
          for line in fh:
            parts = line.split("#", 1)[0].split()
            if not parts:
                continue
            w = parts[0]
            if w in seen:
                continue
            seen.add(w)
            if not (MIN_LEN <= len(w) <= MAX_LEN) or not w.isalpha():
                continue
            if not set(w) <= pool:
                continue
            cost = sum(prices[ch] * n for ch, n in Counter(w).items())
            if cost > budget:
                continue
            if len(w) > best_len:
                best_len, best_words = len(w), [w]
            elif len(w) == best_len:
                best_words.append(w)
    return best_len, sorted(best_words)


def main(path):
    days = json.loads(Path(path).read_text())
    failures = 0
    for i, day in enumerate(days, 1):
        exp_len, exp_words = brute_force(day["letters"], day["prices"], day["budget"])
        problems = []
        if exp_len != day["optimum_len"]:
            problems.append(f"optimum {day['optimum_len']} but brute force {exp_len}")
        if exp_words != sorted(day["optimal_words"]):
            problems.append(f"optimal set {day['optimal_words']} vs {exp_words}")
        answer_cost = sum(
            day["prices"][ch] * n for ch, n in Counter(day["answer"]).items()
        )
        if answer_cost != day["answer_cost"]:
            problems.append(f"cost {day['answer_cost']} but recomputed {answer_cost}")
        if answer_cost > day["budget"]:
            problems.append(f"answer costs {answer_cost} over budget {day['budget']}")
        if not set(day["answer"]) <= set(day["letters"]):
            problems.append("answer uses letters outside the pool")

        if problems:
            failures += 1
            print(f"FAIL #{i} {day['answer'].upper()}")
            for p in problems:
                print(f"     - {p}")
        else:
            print(f"ok   #{i} {day['answer'].upper():<12} {exp_len} letters, "
                  f"{len(exp_words)} optimal")

    print(f"\n{len(days) - failures}/{len(days)} days verified")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "days.json"))
