const canvas = document.querySelector("#race");
const ctx = canvas.getContext("2d", { alpha: false });
const stage = document.querySelector("#stage");

const ui = {
  distance: document.querySelector("#distance"),
  speed: document.querySelector("#speed"),
  command: document.querySelector("#command"),
  reason: document.querySelector("#reason"),
  rank: document.querySelector("#rank"),
  phase: document.querySelector("#phase"),
  stamina: document.querySelector("#stamina"),
  road: document.querySelector("#roadState"),
  frame: document.querySelector("#frameState"),
  asset: document.querySelector("#assetState"),
  pause: document.querySelector("#pause"),
  reset: document.querySelector("#reset")
};

const BASE = import.meta.env.BASE_URL || "/";
const FPS = 60;
const STEP = 1 / FPS;
const SEGMENT_LENGTH = 180;
const ROAD_HALF_WIDTH = 1850;
const DRAW_DISTANCE = 230;
const CAMERA_HEIGHT = 980;
const FOV = 92;
const CAMERA_DEPTH = 1 / Math.tan((FOV / 2) * Math.PI / 180);
const LANES = 5;
const TRACK_METERS = 2400;
const WORLD_TO_METERS = 0.12;
const TRACK_WORLD = TRACK_METERS / WORLD_TO_METERS;
const MAX_SPEED = 22.5 / WORLD_TO_METERS;
const START_Z = 5200;
const CAMERA_TRAIL = 3450;

let width = 0;
let height = 0;
let dpr = 1;
let accumulator = 0;
let last = performance.now();
let elapsed = 0;
let cameraZ = 0;
let paused = false;
let finish = false;

const image = new Image();
image.decoding = "async";
image.onload = () => {
  stage.dataset.sSheet = "ready";
  ui.asset.textContent = "S run sheet / 6 frames ready";
};
image.onerror = () => {
  stage.dataset.sSheet = "error";
  ui.asset.textContent = "S run sheet failed";
};
image.src = BASE + "concept/s-run-sheet.webp";

