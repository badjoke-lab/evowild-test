// P-only rigid cutouts. Each foot owns a persistent world contact; a supported
// body changes depth only as far as those contacts and fixed bones permit.
const TAU = Math.PI * 2;
const STRIDE = 352;
const DUTY = .30;
const MAX_COMPRESSION = 10;
const LIMBS = [
  {id:'fore-far',kind:'fore',offset:.56,far:true},
  {id:'hind-far',kind:'hind',offset:.06,far:true},
  {id:'hind-near',kind:'hind',offset:0,far:false},
  {id:'fore-near',kind:'fore',offset:.50,far:false}
];
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const mix=(a,b,t)=>a+(b-a)*t;
const smooth=t=>t*t*t*(10+t*(-15+6*t));
const fract=t=>((t%1)+1)%1;
const rotate=(p,a)=>({x:p.x*Math.cos(a)-p.y*Math.sin(a),y:p.x*Math.sin(a)+p.y*Math.cos(a)});
const states=new WeakMap();
let atlas=null;

export async function loadPLayered(base){
  const response=await fetch(`${base}concept/p-layered/atlas.json`);
  if(!response.ok)throw Error(`P layered atlas: ${response.status}`);
  atlas=await response.json();
  await Promise.all(Object.values(atlas.parts).map(async p=>{
    const image=new Image();image.src=`${base}concept/p-layered/${p.image}`;
    await image.decode();p.bitmap=image;
    // Bake depth shading once. Applying a Canvas filter to large source
    // cutouts for every limb every frame stalled the software CI renderer.
    const far=document.createElement('canvas');far.width=image.width;far.height=image.height;
    const context=far.getContext('2d');context.filter='brightness(0.78)';context.drawImage(image,0,0);
    p.bitmapFar=far;
  }));
  return atlas;
}
export const pLayeredReady=()=>Boolean(atlas&&Object.values(atlas.parts).every(p=>p.bitmap));

// The opt-in P simulation uses the last contact corridor too, so the actual
// racer and its visible body step sideways together instead of diverging.
export function constrainPLayeredLane(r,proposed,distance,time){
  const view=states.get(r)?.view;
  if(!view)return proposed;
  const depthBias=r.depthBias||0,lane=clamp(proposed+depthBias,0,3);
  // Advance contacts at the simulation step, before the next render. A stale
  // previous-frame corridor cannot constrain a fast lane change correctly.
  const pose=drawPLayered(null,r,{...view,x:view.projectX(distance),lane,distance,time,
    width:view.widthForLane?view.widthForLane(lane):view.width});
  return clamp(pose.renderLane-depthBias,0,3);
}

