const canvas = document.querySelector("#raceCanvas");
const ctx = canvas.getContext("2d", { alpha: false, desynchronized: true });
const stage = document.querySelector("#stage");

const ui = {
  rank: document.querySelector("#rank"),
  speed: document.querySelector("#speed"),
  command: document.querySelector("#command"),
  reason: document.querySelector("#reason"),
  countdown: document.querySelector("#countdown"),
  distance: document.querySelector("#distance"),
  clock: document.querySelector("#clock"),
  progress: document.querySelector("#progress"),
  ranking: document.querySelector("#ranking"),
  pause: document.querySelector("#pause"),
  reset: document.querySelector("#reset"),
  assetStatus: document.querySelector("#assetStatus")
};

const BASE = import.meta.env.BASE_URL || "/";
const FIELD_SIZE = 8;
const SELECTED_ID = 1;
const METERS_PER_SEGMENT = 4;
const SEGMENT_LENGTH = 180;
const WORLD_PER_METER = SEGMENT_LENGTH / METERS_PER_SEGMENT;
const ROAD_WIDTH = 1850;
const CAMERA_HEIGHT = 860;
const DRAW_DISTANCE = 220;
const BASE_FOV = 88;
const RACE_METERS = 1440;
const START_PAD_METERS = 44;
const TRACK_METERS = RACE_METERS + START_PAD_METERS + 12;
const LANES = [0.04, -0.20, 0.26, -0.42, 0.48, -0.62, 0.68, -0.02];

const S_FRAMES = [
  { phase: "CONTACT", col: 0, row: 0, y: 0.00 },
  { phase: "PUSH",    col: 1, row: 0, y: 0.00 },
  { phase: "LIFT",    col: 2, row: 0, y: 0.00 },
  { phase: "FLIGHT",  col: 0, row: 1, y: -0.42 },
  { phase: "REACH",   col: 1, row: 1, y: -0.17 },
  { phase: "LAND",    col: 2, row: 1, y: -0.16 }
];

const racerNames = ["Mica", "Vela", "Rook", "Serein", "Flint", "Nacre", "Ilex", "Sora"];

let width = 1;
let height = 1;
let dpr = 1;
let fov = BASE_FOV;
let cameraDepth = 1 / Math.tan((fov * 0.5) * Math.PI / 180);
let cameraX = 0;
let cameraXTarget = 0;
let elapsed = 0;
let paused = false;
let last = performance.now();
let countdownRemaining = 2500;
let raceState = "countdown";
let finishCounter = 0;
let frameCounter = 0;
let lastRankingPaint = 0;

const spriteSheet = new Image();
spriteSheet.decoding = "async";
spriteSheet.onload = () => {
  stage.dataset.sRunSheet = "ready";
  ui.assetStatus.textContent = "S run cycle ready";
};
spriteSheet.onerror = () => {
  stage.dataset.sRunSheet = "error";
  ui.assetStatus.textContent = "S run cycle failed to load";
};
spriteSheet.src = BASE + "concept/s-run-sheet.webp";

