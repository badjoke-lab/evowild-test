const canvas = document.querySelector("#raceCanvas");
const ctx = canvas.getContext("2d", { alpha: false, desynchronized: true });
const stage = document.querySelector("#stage");

const ui = {
  rank: document.querySelector("#rank"),
  speed: document.querySelector("#speed"),
  command: document.querySelector("#command"),
  reason: document.querySelector("#reason"),
  distance: document.querySelector("#distance"),
  clock: document.querySelector("#clock"),
  progress: document.querySelector("#progress"),
  ranking: document.querySelector("#ranking"),
  countdown: document.querySelector("#countdown"),
  pause: document.querySelector("#pause"),
  reset: document.querySelector("#reset"),
  assetStatus: document.querySelector("#assetStatus")
};

const BASE = import.meta.env.BASE_URL || "/";

const UPSTREAM = window.Util;
if (!UPSTREAM || typeof UPSTREAM.accelerate !== "function" || typeof UPSTREAM.limit !== "function") {
  stage.dataset.upstreamRuntime = "missing";
  throw new Error("Lane 5 requires vendored javascript-racer common.js at runtime");
}
stage.dataset.upstreamRuntime = "javascript-racer-common-live";

const FIELD_SIZE = 8;
const SELECTED_ID = 1;
const RACE_METERS = 1600;
stage.dataset.engineLineage = "horse-race-animation-plus-fixed-step-racer";
const LANES = [1, 1, 2, 3, 0, 2, 1, 3];
const CRUISE = [36.8,34.7,35.9,34.9,36.1,35.2,35.6,34.8];
const ACCEL = [15.0,13.4,14.3,13.6,14.0,13.5,13.9,13.4];
const NAMES = ["Mica","Vela","Rook","Serein","Flint","Nacre","Ilex","Sora"];

const S_FRAMES = [
  { phase:"CONTACT", col:0, row:0, y:0.00 },
  { phase:"PUSH",    col:1, row:0, y:0.00 },
  { phase:"LIFT",    col:2, row:0, y:0.00 },
  { phase:"FLIGHT",  col:0, row:1, y:-0.42 },
  { phase:"REACH",   col:1, row:1, y:-0.17 },
  { phase:"LAND",    col:2, row:1, y:-0.16 }
];

const spriteSheet = new Image();
spriteSheet.decoding = "async";
spriteSheet.onload = () => {
  stage.dataset.sRunSheet = "ready";
  ui.assetStatus.textContent = "S run cycle ready";
};
spriteSheet.onerror = () => {
  stage.dataset.sRunSheet = "error";
  ui.assetStatus.textContent = "S run cycle failed";
};
spriteSheet.src = BASE + "concept/s-run-sheet.svg";

let width = 1;
let height = 1;
let dpr = 1;
let elapsed = 0;
let last = performance.now();
let paused = false;
let raceState = "countdown";
let countdownRemaining = 2500;
let finishCounter = 0;
let frameCounter = 0;
let lastRankingPaint = 0;
let cameraMeters = 0;
let cameraVelocity = 0;
let pixelsPerMeter = 8;
let pixelsPerMeterVelocity = 0;

const clamp = (v,a,b) => UPSTREAM.limit(v,a,b);
const lerp = (a,b,t) => a + (b-a)*t;
const smooth = (t) => t*t*(3-2*t);

