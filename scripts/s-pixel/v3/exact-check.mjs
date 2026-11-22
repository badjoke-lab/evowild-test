// Validate the sparse voxel intersection against the full 128-slice reference
// at identical camera, pose, phase and single-sample coverage.
import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab, DEMO} from '../browser.mjs';
process.env.LAB_URL ||= 'http://127.0.0.1:4173/s-pixel-lab/v2/';
const {browser,page,errors}=await openLab({width:1280,height:900});
try{
 const result=await page.evaluate(async()=>{
  sLab.manual(true);
  const {ExactSurface}=await import('../v3/exact.js');
  const r=sLab.renderer,s=sLab.state,gl=r.gl,brick=new ExactSurface(gl,r.meta);
  const original=r.drawActors.bind(r);
  await brick.load();
  r.canvas.style.width='512px';r.canvas.style.height='320px';
  Object.assign(s,{method:'stack',layers:128,number:1,samples:24,mask:true,coverage:false,time:0,magnification:1});
  const views=[[0,0],[-90,0],[90,0],[0,90],[-45,13],[27,18],[105,31],[-88,2]];
  const rows=[];
  for(const [i,[yaw,tilt]] of views.entries()){
   Object.assign(s,{yaw,tilt,course:i>=5,idle:i<5,time:i<5?0:3.15+i*.071});
   const image=useExact=>{
    r.drawActors=useExact?(state,frame,use)=>{
     const tick=state.time/r.meta.period*state.samples;
     const drift=state.course?(tick-Math.floor(tick+1e-6))*r.meta.stride/state.samples:0;
     return brick.draw(frame.groups,use,drift);
    }:original;
    const triangles=r.draw(s);
    const a=new Uint8Array(r.canvas.width*r.canvas.height*4);
    gl.readPixels(0,0,r.canvas.width,r.canvas.height,gl.RGBA,gl.UNSIGNED_BYTE,a);
    if(gl.getError())throw Error('GL failure in brick validation');
    return {a,triangles};
   };
   const p=image(false),q=image(true);let both=0,either=0,agree=0,mae=0,referencePixels=0;
   for(let j=0;j<p.a.length;j+=4){
    const k=(p.a[j]+p.a[j+1]+p.a[j+2])>0,l=(q.a[j]+q.a[j+1]+q.a[j+2])>0;
    if(k)referencePixels++; if(!(k||l))continue;
    either++; if(k&&l)both++;
    const d=Math.abs(p.a[j]-q.a[j])+Math.abs(p.a[j+1]-q.a[j+1])+Math.abs(p.a[j+2]-q.a[j+2]);
    if(d===0)agree++;mae+=d;
   }
   rows.push({yaw,tilt,idle:s.idle,referencePixels,maskIoU:both/either,colourMatch:agree/either,mae:mae/(3*either),
    stackTriangles:p.triangles,brickTriangles:q.triangles});
  }
  return {reference:'v2 128 stack, MSAA disabled for like-for-like single samples',bytes:brick.bytes,rows};
 });
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(path.join(DEMO,'v3/evidence/exact-check.json'),JSON.stringify(result,null,2));
 console.log(JSON.stringify(result));
}finally{await browser.close();}
