"""Exact minimum Steiner tree over the word graph (Dreyfus-Wagner).

A branching ladder is a tree in the word graph joining the start word to all
three targets. The best tree shares a trunk; solving the three ladders
separately does not. The difference between those two numbers is the puzzle,
so par has to be exact rather than a good guess -- hence an exact algorithm
rather than a heuristic.

With four terminals the DP is tiny: 2^4 masks over ~1.6k nodes.
"""

import heapq

INF = float("inf")


def steiner_tree(graph, terminals):
    """Minimum tree connecting all terminals. Returns (cost, set_of_edges)."""
    n = len(graph)
    k = len(terminals)
    full = (1 << k) - 1

    dp = [[INF] * n for _ in range(1 << k)]
    par = [[None] * n for _ in range(1 << k)]

    def relax(mask):
        """Shortest-path relaxation: grow the tree along graph edges."""
        heap = [(dp[mask][v], v) for v in range(n) if dp[mask][v] < INF]
        heapq.heapify(heap)
        while heap:
            d, u = heapq.heappop(heap)
            if d > dp[mask][u]:
                continue
            for v in graph.adj[u]:
                if d + 1 < dp[mask][v]:
                    dp[mask][v] = d + 1
                    par[mask][v] = ("move", u)
                    heapq.heappush(heap, (d + 1, v))

    for i, t in enumerate(terminals):
        dp[1 << i][t] = 0
        relax(1 << i)

    for mask in range(1, 1 << k):
        if mask & (mask - 1) == 0:
            continue  # single bit, already done
        for v in range(n):
            sub = (mask - 1) & mask
            while sub:
                other = mask ^ sub
                if sub < other:  # each split once
                    cost = dp[sub][v] + dp[other][v]
                    if cost < dp[mask][v]:
                        dp[mask][v] = cost
                        par[mask][v] = ("merge", sub)
                sub = (sub - 1) & mask
        relax(mask)

    best = min(range(n), key=lambda v: dp[full][v])
    if dp[full][best] == INF:
        return INF, set()

    edges = set()

    def build(mask, v):
        p = par[mask][v]
        if p is None:
            return
        if p[0] == "move":
            u = p[1]
            edges.add((min(u, v), max(u, v)))
            build(mask, u)
        else:
            sub = p[1]
            build(sub, v)
            build(mask ^ sub, v)

    build(full, best)
    return dp[full][best], edges


def tree_nodes(edges):
    out = set()
    for a, b in edges:
        out.add(a)
        out.add(b)
    return out


def verify(graph, terminals, cost, edges):
    """Independent check that the returned edge set really is a valid tree.

    Confirms: every edge is a legal one-letter step, the terminals are all
    present, the edge set is connected and acyclic, and its size matches the
    reported cost.
    """
    problems = []
    nodes = tree_nodes(edges)

    for a, b in edges:
        wa, wb = graph.words[a], graph.words[b]
        if sum(x != y for x, y in zip(wa, wb)) != 1:
            problems.append(f"{wa}->{wb} is not a one-letter step")

    for t in terminals:
        if t not in nodes and len(edges) > 0:
            problems.append(f"terminal {graph.words[t]} missing from tree")

    if len(edges) != cost:
        problems.append(f"cost {cost} but {len(edges)} edges")

    if nodes and len(edges) != len(nodes) - 1:
        problems.append(f"not a tree: {len(nodes)} nodes, {len(edges)} edges")

    # connectivity over the returned edges only
    if nodes:
        adj = {}
        for a, b in edges:
            adj.setdefault(a, []).append(b)
            adj.setdefault(b, []).append(a)
        seen = {next(iter(nodes))}
        stack = [next(iter(nodes))]
        while stack:
            u = stack.pop()
            for v in adj.get(u, []):
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
        if len(seen) != len(nodes):
            problems.append("tree is disconnected")

    return problems
