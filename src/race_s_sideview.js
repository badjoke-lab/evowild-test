const canvas = document.querySelector("#motionCanvas");
const ctx = canvas.getContext("2d", { alpha: false, desynchronized: true });
const stage = document.querySelector("#stage");
const assetStatus = document.querySelector("#assetStatus");

const BASE = import.meta.env.BASE_URL || "/";
const params = new URLSearchParams(location.search);
const PLAYBACK_RATE = params.has("slow") ? 0.34 : 1;
const CYCLE_MS = 560;
const TAU = Math.PI * 2;

let width = 1;
let height = 1;
let dpr = 1;
let last = performance.now();
let elapsed = 0;
let worldTravel = 0;
let rig = null;

const source = new Image();
source.decoding = "async";
source.src = BASE + "concept/S.webp";

const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
const lerp = (a, b, t) => a + (b - a) * t;
const smooth = t => t * t * (3 - 2 * t);
const mod1 = v => ((v % 1) + 1) % 1;
const rad = deg => deg * Math.PI / 180;

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

function makeMaskedPart(srcCanvas, polygon) {
  const c = document.createElement("canvas");
  c.width = srcCanvas.width;
  c.height = srcCanvas.height;
  const cctx = c.getContext("2d");
  cctx.imageSmoothingEnabled = true;
  cctx.beginPath();
  polygon.forEach(([nx, ny], i) => {
    const x = nx * c.width;
    const y = ny * c.height;
    if (i === 0) cctx.moveTo(x, y);
    else cctx.lineTo(x, y);
  });
  cctx.closePath();
  cctx.clip();
  cctx.drawImage(srcCanvas, 0, 0);
  return c;
}

function pt(nx, ny, sw, sh) {
  return { x: nx * sw, y: ny * sh };
}

function makeSegmentPart(srcCanvas, a, b, radius) {
  const c = document.createElement("canvas");
  c.width = srcCanvas.width;
  c.height = srcCanvas.height;
  const cctx = c.getContext("2d");
  cctx.drawImage(srcCanvas, 0, 0);
  cctx.globalCompositeOperation = "destination-in";
  cctx.strokeStyle = "#fff";
  cctx.lineCap = "round";
  cctx.lineJoin = "round";
  cctx.lineWidth = radius * 2;
  cctx.beginPath();
  cctx.moveTo(a.x, a.y);
  cctx.lineTo(b.x, b.y);
  cctx.stroke();
  cctx.globalCompositeOperation = "source-over";
  return c;
}

function buildRig() {
  const sw = source.naturalWidth;
  const sh = source.naturalHeight;

  // The authoritative S art faces left. Mirror it once so every rig layer keeps
  // the original pixels while the motion study runs left-to-right.
  const mirrored = document.createElement("canvas");
  mirrored.width = sw;
  mirrored.height = sh;
  const mctx = mirrored.getContext("2d");
  mctx.translate(sw, 0);
  mctx.scale(-1, 1);
  mctx.drawImage(source, 0, 0);

  const front = {
    root: pt(.56,.54,sw,sh),
    knee: pt(.73,.78,sw,sh),
    foot: pt(.90,.985,sw,sh)
  };
  const hind = {
    root: pt(.30,.54,sw,sh),
    knee: pt(.17,.78,sw,sh),
    foot: pt(.16,.985,sw,sh)
  };

  const bodyDefs = {
    torso: [
      [.20,.24],[.39,.19],[.63,.21],[.79,.36],
      [.77,.60],[.63,.73],[.37,.74],[.18,.59]
    ],
    head: [
      [.55,.00],[.99,.00],[1,.45],[.89,.59],
      [.73,.63],[.58,.49]
    ],
    tail: [
      [.00,.30],[.31,.27],[.39,.39],[.35,.62],
      [.16,.69],[.00,.69]
    ],
    shoulder: [
      [.47,.34],[.68,.34],[.72,.49],[.65,.70],
      [.47,.69],[.41,.51]
    ],
    hip: [
      [.20,.35],[.42,.33],[.47,.49],[.40,.70],
      [.20,.70],[.16,.52]
    ]
  };

  const parts = Object.fromEntries(
    Object.entries(bodyDefs).map(([name, polygon]) => [name, makeMaskedPart(mirrored, polygon)])
  );

  parts.foreUpper = makeSegmentPart(mirrored, front.root, front.knee, Math.max(5, sw * .043));
  parts.foreLower = makeSegmentPart(mirrored, front.knee, front.foot, Math.max(4, sw * .030));
  parts.hindUpper = makeSegmentPart(mirrored, hind.root, hind.knee, Math.max(5, sw * .046));
  parts.hindLower = makeSegmentPart(mirrored, hind.knee, hind.foot, Math.max(4, sw * .030));

  return {
    sw,
    sh,
    parts,
    bodyCenter: pt(.50, .47, sw, sh),
    neckPivot: pt(.66, .41, sw, sh),
    tailPivot: pt(.29, .48, sw, sh),
    shoulderPivot: pt(.56, .52, sw, sh),
    hipPivot: pt(.31, .53, sw, sh),
    front,
    hind
  };
}

