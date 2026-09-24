/*
  EvoWild Run Lane 4 V3
  Road projection / segmented pseudo-3D structure adapted from:
  Jake Gordon, javascript-racer (MIT License)
  https://github.com/jakesgordon/javascript-racer

  No upstream OutRun-derived sprites or licensed music are included.
*/

const canvas = document.querySelector("#race");
const ctx = canvas.getContext("2d", { alpha: false });
const stage = document.querySelector("#stage");

const ui = {
  speed: document.querySelector("#speed"),
  distance: document.querySelector("#distance"),
  rank: document.querySelector("#rank"),
  phase: document.querySelector("#phase"),
  command: document.querySelector("#command"),
  reason: document.querySelector("#reason")
};

const BASE = import.meta.env.BASE_URL || "/";
const fps = 60;
const step = 1 / fps;
const width = 1280;
const height = 720;
const lanes = 5;
const roadWidth = 2000;
const segmentLength = 200;
const rumbleLength = 3;
const drawDistance = 300;
const fieldOfView = 100;
const cameraHeight = 1000;
const cameraDepth = 1 / Math.tan((fieldOfView / 2) * Math.PI / 180);
const playerZ = cameraHeight * cameraDepth;
const fogDensity = 5;
const maxSpeed = segmentLength / step;
const raceMeters = 2400;
const worldToMeters = 0.055;
const selectedId = 0;

canvas.width = width;
canvas.height = height;

const Util = {
  limit: (v, min, max) => Math.max(min, Math.min(max, v)),
  interpolate: (a, b, p) => a + (b - a) * p,
  easeIn: (a, b, p) => a + (b - a) * Math.pow(p, 2),
  easeOut: (a, b, p) => a + (b - a) * (1 - Math.pow(1 - p, 2)),
  easeInOut: (a, b, p) => a + (b - a) * ((-Math.cos(p * Math.PI) / 2) + 0.5),
  percentRemaining: (n, total) => (n % total) / total,
  exponentialFog: (distance, density) => 1 / Math.pow(Math.E, distance * distance * density),
  increase(start, increment, max) {
    let result = start + increment;
    while (result >= max) result -= max;
    while (result < 0) result += max;
    return result;
  },
  project(p, cameraX, cameraY, cameraZ) {
    p.camera.x = (p.world.x || 0) - cameraX;
    p.camera.y = (p.world.y || 0) - cameraY;
    p.camera.z = (p.world.z || 0) - cameraZ;
    p.screen.scale = cameraDepth / p.camera.z;
    p.screen.x = Math.round((width / 2) + (p.screen.scale * p.camera.x * width / 2));
    p.screen.y = Math.round((height / 2) - (p.screen.scale * p.camera.y * height / 2));
    p.screen.w = Math.round(p.screen.scale * roadWidth * width / 2);
  }
};

const COLORS = {
  LIGHT: { road: "#515860", grass: "#31543c", rumble: "#c9e2e2", lane: "#aebfc2" },
  DARK:  { road: "#454c54", grass: "#294934", rumble: "#22343d", lane: null },
  START: { road: "#d8e4e8", grass: "#31543c", rumble: "#d8e4e8", lane: "#65737a" },
  FINISH:{ road: "#14191e", grass: "#294934", rumble: "#d8e4e8", lane: "#d8e4e8" }
};

const ROAD = {
  LENGTH: { SHORT: 25, MEDIUM: 50, LONG: 100 },
  HILL: { NONE: 0, LOW: 20, MEDIUM: 40, HIGH: 60 },
  CURVE: { NONE: 0, EASY: 2, MEDIUM: 4, HARD: 6 }
};

let segments = [];
let trackLength = 0;

function lastY() {
  return segments.length === 0 ? 0 : segments[segments.length - 1].p2.world.y;
}

