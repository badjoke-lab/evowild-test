import {chromium} from '@playwright/test';
import fs from 'node:fs/promises';
const out='public/exp-sprite-stacking/assets';await fs.mkdir(out+'/sprite',{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:1100,height:800}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));page.on('console',m=>{if(m.type()==='error')errors.push(m.text());});
await page.goto((process.env.STACK_URL||'http://127.0.0.1:4173/evowild-test/exp-sprite-stacking/index.html')+'?method=glb&scene=turntable');await page.waitForFunction(()=>window.lab?.state().ready,{timeout:60000});await page.evaluate(()=>window.lab.setPaused(true));
for(let f=0;f<48;f++){const b=await page.evaluate(f=>window.lab.bakeSpriteFrame(f),f);await fs.writeFile(`${out}/sprite/${String(f).padStart(2,'0')}.png`,Buffer.from(b,'base64'));if(f%12===0)console.log('Sprite frame',f);}
await fs.writeFile(out+'/sprite-manifest.json',JSON.stringify({source:'source.glb',sourceSha256:'6edb45e7aeb3179104d5b406d09eaa1f34da6baf09ddc9a6a0535d7e96f3f1c0',frames:48,directions:16,elevation:35,pixelsPerUnit:64,size:256,lighting:'same local Lambert as slices',method:'Existing 2D billboard technique, same-source re-bake; production sheet is a separate unmatched baseline',browserErrors:errors}));console.log('Browser errors',errors);await browser.close();if(errors.length)process.exitCode=1;
