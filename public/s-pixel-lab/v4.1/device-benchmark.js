import {raceState} from '../v3/scenarios.js';
export const sizes={desktop:{width:877,height:414},mobile:{width:352,height:335}};
export const names={near1:'近景1体',near10:'近景10体',mixed50:'混在50体',mixed100:'混在100体',overview100:'全景100体'};
export const nextFrame=()=>new Promise(requestAnimationFrame);
const avg=a=>a.reduce((sum,v)=>sum+v,0)/a.length;
export function timing(intervals){
 if(!intervals.length)return {fps:null,p95_ms:null};
 const sorted=[...intervals].sort((a,b)=>a-b);
 return {fps:1000/avg(intervals),p95_ms:sorted[Math.ceil(.95*sorted.length)-1]};
}
export function count(m){return m.near+m.mid+m.transition+m.sprite;}
export async function sampleRace(lab,key,raster,onProgress,signal){
 const r=lab.renderer,g=r.gl,{width,height}=raster;
 const states=Array.from({length:48},(_,i)=>raceState(key,i/48,width,height,lab.meta));
 const ext=g.getExtension('EXT_disjoint_timer_query_webgl2'),pixel=new Uint8Array(4),queries=[],samples=[];
 const check=()=>{if(signal.aborted)throw Error('測定を中断しました。タブを前面に戻して再計測してください。');if(g.isContextLost())throw Error('WebGLコンテキストを失いました。ページを再読込してください。');};
 // A hidden tab can suspend requestAnimationFrame indefinitely. Reject even
 // when no further frame is delivered, and remove the abort listener on exit.
 const frame=()=>new Promise((resolve,reject)=>{
  check();
  const cancel=()=>{cancelAnimationFrame(id);reject(Error('タブが非表示になったため測定を中断しました。'));};
  const id=requestAnimationFrame(t=>{signal.removeEventListener('abort',cancel);resolve(t);});
  signal.addEventListener('abort',cancel,{once:true});
 });
 for(const bank of new Set(states.map(s=>Math.round(s.tilt/10))))await r.sprites.load(bank);
 function draw(state,timed){
  check();Object.assign(lab.state,state);
  const q=ext&&timed?g.createQuery():null;if(q){g.beginQuery(ext.TIME_ELAPSED_EXT,q);queries.push({q,i:samples.length});}
  const start=performance.now();
  let tris;try{tris=lab.draw();}finally{if(q)g.endQuery(ext.TIME_ELAPSED_EXT);}
  const submit=performance.now();
  if(r.canvas.width!==width||r.canvas.height!==height)throw Error('描画バッファ寸法が指定値と異なります。');
  g.readPixels(width>>1,height>>1,1,1,g.RGBA,g.UNSIGNED_BYTE,pixel);
  const end=performance.now();
  if(timed)samples.push({i:samples.length,time:state.time,yaw:state.yaw,tilt:state.tilt,magnification:state.magnification,
    submit_ms:submit-start,sync_ms:end-start,triangles:tris,drawn:count(r.mix),mix:{...r.mix},gpu_ms:null});
  return end;
 }
 try{
  for(const s of states.slice(0,3)){await frame();draw(s,false);}
  let previous=performance.now();
  for(const s of states){
   await frame();const end=draw(s,true);samples.at(-1).interval_ms=end-previous;previous=end;
   onProgress(samples);
  }
  if(queries.length){
   for(let i=0;i<60&&!g.getQueryParameter(queries.at(-1).q,g.QUERY_RESULT_AVAILABLE);i++)await frame();
   if(!g.getParameter(ext.GPU_DISJOINT_EXT))queries.forEach(({q,i})=>{
    if(g.getQueryParameter(q,g.QUERY_RESULT_AVAILABLE))samples[i].gpu_ms=g.getQueryParameter(q,g.QUERY_RESULT)/1e6;
   });
  }
  check();if(g.getError()!==g.NO_ERROR)throw Error('WebGL計測中にエラーが発生しました。');
  const gpu=samples.map(s=>s.gpu_ms).filter(Number.isFinite);
  return {scenario:key,width,height,frames:samples.length,...timing(samples.map(s=>s.interval_ms)),
   gpu_ms:gpu.length?avg(gpu):null,gpu_samples:gpu.length,samples};
 }finally{for(const {q} of queries)g.deleteQuery(q);}
}