source.onload = () => {
  rig = buildRig();
  stage.dataset.rigReady = "true";
  stage.dataset.motionPhase = "CONTACT";
  assetStatus.textContent = "S rig ready";
};

source.onerror = () => {
  stage.dataset.rigReady = "error";
  stage.dataset.motionPhase = "error";
  assetStatus.textContent = "S rig failed";
};

function sample(frames, p) {
  for (let i = 0; i < frames.length - 1; i++) {
    const a = frames[i];
    const b = frames[i + 1];
    if (p >= a[0] && p <= b[0]) {
      const t = smooth((p - a[0]) / Math.max(.0001, b[0] - a[0]));
      return lerp(a[1], b[1], t);
    }
  }
  return frames[frames.length - 1][1];
}

const BODY_Y = [
  [0, 0], [.07, 2.5], [.20, -7], [.36, -19],
  [.54, -27], [.68, -18], [.84, 5], [1, 0]
];

const BODY_X = [
  [0, -2], [.12, 3], [.28, 6], [.48, 1],
  [.68, -3], [.86, -5], [1, -2]
];

const BODY_PITCH = [
  [0, 2.2], [.12, 0.4], [.25, -3.8], [.48, -1.7],
  [.67, 1.6], [.86, 4.4], [1, 2.2]
];

function motionPhase(p) {
  if (p < .06) return "CONTACT";
  if (p < .23) return "PUSH";
  if (p < .39) return "RECOVERY";
  if (p < .66) return "FLIGHT";
  if (p < .86) return "REACH";
  return "LAND";
}

function rotateAround(point, center, angle) {
  const dx = point.x - center.x;
  const dy = point.y - center.y;
  const c = Math.cos(angle);
  const s = Math.sin(angle);
  return {
    x: center.x + dx * c - dy * s,
    y: center.y + dx * s + dy * c
  };
}

function sourcePointToWorld(sourcePoint, bodyCenterWorld, scale, rotation) {
  const local = {
    x: bodyCenterWorld.x + (sourcePoint.x - rig.bodyCenter.x) * scale,
    y: bodyCenterWorld.y + (sourcePoint.y - rig.bodyCenter.y) * scale
  };
  return rotateAround(local, bodyCenterWorld, rotation);
}

function drawRigid(partName, sourcePivot, targetPivot, rotation, scale, alpha = 1) {
  const part = rig.parts[partName];
  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(targetPivot.x, targetPivot.y);
  ctx.rotate(rotation);
  ctx.scale(scale, scale);
  ctx.translate(-sourcePivot.x, -sourcePivot.y);
  ctx.drawImage(part, 0, 0);
  ctx.restore();
}

function drawBone(partName, srcA, srcB, targetA, targetB, alpha = 1) {
  const sourceAngle = Math.atan2(srcB.y - srcA.y, srcB.x - srcA.x);
  const targetAngle = Math.atan2(targetB.y - targetA.y, targetB.x - targetA.x);
  const sourceLength = Math.hypot(srcB.x - srcA.x, srcB.y - srcA.y);
  const targetLength = Math.hypot(targetB.x - targetA.x, targetB.y - targetA.y);
  const scale = targetLength / Math.max(1, sourceLength);

  ctx.save();
  ctx.globalAlpha = alpha;
  ctx.translate(targetA.x, targetA.y);
  ctx.rotate(targetAngle - sourceAngle);
  ctx.scale(scale, scale);
  ctx.translate(-srcA.x, -srcA.y);
  ctx.drawImage(rig.parts[partName], 0, 0);
  ctx.restore();
}

function constrainTarget(root, target, minDistance, maxDistance) {
  const dx = target.x - root.x;
  const dy = target.y - root.y;
  const d = Math.max(.001, Math.hypot(dx, dy));
  const wanted = clamp(d, minDistance, maxDistance);
  if (Math.abs(wanted - d) < .01) return { ...target };
  return {
    x: root.x + dx / d * wanted,
    y: root.y + dy / d * wanted
  };
}

