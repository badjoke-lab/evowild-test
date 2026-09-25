import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { MTLLoader } from "three/addons/loaders/MTLLoader.js";
import { CREATURE_3D_PROFILES, cloneCreature3D, createStaticCreatureInstanceBatch, fitCreature3D, loadCreature3D } from "./creature3d.js";
import "./styles.css";

const canvas = document.querySelector("#game");
const stage = document.querySelector("#stage");
const isMobile = matchMedia("(pointer: coarse)").matches || innerWidth < 800;
const query = new URLSearchParams(location.search);
const preview3d = location.pathname.includes("/preview-3d");
const sf3dBenchCount = Math.min(18, Math.max(0, Number.parseInt(query.get("sf3dBench") || "0", 10) || 0));
const sf3dBenchSide = query.get("sf3dSide") === "front" ? "front" : "double";
const sf3dBenchMode = query.get("sf3dMode") === "instance" ? "instance" : "clone";
const sf3dRaceLodBench = query.get("sf3dRaceLodBench") === "1";
const sf3dRaceStress = query.get("sf3dRaceStress") === "1";
const sf3dRaceStressMode = query.get("sf3dRaceStressMode") === "instance" ? "instance" : "clone";
const sf3dMaterialMode = query.get("sf3dMaterialMode") === "lite" ? "lite" : "full";
const hunyuanRacePack =
  query.get("hunyuanRacePack") === "1" ||
  (preview3d && !query.has("hunyuanRacePack"));
const hunyuanRacePackSide = query.get("hunyuanRacePackSide") === "double" ? "double" : "front";
const requestedHunyuanGait = query.get("hunyuanGait");
const hunyuanGaitVersion = ["v1", "v2", "v21", "v3", "v3hybrid"].includes(requestedHunyuanGait)
  ? requestedHunyuanGait
  : "v3hybrid";
const previewRenderScale = preview3d ? (isMobile ? 0.5 : 0.75) : 1;
const renderScale = Math.min(
  1,
  Math.max(0.5, Number.parseFloat(query.get("renderScale") || String(previewRenderScale)) || previewRenderScale)
);
const modelYawDegrees = Number.parseFloat(query.get("modelYaw") || "0") || 0;
const modelYawRadians = THREE.MathUtils.degToRad(modelYawDegrees);
let sf3dBenchGroup = null;
let sf3dBenchStartedAt = 0;
let sf3dBenchFrameTimes = [];
let sf3dBenchReady = false;
let sf3dTrianglesPerInstance = 0;
let sf3dRaceLodBenchStartedAt = 0;
let sf3dRaceLodBenchFrameTimes = [];
let sf3dRaceLodBenchReady = false;
let sf3dRaceStressStartedAt = 0;
let sf3dRaceStressFrames = [];
let sf3dRaceStressReady = false;
let sf3dRaceStressBatches = null;
let sf3dRaceStressConfig = null;
let sf3dRaceStressLevelCounts = [];
let hunyuanRacePackBatches = null;
let hunyuanRacePackCounts = [0, 0, 0];
let hunyuanRacePackRiggedSelected = null;
let hunyuanRacePackRiggedFar = [];
let hunyuanRacePackAnimated = false;
let hunyuanRacePackSelectedAction = null;
const hunyuanStrideMetersPerCycle = THREE.MathUtils.clamp(
  Number.parseFloat(query.get("hunyuanStrideMeters") || "5.6") || 5.6,
  2.5,
  9.0
);
let sf3dLabMixer = null;
const sf3dRaceMixers = [];

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
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  const basePixelRatio = isMobile ? Math.min(devicePixelRatio, 1.5) : Math.min(devicePixelRatio, 1.25);
  renderer.setPixelRatio(basePixelRatio * renderScale);
  stage.dataset.renderScale = String(renderScale);
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
scene.add(new THREE.HemisphereLight(0xddeeff, 0x26332e, 1.18));
const sun = new THREE.DirectionalLight(0xfff0d2, 1.55);
sun.position.set(30, 42, 12);
scene.add(sun);
const rim = new THREE.DirectionalLight(0x79bfff, 0.55);
rim.position.set(-24, 18, -28);
scene.add(rim);

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

const raceEnvironment = scene.children.filter((obj) => !obj.isLight);

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

const headsetMat = new THREE.MeshStandardMaterial({ color: 0x111820, roughness: 0.72, flatShading: true });
const headsetAccent = new THREE.MeshStandardMaterial({ color: 0x42c7ff, emissive: 0x123547, emissiveIntensity: 0.65, roughness: 0.4, flatShading: true });
const eyeMat = new THREE.MeshBasicMaterial({ color: 0x7ee8ff });
const makeMat = (color) => new THREE.MeshStandardMaterial({ color, roughness: 0.58, metalness: 0.04, flatShading: false });

function profileGeometry(sections, radialSegments = 12) {
  const vertices = [];
  const indices = [];
  const ring = radialSegments;

  for (const [x, cy, ry, rz] of sections) {
    for (let j = 0; j < ring; j++) {
      const angle = (j / ring) * Math.PI * 2;
      vertices.push(x, cy + Math.cos(angle) * ry, Math.sin(angle) * rz);
    }
  }

  for (let i = 0; i < sections.length - 1; i++) {
    for (let j = 0; j < ring; j++) {
      const n = (j + 1) % ring;
      const a0 = i * ring + j;
      const a1 = i * ring + n;
      const b0 = (i + 1) * ring + j;
      const b1 = (i + 1) * ring + n;
      indices.push(a0, b0, a1, a1, b0, b1);
    }
  }

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();
  return geometry;
}

function addProfile(group, sections, material, radialSegments = 12) {
  const mesh = new THREE.Mesh(profileGeometry(sections, radialSegments), material);
  group.add(mesh);
  return mesh;
}

function addSegment(group, start, end, rStart, rEnd, material, radial = 8) {
  const a = new THREE.Vector3(...start);
  const b = new THREE.Vector3(...end);
  const dir = b.clone().sub(a);
  const length = dir.length();
  const mesh = new THREE.Mesh(new THREE.CylinderGeometry(rEnd, rStart, length, radial, 2, false), material);
  mesh.position.copy(a.clone().add(b).multiplyScalar(0.5));
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
  group.add(mesh);
  return mesh;
}

function addCueBand(group, x, y, scale = 1) {
  const band = new THREE.Mesh(new THREE.BoxGeometry(0.30 * scale, 0.08 * scale, 0.66 * scale), headsetMat);
  band.position.set(x - 0.05 * scale, y + 0.08 * scale, 0);
  band.rotation.z = -0.10;
  group.add(band);

  for (const z of [-0.36, 0.36]) {
    const pod = new THREE.Mesh(new THREE.BoxGeometry(0.16 * scale, 0.18 * scale, 0.10 * scale), headsetAccent);
    pod.position.set(x + 0.02 * scale, y + 0.02 * scale, z * scale);
    group.add(pod);
  }
}

function addEyes(group, x, y, z = 0.26, scale = 1) {
  for (const side of [-1, 1]) {
    const eye = new THREE.Mesh(new THREE.SphereGeometry(0.055 * scale, 6, 5), eyeMat);
    eye.position.set(x, y, side * z * scale);
    group.add(eye);
  }
}

function addLeg(group, hipX, hipY, hipZ, upper, lower, thickness, material, forward = 1) {
  const knee = [hipX + 0.12 * forward, hipY - upper * 0.52, hipZ];
  const ankle = [hipX - 0.10 * forward, hipY - upper * 0.52 - lower * 0.46, hipZ];
  const hoof = [hipX + 0.12 * forward, hipY - upper * 0.52 - lower * 0.56, hipZ];
  const upperMesh = addSegment(group, [hipX, hipY, hipZ], knee, thickness, thickness * 0.78, material, 5);
  const lowerMesh = addSegment(group, knee, ankle, thickness * 0.78, thickness * 0.50, material, 5);
  addSegment(group, ankle, hoof, thickness * 0.58, thickness * 0.42, material, 5);
  return [upperMesh, lowerMesh];
}