function resize() {
  const rect = canvas.getBoundingClientRect();
  width = Math.max(320, Math.floor(rect.width));
  height = Math.max(420, Math.floor(rect.height));
  dpr = Math.min(window.devicePixelRatio || 1, 1.65);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
new ResizeObserver(resize).observe(canvas);
resize();

const segments = [];

const easeIn = (a, b, p) => a + (b - a) * p * p;
const easeOut = (a, b, p) => a + (b - a) * (1 - Math.pow(1 - p, 2));
const easeInOut = (a, b, p) => a + (b - a) * ((-Math.cos(p * Math.PI) / 2) + 0.5);
const lerp = (a, b, p) => a + (b - a) * p;
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

function lastY() {
  return segments.length ? segments[segments.length - 1].p2.world.y : 0;
}

function addSegment(curve, y) {
  const n = segments.length;
  const prevY = lastY();
  segments.push({
    index: n,
    curve,
    p1: { world: { x: 0, y: prevY, z: n * SEGMENT_LENGTH }, camera: {}, screen: {} },
    p2: { world: { x: 0, y, z: (n + 1) * SEGMENT_LENGTH }, camera: {}, screen: {} },
    clip: height,
    looped: false
  });
}

function addRoad(enter, hold, leave, curve, hill) {
  const startY = lastY();
  const total = enter + hold + leave;
  const endY = startY + hill;

  for (let n = 0; n < enter; n++) {
    addSegment(
      easeIn(0, curve, n / Math.max(1, enter)),
      easeInOut(startY, endY, n / Math.max(1, total))
    );
  }
  for (let n = 0; n < hold; n++) {
    addSegment(
      curve,
      easeInOut(startY, endY, (enter + n) / Math.max(1, total))
    );
  }
  for (let n = 0; n < leave; n++) {
    addSegment(
      easeOut(curve, 0, n / Math.max(1, leave)),
      easeInOut(startY, endY, (enter + hold + n) / Math.max(1, total))
    );
  }
}

function buildTrack() {
  segments.length = 0;
  addRoad(10, 24, 10, 0.0, 0);
  addRoad(14, 28, 16, 0.72, 2200);
  addRoad(10, 18, 10, 0.28, 1800);
  addRoad(8, 18, 10, 0.0, -900);
  addRoad(16, 34, 18, -0.92, -3200);
  addRoad(10, 18, 10, 0.0, -900);
  addRoad(12, 22, 12, 0.64, 1200);
  addRoad(10, 18, 10, -0.52, 700);
  addRoad(10, 30, 10, 0.0, 0);
  const targetSegments = Math.ceil(TRACK_METERS / METERS_PER_SEGMENT);
  while (segments.length < targetSegments) addSegment(0, lastY());
  if (segments.length > targetSegments) {
    segments.length = targetSegments;
  }
}
buildTrack();

const TRACK_LENGTH = segments.length * SEGMENT_LENGTH;

function findSegmentByWorld(z) {
  return segments[Math.floor(z / SEGMENT_LENGTH) % segments.length];
}

function project(point, cameraOffsetX, cameraY, cameraZ) {
  point.camera.x = (point.world.x || 0) - cameraOffsetX;
  point.camera.y = point.world.y - cameraY;
  point.camera.z = point.world.z - cameraZ;

  const safeZ = Math.max(0.0001, point.camera.z);
  point.screen.scale = cameraDepth / safeZ;
  point.screen.x = Math.round((width / 2) + point.screen.scale * point.camera.x * width / 2);
  point.screen.y = Math.round((height / 2) - point.screen.scale * point.camera.y * height / 2);
  point.screen.w = Math.round(point.screen.scale * ROAD_WIDTH * width / 2);
}

function percentRemaining(n, total) {
  return (n % total) / total;
}

function polygon(points, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.moveTo(points[0][0], points[0][1]);
  for (let i = 1; i < points.length; i++) ctx.lineTo(points[i][0], points[i][1]);
  ctx.closePath();
  ctx.fill();
}

function drawMountainBand(horizon, amplitude, period, shift, fill, baseOffset) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.moveTo(0, height);
  ctx.lineTo(0, horizon + baseOffset);
  for (let x = -period; x <= width + period; x += period / 2) {
    const worldX = x + shift;
    const p = Math.abs(Math.sin(worldX * 0.0067)) * 0.65 + Math.abs(Math.sin(worldX * 0.013)) * 0.35;
    ctx.lineTo(x, horizon + baseOffset - amplitude * (0.25 + p * 0.75));
    ctx.lineTo(x + period * 0.24, horizon + baseOffset - amplitude * 0.14);
  }
  ctx.lineTo(width, height);
  ctx.closePath();
  ctx.fill();
}

