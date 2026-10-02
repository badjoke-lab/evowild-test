const canvas = document.querySelector("#raceCanvas");
const ctx = canvas.getContext("2d", { alpha: false, desynchronized: true });
const stage = document.querySelector("#stage");

const ui = {
  rank: document.querySelector("#rank"),
  speed: document.querySelector("#speed"),
  command: document.querySelector("#command"),
  reason: document.querySelector("#reason"),
  distance: document.querySelector("#distance"),
  clock: document.querySelector("#clock"),
  progress: document.querySelector("#progress"),
  ranking: document.querySelector("#ranking"),
  countdown: document.querySelector("#countdown"),
  pause: document.querySelector("#pause"),
  reset: document.querySelector("#reset"),
  assetStatus: document.querySelector("#assetStatus"),
  resultsPanel: document.querySelector("#resultsPanel"),
  resultWinner: document.querySelector("#resultWinner"),
  resultRaceTime: document.querySelector("#resultRaceTime"),
  resultList: document.querySelector("#resultList")
};

const agentTargetSelect = document.querySelector("#agentTargetSelect");
const agentStaminaEl = document.querySelector("#agentStamina");
const agentFatigueEl = document.querySelector("#agentFatigue");
const agentResponseEl = document.querySelector("#agentResponse");
const agentResultEl = document.querySelector("#agentResult");
const agentCommandButtons = [...document.querySelectorAll("[data-agent-command]")];

const BASE = import.meta.env.BASE_URL || "/";
const FINISH_REVIEW_MODE = new URLSearchParams(location.search).get("finishReview") === "1";
const FIELD_SIZE = 18;
const SELECTED_ID = 1;
const RACE_METERS = 1600;
stage.dataset.engineLineage = "lane5-fixed-step-plus-four-morph-run-sheets";
stage.dataset.morphSet = "S,P,E,A";
stage.dataset.fieldSize = String(FIELD_SIZE);
stage.dataset.cameraPolicy = "selected-plus-nearby";
const LANE_PATTERN = [1, 2, 0, 3, 1, 3, 0, 2];
const CRUISE_PATTERN = [36.8,34.7,35.9,34.9,36.1,35.2,35.6,34.8];
const ACCEL_PATTERN = [15.0,13.4,14.3,13.6,14.0,13.5,13.9,13.4];
const NAMES = [
  "Mica","Vela","Rook","Serein","Flint","Nacre","Ilex","Sora",
  "Tarin","Ossa","Brink","Nyx","Arden","Vale","Kest","Orin","Tess","Moro"
];
const LANES = Array.from({ length: FIELD_SIZE }, (_, i) => LANE_PATTERN[i % LANE_PATTERN.length]);
const CRUISE = Array.from({ length: FIELD_SIZE }, (_, i) => {
  const base = CRUISE_PATTERN[i % CRUISE_PATTERN.length];
  return base * (1 + ((i % 5) - 2) * 0.003);
});
const ACCEL = Array.from({ length: FIELD_SIZE }, (_, i) => {
  const base = ACCEL_PATTERN[i % ACCEL_PATTERN.length];
  return base * (1 + ((i % 3) - 1) * 0.004);
});
const MORPH_SEQUENCE = Array.from(
  { length: FIELD_SIZE },
  (_, i) => ["S","P","E","A"][i % 4]
);
const MORPH_META = {
  S: { cadence:1.00, width:1.00, lift:1.00 },
  P: { cadence:0.90, width:1.08, lift:0.62 },
  E: { cadence:0.96, width:1.02, lift:0.52 },
  A: { cadence:1.13, width:1.06, lift:0.82 }
};

const AGENT_COMMAND_DURATION_MS = 8000;
const AGENT_COMPATIBILITY = {
  S: { PUSH: 1.00, CONSERVE: 0.70 },
  P: { PUSH: 0.94, CONSERVE: 0.76 },
  E: { PUSH: 0.76, CONSERVE: 1.00 },
  A: { PUSH: 0.88, CONSERVE: 0.90 }
};

function createAgentState(id) {
  return {
    id: `AGENT-${String(id + 1).padStart(2, "0")}`,
    version: 1,
    command: "NEUTRAL",
    commandIssuedAt: -999999,
    commandUntil: -999999,
    response: 0,
    lastResult: "NEUTRAL"
  };
}

const RUN_FRAMES = [
  { phase:"CONTACT", col:0, row:0, y:0.00 },
  { phase:"PUSH",    col:1, row:0, y:0.00 },
  { phase:"LIFT",    col:2, row:0, y:0.00 },
  { phase:"FLIGHT",  col:0, row:1, y:-0.42 },
  { phase:"REACH",   col:1, row:1, y:-0.17 },
  { phase:"LAND",    col:2, row:1, y:-0.16 }
];

const spriteSheets = new Map();
const spriteFrames = new Map();
let readySheets = 0;
let failedSheets = 0;

function extractConnectedFrame(image, col, row) {
  const fw = Math.floor(image.naturalWidth / 3);
  const fh = Math.floor(image.naturalHeight / 2);
  const canvas = document.createElement("canvas");
  canvas.width = fw;
  canvas.height = fh;
  const c = canvas.getContext("2d", { willReadFrequently: true });
  c.clearRect(0, 0, fw, fh);
  c.drawImage(image, col * fw, row * fh, fw, fh, 0, 0, fw, fh);

  const pixels = c.getImageData(0, 0, fw, fh);
  const alpha = pixels.data;
  const count = fw * fh;
  let seed = -1;
  let bestDistance = Infinity;
  const centerX = fw * 0.5;
  const centerY = fh * 0.48;

  for (let i = 0; i < count; i++) {
    if (alpha[i * 4 + 3] <= 12) continue;
    const x = i % fw;
    const y = Math.floor(i / fw);
    const dx = x - centerX;
    const dy = y - centerY;
    const d = dx * dx + dy * dy;
    if (d < bestDistance) {
      bestDistance = d;
      seed = i;
    }
  }

  if (seed < 0) return canvas;

  const visited = new Uint8Array(count);
  const queue = new Int32Array(count);
  let head = 0;
  let tail = 0;
  queue[tail++] = seed;
  visited[seed] = 1;

  while (head < tail) {
    const index = queue[head++];
    const x = index % fw;
    const y = Math.floor(index / fw);

    for (let oy = -1; oy <= 1; oy++) {
      for (let ox = -1; ox <= 1; ox++) {
        if (ox === 0 && oy === 0) continue;
        const nx = x + ox;
        const ny = y + oy;
        if (nx < 0 || nx >= fw || ny < 0 || ny >= fh) continue;
        const next = ny * fw + nx;
        if (visited[next] || alpha[next * 4 + 3] <= 12) continue;
        visited[next] = 1;
        queue[tail++] = next;
      }
    }
  }

  for (let i = 0; i < count; i++) {
    if (!visited[i]) alpha[i * 4 + 3] = 0;
  }
  c.putImageData(pixels, 0, 0);
  return canvas;
}