function resize() {
  const r = canvas.getBoundingClientRect();
  width = Math.max(320, Math.floor(r.width));
  height = Math.max(420, Math.floor(r.height));
  dpr = Math.min(window.devicePixelRatio || 1, 1.65);
  canvas.width = Math.round(width*dpr);
  canvas.height = Math.round(height*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
new ResizeObserver(resize).observe(canvas);
resize();

function terrainY(m) {
  const a = Math.sin(m*0.0125)*14;
  const b = Math.sin(m*0.0042 + 0.8)*25;
  const c = Math.sin(m*0.021 + 1.7)*5;
  const openingRise = m > 35 && m < 205 ? Math.sin((m-35)/170*Math.PI)*48 : 0;
  const openingDrop = m >= 205 && m < 330 ? -Math.sin((m-205)/125*Math.PI)*28 : 0;
  const climb = m > 360 && m < 610 ? Math.sin((m-360)/250*Math.PI)*52 : 0;
  const dip = m > 760 && m < 1030 ? -Math.sin((m-760)/270*Math.PI)*38 : 0;
  return a+b+c+openingRise+openingDrop+climb+dip;
}

function terrainSlope(m) {
  return (terrainY(m+1.5)-terrainY(m-1.5))/3;
}

function courseBank(m) {
  const bankA = m > 170 && m < 360
    ? Math.sin((m-170)/190*Math.PI)*22
    : 0;
  const bankB = m > 520 && m < 760
    ? -Math.sin((m-520)/240*Math.PI)*28
    : 0;
  const bankC = m > 980 && m < 1240
    ? Math.sin((m-980)/260*Math.PI)*24
    : 0;
  return bankA+bankB+bankC;
}

function laneBankOffset(m,lane) {
  const depth=clamp(lane/3,0,1)*2-1;
  return courseBank(m)*depth;
}

function makeRacers() {
  return Array.from({length:FIELD_SIZE}, (_,i) => ({
    id:i+1,
    name:NAMES[i],
    distance: i*4.0,
    speed:0,
    cruise:CRUISE[i],
    accel:ACCEL[i],
    stamina:100,
    lane:LANES[i],
    targetLane:LANES[i],
    phaseOffset:i*0.87,
    cooldown:0,
    command:"HOLD FORM",
    reason:"Pre-start",
    finished:false,
    finishPlace:0,
    finishTime:0
  }));
}
let racers = makeRacers();

const selected = () => racers.find(r => r.id===SELECTED_ID);
const order = () => [...racers].sort((a,b) => {
  if (a.finished && b.finished) return a.finishPlace-b.finishPlace;
  if (a.finished) return -1;
  if (b.finished) return 1;
  return b.distance-a.distance;
});
const rankOf = r => order().findIndex(x=>x===r)+1;

function occupiedNear(r, lane, radius=8.5) {
  return racers.some(o => o!==r && !o.finished && o.lane===lane && Math.abs(o.distance-r.distance)<radius);
}
function gapAhead(r) {
  let best = Infinity;
  for (const o of racers) {
    if (o===r || o.finished || o.lane!==r.lane) continue;
    const g = o.distance-r.distance;
    if (g>0 && g<best) best=g;
  }
  return best;
}
function chooseLane(r) {
  const choices = [r.lane-1,r.lane+1,r.lane-2,r.lane+2]
    .filter(l => l>=0 && l<=3 && !occupiedNear(r,l,9))
    .sort((a,b) => Math.abs(a-r.lane)-Math.abs(b-r.lane));
  return choices[0] ?? r.lane;
}

function targetSpeedFor(r) {
  const p = r.distance/RACE_METERS;
  let target = r.cruise * (p<.15 ? 1.035 : p>.87 ? 1.085 : p>.68 ? 1.025 : 1.0);
  const gap = gapAhead(r);
  if (gap<7.5 && r.cooldown<=0) {
    const nextLane = chooseLane(r);
    if (nextLane!==r.lane) {
      r.targetLane = nextLane;
      r.cooldown = 1500;
      r.command = "SHIFT LINE";
      r.reason = "Traffic ahead";
      target *= 1.015;
    } else {
      target *= clamp(gap/7.5,.77,.97);
      r.command = "HOLD GAP";
      r.reason = "Blocked";
    }
  } else if (p>.87 && r.stamina>22) {
    r.command = "COMMIT";
    r.reason = "Final drive";
  } else if (p>.68) {
    r.command = "PRESS";
    r.reason = "Build phase";
  } else {
    r.command = "HOLD FORM";
    r.reason = "Efficient pace";
  }

  if (r.stamina<18) {
    target *= .89;
    r.command = "PRESERVE";
    r.reason = "Low stamina";
  }
  return target * (.83 + .17*(r.stamina/100));
}

function updateRace(dtMs) {
  if (paused) return;
  const dt = Math.min(50,dtMs)/1000;

  if (raceState==="countdown") {
    countdownRemaining -= dtMs;
    const n = Math.ceil(countdownRemaining/800);
    ui.countdown.hidden = false;
    ui.countdown.textContent = n>0 ? String(n) : "GO";
    if (countdownRemaining<=0) {
      raceState = "running";
      stage.dataset.raceState = "running";
      ui.countdown.textContent = "GO";
    }
    return;
  }

  if (raceState!=="running") return;
  elapsed += dtMs;
  if (elapsed>650) ui.countdown.hidden = true;

  for (const r of racers) {
    if (r.finished) continue;
    r.cooldown = Math.max(0,r.cooldown-dtMs);

    let target = targetSpeedFor(r);
    target += Math.sin(elapsed*.0015 + r.id*1.51)*.16;

    const diff = target-r.speed;
    const appliedAccel = r.accel * (diff >= 0 ? 1 : 1.45);
    r.speed = diff >= 0
      ? Math.min(target, UPSTREAM.accelerate(r.speed, appliedAccel, dt))
      : Math.max(target, UPSTREAM.accelerate(r.speed, -appliedAccel, dt));

    if (r.lane!==r.targetLane) {
      const dir = Math.sign(r.targetLane-r.lane);
      const laneStep = dt*1.9;
      const next = r.lane + dir*laneStep;
      if ((dir>0 && next>=r.targetLane)||(dir<0 && next<=r.targetLane)) r.lane=r.targetLane;
      else r.lane=next;
    }

    const effort = Math.max(0,r.speed/r.cruise-.95);
    r.stamina = Math.max(0,r.stamina-(.62+effort*effort*4.4)*dt);
    r.distance += Math.max(0,r.speed)*dt;

    if (r.distance>=RACE_METERS) {
      r.distance=RACE_METERS;
      r.finished=true;
      r.finishPlace=++finishCounter;
      r.finishTime=elapsed;
    }
  }
  if (finishCounter===racers.length) {
    raceState="finished";
    stage.dataset.raceState="finished";
  }
}

function drawSky() {
  const horizon = height*.48;
  const sky = ctx.createLinearGradient(0,0,0,horizon);
  sky.addColorStop(0,"#789fb6");
  sky.addColorStop(.56,"#b8c9c9");
  sky.addColorStop(1,"#d8c6a3");
  ctx.fillStyle=sky;
  ctx.fillRect(0,0,width,horizon);

  const sunX=width*.76, sunY=height*.18, r=Math.max(28,width*.025);
  const glow=ctx.createRadialGradient(sunX,sunY,0,sunX,sunY,r*3.2);
  glow.addColorStop(0,"rgba(255,243,204,.9)");
  glow.addColorStop(1,"rgba(255,243,204,0)");
  ctx.fillStyle=glow;
  ctx.fillRect(sunX-r*3.3,sunY-r*3.3,r*6.6,r*6.6);
}

function drawParallaxLayer(baseY, amplitude, speed, period, fill, jaggedness) {
  const shift = cameraMeters*speed;
  ctx.fillStyle=fill;
  ctx.beginPath();
  ctx.moveTo(0,height);
  ctx.lineTo(0,baseY);
  const step=Math.max(24,period*.12);
  for(let x=0;x<=width+step;x+=step){
    const worldX=x+shift;
    const wave=
      Math.abs(Math.sin(worldX*.0067))*jaggedness +
      Math.abs(Math.sin(worldX*.013))*(1-jaggedness);
    const ridge=Math.sin(worldX*.0021+1.2)*.16;
    ctx.lineTo(x,baseY-amplitude*(.22+.66*wave+ridge));
  }
  ctx.lineTo(width,height);
  ctx.closePath();
  ctx.fill();
}

function drawBackground() {
  drawSky();
  drawParallaxLayer(height*.50,95,.20,280,"#7b8f96",.7);
  drawParallaxLayer(height*.54,68,.38,210,"#62786d",.6);
  drawParallaxLayer(height*.58,42,.62,150,"#455d4d",.5);

  const ground=ctx.createLinearGradient(0,height*.53,0,height);
  ground.addColorStop(0,"#607d52");
  ground.addColorStop(1,"#253c2c");
  ctx.fillStyle=ground;
  ctx.fillRect(0,height*.53,width,height*.47);

  const treeShift = -cameraMeters*1.18;
  for (let i=-2;i<Math.ceil(width/54)+4;i++) {
    const x=i*54 + (treeShift%54);
    const v=Math.abs(Math.sin((i+Math.floor(cameraMeters/54))*.81));
    const h=32+v*46;
    const y=height*.57+v*7;
    ctx.fillStyle="#294634";
    ctx.fillRect(x-2,y-h*.08,4,h*.36);
    ctx.beginPath();
    ctx.moveTo(x,y-h);
    ctx.lineTo(x-h*.34,y-h*.15);
    ctx.lineTo(x+h*.34,y-h*.15);
    ctx.closePath();
    ctx.fill();
  }
}

function screenXForMeters(m) {
  const anchor = width<700 ? width*.50 : width*.46;
  return anchor + (m-cameraMeters)*pixelsPerMeter;
}

function trackBaseY(m) {
  const portrait=height>width*1.35;
  const base=portrait?height*.54:height*.64;
  return base - terrainY(m)*(portrait?.68:.52);
}

function laneYAt(m,lane) {
  return trackBaseY(m)+laneOffset(lane)+laneBankOffset(m,lane);
}

function laneOffset(lane) {
  const portrait=height>width*1.35;
  const stops=portrait?[-142,-48,50,148]:[-82,-28,30,88];
  const lo=Math.floor(clamp(lane,0,3));
  const hi=Math.ceil(clamp(lane,0,3));
  const t=clamp(lane-lo,0,1);
  return lerp(stops[lo],stops[hi],t);
}
function laneScale(lane) {
  const t=clamp(lane/3,0,1);
  return lerp(.68,1.12,t);
}

function drawTrack() {
  const leftM = cameraMeters - width*.40/pixelsPerMeter;
  const rightM = cameraMeters + width*.84/pixelsPerMeter;
  const step=2.0;

  const laneCenters=[0,1,2,3].map(laneOffset);
  const boundaries=[
    laneCenters[0]-36,
    (laneCenters[0]+laneCenters[1])*.5,
    (laneCenters[1]+laneCenters[2])*.5,
    (laneCenters[2]+laneCenters[3])*.5,
    laneCenters[3]+38
  ];

  // One continuous racing surface. Lane depth exists inside it; there are no stacked roads.
  for(let lane=0;lane<4;lane++){
    const far=boundaries[lane];
    const near=boundaries[lane+1];
    const shade=lane%2===0?"#4b5154":"#464c4f";
    ctx.fillStyle=shade;
    ctx.beginPath();
    let first=true;
    for(let m=leftM;m<=rightM+step;m+=step){
      const x=screenXForMeters(m);
      const bank=courseBank(m);
      const farDepth=lane/4*2-1;
      const y=trackBaseY(m)+far+bank*farDepth;
      if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);
    }
    for(let m=rightM+step;m>=leftM;m-=step){
      const x=screenXForMeters(m);
      const bank=courseBank(m);
      const nearDepth=(lane+1)/4*2-1;
      const y=trackBaseY(m)+near+bank*nearDepth;
      ctx.lineTo(x,y);
    }
    ctx.closePath();
    ctx.fill();
  }

  // Back and near track edges anchor the whole surface in the scene.
  for(const [offset,alpha,lineWidth] of [
    [boundaries[0],"rgba(226,236,237,.46)",2],
    [boundaries[4],"rgba(226,236,237,.62)",2.4]
  ]){
    ctx.strokeStyle=alpha;
    ctx.lineWidth=lineWidth;
    ctx.beginPath();
    let first=true;
    for(let m=leftM;m<=rightM+step;m+=step){
      const x=screenXForMeters(m);
      const depthNorm=(offset-boundaries[0])/(boundaries[4]-boundaries[0])*2-1;
      const y=trackBaseY(m)+offset+courseBank(m)*depthNorm;
      if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);
    }
    ctx.stroke();
  }

  // Internal lane boundaries are subtle, broken markers rather than separate roads.
  for(let divider=1;divider<4;divider++){
    const offset=boundaries[divider];
    ctx.strokeStyle="rgba(225,234,235,.19)";
    ctx.lineWidth=1.2;
    for(let m=Math.floor(leftM/10)*10;m<=rightM+10;m+=10){
      const m2=m+4.0;
      ctx.beginPath();
      const dividerDepth=divider/4*2-1;
      ctx.moveTo(screenXForMeters(m),trackBaseY(m)+offset+courseBank(m)*dividerDepth);
      ctx.lineTo(screenXForMeters(m2),trackBaseY(m2)+offset+courseBank(m2)*dividerDepth);
      ctx.stroke();
    }
  }

  // Short longitudinal texture marks make lateral speed readable without covering the creatures.
  for(let lane=0;lane<4;lane++){
    const yOffset=laneCenters[lane]+18;
    ctx.strokeStyle=lane===3?"rgba(238,243,235,.27)":"rgba(229,236,226,.15)";
    ctx.lineWidth=lane===3?1.7:1;
    for(let m=Math.floor(leftM/7)*7;m<=rightM+8;m+=7){
      const x1=screenXForMeters(m);
      const x2=screenXForMeters(m+2.0);
      const laneDepth=lane/3*2-1;
      const y1=trackBaseY(m)+yOffset+courseBank(m)*laneDepth;
      const y2=trackBaseY(m+2.0)+yOffset+courseBank(m+2.0)*laneDepth;
      ctx.beginPath();
      ctx.moveTo(x1,y1);
      ctx.lineTo(x2,y2);
      ctx.stroke();
    }
  }

  // Fence only on the back edge. It no longer cuts the race into separate horizontal strips.
  const fenceOffset=boundaries[0]-6;
  ctx.strokeStyle="rgba(212,224,219,.38)";
  ctx.lineWidth=2;
  ctx.beginPath();
  let fenceFirst=true;
  for(let m=leftM;m<=rightM+step;m+=step){
    const x=screenXForMeters(m);
    const y=trackBaseY(m)+fenceOffset-22-courseBank(m);
    if(fenceFirst){ctx.moveTo(x,y);fenceFirst=false;}else ctx.lineTo(x,y);
  }
  ctx.stroke();

  for(let m=Math.floor(leftM/14)*14;m<=rightM+16;m+=14){
    const x=screenXForMeters(m);
    const baseY=trackBaseY(m)+fenceOffset-courseBank(m);
    const sc=clamp(1+(m-cameraMeters)*.0015,.78,1.14);
    ctx.fillStyle="rgba(224,234,230,.82)";
    ctx.fillRect(x-1.5*sc,baseY-31*sc,3*sc,31*sc);
  }

  // Near-field streaks remain outside the track to sell speed.
  const focus=selected();
  const speedNorm=clamp(focus.speed/31.5,0,1);
  if(speedNorm>.30){
    ctx.save();
    ctx.globalAlpha=clamp((speedNorm-.30)*.64,0,.43);
    ctx.strokeStyle="rgba(232,240,214,.48)";
    for(let i=0;i<18;i++){
      const y=height*(.80+((i*29)%17)/100);
      const x=((i*83-cameraMeters*(pixelsPerMeter*1.72))%(width+180))-90;
      ctx.beginPath();
      ctx.moveTo(x,y);
      ctx.lineTo(x-58-speedNorm*92,y+3);
      ctx.stroke();
    }
    ctx.restore();
  }

  stage.dataset.trackSurface="single-field";
}

