const stage = document.querySelector("#stage");
const canvas = document.querySelector("#game");
const ctx = canvas.getContext("2d", { alpha: false, desynchronized: true });
const speedEl = document.querySelector("#speed");
const placeEl = document.querySelector("#place");
const phaseEl = document.querySelector("#phase");
const goEl = document.querySelector("#go");

const W = canvas.width;
const H = canvas.height;
const TAU = Math.PI * 2;
const palette = ["#80ddff", "#ffd36f", "#ff8aa4", "#9cf17a", "#b89cff"];

let last = performance.now();
let raceTime = 0;
let ready = false;
let goPlayed = false;
let frameCounter = 0;
let cameraDistance = 0;
let visualSpeed = 0;
let cameraLead = 0;
let cameraShake = 0;

const racers = [
  { id: 1, distance: 52, lane: 0.12, laneTarget: 0.12, speed: 31.0, target: 31.6, phase: 0.2 },
  { id: 2, distance: 38, lane: 0.74, laneTarget: 0.74, speed: 30.2, target: 31.1, phase: 1.4 },
  { id: 3, distance: 24, lane: 0.38, laneTarget: 0.38, speed: 30.6, target: 31.4, phase: 2.5 },
  { id: 4, distance: 12, lane: 0.91, laneTarget: 0.91, speed: 30.0, target: 31.0, phase: 3.7 },
  { id: 5, distance: 0,  lane: 0.56, laneTarget: 0.56, speed: 0, target: 35.8, phase: 4.8, selected: true }
];

const spriteSheet = new Image();
spriteSheet.decoding = "async";
spriteSheet.src = "./concept/s-run-sheet.webp";
const tinted = [];

function clamp(v, a, b) { return Math.max(a, Math.min(b, v)); }
function lerp(a, b, t) { return a + (b - a) * t; }
function smoothstep(a, b, x) {
  const t = clamp((x - a) / (b - a), 0, 1);
  return t * t * (3 - 2 * t);
}
function fract(v) { return v - Math.floor(v); }
function hash(n) { return fract(Math.sin(n * 127.1 + 311.7) * 43758.5453); }
function noise1(x) {
  const i = Math.floor(x);
  const f = x - i;
  const a = hash(i);
  const b = hash(i + 1);
  const t = f * f * (3 - 2 * f);
  return lerp(a, b, t);
}

function makeTintFrames() {
  tinted.length = 0;
  const fw = Math.floor(spriteSheet.naturalWidth / 3);
  const fh = Math.floor(spriteSheet.naturalHeight / 2);
  for (let p = 0; p < palette.length; p++) {
    const frames = [];
    for (let i = 0; i < 6; i++) {
      const off = document.createElement("canvas");
      off.width = fw;
      off.height = fh;
      const o = off.getContext("2d");
      const sx = (i % 3) * fw;
      const sy = Math.floor(i / 3) * fh;
      o.drawImage(spriteSheet, sx, sy, fw, fh, 0, 0, fw, fh);
      o.globalCompositeOperation = "source-atop";
      o.globalAlpha = 0.18;
      o.fillStyle = palette[p];
      o.fillRect(0, 0, fw, fh);
      o.globalCompositeOperation = "source-over";
      o.globalAlpha = 1;
      frames.push(off);
    }
    tinted.push(frames);
  }
}

function racerTargetSpeed(r) {
  const t = raceTime * 0.001;
  if (r.selected) return 35.8;
  return r.target + Math.sin(t * 0.72 + r.phase) * 1.25 + Math.sin(t * 1.41 + r.id) * 0.45;
}

const dust = [];
function spawnDust(x, y, size, color) {
  dust.push({
    x, y,
    vx: -95 - Math.random() * 90,
    vy: -5 - Math.random() * 24,
    life: 0.45 + Math.random() * 0.32,
    max: 0.78,
    size,
    color
  });
  if (dust.length > 110) dust.shift();
}
function updateDust(dt) {
  for (let i = dust.length - 1; i >= 0; i--) {
    const p = dust[i];
    p.life -= dt;
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.vx *= 0.985;
    p.size *= 1 + dt * 1.15;
    if (p.life <= 0) dust.splice(i, 1);
  }
}