function joint(kind,bob,pitch){
  const p=atlas.parts.body[kind==='fore'?'shoulder':'hip'];
  const scale=atlas.body.width/atlas.parts.body.crop[2];
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

function segment(ctx,part,a,b,length,far=false){
  const sx=part.b[0]-part.a[0],sy=part.b[1]-part.a[1];
  const scale=length/Math.hypot(sx,sy);
  ctx.save();ctx.translate(a.x,a.y);
  ctx.rotate(Math.atan2(b.y-a.y,b.x-a.x)-Math.atan2(sy,sx));ctx.scale(scale,scale);
  ctx.drawImage(far?part.bitmapFar:part.bitmap,-part.a[0],-part.a[1]);ctx.restore();
}

function foot(ctx,part,point,angle,far=false){
  const scale=part.width/part.crop[2];
  ctx.save();ctx.translate(point.x,point.y);ctx.rotate(angle);ctx.scale(scale,scale);
  ctx.drawImage(far?part.bitmapFar:part.bitmap,-part.sole[0],-part.sole[1]);ctx.restore();
}

function jointCover(ctx,part,c){
  if(!part)return;
  const angle=Math.atan2(c.ankle.y-c.j.y,c.ankle.x-c.j.x)-Math.PI/2;
  const scale=part.width/part.crop[2];
  ctx.save();ctx.translate(c.knee.x,c.knee.y);ctx.rotate(angle);ctx.scale(scale,scale);
  ctx.drawImage(c.limb.far?part.bitmapFar:part.bitmap,-part.center[0],-part.center[1]);ctx.restore();
}

function laneForY(groundY,distance,value){
  let low=0,high=3;
  for(let i=0;i<24;i++){
    const middle=(low+high)/2;
    if(groundY(distance,middle)<value)low=middle;else high=middle;
  }
  return (low+high)/2;
}

export function drawPLayered(ctx,r,view){
  if(!pLayeredReady())return null;
  const {x,width,ppm,projectX,groundY,lane,time,reviewPhase,neutral=false,debug=false}=view;
  const rootDistance=view.distance??r.distance;
  const scale=width/416,metresPerUnit=scale/ppm;
  let state=states.get(r);
  if(!state||rootDistance<state.distance||time<state.time){
    state={distance:rootDistance,time,cycle:r.phaseOffset/6,feet:new Map(),renderLane:lane};
    states.set(r,state);
  }
  const dt=Math.max(0,(time-state.time)/1000);
  const travel=Math.max(0,rootDistance-state.distance)/metresPerUnit;
  state.cycle+=travel/STRIDE;state.distance=rootDistance;state.time=time;
  state.view=view;
  const cycle=reviewPhase??state.cycle,phase=fract(cycle);
  // Hind and fore pairs load in turn, separated by actual suspension windows.
  const half=fract(phase+.06)*2%1,supportPart=(DUTY+.06)*2;
  const flight=!neutral&&half>supportPart;
  const bob=neutral?0:half<=supportPart
    ? 8*Math.sin(Math.PI*half/supportPart)**2
    : -14*Math.sin(Math.PI*(half-supportPart)/(1-supportPart))**2;
  const pitch=neutral?0:.030*Math.sin(TAU*(phase-.12));
  const previousLane=state.renderLane;
  let renderLane=reviewPhase!==undefined?lane
    : previousLane+clamp(lane-previousLane,-2.8*dt,2.8*dt);

  // Existing planted contacts define a feasible body-depth interval. This is
  // a constraint on the moving body, never an adjustment of a planted foot.
  let lower=-Infinity,upper=Infinity;
  for(const limb of LIMBS){
    const local=fract(cycle+limb.offset),f=state.feet.get(limb.id);
    if(neutral||reviewPhase!==undefined||!f?.stance||local>=DUTY||Math.floor(cycle+limb.offset)!==f.cycleId)continue;
    const j=joint(limb.kind,bob,pitch),part=atlas.parts[`${limb.kind}-foot`];
    const angle=Math.atan2(groundY(f.worldX+.05,f.lane)-groundY(f.worldX-.05,f.lane),.1*ppm);
    const fs=part.width/part.crop[2];
    const off=rotate({x:(part.ankle[0]-part.sole[0])*fs,y:(part.ankle[1]-part.sole[1])*fs},angle);
    const ankleX=projectX(f.worldX)+off.x*scale;
    const ankleY=groundY(f.worldX,f.lane)+off.y*scale;
    const dx=(ankleX-x)/scale+208-j.x;
    const lengths=atlas.bones?.[limb.kind]??[70,68];
    const reach=lengths[0]+lengths[1]-3;
    const vertical=Math.sqrt(Math.max(0,reach*reach-dx*dx));
    lower=Math.max(lower,ankleY-(vertical+j.y-296+MAX_COMPRESSION)*scale);
    // A supported hip stays above its ankle, rather than folding below it.
    upper=Math.min(upper,ankleY-(45+j.y-296)*scale);
  }
  const requestedY=groundY(rootDistance,renderLane);
  const constrainedY=lower<=upper?clamp(requestedY,lower,upper):requestedY;
  state.laneBounds=lower<=upper?[
    Number.isFinite(lower)?laneForY(groundY,rootDistance,lower):0,
    Number.isFinite(upper)?laneForY(groundY,rootDistance,upper):3
  ]:null;
  if(Number.isFinite(constrainedY)&&constrainedY!==requestedY)renderLane=laneForY(groundY,rootDistance,constrainedY);
  if(neutral||reviewPhase!==undefined)renderLane=lane;
  state.renderLane=renderLane;
  const y=groundY(rootDistance,renderLane);
  const commands=[],feet=[];

  for(const limb of LIMBS){
    const local=neutral?(limb.kind==='fore'?.12:.20)+(limb.far?.02:0):fract(cycle+limb.offset);
    const stance=local<DUTY,cycleId=Math.floor(cycle+limb.offset);
    const j=joint(limb.kind,bob,pitch),rest=joint(limb.kind,0,0);
    const footLane=clamp(renderLane+(limb.far?-.015:.015),0,3);
    const lead=STRIDE*DUTY*.5;
    let f=state.feet.get(limb.id);
    if(!f||reviewPhase!==undefined){
      f={stance,cycleId,contactId:0,worldX:rootDistance+(rest.x-208+lead-local*STRIDE)*metresPerUnit,lane:footLane};
      if(!stance){
        f.liftX=rootDistance+(rest.x-208-lead-(local-DUTY)*STRIDE)*metresPerUnit;
        f.liftTargetLane=footLane;
      }
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
      const lateralRecovery=smooth(clamp(u/.30,0,1));
      worldLane=footLane+((f.liftLane??f.lane)-(f.liftTargetLane??footLane))*(1-lateralRecovery);
      lift=(limb.kind==='fore'?64:62)*Math.sin(Math.PI*u);
      angle=-.20*Math.sin(Math.PI*u);
    }
    f.stance=stance;
    const screen={x:projectX(worldX),y:groundY(worldX,worldLane)-lift*scale};
    if(stance)angle=Math.atan2(groundY(worldX+.05,worldLane)-groundY(worldX-.05,worldLane),.1*ppm);
    const contact={x:(screen.x-x)/scale+208,y:(screen.y-y)/scale+296};
    const part=atlas.parts[`${limb.kind}-foot`],fs=part.width/part.crop[2];
    const off=rotate({x:(part.ankle[0]-part.sole[0])*fs,y:(part.ankle[1]-part.sole[1])*fs},angle);
    const ankle={x:contact.x+off.x,y:contact.y+off.y};
    const lengths=atlas.bones?.[limb.kind]??[70,68];
    let recoveryLiftAdjustment=0;
    if(!stance){
      // A free foot is lifted into a reachable recovery arc. This plans the
      // ankle target before IK; it neither clips a bone nor moves a contact.
      const reach=lengths[0]+lengths[1]-8,dx=ankle.x-j.x;
      const lowest=j.y+Math.sqrt(Math.max(0,reach*reach-dx*dx));
      recoveryLiftAdjustment=Math.max(0,ankle.y-lowest);
      ankle.y-=recoveryLiftAdjustment;contact.y-=recoveryLiftAdjustment;
      screen.y-=recoveryLiftAdjustment*scale;lift+=recoveryLiftAdjustment;
    }
    commands.push({limb,j,ankle,contact,angle,lengths,part});
    feet.push({id:limb.id,stance,phase:local,contactId:f.contactId,worldX,worldLane,
      screenX:screen.x,screenY:screen.y,lift,angle,ankle,recoveryLiftAdjustment});
  }
  const required=Math.max(0,...commands.filter(c=>feet.find(f=>f.id===c.limb.id).stance).map(c=>{
    const reach=c.lengths[0]+c.lengths[1]-3,dx=c.ankle.x-c.j.x;
    return c.ankle.y-c.j.y-Math.sqrt(Math.max(0,reach*reach-dx*dx));
  }));
  const bodyOffset=Math.max(required,(state.bodyOffset??required)*Math.exp(-dt*28));
  state.bodyOffset=bodyOffset;
  for(const c of commands){
    c.j.y+=bodyOffset;
    const ik=solve(c.j,c.ankle,...c.lengths,c.limb.kind==='fore'?1:-1);c.knee=ik.knee;
    const boneLengthError=Math.max(
      Math.abs(Math.hypot(c.j.x-c.knee.x,c.j.y-c.knee.y)-c.lengths[0]),
      Math.abs(Math.hypot(c.ankle.x-c.knee.x,c.ankle.y-c.knee.y)-c.lengths[1]));
    Object.assign(feet.find(f=>f.id===c.limb.id),{reachError:ik.reachError,boneLengthError,hip:c.j,knee:c.knee});
  }

  const drawBody=target=>{
    target.save();target.translate(208,170+bob+bodyOffset);target.rotate(pitch);target.translate(-208,-170);
    const p=atlas.parts.body;
    target.drawImage(p.bitmap,atlas.body.x,atlas.body.y,atlas.body.width,atlas.body.width*p.crop[3]/p.crop[2]);target.restore();
  };
  const drawLimb=(target,c)=>{
    target.save();
    segment(target,atlas.parts[`${c.limb.kind}-upper`],c.j,c.knee,c.lengths[0],c.limb.far);
    segment(target,atlas.parts[`${c.limb.kind}-lower`],c.knee,c.ankle,c.lengths[1],c.limb.far);
    jointCover(target,atlas.parts[`${c.limb.kind}-joint`],c);
    foot(target,c.part,c.contact,c.angle,c.limb.far);target.restore();
  };
  const paint=target=>{
    target.save();target.translate(x,y);target.scale(scale,scale);target.translate(-208,-296);
    commands.filter(c=>c.limb.far).forEach(c=>drawLimb(target,c));drawBody(target);
    commands.filter(c=>!c.limb.far).forEach(c=>{
      drawLimb(target,c);
      target.save();target.beginPath();target.arc(c.j.x,c.j.y,c.limb.kind==='fore'?29:26,0,TAU);target.clip();drawBody(target);target.restore();
    });
    if(debug)for(const f of feet){
      target.strokeStyle=f.stance?'#26ffaf':'#ffc45a';target.lineWidth=1.5;
      target.beginPath();target.moveTo(f.hip.x,f.hip.y);target.lineTo(f.knee.x,f.knee.y);target.lineTo(f.ankle.x,f.ankle.y);target.stroke();
    }
    target.restore();
  };
  if(ctx)paint(ctx);
  return {phase,cycle:state.cycle,bob,pitch,bodyOffset,feet,scale,commands,paint,flight,
    renderLane,laneLag:lane-renderLane,rootY:y,bodySink:bob+bodyOffset,requestedLane:lane,
    paintFoot:(target,id)=>{
      const c=commands.find(c=>c.limb.id===id);
      target.save();target.translate(x,y);target.scale(scale,scale);target.translate(-208,-296);
      foot(target,c.part,c.contact,c.angle,c.limb.far);target.restore();
    }};
}
