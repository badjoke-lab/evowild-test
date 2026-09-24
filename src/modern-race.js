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

const roadHalf = 5.15;
const cameraHeight = 2.15;
const focal = 820;
const baseHorizon = 248;
const nearZ = 4.6;
const farZ = 188;
const segment = 1.45;

const palette = ["#7edcff", "#ffd26d", "#ff8d9e", "#9ff07d", "#c5a0ff"];
const racers = [
  { id: 1, z: 34, lane: -0.58, speed: 28.0, target: 31.0, phase: 0.1 },
  { id: 2, z: 26, lane:  0.52, speed: 27.4, target: 30.4, phase: 1.2 },
  { id: 3, z: 18, lane: -0.08, speed: 27.8, target: 30.6, phase: 2.4 },
  { id: 4, z: 10, lane:  0.65, speed: 27.1, target: 30.2, phase: 3.5 },
  { id: 5, z:  0, lane: -0.32, speed:  0.0, target: 34.0, phase: 4.6, selected: true }
];

let last = performance.now();
let raceTime = 0;
let cameraZ = -6.2;
let goPlayed = false;
let ready = false;
let frameCounter = 0;
let selected = racers[4];
let visualSpeed = 0;

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
function hash(n) {
  const x = Math.sin(n * 91.173 + 17.77) * 43758.5453;
  return x - Math.floor(x);
}

function roadCenter(z) {
  return Math.sin(z * 0.028) * 3.1 + Math.sin(z * 0.0105 + 1.1) * 1.7;
}
function roadHeight(z) {
  return Math.sin(z * 0.020) * 0.75 + Math.sin(z * 0.006 + 0.4) * 0.42;
}
function curveAt(z) {
  return Math.cos(z * 0.028) * 0.086 + Math.cos(z * 0.0105 + 1.1) * 0.035;
}

function project(absZ, worldX = roadCenter(absZ), worldY = roadHeight(absZ)) {
  const relZ = absZ - cameraZ;
  if (relZ <= 0.15) return null;
  const cameraX = roadCenter(cameraZ);
  const cameraY = roadHeight(cameraZ);
  const s = focal / relZ;
  const horizon = baseHorizon - roadHeight(cameraZ + 30) * 13;
  return {
    z: relZ,
    scale: s,
    x: W * 0.5 + (worldX - cameraX) * s,
    y: horizon + (cameraHeight - (worldY - cameraY)) * s,
    roadW: roadHalf * s
  };
}

function polygon(a, b, c, d, fill) {
  ctx.fillStyle = fill;
  ctx.beginPath();
  ctx.moveTo(a.x, a.y);
  ctx.lineTo(b.x, b.y);
  ctx.lineTo(c.x, c.y);
  ctx.lineTo(d.x, d.y);
  ctx.closePath();
  ctx.fill();
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
      o.imageSmoothingEnabled = true;
      const sx = (i % 3) * fw;
      const sy = Math.floor(i / 3) * fh;
      o.drawImage(spriteSheet, sx, sy, fw, fh, 0, 0, fw, fh);
      o.globalCompositeOperation = "source-atop";
      o.globalAlpha = 0.22;
      o.fillStyle = palette[p];
      o.fillRect(0, 0, fw, fh);
      o.globalCompositeOperation = "source-over";
      o.globalAlpha = 1;
      frames.push(off);
    }
    tinted.push(frames);
  }
}

function drawSky() {
  const grad = ctx.createLinearGradient(0, 0, 0, baseHorizon + 120);
  grad.addColorStop(0, "#62b9d3");
  grad.addColorStop(0.56, "#9ed4df");
  grad.addColorStop(1, "#dbe8dd");
  ctx.fillStyle = grad;
  ctx.fillRect(0, 0, W, H);

  const curveShift = roadCenter(cameraZ) * 20;
  const sunX = 990 - curveShift * 0.18;
  const sunY = 108;
  const sun = ctx.createRadialGradient(sunX, sunY, 2, sunX, sunY, 44);
  sun.addColorStop(0, "rgba(255,248,190,.95)");
  sun.addColorStop(0.35, "rgba(255,234,163,.55)");
  sun.addColorStop(1, "rgba(255,234,163,0)");
  ctx.fillStyle = sun;
  ctx.fillRect(sunX - 48, sunY - 48, 96, 96);

  drawClouds(curveShift);
  drawMountainLayer(baseHorizon + 32, 72, 0.009, "#73958e", curveShift * 0.22);
  drawMountainLayer(baseHorizon + 58, 48, 0.016, "#587b70", curveShift * 0.44);
  drawForestLayer(baseHorizon + 73, curveShift * 0.68);

  const haze = ctx.createLinearGradient(0, baseHorizon - 10, 0, baseHorizon + 100);
  haze.addColorStop(0, "rgba(225,239,231,.30)");
  haze.addColorStop(1, "rgba(225,239,231,0)");
  ctx.fillStyle = haze;
  ctx.fillRect(0, baseHorizon - 10, W, 110);
}

