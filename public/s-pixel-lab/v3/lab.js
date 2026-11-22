import {RaceRenderer} from './race-renderer.js';
import {raceState} from './scenarios.js';
const $=id=>document.getElementById(id);
const defaults={yaw:-27,tilt:12,number:1,layers:128,samples:24,course:false,idle:true,spin:false,playing:false,time:0,zoom:1,mask:false,method:'lod',magnification:1};
const state={...defaults},views=[['side','側面','SIDE',0,0],['front','正面','FRONT',-90,0],['rear','背面','REAR',90,0],['top','上面','TOP',0,90],['quarter','斜め45°','3/4',-45,13]];
let meta,atlas,renderer,ref,selected='',tour=0,manual=false,paired=false;
let previous=0,elapsed=0,frames=0,busy=0;
const stackReady=new WeakMap();
const models={lod:'距離LOD',surface:'表面メッシュ',exact:'原本レイ描画',stack:'断面積層'};
const names={near1:'近景 1体',near10:'近景 10体',mixed50:'混在 50体',mixed100:'混在 100体',overview100:'全景 100体'};
function buttons(id,fn){$(id).onclick=e=>{const b=e.target.closest('button');if(b)fn(b);};}
function active(id,pred){for(const b of $(id).querySelectorAll('button'))b.setAttribute('aria-pressed',String(pred(b)));}
function sync(){
 active('scenario',b=>b.dataset.case===selected);active('method',b=>b.dataset.method===state.method);active('number',b=>Number(b.textContent)===state.number);
 $('play').classList.toggle('running',state.playing);$('play').setAttribute('aria-label',state.playing?'走行を停止':'走行を再生');
 $('spin').setAttribute('aria-pressed',String(state.spin));$('compare').setAttribute('aria-pressed',String(paired));
 for(const k of ['yaw','tilt']){$(k).value=state[k];$(k+'Out').value=Math.round(state[k])+'°';}
 $('magnification').value=state.magnification;$('zoomOut').value=state.magnification.toFixed(2)+'×';
 const f=Math.floor(state.time/(meta?.period||.72)*24+1e-6)%24;
 $('scrub').value=state.idle?0:f;$('frame').innerHTML=(state.idle?'—':String(f+1).padStart(2,'0'))+' <small>/ 24</small>';
 const feet=meta?.poses[1+f]?.feet;const support=feet?Object.entries(feet).filter(([,v])=>v.contact).map(([k])=>({nearF:'左前',farF:'右前',nearH:'左後',farH:'右後'})[k]):[];
 $('phase').textContent=state.idle?'静止姿勢':support.length?'接地 · '+support.join(' / '):'空中局面';
 $('sceneName').textContent=names[selected]||(state.course?'走行コース':'標本ビュー');$('primaryCaption').textContent=models[state.method];
 active('tiles',b=>!state.course&&b.dataset.view===views.find(v=>v[3]===state.yaw&&v[4]===state.tilt)?.[0]);
}
function draw(){
 if(!renderer?.surface.info)return 0;
 const loadingModel=(state.method==='stack'&&!stackReady.get(renderer)?.done)||(state.method==='exact'&&!renderer.exact?.index);
 const tris=renderer.draw(loadingModel?{...state,method:'surface'}:state);
 if(paired&&ref&&stackReady.get(ref)?.done)ref.draw({...state,method:'stack'});
 const m=renderer.mix;
 const summary=`近 ${m.near}　中 ${m.mid||0}　移行 ${m.transition||0}　遠 ${m.sprite}`+(m.offscreen?`　画面外 ${m.offscreen}`:'');
 if($('lodCounts').textContent!==summary)$('lodCounts').textContent=summary;
 return tris;
}
function ensureStack(target=renderer){
 if(stackReady.has(target))return stackReady.get(target).promise;
 const entry={done:false};stackReady.set(target,entry);
 entry.promise=new Promise((resolve,reject)=>{
  const worker=new Worker(new URL('./sections.js',import.meta.url));let i=0;
  const fail=reason=>{worker.terminate();stackReady.delete(target);reject(Error(reason));};
  worker.onerror=e=>fail(e.message);worker.onmessage=({data})=>{
   if(data.error){fail(data.error);return;}target.add(data);
   if(++i<meta.poses.length){worker.postMessage({count:128,pose:i});return;}
   worker.terminate();entry.done=true;resolve();
  };worker.postMessage({pose:0,count:128,meta});
 });return entry.promise;
}
function ready(){return Promise.all([state.method==='stack'?ensureStack():null,state.method==='exact'?renderer.loadExact():null,paired&&ref?ensureStack(ref):null]);}
function makeRenderer(canvas){
 const r=new RaceRenderer(canvas,meta,atlas,err=>{if(err)$('loading').textContent='方位素材の読込に失敗しました。表面メッシュで表示します。';draw();});
 canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();manual=true;$('loading').textContent='WebGLの復旧を待っています。';});canvas.addEventListener('webglcontextrestored',()=>location.reload());return r;
}
async function update(action){
 const generation=++busy;
 try{action();sync();if((state.method==='stack'&&!stackReady.get(renderer)?.done)||(paired&&!stackReady.get(ref)?.done))$('loading').textContent='断面を組み立て中…';await ready();if(generation===busy){$('loading').textContent='';draw();}}
 catch(error){$('loading').textContent=error.message;console.error(error);}
}
function setScenario(key){selected=key;tour=0;Object.assign(state,raceState(key,0,renderer.canvas.clientWidth,renderer.canvas.clientHeight,meta));previous=0;}
function freeCamera(){selected='';state.spin=false;}
buttons('scenario',b=>update(()=>setScenario(b.dataset.case)));buttons('method',b=>update(()=>{state.method=b.dataset.method;}));
buttons('number',b=>update(()=>{freeCamera();state.number=Number(b.textContent);}));
$('compare').onclick=()=>update(()=>{
 paired=!paired;if(paired&&!ref)ref=makeRenderer($('reference'));$('stage').classList.toggle('paired',paired);$('reference').parentElement.hidden=!paired;
 if(paired&&state.method==='stack')state.method='surface';
});
$('reset').onclick=()=>update(()=>{Object.assign(state,defaults);selected='';paired=false;$('stage').classList.remove('paired');$('reference').parentElement.hidden=true;});
$('play').onclick=()=>{state.playing=!state.playing;state.idle=false;previous=0;sync();draw();};
$('idle').onclick=()=>{freeCamera();Object.assign(state,{time:0,playing:false,idle:true});sync();draw();};
$('spin').onclick=()=>{selected='';state.spin=!state.spin;sync();};
for(const k of ['yaw','tilt','magnification'])$(k).oninput=e=>{freeCamera();state[k]=Number(e.target.value);sync();draw();};
$('scrub').oninput=e=>{freeCamera();Object.assign(state,{time:Number(e.target.value)*meta.period/24,idle:false,playing:false});sync();draw();};
for(const [key,name,en,yaw,tilt] of views){const b=document.createElement('button');b.className='tile';b.dataset.view=key;b.innerHTML=`<img src="${new URL(key+'.png',new URL(document.body.dataset.viewImages || './assets/views/',import.meta.url))}" alt=""><span>${name}<small>${en}</small></span>`;b.onclick=()=>{freeCamera();Object.assign(state,{number:1,course:false,magnification:1,yaw,tilt});sync();draw();};$('tiles').append(b);}
for(const id of ['scene','reference']){
 const c=$(id);let drag;c.onpointerdown=e=>{drag=[e.clientX,e.clientY,state.yaw,state.tilt];c.setPointerCapture(e.pointerId);};
 c.onpointermove=e=>{if(!drag)return;freeCamera();state.yaw=((drag[2]+(e.clientX-drag[0])*.48+540)%360)-180;state.tilt=Math.max(0,Math.min(90,drag[3]-(e.clientY-drag[1])*.33));sync();draw();};c.onlostpointercapture=()=>{drag=null;};
}
async function boot(){
 const controls=document.querySelectorAll('main button,main input');
 for(const el of controls)el.disabled=true;
 const assetUrl=new URL('./assets/directions.json',import.meta.url);
 const json=async url=>{const r=await fetch(url);if(!r.ok)throw Error(`${r.status} ${url}`);return r.json();};
 const [manifest,directions]=await Promise.all([json(new URL('./assets/manifest.json',import.meta.url)),json(assetUrl)]);meta=manifest;
 const indexUrl=new URL(directions.index,assetUrl);atlas=await json(indexUrl);
 const root=new URL('../',import.meta.url);
 for(const bank of atlas.angles)for(const file of bank.files)for(const f of [0,3]){
  const page=new URL(file[f],indexUrl);if(page.origin!==root.origin||!page.pathname.startsWith(root.pathname))throw Error('方位素材の格納先が不正です');
  file[f]='../../../'+page.pathname.slice(root.pathname.length);
 }
 renderer=makeRenderer($('scene'));await renderer.surface.load();for(const el of controls)el.disabled=false;$('loading').textContent='';$('live').querySelector('b').textContent='READY';sync();draw();
 window.sLab={state,meta,renderer,views,draw,sync,ready,ensureStack,selectLayers:ensureStackFor128,manual:v=>{manual=v;previous=0;}};
 function ensureStackFor128(n){if(n!==128)throw Error('積層比較は128層です');return ensureStack();}
 new ResizeObserver(()=>{if(!manual)draw();}).observe($('scene'));
 function tick(now){const dt=previous?(now-previous)/1000:0;previous=now;
  if(!manual&&(state.playing||state.spin)){
   if(selected&&state.playing){tour+=dt;const phase=tour/3;const settings=raceState(selected,phase,renderer.canvas.clientWidth,renderer.canvas.clientHeight,meta);const keep=state.method;Object.assign(state,settings,{method:keep});}
   else{if(state.playing)state.time+=dt;if(state.spin)state.yaw=((state.yaw+dt*40+540)%360)-180;}
   sync();draw();
  }
  if(!manual){elapsed+=dt;frames++;if(elapsed>=.65){$('live').querySelector('b').textContent=state.playing||state.spin?Math.round(frames/elapsed)+' FPS':'READY';frames=elapsed=0;}}
  requestAnimationFrame(tick);
 }requestAnimationFrame(tick);
}
boot().catch(e=>{$('loading').textContent=e.message;console.error(e);});
