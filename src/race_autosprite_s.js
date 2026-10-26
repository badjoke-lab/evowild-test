const canvas = document.querySelector("#race2d");
const ctx = canvas.getContext("2d", { alpha: false });
const stage = document.querySelector("#stage");
const assetState = document.querySelector("#assetState");

const ui = {
  clock: document.querySelector("#clock"),
  rank: document.querySelector("#rank"),
  lane: document.querySelector("#lane"),
  speed: document.querySelector("#speed"),
  stamina: document.querySelector("#stamina"),
  phase: document.querySelector("#phase"),
  morph: document.querySelector("#morph"),
  command: document.querySelector("#command"),
  reason: document.querySelector("#reason"),
  ranking: document.querySelector("#ranking"),
  progress: document.querySelector("#progressBar"),
  pause: document.querySelector("#pause"),
  reset: document.querySelector("#reset")
};

const MORPHS = {
  S: { label: "S — Sprint", cruise: 18.7, accel: 4.2, drain: 1.03, width: 150, height: 112, bob: 4.2 },
  P: { label: "P — Power", cruise: 18.0, accel: 4.8, drain: 1.12, width: 154, height: 116, bob: 3.3 },
  E: { label: "E — Endurance", cruise: 17.7, accel: 3.5, drain: 0.83, width: 148, height: 116, bob: 3.7 },
  A: { label: "A — Agility", cruise: 18.2, accel: 4.1, drain: 0.94, width: 156, height: 108, bob: 4.6 }
};

const names = [
  "Vela", "Rook", "Serein", "Flint", "Nacre", "Mica",
  "Ilex", "Sora", "Dune", "Kite", "Rime", "Tern",
  "Lumen", "Aster", "Brine", "Cairn", "Nilo", "Edda"
];

const morphCycle = ["S", "P", "E", "A"];
const selectedId = 1;
const raceMeters = 1800;
const laneCount = 6;
const BASE = import.meta.env.BASE_URL || "/";

const images = new Map();
let autoSpriteS = null;

async function loadAutoSpriteS() {
  const atlasUrl = BASE + "autosprite/s/sprint.json";
  const sheetUrl = BASE + "autosprite/s/sprint.png";
  const atlasResponse = await fetch(atlasUrl, { cache: "no-store" });
  if (!atlasResponse.ok) throw new Error("AutoSprite S atlas not found");
  const atlas = await atlasResponse.json();

  const rawFrames = atlas.frames || {};
  const frameMap = new Map(
    Object.entries(rawFrames).map(([name, value]) => {
      const rect = value && value.frame ? value.frame : value;
      return [name, { name, x: rect.x, y: rect.y, w: rect.w, h: rect.h }];
    })
  );

  let orderedNames = [];
  if (atlas.animations && typeof atlas.animations === "object") {
    const preferredKey = Object.keys(atlas.animations).find((key) => /sprint|run/i.test(key))
      || Object.keys(atlas.animations)[0];
    if (preferredKey && Array.isArray(atlas.animations[preferredKey])) {
      orderedNames = atlas.animations[preferredKey];
    }
  }

  const frames = (orderedNames.length ? orderedNames.map((name) => frameMap.get(name)) : [...frameMap.values()])
    .filter((frame) => frame && [frame.x, frame.y, frame.w, frame.h].every(Number.isFinite));

  if (!frames.length) throw new Error("AutoSprite S atlas has no usable frames");

  const img = new Image();
  img.decoding = "async";
  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = reject;
    img.src = sheetUrl;
  });

  autoSpriteS = {
    img,
    frames,
    fps: Number(atlas.meta?.framerate || atlas.framerate || 12) || 12
  };
}

function loadImage(morph) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.decoding = "async";
    img.onload = () => {
      images.set(morph, img);
      resolve();
    };
    img.onerror = reject;
    img.src = BASE + "concept/" + morph + ".webp";
  });
}

Promise.all([
  ...Object.keys(MORPHS).map(loadImage),
  loadAutoSpriteS().catch((error) => {
    console.warn(error.message);
    return null;
  })
])
  .then(() => {
    stage.dataset.assets = "ready";
    assetState.textContent = autoSpriteS
      ? "AutoSprite S Sprint active / P E A baseline"
      : "AutoSprite export missing — baseline S fallback";
  })
  .catch((error) => {
    stage.dataset.assets = "error";
    assetState.textContent = "Creature asset load failed";
    console.error(error);
  });

let width = 0;
let height = 0;
let dpr = 1;