function drawClouds(shift) {
  ctx.save();
  ctx.globalAlpha = 0.18;
  for (let i = 0; i < 9; i++) {
    const x = ((i * 173 + raceTime * 0.003 - shift * 0.15) % (W + 260)) - 130;
    const y = 58 + (i % 4) * 34;
    const r = 24 + (i % 3) * 10;
    const g = ctx.createRadialGradient(x, y, 2, x, y, r * 2.1);
    g.addColorStop(0, "rgba(255,255,255,.95)");
    g.addColorStop(1, "rgba(255,255,255,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(x, y, r * 2.1, r * 0.75, -0.12, 0, TAU);
    ctx.fill();
  }
  ctx.restore();
}

function drawMountainLayer(baseY, amp, freq, color, shift) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, H);
  ctx.lineTo(0, baseY);
  for (let x = 0; x <= W + 8; x += 8) {
    const xx = x + shift;
    const primary = Math.abs(Math.sin(xx * freq)) * amp;
    const secondary = Math.abs(Math.sin(xx * freq * 0.47 + 1.8)) * amp * 0.44;
    ctx.lineTo(x, baseY - primary - secondary);
  }
  ctx.lineTo(W, H);
  ctx.closePath();
  ctx.fill();
}

function drawForestLayer(baseY, shift) {
  const band = ctx.createLinearGradient(0, baseY - 40, 0, baseY + 36);
  band.addColorStop(0, "#315f49");
  band.addColorStop(1, "#214a3a");
  ctx.fillStyle = band;
  ctx.fillRect(0, baseY, W, 44);
  const spacing = 18;
  for (let i = -4; i < Math.ceil(W / spacing) + 4; i++) {
    const x = i * spacing - (shift % spacing);
    const h = 18 + hash(i + 9) * 24;
    ctx.fillStyle = i % 2 ? "#2a5a43" : "#35694c";
    ctx.beginPath();
    ctx.moveTo(x - 8, baseY + 8);
    ctx.lineTo(x, baseY - h);
    ctx.lineTo(x + 8, baseY + 8);
    ctx.fill();
  }
}

function roadStripe(absZ, period, a, b) {
  return Math.floor(absZ / period) % 2 ? a : b;
}