function addSegment(curve, y) {
  const n = segments.length;
  segments.push({
    index: n,
    p1: { world: { y: lastY(), z: n * segmentLength }, camera: {}, screen: {} },
    p2: { world: { y, z: (n + 1) * segmentLength }, camera: {}, screen: {} },
    curve,
    cars: [],
    color: Math.floor(n / rumbleLength) % 2 ? COLORS.DARK : COLORS.LIGHT,
    fog: 1,
    clip: height
  });
}

function addRoad(enter, hold, leave, curve, y) {
  const startY = lastY();
  const endY = startY + y * segmentLength;
  const total = enter + hold + leave;
  for (let n = 0; n < enter; n++) addSegment(Util.easeIn(0, curve, n / enter), Util.easeInOut(startY, endY, n / total));
  for (let n = 0; n < hold; n++) addSegment(curve, Util.easeInOut(startY, endY, (enter + n) / total));
  for (let n = 0; n < leave; n++) addSegment(Util.easeInOut(curve, 0, n / leave), Util.easeInOut(startY, endY, (enter + hold + n) / total));
}

function addStraight(num = ROAD.LENGTH.MEDIUM) { addRoad(num, num, num, 0, 0); }
function addHill(num = ROAD.LENGTH.MEDIUM, h = ROAD.HILL.MEDIUM) { addRoad(num, num, num, 0, h); }
function addCurve(num = ROAD.LENGTH.MEDIUM, curve = ROAD.CURVE.MEDIUM, h = 0) { addRoad(num, num, num, curve, h); }
function addLowRollingHills(num = ROAD.LENGTH.SHORT, h = ROAD.HILL.LOW) {
  addRoad(num, num, num, 0, h / 2);
  addRoad(num, num, num, 0, -h);
  addRoad(num, num, num, ROAD.CURVE.EASY, h);
  addRoad(num, num, num, 0, 0);
  addRoad(num, num, num, -ROAD.CURVE.EASY, h / 2);
  addRoad(num, num, num, 0, 0);
}
function addSCurves() {
  addRoad(50, 50, 50, -ROAD.CURVE.EASY, 0);
  addRoad(50, 50, 50, ROAD.CURVE.MEDIUM, ROAD.HILL.MEDIUM);
  addRoad(50, 50, 50, ROAD.CURVE.EASY, -ROAD.HILL.LOW);
  addRoad(50, 50, 50, -ROAD.CURVE.EASY, ROAD.HILL.MEDIUM);
  addRoad(50, 50, 50, -ROAD.CURVE.MEDIUM, -ROAD.HILL.MEDIUM);
}
function addBumps() {
  [[5,0],[8,0],[-2,0],[-5,0],[8,0],[5,0],[-7,0]].forEach(([h,c]) => addRoad(10,10,10,c,h));
}
function addDownhillToEnd(num = 150) { addRoad(num, num, num, -ROAD.CURVE.EASY, -lastY() / segmentLength); }

function resetRoad() {
  segments = [];
  addStraight(ROAD.LENGTH.SHORT);
  addLowRollingHills();
  addSCurves();
  addCurve(ROAD.LENGTH.MEDIUM, ROAD.CURVE.MEDIUM, ROAD.HILL.LOW);
  addBumps();
  addLowRollingHills();
  addCurve(ROAD.LENGTH.LONG, ROAD.CURVE.MEDIUM, ROAD.HILL.MEDIUM);
  addStraight();
  addHill(ROAD.LENGTH.MEDIUM, ROAD.HILL.HIGH);
  addSCurves();
  addCurve(ROAD.LENGTH.LONG, -ROAD.CURVE.MEDIUM, 0);
  addHill(ROAD.LENGTH.LONG, ROAD.HILL.HIGH);
  addCurve(ROAD.LENGTH.LONG, ROAD.CURVE.MEDIUM, -ROAD.HILL.LOW);
  addBumps();
  addHill(ROAD.LENGTH.LONG, -ROAD.HILL.MEDIUM);
  addStraight();
  addSCurves();
  addDownhillToEnd();

  trackLength = segments.length * segmentLength;
  const startIndex = findSegment(playerZ).index + 2;
  segments[startIndex].color = COLORS.START;
  segments[startIndex + 1].color = COLORS.START;
  for (let n = 0; n < rumbleLength; n++) segments[segments.length - 1 - n].color = COLORS.FINISH;
}

