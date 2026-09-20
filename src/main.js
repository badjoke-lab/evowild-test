import * as THREE from "three";
import "./styles.css";

const canvas = document.querySelector("#game");
const stage = document.querySelector("#stage");
const isMobile = matchMedia("(pointer: coarse)").matches || innerWidth < 800;

const runtimeStatus = document.createElement("div");
runtimeStatus.className = "runtime-status";
runtimeStatus.textContent = "Starting 3D race renderer…";
stage.append(runtimeStatus);

function failRuntime(error) {
  const message = error instanceof Error ? error.message : String(error);
  runtimeStatus.textContent = `3D runtime error: ${message}`;
  runtimeStatus.classList.add("error");
  runtimeStatus.hidden = false;
  console.error(error);
}

let renderer;
try {
  renderer = new THREE.WebGLRenderer({
    canvas,
    antialias: !isMobile,
    powerPreference: "default",
    precision: "mediump"
  });
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setPixelRatio(isMobile ? 1 : Math.min(devicePixelRatio, 1.25));
  renderer.shadowMap.enabled = false;
} catch (error) {
  failRuntime(error);
  throw error;
}

canvas.addEventListener("webglcontextlost", (event) => {
  event.preventDefault();
  runtimeStatus.textContent = "WebGL context lost — restoring renderer…";
  runtimeStatus.classList.add("error");
  runtimeStatus.hidden = false;
});

canvas.addEventListener("webglcontextrestored", () => {
  runtimeStatus.textContent = "WebGL restored — restarting race…";
  runtimeStatus.classList.remove("error");
  runtimeStatus.hidden = false;
});

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x9bc6dc);
const raceFog = new THREE.Fog(0x9bc6dc, 75, 150);
scene.fog = raceFog;

const camera = new THREE.PerspectiveCamera(42, 16 / 9, 0.1, 240);
scene.add(new THREE.HemisphereLight(0xdceeff, 0x557050, 1.05));
const sun = new THREE.DirectionalLight(0xfff6dd, 1.25);
sun.position.set(30, 42, 12);
scene.add(sun);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(210, 160),
  new THREE.MeshStandardMaterial({ color: 0x6d8d62, roughness: 1 })
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -0.03;
scene.add(ground);

const curve = new THREE.CatmullRomCurve3(
  [
    [-34, -7], [-26, -18], [-5, -22], [17, -19], [33, -9],
    [36, 8], [23, 20], [1, 23], [-20, 18], [-35, 7]
  ].map(([x, z]) => new THREE.Vector3(x, 0, z)),
  true,
  "centripetal",
  0.4
);

function buildTrack() {
  const samples = 180;
  const half = 5.8;
  const vertices = [];
  const normals = [];
  const indices = [];

  for (let i = 0; i <= samples; i++) {
    const t = i / samples;
    const p = curve.getPointAt(t);
    const tangent = curve.getTangentAt(t).normalize();
    const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();

    for (const offset of [-half, half]) {
      const q = p.clone().addScaledVector(side, offset);
      vertices.push(q.x, 0.03, q.z);
      normals.push(0, 1, 0);
    }
  }

  for (let i = 0; i < samples; i++) {
    const a = i * 2;
    const b = a + 1;
    const c = a + 2;
    const d = a + 3;
    indices.push(a, c, b, b, c, d);
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
  geometry.setIndex(indices);

  scene.add(
    new THREE.Mesh(
      geometry,
      new THREE.MeshStandardMaterial({ color: 0xb98c5b, roughness: 1 })
    )
  );

  for (const offset of [-half, half]) {
    const points = [];
    for (let i = 0; i <= samples; i++) {
      const t = i / samples;
      const p = curve.getPointAt(t);
      const tangent = curve.getTangentAt(t).normalize();
      const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
      points.push(p.clone().addScaledVector(side, offset).add(new THREE.Vector3(0, 0.18, 0)));
    }
    scene.add(
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(points),
        new THREE.LineBasicMaterial({ color: 0xe6d6b8 })
      )
    );
  }
}
buildTrack();

