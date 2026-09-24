/*
 * EvoWild Run Road Lab
 *
 * The segmented pseudo-3D road projection in this experimental lane is
 * adapted from the MIT-licensed javascript-racer architecture by Jake Gordon
 * and contributors. See /THIRD_PARTY_NOTICES.md.
 *
 * No javascript-racer image, sprite, or music assets are used here.
 */

const canvas = document.querySelector("#roadCanvas");
const ctx = canvas.getContext("2d", { alpha: false, desynchronized: true });
const board = document.querySelector("#board");
const ui = {
  phase: document.querySelector("#phase"),
  clock: document.querySelector("#clock"),
  remain: document.querySelector("#remain"),
  rank: document.querySelector("#rank"),
  speed: document.querySelector("#speed")
};

const BASE = import.meta.env.BASE_URL || "/";
const FPS = 60;
const STEP = 1 / FPS;
const SEGMENT_LENGTH = 180;
const ROAD_WIDTH = 2150;
const RUMBLE_LENGTH = 3;
const LANES = 6;
const DRAW_DISTANCE = 260;
const CAMERA_HEIGHT = 930;
const FIELD_OF_VIEW = 88;
const CAMERA_DEPTH = 1 / Math.tan((FIELD_OF_VIEW / 2) * Math.PI / 180);
const CAMERA_LEAD = 1450;
const SPRITE_SCALE = 0.00050;
const RACE_METERS = 1200;
const SELECTED_ID = 1;

let width = 1280;
let height = 720;
let dpr = 1;
let elapsed = 0;
let accumulator = 0;
let last = performance.now();
let trackLength = 0;
let cameraZ = 0;
let cameraX = 0;
let cameraY = CAMERA_HEIGHT;
let baseCurve = 0;
let lastBoardPaint = 0;

const segments = [];
const runners = [];
let sSheet = null;

const COLORS = {
  skyTop: "#3d7fa9",
  skyMid: "#9fc0cf",
  skyLow: "#dcc59c",
  grassLight: "#416a4e",
  grassDark: "#365d45",
  roadLight: "#9e6c42",
  roadDark: "#865936",
  rumbleLight: "#e5d8be",
  rumbleDark: "#4f6471",
  lane: "rgba(248,231,198,.74)",
  fog: "#b5c1b7"
};

function clamp(v, min, max) { return Math.max(min, Math.min(max, v)); }
function lerp(a, b, t) { return a + (b - a) * t; }
function easeIn(a, b, t) { return a + (b - a) * t * t; }
function easeOut(a, b, t) { return a + (b - a) * (1 - (1 - t) * (1 - t)); }
function easeInOut(a, b, t) { return a + (b - a) * ((-Math.cos(t * Math.PI) / 2) + .5); }
function percentRemaining(n, total) { return (n % total) / total; }
function increase(start, inc, max) {
  let r = start + inc;
  while (r >= max) r -= max;
  while (r < 0) r += max;
  return r;
}
function fogFactor(distance, density = 4.1) {
  return 1 / Math.pow(Math.E, distance * distance * density);
}

function resize() {
  const rect = canvas.getBoundingClientRect();
  width = Math.max(320, rect.width);
  height = Math.max(480, rect.height);
  dpr = Math.min(window.devicePixelRatio || 1, 1.7);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
new ResizeObserver(resize).observe(canvas);
resize();

function loadImage(src) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = "async";
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = src;
  });
}

loadImage(BASE + "concept/s-run-sheet.svg")
  .then(img => {
    sSheet = img;
    document.querySelector(".roadlab").dataset.state = "ready";
  })
  .catch(err => {
    document.querySelector(".roadlab").dataset.state = "asset-error";
    console.error(err);
  });

function lastY() {
  return segments.length ? segments[segments.length - 1].p2.world.y : 0;
}

function addSegment(curve, y) {
  const n = segments.length;
  segments.push({
    index: n,
    p1: { world: { y: lastY(), z: n * SEGMENT_LENGTH }, camera: {}, screen: {} },
    p2: { world: { y, z: (n + 1) * SEGMENT_LENGTH }, camera: {}, screen: {} },
    curve,
    clip: height,
    fog: 1,
    visible: false,
    colorIndex: Math.floor(n / RUMBLE_LENGTH) % 2
  });
}

