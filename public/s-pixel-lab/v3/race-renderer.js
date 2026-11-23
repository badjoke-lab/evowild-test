import {CrowdRenderer} from '../v2/renderer.js';
import {PaintedSurface} from './surface.js';
import {ExactSurface} from './exact.js';
import {TrackFloor} from './track.js';

const clamp=(x,a,b)=>Math.min(b,Math.max(a,x));
function outsideView(x,z,a,b,{right,up,aim,ext,w,h}){
 function beyond(axis,extent){
  const [ax,ay,az]=axis;
  const center=(x-aim[0])*ax+(224-aim[1])*ay+(z-aim[2])*az;
  const radius=Math.abs(a*ax+b*az)*450+Math.abs(ay)*240+Math.abs(-b*ax+a*az)*110;
  return Math.abs(center)>extent+radius;
 }
 return beyond(right,ext*w/h)||beyond(up,ext);
}
export class RaceRenderer extends CrowdRenderer{
 constructor(canvas,meta,atlas,onReady){
  super(canvas,meta,atlas,onReady);
  this.footBits=meta.poses.map(({feet})=>['nearF','farF','nearH','farH'].reduce((n,k,i)=>n|(Number(feet[k].contact)<<i),0));
  this.maxCoverage=this.coverage.samples;this.track=new (this.constructor.Floor || TrackFloor)(this.gl);this.surface=new (this.constructor.Surface || PaintedSurface)(this.gl,meta);
 }
 beginFrame(s,ext,w,h){
  const hero=s.number===1&&s.method!=='exact'&&700*h/(2*ext)>=205;
  const samples=s.method==='stack'?this.maxCoverage:hero?Math.min(s.heroAA??(s.course?0:4),this.maxCoverage):0;
  if(samples<2)return;
  if(this.coverage.samples!==samples){this.coverage.release();this.coverage.samples=samples;}
  this.coverage.begin(w,h);
 }
 drawFloor(s,frame,use){
  if(s.course&&s.originalFloor!==true)this.track.draw(frame,use);
  else super.drawFloor(s,frame,use);
 }
 async loadExact(){
  if(!this.exact)this.exact=new ExactSurface(this.gl,this.meta);
  await this.exact.load();
 }
 drawActors(s,frame,use){
  if(s.method==='stack')return super.drawActors(s,frame,use);
  const {ext,h,aim,eye}=frame,batches=new Map(),far=new Map(),exact=new Map();
  const angularSize=700*h/(2*ext),cameraDistance=ext/Math.tan(Math.PI/8);
  const mix={near:0,mid:0,transition:0,sprite:0,offscreen:0,fine:0,race:0};
  const atlas=this.sprites.index,yaw=s.yaw*Math.PI/180,tilt=s.tilt*Math.PI/180;
  const bank=s.method==='lod'&&angularSize*.8<113?this.sprites.select(s.tilt,this.onReady):-1;
  for(const [pose,places] of frame.groups){
   const feet=this.footBits[pose];
   for(let i=0;i<places.length;i+=4){
    const x=places[i],z=places[i+1],a=places[i+2],b=places[i+3];
    if(s.course&&s.magnification>1&&outsideView(x,z,a,b,frame)){mix.offscreen++;continue;}
    const depth=(x-aim[0])*eye[0]+(214-aim[1])*eye[1]+(z-aim[2])*eye[2];
    const span=angularSize*clamp(cameraDistance/Math.max(50,cameraDistance-depth),.80,1.25);
    if(s.method==='exact'){
     if(!exact.has(pose))exact.set(pose,[]);
     exact.get(pose).push(x,z,a,b);mix.near++;continue;
    }
    const fraction=bank<0?0:clamp((113-span)/10,0,1);
    const card=this.effectiveCoverage?.(fraction) ?? fraction;
    if(card<1){
     const level=s.level||((s.method==='surface'||span>=245)?'fine':span>=148?'race':'mid');
     const direction=s.frontFaces===false?null:this.surface.facing.constructor.direction(yaw+Math.atan2(b,a),tilt);
     const key=pose+'/'+level+'/'+direction;
     if(!batches.has(key))batches.set(key,{pose,level,direction,places:[]});
     batches.get(key).places.push(x,z,a,b,feet,1-card);
     if(card>0)mix.transition++;
     else if(level==='mid')mix.mid++;
     else{mix.near++;mix[level]++;}
    }else mix.sprite++;
    if(card>0){
     const angle=yaw+Math.atan2(b,a),n=atlas.directions;
     const k=(Math.round(angle*n/(2*Math.PI))%n+n)%n;
     const [page,u,v,w,h,dx,dy]=atlas.angles[bank].rects[pose*n+k];
     if(!far.has(page))far.set(page,[]);
     far.get(page).push(x,z,angle,k*Math.PI*2/n,u,v,w,h,dx,dy,card,feet);
    }
   }
  }
  const tick=s.time/this.meta.period*s.samples;
  const drift=s.course&&!s.idle?(tick-Math.floor(tick+1e-6))*this.meta.stride/s.samples:0;
  const triangles=exact.size?this.exact.draw(exact,use,drift):this.surface.draw(batches,use,drift);
  if(far.size)this.sprites.draw(new Map(),far,bank,use,tilt,drift);
  this.mix=mix;this.bank=bank;this.screenSpan=angularSize;
  return triangles+(mix.sprite+mix.transition)*72;
 }
}