for (const morph of ["S","P","E","A"]) {
  const image = new Image();
  image.decoding = "async";
  image.onload = () => {
    spriteFrames.set(
      morph,
      RUN_FRAMES.map((frame) => extractConnectedFrame(image, frame.col, frame.row))
    );
    readySheets++;
    stage.dataset.runSheetsReady = String(readySheets);
    stage.dataset.runSheetCleanup = "connected-body-alpha";
    if (readySheets === 4 && failedSheets === 0) {
      stage.dataset.runSheets = "ready";
      ui.assetStatus.textContent = "S / P / E / A run cycles ready";
    }
  };
  image.onerror = () => {
    failedSheets++;
    stage.dataset.runSheets = "error";
    stage.dataset.runSheetsFailed = String(failedSheets);
    ui.assetStatus.textContent = morph + " run cycle failed";
  };
  image.src = BASE + "concept/" + morph.toLowerCase() + "-run-sheet.webp";
  spriteSheets.set(morph, image);
}

let width = 1;
let height = 1;
let dpr = 1;
let elapsed = 0;
let last = performance.now();
let paused = false;
let raceState = "countdown";
let countdownRemaining = 2500;
let finishCounter = 0;
let frameCounter = 0;
let lastRankingPaint = 0;
let cameraMeters = 0;
let cameraVelocity = 0;
let pixelsPerMeter = 8;
let pixelsPerMeterVelocity = 0;

const clamp = (v,a,b) => Math.max(a, Math.min(b,v));
const lerp = (a,b,t) => a + (b-a)*t;
const smooth = (t) => t*t*(3-2*t);

function resize() {
  const r = canvas.getBoundingClientRect();
  width = Math.max(320, Math.floor(r.width));
  height = Math.max(420, Math.floor(r.height));
  dpr = Math.min(window.devicePixelRatio || 1, 1.65);
  canvas.width = Math.round(width*dpr);
  canvas.height = Math.round(height*dpr);
  ctx.setTransform(dpr,0,0,dpr,0,0);
}
new ResizeObserver(resize).observe(canvas);
resize();

function terrainY(m) {
  const a = Math.sin(m*0.0125)*14;
  const b = Math.sin(m*0.0042 + 0.8)*25;
  const c = Math.sin(m*0.021 + 1.7)*5;
  const openingRise = m > 35 && m < 205 ? Math.sin((m-35)/170*Math.PI)*48 : 0;
  const openingDrop = m >= 205 && m < 330 ? -Math.sin((m-205)/125*Math.PI)*28 : 0;
  const climb = m > 360 && m < 610 ? Math.sin((m-360)/250*Math.PI)*52 : 0;
  const dip = m > 760 && m < 1030 ? -Math.sin((m-760)/270*Math.PI)*38 : 0;
  return a+b+c+openingRise+openingDrop+climb+dip;
}

function terrainSlope(m) {
  return (terrainY(m+1.5)-terrainY(m-1.5))/3;
}

function courseBank(m) {
  const bankA = m > 170 && m < 360
    ? Math.sin((m-170)/190*Math.PI)*22
    : 0;
  const bankB = m > 520 && m < 760
    ? -Math.sin((m-520)/240*Math.PI)*28
    : 0;
  const bankC = m > 980 && m < 1240
    ? Math.sin((m-980)/260*Math.PI)*24
    : 0;
  return bankA+bankB+bankC;
}

function laneBankOffset(m,lane) {
  const depth=clamp(lane/3,0,1)*2-1;
  return courseBank(m)*depth;
}

function makeRacers() {
  return Array.from({length:FIELD_SIZE}, (_,i) => ({
    id:i+1,
    name:NAMES[i],
    morph:MORPH_SEQUENCE[i],
    distance: FINISH_REVIEW_MODE
      ? 1544 - Math.floor(i / 4) * 1.8 - (i % 4) * 0.22
      : Math.floor(i / 4) * 4.4 + (i % 4) * 0.28,
    speed:0,
    cruise:CRUISE[i],
    accel:ACCEL[i],
    stamina:100,
    fatigue:0,
    agent:createAgentState(i),
    lane:LANES[i],
    targetLane:LANES[i],
    phaseOffset:i*0.87,
    cooldown:0,
    command:"HOLD FORM",
    reason:"Pre-start",
    finished:false,
    finishPlace:0,
    finishTime:0
  }));
}
let racers = makeRacers();
let agentTargetIndex = 0;

function populateAgentTargets() {
  if (!agentTargetSelect) return;
  agentTargetSelect.replaceChildren();
  racers.forEach((r, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = `${r.name} · ${r.morph}`;
    agentTargetSelect.append(option);
  });
  agentTargetSelect.value = String(agentTargetIndex);
}
populateAgentTargets();

const selected = () => racers.find(r => r.id===SELECTED_ID);
const order = () => [...racers].sort((a,b) => {
  if (a.finished && b.finished) return a.finishPlace-b.finishPlace;
  if (a.finished) return -1;
  if (b.finished) return 1;
  return b.distance-a.distance;
});
const rankOf = r => order().findIndex(x=>x===r)+1;