function resize() {
  const rect = canvas.getBoundingClientRect();
  width = Math.max(320, rect.width);
  height = Math.max(400, rect.height);
  dpr = Math.min(2, window.devicePixelRatio || 1);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
new ResizeObserver(resize).observe(canvas);
resize();

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function lerp(a, b, t) { return a + (b - a) * t; }
function easeIn(a, b, t) { return a + (b - a) * t * t; }
function easeOut(a, b, t) { return a + (b - a) * (1 - (1 - t) * (1 - t)); }
function easeInOut(a, b, t) { return a + (b - a) * ((-Math.cos(t * Math.PI) / 2) + 0.5); }

function pseudoNoise(n) {
  const x = Math.sin(n * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
}

const segments = [];
function addSegment(curve, y) {
  const n = segments.length;
  segments.push({
    index: n,
    curve,
    p1: { world: { x: 0, y: n === 0 ? 0 : segments[n - 1].p2.world.y, z: n * SEGMENT_LENGTH }, camera: {}, screen: {} },
    p2: { world: { x: 0, y, z: (n + 1) * SEGMENT_LENGTH }, camera: {}, screen: {} }
  });
}
function addRoad(enter, hold, leave, curve, hill) {
  const startY = segments.length ? segments[segments.length - 1].p2.world.y : 0;
  const endY = startY + hill * SEGMENT_LENGTH;
  const total = enter + hold + leave;
  for (let n = 0; n < enter; n++) {
    addSegment(easeIn(0, curve, n / Math.max(1, enter)), easeInOut(startY, endY, n / total));
  }
  for (let n = 0; n < hold; n++) {
    addSegment(curve, easeInOut(startY, endY, (enter + n) / total));
  }
  for (let n = 0; n < leave; n++) {
    addSegment(easeOut(curve, 0, n / Math.max(1, leave)), easeInOut(startY, endY, (enter + hold + n) / total));
  }
}
function buildTrack() {
  segments.length = 0;
  addRoad(20, 45, 20, 0, 0);
  addRoad(18, 38, 22, 0.9, 6);
  addRoad(15, 36, 18, -1.25, -8);
  addRoad(18, 28, 18, 0.55, 10);
  addRoad(18, 42, 18, 1.6, -5);
  addRoad(16, 34, 20, -1.05, 4);
  addRoad(12, 42, 18, 0, -7);
  addRoad(18, 36, 22, 1.2, 7);
  addRoad(14, 52, 20, -1.45, 0);
  addRoad(18, 70, 18, 0.4, -3);
  addRoad(12, 100, 12, 0, 0);
}
buildTrack();
const trackLength = segments.length * SEGMENT_LENGTH;

function findSegment(z) {
  return segments[Math.floor(z / SEGMENT_LENGTH) % segments.length];
}
function project(point, cameraX, cameraY, cameraZ) {
  point.camera.x = (point.world.x || 0) - cameraX;
  point.camera.y = (point.world.y || 0) - cameraY;
  point.camera.z = (point.world.z || 0) - cameraZ;
  const z = Math.max(0.0001, point.camera.z);
  point.screen.scale = CAMERA_DEPTH / z;
  point.screen.x = Math.round((width / 2) + point.screen.scale * point.camera.x * width / 2);
  point.screen.y = Math.round((height / 2) - point.screen.scale * point.camera.y * height / 2);
  point.screen.w = Math.round(point.screen.scale * ROAD_HALF_WIDTH * width / 2);
}

const racerNames = ["Mica", "Vela", "Rook", "Nacre", "Serein", "Kite", "Flint", "Dune"];
const startOffsets = [260, 0, 180, 360, 90, 460, 220, 400];
const selectedId = 0;

function makeRacers() {
  return racerNames.map((name, i) => {
    const startZ = START_Z + startOffsets[i];
    return {
      id: i,
      name,
      lane: (i % LANES) - (LANES - 1) / 2,
      laneTarget: (i % LANES) - (LANES - 1) / 2,
      startZ,
      z: startZ,
      speed: 0,
      max: MAX_SPEED * (0.965 + pseudoNoise(i + 1) * 0.065),
      accel: 37 + pseudoNoise(i + 9) * 8,
      stamina: 100,
      seed: i * 7.31,
      cooldown: 0,
      finished: false
    };
  });
}
let racers = makeRacers();

function currentRaceMeters(r) {
  return clamp((r.z - r.startZ) * WORLD_TO_METERS, 0, TRACK_METERS);
}
function rankOf(r) {
  return [...racers].sort((a,b) => b.z - a.z).findIndex(x => x === r) + 1;
}
function selected() { return racers[selectedId]; }

function phaseFor(r) {
  const p = currentRaceMeters(r) / TRACK_METERS;
  if (p < 0.09) return "START";
  if (p < 0.64) return "MID";
  if (p < 0.84) return "BUILD";
  return "FINAL";
}

function nearestAhead(r, laneTarget = r.laneTarget) {
  let best = null;
  let gap = Infinity;
  for (const other of racers) {
    if (other === r || Math.abs(other.lane - laneTarget) > 0.5) continue;
    const d = other.z - r.z;
    if (d > 0 && d < gap) { gap = d; best = other; }
  }
  return { racer: best, gap };
}
function chooseLane(r) {
  const candidates = [];
  for (let lane = -(LANES - 1) / 2; lane <= (LANES - 1) / 2; lane++) {
    const ahead = nearestAhead(r, lane);
    const occupancy = racers.some(o => o !== r && Math.abs(o.lane - lane) < 0.55 && Math.abs(o.z - r.z) < 420);
    if (!occupancy) candidates.push({ lane, gap: ahead.gap });
  }
  candidates.sort((a,b) => b.gap - a.gap);
  return candidates[0]?.lane ?? r.laneTarget;
}

function updateRace(dt) {
  if (paused || finish) return;
  elapsed += dt;

  for (const r of racers) {
    if (r.finished) continue;

    const meters = currentRaceMeters(r);
    const p = meters / TRACK_METERS;
    const phase = phaseFor(r);
    r.cooldown = Math.max(0, r.cooldown - dt);

    let target = r.max;
    if (p < 0.07) target *= 1.04;
    else if (p > 0.82 && r.stamina > 22) target *= 1.055;

    const ahead = nearestAhead(r);
    if (ahead.gap < 520 && r.cooldown <= 0) {
      const next = chooseLane(r);
      if (next !== r.laneTarget) {
        r.laneTarget = next;
        r.cooldown = 1.0 + pseudoNoise(r.seed + elapsed) * 0.8;
      } else {
        target *= 0.91;
      }
    }

    if (r.stamina < 18) target *= 0.88;
    target += Math.sin(elapsed * 1.5 + r.seed) * 1.4;

    const accel = r.accel * dt;
    r.speed += clamp(target - r.speed, -accel * 1.8, accel);
    r.speed = Math.max(0, r.speed);
    r.z += r.speed * dt;

    const effort = Math.max(0, r.speed / r.max - 0.91);
    r.stamina = Math.max(0, r.stamina - (0.32 + 1.9 * effort * effort) * dt);
    r.lane = lerp(r.lane, r.laneTarget, clamp(dt * 4.2, 0, 1));

    if (currentRaceMeters(r) >= TRACK_METERS) r.finished = true;

    if (r === selected()) {
      if (phase === "FINAL" && r.stamina > 22) {
        ui.command.textContent = "COMMIT";
        ui.reason.textContent = "Final drive";
      } else if (ahead.gap < 520) {
        ui.command.textContent = "SHIFT / HOLD";
        ui.reason.textContent = "Traffic ahead";
      } else if (phase === "BUILD") {
        ui.command.textContent = "PRESS";
        ui.reason.textContent = "Build phase";
      } else {
        ui.command.textContent = "CRUISE";
        ui.reason.textContent = phase === "START" ? "Settle into pace" : "Maintain efficiency";
      }
    }
  }

  const leader = [...racers].sort((a,b) => b.z - a.z)[0];
  const focus = selected();
  const desiredCamera = Math.max(0, Math.min(focus.z - 2450, leader.z - 2100));
  cameraZ = lerp(cameraZ, desiredCamera, clamp(dt * 3.2, 0, 1));
  finish = racers.every(r => r.finished);
}

function polygon(color, ...pts) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(pts[0], pts[1]);
  for (let i = 2; i < pts.length; i += 2) ctx.lineTo(pts[i], pts[i + 1]);
  ctx.closePath();
  ctx.fill();
}

function drawSky(curveAccum, horizon) {
  const grad = ctx.createLinearGradient(0, 0, 0, horizon + 120);
  grad.addColorStop(0, "#071523");
  grad.addColorStop(0.52, "#1a4057");
  grad.addColorStop(1, "#8aa5a8");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, width, height);

  const sunX = width * 0.73 - curveAccum * 34;
  const sunY = horizon * 0.34;
  const rg = ctx.createRadialGradient(sunX, sunY, 2, sunX, sunY, 110);
  rg.addColorStop(0, "rgba(225,246,255,.62)");
  rg.addColorStop(1, "rgba(225,246,255,0)");
  ctx.fillStyle = rg;
  ctx.fillRect(sunX - 120, sunY - 120, 240, 240);

  const layers = [
    { y: horizon * 0.73, amp: 62, step: 110, speed: 0.13, color: "#112b36" },
    { y: horizon * 0.88, amp: 38, step: 74, speed: 0.23, color: "#17333b" },
    { y: horizon * 0.98, amp: 18, step: 42, speed: 0.36, color: "#1b3d40" }
  ];
  for (const [li, layer] of layers.entries()) {
    const shift = -(cameraZ * layer.speed * 0.015 + curveAccum * 45) % layer.step;
    ctx.fillStyle = layer.color;
    ctx.beginPath();
    ctx.moveTo(0, height);
    ctx.lineTo(0, layer.y);
    for (let x = shift - layer.step; x < width + layer.step; x += layer.step) {
      const n = pseudoNoise(Math.floor((x - shift) / layer.step) + li * 33);
      ctx.lineTo(x + layer.step * 0.25, layer.y - layer.amp * (0.35 + n * 0.65));
      ctx.lineTo(x + layer.step * 0.70, layer.y - layer.amp * (0.12 + n * 0.28));
      ctx.lineTo(x + layer.step, layer.y);
    }
    ctx.lineTo(width, height);
    ctx.closePath();
    ctx.fill();
  }
}