function solveIK(root, target, upper, lower, bend) {
  const dx = target.x - root.x;
  const dy = target.y - root.y;
  let d = Math.hypot(dx, dy);
  d = clamp(d, Math.abs(upper - lower) + .01, upper + lower - .01);

  const ux = dx / Math.max(.001, Math.hypot(dx, dy));
  const uy = dy / Math.max(.001, Math.hypot(dx, dy));
  const along = (upper * upper - lower * lower + d * d) / (2 * d);
  const h = Math.sqrt(Math.max(0, upper * upper - along * along));
  const mx = root.x + ux * along;
  const my = root.y + uy * along;
  const px = -uy;
  const py = ux;

  return {
    x: mx + px * h * bend,
    y: my + py * h * bend
  };
}

function legPhase(globalPhase, contactStart) {
  return mod1(globalPhase - contactStart);
}

function footTrajectory(q, root, stride, lift, groundY, frontBias = 0) {
  let x;
  let y;

  if (q < .22) {
    const t = smooth(q / .22);
    x = lerp(root.x + stride * .58, root.x - stride * .78, t);
    y = groundY;
  } else if (q < .40) {
    const t = smooth((q - .22) / .18);
    x = lerp(root.x - stride * .78, root.x - stride * .62, t);
    y = groundY - lift * t;
  } else if (q < .65) {
    const t = smooth((q - .40) / .25);
    x = lerp(root.x - stride * .62, root.x + stride * .05, t);
    y = groundY - lift * (1 + .12 * Math.sin(t * Math.PI));
  } else if (q < .86) {
    const t = smooth((q - .65) / .21);
    x = lerp(root.x + stride * .05, root.x + stride * .78, t);
    y = groundY - lerp(lift, lift * .28, t);
  } else {
    const t = smooth((q - .86) / .14);
    x = lerp(root.x + stride * .78, root.x + stride * .58, t);
    y = lerp(groundY - lift * .28, groundY - 1.2, t);
  }

  return { x: x + frontBias, y };
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

  const ground = ctx.createLinearGradient(0, horizon, 0, height);
  ground.addColorStop(0, "#59645d");
  ground.addColorStop(1, "#2d3333");
  ctx.fillStyle = ground;
  ctx.fillRect(0, horizon, width, height - horizon);

  const trackTop = height * .72;
  const trackGrad = ctx.createLinearGradient(0, trackTop, 0, height);
  trackGrad.addColorStop(0, "#555b5e");
  trackGrad.addColorStop(1, "#30363a");
  ctx.fillStyle = trackGrad;
  ctx.fillRect(0, trackTop, width, height - trackTop);

  const streakSpeed = 1.1 + speedNorm * 1.9;
  const spacing = width < 700 ? 82 : 118;
  const shift = (worldTravel * streakSpeed) % spacing;

  ctx.strokeStyle = "rgba(229,235,236,.18)";
  ctx.lineWidth = 1.2;
  for (let x = -spacing; x < width + spacing; x += spacing) {
    const sx = x - shift;
    const len = 26 + speedNorm * 72;
    ctx.beginPath();
    ctx.moveTo(sx, trackTop + 38);
    ctx.lineTo(sx - len, trackTop + 38);
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(sx + spacing * .37, trackTop + 92);
    ctx.lineTo(sx + spacing * .37 - len * 1.25, trackTop + 92);
    ctx.stroke();
  }

  if (speedNorm > .35) {
    ctx.save();
    ctx.globalAlpha = clamp((speedNorm - .35) * .46, 0, .34);
    ctx.strokeStyle = "rgba(238,245,244,.85)";
    for (let i = 0; i < 15; i++) {
      const y = height * (.77 + (i % 7) * .03);
      const x = ((i * 143 - worldTravel * 2.3) % (width + 240)) + width;
      const len = 65 + speedNorm * 105;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x - len, y + 2);
      ctx.stroke();
    }
    ctx.restore();
  }
}

function drawShadow(cx, groundY, phase) {
  const flight = phase === "FLIGHT" ? 1 : phase === "REACH" ? .65 : phase === "RECOVERY" ? .35 : 0;
  ctx.save();
  ctx.globalAlpha = .30 - flight * .12;
  ctx.fillStyle = "#091014";
  ctx.beginPath();
  ctx.ellipse(cx - 12, groundY + 6, 108 - flight * 18, 15 - flight * 4, 0, 0, TAU);
  ctx.fill();
  ctx.restore();
}