function occupiedNear(r, lane, radius=8.5) {
  return racers.some(o => o!==r && !o.finished && o.lane===lane && Math.abs(o.distance-r.distance)<radius);
}
function gapAhead(r) {
  let best = Infinity;
  for (const o of racers) {
    if (o===r || o.finished || o.lane!==r.lane) continue;
    const g = o.distance-r.distance;
    if (g>0 && g<best) best=g;
  }
  return best;
}
function chooseLane(r) {
  const choices = [r.lane-1,r.lane+1,r.lane-2,r.lane+2]
    .filter(l => l>=0 && l<=3 && !occupiedNear(r,l,9))
    .sort((a,b) => Math.abs(a-r.lane)-Math.abs(b-r.lane));
  return choices[0] ?? r.lane;
}

function resolveAgentCommand(r, dt) {
  const agent = r.agent;
  if (!agent) return { speedFactor: 1, staminaDrainScale: 1 };

  if (agent.command !== "NEUTRAL" && elapsed >= agent.commandUntil) {
    agent.command = "NEUTRAL";
    agent.response = 0;
    agent.lastResult = "EXPIRED";
  }

  const command = agent.command;
  const compat = AGENT_COMPATIBILITY[r.morph]?.[command] ?? 0;
  const staminaFactor = clamp(r.stamina / 100, 0, 1);
  const fatiguePenalty = clamp(1 - r.fatigue * 0.72, 0.25, 1);
  const response = command === "NEUTRAL"
    ? 0
    : compat * staminaFactor * fatiguePenalty;
  agent.response = response;

  let speedFactor = 1;
  let staminaDrainScale = 1;
  let fatigueDelta = r.speed > r.cruise * 0.98 ? 0.0018 : -0.0015;

  if (command === "PUSH") {
    const effective = Math.max(0.35, response);
    speedFactor = 1 + 0.035 * response;
    staminaDrainScale = 1 + 0.55 * effective;
    fatigueDelta = 0.0105 * effective;
    agent.lastResult = response >= 0.72 ? "STRONG" : response >= 0.46 ? "PARTIAL" : "WEAK";
  } else if (command === "CONSERVE") {
    const effective = Math.max(0.35, response);
    speedFactor = 1 - 0.025 * response;
    staminaDrainScale = 0.34;
    fatigueDelta = -0.0065 * effective;
    agent.lastResult = response >= 0.72 ? "SETTLED" : response >= 0.46 ? "PARTIAL" : "WEAK";
  }

  r.fatigue = clamp(r.fatigue + fatigueDelta * dt, 0, 1);
  return { speedFactor, staminaDrainScale };
}

function issueAgentCommand(r, command) {
  if (!r?.agent || !["PUSH","CONSERVE","CLEAR"].includes(command)) return;

  if (command === "CLEAR") {
    r.agent.command = "NEUTRAL";
    r.agent.commandIssuedAt = elapsed;
    r.agent.commandUntil = elapsed;
    r.agent.response = 0;
    r.agent.lastResult = "CLEARED";
  } else {
    r.agent.command = command;
    r.agent.commandIssuedAt = elapsed;
    r.agent.commandUntil = elapsed + AGENT_COMMAND_DURATION_MS;
    r.agent.lastResult = "PENDING";
  }

  stage.dataset.agentCommand = r.agent.command;
  stage.dataset.agentRunnerId = String(r.id);
  stage.dataset.agentCommandUntil = String(Math.round(r.agent.commandUntil));
}

function targetSpeedFor(r) {
  const p = r.distance/RACE_METERS;
  let target = r.cruise * (p<.15 ? 1.035 : p>.87 ? 1.085 : p>.68 ? 1.025 : 1.0);
  const gap = gapAhead(r);
  if (gap<7.5 && r.cooldown<=0) {
    const nextLane = chooseLane(r);
    if (nextLane!==r.lane) {
      r.targetLane = nextLane;
      r.cooldown = 1500;
      r.command = "SHIFT LINE";
      r.reason = "Traffic ahead";
      target *= 1.015;
    } else {
      target *= clamp(gap/7.5,.77,.97);
      r.command = "HOLD GAP";
      r.reason = "Blocked";
    }
  } else if (p>.87 && r.stamina>22) {
    r.command = "COMMIT";
    r.reason = "Final drive";
  } else if (p>.68) {
    r.command = "PRESS";
    r.reason = "Build phase";
  } else {
    r.command = "HOLD FORM";
    r.reason = "Efficient pace";
  }

  if (r.stamina<18) {
    target *= .89;
    r.command = "PRESERVE";
    r.reason = "Low stamina";
  }
  return target * (.83 + .17*(r.stamina/100));
}

function updateRace(dtMs) {
  if (paused) return;
  const dt = Math.min(50,dtMs)/1000;

  if (raceState==="countdown") {
    countdownRemaining -= dtMs;
    const n = Math.ceil(countdownRemaining/800);
    ui.countdown.hidden = false;
    ui.countdown.textContent = n>0 ? String(n) : "GO";
    if (countdownRemaining<=0) {
      raceState = "running";
      stage.dataset.raceState = "running";
      ui.countdown.textContent = "GO";
    }
    return;
  }

  if (raceState!=="running") return;
  elapsed += dtMs;
  if (elapsed>650) ui.countdown.hidden = true;

  for (const r of racers) {
    if (r.finished) continue;
    r.cooldown = Math.max(0,r.cooldown-dtMs);

    const agentResolution = resolveAgentCommand(r, dt);
    let target = targetSpeedFor(r) *
      agentResolution.speedFactor *
      (1 - r.fatigue * 0.022);
    target += Math.sin(elapsed*.0015 + r.id*1.51)*.16;

    const diff = target-r.speed;
    const step = r.accel*dt*(diff>=0 ? 1 : 1.45);
    r.speed += clamp(diff,-step,step);

    if (r.lane!==r.targetLane) {
      const dir = Math.sign(r.targetLane-r.lane);
      const laneStep = dt*1.9;
      const next = r.lane + dir*laneStep;
      if ((dir>0 && next>=r.targetLane)||(dir<0 && next<=r.targetLane)) r.lane=r.targetLane;
      else r.lane=next;
    }

    const effort = Math.max(0,r.speed/r.cruise-.95);
    r.stamina = Math.max(
      0,
      r.stamina-(.62+effort*effort*4.4)*dt*agentResolution.staminaDrainScale
    );
    r.distance += Math.max(0,r.speed)*dt;

    if (r.distance>=RACE_METERS) {
      r.distance=RACE_METERS;
      r.finished=true;
      r.finishPlace=++finishCounter;
      r.finishTime=elapsed;
    }
  }
  if (finishCounter===racers.length) {
    raceState="finished";
    stage.dataset.raceState="finished";
    renderResults();
  }
}