function roadPalette(index) {
  const band = Math.floor(index / 3) % 2;
  return {
    terrain: band ? "#334434" : "#304031",
    road: band ? "#4b5157" : "#454a50",
    edge: band ? "#dce9e8" : "#24313a",
    lane: "#c5d3d2"
  };
}

function drawRoad() {
  const base = findSegment(cameraZ);
  const basePercent = (cameraZ % SEGMENT_LENGTH) / SEGMENT_LENGTH;
  const playerSeg = findSegment(selected().z);
  const playerPercent = (selected().z % SEGMENT_LENGTH) / SEGMENT_LENGTH;
  const playerY = lerp(playerSeg.p1.world.y, playerSeg.p2.world.y, playerPercent);

  let x = 0;
  let dx = -(base.curve * basePercent);
  let maxY = height;
  let curveAccum = 0;
  const visible = [];

  for (let n = 0; n < DRAW_DISTANCE; n++) {
    const seg = segments[(base.index + n) % segments.length];
    seg.looped = seg.index < base.index;
    const cameraZForSegment = cameraZ - (seg.looped ? trackLength : 0);
    project(seg.p1, x, CAMERA_HEIGHT + playerY, cameraZForSegment);
    project(seg.p2, x + dx, CAMERA_HEIGHT + playerY, cameraZForSegment);
    x += dx;
    dx += seg.curve;
    curveAccum += seg.curve;

    if (seg.p1.camera.z <= CAMERA_DEPTH || seg.p2.screen.y >= maxY) continue;
    visible.push(seg);
    maxY = seg.p2.screen.y;
  }

  const horizon = visible.length ? visible[visible.length - 1].p2.screen.y : height * 0.38;
  drawSky(curveAccum / Math.max(1, visible.length), horizon);

  for (let i = visible.length - 1; i >= 0; i--) {
    const seg = visible[i];
    const p1 = seg.p1.screen;
    const p2 = seg.p2.screen;
    const c = roadPalette(seg.index);

    ctx.fillStyle = c.terrain;
    ctx.fillRect(0, p2.y, width, Math.max(0, p1.y - p2.y));

    const edge1 = p1.w / Math.max(8, LANES * 1.8);
    const edge2 = p2.w / Math.max(8, LANES * 1.8);

    polygon(c.edge,
      p1.x - p1.w - edge1, p1.y,
      p1.x - p1.w, p1.y,
      p2.x - p2.w, p2.y,
      p2.x - p2.w - edge2, p2.y
    );
    polygon(c.edge,
      p1.x + p1.w + edge1, p1.y,
      p1.x + p1.w, p1.y,
      p2.x + p2.w, p2.y,
      p2.x + p2.w + edge2, p2.y
    );
    polygon(c.road,
      p1.x - p1.w, p1.y,
      p1.x + p1.w, p1.y,
      p2.x + p2.w, p2.y,
      p2.x - p2.w, p2.y
    );

    if ((seg.index % 5) < 3) {
      const lw1 = p1.w * 0.011;
      const lw2 = p2.w * 0.011;
      for (let lane = 1; lane < LANES; lane++) {
        const t = lane / LANES;
        const lx1 = lerp(p1.x - p1.w, p1.x + p1.w, t);
        const lx2 = lerp(p2.x - p2.w, p2.x + p2.w, t);
        polygon("rgba(219,232,232,.42)",
          lx1 - lw1, p1.y,
          lx1 + lw1, p1.y,
          lx2 + lw2, p2.y,
          lx2 - lw2, p2.y
        );
      }
    }

    if (seg.index % 5 === 0) {
      drawRoadsideMarker(p1, p2, -1, seg.index);
      drawRoadsideMarker(p1, p2, 1, seg.index);
    }
  }

  return { base, horizon };
}