function addHorn(group, start, end, radius, material) {
  addSegment(group, start, end, radius, 0.018, material, 5);
}

function addSpeciesHead(group, headY, neckRootY, scale, body, accent) {
  addProfile(group, [
    [0.72, neckRootY, 0.28 * scale, 0.30 * scale],
    [1.02, (neckRootY + headY) * 0.52, 0.24 * scale, 0.27 * scale],
    [1.28, headY - 0.04, 0.20 * scale, 0.24 * scale]
  ], accent, 10);

  addProfile(group, [
    [1.18, headY, 0.22 * scale, 0.26 * scale],
    [1.50, headY + 0.01, 0.24 * scale, 0.28 * scale],
    [1.82, headY - 0.04, 0.18 * scale, 0.22 * scale],
    [2.10, headY - 0.10, 0.09 * scale, 0.14 * scale]
  ], body, 10);

  addProfile(group, [
    [1.45, headY - 0.16, 0.08 * scale, 0.22 * scale],
    [1.78, headY - 0.18, 0.08 * scale, 0.18 * scale],
    [2.06, headY - 0.17, 0.04 * scale, 0.10 * scale]
  ], accent, 8);

  for (const z of [-0.11 * scale, 0.11 * scale]) {
    addHorn(
      group,
      [1.48, headY + 0.24 * scale, z],
      [0.56, headY + 1.02 * scale, z * 1.12],
      0.06 * scale,
      accent
    );
  }

  addCueBand(group, 1.60, headY + 0.01, 0.78 * scale);
  addEyes(group, 1.82, headY + 0.01, 0.20, 0.86 * scale);
}

function buildMorph(index, morph, forcedColor = null) {
  const group = new THREE.Group();
  const baseColor = forcedColor ?? palette[index];
  const body = makeMat(baseColor);
  const darker = new THREE.Color(baseColor).offsetHSL(0, 0.05, -0.15);
  const accent = makeMat(darker);
  const legs = [];

  const legPair = (hipXs, hipY, hipZ, upper, lower, thickness) => {
    hipXs.forEach((x, xi) => {
      for (const z of [-hipZ, hipZ]) {
        legs.push(...addLeg(group, x, hipY, z, upper, lower, thickness, body, xi ? -1 : 1));
      }
    });
  };

  if (morph === "S") {
    addProfile(group, [
      [-1.82, 0.24, 0.16, 0.20],
      [-1.35, 0.24, 0.34, 0.40],
      [-0.72, 0.24, 0.39, 0.45],
      [-0.12, 0.25, 0.34, 0.40],
      [0.50, 0.30, 0.40, 0.44],
      [0.86, 0.37, 0.25, 0.30]
    ], body);
    addProfile(group, [
      [-1.30, 0.50, 0.13, 0.30],
      [-0.42, 0.51, 0.15, 0.34],
      [0.48, 0.55, 0.16, 0.34]
    ], accent, 10);
    legPair([-0.78, 0.58], -0.04, 0.27, 0.98, 0.90, 0.095);
    addSegment(group, [-1.62, 0.30, 0], [-2.38, 0.55, 0], 0.09, 0.022, accent, 5);
    addSpeciesHead(group, 0.86, 0.36, 0.92, body, accent);
  } else if (morph === "P") {
    addProfile(group, [
      [-1.58, 0.18, 0.30, 0.38],
      [-1.18, 0.22, 0.54, 0.62],
      [-0.52, 0.24, 0.62, 0.70],
      [0.12, 0.28, 0.64, 0.72],
      [0.66, 0.38, 0.70, 0.72],
      [0.94, 0.44, 0.40, 0.46]
    ], body);
    addProfile(group, [
      [-0.62, 0.66, 0.15, 0.45],
      [0.06, 0.72, 0.18, 0.52],
      [0.62, 0.76, 0.22, 0.50]
    ], accent, 10);
    legPair([-0.66, 0.54], -0.20, 0.36, 0.68, 0.58, 0.16);
    addSegment(group, [-1.42, 0.28, 0], [-1.94, 0.39, 0], 0.15, 0.055, accent, 6);
    addSpeciesHead(group, 0.82, 0.42, 0.98, body, accent);
  } else if (morph === "E") {
    addProfile(group, [
      [-1.92, 0.43, 0.14, 0.18],
      [-1.45, 0.43, 0.27, 0.31],
      [-0.78, 0.44, 0.32, 0.36],
      [-0.10, 0.46, 0.29, 0.34],
      [0.54, 0.51, 0.31, 0.35],
      [0.90, 0.60, 0.21, 0.25]
    ], body);
    addProfile(group, [
      [-1.34, 0.64, 0.10, 0.24],
      [-0.48, 0.66, 0.11, 0.27],
      [0.46, 0.70, 0.12, 0.27]
    ], accent, 10);
    legPair([-0.78, 0.62], 0.14, 0.23, 1.12, 1.02, 0.078);
    addSegment(group, [-1.72, 0.48, 0], [-2.44, 0.68, 0], 0.065, 0.015, accent, 5);
    addSpeciesHead(group, 1.22, 0.58, 0.86, body, accent);
  } else {
    addProfile(group, [
      [-1.34, 0.02, 0.25, 0.34],
      [-1.04, 0.04, 0.42, 0.50],
      [-0.46, 0.07, 0.48, 0.57],
      [0.12, 0.10, 0.44, 0.54],
      [0.60, 0.17, 0.46, 0.52],
      [0.86, 0.25, 0.30, 0.35]
    ], body);
    addProfile(group, [
      [-0.76, 0.37, 0.11, 0.34],
      [-0.15, 0.42, 0.12, 0.40],
      [0.48, 0.48, 0.14, 0.38]
    ], accent, 10);
    for (let j = 0; j < 3; j++) {
      addHorn(group, [-0.35 + j * 0.28, 0.48, 0], [-0.42 + j * 0.28, 0.82 + j * 0.04, 0], 0.045, accent);
    }
    legPair([-0.55, 0.46], -0.27, 0.32, 0.54, 0.48, 0.11);
    addSegment(group, [-1.14, 0.12, 0], [-1.62, 0.25, 0], 0.14, 0.09, accent, 6);
    const blade = new THREE.Mesh(new THREE.ConeGeometry(0.38, 1.30, 5), accent);
    blade.rotation.z = 1.20;
    blade.position.set(-1.92, 0.34, 0);
    blade.scale.z = 1.12;
    group.add(blade);
    addSpeciesHead(group, 0.64, 0.24, 0.90, body, accent);
  }

  group.userData.legs = legs;
  return group;
}

const racers = [];
const selectedId = 6;
const raceMeters = 1800;
const laneCount = 6;
const laneSpacing = 1.55;
const laneOffset = (lane) => (lane - (laneCount - 1) / 2) * laneSpacing;

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
    lane: i % laneCount,
    laneF: i % laneCount,
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

const labGroup = new THREE.Group();
const labFloor = new THREE.Mesh(
  new THREE.PlaneGeometry(18, 8),
  new THREE.MeshStandardMaterial({ color: 0x151b23, roughness: 1 })
);
labFloor.rotation.x = -Math.PI / 2;
labFloor.position.y = 0.02;
labFloor.visible = false;
scene.add(labFloor);

const labSpecs = [
  ["S", 0x587aa3],
  ["P", 0x8f4a45],
  ["E", 0xa39578],
  ["A", 0x326f82]
];
const labObjects = new Map();
for (let i = 0; i < labSpecs.length; i++) {
  const [morph, color] = labSpecs[i];
  const obj = buildMorph(i, morph, color);
  obj.position.set(0, 1.12, 0);
  obj.scale.setScalar(1.68);
  obj.visible = morph === "S";
  labGroup.add(obj);
  labObjects.set(morph, obj);
}
labGroup.visible = false;
scene.add(labGroup);

let activeLabMorph = "S";
let dedicatedS = null;
let dedicatedSReady = false;
let sf3dLab = null;
let sf3dReady = false;

