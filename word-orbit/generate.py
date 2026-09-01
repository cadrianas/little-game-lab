#!/usr/bin/env python3
"""Generate deterministic Word Orbit playtest sets from the local word corpus."""

from __future__ import annotations

import argparse
import itertools
import json
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CORPUS = ROOT.parent / "letter-economy" / "data"
FREQUENCY_LIMIT = 20_000
PUBLISH_LIMIT = 1_200
CENTER_LIMIT = 2_500
AMBIGUITY_LIMIT = 12_000
GENERATION_BLOCKLIST = {
    "aids", "amin", "ares", "ass", "bens", "boobs", "buss", "carte", "cates", "chad", "cham", "cine", "coles",
    "costa", "debs", "dees", "del", "docs", "don", "dos", "duns", "ester", "farts", "fete", "fowler", "hart", "hast", "hist",
    "jones", "kain", "kats", "las", "lat", "latex", "lats", "lear", "leas", "livre", "mar", "marc", "meta", "mina", "mots",
    "mon", "morel", "moray", "nema", "plage", "plats", "rape", "reals", "rede", "sain", "scart", "scop", "sept", "seton", "shit",
    "spicer", "stat", "tach", "tass", "tesla", "toon", "trice", "wales", "wold", "zeta",
}


def load_words():
    enabled = {
        line.strip().lower()
        for line in (CORPUS / "enable1.txt").read_text().splitlines()
        if line.strip().isalpha()
    }
    ordered = []
    for line in (CORPUS / "count_1w.txt").read_text().splitlines():
        parts = line.split("\t")
        if len(parts) != 2:
            continue
        word = parts[0].lower()
        if word.isalpha() and word in enabled and 3 <= len(word) <= 6:
            ordered.append(word)
            if len(ordered) >= FREQUENCY_LIMIT:
                break
    rank = {word: index + 1 for index, word in enumerate(ordered)}
    return ordered, rank


def changed_one(a: str, b: str) -> bool:
    return len(a) == len(b) and sum(x != y for x, y in zip(a, b)) == 1


def remove_one(longer: str, shorter: str) -> bool:
    return len(longer) == len(shorter) + 1 and any(
        longer[:index] + longer[index + 1 :] == shorter
        for index in range(len(longer))
    )


def trivial_suffix_extension(longer: str, shorter: str) -> bool:
    """Reject clues that merely expose a routine plural or past-tense suffix."""
    return longer in {shorter + "s", shorter + "es", shorter + "d", shorter + "ed"}


def related(candidate: str, clue: str, relation: str) -> bool:
    if relation == "change":
        return changed_one(candidate, clue)
    if relation == "remove":
        return remove_one(candidate, clue)
    if relation == "anagram":
        return candidate != clue and sorted(candidate) == sorted(clue)
    raise ValueError(relation)


def build_relation_index(words):
    patterns = defaultdict(set)
    anagrams = defaultdict(set)
    expansions = defaultdict(set)
    for word in words:
        anagrams["".join(sorted(word))].add(word)
        for index in range(len(word)):
            patterns[word[:index] + "_" + word[index + 1 :]].add(word)
            expansions[word[:index] + word[index + 1 :]].add(word)
    return {"patterns": patterns, "anagrams": anagrams, "expansions": expansions}


def relation_answers(index, relation, clue):
    if relation == "change":
        answers = set()
        for position in range(len(clue)):
            answers.update(index["patterns"][clue[:position] + "_" + clue[position + 1 :]])
        answers.discard(clue)
        return answers
    if relation == "remove":
        return set(index["expansions"][clue])
    if relation == "anagram":
        return index["anagrams"]["".join(sorted(clue))] - {clue}
    raise ValueError(relation)


def possible_answers(index, clues):
    pools = [relation_answers(index, clue["type"], clue["word"]) for clue in clues]
    return set.intersection(*pools) if pools else set()


def build_candidates(ordered, rank):
    publish = set(ordered[:PUBLISH_LIMIT]) - GENERATION_BLOCKLIST
    familiar = set(ordered[:AMBIGUITY_LIMIT]) - GENERATION_BLOCKLIST
    accepted_index = build_relation_index(set(ordered))
    common_index = build_relation_index(familiar)

    candidates = []
    for center in ordered[:CENTER_LIMIT]:
        if not 4 <= len(center) <= 6:
            continue
        if center in GENERATION_BLOCKLIST:
            continue
        changes = relation_answers(common_index, "change", center)
        removes = {
            center[:index] + center[index + 1 :]
            for index in range(len(center))
            if center[:index] + center[index + 1 :] in publish
            and not trivial_suffix_extension(center, center[:index] + center[index + 1 :])
        }
        anas = relation_answers(common_index, "anagram", center)
        if len(changes) < 2 or not removes or not anas:
            continue
        sort_key = lambda word: (rank.get(word, FREQUENCY_LIMIT), word)
        candidates.append(
            {
                "answer": center,
                "change": sorted(changes, key=sort_key)[:12],
                "remove": sorted(removes, key=sort_key)[:8],
                "anagram": sorted(anas, key=sort_key)[:8],
            }
        )
    return candidates, accepted_index, common_index


