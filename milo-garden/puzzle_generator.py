#!/usr/bin/env python3
"""Generate deterministic Firefly v2 puzzles with necessary moonflower clues."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
Cell = tuple[int, int]


def neighbors(cell: Cell, size: int):
    row, col = cell
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        other = (row + dr, col + dc)
        if 0 <= other[0] < size and 0 <= other[1] < size:
            yield other


def make_solution(size: int, rng: random.Random):
    """Choose size fireflies with varied row and column totals of at most two."""
    cells = [(row, col) for row in range(size) for col in range(size)]
    for _ in range(5_000):
        chosen: list[Cell] = []
        row_counts = [0] * size
        col_counts = [0] * size
        options = cells[:]
        rng.shuffle(options)
        for cell in options:
            row, col = cell
            if row_counts[row] >= 2 or col_counts[col] >= 2:
                continue
            chosen.append(cell)
            row_counts[row] += 1
            col_counts[col] += 1
            if len(chosen) == size:
                break
        if len(chosen) != size:
            continue
        if 0 in row_counts and 2 in row_counts and 0 in col_counts and 2 in col_counts:
            return sorted(chosen), row_counts, col_counts
    raise RuntimeError("Could not create a varied solution")


def grow_regions(size: int, solution: list[Cell], rng: random.Random):
    regions = [[-1] * size for _ in range(size)]
    frontier: list[tuple[int, int, int]] = []
    for region, (row, col) in enumerate(solution):
        regions[row][col] = region
    for region, cell in enumerate(solution):
        for row, col in neighbors(cell, size):
            if regions[row][col] == -1:
                frontier.append((row, col, region))
    while frontier:
        index = rng.randrange(len(frontier))
        row, col, region = frontier.pop(index)
        if regions[row][col] != -1:
            continue
        regions[row][col] = region
        for row2, col2 in neighbors((row, col), size):
            if regions[row2][col2] == -1:
                frontier.append((row2, col2, region))
    return regions


def base_candidates(size, regions, row_targets, col_targets, limit=8_000):
    """Enumerate placements satisfying habitats and variable line totals."""
    region_cells = [
        [(row, col) for row in range(size) for col in range(size) if regions[row][col] == region]
        for region in range(size)
    ]
    order = sorted(range(size), key=lambda region: len(region_cells[region]))
    answers: list[frozenset[Cell]] = []
    row_counts = [0] * size
    col_counts = [0] * size
    chosen: set[Cell] = set()

    def visit(depth: int):
        if len(answers) >= limit:
            return
        if depth == size:
            if row_counts == row_targets and col_counts == col_targets:
                answers.append(frozenset(chosen))
            return
        region = order[depth]
        for cell in region_cells[region]:
            row, col = cell
            if row_counts[row] >= row_targets[row] or col_counts[col] >= col_targets[col]:
                continue
            chosen.add(cell)
            row_counts[row] += 1
            col_counts[col] += 1
            visit(depth + 1)
            col_counts[col] -= 1
            row_counts[row] -= 1
            chosen.remove(cell)

    visit(0)
    return answers


def obeys_flower(answer: frozenset[Cell], flower: tuple[int, int, int], size: int):
    row, col, required = flower
    return (row, col) not in answer and sum(cell in answer for cell in neighbors((row, col), size)) == required


def candidates(size, regions, row_targets, col_targets, flowers):
    answers = base_candidates(size, regions, row_targets, col_targets)
    answers = [answer for answer in answers if all(obeys_flower(answer, flower, size) for flower in flowers)]
    flower_cells = {(row, col) for row, col, _ in flowers}
    return [
        answer for answer in answers
        if all(any(flower in flower_cells for flower in neighbors(firefly, size)) for firefly in answer)
    ]


def choose_flowers(size: int, solution: list[Cell], base: list[frozenset[Cell]], rng: random.Random):
    target = frozenset(solution)
    options = []
    for row in range(size):
        for col in range(size):
            if (row, col) in target:
                continue
            required = sum(cell in target for cell in neighbors((row, col), size))
            if 1 <= required <= 3:
                options.append((row, col, required))
    rng.shuffle(options)
    selected: list[tuple[int, int, int]] = []
    current = base
    covered: set[Cell] = set()

    while len(current) > 1 or covered != target:
        scored = []
        for flower in options:
            if flower in selected:
                continue
            reduced = [answer for answer in current if obeys_flower(answer, flower, size)]
            if target not in reduced:
                continue
            newly_covered = (set(neighbors((flower[0], flower[1]), size)) & target) - covered
            if len(reduced) == len(current) and not newly_covered:
                continue
            scored.append(((len(reduced), -len(newly_covered), rng.random()), flower, reduced, newly_covered))
        if not scored or len(selected) >= size + 3:
            return None
        _, flower, current, newly_covered = min(scored)
        selected.append(flower)
        covered.update(newly_covered)

    flower_cells = {(row, col) for row, col, _ in selected}
    final = [
        answer for answer in current
        if all(any(flower in flower_cells for flower in neighbors(firefly, size)) for firefly in answer)
    ]
    return sorted(selected) if final == [target] else None


def make_puzzle(size: int, seed: int, name: str, difficulty: str):
    rng = random.Random(seed)
    for _ in range(3_000):
        solution, row_counts, col_counts = make_solution(size, rng)
        regions = grow_regions(size, solution, rng)
        base = base_candidates(size, regions, row_counts, col_counts)
        if not 4 <= len(base) <= 1_500:
            continue
        flowers = choose_flowers(size, solution, base, rng)
        if not flowers:
            continue
        final = candidates(size, regions, row_counts, col_counts, flowers)
        if final == [frozenset(solution)]:
            return {
                "id": seed, "name": name, "difficulty": difficulty, "size": size,
                "regions": regions, "rowCounts": row_counts, "colCounts": col_counts,
                "flowers": [list(flower) for flower in flowers],
                "solution": [list(cell) for cell in solution], "baseSolutions": len(base),
            }
    raise RuntimeError(f"Could not generate {name}")


def generate():
    specs = [
        (5, 2712, "First Bloom", "Gentle"), (5, 2918, "Fern Hollow", "Gentle"),
        (6, 3204, "Blue Dusk", "Growing"), (6, 3511, "Mossy Path", "Growing"),
        (8, 3907, "Quiet Meadow", "Hard"), (9, 4309, "Afterglow", "Hard"),
    ]
    return {"version": 2, "puzzles": [make_puzzle(*spec) for spec in specs]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "days.json")
    args = parser.parse_args()
    data = generate()
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote {len(data['puzzles'])} unique Firefly v2 puzzles to {args.output}")


if __name__ == "__main__":
    main()
