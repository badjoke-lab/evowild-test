
const canvas = document.querySelector("#race");
const ctx = canvas.getContext("2d", { alpha: false });
const statusEl = document.querySelector("#status");
const query = new URLSearchParams(location.search);
if (query.get("capture") === "1") document.body.classList.add("capture");

const DPR = Math.min(2, window.devicePixelRatio || 1);
let W = 1280;
let H = 720;

function resize() {
  const rect = canvas.getBoundingClientRect();
  W = Math.max(640, Math.round(rect.width * DPR));
  H = Math.max(360, Math.round(rect.height * DPR));
  canvas.width = W;
  canvas.height = H;
}
addEventListener("resize", resize, { passive: true });
resize();

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const easeIn = (a, b, t) => a + (b - a) * t * t;
const easeInOut = (a, b, t) => a + (b - a) * ((-Math.cos(t * Math.PI) / 2) + 0.5);
const mod = (n, m) => ((n % m) + m) % m;

const COLORS = {
  skyTop: "#315c79",
  skyMid: "#6f9fac",
  horizon: "#d0c29c",
  hillFar: "#58746d",
  hillNear: "#405d56",
  grassA: "#708a67",
  grassB: "#6c8663",
  shoulderA: "#233d45",
  shoulderB: "#9acfd1",
  roadA: "#9f6b52",
  roadB: "#9f6b52",
  lane: "rgba(226,238,229,.58)",
  fog: "#8ba6a0",
  rail: "#17333d",
  railGlow: "#6bd8e1",
};

const SEGMENT_LENGTH = 180;
const ROAD_WIDTH = 2050;
const LANES = 5;
const CAMERA_HEIGHT = 930;
const FOV = 76;
const CAMERA_DEPTH = 1 / Math.tan((FOV * Math.PI / 180) / 2);
const PLAYER_Z = CAMERA_HEIGHT * CAMERA_DEPTH;
const DRAW_DISTANCE = 210;
const RUMBLE_LENGTH = 3;
const HORIZON_Y = 0.37;
const HORIZON_SHIFT = 0.18;

let segments = [];
let trackLength = 0;
let raceDistance = 0;
let elapsed = 0;
let speed = 19800;
let lastTs = performance.now();

function lastY() {
  return segments.length ? segments[segments.length - 1].p2.world.y : 0;
}

function addSegment(curve, y) {
  const n = segments.length;
  segments.push({
    index: n,
    p1: { world: { x: 0, y: lastY(), z: n * SEGMENT_LENGTH }, camera: {}, screen: {} },
    p2: { world: { x: 0, y, z: (n + 1) * SEGMENT_LENGTH }, camera: {}, screen: {} },
    curve,
    visible: false,
    clip: H,
  });
}

function addRoad(enter, hold, leave, curve, hill) {
  const startY = lastY();
  const endY = startY + hill * SEGMENT_LENGTH;
  const total = enter + hold + leave;
  for (let n = 0; n < enter; n++) {
    addSegment(easeIn(0, curve, n / Math.max(1, enter)), easeInOut(startY, endY, n / total));
  }
  for (let n = 0; n < hold; n++) {
    addSegment(curve, easeInOut(startY, endY, (enter + n) / total));
  }
  for (let n = 0; n < leave; n++) {
    addSegment(easeInOut(curve, 0, n / Math.max(1, leave)), easeInOut(startY, endY, (enter + hold + n) / total));
  }
}

