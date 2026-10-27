import {chromium,devices} from 'playwright';import fs from 'node:fs';import {spawnSync} from 'node:child_process';
const out='docs/2p5d/evidence/20261027-s-toe-roll-d1b';const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});const observations=[],errors=[];
const page=await browser.newPage({viewport:{width:960,height:640}});page.on('pageerror',e=>errors.push(e.message));
for(const [label,query] of [['before',''],['after','&toe=roll-v1']]){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3'+query);await page.waitForFunction(()=>window.sRunReview);await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});
 for(const view of ['SIDE','CHASE','LOW','REAR_3_4']){
  await page.evaluate(view=>{window.sRunReview.setRate(1);window.sRunReview.setPhase(.64,view);},view);
  const dir=`${out}/frames/${label}-${view}`;fs.mkdirSync(dir,{recursive:true});
  for(let i=0;i<24;i++){
   const state=await page.evaluate(i=>{const a=window.sRunReview;if(i)a.step((1/2.4)/24);a.advance(0);return {state:a.motionSample(),feet:a.footSample().map(({points,...f})=>f)};},i);
   observations.push({label,view,frame:i,...state});await page.screenshot({path:`${dir}/${String(i).padStart(2,'0')}.png`});
  }
  const r=spawnSync('ffmpeg',['-y','-framerate','57.6','-i',`${dir}/%02d.png`,'-c:v','libx264','-pix_fmt','yuv420p',`${out}/${label}-${view}.mp4`],{encoding:'utf8'});if(r.status)throw Error(r.stderr);
 }
}
await page.close();
for(const [device,options] of [['desktop',{viewport:{width:1280,height:800}}],['android',devices['Pixel 7']]]){
 const p=await browser.newPage(options);
 for(const [label,query] of [['before',''],['after','&toe=roll-v1']]){
  await p.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3'+query);await p.waitForFunction(()=>window.sRunReview);await p.evaluate(()=>{window.requestAnimationFrame=()=>0;});await p.evaluate(()=>{window.sRunReview.setRate(1);window.sRunReview.setPhase(.80,'REAR_3_4');});await p.screenshot({path:`${out}/${device}-${label}.png`});
 }
 await p.close();
}
fs.writeFileSync(`${out}/visual-observations.json`,JSON.stringify({errors,samples:observations})+'\n');await browser.close();
