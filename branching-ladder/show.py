"""Render sampled branching ladders and measure where the fork actually sits.

The saving in rungs is not the whole story. If the tree forks at the start
word itself there is no trunk, so there is no "where do I split" decision --
the puzzle is three ladders in a trenchcoat. Trunk length is the metric that
separates a real branching puzzle from that.
"""

import argparse
import random
import statistics
from collections import Counter, defaultdict

from graph import WordGraph
from measure import sample
from steiner import tree_nodes


def rooted(edges, root):
    """Adjacency of the tree, plus parent/children maps rooted at the start."""
    adj = defaultdict(list)
    for a, b in edges:
        adj[a].append(b)
        adj[b].append(a)
    children, parent = defaultdict(list), {root: None}
    stack = [root]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in parent:
                parent[v] = u
                children[u].append(v)
                stack.append(v)
    return children, parent


def trunk_length(edges, root):
    """Rungs from the start before the tree first branches."""
    children, _ = rooted(edges, root)
    n, node = 0, root
    while len(children[node]) == 1:
        node = children[node][0]
        n += 1
    return n


def render(graph, r):
    children, _ = rooted(r["edges"], r["start"])
    targets = set(r["targets"])
    lines = []

    def walk(node, prefix, is_last, top=False):
        w = graph.words[node].upper()
        mark = "  <-- target" if node in targets else ""
        if top:
            lines.append(w)
        else:
            lines.append(prefix + ("└─ " if is_last else "├─ ") + w + mark)
        kids = children[node]
        for i, kid in enumerate(kids):
            last = i == len(kids) - 1
            ext = "" if top else ("   " if is_last else "│  ")
            walk(kid, prefix + ext, last)

    walk(r["start"], "", True, top=True)
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--samples", type=int, default=120)
    ap.add_argument("-e", "--examples", type=int, default=4)
    ap.add_argument("--seed", type=int, default=11)
    args = ap.parse_args()

    graph = WordGraph(4)
    comp = graph.components()[0]
    rng = random.Random(args.seed)
    cache = {}

    results = []
    while len(results) < args.samples:
        r = sample(graph, comp, rng, cache)
        if r:
            r["trunk"] = trunk_length(r["edges"], r["start"])
            results.append(r)

    trunks = [r["trunk"] for r in results]
    print(f"{len(results)} puzzles — where does the tree first branch?")
    for t, c in sorted(Counter(trunks).items()):
        label = "at the start word (no trunk)" if t == 0 else f"{t} rung{'s' if t > 1 else ''} in"
        print(f"   {label:<30} {c:>4}  {c/len(results)*100:>5.1f}%  {'#' * round(c/len(results)*50)}")
    print(f"median trunk {statistics.median(trunks):.0f}")
    good = [r for r in results if r["trunk"] >= 1 and r["gap"] >= 3]
    print(f"\npuzzles with a real trunk AND a 3+ rung saving: "
          f"{len(good)}/{len(results)} ({len(good)/len(results)*100:.0f}%)\n")

    good.sort(key=lambda r: (-r["gap"], r["steiner"]))
    for r in good[: args.examples]:
        print("-" * 46)
        print(
            f"{graph.words[r['start']].upper()} -> "
            + ", ".join(graph.words[t].upper() for t in r["targets"])
        )
        print(
            f"par {r['steiner']} rungs · separately {r['independent']} · "
            f"saves {r['gap']} · trunk {r['trunk']}"
        )
        print()
        print(render(graph, r))
        print()


if __name__ == "__main__":
    main()