function findSegment(z) {
  return segments[Math.floor(z / segmentLength) % segments.length];
}

resetRoad();

const names = ["Mica","Vela","Rook","Nacre","Serein","Kite","Flint","Dune","Lumen","Aster"];
const laneSlots = [-0.72, -0.36, 0, 0.36, 0.72];
const startZ = 5200;

function makeRacers() {
  return names.map((name, i) => ({
    id: i,
    name,
    offset: laneSlots[i % laneSlots.length],
    targetOffset: laneSlots[i % laneSlots.length],
    z: Util.increase(startZ, i === selectedId ? 0 : 240 + i * 155, trackLength),
    speed: 0,
    max: maxSpeed * (0.70 + (i % 5) * 0.012),
    accel: maxSpeed / (4.4 + (i % 3) * 0.25),
    stamina: 100,
    cooldown: 0,
    phase: "START",
    frameSeed: i * 0.71,
    command: "BUILD SPEED",
    reason: "Launch phase"
  }));
}

let racers = makeRacers();
let elapsed = 0;
let last = performance.now();
let accumulator = 0;
let cameraPosition = Util.increase(racers[selectedId].z, -playerZ, trackLength);

function selected() { return racers[selectedId]; }

function distanceAhead(from, to) {
  return (to.z - from.z + trackLength) % trackLength;
}

function currentRaceMeters(r) {
  const d = (r.z - startZ + trackLength) % trackLength;
  return Math.min(raceMeters, d * worldToMeters);
}

function phaseOf(r) {
  const p = currentRaceMeters(r) / raceMeters;
  if (p < 0.08) return "START";
  if (p < 0.60) return "MID";
  if (p < 0.83) return "BUILD";
  return "FINAL";
}

function rankOf(r) {
  const d = currentRaceMeters(r);
  return 1 + racers.filter(o => o !== r && currentRaceMeters(o) > d).length;
}

function nearestAhead(r, offset = r.targetOffset) {
  let best = null;
  let gap = Infinity;
  for (const o of racers) {
    if (o === r || Math.abs(o.offset - offset) > 0.24) continue;
    const d = distanceAhead(r, o);
    if (d > 0 && d < gap && d < 2600) { gap = d; best = o; }
  }
  return { racer: best, gap };
}

function chooseLane(r) {
  let best = r.targetOffset;
  let bestGap = -1;
  for (const slot of laneSlots) {
    const occupied = racers.some(o => o !== r && Math.abs(o.offset - slot) < 0.22 && Math.min(distanceAhead(r,o), distanceAhead(o,r)) < 720);
    if (occupied) continue;
    const gap = nearestAhead(r, slot).gap;
    if (gap > bestGap) { bestGap = gap; best = slot; }
  }
  return best;
}