const conceptSprites = new Map();
const conceptTextures = new Map();
const conceptReady = new Set();
const textureLoader = new THREE.TextureLoader();
const conceptLayout = {
  S: { scale: [4.85, 4.45], y: 2.35 },
  P: { scale: [5.20, 4.10], y: 2.18 },
  E: { scale: [4.85, 4.16], y: 2.20 },
  A: { scale: [5.25, 3.66], y: 1.96 }
};

function updateConceptReadyState() {
  if (conceptReady.size === 4) stage.dataset.conceptMorphs = "loaded";
}

for (const morph of ["S", "P", "E", "A"]) {
  textureLoader.load(
    `${import.meta.env.BASE_URL}concept/${morph}.webp`,
    (texture) => {
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.minFilter = THREE.LinearFilter;
      texture.magFilter = THREE.LinearFilter;
      conceptTextures.set(morph, texture);

      const material = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        depthWrite: false
      });
      const sprite = new THREE.Sprite(material);
      const layout = conceptLayout[morph];
      sprite.name = `Concept_${morph}_2_5D`;
      sprite.position.set(0, layout.y, 0.15);
      sprite.scale.set(layout.scale[0], layout.scale[1], 1);
      sprite.visible = activeLabMorph === morph && !(morph === "S" && sf3dReady);
      conceptSprites.set(morph, sprite);
      conceptReady.add(morph);
      labGroup.add(sprite);
      stage.dataset[`concept${morph}`] = "loaded";
      updateConceptReadyState();
      setLabMorph(activeLabMorph);
    },
    undefined,
    (error) => {
      stage.dataset[`concept${morph}`] = "error";
      console.error(`Concept ${morph} sprite failed to load`, error);
    }
  );
}

function makeLiteMaterialProfile(profile) {
  return {
    ...profile,
    id: `${profile.id}-lite-runtime`,
    material: {
      ...(profile.material || {}),
      preserveBaseColorMap: true,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      metalness: 0.0,
      minRoughness: Math.max(0.68, profile.material?.minRoughness ?? 0.68)
    }
  };
}

const sf3dVariant = query.get("sf3dVariant") || (preview3d ? "hunyuanstyled" : null);
const sf3dBaseProfile = sf3dVariant === "hunyuanrigged"
  ? CREATURE_3D_PROFILES.sHunyuan2mvRigged
  : sf3dVariant === "hunyuanstyled"
  ? CREATURE_3D_PROFILES.sHunyuan2mvStyled
  : sf3dVariant === "hunyuan2mv"
    ? CREATURE_3D_PROFILES.sHunyuan2mvRaw
  : sf3dVariant === "hunyuanclean"
    ? CREATURE_3D_PROFILES.sHunyuan2mvClean
    : sf3dVariant === "hunyuanlod1"
      ? CREATURE_3D_PROFILES.sHunyuan2mvLod1
    : sf3dVariant === "hunyuanlod2"
      ? CREATURE_3D_PROFILES.sHunyuan2mvLod2
    : sf3dVariant === "hunyuanlod3"
      ? CREATURE_3D_PROFILES.sHunyuan2mvLod3
    : sf3dVariant === "hunyuanlod4"
      ? CREATURE_3D_PROFILES.sHunyuan2mvLod4
      : sf3dVariant === "lod1"
    ? CREATURE_3D_PROFILES.sSf3dCorrectedLod1
  : sf3dVariant === "lod2lite"
    ? CREATURE_3D_PROFILES.sSf3dCorrectedLod2Lite
    : sf3dVariant === "lod3lite"
      ? CREATURE_3D_PROFILES.sSf3dCorrectedLod3Lite
    : sf3dVariant === "lod2"
      ? CREATURE_3D_PROFILES.sSf3dCorrectedLod2
      : sf3dVariant === "lod3"
        ? CREATURE_3D_PROFILES.sSf3dCorrectedLod3
    : sf3dVariant === "triposr3q"
      ? CREATURE_3D_PROFILES.sTripoSr3q
      : sf3dVariant === "triposr"
        ? CREATURE_3D_PROFILES.sTripoSrSide
        : sf3dVariant === "side"
          ? CREATURE_3D_PROFILES.sSf3dSide
          : sf3dVariant === "white"
            ? CREATURE_3D_PROFILES.sSf3dWhite
            : CREATURE_3D_PROFILES.sSf3dCorrected;

const sf3dProfile = sf3dMaterialMode === "lite" && (sf3dVariant === "lod2" || sf3dVariant === "lod3")
  ? makeLiteMaterialProfile(sf3dBaseProfile)
  : sf3dBaseProfile;

function setupSf3dBenchmark(source, count) {
  if (!count) return;

  sf3dBenchGroup = new THREE.Group();
  sf3dBenchGroup.name = `SF3D_Benchmark_${sf3dBenchMode}_${count}`;
  const columns = Math.min(6, count);
  const rows = Math.ceil(count / columns);
  const transforms = Array.from({ length: count }, (_, i) => {
    const column = i % columns;
    const row = Math.floor(i / columns);
    return {
      position: [
        (column - (columns - 1) / 2) * 1.42,
        0,
        (row - (rows - 1) / 2) * 1.18
      ],
      rotation: [0, (column - (columns - 1) / 2) * 0.035, 0]
    };
  });

  if (sf3dBenchMode === "instance") {
    const batch = createStaticCreatureInstanceBatch(source, {
      renderer,
      profile: sf3dProfile,
      placement: "benchmark",
      count,
      materialSide: sf3dBenchSide,
      transforms
    });

    if (batch.supported) {
      sf3dBenchGroup.add(batch.object);
      stage.dataset.sf3dBenchInstancing = "supported";
    } else {
      stage.dataset.sf3dBenchInstancing = `unsupported:${batch.reason}`;
      sf3dBenchReady = true;
      stage.dataset.sf3dBench = "unsupported";
      window.__sf3dBench = {
        count,
        mode: sf3dBenchMode,
        materialSide: sf3dBenchSide,
        supported: false,
        reason: batch.reason
      };
      return;
    }
  } else {
    for (let i = 0; i < count; i++) {
      const model = fitCreature3D(cloneCreature3D(source), {
        renderer,
        profile: sf3dProfile,
        placement: "benchmark",
        materialSide: sf3dBenchSide
      });
      const transform = transforms[i];
      model.position.x += transform.position[0];
      model.position.z += transform.position[2];
      model.rotation.y += transform.rotation[1];
      sf3dBenchGroup.add(model);
    }
  }

  if (sf3dLab) sf3dLab.visible = false;
  conceptSprites.forEach((sprite) => { sprite.visible = false; });
  labGroup.add(sf3dBenchGroup);
  view = "lab";
  sf3dBenchStartedAt = performance.now();
  sf3dBenchFrameTimes = [];
  sf3dBenchReady = false;
  stage.dataset.sf3dBench = "running";
  stage.dataset.sf3dBenchCount = String(count);
  stage.dataset.sf3dBenchSide = sf3dBenchSide;
  stage.dataset.sf3dBenchMode = sf3dBenchMode;
}

function profileForStress(profile, level) {
  if (sf3dMaterialMode !== "lite" || level < 2) return profile;
  return makeLiteMaterialProfile(profile);
}

