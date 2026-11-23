import {RaceRenderer} from './race-renderer.js';
import {RaceRenderer as V4} from '../v4/race-renderer.js';
import {raceState} from '../v3/scenarios.js';
import {sizes,names,timing,count,sampleRace} from './device-benchmark.js';

const el=id=>document.getElementById(id);
const version=new URLSearchParams(location.search).get('version')==='v4'?'v4':'v4.1';
const canvas=el('scene'),profile=el('profile');
let lab,selected='mixed100',playing=true,manual=false,running=false,last=null,time=0,intervals=[],lastHUD=0,measurement=null;
profile.value=matchMedia('(max-width:600px)').matches?'mobile':'desktop';
el(version==='v4'?'old':'current').setAttribute('aria-current','page');

function hud(m,rate){
 el('fps').textContent=rate.fps?.toFixed(1)??'—';
 el('p95').textContent=rate.p95_ms==null?'—':rate.p95_ms.toFixed(1)+' ms';
 el('actors').textContent=String(count(m));
 el('lod').textContent=`近 ${m.near}　中 ${m.mid}　移行 ${m.transition}　遠 ${m.sprite}`;
}
function controls(){
 for(const b of el('cases').children){b.disabled=running||!lab;b.setAttribute('aria-pressed',String(b.value===selected));}
 for(const id of ['run','play','profile','device'])el(id).disabled=running||!lab;
 el('save').disabled=!measurement||running;
 el('play').textContent=playing?'一時停止':'再生';el('case-name').textContent=names[selected];
}
function resetClock(){last=null;intervals=[];lastHUD=0;}
function preview(){
 const s=sizes[profile.value];lab.renderer.fixedRaster=s;
 canvas.classList.toggle('mobile',profile.value==='mobile');
 Object.assign(lab.state,raceState(selected,time/3,s.width,s.height,lab.meta));lab.draw();
}
function tick(now){
 if(!manual&&!running&&!document.hidden){
  if(playing){
   if(last!=null){const dt=now-last;intervals.push(dt);if(intervals.length>48)intervals.shift();time+=dt/1000;}
   last=now;preview();
   if(now-lastHUD>240){hud(lab.renderer.mix,timing(intervals));lastHUD=now;}
  }
 }
 requestAnimationFrame(tick);
}
el('cases').onclick=e=>{if(!names[e.target.value]||running)return;selected=e.target.value;time=0;resetClock();preview();hud(lab.renderer.mix,timing([]));controls();};
el('play').onclick=()=>{playing=!playing;resetClock();controls();if(!playing)hud(lab.renderer.mix,timing([]));};
profile.onchange=()=>{resetClock();preview();hud(lab.renderer.mix,timing([]));};
document.addEventListener('visibilitychange',resetClock);
el('save').onclick=()=>{
 if(!measurement)return;
 const url=URL.createObjectURL(new Blob([JSON.stringify(measurement,null,1)],{type:'application/json'}));
 const a=document.createElement('a');a.href=url;a.download='evowild-'+version+'-'+measurement.profile+'-'+measurement.started_at.replace(/[:.]/g,'-')+'.json';
 document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),30000);
};
el('run').onclick=async()=>{
 if(running||!lab)return;
 const ac=new AbortController(),hide=()=>{if(document.hidden)ac.abort();},lost=()=>ac.abort();
 document.addEventListener('visibilitychange',hide);canvas.addEventListener('webglcontextlost',lost);
 const saved=selected;running=true;measurement=null;controls();el('results').replaceChildren();
 const raster=sizes[profile.value],r=lab.renderer,g=r.gl,ext=g.getExtension('WEBGL_debug_renderer_info');
 r.fixedRaster=raster;
 const data={schema_version:1,version,profile:profile.value,started_at:new Date().toISOString(),device_label:el('device').value,
  user_agent:navigator.userAgent,renderer:ext?g.getParameter(ext.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER),
  dpr:devicePixelRatio,viewport:[innerWidth,innerHeight],raster,antialias:g.getContextAttributes().antialias,
  measurement:'48 fixed race states, 3 warmups per case; RAF completion interval; 1 centre RGBA8 pixel read per draw; no CPU throttle requested by this page',
  rows:[]};
 try{
  for(const key of ['mixed50','mixed100']){
   selected=key;controls();el('loading').textContent=names[key]+'　素材を準備中…';
   data.rows.push(await sampleRace(lab,key,raster,samples=>{
    if(samples.length%6===0||samples.length===1){
     hud(r.mix,timing(samples.map(s=>s.interval_ms)));el('loading').textContent=names[key]+'　'+samples.length+' / 48';
    }
   },ac.signal));
  }
  data.finished_at=new Date().toISOString();measurement=data;
  el('results').innerHTML='<table><thead><tr><th>条件</th><th>平均 FPS</th><th>p95</th><th>GPU平均</th></tr></thead><tbody>'+
   data.rows.map(row=>`<tr><td>${names[row.scenario]}</td><td>${row.fps.toFixed(2)}</td><td>${row.p95_ms.toFixed(1)} ms</td><td>${row.gpu_ms===null?'未取得':row.gpu_ms.toFixed(1)+' ms'}</td></tr>`).join('')+'</tbody></table>';
  el('loading').textContent='測定完了。全96フレームをJSONで保存できます。 GPU：'+data.renderer;
 }catch(e){el('loading').textContent=e.message;}
 finally{document.removeEventListener('visibilitychange',hide);canvas.removeEventListener('webglcontextlost',lost);running=false;selected=saved;resetClock();controls();if(!g.isContextLost()){preview();hud(r.mix,timing([]));}}
};
async function boot(){
 controls();
 const json=async url=>{const resp=await fetch(url);if(!resp.ok)throw Error('取得失敗 '+url);return resp.json();};
 const meta=await json(new URL('../v3/assets/manifest.json',import.meta.url));
 const atlas=await json(new URL('../v2/assets/angles/index.json',import.meta.url));
 const Renderer=version==='v4'?V4:RaceRenderer;
 const r=new Renderer(canvas,meta,atlas,err=>{if(err)el('loading').textContent='方位素材を読み込めませんでした。';});
 await r.surface.load();
 const state={...raceState(selected,0,sizes[profile.value].width,sizes[profile.value].height,meta)};
 lab={meta,renderer:r,state,draw:()=>r.draw(state),ready:async()=>{},manual:v=>{manual=v;if(v)r.fixedRaster=null;resetClock();}};
 window.sLab=lab;preview();controls();el('loading').textContent='観察中の表示は直近48フレーム。実測値は「2条件を測定」で記録します。';
 requestAnimationFrame(tick);
}
boot().catch(e=>{el('loading').textContent=e.message;console.error(e);});
