import {chromium} from 'playwright';import fs from 'node:fs';import {spawnSync} from 'node:child_process';
const out=process.env.S_BODY_OUT||'docs/2p5d/evidence/20261028-s-body-d2b',browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}}),records=[],errors=[];page.on('pageerror',e=>errors.push(e.message));
// Holds at .5/1/1.5, continuous acceleration/deceleration, then abrupt reversal.
const rate=t=>t<.4?.5:t<1?.5+(t-.4)/.6:t<1.4?1.5:t<2?1.5-(t-1.4)/.6:t<2.4?.5:t<2.8?1.5:1;
for(const [label,query] of [['before',process.env.S_BODY_BEFORE||'&toe=roll-v2'],['after',process.env.S_BODY_AFTER||'&toe=roll-v2&body=push-v1']]){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3'+query);await page.waitForFunction(()=>window.sRunReview?.bodySample);await page.evaluate(()=>{window.requestAnimationFrame=()=>0;window.sRunReview.setRate(.5);window.sRunReview.setPhase(.2,'REAR_3_4');});
 const dir=`work/${process.env.S_SPEED_WORK||"d2b-speed-frames"}/${label}`;fs.mkdirSync(dir,{recursive:true});
 for(let i=0;i<=96;i++){
  const state=await page.evaluate(({i,r})=>{const a=window.sRunReview;a.setRate(r);if(i)a.step(1/30);a.advance(0);return {...a.motionSample(),body:a.bodySample()};},{i,r:rate(i/30)});records.push({label,t:i/30,requested:rate(i/30),...state});await page.screenshot({path:`${dir}/${String(i).padStart(3,'0')}.png`});
 }
 const r=spawnSync('ffmpeg',['-y','-framerate','30','-i',`${dir}/%03d.png`,'-c:v','libx264','-pix_fmt','yuv420p',`${out}/${label}-speed-changes.mp4`],{encoding:'utf8'});if(r.status)throw Error(r.stderr);
 fs.copyFileSync(`${dir}/048.png`,`${out}/${label}-speed-change-frame.png`);
}
fs.writeFileSync(`${out}/speed-video-observations.json`,JSON.stringify({errors,records})+'\n');await browser.close();
