"""The falsification test: does trunk-sharing actually save enough rungs?

If the best tree is barely cheaper than solving three separate ladders, there
is no decision in the puzzle and the whole idea is just three ladders stacked.
This samples random puzzles and reports how big the saving really is.
"""

import argparse
import random
import statistics
from collections import Counter

from graph import WordGraph
from steiner import steiner_tree, tree_nodes, verify

MIN_LEG = 3
MAX_LEG = 6


def sample(graph, comp, rng, dist_cache):
    start = rng.choice(comp)
    if start not in dist_cache:
        dist_cache[start] = graph.bfs(start)
    dist = dist_cache[start]

    reach = [v for v in comp if dist[v] is not None and MIN_LEG <= dist[v] <= MAX_LEG]
    if len(reach) < 3:
        return None
    targets = rng.sample(reach, 3)

    independent = sum(dist[t] for t in targets)
    cost, edges = steiner_tree(graph, [start] + targets)
    if cost == float("inf"):
        return None

    return {
        "start": start,
        "targets": targets,
        "legs": [dist[t] for t in targets],
        "independent": independent,
        "steiner": cost,
        "gap": independent - cost,
        "edges": edges,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--samples", type=int, default=150)
    ap.add_argument("--length", type=int, default=4)
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    graph = WordGraph(args.length)
    comp = graph.components()[0]
    rng = random.Random(args.seed)
    dist_cache = {}

    results, checked, bad = [], 0, 0
    while len(results) < args.samples:
        r = sample(graph, comp, rng, dist_cache)
        if r is None:
            continue
        results.append(r)
        if checked < 25:  # verify a subset against the independent checker
            problems = verify(graph, [r["start"]] + r["targets"], r["steiner"], r["edges"])
            checked += 1
            if problems:
                bad += 1
                print("INVALID TREE:", problems)

    gaps = [r["gap"] for r in results]
    sizes = [r["steiner"] for r in results]

    print(f"{len(results)} puzzles sampled on the {args.length}-letter graph")
    print(f"verified {checked} trees, {bad} invalid\n")
    print(f"tree size (rungs)   median {statistics.median(sizes):.0f}  "
          f"range {min(sizes)}-{max(sizes)}")
    print(f"rungs saved by sharing a trunk:")
    for gap, count in sorted(Counter(gaps).items()):
        bar = "#" * round(count / len(results) * 60)
        print(f"   {gap:>2}  {count:>4}  {count/len(results)*100:>5.1f}%  {bar}")
    print(f"\nmedian saving {statistics.median(gaps):.0f} rungs, "
          f"mean {statistics.mean(gaps):.2f}")
    share = sum(1 for g in gaps if g >= 2) / len(gaps)
    print(f"puzzles saving 2+ rungs: {share*100:.0f}%")


if __name__ == "__main__":
    main()
