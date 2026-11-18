import fs from 'node:fs';import {gzipSync} from 'node:zlib';import {chromium} from 'playwright';
import {profiles,captureContactProfile} from './s_contact_profiles.mjs';import {summarizeToeProfile} from './s_toe_metrics.mjs';
const out='docs/2p5d/evidence/20261029-s-d3b-fore-reach';fs.mkdirSync(out,{recursive:true});
const after=process.argv.includes('--after'),variants=after?[['fixed','push-v5']]:[['baseline','push-v3'],['failed','push-v5']];
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});const page=await browser.newPage({viewport:{width:960,height:640}});const reports=[];
const cases=[...[.5,1,1.5].map(rate=>({name:'steady-'+rate,phase:0,mode:'step',knots:[[0,rate],[1,rate]]})),...profiles];
for(const [label,body] of variants){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body='+body);await page.waitForFunction(()=>window.sRunReview);
 await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});
 for(const profile of cases){
  const trace=await page.evaluate(captureContactProfile,{profile,recordFootSurface:true,recordBody:true});
  fs.writeFileSync(`${out}/${label}-${profile.name}.json.gz`,gzipSync(JSON.stringify(trace)));
  const summary=summarizeToeProfile(trace);
  const events=trace.switches.map(s=>({...s,frame:trace.frames.find(f=>Math.abs(f.t-s.t)<1e-8)}));
  const max=events.sort((a,b)=>Math.max(...b.meshVelocityResidual)-Math.max(...a.meshVelocityResidual))[0];
  reports.push({label,...summary,worstSwitch:max?{t:max.t,phase:max.beforePhase%1,from:max.from,to:max.to,residuals:max.meshVelocityResidual,limbs:max.frame.contact.limbs,body:max.frame.body}:null});
  console.log(label,profile.name,JSON.stringify(reports.at(-1).worstSwitch));
 }
}
fs.writeFileSync(`${out}/${after?'fixed':'diagnosis'}-summary.json`,JSON.stringify(reports,null,2)+'\n');await browser.close();
