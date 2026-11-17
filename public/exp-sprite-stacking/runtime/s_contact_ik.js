import {Vector3,Quaternion} from 'three';
import {createToeRoll} from './s_toe_roll.js';
const forward=new Vector3(0,0,1);
const mod=x=>((x%1)+1)%1;
const smooth=x=>x*x*(3-2*x);
// Review-only locomotion. Rest geometry/joint positions are immutable v2.
// Root/chest/neck keep their native animation; only limb rotations are solved.
export function createContactIK(mesh,patches,{toeSurfaces=null,continuousToe=false,toeRoundingWidth=.003,foreReach=false}={}){
 const limbs=patches.map((patch,i)=>{
  const hind=patch.name.startsWith('hind'),names=['_upper','_lower','_foot',...(hind?['_toe']:[])];
  const bones=names.map(s=>mesh.skeleton.bones.find(b=>b.name===patch.name+s));
  const positions=bones.map(b=>b.getWorldPosition(new Vector3()));
  const rotations=bones.map(b=>b.getWorldQuaternion(new Quaternion()));
  const segments=positions.slice(1).map((p,i)=>p.clone().sub(positions[i]));
  const point=patch.indices.map(i=>mesh.localToWorld(mesh.getVertexPosition(i,new Vector3()))).reduce((a,p)=>p.y<a.y?p:a);
  return {name:patch.name,hind,bones,rotations,segments,lengths:segments.map(s=>s.length()),soleOffset:point.clone().sub(positions.at(-1)),base:point,offset:[.64,.72,.15,.24][i],stance:hind?.23:.17};
 });
 if(toeSurfaces)limbs.forEach((l,i)=>{l.roll=createToeRoll(toeSurfaces[i],l.base,l.hind?28:22,{continuous:continuousToe,roundingWidth:toeRoundingWidth});});
 function rotate(limb,index,direction){
  const bone=limb.bones[index],delta=new Quaternion().setFromUnitVectors(limb.segments[index].clone().normalize(),direction.clone().normalize());
  const world=delta.multiply(limb.rotations[index]);
  bone.quaternion.copy(bone.parent.getWorldQuaternion(new Quaternion()).invert().multiply(world));bone.updateWorldMatrix(false,true);
 }
 function twoBone(a,b,l1,l2){
  const direction=b.clone().sub(a),requested=direction.length(),d=Math.min(l1+l2-.0005,Math.max(Math.abs(l1-l2)+.0005,requested));direction.normalize();
  const pole=forward.clone().addScaledVector(direction,-forward.dot(direction)).normalize();
  const along=(l1*l1-l2*l2+d*d)/(2*d),height=Math.sqrt(Math.max(0,l1*l1-along*along));
  return {knee:a.clone().addScaledVector(direction,along).addScaledVector(pole,height),end:a.clone().addScaledVector(direction,d),reachError:Math.abs(requested-d)};
 }
 const kinematics=rate=>{const cadence=rate>0?2.4*Math.sqrt(rate):0;return {speed:4*rate,cadence,period:cadence?1/cadence:Infinity,stride:cadence?4*rate/cadence:0};};
 let state;
 function nominal(limb,cycles,distance,rate){
  const k=kinematics(rate),p=mod(cycles-limb.offset),span=k.stride*limb.stance;
  let z,y,vz,vy;
  if(p<limb.stance){z=span/2-k.stride*p;y=0;vz=0;vy=0;}
  else {const u=(p-limb.stance)/(1-limb.stance),d=-k.stride*(1-limb.stance);
   z=-span/2+span*smooth(u)+d*(u-3*u*u+2*u*u*u);
   y=(limb.hind?.48:.34)*Math.sin(Math.PI*u)**2;
   vz=k.speed*6*u*(1-u)/(1-limb.stance);
   vy=(limb.hind?.48:.34)*Math.PI*Math.sin(2*Math.PI*u)*k.cadence/(1-limb.stance);
  }
  return {target:new Vector3(limb.base.x,y,limb.base.z+distance+z+(limb.hind?.18:0)),velocity:new Vector3(0,vy,vz),stance:p<limb.stance,nextEvent:cycles+(p<limb.stance?limb.stance-p:1-p)};
 }
 function reset(cycles=0,distance=0,rate=1){
  // Explicit diagnostic seek only. Normal time progression never resets anchors.
  const activeRate=rate>0?rate:state?.rate||1;
  state={cycles,distance,elapsed:0,rate:activeRate,requestedRate:rate,frozen:rate===0,feet:limbs.map(l=>{
   const f=nominal(l,cycles,distance,activeRate);return {...f,anchor:f.stance?f.target.clone():null,touchdowns:0};
  })};
  if(foreReach){state.poseRate=activeRate;state.poseRateVelocity=0;}
  return state;
 }
 function events(){
  state.feet.forEach((f,i)=>{
   if(f.nextEvent>state.cycles+1e-9)return;
   f.stance=!f.stance;f.velocity.set(0,0,0);
   if(f.stance){f.target.y=0;f.anchor=f.target.clone();f.touchdowns++;f.nextEvent+=limbs[i].stance;}
   else {f.anchor=null;f.nextEvent+=1-limbs[i].stance;}
  });
 }
 function advance(dt,requestedRate){
  if(!Number.isFinite(dt)||dt<0||!Number.isFinite(requestedRate)||requestedRate<0)throw Error('Invalid locomotion step');
  state.requestedRate=requestedRate;state.frozen=requestedRate===0;
  if(dt===0||state.frozen)return state; // A command has no positional side effect.
  let remaining=dt;
  while(remaining>1e-10){
   events();const k=kinematics(state.rate);
   const next=Math.min(...state.feet.map(f=>f.nextEvent));
   const h=Math.min(remaining,1/480,(next-state.cycles)/k.cadence);
   if(h<=1e-10){events();continue;}
   // Replan longitudinal swing from its actual current position AND world
   // velocity. Touchdown follows predicted travel; stance anchors never do.
   state.feet.forEach((f,i)=>{
    if(f.stance)return;
    const l=limbs[i],duration=(f.nextEvent-state.cycles)/k.cadence;
    const landing=l.base.z+(l.hind?.18:0)+state.distance+k.speed*duration+k.stride*l.stance/2;
    const u=Math.min(1,h/duration),z0=f.target.z,v0=f.velocity.z;
    f.target.z=(2*u*u*u-3*u*u+1)*z0+(u*u*u-2*u*u+u)*duration*v0+(-2*u*u*u+3*u*u)*landing;
    f.velocity.z=((6*u*u-6*u)*z0+(3*u*u-4*u+1)*duration*v0+(-6*u*u+6*u)*landing)/duration;
    const phase=1-(f.nextEvent-state.cycles-k.cadence*h)/(1-l.stance),height=l.hind?.48:.34;
    f.target.y=height*Math.sin(Math.PI*phase)**2;
    f.velocity.y=height*Math.PI*Math.sin(2*Math.PI*phase)*k.cadence/(1-l.stance);
   });
   state.cycles+=k.cadence*h;state.distance+=k.speed*h;state.elapsed+=h;
   // Bounded acceleration changes both travel and cadence continuously in
   // elapsed time. Zero is an explicit freeze, not a decay that moves feet.
   state.rate+=Math.max(-4*h,Math.min(4*h,requestedRate-state.rate));
   if(foreReach){
    // D3-B amplitudes need continuous velocity, not just continuous rate.
    // Keep locomotion rate/cadence/travel untouched. This exact critically
    // damped response carries its velocity across commands and substeps.
    // At steady speed the original reach and chest amplitudes are unchanged.
    const omega=20,offset=state.poseRate-state.rate;
    const c=state.poseRateVelocity+omega*offset,decay=Math.exp(-omega*h);
    state.poseRate=state.rate+(offset+c*h)*decay;
    state.poseRateVelocity=(state.poseRateVelocity-omega*c*h)*decay;
   }
   remaining-=h;events();
  }
  return state;
 }
 return {limbs,kinematics,reset,advance,get state(){return state;},apply(authoredSwing=null){
  if(!state)reset();
  const {cycles,distance}=state,k=kinematics(state.rate),diagnostics=[];
  mesh.updateWorldMatrix(true,false);
  for(let i=0;i<limbs.length;i++){
   const limb=limbs[i],f=state.feet[i],p=mod(cycles-limb.offset),u=(p-limb.stance)/(1-limb.stance);
   const stage=f.stance?(p<limb.stance*.55?'CONTACT':'PUSH'):(u<.42?'RECOVERY':u<.58?'FLIGHT':'EXTENSION');
   const target=f.target;
   // D3-B opt-in. Add forward visual swing during the FORELEGS' airborne
   // recovery only. The touchdown target/anchor stays exactly unchanged.
   // Value and phase slope vanish at swing endpoints. The persistent pose
   // rate additionally prevents speed commands from jumping its world velocity.
   const swing=Math.max(0,Math.min(1,u));
   const forwardEnvelope=f.stance||limb.hind||!foreReach?0:
    Math.sin(Math.PI*swing)**2*(.55+.45*swing);
   const additionalReach=forwardEnvelope*(.045+.035*Math.max(0,Math.min(1.5,state.poseRate??state.rate)));
   let visualTarget=additionalReach?target.clone().addScaledVector(forward,additionalReach):target;
   if(authoredSwing&&!f.stance&&!limb.hind&&authoredSwing[limb.name])visualTarget=visualTarget.clone().add(authoredSwing[limb.name]);
   const roll=limb.roll?.pose(p,limb.stance);
   const footRotation=roll?roll.rotation.clone().multiply(limb.rotations.at(-1)):limb.rotations.at(-1);
   const end=roll?visualTarget.clone().add(roll.translation).sub(limb.soleOffset.clone().applyQuaternion(roll.rotation)):visualTarget.clone().sub(limb.soleOffset),hip=limb.bones[0].getWorldPosition(new Vector3());
   let solved;
   if(limb.hind){
    // Retain hock-to-toe segment length and anatomical rear bend; solve knee
    // ahead of the hip/hock axis, never flip to the opposite IK solution.
    const distal=limb.segments[2].clone();
    const hock=end.clone().sub(distal);solved=twoBone(hip,hock,...limb.lengths);
    rotate(limb,0,solved.knee.clone().sub(hip));
    rotate(limb,1,solved.end.clone().sub(solved.knee));
    rotate(limb,2,distal);
   }else{
    solved=twoBone(hip,end,...limb.lengths);
    rotate(limb,0,solved.knee.clone().sub(hip));rotate(limb,1,solved.end.clone().sub(solved.knee));
   }
   const foot=limb.bones.at(-1);foot.quaternion.copy(foot.parent.getWorldQuaternion(new Quaternion()).invert().multiply(footRotation));foot.updateWorldMatrix(false,true);
   const joints=limb.bones.map(b=>b.getWorldPosition(new Vector3()));
   const angles=joints.slice(1,-1).map((p,j)=>joints[j].clone().sub(p).angleTo(joints[j+2].clone().sub(p))*180/Math.PI);
   diagnostics.push({name:limb.name,stage,phase:p,foreVisualReach:additionalReach,target:target.toArray(),velocity:(state.frozen?new Vector3():f.velocity).toArray(),anchor:f.anchor?.toArray()||null,touchdowns:f.touchdowns,toe:roll?{mode:roll.mode,angleDegrees:roll.angle*180/Math.PI,pivotId:roll.pivotId,supportWorld:target.clone().add(roll.translation).add(roll.pivotOffset.clone().applyQuaternion(roll.rotation)).toArray()}:null,reachError:solved.reachError,jointAngles:angles,joints:joints.map(p=>p.toArray())});
  }
  mesh.skeleton.update();return {cycles,distance,elapsed:state.elapsed,effectiveRate:state.rate,...(foreReach?{poseRate:state.poseRate,poseRateVelocity:state.poseRateVelocity}:{}),requestedRate:state.requestedRate,frozen:state.frozen,...k,limbs:diagnostics};
 }};
}