function drawDust(foot, intensity, scale) {
  if (intensity <= 0) return;
  ctx.save();
  ctx.globalAlpha = .14 * intensity;
  ctx.fillStyle = "#d7c3a1";
  for (let i = 0; i < 4; i++) {
    ctx.beginPath();
    ctx.ellipse(
      foot.x - (12 + i * 13) * scale,
      foot.y + 2 + i,
      (7 + i * 3) * scale,
      (2.3 + i * .8) * scale,
      0,
      0,
      TAU
    );
    ctx.fill();
  }
  ctx.restore();
}

function drawLeg(root, foot, sourceDef, upperLength, lowerLength, bend, alpha) {
  const safeFoot = constrainTarget(
    root,
    foot,
    Math.abs(upperLength - lowerLength) + 2,
    upperLength + lowerLength - 2
  );
  const knee = solveIK(root, safeFoot, upperLength, lowerLength, bend);
  drawBone("foreUpper", sourceDef.root, sourceDef.knee, root, knee, alpha);
  drawBone("foreLower", sourceDef.knee, sourceDef.foot, knee, safeFoot, alpha);
  return { knee, foot: safeFoot };
}

function drawHindLeg(root, foot, sourceDef, upperLength, lowerLength, bend, alpha) {
  const safeFoot = constrainTarget(
    root,
    foot,
    Math.abs(upperLength - lowerLength) + 2,
    upperLength + lowerLength - 2
  );
  const knee = solveIK(root, safeFoot, upperLength, lowerLength, bend);
  drawBone("hindUpper", sourceDef.root, sourceDef.knee, root, knee, alpha);
  drawBone("hindLower", sourceDef.knee, sourceDef.foot, knee, safeFoot, alpha);
  return { knee, foot: safeFoot };
}

