/*
 * EvoWild Run — lane 5 pseudo-3D race proof.
 * Road projection / segment rendering foundation follows the vendored
 * jakesgordon/javascript-racer MIT implementation in /vendor/javascript-racer/.
 */

const Util = {
  limit(value, min, max) { return Math.max(min, Math.min(value, max)); },
  percentRemaining(n, total) { return (n % total) / total; },
  interpolate(a, b, percent) { return a + (b - a) * percent; },
  easeIn(a, b, percent) { return a + (b - a) * Math.pow(percent, 2); },
  easeInOut(a, b, percent) { return a + (b - a) * ((-Math.cos(percent * Math.PI) / 2) + 0.5); },
  exponentialFog(distance, density) { return 1 / Math.pow(Math.E, distance * distance * density); },
  project(p, cameraX, cameraY, cameraZ, cameraDepth, viewWidth, viewHeight, projectedRoadWidth) {
    p.camera.x = (p.world.x || 0) - cameraX;
    p.camera.y = (p.world.y || 0) - cameraY;
    p.camera.z = (p.world.z || 0) - cameraZ;
    p.screen.scale = cameraDepth / p.camera.z;
    p.screen.x = Math.round((viewWidth / 2) + (p.screen.scale * p.camera.x * viewWidth / 2));
    p.screen.y = Math.round((viewHeight / 2) - (p.screen.scale * p.camera.y * viewHeight / 2));
    p.screen.w = Math.round(p.screen.scale * projectedRoadWidth * viewWidth / 2);
  }
};

const Render = {
  polygon(context, x1, y1, x2, y2, x3, y3, x4, y4, color) {
    context.fillStyle = color;
    context.beginPath();
    context.moveTo(x1, y1);
    context.lineTo(x2, y2);
    context.lineTo(x3, y3);
    context.lineTo(x4, y4);
    context.closePath();
    context.fill();
  },
  segment(context, viewWidth, laneCount, x1, y1, w1, x2, y2, w2, fog, color) {
    const r1 = Render.rumbleWidth(w1, laneCount);
    const r2 = Render.rumbleWidth(w2, laneCount);
    const l1 = Render.laneMarkerWidth(w1, laneCount);
    const l2 = Render.laneMarkerWidth(w2, laneCount);

    context.fillStyle = color.grass;
    context.fillRect(0, y2, viewWidth, y1 - y2);

    Render.polygon(context, x1-w1-r1, y1, x1-w1, y1, x2-w2, y2, x2-w2-r2, y2, color.rumble);
    Render.polygon(context, x1+w1+r1, y1, x1+w1, y1, x2+w2, y2, x2+w2+r2, y2, color.rumble);
    Render.polygon(context, x1-w1, y1, x1+w1, y1, x2+w2, y2, x2-w2, y2, color.road);

    if (color.lane) {
      const laneW1 = w1 * 2 / laneCount;
      const laneW2 = w2 * 2 / laneCount;
      let laneX1 = x1 - w1 + laneW1;
      let laneX2 = x2 - w2 + laneW2;
      for (let lane = 1; lane < laneCount; lane++, laneX1 += laneW1, laneX2 += laneW2) {
        Render.polygon(context, laneX1-l1/2, y1, laneX1+l1/2, y1, laneX2+l2/2, y2, laneX2-l2/2, y2, color.lane);
      }
    }

    Render.fog(context, 0, y1, viewWidth, y2 - y1, fog);
  },
  fog(context, x, y, w, h, fog) {
    if (fog < 1) {
      context.globalAlpha = 1 - fog;
      context.fillStyle = COLORS.FOG;
      context.fillRect(x, y, w, h);
      context.globalAlpha = 1;
    }
  },
  rumbleWidth(projectedRoadWidth, laneCount) {
    return projectedRoadWidth / Math.max(6, 2 * laneCount);
  },
  laneMarkerWidth(projectedRoadWidth, laneCount) {
    return projectedRoadWidth / Math.max(32, 8 * laneCount);
  }
};

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

const ambientTexture = new Image();
ambientTexture.decoding = "async";
ambientTexture.src = BASE + "upstream/js-racer-turbo/low_ambient.png";

const objectTexture = new Image();
objectTexture.decoding = "async";
objectTexture.src = BASE + "upstream/js-racer-turbo/low_objects.png";

const BACKGROUND = {
  SKY: { x:20, y:2062, w:1280, h:640 },
  HILLS: { x:20, y:2744, w:1280, h:640 },
  TREES: { x:20, y:3424, w:1280, h:640 }
};

