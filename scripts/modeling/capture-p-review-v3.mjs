// Run against Vite on :4173. Capture the actual GLB, not an illustration.
import {chromium,devices} from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';
const dest='docs/evidence/p-canonical-3d-v3-20261011',scratch='work/p-canonical-v3';
const oldEvidence='docs/evidence/p-canonical-3d-20261011';
fs.mkdirSync(`${scratch}/run-frames`,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',headless:true,args:['--no-sandbox','--disable-dev-shm-usage','--use-angle=swiftshader','--enable-unsafe-swiftshader']});
const errors=[],failedRequests=[];
async function open(options={},previous=false){
 const context=await browser.newContext(options);const page=await context.newPage();
 page.on('pageerror',e=>errors.push(String(e)));page.on('requestfailed',r=>failedRequests.push({url:r.url(),error:r.failure()?.errorText}));
 // Historical proxy is evidence, not a runtime production asset.
 if(previous)await page.route('**/docs/evidence/p-canonical-3d-20261011/previous-proxy.glb',route=>route.fulfill({path:path.resolve(`${oldEvidence}/previous-proxy.glb`),contentType:'model/gltf-binary'}));
 await page.goto(`http://127.0.0.1:4173/evowild-test/p-canonical-review.html${previous?'?previous=1':'?model=v3'}`);
 await page.waitForFunction(()=>window.pReview?.ready===true);return {context,page};
}
const {page,context}=await open({viewport:{width:1200,height:900},deviceScaleFactor:1});
const stats={browser:await browser.version(),desktop:{},mobile:{},errors,failedRequests};
for(const view of ['SIDE','FRONT','FRONT34','REAR34','BACK']){
 await page.evaluate(v=>window.pReview.setView(v),view);
 await page.screenshot({path:`${dest}/${view}.png`});stats.desktop[view]=await page.evaluate(()=>window.pReview.stats());console.log('Captured',view);
}
await page.evaluate(()=>{window.pReview.setView('SIDE');window.pReview.silhouette(true);});
await page.screenshot({path:`${dest}/new-silhouette-SIDE.png`});
await page.evaluate(()=>window.pReview.silhouette(false));
// 2 x 24 distinct source frames, repeated only by the encoder to show complete cycles.
await page.evaluate(()=>window.pReview.setRunning(true));
for(const [index,view]of ['SIDE','FRONT34'].entries()){
 await page.evaluate(v=>window.pReview.setView(v),view);
 for(let f=0;f<24;f++){
  await page.evaluate(t=>window.pReview.setTime(t),f/30);
  await page.screenshot({path:`${scratch}/run-frames/${view}-${String(f).padStart(3,'0')}.png`});
  if([0,6,12,18].includes(f))fs.copyFileSync(`${scratch}/run-frames/${view}-${String(f).padStart(3,'0')}.png`,`${dest}/run-${view}-${String(f).padStart(2,'0')}.png`);
 }
 console.log('Captured run cycle',view);
}
// Exercise pause/restore and UI camera controls, not just screenshot API.
await page.getByRole('button',{name:'RUN REVIEW',exact:true}).click();
await page.getByRole('button',{name:'BACK',exact:true}).click();
if(await page.locator('#viewLabel').textContent()!=='BACK · rest stance')throw Error('Pause/camera controls failed');
await context.close();
const prior=await open({viewport:{width:1200,height:900},deviceScaleFactor:1},true);
for(const view of ['SIDE','FRONT34']){
 await prior.page.evaluate(v=>window.pReview.setView(v),view);await prior.page.screenshot({path:`${dest}/previous-proxy-${view}.png`});
}
await prior.page.evaluate(()=>{window.pReview.setView('SIDE');window.pReview.silhouette(true);});await prior.page.screenshot({path:`${dest}/previous-silhouette-SIDE.png`});
stats.previous=await prior.page.evaluate(()=>window.pReview.stats());await prior.context.close();
const mobile=await open({...devices['Pixel 7']});
for(const view of ['SIDE','FRONT34']){
 await mobile.page.getByRole('button',{name:view,exact:true}).click();await mobile.page.screenshot({path:`${dest}/mobile-${view}.png`});stats.mobile[view]=await mobile.page.evaluate(()=>window.pReview.stats());
}
await mobile.page.getByRole('button',{name:'RUN REVIEW',exact:true}).click();await mobile.page.evaluate(()=>window.pReview.setTime(.2));await mobile.page.screenshot({path:`${dest}/mobile-run.png`});
await mobile.context.close();await browser.close();
fs.writeFileSync(`${dest}/browser-validation.json`,JSON.stringify(stats,null,2)+'\n');
if(errors.length||failedRequests.length)throw Error(JSON.stringify({errors,failedRequests}));
console.log('Review capture complete; desktop + Pixel 7 emulation, zero page errors or failed requests');
