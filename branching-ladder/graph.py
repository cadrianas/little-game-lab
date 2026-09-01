"""Word graph for the branching ladder.

Nodes are words of one fixed length; an edge joins two words that differ in
exactly one position. Words are filtered by commonness, because a ladder that
routes through a word nobody knows is not a puzzle, it is a dictionary lookup.
"""

from collections import deque
from pathlib import Path

DATA = Path(__file__).parent / "data"


def load_blocklist(filename="blocklist.txt"):
    words = set()
    with open(DATA / filename) as fh:
        for line in fh:
            line = line.strip()
            if line and not line.startswith("#"):
                words.add(line)
    return words


def load_ranks():
    ranks = {}
    with open(DATA / "count_1w.txt") as fh:
        for i, line in enumerate(fh):
            word = line.split("\t", 1)[0]
            if word not in ranks:
                ranks[word] = i
    return ranks


class WordGraph:
    def __init__(self, length=4, max_rank=25_000, extra_blocklist=None):
        ranks = load_ranks()
        blocked = load_blocklist()
        if extra_blocklist:
            blocked |= set(extra_blocklist)
        words = []
        for line in open(DATA / "enable1.txt"):
            w = line.strip()
            if len(w) != length or not w.isalpha() or not w.islower():
                continue
            if max_rank is not None and ranks.get(w, 10**9) > max_rank:
                continue
            # A ladder walks the player through every rung, so a blocked word
            # is removed from the graph rather than merely disallowed as an
            # answer -- no puzzle can route through it.
            if w in blocked:
                continue
            words.append(w)
        self.blocked = blocked

        self.words = words
        self.index = {w: i for i, w in enumerate(words)}
        self.rank = [ranks.get(w, 10**9) for w in words]
        self.length = length

        # Bucket by wildcard pattern: words sharing "c_ld" are one step apart.
        buckets = {}
        for i, w in enumerate(words):
            for p in range(length):
                buckets.setdefault(w[:p] + "_" + w[p + 1:], []).append(i)

        adj = [[] for _ in words]
        for group in buckets.values():
            for a in group:
                for b in group:
                    if a != b:
                        adj[a].append(b)
        self.adj = [sorted(set(a)) for a in adj]

    def __len__(self):
        return len(self.words)

    def bfs(self, source):
        """Distances from one node to every node; unreachable stays None."""
        dist = [None] * len(self.words)
        dist[source] = 0
        q = deque([source])
        while q:
            u = q.popleft()
            for v in self.adj[u]:
                if dist[v] is None:
                    dist[v] = dist[u] + 1
                    q.append(v)
        return dist

    def components(self):
        seen = [False] * len(self.words)
        out = []
        for start in range(len(self.words)):
            if seen[start]:
                continue
            comp, q = [], deque([start])
            seen[start] = True
            while q:
                u = q.popleft()
                comp.append(u)
                for v in self.adj[u]:
                    if not seen[v]:
                        seen[v] = True
                        q.append(v)
            out.append(comp)
        return sorted(out, key=len, reverse=True)


if __name__ == "__main__":
    for length in (4, 5):
        g = WordGraph(length)
        comps = g.components()
        edges = sum(len(a) for a in g.adj) // 2
        print(
            f"{length}-letter: {len(g)} words, {edges} edges, "
            f"{len(comps)} components, largest {len(comps[0])}"
        )
