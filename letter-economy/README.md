# Letter Economy — puzzle generator

Seven letters, each with a price. Repeats are charged every time. Spend no more
than the budget. Score is word length. Longest word wins.

The playable version keeps that longest-word search as the main challenge. An
optional side challenge asks for up to three affordable words of each length:
four, five, and six letters. Any valid affordable word counts; there is no
hidden target list. A daily quota is smaller when the puzzle does not contain
enough reasonably common words at that length.

The interface never reveals the numeric par or answer. Instead, players may
request up to three progressive hints about one longest word: its first letter,
last letter, and number of distinct letters. The game confirms when a banked
word reaches the daily maximum.

The answer schedule has three controlled rarity bands: about 80% familiar,
15% uncommon, and 5% explicitly labelled **Deep Cut** days. Deep Cut answers
come only from `data/deep_cut_words.tsv`, where every entry has a curated part
of speech, player-facing definition, and dictionary source. Their first hint is
the definition rather than a revealed letter. The full ENABLE + custom corpus
still accepts broad guesses, but it cannot silently promote dictionary debris
into a daily answer.

Every unique valid affordable submission before that maximum counts as a try.
The first maximum word freezes the result, triggers a coin-and-letter
celebration, and adds it to browser-local statistics: wins, average extra
tries, current and best streaks, and a 0-through-6+ histogram. No account or
server-side player data is required.

```
  W  M  D  N  I  O  T
  1  1  2  2  3  4  5      Budget: 13
```
`WIND` costs 8 and gets you 4 letters. `WINDOW` costs exactly 13 and gets you 6.
That gap is the game.

## Running it

```bash
python3 generate.py -n 20 -o days.json
```

Generate a numbered, dated launch year with:

```bash
python3 generate.py -n 365 --start-date 2026-08-27 -o year_days.json
```

```bash
python3 verify.py days.json
```

Build the self-contained playtest page and its embedded day data with:

```bash
python3 export_playtest.py
```

`verify.py` re-solves every day by scanning the full dictionary with plain
string logic, deliberately avoiding the bitmask index `generate.py` uses, so a
bug in the fast path can't hide behind the same bug in the checker.

## Data

- `data/enable1.txt` — ENABLE word list (~173k words, public domain). TWL and
  SOWPODS are Hasbro/Collins licensed and deliberately not used.
- `data/custom_words.txt` — curated local additions. A bare word is accepted as
  a guess only; an optional numeric frequency rank makes it eligible for fair
  answer and side-goal filtering.
- `data/deep_cut_words.tsv` — the small, sourced list allowed to become a
  deliberately obscure daily answer.
- `data/count_1w.txt` — Google Web Trillion Word Corpus frequencies (Norvig),
  used only to rank words by commonness.

## Price variety

Every pool is tested against standard, inverted, and several seeded mixed
markets, all using the same `[1, 1, 2, 2, 3, 4, 5]` price ladder. The yearly
scheduler prioritizes changing the price of every recurring letter: when a
letter appears on consecutive days, it keeps the same price only if no valid
alternative schedule exists. The seed keeps the published year reproducible.

## What makes a day publishable

A day ships only if it contains a decision. The filters in `generate.py`:

| Filter | Why |
|---|---|
| `MIN_INSIGHT_GAP` | The best word must beat the most *efficient-looking* word a player would actually reach for. No gap, no puzzle. |
| `MAX_REPEAT_RATIO` | Scoring by length rewards repetition, so without this the optimum is always a drum solo: `COCCIC`, `GIGGING`, `NONIONIC`. |
| `ANSWER_FREQ_RANK` | The answer must be a word people know. |
| `NAIVE_FREQ_RANK` | So must the trap — an obscure trap traps nobody. |
| `MAX_SLACK` | The budget has to bind, or it's decoration. |
| `MAX_OPTIMAL_WORDS` | Too many ways to hit par turns the day to mush. |
| ladder check | Words available just below the optimum, so partial success feels like progress. |

Yield is ~370 unique vetted days in 6 seconds from 4,000 seed pools, and
`seed_pools(limit=...)` is the cap, not the ceiling.

## Known rough edge

Any word at optimum length hits par, and some of those are junk (`LEALLY`,
`IONOGEN`, `NIDING`). A player can tie par with a word they don't know. Fixable
by requiring exactly one *common* word at the optimum.
