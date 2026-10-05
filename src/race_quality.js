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
const agentPressureEl = document.querySelector("#agentPressure");
const creatureStateEl = document.querySelector("#creatureState");
const agentResponseEl = document.querySelector("#agentResponse");
const agentResultEl = document.querySelector("#agentResult");
const agentFeedbackEl = document.querySelector("#agentFeedback");
const agentFeedbackMetaEl = document.querySelector("#agentFeedbackMeta");
const agentFeedbackCommandEl = document.querySelector("#agentFeedbackCommand");
const agentFeedbackResultEl = document.querySelector("#agentFeedbackResult");
const battleReadoutEl = document.querySelector("#battleReadout");
const battleStateEl = document.querySelector("#battleState");
const battleMetaEl = document.querySelector("#battleMeta");
const agentCommandButtons = [...document.querySelectorAll("[data-agent-command]")];

const BASE = import.meta.env.BASE_URL || "/";
const FINISH_REVIEW_MODE = new URLSearchParams(location.search).get("finishReview") === "1";
const BATTLE_REVIEW_MODE = new URLSearchParams(location.search).get("battleReview") === "1";
const TRAFFIC_REVIEW_MODE = new URLSearchParams(location.search).get("trafficReview") === "1";
const LANE_REVIEW_MODE = new URLSearchParams(location.search).get("laneReview") === "1";
const MOTION_REVIEW_MODE = new URLSearchParams(location.search).get("motionReview") === "1";
const MOTION_REVIEW_FRAME = Math.max(
  -1,
  Math.min(5, Number(new URLSearchParams(location.search).get("motionFrame") ?? -1))
);
const FIELD_SIZE = 18;
const SELECTED_ID = Math.max(
  1,
  Math.min(FIELD_SIZE, Number(new URLSearchParams(location.search).get("selected")) || 1)
);
const RACE_METERS = 1600;
stage.dataset.engineLineage = "lane5-fixed-step-plus-four-morph-run-sheets";
stage.dataset.morphSet = "S,P,E,A";
stage.dataset.fieldSize = String(FIELD_SIZE);
stage.dataset.cameraPolicy = "selected-plus-nearby";
stage.dataset.peaMotionVersion = "grounded-stride-v2";
const LANE_PATTERN = [1, 2, 0, 3, 1, 3, 0, 2];
const CRUISE_PATTERN = [36.8,34.7,35.9,34.9,36.1,35.2,35.6,34.8];
const ACCEL_PATTERN = [15.0,13.4,14.3,13.6,14.0,13.5,13.9,13.4];
const NAMES = [
  "Mica","Vela","Rook","Serein","Flint","Nacre","Ilex","Sora",
  "Tarin","Ossa","Brink","Nyx","Arden","Vale","Kest","Orin","Tess","Moro"
];
const LANES = Array.from({ length: FIELD_SIZE }, (_, i) => LANE_PATTERN[i % LANE_PATTERN.length]);
const START_VISUAL_OFFSETS = (() => {
  const laneRows = [0,0,0,0];
  return LANES.map((lane) => {
    const laneIndex = Math.max(0, Math.min(3, Math.round(lane)));
    const row = laneRows[laneIndex]++;
    return -row * 3.2;
  });
})();
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
  P: { cadence:0.94, width:1.08, lift:0.62 },
  E: { cadence:0.97, width:1.02, lift:0.52 },
  A: { cadence:1.02, width:1.06, lift:0.82 }
};

const PEA_MOTION_V2 = {
  P: {
    durations:[0.76,1.18,0.82,0.82,1.26,1.16],
    transform:{
      CONTACT:{ sx:1.00, sy:1.01, lean:-0.004, lift: 0.000 },
      PUSH:   { sx:1.06, sy:0.98, lean: 0.018, lift:-0.006 },
      LIFT:   { sx:1.02, sy:0.99, lean: 0.014, lift:-0.020 },
      FLIGHT: { sx:1.08, sy:0.96, lean: 0.018, lift:-0.052 },
      REACH:  { sx:1.07, sy:0.97, lean: 0.010, lift:-0.030 },
      LAND:   { sx:1.00, sy:1.02, lean:-0.006, lift:-0.004 }
    }
  },
  E: {
    durations:[0.82,0.98,0.78,1.08,1.36,0.98],
    transform:{
      CONTACT:{ sx:1.00, sy:1.00, lean:-0.004, lift: 0.000 },
      PUSH:   { sx:1.03, sy:0.99, lean: 0.010, lift:-0.006 },
      LIFT:   { sx:1.02, sy:1.00, lean: 0.008, lift:-0.018 },
      FLIGHT: { sx:1.08, sy:0.98, lean: 0.006, lift:-0.044 },
      REACH:  { sx:1.10, sy:0.98, lean: 0.004, lift:-0.026 },
      LAND:   { sx:0.99, sy:1.01, lean:-0.006, lift:-0.003 }
    }
  },
  A: {
    durations:[0.72,1.12,0.74,1.14,1.28,1.00],
    transform:{
      CONTACT:{ sx:1.00, sy:0.99, lean: 0.004, lift: 0.000 },
      PUSH:   { sx:1.07, sy:0.96, lean: 0.022, lift:-0.008 },
      LIFT:   { sx:1.04, sy:0.97, lean: 0.018, lift:-0.024 },
      FLIGHT: { sx:1.12, sy:0.94, lean: 0.020, lift:-0.060 },
      REACH:  { sx:1.10, sy:0.95, lean: 0.014, lift:-0.035 },
      LAND:   { sx:0.99, sy:1.00, lean:-0.006, lift:-0.004 }
    }
  }
};