def choose_clues(candidate, accepted_index, common_index, count, level, rng, hard=False):
    combinations = []
    min_individual = [4, 6, 8, 10, 12][level]
    for change_count in range(1, count):
        remove_count = count - change_count
        if change_count > len(candidate["change"]) or remove_count > len(candidate["remove"]):
            continue
        for change_words in itertools.combinations(candidate["change"], change_count):
            for remove_words in itertools.combinations(candidate["remove"], remove_count):
                clues = [
                    *({"type": "change", "word": word} for word in change_words),
                    *({"type": "remove", "word": word} for word in remove_words),
                ]
                if possible_answers(accepted_index, clues) != {candidate["answer"]}:
                    continue
                counts = [
                    len(relation_answers(accepted_index, clue["type"], clue["word"]))
                    for clue in clues
                ]
                if min(counts) < min_individual:
                    continue
                score = min(counts) * 100 + sum(counts)
                combinations.append((score, clues, counts))
    if not combinations:
        return None
    combinations.sort(key=lambda item: item[0], reverse=True)
    shortlist = combinations[: min(8, len(combinations))]
    score, clues, counts = rng.choice(shortlist)
    # Progressive modes reveal the broadest clue first, then add increasingly
    # informative intersections. This makes "one clue" genuinely exploratory.
    ordered_clues = sorted(zip(clues, counts), key=lambda item: item[1], reverse=True)
    clues = [clue for clue, _ in ordered_clues]
    counts = [count for _, count in ordered_clues]
    hint_word = candidate["anagram"][0]
    hint = {"type": "anagram", "word": hint_word}
    return clues, hint, {"individual": counts, "score": score}


def diversify_opening(clues, counts, change_first):
    """Put one clue of each operation in the first two reveal positions."""
    pairs = list(zip(clues, counts))
    changes = sorted(
        (pair for pair in pairs if pair[0]["type"] == "change"),
        key=lambda pair: pair[1],
        reverse=True,
    )
    removes = sorted(
        (pair for pair in pairs if pair[0]["type"] == "remove"),
        key=lambda pair: pair[1],
        reverse=True,
    )
    if not changes or not removes:
        raise ValueError("Every orbit must contain both change and remove clues")
    opening = [changes.pop(0), removes.pop(0)]
    if not change_first:
        opening.reverse()
    rest = sorted(changes + removes, key=lambda pair: pair[1], reverse=True)
    ordered = opening + rest
    return [clue for clue, _ in ordered], [count for _, count in ordered]


def generate_sets(set_count=6, seed=17):
    ordered, rank = load_words()
    candidates, accepted_index, common_index = build_candidates(ordered, rank)
    rng = random.Random(seed)
    rng.shuffle(candidates)
    used_answers = set()
    rounds_by_level = [[] for _ in range(5)]
    plan = [(4, False)] * 5
    # Allocate the constrained hard rounds first so easier rounds cannot consume
    # the small supply of high-ambiguity answer families.
    for level in reversed(range(5)):
        clue_count, hard = plan[level]
        for _ in range(set_count):
            selected = None
            for candidate in candidates:
                answer = candidate["answer"]
                if answer in used_answers:
                    continue
                choice = choose_clues(
                    candidate, accepted_index, common_index, clue_count, level, rng, hard
                )
                if choice:
                    clues, hint, ambiguity = choice
                    slot = len(rounds_by_level[level])
                    clues, ambiguity["individual"] = diversify_opening(
                        clues,
                        ambiguity["individual"],
                        change_first=(level + slot) % 2 == 0,
                    )
                    selected = {
                        "answer": answer,
                        "clues": clues,
                        "hint": hint,
                        "hard": hard,
                        "difficulty": level + 1,
                        "ambiguity": ambiguity,
                    }
                    used_answers.add(answer)
                    break
            if not selected:
                raise RuntimeError(f"Could not generate difficulty {level + 1}")
            rounds_by_level[level].append(selected)

    sets = []
    for index in range(set_count):
        chunk = [rounds_by_level[level][index] for level in range(5)]
        sets.append({"id": index + 1, "rounds": chunk})
    return {"version": 5, "words": ordered, "sets": sets}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", "--sets", type=int, default=6)
    parser.add_argument("--seed", type=int, default=17)
    parser.add_argument("-o", "--output", type=Path, default=ROOT / "days.json")
    args = parser.parse_args()
    data = generate_sets(args.sets, args.seed)
    args.output.write_text(json.dumps(data, indent=2) + "\n")
    print(f"Wrote {args.sets * 5} rounds to {args.output}")


if __name__ == "__main__":
    main()