function resize() {
  const rect = canvas.getBoundingClientRect();
  width = Math.max(320, rect.width);
  height = Math.max(420, rect.height);
  dpr = Math.min(window.devicePixelRatio || 1, 1.5);
  canvas.width = Math.round(width * dpr);
  canvas.height = Math.round(height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
}
new ResizeObserver(resize).observe(canvas);
resize();

function makeRacers() {
  return names.map((name, index) => {
    const morph = index === selectedId - 1 ? "S" : morphCycle[index % morphCycle.length];
    const stat = MORPHS[morph];
    return {
      id: index + 1,
      name,
      morph,
      lane: index % laneCount,
      laneF: index % laneCount,
      distance: Math.max(0, (17 - index) * 1.25),
      speed: 0,
      stamina: 100,
      cooldown: 0,
      command: "BUILD SPEED",
      reason: "Start phase",
      phase: "START",
      cruise: stat.cruise + ((index * 7) % 5) * 0.12,
      accel: stat.accel,
      drain: stat.drain,
      seed: index * 1.37
    };
  });
}

let racers = makeRacers();
let elapsed = 0;
let paused = false;
let last = performance.now();
let finishedAt = 0;

function selected() {
  return racers[selectedId - 1];
}

function ranks() {
  return [...racers].sort((a, b) => b.distance - a.distance);
}

function rankOf(racer) {
  return ranks().findIndex((r) => r === racer) + 1;
}

function phaseOf(racer) {
  const p = racer.distance / raceMeters;
  if (p < 0.08) return "START";
  if (p < 0.56) return "MID";
  if (p < 0.82) return "BUILD";
  return "FINAL";
}

function gapAhead(racer, lane) {
  let gap = Infinity;
  const currentLane = lane == null ? Math.round(racer.laneF) : lane;
  for (const other of racers) {
    if (other === racer || Math.round(other.laneF) !== currentLane) continue;
    const d = other.distance - racer.distance;
    if (d > 0 && d < gap) gap = d;
  }
  return gap;
}

function laneFree(racer, lane) {
  return racers.every((other) =>
    other === racer ||
    Math.round(other.laneF) !== lane ||
    Math.abs(other.distance - racer.distance) > 10
  );
}

function bestLane(racer) {
  const options = [];
  for (let lane = 0; lane < laneCount; lane++) {
    if (lane === Math.round(racer.laneF) || !laneFree(racer, lane)) continue;
    options.push([lane, gapAhead(racer, lane)]);
  }
  options.sort((a, b) => b[1] - a[1]);
  return options.length ? options[0][0] : null;
}

function targetSpeed(racer) {
  const p = racer.distance / raceMeters;
  let multiplier = 1;

  if (racer.morph === "S") multiplier = p < 0.28 ? 1.055 : p < 0.78 ? 1.005 : 0.985;
  if (racer.morph === "P") multiplier = p < 0.18 ? 1.04 : p < 0.76 ? 1.012 : racer.stamina > 26 ? 1.035 : 0.92;
  if (racer.morph === "E") multiplier = p < 0.55 ? 0.975 : p < 0.82 ? 1.02 : 1.085;
  if (racer.morph === "A") multiplier = p < 0.20 ? 0.995 : p < 0.72 ? 1.02 : 1.06;

  return racer.cruise * multiplier;
}

function update(dtMs) {
  if (paused) return;
  const dt = Math.min(dtMs, 50) / 1000;
  elapsed += dtMs;

  let allFinished = true;

  for (const racer of racers) {
    if (racer.distance >= raceMeters) {
      racer.speed *= 0.96;
      continue;
    }

    allFinished = false;
    racer.cooldown = Math.max(0, racer.cooldown - dtMs);
    racer.phase = phaseOf(racer);

    let target = targetSpeed(racer);
    const gap = gapAhead(racer);

    if (racer.stamina < 16) {
      target *= 0.86;
      racer.command = "PRESERVE";
      racer.reason = "Low stamina";
    } else if (gap < 14 && racer.cooldown <= 0) {
      const nextLane = bestLane(racer);
      if (nextLane != null) {
        racer.lane = nextLane;
        racer.cooldown = 1400;
        racer.command = "SHIFT LANE";
        racer.reason = "Traffic ahead";
      } else {
        target *= Math.max(0.82, gap / 14);
        racer.command = "HOLD";
        racer.reason = "No clean lane";
      }
    } else if (racer.phase === "FINAL" && racer.stamina > 22) {
      target *= 1.035;
      racer.command = "COMMIT";
      racer.reason = "Final phase";
    } else if (racer.phase === "BUILD") {
      racer.command = "PRESS";
      racer.reason = "Build phase";
    } else {
      racer.command = "CRUISE";
      racer.reason = racer.phase === "START" ? "Settle into pace" : "Maintain efficiency";
    }

    target *= 0.78 + 0.22 * (racer.stamina / 100);
    target += Math.sin(elapsed * 0.0011 + racer.seed) * 0.15;

    const diff = target - racer.speed;
    const step = racer.accel * dt * (diff >= 0 ? 1 : 1.45);
    racer.speed += Math.max(-step, Math.min(step, diff));
    racer.distance = Math.min(raceMeters, racer.distance + Math.max(0, racer.speed) * dt);

    const effort = Math.max(0, racer.speed / racer.cruise - 0.94);
    racer.stamina = Math.max(0, racer.stamina - (0.8 + 2.1 * effort * effort) * racer.drain * dt);
    racer.laneF += (racer.lane - racer.laneF) * Math.min(1, dt * 3.2);
  }

  if (allFinished && !finishedAt) finishedAt = performance.now();
}

function roundedRect(x, y, w, h, r) {
  const rr = Math.min(r, w / 2, h / 2);
  ctx.beginPath();
  ctx.moveTo(x + rr, y);
  ctx.arcTo(x + w, y, x + w, y + h, rr);
  ctx.arcTo(x + w, y + h, x, y + h, rr);
  ctx.arcTo(x, y + h, x, y, rr);
  ctx.arcTo(x, y, x + w, y, rr);
  ctx.closePath();
}

function drawMountainLayer(baseY, amplitude, period, shift, color) {
  ctx.fillStyle = color;
  ctx.beginPath();
  ctx.moveTo(0, height);
  ctx.lineTo(0, baseY);

  for (let x = 0; x <= width + period; x += period / 2) {
    const world = x + shift;
    const peak = baseY - amplitude * (0.42 + 0.58 * Math.abs(Math.sin(world * 0.0087)));
    ctx.lineTo(x, peak);
    ctx.lineTo(x + period * 0.24, baseY - amplitude * 0.18);
    ctx.lineTo(x + period * 0.5, baseY);
  }

  ctx.lineTo(width, height);
  ctx.closePath();
  ctx.fill();
}

function drawBackground(cameraDistance) {
  const sky = ctx.createLinearGradient(0, 0, 0, height * 0.62);
  sky.addColorStop(0, "#8cb8cf");
  sky.addColorStop(0.52, "#b9c9c4");
  sky.addColorStop(1, "#c9b68f");
  ctx.fillStyle = sky;
  ctx.fillRect(0, 0, width, height);

  const sunX = width * 0.77;
  const sunY = height * 0.18;
  const sunR = Math.max(34, width * 0.035);
  const glow = ctx.createRadialGradient(sunX, sunY, 0, sunX, sunY, sunR * 2.4);
  glow.addColorStop(0, "rgba(255,239,190,.75)");
  glow.addColorStop(1, "rgba(255,239,190,0)");
  ctx.fillStyle = glow;
  ctx.fillRect(sunX - sunR * 2.4, sunY - sunR * 2.4, sunR * 4.8, sunR * 4.8);

  drawMountainLayer(height * 0.46, 82, 210, cameraDistance * 0.12, "#718996");
  drawMountainLayer(height * 0.50, 62, 180, cameraDistance * 0.28, "#627b7b");
  drawMountainLayer(height * 0.54, 44, 150, cameraDistance * 0.46, "#536f63");
}

function trackYForLane(laneF) {
  const top = height * 0.55;
  const bottom = height * 0.93;
  const t = laneF / (laneCount - 1);
  return top + (bottom - top) * Math.pow(t, 1.12);
}

function laneScale(laneF) {
  const t = laneF / (laneCount - 1);
  return 0.56 + t * 0.62;
}

function drawTrack(cameraDistance, ppm, focusX) {
  const top = height * 0.52;
  const bottom = height;

  const grad = ctx.createLinearGradient(0, top, 0, bottom);
  grad.addColorStop(0, "#566068");
  grad.addColorStop(1, "#272f37");
  ctx.fillStyle = grad;
  ctx.beginPath();
  ctx.moveTo(-width * 0.2, top);
  ctx.lineTo(width * 1.2, top);
  ctx.lineTo(width * 1.2, bottom);
  ctx.lineTo(-width * 0.2, bottom);
  ctx.closePath();
  ctx.fill();

  for (let lane = 0; lane < laneCount; lane++) {
    const y = trackYForLane(lane);
    ctx.strokeStyle = "rgba(232,239,242," + (0.09 + lane * 0.025) + ")";
    ctx.lineWidth = 1 + lane * 0.2;
    ctx.beginPath();
    ctx.moveTo(0, y);
    ctx.lineTo(width, y);
    ctx.stroke();
  }

  const startMark = Math.floor((cameraDistance - focusX / ppm) / 50) * 50 - 50;
  ctx.font = "10px ui-monospace, SFMono-Regular, Menlo, monospace";
  ctx.textAlign = "center";

  for (let mark = startMark; mark < startMark + width / ppm + 200; mark += 50) {
    const x = focusX + (mark - cameraDistance) * ppm;
    if (x < -80 || x > width + 80) continue;

    ctx.strokeStyle = "rgba(255,255,255,.12)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
    ctx.stroke();

    if (mark >= 0 && mark <= raceMeters) {
      ctx.fillStyle = "rgba(236,245,250,.62)";
      ctx.fillText(mark + "m", x, top + 18);
    }
  }

  const finishX = focusX + (raceMeters - cameraDistance) * ppm;
  if (finishX > -40 && finishX < width + 40) {
    ctx.fillStyle = "rgba(255,255,255,.87)";
    for (let i = 0; i < 8; i++) {
      ctx.fillRect(finishX + (i % 2) * 6, top + i * ((bottom - top) / 8), 6, (bottom - top) / 8);
    }
    ctx.fillStyle = "#eef7fb";
    ctx.font = "800 11px ui-sans-serif, system-ui";
    ctx.fillText("FINISH", finishX + 6, top - 8);
  }
}

function drawRacer(racer, cameraDistance, ppm, focusX) {
  const img = images.get(racer.morph);
  const y = trackYForLane(racer.laneF);
  const scale = laneScale(racer.laneF);
  const x = focusX + (racer.distance - cameraDistance) * ppm;
  const stat = MORPHS[racer.morph];

  if (x < -220 || x > width + 220) return;

  const pace = Math.max(0, Math.min(1, racer.speed / 19.5));
  const stridePhase = elapsed * (0.012 + pace * 0.012) + racer.seed;
  const usingAutoSprite = racer.morph === "S" && autoSpriteS?.frames?.length;
  const bob = usingAutoSprite ? 0 : Math.abs(Math.sin(stridePhase)) * stat.bob * scale;
  const tilt = usingAutoSprite ? 0 : Math.sin(stridePhase * 0.5) * 0.018 * pace;
  const w = stat.width * scale;
  const h = stat.height * scale;
  const alpha = 0.72 + 0.28 * scale / 1.18;

  ctx.save();

  if (pace > 0.7) {
    ctx.strokeStyle = "rgba(199,234,255," + (0.05 + 0.12 * scale) + ")";
    ctx.lineWidth = Math.max(1, 2.4 * scale);
    const streak = 28 + pace * 42;
    for (let i = 0; i < 3; i++) {
      const sy = y - h * (0.18 + i * 0.19);
      ctx.beginPath();
      ctx.moveTo(x - w * 0.42, sy);
      ctx.lineTo(x - w * 0.42 - streak * (0.6 + i * 0.15), sy + i * 2);
      ctx.stroke();
    }
  }

  ctx.fillStyle = "rgba(0,0,0," + (0.11 + 0.14 * scale) + ")";
  ctx.beginPath();
  ctx.ellipse(x, y + 5, w * 0.35, 6 * scale, 0, 0, Math.PI * 2);
  ctx.fill();

  ctx.translate(x, y - h * 0.48 - bob);
  ctx.rotate(tilt);
  ctx.globalAlpha = alpha;

  if (usingAutoSprite) {
    const playbackFps = Math.max(1, autoSpriteS.fps * (0.72 + pace * 0.45));
    const frameIndex = Math.floor((elapsed / 1000) * playbackFps + racer.seed * 2) % autoSpriteS.frames.length;
    const frame = autoSpriteS.frames[frameIndex];
    ctx.drawImage(
      autoSpriteS.img,
      frame.x, frame.y, frame.w, frame.h,
      -w * 0.5, -h * 0.5, w, h
    );
  } else if (img) {
    ctx.drawImage(img, -w * 0.5, -h * 0.5, w, h);
  } else {
    ctx.fillStyle = "#d7e7ef";
    ctx.fillRect(-w * 0.42, -h * 0.22, w * 0.84, h * 0.44);
  }

  ctx.globalAlpha = 1;

  if (racer.id === selectedId) {
    ctx.strokeStyle = "#8dd8ff";
    ctx.lineWidth = Math.max(1.5, 2 * scale);
    ctx.setLineDash([5, 5]);
    roundedRect(-w * 0.56, -h * 0.58, w * 1.12, h * 1.08, 12 * scale);
    ctx.stroke();
    ctx.setLineDash([]);

    ctx.fillStyle = "rgba(5,16,27,.84)";
    roundedRect(-34 * scale, -h * 0.67, 68 * scale, 20 * scale, 6 * scale);
    ctx.fill();
    ctx.fillStyle = "#dff4ff";
    ctx.font = "800 " + Math.max(9, 10 * scale) + "px ui-sans-serif, system-ui";
    ctx.textAlign = "center";
    ctx.fillText("#01 VELA", 0, -h * 0.53);
  }

  ctx.restore();
}

function drawForeground(cameraDistance) {
  const shift = (cameraDistance * 0.75) % 240;
  ctx.fillStyle = "#142920";
  for (let x = -240 + shift; x < width + 240; x += 240) {
    const base = height * 0.985;
    ctx.beginPath();
    ctx.moveTo(x, base);
    ctx.lineTo(x + 30, base - 52);
    ctx.lineTo(x + 54, base);
    ctx.closePath();
    ctx.fill();
  }
}

function render() {
  const focus = selected();
  const focusX = width < 700 ? width * 0.34 : width * 0.39;
  const ppm = Math.max(0.74, Math.min(1.05, width / 1200));
  const cameraDistance = focus.distance;

  drawBackground(cameraDistance);
  drawTrack(cameraDistance, ppm, focusX);

  const ordered = [...racers].sort((a, b) => a.laneF - b.laneF);
  ordered.forEach((racer) => drawRacer(racer, cameraDistance, ppm, focusX));

  drawForeground(cameraDistance);

  ctx.fillStyle = "rgba(2,8,14,.16)";
  ctx.fillRect(0, 0, width, height);

  const vignette = ctx.createRadialGradient(width * 0.5, height * 0.46, height * 0.25, width * 0.5, height * 0.5, width * 0.8);
  vignette.addColorStop(0, "rgba(0,0,0,0)");
  vignette.addColorStop(1, "rgba(0,0,0,.24)");
  ctx.fillStyle = vignette;
  ctx.fillRect(0, 0, width, height);
}

function fmtTime(ms) {
  const total = ms / 1000;
  const min = Math.floor(total / 60);
  const sec = Math.floor(total % 60);
  const cs = Math.floor((total - Math.floor(total)) * 100);
  return String(min).padStart(2, "0") + ":" + String(sec).padStart(2, "0") + "." + String(cs).padStart(2, "0");
}

let lastRankingRender = 0;

function updateUI(now) {
  const s = selected();
  const order = ranks();
  const currentRank = rankOf(s);

  ui.clock.textContent = fmtTime(elapsed);
  ui.rank.textContent = currentRank + " / " + racers.length;
  ui.lane.textContent = String(Math.round(s.laneF) + 1);
  ui.speed.textContent = s.speed.toFixed(1) + " m/s";
  ui.stamina.textContent = String(Math.round(s.stamina));
  ui.phase.textContent = s.phase;
  ui.morph.textContent = MORPHS[s.morph].label;
  ui.command.textContent = s.command;
  ui.reason.textContent = s.reason;
  ui.progress.style.width = Math.min(100, (s.distance / raceMeters) * 100).toFixed(2) + "%";

  if (now - lastRankingRender > 250) {
    lastRankingRender = now;
    ui.ranking.innerHTML = order.map((racer, index) => {
      const gap = Math.max(0, order[0].distance - racer.distance);
      return '<div class="rank-row' + (racer.id === selectedId ? ' selected' : '') + '">' +
        '<span>' + (index + 1) + '</span>' +
        '<span class="name"><i class="morph">' + racer.morph + '</i> #' + String(racer.id).padStart(2, "0") + ' ' + racer.name + '</span>' +
        '<span class="gap">' + (index === 0 ? 'LEAD' : '+' + gap.toFixed(1) + 'm') + '</span>' +
        '</div>';
    }).join("");
  }
}

function resetRace() {
  racers = makeRacers();
  elapsed = 0;
  finishedAt = 0;
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

  if (finishedAt && now - finishedAt > 3200) resetRace();

  requestAnimationFrame(frame);
}

requestAnimationFrame((now) => {
  last = now;
  frame(now);
});