function drawRoad() {
  let farther = project(cameraZ + farZ);
  let crestClip = baseHorizon + 4;

  for (let z = cameraZ + farZ - segment; z > cameraZ + nearZ; z -= segment) {
    const nearer = project(z);
    if (!nearer || !farther) {
      farther = nearer;
      continue;
    }

    if (nearer.y <= farther.y + 0.2) {
      farther = nearer;
      continue;
    }

    const yFar = Math.max(crestClip, farther.y);
    const yNear = Math.min(H + 30, nearer.y);
    if (yNear <= yFar) {
      farther = nearer;
      continue;
    }

    ctx.fillStyle = roadStripe(z, 8.0, "#4d8150", "#477749");
    ctx.fillRect(0, yFar, W, yNear - yFar + 1);

    const shoulderFar = farther.roadW * 1.115;
    const shoulderNear = nearer.roadW * 1.115;
    polygon(
      { x: farther.x - shoulderFar, y: yFar },
      { x: farther.x + shoulderFar, y: yFar },
      { x: nearer.x + shoulderNear, y: yNear },
      { x: nearer.x - shoulderNear, y: yNear },
      roadStripe(z, 5.1, "#f3ead5", "#cc5b4d")
    );

    polygon(
      { x: farther.x - farther.roadW, y: yFar },
      { x: farther.x + farther.roadW, y: yFar },
      { x: nearer.x + nearer.roadW, y: yNear },
      { x: nearer.x - nearer.roadW, y: yNear },
      roadStripe(z, 13.5, "#665f59", "#6f6860")
    );

    const edgeGlow = nearer.z < 48 ? 0.13 * (1 - nearer.z / 48) : 0;
    if (edgeGlow > 0) {
      ctx.globalAlpha = edgeGlow;
      polygon(
        { x: farther.x - farther.roadW * 0.97, y: yFar },
        { x: farther.x + farther.roadW * 0.97, y: yFar },
        { x: nearer.x + nearer.roadW * 0.97, y: yNear },
        { x: nearer.x - nearer.roadW * 0.97, y: yNear },
        "#fff7dd"
      );
      ctx.globalAlpha = 1;
    }

    if (Math.floor(z / 4.6) % 3 !== 0) {
      for (let lane = 1; lane < 4; lane++) {
        const t = lane / 4;
        const lxFar = lerp(farther.x - farther.roadW, farther.x + farther.roadW, t);
        const lxNear = lerp(nearer.x - nearer.roadW, nearer.x + nearer.roadW, t);
        const mwFar = Math.max(0.7, farther.roadW * 0.008);
        const mwNear = Math.max(1.2, nearer.roadW * 0.008);
        polygon(
          { x: lxFar - mwFar, y: yFar },
          { x: lxFar + mwFar, y: yFar },
          { x: lxNear + mwNear, y: yNear },
          { x: lxNear - mwNear, y: yNear },
          "#efe8d5"
        );
      }
    }

    drawRoadside(z, nearer);
    drawNearMotionMarkers(z, farther, nearer, yFar, yNear);

    farther = nearer;
    crestClip = Math.max(crestClip, yFar);
  }
}

function drawNearMotionMarkers(z, farP, nearP, yFar, yNear) {
  if (nearP.z > 44 || Math.floor(z / 2.2) % 2) return;
  const alpha = 0.10 + (1 - nearP.z / 44) * 0.22;
  ctx.globalAlpha = alpha;
  for (const side of [-1, 1]) {
    const xf = farP.x + side * farP.roadW * 1.30;
    const xn = nearP.x + side * nearP.roadW * 1.30;
    const wf = Math.max(0.8, farP.roadW * 0.012);
    const wn = Math.max(2.0, nearP.roadW * 0.016);
    polygon(
      { x: xf - wf, y: yFar },
      { x: xf + wf, y: yFar },
      { x: xn + wn, y: yNear },
      { x: xn - wn, y: yNear },
      "#d7edcf"
    );
  }
  ctx.globalAlpha = 1;
}

function drawRoadside(z, p) {
  if (p.z > 132) return;
  const band = Math.floor(z / 5.4);
  if (band % 2 !== 0) return;

  const side = band % 4 < 2 ? -1 : 1;
  const x = roadCenter(z) + side * roadHalf * (band % 9 === 0 ? 1.74 : 1.48);
  const q = project(z, x, roadHeight(z));
  if (!q || q.y < baseHorizon - 8 || q.y > H + 40) return;

  const scale = clamp(q.scale * 0.20, 0.12, 2.6);
  if (band % 9 === 0) drawTree(q.x, q.y, scale, band);
  else drawReflector(q.x, q.y, scale, band);
}

function drawTree(x, y, s, seed) {
  const h = 92 * s;
  const w = 46 * s;
  ctx.save();
  ctx.translate(x, y);
  ctx.fillStyle = "rgba(25,31,26,.28)";
  ctx.beginPath();
  ctx.ellipse(0, 4, w * 0.55, Math.max(2, 5 * s), 0, 0, TAU);
  ctx.fill();

  ctx.fillStyle = "#5a4230";
  ctx.fillRect(-4 * s, -h * 0.55, 8 * s, h * 0.58);

  const greens = seed % 2 ? ["#2b6b45", "#3c8152"] : ["#2a6340", "#39794d"];
  for (let i = 0; i < 3; i++) {
    const cy = -h * (0.40 + i * 0.19);
    const r = w * (0.48 - i * 0.07);
    const g = ctx.createRadialGradient(-r * 0.15, cy - r * 0.25, r * 0.08, 0, cy, r);
    g.addColorStop(0, greens[1]);
    g.addColorStop(1, greens[0]);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(0, cy, r, 0, TAU);
    ctx.fill();
  }
  ctx.restore();
}