function buildTrack() {
  segments = [];
  const S = 28, M = 48, L = 82;
  addRoad(S, S, S, 0, 0);
  addRoad(S, M, S, 1.2, 8);
  addRoad(S, M, S, -2.2, 16);
  addRoad(S, S, S, 0.8, -10);
  addRoad(M, L, M, 2.8, 4);
  addRoad(S, S, S, -3.3, 0);
  addRoad(S, M, S, 1.7, 18);
  addRoad(M, M, M, 0, -14);
  addRoad(S, L, S, -2.6, 6);
  addRoad(S, S, S, 3.6, 12);
  addRoad(M, L, M, -1.5, -8);
  addRoad(S, M, S, 0.6, 0);
  addRoad(S, S, S, 2.8, 6);
  addRoad(S, S, S, -3.1, -6);
  addRoad(M, L, M, 0, 0);
  const correction = -lastY() / SEGMENT_LENGTH;
  addRoad(M, M, M, -0.8, correction);
  trackLength = segments.length * SEGMENT_LENGTH;
}
buildTrack();

function findSegment(z) {
  return segments[Math.floor(mod(z, trackLength) / SEGMENT_LENGTH) % segments.length];
}

function percentRemaining(z) {
  return mod(z, SEGMENT_LENGTH) / SEGMENT_LENGTH;
}

function project(p, cameraX, cameraY, cameraZ, curveX, relIndex) {
  p.camera.x = (p.world.x || 0) - cameraX - curveX;
  p.camera.y = (p.world.y || 0) - cameraY;
  p.camera.z = p.world.z - cameraZ;
  if (p.camera.z < 0) p.camera.z += trackLength;

  const scale = CAMERA_DEPTH / Math.max(1, p.camera.z);
  const depthT = clamp(relIndex / DRAW_DISTANCE, 0, 1);
  const perspectiveShift = W * HORIZON_SHIFT * Math.pow(depthT, 0.55);

  p.screen.scale = scale;
  p.screen.x = Math.round((W * 0.49) + perspectiveShift + scale * p.camera.x * W * 0.5);
  p.screen.y = Math.round((H * HORIZON_Y) - scale * p.camera.y * H * 0.5);
  p.screen.w = Math.round(scale * ROAD_WIDTH * W * 0.5);
}

function polygon(color, ...coords) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(coords[0], coords[1]);
  for (let i = 2; i < coords.length; i += 2) ctx.lineTo(coords[i], coords[i + 1]);
  ctx.closePath();
  ctx.fill();
}

function drawBackground(curveBias) {
  const sky = ctx.createLinearGradient(0, 0, 0, H * 0.66);
  sky.addColorStop(0, COLORS.skyTop);
  sky.addColorStop(0.55, COLORS.skyMid);
  sky.addColorStop(1, COLORS.horizon);
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, W, H);

  const sunX = W * 0.79;
  const sunY = H * 0.15;
  const sunR = Math.max(26, H * 0.055);
  const sun = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR * 2.2);
  sun.addColorStop(0, "rgba(255,237,184,.85)");
  sun.addColorStop(0.45, "rgba(255,212,148,.30)");
  sun.addColorStop(1, "rgba(255,210,140,0)");
  ctx.fillStyle = sun;
  ctx.beginPath();
  ctx.arc(sunX, sunY, sunR * 2.2, 0, Math.PI * 2);
  ctx.fill();

  const baseY = H * HORIZON_Y + 20 * DPR;
  drawHillLayer(baseY, H * 0.10, COLORS.hillFar, curveBias * 0.35, 0.0046);
  drawHillLayer(baseY + H * 0.035, H * 0.13, COLORS.hillNear, curveBias * 0.62, 0.0064);

  const haze = ctx.createLinearGradient(0, H * 0.23, 0, H * HORIZON_Y + H * 0.08);
  haze.addColorStop(0, "rgba(194,211,205,0)");
  haze.addColorStop(1, "rgba(195,206,184,.28)");
  ctx.fillStyle = haze;
  ctx.fillRect(0, H * 0.20, W, H * 0.30);
}

function drawHillLayer(baseY, amp, color, shift, frequency) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, H);
  for (let x = 0; x <= W + 20; x += Math.max(12, W / 90)) {
    const xx = x + shift;
    const y =
      baseY
      - Math.sin(xx * frequency) * amp * 0.44
      - Math.sin(xx * frequency * 2.35 + 1.4) * amp * 0.24
      - Math.sin(xx * frequency * 4.4 + 2.1) * amp * 0.10;
    ctx.lineTo(x, y);
  }
  ctx.lineTo(W, H);
  ctx.closePath();
  ctx.fill();
}

