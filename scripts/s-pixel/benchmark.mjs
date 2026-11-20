import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from './browser.mjs';
const rows=[];
for(const mobile of [false,true]){
 const viewport=mobile?{width:390,height:844}:{width:1280,height:900};
 const {browser,page,errors}=await openLab(viewport,mobile);
 try{
  const cdp=await page.context().newCDPSession(page);
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:mobile?4:1});
  await page.evaluate(()=>sLab.manual(true));
  for(const layers of [16,32,64,128]){
   await page.evaluate(n=>sLab.selectLayers(n),layers);
   for(const number of [1,10,50,100]){
    const result=await page.evaluate(async({layers,number})=>{
     const {renderer:r,state:s}=sLab,gl=r.gl;
     const ext=gl.getExtension('WEBGL_debug_renderer_info');
     Object.assign(s,{number,layers,course:false,idle:false,time:0,yaw:-22,tilt:12,samples:24});
     const rgba=new Uint8Array(4),times=[];let tris=0;
     const raf=()=>new Promise(ok=>requestAnimationFrame(ok));
     function frame(t){
       s.time=t/1000;tris=sLab.draw();
       // One-pixel readback includes GPU completion in the interval.
       gl.readPixels(gl.drawingBufferWidth>>1,gl.drawingBufferHeight>>1,1,1,gl.RGBA,gl.UNSIGNED_BYTE,rgba);
     }
     for(let i=0;i<3;i++)frame(await raf());
     const start=performance.now();let last=start;
     do{const t=await raf();frame(t);const end=performance.now();times.push(end-last);last=end;}
     while((last-start<1200||times.length<5)&&times.length<120);
     const sorted=[...times].sort((a,b)=>a-b),avg=(last-start)/times.length;
     return {width:r.canvas.width,height:r.canvas.height,count:number,layers,frames:times.length,fps:+(1000/avg).toFixed(2),mean_ms:+avg.toFixed(2),p95_ms:+sorted[Math.ceil(sorted.length*.95)-1].toFixed(2),last_triangles:tris,renderer:ext?gl.getParameter(ext.UNMASKED_RENDERER_WEBGL):gl.getParameter(gl.RENDERER),intervals_ms:times.map(t=>+t.toFixed(2))};
    },{layers,number});
    rows.push({profile:mobile?'mobile-viewport-4x':'desktop-1x',...result});
    console.log(rows.at(-1).profile,layers,number,result.fps);
    await fs.writeFile(path.join(DEMO,'evidence/performance.json'),JSON.stringify({browser:browser.version(),rows},null,1));
   }
  }
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
const keys=['profile','width','height','count','layers','frames','fps','mean_ms','p95_ms','last_triangles'];
await fs.writeFile(path.join(DEMO,'evidence/performance.csv'),keys.join(',')+'\n'+rows.map(r=>keys.map(k=>r[k]).join(',')).join('\n')+'\n');