function updateRace(dt) {
  raceTime += dt * 1000;
  const selected = racers[4];

  for (const r of racers) {
    const target = racerTargetSpeed(r);
    const accel = r.selected ? (raceTime < 1800 ? 7.6 : 2.3) : 1.5;
    r.speed = lerp(r.speed, target, clamp(dt * accel, 0, 1));
    r.distance += r.speed * dt;

    if (!r.selected) {
      if (Math.random() < dt * 0.22) {
        r.laneTarget = clamp(r.laneTarget + (Math.random() - 0.5) * 0.34, 0.08, 0.94);
      }
      r.lane = lerp(r.lane, r.laneTarget, clamp(dt * 0.52, 0, 1));
    } else {
      const targetLane = 0.53 + Math.sin(raceTime * 0.00038) * 0.08;
      r.lane = lerp(r.lane, targetLane, clamp(dt * 0.38, 0, 1));
    }
  }

  visualSpeed = lerp(visualSpeed, selected.speed, clamp(dt * 4.4, 0, 1));
  cameraDistance = lerp(cameraDistance, selected.distance, clamp(dt * 4.8, 0, 1));
  cameraLead = lerp(cameraLead, clamp((selected.speed - 26) * 2.2, 0, 26), clamp(dt * 2.4, 0, 1));
  cameraShake = smoothstep(0.58, 1.0, visualSpeed / 36);

  updateDust(dt);

  if (!goPlayed && raceTime > 620) {
    goPlayed = true;
    goEl.classList.remove("play");
    void goEl.offsetWidth;
    goEl.classList.add("play");
  }

  const order = [...racers].sort((a, b) => b.distance - a.distance);
  const place = order.findIndex(r => r.selected) + 1;
  placeEl.textContent = `${place} / 5`;
  speedEl.textContent = String(Math.round(visualSpeed * 8.5)).padStart(3, "0");
  phaseEl.textContent = raceTime < 2200 ? "LAUNCH" : place <= 2 ? "ATTACK" : "CHASE";
}

function skyGradient() {
  const g = ctx.createLinearGradient(0, 0, 0, 390);
  g.addColorStop(0, "#65b8d2");
  g.addColorStop(0.50, "#98cfdb");
  g.addColorStop(1, "#d6e4dc");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  const sunX = 1030;
  const sunY = 94;
  const sun = ctx.createRadialGradient(sunX, sunY, 2, sunX, sunY, 68);
  sun.addColorStop(0, "rgba(255,250,207,.95)");
  sun.addColorStop(0.26, "rgba(255,235,154,.54)");
  sun.addColorStop(1, "rgba(255,235,154,0)");
  ctx.fillStyle = sun;
  ctx.fillRect(sunX - 75, sunY - 75, 150, 150);
}

function drawCloudBand(scroll, layer, alpha) {
  ctx.save();
  ctx.globalAlpha = alpha;
  for (let i = 0; i < 11; i++) {
    const span = 190 + layer * 20;
    const x = ((i * span - scroll * (0.06 + layer * 0.035)) % (W + 260)) - 130;
    const y = 70 + (i % 4) * 37 + layer * 17;
    const rx = 54 + (i % 3) * 16;
    const ry = 12 + (i % 2) * 6;
    const g = ctx.createRadialGradient(x, y, 3, x, y, rx);
    g.addColorStop(0, "rgba(255,255,255,.90)");
    g.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(x, y, rx, ry, 0, 0, TAU);
    ctx.fill();
  }
  ctx.restore();
}

function drawMountainLayer(baseY, amplitude, scrollFactor, color, detail = 1) {
  const scroll = cameraDistance * scrollFactor;
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, H);
  ctx.lineTo(0, baseY);
  for (let x = 0; x <= W + 10; x += 10) {
    const world = x + scroll;
    const n = noise1(world * 0.0067 * detail) * 0.72 + noise1(world * 0.0029 + 44) * 0.28;
    const ridge = Math.pow(n, 1.65) * amplitude;
    ctx.lineTo(x, baseY - ridge);
  }
  ctx.lineTo(W, H);
  ctx.closePath();
  ctx.fill();
}

