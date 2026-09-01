"""Letter Economy puzzle generator + vetting pipeline.

The game: 7 letters, each with a price. Repeats allowed and charged each time.
Spend no more than the budget. Score is word length. Longest word wins.

The design bet is that the *price table*, not the letter pool, is what makes a
day interesting. On a STANDARD day common letters are cheap and the puzzle
rewards fluency. On an INVERTED day vowels are expensive and every instinct you
have is wrong, so the same mechanic plays like a different game.

A day is only worth publishing if it contains an insight: the best word must
beat what you get by simply avoiding the expensive letters. That gap is what
this module measures and filters on.
"""

import argparse
import json
import random
from collections import Counter
from datetime import date, timedelta
from itertools import combinations
from pathlib import Path

from corpus import (
    ANSWER_FREQ_RANK,
    load_deep_cuts,
    load_words,
    mask_of,
    spellable,
)

# Rough English letter frequency, most common first.
FREQ_ORDER = "etaoinshrdlcumwfgypbvkjxqz"
FREQ_POS = {ch: i for i, ch in enumerate(FREQ_ORDER)}

VOWELS = set("aeiou")

# Fixed price multiset, so budgets mean the same thing from day to day.
PRICE_LADDER = [1, 1, 2, 2, 3, 4, 5]

# Alongside the two frequency-shaped markets, try several stable shuffled
# markets for each pool. This makes the price table a daily puzzle ingredient
# rather than a lookup table where a familiar letter always feels the same.
MIXED_PRICE_VARIANTS = 5

# How a word's cost is computed.
#   per_use    - every occurrence of a letter is charged (repeats cost more)
#   per_letter - you buy the letter once and may reuse it freely
CHARGE_MODES = ("per_use", "per_letter")

# Vetting thresholds.
MIN_OPTIMUM_LEN = 6
MIN_INSIGHT_GAP = 1
MAX_OPTIMAL_WORDS = 4
MAX_SLACK = 2

# No single letter may make up more than this share of the answer. Without it
# the optimum is always a cheap-letter drum solo (COCCIC, GIGGING, NONIONIC):
# scoring by length rewards repetition no matter how letters are charged.
MAX_REPEAT_RATIO = 0.34

# The efficiency trap has to be a word a real person would actually land on.
NAIVE_FREQ_RANK = 20_000

# The ordinary generator remains conservative. A small, explicitly curated
# layer supplies the genuinely obscure days, while this upper slice of the
# normal answer band provides gentler "uncommon" days.
UNCOMMON_RANK_FLOOR = 11_000
UNCOMMON_SHARE = 0.15
DEEP_CUT_SHARE = 0.05


def price_pool(pool_letters, inverted):
    """Assign the fixed price ladder to a pool by English letter frequency."""
    order = sorted(pool_letters, key=lambda ch: FREQ_POS[ch], reverse=inverted)
    return {ch: PRICE_LADDER[i] for i, ch in enumerate(order)}


def price_variants(pool_letters, seed, mixed_count=MIXED_PRICE_VARIANTS):
    """Stable, distinct price markets for one seven-letter pool."""
    variants = []
    seen = set()

    def add(mode, prices):
        signature = tuple(prices[ch] for ch in sorted(pool_letters))
        if signature in seen:
            return
        seen.add(signature)
        variants.append((mode, prices))

    add("standard", price_pool(pool_letters, inverted=False))
    add("inverted", price_pool(pool_letters, inverted=True))

    rng = random.Random(f"{seed}:{''.join(sorted(pool_letters))}")
    attempts = 0
    while len(variants) < mixed_count + 2 and attempts < mixed_count * 20:
        attempts += 1
        ladder = PRICE_LADDER.copy()
        rng.shuffle(ladder)
        prices = {ch: ladder[i] for i, ch in enumerate(sorted(pool_letters))}
        add("mixed", prices)
    return variants