function drawCourseLandmarks() {
  const leftM=cameraMeters-width*.55/pixelsPerMeter;
  const rightM=cameraMeters+width*.62/pixelsPerMeter;
  const farY=laneOffset(0)-42;

  for(let mark=60;mark<RACE_METERS;mark+=60){
    if(mark<leftM-8||mark>rightM+8) continue;
    const x=screenXForMeters(mark);
    const baseY=trackBaseY(mark)+farY-courseBank(mark);
    const major=mark%360===0;
    const h=major?(height>width*1.35?86:64):(height>width*1.35?58:44);
    const w=major?54:38;

    ctx.save();
    ctx.fillStyle="rgba(22,35,38,.88)";
    ctx.fillRect(x-w*.5,baseY-h,w,major?24:19);
    ctx.fillStyle="rgba(226,241,242,.92)";
    ctx.font=`${major?"800":"700"} ${major?11:9}px ui-monospace, Menlo, monospace`;
    ctx.textAlign="center";
    ctx.textBaseline="middle";
    ctx.fillText(major?`SECTOR ${mark/360}`:`${mark}m`,x,baseY-h+(major?12:9.5));
    ctx.fillStyle="rgba(218,231,226,.70)";
    ctx.fillRect(x-2,baseY-h+(major?24:19),4,h-(major?24:19));
    ctx.restore();
  }

  for(let mark=360;mark<RACE_METERS;mark+=360){
    if(mark<leftM-18||mark>rightM+18) continue;
    const x=screenXForMeters(mark);
    const trackTop=laneYAt(mark,0)-45;
    const trackBottom=laneYAt(mark,3)+48;
    ctx.save();
    ctx.globalAlpha=.72;
    ctx.fillStyle="#23363a";
    ctx.fillRect(x-6,trackTop-34,6,trackBottom-trackTop+42);
    ctx.fillStyle="#8ddff4";
    ctx.fillRect(x-6,trackTop-34,6,9);
    ctx.restore();
  }
}