function drawBackground(cameraMeters, baseCurve, horizon) {
  const sky = ctx.createLinearGradient(0, 0, 0, Math.max(horizon + 80, height * 0.6));
  sky.addColorStop(0, "#78a9c3");
  sky.addColorStop(0.55, "#bdd0cf");
  sky.addColorStop(1, "#e2c89c");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, width, height);

  const sunX = width * 0.77;
  const sunY = height * 0.18;
  const sunR = Math.max(34, width * 0.028);
  const glow = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR * 2.8);
  glow.addColorStop(0, "rgba(255,242,201,.88)");
  glow.addColorStop(1, "rgba(255,242,201,0)");
  ctx.fillStyle = glow;
  ctx.fillRect(sunX - sunR * 3, sunY - sunR * 3, sunR * 6, sunR * 6);

  const shift = cameraMeters * 0.9 + baseCurve * width * 42;
  drawMountainBand(horizon + 12, 84, 240, shift * 0.20, "#78909a", 0);
  drawMountainBand(horizon + 20, 62, 190, shift * 0.38, "#687f78", 10);
  drawMountainBand(horizon + 28, 40, 148, shift * 0.62, "#536c58", 18);

  const grass = ctx.createLinearGradient(0, horizon, 0, height);
  grass.addColorStop(0, "#55794e");
  grass.addColorStop(1, "#263f2d");
  ctx.fillStyle = grass;
  ctx.fillRect(0, horizon, width, height - horizon);

  // Horizontal field bands make forward motion legible even when the road is straight.
  for (let i = 0; i < 7; i++) {
    const y = horizon + (height - horizon) * (0.12 + i * 0.13);
    ctx.fillStyle = `rgba(207,226,177,${0.018 + i * 0.007})`;
    ctx.fillRect(0, y, width, Math.max(1, (i + 1) * 0.8));
  }

  // Mid-distance tree line; deliberately procedural so it remains free and lightweight.
  const treeShift = ((cameraMeters * 2.4 + baseCurve * 160) % 92 + 92) % 92;
  for (let x = -110 - treeShift; x < width + 110; x += 46) {
    const variant = Math.abs(Math.sin((x + cameraMeters) * 0.031));
    const treeH = 18 + variant * 28;
    const treeY = horizon + 8 + variant * 8;
    ctx.fillStyle = "rgba(43,70,51,.72)";
    ctx.fillRect(x - 2, treeY - treeH * 0.08, 4, treeH * 0.34);
    ctx.beginPath();
    ctx.moveTo(x, treeY - treeH);
    ctx.lineTo(x - treeH * 0.38, treeY);
    ctx.lineTo(x + treeH * 0.38, treeY);
    ctx.closePath();
    ctx.fill();
  }
}