function setupRaceStress(baseSource, baseProfile, lodData, config = {}) {
  if (!sf3dRaceStress) return;

  const distances = config.distances || [9, 18, 30];
  if (lodData.length !== distances.length) {
    throw new Error(`Race stress LOD mismatch: ${lodData.length} assets for ${distances.length} distances`);
  }

  const levelData = [
    {
      source: baseSource,
      profile: profileForStress(baseProfile, 0),
      triangles: Number(config.baseTriangles) || 0
    },
    ...lodData.map((data, index) => ({
      source: data.source,
      profile: profileForStress(data.profile, index + 1),
      triangles: Number(data.stats?.triangles) || 0
    }))
  ];
  const materialSide = config.materialSide || "front";

  sf3dRaceStressConfig = {
    label: config.label || baseProfile.id,
    distances: [...distances],
    profiles: levelData.map((level) => level.profile.id),
    triangles: levelData.map((level) => level.triangles),
    materialSide
  };
  sf3dRaceStressLevelCounts = Array(levelData.length).fill(0);

  for (const racer of racers) {
    racer.obj.children.forEach((child) => { child.visible = false; });
  }

  if (sf3dRaceStressMode === "instance") {
    sf3dRaceStressBatches = levelData.map((level) => {
      const batch = createStaticCreatureInstanceBatch(level.source, {
        renderer,
        profile: level.profile,
        placement: "race",
        count: racers.length,
        materialSide
      });
      if (!batch.supported) {
        throw new Error(`Dynamic instancing unsupported for ${level.profile.id}: ${batch.reason}`);
      }
      batch.object.count = 0;
      scene.add(batch.object);
      return batch;
    });
  } else {
    for (const racer of racers) {
      const lod = new THREE.LOD();
      lod.name = `${sf3dRaceStressConfig.label}_RaceStress_${racer.id}`;

      levelData.forEach((level, index) => {
        const model = fitCreature3D(cloneCreature3D(level.source), {
          renderer,
          profile: level.profile,
          placement: "race",
          materialSide
        });
        lod.addLevel(model, index === 0 ? 0 : distances[index - 1]);
      });

      racer.obj.add(lod);
      racer.obj.userData.sf3dStressLod = lod;
    }
  }

  view = "race";
  stage.dataset.sf3dRaceStress = "running";
  stage.dataset.sf3dRaceStressMode = sf3dRaceStressMode;
  stage.dataset.sf3dRaceStressLabel = sf3dRaceStressConfig.label;
  stage.dataset.sf3dRaceStressDistances = distances.join(",");
  stage.dataset.sf3dRaceStressProfiles = sf3dRaceStressConfig.profiles.join(",");
  stage.dataset.sf3dMaterialMode = sf3dMaterialMode;
  stage.dataset.sf3dRaceStressRacers = String(racers.length);
  sf3dRaceStressStartedAt = performance.now();
  sf3dRaceStressFrames = [];
  sf3dRaceStressReady = false;
}

function updateRaceStressInstances() {
  if (!sf3dRaceStress || sf3dRaceStressMode !== "instance" || !sf3dRaceStressBatches || !sf3dRaceStressConfig) return;

  const counts = Array(sf3dRaceStressBatches.length).fill(0);
  const finalMatrix = new THREE.Matrix4();
  const distances = sf3dRaceStressConfig.distances;

  for (const racer of racers) {
    racer.obj.updateMatrixWorld(true);
    const distance = camera.position.distanceTo(racer.obj.position);
    let level = 0;
    while (level < distances.length && distance >= distances[level]) level += 1;
    const batch = sf3dRaceStressBatches[level];
    finalMatrix.multiplyMatrices(racer.obj.matrixWorld, batch.prototypeMatrix);
    batch.object.setMatrixAt(counts[level], finalMatrix);
    counts[level] += 1;
  }

  for (let i = 0; i < sf3dRaceStressBatches.length; i++) {
    const batch = sf3dRaceStressBatches[i];
    batch.object.count = counts[i];
    batch.object.instanceMatrix.needsUpdate = true;
  }

  sf3dRaceStressLevelCounts = counts;
  stage.dataset.sf3dRaceStressCounts = counts.join(",");
}

function sampleRaceStress(now, frameMs) {
  if (!sf3dRaceStress || !sf3dRaceStressStartedAt || sf3dRaceStressReady || !sf3dRaceStressConfig) return;
  const elapsed = now - sf3dRaceStressStartedAt;
  if (elapsed >= 1000 && Number.isFinite(frameMs) && frameMs > 0) {
    const levelCounts = [...sf3dRaceStressLevelCounts];
    const modelTriangles = levelCounts.reduce(
      (sum, count, index) => sum + count * (sf3dRaceStressConfig.triangles[index] || 0),
      0
    );
    sf3dRaceStressFrames.push({
      ms: frameMs,
      triangles: renderer.info.render.triangles,
      calls: renderer.info.render.calls,
      levelCounts,
      modelTriangles
    });
  }
  if (elapsed < 6500 || sf3dRaceStressFrames.length < 12) return;

  const ms = sf3dRaceStressFrames.map((frame) => frame.ms).sort((a, b) => a - b);
  const triangles = sf3dRaceStressFrames.map((frame) => frame.triangles);
  const calls = sf3dRaceStressFrames.map((frame) => frame.calls);
  const modelTriangles = sf3dRaceStressFrames.map((frame) => frame.modelTriangles);
  const avg = ms.reduce((sum, value) => sum + value, 0) / ms.length;
  const avgTriangles = triangles.reduce((sum, value) => sum + value, 0) / triangles.length;
  const avgCalls = calls.reduce((sum, value) => sum + value, 0) / calls.length;
  const avgModelTriangles = modelTriangles.reduce((sum, value) => sum + value, 0) / modelTriangles.length;
  const percentile = (p) => ms[Math.min(ms.length - 1, Math.floor((ms.length - 1) * p))];
  const maxLevelCounts = sf3dRaceStressConfig.triangles.map((_, index) =>
    Math.max(...sf3dRaceStressFrames.map((frame) => frame.levelCounts[index] || 0))
  );
  const allBaseTriangles = racers.length * (sf3dRaceStressConfig.triangles[0] || 0);

  window.__sf3dRaceStress = {
    racers: racers.length,
    mode: sf3dRaceStressMode,
    label: sf3dRaceStressConfig.label,
    materialMode: sf3dMaterialMode,
    materialSide: sf3dRaceStressConfig.materialSide,
    distances: sf3dRaceStressConfig.distances,
    profiles: sf3dRaceStressConfig.profiles,
    levelTriangles: sf3dRaceStressConfig.triangles,
    finalLevelCounts: [...sf3dRaceStressLevelCounts],
    maxLevelCounts,
    durationMs: Number(elapsed.toFixed(0)),
    samples: ms.length,
    averageFrameMs: Number(avg.toFixed(3)),
    averageFps: Number((1000 / avg).toFixed(2)),
    medianFrameMs: Number(percentile(0.5).toFixed(3)),
    p95FrameMs: Number(percentile(0.95).toFixed(3)),
    averageModelTriangles: Math.round(avgModelTriangles),
    allBaseTriangles,
    averageRendererTriangles: Math.round(avgTriangles),
    minRendererTriangles: Math.min(...triangles),
    maxRendererTriangles: Math.max(...triangles),
    averageRendererCalls: Number(avgCalls.toFixed(2)),
    minRendererCalls: Math.min(...calls),
    maxRendererCalls: Math.max(...calls),
    renderScale,
    viewport: {
      width: renderer.domElement.width,
      height: renderer.domElement.height,
      pixelRatio: renderer.getPixelRatio()
    },
    note: `CI Chromium real race-loop stress test with 18 moving ${sf3dRaceStressConfig.triangles.length}-level LOD creatures; not physical-device FPS`
  };
  sf3dRaceStressReady = true;
  stage.dataset.sf3dRaceStress = "ready";
}