function drawForest(scrollFactor, baseY, dark, light) {
  const scroll = cameraDistance * scrollFactor;
  ctx.fillStyle = dark;
  ctx.fillRect(0, baseY, W, H - baseY);

  const spacing = 26;
  const start = -((scroll * 7.5) % spacing) - spacing;
  for (let i = 0; i < Math.ceil(W / spacing) + 3; i++) {
    const x = start + i * spacing;
    const seed = Math.floor((scroll * 7.5 + x) / spacing);
    const h = 18 + hash(seed + 13) * 32;
    ctx.fillStyle = seed % 2 ? light : dark;
    ctx.beginPath();
    ctx.moveTo(x - 11, baseY + 9);
    ctx.lineTo(x, baseY - h);
    ctx.lineTo(x + 11, baseY + 9);
    ctx.closePath();
    ctx.fill();
  }
}

function drawFarArchitecture() {
  const scroll = cameraDistance * 2.1;
  const spacing = 260;
  const offset = -((scroll * 3.2) % spacing) - spacing;
  for (let i = 0; i < 8; i++) {
    const x = offset + i * spacing;
    const seed = Math.floor((scroll * 3.2 + x) / spacing);
    if (seed % 3 === 0) {
      ctx.fillStyle = "rgba(33,57,65,.62)";
      ctx.fillRect(x, 300, 120, 34);
      ctx.fillStyle = "rgba(223,235,230,.66)";
      for (let j = 0; j < 5; j++) ctx.fillRect(x + 10 + j * 22, 306, 13, 10);
    } else {
      ctx.strokeStyle = "rgba(234,242,239,.58)";
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(x + 10, 337);
      ctx.lineTo(x + 10, 290);
      ctx.lineTo(x + 84, 290);
      ctx.lineTo(x + 84, 337);
      ctx.stroke();
    }
  }
}

function roadYFromLane(lane) {
  return lerp(418, 594, lane);
}
function roadScaleFromLane(lane) {
  return lerp(0.72, 1.05, lane);
}

function drawTrack() {
  const topY = 360;
  const bottomY = 650;

  const grd = ctx.createLinearGradient(0, topY, 0, bottomY);
  grd.addColorStop(0, "#696a68");
  grd.addColorStop(0.55, "#5f605f");
  grd.addColorStop(1, "#505251");
  ctx.fillStyle = grd;
  ctx.fillRect(0, topY, W, bottomY - topY);

  ctx.fillStyle = "#d95a4f";
  ctx.fillRect(0, topY, W, 10);
  ctx.fillRect(0, bottomY - 10, W, 10);
  ctx.fillStyle = "#eee7d7";
  ctx.fillRect(0, topY + 10, W, 5);
  ctx.fillRect(0, bottomY - 15, W, 5);

  // Horizontal lane dividers, perspective-weighted.
  ctx.strokeStyle = "rgba(244,240,222,.74)";
  ctx.lineWidth = 2;
  for (const lane of [0.25, 0.50, 0.75]) {
    const y = roadYFromLane(lane);
    ctx.setLineDash([38, 30]);
    ctx.lineDashOffset = -((cameraDistance * 11.5 * (0.72 + lane * 0.5)) % 68);
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(W, y);
    ctx.stroke();
  }
  ctx.setLineDash([]);

  // Surface seams streaming left.
  const scroll = cameraDistance * 12.6;
  for (let lane = 0; lane < 4; lane++) {
    const y0 = roadYFromLane(lane / 4);
    const y1 = roadYFromLane((lane + 1) / 4);
    const period = 118 - lane * 12;
    const offset = -(scroll * (0.70 + lane * 0.13) % period);
    for (let x = offset - period; x < W + period; x += period) {
      ctx.globalAlpha = 0.10 + lane * 0.018;
      ctx.fillStyle = lane % 2 ? "#efebdf" : "#282d2e";
      ctx.fillRect(x, y0 + 7, 2 + lane, Math.max(2, y1 - y0 - 14));
    }
  }
  ctx.globalAlpha = 1;

  // Trackside safety fence/posts.
  const postScroll = cameraDistance * 14.8;
  for (const y of [350, 660]) {
    const front = y > 500;
    const period = front ? 92 : 138;
    const offset = -(postScroll * (front ? 1.0 : 0.68) % period);
    for (let x = offset - period; x < W + period; x += period) {
      const h = front ? 76 : 46;
      const w = front ? 5 : 3;
      ctx.fillStyle = front ? "rgba(30,45,49,.82)" : "rgba(230,240,238,.82)";
      ctx.fillRect(x, y - h, w, h);
      ctx.fillStyle = front ? "rgba(200,220,220,.28)" : "rgba(42,57,62,.50)";
      ctx.fillRect(x + w, y - h * 0.72, front ? 34 : 22, front ? 3 : 2);
    }
  }
}