function drawReflector(x, y, s, seed) {
  const h = 30 * s;
  const w = Math.max(2, 4 * s);
  ctx.fillStyle = "#e9eee9";
  ctx.fillRect(x - w / 2, y - h, w, h);
  ctx.fillStyle = seed % 4 === 0 ? "#f4c661" : "#42535d";
  ctx.fillRect(x - w * 1.5, y - h * 0.78, w * 3, Math.max(2, 5 * s));
}

const particles = [];
function spawnDust(x, y, size, hue) {
  particles.push({
    x, y,
    vx: -10 + Math.random() * 20,
    vy: -5 - Math.random() * 9,
    life: 0.45 + Math.random() * 0.25,
    max: 0.7,
    size,
    hue
  });
  if (particles.length > 80) particles.shift();
}
function updateParticles(dt) {
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.life -= dt;
    p.x += p.vx * dt;
    p.y += p.vy * dt;
    p.size *= 1 + dt * 0.9;
    if (p.life <= 0) particles.splice(i, 1);
  }
}
function drawParticles() {
  for (const p of particles) {
    const a = clamp(p.life / p.max, 0, 1) * 0.32;
    ctx.globalAlpha = a;
    const g = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 2.2);
    g.addColorStop(0, p.hue);
    g.addColorStop(1, "rgba(180,145,108,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.size * 2.2, 0, TAU);
    ctx.fill();
  }
  ctx.globalAlpha = 1;
}

function racerTargetSpeed(r) {
  const t = raceTime / 1000;
  if (r.selected) return 34.5;
  return r.target + Math.sin(t * 0.64 + r.phase) * 1.6 + Math.sin(t * 1.33 + r.id) * 0.7;
}

function updateRace(dt) {
  raceTime += dt * 1000;

  for (const r of racers) {
    const target = racerTargetSpeed(r);
    const accel = r.selected ? (raceTime < 1600 ? 17.5 : 6.5) : 3.8;
    r.speed = lerp(r.speed, target, clamp(dt * accel * 0.16, 0, 1));
    r.z += r.speed * dt * (r.selected ? 1.78 : 1.72);

    if (!r.selected) {
      const laneTarget = Math.sin(raceTime * 0.00023 + r.phase) * 0.64;
      r.lane = lerp(r.lane, laneTarget, dt * 0.14);
    } else {
      r.lane = lerp(r.lane, Math.sin(raceTime * 0.00018) * 0.13 - 0.12, dt * 0.10);
    }
  }

  selected = racers.find(r => r.selected);
  visualSpeed = lerp(visualSpeed, selected.speed, clamp(dt * 3.5, 0, 1));
  cameraZ = selected.z - 6.3;

  updateParticles(dt);

  if (!goPlayed && raceTime > 740) {
    goPlayed = true;
    goEl.classList.remove("play");
    void goEl.offsetWidth;
    goEl.classList.add("play");
  }

  const order = [...racers].sort((a, b) => b.z - a.z);
  const place = order.findIndex(r => r.selected) + 1;
  placeEl.textContent = `${place} / 5`;
  speedEl.textContent = String(Math.round(visualSpeed * 8.4)).padStart(3, "0");
  phaseEl.textContent = raceTime < 2300 ? "LAUNCH" : place <= 2 ? "ATTACK" : "CHASE";
}

