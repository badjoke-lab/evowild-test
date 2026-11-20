import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';
process.env.LAB_URL='http://127.0.0.1:4173/s-pixel-lab/v2/';
const rows=[];
for(const mobile of [false,true]){
 const {browser,page,errors}=await openLab(mobile?{width:390,height:844}:{width:1280,height:900},mobile);
 try{
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:mobile?4:1});
  await page.evaluate(async m=>{sLab.manual(true);const c=sLab.renderer.canvas;c.style.width=(m?352:877)+'px';c.style.height=(m?335:414)+'px';await sLab.renderer.sprites.load(1);},mobile);
  for(const scenario of ['overview','mixed'])for(const n of [50,100]){
   const r=await page.evaluate(async ({n,scenario})=>{
    const {state:s,renderer:r}=sLab,g=r.gl;Object.assign(s,{number:n,method:'lod',idle:false,course:true,tilt:12,samples:24,spin:true,magnification:1,time:3,yaw:-22});
    sLab.draw();if(scenario==='mixed')s.magnification=Math.min(7,122/r.screenSpan);
    const px=new Uint8Array(4),intervals=[],ticks=[],mixSamples=[];
    const raf=()=>new Promise(requestAnimationFrame);
    const draw=t=>{s.time=3+t;s.yaw=-22+t*40;sLab.draw();g.readPixels(r.canvas.width>>1,r.canvas.height>>1,1,1,g.RGBA,g.UNSIGNED_BYTE,px);};
    for(let i=0;i<3;i++){await raf();draw(i/30);}
    const start=performance.now();let prev=start;
    do{const t=await raf();const a=performance.now();draw((t-start)/1000);const b=performance.now();mixSamples.push({...r.mix});ticks.push(b-a);intervals.push(b-prev);prev=b;}while(prev-start<2400||intervals.length<8);
    const sorted=[...intervals].sort((a,b)=>a-b);return {count:n,scenario,zoom:s.magnification,mixSamples,frames:intervals.length,fps:1000*intervals.length/(prev-start),p95_ms:sorted[Math.ceil(.95*sorted.length)-1],draw_sync_ms:ticks.reduce((a,b)=>a+b)/ticks.length,mix:r.mix,intervals_ms:intervals};
   },{n,scenario});
   rows.push({profile:mobile?'mobile-4x':'desktop-1x',...r});console.log(mobile,n,r.fps,r.draw_sync_ms);
  }
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
await fs.writeFile(path.join(DEMO,'v2/evidence/course-measurement.json'),JSON.stringify(rows,null,2));
