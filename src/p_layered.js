// P-only 2D cutout rig. Feet have persistent identities and planted world
// anchors. The body can advance while a support foot stays on the terrain.
const TAU=Math.PI*2;
const STRIDE=384; // Rig-space travel per cycle; selected to fit the rigid bones.
const DUTY=.42;
const LIMBS=[
  {id:'fore-far',kind:'fore',offset:.10,far:true},
  {id:'hind-far',kind:'hind',offset:.60,far:true},
  {id:'hind-near',kind:'hind',offset:.50,far:false},
  {id:'fore-near',kind:'fore',offset:0,far:false}
];
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const mix=(a,b,t)=>a+(b-a)*t;
const smooth=t=>t*t*t*(10+t*(-15+6*t));
const rotate=(p,a)=>({x:p.x*Math.cos(a)-p.y*Math.sin(a),y:p.x*Math.sin(a)+p.y*Math.cos(a)});
const states=new WeakMap();
let atlas=null;

export async function loadPLayered(base){
  const response=await fetch(`${base}concept/p-layered/atlas.json`);
  if(!response.ok)throw Error(`P layered atlas: ${response.status}`);
  atlas=await response.json();
  await Promise.all(Object.values(atlas.parts).map(async p=>{const im=new Image();im.src=`${base}concept/p-layered/${p.image}`;await im.decode();p.bitmap=im;}));
  return atlas;
}
export const pLayeredReady=()=>Boolean(atlas&&Object.values(atlas.parts).every(p=>p.bitmap));

function joint(kind,bob,pitch){
  const p=atlas.parts.body[kind==='fore'?'shoulder':'hip'],scale=atlas.body.width/atlas.parts.body.crop[2];
  const v=rotate({x:atlas.body.x+p[0]*scale-208,y:atlas.body.y+p[1]*scale-170},pitch);
  return {x:v.x+208,y:v.y+170+bob};
}

function solve(a,b,l1,l2,bend){
  const dx=b.x-a.x,dy=b.y-a.y,d=Math.hypot(dx,dy);
  const reachError=Math.max(0,d-l1-l2,Math.abs(l1-l2)-d);
  const distance=clamp(d,Math.abs(l1-l2)+.001,l1+l2-.001);
  const along=(l1*l1-l2*l2+distance*distance)/(2*distance);
  const h=Math.sqrt(Math.max(0,l1*l1-along*along));
  const ux=dx/Math.max(d,.001),uy=dy/Math.max(d,.001);
  return {knee:{x:a.x+ux*along-uy*h*bend,y:a.y+uy*along+ux*h*bend},reachError};
}

function segment(ctx,part,a,b,length){
  const sx=part.b[0]-part.a[0],sy=part.b[1]-part.a[1],scale=length/Math.hypot(sx,sy);
  ctx.save();ctx.translate(a.x,a.y);ctx.rotate(Math.atan2(b.y-a.y,b.x-a.x)-Math.atan2(sy,sx));ctx.scale(scale,scale);
  ctx.drawImage(part.bitmap,-part.a[0],-part.a[1]);ctx.restore();
}

function foot(ctx,part,point,angle){
  const scale=part.width/part.crop[2];
  ctx.save();ctx.translate(point.x,point.y);ctx.rotate(angle);ctx.scale(scale,scale);
  ctx.drawImage(part.bitmap,-part.sole[0],-part.sole[1]);ctx.restore();
}

