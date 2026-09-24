const canvas = document.querySelector("#motionCanvas");
const ctx = canvas.getContext("2d", { alpha: false, desynchronized: true });
const stage = document.querySelector("#stage");
const assetStatus = document.querySelector("#assetStatus");

const BASE = import.meta.env.BASE_URL || "/";
const params = new URLSearchParams(location.search);
const PLAYBACK_RATE = params.has("slow") ? 0.35 : 1;

let width = 1;
let height = 1;
let dpr = 1;
let last = performance.now();
let elapsed = 0;
let worldTravel = 0;
let sheetReady = false;
let frameMeta = [];

const sheet = new Image();
sheet.decoding = "async";
sheet.src = BASE + "concept/s-run-sheet.webp";

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = t => t * t * (3 - 2 * t);

const PHASES = [
  { name:"CONTACT",  col:0, row:0, duration:68,  lift:0,   pitch:1.8,  x:-3, scaleX:.995, scaleY:1.01 },
  { name:"PUSH",     col:1, row:0, duration:82,  lift:4,   pitch:-.7,  x:1,  scaleX:1.015, scaleY:.995 },
  { name:"RECOVERY", col:2, row:0, duration:86,  lift:15,  pitch:-2.4, x:5,  scaleX:1.025, scaleY:.985 },
  { name:"FLIGHT",   col:0, row:1, duration:118, lift:29,  pitch:-1.4, x:8,  scaleX:1.035, scaleY:.98 },
  { name:"REACH",    col:1, row:1, duration:92,  lift:17,  pitch:.7,   x:5,  scaleX:1.025, scaleY:.99 },
  { name:"LAND",     col:2, row:1, duration:74,  lift:2,   pitch:2.7,  x:0,  scaleX:1.0,   scaleY:1.01 }
];
const CYCLE_MS = PHASES.reduce((sum, p) => sum + p.duration, 0);

function resize() {
  const r = canvas.getBoundingClientRect();
  width = Math.max(320, Math.floor(r.width));
  height = Math.max(360, Math.floor(r.height));
  dpr = Math.min(window.devicePixelRatio || 1, 1.75);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.imageSmoothingEnabled = true;
  ctx.imageSmoothingQuality = "high";
}

new ResizeObserver(resize).observe(canvas);
resize();

function analyzeFrame(col, row) {
  const fw = Math.floor(sheet.naturalWidth / 3);
  const fh = Math.floor(sheet.naturalHeight / 2);
  const temp = document.createElement("canvas");
  temp.width = fw;
  temp.height = fh;
  const tctx = temp.getContext("2d", { willReadFrequently: true });
  tctx.clearRect(0, 0, fw, fh);
  tctx.drawImage(sheet, col * fw, row * fh, fw, fh, 0, 0, fw, fh);

  const data = tctx.getImageData(0, 0, fw, fh).data;
  let minX = fw, minY = fh, maxX = 0, maxY = 0;
  const rowCounts = new Uint16Array(fh);

  for (let y = 0; y < fh; y++) {
    for (let x = 0; x < fw; x++) {
      const a = data[(y * fw + x) * 4 + 3];
      if (a < 28) continue;
      minX = Math.min(minX, x);
      maxX = Math.max(maxX, x);
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      rowCounts[y]++;
    }
  }

  // Ignore one-pixel debris when finding the visual ground anchor.
  let robustBottom = maxY;
  for (let y = fh - 1; y >= 0; y--) {
    if (rowCounts[y] >= 5) {
      robustBottom = y;
      break;
    }
  }

  const padX = Math.max(2, Math.round(fw * .012));
  const padY = Math.max(2, Math.round(fh * .012));
  minX = clamp(minX - padX, 0, fw - 1);
  maxX = clamp(maxX + padX, minX + 1, fw - 1);
  minY = clamp(minY - padY, 0, fh - 1);
  robustBottom = clamp(robustBottom + padY, minY + 1, fh - 1);

  return {
    sx: col * fw + minX,
    sy: row * fh + minY,
    sw: maxX - minX + 1,
    sh: robustBottom - minY + 1,
    rawBottom: robustBottom,
    cellW: fw,
    cellH: fh
  };
}

sheet.onload = () => {
  frameMeta = PHASES.map(p => analyzeFrame(p.col, p.row));
  sheetReady = true;
  stage.dataset.rigReady = "true";
  stage.dataset.frameSource = "s-run-sheet";
  stage.dataset.motionPhase = "CONTACT";
  assetStatus.textContent = "S run frames ready";
};