def evaluate(
    pool_letters,
    prices,
    budget,
    by_mask,
    charge="per_use",
    target_word=None,
    deep_cut=None,
):
    """Score a candidate day. Returns None if it is not publishable."""
    pool_mask = mask_of(pool_letters)
    candidates = spellable(pool_mask, by_mask)

    costs = {w: w.cost(prices, charge) for w in candidates}
    affordable = [w for w in candidates if costs[w] <= budget]
    if not affordable:
        return None

    optimum_len = max(len(w.text) for w in affordable)
    if optimum_len < MIN_OPTIMUM_LEN:
        return None

    optimal = [w for w in affordable if len(w.text) == optimum_len]
    if not target_word and len(optimal) > MAX_OPTIMAL_WORDS:
        return None

    # The answer a player is expected to find must be a word they know, and it
    # must not be one letter hammered over and over.
    def repeat_ratio(w):
        return max(w.counts.values()) / len(w.text)

    if target_word:
        targets = [w for w in optimal if w.text == target_word]
        if not targets:
            return None
        # A Deep Cut should actually be needed. If a normal answer reaches the
        # same length, the label would be theatre rather than a challenge.
        if any(w.text != target_word and w.rank <= ANSWER_FREQ_RANK for w in optimal):
            return None
        best = targets[0]
    else:
        fair = [
            w
            for w in optimal
            if w.rank <= ANSWER_FREQ_RANK and repeat_ratio(w) <= MAX_REPEAT_RATIO
        ]
        if not fair:
            return None
        best = min(fair, key=lambda w: w.rank)

    # The budget has to actually bind, otherwise it is decoration.
    slack = budget - costs[best]
    if slack > MAX_SLACK:
        return None

    # The insight. A naive player maximises letters-per-coin: they reach for the
    # most "efficient" word they can think of and stop. If that word is already
    # the longest, the day has no decision in it. The trap only works if it is a
    # word they would actually reach for, so it is drawn from common words only.
    plausible = [w for w in affordable if w.rank <= NAIVE_FREQ_RANK]
    if not plausible:
        return None
    ratio_best = max(plausible, key=lambda w: (len(w.text) / costs[w], len(w.text)))
    gap = optimum_len - len(ratio_best.text)
    if not target_word and gap < MIN_INSIGHT_GAP:
        return None

    # A gradient below the optimum, so partial success feels like progress.
    ladder = {}
    for w in affordable:
        ladder[len(w.text)] = ladder.get(len(w.text), 0) + 1
    if ladder.get(optimum_len - 1, 0) < 2:
        return None

    top_repeat = repeat_ratio(best)

    result = {
        "letters": sorted(pool_letters, key=lambda ch: prices[ch]),
        "prices": prices,
        "budget": budget,
        "charge": charge,
        "answer": best.text,
        "answer_cost": costs[best],
        "answer_rank": best.rank,
        "optimum_len": optimum_len,
        "optimal_words": sorted(w.text for w in optimal),
        "trap_word": ratio_best.text,
        "trap_len": len(ratio_best.text),
        "insight_gap": gap,
        "slack": slack,
        "top_repeat": round(top_repeat, 2),
        "n_affordable": len(affordable),
        "ladder": dict(sorted(ladder.items())),
    }
    if target_word:
        result.update({"rarity": "deep_cut", **deep_cut})
    else:
        result["rarity"] = (
            "uncommon" if best.rank >= UNCOMMON_RANK_FLOOR else "common"
        )
    return result


def deep_cut_candidates(by_mask, seed, charge="per_use", mixed_variants=5):
    """Build one independently vetted puzzle for every curated rare answer."""
    cuts = load_deep_cuts()
    alphabet = set("abcdefghijklmnopqrstuvwxyz")
    rng = random.Random(f"deep-cuts:{seed}")
    found = []

    for target, metadata in cuts.items():
        required = set(target)
        missing = 7 - len(required)
        if missing < 0:
            raise ValueError(f"deep cut {target} uses more than seven letters")
        fillers = list(combinations(sorted(alphabet - required), missing))
        rng.shuffle(fillers)
        options = []
        for filler in fillers[:1800]:
            pool = sorted(required | set(filler))
            if len(set(pool) & VOWELS) < 2:
                continue
            for mode, prices in price_variants(
                pool, f"deep:{seed}:{target}", mixed_variants
            ):
                target_cost = sum(prices[ch] for ch in target)
                if target_cost > 18:
                    continue
                for budget in range(max(9, target_cost), min(18, target_cost + 2) + 1):
                    day = evaluate(
                        pool,
                        prices,
                        budget,
                        by_mask,
                        charge,
                        target_word=target,
                        deep_cut=metadata,
                    )
                    if day:
                        day["mode"] = mode
                        options.append(day)
                        break
            if len(options) >= 24:
                break
        if not options:
            raise RuntimeError(f"could not build a fair Deep Cut day for {target}")
        # Prefer a healthy word ladder; seeded tie-breaking keeps the year stable.
        rng.shuffle(options)
        found.append(max(options, key=lambda d: (d["n_affordable"], -d["slack"])))
    return found


