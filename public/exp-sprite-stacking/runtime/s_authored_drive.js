import {Vector3,Quaternion} from 'three';
// Review-only adapter for the independently authored GLB. Poses come from
// GLTF tracks; IK owns planted soles. FK humerus/elbow poses guide swing.
export function createAuthoredDrive(mesh,nativeClip,driveClip,{nativeJoinClip=null}={}){
 if(!driveClip)throw Error('Missing authored D3-C v2 pose clip');
 const bones=new Map(mesh.skeleton.bones.map(b=>[b.name,b]));
 bones.set(mesh.parent.name,mesh.parent);
 const tracks=clip=>clip.tracks.map(t=>{const [name,property]=t.name.split('.');const it=t.createInterpolant();
  it.resultBuffer=new Float64Array(t.getValueSize()/(t.createInterpolant.isInterpolantFactoryMethodGLTFCubicSpline?3:1));
  return {name,property,bone:bones.get(name),it};}).filter(t=>t.bone);
 const delta=tracks(driveClip),scapNative=tracks(nativeClip).filter(t=>t.name.endsWith('_scapula'));
 const join=nativeJoinClip?tracks(nativeJoinClip):[],native=join.length?tracks(nativeClip):[];
 const joinTimes=nativeJoinClip?.tracks[0].times;
 const scapRest=[...bones.values()].filter(b=>b.name.endsWith('_scapula')).map(b=>({bone:b,position:b.position.clone()}));
 const duration=nativeClip.duration,wrap=t=>((t%duration)+duration)%duration;let stamp=0;
 return {applyBody(time){stamp=wrap(time);
  if(joinTimes&&stamp>joinTimes[0]&&stamp<joinTimes.at(-1))for(const t of join){
   const source=native.find(n=>n.name===t.name&&n.property===t.property),a=source.it.evaluate(stamp),b=t.it.evaluate(stamp);
   // Left-multiply the native-to-bridge delta so existing D3-B local load
   // rotations survive. Only the v3 GLB supplies this optional clip.
   if(t.property==='quaternion')t.bone.quaternion.premultiply(new Quaternion().fromArray(b).normalize().multiply(new Quaternion().fromArray(a).invert())).normalize();
   else t.bone[t.property].add(new Vector3().fromArray(b).sub(new Vector3().fromArray(a)));
  }
  // A native translation track is absent for these new bones. Explicit reset
  // prevents accumulated glide and repeated-dt0 drift from mixer caching.
  for(const s of scapRest)s.bone.position.copy(s.position);
  for(const t of scapNative)t.bone[t.property].fromArray(t.it.evaluate(stamp));
  for(const t of delta){if(/^fore_.*_(upper|lower)$/.test(t.name))continue;const values=t.it.evaluate(stamp);
   if(t.property==='quaternion'&&t.name.endsWith('_scapula'))t.bone.quaternion.fromArray(values).normalize();
   else if(t.property==='quaternion')t.bone.quaternion.multiply(t.bone.quaternion.clone().fromArray(values)).normalize();
   else t.bone.position.add(new Vector3().fromArray(values));
  }mesh.updateWorldMatrix(true,false);
 },swingGuides(limbs,trace=null){const result={};for(const l of limbs){if(l.hind)continue;
   const before=l.bones.at(-1).getWorldPosition(new Vector3()),saved=l.bones.slice(0,2).map(b=>b.quaternion.clone());
   for(const t of delta)if(l.bones.slice(0,2).includes(t.bone))t.bone.quaternion.multiply(t.bone.quaternion.clone().fromArray(t.it.evaluate(stamp))).normalize();
   l.bones[0].updateWorldMatrix(true,true);result[l.name]=l.bones.at(-1).getWorldPosition(new Vector3()).sub(before);
   if(trace){const joints=l.bones.map(b=>b.getWorldPosition(new Vector3()));trace[l.name]={offset:result[l.name].toArray(),joints:joints.map(p=>p.toArray()),elbowDegrees:joints[0].clone().sub(joints[1]).angleTo(joints[2].clone().sub(joints[1]))*180/Math.PI};}
   l.bones.slice(0,2).forEach((b,i)=>b.quaternion.copy(saved[i]));l.bones[0].updateWorldMatrix(true,true);
  }return result;
 }};
}