sheet.onerror = () => {
  stage.dataset.rigReady = "error";
  stage.dataset.motionPhase = "error";
  assetStatus.textContent = "S run frames failed";
};

function phaseState(ms) {
  const cycle = ((ms % CYCLE_MS) + CYCLE_MS) % CYCLE_MS;
  let cursor = 0;
  for (let i = 0; i < PHASES.length; i++) {
    const phase = PHASES[i];
    const end = cursor + phase.duration;
    if (cycle < end) {
      const t = (cycle - cursor) / phase.duration;
      return { index:i, phase, t, cycle };
    }
    cursor = end;
  }
  return { index:0, phase:PHASES[0], t:0, cycle:0 };
}

function drawBackground(speedNorm) {
  const horizon = height * .61;
  const sky = ctx.createLinearGradient(0, 0, 0, horizon);
  sky.addColorStop(0, "#91aeb8");
  sky.addColorStop(.58, "#c5c9bd");
  sky.addColorStop(1, "#d7c6a5");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, width, horizon);

  const sunX = width * .78;
  const sunY = height * .19;
  const sunR = Math.max(34, width * .036);
  const glow = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR * 3);
  glow.addColorStop(0, "rgba(255,244,207,.82)");
  glow.addColorStop(1, "rgba(255,244,207,0)");
  ctx.fillStyle = glow;
  ctx.fillRect(sunX - sunR * 3, sunY - sunR * 3, sunR * 6, sunR * 6);

  const drawRidge = (baseY, amp, speed, fill) => {
    const shift = worldTravel * speed;
    ctx.fillStyle = fill;
    ctx.beginPath();
    ctx.moveTo(0, height);
    ctx.lineTo(0, baseY);
    for (let x = 0; x <= width + 45; x += 45) {
      const wx = x + shift;
      const n = .45 + .55 * Math.abs(Math.sin(wx * .009) * Math.cos(wx * .0037));
      ctx.lineTo(x, baseY - amp * n);
    }
    ctx.lineTo(width, height);
    ctx.closePath();
    ctx.fill();
  };

  drawRidge(height * .58, 75, .07, "#6d8383");
  drawRidge(height * .62, 47, .13, "#536f60");

  const trackTop = height * .72;
  const ground = ctx.createLinearGradient(0, horizon, 0, trackTop);
  ground.addColorStop(0, "#59645d");
  ground.addColorStop(1, "#394840");
  ctx.fillStyle = ground;
  ctx.fillRect(0, horizon, width, trackTop - horizon);

  const trackGrad = ctx.createLinearGradient(0, trackTop, 0, height);
  trackGrad.addColorStop(0, "#555b5e");
  trackGrad.addColorStop(1, "#30363a");
  ctx.fillStyle = trackGrad;
  ctx.fillRect(0, trackTop, width, height - trackTop);

  const spacing = width < 700 ? 80 : 116;
  const shift = (worldTravel * (1.1 + speedNorm * 2.1)) % spacing;
  ctx.strokeStyle = "rgba(229,235,236,.18)";
  ctx.lineWidth = 1.2;
  for (let x = -spacing; x < width + spacing; x += spacing) {
    const sx = x - shift;
    const len = 28 + speedNorm * 76;
    ctx.beginPath();
    ctx.moveTo(sx, trackTop + 37);
    ctx.lineTo(sx - len, trackTop + 37);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(sx + spacing * .41, trackTop + 94);
    ctx.lineTo(sx + spacing * .41 - len * 1.25, trackTop + 94);
    ctx.stroke();
  }

  ctx.save();
  ctx.globalAlpha = .12 + speedNorm * .12;
  ctx.strokeStyle = "rgba(239,246,245,.72)";
  for (let i = 0; i < (width < 700 ? 12 : 20); i++) {
    const band = (i % 6) / 6;
    const y = height * (.76 + band * .20);
    const x = ((i * 137 - worldTravel * 2.7) % (width + 240)) + width;
    const len = 50 + speedNorm * 115 + band * 35;
    ctx.lineWidth = .6 + band * 1.1;
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.lineTo(x - len, y + 2);
    ctx.stroke();
  }
  ctx.restore();
}

function drawShadow(cx, groundY, lift, spriteW) {
  const liftNorm = clamp(lift / 30, 0, 1);
  ctx.save();
  ctx.globalAlpha = .30 - liftNorm * .13;
  ctx.fillStyle = "#091014";
  ctx.beginPath();
  ctx.ellipse(
    cx - spriteW * .02,
    groundY + 7,
    spriteW * (.22 - liftNorm * .025),
    Math.max(6, spriteW * (.032 - liftNorm * .008)),
    0, 0, Math.PI * 2
  );
  ctx.fill();
  ctx.restore();
}

