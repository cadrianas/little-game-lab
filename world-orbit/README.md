# World Orbit — geographic triangulation prototype

Find the hidden country from distance-band signals sent by four satellite
countries. The interface deliberately has no map, silhouette, direction arrow,
capital trivia, or climate clue. It tests whether distance intersections alone
create a satisfying deduction puzzle.

## Modes

- Easy starts with all four signals.
- Medium starts with two.
- Hard starts with one.

Signals may be revealed individually. A guessed country that satisfies every
visible signal but is not the intended target reveals another signal without
counting as a miss. Results prioritize average signals used.

Distances are great-circle calculations between one representative coordinate
near the geographic centre of each country—not between the countries' nearest
borders. They are grouped into 1,000 km bands to avoid presenting the result as
falsely precise. Every published puzzle moves
from 15–70 candidates after signal one, to 3–15 after signal two, to 2–5 after
signal three, and exactly one after signal four. Every reveal strictly reduces
the shortlist. A separate worked tutorial shows a real 19 → 3 → 2 → 1 example
and makes clear that requesting another signal is part of the intended strategy.

## Build

```bash
python3 generate.py
python3 export_playtest.py
python3 verify.py
```

Country names and reference coordinates come from the
[mledoze/countries](https://github.com/mledoze/countries) dataset (CC BY-SA
4.0), retrieved August 31, 2026. Only UN member states are accepted as guesses.
