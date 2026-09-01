"""Run the deterministic Branching Ladder shipping gates."""

import json
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from generate import (
    GENERATION_BLOCKLIST,
    GENERATION_RANK,
    MAX_TARGET_DISTANCE_SPREAD,
    MIN_SAVING,
    MIN_TRUNK,
    PAR_RANGE,
    PLAY_BLOCKLIST,
    PLAY_RANK,
    SCHEDULE_DAYS,
    SCHEDULE_START,
    puzzle_id,
    vocabulary_report,
)
from graph import WordGraph, load_blocklist
from measure import MAX_LEG, MIN_LEG
from show import rooted, trunk_length
from steiner import steiner_tree, verify as verify_tree


GATE_ORDER = (
    "player dictionary",
    "stable puzzle IDs",
    "annual schedule",
    "dated schedule",
    "solution vocabulary",
    "valid solution tree",
    "exact optimal par",
    "targets are leaves",
    "difficulty thresholds",
    "human-friendly optimum",
    "target distance balance",
    "vocabulary audit",
    "playable build",
    "browser gate artifact",
)


def main():
    payload_path = Path("days.json")
    payload = json.loads(payload_path.read_text())
    play_graph = WordGraph(
        4,
        max_rank=PLAY_RANK,
        extra_blocklist=load_blocklist(PLAY_BLOCKLIST),
    )
    generation_graph = WordGraph(
        4,
        max_rank=GENERATION_RANK,
        extra_blocklist=(
            load_blocklist(PLAY_BLOCKLIST)
            | load_blocklist(GENERATION_BLOCKLIST)
        ),
    )

    totals = defaultdict(int)
    passes = defaultdict(int)
    problems = []

    def gate(name, condition, problem):
        totals[name] += 1
        if condition:
            passes[name] += 1
        else:
            problems.append(f"[{name}] {problem}")

    gate(
        "player dictionary",
        payload["words"] == play_graph.words,
        "embedded player dictionary is stale",
    )
    gate(
        "annual schedule",
        len(payload["days"]) == SCHEDULE_DAYS,
        f"expected {SCHEDULE_DAYS} dated puzzles, found {len(payload['days'])}",
    )

    seen_starts = set()
    seen_target_sets = set()
    seen_ids = set()
    seen_dates = set()
    for i, day in enumerate(payload["days"], 1):
        expected_id = puzzle_id(day["start"], day["targets"])
        duplicate_id = day.get("id") in seen_ids
        seen_ids.add(day.get("id"))
        gate(
            "stable puzzle IDs",
            day.get("id") == expected_id and not duplicate_id,
            f"day {i}: expected ID {expected_id}, found {day.get('id')!r}"
            + (" (duplicate)" if duplicate_id else ""),
        )
        expected_date = (SCHEDULE_START + timedelta(days=i - 1)).isoformat()
        try:
            parsed_date = date.fromisoformat(day.get("date", ""))
        except (TypeError, ValueError):
            parsed_date = None
        duplicate_date = day.get("date") in seen_dates
        seen_dates.add(day.get("date"))
        gate(
            "dated schedule",
            parsed_date is not None
            and day.get("date") == expected_date
            and not duplicate_date,
            f"day {i}: expected date {expected_date}, found {day.get('date')!r}"
            + (" (duplicate)" if duplicate_date else ""),
        )
        shown = {day["start"], *day["targets"]}
        for parent, child in day["solution"]:
            shown.add(parent)
            shown.add(child)
        rejected = sorted(shown - generation_graph.index.keys())
        gate(
            "solution vocabulary",
            not rejected,
            f"day {i}: rejected or questionable words {rejected}",
        )
        if rejected:
            continue

        terminals = [generation_graph.index[day["start"]]] + [
            generation_graph.index[word] for word in day["targets"]
        ]
        edges = {
            tuple(sorted((generation_graph.index[parent], generation_graph.index[child])))
            for parent, child in day["solution"]
        }
        exact, _ = steiner_tree(generation_graph, terminals)
        distances = generation_graph.bfs(terminals[0])
        legs = [distances[target] for target in terminals[1:]]
        separate = sum(legs)
        tree_problems = verify_tree(
            generation_graph,
            terminals,
            day["par"],
            edges,
        )
        children, _ = rooted(edges, terminals[0])
        actual_trunk = trunk_length(edges, terminals[0])
        saving = day["separate"] - day["par"]

        duplicate_start = day["start"] in seen_starts
        target_key = frozenset(day["targets"])
        duplicate_targets = target_key in seen_target_sets
        seen_starts.add(day["start"])
        seen_target_sets.add(target_key)

        structural_details = list(tree_problems)
        if separate != day["separate"]:
            structural_details.append(
                f"separate score is {separate}, exported {day['separate']}"
            )
        if actual_trunk != day["trunk"]:
            structural_details.append(
                f"trunk is {actual_trunk}, exported {day['trunk']}"
            )
        if duplicate_start:
            structural_details.append("duplicate start word")
        if duplicate_targets:
            structural_details.append("duplicate target set")
        gate(
            "valid solution tree",
            not structural_details,
            f"day {i}: " + "; ".join(structural_details),
        )
        gate(
            "exact optimal par",
            exact == day["par"],
            f"day {i}: exact par is {exact}, exported {day['par']}",
        )
        non_leaf_targets = [
            generation_graph.words[target]
            for target in terminals[1:]
            if children[target]
        ]
        gate(
            "targets are leaves",
            not non_leaf_targets,
            f"day {i}: non-leaf targets {non_leaf_targets}",
        )
        gate(
            "difficulty thresholds",
            day["trunk"] >= MIN_TRUNK
            and saving >= MIN_SAVING
            and PAR_RANGE[0] <= day["par"] <= PAR_RANGE[1],
            f"day {i}: trunk {day['trunk']}, saving {saving}, par {day['par']}",
        )
        gate(
            "human-friendly optimum",
            exact == day["par"] and not tree_problems and not rejected,
            f"day {i}: exported optimum is not a valid curated solution",
        )
        gate(
            "target distance balance",
            all(MIN_LEG <= leg <= MAX_LEG for leg in legs)
            and max(legs) - min(legs) <= MAX_TARGET_DISTANCE_SPREAD,
            f"day {i}: target distances {legs} exceed range {MIN_LEG}-{MAX_LEG} "
            f"or spread {MAX_TARGET_DISTANCE_SPREAD}",
        )

    expected_review = vocabulary_report(generation_graph, payload["days"])
    gate(
        "vocabulary audit",
        Path("vocab_review.txt").read_text() == expected_review,
        "vocab_review.txt is stale",
    )

    expected_html = Path("prototype.template.html").read_text().replace(
        "__DAYS__",
        payload_path.read_text(),
    )
    gate(
        "playable build",
        Path("prototype.html").read_text() == expected_html,
        "prototype.html is stale",
    )
    gate(
        "browser gate artifact",
        Path("browser_verify.html").is_file(),
        "browser_verify.html is missing",
    )

    for name in GATE_ORDER:
        status = "PASS" if passes[name] == totals[name] else "FAIL"
        print(f"{status}  {name:<27} {passes[name]}/{totals[name]}")

    if problems:
        print("\n" + "\n".join(problems))
        raise SystemExit(1)

    print(
        f"\nshipping data passed: {len(payload['days'])} days, "
        f"{len(play_graph.words)} accepted words"
    )
    print("browser gate is run headlessly by ./release_check")


if __name__ == "__main__":
    main()