function setupHunyuanRacePack(baseData, lod3Data, lod4Data, riggedData, lod4RiggedData) {
  if (!hunyuanRacePack) return;

  const levels = [baseData, lod3Data, lod4Data];
  hunyuanRacePackAnimated = Boolean(lod4RiggedData?.animations?.length);
  hunyuanRacePackBatches = null;
  hunyuanRacePackRiggedFar = [];

  racers.forEach((racer, index) => {
    racer.obj.children.forEach((child) => { child.visible = false; });
    racer.morph = "S";
    racer.cruise = morphStats.S.cruise + (index % 5) * 0.18;
    racer.accel = morphStats.S.accel;
    racer.drain = morphStats.S.drain;
  });

  if (hunyuanRacePackAnimated) {
    const clip = lod4RiggedData.animations[0];
    racers.forEach((racer, index) => {
      const model = fitCreature3D(cloneCreature3D(lod4RiggedData.source), {
        renderer,
        profile: lod4RiggedData.profile,
        placement: "race",
        materialSide: hunyuanRacePackSide
      });
      model.name = `Hunyuan_RacePack_LOD4_Rigged_${racer.id}`;
      racer.obj.add(model);

      const mixer = new THREE.AnimationMixer(model);
      const action = mixer.clipAction(clip);
      action.play();
      if (clip.duration > 0) mixer.setTime((index / racers.length) * clip.duration);
      sf3dRaceMixers.push(mixer);
      hunyuanRacePackRiggedFar.push({
        racerId: racer.id,
        racer,
        model,
        mixer,
        action,
        clipDuration: Math.max(0.001, clip.duration || 1)
      });
    });

    window.__hunyuanRacePackRiggedFar = hunyuanRacePackRiggedFar.map((entry) => entry.model);
    stage.dataset.hunyuanRacePackMode = "animated-lod4";
    stage.dataset.hunyuanRacePackFarAnimation = clip.name || "unnamed";
  } else {
    hunyuanRacePackBatches = levels.map((data) => {
      const batch = createStaticCreatureInstanceBatch(data.source, {
        renderer,
        profile: data.profile,
        placement: "race",
        count: racers.length,
        materialSide: hunyuanRacePackSide
      });
      if (!batch.supported) {
        throw new Error(`Hunyuan race pack instancing unsupported for ${data.profile.id}: ${batch.reason}`);
      }
      batch.object.count = 0;
      batch.object.visible = false;
      scene.add(batch.object);
      return batch;
    });
    stage.dataset.hunyuanRacePackMode = "static-lod-fallback";
  }

  const selectedRacer = racers.find((racer) => racer.id === selectedId);
  if (selectedRacer && riggedData) {
    hunyuanRacePackRiggedSelected = fitCreature3D(cloneCreature3D(riggedData.source), {
      renderer,
      profile: riggedData.profile,
      placement: "race",
      materialSide: hunyuanRacePackSide
    });
    hunyuanRacePackRiggedSelected.name = "Hunyuan_RacePack_Selected_Rigged";
    hunyuanRacePackRiggedSelected.visible = false;
    selectedRacer.obj.add(hunyuanRacePackRiggedSelected);

    if (riggedData.animations?.length) {
      const mixer = new THREE.AnimationMixer(hunyuanRacePackRiggedSelected);
      const action = mixer.clipAction(riggedData.animations[0]);
      action.play();
      sf3dRaceMixers.push(mixer);
      hunyuanRacePackSelectedAction = {
        racer: selectedRacer,
        mixer,
        action,
        clipDuration: Math.max(0.001, riggedData.animations[0].duration || 1)
      };
      window.__hunyuanRacePackRiggedSelected = hunyuanRacePackRiggedSelected;
      stage.dataset.hunyuanRacePackRigged = "playing";
      stage.dataset.hunyuanRacePackRiggedClip = riggedData.animations[0].name || "unnamed";
    } else {
      stage.dataset.hunyuanRacePackRigged = "no-animation";
    }
  }

  stage.dataset.hunyuanRacePack = "loaded";
  stage.dataset.hunyuanRacePackGait = hunyuanGaitVersion;
  stage.dataset.hunyuanRacePackSide = hunyuanRacePackSide;
  stage.dataset.hunyuanRacePackProfiles = levels.map((data) => data.profile.id).join(",");
  stage.dataset.hunyuanRacePackTriangles = levels.map((data) => data.stats.triangles).join(",");
}

function syncHunyuanStrideToSpeed() {
  if (!hunyuanRacePackAnimated) return;

  let minScale = Infinity;
  let maxScale = 0;
  let totalScale = 0;
  let count = 0;
  let maxSyncError = 0;

  const apply = (entry) => {
    if (!entry?.action || !entry?.racer) return;
    const speed = Math.max(0, entry.racer.speed);
    const cycleHz = speed / hunyuanStrideMetersPerCycle;
    const timeScale = THREE.MathUtils.clamp(
      cycleHz * entry.clipDuration,
      0,
      6.0
    );
    entry.action.timeScale = timeScale;

    const representedSpeed =
      (timeScale / entry.clipDuration) * hunyuanStrideMetersPerCycle;
    const syncError = Math.abs(representedSpeed - speed);

    minScale = Math.min(minScale, timeScale);
    maxScale = Math.max(maxScale, timeScale);
    totalScale += timeScale;
    count += 1;
    maxSyncError = Math.max(maxSyncError, syncError);
  };

  for (const entry of hunyuanRacePackRiggedFar) apply(entry);
  apply(hunyuanRacePackSelectedAction);

  if (count > 0) {
    const selectedFar = hunyuanRacePackRiggedFar.find((entry) => entry.racerId === selectedId);
    stage.dataset.hunyuanStrideSync = "active";
    stage.dataset.hunyuanStrideMeters = String(hunyuanStrideMetersPerCycle);
    stage.dataset.hunyuanStrideScaleRange =
      `${minScale.toFixed(3)},${maxScale.toFixed(3)}`;
    stage.dataset.hunyuanStrideScaleAverage = (totalScale / count).toFixed(3);
    stage.dataset.hunyuanStrideSyncError = maxSyncError.toFixed(4);
    if (selectedFar) {
      stage.dataset.hunyuanSelectedSpeed = selectedFar.racer.speed.toFixed(3);
      stage.dataset.hunyuanSelectedStrideScale = selectedFar.action.timeScale.toFixed(3);
      const selectedRepresentedSpeed =
        (selectedFar.action.timeScale / selectedFar.clipDuration) * hunyuanStrideMetersPerCycle;
      stage.dataset.hunyuanSelectedStrideRepresentedSpeed = selectedRepresentedSpeed.toFixed(3);
      stage.dataset.hunyuanSelectedStrideError =
        Math.abs(selectedRepresentedSpeed - selectedFar.racer.speed).toFixed(4);
    }
  }
}

function updateHunyuanRacePackInstances() {
  if (!hunyuanRacePack) return;

  const visible = view === "race" || view === "follow";
  const selectedHighVisible = visible && view === "follow" && Boolean(hunyuanRacePackRiggedSelected);

  if (hunyuanRacePackRiggedSelected) {
    hunyuanRacePackRiggedSelected.visible = selectedHighVisible;
    stage.dataset.hunyuanRacePackRiggedSelected =
      hunyuanRacePackRiggedSelected.visible ? "visible" : "hidden";
  }

  if (hunyuanRacePackAnimated) {
    let farVisible = 0;
    for (const entry of hunyuanRacePackRiggedFar) {
      const useFar = visible && !(view === "follow" && entry.racerId === selectedId && hunyuanRacePackRiggedSelected);
      entry.model.visible = useFar;
      if (useFar) farVisible += 1;
    }

    const highVisible = selectedHighVisible ? 1 : 0;
    stage.dataset.hunyuanRacePackAnimatedCounts = `${farVisible},${highVisible}`;
    stage.dataset.hunyuanRacePackCounts = "0,0,0";
    stage.dataset.hunyuanRacePackView = view;
    return;
  }

  if (!hunyuanRacePackBatches) return;

  for (const batch of hunyuanRacePackBatches) batch.object.visible = visible;
  if (!visible) {
    hunyuanRacePackCounts = [0, 0, 0];
    stage.dataset.hunyuanRacePackCounts = "0,0,0";
    return;
  }

  const counts = [0, 0, 0];
  const finalMatrix = new THREE.Matrix4();

  for (const racer of racers) {
    racer.obj.updateMatrixWorld(true);
    const distance = camera.position.distanceTo(racer.obj.position);

    if (view === "follow" && racer.id === selectedId && hunyuanRacePackRiggedSelected) {
      continue;
    }

    let level = 2;
    if (view === "follow" && distance < 8) {
      level = 1;
    } else if (view === "race" && distance < 12) {
      level = 1;
    }

    const batch = hunyuanRacePackBatches[level];
    finalMatrix.multiplyMatrices(racer.obj.matrixWorld, batch.prototypeMatrix);
    batch.object.setMatrixAt(counts[level], finalMatrix);
    counts[level] += 1;
  }

  for (let i = 0; i < hunyuanRacePackBatches.length; i++) {
    const batch = hunyuanRacePackBatches[i];
    batch.object.count = counts[i];
    batch.object.instanceMatrix.needsUpdate = true;
  }

  hunyuanRacePackCounts = counts;
  stage.dataset.hunyuanRacePackCounts = counts.join(",");
  stage.dataset.hunyuanRacePackView = view;
}