function drawSky() {
  const horizon = height*.48;
  const sky = ctx.createLinearGradient(0,0,0,horizon);
  sky.addColorStop(0,"#789fb6");
  sky.addColorStop(.56,"#b8c9c9");
  sky.addColorStop(1,"#d8c6a3");
  ctx.fillStyle=sky;
  ctx.fillRect(0,0,width,horizon);

  const sunX=width*.76, sunY=height*.18, r=Math.max(28,width*.025);
  const glow=ctx.createRadialGradient(sunX,sunY,0,sunX,sunY,r*3.2);
  glow.addColorStop(0,"rgba(255,243,204,.9)");
  glow.addColorStop(1,"rgba(255,243,204,0)");
  ctx.fillStyle=glow;
  ctx.fillRect(sunX-r*3.3,sunY-r*3.3,r*6.6,r*6.6);
}

function drawParallaxLayer(baseY, amplitude, speed, period, fill, jaggedness) {
  const shift = cameraMeters*speed;
  ctx.fillStyle=fill;
  ctx.beginPath();
  ctx.moveTo(0,height);
  ctx.lineTo(0,baseY);
  const step=Math.max(24,period*.12);
  for(let x=0;x<=width+step;x+=step){
    const worldX=x+shift;
    const wave=
      Math.abs(Math.sin(worldX*.0067))*jaggedness +
      Math.abs(Math.sin(worldX*.013))*(1-jaggedness);
    const ridge=Math.sin(worldX*.0021+1.2)*.16;
    ctx.lineTo(x,baseY-amplitude*(.22+.66*wave+ridge));
  }
  ctx.lineTo(width,height);
  ctx.closePath();
  ctx.fill();
}

function drawBackground() {
  drawSky();
  drawParallaxLayer(height*.50,95,.20,280,"#7b8f96",.7);
  drawParallaxLayer(height*.54,68,.38,210,"#62786d",.6);
  drawParallaxLayer(height*.58,42,.62,150,"#455d4d",.5);

  const ground=ctx.createLinearGradient(0,height*.53,0,height);
  ground.addColorStop(0,"#607d52");
  ground.addColorStop(1,"#253c2c");
  ctx.fillStyle=ground;
  ctx.fillRect(0,height*.53,width,height*.47);

  const treeShift = -cameraMeters*1.18;
  for (let i=-2;i<Math.ceil(width/54)+4;i++) {
    const x=i*54 + (treeShift%54);
    const v=Math.abs(Math.sin((i+Math.floor(cameraMeters/54))*.81));
    const h=32+v*46;
    const y=height*.57+v*7;
    ctx.fillStyle="#294634";
    ctx.fillRect(x-2,y-h*.08,4,h*.36);
    ctx.beginPath();
    ctx.moveTo(x,y-h);
    ctx.lineTo(x-h*.34,y-h*.15);
    ctx.lineTo(x+h*.34,y-h*.15);
    ctx.closePath();
    ctx.fill();
  }
}

function screenXForMeters(m) {
  const anchor = width<700 ? width*.50 : width*.46;
  return anchor + (m-cameraMeters)*pixelsPerMeter;
}

function trackBaseY(m) {
  const portrait=height>width*1.35;
  const base=portrait?height*.54:height*.64;
  return base - terrainY(m)*(portrait?.68:.52);
}

function laneYAt(m,lane) {
  return trackBaseY(m)+laneOffset(lane)+laneBankOffset(m,lane);
}

function laneOffset(lane) {
  const portrait=height>width*1.35;
  const stops=portrait?[-78,-26,28,84]:[-82,-28,30,88];
  const lo=Math.floor(clamp(lane,0,3));
  const hi=Math.ceil(clamp(lane,0,3));
  const t=clamp(lane-lo,0,1);
  return lerp(stops[lo],stops[hi],t);
}
function laneScale(lane) {
  const t=clamp(lane/3,0,1);
  return lerp(.76,1.08,t);
}