function peaFrameIndex(morph, cyclePosition) {
  const profile = PEA_MOTION_V2[morph];
  if (!profile) return Math.floor(cyclePosition) % RUN_FRAMES.length;
  let cursor = 0;
  for (let index = 0; index < profile.durations.length; index++) {
    cursor += profile.durations[index];
    if (cyclePosition < cursor) return index;
  }
  return profile.durations.length - 1;
}

const AGENT_COMMAND_DURATION_MS = 8000;
const AGENT_FEEDBACK_HOLD_MS = 2400;
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

  let minX = fw;
  let maxX = -1;
  let minY = fh;
  let maxY = -1;
  let footY = -1;
  const footMinX = fw * 0.18;
  const footMaxX = fw * 0.88;

  for (let i = 0; i < count; i++) {
    if (!visited[i]) {
      alpha[i * 4 + 3] = 0;
      continue;
    }
    const x = i % fw;
    const y = Math.floor(i / fw);
    minX = Math.min(minX, x);
    maxX = Math.max(maxX, x);
    minY = Math.min(minY, y);
    maxY = Math.max(maxY, y);
    if (x >= footMinX && x <= footMaxX) footY = Math.max(footY, y);
  }
  c.putImageData(pixels, 0, 0);
  canvas.__motionMetrics = {
    minX, maxX, minY, maxY,
    footYNorm: footY >= 0 ? footY / Math.max(1, fh - 1) : 0.98
  };
  return canvas;
}

for (const morph of ["S","P","E","A"]) {
  const image = new Image();
  image.decoding = "async";
  image.onload = () => {
    const frames = RUN_FRAMES.map((frame) => extractConnectedFrame(image, frame.col, frame.row));
    spriteFrames.set(morph, frames);
    if (morph !== "S") {
      const feet = frames.map((frame) => frame.__motionMetrics?.footYNorm ?? 0.98);
      const spread = Math.max(...feet) - Math.min(...feet);
      stage.dataset[`${morph.toLowerCase()}FootSpreadRaw`] = spread.toFixed(3);
      stage.dataset[`${morph.toLowerCase()}GroundAnchor`] = "auto-foot-v2";
    }
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
let cameraRoll = 0;
let cameraLift = 0;
let overtakePulse = 0;
let previousRank = FIELD_SIZE;

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
      : BATTLE_REVIEW_MODE
        ? i===0 ? 120 : i===1 ? 124 : 72 - (i-2)*2
        : TRAFFIC_REVIEW_MODE
          ? i===0 ? 100 : i===1 ? 105 : 62 - (i-2)*1.6
          : LANE_REVIEW_MODE
            ? i===0 ? 100 : i===1 ? 104 : i===2 ? 103 : 62 - (i-3)*1.4
            : MOTION_REVIEW_MODE
              ? i===SELECTED_ID-1 ? 120 : 54 - i*1.6
              : 0,
    speed:0,
    cruise:CRUISE[i],
    accel:ACCEL[i],
    stamina:100,
    fatigue:0,
    pressure:0,
    creatureState:"FRESH",
    agent:createAgentState(i),
    startVisualOffset:(FINISH_REVIEW_MODE || BATTLE_REVIEW_MODE || TRAFFIC_REVIEW_MODE || LANE_REVIEW_MODE || MOTION_REVIEW_MODE)
      ? 0
      : START_VISUAL_OFFSETS[i],
    depthBias:[-0.14,0.10,-0.08,0.14,0.04][Math.floor(i/4)%5],
    lane:BATTLE_REVIEW_MODE && i<2
      ? 1
      : TRAFFIC_REVIEW_MODE && i===0
        ? 1
        : TRAFFIC_REVIEW_MODE && i===1
          ? 1.42
          : LANE_REVIEW_MODE && i===0
            ? 1
            : LANE_REVIEW_MODE && i===1
              ? 1
              : LANE_REVIEW_MODE && i===2
                ? 2
                : MOTION_REVIEW_MODE && i===SELECTED_ID-1
                  ? 1.5
                  : LANES[i],
    targetLane:BATTLE_REVIEW_MODE && i<2
      ? 1
      : TRAFFIC_REVIEW_MODE && i===0
        ? 1
        : TRAFFIC_REVIEW_MODE && i===1
          ? 1.42
          : LANE_REVIEW_MODE && i===0
            ? 1
            : LANE_REVIEW_MODE && i===1
              ? 1
              : LANE_REVIEW_MODE && i===2
                ? 2
                : MOTION_REVIEW_MODE && i===SELECTED_ID-1
                  ? 1.5
                  : LANES[i],
    phaseOffset:i*0.87,
    cooldown:(BATTLE_REVIEW_MODE && i===1) || (TRAFFIC_REVIEW_MODE && i<2) || (LANE_REVIEW_MODE && (i===1 || i===2)) ? 999999 : 0,
    laneHoldUntil:0,
    laneDecisionCount:0,
    laneChangeStartedAt:-999999,
    command:"HOLD FORM",
    reason:"Pre-start",
    finished:false,
    finishPlace:0,
    finishTime:0
  }));
}
let racers = makeRacers();
const INITIAL_LOGICAL_DISTANCE_SPREAD = (() => {
  const values = racers.map((r) => r.distance);
  return Math.max(...values)-Math.min(...values);
})();
const INITIAL_VISUAL_OFFSET_SPREAD = (() => {
  const values = racers.map((r) => r.startVisualOffset || 0);
  return Math.max(...values)-Math.min(...values);
})();
let agentTargetIndex = 0;
let agentFeedbackRunnerId = -1;
let agentFeedbackCommand = "NEUTRAL";
let agentFeedbackUntil = -999999;
let battleRivalId = -1;
let battleState = "CLEAR";
let battleGap = Infinity;
let battleEventUntil = -999999;

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