function drawRoadsideMarker(p1, p2, side, index) {
  const near = p1.w > p2.w ? p1 : p2;
  const far = near === p1 ? p2 : p1;
  const sideX = near.x + side * (near.w * 1.13);
  const farX = far.x + side * (far.w * 1.13);
  const h = clamp(near.w * 0.11, 2, 80);
  const fw = clamp(near.w * 0.018, 1, 16);

  ctx.strokeStyle = index % 10 === 0 ? "rgba(121,231,255,.9)" : "rgba(214,226,226,.58)";
  ctx.lineWidth = fw;
  ctx.beginPath();
  ctx.moveTo(sideX, near.y);
  ctx.lineTo(farX, far.y - h * 0.10);
  ctx.stroke();

  if (h > 18) {
    ctx.fillStyle = index % 10 === 0 ? "#79e7ff" : "#dce8e6";
    ctx.fillRect(sideX - fw * 0.6, near.y - h, fw * 1.2, h);
  }
}

function screenForRacer(r) {
  const seg = findSegment(r.z);
  const percent = (r.z % SEGMENT_LENGTH) / SEGMENT_LENGTH;
  const y = lerp(seg.p1.screen.y || height, seg.p2.screen.y || height, percent);
  const xCenter = lerp(seg.p1.screen.x || width / 2, seg.p2.screen.x || width / 2, percent);
  const roadW = lerp(seg.p1.screen.w || 0, seg.p2.screen.w || 0, percent);
  const laneNorm = r.lane / ((LANES - 1) / 2 || 1);
  return { x: xCenter + laneNorm * roadW * 0.66, y, roadW, scale: roadW / ROAD_HALF_WIDTH };
}