function setupRaceLodBenchmark(baseSource, baseProfile, lod1Data, lod2Data, lod3Data) {
  if (!sf3dRaceLodBench) return;

  const group = new THREE.Group();
  group.name = "SF3D_Race_LOD_Benchmark_18";

  const near = 4;
  const mid = 5;
  const far = 5;
  const veryFar = 4;
  const distances = [
    ...Array.from({ length: near }, (_, i) => 4 + i * 1.1),
    ...Array.from({ length: mid }, (_, i) => 10 + i * 1.4),
    ...Array.from({ length: far }, (_, i) => 19 + i * 1.6),
    ...Array.from({ length: veryFar }, (_, i) => 31 + i * 1.8)
  ];

  for (let i = 0; i < distances.length; i++) {
    const lod = new THREE.LOD();

    const baseModel = fitCreature3D(cloneCreature3D(baseSource), {
      renderer,
      profile: baseProfile,
      placement: "benchmark",
      materialSide: "front"
    });
    const lod1Model = fitCreature3D(cloneCreature3D(lod1Data.source), {
      renderer,
      profile: lod1Data.profile,
      placement: "benchmark",
      materialSide: "front"
    });
    const lod2Model = fitCreature3D(cloneCreature3D(lod2Data.source), {
      renderer,
      profile: lod2Data.profile,
      placement: "benchmark",
      materialSide: "front"
    });
    const lod3Model = fitCreature3D(cloneCreature3D(lod3Data.source), {
      renderer,
      profile: lod3Data.profile,
      placement: "benchmark",
      materialSide: "front"
    });

    lod.addLevel(baseModel, 0);
    lod.addLevel(lod1Model, 9);
    lod.addLevel(lod2Model, 18);
    lod.addLevel(lod3Model, 30);

    const column = i % 6;
    const row = Math.floor(i / 6);
    lod.position.set(
      (column - 2.5) * 1.45,
      0,
      -distances[i]
    );
    lod.rotation.y = (column - 2.5) * 0.025;
    group.add(lod);
  }

  if (sf3dLab) sf3dLab.visible = false;
  conceptSprites.forEach((sprite) => { sprite.visible = false; });
  labGroup.add(group);
  labGroup.visible = true;
  view = "lab";

  camera.position.set(0, 5.4, 5.5);
  camera.lookAt(0, 0.8, -14);
  camera.updateMatrixWorld(true);
  group.updateMatrixWorld(true);

  sf3dRaceLodBenchStartedAt = performance.now();
  sf3dRaceLodBenchFrameTimes = [];
  sf3dRaceLodBenchReady = false;
  stage.dataset.sf3dRaceLodBench = "running";
}

function sampleRaceLodBenchmark(now, frameMs) {
  if (!sf3dRaceLodBench || !sf3dRaceLodBenchStartedAt || sf3dRaceLodBenchReady) return;
  const elapsed = now - sf3dRaceLodBenchStartedAt;
  if (elapsed >= 500 && Number.isFinite(frameMs) && frameMs > 0) {
    sf3dRaceLodBenchFrameTimes.push(frameMs);
  }
  if (elapsed < 3000 || sf3dRaceLodBenchFrameTimes.length < 8) return;

  const times = [...sf3dRaceLodBenchFrameTimes].sort((a, b) => a - b);
  const avg = times.reduce((s, v) => s + v, 0) / times.length;
  const percentile = (p) => times[Math.min(times.length - 1, Math.floor((times.length - 1) * p))];

  window.__sf3dRaceLodBench = {
    count: 18,
    expectedNear: 4,
    expectedMid: 5,
    expectedFar: 5,
    expectedVeryFar: 4,
    theoreticalTriangles: 4 * 8960 + 5 * 4480 + 5 * 2240 + 4 * 1120,
    allBaseTriangles: 18 * 8960,
    rendererTriangles: renderer.info.render.triangles,
    rendererCalls: renderer.info.render.calls,
    averageFrameMs: Number(avg.toFixed(3)),
    averageFps: Number((1000 / avg).toFixed(2)),
    medianFrameMs: Number(percentile(0.5).toFixed(3)),
    p95FrameMs: Number(percentile(0.95).toFixed(3)),
    note: "CI Chromium synthetic mixed-distance LOD benchmark; not physical-device FPS"
  };
  sf3dRaceLodBenchReady = true;
  stage.dataset.sf3dRaceLodBench = "ready";
}

function sampleSf3dBenchmark(now, frameMs) {
  if (!sf3dBenchCount || !sf3dBenchStartedAt || sf3dBenchReady) return;
  const elapsedMs = now - sf3dBenchStartedAt;

  if (elapsedMs >= 500 && Number.isFinite(frameMs) && frameMs > 0) {
    sf3dBenchFrameTimes.push(frameMs);
  }

  if (elapsedMs < 3000 || sf3dBenchFrameTimes.length < 5) return;

  const times = [...sf3dBenchFrameTimes].sort((a, b) => a - b);
  const average = times.reduce((sum, value) => sum + value, 0) / times.length;
  const percentile = (p) => times[Math.min(times.length - 1, Math.floor((times.length - 1) * p))];

  window.__sf3dBench = {
    count: sf3dBenchCount,
    mode: sf3dBenchMode,
    materialSide: sf3dBenchSide,
    supported: true,
    samples: times.length,
    averageFrameMs: Number(average.toFixed(3)),
    averageFps: Number((1000 / average).toFixed(2)),
    medianFrameMs: Number(percentile(0.5).toFixed(3)),
    p95FrameMs: Number(percentile(0.95).toFixed(3)),
    trianglesPerInstance: sf3dTrianglesPerInstance,
    expectedModelTriangles: sf3dTrianglesPerInstance * sf3dBenchCount,
    rendererTriangles: renderer.info.render.triangles,
    rendererCalls: renderer.info.render.calls,
    rendererLines: renderer.info.render.lines,
    rendererPoints: renderer.info.render.points,
    geometries: renderer.info.memory.geometries,
    textures: renderer.info.memory.textures,
    viewport: {
      width: renderer.domElement.width,
      height: renderer.domElement.height,
      pixelRatio: renderer.getPixelRatio()
    },
    note: "CI Chromium benchmark; not a physical-device FPS measurement"
  };
  sf3dBenchReady = true;
  stage.dataset.sf3dBench = "ready";
}

