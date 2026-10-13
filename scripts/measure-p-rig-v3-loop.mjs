import fs from 'node:fs';
import assert from 'node:assert/strict';
import {chromium} from '@playwright/test';
const dir='docs/evidence/p-rig-v3-20261013';
const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||'/usr/bin/chromium',args:['--no-sandbox']});
try{
 const page=await browser.newPage();
 await page.goto('http://127.0.0.1:4173/evowild-test/race-quality.html');
 const result=await page.evaluate(async()=>{
  const {loadPLayered,drawPLayered}=await import('/evowild-test/src/p_layered.js');await loadPLayered('/evowild-test/');
  const sample=phase=>{
   const canvas=Object.assign(document.createElement('canvas'),{width:416,height:320}),ctx=canvas.getContext('2d');
   const pose=drawPLayered(ctx,{distance:100,phaseOffset:0},{x:208,y:296,width:416,ppm:10,projectX:m=>208+(m-100)*10,groundY:()=>296,lane:1.5,time:0,reviewPhase:phase});
   const points=pose.feet.flatMap(f=>[f.hip,f.knee,f.ankle,{x:f.screenX,y:f.screenY}]);
   return {points,pixels:Array.from(ctx.getImageData(0,0,416,320).data)};
  };
  const distance=(a,b)=>Math.max(...a.points.map((p,i)=>Math.hypot(p.x-b.points[i].x,p.y-b.points[i].y)));
  const zero=sample(0),one=sample(1),epsilon=.0001;
  return {units:'416x320 rig source pixels',epsilonCycle:epsilon,
   exactEndpointMaxJointDelta:distance(zero,one),exactEndpointDifferentChannels:zero.pixels.filter((p,i)=>p!==one.pixels[i]).length,
   boundaries:[{name:'6-to-7',phase:.5},{name:'8-to-9',phase:8/12},{name:'9-to-10',phase:9/12},{name:'12-to-1',phase:1}].map(b=>({...b,maxJointTravelAcrossEpsilon:distance(sample(b.phase-epsilon),sample(b.phase+epsilon))})),
   limitation:'Flat-ground stateless phase probe using the runtime painter. Live support anchoring and body-height history are measured separately in the video traces.'};
 });
 fs.writeFileSync(`${dir}/loop-validation.json`,JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
 assert.ok(result.exactEndpointMaxJointDelta<1e-8);assert.equal(result.exactEndpointDifferentChannels,0);
 assert.ok(result.boundaries.every(b=>b.maxJointTravelAcrossEpsilon<.5));
}finally{await browser.close();}
