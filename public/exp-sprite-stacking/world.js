import {ovalWorld,OVAL_DISTANCE} from './runtime/oval_course_2p5d.js';
import {projected} from './renderers.js';
const SCALE=.08,TAU=Math.PI*2;
export function coursePoint(distance,lateral=0){const p=ovalWorld(distance,1.5);return {x:p.x*SCALE-p.tz*lateral,z:p.z*SCALE+p.tx*lateral,heading:Math.atan2(p.tx,p.tz),tx:p.tx,tz:p.tz};}
export function createSimulation(count=6){return {time:0,distance:440,phase:0,speed:4,targetRate:1,lateral:0,headingOffset:0,heading:Math.PI/2,player:coursePoint(440),count,rotation:0,keys:new Set()};}
export function stepSimulation(s,dt,settings,stride){s.time+=dt;const key=s.keys,accelerate=key.has('ArrowUp')||key.has('w'),brake=key.has('ArrowDown')||key.has('s'),steer=(key.has('ArrowRight')||key.has('d')?1:0)-(key.has('ArrowLeft')||key.has('a')?1:0);
 if(accelerate||brake)s.targetRate=Math.max(0,Math.min(1.5,s.targetRate+(accelerate?1:-1)*dt*.7));s.speed+=(s.targetRate*4-s.speed)*(1-Math.exp(-dt*3));if(s.targetRate===0&&s.speed<.01)s.speed=0;
 if(settings.auto){s.distance+=s.speed/SCALE*dt;s.lateral=Math.max(-7,Math.min(7,s.lateral+steer*dt*2));s.headingOffset+=(steer*.3-s.headingOffset)*(1-Math.exp(-dt*4));s.player=coursePoint(s.distance,s.lateral);s.heading=s.player.heading+s.headingOffset;}
 else{s.heading+=steer*dt*1.25;s.player.x+=Math.sin(s.heading)*s.speed*dt;s.player.z+=Math.cos(s.heading)*s.speed*dt;s.distance+=s.speed/SCALE*dt;}
 if(settings.animate)s.phase=(s.phase+s.speed/stride*dt)%1;if(settings.rotate)s.rotation=(s.rotation+dt*.42)%TAU;
}
export function entities(s,scene,count){if(scene!=='course')return [{x:0,z:0,heading:s.rotation,phase:s.phase,id:0}];return Array.from({length:count},(_,i)=>i===0?{...s.player,heading:s.heading,phase:s.phase,id:0}:{...coursePoint(s.distance-(Math.floor((i+2)/3))*42,(i%3-1)*2.4),phase:(s.phase+i*.137)%1,id:i});}
function path(ctx,points,c,close=true){ctx.beginPath();for(let i=0;i<points.length;i++){const p=projected(points[i],c);if(i===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);}if(close)ctx.closePath();}
export function floor(ctx,c,scene){ctx.fillStyle=scene==='course'?'#c5cfb6':'#dfe3d6';ctx.fillRect(0,0,c.w,c.h);
 if(scene==='course'){
  // Unmodified existing 1600m oval centerline, uniformly scaled .08 for the lab.
  const outer=[],inner=[];for(let d=0;d<OVAL_DISTANCE;d+=8){outer.push(coursePoint(d,6.3));inner.unshift(coursePoint(d,-6.3));}path(ctx,outer,c);ctx.fillStyle='#b2bda4';ctx.fill();path(ctx,[...outer,...inner],c);ctx.fillStyle='#d9d8c9';ctx.fill('evenodd');
  for(const side of [-6,6]){path(ctx,Array.from({length:201},(_,i)=>({...coursePoint(i*8,side),y:.03})),c);ctx.strokeStyle='#f2f2e6';ctx.lineWidth=2;ctx.stroke();}
  for(const lateral of [-3,0,3]){path(ctx,Array.from({length:201},(_,i)=>coursePoint(i*8,lateral)),c);ctx.strokeStyle='#f8f6ea80';ctx.lineWidth=1;ctx.setLineDash([10,12]);ctx.stroke();ctx.setLineDash([]);}
 }else{const points=[];for(let i=0;i<65;i++){const a=i/64*TAU;points.push({x:Math.cos(a)*2.7,z:Math.sin(a)*2.7});}path(ctx,points,c);ctx.fillStyle='#d0d6c6';ctx.fill();ctx.strokeStyle='#b6c2a9';ctx.lineWidth=1;ctx.stroke();}
 // Ground grid provides a stationary reference for turn/foot-contact review.
 ctx.strokeStyle=scene==='course'?'#78896912':'#82936b17';ctx.lineWidth=.7;const gx=Math.floor(c.x/2)*2,gz=Math.floor(c.z/2)*2;for(let i=-16;i<=16;i++){path(ctx,[{x:gx+i*2,z:gz-32},{x:gx+i*2,z:gz+32}],c,false);ctx.stroke();path(ctx,[{x:gx-32,z:gz+i*2},{x:gx+32,z:gz+i*2}],c,false);ctx.stroke();}
}
export function shadows(ctx,list,c){for(const e of list){const p=projected(e,c);ctx.save();ctx.translate(p.x,p.y);ctx.rotate(Math.atan2(c.se*Math.cos(e.heading-c.az),Math.sin(e.heading-c.az)));ctx.scale(1,c.se);const r=c.scale*1.6,gradient=ctx.createRadialGradient(0,0,0,0,0,r);gradient.addColorStop(0,'#34462842');gradient.addColorStop(1,'#34462800');ctx.fillStyle=gradient;ctx.beginPath();ctx.ellipse(0,0,r,r*.32,0,0,TAU);ctx.fill();ctx.restore();}}
export function rails(ctx,c,front){ctx.lineCap='round';for(let d=0;d<OVAL_DISTANCE;d+=12){for(const side of [-6.6,6.6]){const a=coursePoint(d,side),b=coursePoint(d+12,side),depth=c.sin*((a.x+b.x)/2-c.x)+c.cos*((a.z+b.z)/2-c.z);if((depth>0)!==front)continue;const p=projected(a,c),q=projected({...a,y:.7},c),r=projected({...b,y:.7},c);if(Math.max(p.x,q.x,r.x)<-30||Math.min(p.x,q.x,r.x)>c.w+30)continue;ctx.strokeStyle=front?'#657955':'#879579';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(p.x,p.y);ctx.lineTo(q.x,q.y);ctx.lineTo(r.x,r.y);ctx.stroke();}}}