function drawForegroundSpeed() {
  const ratio = clamp(visualSpeed / 36, 0, 1);
  const strength = smoothstep(0.42, 0.93, ratio);
  const scroll = cameraDistance * 24;

  // Near grass / rail blur.
  const y = 675;
  ctx.globalAlpha = 0.16 + strength * 0.24;
  for (let i = 0; i < 44; i++) {
    const seed = i + Math.floor(scroll / 35);
    const x = ((i * 43 - scroll * 0.9) % (W + 180)) - 90;
    const len = 36 + hash(seed) * 120 * strength;
    const h = 1 + Math.floor(hash(seed + 4) * 3);
    ctx.fillStyle = seed % 2 ? "#9fc6a0" : "#5c8a66";
    ctx.fillRect(x, y + (seed % 5) * 8, len, h);
  }
  ctx.globalAlpha = 1;

  // Screen-edge streaks at high speed.
  if (strength > 0.02) {
    ctx.save();
    ctx.globalCompositeOperation = "screen";
    for (let i = 0; i < 28; i++) {
      const yy = 380 + ((i * 29 + raceTime * (0.15 + (i % 4) * 0.018)) % 310);
      const len = 18 + strength * (42 + (i % 7) * 18);
      ctx.globalAlpha = 0.04 + strength * 0.09;
      ctx.fillStyle = "#dff7ef";
      if (i % 2) ctx.fillRect(0, yy, len, 1);
      else ctx.fillRect(W - len, yy, len, 1);
    }
    ctx.restore();
  }
}

