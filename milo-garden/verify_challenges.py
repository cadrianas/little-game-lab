"""Verify hard-bank uniqueness, habitat connectivity, and deduction benchmark."""
import json
from pathlib import Path
from puzzle_generator import base_candidates,obeys_flower,neighbors
from generate_challenges import difficulty
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
 data=json.loads((ROOT/'challenges.json').read_text());original=json.loads((ROOT/'gardens.json').read_text())['puzzles']
 assert len(data['puzzles'])==24
 ids={p['id'] for p in original};seen=set();ratings=[]
 for p in data['puzzles']:
  n=p['size'];assert n==10;assert p['id'] not in ids;ids.add(p['id'])
  signature=json.dumps([p['regions'],p['rowCounts'],p['colCounts'],p['flowers']]);assert signature not in seen;seen.add(signature)
  for r in range(n):
   cells={(i,j) for i in range(n) for j in range(n) if p['regions'][i][j]==r};visited={next(iter(cells))};stack=list(visited)
   while stack:
    for c in neighbors(stack.pop(),n):
     if c in cells and c not in visited:visited.add(c);stack.append(c)
   assert visited==cells
  base=base_candidates(n,p['regions'],p['rowCounts'],p['colCounts'],limit=float('inf'))
  assert len(base)==p['baseSolutions']>1
  flowers={tuple(f[:2]) for f in p['flowers']}
  solutions=[s for s in base if all(obeys_flower(s,f,n) for f in p['flowers']) and all(any(f in flowers for f in neighbors(c,n)) for c in s)]
  assert solutions==[frozenset(map(tuple,p['solution']))],p['name']
  rating=difficulty(p);assert rating==p['challengeRating'];assert rating['unresolvedAfterLocalDeductions']>=data['threshold'];ratings.append(rating['unresolvedAfterLocalDeductions'])
 print(f"24 hard gardens verified: connected habitats, unique solutions, required flower clues; {min(ratings)}–{max(ratings)} cells unresolved by basic deductions.")