function drawTrack() {
  const leftM = cameraMeters - width*.40/pixelsPerMeter;
  const rightM = cameraMeters + width*.84/pixelsPerMeter;
  const step=2.0;

  const laneCenters=[0,1,2,3].map(laneOffset);
  const boundaries=[
    laneCenters[0]-36,
    (laneCenters[0]+laneCenters[1])*.5,
    (laneCenters[1]+laneCenters[2])*.5,
    (laneCenters[2]+laneCenters[3])*.5,
    laneCenters[3]+38
  ];

  // One continuous racing surface. Lane depth exists inside it; there are no stacked roads.
  for(let lane=0;lane<4;lane++){
    const far=boundaries[lane];
    const near=boundaries[lane+1];
    const shade=lane%2===0?"#4b5154":"#464c4f";
    ctx.fillStyle=shade;
    ctx.beginPath();
    let first=true;
    for(let m=leftM;m<=rightM+step;m+=step){
      const x=screenXForMeters(m);
      const bank=courseBank(m);
      const farDepth=lane/4*2-1;
      const y=trackBaseY(m)+far+bank*farDepth;
      if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);
    }
    for(let m=rightM+step;m>=leftM;m-=step){
      const x=screenXForMeters(m);
      const bank=courseBank(m);
      const nearDepth=(lane+1)/4*2-1;
      const y=trackBaseY(m)+near+bank*nearDepth;
      ctx.lineTo(x,y);
    }
    ctx.closePath();
    ctx.fill();
  }

  // Back and near track edges anchor the whole surface in the scene.
  for(const [offset,alpha,lineWidth] of [
    [boundaries[0],"rgba(226,236,237,.46)",2],
    [boundaries[4],"rgba(226,236,237,.62)",2.4]
  ]){
    ctx.strokeStyle=alpha;
    ctx.lineWidth=lineWidth;
    ctx.beginPath();
    let first=true;
    for(let m=leftM;m<=rightM+step;m+=step){
      const x=screenXForMeters(m);
      const depthNorm=(offset-boundaries[0])/(boundaries[4]-boundaries[0])*2-1;
      const y=trackBaseY(m)+offset+courseBank(m)*depthNorm;
      if(first){ctx.moveTo(x,y);first=false;}else ctx.lineTo(x,y);
    }
    ctx.stroke();
  }

  // Internal lane boundaries are subtle, broken markers rather than separate roads.
  for(let divider=1;divider<4;divider++){
    const offset=boundaries[divider];
    ctx.strokeStyle="rgba(225,234,235,.19)";
    ctx.lineWidth=1.2;
    for(let m=Math.floor(leftM/10)*10;m<=rightM+10;m+=10){
      const m2=m+4.0;
      ctx.beginPath();
      const dividerDepth=divider/4*2-1;
      ctx.moveTo(screenXForMeters(m),trackBaseY(m)+offset+courseBank(m)*dividerDepth);
      ctx.lineTo(screenXForMeters(m2),trackBaseY(m2)+offset+courseBank(m2)*dividerDepth);
      ctx.stroke();
    }
  }

  // Short longitudinal texture marks make lateral speed readable without covering the creatures.
  for(let lane=0;lane<4;lane++){
    const yOffset=laneCenters[lane]+18;
    ctx.strokeStyle=lane===3?"rgba(238,243,235,.27)":"rgba(229,236,226,.15)";
    ctx.lineWidth=lane===3?1.7:1;
    for(let m=Math.floor(leftM/7)*7;m<=rightM+8;m+=7){
      const x1=screenXForMeters(m);
      const x2=screenXForMeters(m+2.0);
      const laneDepth=lane/3*2-1;
      const y1=trackBaseY(m)+yOffset+courseBank(m)*laneDepth;
      const y2=trackBaseY(m+2.0)+yOffset+courseBank(m+2.0)*laneDepth;
      ctx.beginPath();
      ctx.moveTo(x1,y1);
      ctx.lineTo(x2,y2);
      ctx.stroke();
    }
  }

  // Fence only on the back edge. It no longer cuts the race into separate horizontal strips.
  const fenceOffset=boundaries[0]-6;
  ctx.strokeStyle="rgba(212,224,219,.38)";
  ctx.lineWidth=2;
  ctx.beginPath();
  let fenceFirst=true;
  for(let m=leftM;m<=rightM+step;m+=step){
    const x=screenXForMeters(m);
    const y=trackBaseY(m)+fenceOffset-22-courseBank(m);
    if(fenceFirst){ctx.moveTo(x,y);fenceFirst=false;}else ctx.lineTo(x,y);
  }
  ctx.stroke();

  for(let m=Math.floor(leftM/14)*14;m<=rightM+16;m+=14){
    const x=screenXForMeters(m);
    const baseY=trackBaseY(m)+fenceOffset-courseBank(m);
    const sc=clamp(1+(m-cameraMeters)*.0015,.78,1.14);
    ctx.fillStyle="rgba(224,234,230,.82)";
    ctx.fillRect(x-1.5*sc,baseY-31*sc,3*sc,31*sc);
  }

  // Near-field streaks remain outside the track to sell speed.
  const focus=selected();
  const speedNorm=clamp(focus.speed/31.5,0,1);
  if(speedNorm>.30){
    ctx.save();
    ctx.globalAlpha=clamp((speedNorm-.30)*.46,0,.28);
    ctx.strokeStyle="rgba(232,240,214,.48)";
    for(let i=0;i<12;i++){
      const y=height*(.80+((i*29)%17)/100);
      const x=((i*83-cameraMeters*(pixelsPerMeter*1.72))%(width+180))-90;
      ctx.beginPath();
      ctx.moveTo(x,y);
      ctx.lineTo(x-42-speedNorm*76,y+2);
      ctx.stroke();
    }
    ctx.restore();
  }

  stage.dataset.trackSurface="single-field";
}

function drawCourseLandmarks() {
  const leftM=cameraMeters-width*.55/pixelsPerMeter;
  const rightM=cameraMeters+width*.62/pixelsPerMeter;
  const farY=laneOffset(0)-42;

  for(let mark=60;mark<RACE_METERS;mark+=60){
    if(mark<leftM-8||mark>rightM+8) continue;
    const x=screenXForMeters(mark);
    const baseY=trackBaseY(mark)+farY-courseBank(mark);
    const major=mark%360===0;
    const h=major?(height>width*1.35?86:64):(height>width*1.35?58:44);
    const w=major?54:38;

    ctx.save();
    ctx.fillStyle="rgba(22,35,38,.88)";
    ctx.fillRect(x-w*.5,baseY-h,w,major?24:19);
    ctx.fillStyle="rgba(226,241,242,.92)";
    ctx.font=`${major?"800":"700"} ${major?11:9}px ui-monospace, Menlo, monospace`;
    ctx.textAlign="center";
    ctx.textBaseline="middle";
    ctx.fillText(major?`SECTOR ${mark/360}`:`${mark}m`,x,baseY-h+(major?12:9.5));
    ctx.fillStyle="rgba(218,231,226,.70)";
    ctx.fillRect(x-2,baseY-h+(major?24:19),4,h-(major?24:19));
    ctx.restore();
  }

  for(let mark=360;mark<RACE_METERS;mark+=360){
    if(mark<leftM-18||mark>rightM+18) continue;
    const x=screenXForMeters(mark);
    const trackTop=laneYAt(mark,0)-45;
    const trackBottom=laneYAt(mark,3)+48;
    ctx.save();
    ctx.globalAlpha=.72;
    ctx.fillStyle="#23363a";
    ctx.fillRect(x-6,trackTop-34,6,trackBottom-trackTop+42);
    ctx.fillStyle="#8ddff4";
    ctx.fillRect(x-6,trackTop-34,6,9);
    ctx.restore();
  }
}

