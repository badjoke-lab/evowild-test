// Lane 5 runtime.
// Race-loop structure is ported from olivierluethy/Horse-Racing (MIT),
// especially the requestAnimationFrame race loop / countdown / per-runner progress model.
// EvoWild changes: S-type six-frame sprite sheet, camera tracking, parallax,
// metre-based race distance, stamina/pace variation, and finish-line projection.

const stage = document.getElementById("raceStage");
const track = document.getElementById("track");
const farLayer = document.getElementById("farLayer");
const midLayer = document.getElementById("midLayer");
const foregroundLayer = document.getElementById("foregroundLayer");
const finishLine = document.getElementById("finishLine");
const countdown = document.getElementById("countdown");
const countdownText = document.getElementById("countdownText");
const startButton = document.getElementById("startButton");
const restartButton = document.getElementById("restartButton");
const stateText = document.getElementById("stateText");
const leaderText = document.getElementById("leaderText");
const distanceText = document.getElementById("distanceText");
const speedText = document.getElementById("speedText");
const resultText = document.getElementById("resultText");

const RACE_LENGTH = 1600;
const LANE_COUNT = 5;
const SELECTED = 3;
const runners = Array.from(document.querySelectorAll(".runner"));

const BASE_SPEED = [33.4, 34.2, 33.8, 34.8, 34.0];
const ACCEL = [8.8, 8.4, 8.7, 9.1, 8.6];
const FINISH_KICK = [1.4, 0.7, 1.1, 1.8, 0.9];
const PHASE = [0.2, 1.7, 2.9, 4.1, 5.4];

let horsePositions = [0, 0, 0, 0, 0];
let horseSpeeds = [0, 0, 0, 0, 0];
let horseEnergy = [100, 100, 100, 100, 100];
let raceInProgress = false;
let finished = false;
let winnerLane = -1;
let startStamp = 0;
let lastStamp = 0;
let cameraMeters = 0;
let cameraVelocity = 0;
let frameId = 0;
let jumpCooldown = [0,0,0,0,0];
let nextTerrainCue = [210,255,300,235,280];

function clamp(v, min, max) {
  return Math.max(min, Math.min(max, v));
}

function ease(current, target, rate, dt) {
  return current + (target - current) * (1 - Math.exp(-rate * dt));
}

function resetRace() {
  cancelAnimationFrame(frameId);
  raceInProgress = false;
  finished = false;
  winnerLane = -1;
  horsePositions = [0,0,0,0,0];
  horseSpeeds = [0,0,0,0,0];
  horseEnergy = [100,100,100,100,100];
  cameraMeters = 0;
  cameraVelocity = 0;
  jumpCooldown = [0,0,0,0,0];
  nextTerrainCue = [210,255,300,235,280];

  stage.dataset.raceState = "ready";
  stage.dataset.engineLineage = "olivierluethy-horse-racing-direct-port";
  stage.dataset.upstreamRuntime = "active";
  stage.dataset.selectedRunner = "S04";
  stateText.textContent = "READY";
  leaderText.textContent = "—";
  distanceText.textContent = "0";
  speedText.textContent = "0.0";
  resultText.textContent = "Existing-game race loop first. EvoWild-specific systems are intentionally not layered on top yet.";
  finishLine.style.opacity = "0";

  runners.forEach((el, i) => {
    el.style.transform = `translate3d(${80 + i * 4}px,-50%,0)`;
    el.classList.remove("jump");
  });

  renderWorld(0);
}

function runCountdown(done) {
  const steps = ["3", "2", "1", "GO"];
  countdown.classList.remove("hidden");
  let index = 0;

  function tick() {
    if (index >= steps.length) {
      countdown.classList.add("hidden");
      done();
      return;
    }
    countdownText.textContent = steps[index++];
    setTimeout(tick, 620);
  }
  tick();
}

function startGame() {
  if (raceInProgress || finished) return;

  startButton.disabled = true;
  stage.dataset.raceState = "countdown";
  stateText.textContent = "COUNTDOWN";

  runCountdown(() => {
    raceInProgress = true;
    stage.dataset.raceState = "running";
    stateText.textContent = "RACING";
    resultText.textContent = "Upstream race loop active — no Race Agent layer yet.";
    startStamp = performance.now();
    lastStamp = startStamp;
    frameId = requestAnimationFrame(frame);
  });
}

function paceTarget(i) {
  const p = horsePositions[i] / RACE_LENGTH;
  let target = BASE_SPEED[i];

  if (p < 0.09) target *= 0.92;
  if (p > 0.67) target += FINISH_KICK[i] * ((p - 0.67) / 0.33);
  if (horseEnergy[i] < 38) target -= (38 - horseEnergy[i]) * 0.035;

  const wave = Math.sin(p * 23 + PHASE[i]) * 0.42;
  return target + wave;
}