function drawRoadSegment(seg, indexInView) {
  const p1 = seg.p1.screen;
  const p2 = seg.p2.screen;
  if (p1.y <= p2.y || p2.y >= height + 80 || p1.y < 0) return;

  const alt = Math.floor(seg.index / 3) % 2 === 0;
  const road = alt ? "#4a5156" : "#43494e";
  const shoulder = alt ? "#b8a17f" : "#9c8a6f";
  const curb = Math.floor(seg.index / 2) % 2 === 0 ? "#d9e3e6" : "#b85d51";

  const rumble1 = Math.max(2, p1.w * 0.075);
  const rumble2 = Math.max(1, p2.w * 0.075);

  polygon([
    [p1.x - p1.w - rumble1, p1.y],
    [p1.x + p1.w + rumble1, p1.y],
    [p2.x + p2.w + rumble2, p2.y],
    [p2.x - p2.w - rumble2, p2.y]
  ], shoulder);

  polygon([
    [p1.x - p1.w - rumble1, p1.y],
    [p1.x - p1.w, p1.y],
    [p2.x - p2.w, p2.y],
    [p2.x - p2.w - rumble2, p2.y]
  ], curb);

  polygon([
    [p1.x + p1.w, p1.y],
    [p1.x + p1.w + rumble1, p1.y],
    [p2.x + p2.w + rumble2, p2.y],
    [p2.x + p2.w, p2.y]
  ], curb);

  polygon([
    [p1.x - p1.w, p1.y],
    [p1.x + p1.w, p1.y],
    [p2.x + p2.w, p2.y],
    [p2.x - p2.w, p2.y]
  ], road);

  if (seg.index % 6 < 3) {
    for (let lane = 1; lane < 4; lane++) {
      const lane1 = lerp(p1.x - p1.w, p1.x + p1.w, lane / 4);
      const lane2 = lerp(p2.x - p2.w, p2.x + p2.w, lane / 4);
      const lw1 = Math.max(1, p1.w * 0.004);
      const lw2 = Math.max(1, p2.w * 0.004);
      polygon([
        [lane1 - lw1, p1.y],
        [lane1 + lw1, p1.y],
        [lane2 + lw2, p2.y],
        [lane2 - lw2, p2.y]
      ], "rgba(232,238,239,.26)");
    }
  }

  if (seg.index % 8 === 0 && indexInView < 120) {
    const postH = clamp(p1.screenScaleForPost || p1.w * 0.16, 4, 96);
    const postW = clamp(postH * 0.16, 2, 10);
    const leftX = p1.x - p1.w - rumble1 - postW * 2;
    const rightX = p1.x + p1.w + rumble1 + postW * 2;
    ctx.fillStyle = "rgba(231,241,236,.8)";
    ctx.fillRect(leftX - postW / 2, p1.y - postH, postW, postH);
    ctx.fillRect(rightX - postW / 2, p1.y - postH, postW, postH);
    ctx.fillStyle = "rgba(43,66,56,.9)";
    ctx.fillRect(leftX - postW * 1.8, p1.y - postH, postW * 3.6, Math.max(2, postH * 0.12));
    ctx.fillRect(rightX - postW * 1.8, p1.y - postH, postW * 3.6, Math.max(2, postH * 0.12));
  }

  // Larger roadside silhouettes are a near-field speed reference, not decoration.
  if (seg.index % 18 === 5 && indexInView < 88) {
    const treeH = clamp(p1.w * 0.34, 8, 170);
    const treeW = treeH * 0.48;
    for (const side of [-1, 1]) {
      const tx = p1.x + side * (p1.w + rumble1 + treeW * 0.95);
      const ty = p1.y;
      ctx.fillStyle = "rgba(48,57,42,.92)";
      ctx.fillRect(tx - treeW * 0.07, ty - treeH * 0.28, treeW * 0.14, treeH * 0.28);
      ctx.fillStyle = side < 0 ? "#31543c" : "#294a36";
      ctx.beginPath();
      ctx.moveTo(tx, ty - treeH);
      ctx.lineTo(tx - treeW, ty - treeH * 0.18);
      ctx.lineTo(tx + treeW, ty - treeH * 0.18);
      ctx.closePath();
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(tx, ty - treeH * 0.76);
      ctx.lineTo(tx - treeW * 0.82, ty);
      ctx.lineTo(tx + treeW * 0.82, ty);
      ctx.closePath();
      ctx.fill();
    }
  }
}

function makeRacers() {
  return Array.from({ length: FIELD_SIZE }, (_, i) => ({
    id: i + 1,
    name: racerNames[i],
    distance: 2.5 * i,
    speed: 0,
    cruise: 21.7 + ((i * 7) % 5) * 0.22,
    accel: 5.2 + (i % 3) * 0.22,
    stamina: 100,
    lane: LANES[i],
    targetLane: LANES[i],
    phaseOffset: i * 0.83,
    cooldown: 0,
    command: "HOLD FORM",
    reason: "Pre-start",
    finished: false,
    finishPlace: 0,
    finishTime: 0
  }));
}

let racers = makeRacers();

function selected() {
  return racers.find((r) => r.id === SELECTED_ID);
}

function ranking() {
  return [...racers].sort((a, b) => {
    if (a.finished && b.finished) return a.finishPlace - b.finishPlace;
    if (a.finished) return -1;
    if (b.finished) return 1;
    return b.distance - a.distance;
  });
}

function rankOf(r) {
  return ranking().findIndex((x) => x === r) + 1;
}

function gapAhead(r, laneTolerance = 0.18) {
  let best = Infinity;
  for (const other of racers) {
    if (other === r || other.finished) continue;
    if (Math.abs(other.lane - r.lane) > laneTolerance) continue;
    const gap = other.distance - r.distance;
    if (gap > 0 && gap < best) best = gap;
  }
  return best;
}

