import {chromium} from 'playwright';import fs from 'node:fs';import {gzipSync} from 'node:zlib';
import {profiles,captureContactProfile,summarizeProfile} from './s_contact_profiles.mjs';
const out='docs/2p5d/evidence/20261026-s-acceleration-c2';fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});const page=await browser.newPage({viewport:{width:960,height:640}});const reports=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
for(const [label,port] of [['before',4174],['after',4173]]){
 await page.goto(`http://127.0.0.1:${port}/evowild-test/s-run-review.html?rig=contact-v3`);await page.waitForFunction(()=>window.sRunReview);
 for(const profile of profiles){const trace=await page.evaluate(captureContactProfile,{profile});fs.writeFileSync(`${out}/${label}-${profile.name}-trace.json.gz`,gzipSync(JSON.stringify(trace)));const summary=summarizeProfile(trace);reports.push({label,...summary});console.log(JSON.stringify({label,...summary}));}
}
fs.writeFileSync(`${out}/summary.json`,JSON.stringify({errors,reports},null,2)+'\n');await browser.close();