const ENV_SPRITES = [
  { x:619, y:21, w:277, h:690, scale:0.52 },
  { x:1105, y:80, w:378, h:377, scale:0.58 },
  { x:1149, y:489, w:334, h:344, scale:0.62 },
  { x:906, y:21, w:189, h:437, scale:0.64 },
  { x:906, y:488, w:234, h:474, scale:0.62 },
  { x:293, y:754, w:277, h:142, scale:0.52 },
  { x:346, y:904, w:223, h:212, scale:0.54 },
  { x:335, y:1124, w:235, h:212, scale:0.54 },
  { x:1213, y:845, w:271, h:239, scale:0.48 },
  { x:907, y:1187, w:224, h:147, scale:0.52 },
  { x:1142, y:1094, w:342, h:240, scale:0.46 }
];

const lanes = 3;
const roadWidth = 2200;
const segmentLength = 200;
const rumbleLength = 6;
const drawDistance = 330;
const maxSpeed = 16500;
const accel = 7600;
const decel = 9200;
const selectedId = 6;
const raceMeters = 1800;
const playerZ = 920;
const SPRITE_WORLD_SCALE = 0.00072;
const ENV_WORLD_SCALE = 0.00030;

const COLORS = {
  FOG:"#180028",
  LIGHT: { road:"#10121a", grass:"#4c075e", rumble:"#0ee7ff", lane:"#d9fbff" },
  DARK:  { road:"#0b0d14", grass:"#2a053f", rumble:"#ff38dc", lane:"#9eeeff" },
  START: { road:"#19142c", grass:"#4c075e", rumble:"#ffffff", lane:"#ffffff" },
  FINISH:{ road:"#05060a", grass:"#2a053f", rumble:"#ffffff", lane:"#ffffff" }
};
window.COLORS = COLORS;

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
  const baseColor = Math.floor(n / rumbleLength) % 2 ? COLORS.DARK : COLORS.LIGHT;
  const laneDashOn = Math.floor(n / 4) % 2 === 0;
  segments.push({
    index:n,
    p1:{ world:{ y:lastY(), z:n * segmentLength }, camera:{}, screen:{} },
    p2:{ world:{ y, z:(n + 1) * segmentLength }, camera:{}, screen:{} },
    curve,
    color:{ ...baseColor, lane: laneDashOn ? baseColor.lane : null },
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
  addRoad(8, 14, 8, 0, 0);
  addRoad(10, 28, 10, 5.2, 8);
  addRoad(10, 24, 10, -4.4, -5);
  const curves = [4.8,-5.6,3.4,6.0,-4.2,5.2,-6.4,4.6,-3.8,5.8,-4.9,6.2,-3.6];
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
  startZ = playerZ + segmentLength * 6;
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

function drawProceduralBackground(position, curve, speedNorm) {
  const sky = ctx.createLinearGradient(0, 0, 0, height * 0.72);
  sky.addColorStop(0, "#6ca8c8");
  sky.addColorStop(0.47, "#a8c3cb");
  sky.addColorStop(1, "#d6c39c");
  ctx.fillStyle = sky;
  ctx.fillRect(-20, -20, width + 40, height + 40);

  const horizon = height * (0.38 - speedNorm * 0.025);
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

function drawBackdropLayer(layer, rotation, offsetY, destH, alpha = 1) {
  const imageW = layer.w / 2;
  const sourceX = layer.x + Math.floor(layer.w * (((rotation % 1) + 1) % 1));
  const sourceW = Math.min(imageW, layer.x + layer.w - sourceX);
  const destW = Math.floor(width * (sourceW / imageW));

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.drawImage(ambientTexture, sourceX, layer.y, sourceW, layer.h, 0, offsetY, destW, destH);
  if (sourceW < imageW) {
    ctx.drawImage(
      ambientTexture,
      layer.x,
      layer.y,
      imageW - sourceW,
      layer.h,
      destW - 1,
      offsetY,
      width - destW + 2,
      destH
    );
  }
  ctx.restore();
}

function drawBackground(position, curve, speedNorm) {
  if (!ambientTexture.complete || !ambientTexture.naturalWidth) {
    drawProceduralBackground(position, curve, speedNorm);
    return;
  }

  const curveShift = curve * 0.012;
  const vertical = -height * 0.10 - speedNorm * height * 0.012;
  drawBackdropLayer(BACKGROUND.SKY, position * 0.0000014 + curveShift * 0.14, vertical, height * 1.04, 1);
  drawBackdropLayer(BACKGROUND.HILLS, position * 0.0000044 + curveShift * 0.62, vertical + height * 0.01, height * 1.06, 1);
  drawBackdropLayer(BACKGROUND.TREES, position * 0.0000105 + curveShift, vertical + height * 0.035, height * 1.08, 1);

  const horizonShade = ctx.createLinearGradient(0, height * 0.28, 0, height * 0.70);
  horizonShade.addColorStop(0, "rgba(8,4,18,0)");
  horizonShade.addColorStop(0.72, "rgba(14,2,27,.12)");
  horizonShade.addColorStop(1, "rgba(9,0,18,.34)");
  ctx.fillStyle = horizonShade;
  ctx.fillRect(0, height * 0.26, width, height * 0.46);
}

function drawEnvironmentSprite(segment, index) {
  if (!objectTexture.complete || !objectTexture.naturalWidth) return;
  if (index % 11 !== 0 && index % 17 !== 0) return;
  const source = ENV_SPRITES[Math.abs((index * 7 + 3) % ENV_SPRITES.length)];
  const side = index % 2 === 0 ? -1 : 1;
  const offset = side * (1.42 + ((index * 17) % 31) / 100);
  const scale = segment.p1.screen.scale;
  const pxScale = scale * width / 2 * (ENV_WORLD_SCALE * roadWidth) * source.scale;
  let destW = source.w * pxScale;
  let destH = source.h * pxScale;
  if (destW < 2 || destH < 3) return;

  const maxH = height * 0.46;
  if (destH > maxH) {
    const k = maxH / destH;
    destW *= k;
    destH *= k;
  }

  const x = segment.p1.screen.x + scale * offset * roadWidth * width / 2;
  const y = segment.p1.screen.y;
  const clipY = segment.clip;
  const clipH = Number.isFinite(clipY) ? Math.max(0, y - clipY) : 0;
  const visibleH = Math.max(0, destH - clipH);
  if (visibleH <= 0) return;

  ctx.drawImage(
    objectTexture,
    source.x,
    source.y,
    source.w,
    source.h * (visibleH / destH),
    x - destW / 2,
    y - destH,
    destW,
    visibleH
  );
}

function drawRoadside(segment, index, speedNorm) {
  if (!segment.p1.screen.scale || segment.p1.screen.y >= height) return;
  drawEnvironmentSprite(segment, index);
  const x = segment.p1.screen.x;
  const y = segment.p1.screen.y;
  const w = segment.p1.screen.w;

  if (index % 9 === 0) {
    const postH = Util.limit(w * 0.30, 4, height * 0.24);
    const postW = Util.limit(postH * 0.10, 1, 7);
    ctx.fillStyle = "rgba(219,245,255,.76)";
    ctx.fillRect(x - w * 1.14 - postW / 2, y - postH, postW, postH);
    ctx.fillRect(x + w * 1.14 - postW / 2, y - postH, postW, postH);
    ctx.fillStyle = "rgba(37,226,255,.78)";
    ctx.fillRect(x - w * 1.14 - postW, y - postH, postW * 2, Math.max(1, postW));
    ctx.fillRect(x + w * 1.14 - postW, y - postH, postW * 2, Math.max(1, postW));
  }

  if (index % 41 === 0 && w > 15) {
    const gateH = Util.limit(w * 0.42, 12, height * 0.32);
    const left = x - w * 1.02;
    const right = x + w * 1.02;
    ctx.strokeStyle = "rgba(255,72,226," + (0.32 + speedNorm * 0.34) + ")";
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

  if (r.id === selectedId && speedNorm > 0.52) {
    ctx.save();
    const dustAlpha = 0.10 + (speedNorm - 0.52) * 0.22;
    for (let i = 0; i < 9; i++) {
      const cycle = ((elapsed * (0.00055 + i * 0.000017) + i * 0.113) % 1);
      const trail = cycle * w * (0.34 + speedNorm * 0.42);
      const py = baseY + h * 0.01 + Math.sin(i * 2.3 + elapsed * 0.01) * h * 0.025;
      const len = w * (0.035 + (i % 3) * 0.018) * speedNorm;
      ctx.strokeStyle = "rgba(88,229,255," + (dustAlpha * (1 - cycle)).toFixed(3) + ")";
      ctx.lineWidth = Math.max(1, h * 0.009 * (1 - cycle * 0.55));
      ctx.beginPath();
      ctx.moveTo(x - w * 0.22 - trail, py);
      ctx.lineTo(x - w * 0.22 - trail - len, py + h * 0.012);
      ctx.stroke();
    }
    ctx.restore();
  }

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

  if (speedNorm > 0.52) {
    const alpha = (speedNorm - 0.52) * 0.34;
    ctx.strokeStyle = "rgba(111,232,255," + alpha.toFixed(3) + ")";
    ctx.lineWidth = 1;
    const count = 14;
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
