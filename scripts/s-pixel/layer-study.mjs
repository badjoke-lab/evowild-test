import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from './browser.mjs';
const {browser,page,errors}=await openLab();
try{
 await page.evaluate(()=>{sLab.manual(true);window.plate=document.createElement('canvas');plate.width=1120;plate.height=644;});
 for(const [index,layers] of [16,32,64,128].entries()){
  await page.evaluate(n=>sLab.selectLayers(n),layers);
  await page.evaluate(([i,n])=>{
   const c=sLab.renderer.canvas;c.style.width='560px';c.style.height='282px';
   Object.assign(sLab.state,{idle:false,course:false,number:1,yaw:-22,tilt:6,time:17*sLab.meta.period/24});
   sLab.draw();const ctx=plate.getContext('2d'),x=i%2*560,y=Math.floor(i/2)*322;
   ctx.drawImage(c,x,y,560,282);ctx.fillStyle='#26332d';ctx.fillRect(x,y+282,560,40);
   ctx.fillStyle='#f1f1e8';ctx.font='bold 16px monospace';ctx.fillText(n+' LAYERS',x+16,y+309);
   ctx.font='12px monospace';ctx.fillText('POSE 18/24   ELEV 6°',x+321,y+308);
  },[index,layers]);
 }
 await fs.writeFile(path.join(DEMO,'evidence/layer-study.png'),Buffer.from((await page.evaluate(()=>plate.toDataURL())).split(',')[1],'base64'));
 await page.evaluate(()=>{const c=sLab.renderer.canvas;c.style.width='';c.style.height='';Object.assign(sLab.state,{course:true,playing:false,number:100,tilt:47,yaw:25,time:2.5});sLab.sync();sLab.draw();});
 await page.screenshot({path:path.join(DEMO,'evidence/course-100.png')});
 if(errors.length)throw Error(errors.join('\n'));
}finally{await browser.close();}
