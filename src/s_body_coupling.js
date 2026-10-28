// Review-only timing alignment of EXISTING native body animation. No added
// bob, amplitude scaling, force/COM simulation or mesh/rest-pose modification.
export function createBodyCoupling(mesh,clip,{smoothReturn=false}={}){
 const ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*x*(x*(x*6-15)+10);};
 const names=new Set(['root','pelvis','spine','chest','neck','head','tail','EvoWild_S_Armature_V3']);
 const channels=clip.tracks.flatMap(track=>{
  const [name,property]=track.name.split('.');
  const bone=mesh.skeleton.bones.find(b=>b.name===name)||(mesh.parent.name===name?mesh.parent:null);
  // The mixer writes doubles; allocating the default Float32 result here
  // introduced quantization that dominated 10us mesh-velocity measurements.
  return bone&&names.has(name)?[{bone,property,interpolant:track.createInterpolant(smoothReturn?new Float64Array(track.getValueSize()):undefined)}]:[];
 });
 if(channels.length!==22)throw Error('Expected seven native body channels plus native armature translation');
 // Native pelvis trough is near .40, long after hind contact (.15/.24).
 // Advancing body timing places that trough at early support and its rise /
 // forward travel through the combined hind push (.25..47).
 const phaseLead=.25;
 const wrap=t=>((t%clip.duration)+clip.duration)%clip.duration;
 const start=.44,end=.62,span=end-start;
 const sample=(channel,phase)=>Array.from(channel.interpolant.evaluate(wrap(phase*clip.duration)));
 if(smoothReturn)for(const c of channels){
  // Same return duration and native endpoint poses. Match their first AND
  // second derivatives instead of crossfading through interior key corners.
  // Quaternion components use the same hemisphere and are normalized after
  // evaluation; this preserves endpoint angular velocity/acceleration too.
  const h=1e-4;
  const jet=p=>{const v=sample(c,p),l=sample(c,p-h),r=sample(c,p+h);
   if(c.property==='quaternion')for(const q of [l,r])if(q.reduce((s,x,i)=>s+x*v[i],0)<0)q.forEach((x,i)=>q[i]=-x);
   return {v,d:v.map((_,i)=>(r[i]-l[i])/(2*h)),a:v.map((x,i)=>(r[i]-2*x+l[i])/(h*h))};};
  const from=jet(start+phaseLead),to=jet(end);
  if(c.property==='quaternion'&&from.v.reduce((s,x,i)=>s+x*to.v[i],0)<0)for(const a of Object.values(to))a.forEach((v,i)=>a[i]=-v);
  c.returnCoefficients=from.v.map((p,i)=>{
   const delta=to.v[i]-p,v0=from.d[i]*span,v1=to.d[i]*span,a0=from.a[i]*span*span,a1=to.a[i]*span*span;
   return [p,v0,a0/2,10*delta-6*v0-4*v1-1.5*a0+.5*a1,-15*delta+8*v0+7*v1+1.5*a0-a1,6*delta-3*v0-3*v1-.5*a0+.5*a1];
  });
 }
 return {phaseLead,apply(time){
  const phase=((time/clip.duration)%1+1)%1;
  // Align only hind load/push. Return to native motion before fore support;
  // all-cycle retiming overextended the fore chain during its recovery.
  const weight=ease((phase-.06)/.12)*(1-ease((phase-.44)/.18));
  const t=((time+phaseLead*clip.duration)%clip.duration+clip.duration)%clip.duration;
  for(const channel of channels){
   const {bone,property,interpolant}=channel;
   if(smoothReturn){
    // Never use the already modified bone as the native pose. At dt=0 the
    // mixer may skip an unchanged property write; repeated lerp then drifted.
    bone[property].fromArray(interpolant.evaluate(wrap(time)));
    if(phase>start&&phase<end){
     const u=(phase-start)/span;
     bone[property].fromArray(channel.returnCoefficients.map(a=>a.reduceRight((s,c)=>s*u+c,0)));
     if(property==='quaternion')bone[property].normalize();
     continue;
    }
   }
   const target=bone[property].clone().fromArray(interpolant.evaluate(t));
   if(property==='quaternion')bone[property].slerp(target,weight);else bone[property].lerp(target,weight);
  }
 }};
}