loadCreature3D(sf3dProfile)
  .then(({ source, animations, stats, profile }) => {
    sf3dTrianglesPerInstance = stats.triangles;

    sf3dLab = fitCreature3D(cloneCreature3D(source), {
      renderer,
      profile,
      placement: "lab"
    });
    sf3dLab.rotation.y += modelYawRadians;
    sf3dLab.updateMatrixWorld(true);
    sf3dLab.name = "EvoWild_S_SF3D_Lab";
    stage.dataset.modelYaw = String(modelYawDegrees);
    sf3dLab.visible = activeLabMorph === "S";
    labGroup.add(sf3dLab);

    if (animations.length) {
      sf3dLabMixer = new THREE.AnimationMixer(sf3dLab);
      sf3dLabMixer.clipAction(animations[0]).play();
      window.__sf3dLabMixer = sf3dLabMixer;
      let animatedBoneCount = 0;
      sf3dLab.traverse((node) => {
        if (node.isBone) animatedBoneCount += 1;
      });
      stage.dataset.sf3dAnimation = "playing";
      stage.dataset.sf3dAnimationClip = animations[0].name || "unnamed";
      stage.dataset.sf3dAnimationBones = String(animatedBoneCount);
      window.__sf3dAnimatedLab = sf3dLab;
    } else {
      stage.dataset.sf3dAnimation = "none";
    }

    const raceS = racers.find((r) => r.morph === "S");
    if (raceS && !sf3dRaceStress && !hunyuanRacePack) {
      raceS.obj.children.forEach((child) => { child.visible = false; });

      const baseRaceModel = fitCreature3D(cloneCreature3D(source), {
        renderer,
        profile,
        placement: "race"
      });
      baseRaceModel.name = "EvoWild_S_SF3D_Race_Base";

      if (animations.length) {
        const raceMixer = new THREE.AnimationMixer(baseRaceModel);
        raceMixer.clipAction(animations[0]).play();
        sf3dRaceMixers.push(raceMixer);
        window.__sf3dAnimatedRace = baseRaceModel;
      }

      const useSf3dRaceLod = profile.id === CREATURE_3D_PROFILES.sSf3dCorrected.id && !sf3dVariant;
      const useHunyuanRaceLod = profile.id === CREATURE_3D_PROFILES.sHunyuan2mvStyled.id;
      const useRaceLod = (useSf3dRaceLod || useHunyuanRaceLod) && !sf3dRaceStress;

      if (useRaceLod) {
        const raceLod = new THREE.LOD();
        raceLod.name = useHunyuanRaceLod
          ? "EvoWild_S_Hunyuan_Race_LOD"
          : "EvoWild_S_SF3D_Race_LOD";
        raceLod.addLevel(baseRaceModel, 0);
        raceS.obj.add(raceLod);
        raceS.obj.userData.sf3d = raceLod;
        stage.dataset.sf3dRaceLod = "loading";
        stage.dataset.sf3dRaceLodLevels = "1";

        const extraProfiles = useHunyuanRaceLod
          ? [
              CREATURE_3D_PROFILES.sHunyuan2mvStyledLod3,
              CREATURE_3D_PROFILES.sHunyuan2mvStyledLod4
            ]
          : [
              CREATURE_3D_PROFILES.sSf3dCorrectedLod1,
              CREATURE_3D_PROFILES.sSf3dCorrectedLod2Lite,
              CREATURE_3D_PROFILES.sSf3dCorrectedLod3Lite
            ];
        const distances = useHunyuanRaceLod ? [16, 30] : [9, 18, 30];

        Promise.all(extraProfiles.map((lodProfile) => loadCreature3D(lodProfile)))
          .then((lodData) => {
            lodData.forEach((data, index) => {
              const lodModel = fitCreature3D(cloneCreature3D(data.source), {
                renderer,
                profile: data.profile,
                placement: "race"
              });
              lodModel.name = `${raceLod.name}_L${index + 1}`;
              raceLod.addLevel(lodModel, distances[index]);
            });

            stage.dataset.sf3dRaceLod = "loaded";
            stage.dataset.sf3dRaceLodProfiles = [
              profile.id,
              ...lodData.map((data) => data.profile.id)
            ].join(",");
            stage.dataset.sf3dRaceLodLevels = String(raceLod.levels.length);
            stage.dataset.sf3dRaceLodDistances = raceLod.levels.map((level) => level.distance).join(",");
            window.__sf3dRaceLod = raceLod;
          })
          .catch((error) => {
            stage.dataset.sf3dRaceLod = "error";
            console.error("Race LOD assets failed to load; keeping base race model", error);
          });
      } else {
        baseRaceModel.name = "EvoWild_S_3D_Race";
        raceS.obj.add(baseRaceModel);
        raceS.obj.userData.sf3d = baseRaceModel;
        stage.dataset.sf3dRaceLod = "disabled";
      }
    }

    sf3dReady = true;
    stage.dataset.sf3d = "loaded";
    stage.dataset.sf3dProfile = profile.id;
    stage.dataset.sf3dTriangles = String(stats.triangles);
    stage.dataset.sf3dMeshes = String(stats.meshes);
    stage.dataset.sf3dMaterials = String(stats.materials);
    stage.dataset.sf3dTextures = String(stats.textures);
    stage.dataset.sf3dAnimations = String(animations.length);
    stage.dataset.sf3dBounds = `${stats.bounds.x},${stats.bounds.y},${stats.bounds.z}`;
    setLabMorph(activeLabMorph);
    setupSf3dBenchmark(source, sf3dBenchCount);

    if (hunyuanRacePack && profile.id === CREATURE_3D_PROFILES.sHunyuan2mvStyled.id) {
      Promise.all([
        Promise.resolve({ source, animations, stats, profile }),
        loadCreature3D(CREATURE_3D_PROFILES.sHunyuan2mvStyledLod3),
        loadCreature3D(CREATURE_3D_PROFILES.sHunyuan2mvStyledLod4),
        loadCreature3D(
          hunyuanGaitVersion === "v1"
            ? CREATURE_3D_PROFILES.sHunyuan2mvRigged
            : hunyuanGaitVersion === "v2"
              ? CREATURE_3D_PROFILES.sHunyuan2mvRiggedV2
              : hunyuanGaitVersion === "v21"
                ? CREATURE_3D_PROFILES.sHunyuan2mvRiggedV21
                : CREATURE_3D_PROFILES.sHunyuan2mvRiggedV3
        ),
        loadCreature3D(
          hunyuanGaitVersion === "v1"
            ? CREATURE_3D_PROFILES.sHunyuan2mvLod4Rigged
            : hunyuanGaitVersion === "v2"
              ? CREATURE_3D_PROFILES.sHunyuan2mvLod4RiggedV2
              : hunyuanGaitVersion === "v21" || hunyuanGaitVersion === "v3hybrid"
                ? CREATURE_3D_PROFILES.sHunyuan2mvLod4RiggedV21
                : CREATURE_3D_PROFILES.sHunyuan2mvLod4RiggedV3
        )
      ]).then(([baseData, lod3Data, lod4Data, riggedData, lod4RiggedData]) => {
        setupHunyuanRacePack(baseData, lod3Data, lod4Data, riggedData, lod4RiggedData);
      }).catch((error) => {
        stage.dataset.hunyuanRacePack = "error";
        console.error("18-racer Hunyuan S-only race pack failed to load", error);
      });
    }

    if (sf3dRaceLodBench && profile.id === CREATURE_3D_PROFILES.sSf3dCorrected.id) {
      Promise.all([
        loadCreature3D(CREATURE_3D_PROFILES.sSf3dCorrectedLod1),
        loadCreature3D(CREATURE_3D_PROFILES.sSf3dCorrectedLod2),
        loadCreature3D(CREATURE_3D_PROFILES.sSf3dCorrectedLod3)
      ]).then(([lod1Data, lod2Data, lod3Data]) => {
        setupRaceLodBenchmark(source, profile, lod1Data, lod2Data, lod3Data);
      }).catch((error) => {
        stage.dataset.sf3dRaceLodBench = "error";
        console.error("Mixed-distance race LOD benchmark failed to load", error);
      });
    }

    if (sf3dRaceStress && profile.id === CREATURE_3D_PROFILES.sSf3dCorrected.id) {
      const stressLod2Profile = sf3dMaterialMode === "lite"
        ? CREATURE_3D_PROFILES.sSf3dCorrectedLod2Lite
        : CREATURE_3D_PROFILES.sSf3dCorrectedLod2;
      const stressLod3Profile = sf3dMaterialMode === "lite"
        ? CREATURE_3D_PROFILES.sSf3dCorrectedLod3Lite
        : CREATURE_3D_PROFILES.sSf3dCorrectedLod3;

      Promise.all([
        loadCreature3D(CREATURE_3D_PROFILES.sSf3dCorrectedLod1),
        loadCreature3D(stressLod2Profile),
        loadCreature3D(stressLod3Profile)
      ]).then((lodData) => {
        setupRaceStress(source, profile, lodData, {
          label: "sf3d",
          distances: [9, 18, 30],
          baseTriangles: stats.triangles,
          materialSide: "front"
        });
      }).catch((error) => {
        stage.dataset.sf3dRaceStress = "error";
        console.error("18-racer SF3D stress assets failed to load", error);
      });
    }

    if (sf3dRaceStress && profile.id === CREATURE_3D_PROFILES.sHunyuan2mvStyled.id) {
      Promise.all([
        loadCreature3D(CREATURE_3D_PROFILES.sHunyuan2mvStyledLod3),
        loadCreature3D(CREATURE_3D_PROFILES.sHunyuan2mvStyledLod4)
      ]).then((lodData) => {
        const stressNear = Math.max(
          0,
          Number.parseFloat(query.get("hunyuanStressNear") || "16") || 16
        );
        const requestedFar = Math.max(
          0,
          Number.parseFloat(query.get("hunyuanStressFar") || "30") || 30
        );
        const stressFar = Math.max(stressNear, requestedFar);
        setupRaceStress(source, profile, lodData, {
          label: "hunyuan",
          distances: [stressNear, stressFar],
          baseTriangles: stats.triangles,
          materialSide: sf3dBenchSide
        });
      }).catch((error) => {
        stage.dataset.sf3dRaceStress = "error";
        console.error("18-racer Hunyuan mixed-LOD stress assets failed to load", error);
      });
    }
  })
  .catch((error) => {
    stage.dataset.sf3d = "error";
    console.error("3D creature asset failed to load; keeping existing fallback", error);
  });

