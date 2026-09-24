/*
 * EvoWild Run — lane 5 pseudo-3D race proof.
 * Road projection / segment rendering foundation follows the vendored
 * jakesgordon/javascript-racer MIT implementation in /vendor/javascript-racer/.
 */

const { Util, Render } = window;
if (!Util || !Render) throw new Error("Pseudo-3D base failed to load");

const canvas = document.querySelector("#race");
const ctx = canvas.getContext("2d", { alpha: false });
const ui = {
  speed: document.querySelector("#speed"),
  rank: document.querySelector("#rank"),
  command: document.querySelector("#command"),
  phase: document.querySelector("#phase"),
  distance: document.querySelector("#distance"),
  progress: document.querySelector("#progress"),
  roadState: document.querySelector("#roadState"),
  stamina: document.querySelector("#stamina"),
  gap: document.querySelector("#gap"),
  fps: document.querySelector("#fps"),
  pause: document.querySelector("#pause"),
  reset: document.querySelector("#reset")
};

let width = 1280;
let height = 720;
let dpr = 1;

function resize() {
  const rect = canvas.getBoundingClientRect();
  width = Math.max(320, rect.width);
  height = Math.max(460, rect.height);
  dpr = Math.min(1.5, window.devicePixelRatio || 1);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
new ResizeObserver(resize).observe(canvas);
resize();

const BASE = import.meta.env.BASE_URL || "/";
const creature = new Image();
creature.decoding = "async";
creature.src = BASE + "concept/S.webp";

const lanes = 3;
const roadWidth = 2200;
const segmentLength = 200;
const rumbleLength = 3;
const drawDistance = 330;
const maxSpeed = 16500;
const accel = 7600;
const decel = 9200;
const selectedId = 6;
const raceMeters = 1800;
const playerZ = 920;
const SPRITE_WORLD_SCALE = 0.00046;

const COLORS = {
  LIGHT: { road:"#4d5961", grass:"#315949", rumble:"#d6dce0", lane:"#cbd7de" },
  DARK:  { road:"#414b52", grass:"#294d40", rumble:"#6d7880", lane:"#94a4ad" },
  START: { road:"#66717a", grass:"#315949", rumble:"#ffffff", lane:"#e7f2f8" },
  FINISH:{ road:"#222a30", grass:"#294d40", rumble:"#ffffff", lane:"#ffffff" }
};

const segments = [];
let trackLength = 0;
let raceWorld = 540000;
let startZ = 0;
let finishZ = 0;

function lastY() {
  return segments.length ? segments[segments.length - 1].p2.world.y : 0;
}

function addSegment(curve, y) {
  const n = segments.length;
  segments.push({
    index:n,
    p1:{ world:{ y:lastY(), z:n * segmentLength }, camera:{}, screen:{} },
    p2:{ world:{ y, z:(n + 1) * segmentLength }, camera:{}, screen:{} },
    curve,
    color: Math.floor(n / rumbleLength) % 2 ? COLORS.DARK : COLORS.LIGHT,
    clip: height,
    fog:1
  });
}

function addRoad(enter, hold, leave, curve, y) {
  const startY = lastY();
  const endY = startY + y * segmentLength;
  const total = enter + hold + leave;
  let n;
  for (n = 0; n < enter; n++)
    addSegment(Util.easeIn(0, curve, n / Math.max(1, enter)), Util.easeInOut(startY, endY, n / total));
  for (n = 0; n < hold; n++)
    addSegment(curve, Util.easeInOut(startY, endY, (enter + n) / total));
  for (n = 0; n < leave; n++)
    addSegment(Util.easeInOut(curve, 0, n / Math.max(1, leave)), Util.easeInOut(startY, endY, (enter + hold + n) / total));
}

function buildRoad() {
  segments.length = 0;
  addRoad(30, 90, 30, 0, 0);
  const curves = [0,1.8,-2.7,0,3.2,-1.6,0,-3.8,2.2,0,1.2,-2.4,3.5,0,-1.4];
  const hills = [0,8,14,-10,0,18,-12,6,0,-16,10,20,-14,4,0];

  for (let block = 0; block < 30; block++) {
    const c = curves[block % curves.length];
    const h = hills[(block * 3) % hills.length];
    const enter = 24 + (block % 3) * 6;
    const hold = 58 + (block % 5) * 8;
    const leave = 24 + ((block + 1) % 3) * 6;
    addRoad(enter, hold, leave, c, h);
    if (block % 5 === 2) addRoad(16, 38, 16, -c * 0.55, -h * 0.45);
  }

  addRoad(30, 130, 30, 0, -lastY() / segmentLength);
  trackLength = segments.length * segmentLength;
  startZ = playerZ + segmentLength * 10;
  raceWorld = Math.min(540000, trackLength - startZ - drawDistance * segmentLength - 4000);
  finishZ = startZ + raceWorld;

  const startIndex = Math.floor(startZ / segmentLength);
  for (let i = 0; i < 3; i++) {
    if (segments[startIndex + i]) segments[startIndex + i].color = COLORS.START;
  }
  const finishIndex = Math.floor(finishZ / segmentLength);
  for (let i = -2; i <= 2; i++) {
    if (segments[finishIndex + i]) segments[finishIndex + i].color = COLORS.FINISH;
  }
}
buildRoad();

function findSegment(z) {
  const clamped = Math.max(0, Math.min(trackLength - 1, z));
  return segments[Math.floor(clamped / segmentLength) % segments.length];
}

const names = ["Vela","Rook","Serein","Flint","Nacre","Mica","Ilex","Sora","Dune","Kite","Rime","Tern"];

function makeRacers() {
  return names.map((name, i) => {
    const gridRow = Math.floor(i / 3);
    const lane = (i % 3) - 1;
    return {
      id:i + 1,
      name,
      lane,
      targetLane:lane,
      offset:lane * 0.60,
      z:startZ - gridRow * 380 + ((i % 2) ? 80 : 0),
      speed:0,
      stamina:100,
      seed:i * 0.83 + 0.4,
      baseMax:maxSpeed * (0.965 + ((i * 17) % 9) * 0.006),
      cooldown:400 + i * 95,
      command:"BUILD",
      phase:"START",
      finished:false,
      finishTime:0
    };
  });
}

let racers = makeRacers();
let elapsed = 0;
let last = performance.now();
let paused = false;
let resetAt = 0;
let frameCounter = 0;
let fpsClock = performance.now();
let shownFps = 0;

function selected() {
  return racers[selectedId - 1];
}

function progressOf(r) {
  return Util.limit((r.z - startZ) / raceWorld, 0, 1);
}

function phaseFor(p) {
  if (p < 0.08) return "START";
  if (p < 0.50) return "CRUISE";
  if (p < 0.78) return "BUILD";
  return "FINAL";
}

function rankList() {
  return [...racers].sort((a,b) => {
    if (a.finished && b.finished) return a.finishTime - b.finishTime;
    if (a.finished) return -1;
    if (b.finished) return 1;
    return b.z - a.z;
  });
}

function rankOf(r) {
  return rankList().findIndex(x => x === r) + 1;
}

function laneGapAhead(r, lane) {
  let best = Infinity;
  for (const other of racers) {
    if (other === r || other.finished || other.targetLane !== lane) continue;
    const d = other.z - r.z;
    if (d > 0 && d < best) best = d;
  }
  return best;
}

function laneOpen(r, lane) {
  if (lane < -1 || lane > 1) return false;
  return racers.every(other => {
    if (other === r || other.finished || other.targetLane !== lane) return true;
    return Math.abs(other.z - r.z) > 1500;
  });
}

function chooseLane(r) {
  const currentGap = laneGapAhead(r, r.targetLane);
  if (currentGap > 2400) return r.targetLane;
  const options = [-1,0,1]
    .filter(l => laneOpen(r,l))
    .map(l => ({ lane:l, gap:laneGapAhead(r,l) }))
    .sort((a,b) => b.gap - a.gap);
  return options.length ? options[0].lane : r.targetLane;
}

function updateRacer(r, dt) {
  if (r.finished) {
    r.speed = Math.max(0, r.speed - decel * 0.35 * dt);
    return;
  }

  const p = progressOf(r);
  r.phase = phaseFor(p);
  r.cooldown -= dt * 1000;

  let target = r.baseMax;
  if (p < 0.06) target *= 0.94;
  if (p > 0.78) target *= r.stamina > 24 ? 1.035 : 0.90;
  if (r.stamina < 18) target *= 0.84;

  const gap = laneGapAhead(r, r.targetLane);
  if (gap < 2200 && r.cooldown <= 0) {
    const next = chooseLane(r);
    if (next !== r.targetLane) {
      r.targetLane = next;
      r.cooldown = 1000 + ((r.id * 137) % 800);
      r.command = "SHIFT";
    } else {
      target *= Util.limit(gap / 2200, 0.82, 1);
      r.command = "HOLD";
    }
  } else if (r.phase === "FINAL") {
    r.command = r.stamina > 24 ? "COMMIT" : "HOLD";
  } else if (r.phase === "BUILD") {
    r.command = "PRESS";
  } else {
    r.command = "BUILD";
  }

  const fatigue = 0.79 + 0.21 * (r.stamina / 100);
  target *= fatigue;
  const delta = target - r.speed;
  const rate = delta >= 0 ? accel : decel;
  r.speed += Util.limit(delta, -rate * dt, rate * dt);
  r.speed = Util.limit(r.speed, 0, maxSpeed * 1.05);

  r.offset += ((r.targetLane * 0.60) - r.offset) * Math.min(1, dt * 3.8);
  r.z += r.speed * dt;

  const effort = r.speed / r.baseMax;
  r.stamina = Math.max(0, r.stamina - (0.48 + Math.max(0, effort - 0.90) * 2.9) * dt);

  if (r.z >= finishZ) {
    r.z = finishZ;
    r.finished = true;
    r.finishTime = elapsed;
  }
}

function update(dtMs) {
  if (paused) return;
  const dt = Math.min(dtMs, 50) / 1000;
  elapsed += dtMs;

  for (const r of racers) updateRacer(r, dt);

  if (racers.every(r => r.finished) && !resetAt) resetAt = elapsed + 3500;
  if (resetAt && elapsed >= resetAt) resetRace();
}

function drawBackground(position, curve, speedNorm) {
  const sky = ctx.createLinearGradient(0, 0, 0, height * 0.72);
  sky.addColorStop(0, "#6ca8c8");
  sky.addColorStop(0.47, "#a8c3cb");
  sky.addColorStop(1, "#d6c39c");
  ctx.fillStyle = sky;
  ctx.fillRect(-20, -20, width + 40, height + 40);

  const horizon = height * (0.38 - speedNorm * 0.025);
  const sunX = width * 0.76 - curve * width * 0.014;
  const sunY = horizon * 0.52;
  const sunR = Math.max(26, width * 0.026);
  const glow = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR * 3.2);
  glow.addColorStop(0, "rgba(255,245,204,.72)");
  glow.addColorStop(1, "rgba(255,245,204,0)");
  ctx.fillStyle = glow;
  ctx.fillRect(sunX - sunR * 3.2, sunY - sunR * 3.2, sunR * 6.4, sunR * 6.4);

  const layers = [
    { y:horizon + 20, amp:74, step:118, par:0.010, fill:"#6c7f83" },
    { y:horizon + 48, amp:58, step:96, par:0.022, fill:"#526f68" },
    { y:horizon + 74, amp:42, step:74, par:0.045, fill:"#3e6152" }
  ];

  for (const layer of layers) {
    const shift = (position * layer.par + curve * 90) % (layer.step * 2);
    ctx.fillStyle = layer.fill;
    ctx.beginPath();
    ctx.moveTo(-layer.step, height);
    ctx.lineTo(-layer.step, layer.y);
    for (let x = -layer.step; x <= width + layer.step; x += layer.step) {
      const wave = Math.abs(Math.sin((x + shift) * 0.017));
      ctx.lineTo(x, layer.y - layer.amp * (0.32 + wave * 0.68));
      ctx.lineTo(x + layer.step * 0.56, layer.y);
    }
    ctx.lineTo(width + layer.step, height);
    ctx.closePath();
    ctx.fill();
  }
}