function renderCreature(globalPhase) {
  const targetW = clamp(Math.min(width * .61, height * .86), width < 560 ? 285 : 360, 675);
  const scale = targetW / rig.sw;
  const phase = motionPhase(globalPhase);
  const groundY = height * (height > width * 1.15 ? .77 : .80);

  const bodyYOffset = sample(BODY_Y, globalPhase) * scale;
  const bodyXOffset = sample(BODY_X, globalPhase) * scale;
  const bodyPitch = rad(sample(BODY_PITCH, globalPhase));
  const baseDrop = (0.985 * rig.sh - rig.bodyCenter.y) * scale;
  const bodyCenterWorld = {
    x: width * .52 + bodyXOffset,
    y: groundY - baseDrop + bodyYOffset
  };

  const frontRootBase = sourcePointToWorld(rig.front.root, bodyCenterWorld, scale, bodyPitch);
  const hindRootBase = sourcePointToWorld(rig.hind.root, bodyCenterWorld, scale, bodyPitch);

  const legScale = scale;
  const frontUpper = Math.hypot(
    rig.front.knee.x - rig.front.root.x,
    rig.front.knee.y - rig.front.root.y
  ) * legScale;
  const frontLower = Math.hypot(
    rig.front.foot.x - rig.front.knee.x,
    rig.front.foot.y - rig.front.knee.y
  ) * legScale;
  const hindUpper = Math.hypot(
    rig.hind.knee.x - rig.hind.root.x,
    rig.hind.knee.y - rig.hind.root.y
  ) * legScale;
  const hindLower = Math.hypot(
    rig.hind.foot.x - rig.hind.knee.x,
    rig.hind.foot.y - rig.hind.knee.y
  ) * legScale;

  const strideFront = 46 * scale;
  const strideHind = 38 * scale;
  const liftFront = 34 * scale;
  const liftHind = 30 * scale;

  const qHindFar = legPhase(globalPhase, 0.00);
  const qHindNear = legPhase(globalPhase, .055);
  const qForeFar = legPhase(globalPhase, .120);
  const qForeNear = legPhase(globalPhase, .180);

  const hindFarRoot = { x: hindRootBase.x + 7 * scale, y: hindRootBase.y + 4 * scale };
  const hindNearRoot = { x: hindRootBase.x - 3 * scale, y: hindRootBase.y - 1 * scale };
  const foreFarRoot = { x: frontRootBase.x - 8 * scale, y: frontRootBase.y + 5 * scale };
  const foreNearRoot = { x: frontRootBase.x + 3 * scale, y: frontRootBase.y - 1 * scale };

  const hindFarFoot = footTrajectory(qHindFar, hindFarRoot, strideHind, liftHind, groundY, -8 * scale);
  const hindNearFoot = footTrajectory(qHindNear, hindNearRoot, strideHind, liftHind * 1.04, groundY, -1 * scale);
  const foreFarFoot = footTrajectory(qForeFar, foreFarRoot, strideFront, liftFront, groundY, 5 * scale);
  const foreNearFoot = footTrajectory(qForeNear, foreNearRoot, strideFront, liftFront * 1.04, groundY, 11 * scale);

  drawShadow(bodyCenterWorld.x, groundY, phase);

  // Far limbs first: same S pixels, reduced only by depth opacity.
  const hindFarPose = drawHindLeg(hindFarRoot, hindFarFoot, rig.hind, hindUpper * .97, hindLower * .97, -1, .58);
  const foreFarPose = drawLeg(foreFarRoot, foreFarFoot, rig.front, frontUpper * .97, frontLower * .97, 1, .58);

  const tailPivotWorld = sourcePointToWorld(rig.tailPivot, bodyCenterWorld, scale, bodyPitch);
  const tailSwing = rad(Math.sin(globalPhase * TAU + .65) * 5.5 - sample(BODY_PITCH, globalPhase) * .35);
  drawRigid("tail", rig.tailPivot, tailPivotWorld, bodyPitch + tailSwing, scale, .94);

  drawRigid("torso", rig.bodyCenter, bodyCenterWorld, bodyPitch, scale, 1);

  // Near limbs remain fully opaque and articulate from the body roots.
  const hindNearPose = drawHindLeg(hindNearRoot, hindNearFoot, rig.hind, hindUpper, hindLower, -1, 1);
  const foreNearPose = drawLeg(foreNearRoot, foreNearFoot, rig.front, frontUpper, frontLower, 1, 1);

  const shoulderPivotWorld = sourcePointToWorld(rig.shoulderPivot, bodyCenterWorld, scale, bodyPitch);
  const hipPivotWorld = sourcePointToWorld(rig.hipPivot, bodyCenterWorld, scale, bodyPitch);
  const shoulderRock = rad(Math.sin(globalPhase * TAU + .4) * 2.8);
  const hipRock = rad(Math.sin(globalPhase * TAU - .9) * 3.2);
  drawRigid("shoulder", rig.shoulderPivot, shoulderPivotWorld, bodyPitch + shoulderRock, scale, .98);
  drawRigid("hip", rig.hipPivot, hipPivotWorld, bodyPitch + hipRock, scale, .98);

  const neckPivotWorld = sourcePointToWorld(rig.neckPivot, bodyCenterWorld, scale, bodyPitch);
  const headCounter = rad(-sample(BODY_PITCH, globalPhase) * .46 + Math.sin(globalPhase * TAU + .2) * .65);
  drawRigid("head", rig.neckPivot, neckPivotWorld, bodyPitch + headCounter, scale, 1);

  const contacts = [
    [qHindFar, hindFarPose.foot],
    [qHindNear, hindNearPose.foot],
    [qForeFar, foreFarPose.foot],
    [qForeNear, foreNearPose.foot]
  ].filter(([q]) => q < .22);

  for (const [q, foot] of contacts) {
    const pulse = 1 - clamp(q / .22, 0, 1);
    drawDust(foot, pulse, scale * .45);
  }

  const contactError = contacts.length
    ? Math.max(...contacts.map(([, foot]) => Math.abs(foot.y - groundY)))
    : 0;

  stage.dataset.motionPhase = phase;
  stage.dataset.phaseProgress = globalPhase.toFixed(3);
  stage.dataset.contactCount = String(contacts.length);
  stage.dataset.contactError = contactError.toFixed(2);
  stage.dataset.flight = contacts.length === 0 ? "true" : "false";
  stage.dataset.bodyPitch = (bodyPitch * 180 / Math.PI).toFixed(2);
  stage.dataset.bodyY = bodyCenterWorld.y.toFixed(1);
  stage.dataset.frontFootY = foreNearPose.foot.y.toFixed(1);
  stage.dataset.rearFootY = hindNearPose.foot.y.toFixed(1);
}

function render() {
  const p = mod1(elapsed / CYCLE_MS);
  const phase = motionPhase(p);
  const speedNorm = .92;

  drawBackground(speedNorm);
  if (rig) renderCreature(p);

  if (phase === "FLIGHT") {
    const vignette = ctx.createRadialGradient(
      width * .52, height * .53, height * .18,
      width * .52, height * .53, width * .72
    );
    vignette.addColorStop(0, "rgba(0,0,0,0)");
    vignette.addColorStop(1, "rgba(0,5,8,.10)");
    ctx.fillStyle = vignette;
    ctx.fillRect(0, 0, width, height);
  }
}

function frame(now) {
  const dt = clamp(now - last, 0, 45);
  last = now;
  elapsed += dt * PLAYBACK_RATE;
  worldTravel += dt * .46 * PLAYBACK_RATE;
  render();
  requestAnimationFrame(frame);
}

requestAnimationFrame(now => {
  last = now;
  frame(now);
});
