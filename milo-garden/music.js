'use strict';
// Original, locally synthesized 32-bar music; no recordings, streaming or autoplay.
(()=>{
 const button=document.getElementById('musicToggle'),slider=document.getElementById('musicVolume'),status=document.getElementById('musicStatus');
 let request=0;let ctx,master,timer=null,wanted=false,beat=0,nextTime=0,voices=new Set();
 const chords=[[50,57,61,66],[47,54,57,62],[43,50,54,59],[45,52,57,61]];
 const pattern=[0,2,1,3,2,1,3,2];
 try{const v=Number(localStorage.getItem('milo:music:volume')??30);if(Number.isFinite(v))slider.value=String(Math.max(0,Math.min(100,v)));}catch{}
 function note(midi,time,duration,gain){
  const osc=ctx.createOscillator(),env=ctx.createGain();osc.type='sine';osc.frequency.value=440*2**((midi-69)/12);
  env.gain.setValueAtTime(0,time);env.gain.linearRampToValueAtTime(gain,time+.08);env.gain.exponentialRampToValueAtTime(.0001,time+duration);
  osc.connect(env);env.connect(master);osc.start(time);osc.stop(time+duration+.05);voices.add(osc);osc.onended=()=>{voices.delete(osc);osc.disconnect();env.disconnect();};
 }
 function schedule(){if(!wanted||document.hidden)return;while(nextTime<ctx.currentTime+.25){const chord=chords[Math.floor(beat/8)%4];note(chord[pattern[beat%8]]+12,nextTime,2.5,.12);if(beat%8===0){note(chord[0],nextTime,7.3,.16);note(chord[2],nextTime,6.8,.055);}beat=(beat+1)%256;nextTime+=.9;}timer=setTimeout(schedule,100);}
 function stop(){request++;clearTimeout(timer);timer=null;if(ctx){for(const v of voices){try{v.stop();}catch{}}voices.clear();}}
 async function start(){
  const current=++request;
  try{ctx ||= new(window.AudioContext||window.webkitAudioContext)();if(!master){master=ctx.createGain();master.connect(ctx.destination);}master.gain.value=Number(slider.value)/100*.7;await ctx.resume();if(current!==request||!wanted||document.hidden)return;if(ctx.state!=='running')throw Error('Audio not available');nextTime=ctx.currentTime+.08;schedule();status.textContent='';}
  catch{wanted=false;button.setAttribute('aria-pressed','false');button.textContent='♫ Music off';status.textContent='Music couldn’t start. Tap to try again.';}
 }
 button.onclick=()=>{wanted=!wanted;button.setAttribute('aria-pressed',String(wanted));button.textContent=wanted?'♫ Music on':'♫ Music off';if(wanted)start();else{stop();status.textContent='';}};
 slider.oninput=()=>{if(master)master.gain.setTargetAtTime(Number(slider.value)/100*.7,ctx.currentTime,.08);try{localStorage.setItem('milo:music:volume',slider.value);}catch{}};
 document.addEventListener('visibilitychange',()=>{stop();if(wanted&&!document.hidden)start();});
 window.addEventListener('pagehide',stop);window.addEventListener('pageshow',()=>{if(wanted&&!timer&&!document.hidden)start();});
})();
