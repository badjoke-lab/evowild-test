// Run the uninstrumented integrated game using its existing reset/warm/export
// controls. The driver does not replace RAF, the camera or WebGL commands.
import fs from 'node:fs/promises';
import path from 'node:path';
import {launch} from '../race-integration/browser.mjs';

const [base,folder]=process.argv.slice(2);
await fs.mkdir(folder,{recursive:true});
const browser=await launch();
const screens={pc:{viewport:{width:1100,height:745},deviceScaleFactor:1},
 phone:{viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:2.625}};
try{
 for(const [screen,options] of Object.entries(screens))for(const n of [18,50,100]){
   const ctx=await browser.newContext(options),page=await ctx.newPage();
   const errors=[];page.on('pageerror',e=>errors.push(e.message));
   const order=n===50?['classic','pixel']:['pixel','classic'];
   await page.goto(base+'?raceTrial=1&field='+(n===18?'mixed':'s')+'&count='+n+'&look='+order[0]);
   await page.getByText('実機計測',{exact:true}).click();
   await page.locator('#trial-device').fill(screen+' / SwiftShader');
   for(const mode of order){
     await page.selectOption('#trial-mode',mode);
     await page.waitForFunction(v=>document.querySelector('#race-trial').dataset.renderer===v,mode);
     for(const camera of ['race','follow']){
       const id=[screen,n,mode,camera].join('-');
       await page.locator('[data-view="'+camera+'"]').click();
       await page.locator('#trial-measure').click();
       await page.waitForFunction(()=>!document.querySelector('#trial-save').disabled,null,{timeout:240000});
       const downloading=page.waitForEvent('download');await page.locator('#trial-save').click();
       const file=await downloading,data=JSON.parse(await fs.readFile(await file.path()));
       if(data.samples.length!==96||data.count!==n||data.camera!==camera||data.samples.some(s=>s.atlas_errors.length))throw Error('Invalid race export '+id);
       await fs.writeFile(path.join(folder,id+'.json'),JSON.stringify(data)+'\n');
       console.log(id,data.fps.toFixed(2),data.p95_ms.toFixed(1),data.samples.filter(s=>s.streaming).length);
     }
   }
   if(errors.length)throw Error(errors);await ctx.close();
 }
}finally{await browser.close();}
