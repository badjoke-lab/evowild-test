import {chromium} from 'playwright';
import fs from 'node:fs';import {gzipSync} from 'node:zlib';
export function captureBodyReturn(){
 const a=window.sRunReview;window.requestAnimationFrame=()=>0;
 const snap=()=>({phase:a.sample().phase,distance:a.sample().distance,body:a.bodySample(),bodyPoints:a.probe(a.bodyVertexIds),soles:a.motionSample().soles,contact:a.motionSample().contact});
 const traces=[];a.setRate(1);
 // Sequential integrated motion, not successive diagnostic seeks.
 for(const range of [[.04,.20],[.38,.68]]){
  a.setPhase(range[0],'SIDE',false);const rows=[];
  for(let i=0;i<=Math.round((range[1]-range[0])*2000);i++){if(i)a.step(.0005/2.4);rows.push(snap());}traces.push({range,dt:.0005/2.4,rows});
 }
 const boundaries=[];
 // Explicit reset for independent probes only; each probe then progresses normally.
 for(const phase of [.06,.18,.3940692842400813,.40506096654409807,.44,.47,.5,.53,.56,.59,.62,.64]){
  for(const eps of [1e-4,1e-5,1e-6]){
   a.setRate(1);a.setPhase(phase-2.4*eps,'SIDE',false);const left=snap();a.step(eps);const mid=snap();a.setRate(1.5);a.step(0);const command=snap();a.step(eps);const right=snap();
   boundaries.push({phase,eps,left,mid,command,right});
  }
 }
 return {bodyVertexIds:a.bodyVertexIds,traces,boundaries};
}
export function summarizeBodyReturn(data){
 const sub=(p,q)=>p.map((v,i)=>v-q[i]),norm=v=>Math.hypot(...v),vel=(p,q,dt)=>sub(p,q).map(v=>v/dt);
 const angular=(a,b,dt)=>{
  // World quaternion increment b * inverse(a), shortest arc.
  const [x,y,z,w]=a,[X,Y,Z,W]=b;let q=[-W*x+X*w-Y*z+Z*y,-W*y+X*z+Y*w-Z*x,-W*z-X*y+Y*x+Z*w,W*w+X*x+Y*y+Z*z];if(q[3]<0)q=q.map(v=>-v);
  const s=norm(q.slice(0,3)),k=s>1e-14?2*Math.atan2(s,q[3])/s/dt:2/dt;return q.slice(0,3).map(v=>v*k);
 };
 const ranges=data.traces.map(({range,rows,dt})=>({range,parts:rows[0].body.map((b,j)=>{
  const speeds=[],omegas=[];
  for(let i=1;i<rows.length;i++){
   const p=rows[i-1],q=rows[i],v=vel(q.body[j].position,p.body[j].position,dt);v[2]-=(q.distance-p.distance)/dt;
   speeds.push(v);omegas.push(angular(p.body[j].quaternion,q.body[j].quaternion,dt));
  }
  const peak=a=>{let index=0;a.forEach((v,i)=>{if(v>a[index])index=i;});return {value:a[index],phase:rows[index+1].phase};};
  return {name:b.name,peakSpeed:peak(speeds.map(norm)),peakAngularSpeed:peak(omegas.map(norm)),peakAcceleration:peak(speeds.slice(1).map((v,i)=>norm(sub(v,speeds[i]))/dt)),peakAngularAcceleration:peak(omegas.slice(1).map((v,i)=>norm(sub(v,omegas[i]))/dt))};
 })}));
 const boundaries=data.boundaries.map(({phase,eps,left,mid,command,right})=>{
  const points=s=>[...s.bodyPoints,...s.soles.flatMap(f=>f.points)];const l=points(left),m=points(mid),c=points(command),r=points(right);
  return {phase,eps,positionJump:Math.max(...m.map((p,i)=>norm(sub(p,c[i])))),velocityResidual:Math.max(...m.map((p,i)=>norm(sub(vel(r[i],c[i],eps),vel(p,l[i],eps))))),bodyVelocityResidual:Math.max(...mid.bodyPoints.map((p,i)=>norm(sub(vel(right.bodyPoints[i],command.bodyPoints[i],eps),vel(p,left.bodyPoints[i],eps)))))};
 });
 return {ranges,boundaries};
}
if(process.argv[1]?.endsWith('measure_s_body_return.mjs')){
 const out=process.env.S_RETURN_OUT||'docs/2p5d/evidence/20261028-s-return-d2c1';fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({executablePath:process.env.CHROMIUM_PATH||undefined,args:['--enable-unsafe-swiftshader']});const page=await browser.newPage({viewport:{width:960,height:640}});const reports=[];
 const variants=process.env.S_RETURN_QUERY?[['after',process.env.S_RETURN_QUERY]]:[['native','&toe=roll-v2'],['before','&toe=roll-v2&body=push-v1']];
 for(const [label,query] of variants){
  await page.goto('http://127.0.0.1:4173/evowild-test/s-run-review.html?rig=contact-v3'+query);await page.waitForFunction(()=>window.sRunReview);
  const data=await page.evaluate(captureBodyReturn);fs.writeFileSync(`${out}/${label}-return-trace.json.gz`,gzipSync(JSON.stringify(data)));reports.push({label,...summarizeBodyReturn(data)});
 }
 fs.writeFileSync(`${out}/return-summary.json`,JSON.stringify(reports,null,2)+'\n');await browser.close();
}
