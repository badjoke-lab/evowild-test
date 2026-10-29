// D2-D evidence only: real WebGL key-join microsequence, not generated art.
import {chromium} from 'playwright';
import fs from 'node:fs';
import {spawnSync} from 'node:child_process';

const out=process.env.S_D2D_OUT||'docs/2p5d/evidence/20261029-s-native-join-d2d';
const work=process.env.S_D2D_WORK||'work/s-native-join-d2d-frames';
fs.mkdirSync(out,{recursive:true});fs.mkdirSync(work,{recursive:true});
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const observations=[];
const variants=[['before','&toe=roll-v3&body=push-v2'],['after','&toe=roll-v3&body=push-v3']];
const views=['SIDE','CHASE','LOW','REAR_3_4'];
for(const [label,query] of variants){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3'+query);
 await page.waitForFunction(()=>window.sRunReview?.bodyVertexIds?.length>0);
 await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});
 for(const view of views){
  const dir=work+'/'+label+'-'+view;
  fs.mkdirSync(dir,{recursive:true});
  await page.evaluate(view=>{const a=window.sRunReview;a.setRate(1);a.setPhase(.632,view);},view);
  for(let i=0;i<=16;i++){
   const measured=await page.evaluate(i=>{
    const a=window.sRunReview;
    if(i)a.step(.001/2.4);
    a.advance(0);
    return {phase:a.sample().phase,body:a.bodySample(),contact:a.motionSample().contact};
   },i);
   observations.push({label,view,frame:i,...measured});
   const filename=String(i).padStart(2,'0')+'.png';
   await page.screenshot({path:dir+'/'+filename});
   if([0,6,8,10,16].includes(i))fs.copyFileSync(dir+'/'+filename,out+'/'+label+'-'+view+'-phase-'+(632+i)+'.png');
  }
  const result=spawnSync('ffmpeg',['-hide_banner','-loglevel','error','-y','-framerate','30','-i',dir+'/%02d.png','-c:v','libx264','-pix_fmt','yuv420p',out+'/'+label+'-'+view+'-join-slow80x.mp4'],{encoding:'utf8'});
  if(result.status!==0)throw Error('ffmpeg '+label+' '+view+': '+result.stderr);
  console.log('D2D_CAPTURE',label,view,'17 REAL WebGL frames, 80x slow');
 }
}
fs.writeFileSync(out+'/join-observations.json',JSON.stringify({source:'actual WebGL, same asset/cameras/lighting',phaseStart:.632,phaseEnd:.648,phaseStep:.001,simulationHz:2400,playbackHz:30,slowMotionFactor:80,variants,views,pageErrors:errors,observations},null,2)+'\n');
await browser.close();
if(errors.length)throw Error('Browser page errors: '+JSON.stringify(errors));
console.log('D2D_CAPTURE_COMPLETE',out,observations.length);