function addRoad(enter, hold, leave, curve, hill) {
  const startY = lastY();
  const endY = startY + hill * SEGMENT_LENGTH;
  const total = enter + hold + leave;
  for (let n = 0; n < enter; n++)
    addSegment(easeIn(0, curve, n / Math.max(1, enter)), easeInOut(startY, endY, n / total));
  for (let n = 0; n < hold; n++)
    addSegment(curve, easeInOut(startY, endY, (enter + n) / total));
  for (let n = 0; n < leave; n++)
    addSegment(easeInOut(curve, 0, n / Math.max(1, leave)), easeInOut(startY, endY, (enter + hold + n) / total));
}

function buildTrack() {
  segments.length = 0;

  addRoad(20, 36, 20, 0.0, 8);
  addRoad(24, 46, 24, 1.2, 18);
  addRoad(18, 38, 18, 2.7, -10);
  addRoad(20, 42, 20, 0.0, 24);
  addRoad(24, 54, 24, -3.1, 8);
  addRoad(18, 34, 18, -1.4, -24);
  addRoad(20, 48, 20, 2.2, 12);
  addRoad(20, 36, 20, 0.0, 8);
  addRoad(22, 46, 22, -2.5, 18);
  addRoad(18, 42, 18, 1.7, -10);
  addRoad(20, 50, 20, 0.0, 0);

  trackLength = segments.length * SEGMENT_LENGTH;
}

function findSegment(z) {
  return segments[Math.floor(z / SEGMENT_LENGTH) % segments.length];
}

function project(point, camX, camY, camZ) {
  point.camera.x = -camX;
  point.camera.y = point.world.y - camY;
  point.camera.z = point.world.z - camZ;
  point.screen.scale = CAMERA_DEPTH / point.camera.z;
  point.screen.x = Math.round((width / 2) + point.screen.scale * point.camera.x * width / 2);
  point.screen.y = Math.round((height / 2) - point.screen.scale * point.camera.y * height / 2);
  point.screen.w = Math.round(point.screen.scale * ROAD_WIDTH * width / 2);
}

function roadPolygon(x1,y1,w1,x2,y2,w2,color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x1 - w1, y1);
  ctx.lineTo(x1 + w1, y1);
  ctx.lineTo(x2 + w2, y2);
  ctx.lineTo(x2 - w2, y2);
  ctx.closePath();
  ctx.fill();
}

function quad(x1,y1,x2,y2,x3,y3,x4,y4,color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x1,y1);
  ctx.lineTo(x2,y2);
  ctx.lineTo(x3,y3);
  ctx.lineTo(x4,y4);
  ctx.closePath();
  ctx.fill();
}

function renderRoadSegment(seg) {
  const { p1, p2 } = seg;
  const light = seg.colorIndex === 0;
  const grass = light ? COLORS.grassLight : COLORS.grassDark;
  const road = light ? COLORS.roadLight : COLORS.roadDark;
  const rumble = light ? COLORS.rumbleLight : COLORS.rumbleDark;

  const r1 = p1.screen.w / 13;
  const r2 = p2.screen.w / 13;
  const l1 = p1.screen.w / 58;
  const l2 = p2.screen.w / 58;

  ctx.fillStyle = grass;
  ctx.fillRect(0, p2.screen.y, width, p1.screen.y - p2.screen.y + 1);

  quad(
    p1.screen.x - p1.screen.w - r1, p1.screen.y,
    p1.screen.x - p1.screen.w, p1.screen.y,
    p2.screen.x - p2.screen.w, p2.screen.y,
    p2.screen.x - p2.screen.w - r2, p2.screen.y,
    rumble
  );
  quad(
    p1.screen.x + p1.screen.w + r1, p1.screen.y,
    p1.screen.x + p1.screen.w, p1.screen.y,
    p2.screen.x + p2.screen.w, p2.screen.y,
    p2.screen.x + p2.screen.w + r2, p2.screen.y,
    rumble
  );

  roadPolygon(p1.screen.x, p1.screen.y, p1.screen.w, p2.screen.x, p2.screen.y, p2.screen.w, road);

  const laneW1 = p1.screen.w * 2 / LANES;
  const laneW2 = p2.screen.w * 2 / LANES;
  let lx1 = p1.screen.x - p1.screen.w + laneW1;
  let lx2 = p2.screen.x - p2.screen.w + laneW2;
  for (let lane = 1; lane < LANES; lane++) {
    if ((seg.index + lane) % 5 < 3) {
      quad(lx1-l1/2,p1.screen.y,lx1+l1/2,p1.screen.y,lx2+l2/2,p2.screen.y,lx2-l2/2,p2.screen.y,COLORS.lane);
    }
    lx1 += laneW1;
    lx2 += laneW2;
  }

  if (seg.fog < 1) {
    ctx.globalAlpha = 1 - seg.fog;
    ctx.fillStyle = COLORS.fog;
    ctx.fillRect(0, p2.screen.y, width, p1.screen.y - p2.screen.y + 1);
    ctx.globalAlpha = 1;
  }
}