function drawRoadside(segment, index, speedNorm) {
  if (!segment.p1.screen.scale || segment.p1.screen.y >= height) return;
  const x = segment.p1.screen.x;
  const y = segment.p1.screen.y;
  const w = segment.p1.screen.w;

  if (index % 7 === 0) {
    const postH = Util.limit(w * 0.30, 4, height * 0.24);
    const postW = Util.limit(postH * 0.10, 1, 7);
    ctx.fillStyle = "rgba(222,236,241,.86)";
    ctx.fillRect(x - w * 1.14 - postW / 2, y - postH, postW, postH);
    ctx.fillRect(x + w * 1.14 - postW / 2, y - postH, postW, postH);
    ctx.fillStyle = "rgba(90,214,255,.68)";
    ctx.fillRect(x - w * 1.14 - postW, y - postH, postW * 2, Math.max(1, postW));
    ctx.fillRect(x + w * 1.14 - postW, y - postH, postW * 2, Math.max(1, postW));
  }

  if (index % 41 === 0 && w > 15) {
    const gateH = Util.limit(w * 0.42, 12, height * 0.32);
    const left = x - w * 1.02;
    const right = x + w * 1.02;
    ctx.strokeStyle = "rgba(163,231,255," + (0.34 + speedNorm * 0.25) + ")";
    ctx.lineWidth = Util.limit(w * 0.012, 1, 5);
    ctx.beginPath();
    ctx.moveTo(left, y);
    ctx.lineTo(left, y - gateH);
    ctx.lineTo(right, y - gateH);
    ctx.lineTo(right, y);
    ctx.stroke();
  }
}

