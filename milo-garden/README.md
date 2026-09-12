# Milo & the Firefly Garden

A standalone, offline-capable browser game with 389 unique 10×10 puzzle layouts (365 evening walks and 24 harder Deep Woods gardens), Milo's three illustrated poses, and optional locally synthesized music. Open `index.html`. All runtime files are in this folder; no dependency on the Firefly or Little Game Lab folders, package installation, account, or external service is required.

Place one firefly per connected habitat, match the row and column totals, satisfy each moonflower's orthogonal neighbor count, and ensure every firefly lights a flower. Hints and undo are available. Completion leaves Milo asleep beside the board.

Use the walk selector or arrows to explore the evening walks and Deep Woods layouts. In-progress grids, leaf notes, move/hint counts, completed walks, last-open walk and volume are saved in browser-local storage. The original six gardens keep their IDs; old completion records migrate when available on the same origin. Reset clears only the current grid. A different browser or origin has its own saves.

## Music

Tap Music to start an original synthesized arrangement: soft sine tones with a slow arpeggio over four warm chords. No autoplay or downloaded recordings. Volume is adjustable and remembered. Music pauses in hidden tabs and stops when turned off or the page is left. Playback must be explicitly started again after a reload.

## Generate and verify

- `python3 generate.py`: reproducible generation of the bank; retains the six originals. Do not replace published puzzle IDs with different layouts.
- `python3 verify.py`: exhaustively verify connected habitats, unique solutions, necessary flower clues, distinct layouts, and preservation of the originals.
- `python3 generate_challenges.py`: generate 24 harder gardens with cells unresolved by basic exact-count deductions. This benchmark is a difficulty filter, not a complete model of human solving.
- `python3 verify_challenges.py`: exhaustively verify uniqueness and connectivity for the harder bank and check its difficulty ratings.
- `python3 build.py`: embed the bank in `index.html`.

For static hosting or offline distribution, ship `index.html`, `milo.css`, `standalone.css`, `milo.js`, `standalone.js`, `music.js`, and the three `milo-*.png` images. The accompanying ZIP contains these runtime files only. The 365 layouts are freely selectable rather than date-locked.

## Pencil and undo

Pencil marks are tentative fireflies and do not count toward any clue or completion. Turn Pencil off and tap a tentative firefly to confirm it. Undo retains the last 10 board changes per walk, including across reloads. Existing saved grids remain compatible.

Completing a garden opens a dismissible Milo pop-up with a brief confetti animation. Reduced-motion preferences disable the confetti. Reopening a saved completed garden does not trigger the pop-up; its celebration can be replayed from the completed garden controls. Include `celebration.js` when distributing the game.

Flowers show their exact target and current/needed count. Fully satisfied flowers glow gold and show a checkmark. Tap a flower to highlight its orthogonal neighbours without making a move.