function laneClear(r, lane) {
  return racers.every((other) =>
    other === r ||
    other.finished ||
    Math.abs(other.lane - lane) > 0.15 ||
    Math.abs(other.distance - r.distance) > 10
  );
}

function chooseLane(r) {
  const candidates = [-0.62, -0.42, -0.20, 0.04, 0.26, 0.48, 0.68]
    .filter((lane) => laneClear(r, lane))
    .sort((a, b) => Math.abs(a - r.lane) - Math.abs(b - r.lane));
  return candidates[0] ?? r.lane;
}

function targetSpeedFor(r) {
  const p = r.distance / RACE_METERS;
  let target = r.cruise;
  if (p < 0.13) target *= 1.045;
  else if (p < 0.72) target *= 1.005;
  else if (p < 0.88) target *= 1.025;
  else target *= 1.075;

  const gap = gapAhead(r);
  if (gap < 8 && r.cooldown <= 0) {
    const lane = chooseLane(r);
    if (Math.abs(lane - r.lane) > 0.05) {
      r.targetLane = lane;
      r.cooldown = 1300;
      r.command = "SHIFT OUT";
      r.reason = "Traffic ahead";
      target *= 1.018;
    } else {
      target *= clamp(gap / 8, 0.78, 0.98);
      r.command = "HOLD GAP";
      r.reason = "No clean line";
    }
  } else if (p > 0.88 && r.stamina > 24) {
    r.command = "COMMIT";
    r.reason = "Final drive";
  } else if (p > 0.70) {
    r.command = "PRESS";
    r.reason = "Build phase";
  } else {
    r.command = "HOLD FORM";
    r.reason = "Efficient pace";
  }

  if (r.stamina < 18) {
    target *= 0.88;
    r.command = "PRESERVE";
    r.reason = "Low stamina";
  }

  return target * (0.82 + 0.18 * (r.stamina / 100));
}

function updateRace(dtMs) {
  if (paused) return;
  const dt = Math.min(50, dtMs) / 1000;

  if (raceState === "countdown") {
    countdownRemaining -= dtMs;
    const n = Math.ceil(countdownRemaining / 800);
    ui.countdown.hidden = false;
    ui.countdown.classList.remove("go");
    ui.countdown.textContent = n > 0 ? String(n) : "GO";

    if (countdownRemaining <= 0) {
      raceState = "running";
      stage.dataset.raceState = "running";
      ui.countdown.textContent = "GO";
      ui.countdown.classList.add("go");
    }
    return;
  }

  if (raceState !== "running") return;

  elapsed += dtMs;

  if (elapsed > 650) ui.countdown.hidden = true;

  for (const r of racers) {
    if (r.finished) continue;

    r.cooldown = Math.max(0, r.cooldown - dtMs);

    let target = targetSpeedFor(r);
    target += Math.sin(elapsed * 0.0014 + r.id * 1.73) * 0.18;

    const diff = target - r.speed;
    const maxStep = r.accel * dt * (diff >= 0 ? 1 : 1.5);
    r.speed += clamp(diff, -maxStep, maxStep);

    r.lane = lerp(r.lane, r.targetLane, Math.min(1, dt * 2.25));

    const effort = Math.max(0, r.speed / r.cruise - 0.95);
    r.stamina = Math.max(0, r.stamina - (0.65 + effort * effort * 4.4) * dt);
    r.distance += Math.max(0, r.speed) * dt;

    if (r.distance >= RACE_METERS) {
      r.distance = RACE_METERS;
      r.finished = true;
      r.finishPlace = ++finishCounter;
      r.finishTime = elapsed;
      r.speed *= 0.96;
    }
  }

  if (finishCounter === racers.length) {
    raceState = "finished";
    stage.dataset.raceState = "finished";
  }
}