function drawCreature(r, x, y, roadScale, clipY) {
  const speedNorm = Util.limit(r.speed / maxSpeed, 0, 1);
  const imgW = creature.naturalWidth || 512;
  const imgH = creature.naturalHeight || 384;
  const pxScale = roadScale * width / 2 * (SPRITE_WORLD_SCALE * roadWidth);
  let w = imgW * pxScale;
  let h = imgH * pxScale;

  const maxW = width * 0.34;
  if (w > maxW) {
    const k = maxW / w;
    w *= k;
    h *= k;
  }
  if (w < 5 || h < 4) return;

  const phase = elapsed * (0.0105 + speedNorm * 0.0105) + r.seed;
  const bob = Math.sin(phase * 2) * h * 0.012 * speedNorm;
  const compression = 1 + Math.sin(phase * 2 + Math.PI / 2) * 0.018 * speedNorm;
  const lean = -0.018 - speedNorm * 0.028;
  const baseY = y + bob;

  ctx.save();
  if (Number.isFinite(clipY) && clipY > 0 && clipY < height) {
    ctx.beginPath();
    ctx.rect(-50, -50, width + 100, clipY + 50);
    ctx.clip();
  }

  const shadowAlpha = 0.16 + 0.14 * speedNorm;
  ctx.fillStyle = "rgba(0,0,0," + shadowAlpha + ")";
  ctx.beginPath();
  ctx.ellipse(x, baseY + 3, w * 0.34, Math.max(2, h * 0.055), 0, 0, Math.PI * 2);
  ctx.fill();

  if (speedNorm > 0.68 && creature.complete) {
    const trails = 2 + Math.floor(speedNorm * 2);
    for (let i = trails; i >= 1; i--) {
      ctx.globalAlpha = (0.035 + speedNorm * 0.035) * (1 - i / (trails + 1));
      ctx.drawImage(creature, x - w / 2 - i * (7 + speedNorm * 13), baseY - h, w, h);
    }
    ctx.globalAlpha = 1;
  }

  ctx.translate(x, baseY - h);
  ctx.rotate(lean);

  if (!creature.complete || !creature.naturalWidth) {
    ctx.fillStyle = "#d7edf5";
    ctx.fillRect(-w / 2, h * 0.25, w, h * 0.42);
    ctx.restore();
    return;
  }

  const sw = creature.naturalWidth;
  const sh = creature.naturalHeight;
  const bodyCut = Math.floor(sh * 0.60);

  ctx.save();
  ctx.translate(0, h * (1 - compression) * 0.3);
  ctx.scale(1, compression);
  ctx.drawImage(creature, 0, 0, sw, bodyCut, -w / 2, 0, w, h * (bodyCut / sh));
  ctx.restore();

  const lowerY = Math.floor(sh * 0.48);
  const lowerH = sh - lowerY;
  const chunkCount = 4;
  const chunkSrcW = sw / chunkCount;
  const chunkDestW = w / chunkCount;
  const destBaseY = h * (lowerY / sh);

  for (let i = 0; i < chunkCount; i++) {
    const gait = phase + (i % 2 === 0 ? 0 : Math.PI) + (i > 1 ? Math.PI * 0.18 : 0);
    const swing = Math.sin(gait) * w * 0.026 * speedNorm;
    const lift = Math.max(0, Math.sin(gait + Math.PI / 2)) * h * 0.045 * speedNorm;
    const twist = Math.sin(gait) * 0.055 * speedNorm;
    const dx = -w / 2 + chunkDestW * (i + 0.5);

    ctx.save();
    ctx.translate(dx + swing, destBaseY + lift);
    ctx.rotate(twist);
    ctx.drawImage(
      creature,
      Math.floor(i * chunkSrcW),
      lowerY,
      Math.ceil(chunkSrcW + 1),
      lowerH,
      -chunkDestW * 0.51,
      0,
      chunkDestW * 1.02,
      h * (lowerH / sh)
    );
    ctx.restore();
  }

  if (r.id === selectedId && w > 90) {
    ctx.strokeStyle = "rgba(136,220,255,.72)";
    ctx.lineWidth = Math.max(1.2, w * 0.005);
    ctx.setLineDash([Math.max(3,w*.018),Math.max(3,w*.014)]);
    ctx.strokeRect(-w * 0.55, -h * 0.03, w * 1.1, h * 1.02);
    ctx.setLineDash([]);
  }

  ctx.restore();
}

