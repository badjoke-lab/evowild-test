import fs from 'node:fs/promises';
import path from 'node:path';
import {openLab,DEMO} from '../browser.mjs';
import {raceState} from '../../../public/s-pixel-lab/v3/scenarios.js';

const output=path.join(DEMO,'v4/evidence');
for(const version of ['v3','v4']){
 process.env.LAB_URL=(process.env.LAB_BASE_URL||'http://127.0.0.1:4173/s-pixel-lab/')+version+'/';
 const {page,browser,errors}=await openLab({width:1280,height:900});
 try{
  const meta=await page.evaluate(async()=>{
   sLab.manual(true);const r=sLab.renderer;r.canvas.style.width='877px';r.canvas.style.height='414px';
   for(const k of [1,2])await r.sprites.load(k);
   return {period:sLab.meta.period,stride:sLab.meta.stride};
  });
  for(const key of ['mixed50','mixed100']){
   const data=await page.evaluate(state=>{
    Object.assign(sLab.state,state);sLab.draw();
    return sLab.renderer.canvas.toDataURL().split(',')[1];
   },raceState(key,19/48,877,414,meta));
   await fs.writeFile(path.join(output,version+'-'+key+'.png'),Buffer.from(data,'base64'));
  }
  if(errors.length)throw Error(errors.join('\n'));
 }finally{await browser.close();}
}
