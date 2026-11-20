import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';
const mode=process.argv[2]||'v1';
const layers=Number(process.argv[3]||128);
if(![64,128].includes(layers))throw Error('Expected 64 or 128');
const out=path.join(DEMO,'v2/evidence');
const rows=[];
for(const mobile of [false,true]){
 process.env.LAB_URL='http://127.0.0.1:4173/s-pixel-lab/'+(mode==='v1'?'':'v2/');
 const {page,browser,errors}=await openLab(mobile?{width:390,height:844}:{width:1280,height:900},mobile);
 try{
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:mobile?4:1});
  await page.evaluate(m=>{
    sLab.manual(true);const c=sLab.renderer.canvas;c.style.width=(m?352:877)+'px';c.style.height=(m?335:414)+'px';
  },mobile);
  await page.evaluate(n=>sLab.selectLayers(n),layers);
  for(const method of (mode==='v1'?['v1']:['stack','lod'])){
   if(method==='lod')await page.evaluate(()=>sLab.renderer.sprites.load(1));
   for(const number of [1,10,50,100]){
    const row=await page.evaluate(async ({number,method,layers})=>{
     const r=sLab.renderer,gl=r.gl;
     const ext=gl.getExtension('EXT_disjoint_timer_query_webgl2'),info=gl.getExtension('WEBGL_debug_renderer_info');
     Object.assign(sLab.state,{number,layers,samples:24,idle:false,course:false,time:0,yaw:-22,tilt:12,method,magnification:1});
     const methods=['drawElementsInstanced','drawArrays','drawArraysInstanced'],originals=methods.map(k=>gl[k]);
     let calls=0,triangles=0,blits=0;const blit=gl.blitFramebuffer;gl.blitFramebuffer=function(...args){blits++;return blit.apply(this,args);};
     methods.forEach((k,i)=>{gl[k]=function(...args){calls++;triangles+=(k==='drawElementsInstanced'?args[1]*args[4]:args[2]*(args[3]||1))/3;return originals[i].apply(this,args);};});
     const raf=()=>new Promise(requestAnimationFrame),pixel=new Uint8Array(4);
     const intervals=[],submit=[],complete=[],queries=[],gpu=[],mix=[];
     function frame(t,measure){
      calls=0;triangles=0;blits=0;sLab.state.time=t/1000;
      const query=measure&&ext?gl.createQuery():null;
      if(query)gl.beginQuery(ext.TIME_ELAPSED_EXT,query);
      const a=performance.now();sLab.draw();const b=performance.now();
      if(query){gl.endQuery(ext.TIME_ELAPSED_EXT);queries.push(query);}
      gl.readPixels(gl.drawingBufferWidth>>1,gl.drawingBufferHeight>>1,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);
      if(measure){submit.push(b-a);complete.push(performance.now()-a);mix.push(r.mix||null);}
     }
     for(let i=0;i<3;i++)frame(await raf(),false);
     let last=performance.now(),start=last;
     do{frame(await raf(),true);const end=performance.now();intervals.push(end-last);last=end;}
     while((last-start<1200 || intervals.length<5)&&intervals.length<120);
     if(queries.length){for(let i=0;i<20&&!gl.getQueryParameter(queries.at(-1),gl.QUERY_RESULT_AVAILABLE);i++)await raf();
       const valid=!gl.getParameter(ext.GPU_DISJOINT_EXT);
       for(const q of queries){if(valid&&gl.getQueryParameter(q,gl.QUERY_RESULT_AVAILABLE))gpu.push(gl.getQueryParameter(q,gl.QUERY_RESULT)/1e6);gl.deleteQuery(q);}
     }
     gl.blitFramebuffer=blit;methods.forEach((k,i)=>gl[k]=originals[i]);
     let buffers=0;
     for(const m of r.mesh.values()){
       gl.bindVertexArray(m.vao);gl.bindBuffer(gl.ARRAY_BUFFER,m.vb);buffers+=gl.getBufferParameter(gl.ARRAY_BUFFER,gl.BUFFER_SIZE)+gl.getBufferParameter(gl.ELEMENT_ARRAY_BUFFER,gl.BUFFER_SIZE);
     }
     gl.bindVertexArray(null);
     const avg=a=>a.length?+(a.reduce((x,y)=>x+y,0)/a.length).toFixed(3):null;
     return {method,number,layers,width:r.canvas.width,height:r.canvas.height,frames:intervals.length,
       fps:+(1000*intervals.length/(last-start)).toFixed(2),p95_ms:+[...intervals].sort((a,b)=>a-b)[Math.ceil(intervals.length*.95)-1].toFixed(2),submit_ms:avg(submit),draw_sync_ms:avg(complete),gpu_ms:avg(gpu),gpu_samples:gpu.length,
       triangles,draw_calls:calls,blits,aux_mib:+(((r.coverage?.bytes||0)+(r.floorW||0)*(r.floorH||0)*4)/1048576).toFixed(2),mesh_mib:+(buffers/1048576).toFixed(2),atlas_mib:+((r.atlasBytes||0)/1048576).toFixed(2),mix:mix.at(-1),intervals_ms:intervals.map(x=>+x.toFixed(2)),renderer:info?gl.getParameter(info.UNMASKED_RENDERER_WEBGL):'unknown'};
    },{number,method,layers});
    const heap=await cdp.send('Runtime.getHeapUsage');row.js_heap_mib=+(heap.usedSize/1048576).toFixed(2);
    rows.push({profile:mobile?'mobile-4x':'desktop-1x',...row});console.log(mode,mobile,method,number,row.fps,row.triangles,row.draw_calls,row.gpu_ms);
   }
  }
  if(mode==='v1'&&!mobile&&layers===128){
   // Isolate the cost of submitting all 100 instances, a single instance of each
   // same pose group, and zero creature triangles. Same world, floor and shadows.
   const result=await page.evaluate(async()=>{
    const gl=sLab.renderer.gl,original=gl.drawElementsInstanced,pixel=new Uint8Array(4),out=[];
    for(const cap of [100,1,0]){
     let tris=0;gl.drawElementsInstanced=function(mode,count,type,offset,n){tris+=count/3*Math.min(n,cap);return original.call(gl,mode,count,type,offset,Math.min(n,cap));};
     const times=[];for(let i=0;i<9;i++){await new Promise(requestAnimationFrame);tris=0;sLab.state.time=i*.03;const t=performance.now();sLab.draw();gl.readPixels(400,200,1,1,gl.RGBA,gl.UNSIGNED_BYTE,pixel);if(i>1)times.push(performance.now()-t);}
     out.push({instance_cap_per_pose:cap,last_runner_triangles:tris,draw_sync_ms:times.reduce((a,b)=>a+b)/times.length});
    }
    gl.drawElementsInstanced=original;return out;
   });await fs.writeFile(path.join(out,'bottleneck.json'),JSON.stringify(result,null,2));
  }
  if(errors.length)throw Error(errors.join('\n'));
  await fs.writeFile(path.join(out,mode+(layers===128?'':'-'+layers)+'-measurement.json'),JSON.stringify({chromium:browser.version(),rows},null,1));
 }finally{await browser.close();}
}