function renderSegment(seg, n) {
  const p1 = seg.p1.screen;
  const p2 = seg.p2.screen;
  const alt = Math.floor(seg.index / RUMBLE_LENGTH) % 2;
  const grass = alt ? COLORS.grassA : COLORS.grassB;
  const road = alt ? COLORS.roadA : COLORS.roadB;
  const rumble = alt ? COLORS.shoulderA : COLORS.shoulderB;

  const r1 = p1.w / Math.max(8, 2.2 * LANES);
  const r2 = p2.w / Math.max(8, 2.2 * LANES);

  ctx.fillStyle = grass;
  ctx.fillRect(0, p2.y, W, Math.max(0, p1.y - p2.y + 1));

  polygon(rumble,
    p1.x - p1.w - r1, p1.y,
    p1.x - p1.w, p1.y,
    p2.x - p2.w, p2.y,
    p2.x - p2.w - r2, p2.y
  );
  polygon(rumble,
    p1.x + p1.w + r1, p1.y,
    p1.x + p1.w, p1.y,
    p2.x + p2.w, p2.y,
    p2.x + p2.w + r2, p2.y
  );
  polygon(road,
    p1.x - p1.w, p1.y,
    p1.x + p1.w, p1.y,
    p2.x + p2.w, p2.y,
    p2.x - p2.w, p2.y
  );

  if (alt === 0 || n < 20) {
    const laneW1 = p1.w * 2 / LANES;
    const laneW2 = p2.w * 2 / LANES;
    const marker1 = Math.max(1, p1.w / 80);
    const marker2 = Math.max(1, p2.w / 80);
    let x1 = p1.x - p1.w + laneW1;
    let x2 = p2.x - p2.w + laneW2;
    for (let lane = 1; lane < LANES; lane++) {
      polygon(COLORS.lane,
        x1 - marker1, p1.y,
        x1 + marker1, p1.y,
        x2 + marker2, p2.y,
        x2 - marker2, p2.y
      );
      x1 += laneW1;
      x2 += laneW2;
    }
  }

  if (n < 68 && alt === 0) {
    const alpha = clamp(1 - n / 72, 0, 1);
    ctx.strokeStyle = "rgba(247,221,184," + (0.10 + alpha * 0.18) + ")";
    ctx.lineWidth = Math.max(1, p1.w / 150);
    const lane = ((seg.index * 37) % 9) / 8 * 1.6 - 0.8;
    const x1 = p1.x + p1.w * lane;
    const x2 = p2.x + p2.w * lane;
    ctx.beginPath();
    ctx.moveTo(x1, p1.y);
    ctx.lineTo(x2, p2.y);
    ctx.stroke();
  }

  const fog = 1 - Math.exp(-Math.pow(n / DRAW_DISTANCE, 2) * 5.0);
  if (fog > 0.04) {
    ctx.fillStyle = "rgba(139,166,160," + (fog * 0.70) + ")";
    ctx.fillRect(0, p2.y, W, Math.max(0, p1.y - p2.y + 1));
  }
}

