#!/usr/bin/env python3
"""Independently verify every published distance-band intersection."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "days.json").read_text())
countries = {country["name"]: country for country in data["countries"]}


def distance(a, b):
    lat1, lon1 = map(math.radians, (a["lat"], a["lon"]))
    lat2, lon2 = map(math.radians, (b["lat"], b["lon"]))
    value = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    value = max(0, min(1, value))
    return 6371 * 2 * math.atan2(math.sqrt(value), math.sqrt(1-value))


def matches(name, clue):
    km = distance(countries[name], countries[clue["anchor"]])
    return clue["minKm"] <= km <= clue["maxKm"] + 1


assert data["version"] == 2 and data["bandKm"] == 1000
assert len(data["sets"]) == 6
assert all(len(playset["rounds"]) == 5 for playset in data["sets"])
answers = []
puzzles = [puzzle for playset in data["sets"] for puzzle in playset["rounds"]] + [data["tutorial"]]
for puzzle in puzzles:
    assert len(puzzle["clues"]) == 4
    remaining = set(countries)
    counts = []
    for clue in puzzle["clues"]:
        remaining = {name for name in remaining if name != clue["anchor"] and matches(name, clue)}
        counts.append(len(remaining))
        assert clue["candidates"] == len(remaining)
    assert 15 <= counts[0] <= 70
    assert 3 <= counts[1] <= 15
    assert 2 <= counts[2] <= 5 and counts[2] < counts[1]
    assert remaining == {puzzle["answer"]}, (puzzle["answer"], remaining)
    answers.append(puzzle["answer"])
assert len(answers) == len(set(answers)) == 31
assert data["tutorial"]["clues"][1]["candidates"] <= 5
print("PASS — 30 playtest rounds plus one worked tutorial narrow at every reveal")
