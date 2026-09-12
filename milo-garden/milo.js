'use strict';
// Wide Garden's companion layer. The puzzle rules and saved result IDs stay intact.
const companion=document.createElement('section');
companion.className='milo-companion';companion.setAttribute('aria-label','Milo, your garden companion');
companion.innerHTML='<img id="miloPortrait" src="milo-sitting.png" alt="Milo, a chestnut Irish setter puppy, sitting beside a firefly"><div class="milo-copy"><h2 id="miloTitle">An evening with Milo</h2><p id="miloWords">He’s found a quiet spot. Let’s watch the little lights together.</p></div>';
document.querySelector('.layout').prepend(companion);
const ending=document.createElement('div');ending.className='evening-end';ending.hidden=true;ending.innerHTML='<p>The garden is glowing. Milo is already dreaming.</p><button class="action primary" id="eveningWalk">Another evening walk</button>';
document.querySelector('.side').append(ending);
$('#eveningWalk').onclick=()=>reset((puzzleIndex+1)%DATA.puzzles.length);
for(const src of ['milo-paw.png','milo-sleepy.png']){const preload=new Image();preload.src=src;}
let previousSettled=0,poseTimer;
function miloPose(pose){const image=$('#miloPortrait');const src=`milo-${pose}.png`;if(image.getAttribute('src')!==src)image.src=src;image.alt={sitting:'Milo sitting quietly, watching a firefly',paw:'Milo gently lifting a paw beside the glowing garden',sleepy:'Milo curled up asleep among softly glowing flowers'}[pose];}
function updateMilo(){
 clearTimeout(poseTimer);
 if(finished){miloPose('sleepy');$('#miloTitle').textContent='A good place to rest';$('#miloWords').textContent='Every little light is home. Stay here with Milo for a while.';ending.hidden=false;$('#hintButton').disabled=true;$('#undoButton').disabled=true;return;}
 ending.hidden=true;$('#hintButton').disabled=false;
 const p=puzzle(),bad=conflicts(),flies=placed();
 const settled=Array.from({length:p.size},(_,region)=>flies.filter(([r,c])=>p.regions[r][c]===region)).filter(group=>group.length===1&&!bad.has(key(...group[0]))).length;
 if(settled>previousSettled){miloPose('paw');$('#miloTitle').textContent='Something caught his eye';$('#miloWords').textContent='A little glow, a lifted paw. Milo is keeping you company.';poseTimer=setTimeout(()=>{if(!finished){miloPose('sitting');$('#miloTitle').textContent='An evening with Milo';$('#miloWords').textContent='There’s no hurry. He’s happy to sit a little longer.';}},2200);}else{miloPose('sitting');$('#miloTitle').textContent='An evening with Milo';$('#miloWords').textContent='There’s no hurry. He’s happy to sit a little longer.';}
 previousSettled=settled;
}
checkWin=function(){if(!finished&&solved()){finished=true;save();} };
showResults=function(){updateMilo();};
const gardenRender=render;
render=function(){gardenRender();updateMilo();};
const gardenReset=reset;
reset=function(index=puzzleIndex){clearTimeout(poseTimer);previousSettled=0;gardenReset(index);};
const gardenFeedback=setFeedback;
setFeedback=function(message,kind=''){
 if(finished){gardenFeedback('The garden is glowing. Milo has settled down beside you.','good');return;}
 if(kind==='error'){message=message.startsWith('The firefly at row')?message.replace('The firefly','This little light').replace('cannot satisfy all the clues.','needs another spot.'): 'This little light needs another spot. Check its row, habitat, and nearby flowers.';}
 gardenFeedback(message,kind);
};
updateMilo();
