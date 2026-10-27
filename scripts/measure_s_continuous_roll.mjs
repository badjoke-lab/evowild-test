import {chromium} from 'playwright';import fs from 'node:fs';import {gzipSync} from 'node:zlib';
import {profiles,captureContactProfile} from './s_contact_profiles.mjs';import {summarizeToeProfile} from './s_toe_metrics.mjs';
const out='docs/2p5d/evidence/20261028-s-continuous-d2a';fs.mkdirSync(out,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});const page=await browser.newPage({viewport:{width:960,height:640}}),reports=process.argv.includes('--after-only')?JSON.parse(fs.readFileSync(`${out}/summary.json`)).reports.filter(r=>r.label==='before'):[],errors=[];page.on('pageerror',e=>errors.push(e.message));
const cases=[...[.5,1,1.5].map(rate=>({name:'steady-'+rate,phase:0,mode:'step',knots:[[0,rate],[1,rate]]})),...profiles];
for(const [label,query] of (process.argv.includes('--after-only')?[['after','&toe=roll-v2']]:[['before','&toe=roll-v1'],['after','&toe=roll-v2']])){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3'+query);await page.waitForFunction(()=>window.sRunReview);
 if(label==='after')fs.writeFileSync(`${out}/roll-descriptors.json`,JSON.stringify(await page.evaluate(()=>window.sRunReview.rollDescriptors),null,2)+'\n');
 for(const profile of cases){
  const trace=await page.evaluate(captureContactProfile,{profile,recordFootSurface:true});fs.writeFileSync(`${out}/${label}-${profile.name}-trace.json.gz`,gzipSync(JSON.stringify(trace)));const summary=summarizeToeProfile(trace);reports.push({label,...summary});console.log(JSON.stringify({label,...summary}));
 }
 for(const view of ['SIDE','LOW']){await page.evaluate(view=>window.sRunReview.setPhase(.35,view),view);await page.screenshot({path:`${out}/${label}-${view}.png`});}
}
fs.writeFileSync(`${out}/summary.json`,JSON.stringify({errors,reports},null,2)+'\n');await browser.close();