function updateRacers(dt) {
  for (const r of racers) {
    const oldSegment = findSegment(r.z);
    r.cooldown = Math.max(0, r.cooldown - dt);
    r.phase = phaseOf(r);

    let target = r.max;
    const p = currentRaceMeters(r) / raceMeters;
    if (p < 0.08) target *= 1.035;
    if (r.phase === "FINAL" && r.stamina > 24) target *= 1.055;
    if (r.stamina < 18) target *= 0.88;

    const ahead = nearestAhead(r);
    if (ahead.gap < 900 && r.cooldown <= 0) {
      const lane = chooseLane(r);
      if (lane !== r.targetOffset) {
        r.targetOffset = lane;
        r.cooldown = 0.8 + (r.id % 4) * 0.13;
        r.command = "SHIFT LANE";
        r.reason = "Traffic ahead";
      } else {
        target *= Math.max(0.84, ahead.gap / 900);
        r.command = "HOLD";
        r.reason = "No clean line";
      }
    } else if (r.phase === "FINAL") {
      r.command = "COMMIT";
      r.reason = "Final drive";
    } else if (r.phase === "BUILD") {
      r.command = "PRESS";
      r.reason = "Build phase";
    } else {
      r.command = "CRUISE";
      r.reason = r.phase === "START" ? "Settle into pace" : "Maintain efficiency";
    }

    const diff = target - r.speed;
    const change = r.accel * dt * (diff >= 0 ? 1 : 1.6);
    r.speed += Util.limit(diff, -change, change);
    r.speed = Math.max(0, r.speed);
    r.z = Util.increase(r.z, r.speed * dt, trackLength);
    r.offset += (r.targetOffset - r.offset) * Math.min(1, dt * 3.3);

    const effort = Math.max(0, r.speed / r.max - 0.93);
    r.stamina = Math.max(0, r.stamina - (0.22 + effort * effort * 1.8) * dt);

    const newSegment = findSegment(r.z);
    if (r.id !== selectedId && oldSegment !== newSegment) {
      const idx = oldSegment.cars.indexOf(r);
      if (idx >= 0) oldSegment.cars.splice(idx, 1);
      if (!newSegment.cars.includes(r)) newSegment.cars.push(r);
    }
  }

  const s = selected();
  cameraPosition = Util.increase(s.z, -playerZ, trackLength);
}

for (const r of racers) if (r.id !== selectedId) findSegment(r.z).cars.push(r);

const runSheet = new Image();
runSheet.decoding = "async";
runSheet.onload = () => {
  stage.dataset.lane4 = "running";
  stage.dataset.spriteSheet = "ready";
};
runSheet.onerror = () => {
  stage.dataset.lane4 = "error";
  stage.dataset.spriteSheet = "error";
};
runSheet.src = BASE + "concept/s-run-sheet.webp";

function polygon(x1,y1,x2,y2,x3,y3,x4,y4,color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(x1,y1); ctx.lineTo(x2,y2); ctx.lineTo(x3,y3); ctx.lineTo(x4,y4);
  ctx.closePath(); ctx.fill();
}

function drawSegment(x1,y1,w1,x2,y2,w2,fog,color) {
  const r1 = w1 / Math.max(6, 2 * lanes);
  const r2 = w2 / Math.max(6, 2 * lanes);
  const l1 = w1 / Math.max(32, 8 * lanes);
  const l2 = w2 / Math.max(32, 8 * lanes);

  ctx.fillStyle = color.grass;
  ctx.fillRect(0, y2, width, Math.max(0, y1 - y2));

  polygon(x1-w1-r1,y1,x1-w1,y1,x2-w2,y2,x2-w2-r2,y2,color.rumble);
  polygon(x1+w1+r1,y1,x1+w1,y1,x2+w2,y2,x2+w2+r2,y2,color.rumble);
  polygon(x1-w1,y1,x1+w1,y1,x2+w2,y2,x2-w2,y2,color.road);

  if (color.lane) {
    let laneW1 = w1 * 2 / lanes;
    let laneW2 = w2 * 2 / lanes;
    let laneX1 = x1 - w1 + laneW1;
    let laneX2 = x2 - w2 + laneW2;
    for (let lane = 1; lane < lanes; lane++, laneX1 += laneW1, laneX2 += laneW2) {
      polygon(laneX1-l1/2,y1,laneX1+l1/2,y1,laneX2+l2/2,y2,laneX2-l2/2,y2,color.lane);
    }
  }

  if (fog < 1) {
    ctx.globalAlpha = 1 - fog;
    ctx.fillStyle = "#132b34";
    ctx.fillRect(0, y2, width, y1 - y2);
    ctx.globalAlpha = 1;
  }
}

