import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';
process.env.LAB_URL='http://127.0.0.1:4173/s-pixel-lab/v2/';
const {page,browser,errors}=await openLab();
try{
 const results=await page.evaluate(async()=>{
  const {state:s,renderer:r}=sLab,g=r.gl,c=r.canvas;
  sLab.manual(true);await r.sprites.load(1);c.style.width='320px';c.style.height='200px';
  Object.assign(s,{time:.48,course:false,number:1,idle:false,mask:true,tilt:12});
  const sets={};
  function render(method){
   s.method=method;sLab.draw();const raw=new Uint8Array(c.width*c.height*4);
   g.readPixels(0,0,c.width,c.height,g.RGBA,g.UNSIGNED_BYTE,raw);
   const mask=new Uint8Array(raw.length/4);let x=0,y=0,n=0;
   for(let j=0;j<mask.length;j++)if(Math.max(raw[4*j],raw[4*j+1],raw[4*j+2])>12){mask[j]=1;x+=j%c.width;y+=Math.floor(j/c.width);n++;}
   if(!n)throw Error('empty silhouette');return {x:x/n,y:y/n,mask};
  }
  for(const kind of ['zoom','rotating-gallop']){
   let last=null;const frames=[];
   for(let i=0;i<(kind==='zoom'?81:180);i++){
    s.yaw=kind==='zoom'?-22:i*2;s.time=kind==='zoom'?.48:i/24;s.method='lod';s.magnification=1;
    // Use the actual renderer framing to find the requested projected size.
    sLab.draw();s.magnification=(kind==='zoom'?72+i*1.1:76)/r.screenSpan;
    const ref=render('stack'),lod=render('lod');
    let union=0,intersection=0;for(let j=0;j<ref.mask.length;j++){union+=ref.mask[j]|lod.mask[j];intersection+=ref.mask[j]&lod.mask[j];}
    const err=[lod.x-ref.x,lod.y-ref.y];
    frames.push({yaw:s.yaw,span:r.screenSpan,pose:1+Math.floor(s.time/.72*24)%24,mix:r.mix,iou:intersection/union,centroid_px:Math.hypot(...err),extra_motion_px:last?Math.hypot(err[0]-last[0],err[1]-last[1]):0});last=err;
   }
   sets[kind]=frames;
  }
  return sets;
 });
 await fs.writeFile(path.join(DEMO,'v2/evidence/sweep.json'),JSON.stringify(results,null,1));if(errors.length)throw Error(errors.join('\n'));
}finally{await browser.close();}
