// Real GLB rendering, identical v4/v5 cameras, four continuous cycles per run view.
import {chromium,devices} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const dest='docs/evidence/p-canonical-3d-v5-20261011',scratch='work/p-canonical-v5';
fs.mkdirSync(`${scratch}/run-frames`,{recursive:true});
fs.mkdirSync(dest,{recursive:true});
const offline=process.argv.includes('--offline');
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const errors=[],failedRequests=[],responses=[];
async function open(options={},version='v5'){
 const context=await browser.newContext(options);const page=await context.newPage();
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>failedRequests.push({url:r.url(),error:r.failure()?.errorText}));
 page.on('response',r=>{if(r.status()>=400)responses.push({url:r.url(),status:r.status()});});
 // File-backed HTTP routing permits real Chromium/WebGL tests without a listening
 // socket in a restricted local sandbox. CI uses the regular Vite HTTP server.
 if(offline)await page.route('http://127.0.0.1:4173/**',route=>{
   const url=new URL(route.request().url());let p=decodeURIComponent(url.pathname).replace(/^\/evowild-test\//,'');
   const root=p.startsWith('docs/')?process.cwd():path.resolve('dist');
   const file=path.resolve(root,p);
   if(!file.startsWith(root+path.sep)||!fs.existsSync(file))return route.fulfill({status:404,body:p});
   const type={'.js':'application/javascript','.html':'text/html','.css':'text/css','.glb':'model/gltf-binary','.png':'image/png','.webp':'image/webp'}[path.extname(file)]||'application/octet-stream';
   return route.fulfill({path:file,contentType:type});
 });
 await page.goto(`http://127.0.0.1:4173/evowild-test/p-canonical-review.html?model=${version}`);
 await page.waitForFunction(()=>window.pReview?.ready===true);return {context,page};
}
const {page,context}=await open({viewport:{width:1200,height:900},deviceScaleFactor:1});
const stats={browser:await browser.version(),transport:offline?'Playwright local-file route':'Vite HTTP',desktop:{},mobile:{},run:{cycleSeconds:.8,cyclesPerView:4,framesPerView:96,views:['SIDE','FRONT34']},errors,failedRequests,responses};
for(const view of ['SIDE','FRONT','FRONT34','REAR34','BACK']){
 await page.getByRole('button',{name:view,exact:true}).click();
 await page.screenshot({path:`${dest}/${view}.png`});stats.desktop[view]=await page.evaluate(()=>window.pReview.stats());console.log('Captured v5',view);
}
await page.evaluate(()=>{window.pReview.setView('SIDE');window.pReview.silhouette(true);});
await page.screenshot({path:`${dest}/silhouette-SIDE.png`});
await page.evaluate(()=>window.pReview.silhouette(false));
await page.getByRole('button',{name:'RUN REVIEW',exact:true}).click();
for(const view of stats.run.views){
 await page.evaluate(v=>window.pReview.setView(v),view);
 for(let f=0;f<96;f++){
  await page.evaluate(t=>window.pReview.setTime(t),f/30);
  await page.screenshot({path:`${scratch}/run-frames/${view}-${String(f).padStart(3,'0')}.png`});
  if([0,6,12,18,23,24,47,48,71,72].includes(f))fs.copyFileSync(`${scratch}/run-frames/${view}-${String(f).padStart(3,'0')}.png`,`${dest}/run-${view}-${String(f).padStart(2,'0')}.png`);
 }
 console.log('Captured four continuous cycles',view);
}
await page.getByRole('button',{name:'RUN REVIEW',exact:true}).click();
await page.getByRole('button',{name:'BACK',exact:true}).click();
if(await page.locator('#viewLabel').textContent()!=='BACK · rest stance')throw Error('Pause/camera controls failed');
await page.setViewportSize({width:960,height:720});
await page.screenshot({path:`${dest}/desktop-resized.png`});
await context.close();
const prior=await open({viewport:{width:1200,height:900},deviceScaleFactor:1},'v4');
for(const view of ['SIDE','FRONT','FRONT34','REAR34','BACK']){
 await prior.page.evaluate(v=>window.pReview.setView(v),view);
 await prior.page.screenshot({path:`${dest}/v4-${view}.png`});
}
stats.v4=await prior.page.evaluate(()=>window.pReview.stats());await prior.context.close();
const mobile=await open({...devices['Pixel 7']});
for(const view of ['SIDE','FRONT34']){
 await mobile.page.getByRole('button',{name:view,exact:true}).click();
 await mobile.page.screenshot({path:`${dest}/mobile-${view}.png`});stats.mobile[view]=await mobile.page.evaluate(()=>window.pReview.stats());
}
await mobile.page.getByRole('button',{name:'RUN REVIEW',exact:true}).click();
await mobile.page.evaluate(()=>window.pReview.setTime(2.6));
await mobile.page.screenshot({path:`${dest}/mobile-run.png`});
await mobile.context.close();await browser.close();
fs.writeFileSync(`${dest}/browser-validation.json`,JSON.stringify(stats,null,2)+'\n');
if(errors.length||failedRequests.length||responses.length)throw Error(JSON.stringify({errors,failedRequests,responses}));
console.log('PASS: real v4/v5 loads, 5 views, 4 cycles, pause, resize, Pixel 7; no errors');
