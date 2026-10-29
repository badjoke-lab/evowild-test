// D3 measurement of actual skinned S rig: one continuous integrated stride, no
// screenshot-only proxy. Records both review variants with same native GLB.
import {chromium} from 'playwright';
import {mkdirSync,writeFileSync} from 'node:fs';
const output='docs/2p5d/evidence/20261029-s-d3-cycle-audit';
mkdirSync(output,{recursive:true});
const browser=await chromium.launch({args:['--enable-unsafe-swiftshader']});
const page=await browser.newPage({viewport:{width:960,height:640}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const audit=[];
for(const [label,body] of [['before','push-v2'],['after','push-v3'],['trial','push-v4']]){
 await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3&toe=roll-v3&body='+body);
 await page.waitForFunction(()=>window.sRunReview?.bodySample);
 await page.evaluate(()=>{window.requestAnimationFrame=()=>0;});
 for(const rate of [.5,1,1.5]){
  const data=await page.evaluate(({rate})=>{
   const a=window.sRunReview,n=96;
   const period=a.measureCycle(rate,n).cycleDuration;
   a.setRate(rate);a.setPhase(0,'SIDE',false);
   const frames=[];
   for(let i=0;i<=n;i++){
    if(i)a.step(period/n);
    a.advance(0);
    const state=a.sample(),parts=a.bodySample(),motion=a.motionSample();
    const rootZ=state.distance;
    const bodies=Object.fromEntries(parts.map(b=>[b.name,{pos:b.position.map((v,j)=>j===2?v-rootZ:v),q:b.quaternion}]));
    const legs=motion.contact.limbs.map(l=>({name:l.name,stage:l.stage,stance:l.anchor!==null,
      reachError:l.reachError,kneeAngles:l.jointAngles}));
    frames.push({phase:state.phase,cycle:i/n,rate:state.rate,bodies,legs});
   }
   return {period,bodyNames:Object.keys(frames[0].bodies),frames};
  },{rate});
  const key=(s,i)=>s.bodies[i];
  const names=['pelvis','spine','chest','neck','head','tail'].filter(k=>data.bodyNames.includes(k));
  const range=v=>Math.max(...v)-Math.min(...v);
  const angular=qs=>{
   const q0=qs[0],dot=q=>Math.abs(q.reduce((sum,x,i)=>sum+x*q0[i],0));
   return Math.max(...qs.map(q=>2*Math.acos(Math.max(-1,Math.min(1,dot(q))))))*180/Math.PI;
  };
  const bones=Object.fromEntries(names.map(name=>{
   const ps=data.frames.map(f=>key(f,name).pos);
   const relToPelvis=data.frames.map(f=>f.bodies.pelvis&&name!=='pelvis'?key(f,name).pos.map((v,i)=>v-f.bodies.pelvis.pos[i]):[0,0,0]);
   return [name,{worldRangeX:range(ps.map(p=>p[0])),worldRangeY:range(ps.map(p=>p[1])),worldRangeZ:range(ps.map(p=>p[2])),
      relativePelvisYRange:range(relToPelvis.map(p=>p[1])),quaternionAngularSpreadFromInitialDeg:angular(data.frames.map(f=>key(f,name).q))}];
  }));
  const counts=data.frames.map(f=>f.legs.filter(l=>l.stance).length);
  const stageCounts=Object.fromEntries(data.frames[0].legs.map((leg,i)=>[leg.name,Object.fromEntries(['CONTACT','PUSH','RECOVERY','FLIGHT','EXTENSION'].map(stage=>[stage,data.frames.filter(f=>f.legs[i].stage===stage).length]))]));
  const metrics={label,rate,period:data.period,samples:data.frames.length,bodyNames:data.bodyNames,bones,
    supportCountDistribution:Object.fromEntries([0,1,2,3,4].map(k=>[k,counts.filter(x=>x===k).length])),
    supportCountMin:Math.min(...counts),supportCountMax:Math.max(...counts),stages:stageCounts,
    maxReachError:Math.max(...data.frames.flatMap(f=>f.legs.map(l=>l.reachError))),
    sampledPhases:[0,.125,.25,.375,.5,.625,.75,.875,1].map(t=>data.frames[Math.round(t*96)]).map(f=>({cycle:f.cycle,phase:f.phase,stance:f.legs.filter(l=>l.stance).map(l=>l.name),
      parts:Object.fromEntries(names.map(name=>[name,{pos:f.bodies[name].pos,q:f.bodies[name].q}]))}))};
  audit.push(metrics);
  console.log('D3_GAIT_SUMMARY',JSON.stringify({label,rate,bones,distribution:metrics.supportCountDistribution,stageCounts,reachError:metrics.maxReachError}));
 }
}
await browser.close();
writeFileSync(output+'/d3-cycle-metrics.json',JSON.stringify({source:'Native S GLB via integrated continuous WebGL motion, no artificial image data',stepsPerCycle:96,variants:['push-v2','push-v3','push-v4'],speeds:[.5,1,1.5],pageErrors:errors,results:audit},null,2)+'\n');
if(errors.length)throw Error('Browser errors: '+JSON.stringify(errors));
