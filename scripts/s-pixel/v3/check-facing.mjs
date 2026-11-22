// Compare the optional front-face index cache with the complete surface EBO.
// Use the same single-sample framebuffer for both sides, including foot drift.
import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';
process.env.LAB_URL=(process.env.LAB_ORIGIN||'http://127.0.0.1:4173')+'/s-pixel-lab/v3/';
const {browser,page,errors}=await openLab();
try{
 const result=await page.evaluate(()=>{
  sLab.manual(true);const {state:s,renderer:r}=sLab,gl=r.gl,c=r.canvas;
  c.style.width='400px';c.style.height='300px';
  Object.assign(s,{idle:false,course:true,mask:true,spin:false,number:1,samples:24,method:'surface',heroAA:0});
  const diff={frames:0,changedPixels:0,maxChannelDelta:0,maxTrianglesFull:0,maxTrianglesFacing:0};
  for(let f=0;f<24;f++)for(const [yaw,tilt] of [[-90,0],[90,0],[0,0],[-45,13],[23,28],[-138,14],[168,73],[0,90]]){
   Object.assign(s,{yaw,tilt,time:1.1+(f+.82)*sLab.meta.period/24,level:['fine','race','mid'][f%3]});
   sLab.draw();const pix=new Uint8Array(c.width*c.height*4),other=new Uint8Array(pix.length);
   s.frontFaces=false;diff.maxTrianglesFull=Math.max(diff.maxTrianglesFull,sLab.draw());gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,pix);
   s.frontFaces=true;diff.maxTrianglesFacing=Math.max(diff.maxTrianglesFacing,sLab.draw());gl.readPixels(0,0,c.width,c.height,gl.RGBA,gl.UNSIGNED_BYTE,other);
   for(let j=0;j<pix.length;j+=4){const d=Math.max(...[0,1,2].map(k=>Math.abs(pix[j+k]-other[j+k])));diff.changedPixels+=Number(d>0);diff.maxChannelDelta=Math.max(diff.maxChannelDelta,d);}
   diff.frames++;
  }
  if(gl.getError())throw Error('WebGL readback');return diff;
 });
 if(errors.length)throw Error(errors.join('\n'));
 await fs.writeFile(path.join(DEMO,'v3/evidence/facing-check.json'),JSON.stringify(result,null,2)+'\n');console.log(result);
}finally{await browser.close();}
