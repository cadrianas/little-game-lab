# Word Orbit — mechanic prototype

Find the word connected to every clue. The main puzzle uses change-one-letter
and remove-one-letter relationships. Once all four main clues are visible, an
anagram becomes available as an optional rescue after a miss.

Six playtest sets contain five rounds each. Every puzzle has four main clues and
is uniquely solvable without the rescue anagram. Easy shows all four clues,
Medium starts with two, and Hard starts with one. The player can reveal clues
one at a time; the result records the average number used.

The Medium opening pair is always mixed: one change-one-letter clue and one
remove-one-letter clue. Hard alternates its starting relationship across
rounds, so consecutive puzzles do not all begin with the same kind of logic.

A submitted word that satisfies every clue currently visible but is not the
hidden answer reveals another clue without counting as a miss. This makes the
progressive modes difficult without penalizing a genuinely valid partial solve.

Difficulty is based on candidate-set size rather than obscure vocabulary. No
individual clue may identify the centre by itself, and the minimum number of
plausible candidates rises by round. This forces players to intersect
relationships instead of reading the answer straight from an anagram.

## Build

```bash
python3 generate.py
python3 export_playtest.py
python3 verify.py
```

Open `prototype.html` directly, or serve this directory with any static server.
Progress is stored only in the browser.

## What this prototype is testing

- Can a player explain the rule after the first round?
- Do relationship labels prevent operation confusion?
- Does solving still feel satisfying across all five rounds?
- Do errors feel fair rather than like dictionary rejection?
- Does the player voluntarily start another five-round set?

The generator builds each orbit from the shared ENABLE and frequency corpora.
It rejects any clue set with more than one answer in the accepted prototype
vocabulary. The web UI accepts all words in that same vocabulary, embedded at
build time as the generated answer set is intentionally smaller.