function runnerCode(r) {
  return `${r.morph}${String(r.id).padStart(2,"0")}`;
}

function battleCandidateFor(focus) {
  let best = null;
  let bestScore = Infinity;
  for (const other of racers) {
    if (other===focus || other.finished) continue;
    const gap = other.distance-focus.distance;
    if (gap<=0 || gap>10) continue;
    const laneGap = Math.abs(other.lane-focus.lane);
    if (laneGap>1.15) continue;
    const score = gap + laneGap*2.8;
    if (score<bestScore) {
      bestScore=score;
      best={rival:other,gap,laneGap};
    }
  }
  return best;
}

function exposeBattleState(focus, rival, state, gap) {
  battleState=state;
  battleGap=Math.abs(gap);
  if (battleReadoutEl) {
    battleReadoutEl.hidden=false;
    battleReadoutEl.dataset.state=state==="OVERTAKE COMPLETE" ? "complete" : "active";
  }
  if (battleStateEl) battleStateEl.textContent=state;
  if (battleMetaEl) {
    const arrow = state==="OVERTAKE COMPLETE" ? "PASSED" : "→";
    battleMetaEl.textContent=`${runnerCode(focus)} ${arrow} ${runnerCode(rival)} · ${battleGap.toFixed(1)} m`;
  }
  stage.dataset.battleVisible="1";
  stage.dataset.battleState=state;
  stage.dataset.battleRivalId=String(rival.id);
  stage.dataset.battleRivalCode=runnerCode(rival);
  stage.dataset.battleGap=battleGap.toFixed(2);
}

function clearBattleState() {
  battleState="CLEAR";
  battleGap=Infinity;
  battleRivalId=-1;
  if (battleReadoutEl) battleReadoutEl.hidden=true;
  stage.dataset.battleVisible="0";
  stage.dataset.battleState="CLEAR";
  stage.dataset.battleRivalId="";
  stage.dataset.battleRivalCode="";
  stage.dataset.battleGap="";
}

function updateBattleState() {
  const focus=selected();
  if (!focus || focus.finished || raceState!=="running" || elapsed<700) {
    clearBattleState();
    return;
  }

  if (battleState==="OVERTAKE COMPLETE" && elapsed<battleEventUntil) {
    const rival=racers.find((r)=>r.id===battleRivalId);
    if (rival) exposeBattleState(focus,rival,"OVERTAKE COMPLETE",focus.distance-rival.distance);
    return;
  }

  if (battleRivalId>0) {
    const previousRival=racers.find((r)=>r.id===battleRivalId);
    if (previousRival && focus.distance>previousRival.distance+0.02) {
      battleEventUntil=elapsed+1600;
      exposeBattleState(focus,previousRival,"OVERTAKE COMPLETE",focus.distance-previousRival.distance);
      return;
    }
  }

  const candidate=battleCandidateFor(focus);
  if (!candidate) {
    clearBattleState();
    return;
  }

  battleRivalId=candidate.rival.id;
  const closing=focus.speed-candidate.rival.speed;
  exposeBattleState(
    focus,
    candidate.rival,
    closing>0.25 ? "OVERTAKE ATTEMPT" : "CLOSE BATTLE",
    candidate.gap
  );
}