const hillMaterial = new THREE.MeshStandardMaterial({ color: 0x738474, roughness: 1, flatShading: true });
function addHill(x, z, s) {
  const hill = new THREE.Mesh(new THREE.ConeGeometry(1, 1.5, 7), hillMaterial);
  const hillScale = s * (isMobile ? 0.42 : 1);
  hill.position.set(x, hillScale * 0.65, z);
  hill.scale.setScalar(hillScale);
  scene.add(hill);
}
addHill(-60, -34, 11);
addHill(58, -33, 13);
addHill(-62, 30, 9);

const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5a4432, roughness: 1 });
const leafMat = new THREE.MeshStandardMaterial({ color: 0x3f6542, roughness: 1, flatShading: true });
function addTree(x, z, s = 0.85) {
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 1.4, 5), trunkMat);
  trunk.position.set(x, 0.7, z);
  const leaves = new THREE.Mesh(new THREE.ConeGeometry(0.75, 2.2, 7), leafMat);
  leaves.position.set(x, 2, z);
  leaves.scale.setScalar(s);
  scene.add(trunk, leaves);
}
for (let i = 0; i < 22; i++) {
  const a = (i / 22) * Math.PI * 2;
  const r = 49 + (i % 3) * 2;
  addTree(Math.cos(a) * r, Math.sin(a) * r * 0.68, 0.74 + (i % 4) * 0.05);
}

const stand = new THREE.Mesh(
  new THREE.BoxGeometry(14, 3, 4.6),
  new THREE.MeshStandardMaterial({ color: 0x626a71, roughness: 1 })
);
stand.position.set(7, 1.5, -31);
scene.add(stand);

const palette = [
  0x78a9d7, 0xc96e62, 0x78a877, 0xd0ad59, 0x9a78b8, 0xdf8b4e,
  0x6caea5, 0xc47f9a, 0x8ba0cc, 0xd08c72, 0x72aec8, 0xa1b666,
  0xb47ac7, 0xcfa45a, 0x6a98bf, 0xc86f6b, 0x75a16c, 0xb18c65
];
const names = ["Aster","Brim","Cove","Dusk","Ember","Mica","Fenn","Gale","Hush","Iris","Jade","Kite","Lumen","Moss","Neri","Orrin","Pale","Quill"];
const morphCycle = ["S", "P", "E", "A"];
const morphLabel = { S: "Sprint", P: "Power", E: "Endurance", A: "Agility" };
const morphStats = {
  S: { cruise: 16.7, accel: 3.5, drain: 1.11 },
  P: { cruise: 15.8, accel: 3.1, drain: 1.02 },
  E: { cruise: 15.9, accel: 2.6, drain: 0.80 },
  A: { cruise: 16.2, accel: 3.7, drain: 0.95 }
};

const headsetMat = new THREE.MeshStandardMaterial({ color: 0x1b252d, roughness: 0.68, flatShading: true });
const headsetAccent = new THREE.MeshStandardMaterial({ color: 0x6bb1ff, roughness: 0.45, flatShading: true });
const makeMat = (color) => new THREE.MeshStandardMaterial({ color, roughness: 0.92, flatShading: true });

function addHeadset(group, x, y, scale = 1) {
  const band = new THREE.Mesh(new THREE.TorusGeometry(0.40 * scale, 0.038 * scale, 5, 16, Math.PI * 1.3), headsetMat);
  band.rotation.y = Math.PI / 2;
  band.rotation.z = 0.24;
  band.position.set(x, y, 0);
  group.add(band);

  for (const z of [-0.35, 0.35]) {
    const pod = new THREE.Mesh(new THREE.BoxGeometry(0.11 * scale, 0.19 * scale, 0.08 * scale), headsetAccent);
    pod.position.set(x + 0.01, y - 0.02, z * scale);
    group.add(pod);
  }
}

function addMarkings(group, color, index) {
  const mark = new THREE.MeshStandardMaterial({ color, roughness: 0.85, flatShading: true });
  for (const z of [-0.66, 0.66]) {
    const stripe = new THREE.Mesh(new THREE.BoxGeometry(0.62, 0.16, 0.05), mark);
    stripe.position.set(index % 2 ? 0.15 : -0.15, 0.15, z);
    stripe.rotation.z = index % 2 ? 0.35 : -0.35;
    group.add(stripe);
  }
}

