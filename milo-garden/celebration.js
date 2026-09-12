'use strict';
const celebration=document.createElement('dialog');
celebration.className='milo-celebration';celebration.setAttribute('aria-labelledby','celebrationTitle');
celebration.innerHTML='<div class="celebration-sparkles" aria-hidden="true"></div><img src="milo-sleepy.png" alt="Milo curled up asleep in the glowing garden"><div class="celebration-copy"><p class="eyebrow">Every little light is home</p><h2 id="celebrationTitle">Garden complete!</h2><p id="celebrationGarden"></p><p>You found every firefly. Milo couldn’t wish for a cozier place to rest.</p><div class="actions"><button class="action primary" id="enjoyGarden" autofocus>Enjoy my garden</button><button class="action secondary" id="celebrationNext">Another evening walk</button></div></div>';
document.body.append(celebration);
let celebrationReturnFocus;
function celebrate(){
 if(!finished||celebration.open)return;
 celebrationReturnFocus=document.activeElement;
 document.getElementById('celebrationGarden').textContent=`${puzzle().name} · Walk ${puzzleIndex+1} of ${DATA.puzzles.length}`;
 const sparkles=celebration.querySelector('.celebration-sparkles');sparkles.replaceChildren();
 if(!window.matchMedia('(prefers-reduced-motion: reduce)').matches){
  for(let i=0;i<32;i++){const piece=document.createElement('i');piece.style.setProperty('--x',`${(i*37)%100}%`);piece.style.setProperty('--delay',`${(i%8)*.08}s`);piece.style.setProperty('--turn',`${i%2?1:-1}turn`);sparkles.append(piece);}
 }
 celebration.showModal();
}
document.getElementById('enjoyGarden').onclick=()=>celebration.close();
document.getElementById('celebrationNext').onclick=()=>{celebration.close();reset((puzzleIndex+1)%DATA.puzzles.length);};
celebration.addEventListener('close',()=>{celebration.querySelector('.celebration-sparkles').replaceChildren();if(celebrationReturnFocus?.isConnected)celebrationReturnFocus.focus({preventScroll:true});});
const placeWithMilo=play;
play=function(index,reverse=false){const wasFinished=finished;placeWithMilo(index,reverse);if(!wasFinished&&finished)celebrate();};
const replayCelebration=document.createElement('button');replayCelebration.className='action secondary';replayCelebration.textContent='Garden complete · Celebrate';replayCelebration.onclick=celebrate;ending.append(replayCelebration);