function sameTrafficLine(a, b, tolerance=0.58) {
  return Math.abs(a-b)<=tolerance;
}

function occupiedNear(r, lane, radius=8.5) {
  return racers.some(
    (o) => o!==r &&
      !o.finished &&
      sameTrafficLine(o.lane,lane) &&
      Math.abs(o.distance-r.distance)<radius
  );
}
function gapAhead(r) {
  let best = Infinity;
  for (const o of racers) {
    if (o===r || o.finished || !sameTrafficLine(o.lane,r.lane)) continue;
    const g = o.distance-r.distance;
    if (g>0 && g<best) best=g;
  }
  return best;
}
function laneForwardGap(r, lane, limit=22) {
  let best = limit;
  for (const other of racers) {
    if (other===r || other.finished || !sameTrafficLine(other.lane,lane)) continue;
    const gap=other.distance-r.distance;
    if (gap>0 && gap<best) best=gap;
  }
  return best;
}

function laneRearGap(r, lane, limit=12) {
  let best = limit;
  for (const other of racers) {
    if (other===r || other.finished || !sameTrafficLine(other.lane,lane)) continue;
    const gap=r.distance-other.distance;
    if (gap>0 && gap<best) best=gap;
  }
  return best;
}

function laneOpportunityScore(r, lane) {
  const forward=laneForwardGap(r,lane,22);
  const rear=laneRearGap(r,lane,12);
  const rearPenalty=rear<5 ? (5-rear)*2.4 : 0;
  const shiftCost=Math.abs(lane-r.lane)*1.35;
  return forward-rearPenalty-shiftCost;
}

function chooseLane(r) {
  const currentLane=clamp(Math.round(r.lane),0,3);
  const currentScore=laneOpportunityScore(r,currentLane);
  let bestLane=currentLane;
  let bestScore=currentScore;

  for (let lane=0;lane<=3;lane++) {
    if (lane===currentLane || occupiedNear(r,lane,7.0)) continue;
    const score=laneOpportunityScore(r,lane);
    if (score>bestScore) {
      bestScore=score;
      bestLane=lane;
    }
  }

  // Do not weave for marginal gains. A line change needs a clear traffic benefit.
  return bestScore>=currentScore+2.5 ? bestLane : currentLane;
}

function computeRunnerPressure(r) {
  if (r.finished) return 0;

  let strongest = 0;
  for (const other of racers) {
    if (other===r || other.finished) continue;
    const gap = other.distance-r.distance;
    if (gap<=0 || gap>8.0) continue;

    const laneGap = Math.abs(other.lane-r.lane);
    if (laneGap>0.82) continue;

    const longitudinal = 1-gap/8.0;
    const lateral = 1-laneGap/0.82;
    strongest = Math.max(strongest,longitudinal*lateral);
  }
  return clamp(strongest,0,1);
}

function deriveCreatureState(r) {
  if (r.fatigue>=0.68 || r.stamina<=30) return "TIRED";
  if (r.fatigue>=0.34 || r.stamina<=58) return "WORKING";
  if (r.pressure>=0.58) return "PRESSURED";
  return "FRESH";
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
  const pressurePenalty = command === "PUSH"
    ? lerp(1,0.62,r.pressure)
    : command === "CONSERVE"
      ? lerp(1,0.88,r.pressure)
      : 1;
  const response = command === "NEUTRAL"
    ? 0
    : compat * staminaFactor * fatiguePenalty * pressurePenalty;
  agent.response = response;

  let speedFactor = 1;
  let staminaDrainScale = 1;
  let fatigueDelta = r.speed > r.cruise * 0.98 ? 0.0018 : -0.0015;

  if (command === "PUSH") {
    const effective = Math.max(0.35, response);
    speedFactor = 1 + 0.035 * response;
    staminaDrainScale = 1 + 0.55 * effective;
    fatigueDelta = 0.0105 * effective + 0.0040 * r.pressure;
    agent.lastResult = response >= 0.72 ? "STRONG" : response >= 0.46 ? "PARTIAL" : "WEAK";
  } else if (command === "CONSERVE") {
    const effective = Math.max(0.35, response);
    speedFactor = 1 - 0.025 * response;
    staminaDrainScale = 0.34;
    fatigueDelta = -0.0065 * effective;
    agent.lastResult = response >= 0.72 ? "SETTLED" : response >= 0.46 ? "PARTIAL" : "WEAK";
  }

  r.fatigue = clamp(r.fatigue + fatigueDelta * dt, 0, 1);
  r.creatureState = deriveCreatureState(r);
  return { speedFactor, staminaDrainScale };
}