function drawRacers() {
  const list=[];
  let minEdge=Infinity;
  let maxEdge=-Infinity;
  for(const r of racers){
    const x=screenXForMeters(r.distance);
    if(x<-220 || x>width+260) continue;
    const lane=clamp(r.lane,0,3);
    const y=laneYAt(r.distance,lane);
    list.push({r,x,y,lane});
  }
  list.sort((a,b)=>a.lane-b.lane);

  for(const item of list){
    const r=item.r;
    const selectedRacer=r.id===SELECTED_ID;
    const scale=laneScale(item.lane);
    const baseW = width<700
      ? clamp(width*.14,90,124)
      : clamp(width*.092,122,148);
    const spriteW=baseW*scale*(selectedRacer?1.04:1);
    const spriteH=spriteW*.84;
    minEdge=Math.min(minEdge,item.x-spriteW*.52);
    maxEdge=Math.max(maxEdge,item.x+spriteW*.52);

    const cadence=9.5+clamp(r.speed/34,0,1)*9.5;
    const frameFloat=elapsed/1000*cadence+r.phaseOffset;
    const frameIndex=((Math.floor(frameFloat)%S_FRAMES.length)+S_FRAMES.length)%S_FRAMES.length;
    const frame=S_FRAMES[frameIndex];

    const slope=terrainSlope(r.distance);
    const lean=clamp(slope*.022,-.045,.045);

    const flight =
      frame.phase==="FLIGHT" ? 1 :
      frame.phase==="REACH" ? .55 :
      frame.phase==="LIFT" ? .28 : 0;
    const shadowW=spriteW*(.40-flight*.09);
    const shadowH=Math.max(3,spriteH*(.05-flight*.012));
    ctx.save();
    ctx.globalAlpha=.32-flight*.14;
    ctx.fillStyle="#071016";
    ctx.beginPath();
    ctx.ellipse(item.x,item.y+6+flight*3,shadowW,shadowH,0,0,Math.PI*2);
    ctx.fill();
    ctx.restore();

    const contactKick=frame.phase==="LAND"||frame.phase==="CONTACT"||frame.phase==="PUSH";
    if(r.speed>16&&contactKick){
      ctx.save();
      ctx.globalAlpha=.14;
      ctx.fillStyle="#d9c7a0";
      for(let p=0;p<3;p++){
        ctx.beginPath();
        ctx.ellipse(item.x-spriteW*(.28+p*.18),item.y+4+p*2,spriteW*(.09+p*.03),spriteH*.035,0,0,Math.PI*2);
        ctx.fill();
      }
      ctx.restore();
    }

    if(spriteSheet.complete && spriteSheet.naturalWidth>0){
      const fw=spriteSheet.naturalWidth/3, fh=spriteSheet.naturalHeight/2;
      const sx=frame.col*fw, sy=frame.row*fh;
      const footAdjust=frame.y*spriteH*.12;

      ctx.save();
      ctx.translate(item.x,item.y-spriteH*.48);
      ctx.rotate(lean);
      if(selectedRacer){
        ctx.shadowColor="rgba(126,226,255,.85)";
        ctx.shadowBlur=clamp(spriteW*.08,4,18);
      }
      ctx.drawImage(spriteSheet,sx,sy,fw,fh,-spriteW/2,-spriteH/2+footAdjust,spriteW,spriteH);
      ctx.restore();
    }

    const labelY=item.y-spriteH*.66;
    ctx.font=`800 ${width<700?9:11}px ui-monospace, Menlo, monospace`;
    ctx.textAlign="center";
    const txt=`S${String(r.id).padStart(2,"0")}`;
    const tw=ctx.measureText(txt).width+10;
    ctx.fillStyle=selectedRacer?"rgba(8,41,56,.92)":"rgba(3,10,15,.72)";
    ctx.fillRect(item.x-tw/2,labelY-12,tw,15);
    ctx.fillStyle="#eef9ff";
    ctx.fillText(txt,item.x,labelY);

    if(selectedRacer){
      stage.dataset.sRunFrame=String(frameIndex);
      stage.dataset.sRunPhase=frame.phase;
      stage.dataset.selectedX=item.x.toFixed(1);
      stage.dataset.selectedY=item.y.toFixed(1);
    }
  }

  stage.dataset.visibleRacers=String(list.length);
  stage.dataset.fieldMinX=Number.isFinite(minEdge)?minEdge.toFixed(1):"";
  stage.dataset.fieldMaxX=Number.isFinite(maxEdge)?maxEdge.toFixed(1):"";
}