function render() {
  const focus = selected();
  const speedNorm = Util.limit(focus.speed / maxSpeed, 0, 1);
  const fov = 88 + speedNorm * 18;
  const cameraDepth = 1 / Math.tan((fov / 2) * Math.PI / 180);
  const cameraHeight = 980 - speedNorm * 120;
  const position = Math.max(0, focus.z - playerZ);
  const baseSegment = findSegment(position);
  const basePercent = Util.percentRemaining(position, segmentLength);
  const focusSegment = findSegment(focus.z);
  const focusPercent = Util.percentRemaining(focus.z, segmentLength);
  const playerY = Util.interpolate(focusSegment.p1.world.y, focusSegment.p2.world.y, focusPercent);
  const shakeX = Math.sin(elapsed * 0.061) * speedNorm * 1.7;
  const shakeY = Math.sin(elapsed * 0.089 + 1.1) * speedNorm * 1.2;

  ctx.save();
  ctx.translate(shakeX, shakeY);

  drawBackground(position, baseSegment.curve, speedNorm);

  let maxy = height;
  let x = 0;
  let dx = -(baseSegment.curve * basePercent);

  for (let n = 0; n < drawDistance; n++) {
    const segment = segments[baseSegment.index + n];
    if (!segment) break;

    segment.fog = Util.exponentialFog(n / drawDistance, 4.2);
    segment.clip = maxy;

    Util.project(segment.p1, (focus.offset * roadWidth) - x, playerY + cameraHeight, position, cameraDepth, width, height, roadWidth);
    Util.project(segment.p2, (focus.offset * roadWidth) - x - dx, playerY + cameraHeight, position, cameraDepth, width, height, roadWidth);

    x += dx;
    dx += segment.curve;

    if (
      segment.p1.camera.z <= cameraDepth ||
      segment.p2.screen.y >= segment.p1.screen.y ||
      segment.p2.screen.y >= maxy
    ) continue;

    Render.segment(
      ctx,
      width,
      lanes,
      segment.p1.screen.x,
      segment.p1.screen.y,
      segment.p1.screen.w,
      segment.p2.screen.x,
      segment.p2.screen.y,
      segment.p2.screen.w,
      segment.fog,
      segment.color
    );
    maxy = segment.p1.screen.y;
  }

  for (let n = drawDistance - 1; n > 1; n--) {
    const segment = segments[baseSegment.index + n];
    if (!segment || !segment.p1.screen.scale) continue;
    drawRoadside(segment, segment.index, speedNorm);
  }

  const visible = racers
    .filter(r => r.z >= position && r.z - position <= drawDistance * segmentLength)
    .sort((a,b) => b.z - a.z);

  for (const r of visible) {
    const segment = findSegment(r.z);
    if (!segment.p1.screen.scale || !segment.p2.screen.scale) continue;
    const percent = Util.percentRemaining(r.z, segmentLength);
    const scale = Util.interpolate(segment.p1.screen.scale, segment.p2.screen.scale, percent);
    const sx = Util.interpolate(segment.p1.screen.x, segment.p2.screen.x, percent)
      + scale * r.offset * roadWidth * width / 2;
    const sy = Util.interpolate(segment.p1.screen.y, segment.p2.screen.y, percent);
    drawCreature(r, sx, sy, scale, segment.clip);
  }

  if (speedNorm > 0.58) {
    const alpha = (speedNorm - 0.58) * 0.22;
    ctx.strokeStyle = "rgba(226,244,255," + alpha.toFixed(3) + ")";
    ctx.lineWidth = 1;
    const count = 10;
    for (let i = 0; i < count; i++) {
      const yy = height * (0.20 + ((i * 0.071 + elapsed * 0.00033) % 0.68));
      const len = 20 + speedNorm * 80 + (i % 4) * 12;
      ctx.beginPath();
      ctx.moveTo(0, yy);
      ctx.lineTo(len, yy + 3);
      ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(width, yy + 12);
      ctx.lineTo(width - len, yy + 15);
      ctx.stroke();
    }
  }

  const vignette = ctx.createRadialGradient(width * 0.5, height * 0.48, height * 0.20, width * 0.5, height * 0.52, width * 0.78);
  vignette.addColorStop(0, "rgba(0,0,0,0)");
  vignette.addColorStop(1, "rgba(0,0,0,.28)");
  ctx.fillStyle = vignette;
  ctx.fillRect(-10, -10, width + 20, height + 20);

  ctx.restore();
}