function buildMorph(index, morph) {
  const group = new THREE.Group();
  const baseColor = palette[index];
  const body = makeMat(baseColor);
  const accent = makeMat(new THREE.Color(baseColor).offsetHSL((index % 3 - 1) * 0.025, 0.04, 0.04));
  const legs = [];

  const addLegs = (xs, zs, radius, length, y) => {
    for (const x of xs) {
      for (const z of zs) {
        const leg = new THREE.Mesh(new THREE.CylinderGeometry(radius * 0.8, radius, length, 5), body);
        leg.position.set(x, y, z);
        group.add(leg);
        legs.push(leg);
      }
    }
  };

  if (morph === "S") {
    const torso = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), body);
    torso.scale.set(1.75, 0.46, 0.44);
    group.add(torso);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.22, 1.12, 6), accent);
    neck.rotation.z = -1.15;
    neck.position.set(1.10, 0.34, 0);
    group.add(neck);
    const head = new THREE.Mesh(new THREE.IcosahedronGeometry(0.37, 1), body);
    head.scale.set(1.22, 0.63, 0.62);
    head.position.set(1.65, 0.63, 0);
    group.add(head);
    for (const z of [-0.16, 0.16]) {
      const horn = new THREE.Mesh(new THREE.ConeGeometry(0.055, 0.78, 5), accent);
      horn.position.set(1.65, 1.06, z);
      horn.rotation.z = -0.75;
      group.add(horn);
    }
    addLegs([-0.72, 0.68], [-0.27, 0.27], 0.085, 1.40, -0.92);
    const tail = new THREE.Mesh(new THREE.ConeGeometry(0.07, 1.55, 5), accent);
    tail.rotation.z = 1.43;
    tail.position.set(-1.72, 0.04, 0);
    group.add(tail);
    addHeadset(group, 1.63, 0.63, 0.84);
  } else if (morph === "P") {
    const torso = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), body);
    torso.scale.set(1.45, 0.96, 0.98);
    torso.position.y = 0.02;
    group.add(torso);
    const shoulder = new THREE.Mesh(new THREE.IcosahedronGeometry(0.68, 0), accent);
    shoulder.scale.set(1.18, 1.05, 1.05);
    shoulder.position.set(0.62, 0.20, 0);
    group.add(shoulder);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.30, 0.44, 0.78, 6), accent);
    neck.rotation.z = -0.88;
    neck.position.set(0.98, 0.25, 0);
    group.add(neck);
    const head = new THREE.Mesh(new THREE.IcosahedronGeometry(0.50, 1), body);
    head.scale.set(1.06, 0.90, 0.92);
    head.position.set(1.42, 0.46, 0);
    group.add(head);
    for (const z of [-0.24, 0.24]) {
      const horn = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.48, 5), accent);
      horn.position.set(1.43, 0.92, z);
      horn.rotation.z = -0.15;
      group.add(horn);
    }
    addLegs([-0.60, 0.54], [-0.38, 0.38], 0.19, 0.72, -0.78);
    const tail = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.24, 0.78, 6), accent);
    tail.rotation.z = 1.12;
    tail.position.set(-1.35, 0, 0);
    group.add(tail);
    addHeadset(group, 1.40, 0.46, 1.03);
  } else if (morph === "E") {
    const torso = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), body);
    torso.scale.set(1.48, 0.42, 0.42);
    torso.position.y = 0.08;
    group.add(torso);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.21, 1.22, 6), accent);
    neck.rotation.z = -1.18;
    neck.position.set(1.08, 0.48, 0);
    group.add(neck);
    const head = new THREE.Mesh(new THREE.IcosahedronGeometry(0.35, 1), body);
    head.scale.set(1.18, 0.62, 0.62);
    head.position.set(1.60, 0.84, 0);
    group.add(head);
    for (const z of [-0.14, 0.14]) {
      const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.05, 0.80, 5), accent);
      stem.rotation.z = -0.52;
      stem.position.set(1.54, 1.20, z);
      group.add(stem);
    }
    addLegs([-0.65, 0.62], [-0.23, 0.23], 0.075, 1.62, -1.03);
    const tail = new THREE.Mesh(new THREE.ConeGeometry(0.06, 1.52, 5), accent);
    tail.rotation.z = 1.44;
    tail.position.set(-1.56, 0.05, 0);
    group.add(tail);
    addHeadset(group, 1.58, 0.84, 0.80);
  } else {
    const torso = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), body);
    torso.scale.set(1.12, 0.54, 0.66);
    torso.position.y = -0.14;
    group.add(torso);
    const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.26, 0.62, 6), accent);
    neck.rotation.z = -0.92;
    neck.position.set(0.78, 0.11, 0);
    group.add(neck);
    const head = new THREE.Mesh(new THREE.IcosahedronGeometry(0.39, 1), body);
    head.scale.set(1.14, 0.72, 0.80);
    head.position.set(1.18, 0.32, 0);
    group.add(head);
    for (let j = 0; j < 5; j++) {
      const fin = new THREE.Mesh(new THREE.ConeGeometry(0.075, 0.48 + (j % 2) * 0.10, 5), accent);
      fin.position.set(-0.38 + j * 0.25, 0.53, 0);
      fin.rotation.z = -0.12;
      group.add(fin);
    }
    addLegs([-0.48, 0.44], [-0.34, 0.34], 0.11, 0.62, -0.62);
    const tailStem = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.20, 0.78, 6), accent);
    tailStem.rotation.z = 1.16;
    tailStem.position.set(-1.02, -0.02, 0);
    group.add(tailStem);
    const blade = new THREE.Mesh(new THREE.ConeGeometry(0.42, 1.35, 5), accent);
    blade.rotation.z = 1.23;
    blade.position.set(-1.72, 0.03, 0);
    blade.scale.z = 1.25;
    group.add(blade);
    addHeadset(group, 1.17, 0.32, 0.88);
  }

  addMarkings(group, morph === "P" ? 0x171b22 : 0xe9eef4, index);
  group.userData.legs = legs;
  return group;
}