// Pure projection inputs let the evidence harness use the exact same painter
// for transparent phase exports and isolated per-foot raster measurements.
export function drawPLayered(ctx,r,view){
  if(!pLayeredReady())return null;
  const {x,y,width,ppm,projectX,groundY,lane,time,reviewPhase,neutral=false,debug=false}=view;
  const rootDistance=view.distance??r.distance;
  const scale=width/416,metresPerUnit=scale/ppm;
  let state=states.get(r);
  if(!state||rootDistance<state.distance||time<state.time){
    state={distance:rootDistance,time,cycle:r.phaseOffset/6,feet:new Map()};states.set(r,state);
  }
  const dt=Math.max(0,(time-state.time)/1000);
  const travel=Math.max(0,rootDistance-state.distance)/metresPerUnit;
  state.cycle+=travel/STRIDE;state.distance=rootDistance;state.time=time;
  const cycle=reviewPhase??state.cycle,phase=((cycle%1)+1)%1;
  const bob=neutral?0:5*Math.cos(TAU*(phase-.10)),pitch=neutral?0:.018*Math.sin(TAU*(phase+.10));
  const commands=[],feet=[];
  for(const limb of LIMBS){
    const local=neutral?(limb.kind==='fore'?.16:.28)+(limb.far?.03:0):((cycle+limb.offset)%1+1)%1,stance=local<DUTY;
    const j=joint(limb.kind,bob,pitch);
    // Far limbs have separate contacts and a modest depth offset; their bones
    // keep the same morphology. Terrain contact includes their actual lane.
    const footLane=clamp(lane+(limb.far?-.065:.025),0,3);
    const rest=joint(limb.kind,0,0),lead=STRIDE*DUTY*.5;
    let f=state.feet.get(limb.id);
    const cycleId=Math.floor(cycle+limb.offset);
    if(!f||reviewPhase!==undefined){
      f={stance,cycleId,contactId:0,worldX:rootDistance+(rest.x-208+lead-local*STRIDE)*metresPerUnit,lane:footLane};
      if(!stance){f.liftX=rootDistance+(rest.x-208-lead-(local-DUTY)*STRIDE)*metresPerUnit;f.liftTargetLane=footLane;}
      state.feet.set(limb.id,f);
    }
    if(stance&&(!f.stance||cycleId!==f.cycleId)){
      f.worldX=rootDistance+(rest.x-208+lead-local*STRIDE)*metresPerUnit;
      f.lane=footLane;f.contactId++;f.cycleId=cycleId;
    }
    if(!stance&&f.stance){f.liftX=f.worldX;f.liftLane=f.lane;f.liftTargetLane=footLane;}
    let worldX=f.worldX,worldLane=f.lane,lift=0,angle=0;
    if(!stance){
      const u=(local-DUTY)/(1-DUTY),ease=smooth(u);
      const landing=rootDistance+(rest.x-208+lead+(1-u)*STRIDE*(1-DUTY))*metresPerUnit;
      worldX=mix(f.liftX??landing-STRIDE*metresPerUnit,landing,ease);
      // A free foot follows subsequent body depth movement. Only the offset
      // present at lift-off is recovered gradually; planted feet stay fixed.
      worldLane=footLane+((f.liftLane??f.lane)-(f.liftTargetLane??footLane))*(1-ease);
      // Leave the planted endpoint smoothly, but clear the ground before the
      // advancing hip can pull the rigid chain beyond its reach.
      lift=(limb.kind==='fore'?48:46)*Math.sin(Math.PI*u)**1.25;
      angle=-.15*Math.sin(Math.PI*u); // Low clawed foot, never a curled wrist.
    }
    f.stance=stance;
    const screen={x:projectX(worldX),y:groundY(worldX,worldLane)-lift*scale};
    const tangent=Math.atan2(groundY(worldX+.05,worldLane)-groundY(worldX-.05,worldLane),.1*ppm);
    if(stance)angle=tangent;
    const contact={x:(screen.x-x)/scale+208,y:(screen.y-y)/scale+296};
    const part=atlas.parts[`${limb.kind}-foot`],fs=part.width/part.crop[2];
    const ankleOffset=rotate({x:(part.ankle[0]-part.sole[0])*fs,y:(part.ankle[1]-part.sole[1])*fs},angle);
    const ankle={x:contact.x+ankleOffset.x,y:contact.y+ankleOffset.y};
    // Balanced rigid segments can fold without an unreachable inner radius.
    // They are calibrated once, never stretched per animation frame.
    const lengths=limb.kind==='fore'?[91,91]:[89,89];
    commands.push({limb,j,ankle,contact,angle,lengths,part});
    feet.push({id:limb.id,stance,phase:local,contactId:f.contactId,worldX,worldLane,screenX:screen.x,screenY:screen.y,lift,angle,ankle});
  }
  // Pelvis/chest follow the planted feet during depth changes. Adjusting the
  // body height keeps fixed-length bones in reach; the feet are never dragged
  // toward the advancing root to disguise an unreachable target.
  const required=Math.max(0,...commands.map(c=>{
    const reach=c.lengths[0]+c.lengths[1]-3,dx=c.ankle.x-c.j.x;
    return c.ankle.y-c.j.y-Math.sqrt(Math.max(0,reach*reach-dx*dx));
  }));
  const bodyOffset=Math.max(required,(state.bodyOffset??required)*Math.exp(-dt*22));
  state.bodyOffset=bodyOffset;
  for(const c of commands){
    c.j.y+=bodyOffset;
    const ik=solve(c.j,c.ankle,...c.lengths,c.limb.kind==='fore'?1:-1);c.knee=ik.knee;
    const boneLengthError=Math.max(
      Math.abs(Math.hypot(c.j.x-c.knee.x,c.j.y-c.knee.y)-c.lengths[0]),
      Math.abs(Math.hypot(c.ankle.x-c.knee.x,c.ankle.y-c.knee.y)-c.lengths[1]));
    Object.assign(feet.find(f=>f.id===c.limb.id),{reachError:ik.reachError,boneLengthError,hip:c.j,knee:ik.knee});
  }
  const drawBody=()=>{ctx.save();ctx.translate(208,170+bob+bodyOffset);ctx.rotate(pitch);ctx.translate(-208,-170);const p=atlas.parts.body;ctx.drawImage(p.bitmap,atlas.body.x,atlas.body.y,atlas.body.width,atlas.body.width*p.crop[3]/p.crop[2]);ctx.restore();};
  const drawLimb=c=>{
    ctx.save();if(c.limb.far)ctx.filter='brightness(0.78)';
    segment(ctx,atlas.parts[`${c.limb.kind}-upper`],c.j,c.knee,c.lengths[0]);
    segment(ctx,atlas.parts[`${c.limb.kind}-lower`],c.knee,c.ankle,c.lengths[1]);
    foot(ctx,c.part,c.contact,c.angle);ctx.restore();
  };
  ctx.save();ctx.translate(x,y);ctx.scale(scale,scale);ctx.translate(-208,-296);
  commands.filter(c=>c.limb.far).forEach(drawLimb);drawBody();
  commands.filter(c=>!c.limb.far).forEach(c=>{
    drawLimb(c);
    // Original torso pixels cover the proximal cutout joint, without stretch.
    ctx.save();ctx.beginPath();ctx.arc(c.j.x,c.j.y,c.limb.kind==='fore'?24:23,0,TAU);ctx.clip();drawBody();ctx.restore();
  });
  if(debug){for(const f of feet){ctx.strokeStyle=f.stance?'#26ffaf':'#ffc45a';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(f.hip.x,f.hip.y);ctx.lineTo(f.knee.x,f.knee.y);ctx.lineTo(f.ankle.x,f.ankle.y);ctx.stroke();}}
  ctx.restore();
  // The footprint masks use the same image, transform and sole origin as the
  // actual visible foot. They permit pixel measurement independent of anchors.
  return {phase,cycle:state.cycle,bob,pitch,bodyOffset,feet,scale,commands,paintFoot:(target,id)=>{const c=commands.find(c=>c.limb.id===id);target.save();target.translate(x,y);target.scale(scale,scale);target.translate(-208,-296);foot(target,c.part,c.contact,c.angle);target.restore();}};
}