def seed_pools(words, limit=4000, max_rank=60_000):
    """Pools drawn from the letter sets of real words, so they are fertile."""
    seen = set()
    pools = []
    for w in words:
        if w.rank > max_rank or len(w.text) < 7:
            continue
        letters = set(w.text)
        if len(letters) != 7:
            continue
        if len(letters & VOWELS) < 2:
            continue
        key = frozenset(letters)
        if key in seen:
            continue
        seen.add(key)
        pools.append(sorted(letters))
        if len(pools) >= limit:
            break
    return pools


def schedule_days(candidates, count, rng):
    """Choose a varied sequence, avoiding repeated per-letter prices."""
    remaining = candidates.copy()
    scheduled = []
    mode_counts = Counter()
    rarity_counts = Counter()
    rarity_totals = Counter(d.get("rarity", "common") for d in candidates)
    last_price = {}

    while remaining and len(scheduled) < count:
        previous = scheduled[-1] if scheduled else None

        def score(day):
            position = len(scheduled) + 1
            candidate_rarity = day.get("rarity", "common")
            # Compare the whole mix after this choice. Looking only at the
            # candidate's own band consumes all special days too early.
            rarity_pacing = sum(
                abs(
                    rarity_counts[rarity]
                    + (rarity == candidate_rarity)
                    - round(position * rarity_totals[rarity] / count)
                )
                for rarity in rarity_totals
            )
            # Most important: if a letter appeared recently, change its price.
            repeated_recent_prices = sum(
                last_price.get(ch) == day["prices"][ch] for ch in day["letters"]
            )
            repeated_yesterday = 0
            if previous:
                repeated_yesterday = sum(
                    ch in previous["prices"]
                    and previous["prices"][ch] == day["prices"][ch]
                    for ch in day["letters"]
                )
            return (
                repeated_yesterday,
                rarity_pacing,
                repeated_recent_prices,
                mode_counts[day["mode"]],
                day["mode"] == (previous or {}).get("mode"),
                rng.random(),
            )

        chosen = min(remaining, key=score)
        remaining.remove(chosen)
        scheduled.append(chosen)
        mode_counts[chosen["mode"]] += 1
        rarity_counts[chosen.get("rarity", "common")] += 1
        last_price.update(chosen["prices"])

    return repair_price_repeats(scheduled)


def adjacent_price_repeats(left, right):
    """Count shared letters whose price failed to change overnight."""
    return sum(
        ch in left["prices"] and left["prices"][ch] == right["prices"][ch]
        for ch in right["letters"]
    )


def repair_price_repeats(days):
    """Remove the rare conflicts left by greedy scheduling via local swaps.

    Swaps stay within a rarity band, so Deep Cut pacing is preserved.
    """
    days = days.copy()

    def affected_score(indexes):
        edges = {
            edge
            for i in indexes
            for edge in (i - 1, i)
            if 0 <= edge < len(days) - 1
        }
        return sum(adjacent_price_repeats(days[e], days[e + 1]) for e in edges)

    while True:
        improved = False
        for i in range(len(days)):
            for j in range(i + 1, len(days)):
                if days[i].get("rarity") != days[j].get("rarity"):
                    continue
                before = affected_score((i, j))
                if not before:
                    continue
                days[i], days[j] = days[j], days[i]
                after = affected_score((i, j))
                if after < before:
                    improved = True
                    break
                days[i], days[j] = days[j], days[i]
            if improved:
                break
        if not improved:
            return days