const racers = [];
const selectedId = 6;
const raceMeters = 1800;

for (let i = 0; i < 18; i++) {
  const morph = i === 5 ? "A" : morphCycle[i % 4];
  const obj = buildMorph(i, morph);
  obj.scale.setScalar(isMobile ? 1.02 : 0.88);
  scene.add(obj);

  const stats = morphStats[morph];
  racers.push({
    id: i + 1,
    name: names[i],
    morph,
    obj,
    distance: Math.max(0, (17 - i) * 1.1),
    lane: i % 3,
    laneF: i % 3,
    cruise: stats.cruise + (i % 5) * 0.18,
    accel: stats.accel,
    drain: stats.drain,
    stamina: 100,
    speed: 0,
    decision: "START",
    command: "BUILD SPEED",
    cooldown: 0,
    color: "#" + palette[i].toString(16).padStart(6, "0")
  });
}

const selected = racers[selectedId - 1];
const ring = new THREE.Mesh(
  new THREE.RingGeometry(1.15, 1.28, 36),
  new THREE.MeshBasicMaterial({ color: 0x6bb1ff, side: THREE.DoubleSide, transparent: true, opacity: 0.9 })
);
ring.rotation.x = -Math.PI / 2;
scene.add(ring);

const tacticalMarkers = racers.map((r) => {
  const marker = new THREE.Mesh(
    new THREE.CircleGeometry(r.id === selectedId ? 1.25 : 0.88, 18),
    new THREE.MeshBasicMaterial({
      color: r.id === selectedId ? 0xffffff : palette[r.id - 1],
      transparent: true,
      opacity: r.id === selectedId ? 1 : 0.9,
      depthTest: false,
      fog: false
    })
  );
  marker.rotation.x = -Math.PI / 2;
  marker.visible = false;
  marker.renderOrder = 10;
  scene.add(marker);
  return marker;
});

let elapsed = 0;
let last = performance.now();
let paused = false;
let view = "race";

const ranks = () => [...racers].sort((a, b) => b.distance - a.distance);
const rankOf = (r) => ranks().findIndex((x) => x === r) + 1;