function renderWorld() {
  const focus = selected();
  const speedNorm = clamp(focus.speed / 24.5, 0, 1);
  fov = BASE_FOV + speedNorm * 8;
  cameraDepth = 1 / Math.tan((fov * 0.5) * Math.PI / 180);

  const followDistance = width < 700 ? 34 : 28;
  const focusWorldMeters = focus.distance + START_PAD_METERS;
  const cameraMeters = clamp(focusWorldMeters - followDistance, 0, TRACK_METERS - 0.1);
  const cameraZ = cameraMeters * WORLD_PER_METER;
  const baseSegment = findSegmentByWorld(cameraZ);
  const baseIndex = baseSegment.index;
  const basePercent = percentRemaining(cameraZ, SEGMENT_LENGTH);
  const cameraY = lerp(baseSegment.p1.world.y, baseSegment.p2.world.y, basePercent) + CAMERA_HEIGHT;

  cameraXTarget = focus.lane * ROAD_WIDTH * 0.66;
  cameraX = lerp(cameraX, cameraXTarget, 0.055 + speedNorm * 0.035);

  let x = 0;
  let dx = -(baseSegment.curve * basePercent);
  let horizon = Math.round(height * 0.43);
  const visible = [];

  for (let n = 0; n < DRAW_DISTANCE; n++) {
    const seg = segments[(baseIndex + n) % segments.length];
    seg.looped = seg.index < baseIndex;
    const cameraWrapZ = cameraZ - (seg.looped ? TRACK_LENGTH : 0);

    project(seg.p1, cameraX - x, cameraY, cameraWrapZ);
    project(seg.p2, cameraX - x - dx, cameraY, cameraWrapZ);

    x += dx;
    dx += seg.curve;

    if (seg.p1.camera.z <= cameraDepth) continue;
    if (seg.p2.screen.y >= seg.p1.screen.y) continue;

    seg.clip = height;
    visible.push({ seg, n });
    if (n > DRAW_DISTANCE * 0.72) horizon = Math.min(horizon, seg.p2.screen.y);
  }

  horizon = clamp(horizon, height * 0.30, height * 0.56);

  const shakeAmp = speedNorm > 0.72 ? (speedNorm - 0.72) * 5.2 : 0;
  const shakeX = Math.sin(elapsed * 0.037) * shakeAmp;
  const shakeY = Math.sin(elapsed * 0.049 + 1.4) * shakeAmp * 0.42;
  const roll = clamp(baseSegment.curve * speedNorm * 0.0048, -0.008, 0.008);

  ctx.save();
  ctx.translate(width / 2 + shakeX, height / 2 + shakeY);
  ctx.rotate(roll);
  ctx.translate(-width / 2, -height / 2);

  drawBackground(cameraMeters, baseSegment.curve, horizon);

  for (let i = visible.length - 1; i >= 0; i--) {
    drawRoadSegment(visible[i].seg, visible[i].n);
  }

  drawTracksideMotion(visible, speedNorm);
  drawRacers(cameraZ, baseIndex, speedNorm);

  ctx.restore();

  drawSpeedOverlay(speedNorm);
}

function drawTracksideMotion(visible, speedNorm) {
  if (speedNorm < 0.48) return;
  ctx.save();
  ctx.globalAlpha = (speedNorm - 0.48) * 0.5;
  ctx.strokeStyle = "rgba(235,246,248,.38)";
  ctx.lineWidth = 1.2;
  const count = width < 700 ? 7 : 12;

  for (let i = 0; i < count; i++) {
    const side = i % 2 ? -1 : 1;
    const y = height * (0.66 + ((i * 37) % 31) / 100);
    const length = 42 + speedNorm * 95 + (i % 4) * 18;
    const x = side < 0 ? width * 0.04 + (i % 3) * 18 : width * 0.96 - (i % 3) * 18;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x - side * length, y - 2 - (i % 2) * 3);
    ctx.stroke();
  }
  ctx.restore();
}

