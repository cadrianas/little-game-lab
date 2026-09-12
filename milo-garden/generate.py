"""Reproducible, offline 365-layout Milo garden bank."""
import json
from pathlib import Path
from puzzle_generator import make_puzzle
ROOT=Path(__file__).resolve().parent
if __name__=='__main__':
 puzzles=json.loads((ROOT/'original-gardens.json').read_text())['puzzles']
 signatures={json.dumps([p['regions'],p['rowCounts'],p['colCounts'],p['flowers']]) for p in puzzles}
 places=['Lantern Meadow','Willow Reach','Moonlit Orchard','Silver Marsh','Quiet Clearing','Fern Hollow','Clover Corner','Dewdrop Path','Birch Grove','Starling Field','Evening Brook','Mossy Hollow']
 seed=62000
 while len(puzzles)<365:
  seed+=1;p=make_puzzle(10,seed,places[len(puzzles)%len(places)],'An evening walk')
  key=json.dumps([p['regions'],p['rowCounts'],p['colCounts'],p['flowers']])
  if key in signatures:continue
  signatures.add(key);puzzles.append(p)
  if len(puzzles)%50==0:print(f'{len(puzzles)} gardens generated',flush=True)
 (ROOT/'gardens.json').write_text(json.dumps({'version':2,'puzzles':puzzles},separators=(',',':'))+'\n')
 print('365 gardens ready.',flush=True)