function drawRacers() {
  const draw = [];
  for (const r of racers) {
    const x = roadCenter(r.z) + r.lane * roadHalf * 0.84;
    const p = project(r.z, x, roadHeight(r.z));
    if (!p || p.z < 2.3 || p.z > 130) continue;
    draw.push({ r, p });
  }
  draw.sort((a, b) => b.p.z - a.p.z);

  for (const item of draw) {
    const { r, p } = item;
    const speedRatio = clamp(r.speed / 35, 0, 1);
    const frameMs = lerp(132, 64, speedRatio);
    const frame = Math.floor((raceTime + r.id * 73) / frameMs) % 6;
    const src = tinted[r.id - 1]?.[frame];
    if (!src) continue;

    let width = clamp(p.scale * (r.selected ? 2.28 : 2.10), 22, r.selected ? 220 : 180);
    let height = width * (src.height / src.width);
    const bob = Math.sin(raceTime * 0.027 + r.phase) * Math.min(4, width * 0.016);
    const x = p.x - width / 2;
    const y = p.y - height + bob;

    ctx.globalAlpha = 0.28;
    ctx.fillStyle = "#101919";
    ctx.beginPath();
    ctx.ellipse(p.x, p.y + 3, width * 0.34, Math.max(3, width * 0.055), 0, 0, TAU);
    ctx.fill();

    if (speedRatio > 0.62) {
      ctx.globalAlpha = 0.10 + (speedRatio - 0.62) * 0.24;
      ctx.drawImage(src, x - width * 0.09, y + 1, width, height);
      ctx.globalAlpha = 0.07 + (speedRatio - 0.62) * 0.16;
      ctx.drawImage(src, x - width * 0.16, y + 2, width, height);
    }

    ctx.globalAlpha = 1;
    ctx.drawImage(src, x, y, width, height);

    const barW = Math.max(18, width * 0.21);
    const barH = Math.max(3, width * 0.025);
    ctx.fillStyle = palette[r.id - 1];
    ctx.fillRect(p.x - barW / 2, p.y - height * 0.10, barW, barH);

    if (r.selected && frameCounter % 2 === 0 && speedRatio > 0.50) {
      spawnDust(
        p.x - width * 0.18,
        p.y - Math.max(4, width * 0.015),
        Math.max(4, width * 0.045),
        "rgba(224,190,145,.9)"
      );
    }
  }
}

function drawSpeedFX() {
  const ratio = clamp(visualSpeed / 35, 0, 1);
  const strength = smoothstep(0.48, 0.96, ratio);

  if (strength > 0) {
    ctx.save();
    ctx.globalCompositeOperation = "screen";
    for (let i = 0; i < 28; i++) {
      const side = i % 2 ? -1 : 1;
      const yy = 260 + ((i * 31 + raceTime * (0.11 + (i % 5) * 0.009)) % 430);
      const len = 18 + strength * (48 + (i % 7) * 13);
      const x = side < 0 ? 0 : W - len;
      const g = ctx.createLinearGradient(side < 0 ? 0 : W, yy, side < 0 ? len : W - len, yy);
      g.addColorStop(0, "rgba(220,247,241,0)");
      g.addColorStop(1, `rgba(220,247,241,${0.06 + strength * 0.12})`);
      ctx.fillStyle = g;
      ctx.fillRect(x, yy, len, 1 + (i % 3 === 0 ? 1 : 0));
    }
    ctx.restore();
  }

  const vignette = ctx.createRadialGradient(W / 2, H * 0.50, H * 0.16, W / 2, H * 0.50, H * 0.76);
  vignette.addColorStop(0, "rgba(3,12,18,0)");
  vignette.addColorStop(0.72, "rgba(3,12,18,.04)");
  vignette.addColorStop(1, `rgba(3,12,18,${0.22 + strength * 0.10})`);
  ctx.fillStyle = vignette;
  ctx.fillRect(0, 0, W, H);
}

function render() {
  const speedRatio = clamp(visualSpeed / 35, 0, 1);
  const bank = clamp(curveAt(selected.z + 14) * speedRatio * 0.42, -0.038, 0.038);
  const shakeX = speedRatio > 0.72 ? Math.sin(raceTime * 0.031) * 0.85 : 0;
  const shakeY = speedRatio > 0.72 ? Math.sin(raceTime * 0.041 + 0.8) * 0.65 : 0;

  ctx.save();
  ctx.translate(W / 2 + shakeX, H / 2 + shakeY);
  ctx.rotate(bank);
  ctx.translate(-W / 2, -H / 2);

  drawSky();
  drawRoad();
  drawParticles();
  drawRacers();
  drawSpeedFX();

  ctx.restore();

  frameCounter++;
  stage.dataset.ready = ready ? "true" : "false";
  stage.dataset.mode = "modern-hd";
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
