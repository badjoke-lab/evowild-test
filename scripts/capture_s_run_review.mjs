import {chromium} from 'playwright';
import fs from 'node:fs';
const out=process.argv[2] || 'docs/2p5d/evidence/20261026-s-run/aligned';fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({...(process.env.CHROMIUM_PATH ? {executablePath:process.env.CHROMIUM_PATH} : {}),headless:true,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}});const errors=[];page.on('pageerror',e=>errors.push(String(e)));
await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html'+(process.argv[3] || ''));
await page.waitForFunction(()=>window.sRunReview,{timeout:30000});
const first=await page.evaluate(()=>window.sRunReview.sample());await page.waitForTimeout(800);
const running=await page.evaluate(()=>window.sRunReview.sample());
const samples=[];
for(const view of ['SIDE','CHASE','LOW','REAR_3_4']){
 fs.mkdirSync(`${out}/${view}`,{recursive:true});
 for(let frame=0;frame<12;frame++){
  const state=await page.evaluate(({phase,view})=>window.sRunReview.setPhase(phase,view),{phase:frame/12,view});
  samples.push(state);await page.screenshot({path:`${out}/${view}/${String(frame).padStart(2,'0')}.png`});
 }
}
fs.writeFileSync(`${out}/native-observations.json`,JSON.stringify({first,running,errors,samples},null,2)+'\n');
console.log(JSON.stringify({first,running,errors,frames:samples.length}));await browser.close();