function drawDust(cx, groundY, strength, spriteW) {
  if (strength <= 0) return;
  ctx.save();
  ctx.globalAlpha = .13 * strength;
  ctx.fillStyle = "#d7c3a1";
  for (let i = 0; i < 4; i++) {
    ctx.beginPath();
    ctx.ellipse(
      cx - spriteW * (.20 + i * .055),
      groundY + 2 + i,
      spriteW * (.035 + i * .012),
      Math.max(2, spriteW * (.009 + i * .002)),
      0, 0, Math.PI * 2
    );
    ctx.fill();
  }
  ctx.restore();
}

function drawFrame(index, cx, groundY, alpha = 1, trailX = 0, extraBlur = 0) {
  if (!sheetReady) return;
  const phase = PHASES[index];
  const meta = frameMeta[index];
  const targetCreatureW = clamp(
    Math.min(width * .54, height * .78),
    width < 560 ? 285 : 360,
    640
  );
  const scale = targetCreatureW / meta.sw;
  const drawW = meta.sw * scale * phase.scaleX;
  const drawH = meta.sh * scale * phase.scaleY;
  const liftPx = phase.lift * scale * .64;
  const x = cx - drawW * .50 + phase.x * scale * .28 + trailX;
  const y = groundY - drawH - liftPx;

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(cx + trailX, groundY - liftPx);
  ctx.rotate(phase.pitch * Math.PI / 180);
  ctx.translate(-(cx + trailX), -(groundY - liftPx));
  if (extraBlur) ctx.filter = "blur(" + extraBlur + "px)";
  ctx.drawImage(
    sheet,
    meta.sx, meta.sy, meta.sw, meta.sh,
    x, y, drawW, drawH
  );
  ctx.restore();

  return { drawW, drawH, liftPx, x, y };
}

function renderCreature(state) {
  const { index, phase, t } = state;
  const groundY = height * (height > width * 1.15 ? .80 : .82);
  const cx = width * .51;

  const meta = frameMeta[index];
  const targetCreatureW = clamp(
    Math.min(width * .54, height * .78),
    width < 560 ? 285 : 360,
    640
  );
  const spriteW = targetCreatureW;

  drawShadow(cx, groundY, phase.lift, spriteW);

  // A short, blurred echo from the preceding complete pose reads as speed,
  // without dismembering the creature into rotating limb cards.
  const prev = (index + PHASES.length - 1) % PHASES.length;
  if (phase.name !== "CONTACT" && phase.name !== "LAND") {
    drawFrame(prev, cx, groundY, .075, -12 - t * 8, 1.2);
  }

  const draw = drawFrame(index, cx, groundY, 1, 0, 0);

  const dust =
    phase.name === "CONTACT" ? 1 - t * .45 :
    phase.name === "PUSH" ? .72 * (1 - t) :
    phase.name === "LAND" ? .75 * t :
    0;
  drawDust(cx, groundY, dust, spriteW);

  stage.dataset.motionPhase = phase.name;
  stage.dataset.phaseProgress = t.toFixed(3);
  stage.dataset.frameIndex = String(index);
  stage.dataset.flight = phase.name === "RECOVERY" || phase.name === "FLIGHT" || phase.name === "REACH" ? "true" : "false";
  stage.dataset.groundAnchorY = groundY.toFixed(1);
  stage.dataset.spriteBottomY = (draw.y + draw.drawH).toFixed(1);
  stage.dataset.visualLift = draw.liftPx.toFixed(1);
  stage.dataset.bodyPitch = phase.pitch.toFixed(2);
  stage.dataset.frameWidth = meta.sw.toFixed(0);
  stage.dataset.frameHeight = meta.sh.toFixed(0);
}

function render() {
  const state = phaseState(elapsed);
  drawBackground(.94);
  if (sheetReady) renderCreature(state);

  if (state.phase.name === "FLIGHT") {
    const vignette = ctx.createRadialGradient(
      width * .52, height * .54, height * .17,
      width * .52, height * .54, width * .73
    );
    vignette.addColorStop(0, "rgba(0,0,0,0)");
    vignette.addColorStop(1, "rgba(0,5,8,.09)");
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, width, height);
  }
}

function frame(now) {
  const dt = clamp(now - last, 0, 45);
  last = now;
  elapsed += dt * PLAYBACK_RATE;
  worldTravel += dt * .48 * PLAYBACK_RATE;
  render();
  requestAnimationFrame(frame);
}

requestAnimationFrame(now => {
  last = now;
  frame(now);
});