function drawRacers() {
  const list=[];
  let minEdge=Infinity;
  let maxEdge=-Infinity;
  let visibleLabelCount=0;
  for(const r of racers){
    const x=screenXForMeters(r.distance);
    if(x<-220 || x>width+260) continue;
    const lane=clamp(r.lane,0,3);
    const y=laneYAt(r.distance,lane);
    list.push({r,x,y,lane});
  }
  list.sort((a,b)=>a.lane-b.lane);

  for(const item of list){
    const r=item.r;
    const selectedRacer=r.id===SELECTED_ID;
    const scale=laneScale(item.lane);
    const meta=MORPH_META[r.morph] ?? MORPH_META.S;
    const frames=spriteFrames.get(r.morph);
    const baseW = width<700
      ? clamp(width*.13,78,108)
      : clamp(width*.078,104,128);
    const spriteW=baseW*scale*(selectedRacer?1.04:1)*meta.width;
    const sampleFrame=frames?.[0];
    const sourceAspect=sampleFrame
      ? sampleFrame.height/sampleFrame.width
      : .84;
    const spriteH=spriteW*clamp(sourceAspect,.58,1.08);
    minEdge=Math.min(minEdge,item.x-spriteW*.52);
    maxEdge=Math.max(maxEdge,item.x+spriteW*.52);

    const cadence=(9.5+clamp(r.speed/34,0,1)*9.5)*meta.cadence;
    const frameFloat=elapsed/1000*cadence+r.phaseOffset;
    const frameIndex=((Math.floor(frameFloat)%RUN_FRAMES.length)+RUN_FRAMES.length)%RUN_FRAMES.length;
    const frame=RUN_FRAMES[frameIndex];

    const slope=terrainSlope(r.distance);
    const lean=clamp(slope*.022,-.045,.045);

    const flight =
      frame.phase==="FLIGHT" ? 1 :
      frame.phase==="REACH" ? .55 :
      frame.phase==="LIFT" ? .28 : 0;
    const shadowW=spriteW*(.40-flight*.09);
    const shadowH=Math.max(3,spriteH*(.05-flight*.012));
    ctx.save();
    ctx.globalAlpha=.32-flight*.14;
    ctx.fillStyle="#071016";
    ctx.beginPath();
    ctx.ellipse(item.x,item.y+6+flight*3,shadowW,shadowH,0,0,Math.PI*2);
    ctx.fill();
    ctx.restore();

    const contactKick=frame.phase==="LAND"||frame.phase==="CONTACT"||frame.phase==="PUSH";
    if(r.speed>16&&contactKick){
      ctx.save();
      ctx.globalAlpha=.14;
      ctx.fillStyle="#d9c7a0";
      for(let p=0;p<3;p++){
        ctx.beginPath();
        ctx.ellipse(item.x-spriteW*(.28+p*.18),item.y+4+p*2,spriteW*(.09+p*.03),spriteH*.035,0,0,Math.PI*2);
        ctx.fill();
      }
      ctx.restore();
    }

    const frameCanvas=frames?.[frameIndex];
    if(frameCanvas){
      const footAdjust=frame.y*spriteH*.12*meta.lift;

      ctx.save();
      ctx.translate(item.x,item.y-spriteH*.48);
      ctx.rotate(lean);
      if(selectedRacer){
        ctx.shadowColor="rgba(126,226,255,.85)";
        ctx.shadowBlur=clamp(spriteW*.08,4,18);
      }
      ctx.drawImage(frameCanvas,-spriteW/2,-spriteH/2+footAdjust,spriteW,spriteH);
      ctx.restore();

      stage.dataset[`${r.morph.toLowerCase()}Animated`] = "true";
      stage.dataset[`${r.morph.toLowerCase()}Frame`] = String(frameIndex);
    }

    const raceRank=rankOf(r);
    const showLabel=selectedRacer || raceRank<=3;
    if(showLabel){
      visibleLabelCount++;
      const labelY=item.y-spriteH*.66;
      ctx.font=`800 ${width<700?9:11}px ui-monospace, Menlo, monospace`;
      ctx.textAlign="center";
      const txt=selectedRacer
        ? `YOU · ${r.morph}${String(r.id).padStart(2,"0")}`
        : `#${raceRank} ${r.morph}${String(r.id).padStart(2,"0")}`;
      const tw=ctx.measureText(txt).width+10;
      ctx.fillStyle=selectedRacer?"rgba(8,41,56,.94)":"rgba(3,10,15,.76)";
      ctx.fillRect(item.x-tw/2,labelY-12,tw,15);
      ctx.fillStyle=selectedRacer?"#9ce9fb":"#eef9ff";
      ctx.fillText(txt,item.x,labelY);
    }

    if(selectedRacer){
      stage.dataset.selectedRunFrame=String(frameIndex);
      stage.dataset.selectedRunPhase=frame.phase;
      stage.dataset.selectedMorph=r.morph;
      stage.dataset.selectedX=item.x.toFixed(1);
      stage.dataset.selectedY=item.y.toFixed(1);
    }
  }

  stage.dataset.visibleRacers=String(list.length);
  stage.dataset.visibleLabels=String(visibleLabelCount);
  stage.dataset.fieldMinX=Number.isFinite(minEdge)?minEdge.toFixed(1):"";
  stage.dataset.fieldMaxX=Number.isFinite(maxEdge)?maxEdge.toFixed(1):"";
}

function drawForeground() {
  const shift=-cameraMeters*(pixelsPerMeter*.52);
  ctx.save();
  ctx.globalAlpha=.68;
  for(let i=-2;i<Math.ceil(width/90)+4;i++){
    const x=i*90+(shift%90);
    const h=38+Math.abs(Math.sin(i*1.3))*34;
    ctx.strokeStyle="#1c3528";
    ctx.lineWidth=3;
    ctx.beginPath();
    ctx.moveTo(x,height);
    ctx.lineTo(x+8,height-h);
    ctx.stroke();
    ctx.strokeStyle="#274936";
    ctx.lineWidth=2;
    for(let b=0;b<3;b++){
      ctx.beginPath();
      ctx.moveTo(x+5,height-h+b*10);
      ctx.lineTo(x-10-b*2,height-h-8+b*8);
      ctx.stroke();
    }
  }
  ctx.restore();
}