function drawForeground() {
  const shift=-cameraMeters*(pixelsPerMeter*.52);
  ctx.save();
  ctx.globalAlpha=.68;
  for(let i=-2;i<Math.ceil(width/90)+4;i++){
    const x=i*90+(shift%90);
    const h=38+Math.abs(Math.sin(i*1.3))*34;
    ctx.strokeStyle="#1c3528";
    ctx.lineWidth=3;
    ctx.beginPath();
    ctx.moveTo(x,height);
    ctx.lineTo(x+8,height-h);
    ctx.stroke();
    ctx.strokeStyle="#274936";
    ctx.lineWidth=2;
    for(let b=0;b<3;b++){
      ctx.beginPath();
      ctx.moveTo(x+5,height-h+b*10);
      ctx.lineTo(x-10-b*2,height-h-8+b*8);
      ctx.stroke();
    }
  }
  ctx.restore();
}

function updateCamera() {
  const focus=selected();
  const live=racers.filter(r=>!r.finished);
  const front=live.length?Math.max(...live.map(r=>r.distance)):focus.distance;
  const back=live.length?Math.min(...live.map(r=>r.distance)):focus.distance;
  const span=Math.max(1,front-back);
  const p=clamp(focus.distance/RACE_METERS,0,1);

  // Lane 5 v2 stops shrinking the whole field to fit the screen.
  // The selected runner becomes the camera subject; rivals are allowed to enter/leave frame.
  let mode="LAUNCH";
  let targetPPM=width<700?5.9:7.2;
  let lead=-span*.08;

  if(p>=.12 && p<.62){
    mode="CHASE";
    targetPPM=width<700?6.8:8.7;
    lead=2.5;
  } else if(p>=.62 && p<.88){
    mode="ATTACK";
    targetPPM=width<700?7.5:9.7;
    lead=5.0;
  } else if(p>=.88){
    mode="FINISH";
    targetPPM=width<700?8.2:10.6;
    lead=8.0;
  }

  const targetCamera=focus.distance+lead;
  const zoomRate=targetPPM>pixelsPerMeter?.085:.15;
  pixelsPerMeter=lerp(pixelsPerMeter,targetPPM,zoomRate);
  cameraMeters=lerp(cameraMeters,targetCamera,mode==="LAUNCH"?.10:.18);

  stage.dataset.cameraMode=mode;
  stage.dataset.pixelsPerMeter=pixelsPerMeter.toFixed(2);
  stage.dataset.packSpan=span.toFixed(2);
}