function updateRace(dt) {
  let leader = 0;
  let leaderDistance = -Infinity;

  for (let i = 0; i < LANE_COUNT; i++) {
    if (horsePositions[i] >= RACE_LENGTH) continue;

    const target = paceTarget(i);
    const acceleration = ACCEL[i];
    horseSpeeds[i] = ease(horseSpeeds[i], target, acceleration * 0.11, dt);

    // Small bounded variation: continuous movement rather than interval jumps.
    const jitter = Math.sin((performance.now() * 0.0028) + PHASE[i]) * 0.17;
    horseSpeeds[i] = clamp(horseSpeeds[i] + jitter * dt, 0, 39.5);

    horsePositions[i] = Math.min(
      RACE_LENGTH,
      horsePositions[i] + horseSpeeds[i] * dt
    );

    const drain = 0.74 + (horseSpeeds[i] / 38) * 0.30;
    horseEnergy[i] = Math.max(0, horseEnergy[i] - drain * dt);

    jumpCooldown[i] = Math.max(0, jumpCooldown[i] - dt);
    if (horsePositions[i] >= nextTerrainCue[i] && jumpCooldown[i] <= 0 && horsePositions[i] < RACE_LENGTH - 180) {
      triggerJump(i);
      nextTerrainCue[i] += 250 + ((i * 37 + Math.floor(horsePositions[i])) % 120);
    }

    if (horsePositions[i] > leaderDistance) {
      leaderDistance = horsePositions[i];
      leader = i;
    }

    if (horsePositions[i] >= RACE_LENGTH && winnerLane === -1) {
      winnerLane = i;
      finished = true;
      raceInProgress = false;
      stage.dataset.raceState = "finished";
      stateText.textContent = "FINISHED";
      resultText.textContent = `S0${i + 1} wins. This result is coming from the upstream-based race runtime, not the previous Lane 5 engine.`;
    }
  }

  const selectedDistance = horsePositions[SELECTED];
  const desiredCamera = Math.max(0, selectedDistance - 150);
  cameraVelocity = ease(cameraVelocity, (desiredCamera - cameraMeters) * 3.2, 5.5, dt);
  cameraMeters += cameraVelocity * dt;
  cameraMeters = Math.max(0, cameraMeters);

  leaderText.textContent = `S0${leader + 1}`;
  distanceText.textContent = Math.round(selectedDistance);
  speedText.textContent = horseSpeeds[SELECTED].toFixed(1);

  stage.dataset.leader = `S0${leader + 1}`;
  stage.dataset.selectedDistance = selectedDistance.toFixed(2);
  stage.dataset.selectedSpeed = horseSpeeds[SELECTED].toFixed(2);
}

function triggerJump(i) {
  const runner = runners[i];
  runner.classList.remove("jump");
  void runner.offsetWidth;
  runner.classList.add("jump");
  jumpCooldown[i] = 0.72;
  setTimeout(() => runner.classList.remove("jump"), 650);
}

function renderWorld(now) {
  const rect = track.getBoundingClientRect();
  const width = Math.max(320, rect.width);
  const mobile = width < 760;
  const anchorX = mobile ? width * 0.31 : width * 0.36;
  const pixelsPerMeter = mobile ? 2.0 : 2.55;

  for (let i = 0; i < LANE_COUNT; i++) {
    const relative = horsePositions[i] - cameraMeters;
    const x = anchorX + relative * pixelsPerMeter;
    const laneBias = i * 3.5;
    const scale = 0.91 + i * 0.026;
    runners[i].style.transform = `translate3d(${x + laneBias}px,-50%,0) scale(${scale})`;
  }

  const selectedSpeedRatio = clamp(horseSpeeds[SELECTED] / 36, 0, 1.1);
  const farShift = -cameraMeters * 0.16;
  const midShift = -cameraMeters * 0.44;
  const nearShift = -cameraMeters * 1.18;

  farLayer.style.transform = `translate3d(${farShift % 220}px,0,0)`;
  midLayer.style.transform = `translate3d(${midShift % 260}px,0,0)`;
  foregroundLayer.style.transform = `translate3d(${nearShift % 140}px,0,0) scaleY(${1 + selectedSpeedRatio * 0.05})`;

  track.style.backgroundPositionX = `${(-cameraMeters * 1.55) % 112}px, 0px`;

  const finishRelative = RACE_LENGTH - cameraMeters;
  const finishX = anchorX + finishRelative * pixelsPerMeter;
  if (finishX < width + 80) {
    finishLine.style.opacity = "1";
    finishLine.style.transform = `translate3d(${finishX}px,0,0)`;
  } else {
    finishLine.style.opacity = "0";
  }

  if (raceInProgress && selectedSpeedRatio > 0.7) {
    const shake = Math.sin(now * 0.055) * (selectedSpeedRatio - 0.7) * 2.1;
    stage.style.transform = `translate3d(0,${shake}px,0)`;
  } else {
    stage.style.transform = "translate3d(0,0,0)";
  }

  stage.dataset.cameraMeters = cameraMeters.toFixed(2);
}

function frame(now) {
  if (!raceInProgress) {
    renderWorld(now);
    startButton.disabled = false;
    return;
  }

  const dt = Math.min(0.05, Math.max(0, (now - lastStamp) / 1000));
  lastStamp = now;

  updateRace(dt);
  renderWorld(now);

  if (raceInProgress) {
    frameId = requestAnimationFrame(frame);
  } else {
    startButton.disabled = false;
  }
}

startButton.addEventListener("click", startGame);
restartButton.addEventListener("click", () => {
  resetRace();
  startButton.disabled = false;
});

window.addEventListener("resize", () => renderWorld(performance.now()));

resetRace();
