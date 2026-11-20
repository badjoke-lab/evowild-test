// OS RSS is collected separately; summing Chrome processes counts shared pages
// more than once. This is distinct from VBO/texture allocation and JS heap.
import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';
const rows=[];
for(const mobile of [false,true])for(const method of ['v1','stack','lod']){
 process.env.LAB_URL='http://127.0.0.1:4173/s-pixel-lab/'+(method==='v1'?'':'v2/');
 const {browser,page,errors}=await openLab(mobile?{width:390,height:844}:{width:1280,height:900},mobile);
 try{
  const cdp=await page.context().newCDPSession(page),proc=await browser.newBrowserCDPSession();
  await cdp.send('Emulation.setCPUThrottlingRate',{rate:mobile?4:1});
  await page.evaluate(()=>sLab.manual(true));
  for(const n of [1,10,50,100]){
   const data=await page.evaluate(async ({method,n})=>{
    const {renderer:r,state:s}=sLab,gl=r.gl;Object.assign(s,{number:n,method,idle:false,course:false,yaw:-22,tilt:12,time:0});sLab.draw();
    if(method==='lod'&&r.sprites.banks.has(1))await r.sprites.load(1);
    for(let k=0;k<3;k++){s.time=k*.03;sLab.draw();gl.readPixels(0,0,1,1,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array(4));}
    return {atlas_bytes:r.atlasBytes||0,coverage_bytes:r.coverage?.bytes||0,cache_bytes:(r.floorW||0)*(r.floorH||0)*4};
   },{method,n});
   const info=await proc.send('SystemInfo.getProcessInfo'),by_type={};
   for(const p of info.processInfo){
    try{
     const status=await fs.readFile('/proc/'+p.id+'/status','utf8'),kb=Number(/^VmRSS:\s+(\d+)/m.exec(status)?.[1]||0);
     by_type[p.type]=(by_type[p.type]||0)+kb/1024;
    }catch(e){if(!['ENOENT','EACCES'].includes(e.code))throw e;}
   }
   rows.push({profile:mobile?'mobile-4x':'desktop-1x',method,number:n,rss_mib:Object.values(by_type).reduce((a,b)=>a+b,0),by_type,...data});
  }
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
await fs.writeFile(path.join(DEMO,'v2/evidence/memory.json'),JSON.stringify(rows,null,2));