function drawSpeedRush() {
  const focus=selected();
  const speedNorm=clamp(focus.speed/36.5,0,1);
  if(speedNorm<.36)return;

  ctx.save();
  const strength=clamp((speedNorm-.36)/.64,0,1);
  ctx.globalAlpha=.12+.25*strength;
  ctx.strokeStyle="rgba(238,247,243,.78)";
  ctx.lineCap="round";
  const count=width<700?20:34;
  for(let i=0;i<count;i++){
    const band=(i%5)/5;
    const y=height*(.61+band*.31)+Math.sin(i*1.73)*8;
    const phase=(elapsed*.24*(1+band*.6)+i*97)%(width+220);
    const x=width+80-phase;
    const len=52+strength*165+band*78;
    ctx.lineWidth=.7+band*1.4;
    ctx.beginPath();
    ctx.moveTo(x,y);
    ctx.lineTo(x-len,y+band*3);
    ctx.stroke();
  }
  ctx.restore();
}

function render() {
  const focus=selected();
  updateCamera();

  const speedNorm=clamp(focus.speed/36.5,0,1);
  const shake=speedNorm>.62?(speedNorm-.62)*7.6:0;
  ctx.save();
  ctx.translate(Math.sin(elapsed*.041)*shake,Math.sin(elapsed*.053+1.2)*shake*.38);

  drawBackground();
  drawTrack();
  drawCourseLandmarks();
  drawRacers();
  drawForeground();
  drawSpeedRush();
  ctx.restore();

  // subtle speed vignette
  const vignetteSpeed=clamp(focus.speed/36.5,0,1);
  if(vignetteSpeed>.58){
    const a=(vignetteSpeed-.58)*.17;
    const vg=ctx.createRadialGradient(width*.5,height*.55,height*.12,width*.5,height*.55,width*.78);
    vg.addColorStop(0,"rgba(0,0,0,0)");
    vg.addColorStop(1,`rgba(0,5,8,${a})`);
    ctx.fillStyle=vg;
    ctx.fillRect(0,0,width,height);
  }
}

