import {summarizeProfile} from './s_contact_profiles.mjs';
export function summarizeToeProfile(trace){
 const old=summarizeProfile(trace),frames=trace.frames;
 return {...old,feet:old.feet.map((foot,i)=>{
  let supportSlip=0,maxSupportStep=0,flatTime=0,toeTime=0,guardPenetration=0,minPitch=Infinity,maxPitch=-Infinity,flatRear=Infinity,toeRear=-Infinity,supportError=0;
  for(let j=0;j<frames.length;j++){
   const f=frames[j],s=f.supportVertices[i],surf=f.footSurfaces[i],l=f.contact.limbs[i];
   guardPenetration=Math.max(guardPenetration,-surf.guardMinY);minPitch=Math.min(minPitch,surf.pitchDegrees);maxPitch=Math.max(maxPitch,surf.pitchDegrees);
   if(s.mode==='FLAT_SUPPORT')flatRear=Math.min(flatRear,surf.rear[1]);if(s.mode==='TOE_SUPPORT')toeRear=Math.max(toeRear,surf.rear[1]);
   if(s.mode!=='SWING')supportError=Math.max(supportError,Math.abs(s.point[1]));
   if(!j)continue;const p=frames[j-1],prev=p.supportVertices[i],dt=f.t-p.t;
   if(s.mode==='FLAT_SUPPORT')flatTime+=dt;if(s.mode==='TOE_SUPPORT')toeTime+=dt;
   if(s.mode!=='SWING'&&prev.mode!=='SWING'&&s.id===prev.id&&l.touchdowns===p.contact.limbs[i].touchdowns){const d=Math.hypot(s.point[0]-prev.point[0],s.point[2]-prev.point[2]);supportSlip+=d;maxSupportStep=Math.max(maxSupportStep,d);}
  }
  return {...foot,legacyAllPatchMovement:foot.stanceSlip,supportSlip,maxSupportStep,flatTime,toeTime,guardPenetration,pitchRange:[minPitch,maxPitch],rearRise:Number.isFinite(toeRear)?toeRear-flatRear:0,maxSupportPlaneError:supportError};
 })};
}
