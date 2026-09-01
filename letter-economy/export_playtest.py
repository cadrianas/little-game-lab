"""Export vetted days plus their word lists for the playable prototype.

The prototype is a single self-contained page, so every word it will ever need
to validate has to travel with it.
"""

import hashlib
import json
from pathlib import Path

from corpus import load_words, mask_of, spellable
from generate import build

# The optional side challenge accepts *any* affordable word, avoiding a hidden
# list where one valid word counts and another arbitrarily does not. Each day
# asks for up to three words at each approachable length; a quota shrinks when
# the puzzle does not contain three words of that length.
CHALLENGE_LENGTHS = (4, 5, 6)
WORDS_PER_LENGTH = 3

# Quotas should reflect words a player could reasonably be expected to find,
# rather than being inflated by obscure entries in the full ENABLE dictionary.
# Any valid affordable word still advances the resulting quota.
SIDE_WORD_FREQ_RANK = 20_000


def export(
    count=24,
    out=Path("playtest_days.json"),
    html=Path("prototype.html"),
    template=Path("prototype.template.html"),
):
    days, *_ = build(count, charge="per_use")
    _, by_mask = load_words()
    picked = days[:count]

    out_days = []
    for day in picked:
        words = spellable(mask_of(day["letters"]), by_mask)
        prices = day["prices"]
        affordable = [
            w for w in words
            if sum(prices[ch] for ch in w.text) <= day["budget"]
        ]
        fair_affordable = [w for w in affordable if w.rank <= SIDE_WORD_FREQ_RANK]
        available_by_length = {
            length: sum(1 for w in fair_affordable if len(w.text) == length)
            for length in CHALLENGE_LENGTHS
        }
        challenge = {
            length: min(WORDS_PER_LENGTH, available)
            for length, available in available_by_length.items()
            if available
        }
        price_key = ",".join(f"{ch}{prices[ch]}" for ch in sorted(day["letters"]))
        puzzle_key = "".join(day["letters"]) + f":{price_key}:{day['budget']}"
        puzzle_id = hashlib.sha256(puzzle_key.encode()).hexdigest()[:12]
        # Every word spellable from the pool travels with the day, not just the
        # affordable ones: telling a player "that is a word, but it costs 15"
        # is better than telling them it is not a word.
        out_days.append(
            {
                "letters": day["letters"],
                "id": puzzle_id,
                "prices": [day["prices"][ch] for ch in day["letters"]],
                "budget": day["budget"],
                "par": day["optimum_len"],
                "answer": day["answer"],
                "best": day["optimal_words"],
                "trap": day["trap_word"],
                "mode": day["mode"],
                "rarity": day.get("rarity", "common"),
                "partOfSpeech": day.get("part_of_speech"),
                "definition": day.get("definition"),
                "challenge": challenge,
                "words": sorted(w.text for w in words),
            }
        )

    days_json = json.dumps(out_days, separators=(",", ":"))
    out.write_text(days_json)
    html.write_text(template.read_text().replace("__DAYS__", days_json))
    total = sum(len(d["words"]) for d in out_days)
    print(f"{len(out_days)} days, {total} words, {out.stat().st_size/1024:.0f} KB")
    for d in out_days:
        print(
            f"  {''.join(d['letters']).upper():<9} budget {d['budget']:>2}  "
            f"par {d['par']}  {d['mode']:<9} {len(d['words']):>4} words  "
            f"{d['answer'].upper():<11} side goal {d['challenge']}"
        )
    print(f"wrote playable prototype -> {html}")


if __name__ == "__main__":
    export()