function drawTreeSprite(x, y, h, side) {
  const trunkW = Math.max(2 * DPR, h * 0.055);
  ctx.fillStyle = "#30483b";
  ctx.fillRect(x - trunkW / 2, y - h * 0.46, trunkW, h * 0.46);

  const layers = [
    [0.98, 0.58, "#315a46"],
    [0.76, 0.48, "#3b684f"],
    [0.55, 0.38, "#46765a"]
  ];
  for (let i = 0; i < layers.length; i++) {
    const layer = layers[i];
    const yy = y - h * (0.34 + i * 0.20);
    const half = h * layer[1] * 0.34;
    ctx.fillStyle = layer[2];
    ctx.beginPath();
    ctx.moveTo(x, yy - h * 0.30);
    ctx.lineTo(x - half, yy + h * 0.18);
    ctx.lineTo(x + half, yy + h * 0.18);
    ctx.closePath();
    ctx.fill();
  }

  if (h > 95 * DPR) {
    ctx.strokeStyle = "rgba(105,215,224,.15)";
    ctx.lineWidth = Math.max(1, h * 0.012);
    ctx.beginPath();
    ctx.moveTo(x + side * h * 0.03, y - h * 0.88);
    ctx.lineTo(x + side * h * 0.12, y - h * 0.42);
    ctx.stroke();
  }
}

function drawTrackBoard(x, y, w, h, side) {
  ctx.save();
  ctx.translate(x, y);
  ctx.fillStyle = "rgba(20,47,57,.92)";
  ctx.fillRect(-w / 2, -h, w, h);
  ctx.fillStyle = "rgba(106,216,225,.88)";
  ctx.fillRect(-w / 2, -h, w, Math.max(2 * DPR, h * 0.09));
  ctx.fillStyle = "rgba(222,235,228,.48)";
  ctx.fillRect(-w * 0.28, -h * 0.56, w * 0.56, Math.max(2 * DPR, h * 0.08));
  ctx.restore();
}

function drawTrackside(seg, n) {
  if (n < 4 || n > 135) return;
  const p = seg.p1.screen;
  if (!seg.visible || p.scale <= 0) return;

  const outward = p.w + clamp(p.w * 0.20, 12, 170);

  if (seg.index % 7 === 0) {
    const poleH = clamp(p.scale * 185000, 4, H * 0.30);
    const poleW = clamp(poleH * 0.055, 1.4, 8 * DPR);
    const sides = seg.index % 14 === 0 ? [-1, 1] : [seg.index % 2 ? 1 : -1];

    for (const side of sides) {
      const x = p.x + outward * side;
      const y = p.y;
      ctx.fillStyle = COLORS.rail;
      ctx.fillRect(x - poleW / 2, y - poleH, poleW, poleH);

      ctx.fillStyle = COLORS.railGlow;
      const glow = Math.max(2.4 * DPR, poleW * 1.6);
      ctx.fillRect(x - glow / 2, y - poleH, glow, Math.max(2 * DPR, poleH * 0.08));

      if (n < 42) {
        ctx.strokeStyle = "rgba(107,216,225," + (0.10 + (1 - n / 42) * 0.22) + ")";
        ctx.lineWidth = Math.max(1, poleW * 0.35);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + side * clamp(p.w * 0.42, 25, 210), y + clamp(poleH * 0.22, 5, 24));
        ctx.stroke();
      }
    }
  }

  if (seg.index % 13 === 0 && n > 8) {
    const side = seg.index % 26 === 0 ? -1 : 1;
    const h = clamp(p.scale * 460000, 18 * DPR, H * 0.44);
    const x = p.x + side * (outward + clamp(p.w * 0.42, 16, 240));
    drawTreeSprite(x, p.y, h, side);
  }

  if (seg.index % 41 === 0 && n > 10 && n < 95) {
    const side = seg.index % 82 === 0 ? 1 : -1;
    const h = clamp(p.scale * 210000, 12 * DPR, H * 0.20);
    const w = h * 1.28;
    const x = p.x + side * (outward + clamp(p.w * 0.24, 12, 140));
    drawTrackBoard(x, p.y, w, h, side);
  }
}

const racers = [
  { id: 1, gap: 0, lane: -0.62, phase: 0, selected: true },
  { id: 2, gap: 1250, lane: -0.28, phase: 1.1 },
  { id: 3, gap: 2350, lane: 0.18, phase: 2.4 },
  { id: 4, gap: 3600, lane: 0.52, phase: 3.2 },
  { id: 5, gap: 4950, lane: -0.02, phase: 4.4 },
];

