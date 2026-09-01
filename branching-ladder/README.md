# Branching Ladder — feasibility test

One start word, three targets. Change one letter at a time. Score is total
rungs, so the puzzle is finding the branch point that serves all three.

```
UNIT -> SLOT, CHOW, SHOE          par 9 rungs · separately 18

UNIT
└─ KNIT
   └─ KNOT
      └─ KNOW
         └─ SNOW
            └─ SHOW
               ├─ SHOT
               │  └─ SLOT
               ├─ SHOE
               └─ CHOW
```

## Running it

```bash
python3 generate.py -n 365 --pool 4000 --seed 3 --start-date 2026-09-01 -o days.json
```

```bash
python3 measure.py -n 150
```

```bash
python3 show.py -n 120 -e 4
```

```bash
python3 verify.py
```

## Shipping gates

Run the complete release check:

```bash
./release_check
```

It regenerates the schedule and vocabulary audit into a temporary directory,
rejects drift in committed data or the playable build, compiles the Python
sources, runs every deterministic gate, starts a temporary local server, and
launches Chrome or Chromium through Playwright Core. Run `npm ci` once
when the dependency is not already available in the workspace. The command
exits nonzero on any failure and prints `RELEASE READY` only after the browser reports
`PASS — 365/365 rendered solutions passed.` Set `BROWSER_BIN` to an explicit
Chrome/Chromium executable or `NODE_BIN` to a Node.js 20+ executable when
automatic discovery is not appropriate.

The browser stage completes and compares every published solution through the
real UI. It checks target status, par and node counts, completion feedback,
over-par improvement, preservation of the player tree, the separate par tree,
the visual share result, disabled post-reveal controls, and browser runtime
errors. `browser_verify.html` remains available for interactive diagnosis, but
opening it manually is no longer part of the release process.

For a quicker data-only check during development, run:

```bash
python3 verify.py
```

`generate.py` vets and exports days, plus `vocab_review.txt`, an editorial
audit of every word used by every published solution. `measure.py` samples
random puzzles and reports the rung saving. `show.py` adds the trunk-length
metric and renders example trees.

Build the playable page by inlining the day data into the template:

```bash
python3 -c "from pathlib import Path; Path('prototype.html').write_text(Path('prototype.template.html').read_text().replace('__DAYS__', Path('days.json').read_text()))"
```

## The game

The player grows one tree. Type a word; if it is real and one letter from
anything already on the tree, it joins. In Standard Mode, all three targets
are visible and may be reached in any order. Score is
words added, against par. Framing it as one growing tree rather than three
branches means trunk-sharing happens naturally, without the player having to
manage which branch they are on.

The playable tree highlights the current shared trunk, labels its first fork,
and reports the number of shared rungs as the structure changes.

Every non-root leaf is selectable. Pruning a leaf removes only that word,
preserves unrelated branches, updates the score and reached targets, and moves
keyboard focus to the newly exposed parent leaf when possible.

Hints escalate without replacing the player's tree: shared-trunk length,
which letter changes first, the first optimal rung, then the optimal fork word.
Hint usage is saved per puzzle, survives a reset, and is included in shared
results. The complete par tree remains a separate reveal.

Completing a tree animates the shared trunk before its branches and opens a
results card with rungs, par, hints, trunk length, and actual savings against
three separate ladders. An over-par result offers **Keep improving**; pruning
an unnecessary leaf immediately refreshes the result. **Compare with par**
freezes the attempt but preserves the player's tree and renders an official
optimal tree beneath it. Shared results use a compact text tree with target
status marks and the same completion metrics.

Every puzzle has a content-derived ID that is stable across schedule reordering
and target ordering. Standard Mode progress is stored under the versioned
`branching-ladder:standard:v2` key and indexed by that ID. The original
day-number save format is migrated once; future schedule changes cannot attach
old progress to a replacement puzzle. Hard Mode uses the separate
`branching-ladder:hard:v1` key.

## Daily schedule and history

Published puzzles have unique consecutive ISO dates as well as stable content
IDs. The first-year archive runs from September 1, 2026 through August 31,
2027. Normal play
opens the newest released puzzle; the next-day button, archive, and direct day
loading all stop at today's release. Before launch, the page shows an unlock
message without exposing puzzle content. Verification mode may access the full
schedule so future releases can be tested before publication.

The archive is a separate, month-grouped surface rather than a 365-item menu in
the play screen. It lists released dates newest first, marks the current and
completed puzzles, shows each day's best result, and filters between all,
unfinished, and completed days. Its summary reports played, completed, current
streak, and best streak. Standard Mode stores the first completion time plus
the best rung and hint result for each date. Resetting or improving a tree does
not erase a completion, and a better result updates the saved best. Standard
and Hard Mode histories never share a storage namespace.

## The two metrics that matter

**Rungs saved** — the optimal tree against solving the three ladders
separately. No saving means no decision, just three ladders stacked.

**Trunk length** — how far the tree runs before it first branches. A tree
that forks at the start word has no trunk, so there is nothing to find even
when the rung saving looks good. This is the metric that separates a real
branching puzzle from three ladders in a trenchcoat.

Measured on 4-letter common words: 85% of random puzzles save 2+ rungs
(median 3), median trunk 2, and 63% clear both bars at once.

## Why the Steiner tree is exact

`steiner.py` is Dreyfus-Wagner, not a heuristic. Par is the headline number a
player is scored against, so it has to be provable. `verify()` re-checks a
returned tree independently: every edge a legal one-letter step, all terminals
present, connected, acyclic, edge count matching the reported cost.

## Blocklist

`data/blocklist.txt` words are removed from the graph, not merely disallowed
as answers. A ladder walks the player through every intermediate rung, so a
blocked word would be shown to them by the puzzle itself. Found because a
sampled puzzle routed through DICK on its way from KIND to DUCK.

Published solutions use a second, stricter vocabulary layer. Generation is
limited to the top 6,000 frequency-ranked words, minus both editorial lists.
The playable page accepts the full four-letter ENABLE corpus after safety and
editorial exclusions, so obscure but legitimate alternate routes are not
rejected merely because they were not clean enough to publish as the official
solution.

`data/play_blocklist.txt` is the shared editorial exclusion layer for clear
names, abbreviations, archaic forms, and dictionary artifacts. The smaller
`data/generation_blocklist.txt` contains valid words that players may use but
that should not appear in an official puzzle.

## Data

ENABLE word list and Google web frequencies, copied from `../letter-economy/data`.