function agentFeedbackTone(result) {
  if (["STRONG","SETTLED"].includes(result)) return "positive";
  if (result==="PARTIAL") return "partial";
  if (result==="WEAK") return "weak";
  return "neutral";
}

function showAgentFeedback(r, command) {
  if (!agentFeedbackEl || !r?.agent) return;
  agentFeedbackRunnerId = r.id;
  agentFeedbackCommand = command;
  agentFeedbackUntil = elapsed + (command==="CLEAR" ? 1600 : AGENT_FEEDBACK_HOLD_MS);
  agentFeedbackEl.hidden = false;
  agentFeedbackEl.dataset.tone = "neutral";
  if (agentFeedbackMetaEl) agentFeedbackMetaEl.textContent = `${r.agent.id} → ${r.name}`;
  if (agentFeedbackCommandEl) agentFeedbackCommandEl.textContent = command;
  if (agentFeedbackResultEl) {
    agentFeedbackResultEl.textContent = command==="CLEAR" ? "CLEARED" : "PENDING";
  }
  stage.dataset.agentFeedbackVisible = "1";
  stage.dataset.agentFeedbackRunner = String(r.id);
  stage.dataset.agentFeedbackCommand = command;
  stage.dataset.agentFeedbackResult = command==="CLEAR" ? "CLEARED" : "PENDING";
}

function updateAgentFeedback() {
  if (!agentFeedbackEl) return;
  if (agentFeedbackRunnerId<0 || elapsed>=agentFeedbackUntil || raceState==="finished") {
    agentFeedbackEl.hidden = true;
    stage.dataset.agentFeedbackVisible = "0";
    return;
  }

  const r = racers.find((runner) => runner.id===agentFeedbackRunnerId);
  if (!r?.agent) return;
  const result = agentFeedbackCommand==="CLEAR"
    ? "CLEARED"
    : r.agent.lastResult==="NEUTRAL"
      ? "PENDING"
      : r.agent.lastResult;

  agentFeedbackEl.dataset.tone = agentFeedbackTone(result);
  if (agentFeedbackResultEl) agentFeedbackResultEl.textContent = result;
  stage.dataset.agentFeedbackResult = result;
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
  showAgentFeedback(r, command);
}