function drawRacer(r, nowSec) {
  if (!image.complete || !image.naturalWidth) return;
  const s = screenForRacer(r);
  if (s.y < 0 || s.y > height + 60 || s.roadW < 5) return;

  const frame = Math.floor(nowSec * (9.5 + r.speed / MAX_SPEED * 5) + r.id * 0.77) % 6;
  const col = frame % 3;
  const row = Math.floor(frame / 3);
  const sw = image.naturalWidth / 3;
  const sh = image.naturalHeight / 2;

  const perspective = clamp(s.roadW / (width * 0.44), 0.11, 1.7);
  const focus = r.id === selectedId ? 1.12 : 0.96;
  const dw = clamp(205 * perspective * focus, 22, 260);
  const dh = dw * (sh / sw);

  const speedPulse = 1 + Math.sin(nowSec * 12 + r.id) * 0.018;
  const bob = Math.sin(nowSec * 17 + r.id * 0.8) * Math.min(2.4, perspective * 2.0);

  ctx.save();
  ctx.translate(s.x, s.y + bob);
  ctx.scale(speedPulse, 1 / speedPulse);

  const shadowW = dw * 0.58;
  const shadowH = dh * 0.10;
  const sg = ctx.createRadialGradient(0, -shadowH * .1, 1, 0, 0, shadowW * .5);
  sg.addColorStop(0, "rgba(0,0,0,.50)");
  sg.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = sg;
  ctx.beginPath();
  ctx.ellipse(0, 1, shadowW * .5, shadowH, 0, 0, Math.PI * 2);
  ctx.fill();

  if (r.id === selectedId) {
    const markerY = -dh - clamp(7 * perspective, 4, 9);
    ctx.fillStyle = "rgba(121,231,255,.92)";
    ctx.beginPath();
    ctx.moveTo(0, markerY + 6);
    ctx.lineTo(-5, markerY - 2);
    ctx.lineTo(5, markerY - 2);
    ctx.closePath();
    ctx.fill();
    ctx.globalAlpha = 0.72;
    ctx.strokeStyle = "#79e7ff";
    ctx.lineWidth = Math.max(1, 1.4 * perspective);
    ctx.beginPath();
    ctx.moveTo(-dw * 0.28, 2);
    ctx.lineTo(dw * 0.28, 2);
    ctx.stroke();
    ctx.globalAlpha = 1;
  }

  ctx.drawImage(image, col * sw, row * sh, sw, sh, -dw / 2, -dh, dw, dh);
  ctx.restore();

  if (r.id === selectedId) ui.frame.textContent = `${frame + 1} / 6`;
}

