import {Vector3} from 'three';
// Review-only adapter for the independently authored GLB. Poses come from
// GLTF tracks; IK owns planted soles. FK humerus/elbow poses guide swing.
export function createAuthoredDrive(mesh,nativeClip,driveClip){
 if(!driveClip)throw Error('Missing authored D3-C v2 pose clip');
 const bones=new Map(mesh.skeleton.bones.map(b=>[b.name,b]));
 const tracks=clip=>clip.tracks.map(t=>{const [name,property]=t.name.split('.');const it=t.createInterpolant();
  it.resultBuffer=new Float64Array(t.getValueSize()/(t.createInterpolant.isInterpolantFactoryMethodGLTFCubicSpline?3:1));
  return {name,property,bone:bones.get(name),it};}).filter(t=>t.bone);
 const delta=tracks(driveClip),scapNative=tracks(nativeClip).filter(t=>t.name.endsWith('_scapula'));
 const scapRest=[...bones.values()].filter(b=>b.name.endsWith('_scapula')).map(b=>({bone:b,position:b.position.clone()}));
 const duration=nativeClip.duration,wrap=t=>((t%duration)+duration)%duration;let stamp=0;
 return {applyBody(time){stamp=wrap(time);
  // A native translation track is absent for these new bones. Explicit reset
  // prevents accumulated glide and repeated-dt0 drift from mixer caching.
  for(const s of scapRest)s.bone.position.copy(s.position);
  for(const t of scapNative)t.bone[t.property].fromArray(t.it.evaluate(stamp));
  for(const t of delta){if(/^fore_.*_(upper|lower)$/.test(t.name))continue;const values=t.it.evaluate(stamp);
   if(t.property==='quaternion'&&t.name.endsWith('_scapula'))t.bone.quaternion.fromArray(values).normalize();
   else if(t.property==='quaternion')t.bone.quaternion.multiply(t.bone.quaternion.clone().fromArray(values)).normalize();
   else t.bone.position.add(new Vector3().fromArray(values));
  }mesh.updateWorldMatrix(true,false);
 },swingGuides(limbs){const result={};for(const l of limbs){if(l.hind)continue;
   const before=l.bones.at(-1).getWorldPosition(new Vector3()),saved=l.bones.slice(0,2).map(b=>b.quaternion.clone());
   for(const t of delta)if(l.bones.slice(0,2).includes(t.bone))t.bone.quaternion.multiply(t.bone.quaternion.clone().fromArray(t.it.evaluate(stamp))).normalize();
   l.bones[0].updateWorldMatrix(true,true);result[l.name]=l.bones.at(-1).getWorldPosition(new Vector3()).sub(before);
   l.bones.slice(0,2).forEach((b,i)=>b.quaternion.copy(saved[i]));l.bones[0].updateWorldMatrix(true,true);
  }return result;
 }};
}
