import {chromium,devices} from 'playwright';import fs from 'node:fs';import {spawnSync} from 'node:child_process';
import {profiles} from './s_contact_profiles.mjs';
const out='docs/2p5d/evidence/20261026-s-acceleration-c2';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}}),observations=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
function rateAt(profile,t){const k=profile.knots;let i=0;while(i+1<k.length&&t>=k[i+1][0]-1e-10)i++;if(profile.mode==='step'||i===k.length-1)return k[i][1];return k[i][1]+(t-k[i][0])/(k[i+1][0]-k[i][0])*(k[i+1][1]-k[i][1]);}
async function run(page,label,profile,view,frames){
 await page.evaluate(({rate,phase,view})=>{window.sRunReview.setRate(rate);window.sRunReview.setPhase(phase,view);},{rate:profile.knots[0][1],phase:profile.phase,view});
 const dir=`${out}/frames/${label}-${profile.name}-${view}`;fs.mkdirSync(dir,{recursive:true});let time=0;const duration=profile.knots.at(-1)[0];
 for(let i=0;i<=frames;i++){
  const target=i/frames*duration,steps=[];while(time<target-1e-9){const dt=Math.min(1/240,target-time);steps.push([dt,rateAt(profile,time)]);time+=dt;}
  const sample=await page.evaluate(steps=>{const a=window.sRunReview;for(const [dt,rate] of steps){a.setRate(rate);a.step(dt);}a.advance(0);return a.motionSample();},steps);
  observations.push({label,profile:profile.name,view,t:target,...sample});await page.screenshot({path:`${dir}/${String(i).padStart(2,'0')}.png`});
 }
 if(view==='REAR_3_4'){
  const r=spawnSync('ffmpeg',['-y','-framerate',String(frames/duration),'-i',`${dir}/%02d.png`,'-c:v','libx264','-pix_fmt','yuv420p',`${out}/${label}-${profile.name}-rear.mp4`],{encoding:'utf8'});if(r.status)throw Error(r.stderr);
 }
}
for(const [label,port] of [['before',4174],['after',4173]]){
 await page.goto(`http://127.0.0.1:${port}/evowild-test/s-run-review.html?rig=contact-v3`);await page.waitForFunction(()=>window.sRunReview);
 // 12 consecutive time samples of the full two-second acceleration in all views.
 for(const view of ['SIDE','CHASE','LOW','REAR_3_4'])await run(page,label,profiles[0],view,12);
 await run(page,label,profiles[1],'REAR_3_4',12);
 // Dense 120Hz sequence straddles the abrupt change, at the same starting phase.
 const abrupt={name:'abrupt-closeup',phase:.2,mode:'step',knots:[[0,.5],[.025,1.5],[.1,1.5]]};
 await run(page,label,abrupt,'REAR_3_4',12);
}
await page.close();
for(const [device,options] of [['desktop',{viewport:{width:1280,height:800}}],['android',devices['Pixel 7']]]){
 const p=await browser.newPage(options);
 for(const [label,port] of [['before',4174],['after',4173]]){
  await p.goto(`http://127.0.0.1:${port}/evowild-test/s-run-review.html?rig=contact-v3`);await p.waitForFunction(()=>window.sRunReview);
  await p.evaluate(()=>{const a=window.sRunReview;a.setRate(.5);a.setPhase(.7,'REAR_3_4');a.setRate(1.5);a.advance(.08);});
  await p.screenshot({path:`${out}/${device}-${label}.png`});
 }
 await p.close();
}
fs.writeFileSync(`${out}/visual-observations.json`,JSON.stringify({errors,samples:observations})+'\n');await browser.close();
