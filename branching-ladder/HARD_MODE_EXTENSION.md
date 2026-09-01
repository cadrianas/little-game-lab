# Branching Ladder Extension: Ordered Hard Mode

## Status

Proposed extension. This is a separate mode, not a replacement for the main
game.

## Summary

Ordered Hard Mode turns the three targets into a sequence. The player begins
with only Target 1 visible. Reaching it reveals Target 2; reaching Target 2
reveals Target 3. The same tree remains in place throughout the puzzle.

The main game asks, “What trunk serves these three known destinations?” Hard
Mode asks, “Can you grow a useful tree while the destination keeps changing?”

## Core rules

1. The player starts from one word and grows a single persistent tree.
2. Only the current target is visible.
3. A new word must be a valid word and one letter different from any word
   already on the tree.
4. Reaching the current target reveals the next numbered target.
5. Previously added words and branches remain available after each reveal.
6. The puzzle is complete after Targets 1, 2, and 3 have been reached in order.
7. Score remains the total number of words added to the tree.

## Target presentation

Before play:

```text
FROM    SPIN
TARGET  1 OF 3    SNOW
NEXT    hidden
```

After reaching Target 1:

```text
REACHED 1 OF 3    SNOW
TARGET  2 OF 3    SPOT
NEXT    hidden
```

After reaching Target 2:

```text
REACHED 2 OF 3    SPOT
TARGET  3 OF 3    SLOT
```

The interface should celebrate each reveal briefly, then return focus to the
word input.

## Hidden future targets

A player may accidentally enter a future target before it is revealed. That
word must still behave like an ordinary valid word; rejecting it would reveal
that it has a secret role.

The game records such a target as **pre-reached**. When that target becomes
current, it is immediately marked reached and the next target is revealed.
This can cause two reveals in succession. The transition should explain what
happened:

> SPOT was already on your tree. Target 2 reached.

This means the mode strictly orders the information revealed to the player,
not the physical order in which every target word must be typed.

## Scoring and par

The final object is still one tree connecting the start and all three targets,
so the normal exact Steiner-tree par remains valid. Hard Mode should display:

- Rungs used
- Par
- Hints used
- Targets reached
- Shared trunk, once the first fork exists

The result should identify the mode:

```text
Branching Ladder #12 · Hard Mode
3/3 targets · 11 rungs · par 9 (+2) · 1 hint
```

An optional future metric could count rungs added during each target stage,
but it should not replace total-rung scoring.

## Hints

Hints must respect hidden information. They may refer only to the current
target and already revealed targets.

Suggested progression for each stage:

1. Give the shortest distance from the existing tree to the current target.
2. Highlight a promising existing branch or node.
3. Reveal which letter position to change next.
4. Reveal one useful next word.

The existing hints about the global optimal trunk and fork must not be used
before all three targets are visible, because they could leak future-target
information.

“Show par tree” should reveal all remaining targets and end the hidden-target
challenge.

## Generator requirements

Hard Mode needs its own quality gates in addition to the normal vocabulary,
par, trunk-length, and rung-saving checks:

- Each target must be a leaf in the official optimal tree.
- A target must never sit on the unavoidable path to a later target.
- The first target should not force a large dead-end branch before the shared
  trunk becomes useful.
- Each newly revealed target should be meaningfully different from the prior
  one; near-duplicate consecutive targets make the reveal feel trivial.
- The target order should be deliberately selected, not randomly shuffled.
- Every stage must have at least one understandable route using the curated
  publishing vocabulary.
- The ordered puzzle should be playtested independently from its normal-mode
  version.

Candidate target orders can be evaluated by simulating all six permutations.
Prefer orders that reward retaining and reusing earlier structure rather than
orders that merely demand unrelated detours.

## Fairness risk

Hiding future targets removes the player’s ability to plan the complete shared
trunk at the beginning. This creates surprise and adaptation, but it can also
make an inefficient result feel caused by missing information rather than a
bad decision.

To keep the mode fair:

- Present it explicitly as a mystery or expert mode.
- Do not compare Hard Mode streaks or scores directly with normal mode.
- Curate target order carefully.
- Favor puzzles where early work remains useful after later reveals.
- Explain that the tree persists and reuse is the central strategy.

If playtesting finds the hidden information too arbitrary, the fallback
version should show all three targets from the start, number them 1–3, and
require them in order. That version preserves advance planning while still
adding an ordering constraint.

## Mode selection

Hard Mode should be opt-in:

```text
MODE
[ Standard ]  All three targets visible; reach them in any order.
[ Hard ]      Targets are revealed one at a time; the tree persists.
```

The chosen mode should be saved locally and included in copied results. A
puzzle should keep separate progress records for Standard and Hard Mode.
Standard Mode uses `branching-ladder:standard:v2`; Hard Mode must use
`branching-ladder:hard:v1`, including its own completion history and streak.

## Success criteria

The extension is ready to implement when playtests show that:

- Players understand that their tree persists between targets.
- Later reveals reward reuse more often than they punish missing information.
- Pre-reached targets are understood when they unlock automatically.
- Hard Mode feels meaningfully harder without feeling random.
- Ordered scores remain comparable between players using the same mode.