const assetBase = `${import.meta.env.BASE_URL}models/`;
const mtlLoader = new MTLLoader();
mtlLoader.load(
  `${assetBase}evowild-s.mtl`,
  (materials) => {
    materials.preload();
    const objLoader = new OBJLoader();
    objLoader.setMaterials(materials);
    objLoader.load(
      `${assetBase}evowild-s.obj`,
      (asset) => {
        asset.name = "EvoWild_S_Dedicated";
        asset.position.set(0, 0.02, 0);
        asset.scale.setScalar(1.25);
        asset.visible = activeLabMorph === "S";
        asset.traverse((node) => {
          if (!node.isMesh) return;
          node.frustumCulled = true;
          if (node.material) {
            node.material.side = THREE.FrontSide;
            node.material.needsUpdate = true;
          }
        });
        dedicatedS = asset;
        dedicatedSReady = true;
        labGroup.add(asset);
        stage.dataset.sAsset = "loaded";
        setLabMorph(activeLabMorph);
      },
      undefined,
      (error) => {
        stage.dataset.sAsset = "error";
        console.error("Dedicated S asset failed to load", error);
      }
    );
  },
  undefined,
  (error) => {
    stage.dataset.sAsset = "error";
    console.error("Dedicated S material failed to load", error);
  }
);

const labText = {
  S: ["S — Sprint", "細身・長脚・後方へ流れる角"],
  P: ["P — Power", "太い胴・大型肩・短く太い脚"],
  E: ["E — Endurance", "細長い体・最長脚・高い頭"],
  A: ["A — Agility", "低重心・短脚・大型の尾"]
};

function setLabMorph(morph) {
  activeLabMorph = morph;
  labObjects.forEach((obj, key) => {
    obj.visible = key === morph && !conceptReady.has(key) && !(key === "S" && (dedicatedSReady || sf3dReady));
  });
  if (dedicatedS) dedicatedS.visible = morph === "S" && !conceptReady.has("S") && !sf3dReady;
  if (sf3dLab) sf3dLab.visible = morph === "S" && sf3dReady;
  conceptSprites.forEach((sprite, key) => {
    sprite.visible = key === morph && !(key === "S" && sf3dReady);
  });

  const [title, baseDetail] = labText[morph];
  const detail = morph === "S" && sf3dReady
    ? `${baseDetail} / Stable Fast 3D live candidate`
    : conceptReady.has(morph)
      ? `${baseDetail} / 2.5D concept-source test`
      : morph === "S" && dedicatedSReady
        ? `${baseDetail} / dedicated 3D fallback`
        : baseDetail;
  const label = document.querySelector("#labLabel");
  label.innerHTML = `<strong>${title}</strong><span>${detail}</span>`;
  document.querySelectorAll("[data-morph]").forEach((button) => {
    button.classList.toggle("active", button.dataset.morph === morph);
  });
}
setLabMorph("S");

let elapsed = 0;
let last = performance.now();
let paused = false;
let view = preview3d ? "race" : "lab";
if (preview3d) {
  const viewLabel = document.querySelector("#viewLabel");
  if (viewLabel) viewLabel.textContent = "RACE VIEW";
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === "race");
  });
}

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
  const options = Array.from({ length: laneCount }, (_, lane) => lane).filter((lane) => lane !== Math.round(r.laneF) && laneFree(r, lane));
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
    const targetPos = p.clone().addScaledVector(side, laneOffset(r.laneF));
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

  const lab = view === "lab";
  const tactical = view === "tactical";
  scene.fog = (lab || tactical) ? null : raceFog;
  scene.background = new THREE.Color(lab ? 0x202a35 : 0x9bc6dc);
  raceEnvironment.forEach((obj) => { obj.visible = !lab; });
  racers.forEach((r) => { r.obj.visible = !lab && !tactical; });
  ring.visible = !lab && !tactical;
  tacticalMarkers.forEach((marker) => { marker.visible = tactical; });
  labGroup.visible = lab;
  labFloor.visible = lab;
  document.querySelector(".hud-race").hidden = lab;
  document.querySelector(".hud-mini").hidden = lab;
  document.querySelector("#morphSwitcher").hidden = !lab;
  document.querySelector("#labLabel").hidden = !lab;

  if (lab) {
    camera.up.set(0, 1, 0);
    camera.position.lerp(new THREE.Vector3(0, 2.7, isMobile ? 12.5 : 11.5), 0.20);
    camera.lookAt(0, 1.25, 0);
  } else if (view === "follow") {
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
  camera.fov = isMobile ? (view === "lab" ? 44 : view === "tactical" ? 50 : view === "follow" ? 54 : 50) : 42;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

function resetRace() {
  racers.forEach((r, i) => {
    r.distance = Math.max(0, (17 - i) * 1.1);
    r.lane = i % laneCount;
    r.laneF = i % laneCount;
    r.stamina = 100;
    r.speed = 0;
    r.cooldown = 0;
    r.decision = "START";
    r.command = "BUILD SPEED";

    const t = (r.distance / raceMeters) % 1;
    const p = curve.getPointAt(t);
    const tangent = curve.getTangentAt(t).normalize();
    const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    r.obj.position.copy(p.clone().addScaledVector(side, laneOffset(r.laneF)));
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
    const rawFrameMs = Math.max(0, now - last);
    const dt = Math.min(45, rawFrameMs);
    last = now;
    update(dt);
    if (!paused) {
      const animationDt = dt / 1000;
      if (sf3dLabMixer) sf3dLabMixer.update(animationDt);
      syncHunyuanStrideToSpeed();
      for (const mixer of sf3dRaceMixers) mixer.update(animationDt);
    }
    setCamera();
    updateRaceStressInstances();
    updateHunyuanRacePackInstances();
    renderer.render(scene, camera);
    sampleSf3dBenchmark(now, rawFrameMs);
    sampleRaceLodBenchmark(now, rawFrameMs);
    sampleRaceStress(now, rawFrameMs);
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
      view === "lab" ? "MORPH LAB" : view === "race" ? "RACE VIEW" : view === "follow" ? "FOLLOW VIEW" : "TACTICAL VIEW";
    document.querySelectorAll("[data-view]").forEach((b) => b.classList.toggle("active", b === button));
  });
});

document.querySelectorAll("[data-morph]").forEach((button) => {
  button.addEventListener("click", () => {
    setLabMorph(button.dataset.morph);
  });
});

document.querySelector("#pause").addEventListener("click", (event) => {
  paused = !paused;
  event.currentTarget.textContent = paused ? "Resume" : "Pause";
});

document.querySelector("#reset").addEventListener("click", resetRace);