function updateCamera() {
  const focus=selected();
  const live=racers.filter(r=>!r.finished);
  const byFocusDistance = (a,b) =>
    Math.abs(a.distance-focus.distance)-Math.abs(b.distance-focus.distance);
  const nearby=live
    .filter(r=>Math.abs(r.distance-focus.distance)<=28)
    .sort(byFocusDistance);
  const relevant=(nearby.length>=3?nearby:live.slice().sort(byFocusDistance))
    .slice(0,6);

  const front=relevant.length?Math.max(...relevant.map(r=>r.distance)):focus.distance;
  const back=relevant.length?Math.min(...relevant.map(r=>r.distance)):focus.distance;
  const localSpan=Math.max(1,front-back);
  const mobile=width<700;
  const base=mobile?8.2:10.4;
  const min=mobile?5.8:7.6;
  const available=width*(mobile?.62:.58);
  const targetPPM=clamp(Math.min(base,available/Math.max(12,localSpan)),min,base);

  const zoomRate=targetPPM<pixelsPerMeter?.18:.075;
  pixelsPerMeter=lerp(pixelsPerMeter,targetPPM,zoomRate);

  // Keep the selected creature readable while nearby rivals enter and leave frame.
  // The camera must not shrink all 18 runners just to keep the whole field visible.
  const lookAhead=clamp((front-focus.distance)*.10,1.5,4.5);
  const targetCamera=Math.max(0,focus.distance+lookAhead);
  const followRate=mobile?.22:.14;
  cameraMeters=lerp(cameraMeters,targetCamera,followRate);

  stage.dataset.pixelsPerMeter=pixelsPerMeter.toFixed(2);
  stage.dataset.packSpan=localSpan.toFixed(2);
  stage.dataset.cameraSubject="selected-plus-nearby";
  stage.dataset.cameraRelevantCount=String(relevant.length);
}
function drawSpeedRush() {
  const focus=selected();
  const speedNorm=clamp(focus.speed/36.5,0,1);
  if(speedNorm<.36)return;

  ctx.save();
  const strength=clamp((speedNorm-.36)/.64,0,1);
  ctx.globalAlpha=.08+.18*strength;
  ctx.strokeStyle="rgba(238,247,243,.78)";
  ctx.lineCap="round";
  const count=width<700?14:24;
  for(let i=0;i<count;i++){
    const band=(i%5)/5;
    const y=height*(.61+band*.31)+Math.sin(i*1.73)*8;
    const phase=(elapsed*.24*(1+band*.6)+i*97)%(width+220);
    const x=width+80-phase;
    const len=52+strength*165+band*78;
    ctx.lineWidth=.7+band*1.4;
    ctx.beginPath();
    ctx.moveTo(x,y);
    ctx.lineTo(x-len,y+band*3);
    ctx.stroke();
  }
  ctx.restore();
}

function render() {
  const focus=selected();
  updateCamera();

  const speedNorm=clamp(focus.speed/36.5,0,1);
  const shake=speedNorm>.62?(speedNorm-.62)*7.6:0;
  ctx.save();
  ctx.translate(Math.sin(elapsed*.041)*shake,Math.sin(elapsed*.053+1.2)*shake*.38);

  drawBackground();
  drawTrack();
  drawCourseLandmarks();
  drawRacers();
  drawForeground();
  drawSpeedRush();
  ctx.restore();

  // subtle speed vignette
  const vignetteSpeed=clamp(focus.speed/36.5,0,1);
  if(vignetteSpeed>.58){
    const a=(vignetteSpeed-.58)*.17;
    const vg=ctx.createRadialGradient(width*.5,height*.55,height*.12,width*.5,height*.55,width*.78);
    vg.addColorStop(0,"rgba(0,0,0,0)");
    vg.addColorStop(1,`rgba(0,5,8,${a})`);
    ctx.fillStyle=vg;
    ctx.fillRect(0,0,width,height);
  }
}

function renderResults() {
  const ranks = order();
  const winner = ranks[0];
  if (!winner) return;

  if (ui.resultsPanel) ui.resultsPanel.hidden = false;
  if (ui.resultWinner) {
    ui.resultWinner.textContent = `#1 ${winner.morph}${String(winner.id).padStart(2,"0")} · ${winner.name}`;
  }
  if (ui.resultRaceTime) ui.resultRaceTime.textContent = fmtTime(winner.finishTime);
  if (ui.resultList) {
    ui.resultList.innerHTML = ranks.map((r,index) =>
      `<li data-runner-id="${r.id}" data-finish-time="${r.finishTime.toFixed(1)}">` +
      `<b>#${index+1}</b><span>${r.morph}${String(r.id).padStart(2,"0")} · ${r.name}</span>` +
      `<time>${fmtTime(r.finishTime)}</time></li>`
    ).join("");
  }

  stage.dataset.resultReady = "1";
  stage.dataset.resultCount = String(ranks.length);
  stage.dataset.winnerId = String(winner.id);
  stage.dataset.winnerMorph = winner.morph;
  stage.dataset.winnerTime = winner.finishTime.toFixed(1);
}

function fmtTime(ms){
  const t=Math.max(0,ms)/1000;
  const min=Math.floor(t/60), sec=Math.floor(t%60), cs=Math.floor((t%1)*100);
  return `${String(min).padStart(2,"0")}:${String(sec).padStart(2,"0")}.${String(cs).padStart(2,"0")}`;
}