function drawBackground(curve, roadY) {
  const sky = ctx.createLinearGradient(0,0,0,height*.64);
  sky.addColorStop(0,COLORS.skyTop);
  sky.addColorStop(.56,COLORS.skyMid);
  sky.addColorStop(1,COLORS.skyLow);
  ctx.fillStyle = sky;
  ctx.fillRect(0,0,width,height);

  const sunX = width * .78 - curve * 18;
  const sunY = height * .14;
  const sr = Math.max(38, width * .028);
  const glow = ctx.createRadialGradient(sunX,sunY,0,sunX,sunY,sr*3);
  glow.addColorStop(0,"rgba(255,246,205,.88)");
  glow.addColorStop(1,"rgba(255,246,205,0)");
  ctx.fillStyle = glow;
  ctx.fillRect(sunX-sr*3,sunY-sr*3,sr*6,sr*6);

  const shift1 = (cameraZ * .012 + curve * 130) % 420;
  const shift2 = (cameraZ * .020 + curve * 190) % 290;

  ctx.fillStyle = "#6d8791";
  ctx.beginPath();
  ctx.moveTo(0,height*.50);
  for(let x=-440;x<width+440;x+=210) {
    const xx=x-shift1;
    const peak=height*.31 - Math.abs(Math.sin((x+cameraZ*.001)*.013))*height*.08;
    ctx.lineTo(xx,peak);
    ctx.lineTo(xx+105,height*.50);
  }
  ctx.lineTo(width,height*.56);
  ctx.lineTo(0,height*.56);
  ctx.closePath();
  ctx.fill();

  ctx.fillStyle = "#486b5d";
  ctx.beginPath();
  ctx.moveTo(0,height*.54);
  for(let x=-320;x<width+320;x+=95) {
    const xx=x-shift2;
    const peak=height*.43 - Math.abs(Math.sin((x+cameraZ*.002)*.041))*height*.05;
    ctx.lineTo(xx,peak);
    ctx.lineTo(xx+48,height*.55);
  }
  ctx.lineTo(width,height*.62);
  ctx.lineTo(0,height*.62);
  ctx.closePath();
  ctx.fill();

  const haze = ctx.createLinearGradient(0,height*.35,0,height*.63);
  haze.addColorStop(0,"rgba(225,235,226,0)");
  haze.addColorStop(1,"rgba(225,235,226,.20)");
  ctx.fillStyle=haze;
  ctx.fillRect(0,height*.34,width,height*.30);

  if (roadY > height*.40) {
    ctx.fillStyle="rgba(15,28,31,.08)";
    ctx.fillRect(0,roadY-2,width,3);
  }
}

function drawTrackside(seg) {
  if (!seg.visible) return;
  const p = seg.p1.screen;
  if (p.scale <= 0) return;

  const left = p.x - p.w * 1.07;
  const right = p.x + p.w * 1.07;
  const postH = clamp(p.scale * 290000, 3, 145);
  const postW = clamp(postH * .045, 1, 5);

  if (seg.index % 7 === 0) {
    ctx.strokeStyle = "rgba(225,234,233,.70)";
    ctx.lineWidth = postW;
    ctx.beginPath();
    ctx.moveTo(left,p.y);
    ctx.lineTo(left,p.y-postH);
    ctx.moveTo(right,p.y);
    ctx.lineTo(right,p.y-postH);
    ctx.stroke();

    ctx.strokeStyle = "rgba(215,229,231,.44)";
    ctx.lineWidth = Math.max(1,postW*.55);
    ctx.beginPath();
    ctx.moveTo(left,p.y-postH*.60);
    ctx.lineTo(right,p.y-postH*.60);
    ctx.stroke();
  }

  if (seg.index % 31 === 0 && p.scale > .00018) {
    const side = (Math.floor(seg.index/31)%2===0) ? -1 : 1;
    const bx = p.x + side * p.w * 1.38;
    const bw = clamp(postH * .72, 16, 118);
    const bh = bw * .34;
    ctx.fillStyle = "rgba(13,34,45,.90)";
    ctx.fillRect(bx - (side<0?bw:0), p.y-postH*.92, bw, bh);
    ctx.fillStyle = "rgba(105,220,247,.86)";
    ctx.fillRect(bx - (side<0?bw*.76: -bw*.12), p.y-postH*.78, bw*.62, Math.max(2,bh*.12));
  }

  if (seg.index % 53 === 0 && p.scale > .00021) {
    const side = (Math.floor(seg.index/53)%2===0) ? 1 : -1;
    const gx = p.x + side * p.w * 1.65;
    const gw = clamp(postH * 1.35, 32, 190);
    const gh = gw * .46;
    ctx.fillStyle = "rgba(31,45,52,.92)";
    ctx.fillRect(gx - (side<0?gw:0), p.y-gh, gw, gh);
    ctx.fillStyle = "rgba(195,205,204,.68)";
    for(let row=0;row<3;row++){
      for(let col=0;col<8;col++){
        if((row*3+col+seg.index)%4===0) ctx.fillStyle="#d4a983";
        else if((row+col)%3===0) ctx.fillStyle="#8faab3";
        else ctx.fillStyle="#c9d2d0";
        ctx.fillRect(gx + (side<0?-gw:0) + 5 + col*(gw/9), p.y-gh+6+row*(gh/4), Math.max(2,gw/24), Math.max(2,gh/14));
      }
    }
  }
}