function drawBackdrop(baseCurve, playerY) {
  const g = ctx.createLinearGradient(0,0,0,height*0.62);
  g.addColorStop(0,"#071421");
  g.addColorStop(.48,"#183d52");
  g.addColorStop(1,"#9bb0ae");
  ctx.fillStyle = g;
  ctx.fillRect(0,0,width,height);

  const sunX = width * 0.72 - baseCurve * 48;
  const sunY = height * 0.20 - playerY * 0.003;
  const rg = ctx.createRadialGradient(sunX,sunY,2,sunX,sunY,120);
  rg.addColorStop(0,"rgba(226,248,255,.58)");
  rg.addColorStop(1,"rgba(226,248,255,0)");
  ctx.fillStyle = rg;
  ctx.fillRect(sunX-130,sunY-130,260,260);

  const horizon = height * 0.46;
  const layers = [
    {base:horizon+22,amp:92,step:170,speed:.0008,fill:"#102a35"},
    {base:horizon+48,amp:54,step:105,speed:.0014,fill:"#17343b"},
    {base:horizon+70,amp:30,step:72,speed:.0021,fill:"#1c3c3d"}
  ];
  for (let li=0; li<layers.length; li++) {
    const l=layers[li];
    const shift = -((cameraPosition*l.speed + baseCurve*26) % l.step);
    ctx.fillStyle=l.fill;
    ctx.beginPath();
    ctx.moveTo(0,height);
    ctx.lineTo(0,l.base);
    for(let x=shift-l.step;x<width+l.step;x+=l.step){
      const n=Math.abs(Math.sin((x/l.step+li*1.7)*2.73));
      ctx.lineTo(x+l.step*.25,l.base-l.amp*(.32+n*.68));
      ctx.lineTo(x+l.step*.68,l.base-l.amp*(.10+n*.26));
      ctx.lineTo(x+l.step,l.base);
    }
    ctx.lineTo(width,height);
    ctx.closePath(); ctx.fill();
  }
}

function drawPost(segment, side) {
  if (segment.index % 7 !== 0 || segment.p1.screen.w < 8) return;
  const p = segment.p1.screen;
  const edge = p.x + side * (p.w * 1.11);
  const h = Util.limit(p.w * 0.12, 2, 62);
  const w = Util.limit(p.w * 0.018, 1, 11);
  ctx.fillStyle = segment.index % 14 === 0 ? "#79e7ff" : "#d9e5e6";
  ctx.fillRect(edge - w / 2, p.y - h, w, h);
}