function gapAhead(r, lane = Math.round(r.laneF)) {
  let gap = 999;
  for (const other of racers) {
    if (other === r || Math.round(other.laneF) !== lane) continue;
    const d = other.distance - r.distance;
    if (d > 0 && d < gap) gap = d;
  }
  return gap;
}

function laneFree(r, lane) {
  return racers.every((other) => other === r || Math.round(other.laneF) !== lane || Math.abs(other.distance - r.distance) > 6.5);
}

function chooseLane(r) {
  const options = [0, 1, 2].filter((lane) => lane !== Math.round(r.laneF) && laneFree(r, lane));
  if (!options.length) return null;
  options.sort((a, b) => gapAhead(r, b) - gapAhead(r, a));
  return options[0];
}

function phase(r) {
  const p = r.distance / raceMeters;
  if (p < 0.08) return "START";
  if (p < 0.55) return "MID";
  if (p < 0.80) return "BUILD";
  return "FINAL";
}

function morphTarget(r) {
  const p = r.distance / raceMeters;
  if (r.morph === "S") return r.cruise * (p < 0.25 ? 1.05 : p < 0.75 ? 1.005 : 1.02);
  if (r.morph === "P") return r.cruise * (p < 0.15 ? 1.03 : p < 0.70 ? 1.01 : r.stamina > 30 ? 1.04 : 0.93);
  if (r.morph === "E") return r.cruise * (p < 0.52 ? 0.98 : p < 0.82 ? 1.02 : 1.08);
  return r.cruise * (p < 0.20 ? 1.00 : p < 0.70 ? 1.02 : 1.07);
}

function update(dt) {
  if (paused) return;
  elapsed += dt;
  const sec = dt / 1000;

  for (const r of racers) {
    r.cooldown = Math.max(0, r.cooldown - dt);
    const currentPhase = phase(r);
    const gap = gapAhead(r);
    const position = rankOf(r);
    let target = morphTarget(r);

    if (r.stamina < 18) {
      target *= 0.88;
      r.decision = "PRESERVE";
      r.command = "EASE";
    } else if (gap < 4.2 && r.cooldown <= 0) {
      const nextLane = chooseLane(r);
      if (nextLane !== null) {
        r.lane = nextLane;
        r.cooldown = 900;
        r.decision = "OVERTAKE";
        r.command = nextLane < r.laneF ? "MOVE INSIDE" : "MOVE OUTSIDE";
        target *= 1.025;
      } else {
        target *= 0.90;
        r.decision = "BLOCKED";
        r.command = "WAIT";
      }
    } else if (currentPhase === "FINAL") {
      target *= 1.04;
      r.decision = "ATTACK";
      r.command = "PUSH";
    } else if (position > 12 && currentPhase !== "START") {
      target *= 1.012;
      r.decision = "ADVANCE";
      r.command = "PUSH";
    } else {
      r.decision = currentPhase === "START" ? "START" : "HOLD";
      r.command = currentPhase === "START" ? "BUILD SPEED" : "MAINTAIN";
    }

    if (gap < 2.5) target *= Math.max(0.72, gap / 2.5);
    target *= 0.76 + 0.24 * (r.stamina / 100);
    target += Math.sin(elapsed * 0.0011 + r.id * 1.57) * 0.20;

    const diff = target - r.speed;
    const maxStep = (diff > 0 ? r.accel : r.accel * 1.5) * sec;
    r.speed += THREE.MathUtils.clamp(diff, -maxStep, maxStep);
    r.distance += Math.max(0, r.speed) * sec;

    const load = Math.max(0, r.speed / r.cruise - 0.96);
    r.stamina = Math.max(0, r.stamina - (0.018 + 0.038 * load * load) * r.drain * dt / 1000);
    r.laneF = THREE.MathUtils.lerp(r.laneF, r.lane, Math.min(1, dt * 0.0032));

    const t = (r.distance / raceMeters) % 1;
    const p = curve.getPointAt(t);
    const tangent = curve.getTangentAt(t).normalize();
    const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    const targetPos = p.clone().addScaledVector(side, (r.laneF - 1) * 1.70);
    targetPos.y = 0.98 + Math.abs(Math.sin(elapsed * 0.014 + r.id * 0.8)) * 0.07;
    r.obj.position.lerp(targetPos, 0.44);

    // Model forward axis is +X.
    r.obj.rotation.y = Math.atan2(-tangent.z, tangent.x);

    const stride = Math.sin(elapsed * 0.020 + r.id * 0.73) * 0.44;
    r.obj.userData.legs.forEach((leg, index) => {
      leg.rotation.z = (index % 2 ? 1 : -1) * stride;
    });
  }

  ring.position.set(selected.obj.position.x, 0.08, selected.obj.position.z);
  tacticalMarkers.forEach((marker, index) => {
    const r = racers[index];
    marker.position.set(r.obj.position.x, 2.8, r.obj.position.z);
  });
}