function makeRunners() {
  const names=["Vela","Aster","Mica","Rook","Nacre","Ilex","Lumen","Tern"];
  const lanes=[2,4,1,5,3,0,4,1];
  const offsets=[0,480,-420,950,-760,1450,1880,-1120];
  const baseSpeed=[8650,8520,8760,8430,8600,8480,8700,8570];

  runners.length=0;
  for(let i=0;i<names.length;i++){
    runners.push({
      id:i+1,
      name:names[i],
      lane:lanes[i],
      laneF:lanes[i],
      offset: (lanes[i]-(LANES-1)/2)/(LANES*.60),
      z: 7600 + offsets[i],
      speed:baseSpeed[i],
      baseSpeed:baseSpeed[i],
      stamina:100,
      seed:i*1.81,
      targetLane:lanes[i],
      cooldown:0
    });
  }
}

function runnerRank(r) {
  return [...runners].sort((a,b)=>b.z-a.z).findIndex(x=>x===r)+1;
}

function updateRunnerAI(r, dt) {
  r.cooldown=Math.max(0,r.cooldown-dt);
  const progress=(r.z%trackLength)/trackLength;
  const phaseBoost = progress>.78 ? 1.025 : progress>.52 ? 1.008 : 1;
  const fatigue = .90 + .10*(r.stamina/100);
  const wave = Math.sin(elapsed*.0007+r.seed)*.008;
  const target=r.baseSpeed*phaseBoost*fatigue*(1+wave);

  r.speed += (target-r.speed)*Math.min(1,dt*1.7);

  const ahead=[...runners]
    .filter(o=>o!==r && Math.round(o.laneF)===Math.round(r.laneF) && o.z>r.z && o.z-r.z<720)
    .sort((a,b)=>a.z-b.z)[0];

  if(ahead && r.cooldown<=0){
    const options=[r.targetLane-1,r.targetLane+1].filter(l=>l>=0&&l<LANES);
    const free=options.find(l=>runners.every(o=>o===r || Math.round(o.laneF)!==l || Math.abs(o.z-r.z)>560));
    if(free!==undefined){
      r.targetLane=free;
      r.cooldown=1.2;
    }
  }

  r.laneF += (r.targetLane-r.laneF)*Math.min(1,dt*2.9);
  r.offset=(r.laneF-(LANES-1)/2)/(LANES*.60);
  r.z = increase(r.z, r.speed*dt, trackLength);
  r.stamina=Math.max(18,r.stamina-(.045+Math.max(0,r.speed/r.baseSpeed-1)*.20)*dt);
}

function update(dt) {
  for(const r of runners) updateRunnerAI(r,dt);

  const me=runners.find(r=>r.id===SELECTED_ID);
  cameraZ = increase(me.z,-CAMERA_LEAD,trackLength);
  cameraX += ((me.offset*ROAD_WIDTH*.36)-cameraX)*Math.min(1,dt*2.8);
}

function frameIndexFor(r) {
  const cadence = 76 - clamp((r.speed-r.baseSpeed)*.004,-8,8);
  return Math.floor((elapsed+r.id*61)/cadence)%6;
}

