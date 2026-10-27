import {Vector3,Quaternion} from 'three';
const axis=new Vector3(1,0,0);
const ease=x=>{x=Math.max(0,Math.min(1,x));return x*x*x*(x*(x*6-15)+10);};
const rotated=(p,a)=>p.clone().applyAxisAngle(axis,a);
// Piecewise lower envelope of the EXISTING distal vertices. Rotation is zero
// velocity at each vertex change, avoiding an impulse on a polygonal sole.
export function createToeRoll(surface,base,maxDegrees,{continuous=false}={}){
 const points=surface.bindWorldPoints.map(p=>new Vector3(...p).sub(base));
 let index=points.reduce((best,p,i)=>p.y<points[best].y?i:best,0),angle=0,translation=new Vector3();
 const max=maxDegrees*Math.PI/180,segments=[],flatEnd=surface.hind?.45:.25;
 while(angle<max-1e-10){
  let end=max,next=index;
  points.forEach((p,j)=>{const dy=p.y-points[index].y,dz=p.z-points[index].z;if(dz<=1e-10)return;const crossing=Math.atan2(dy,dz);if(crossing>angle+1e-9&&crossing<end){end=crossing;next=j;}});
  segments.push({a:angle,b:end,index,start:translation.clone()});
  translation.add(rotated(points[index],angle)).sub(rotated(points[index],end));angle=end;index=next;
 }
 // Duration proportional to sqrt(angle span) distributes angular acceleration
 // across short and long mesh facets without changing any regression tolerance.
 const weights=segments.map(s=>Math.sqrt(s.b-s.a)),total=weights.reduce((a,b)=>a+b,0);let phase=0;
 segments.forEach((s,i)=>{s.from=phase;phase+=weights[i]/total;s.to=phase;});
 // Continuous roll keeps the same polygonal support vertices and horizontal
 // no-slip path. A compact C2 upper envelope rounds only the vertical corner
 // (sub-mm clearance, explicitly measured), instead of stopping rotation.
 const inverseEase=y=>{let lo=0,hi=1;for(let i=0;i<50;i++){const m=(lo+hi)/2;if(ease(m)<y)lo=m;else hi=m;}return (lo+hi)/2;};
 if(continuous)segments.forEach(s=>{s.from=inverseEase(s.a/max);s.to=inverseEase(s.b/max);});
 function roundedMax(a,b,width){if(width<1e-12)return Math.max(a,b);const t=Math.abs(a-b)/width;if(t>=1)return Math.max(a,b);return (a+b+width*(3/8+3/4*t*t-1/8*t**4))/2;}
 function at(q){
  q=Math.max(0,Math.min(1,q));const s=segments.find(s=>q<=s.to+1e-12)||segments.at(-1);
  const angle=continuous?max*ease(q):s.a+(s.b-s.a)*ease((q-s.from)/(s.to-s.from));
  const translation=s.start.clone().add(rotated(points[s.index],s.a)).sub(rotated(points[s.index],angle));
  if(continuous){
   const heights=segments.map(segment=>-rotated(points[segment.index],angle).y);
   // Grow the rounding width before the FIRST real vertex transition. Scaling
   // the final correction across a transition would leave its velocity kink.
   const width=.003*ease(angle/(segments[0].b*.5));
   const rounded=heights.reduce((a,b)=>roundedMax(a,b,width)),exact=Math.max(...heights);
   translation.y+=rounded-exact;
  }
  return {angle,rotation:new Quaternion().setFromAxisAngle(axis,angle),translation,pivotId:surface.ids[s.index],pivotOffset:points[s.index]};
 }
 return {surface,maxDegrees,flatEnd,segments:segments.map(s=>({from:s.from,to:s.to,startDegrees:s.a*180/Math.PI,endDegrees:s.b*180/Math.PI,pivotId:surface.ids[s.index]})),pose(phase,stance){
  if(phase>1-1e-9)phase=0;
  // A broad initial support interval precedes late-stance roll. After lift the
  // same pitch path returns continuously to the unchanged recovery orientation.
  const u=(phase-stance)/(1-stance);
  const q=phase<stance?Math.max(0,(phase/stance-flatEnd)/(1-flatEnd)):1-ease(u/.30);
  return {...at(q),mode:phase<stance?(q>1e-10?'TOE_SUPPORT':'FLAT_SUPPORT'):'SWING'};
 }};
}