function drawCreature(racer, scale, x, y, clipY, player = false) {
  if (!runSheet.complete || !runSheet.naturalWidth) return;
  const frame = Math.floor(elapsed * (8.5 + racer.speed / maxSpeed * 6) + racer.frameSeed) % 6;
  const col = frame % 3;
  const row = Math.floor(frame / 3);
  const sw = runSheet.naturalWidth / 3;
  const sh = runSheet.naturalHeight / 2;
  const refScale = 0.23 / sw;
  let dw = sw * scale * width / 2 * (refScale * roadWidth);
  let dh = sh * scale * width / 2 * (refScale * roadWidth);
  const focus = player ? 1.0 : 0.88;
  dw *= focus; dh *= focus;

  if (player) {
    dw = Util.limit(dw, 190, 330);
    dh = dw * (sh / sw);
  }

  const bob = Math.sin(elapsed * 17 + racer.frameSeed) * (player ? 2.5 : Math.min(2, dw * 0.015));
  let dx = x - dw / 2;
  let dy = y - dh + bob;

  const clipH = clipY ? Math.max(0, dy + dh - clipY) : 0;
  if (clipH >= dh) return;

  ctx.save();
  ctx.globalAlpha = player ? 0.38 : 0.22;
  ctx.fillStyle = "#000";
  ctx.beginPath();
  ctx.ellipse(x, y + 2, dw * 0.31, Math.max(2, dh * 0.055), 0, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();

  const sourceH = sh * (1 - clipH / dh);
  ctx.drawImage(runSheet, col*sw, row*sh, sw, sourceH, dx, dy, dw, dh - clipH);
}

function render() {
  const s = selected();
  const baseSegment = findSegment(cameraPosition);
  const basePercent = Util.percentRemaining(cameraPosition, segmentLength);
  const playerSegment = findSegment(s.z);
  const playerPercent = Util.percentRemaining(s.z, segmentLength);
  const playerY = Util.interpolate(playerSegment.p1.world.y, playerSegment.p2.world.y, playerPercent);
  let maxy = height;
  let x = 0;
  let dx = -(baseSegment.curve * basePercent);

  drawBackdrop(baseSegment.curve, playerY);

  for (let n=0; n<drawDistance; n++) {
    const segment = segments[(baseSegment.index+n)%segments.length];
    segment.looped = segment.index < baseSegment.index;
    segment.fog = Util.exponentialFog(n/drawDistance, fogDensity);
    segment.clip = maxy;

    Util.project(segment.p1, (s.offset*roadWidth)-x, playerY+cameraHeight, cameraPosition-(segment.looped?trackLength:0));
    Util.project(segment.p2, (s.offset*roadWidth)-x-dx, playerY+cameraHeight, cameraPosition-(segment.looped?trackLength:0));

    x += dx;
    dx += segment.curve;

    if (segment.p1.camera.z <= cameraDepth ||
        segment.p2.screen.y >= segment.p1.screen.y ||
        segment.p2.screen.y >= maxy) continue;

    drawSegment(segment.p1.screen.x,segment.p1.screen.y,segment.p1.screen.w,
                segment.p2.screen.x,segment.p2.screen.y,segment.p2.screen.w,
                segment.fog,segment.color);
    maxy = segment.p1.screen.y;
  }

  for (let n=drawDistance-1; n>0; n--) {
    const segment = segments[(baseSegment.index+n)%segments.length];

    drawPost(segment,-1);
    drawPost(segment,1);

    for (const car of segment.cars) {
      const spriteScale = Util.interpolate(segment.p1.screen.scale,segment.p2.screen.scale,Util.percentRemaining(car.z,segmentLength));
      const spriteX = Util.interpolate(segment.p1.screen.x,segment.p2.screen.x,Util.percentRemaining(car.z,segmentLength)) +
        spriteScale * car.offset * roadWidth * width/2;
      const spriteY = Util.interpolate(segment.p1.screen.y,segment.p2.screen.y,Util.percentRemaining(car.z,segmentLength));
      drawCreature(car,spriteScale,spriteX,spriteY,segment.clip,false);
    }

    if (segment === playerSegment) {
      const y = (height/2) - (cameraDepth/playerZ *
        Util.interpolate(playerSegment.p1.camera.y,playerSegment.p2.camera.y,playerPercent) * height/2);
      drawCreature(s,cameraDepth/playerZ,width/2,y,null,true);
    }
  }

  const vignette = ctx.createRadialGradient(width/2,height*.58,width*.18,width/2,height*.58,width*.78);
  vignette.addColorStop(0,"rgba(0,0,0,0)");
  vignette.addColorStop(1,"rgba(0,0,0,.30)");
  ctx.fillStyle=vignette; ctx.fillRect(0,0,width,height);
}

function updateUI() {
  const s = selected();
  const m = currentRaceMeters(s);
  ui.speed.textContent = (s.speed * worldToMeters).toFixed(1) + " m/s";
  ui.distance.textContent = String(Math.floor(m)).padStart(4,"0") + " m";
  ui.rank.textContent = rankOf(s) + " / " + racers.length;
  ui.phase.textContent = s.phase;
  ui.command.textContent = s.command;
  ui.reason.textContent = s.reason;
  stage.dataset.baseZ = String(Math.floor(s.z));
  stage.dataset.rank = String(rankOf(s));
}

function frame(now) {
  const dt = Math.min(.05,(now-last)/1000);
  last = now;
  accumulator += dt;
  while (accumulator >= step) {
    updateRacers(step);
    elapsed += step;
    accumulator -= step;
  }
  updateUI();
  render();
  requestAnimationFrame(frame);
}

requestAnimationFrame(frame);