function drawRunner(r) {
  if(!sSheet) return;

  const seg=findSegment(r.z);
  if(!seg.visible) return;

  const percent=percentRemaining(r.z,SEGMENT_LENGTH);
  const scale=lerp(seg.p1.screen.scale,seg.p2.screen.scale,percent);
  if(scale<=0) return;

  const sxRoad=lerp(seg.p1.screen.x,seg.p2.screen.x,percent);
  const syRoad=lerp(seg.p1.screen.y,seg.p2.screen.y,percent);
  const swRoad=lerp(seg.p1.screen.w,seg.p2.screen.w,percent);
  const x=sxRoad + scale*r.offset*ROAD_WIDTH*width/2;
  const y=syRoad;

  const frame=frameIndexFor(r);
  const col=frame%3;
  const row=Math.floor(frame/3);
  const srcX=col*256;
  const srcY=row*256;

  const size = 256 * scale * width/2 * SPRITE_SCALE * ROAD_WIDTH;
  const w=clamp(size,12,width*.30);
  const h=w;
  const bob=[0,2,7,13,7,0][frame]*(w/190)*.34;

  if(y<0||y>height+80||x<-w||x>width+w) return;

  const shadowW=w*.34;
  ctx.fillStyle="rgba(17,12,10,.23)";
  ctx.beginPath();
  ctx.ellipse(x,y+4,shadowW,Math.max(2,w*.027),0,0,Math.PI*2);
  ctx.fill();

  if(w>48){
    const streak=(w/180)*clamp(r.speed/r.baseSpeed,.8,1.08);
    ctx.strokeStyle="rgba(210,236,246,.12)";
    ctx.lineWidth=Math.max(1,w*.008);
    for(let k=0;k<3;k++){
      const yy=y-h*(.26+k*.14);
      ctx.beginPath();
      ctx.moveTo(x-w*.26,yy);
      ctx.lineTo(x-w*(.26+.20*streak+k*.04),yy);
      ctx.stroke();
    }
  }

  const clipY=seg.clip;
  const drawH=Math.min(h,Math.max(0,clipY-(y-h)));
  if(drawH<=0) return;

  const srcH=256*(drawH/h);

  ctx.save();
  ctx.translate(x,y-h*.50-bob);
  ctx.transform(1,-.025,.08,1,0,0);
  ctx.scale(-1,1);
  ctx.drawImage(
    sSheet,
    srcX,srcY,256,srcH,
    -w*.5,-h*.5,w,drawH
  );
  ctx.restore();

  if(r.id===SELECTED_ID && w>60){
    const markerY=y-h-bob-9;
    ctx.fillStyle="rgba(102,223,255,.94)";
    ctx.beginPath();
    ctx.moveTo(x,markerY+7);
    ctx.lineTo(x-6,markerY-3);
    ctx.lineTo(x+6,markerY-3);
    ctx.closePath();
    ctx.fill();
  }
}

function drawSpeedCues(me) {
  const ratio=clamp(me.speed/me.baseSpeed,.75,1.08);
  const strength=clamp((ratio-.82)/.26,0,1);

  ctx.save();
  ctx.globalAlpha=.10+.12*strength;
  ctx.strokeStyle="#d8eef6";
  const count=42;
  for(let i=0;i<count;i++){
    const y=height*(.17+((i*43)%78)/100*.78);
    const x=((i*197-elapsed*.55)%(width+340)+width+340)%(width+340)-140;
    const len=35+strength*(90+(i%5)*24);
    ctx.lineWidth=.6+(i%4)*.28;
    ctx.beginPath();
    ctx.moveTo(x,y);
    ctx.lineTo(x-len,y);
    ctx.stroke();
  }
  ctx.restore();

  const vergeY=height*.982;
  const phase=((cameraZ*.16)%(width+180)+width+180)%(width+180);
  ctx.fillStyle="#243e2d";
  ctx.fillRect(0,vergeY-12,width,30);
  for(let x=-160+phase%160;x<width+160;x+=160){
    ctx.fillStyle="rgba(229,236,233,.76)";
    ctx.fillRect(x,vergeY-31,4,38);
    ctx.fillStyle="rgba(221,235,239,.10)";
    ctx.fillRect(x-40-strength*55,vergeY-16,40+strength*55,3);
  }
}

