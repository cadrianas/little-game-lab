#!/usr/bin/env python3
"""Independent structural checks for generated Word Orbit sets."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
data = json.loads((ROOT / "days.json").read_text())
words = set(data["words"])


def changed_one(a, b):
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def remove_one(longer, shorter):
    return len(longer) == len(shorter) + 1 and any(
        longer[:i] + longer[i + 1 :] == shorter for i in range(len(longer))
    )


def matches(answer, clue):
    if clue["type"] == "change":
        return changed_one(answer, clue["word"])
    if clue["type"] == "remove":
        return remove_one(answer, clue["word"])
    if clue["type"] == "anagram":
        return answer != clue["word"] and sorted(answer) == sorted(clue["word"])
    return False


assert len(data["sets"]) == 6
assert data["version"] == 5
all_answers = []
for playset in data["sets"]:
    assert len(playset["rounds"]) == 5
    for index, puzzle in enumerate(playset["rounds"]):
        answer, clues = puzzle["answer"], puzzle["clues"]
        assert answer in words
        assert puzzle["difficulty"] == index + 1
        assert len(clues) == 4
        assert {clue["type"] for clue in clues} <= {"change", "remove"}
        assert {clues[0]["type"], clues[1]["type"]} == {"change", "remove"}
        assert all(matches(answer, clue) for clue in clues)
        assert puzzle["hint"]["type"] == "anagram"
        assert matches(answer, puzzle["hint"])
        individual_counts = [sum(matches(word, clue) for word in words) for clue in clues]
        minimum = [4, 6, 8, 10, 12][index]
        assert min(individual_counts) >= minimum, (answer, individual_counts)
        assert min(individual_counts) > 1, (answer, "single-clue giveaway")
        candidates = [word for word in words if all(matches(word, c) for c in clues)]
        assert candidates == [answer], (answer, candidates)
        all_answers.append(answer)
assert len(all_answers) == len(set(all_answers)) == 30
first_types = [puzzle["clues"][0]["type"] for playset in data["sets"] for puzzle in playset["rounds"]]
assert first_types.count("change") == first_types.count("remove") == 15
print("PASS — 30 unique rounds; every opening pair mixes change and remove clues")
