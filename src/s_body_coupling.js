// Review-only timing alignment of EXISTING native body animation. No added
// bob, amplitude scaling, force/COM simulation or mesh/rest-pose modification.
export function createBodyCoupling(mesh,clip){
 const ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*x*(x*(x*6-15)+10);};
 const names=new Set(['root','pelvis','spine','chest','neck','head','tail','EvoWild_S_Armature_V3']);
 const channels=clip.tracks.flatMap(track=>{
  const [name,property]=track.name.split('.');
  const bone=mesh.skeleton.bones.find(b=>b.name===name)||(mesh.parent.name===name?mesh.parent:null);
  return bone&&names.has(name)?[{bone,property,interpolant:track.createInterpolant()}]:[];
 });
 if(channels.length!==22)throw Error('Expected seven native body channels plus native armature translation');
 // Native pelvis trough is near .40, long after hind contact (.15/.24).
 // Advancing body timing places that trough at early support and its rise /
 // forward travel through the combined hind push (.25..47).
 const phaseLead=.25;
 return {phaseLead,apply(time){
  const phase=((time/clip.duration)%1+1)%1;
  // Align only hind load/push. Return to native motion before fore support;
  // all-cycle retiming overextended the fore chain during its recovery.
  const weight=ease((phase-.06)/.12)*(1-ease((phase-.44)/.18));
  const t=((time+phaseLead*clip.duration)%clip.duration+clip.duration)%clip.duration;
  for(const {bone,property,interpolant} of channels){
   const target=bone[property].clone().fromArray(interpolant.evaluate(t));
   if(property==='quaternion')bone[property].slerp(target,weight);else bone[property].lerp(target,weight);
  }
 }};
}
