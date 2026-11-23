// Record the complete fixed-time mixed100 trial on the course, using the
// displayed renderers at the measured raster size. Encoding happens afterwards.
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {openLab,DEMO} from '../browser.mjs';
import {raceState} from '../../../public/s-pixel-lab/v3/scenarios.js';
const dir=await fs.mkdtemp(path.join(os.tmpdir(),'s-race-film-'));
try{
 for(const version of ['v4','v4.1']){
  process.env.LAB_URL=(process.env.LAB_BASE_URL||'http://127.0.0.1:4173/s-pixel-lab/')+'v4.1/?version='+version;
  const {browser,page,errors}=await openLab({width:1280,height:900});
  try{
   const meta=await page.evaluate(async()=>{
    sLab.manual(true);sLab.renderer.fixedRaster={width:877,height:414};
    for(const bank of [1,2])await sLab.renderer.sprites.load(bank);
    return {period:sLab.meta.period,stride:sLab.meta.stride};
   });
   for(let i=0;i<48;i++){
    const png=await page.evaluate(s=>{Object.assign(sLab.state,s);sLab.draw();return sLab.renderer.canvas.toDataURL().split(',')[1];},raceState('mixed100',i/48,877,414,meta));
    await fs.writeFile(path.join(dir,version+'-'+String(i).padStart(2,'0')+'.png'),Buffer.from(png,'base64'));
   }
   if(errors.length)throw Error(errors.join('\n'));
  }finally{await browser.close();}
 }
 execFileSync('ffmpeg',['-y','-loglevel','error','-framerate','16','-i',path.join(dir,'v4-%02d.png'),'-framerate','16','-i',path.join(dir,'v4.1-%02d.png'),
  '-filter_complex',"[0:v][1:v]hstack,pad=iw:ih+32:0:32,drawtext=text='v4   |   Mixed 100':x=12:y=5:fontcolor=white:fontsize=18,drawtext=text='v4.1   |   Mixed 100':x=889:y=5:fontcolor=white:fontsize=18",
  '-c:v','libx264','-threads','2','-crf','17','-pix_fmt','yuv420p','-movflags','+faststart',path.join(DEMO,'v4.1/evidence/mixed100.mp4')]);
}finally{await fs.rm(dir,{recursive:true,force:true});}