let lastUi = 0;
function updateUI(now) {
  if (now - lastUi < 80) return;
  lastUi = now;

  const s = selected();
  const p = progressOf(s);
  const order = rankList();
  const rank = rankOf(s);
  const leader = order[0];
  const gapWorld = Math.max(0, leader.z - s.z);
  const gapMeters = gapWorld / raceWorld * raceMeters;
  const meters = Math.round(p * raceMeters);
  const currentRoad = findSegment(s.z);

  ui.speed.textContent = Math.round((s.speed / maxSpeed) * 308) + " km/h";
  ui.rank.textContent = rank + " / " + racers.length;
  ui.command.textContent = s.command;
  ui.phase.textContent = s.phase;
  ui.distance.textContent = meters + "m";
  ui.progress.style.width = (p * 100).toFixed(2) + "%";
  ui.roadState.textContent =
    Math.abs(currentRoad.curve) < 0.35 ? "STRAIGHT" :
    currentRoad.curve > 0 ? "RIGHT " + Math.abs(currentRoad.curve).toFixed(1) :
    "LEFT " + Math.abs(currentRoad.curve).toFixed(1);
  ui.stamina.textContent = Math.round(s.stamina).toString();
  ui.gap.textContent = rank === 1 ? "LEAD" : "+" + gapMeters.toFixed(1) + "m";
  ui.fps.textContent = shownFps ? String(shownFps) : "--";
}

function resetRace() {
  racers = makeRacers();
  elapsed = 0;
  resetAt = 0;
  paused = false;
  ui.pause.textContent = "Pause";
}

ui.pause.addEventListener("click", () => {
  paused = !paused;
  ui.pause.textContent = paused ? "Resume" : "Pause";
});
ui.reset.addEventListener("click", resetRace);

function frame(now) {
  const dt = now - last;
  last = now;

  update(dt);
  render();
  updateUI(now);

  frameCounter++;
  if (now - fpsClock >= 1000) {
    shownFps = Math.round(frameCounter * 1000 / (now - fpsClock));
    frameCounter = 0;
    fpsClock = now;
  }

  requestAnimationFrame(frame);
}

requestAnimationFrame(now => {
  last = now;
  fpsClock = now;
  frame(now);
});