let sSheet = null;
let sheetReady = false;
const sFrames = [
  [0, 0], [1, 0], [2, 0],
  [0, 1], [1, 1], [2, 1],
];

function loadSheet() {
  const img = new Image();
  img.decoding = "async";
  img.onload = () => {
    sSheet = img;
    sheetReady = true;
    canvas.dataset.sSheet = "loaded";
    statusEl.textContent = "RUNNING";
  };
  img.onerror = () => {
    canvas.dataset.sSheet = "error";
    statusEl.textContent = "SHEET ERROR";
  };
  img.src = import.meta.env.BASE_URL + "concept/s-run-sheet.webp";
}
loadSheet();

function drawRunner(frameIndex, x, y, height, alpha = 1, selected = false) {
  if (!sheetReady) return;
  const fw = sSheet.naturalWidth / 3;
  const fh = sSheet.naturalHeight / 2;
  const frame = sFrames[frameIndex % sFrames.length];
  const col = frame[0];
  const row = frame[1];
  const aspect = fw / fh;
  const h = height;
  const w = h * aspect;

  ctx.save();
  ctx.globalAlpha = alpha;

  const shadowW = w * (selected ? 0.46 : 0.40);
  const shadowH = Math.max(3 * DPR, h * 0.036);
  ctx.fillStyle = selected ? "rgba(11,18,22,.40)" : "rgba(11,18,22,.28)";
  ctx.beginPath();
  ctx.ellipse(x, y - shadowH * 0.25, shadowW, shadowH, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.drawImage(
    sSheet,
    col * fw, row * fh, fw, fh,
    x - w * 0.48, y - h, w, h
  );

  ctx.restore();
}

const dust = [];
function spawnDust(x, y, scale) {
  dust.push({
    x: x + (Math.random() - 0.5) * 28 * DPR,
    y,
    vx: -45 * DPR - Math.random() * 55 * DPR,
    vy: -12 * DPR - Math.random() * 16 * DPR,
    r: (9 + Math.random() * 16) * scale * DPR,
    life: 0.42 + Math.random() * 0.34,
    max: 0.76,
  });
  if (dust.length > 80) dust.shift();
}

function updateDust(dt) {
  for (const d of dust) {
    d.life -= dt;
    d.x += d.vx * dt;
    d.y += d.vy * dt;
    d.r *= 1 + dt * 1.1;
  }
  while (dust.length && dust[0].life <= 0) dust.shift();
}

function drawDust() {
  for (const d of dust) {
    if (d.life <= 0) continue;
    const a = clamp(d.life / d.max, 0, 1) * 0.20;
    ctx.fillStyle = "rgba(225,192,151," + a + ")";
    ctx.beginPath();
    ctx.arc(d.x, d.y, d.r, 0, Math.PI * 2);
    ctx.fill();
  }
}

function drawSpeedStreaks(strength) {
  ctx.save();
  ctx.globalCompositeOperation = "screen";
  const count = 22;
  for (let i = 0; i < count; i++) {
    const seed = (i * 0.6180339887 + elapsed * 0.00009 * (1 + i % 4)) % 1;
    const y = H * (0.56 + seed * 0.42);
    const side = i % 2 ? -1 : 1;
    const x = side < 0 ? W * (0.02 + seed * 0.20) : W * (0.80 + seed * 0.18);
    const len = W * (0.025 + (1 - seed) * 0.08) * strength;
    ctx.strokeStyle = "rgba(198,231,225," + (0.035 + strength * 0.055) + ")";
    ctx.lineWidth = Math.max(1, 1.1 * DPR);
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x + side * len, y + len * 0.08);
    ctx.stroke();
  }
  ctx.restore();
}

