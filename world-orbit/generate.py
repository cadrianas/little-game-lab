#!/usr/bin/env python3
"""Generate deterministic World Orbit triangulation puzzles."""

from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data" / "countries-source.json"
BAND_KM = 1_000
EARTH_RADIUS_KM = 6_371

TARGET_NAMES = """Argentina|Australia|Austria|Belgium|Bolivia|Brazil|Bulgaria|Cambodia|Cameroon|Canada|Chile|China|Colombia|Costa Rica|Croatia|Cuba|Czechia|Denmark|Dominican Republic|Ecuador|Egypt|Estonia|Ethiopia|Finland|France|Germany|Ghana|Greece|Hungary|Iceland|India|Indonesia|Ireland|Israel|Italy|Japan|Jordan|Kenya|Laos|Latvia|Lithuania|Madagascar|Malaysia|Mexico|Mongolia|Morocco|Nepal|Netherlands|New Zealand|Nigeria|Norway|Pakistan|Panama|Peru|Philippines|Poland|Portugal|Romania|Serbia|Singapore|Slovakia|Slovenia|South Africa|South Korea|Spain|Sri Lanka|Sweden|Switzerland|Tanzania|Thailand|Tunisia|Türkiye|Uganda|Ukraine|United Kingdom|United States|Uruguay|Vietnam|Zambia|Zimbabwe""".split("|")

ANCHOR_NAMES = [
    name for name in TARGET_NAMES
    if name not in {"Estonia", "Laos", "Latvia", "Lithuania", "Serbia", "Slovakia", "Slovenia", "Uganda", "Zambia", "Zimbabwe"}
]


def load_countries():
    raw = json.loads(SOURCE.read_text())
    countries = {}
    for item in raw:
        coords = item.get("latlng")
        if not item.get("unMember") or not coords or len(coords) != 2:
            continue
        name = item["name"]["common"]
        countries[name] = {"name": name, "lat": coords[0], "lon": coords[1]}
    return countries


def distance_km(a, b):
    lat1, lon1 = map(math.radians, (a["lat"], a["lon"]))
    lat2, lon2 = map(math.radians, (b["lat"], b["lon"]))
    value = (
        math.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    )
    value = max(0, min(1, value))
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(value), math.sqrt(1 - value))


def band_for(distance):
    start = int(distance // BAND_KM) * BAND_KM
    return start, start + BAND_KM - 1


def matching_countries(countries, target_name, anchor_name):
    target_band = band_for(distance_km(countries[target_name], countries[anchor_name]))
    return {
        name
        for name, country in countries.items()
        if name != anchor_name and band_for(distance_km(country, countries[anchor_name])) == target_band
    }


def heat_label(start):
    if start < 1_000:
        return "Near"
    if start < 3_000:
        return "Hot"
    if start < 6_000:
        return "Warm"
    if start < 10_000:
        return "Cool"
    return "Distant"


def make_clue(countries, target, anchor, remaining):
    start, end = band_for(distance_km(countries[target], countries[anchor]))
    return {
        "anchor": anchor,
        "minKm": start,
        "maxKm": end,
        "signal": heat_label(start),
        "candidates": len(remaining),
    }


def find_puzzle(countries, target, anchors, rng):
    anchor_order = [name for name in anchors if name != target]
    rng.shuffle(anchor_order)
    first_options = []
    for first in anchor_order:
        remaining = matching_countries(countries, target, first)
        if 15 <= len(remaining) <= 70:
            first_options.append((first, remaining))
    rng.shuffle(first_options)

    for first, one in first_options:
        seconds = [name for name in anchor_order if name != first]
        rng.shuffle(seconds)
        for second in seconds:
            two = one & matching_countries(countries, target, second)
            if not 3 <= len(two) <= 15:
                continue
            thirds = [name for name in seconds if name != second]
            rng.shuffle(thirds)
            for third in thirds:
                three = two & matching_countries(countries, target, third)
                if not 2 <= len(three) <= 5 or len(three) >= len(two):
                    continue
                fourths = [name for name in thirds if name != third]
                rng.shuffle(fourths)
                for fourth in fourths:
                    four = three & matching_countries(countries, target, fourth)
                    if four != {target}:
                        continue
                    sequence = [(first, one), (second, two), (third, three), (fourth, four)]
                    return {
                        "answer": target,
                        "clues": [make_clue(countries, target, anchor, remaining) for anchor, remaining in sequence],
                    }
    return None


def generate(set_count=6, seed=23):
    countries = load_countries()
    targets = [name for name in TARGET_NAMES if name in countries]
    anchors = [name for name in ANCHOR_NAMES if name in countries]
    rng = random.Random(seed)
    rng.shuffle(targets)
    puzzles = []
    for target in targets:
        puzzle = find_puzzle(countries, target, anchors, rng)
        if puzzle:
            puzzles.append(puzzle)
        if len(puzzles) == set_count * 5 + 1:
            break
    if len(puzzles) < set_count * 5 + 1:
        raise RuntimeError(f"Generated only {len(puzzles)} publishable puzzles")
    tutorial_index = next(
        (index for index, puzzle in enumerate(puzzles) if puzzle["clues"][1]["candidates"] <= 5),
        0,
    )
    tutorial = puzzles.pop(tutorial_index)
    sets = [
        {"id": index + 1, "rounds": puzzles[index * 5 : index * 5 + 5]}
        for index in range(set_count)
    ]
    compact_countries = sorted(countries.values(), key=lambda country: country["name"])
    return {"version": 2, "bandKm": BAND_KM, "countries": compact_countries, "tutorial": tutorial, "sets": sets}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--sets", type=int, default=6)
    parser.add_argument("--seed", type=int, default=23)
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "days.json")
    args = parser.parse_args()
    data = generate(args.sets, args.seed)
    args.output.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    print(f"Wrote {args.sets * 5} World Orbit rounds to {args.output}")


if __name__ == "__main__":
    main()
