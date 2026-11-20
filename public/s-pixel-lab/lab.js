import {SectionsRenderer} from './renderer.js';
const $=id=>document.getElementById(id);
const defaults={yaw:-22,tilt:12,number:1,layers:128,samples:24,course:false,idle:true,spin:false,playing:false,time:0,zoom:1,mask:false};
const state={...defaults};
const views=[
 ['side','側面','SIDE',0,0],['front','正面','FRONT',-90,0],['rear','背面','REAR',90,0],
 ['top','上面','TOP',0,90],['quarter','斜め45°','3/4',-45,13]
];
let renderer,meta,loading=false,manual=false,version=0;
let loadedCount=0, completion=Promise.resolve(), elapsed=0,frames=0,previous=0;
function pressed(group,key,fn=b=>Number(b.textContent)){
 for(const b of $(group).querySelectorAll('button'))b.setAttribute('aria-pressed',String(fn(b)===key));
}
function sync(){
 for(const key of ['layers','number','samples'])pressed(key,state[key]);
 pressed('mode',Number(state.course),b=>Number(b.dataset.v));
 $('spin').setAttribute('aria-pressed',String(state.spin));$('play').classList.toggle('running',state.playing);
 $('play').setAttribute('aria-label',state.playing?'走行を停止':'走行を再生');
 for(const k of ['yaw','tilt']){$(k).value=state[k];$(k+'Out').textContent=Math.round(state[k])+'°';}
 const f=Math.floor(state.time/(meta?.period||.72)*state.samples+1e-6)%state.samples;
 $('scrub').max=state.samples-1;$('scrub').value=f;
 $('frame').innerHTML=(state.idle?'—':String(f+1).padStart(2,'0'))+' <small>/ '+state.samples+'</small>';
 const feet=meta?.poses[1+f*(24/state.samples)]?.feet;
 const support=feet&&Object.entries(feet).filter(([,v])=>v.contact).map(([k])=>({nearF:'左前',farF:'右前',nearH:'左後',farH:'右後'})[k]);
 $('phase').textContent=state.idle?'静止姿勢':support?.length?'接地 · '+support.join(' / '):'空中局面';
 [...$('tiles').children].forEach((b,i)=>b.setAttribute('aria-pressed',String(state.yaw===views[i][3]&&state.tilt===views[i][4])));
}
function draw(){if(renderer)return renderer.draw(state);}
let activeWorker=null,resolveCancelled=null;
async function selectLayers(count){
 if(!renderer||count===loadedCount)return completion;
 const token=++version;
 if(activeWorker)activeWorker.terminate();
 if(resolveCancelled)resolveCancelled();
 if(loadedCount)renderer.discard(loadedCount);
 loadedCount=count;state.layers=count;loading=true;sync();
 $('loading').textContent='断面を読み込み中…';
 completion=new Promise((resolve,reject)=>{
   resolveCancelled=resolve;
   const worker=new Worker(new URL('sections.js',import.meta.url));activeWorker=worker;
   const fail=message=>{worker.terminate();$('loading').textContent=message;loading=false;reject(Error(message));};
   worker.onerror=e=>fail(e.message);
   let received=0;
   worker.onmessage=({data})=>{
     if(token!==version)return;if(data.error){fail(data.error);return;}
     renderer.add(data);received++;
     if(received===1&&state.idle){draw();$('loading').textContent='';}
     if(received===meta.poses.length){
       worker.terminate();activeWorker=null;resolveCancelled=null;loading=false;$('loading').textContent='';previous=0;draw();resolve();return;
     }
     worker.postMessage({pose:received,count});
   };
   worker.postMessage({pose:0,count,meta});
 });
 return completion;
}
function play(){state.playing=!state.playing;state.idle=false;previous=0;sync();draw();}
function idle(){state.idle=true;state.playing=false;state.time=0;sync();draw();}
function angles(y,t){
 state.yaw=((y+540)%360)-180;state.tilt=Math.max(0,Math.min(90,t));
 sync();draw();
}
function handleGroup(id,fn){$(id).onclick=e=>{const b=e.target.closest('button');if(b)fn(b);};}
for(const v of views){
 const b=document.createElement('button');b.className='tile';b.innerHTML='<img src="assets/views/'+v[0]+'.png" alt=""><span>'+v[1]+'<small>'+v[2]+'</small></span>';
 b.onclick=()=>{state.spin=false;state.course=false;state.number=1;angles(v[3],v[4]);};
 $('tiles').append(b);
}
handleGroup('layers',b=>{if(renderer)selectLayers(Number(b.textContent));});
for(const k of ['number','samples'])handleGroup(k,b=>{state[k]=Number(b.textContent);sync();draw();});
handleGroup('mode',b=>{state.course=b.dataset.v==='1';if(state.course){state.idle=false;state.playing=true;}sync();draw();});
$('spin').onclick=()=>{state.spin=!state.spin;sync();};
$('play').onclick=play;$('idle').onclick=idle;
$('reset').onclick=()=>{Object.assign(state,defaults);selectLayers(state.layers);sync();draw();};
for(const k of ['tilt','yaw'])$(k).oninput=e=>{state.spin=false;state[k]=Number(e.target.value);sync();draw();};
$('scrub').oninput=e=>{if(!meta)return;state.time=Number(e.target.value)*meta.period/state.samples;state.playing=false;state.idle=false;sync();draw();};
let drag;
$('scene').onpointerdown=e=>{drag=[e.clientX,e.clientY,state.yaw,state.tilt];$('scene').setPointerCapture(e.pointerId);};
$('scene').onpointermove=e=>{if(drag){state.spin=false;angles(drag[2]+(e.clientX-drag[0])*.48,drag[3]+(drag[1]-e.clientY)*.33);}};
$('scene').onlostpointercapture=()=>{drag=null;};
window.addEventListener('keydown',e=>{
 if(e.target.matches('input,button,a'))return;
 if(e.code==='Space'){e.preventDefault();play();}
 if(['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(e.key)){
   e.preventDefault();angles(state.yaw+({ArrowLeft:-5,ArrowRight:5}[e.key]||0),state.tilt+({ArrowUp:3,ArrowDown:-3}[e.key]||0));
 }
});
async function boot(){
 const response=await fetch('assets/manifest.json');if(!response.ok)throw Error('断面の目録を取得できません。');
 meta=await response.json();renderer=new SectionsRenderer($('scene'),meta);
 $('scene').addEventListener('webglcontextlost',e=>{e.preventDefault();$('loading').textContent='描画を中断しました。復旧を待っています。';manual=true;});
 $('scene').addEventListener('webglcontextrestored',()=>location.reload());
 function tick(now){
   const dt=previous?(now-previous)/1000:0;previous=now;
   if(!manual&&!loading){
     if(state.playing)state.time+=Math.min(dt,.20);
     if(state.spin)state.yaw=((state.yaw+dt*40+540)%360)-180;
     if(state.playing||state.spin){sync();draw();}
     elapsed+=dt;frames++;
     if(elapsed>=.6){
       $('live').querySelector('b').textContent=state.playing||state.spin?Math.round(frames/elapsed)+' FPS':'READY';
       elapsed=0;frames=0;
     }
   }
   requestAnimationFrame(tick);
 }
 new ResizeObserver(draw).observe($('scene'));sync();requestAnimationFrame(tick);
 await selectLayers(state.layers);
 // Deterministic capture uses the same renderer, pose selection and camera as the controls.
 window.sLab={state,meta,renderer,views,draw,sync,selectLayers,ready:()=>completion,manual:value=>{manual=value;previous=0;}};
}
boot().catch(e=>{$('loading').textContent=e.message;console.error(e);});