function setCamera() {
  const selectedPos = selected.obj.position.clone();
  const t = (selected.distance / raceMeters) % 1;
  const tangent = curve.getTangentAt(t).normalize();
  const side = new THREE.Vector3(-tangent.z, 0, tangent.x);

  const tactical = view === "tactical";
  scene.fog = tactical ? null : raceFog;
  racers.forEach((r) => { r.obj.visible = !tactical; });
  ring.visible = !tactical;
  tacticalMarkers.forEach((marker) => { marker.visible = tactical; });

  if (view === "follow") {
    camera.up.set(0, 1, 0);
    const followBack = isMobile ? -9.5 : -8;
    const followSide = isMobile ? 2.8 : 2.2;
    const followHeight = isMobile ? 3.7 : 2.8;
    camera.position.lerp(
      selectedPos.clone().addScaledVector(tangent, followBack).addScaledVector(side, followSide).add(new THREE.Vector3(0, followHeight, 0)),
      0.13
    );
    camera.lookAt(selectedPos.clone().addScaledVector(tangent, 2.8).add(new THREE.Vector3(0, 0.45, 0)));
  } else if (view === "tactical") {
    camera.up.set(0, 0, -1);
    const tacticalHeight = isMobile ? 112 : 78;
    camera.position.lerp(new THREE.Vector3(0, tacticalHeight, 0.01), 0.14);
    camera.lookAt(0, 0, 0);
  } else {
    camera.up.set(0, 1, 0);
    const pack = ranks().slice(0, 10);
    const center = new THREE.Vector3();
    pack.forEach((r) => center.add(r.obj.position));
    center.multiplyScalar(1 / pack.length);

    const leader = pack[0];
    const lt = (leader.distance / raceMeters) % 1;
    const leaderTangent = curve.getTangentAt(lt).normalize();
    const leaderSide = new THREE.Vector3(-leaderTangent.z, 0, leaderTangent.x);

    const raceBack = isMobile ? -4.5 : -14;
    const raceSide = isMobile ? 15.5 : 11;
    const raceHeight = isMobile ? 7.4 : 8.5;
    camera.position.lerp(
      center.clone().addScaledVector(leaderTangent, raceBack).addScaledVector(leaderSide, raceSide).add(new THREE.Vector3(0, raceHeight, 0)),
      0.055
    );
    camera.lookAt(center.clone().add(new THREE.Vector3(0, 0.65, 0)));
  }
}

function updateHud() {
  const position = rankOf(selected);
  const gapValue = gapAhead(selected);
  const currentPhase = phase(selected);
  const sec = elapsed / 1000;

  document.querySelector("#position").textContent = `${position} / 18`;
  document.querySelector("#speed").textContent = Math.round(selected.speed);
  document.querySelector("#stamina").textContent = Math.round(selected.stamina);
  document.querySelector("#morph").textContent = `${selected.morph} / ${morphLabel[selected.morph].toUpperCase()}`;
  document.querySelector("#decision").textContent = `${selected.decision} / ${selected.command}`;
  document.querySelector("#morphName").textContent = `${selected.morph} — ${morphLabel[selected.morph]}`;
  document.querySelector("#lane").textContent = String(Math.round(selected.laneF) + 1);
  document.querySelector("#gap").textContent = gapValue < 900 ? `${gapValue.toFixed(1)} m` : "—";
  document.querySelector("#phase").textContent = currentPhase;
  document.querySelector("#clock").textContent =
    `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(Math.floor(sec % 60)).padStart(2, "0")}.${String(Math.floor((sec % 1) * 100)).padStart(2, "0")}`;

  document.querySelector("#ranking").innerHTML = ranks().map((r, index) => `
    <div class="rank-row ${r.id === selectedId ? "selected" : ""}">
      <b>${index + 1}</b>
      <span><i class="dot" style="background:${r.color}"></i>#${String(r.id).padStart(2, "0")} ${r.name}<span class="badge">${r.morph}</span></span>
      <span>${r.speed.toFixed(1)}</span>
    </div>
  `).join("");
}