function fmtTime(ms){
  const t=Math.max(0,ms)/1000;
  const min=Math.floor(t/60), sec=Math.floor(t%60), cs=Math.floor((t%1)*100);
  return `${String(min).padStart(2,"0")}:${String(sec).padStart(2,"0")}.${String(cs).padStart(2,"0")}`;
}

function updateUI(now){
  const focus=selected();
  const ranks=order();
  ui.rank.textContent=`${rankOf(focus)} / ${FIELD_SIZE}`;
  ui.speed.textContent=String(Math.round(focus.speed*3.6));
  ui.command.textContent=focus.command;
  ui.reason.textContent=focus.reason;
  ui.distance.textContent=`${Math.round(focus.distance)} / ${RACE_METERS} m`;
  ui.clock.textContent=fmtTime(elapsed);
  ui.progress.style.width=`${clamp(focus.distance/RACE_METERS*100,0,100).toFixed(2)}%`;

  if(now-lastRankingPaint>180){
    lastRankingPaint=now;
    ui.ranking.innerHTML=ranks.map((r,i)=>`<span class="${r.id===SELECTED_ID?"selected":""}">#${i+1} S${String(r.id).padStart(2,"0")}</span>`).join("");
  }

  stage.dataset.selectedDistance=focus.distance.toFixed(2);
  stage.dataset.selectedSpeed=focus.speed.toFixed(2);
  stage.dataset.selectedRank=String(rankOf(focus));
  stage.dataset.courseBank=courseBank(focus.distance).toFixed(2);
  stage.dataset.cameraMeters=cameraMeters.toFixed(2);
  stage.dataset.frameCounter=String(frameCounter);
}

