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
const FIELD_SIZE = 8;
const SELECTED_ID = 1;
const RACE_METERS = 1440;
const LANES = [1, 0, 2, 3, 1, 2, 0, 3];
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
spriteSheet.src = BASE + "concept/s-run-sheet.webp";

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

const clamp = (v,a,b) => Math.max(a, Math.min(b,v));
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
  const climb = m > 260 && m < 530 ? Math.sin((m-260)/270*Math.PI)*42 : 0;
  const dip = m > 760 && m < 1030 ? -Math.sin((m-760)/270*Math.PI)*34 : 0;
  return a+b+c+climb+dip;
}

function terrainSlope(m) {
  return (terrainY(m+1.5)-terrainY(m-1.5))/3;
}

function makeRacers() {
  return Array.from({length:FIELD_SIZE}, (_,i) => ({
    id:i+1,
    name:NAMES[i],
    distance: i*7.0,
    speed:0,
    cruise:29.4 + ((i*5)%7)*0.34,
    accel:10.4 + (i%3)*0.45,
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
    const step = r.accel*dt*(diff>=0 ? 1 : 1.45);
    r.speed += clamp(diff,-step,step);

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
  const anchor = width<700 ? width*.27 : width*.34;
  return anchor + (m-cameraMeters)*pixelsPerMeter;
}

function trackBaseY(m) {
  const portrait=height>width*1.35;
  const base=portrait?height*.625:height*.70;
  return base - terrainY(m)*(portrait?.68:.52);
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

  // Four perspective bands.
  for (let lane=0; lane<4; lane++) {
    const far = laneOffset(lane)-24;
    const near = laneOffset(lane)+24;
    const shade = lane%2 ? "#464c4f" : "#50575a";

    ctx.fillStyle=shade;
    ctx.beginPath();
    let first=true;
    for (let m=leftM; m<=rightM+step; m+=step) {
      const x=screenXForMeters(m);
      const y=trackBaseY(m)+far;
      if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);
    }
    for (let m=rightM+step; m>=leftM; m-=step) {
      const x=screenXForMeters(m);
      const y=trackBaseY(m)+near;
      ctx.lineTo(x,y);
    }
    ctx.closePath();
    ctx.fill();

    // Lane edge.
    ctx.strokeStyle = lane===3 ? "rgba(226,236,237,.55)" : "rgba(230,238,240,.16)";
    ctx.lineWidth = lane===3 ? 2 : 1;
    ctx.beginPath();
    first=true;
    for(let m=leftM;m<=rightM+step;m+=step){
      const x=screenXForMeters(m), y=trackBaseY(m)+near;
      if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);
    }
    ctx.stroke();
  }

  // Repeating ground marks make speed visible even when the racers are clustered.
  for(let lane=0;lane<4;lane++){
    const yOffset=laneOffset(lane)+14;
    ctx.strokeStyle=lane===3?"rgba(238,243,235,.34)":"rgba(229,236,226,.18)";
    ctx.lineWidth=lane===3?2:1;
    for(let m=Math.floor(leftM/7)*7;m<=rightM+8;m+=7){
      const x1=screenXForMeters(m);
      const x2=screenXForMeters(m+2.2);
      const y1=trackBaseY(m)+yOffset;
      const y2=trackBaseY(m+2.2)+yOffset;
      ctx.beginPath();
      ctx.moveTo(x1,y1);
      ctx.lineTo(x2,y2);
      ctx.stroke();
    }
  }

  // Roadside posts: strong speed cue.
  for (let m=Math.floor(leftM/10)*10; m<=rightM+16; m+=10) {
    const x=screenXForMeters(m);
    const y=trackBaseY(m)-54;
    const sc=clamp(1+(m-cameraMeters)*.002,.72,1.18);
    ctx.fillStyle="rgba(229,238,235,.9)";
    ctx.fillRect(x-2*sc,y,4*sc,47*sc);
    ctx.fillStyle="#385245";
    ctx.fillRect(x-7*sc,y,14*sc,5*sc);
  }

  // Near grass blades and dust streaks.
  const focus=selected();
  const speedNorm=clamp(focus.speed/24.5,0,1);
  if(speedNorm>.34){
    ctx.save();
    ctx.globalAlpha=clamp((speedNorm-.34)*.62,0,.42);
    ctx.strokeStyle="rgba(232,240,214,.5)";
    for(let i=0;i<18;i++){
      const y=height*(.72+((i*29)%22)/100);
      const x=((i*83 - cameraMeters*(pixelsPerMeter*1.72))%(width+180))-90;
      ctx.beginPath();
      ctx.moveTo(x,y);
      ctx.lineTo(x-55-speedNorm*85,y+3);
      ctx.stroke();
    }
    ctx.restore();
  }
}

function drawRacers() {
  const list=[];
  let minX=Infinity;
  let maxX=-Infinity;
  for(const r of racers){
    const x=screenXForMeters(r.distance);
    if(x<-220 || x>width+260) continue;
    const lane=clamp(r.lane,0,3);
    const y=trackBaseY(r.distance)+laneOffset(lane);
    list.push({r,x,y,lane});
    minX=Math.min(minX,x);
    maxX=Math.max(maxX,x);
  }
  list.sort((a,b)=>a.lane-b.lane);
  stage.dataset.visibleRacers=String(list.length);
  stage.dataset.fieldMinX=Number.isFinite(minX)?minX.toFixed(1):"";
  stage.dataset.fieldMaxX=Number.isFinite(maxX)?maxX.toFixed(1):"";

  for(const item of list){
    const r=item.r;
    const selectedRacer=r.id===SELECTED_ID;
    const scale=laneScale(item.lane);
    const baseW = width<700
      ? clamp(width*.14,90,124)
      : clamp(width*.092,122,148);
    const spriteW=baseW*scale*(selectedRacer?1.04:1);
    const spriteH=spriteW*.84;

    const cadence=7+clamp(r.speed/24,0,1)*7.7;
    const frameFloat=elapsed/1000*cadence+r.phaseOffset;
    const frameIndex=((Math.floor(frameFloat)%S_FRAMES.length)+S_FRAMES.length)%S_FRAMES.length;
    const frame=S_FRAMES[frameIndex];

    const slope=terrainSlope(r.distance);
    const lean=clamp(slope*.022,-.045,.045);

    const shadowW=spriteW*.40, shadowH=Math.max(3,spriteH*.05);
    ctx.save();
    ctx.globalAlpha=.32;
    ctx.fillStyle="#071016";
    ctx.beginPath();
    ctx.ellipse(item.x,item.y+6,shadowW,shadowH,0,0,Math.PI*2);
    ctx.fill();
    ctx.restore();

    if(r.speed>16){
      ctx.save();
      ctx.globalAlpha=.12;
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
  const ahead=Math.max(0,front-focus.distance);
  const behind=Math.max(0,focus.distance-back);

  // Mobile must keep the race readable: zoom out only when the pack genuinely spreads.
  const base=width<700?6.7:8.4;
  const usableAhead=width*(width<700?.64:.56);
  const usableBehind=width*(width<700?.16:.20);
  const byAhead=ahead>1?usableAhead/ahead:base;
  const byBehind=behind>1?usableBehind/behind:base;
  const targetPPM=clamp(Math.min(base,byAhead,byBehind),width<700?3.9:5.2,base);
  const ppmDelta=targetPPM-pixelsPerMeter;
  pixelsPerMeterVelocity=lerp(pixelsPerMeterVelocity,ppmDelta*.18,.16);
  pixelsPerMeter+=pixelsPerMeterVelocity*.11;

  // Keep selected S left-of-centre and give more room in the direction of travel.
  const lookAhead=clamp(ahead*.06,0,3.5);
  const targetCamera=Math.max(0,focus.distance+lookAhead);
  const delta=targetCamera-cameraMeters;
  cameraVelocity=lerp(cameraVelocity,delta*.11,.16);
  cameraMeters+=cameraVelocity*.075;
  if(Math.abs(delta)<.015) cameraMeters=targetCamera;

  stage.dataset.pixelsPerMeter=pixelsPerMeter.toFixed(2);
}

function drawSpeedRush() {
  const focus=selected();
  const speedNorm=clamp(focus.speed/24.5,0,1);
  if(speedNorm<.36)return;

  ctx.save();
  const strength=clamp((speedNorm-.36)/.64,0,1);
  ctx.globalAlpha=.12+.25*strength;
  ctx.strokeStyle="rgba(238,247,243,.78)";
  ctx.lineCap="round";
  const count=width<700?14:22;
  for(let i=0;i<count;i++){
    const band=(i%5)/5;
    const y=height*(.61+band*.31)+Math.sin(i*1.73)*8;
    const phase=(elapsed*.24*(1+band*.6)+i*97)%(width+220);
    const x=width+80-phase;
    const len=34+strength*105+band*55;
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

  const speedNorm=clamp(focus.speed/24.5,0,1);
  const shake=speedNorm>.70?(speedNorm-.70)*5.2:0;
  ctx.save();
  ctx.translate(Math.sin(elapsed*.041)*shake,Math.sin(elapsed*.053+1.2)*shake*.38);

  drawBackground();
  drawTrack();
  drawRacers();
  drawForeground();
  drawSpeedRush();
  ctx.restore();

  // subtle speed vignette
  const vignetteSpeed=clamp(focus.speed/24.5,0,1);
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

function frame(now){
  const dt=Math.min(60,Math.max(0,now-last));
  last=now;
  updateRace(dt);
  render();
  frameCounter++;
  updateUI(now);
  requestAnimationFrame(frame);
}

stage.dataset.raceState="countdown";
requestAnimationFrame(now=>{last=now;frame(now);});