function targetSpeedFor(r) {
  const p = r.distance/RACE_METERS;
  let target = r.cruise * (p<.15 ? 1.035 : p>.87 ? 1.085 : p>.68 ? 1.025 : 1.0);
  const gap = gapAhead(r);
  const laneSettled=Math.abs(r.lane-r.targetLane)<0.04;
  const canReconsiderLane=r.cooldown<=0 && elapsed>=r.laneHoldUntil && laneSettled;
  if (gap<7.5) {
    if (canReconsiderLane) {
      const nextLane = chooseLane(r);
      if (Math.abs(nextLane-r.lane)>=0.25) {
        r.targetLane = nextLane;
        r.cooldown = 1200;
        r.laneHoldUntil = elapsed + 3000;
        r.laneChangeStartedAt = elapsed;
        r.laneDecisionCount += 1;
        r.command = "SHIFT LINE";
        r.reason = "Better forward clearance";
        target *= 1.015;
      } else {
        target *= clamp(gap/7.5,.77,.97);
        r.command = "HOLD GAP";
        r.reason = "Blocked";
      }
    } else {
      // Commitment blocks another weave, not safe following behavior.
      target *= clamp(gap/7.5,.77,.97);
      r.command = laneSettled ? "HOLD LINE" : "COMPLETE SHIFT";
      r.reason = "Committed line";
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
    r.pressure = computeRunnerPressure(r);
    r.creatureState = deriveCreatureState(r);

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
    r.creatureState = deriveCreatureState(r);
    r.distance += Math.max(0,r.speed)*dt;

    if (r.distance>=RACE_METERS) {
      r.distance=RACE_METERS;
      r.finished=true;
      r.finishPlace=++finishCounter;
      r.finishTime=elapsed;
    }
  }
  updateBattleState();
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
  const stops=portrait?[-132,-43,49,142]:[-94,-31,34,101];
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
  stage.dataset.laneSpread=(boundaries[4]-boundaries[0]).toFixed(1);

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
  const startFormationFactor =
    raceState==="countdown"
      ? 1
      : raceState==="running"
        ? clamp(1-elapsed/2400,0,1)
        : 0;
  let minEdge=Infinity;
  let maxEdge=-Infinity;
  let visibleLabelCount=0;
  let labelCollisionAdjustments=0;
  const labelRequests=[];
  for(const r of racers){
    const finishSpread = raceState==="finished" && r.finishPlace
      ? (r.finishPlace-1)*1.35
      : 0;
    const visualDistance=Math.max(
      -20,
      r.distance-finishSpread+(r.startVisualOffset||0)*startFormationFactor
    );
    if(MOTION_REVIEW_MODE && r.id!==SELECTED_ID) continue;
    const x=screenXForMeters(visualDistance);
    if(x<-220 || x>width+260) continue;
    const lane=clamp(r.lane+(r.depthBias||0),0,3);
    const y=laneYAt(visualDistance,lane);
    list.push({r,x,y,lane,visualDistance});
  }
  list.sort((a,b)=>a.lane-b.lane);

  for(const item of list){
    const r=item.r;
    const selectedRacer=r.id===SELECTED_ID;
    const battleRival=r.id===battleRivalId && stage.dataset.battleVisible==="1";
    const scale=laneScale(item.lane);
    const meta=MORPH_META[r.morph] ?? MORPH_META.S;
    const frames=spriteFrames.get(r.morph);
    const baseW = MOTION_REVIEW_MODE && r.id===SELECTED_ID
      ? (width<700 ? clamp(width*.42,170,240) : clamp(width*.23,250,340))
      : width<700
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
    const cyclePosition=((frameFloat%RUN_FRAMES.length)+RUN_FRAMES.length)%RUN_FRAMES.length;
    const frameIndex=MOTION_REVIEW_MODE && r.id===SELECTED_ID && MOTION_REVIEW_FRAME>=0
      ? MOTION_REVIEW_FRAME
      : r.morph==="S"
        ? Math.floor(cyclePosition)
        : peaFrameIndex(r.morph,cyclePosition);
    const frame=RUN_FRAMES[frameIndex];

    const slope=terrainSlope(item.visualDistance);
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
      const peaProfile=PEA_MOTION_V2[r.morph];
      const phaseTransform=peaProfile?.transform?.[frame.phase] ?? { sx:1, sy:1, lean:0, lift:0 };
      const drawW=spriteW*phaseTransform.sx;
      const drawH=spriteH*phaseTransform.sy;
      const footNorm=frameCanvas.__motionMetrics?.footYNorm ?? 0.98;
      const groundCorrection=r.morph==="S" ? 0 : (0.98-footNorm)*drawH;
      const legacyLift=r.morph==="S" ? frame.y*drawH*.12*meta.lift : 0;
      const phaseLift=r.morph==="S" ? 0 : phaseTransform.lift*drawH;
      const footAdjust=groundCorrection+legacyLift+phaseLift;

      ctx.save();
      ctx.translate(item.x,item.y-drawH*.48);
      ctx.rotate(lean+phaseTransform.lean);
      if(selectedRacer){
        ctx.shadowColor="rgba(126,226,255,.85)";
        ctx.shadowBlur=clamp(drawW*.08,4,18);
      } else if(battleRival){
        ctx.shadowColor="rgba(255,220,130,.88)";
        ctx.shadowBlur=clamp(drawW*.075,4,16);
      }
      ctx.drawImage(frameCanvas,-drawW/2,-drawH/2+footAdjust,drawW,drawH);
      ctx.restore();

      stage.dataset[`${r.morph.toLowerCase()}Animated`] = "true";
      stage.dataset[`${r.morph.toLowerCase()}Frame`] = String(frameIndex);
      if(r.morph!=="S"){
        stage.dataset[`${r.morph.toLowerCase()}MotionProfile`] = "grounded-stride-v2";
        stage.dataset[`${r.morph.toLowerCase()}FootAdjust`] = footAdjust.toFixed(2);
      }
    }

    const raceRank=rankOf(r);
    const showLabel=selectedRacer || battleRival || raceRank<=2;
    if(showLabel){
      const txt=selectedRacer
        ? `YOU · ${r.morph}${String(r.id).padStart(2,"0")}`
        : battleRival
          ? `RIVAL · ${r.morph}${String(r.id).padStart(2,"0")}`
          : `#${raceRank} ${r.morph}${String(r.id).padStart(2,"0")}`;
      labelRequests.push({
        x:item.x,
        baseY:item.y-spriteH*.66-(battleRival?(width<700?22:16):0),
        txt,
        selectedRacer,
        battleRival,
        priority:selectedRacer?3:battleRival?2:1
      });
    }

    if(selectedRacer){
      stage.dataset.selectedRunFrame=String(frameIndex);
      stage.dataset.selectedRunPhase=frame.phase;
      stage.dataset.selectedMorph=r.morph;
      stage.dataset.selectedX=item.x.toFixed(1);
      stage.dataset.selectedY=item.y.toFixed(1);
    }
  }

  const placedLabelBoxes=[];
  const labelShifts=width<700 ? [0,-20,20,-40,40,-60,60] : [0,-18,18,-36,36,-54,54];
  labelRequests
    .sort((a,b)=>b.priority-a.priority)
    .forEach((label) => {
      ctx.font=`800 ${width<700?9:11}px ui-monospace, Menlo, monospace`;
      ctx.textAlign="center";
      const tw=ctx.measureText(label.txt).width+10;
      let chosenY=label.baseY;
      let chosenBox=null;
      for(const shift of labelShifts){
        const y=label.baseY+shift;
        const box={left:label.x-tw/2-3,right:label.x+tw/2+3,top:y-14,bottom:y+4};
        const overlaps=placedLabelBoxes.some((other)=>
          box.left<other.right && box.right>other.left &&
          box.top<other.bottom && box.bottom>other.top
        );
        if(!overlaps){
          chosenY=y;
          chosenBox=box;
          if(shift!==0) labelCollisionAdjustments++;
          break;
        }
      }
      if(!chosenBox){
        if(label.priority<2) return;
        chosenBox={left:label.x-tw/2-3,right:label.x+tw/2+3,top:chosenY-14,bottom:chosenY+4};
        labelCollisionAdjustments++;
      }
      placedLabelBoxes.push(chosenBox);
      visibleLabelCount++;
      ctx.fillStyle=label.selectedRacer?"rgba(8,41,56,.94)":"rgba(3,10,15,.82)";
      ctx.fillRect(label.x-tw/2,chosenY-12,tw,15);
      ctx.fillStyle=label.selectedRacer?"#9ce9fb":label.battleRival?"#ffe1a0":"#eef9ff";
      ctx.fillText(label.txt,label.x,chosenY);
    });

  let labelOverlapCount=0;
  for(let i=0;i<placedLabelBoxes.length;i++){
    for(let j=i+1;j<placedLabelBoxes.length;j++){
      const a=placedLabelBoxes[i], b=placedLabelBoxes[j];
      if(a.left<b.right && a.right>b.left && a.top<b.bottom && a.bottom>b.top){
        labelOverlapCount++;
      }
    }
  }

  stage.dataset.visibleRacers=String(list.length);
  stage.dataset.visibleLabels=String(visibleLabelCount);
  stage.dataset.labelLayout="priority-collision-avoidance";
  stage.dataset.labelCollisionAdjustments=String(labelCollisionAdjustments);
  stage.dataset.labelOverlapCount=String(labelOverlapCount);
  stage.dataset.startFormationFactor=startFormationFactor.toFixed(3);
  stage.dataset.visualDepthStagger="enabled";
  stage.dataset.finishSpreadMeters="1.35";
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
  if(MOTION_REVIEW_MODE){
    const targetPPM=width<700?5.2:6.8;
    pixelsPerMeter=lerp(pixelsPerMeter,targetPPM,.16);
    cameraMeters=lerp(cameraMeters,focus.distance+2.0,.18);
    stage.dataset.pixelsPerMeter=pixelsPerMeter.toFixed(2);
    stage.dataset.packSpan="0.00";
    stage.dataset.cameraSubject="motion-review-isolated";
    stage.dataset.cameraRelevantCount="1";
    return;
  }
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
  const rankNow=rankOf(focus);
  if (raceState==="running" && rankNow<previousRank) overtakePulse=1;
  previousRank=rankNow;
  overtakePulse=Math.max(0,overtakePulse-.018);

  const slope=terrainSlope(focus.distance);
  const bank=courseBank(focus.distance);
  const targetRoll=clamp(bank*.00045+slope*.0015,-.014,.014);
  cameraRoll=lerp(cameraRoll,targetRoll,.06);
  cameraLift=lerp(cameraLift,terrainY(focus.distance)*.22,.06);

  const shake=speedNorm>.66?(speedNorm-.66)*5.1:0;
  const pulseZoom=1+overtakePulse*.007;
  ctx.save();
  ctx.translate(width*.5,height*.58);
  ctx.rotate(cameraRoll);
  ctx.scale(pulseZoom,pulseZoom);
  ctx.translate(-width*.5,-height*.58-cameraLift*.035);
  ctx.translate(Math.sin(elapsed*.041)*shake,Math.sin(elapsed*.053+1.2)*shake*.38);

  drawBackground();
  drawTrack();
  drawCourseLandmarks();
  drawRacers();
  drawForeground();
  drawSpeedRush();
  ctx.restore();

  stage.dataset.cameraRoll=cameraRoll.toFixed(4);
  stage.dataset.cameraLift=cameraLift.toFixed(2);
  stage.dataset.overtakePulse=overtakePulse.toFixed(3);

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
    if (agentPressureEl) agentPressureEl.textContent = `${Math.round(agentTarget.pressure * 100)}%`;
    if (creatureStateEl) creatureStateEl.textContent = agentTarget.creatureState;
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
    stage.dataset.agentFocusPressure = agentTarget.pressure.toFixed(3);
    stage.dataset.agentFocusCreatureState = agentTarget.creatureState;
  }
  updateAgentFeedback();

  if(now-lastRankingPaint>180){
    lastRankingPaint=now;
    ui.ranking.innerHTML=ranks.map((r,i)=>`<span class="${r.id===SELECTED_ID?"selected":""}">#${i+1} ${r.morph}${String(r.id).padStart(2,"0")}</span>`).join("");
  }

  stage.dataset.selectedDistance=focus.distance.toFixed(2);
  stage.dataset.selectedSpeed=focus.speed.toFixed(2);
  stage.dataset.selectedRank=String(rankOf(focus));
  const selectedGap=gapAhead(focus);
  stage.dataset.selectedGapAhead=Number.isFinite(selectedGap)?selectedGap.toFixed(2):"";
  stage.dataset.selectedLane=focus.lane.toFixed(2);
  stage.dataset.selectedTargetLane=focus.targetLane.toFixed(2);
  stage.dataset.selectedLaneDecisionCount=String(focus.laneDecisionCount);
  stage.dataset.selectedLaneHoldRemaining=String(Math.max(0,focus.laneHoldUntil-elapsed).toFixed(0));
  stage.dataset.laneDecisionModel="clearance-score-with-hysteresis";
  stage.dataset.trafficModel="continuous-lane-proximity";
  stage.dataset.courseBank=courseBank(focus.distance).toFixed(2);
  stage.dataset.cameraMeters=cameraMeters.toFixed(2);
  stage.dataset.frameCounter=String(frameCounter);
}

