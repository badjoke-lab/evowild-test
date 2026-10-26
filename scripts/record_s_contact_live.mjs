import {chromium} from 'playwright';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';
const out=process.argv[2]||'docs/2p5d/evidence/20261026-s-speeds-b3';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}}),logs=[];
await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3');await page.waitForFunction(()=>window.sRunReview);
const cdp=await page.context().newCDPSession(page);
for(const rate of [.5,1,1.5]){
 await page.evaluate(()=>window.sRunReview.setPhase(0,'REAR_3_4'));await page.selectOption('#speed',String(rate));
 const dir=`work/live-s-${rate}`;fs.mkdirSync(dir,{recursive:true});const frames=[];
 const receive=async e=>{const file=`${dir}/${String(frames.length).padStart(4,'0')}.jpg`;fs.writeFileSync(file,Buffer.from(e.data,'base64'));frames.push({file,t:e.metadata.timestamp});await cdp.send('Page.screencastFrameAck',{sessionId:e.sessionId});};
 cdp.on('Page.screencastFrame',receive);await cdp.send('Page.startScreencast',{format:'jpeg',quality:88,everyNthFrame:1});
 const before=await page.evaluate(()=>window.sRunReview.sample());await page.locator('#pause').click();await page.waitForTimeout(3000);await page.locator('#pause').click();const after=await page.evaluate(()=>window.sRunReview.sample());
 await cdp.send('Page.stopScreencast');cdp.off('Page.screencastFrame',receive);
 const concat=frames.map((f,i)=>`file '${f.file.split('/').at(-1)}'\nduration ${i<frames.length-1?Math.max(.001,frames[i+1].t-f.t):.05}`).join('\n');fs.writeFileSync(dir+'/frames.txt',concat+'\n');
 const result=spawnSync('ffmpeg',['-y','-f','concat','-safe','0','-i',dir+'/frames.txt','-fps_mode','vfr','-c:v','libx264','-pix_fmt','yuv420p',`${out}/live-rear-${rate}.mp4`],{encoding:'utf8'});if(result.status!==0)throw Error(result.stderr);
 logs.push({rate,before,after,frameCount:frames.length,wallCaptureDuration:frames.at(-1).t-frames[0].t,simulationTravel:after.distance-before.distance,simulationCycles:(after.time-before.time)/before.duration,note:'Actual CDP WebGL screen capture with original wall timestamps, no interpolated poses; slow headless rendering may slow simulation due to existing dt cap.'});
}
fs.writeFileSync(`${out}/live-video-observations.json`,JSON.stringify(logs,null,2)+'\n');await browser.close();