function drawMiniMap() {
  const mini = document.querySelector("#mini");
  const ctx = mini.getContext("2d");
  const points = curve.getSpacedPoints(100);
  const scale = 2.25;
  const ox = mini.width / 2;
  const oy = mini.height / 2;

  ctx.clearRect(0, 0, mini.width, mini.height);
  ctx.fillStyle = "#0b1118";
  ctx.fillRect(0, 0, mini.width, mini.height);

  ctx.strokeStyle = "#c9aa7c";
  ctx.lineWidth = 6;
  ctx.beginPath();
  points.forEach((p, index) => {
    const x = ox + p.x * scale;
    const y = oy + p.z * scale;
    index ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
  });
  ctx.closePath();
  ctx.stroke();

  for (const r of racers) {
    const p = curve.getPointAt((r.distance / raceMeters) % 1);
    ctx.fillStyle = r.color;
    ctx.beginPath();
    ctx.arc(ox + p.x * scale, oy + p.z * scale, r.id === selectedId ? 4 : 2.5, 0, Math.PI * 2);
    ctx.fill();
    if (r.id === selectedId) {
      ctx.strokeStyle = "#fff";
      ctx.lineWidth = 1.2;
      ctx.stroke();
    }
  }
}

function resize() {
  const rect = stage.getBoundingClientRect();
  const width = Math.max(1, Math.floor(rect.width));
  const height = Math.max(1, Math.floor(rect.height));
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.fov = isMobile ? (view === "tactical" ? 50 : view === "follow" ? 54 : 50) : 42;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

function resetRace() {
  racers.forEach((r, i) => {
    r.distance = Math.max(0, (17 - i) * 1.1);
    r.lane = i % 3;
    r.laneF = i % 3;
    r.stamina = 100;
    r.speed = 0;
    r.cooldown = 0;
    r.decision = "START";
    r.command = "BUILD SPEED";

    const t = (r.distance / raceMeters) % 1;
    const p = curve.getPointAt(t);
    const tangent = curve.getTangentAt(t).normalize();
    const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    r.obj.position.copy(p.clone().addScaledVector(side, (r.laneF - 1) * 1.70));
    r.obj.position.y = 0.98;
    r.obj.rotation.y = Math.atan2(-tangent.z, tangent.x);
  });
  elapsed = 0;
}
resetRace();

// Draw a valid scene immediately instead of waiting for the first animation tick.
camera.position.set(-12, 12, 28);
camera.up.set(0, 1, 0);
camera.lookAt(0, 0.8, 0);
renderer.render(scene, camera);
updateHud();
drawMiniMap();

let renderedFrames = 0;
function frame(now) {
  try {
    const dt = Math.min(45, Math.max(0, now - last));
    last = now;
    update(dt);
    setCamera();
    renderer.render(scene, camera);
    updateHud();
    drawMiniMap();

    renderedFrames += 1;
    if (renderedFrames === 2) {
      runtimeStatus.hidden = true;
    }
  } catch (error) {
    paused = true;
    failRuntime(error);
    renderer.setAnimationLoop(null);
  }
}
renderer.setAnimationLoop(frame);

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    view = button.dataset.view;
    resize();
    document.querySelector("#viewLabel").textContent =
      view === "race" ? "RACE VIEW" : view === "follow" ? "FOLLOW VIEW" : "TACTICAL VIEW";
    document.querySelectorAll("[data-view]").forEach((b) => b.classList.toggle("active", b === button));
  });
});

document.querySelector("#pause").addEventListener("click", (event) => {
  paused = !paused;
  event.currentTarget.textContent = paused ? "Resume" : "Pause";
});

document.querySelector("#reset").addEventListener("click", resetRace);