function render() {
  if(!segments.length) return;

  const me=runners.find(r=>r.id===SELECTED_ID);
  const base=findSegment(cameraZ);
  const basePercent=percentRemaining(cameraZ,SEGMENT_LENGTH);
  const meSeg=findSegment(me.z);
  const mePercent=percentRemaining(me.z,SEGMENT_LENGTH);
  const roadY=lerp(meSeg.p1.world.y,meSeg.p2.world.y,mePercent);
  cameraY = roadY + CAMERA_HEIGHT;

  baseCurve=base.curve;
  drawBackground(baseCurve,height*.52);

  let x=0;
  let dx=-(base.curve*basePercent);
  let maxY=height;

  for(const seg of segments){
    seg.visible=false;
    seg.clip=height;
  }

  for(let n=0;n<DRAW_DISTANCE;n++){
    const seg=segments[(base.index+n)%segments.length];
    const looped=seg.index<base.index;
    seg.fog=fogFactor(n/DRAW_DISTANCE);
    seg.clip=maxY;

    const camZ=cameraZ-(looped?trackLength:0);
    project(seg.p1,cameraX-x,cameraY,camZ);
    project(seg.p2,cameraX-x-dx,cameraY,camZ);

    x+=dx;
    dx+=seg.curve;

    if(seg.p1.camera.z<=CAMERA_DEPTH) continue;
    if(seg.p2.screen.y>=seg.p1.screen.y) continue;
    if(seg.p2.screen.y>=maxY) continue;

    seg.visible=true;
    renderRoadSegment(seg);
    maxY=seg.p2.screen.y;
  }

  for(let n=DRAW_DISTANCE-1;n>0;n--){
    const seg=segments[(base.index+n)%segments.length];
    if(seg.visible) drawTrackside(seg);
  }

  const cameraRelative = (z)=>{
    let d=z-cameraZ;
    if(d<0)d+=trackLength;
    return d;
  };
  [...runners]
    .filter(r=>cameraRelative(r.z)>0&&cameraRelative(r.z)<DRAW_DISTANCE*SEGMENT_LENGTH)
    .sort((a,b)=>cameraRelative(b.z)-cameraRelative(a.z))
    .forEach(drawRunner);

  drawSpeedCues(me);

  const vignette=ctx.createRadialGradient(width*.49,height*.48,height*.18,width*.5,height*.5,width*.78);
  vignette.addColorStop(0,"rgba(0,0,0,0)");
  vignette.addColorStop(1,"rgba(0,0,0,.28)");
  ctx.fillStyle=vignette;
  ctx.fillRect(0,0,width,height);
}

function phaseOf(progress) {
  if(progress<.12)return "START";
  if(progress<.60)return "MID";
  if(progress<.84)return "BUILD";
  return "FINAL";
}

function fmt(ms) {
  const t=ms/1000;
  const m=Math.floor(t/60);
  const s=Math.floor(t%60);
  const cs=Math.floor((t-Math.floor(t))*100);
  return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}.${String(cs).padStart(2,"0")}`;
}

function paintUI(now) {
  const me=runners.find(r=>r.id===SELECTED_ID);
  const progress=(me.z%trackLength)/trackLength;
  const rank=runnerRank(me);
  ui.phase.textContent=phaseOf(progress);
  ui.clock.textContent=fmt(elapsed);
  ui.remain.textContent=`${Math.max(0,Math.round((1-progress)*RACE_METERS))} m to go`;
  ui.rank.textContent=rank;
  ui.speed.textContent=(me.speed/430).toFixed(1);

  document.querySelector(".roadlab").dataset.running="true";
  document.querySelector(".roadlab").dataset.frame=String(frameIndexFor(me));

  if(now-lastBoardPaint>160){
    lastBoardPaint=now;
    const order=[...runners].sort((a,b)=>b.z-a.z);
    const lead=order[0].z;
    board.innerHTML=order.slice(0,6).map((r,i)=>{
      let gap=lead-r.z;
      if(gap<0)gap+=trackLength;
      return `<div class="board-row ${r.id===SELECTED_ID?"me":""}">
        <span class="p">${i+1}</span>
        <span class="n">#${String(r.id).padStart(2,"0")} ${r.name}</span>
        <span class="g">${i===0?"LEAD":"+"+(gap/430).toFixed(1)+"m"}</span>
      </div>`;
    }).join("");
  }
}

function loop(now) {
  const dt=Math.min(.05,(now-last)/1000);
  last=now;
  elapsed+=dt*1000;
  accumulator+=dt;

  while(accumulator>=STEP){
    update(STEP);
    accumulator-=STEP;
  }

  render();
  paintUI(now);
  requestAnimationFrame(loop);
}

buildTrack();
makeRunners();
cameraZ=increase(runners[0].z,-CAMERA_LEAD,trackLength);
requestAnimationFrame(now=>{
  last=now;
  loop(now);
});