function projectRacer(racer, cameraZ) {
  const racerMeters = Math.min(racer.distance, RACE_METERS - 0.001) + START_PAD_METERS;
  const racerZ = racerMeters * WORLD_PER_METER;
  const dz = racerZ - cameraZ;
  if (dz < SEGMENT_LENGTH * 0.35 || dz > DRAW_DISTANCE * SEGMENT_LENGTH) return null;

  const seg = findSegmentByWorld(racerZ);
  if (!seg?.p1?.screen || !seg?.p2?.screen) return null;

  const percent = percentRemaining(racerZ, SEGMENT_LENGTH);
  const y = lerp(seg.p1.screen.y, seg.p2.screen.y, percent);
  const roadX = lerp(seg.p1.screen.x, seg.p2.screen.x, percent);
  const roadW = lerp(seg.p1.screen.w, seg.p2.screen.w, percent);
  const scale = lerp(seg.p1.screen.scale || 0, seg.p2.screen.scale || 0, percent);

  if (!Number.isFinite(y) || !Number.isFinite(roadX) || roadW <= 1) return null;

  return {
    x: roadX + racer.lane * roadW * 0.66,
    y,
    roadW,
    scale,
    dz
  };
}

function drawRacers(cameraZ, baseIndex, speedNorm) {
  const drawList = [];

  for (const r of racers) {
    const p = projectRacer(r, cameraZ);
    if (!p) continue;
    drawList.push({ racer: r, ...p });
  }

  drawList.sort((a, b) => a.y - b.y);

  for (const item of drawList) {
    const r = item.racer;
    const selectedRacer = r.id === SELECTED_ID;

    const mobile = width < 700;
    const screenFactor = clamp(item.roadW / (width * (mobile ? 0.62 : 0.52)), 0.14, 1.12);
    const maxWidth = mobile
      ? width * (selectedRacer ? 0.34 : 0.29)
      : width * (selectedRacer ? 0.19 : 0.17);
    const spriteW = clamp((mobile ? 150 : 220) * screenFactor, mobile ? 28 : 34, maxWidth);
    const spriteH = spriteW * 0.84;

    const cadence = 7.0 + clamp(r.speed / 24, 0, 1) * 7.4;
    const frameFloat = elapsed / 1000 * cadence + r.phaseOffset;
    const frameIndex = ((Math.floor(frameFloat) % S_FRAMES.length) + S_FRAMES.length) % S_FRAMES.length;
    const frame = S_FRAMES[frameIndex];

    const shadowW = spriteW * 0.43;
    const shadowH = Math.max(3, spriteH * 0.055);
    ctx.fillStyle = selectedRacer ? "rgba(4,12,17,.34)" : "rgba(4,12,17,.24)";
    ctx.beginPath();
    ctx.ellipse(item.x, item.y - 1, shadowW, shadowH, 0, 0, Math.PI * 2);
    ctx.fill();

    if (r.speed > 17 && item.y > height * 0.48) {
      ctx.save();
      ctx.globalAlpha = 0.11 + speedNorm * 0.10;
      ctx.fillStyle = "#d9c79d";
      for (let puff = 0; puff < 2; puff++) {
        const px = item.x - spriteW * (0.18 + puff * 0.18);
        const py = item.y - spriteH * 0.05 + puff * 2;
        ctx.beginPath();
        ctx.ellipse(px, py, spriteW * (0.12 + puff * 0.04), spriteH * 0.035, -0.08, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    }

    if (spriteSheet.complete && spriteSheet.naturalWidth > 0) {
      const fw = spriteSheet.naturalWidth / 3;
      const fh = spriteSheet.naturalHeight / 2;
      const sx = frame.col * fw;
      const sy = frame.row * fh;
      const footAdjust = frame.y * spriteH * 0.12;

      ctx.save();
      if (selectedRacer) {
        ctx.shadowColor = "rgba(130,226,255,.8)";
        ctx.shadowBlur = clamp(spriteW * 0.07, 3, 16);
      }
      ctx.drawImage(
        spriteSheet,
        sx, sy, fw, fh,
        item.x - spriteW / 2,
        item.y - spriteH + footAdjust,
        spriteW,
        spriteH
      );
      ctx.restore();
    } else {
      ctx.fillStyle = selectedRacer ? "#b9efff" : "#d7e5e9";
      ctx.fillRect(item.x - spriteW * 0.35, item.y - spriteH * 0.45, spriteW * 0.7, spriteH * 0.42);
    }

    const tagY = item.y - spriteH - 5;
    if (spriteW > 72) {
      const label = String(r.id).padStart(2, "0");
      ctx.font = `800 ${clamp(spriteW * 0.08, 9, 13)}px ui-monospace, Menlo, monospace`;
      ctx.textAlign = "center";
      const tw = ctx.measureText(label).width + 10;
      ctx.fillStyle = selectedRacer ? "rgba(8,39,54,.9)" : "rgba(4,11,16,.72)";
      ctx.fillRect(item.x - tw / 2, tagY - 13, tw, 16);
      ctx.fillStyle = "#eaf8ff";
      ctx.fillText(label, item.x, tagY - 1);
    }

    if (selectedRacer) {
      stage.dataset.sRunFrame = String(frameIndex);
      stage.dataset.sRunPhase = frame.phase;
      stage.dataset.selectedOnTrack = "true";
    }
  }
}

function drawSpeedOverlay(speedNorm) {
  if (speedNorm < 0.60) return;
  const alpha = (speedNorm - 0.60) * 0.16;
  const vignette = ctx.createRadialGradient(
    width * 0.5, height * 0.54, height * 0.12,
    width * 0.5, height * 0.54, width * 0.78
  );
  vignette.addColorStop(0, "rgba(0,0,0,0)");
  vignette.addColorStop(1, `rgba(1,7,11,${alpha})`);
  ctx.fillStyle = vignette;
  ctx.fillRect(0, 0, width, height);
}

function fmtTime(ms) {
  const t = Math.max(0, ms) / 1000;
  const min = Math.floor(t / 60);
  const sec = Math.floor(t % 60);
  const cs = Math.floor((t % 1) * 100);
  return `${String(min).padStart(2, "0")}:${String(sec).padStart(2, "0")}.${String(cs).padStart(2, "0")}`;
}

function updateUI(now) {
  const focus = selected();
  const order = ranking();

  ui.rank.textContent = `${rankOf(focus)} / ${FIELD_SIZE}`;
  ui.speed.textContent = String(Math.round(focus.speed * 3.6));
  ui.command.textContent = focus.command;
  ui.reason.textContent = focus.reason;
  ui.distance.textContent = `${Math.round(focus.distance)} / ${RACE_METERS} m`;
  ui.clock.textContent = fmtTime(elapsed);
  ui.progress.style.width = `${clamp(focus.distance / RACE_METERS * 100, 0, 100).toFixed(2)}%`;

  if (now - lastRankingPaint > 180) {
    lastRankingPaint = now;
    ui.ranking.innerHTML = order.map((r, index) => (
      `<span class="slot ${r.id === SELECTED_ID ? "selected" : ""}">#${index + 1} S${String(r.id).padStart(2, "0")}</span>`
    )).join("");
  }

  stage.dataset.frameCounter = String(frameCounter);
  stage.dataset.selectedDistance = focus.distance.toFixed(2);
  stage.dataset.selectedSpeed = focus.speed.toFixed(2);
}

function resetRace() {
  racers = makeRacers();
  elapsed = 0;
  countdownRemaining = 2500;
  raceState = "countdown";
  finishCounter = 0;
  cameraX = 0;
  paused = false;
  ui.pause.textContent = "Pause";
  ui.countdown.hidden = false;
  ui.countdown.classList.remove("go");
  ui.countdown.textContent = "3";
  stage.dataset.raceState = "countdown";
  stage.dataset.selectedOnTrack = "false";
}

ui.pause.addEventListener("click", () => {
  paused = !paused;
  ui.pause.textContent = paused ? "Resume" : "Pause";
});

ui.reset.addEventListener("click", resetRace);

function frame(now) {
  const dt = Math.min(60, Math.max(0, now - last));
  last = now;
  updateRace(dt);
  renderWorld();
  frameCounter++;
  updateUI(now);
  requestAnimationFrame(frame);
}

stage.dataset.raceState = "countdown";
requestAnimationFrame((now) => {
  last = now;
  frame(now);
});
