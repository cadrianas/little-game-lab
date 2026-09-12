"""Select harder gardens using a transparent local-deduction benchmark."""
import json
from pathlib import Path
from puzzle_generator import make_puzzle,neighbors,base_candidates,obeys_flower
ROOT=Path(__file__).resolve().parent

def difficulty(p):
 n=p['size'];flowers={tuple(f[:2]) for f in p['flowers']}
 possible={(r,c) for r in range(n) for c in range(n)}-flowers
 possible={c for c in possible if any(f in flowers for f in neighbors(c,n))}
 fixed={c:0 for c in [(r,c) for r in range(n) for c in range(n)] if c not in possible}
 groups=[]
 for r in range(n):groups.append(({(r,c) for c in range(n)},p['rowCounts'][r]))
 for c in range(n):groups.append(({(r,c) for r in range(n)},p['colCounts'][c]))
 for region in range(n):groups.append(({(r,c) for r in range(n) for c in range(n) if p['regions'][r][c]==region},1))
 for r,c,k in p['flowers']:groups.append((set(neighbors((r,c),n)),k))
 rounds=0
 while True:
  changed=False
  for cells,target in groups:
   unknown=cells-fixed.keys();remaining=target-sum(fixed.get(c,0) for c in cells)
   if unknown and remaining in (0,len(unknown)):
    for c in unknown:fixed[c]=int(remaining>0)
    changed=True
  if not changed:break
  rounds+=1
 return {'unresolvedAfterLocalDeductions':n*n-len(fixed),'deductionRounds':rounds}

if __name__=='__main__':
 base=json.loads((ROOT/'gardens.json').read_text())['puzzles'];scores=sorted(difficulty(p)['unresolvedAfterLocalDeductions'] for p in base)
 threshold=max(6,scores[int(len(scores)*.9)]+1)
 print('Original 90th percentile unresolved:',scores[int(len(scores)*.9)],'challenge minimum:',threshold,flush=True)
 selected=[];seed=91000
 while len(selected)<24:
  seed+=1;p=make_puzzle(10,seed,f"Deep Woods {len(selected)+1}",'Deep woods · Challenging')
  # Remove any flower that is unnecessary for uniqueness and light coverage.
  solutions=base_candidates(p['size'],p['regions'],p['rowCounts'],p['colCounts'],limit=float('inf'))
  target=frozenset(map(tuple,p['solution']))
  for flower in p['flowers'][:]:
   trial=[f for f in p['flowers'] if f!=flower];fc={tuple(f[:2]) for f in trial}
   if not all(any(f in fc for f in neighbors(c,p['size'])) for c in target):continue
   valid=[a for a in solutions if all(obeys_flower(a,f,p['size']) for f in trial) and all(any(f in fc for f in neighbors(c,p['size'])) for c in a)]
   if valid==[target]:p['flowers']=trial
  rating=difficulty(p)
  if rating['unresolvedAfterLocalDeductions']<threshold:continue
  p['challengeRating']=rating;selected.append(p)
  print('Selected',len(selected),rating,flush=True)
 (ROOT/'challenges.json').write_text(json.dumps({'version':2,'threshold':threshold,'puzzles':selected},separators=(',',':'))+'\n')
