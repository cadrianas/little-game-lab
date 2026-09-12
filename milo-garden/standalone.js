'use strict';
const PROGRESS='milo:garden:walks:v1';
let walks={},changingWalk=false;
try{const parsed=JSON.parse(localStorage.getItem(PROGRESS));if(parsed&&typeof parsed==='object')walks=parsed;}catch{}
const gardenSelect=document.getElementById('gardenSelect');
DATA.puzzles.forEach((p,i)=>{const o=document.createElement('option');o.value=i;o.textContent=`${i+1}. ${p.name}`;gardenSelect.append(o);});
// Carry existing completion records forward when opening from the same origin.
try{if(!localStorage.getItem(STORE)){const old=localStorage.getItem('firefly:wide:v1');if(old)localStorage.setItem(STORE,old);}}catch{}
function persistWalk(){if(changingWalk)return;walks[puzzle().id]={state:[...state],moves,hints};try{localStorage.setItem(PROGRESS,JSON.stringify(walks));localStorage.setItem(PROGRESS+':last',String(puzzleIndex));}catch{document.querySelector('.footer-note').textContent='Saving is unavailable in this browser. You can still enjoy the garden.';}}
function libraryStatus(){gardenSelect.value=String(puzzleIndex);let complete={};try{complete=JSON.parse(localStorage.getItem(STORE)||'{}')||{};}catch{}const count=DATA.puzzles.filter(p=>Object.hasOwn(complete,p.id)).length;document.getElementById('collectionProgress').textContent=`${count} of ${DATA.puzzles.length} gardens glowing`;}
const companionRender=render;
render=function(){companionRender();persistWalk();libraryStatus();};
const companionReset=reset;
reset=function(nextIndex){
 const restart=nextIndex===undefined,target=restart?puzzleIndex:nextIndex;
 if(!Number.isInteger(target)||target<0||target>=DATA.puzzles.length)return;
 persistWalk();changingWalk=true;
 companionReset(target);
 const entry=walks[puzzle().id];
 if(!restart&&entry&&Array.isArray(entry.state)&&entry.state.length===puzzle().size**2&&entry.state.every((v,i)=>Number.isInteger(v)&&v>=0&&v<=2&&(!flowerMap().has(key(Math.floor(i/puzzle().size),i%puzzle().size))||v===0))){
  state=[...entry.state];moves=Number.isInteger(entry.moves)&&entry.moves>=0?entry.moves:0;hints=Number.isInteger(entry.hints)&&entry.hints>=0?entry.hints:0;
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
