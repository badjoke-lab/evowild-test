import {chromium,devices} from 'playwright';
import fs from 'node:fs';
const out=process.argv[2]||'docs/2p5d/evidence/20261026-s-contact-b2';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
const samples=[];
for(const [device,options] of [['desktop',{viewport:{width:1280,height:800}}],['android',devices['Pixel 7']]]){
 const context=await browser.newContext(options),page=await context.newPage();
 for(const rig of ['hind-v2','contact-v3']){
  await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig='+rig);await page.waitForFunction(()=>window.sRunReview);
  const state=await page.evaluate(()=>window.sRunReview.setPhase(.4,'REAR_3_4'));samples.push({device,rig,state});
  await page.screenshot({path:`${out}/${device}-${rig}.png`});
 }
 await context.close();
}
fs.writeFileSync(`${out}/device-observations.json`,JSON.stringify(samples,null,2)+'\n');await browser.close();
