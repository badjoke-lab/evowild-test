import {
  OVAL_DISTANCE,OVAL_RADIUS,ovalWorld,ovalChaseCamera,
  projectOval,projectOvalRunner,ovalMinimapPoint,ovalSegmentAt
} from "./oval_course_2p5d.js";

const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
const quarter=(ctx,pts,fill,stroke)=>{
  if(pts.some(p=>!p))return;
  ctx.beginPath();
  ctx.moveTo(pts[0].x,pts[0].y);
  for(let i=1;i<pts.length;i++)ctx.lineTo(pts[i].x,pts[i].y);
  ctx.closePath();
  if(fill){ctx.fillStyle=fill;ctx.fill();}
  if(stroke){ctx.strokeStyle=stroke;ctx.stroke();}
};
function skyAndMountains(ctx,w,h,time){
  const sky=ctx.createLinearGradient(0,0,0,h*.75);
  sky.addColorStop(0,"#90c0ec");sky.addColorStop(.54,"#c6dcf1");sky.addColorStop(1,"#e5e1c9");
  ctx.fillStyle=sky;ctx.fillRect(0,0,w,h);
  for(const [range,color,phase] of [[.34,"#98aec1",.21],[.27,"#658797",.53],[.18,"#5b806b",.72]]){
    ctx.fillStyle=color;ctx.beginPath();ctx.moveTo(0,h*.53);
    for(let x=0;x<=w+20;x+=18){
      const y=h*(.40+range*.1)-h*range*Math.pow(Math.abs(Math.sin(x*.0023+phase*7)),5)
        -h*.045*Math.abs(Math.sin(x*.014+phase*11));
      ctx.lineTo(x,y);
    }
    ctx.lineTo(w,h*.58);ctx.closePath();ctx.fill();
  }
  ctx.fillStyle="#638563";ctx.fillRect(0,h*.49,w,h*.51);
  ctx.fillStyle="rgba(221,231,207,.36)";
  for(let i=0;i<8;i++){
    const cx=(w/8)*(i+.5);
    const cy=h*(.49+((i%3)*.026));
    ctx.beginPath();ctx.ellipse(cx,cy,w*.085,5+i%4*2,0,0,Math.PI*2);ctx.fill();
  }
}
function grandstands(ctx,camera,w,h) {
  // Physical grandstands run alongside both straights, not a fictional country/map.
  // These primitives provide a size/perspective guide; detail art remains provisional.
  const bounds=[[-200,-20,-OVAL_RADIUS-34],[20,230,-OVAL_RADIUS-34],
                [-230,-20,OVAL_RADIUS+35],[20,195,OVAL_RADIUS+35]];
  for(const [x0,x1,z] of bounds){
    const p=(x,e)=>projectOval(camera,{x,z},w,h,e);
    const low0=p(x0,0),low1=p(x1,0),high0=p(x0,19),high1=p(x1,19);
    if(!low0||!low1||!high0||!high1)continue;
    const largest=Math.max(Math.abs(low0.x),Math.abs(low1.x),Math.abs(high0.x),Math.abs(high1.x));
    if(largest>w*6)continue;
    quarter(ctx,[low0,low1,high1,high0],"#203e53","#83939f");
    const roof0=p(x0,24),roof1=p(x1,24);
    quarter(ctx,[high0,high1,roof1,roof0],"#142b41");
    for(let i=1;i<=4;i++){
      const e=i*4;
      const q0=p(x0,e),q1=p(x1,e);
      if(!q0||!q1)continue;
      ctx.strokeStyle=i%2?"#587389":"#a4b4ad";ctx.lineWidth=Math.max(1,3*q0.scale/30);
      ctx.beginPath();ctx.moveTo(q0.x,q0.y);ctx.lineTo(q1.x,q1.y);ctx.stroke();
    }
    for(let i=0;i<=8;i++){
      const x=x0+(x1-x0)*i/8;
      const g=p(x,0),roof=p(x,24);
      if(!g||!roof)continue;
      ctx.strokeStyle="#b6c9c9";ctx.lineWidth=Math.max(1,g.scale*.15);
      ctx.beginPath();ctx.moveTo(g.x,g.y);ctx.lineTo(roof.x,roof.y);ctx.stroke();
    }
  }
}
function trackSection(ctx,camera,w,h,m1,m2,fill){
  const a=projectOvalRunner(camera,m1,-.95,w,h);
  const b=projectOvalRunner(camera,m1,3.95,w,h);
  const c=projectOvalRunner(camera,m2,3.95,w,h);
  const d=projectOvalRunner(camera,m2,-.95,w,h);
  quarter(ctx,[a,b,c,d],fill);
}
function drawOvalTrack(ctx,camera,w,h,m){
  // Far-to-near ground quads follow exact oval geometry and take the actual
  // sim distance/lane as input; no disconnected decorative perspective lane.
  const start=m-65,end=m+300,step=5;
  for(let pos=end;pos>start;pos-=step){
    const rear=Math.max(start,pos-step);
    trackSection(ctx,camera,w,h,rear,pos,
      Math.floor(pos/20)%2===0?"#987452":"#a37a56");
  }
  // Continuous lane lines and white rail boundaries.
  for(const lane of [-.95,.05,1.05,2.05,3.05,3.95]){
    const isRail=lane<0 || lane>3.5;
    ctx.lineWidth=isRail?2.5:1;
    ctx.strokeStyle=isRail?"rgba(245,249,248,.93)":"rgba(236,217,179,.24)";
    ctx.beginPath();let active=false;
    for(let m2=start;m2<=end;m2+=3.5){
      const p=projectOvalRunner(camera,m2,lane,w,h);
      if(!p||p.x<-w*2||p.x>w*3){active=false;continue;}
      if(!active)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);
      active=true;
    }
    ctx.stroke();
  }
  for(let p=Math.ceil(start/16)*16;p<end;p+=16){
    for(const lane of [-.95,3.95]){
      const base=projectOvalRunner(camera,p,lane,w,h);
      if(!base||base.x< -30||base.x>w+30||base.y < h*.15||base.y >h*1.25)continue;
      const high=projectOval(camera,ovalWorld(p,lane),w,h,2.4);
      if(!high)continue;
      ctx.lineWidth=Math.max(1,Math.min(4,base.scale*.12));
      ctx.strokeStyle="#f0f6f3";
      ctx.beginPath();ctx.moveTo(base.x,base.y);ctx.lineTo(high.x,high.y);ctx.stroke();
    }
  }
  // Start/finish marker is a genuine world coordinate (m=0/1600).
  // Only displayed as a track stripe when in the local visible interval.
  for(const finish of [0,OVAL_DISTANCE]){
    if(finish<start || finish>end)continue;
    const near=projectOvalRunner(camera,finish,-.95,w,h);
    const far=projectOvalRunner(camera,finish,3.95,w,h);
    if(!near||!far)continue;
    ctx.strokeStyle="#f7f7ec";ctx.lineWidth=7;
    ctx.beginPath();ctx.moveTo(near.x,near.y);ctx.lineTo(far.x,far.y);ctx.stroke();
    ctx.strokeStyle="#242f3d";ctx.lineWidth=2;
    ctx.setLineDash([8,8]);ctx.stroke();ctx.setLineDash([]);
  }
}
function drawOvalMinimap(ctx,w,h,racers,focus){
  const boxW=clamp(w*.18,116,195),boxH=clamp(h*.20,81,124);
  const x=w-boxW-16,y=h-boxH-113;
  ctx.save();ctx.fillStyle="rgba(7,18,33,.85)";
  ctx.strokeStyle="#72a6b8";ctx.lineWidth=1;
  ctx.beginPath();ctx.roundRect(x-9,y-10,boxW+18,boxH+20,10);ctx.fill();ctx.stroke();
  ctx.beginPath();
  for(let m=0;m<=OVAL_DISTANCE;m+=8){
    const p=ovalMinimapPoint(m,x+5,y+7,boxW-10,boxH-14);
    if(m===0)ctx.moveTo(p.x,p.y);else ctx.lineTo(p.x,p.y);
  }
  ctx.closePath();ctx.strokeStyle="#cfb79b";ctx.lineWidth=5;ctx.stroke();
  for(const r of racers){
    const p=ovalMinimapPoint(r.distance,x+5,y+7,boxW-10,boxH-14);
    ctx.beginPath();ctx.arc(p.x,p.y,r.id===focus.id?5:2.75,0,Math.PI*2);
    ctx.fillStyle=r.id===focus.id?"#91f4ff":["#fda17b","#94c5ff","#e8d9a6","#b4f5b0"][r.id%4];
    ctx.fill();
    if(r.id===focus.id){ctx.strokeStyle="#fff";ctx.lineWidth=1.5;ctx.stroke();}
  }
  ctx.restore();
}
export function drawOvalRace(opts){
  const {
    ctx,width,height,elapsed,cameraMeters,racers,focus,framesByMorph,
    spritePhase,orbDrawer,stage,motionReviewMode=false
  }=opts;
  const cam=ovalChaseCamera(cameraMeters,focus.lane);
  skyAndMountains(ctx,width,height,elapsed);
  grandstands(ctx,cam,width,height);
  drawOvalTrack(ctx,cam,width,height,cameraMeters);
  const renderable=[];
  for(const r of racers){
    if(motionReviewMode && r.id!==focus.id)continue;
    const p=projectOvalRunner(cam,r.distance,r.lane,width,height);
    if(!p||p.depth>410||p.x<-210||p.x>width+210||p.y<-200||p.y>height+280)continue;
    renderable.push({r,...p});
  }
  // Correct painter ordering by projected depth: distant runners drawn first.
  renderable.sort((a,b)=>b.depth-a.depth);
  let orbCount=0;
  for(const item of renderable){
    const {r,x,y,scale}=item;
    const chosen=r.id===focus.id;
    const frames=framesByMorph.get(r.morph);
    const frameIndex=spritePhase(r,elapsed);
    const frame=frames?.[frameIndex];
    const aspect=frame? frame.height/frame.width : .86;
    const spriteH=clamp(scale*(chosen?10.8:9.4),12,height*.39);
    const spriteW=spriteH/clamp(aspect,.60,1.08);
    // Side-facing approved source sheets are temporarily billboarded.
    // Do NOT claim this is a true 3/4-animated Creature.
    const shadowW=spriteW*.29;
    ctx.save();ctx.globalAlpha=.38;ctx.fillStyle="#302a24";
    ctx.beginPath();ctx.ellipse(x,y+1,shadowW,spriteH*.047,0,0,Math.PI*2);ctx.fill();
    ctx.restore();
    if(frame){
      const footY=frame.__motionMetrics?.footYNorm??.98;
      const offY=clamp((.98-footY)*spriteH,-spriteH*.16,spriteH*.16);
      ctx.save();ctx.translate(x,y-spriteH*.48);
      if(chosen){ctx.shadowColor="#79d5ff";ctx.shadowBlur=10;}
      ctx.drawImage(frame,-spriteW*.5,-spriteH*.5+offY,spriteW,spriteH);
      ctx.restore();
    }
    // One autonomous Agent orb per *visible* runner, with actual command state.
    orbDrawer(r,x,y,spriteW,spriteH,chosen);
    orbCount++;
    if(chosen){
      stage.dataset.selectedX=x.toFixed(1);
      stage.dataset.selectedY=y.toFixed(1);
      stage.dataset.selectedRunFrame=String(frameIndex);
    }
  }
  drawOvalMinimap(ctx,width,height,racers,focus);
  stage.dataset.cameraMode="oval-three-quarter-follow";
  stage.dataset.trackGeometry="world-space-1600m-oval";
  stage.dataset.trackSegment=ovalSegmentAt(focus.distance);
  stage.dataset.orbCount=String(orbCount);
  stage.dataset.visibleRacers=String(renderable.length);
  stage.dataset.trackVisible="1";
  stage.dataset.creatureFacing="side-billboard-provisional";
}