def build(
    count,
    seed=7,
    charge="per_use",
    budgets=None,
    mixed_variants=MIXED_PRICE_VARIANTS,
):
    if budgets is None:
        budgets = range(9, 19) if charge == "per_use" else range(7, 17)
    words, by_mask = load_words()
    pools = seed_pools(words)
    rng = random.Random(seed)
    rng.shuffle(pools)

    found = []
    for pool in pools:
        for mode, prices in price_variants(pool, seed, mixed_variants):
            for budget in budgets:
                day = evaluate(pool, prices, budget, by_mask, charge)
                if day:
                    day["mode"] = mode
                    found.append(day)
                    break  # one budget per pool/mode is plenty
        if len(found) >= count * 5:
            break

    # Near-identical pools produce the same answer twice; keep one of each.
    rng.shuffle(found)
    unique, seen_answers = [], set()
    for day in found:
        if day["answer"] in seen_answers:
            continue
        seen_answers.add(day["answer"])
        unique.append(day)
    found = unique
    deep_pool = deep_cut_candidates(by_mask, seed, charge, mixed_variants)
    deep_count = min(len(deep_pool), round(count * DEEP_CUT_SHARE))
    uncommon_count = round(count * UNCOMMON_SHARE)
    common_count = count - deep_count - uncommon_count

    common = [d for d in found if d["rarity"] == "common"]
    uncommon = [d for d in found if d["rarity"] == "uncommon"]
    if len(common) < common_count or len(uncommon) < uncommon_count:
        raise RuntimeError(
            f"rarity supply too small: common {len(common)}/{common_count}, "
            f"uncommon {len(uncommon)}/{uncommon_count}"
        )
    rng.shuffle(common)
    rng.shuffle(uncommon)
    rng.shuffle(deep_pool)
    selected = (
        common[:common_count]
        + uncommon[:uncommon_count]
        + deep_pool[:deep_count]
    )
    picked = schedule_days(selected, count, rng)
    return picked, len(found) + len(deep_pool), dict(Counter(d["mode"] for d in selected))


def render(day, index=None):
    head = f"Letter Economy #{index}" if index is not None else "Letter Economy"
    letters = "  ".join(ch.upper() for ch in day["letters"])
    prices = "  ".join(str(day["prices"][ch]) for ch in day["letters"])
    lines = [
        f"{head}   [{day['mode']}]",
        f"  {letters}",
        f"  {prices}",
        f"  Budget: {day['budget']}",
        f"  Answer: {day['answer'].upper()} "
        f"({day['optimum_len']} letters, costs {day['answer_cost']})",
    ]
    if len(day["optimal_words"]) > 1:
        others = ", ".join(
            w.upper() for w in day["optimal_words"] if w != day["answer"]
        )
        lines.append(f"  Also optimal: {others}")
    lines.append(
        f"  Efficiency trap: {day['trap_word'].upper()} "
        f"({day['trap_len']} letters)  ->  insight gap +{day['insight_gap']}"
    )
    lines.append(
        f"  Affordable: {day['n_affordable']}   repeat {day['top_repeat']}   "
        f"ladder {day['ladder']}"
    )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--count", type=int, default=20)
    ap.add_argument("-o", "--out", type=Path, default=None)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--charge", choices=CHARGE_MODES, default="per_use")
    ap.add_argument("--mixed-variants", type=int, default=MIXED_PRICE_VARIANTS)
    ap.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=None,
        help="optional ISO date assigned to puzzle #1",
    )
    args = ap.parse_args()

    days, total, modes = build(
        args.count,
        seed=args.seed,
        charge=args.charge,
        mixed_variants=args.mixed_variants,
    )
    for i, day in enumerate(days, 1):
        day["number"] = i
        if args.start_date:
            day["date"] = (args.start_date + timedelta(days=i - 1)).isoformat()
    print(
        f"vetted {total} publishable days {modes}, keeping {len(days)}\n"
    )
    for i, day in enumerate(days, 1):
        print(render(day, i))
        print()

    if args.out:
        args.out.write_text(json.dumps(days, indent=2))
        print(f"wrote {len(days)} days -> {args.out}")


if __name__ == "__main__":
    main()