function updateUI(now){
  const focus=selected();
  const ranks=order();
  ui.rank.textContent=`${rankOf(focus)} / ${FIELD_SIZE}`;
  ui.speed.textContent=String(Math.round(focus.speed*3.6));
  ui.command.textContent=focus.command;
  ui.reason.textContent=focus.reason;
  ui.distance.textContent=`${Math.round(focus.distance)} / ${RACE_METERS} m`;
  ui.clock.textContent=fmtTime(elapsed);
  ui.progress.style.width=`${clamp(focus.distance/RACE_METERS*100,0,100).toFixed(2)}%`;

  const agentTarget = racers[agentTargetIndex] || racers[0];
  if (agentTarget?.agent) {
    if (agentStaminaEl) agentStaminaEl.textContent = `${Math.round(agentTarget.stamina)}%`;
    if (agentFatigueEl) agentFatigueEl.textContent = `${Math.round(agentTarget.fatigue * 100)}%`;
    if (agentResponseEl) {
      agentResponseEl.textContent = agentTarget.agent.command === "NEUTRAL"
        ? "NEUTRAL"
        : `${agentTarget.agent.command} ${Math.round(agentTarget.agent.response * 100)}%`;
    }
    if (agentResultEl) {
      agentResultEl.textContent = agentTarget.agent.command === "NEUTRAL"
        ? agentTarget.agent.lastResult === "NEUTRAL"
          ? "No active command"
          : `Last: ${agentTarget.agent.lastResult}`
        : `${agentTarget.agent.id} v${agentTarget.agent.version} · ${agentTarget.agent.lastResult}`;
    }
    agentCommandButtons.forEach((button) => {
      button.classList.toggle("active", button.dataset.agentCommand === agentTarget.agent.command);
      button.disabled = raceState !== "running";
    });
    stage.dataset.agentModel = "command-only-creature-resolved";
    stage.dataset.agentTargetRunner = String(agentTarget.id);
    stage.dataset.agentTargetMorph = agentTarget.morph;
    stage.dataset.agentFocusCommand = agentTarget.agent.command;
    stage.dataset.agentFocusResponse = agentTarget.agent.response.toFixed(3);
    stage.dataset.agentFocusStamina = (agentTarget.stamina / 100).toFixed(3);
    stage.dataset.agentFocusFatigue = agentTarget.fatigue.toFixed(3);
  }

  if(now-lastRankingPaint>180){
    lastRankingPaint=now;
    ui.ranking.innerHTML=ranks.map((r,i)=>`<span class="${r.id===SELECTED_ID?"selected":""}">#${i+1} ${r.morph}${String(r.id).padStart(2,"0")}</span>`).join("");
  }

  stage.dataset.selectedDistance=focus.distance.toFixed(2);
  stage.dataset.selectedSpeed=focus.speed.toFixed(2);
  stage.dataset.selectedRank=String(rankOf(focus));
  stage.dataset.courseBank=courseBank(focus.distance).toFixed(2);
  stage.dataset.cameraMeters=cameraMeters.toFixed(2);
  stage.dataset.frameCounter=String(frameCounter);
}

function resetRace(){
  racers=makeRacers();
  agentTargetIndex=0;
  populateAgentTargets();
  elapsed=0;
  raceState="countdown";
  countdownRemaining=2500;
  finishCounter=0;
  if (ui.resultsPanel) ui.resultsPanel.hidden = true;
  if (ui.resultList) ui.resultList.replaceChildren();
  stage.dataset.resultReady="0";
  stage.dataset.resultCount="0";
  stage.dataset.winnerId="";
  stage.dataset.winnerMorph="";
  stage.dataset.winnerTime="";
  cameraMeters=0;
  cameraVelocity=0;
  pixelsPerMeter=width<700?6.7:8.4;
  pixelsPerMeterVelocity=0;
  paused=false;
  ui.pause.textContent="Pause";
  ui.countdown.hidden=false;
  ui.countdown.textContent="3";
  stage.dataset.raceState="countdown";
  stage.dataset.agentModel="command-only-creature-resolved";
  stage.dataset.agentTargetRunner="1";
  stage.dataset.agentTargetMorph="S";
  stage.dataset.agentCommand="NEUTRAL";
  stage.dataset.agentRunnerId="";
  stage.dataset.agentCommandUntil="";
}

ui.pause.addEventListener("click",()=>{
  paused=!paused;
  ui.pause.textContent=paused?"Resume":"Pause";
});
ui.reset.addEventListener("click",resetRace);

if (agentTargetSelect) {
  agentTargetSelect.addEventListener("change", () => {
    agentTargetIndex = clamp(Number(agentTargetSelect.value) || 0, 0, racers.length - 1);
    stage.dataset.agentTargetRunner = String(racers[agentTargetIndex]?.id ?? 1);
    stage.dataset.agentTargetMorph = racers[agentTargetIndex]?.morph ?? "S";
  });
}

agentCommandButtons.forEach((button) => {
  button.addEventListener("click", () => {
    if (raceState !== "running") return;
    const r = racers[agentTargetIndex];
    issueAgentCommand(r, button.dataset.agentCommand);
  });
});

stage.dataset.raceState="countdown";
stage.dataset.resultReady="0";
stage.dataset.resultCount="0";
stage.dataset.winnerId="";
stage.dataset.winnerMorph="";
stage.dataset.winnerTime="";
stage.dataset.finishReview=FINISH_REVIEW_MODE?"1":"0";
stage.dataset.agentModel="command-only-creature-resolved";
stage.dataset.agentTargetRunner="1";
stage.dataset.agentTargetMorph="S";
stage.dataset.agentCommand="NEUTRAL";

// Fixed-step loop: borrowed-racer lane deliberately decouples simulation from render rate.
const FIXED_STEP = 1000 / 60;
let accumulator = 0;
function fixedFrame(now){
  const delta = Math.min(200, Math.max(0, now-last));
  last = now;
  if (!paused) accumulator += delta;
  let guard = 0;
  while (accumulator >= FIXED_STEP && guard < 8) {
    updateRace(FIXED_STEP);
    accumulator -= FIXED_STEP;
    guard++;
  }
  render();
  frameCounter++;
  updateUI(now);
  requestAnimationFrame(fixedFrame);
}
requestAnimationFrame(now=>{last=now;fixedFrame(now);});