function drawRacers(nowSec) {
  const drawList = racers
    .map(r => ({ r, s: screenForRacer(r) }))
    .filter(o => o.s.y >= -80 && o.s.y <= height + 80 && o.s.roadW > 4)
    .sort((a,b) => a.s.y - b.s.y);
  for (const o of drawList) drawRacer(o.r, nowSec);
}

function drawSpeedFX() {
  const focus = selected();
  const ratio = clamp(focus.speed / MAX_SPEED, 0, 1);
  if (ratio < 0.45) return;

  const intensity = (ratio - 0.45) / 0.55;
  ctx.save();
  ctx.globalAlpha = intensity * 0.20;
  ctx.strokeStyle = "#d8f7ff";
  ctx.lineCap = "round";

  const count = Math.floor(14 + intensity * 34);
  for (let i = 0; i < count; i++) {
    const seed = i * 11.7 + Math.floor(elapsed * 9);
    const y = (pseudoNoise(seed) * height);
    const side = i % 2 ? 1 : -1;
    const x0 = side < 0 ? pseudoNoise(seed + 2) * width * 0.22 : width - pseudoNoise(seed + 2) * width * 0.22;
    const len = 15 + pseudoNoise(seed + 5) * 90 * intensity;
    ctx.lineWidth = 0.6 + pseudoNoise(seed + 8) * 1.6;
    ctx.beginPath();
    ctx.moveTo(x0, y);
    ctx.lineTo(x0 + side * len, y + (pseudoNoise(seed + 1) - .5) * 4);
    ctx.stroke();
  }
  ctx.restore();

  if (intensity > 0.45) {
    const shake = (intensity - 0.45) * 1.7;
    stage.style.transform = `translate(${Math.sin(elapsed * 45) * shake}px,${Math.cos(elapsed * 37) * shake * .55}px)`;
  } else {
    stage.style.transform = "";
  }
}

function updateUI() {
  const r = selected();
  const meters = currentRaceMeters(r);
  ui.distance.textContent = String(Math.floor(meters)).padStart(4, "0") + " m";
  ui.speed.textContent = (r.speed * WORLD_TO_METERS).toFixed(1);
  ui.rank.textContent = `${rankOf(r)} / ${racers.length}`;
  ui.phase.textContent = phaseFor(r);
  ui.stamina.textContent = Math.round(r.stamina);

  const seg = findSegment(r.z);
  const curve = seg.curve;
  ui.road.textContent = Math.abs(curve) < 0.18 ? "STRAIGHT" : curve > 0 ? "RIGHT" : "LEFT";
}

function render() {
  ctx.save();
  const r = selected();
  const ratio = clamp(r.speed / MAX_SPEED, 0, 1);
  const zoom = 1 + ratio * 0.025;
  ctx.translate(width / 2, height / 2);
  ctx.scale(zoom, zoom);
  ctx.translate(-width / 2, -height / 2);

  drawRoad();
  drawRacers(elapsed);
  drawSpeedFX();

  ctx.restore();

  const vignette = ctx.createRadialGradient(width / 2, height * .55, width * .16, width / 2, height * .55, width * .74);
  vignette.addColorStop(0, "rgba(0,0,0,0)");
  vignette.addColorStop(1, "rgba(0,0,0,.38)");
  ctx.fillStyle = vignette;
  ctx.fillRect(0,0,width,height);
}

function frame(now) {
  const dt = Math.min(0.05, (now - last) / 1000);
  last = now;
  accumulator += dt;
  while (accumulator >= STEP) {
    updateRace(STEP);
    accumulator -= STEP;
  }
  updateUI();
  render();
  stage.dataset.lane4 = image.complete && image.naturalWidth ? "running" : "loading";
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

ui.pause.addEventListener("click", () => {
  paused = !paused;
  ui.pause.textContent = paused ? "RESUME" : "PAUSE";
});
ui.reset.addEventListener("click", () => {
  racers = makeRacers();
  elapsed = 0;
  cameraZ = 0;
  finish = false;
  paused = false;
  ui.pause.textContent = "PAUSE";
  stage.style.transform = "";
});
