import {chromium} from 'playwright';
import fs from 'node:fs';
import {gzipSync} from 'node:zlib';
import {summarizeSoles} from '../src/s_sole_metrics.js';
const out=process.argv[2]||'docs/2p5d/evidence/20261026-s-soles-b1';
const rig=process.argv[3]||'hind-v2';
const rates=(process.argv[4]||'1').split(',').map(Number);
fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),headless:true,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}});const errors=[];page.on('pageerror',e=>errors.push(e.message));
await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig='+rig);await page.waitForFunction(()=>window.sRunReview);
const reports=[];
for(const rate of rates){
 const trace=await page.evaluate(rate=>window.sRunReview.measureCycle(rate,240),rate);
 const summary=summarizeSoles(trace.frames);reports.push({rig,rate,asset:trace.asset,...summary});
 fs.writeFileSync(`${out}/${rig}-${rate}-trace.json.gz`,gzipSync(JSON.stringify(trace)));
 fs.writeFileSync(`${out}/sole-patches.json`,JSON.stringify(trace.patches,null,2)+'\n');
}
fs.writeFileSync(`${out}/summary.json`,JSON.stringify({errors,reports},null,2)+'\n');
await page.evaluate(()=>window.sRunReview.setPhase(.25,'LOW'));await page.screenshot({path:`${out}/low.png`});
await browser.close();console.log(JSON.stringify(reports.map(r=>({...r,feet:r.feet.map(({phases,...f})=>f)})),null,2));