function resetRace(){
  racers=makeRacers();
  elapsed=0;
  raceState="countdown";
  countdownRemaining=2500;
  finishCounter=0;
  cameraMeters=0;
  cameraVelocity=0;
  pixelsPerMeter=width<700?6.7:8.4;
  pixelsPerMeterVelocity=0;
  paused=false;
  ui.pause.textContent="Pause";
  ui.countdown.hidden=false;
  ui.countdown.textContent="3";
  stage.dataset.raceState="countdown";
}

ui.pause.addEventListener("click",()=>{
  paused=!paused;
  ui.pause.textContent=paused?"Resume":"Pause";
});
ui.reset.addEventListener("click",resetRace);

stage.dataset.raceState="countdown";

// Fixed timestep transplanted from the vendored javascript-racer Game.run pattern.
// Simulation time and rendering time are deliberately decoupled.
const FIXED_STEP_SECONDS = 1 / 60;
let gameDelta = 0;
function fixedFrame(now){
  const dt = Math.min(1, Math.max(0, (now-last)/1000));
  last = now;
  if(!paused) gameDelta += dt;

  let guard=0;
  while(gameDelta > FIXED_STEP_SECONDS && guard < 8){
    gameDelta -= FIXED_STEP_SECONDS;
    updateRace(FIXED_STEP_SECONDS*1000);
    guard++;
  }

  render();
  frameCounter++;
  updateUI(now);
  requestAnimationFrame(fixedFrame);
}
requestAnimationFrame(now=>{last=now;fixedFrame(now);});