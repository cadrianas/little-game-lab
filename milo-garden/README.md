# Milo & the Firefly Garden

A standalone, offline-capable browser game with 365 unique 10×10 puzzle layouts, Milo's three illustrated poses, and optional locally synthesized music. Open `index.html`. All runtime files are in this folder; no dependency on the Firefly or Little Game Lab folders, package installation, account, or external service is required.

Place one firefly per connected habitat, match the row and column totals, satisfy each moonflower's orthogonal neighbor count, and ensure every firefly lights a flower. Hints and undo are available. Completion leaves Milo asleep beside the board.

Use the walk selector or arrows to explore all 365 layouts. In-progress grids, leaf notes, move/hint counts, completed walks, last-open walk and volume are saved in browser-local storage. The original six gardens keep their IDs; old completion records migrate when available on the same origin. Reset clears only the current grid. A different browser or origin has its own saves.

## Music

Tap Music to start an original synthesized arrangement: soft sine tones with a slow arpeggio over four warm chords. No autoplay or downloaded recordings. Volume is adjustable and remembered. Music pauses in hidden tabs and stops when turned off or the page is left. Playback must be explicitly started again after a reload.

## Generate and verify

- `python3 generate.py`: reproducible generation of the bank; retains the six originals. Do not replace published puzzle IDs with different layouts.
- `python3 verify.py`: exhaustively verify connected habitats, unique solutions, necessary flower clues, distinct layouts, and preservation of the originals.
- `python3 build.py`: embed the bank in `index.html`.

For static hosting or offline distribution, ship `index.html`, `milo.css`, `standalone.css`, `milo.js`, `standalone.js`, `music.js`, and the three `milo-*.png` images. The accompanying ZIP contains these runtime files only. The 365 layouts are freely selectable rather than date-locked.
