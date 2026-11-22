// Pass timers run on a separate replay so they never nest the adoption timer.
import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab, DEMO} from '../browser.mjs';
import {raceState} from '../../../public/s-pixel-lab/v3/scenarios.js';
const version=process.argv[2]??'v3';
const transitionOnly=process.argv.includes('--transition');
process.env.LAB_URL=(process.env.LAB_BASE_URL??'http://127.0.0.1:4173/s-pixel-lab/')+version+'/';
const {page,browser,errors}=await openLab({width:1280,height:900});
try {
 const meta=await page.evaluate(async()=>{
  sLab.manual(true); const r=sLab.renderer;
  r.canvas.style.width='877px';r.canvas.style.height='414px';
  for(const bank of [1,2])await r.sprites.load(bank);
  return {period:sLab.meta.period,stride:sLab.meta.stride};
 });
 const result=[];
 for(const key of ['mixed50','mixed100']){
  const states=Array.from({length:48},(_,i)=>raceState(key,i/48,877,414,meta));
  const rows=await page.evaluate(async ({states,transitionOnly})=>{
   const r=sLab.renderer,g=r.gl,ext=g.getExtension('EXT_disjoint_timer_query_webgl2');
   const pixel=new Uint8Array(4), raf=()=>new Promise(requestAnimationFrame);
   const draw=s=>{Object.assign(sLab.state,s);sLab.draw();g.readPixels(0,0,1,1,g.RGBA,g.UNSIGNED_BYTE,pixel);};
   for(const s of states.slice(0,3)){await raf();draw(s);}
   const rows=[],queries=[],restore=[];let row,pass='shadow';
   function wrap(object,key,fn){const prev=object[key];object[key]=function(...args){return fn(prev.bind(this),args);};restore.push(()=>object[key]=prev);}
   function segment(object,key,name){wrap(object,key,(fn,args)=>{
    const q=ext&&g.createQuery();if(q)g.beginQuery(ext.TIME_ELAPSED_EXT,q);
    const before=performance.now();pass=name;const value=fn(...args);pass='shadow';row[name+'_submit']+=performance.now()-before;
    if(q){g.endQuery(ext.TIME_ELAPSED_EXT);queries.push([row,name,q]);}return value;
   });}
   segment(r,'drawFloor','floor');segment(r.surface,'draw','mesh');segment(r.sprites,'draw','sprites');
   // Diagnostic-only isolation. Retain the original camera, classifiers, floor
   // and shadows. Measure the two submissions belonging to fractional LODs.
   if(transitionOnly){
    wrap(r.surface,'draw',(fn,[groups,...rest])=>{
     const partial=new Map();
     for(const [key,b] of groups){
      const places=[];
      for(let i=0;i<b.places.length;i+=6)if(b.places[i+5]<1)places.push(...b.places.slice(i,i+6));
      if(places.length)partial.set(key,{...b,places});
     }
     return fn(partial,...rest);
    });
    wrap(r.sprites,'draw',(fn,[near,groups,...rest])=>{
     const partial=new Map();
     for(const [key,instances] of groups){
      const places=[];
      for(let i=0;i<instances.length;i+=12)if(instances[i+10]<1)places.push(...instances.slice(i,i+12));
      if(places.length)partial.set(key,places);
     }
     return fn(near,partial,...rest);
    });
   }
   wrap(r,'drawActors',(fn,args)=>{const t=performance.now();const result=fn(...args);row.classify_ms=performance.now()-t-row.mesh_submit-row.sprites_submit;return result;});
   for(const method of ['drawArrays','drawElements','drawElementsInstanced','drawArraysInstanced'])wrap(g,method,(fn,args)=>{
    row[pass+'_calls']++; if(pass!=='shadow'||!ext)return fn(...args);
    const q=g.createQuery();g.beginQuery(ext.TIME_ELAPSED_EXT,q);const val=fn(...args);g.endQuery(ext.TIME_ELAPSED_EXT);queries.push([row,'shadow',q]);return val;
   });
   try{
    for(const s of states){await raf();row={};for(const part of ['floor','shadow','mesh','sprites'])for(const field of ['submit','calls','gpu_ms'])row[part+'_'+field]=0;draw(s);row.transition=r.mix.transition;rows.push(row);}
    if(queries.length){for(let i=0;i<60&&!g.getQueryParameter(queries.at(-1)[2],g.QUERY_RESULT_AVAILABLE);i++)await raf();
     if(g.getParameter(ext.GPU_DISJOINT_EXT))throw Error('Disjoint GPU timer');
     for(const [sample,part,q] of queries){if(!g.getQueryParameter(q,g.QUERY_RESULT_AVAILABLE))throw Error('GPU timer unavailable');sample[part+'_gpu_ms']+=g.getQueryParameter(q,g.QUERY_RESULT)/1e6;g.deleteQuery(q);}}
    else throw Error('GPU timer unavailable');
    return rows;
   }finally{for(const undo of restore.reverse())undo();}
  },{states,transitionOnly});
  const mean=Object.fromEntries(Object.keys(rows[0]).map(k=>[k,rows.reduce((sum,r)=>sum+r[k],0)/rows.length]));
  console.log(key,mean);result.push({scenario:key,mean,samples:rows});
 }
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(path.join(DEMO,'v4/evidence',version+(transitionOnly?'-transition-passes.json':'-passes.json')),JSON.stringify(result,null,1)+'\n');
}finally{await browser.close();}