function renderWorld(ts) {
  const cameraZ = mod(raceDistance - PLAYER_Z, trackLength);
  const baseSegment = findSegment(cameraZ);
  const basePercent = percentRemaining(cameraZ);
  const raceSeg = findSegment(raceDistance);
  const playerY = lerp(raceSeg.p1.world.y, raceSeg.p2.world.y, percentRemaining(raceDistance));

  let x = 0;
  let dx = -(baseSegment.curve * basePercent);
  let maxY = H;
  const visible = [];

  drawBackground(-baseSegment.curve * 80 * DPR);

  for (let n = 0; n < DRAW_DISTANCE; n++) {
    const seg = segments[(baseSegment.index + n) % segments.length];
    const looped = seg.index < baseSegment.index;
    const cameraBase = cameraZ - (looped ? trackLength : 0);

    project(seg.p1, -620, playerY + CAMERA_HEIGHT, cameraBase, x, n);
    project(seg.p2, -620, playerY + CAMERA_HEIGHT, cameraBase, x + dx, n + 1);

    x += dx;
    dx += seg.curve * 0.72;

    seg.visible = false;
    if (
      seg.p1.camera.z <= CAMERA_DEPTH ||
      seg.p2.screen.y >= seg.p1.screen.y ||
      seg.p2.screen.y >= maxY
    ) continue;

    seg.clip = maxY;
    seg.visible = true;
    visible.push({ seg, n });
    renderSegment(seg, n);
    maxY = seg.p1.screen.y;
  }

  for (let i = visible.length - 1; i >= 0; i--) {
    const item = visible[i];
    const seg = item.seg;
    const n = item.n;
    drawTrackside(seg, n);

    for (let r = 1; r < racers.length; r++) {
      const racer = racers[r];
      const z = mod(raceDistance + racer.gap + Math.sin(elapsed * 0.0005 + racer.phase) * 260, trackLength);
      const rseg = findSegment(z);
      if (rseg.index !== seg.index || !seg.visible) continue;

      const pct = percentRemaining(z);
      const scale = lerp(seg.p1.screen.scale, seg.p2.screen.scale, pct);
      const sx = lerp(seg.p1.screen.x, seg.p2.screen.x, pct);
      const sy = lerp(seg.p1.screen.y, seg.p2.screen.y, pct);
      const sw = lerp(seg.p1.screen.w, seg.p2.screen.w, pct);
      const laneShift = sw * racer.lane * 0.82;
      const height = clamp(scale * ROAD_WIDTH * W * 0.54, 18 * DPR, H * 0.19);
      const frameIndex = Math.floor((ts * 0.0155 + r * 1.7)) % 6;
      drawRunner(frameIndex, sx + laneShift, sy + 1, height, 0.94, false);
    }
  }

  const selectedX = W * 0.335;
  const selectedY = H * 0.875;
  const selectedH = H * 0.285;
  const selectedFrame = Math.floor(ts * 0.0185) % 6;

  drawDust();
  drawRunner(selectedFrame, selectedX, selectedY, selectedH, 1, true);

  if (Math.floor(ts / 65) % 2 === 0) {
    spawnDust(selectedX - selectedH * 0.18, selectedY - selectedH * 0.04, 0.86);
  }

  drawSpeedStreaks(0.92);

  canvas.dataset.state = sheetReady ? "running" : "loading";
  canvas.dataset.renderer = "pseudo3d-segment-projection";
  canvas.dataset.field = "s-only-5";
  canvas.dataset.speed = String(Math.round(speed));
  canvas.dataset.proofVersion = "v3";
}

function frame(ts) {
  const dt = clamp((ts - lastTs) / 1000, 0, 0.04);
  lastTs = ts;
  elapsed += dt * 1000;

  const pulse = 0.5 + 0.5 * Math.sin(elapsed * 0.00055);
  speed = lerp(18400, 22800, pulse * 0.22 + 0.78);
  raceDistance = mod(raceDistance + speed * dt, trackLength);

  updateDust(dt);
  renderWorld(ts);
  requestAnimationFrame(frame);
}

statusEl.textContent = "LOADING S";
requestAnimationFrame(frame);