function resetRace(){
  racers=makeRacers();
  agentTargetIndex=0;
  agentFeedbackRunnerId=-1;
  agentFeedbackCommand="NEUTRAL";
  agentFeedbackUntil=-999999;
  if (agentFeedbackEl) agentFeedbackEl.hidden=true;
  battleRivalId=-1;
  battleState="CLEAR";
  battleGap=Infinity;
  battleEventUntil=-999999;
  if (battleReadoutEl) battleReadoutEl.hidden=true;
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
  cameraRoll=0;
  cameraLift=0;
  overtakePulse=0;
  previousRank=FIELD_SIZE;
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
  stage.dataset.agentFeedbackVisible="0";
  stage.dataset.agentFeedbackRunner="";
  stage.dataset.agentFeedbackCommand="";
  stage.dataset.agentFeedbackResult="";
stage.dataset.peaMotionVersion="grounded-stride-v2";
  stage.dataset.battleVisible="0";
  stage.dataset.battleState="CLEAR";
  stage.dataset.battleRivalId="";
  stage.dataset.battleRivalCode="";
  stage.dataset.battleGap="";
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
stage.dataset.battleReview=BATTLE_REVIEW_MODE?"1":"0";
stage.dataset.trafficReview=TRAFFIC_REVIEW_MODE?"1":"0";
stage.dataset.laneReview=LANE_REVIEW_MODE?"1":"0";
stage.dataset.motionReview=MOTION_REVIEW_MODE?"1":"0";
stage.dataset.reviewSelectedId=String(SELECTED_ID);
stage.dataset.motionReviewFrame=String(MOTION_REVIEW_FRAME);
stage.dataset.laneDecisionModel="clearance-score-with-hysteresis";
stage.dataset.trafficModel="continuous-lane-proximity";
stage.dataset.startModel="logical-level-visual-grid-decay";
stage.dataset.startLogicalSpread=INITIAL_LOGICAL_DISTANCE_SPREAD.toFixed(2);
stage.dataset.startVisualSpread=INITIAL_VISUAL_OFFSET_SPREAD.toFixed(2);
stage.dataset.battleVisible="0";
stage.dataset.battleState="CLEAR";
stage.dataset.battleRivalId="";
stage.dataset.battleRivalCode="";
stage.dataset.battleGap="";
stage.dataset.agentModel="command-only-creature-resolved";
stage.dataset.agentTargetRunner="1";
stage.dataset.agentTargetMorph="S";
stage.dataset.agentCommand="NEUTRAL";
stage.dataset.agentFeedbackVisible="0";
stage.dataset.agentFeedbackRunner="";
stage.dataset.agentFeedbackCommand="";
stage.dataset.agentFeedbackResult="";

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