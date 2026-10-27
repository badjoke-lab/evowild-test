export const profiles=[
 {name:'acceleration',phase:.2,mode:'linear',knots:[[0,.5],[.2,.5],[.8,1],[1.4,1.5],[2,1.5]]},
 {name:'deceleration',phase:.7,mode:'linear',knots:[[0,1.5],[.2,1.5],[.8,1],[1.4,.5],[2,.5]]},
 {name:'abrupt-hind',phase:.2,mode:'step',knots:[[0,.5],[.12,1.5],[.65,.5],[1.2,.5]]},
 {name:'abrupt-fore',phase:.7,mode:'step',knots:[[0,.5],[.12,1.5],[.65,.5],[1.2,.5]]},
];
// Serialized into the browser by Playwright; every observed point is a real
// SkinnedMesh sole vertex. No controller-target surrogate is used for slip.
export function captureContactProfile({profile,hz=240,recordFootSurface=false,recordBody=false}){
 const api=window.sRunReview,rateAt=t=>{
  const k=profile.knots;let i=0;while(i+1<k.length&&t>=k[i+1][0]-1e-10)i++;
  if(profile.mode==='step'||i===k.length-1)return k[i][1];
  const u=(t-k[i][0])/(k[i+1][0]-k[i][0]);return k[i][1]+u*(k[i+1][1]-k[i][1]);
 };
 const eps=1e-5,duration=profile.knots.at(-1)[0],count=Math.round(duration*hz),dt=duration/count;
 api.setRate(rateAt(0));api.setPhase(profile.phase,'REAR_3_4');
 const frames=[],switches=[];let leftProbe=null,lastRate=rateAt(0);
 for(let i=0;i<=count;i++){
  const t=i*dt,requested=rateAt(t),before=api.motionSample();api.setRate(requested);api.step(0);const after=api.motionSample();
  const jump=after.soles.map((s,f)=>Math.max(...s.points.map((p,k)=>Math.hypot(...p.map((x,d)=>x-before.soles[f].points[k][d])))));
  if(recordFootSurface){after.footSurfaces=api.footSample().map(({points,...f})=>f);after.supportVertices=after.contact.limbs.map((l,j)=>{const id=l.toe?.pivotId??api.footSurfaces[j].flatPivot;return {id,point:api.probe([id])[0],mode:l.toe?.mode??(['CONTACT','PUSH'].includes(l.stage)?'FLAT_SUPPORT':'SWING')};});}
  if(recordBody)after.body=api.bodySample();
  frames.push({t,requested,...after});if(i===count)break;
  api.step(eps);const rightProbe=api.motionSample();
  if(Math.abs(requested-lastRate)>1e-9){
   const velocityResidual=leftProbe?after.soles.map((s,f)=>Math.max(...s.points.map((p,k)=>Math.hypot(...p.map((x,d)=>
    (rightProbe.soles[f].points[k][d]-x)/eps-(before.soles[f].points[k][d]-leftProbe.soles[f].points[k][d])/eps))))):null;
   switches.push({t,from:lastRate,to:requested,positionJump:jump,meshVelocityResidual:velocityResidual,beforePhase:before.contact.cycles});
  }
  api.step(dt-2*eps);leftProbe=api.motionSample();api.step(eps);lastRate=requested;
 }
 api.advance(0);return {profile,hz,eps,frames,switches};
}
export function summarizeProfile(trace){
 const {frames,switches}=trace,first=frames[0],last=frames.at(-1);
 let speedIntegral=0,cadenceIntegral=0;
 for(let i=1;i<frames.length;i++){const a=frames[i-1],b=frames[i],dt=b.t-a.t;speedIntegral+=(a.contact.speed+b.contact.speed)*dt/2;cadenceIntegral+=(a.contact.cadence+b.contact.cadence)*dt/2;}
 const feet=first.soles.map((f,index)=>{
  let slip=0,maxStepSlip=0,penetration=0,recovery=0,reach=0,angleMin=180,angleMax=0,lengthDrift=0,contactTime=0;
  const joints=first.contact.limbs[index].joints,lengths=joints.slice(1).map((p,j)=>Math.hypot(...p.map((x,d)=>x-joints[j][d])));
  for(let i=0;i<frames.length;i++){
   const curr=frames[i],sole=curr.soles[index],limb=curr.contact.limbs[index];penetration=Math.max(penetration,-sole.minY);recovery=Math.max(recovery,sole.minY);reach=Math.max(reach,limb.reachError);angleMin=Math.min(angleMin,...limb.jointAngles);angleMax=Math.max(angleMax,...limb.jointAngles);
   limb.joints.slice(1).forEach((p,j)=>lengthDrift=Math.max(lengthDrift,Math.abs(Math.hypot(...p.map((x,d)=>x-limb.joints[j][d]))-lengths[j])));
   if(!i)continue;const prev=frames[i-1],pl=prev.contact.limbs[index];
   if(['CONTACT','PUSH'].includes(limb.stage)&&['CONTACT','PUSH'].includes(pl.stage)&&limb.touchdowns===pl.touchdowns){
    contactTime+=curr.t-prev.t;let sum=0;
    sole.points.forEach((p,k)=>{const q=prev.soles[index].points[k],d=Math.hypot(p[0]-q[0],p[2]-q[2]);sum+=d;maxStepSlip=Math.max(maxStepSlip,d);});slip+=sum/sole.points.length;
   }
  }
  return {name:f.name,maxPenetration:penetration,stanceSlip:slip,maxStanceStepSlip:maxStepSlip,contactTime,recoveryHeight:recovery,maxReachError:reach,jointAngleRange:[angleMin,angleMax],maxSegmentLengthDrift:lengthDrift,maxZeroTimeJump:Math.max(0,...switches.map(s=>s.positionJump[index])),maxMeshVelocityResidual:Math.max(0,...switches.map(s=>s.meshVelocityResidual?.[index]||0))};
 });
 return {profile:trace.profile.name,samples:frames.length,duration:last.t,travel:last.distance-first.distance,cycles:last.contact.cycles-first.contact.cycles,speedIntegral,travelIntegralError:last.distance-first.distance-speedIntegral,cadenceIntegral,cycleIntegralError:last.contact.cycles-first.contact.cycles-cadenceIntegral,feet};
}
