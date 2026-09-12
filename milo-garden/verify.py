#!/usr/bin/env python3
"""Verify Firefly v2 structure, clue necessity, and solution uniqueness."""

import json
import sys
from pathlib import Path

from puzzle_generator import base_candidates, candidates, neighbors


ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / (sys.argv[1] if len(sys.argv)>1 else "gardens.json")).read_text())
assert data["version"] == 2

for puzzle in data["puzzles"]:
    size = puzzle["size"]
    regions = puzzle["regions"]
    flowers = [tuple(item) for item in puzzle["flowers"]]
    solution = frozenset(map(tuple, puzzle["solution"]))
    assert len(regions) == size and all(len(row) == size for row in regions)
    assert set(cell for row in regions for cell in row) == set(range(size))
    for region in range(size):
        cells={(r,c) for r in range(size) for c in range(size) if regions[r][c]==region}
        reached={next(iter(cells))}
        frontier=list(reached)
        while frontier:
            for other in neighbors(frontier.pop(),size):
                if other in cells and other not in reached:
                    reached.add(other);frontier.append(other)
        assert reached==cells, (puzzle['name'],'disconnected habitat')
    assert sum(puzzle["rowCounts"]) == sum(puzzle["colCounts"]) == size
    assert 0 in puzzle["rowCounts"] and 2 in puzzle["rowCounts"]
    assert 0 in puzzle["colCounts"] and 2 in puzzle["colCounts"]
    base = base_candidates(size, regions, puzzle["rowCounts"], puzzle["colCounts"], limit=float("inf"))
    assert len(base) == puzzle["baseSolutions"] and len(base) > 1
    answers = candidates(size, regions, puzzle["rowCounts"], puzzle["colCounts"], flowers)
    assert answers == [solution], (puzzle["name"], len(answers))


print(f"Verified {len(data['puzzles'])} Firefly v2 puzzles.")

assert len(data["puzzles"])==365
assert data["puzzles"][:6]==json.loads((ROOT/"original-gardens.json").read_text())["puzzles"]
assert len({p["id"] for p in data["puzzles"]})==365
assert len({json.dumps([p["regions"],p["rowCounts"],p["colCounts"],p["flowers"]]) for p in data["puzzles"]})==365
print("365 distinct layouts; original six preserved.")
