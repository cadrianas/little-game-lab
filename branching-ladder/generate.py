"""Vet and export branching ladder days.

A day ships only if it has a decision in it: a trunk to find, and a saving big
enough that finding it matters. The two thresholds below are the whole quality
gate, measured in `show.py` before being fixed here.
"""

import argparse
from datetime import date, timedelta
import hashlib
import json
import random
from pathlib import Path

from graph import WordGraph, load_blocklist
from measure import sample
from show import rooted, trunk_length
from steiner import tree_nodes, verify

MIN_TRUNK = 1          # a tree that forks at the start word has nothing to find
MIN_SAVING = 4         # rungs saved against solving the three ladders separately
PAR_RANGE = (7, 13)    # small enough to finish, big enough to feel like a climb
MAX_TARGET_DISTANCE_SPREAD = 2  # no target should be conspicuously earlier
SCHEDULE_START = date(2026, 9, 1)  # public launch date
SCHEDULE_DAYS = 365

# Published solutions and player guesses deliberately use different
# vocabularies. A solution should contain only immediately familiar words,
# while players deserve a broader dictionary for creative alternate routes.
GENERATION_RANK = 6_000
# Player guesses use the full ENABLE corpus. Frequency rank is intentionally
# uncapped here: an obscure but legitimate alternate route should still work.
PLAY_RANK = None
PLAY_BLOCKLIST = "play_blocklist.txt"
GENERATION_BLOCKLIST = "generation_blocklist.txt"


def vet(graph, r):
    if r["trunk"] < MIN_TRUNK or r["gap"] < MIN_SAVING:
        return False
    if not PAR_RANGE[0] <= r["steiner"] <= PAR_RANGE[1]:
        return False
    if max(r["legs"]) - min(r["legs"]) > MAX_TARGET_DISTANCE_SPREAD:
        return False
    # A target sitting on the path to another target makes the fork ambiguous
    # to render and gives away part of the trunk for free.
    children, _ = rooted(r["edges"], r["start"])
    for t in r["targets"]:
        if children[t]:
            return False
    return True


def as_day(graph, r, puzzle_date):
    _, parent = rooted(r["edges"], r["start"])
    start = graph.words[r["start"]]
    targets = [graph.words[t] for t in r["targets"]]
    solution = [
        [graph.words[parent[v]], graph.words[v]]
        for v in parent
        if parent[v] is not None
    ]
    return {
        "id": puzzle_id(start, targets),
        "date": puzzle_date.isoformat(),
        "start": start,
        "targets": targets,
        "par": r["steiner"],
        "separate": r["independent"],
        "trunk": r["trunk"],
        "solution": solution,
    }


def puzzle_id(start, targets):
    """Stable identity: unchanged by schedule position or target ordering."""
    signature = "v1|" + start + "|" + "|".join(sorted(targets))
    digest = hashlib.sha256(signature.encode()).hexdigest()[:12]
    return "bl-" + digest


def build(count, seed=3, length=4, pool=4_000, start_date=SCHEDULE_START):
    editorial_blocklist = (
        load_blocklist(PLAY_BLOCKLIST)
        | load_blocklist(GENERATION_BLOCKLIST)
    )
    graph = WordGraph(
        length,
        max_rank=GENERATION_RANK,
        extra_blocklist=editorial_blocklist,
    )
    comp = graph.components()[0]
    rng = random.Random(seed)
    cache = {}

    # Gather a pool of publishable puzzles, then keep the ones with the
    # biggest saving rather than whichever the sampler happened to hit first.
    candidates = []
    for _ in range(pool):
        r = sample(graph, comp, rng, cache)
        if not r:
            continue
        r["trunk"] = trunk_length(r["edges"], r["start"])
        if vet(graph, r):
            candidates.append(r)

    candidates.sort(key=lambda r: (-r["gap"], r["steiner"]))

    days, seen_starts, seen_targets = [], set(), set()
    for r in candidates:
        if len(days) >= count:
            break
        start = graph.words[r["start"]]
        tkey = frozenset(graph.words[t] for t in r["targets"])
        if start in seen_starts or tkey in seen_targets:
            continue

        problems = verify(graph, [r["start"]] + r["targets"], r["steiner"], r["edges"])
        if problems:
            print("rejected, invalid tree:", problems)
            continue

        seen_starts.add(start)
        seen_targets.add(tkey)
        puzzle_date = start_date + timedelta(days=len(days))
        days.append(as_day(graph, r, puzzle_date))

    print(f"{len(candidates)}/{pool} sampled puzzles were publishable")
    return graph, days


def vocabulary_report(graph, days):
    """Return an audit of every word a published solution can display."""
    lines = [
        "Branching Ladder vocabulary review",
        f"generation frequency rank <= {GENERATION_RANK}",
        "",
    ]
    for i, day in enumerate(days, 1):
        words = {day["start"], *day["targets"]}
        for parent, child in day["solution"]:
            words.add(parent)
            words.add(child)
        ranked = sorted((graph.rank[graph.index[w]], w) for w in words)
        rendered = "  ".join(f"{word.upper()} ({rank})" for rank, word in ranked)
        lines.append(f"{i:>2}. {rendered}")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--count", type=int, default=SCHEDULE_DAYS)
    ap.add_argument(
        "--pool",
        type=int,
        default=4_000,
        help="number of deterministic candidate puzzles to sample",
    )
    ap.add_argument("-o", "--out", type=Path, default=Path("days.json"))
    ap.add_argument(
        "--review-out",
        type=Path,
        default=Path("vocab_review.txt"),
        help="write every published solution word and its frequency rank",
    )
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument(
        "--start-date",
        type=date.fromisoformat,
        default=SCHEDULE_START,
        help="date assigned to the first generated puzzle (YYYY-MM-DD)",
    )
    args = ap.parse_args()

    graph, days = build(
        args.count,
        seed=args.seed,
        pool=args.pool,
        start_date=args.start_date,
    )
    play_graph = WordGraph(
        4,
        max_rank=PLAY_RANK,
        extra_blocklist=load_blocklist(PLAY_BLOCKLIST),
    )
    payload = {"words": play_graph.words, "days": days}
    args.out.write_text(json.dumps(payload, separators=(",", ":")))
    args.review_out.write_text(vocabulary_report(graph, days))

    print(f"{len(days)} days · {len(play_graph.words)} accepted words · "
          f"{args.out.stat().st_size/1024:.0f} KB -> {args.out}\n")
    print(f"vocabulary audit -> {args.review_out}\n")
    for i, d in enumerate(days, 1):
        print(
            f"{i:>3}. {d['start'].upper()} -> "
            f"{', '.join(t.upper() for t in d['targets']):<22} "
            f"par {d['par']:>2}  separately {d['separate']:>2}  "
            f"saves {d['separate']-d['par']:>2}  trunk {d['trunk']}"
        )


if __name__ == "__main__":
    main()
