'use strict';
const PROGRESS='milo:garden:walks:v1';
let walks={},changingWalk=false;
try{const parsed=JSON.parse(localStorage.getItem(PROGRESS));if(parsed&&typeof parsed==='object')walks=parsed;}catch{}
const gardenSelect=document.getElementById('gardenSelect');
function refreshChoices(target){
 const hard=Boolean(DATA.puzzles[target].challengeRating);
 gardenSelect.replaceChildren();
 DATA.puzzles.forEach((p,i)=>{if(Boolean(p.challengeRating)!==hard)return;const o=document.createElement('option');o.value=i;o.textContent=hard?p.name:`${i+1}. ${p.name}`;gardenSelect.append(o);});
 document.getElementById('gentleGardens').setAttribute('aria-pressed',String(!hard));document.getElementById('hardGardens').setAttribute('aria-pressed',String(hard));
 document.getElementById('difficultyDescription').textContent=hard?'Fewer easy deductions. Connect clues across the garden; pencil marks can help.':'A quiet place to begin. Follow the flowers and take your time.';
}
refreshChoices(0);
document.getElementById("hardGardens").disabled=!DATA.puzzles.some(p=>p.challengeRating);
document.getElementById('gentleGardens').onclick=()=>reset(0);
document.getElementById('hardGardens').onclick=()=>reset(DATA.puzzles.findIndex(p=>p.challengeRating));
// Carry existing completion records forward when opening from the same origin.
try{if(!localStorage.getItem(STORE)){const old=localStorage.getItem('firefly:wide:v1');if(old)localStorage.setItem(STORE,old);}}catch{}
function persistWalk(){if(changingWalk)return;walks[puzzle().id]={state:[...state],moves,hints,history:history.slice(-10).map(s=>[...s])};try{localStorage.setItem(PROGRESS,JSON.stringify(walks));localStorage.setItem(PROGRESS+':last',String(puzzleIndex));}catch{document.querySelector('.footer-note').textContent='Saving is unavailable in this browser. You can still enjoy the garden.';}}
function libraryStatus(){gardenSelect.value=String(puzzleIndex);let complete={};try{complete=JSON.parse(localStorage.getItem(STORE)||'{}')||{};}catch{}const count=DATA.puzzles.filter(p=>Object.hasOwn(complete,p.id)).length;document.getElementById('collectionProgress').textContent=`${count} of ${DATA.puzzles.length} gardens glowing`;}
const companionRender=render;
render=function(){companionRender();$("#undoButton").disabled=!history.length;$("#undoButton").textContent=`Undo (${history.length}/10)`;persistWalk();libraryStatus();};
const companionReset=reset;
reset=function(nextIndex){
 const restart=nextIndex===undefined,target=restart?puzzleIndex:nextIndex;
 if(!Number.isInteger(target)||target<0||target>=DATA.puzzles.length)return;
 persistWalk();changingWalk=true;refreshChoices(target);
 companionReset(target);
 const entry=walks[puzzle().id];
 if(!restart&&entry&&Array.isArray(entry.state)&&entry.state.length===puzzle().size**2&&entry.state.every((v,i)=>Number.isInteger(v)&&v>=0&&v<=3&&(!flowerMap().has(key(Math.floor(i/puzzle().size),i%puzzle().size))||v===0))){
  state=[...entry.state];
  if(Array.isArray(entry.history))history=entry.history.slice(-10).filter(s=>Array.isArray(s)&&s.length===state.length&&s.every((v,i)=>Number.isInteger(v)&&v>=0&&v<=3&&(!flowerMap().has(key(Math.floor(i/puzzle().size),i%puzzle().size))||v===0))).map(s=>[...s]);
  moves=Number.isInteger(entry.moves)&&entry.moves>=0?entry.moves:0;hints=Number.isInteger(entry.hints)&&entry.hints>=0?entry.hints:0;
 }
 changingWalk=false;render();
 setFeedback(finished?'The garden is glowing. Milo has settled down beside you.':'A quiet evening, just where you left it.');
};
gardenSelect.addEventListener('change',()=>reset(Number(gardenSelect.value)));
window.addEventListener('pagehide',persistWalk);
let lastWalk=0;try{lastWalk=Number(localStorage.getItem(PROGRESS+':last')||0);}catch{}
// Do not overwrite an existing first garden before restoring saved progress.
changingWalk=true;
reset(Number.isInteger(lastWalk)&&lastWalk>=0&&lastWalk<DATA.puzzles.length?lastWalk:0);