function drawDust() {
  for (const p of dust) {
    const a = clamp(p.life / p.max, 0, 1) * 0.32;
    ctx.globalAlpha = a;
    const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 2.2);
    g.addColorStop(0, p.color);
    g.addColorStop(1, "rgba(190,154,113,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size * 2.2, 0, TAU);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function drawRacers() {
  const selected = racers[4];
  const anchorX = 420 + cameraLead;
  const field = racers.map(r => {
    const rel = (r.distance - selected.distance) * 8.6;
    const x = anchorX + rel;
    const y = roadYFromLane(r.lane);
    const s = roadScaleFromLane(r.lane);
    return { r, x, y, s };
  }).sort((a, b) => a.r.lane - b.r.lane);

  for (const item of field) {
    const { r, x, y, s } = item;
    if (x < -260 || x > W + 260) continue;

    const speedRatio = clamp(r.speed / 36, 0, 1);
    const frameMs = lerp(132, 60, speedRatio);
    const frame = Math.floor((raceTime + r.id * 71) / frameMs) % 6;
    const src = tinted[r.id - 1]?.[frame];
    if (!src) continue;

    const width = (r.selected ? 188 : 174) * s;
    const height = width * (src.height / src.width);
    const bob = Math.sin(raceTime * 0.028 + r.phase) * 2.4 * s;
    const drawX = x - width * 0.50;
    const drawY = y - height + bob;

    // Soft shadow.
    ctx.globalAlpha = 0.22;
    ctx.fillStyle = "#0c1414";
    ctx.beginPath();
    ctx.ellipse(x - width * 0.04, y + 3, width * 0.31, 8 * s, 0, 0, TAU);
    ctx.fill();

    // Subtle motion ghost, not full duplicate.
    if (speedRatio > 0.62) {
      ctx.globalAlpha = 0.06 + (speedRatio - 0.62) * 0.10;
      ctx.drawImage(src, drawX - 18 * s, drawY + 1, width, height);
    }
    ctx.globalAlpha = 1;
    ctx.drawImage(src, drawX, drawY, width, height);

    // Identity stripe.
    ctx.fillStyle = palette[r.id - 1];
    ctx.globalAlpha = 0.92;
    ctx.fillRect(x - 24 * s, y + 10 * s, 48 * s, 4 * s);
    ctx.globalAlpha = 1;

    if (speedRatio > 0.56 && frameCounter % (r.selected ? 2 : 3) === 0) {
      spawnDust(
        drawX + width * 0.17,
        y - 2,
        7.5 * s,
        "rgba(222,188,145,.88)"
      );
    }
  }
}

function drawAtmosphere() {
  const speedRatio = clamp(visualSpeed / 36, 0, 1);
  const vignette = ctx.createRadialGradient(W * 0.52, H * 0.52, H * 0.18, W * 0.52, H * 0.52, H * 0.78);
  vignette.addColorStop(0, "rgba(2,10,15,0)");
  vignette.addColorStop(0.72, "rgba(2,10,15,.04)");
  vignette.addColorStop(1, `rgba(2,10,15,${0.22 + speedRatio * 0.08})`);
  ctx.fillStyle = vignette;
  ctx.fillRect(0, 0, W, H);

  const haze = ctx.createLinearGradient(0, 250, 0, 390);
  haze.addColorStop(0, "rgba(225,239,232,.16)");
  haze.addColorStop(1, "rgba(225,239,232,0)");
  ctx.fillStyle = haze;
  ctx.fillRect(0, 250, W, 150);
}

function render() {
  const speedRatio = clamp(visualSpeed / 36, 0, 1);
  const shakeX = Math.sin(raceTime * 0.034) * cameraShake * 1.15;
  const shakeY = Math.sin(raceTime * 0.048 + 0.8) * cameraShake * 0.75;
  const lean = Math.sin(raceTime * 0.00062) * cameraShake * 0.006;

  ctx.save();
  ctx.translate(W / 2 + shakeX, H / 2 + shakeY);
  ctx.rotate(lean);
  ctx.scale(1 + speedRatio * 0.012, 1 + speedRatio * 0.012);
  ctx.translate(-W / 2, -H / 2);

  skyGradient();
  drawCloudBand(cameraDistance, 0, 0.12);
  drawCloudBand(cameraDistance, 1, 0.08);
  drawMountainLayer(295, 112, 0.42, "#789893", 1);
  drawMountainLayer(330, 72, 0.82, "#5f8275", 1.15);
  drawForest(1.12, 338, "#234d38", "#316043");
  drawFarArchitecture();
  drawTrack();
  drawDust();
  drawRacers();
  drawForegroundSpeed();
  drawAtmosphere();

  ctx.restore();

  frameCounter++;
  stage.dataset.ready = ready ? "true" : "false";
  stage.dataset.mode = "modern-hd-side";
  stage.dataset.field = "s-5";
  stage.dataset.resolution = `${W}x${H}`;
  stage.dataset.frame = String(frameCounter);
}

function loop(now) {
  const dt = clamp((now - last) / 1000, 0, 0.04);
  last = now;
  if (ready) updateRace(dt);
  render();
  requestAnimationFrame(loop);
}

spriteSheet.onload = () => {
  makeTintFrames();
  ready = true;
  stage.dataset.spriteSheet = "loaded";
};
spriteSheet.onerror = () => {
  stage.dataset.spriteSheet = "error";
};

requestAnimationFrame(loop);
