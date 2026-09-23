import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { MTLLoader } from "three/addons/loaders/MTLLoader.js";
import "./styles.css";

const canvas = document.querySelector("#game");
const stage = document.querySelector("#stage");
const isMobile = matchMedia("(pointer: coarse)").matches || innerWidth < 800;
const proofMode = new URLSearchParams(location.search).get("proof");
const sRunIsolatedProof = proofMode === "s-run";
const pRigIsolatedProof = proofMode === "p-rig";
const isolatedProof = sRunIsolatedProof || pRigIsolatedProof;
const isolatedProofRacerId = pRigIsolatedProof ? 2 : 1;
const fastFinishProof = proofMode === "finish";
if (pRigIsolatedProof) document.body.classList.add("p-rig-proof");
const raceBanner = document.querySelector("#raceBanner");
const resultsPanel = document.querySelector("#resultsPanel");
const resultsList = document.querySelector("#resultsList");
const resultHeadline = document.querySelector("#resultHeadline");

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
  renderer.setPixelRatio(isMobile ? Math.min(devicePixelRatio, 1.5) : Math.min(devicePixelRatio, 1.25));
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

  function makeRibbon(ribbonHalf, y, material) {
    const vertices = [];
    const normals = [];
    const indices = [];

    for (let i = 0; i <= samples; i++) {
      const t = i / samples;
      const p = curve.getPointAt(t);
      const tangent = curve.getTangentAt(t).normalize();
      const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();

      for (const offset of [-ribbonHalf, ribbonHalf]) {
        const q = p.clone().addScaledVector(side, offset);
        vertices.push(q.x, y, q.z);
        normals.push(0, 1, 0);
      }
    }

    for (let i = 0; i < samples; i++) {
      const a = i * 2;
      const b = a + 1;
      const c = a + 2;
      const d = a + 3;
      indices.push(a, b, c, b, d, c);
    }

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices, 3));
    geometry.setAttribute("normal", new THREE.Float32BufferAttribute(normals, 3));
    geometry.setIndex(indices);
    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);
    return mesh;
  }

  makeRibbon(
    half + 0.72,
    0.015,
    new THREE.MeshStandardMaterial({ color: 0x765c40, roughness: 1 })
  );
  makeRibbon(
    half,
    0.035,
    new THREE.MeshStandardMaterial({ color: 0xb88758, roughness: 1 })
  );

  for (const offset of [-half, half]) {
    const points = [];
    for (let i = 0; i <= samples; i++) {
      const t = i / samples;
      const p = curve.getPointAt(t);
      const tangent = curve.getTangentAt(t).normalize();
      const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
      points.push(p.clone().addScaledVector(side, offset).add(new THREE.Vector3(0, 0.07, 0)));
    }
    scene.add(
      new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(points),
        new THREE.LineBasicMaterial({ color: 0xf2dfbd })
      )
    );
  }

  const laneGuideOffsets = [-3.10, -1.55, 0, 1.55, 3.10];
  const laneGuideMaterial = new THREE.LineDashedMaterial({
    color: 0xf1d8b5,
    transparent: true,
    opacity: 0.28,
    dashSize: 0.72,
    gapSize: 0.88
  });
  for (const offset of laneGuideOffsets) {
    const points = [];
    for (let i = 0; i <= samples; i++) {
      const t = i / samples;
      const p = curve.getPointAt(t);
      const tangent = curve.getTangentAt(t).normalize();
      const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
      points.push(p.clone().addScaledVector(side, offset).add(new THREE.Vector3(0, 0.075, 0)));
    }
    const guide = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(points),
      laneGuideMaterial
    );
    guide.computeLineDistances();
    scene.add(guide);
  }

  const railOffset = half + 0.78;
  const railMaterial = new THREE.LineBasicMaterial({ color: 0xd8dee2, transparent: true, opacity: 0.95 });
  for (const offset of [-railOffset, railOffset]) {
    for (const y of [0.52, 0.88]) {
      const points = [];
      for (let i = 0; i <= samples; i++) {
        const t = i / samples;
        const p = curve.getPointAt(t);
        const tangent = curve.getTangentAt(t).normalize();
        const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
        points.push(p.clone().addScaledVector(side, offset).add(new THREE.Vector3(0, y, 0)));
      }
      scene.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(points), railMaterial));
    }
  }

  const postsPerSide = isMobile ? 28 : 42;
  const postGeometry = new THREE.BoxGeometry(0.11, 0.92, 0.11);
  const postMaterial = new THREE.MeshStandardMaterial({ color: 0xd1d7da, roughness: 0.78 });
  const posts = new THREE.InstancedMesh(postGeometry, postMaterial, postsPerSide * 2);
  const postDummy = new THREE.Object3D();
  let postIndex = 0;
  for (const offset of [-railOffset, railOffset]) {
    for (let i = 0; i < postsPerSide; i++) {
      const t = i / postsPerSide;
      const p = curve.getPointAt(t);
      const tangent = curve.getTangentAt(t).normalize();
      const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
      const q = p.clone().addScaledVector(side, offset);
      postDummy.position.set(q.x, 0.46, q.z);
      postDummy.rotation.set(0, Math.atan2(-tangent.z, tangent.x), 0);
      postDummy.updateMatrix();
      posts.setMatrixAt(postIndex++, postDummy.matrix);
    }
  }
  posts.instanceMatrix.needsUpdate = true;
  scene.add(posts);

  const streakCount = isMobile ? 72 : 120;
  const streakGeometry = new THREE.BoxGeometry(1.25, 0.018, 0.065);
  const streakMaterial = new THREE.MeshBasicMaterial({ color: 0x8f6848, transparent: true, opacity: 0.42 });
  const streaks = new THREE.InstancedMesh(streakGeometry, streakMaterial, streakCount);
  const streakDummy = new THREE.Object3D();
  for (let i = 0; i < streakCount; i++) {
    const t = (i + 0.35) / streakCount;
    const p = curve.getPointAt(t);
    const tangent = curve.getTangentAt(t).normalize();
    const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
    const lateral = Math.sin(i * 12.731) * 4.75;
    const q = p.clone().addScaledVector(side, lateral);
    streakDummy.position.set(q.x, 0.055, q.z);
    streakDummy.rotation.set(0, Math.atan2(-tangent.z, tangent.x), 0);
    streakDummy.scale.set(0.65 + (i % 5) * 0.12, 1, 1);
    streakDummy.updateMatrix();
    streaks.setMatrixAt(i, streakDummy.matrix);
  }
  streaks.instanceMatrix.needsUpdate = true;
  scene.add(streaks);

  const startT = 0.012;
  const startPoint = curve.getPointAt(startT);
  const startTangent = curve.getTangentAt(startT).normalize();
  const startYaw = Math.atan2(-startTangent.z, startTangent.x);
  const gantry = new THREE.Group();
  gantry.position.copy(startPoint);
  gantry.rotation.y = startYaw;

  const gantryMat = new THREE.MeshStandardMaterial({ color: 0x263746, roughness: 0.58, metalness: 0.10 });
  const gantryAccent = new THREE.MeshBasicMaterial({ color: 0x63d9ff });
  for (const z of [-6.45, 6.45]) {
    const upright = new THREE.Mesh(new THREE.BoxGeometry(0.30, 4.2, 0.30), gantryMat);
    upright.position.set(0, 2.1, z);
    gantry.add(upright);
  }
  const beam = new THREE.Mesh(new THREE.BoxGeometry(0.34, 0.34, 13.2), gantryMat);
  beam.position.y = 4.05;
  gantry.add(beam);
  const sign = new THREE.Mesh(new THREE.BoxGeometry(0.38, 0.82, 4.6), gantryMat);
  sign.position.y = 4.08;
  gantry.add(sign);
  const accent = new THREE.Mesh(new THREE.BoxGeometry(0.40, 0.08, 3.55), gantryAccent);
  accent.position.set(-0.02, 4.08, 0.22);
  gantry.add(accent);
  scene.add(gantry);

  const startLine = new THREE.Mesh(
    new THREE.BoxGeometry(0.22, 0.026, 11.1),
    new THREE.MeshBasicMaterial({ color: 0xf3eee4 })
  );
  startLine.position.copy(startPoint);
  startLine.position.y = 0.065;
  startLine.rotation.y = startYaw;
  scene.add(startLine);

  stage.dataset.trackPresentation = "v5";
}
buildTrack();

const speedMarkerGeometry = new THREE.BoxGeometry(1.05, 0.08, 0.16);
const speedMarkerMaterial = new THREE.MeshBasicMaterial({ color: 0xf4e8cf });
for (let i = 0; i < 72; i++) {
  const t = i / 72;
  const p = curve.getPointAt(t);
  const tangent = curve.getTangentAt(t).normalize();
  const side = new THREE.Vector3(-tangent.z, 0, tangent.x).normalize();
  const yaw = Math.atan2(-tangent.z, tangent.x);
  for (const offset of [-5.25, 5.25]) {
    const marker = new THREE.Mesh(speedMarkerGeometry, speedMarkerMaterial);
    marker.position.copy(p.clone().addScaledVector(side, offset));
    marker.position.y = 0.085;
    marker.rotation.y = yaw;
    scene.add(marker);
  }
}

const hillMaterial = new THREE.MeshStandardMaterial({ color: 0x697d70, roughness: 1, flatShading: true });
const hillGeometry = new THREE.SphereGeometry(1, 12, 5, 0, Math.PI * 2, 0, Math.PI / 2);
function addHill(x, z, s) {
  const hillScale = s * (isMobile ? 0.44 : 1);
  const lobes = [
    [0.00, 0.00, 1.05, 0.34, 0.76],
    [-0.52, 0.10, 0.72, 0.29, 0.60],
    [0.48, -0.08, 0.64, 0.26, 0.55]
  ];
  for (const [ox, oz, sx, sy, sz] of lobes) {
    const hill = new THREE.Mesh(hillGeometry, hillMaterial);
    hill.position.set(
      x + ox * hillScale * 0.72,
      0,
      z + oz * hillScale * 0.72
    );
    hill.scale.set(hillScale * sx, hillScale * sy, hillScale * sz);
    scene.add(hill);
  }
}
addHill(-60, -34, 11);
addHill(58, -33, 13);
addHill(-62, 30, 9);

const trunkMat = new THREE.MeshStandardMaterial({ color: 0x5a4432, roughness: 1 });
const leafMat = new THREE.MeshStandardMaterial({ color: 0x3f6542, roughness: 1, flatShading: true });
function addTree(x, z, s = 0.85) {
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 1.4, 6), trunkMat);
  trunk.position.set(x, 0.7, z);
  const lower = new THREE.Mesh(new THREE.ConeGeometry(0.82, 1.85, 8), leafMat);
  lower.position.set(x, 1.72, z);
  lower.scale.setScalar(s);
  const upper = new THREE.Mesh(new THREE.ConeGeometry(0.62, 1.55, 8), leafMat);
  upper.position.set(x, 2.45, z);
  upper.scale.setScalar(s * 0.88);
  scene.add(trunk, lower, upper);
}
for (let i = 0; i < 22; i++) {
  const a = (i / 22) * Math.PI * 2;
  const r = 49 + (i % 3) * 2;
  addTree(Math.cos(a) * r, Math.sin(a) * r * 0.68, 0.74 + (i % 4) * 0.05);
}

const standGroup = new THREE.Group();
standGroup.position.set(7, 0, -34.2);
standGroup.rotation.y = -0.03;
const standMat = new THREE.MeshStandardMaterial({ color: 0x596773, roughness: 0.92 });
const seatMat = new THREE.MeshBasicMaterial({ color: 0x8ea0ad });
for (let i = 0; i < 4; i++) {
  const tier = new THREE.Mesh(new THREE.BoxGeometry(15.8 - i * 0.55, 0.42, 1.32), standMat);
  tier.position.set(0, 0.22 + i * 0.43, i * 0.58);
  standGroup.add(tier);
  const row = new THREE.Mesh(new THREE.BoxGeometry(14.7 - i * 0.50, 0.07, 0.10), seatMat);
  row.position.set(0, 0.46 + i * 0.43, i * 0.58 - 0.22);
  standGroup.add(row);
}
const canopy = new THREE.Mesh(new THREE.BoxGeometry(16.8, 0.22, 2.15), standMat);
canopy.position.set(0, 2.35, 2.15);
canopy.rotation.x = -0.12;
standGroup.add(canopy);
scene.add(standGroup);

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

const agentPolicyTemplates = [
  {
    key: "BALANCED",
    label: "Balanced",
    preserveAt: 18,
    overtakeGap: 4.2,
    laneCooldown: 900,
    finalBoost: 1.040,
    advanceAt: 12,
    advanceBoost: 1.012,
    startBias: 1.000,
    midBias: 1.000,
    buildBias: 1.000
  },
  {
    key: "PRESSURE",
    label: "Pressure",
    preserveAt: 14,
    overtakeGap: 5.4,
    laneCooldown: 720,
    finalBoost: 1.060,
    advanceAt: 10,
    advanceBoost: 1.020,
    startBias: 1.010,
    midBias: 1.006,
    buildBias: 1.010
  },
  {
    key: "RESERVE",
    label: "Reserve",
    preserveAt: 27,
    overtakeGap: 3.5,
    laneCooldown: 1120,
    finalBoost: 1.085,
    advanceAt: 14,
    advanceBoost: 1.008,
    startBias: 0.982,
    midBias: 0.992,
    buildBias: 1.005
  },
  {
    key: "OPPORTUNIST",
    label: "Opportunist",
    preserveAt: 20,
    overtakeGap: 6.2,
    laneCooldown: 640,
    finalBoost: 1.050,
    advanceAt: 11,
    advanceBoost: 1.016,
    startBias: 0.996,
    midBias: 1.008,
    buildBias: 1.012
  }
];
const agentNames = [
  "Vela", "Flux", "Morrow", "Kite", "Slate", "Nix",
  "Pace", "Rook", "Aero", "Lumen", "Drift", "Cairn",
  "Vale", "Arc", "Mica", "Sable", "Rill", "Nova"
];
const agentPolicyByKey = (key) => agentPolicyTemplates.find((policy) => policy.key === key) ?? null;

// Gameplay-proof tuning only: compatibility is intentionally small so it matters
// without overriding the creature's own morph, speed, fatigue, traffic, and lane state.
const agentCreatureCompatibility = {
  BALANCED:    { S: 1.000, P: 1.000, E: 1.000, A: 1.000 },
  PRESSURE:    { S: 1.030, P: 1.020, E: 0.970, A: 1.000 },
  RESERVE:     { S: 0.980, P: 0.990, E: 1.030, A: 1.010 },
  OPPORTUNIST: { S: 1.010, P: 1.000, E: 1.000, A: 1.030 }
};

function compatibilityFor(racer) {
  if (!racer?.agent?.policy) return 1;
  return agentCreatureCompatibility[racer.agent.policy.key]?.[racer.morph] ?? 1;
}

function compatibilityScoreFor(racer) {
  return Math.round(compatibilityFor(racer) * 100);
}

const racers = [];
let selectedId = pRigIsolatedProof ? 2 : 1;
const sRunProofRacerId = 1;
const raceMeters = fastFinishProof ? 45 : 700;
const countdownDuration = fastFinishProof ? 1200 : 3000;
document.querySelector(".hud-race strong").textContent = `${raceMeters}m — Ridge Oval`;
stage.dataset.raceDistance = String(raceMeters);
const laneCount = 6;
const laneSpacing = 1.55;
const laneOffset = (lane) => (lane - (laneCount - 1) / 2) * laneSpacing;

for (let i = 0; i < 18; i++) {
  const morph = i === 5 ? "A" : morphCycle[i % 4];
  const obj = buildMorph(i, morph);
  obj.scale.setScalar(isMobile ? 1.02 : 0.88);
  scene.add(obj);

  const stats = morphStats[morph];
  const agentTemplate = agentPolicyTemplates[i % agentPolicyTemplates.length];
  const agent = {
    id: `AG-${String(i + 1).padStart(3, "0")}`,
    name: agentNames[i],
    versionNumber: 1,
    version: "v1",
    policy: { ...agentTemplate },
    pendingPolicyKey: null,
    versionHistory: [{ version: "v1", profile: agentTemplate.key }],
    raceHistory: []
  };
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
    agent,
    decision: "START",
    command: "BUILD SPEED",
    cooldown: 0,
    dustTimer: 0,
    finished: false,
    finishPlace: null,
    finishTime: null,
    agentLog: [],
    agentStats: {
      decisions: 0,
      success: 0,
      partial: 0,
      failed: 0,
      laneMoves: 0
    },
    lastAgentLogSignature: null,
    color: "#" + palette[i].toString(16).padStart(6, "0")
  });
}

let selected = racers[selectedId - 1];
const ring = new THREE.Mesh(
  new THREE.RingGeometry(1.15, 1.28, 36),
  new THREE.MeshBasicMaterial({ color: 0x6bb1ff, side: THREE.DoubleSide, transparent: true, opacity: 0.9 })
);
ring.rotation.x = -Math.PI / 2;
scene.add(ring);

const agentOrbGeometry = new THREE.SphereGeometry(0.075, 8, 6);
const agentOrbs = racers.map((r) => {
  const orb = new THREE.Mesh(
    agentOrbGeometry,
    new THREE.MeshBasicMaterial({
      color: 0x76e59b,
      transparent: true,
      opacity: r.id === selectedId ? 0.86 : 0.16,
      depthWrite: false
    })
  );
  orb.renderOrder = 8;
  scene.add(orb);
  return orb;
});
const agentOrbTravelTangent = new THREE.Vector3();

const agentCommandColors = {
  "BUILD SPEED": 0x76e59b,
  "MAINTAIN": 0x6bdcff,
  "PUSH": 0xffbd68,
  "EASE": 0x7db9ff,
  "WAIT": 0x98a6b2,
  "MOVE INSIDE": 0xd28cff,
  "MOVE OUTSIDE": 0xd28cff
};
let lastAgentCommand = "";
let lastAgentRacerId = null;
let agentPulseUntil = 0;
let agentToastUntil = 0;
const agentToastWorld = new THREE.Vector3();

function creatureResponseFor(racer) {
  if (!racer) return { state: "FAILED", reason: "No selected creature" };
  if (racer.finished) {
    return { state: "FINISHED", reason: `Result fixed at place #${racer.finishPlace}` };
  }
  if (raceState === "countdown") {
    return { state: "READY", reason: "Waiting for the start signal" };
  }
  if (racer.decision === "BLOCKED") {
    return { state: "FAILED", reason: "No safe path available for the requested move" };
  }
  if (Math.abs(racer.laneF - racer.lane) > 0.12) {
    return { state: "PARTIAL", reason: `Lane change in progress toward lane ${racer.lane + 1}` };
  }
  if (racer.stamina < 18) {
    const fatigue = 100 - racer.stamina;
    return { state: "PARTIAL", reason: `High fatigue reduces output (${Math.round(fatigue)}%)` };
  }
  if (racer.command === "PUSH" && racer.speed < racer.cruise * 0.98) {
    return { state: "PARTIAL", reason: "Acceleration/output limits reduce the push response" };
  }
  if (racer.command === "EASE") {
    return { state: "SUCCESS", reason: "Pace reduced to preserve energy" };
  }
  if (racer.command === "WAIT") {
    return { state: "SUCCESS", reason: "Position held while waiting for space" };
  }
  const compatibility = compatibilityFor(racer);
  if (compatibility < 0.985 && ["PUSH", "BUILD SPEED", "MOVE INSIDE", "MOVE OUTSIDE"].includes(racer.command)) {
    return {
      state: "PARTIAL",
      reason: `Agent profile / ${racer.morph} compatibility limits execution (${compatibilityScoreFor(racer)}%)`
    };
  }
  return { state: "SUCCESS", reason: `${racer.command} executed within current capability` };
}

function creatureStateFor(racer) {
  if (!racer) {
    return {
      output: 0,
      condition: "UNKNOWN",
      traffic: "UNKNOWN",
      laneState: "UNKNOWN",
      execution: "FAILED",
      note: "No selected creature."
    };
  }

  const response = creatureResponseFor(racer);
  const fatigue = THREE.MathUtils.clamp(100 - racer.stamina, 0, 100);
  const output = THREE.MathUtils.clamp((racer.speed / Math.max(0.1, racer.cruise)) * 100, 0, 125);
  const gap = gapAhead(racer);
  const laneDelta = Math.abs(racer.laneF - racer.lane);

  const condition = racer.finished
    ? "FINISHED"
    : fatigue >= 85
      ? "STRAINED"
      : fatigue >= 60
        ? "TIRING"
        : fatigue >= 30
          ? "WORKING"
          : "FRESH";

  const traffic = racer.finished
    ? "CLEAR"
    : racer.decision === "BLOCKED" || gap < 2.5
      ? "BLOCKED"
      : gap < 5
        ? "TIGHT"
        : gap < 9
          ? "NEAR"
          : "CLEAR";

  const laneState = racer.finished
    ? "STOPPED"
    : laneDelta > 0.12
      ? `CHANGING → ${racer.lane + 1}`
      : `STABLE ${Math.round(racer.laneF) + 1}`;

  let note = response.reason;
  if (raceState === "running" && response.state === "SUCCESS") {
    if (traffic === "TIGHT") note = "Command is executing, but nearby traffic limits available space.";
    else if (condition === "TIRING") note = "Command is executing while fatigue is beginning to reduce reserve.";
    else if (condition === "STRAINED") note = "Command is executing under severe fatigue constraint.";
  }

  return {
    output: Math.round(output),
    condition,
    traffic,
    laneState,
    execution: response.state,
    note
  };
}

function updateCreatureStateVisual() {
  const state = creatureStateFor(selected);
  const outputEl = document.querySelector("#stateOutput");
  const conditionEl = document.querySelector("#stateCondition");
  const trafficEl = document.querySelector("#stateTraffic");
  const laneEl = document.querySelector("#stateLane");
  const executionEl = document.querySelector("#stateExecution");
  const noteEl = document.querySelector("#stateNote");

  if (outputEl) outputEl.textContent = `${state.output}%`;
  if (conditionEl) conditionEl.textContent = state.condition;
  if (trafficEl) trafficEl.textContent = state.traffic;
  if (laneEl) laneEl.textContent = state.laneState;
  if (executionEl) {
    executionEl.textContent = state.execution;
    executionEl.className = state.execution.toLowerCase();
  }
  if (noteEl) noteEl.textContent = state.note;

  conditionEl?.classList.toggle("warn", state.condition === "TIRING");
  conditionEl?.classList.toggle("critical", state.condition === "STRAINED");
  trafficEl?.classList.toggle("warn", state.traffic === "TIGHT");
  trafficEl?.classList.toggle("critical", state.traffic === "BLOCKED");

  stage.dataset.creatureState = "active";
  stage.dataset.creatureCondition = state.condition;
  stage.dataset.creatureTraffic = state.traffic;
  stage.dataset.creatureExecution = state.execution;
  stage.dataset.creatureOutput = String(state.output);
}

function recordAgentEvent(racer, force = false) {
  if (!racer || (raceState !== "running" && !racer.finished)) return;
  const response = creatureResponseFor(racer);
  const signature = `${racer.decision}|${racer.command}|${response.state}`;
  if (!force && racer.lastAgentLogSignature === signature) return;

  racer.lastAgentLogSignature = signature;
  racer.agentStats.decisions += 1;
  if (response.state === "SUCCESS") racer.agentStats.success += 1;
  else if (response.state === "PARTIAL") racer.agentStats.partial += 1;
  else if (response.state === "FAILED") racer.agentStats.failed += 1;
  if (racer.command === "MOVE INSIDE" || racer.command === "MOVE OUTSIDE") {
    racer.agentStats.laneMoves += 1;
  }

  racer.agentLog.push({
    time: elapsed,
    phase: phase(racer),
    agentId: racer.agent.id,
    agentProfile: racer.agent.policy.key,
    decision: racer.decision,
    order: racer.command,
    result: response.state,
    reason: response.reason,
    fatigue: Math.round(100 - racer.stamina),
    position: rankOf(racer)
  });
  if (racer.agentLog.length > 10) racer.agentLog.shift();

  if (racer.id === selectedId) {
    stage.dataset.agentLogEvents = String(racer.agentLog.length);
  }
}

function updateAgentVisual(now) {
  const panel = document.querySelector("#agentPanel");
  const identityEl = document.querySelector("#agentIdentity");
  const profileEl = document.querySelector("#agentProfile");
  const compatibilityEl = document.querySelector("#agentCompatibility");
  const recordEl = document.querySelector("#agentRecord");
  const policyRuleEl = document.querySelector("#agentPolicyRule");
  const orderEl = document.querySelector("#agentOrder");
  const responseEl = document.querySelector("#creatureResponse");
  const fatigueEl = document.querySelector("#agentFatigue");
  const reasonEl = document.querySelector("#creatureReason");
  const order = selected?.command || "WAIT";
  const response = creatureResponseFor(selected);

  if (selected && (lastAgentRacerId !== selected.id || lastAgentCommand !== order)) {
    lastAgentRacerId = selected.id;
    lastAgentCommand = order;
    agentPulseUntil = now + 420;
    agentToastUntil = now + 1050;

    const toastOrder = document.querySelector("#agentToastOrder");
    const toastResult = document.querySelector("#agentToastResult");
    if (toastOrder) toastOrder.textContent = order;
    if (toastResult) toastResult.textContent = response.state;
  }

  if (identityEl && selected?.agent) identityEl.textContent = `${selected.agent.id} ${selected.agent.name} / ${selected.agent.version}`;
  if (profileEl && selected?.agent) profileEl.textContent = selected.agent.policy.label.toUpperCase();
  if (compatibilityEl && selected?.agent) compatibilityEl.textContent = `${compatibilityScoreFor(selected)}%`;
  if (recordEl && selected?.agent) {
    const history = selected.agent.raceHistory;
    const starts = history.length;
    const wins = history.filter((race) => race.place === 1).length;
    const best = starts ? Math.min(...history.map((race) => race.place)) : null;
    recordEl.textContent = starts ? `${starts}S / ${wins}W / BEST #${best}` : "NO STARTS";
  }
  if (policyRuleEl && selected?.agent) {
    const p = selected.agent.policy;
    policyRuleEl.textContent = `PASS ${p.overtakeGap.toFixed(1)}m · PRESERVE ${p.preserveAt} · FINAL ×${p.finalBoost.toFixed(3)} · LANE ${p.laneCooldown}ms`;
  }
  if (orderEl) orderEl.textContent = order;
  if (responseEl) responseEl.textContent = response.state;
  if (fatigueEl) fatigueEl.textContent = `${Math.round(100 - (selected?.stamina ?? 100))}%`;
  if (reasonEl) reasonEl.textContent = response.reason;
  if (panel) panel.classList.toggle("pulse", now < agentPulseUntil);
  updateCreatureStateVisual();

  const showWorldSignal = view !== "lab" && view !== "tactical";
  agentOrbs.forEach((orb, index) => {
    const racer = racers[index];
    const t = (racer.distance / raceMeters) % 1;
    agentOrbTravelTangent.copy(curve.getTangentAt(t)).normalize();
    orb.position.copy(racer.obj.position).addScaledVector(agentOrbTravelTangent, -0.20);
    orb.position.y += 1.05;

    const racerOrder = racer.command || "WAIT";
    orb.material.color.setHex(agentCommandColors[racerOrder] ?? 0x6bdcff);
    const isSelected = racer.id === selectedId;
    orb.material.opacity = isSelected ? 0.86 : 0.16;
    const pulse = isSelected
      ? (now < agentPulseUntil ? 1.28 : 1 + Math.sin(now * 0.008) * 0.06)
      : 0.58 + Math.sin(now * 0.004 + racer.id) * 0.025;
    orb.scale.setScalar(pulse);
    orb.visible = showWorldSignal && (!isolatedProof || racer.id === isolatedProofRacerId);
  });

  const toast = document.querySelector("#agentToast");
  if (toast && selected && showWorldSignal && now < agentToastUntil) {
    agentToastWorld.copy(selected.obj.position);
    agentToastWorld.y += 1.45;
    agentToastWorld.project(camera);
    toast.style.left = `${(agentToastWorld.x * 0.5 + 0.5) * 100}%`;
    toast.style.top = `${(-agentToastWorld.y * 0.5 + 0.5) * 100}%`;
    toast.hidden = false;
  } else if (toast) {
    toast.hidden = true;
  }
  stage.dataset.agentVisual = "enabled";
  stage.dataset.agentToast = "enabled";
  stage.dataset.agentOrbCount = String(agentOrbs.length);
  stage.dataset.agentSelectedId = String(selectedId);
  stage.dataset.agentIdentity = selected?.agent?.id || "";
  stage.dataset.agentProfile = selected?.agent?.policy?.key || "";
  stage.dataset.agentCompatibility = String(compatibilityScoreFor(selected));
  stage.dataset.agentVersion = selected?.agent?.version || "";
  stage.dataset.agentStarts = String(selected?.agent?.raceHistory?.length ?? 0);
  if (selected?.agent?.policy) {
    const p = selected.agent.policy;
    stage.dataset.agentPolicy = `${p.overtakeGap.toFixed(1)}|${p.preserveAt}|${p.finalBoost.toFixed(3)}|${p.laneCooldown}`;
  }
  stage.dataset.agentOrder = order;
  stage.dataset.creatureResponse = response.state;
}

const tacticalMarkerGeometry = new THREE.CircleGeometry(0.88, 18);
const tacticalMarkers = racers.map((r) => {
  const marker = new THREE.Mesh(
    tacticalMarkerGeometry,
    new THREE.MeshBasicMaterial({
      color: r.id === selectedId ? 0xffffff : palette[r.id - 1],
      transparent: true,
      opacity: r.id === selectedId ? 1 : 0.9,
      depthTest: false,
      fog: false
    })
  );
  marker.rotation.x = -Math.PI / 2;
  marker.scale.setScalar(r.id === selectedId ? 1.42 : 1);
  marker.visible = false;
  marker.renderOrder = 10;
  scene.add(marker);
  return marker;
});

function setSelectedRacer(id) {
  const next = racers.find((r) => r.id === id);
  if (!next) return;

  selectedId = next.id;
  selected = next;
  stage.dataset.selectedRacer = String(selectedId);

  const selectedName = document.querySelector("#selectedName");
  const selectedTitle = document.querySelector("#selectedTitle");
  if (selectedName) selectedName.textContent = `#${String(selected.id).padStart(2, "0")} ${selected.name}`;
  if (selectedTitle) selectedTitle.textContent = `Selected #${String(selected.id).padStart(2, "0")}`;

  tacticalMarkers.forEach((marker, index) => {
    const racer = racers[index];
    const isSelected = racer.id === selectedId;
    marker.material.color.set(isSelected ? 0xffffff : palette[index]);
    marker.material.opacity = isSelected ? 1 : 0.9;
    marker.scale.setScalar(isSelected ? 1.42 : 1);
    const shadow = racerShadows[index];
    if (shadow) shadow.material.opacity = isSelected ? 0.30 : 0.20;
  });

  ring.position.set(selected.obj.position.x, 0.08, selected.obj.position.z);
  lastRankingPaint = -Infinity;
  updateAgentSetupUi();
}

function updateAgentSetupUi() {
  if (!selected?.agent) return;
  const activeKey = selected.agent.policy.key;
  const pendingKey = selected.agent.pendingPolicyKey;

  document.querySelectorAll("[data-agent-policy]").forEach((button) => {
    const key = button.dataset.agentPolicy;
    button.classList.toggle("active", key === activeKey);
    button.classList.toggle("pending", key === pendingKey);
  });

  const status = document.querySelector("#agentSetupStatus");
  if (status) {
    status.textContent = pendingKey
      ? `Active ${activeKey} · ${selected.agent.version} → NEXT ${pendingKey}`
      : `Active ${activeKey} · ${selected.agent.version}`;
  }

  stage.dataset.agentPendingProfile = pendingKey || "";
  stage.dataset.agentVersionHistory = String(selected.agent.versionHistory.length);
}

document.querySelector("#agentProfileButtons")?.addEventListener("click", (event) => {
  const button = event.target.closest("[data-agent-policy]");
  if (!button || !selected?.agent) return;
  const key = button.dataset.agentPolicy;
  if (!agentPolicyByKey(key)) return;

  selected.agent.pendingPolicyKey = key === selected.agent.policy.key ? null : key;
  updateAgentSetupUi();
});

const rankingPanel = document.querySelector("#ranking");
rankingPanel.addEventListener("click", (event) => {
  const row = event.target.closest("[data-racer-id]");
  if (!row) return;
  const id = Number(row.dataset.racerId);
  if (!Number.isInteger(id)) return;
  setSelectedRacer(id);
});
rankingPanel.addEventListener("keydown", (event) => {
  if (event.key !== "Enter" && event.key !== " ") return;
  const row = event.target.closest("[data-racer-id]");
  if (!row) return;
  event.preventDefault();
  const id = Number(row.dataset.racerId);
  if (Number.isInteger(id)) setSelectedRacer(id);
});
stage.dataset.selectedRacer = String(selectedId);
let lastRankingPaint = -Infinity;
updateAgentSetupUi();

const shadowGeometry = new THREE.CircleGeometry(0.78, 20);
const racerShadows = racers.map((r) => {
  const shadow = new THREE.Mesh(
    shadowGeometry,
    new THREE.MeshBasicMaterial({
      color: 0x17202a,
      transparent: true,
      opacity: r.id === selectedId ? 0.30 : 0.20,
      depthWrite: false,
      fog: false
    })
  );
  shadow.rotation.x = -Math.PI / 2;
  shadow.scale.set(1.55, 0.62, 1);
  shadow.position.y = 0.055;
  shadow.renderOrder = 1;
  scene.add(shadow);
  return shadow;
});

const dustCanvas = document.createElement("canvas");
dustCanvas.width = 64;
dustCanvas.height = 64;
const dustCtx = dustCanvas.getContext("2d");
const dustGradient = dustCtx.createRadialGradient(32, 32, 2, 32, 32, 30);
dustGradient.addColorStop(0, "rgba(232,214,184,0.72)");
dustGradient.addColorStop(0.45, "rgba(211,185,150,0.34)");
dustGradient.addColorStop(1, "rgba(190,160,125,0)");
dustCtx.fillStyle = dustGradient;
dustCtx.fillRect(0, 0, 64, 64);
const dustTexture = new THREE.CanvasTexture(dustCanvas);
dustTexture.colorSpace = THREE.SRGBColorSpace;

const dustPool = Array.from({ length: isMobile ? 30 : 48 }, () => {
  const sprite = new THREE.Sprite(new THREE.SpriteMaterial({
    map: dustTexture,
    transparent: true,
    opacity: 0,
    depthWrite: false,
    fog: true
  }));
  sprite.visible = false;
  sprite.renderOrder = 2;
  scene.add(sprite);
  return { sprite, life: 0, maxLife: 1, rise: 0 };
});
let dustCursor = 0;

function spawnDust(racer, tangent) {
  const puff = dustPool[dustCursor++ % dustPool.length];
  const side = new THREE.Vector3(-tangent.z, 0, tangent.x);
  const jitter = Math.sin(elapsed * 0.004 + racer.id * 2.17);
  puff.life = 420 + (racer.id % 3) * 60;
  puff.maxLife = puff.life;
  puff.rise = 0.00045 + (racer.id % 2) * 0.00012;
  puff.sprite.position.copy(racer.obj.position)
    .addScaledVector(tangent, -0.75)
    .addScaledVector(side, jitter * 0.22);
  puff.sprite.position.y = 0.24;
  const baseScale = racer.id === selectedId ? 0.88 : 0.58;
  puff.sprite.scale.set(baseScale * 1.75, baseScale, 1);
  puff.sprite.material.opacity = racer.id === selectedId ? 0.42 : 0.27;
  puff.sprite.visible = true;
}

function updateDust(dt) {
  const show = view !== "lab" && view !== "tactical";
  for (const puff of dustPool) {
    if (puff.life <= 0) {
      puff.sprite.visible = false;
      continue;
    }
    puff.life -= dt;
    const age = 1 - Math.max(0, puff.life) / puff.maxLife;
    puff.sprite.position.y += dt * puff.rise;
    const scale = 1 + age * 1.45;
    puff.sprite.scale.multiplyScalar(1 + dt * 0.0008);
    puff.sprite.material.opacity = (1 - age) * 0.36;
    puff.sprite.visible = show && puff.life > 0;
  }
}

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

const raceSpriteLayout = {
  S: { scale: [2.85, 2.62], y: 0.15 },
  P: { scale: [3.00, 2.48], y: 0.14 },
  E: { scale: [2.82, 2.52], y: 0.15 },
  A: { scale: [3.05, 2.30], y: 0.08 }
};

const sRunFrames = [
  { phase: "CONTACT", col: 0, row: 0, y: 0.00 },
  { phase: "PUSH",    col: 1, row: 0, y: 0.00 },
  { phase: "LIFT",    col: 2, row: 0, y: 0.00 },
  { phase: "FLIGHT",  col: 0, row: 1, y: -0.42 },
  { phase: "REACH",   col: 1, row: 1, y: -0.17 },
  { phase: "LAND",    col: 2, row: 1, y: -0.16 }
];
const staticMotionFrames = [
  { phase: "CONTACT", y: 0.00, sx: 1.02, sy: 0.98, rot:  0.008 },
  { phase: "PUSH",    y: 0.03, sx: 1.04, sy: 0.96, rot: -0.018 },
  { phase: "LIFT",    y: 0.07, sx: 0.99, sy: 1.02, rot: -0.012 },
  { phase: "FLIGHT",  y: 0.11, sx: 1.00, sy: 1.00, rot:  0.014 },
  { phase: "REACH",   y: 0.06, sx: 1.05, sy: 0.97, rot:  0.020 },
  { phase: "LAND",    y: 0.00, sx: 0.98, sy: 1.03, rot: -0.006 }
];
const staticMotionProfile = {
  P: { strength: 0.58, rate: 0.90 },
  E: { strength: 0.64, rate: 0.98 },
  A: { strength: 0.82, rate: 1.14 }
};
const sRunRacers = [];
let sRunSheetTexture = null;
const pCutoutRigRacerId = 2;
const pCutoutRigRacers = [];
const sBillboardParentQ = new THREE.Quaternion();
const sBillboardCameraQ = new THREE.Quaternion();

const pRigLegDefs = [
  { key: "front-far", x: 0.13, y: 0.40, w: 0.22, h: 0.58, hipX: 0.28, hipY: 0.47, amp: 0.34, phase: Math.PI, z: -0.018 },
  { key: "front-near", x: 0.25, y: 0.43, w: 0.23, h: 0.55, hipX: 0.38, hipY: 0.49, amp: 0.40, phase: 0, z: 0.022 },
  { key: "rear-far", x: 0.52, y: 0.45, w: 0.22, h: 0.53, hipX: 0.63, hipY: 0.49, amp: 0.32, phase: 0, z: -0.014 },
  { key: "rear-near", x: 0.66, y: 0.43, w: 0.24, h: 0.55, hipX: 0.72, hipY: 0.48, amp: 0.38, phase: Math.PI, z: 0.026 }
];
const pRigPoseFrames = [
  { phase: "CONTACT", legs: [-0.22,  0.30,  0.24, -0.28], bodyY: 0.00, lean:  0.000 },
  { phase: "PUSH",    legs: [-0.08,  0.50,  0.10, -0.50], bodyY: 0.025, lean: -0.018 },
  { phase: "LIFT",    legs: [ 0.20,  0.18, -0.22, -0.18], bodyY: 0.075, lean: -0.010 },
  { phase: "FLIGHT",  legs: [ 0.30, -0.18, -0.30,  0.20], bodyY: 0.125, lean:  0.012 },
  { phase: "REACH",   legs: [ 0.44, -0.48, -0.42,  0.46], bodyY: 0.070, lean:  0.020 },
  { phase: "LAND",    legs: [ 0.12, -0.28, -0.12,  0.28], bodyY: 0.015, lean: -0.006 }
];

function buildAnimatedSRunPlane(texture, raceLayout, racerId) {
  const sheet = texture.clone();
  sheet.colorSpace = THREE.SRGBColorSpace;
  sheet.minFilter = THREE.LinearFilter;
  sheet.magFilter = THREE.LinearFilter;
  sheet.generateMipmaps = false;
  sheet.wrapS = THREE.ClampToEdgeWrapping;
  sheet.wrapT = THREE.ClampToEdgeWrapping;
  sheet.repeat.set(1 / 3, 1 / 2);
  sheet.needsUpdate = true;

  const geometry = new THREE.PlaneGeometry(1, 1);
  const material = new THREE.MeshBasicMaterial({
    map: sheet,
    transparent: true,
    depthWrite: false,
    alphaTest: 0.02,
    side: THREE.DoubleSide
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = `Race2_5D_S_SpriteSheet_${racerId}`;
  mesh.position.set(0, raceLayout.y, 0);
  const focusScale = racerId === selectedId ? 1.08 : 0.96;
  mesh.scale.set(3.65 * focusScale, 3.10 * focusScale, 1);
  mesh.renderOrder = 4;
  mesh.frustumCulled = false;
  mesh.userData.frameIndex = -1;
  mesh.userData.baseScaleX = Math.abs(mesh.scale.x);
  mesh.userData.facingSign = 1;
  return mesh;
}

function makeCanvasTexture(canvas) {
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  return texture;
}

function buildPCutoutRig(texture, raceLayout, racerId) {
  const image = texture.image;
  const width = image.naturalWidth || image.width;
  const height = image.naturalHeight || image.height;
  if (!width || !height) return null;

  const rig = new THREE.Group();
  rig.name = `Race2_5D_P_CutoutRig_${racerId}`;
  rig.position.set(0, raceLayout.y, 0);
  rig.userData.baseScaleX = 1;
  rig.userData.motionScaleX = 1;
  rig.userData.facingSign = 1;
  rig.userData.legPivots = [];

  const bodyCanvas = document.createElement("canvas");
  bodyCanvas.width = width;
  bodyCanvas.height = height;
  const bodyCtx = bodyCanvas.getContext("2d");
  bodyCtx.drawImage(image, 0, 0, width, height);

  bodyCtx.save();
  bodyCtx.globalCompositeOperation = "destination-out";
  bodyCtx.globalAlpha = 0.88;
  bodyCtx.fillStyle = "#000";
  for (const def of pRigLegDefs) {
    const x = Math.floor(def.x * width);
    const y = Math.floor(def.y * height);
    const w = Math.ceil(def.w * width);
    const h = Math.ceil(def.h * height);
    const fadeTop = Math.floor(y + h * 0.26);
    bodyCtx.fillRect(x, fadeTop, w, Math.max(1, y + h - fadeTop));
  }
  bodyCtx.restore();

  const body = new THREE.Mesh(
    new THREE.PlaneGeometry(1, 1),
    new THREE.MeshBasicMaterial({
      map: makeCanvasTexture(bodyCanvas),
      transparent: true,
      depthWrite: false,
      alphaTest: 0.02,
      side: THREE.DoubleSide
    })
  );
  body.name = `P_Cutout_Body_${racerId}`;
  body.scale.set(raceLayout.scale[0], raceLayout.scale[1], 1);
  body.position.z = 0;
  body.renderOrder = 4;
  rig.add(body);
  rig.userData.body = body;

  for (const def of pRigLegDefs) {
    const x = Math.floor(def.x * width);
    const y = Math.floor(def.y * height);
    const w = Math.max(1, Math.ceil(def.w * width));
    const h = Math.max(1, Math.ceil(def.h * height));
    const hipX = def.hipX * width;
    const hipY = def.hipY * height;

    const legCanvas = document.createElement("canvas");
    legCanvas.width = w;
    legCanvas.height = h;
    const legCtx = legCanvas.getContext("2d");
    legCtx.drawImage(image, x, y, w, h, 0, 0, w, h);

    const pivot = new THREE.Group();
    pivot.name = `P_Cutout_Pivot_${def.key}_${racerId}`;
    pivot.position.set(
      (def.hipX - 0.5) * raceLayout.scale[0],
      (0.5 - def.hipY) * raceLayout.scale[1],
      def.z
    );

    const leg = new THREE.Mesh(
      new THREE.PlaneGeometry(1, 1),
      new THREE.MeshBasicMaterial({
        map: makeCanvasTexture(legCanvas),
        transparent: true,
        depthWrite: false,
        alphaTest: 0.02,
        side: THREE.DoubleSide
      })
    );
    leg.name = `P_Cutout_Leg_${def.key}_${racerId}`;
    leg.scale.set(
      (w / width) * raceLayout.scale[0],
      (h / height) * raceLayout.scale[1],
      1
    );
    leg.position.set(
      ((x + w / 2 - hipX) / width) * raceLayout.scale[0],
      (-(y + h / 2 - hipY) / height) * raceLayout.scale[1],
      0
    );
    leg.renderOrder = def.z > 0 ? 5 : 3;
    pivot.add(leg);
    pivot.userData.amp = def.amp;
    pivot.userData.phase = def.phase;
    pivot.userData.baseX = pivot.position.x;
    pivot.userData.baseY = pivot.position.y;
    rig.userData.legPivots.push(pivot);
    rig.add(pivot);
  }

  rig.userData.baseY = raceLayout.y;
  return rig;
}

function installPCutoutRigFor(racer, texture) {
  if (!racer || racer.morph !== "P" || racer.obj.userData.pCutoutRig) return;
  const oldSprite = racer.obj.userData.raceSprite;
  if (!oldSprite) return;

  const rig = buildPCutoutRig(texture, raceSpriteLayout.P, racer.id);
  if (!rig) return;

  racer.obj.remove(oldSprite);
  if (oldSprite.material) oldSprite.material.dispose();

  racer.obj.add(rig);
  racer.obj.userData.raceRig = rig;
  racer.obj.userData.raceSprite = rig.userData.body;
  racer.obj.userData.pCutoutRig = true;
  pCutoutRigRacers.push(racer);

  stage.dataset.pCutoutRig = "loaded";
  stage.dataset.pCutoutRacers = String(pCutoutRigRacers.length);
  if (racer.id === pCutoutRigRacerId) stage.dataset.pCutoutRacer = String(racer.id);
}

function applyPCutoutRigMotion(racer, frameIndex) {
  const rig = racer?.obj?.userData?.raceRig;
  if (!rig || !racer.obj.userData.pCutoutRig) return;

  const pose = pRigPoseFrames[frameIndex] ?? pRigPoseFrames[0];
  rig.userData.legPivots.forEach((pivot, index) => {
    pivot.rotation.z = pose.legs[index] ?? 0;
    pivot.position.x = pivot.userData.baseX;
    pivot.position.y = pivot.userData.baseY;
  });

  rig.position.y = rig.userData.baseY + pose.bodyY;
  const body = rig.userData.body;
  if (body) {
    body.position.y = 0;
    body.rotation.z = pose.lean;
  }

  if (racer.id === selectedId) {
    stage.dataset.selectedMotionPhase = pose.phase;
  }
  stage.dataset.pCutoutMotion = "6phase-rig-v3";
}

function applyStaticSpriteMotion(racer, frameIndex) {
  if (!racer || racer.obj.userData.sRunAnimated || racer.obj.userData.pCutoutRig) return;
  const sprite = racer.obj.userData.raceSprite;
  const profile = staticMotionProfile[racer.morph];
  const frame = staticMotionFrames[frameIndex];
  if (!sprite?.isSprite || !profile || !frame) return;

  const sx = 1 + (frame.sx - 1) * profile.strength;
  const sy = 1 + (frame.sy - 1) * profile.strength;
  sprite.userData.motionScaleX = sx;
  sprite.scale.y = sprite.userData.baseScaleY * sy;
  sprite.position.y = sprite.userData.baseY + frame.y * profile.strength;
  sprite.material.rotation = frame.rot * profile.strength;
  sprite.userData.motionFrame = frameIndex;

  if (racer.id === selectedId) stage.dataset.selectedMotionPhase = frame.phase;
  stage.dataset.nonSRunMotion = "placeholder-6phase";
}

function applySRunFrame(racer, frameIndex) {
  const mesh = racer?.obj?.userData?.raceSprite;
  if (!mesh?.isMesh || mesh.userData.frameIndex === frameIndex) return;

  const frame = sRunFrames[frameIndex];
  const map = mesh.material?.map;
  if (!map) return;

  map.offset.set(frame.col / 3, frame.row / 2);
  map.updateMatrix();
  mesh.userData.frameIndex = frameIndex;
  mesh.position.y = raceSpriteLayout.S.y + frame.y;

  if (racer.id === sRunProofRacerId) {
    stage.dataset.sRunFrame = String(frameIndex);
    stage.dataset.sRunPhase = frame.phase;
  }
}

function installSRunSpriteFor(racer) {
  if (!sRunSheetTexture || !racer || racer.morph !== "S" || racer.obj.userData.sRunAnimated) return;
  const oldSprite = racer.obj.userData.raceSprite;
  if (!oldSprite) return;

  racer.obj.remove(oldSprite);
  if (oldSprite.material) oldSprite.material.dispose();
  if (oldSprite.isMesh && oldSprite.geometry) oldSprite.geometry.dispose();

  const raceSprite = buildAnimatedSRunPlane(sRunSheetTexture, raceSpriteLayout.S, racer.id);
  racer.obj.add(raceSprite);
  racer.obj.userData.raceSprite = raceSprite;
  racer.obj.userData.sRunAnimated = true;
  sRunRacers.push(racer);
  applySRunFrame(racer, racer.id % sRunFrames.length);

  if (racer.id === sRunProofRacerId) {
    stage.dataset.sRunCycle = "loaded";
    stage.dataset.sRunFrames = String(sRunFrames.length);
    stage.dataset.sRunSource = "sprite-sheet";
  }
  stage.dataset.sRunAnimatedRacers = String(sRunRacers.length);
}

function orientAnimatedSRunPlanes() {
  if (!sRunRacers.length) return;
  camera.getWorldQuaternion(sBillboardCameraQ);
  for (const racer of sRunRacers) {
    const mesh = racer.obj.userData.raceSprite;
    if (!mesh?.isMesh) continue;
    racer.obj.getWorldQuaternion(sBillboardParentQ);
    mesh.quaternion.copy(sBillboardParentQ).invert().multiply(sBillboardCameraQ);
  }
}

function orientPCutoutRigs() {
  if (!pCutoutRigRacers.length) return;
  camera.getWorldQuaternion(sBillboardCameraQ);
  for (const racer of pCutoutRigRacers) {
    const rig = racer.obj.userData.raceRig;
    if (!rig) continue;
    racer.obj.getWorldQuaternion(sBillboardParentQ);
    rig.quaternion.copy(sBillboardParentQ).invert().multiply(sBillboardCameraQ);
  }
}

const cameraRight = new THREE.Vector3();
const spriteTravelTangent = new THREE.Vector3();

function orientRaceSpritesToTravel() {
  cameraRight.set(1, 0, 0).applyQuaternion(camera.quaternion).normalize();

  for (const racer of racers) {
    const visual = racer.obj.userData.raceRig ?? racer.obj.userData.raceSprite;
    if (!visual?.userData?.baseScaleX) continue;

    const t = (racer.distance / raceMeters) % 1;
    spriteTravelTangent.copy(curve.getTangentAt(t)).normalize();
    const screenDirection = spriteTravelTangent.dot(cameraRight);

    if (Math.abs(screenDirection) > 0.08) {
      visual.userData.facingSign = screenDirection >= 0 ? 1 : -1;
    }

    visual.scale.x = visual.userData.baseScaleX * (visual.userData.motionScaleX ?? 1) * visual.userData.facingSign;
  }

  stage.dataset.directionalSpriteFacing = "enabled";
}

textureLoader.load(
  `${import.meta.env.BASE_URL}concept/s-run-sheet.webp`,
  (texture) => {
    sRunSheetTexture = texture;
    stage.dataset.sRunSheet = "loaded";
    racers.forEach(installSRunSpriteFor);
  },
  undefined,
  (error) => {
    stage.dataset.sRunSheet = "error";
    console.error("S run sprite sheet failed to load", error);
  }
);

function updateConceptReadyState() {
  if (conceptReady.size === 4) {
    stage.dataset.conceptMorphs = "loaded";
    stage.dataset.race2p5d = "loaded";
  }
}

for (const morph of ["S", "P", "E", "A"]) {
  textureLoader.load(
    `${import.meta.env.BASE_URL}concept/${morph}.webp`,
    (texture) => {
      texture.colorSpace = THREE.SRGBColorSpace;
      texture.minFilter = THREE.LinearFilter;
      texture.magFilter = THREE.LinearFilter;
      conceptTextures.set(morph, texture);

      for (const racer of racers.filter((r) => r.morph === morph)) {
        racer.obj.children.forEach((child) => { child.visible = false; });
        const raceLayout = raceSpriteLayout[morph];
        let raceSprite;
        const raceMaterial = new THREE.SpriteMaterial({
          map: texture,
          transparent: true,
          depthWrite: false,
          alphaTest: 0.02
        });
        raceSprite = new THREE.Sprite(raceMaterial);
        raceSprite.name = `Race2_5D_${morph}_${racer.id}`;
        raceSprite.position.set(0, raceLayout.y, 0);
        raceSprite.scale.set(raceLayout.scale[0], raceLayout.scale[1], 1);
        raceSprite.renderOrder = 3;
        raceSprite.userData.baseScaleX = Math.abs(raceLayout.scale[0]);
        raceSprite.userData.baseScaleY = Math.abs(raceLayout.scale[1]);
        raceSprite.userData.baseY = raceLayout.y;
        raceSprite.userData.motionScaleX = 1;
        raceSprite.userData.facingSign = 1;
        racer.obj.add(raceSprite);
        racer.obj.userData.raceSprite = raceSprite;
        if (morph === "S") installSRunSpriteFor(racer);
        if (morph === "P") installPCutoutRigFor(racer, texture);
      }

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
      sprite.visible = activeLabMorph === morph;
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
    obj.visible = key === morph && !conceptReady.has(key) && !(key === "S" && dedicatedSReady);
  });
  if (dedicatedS) dedicatedS.visible = morph === "S" && !conceptReady.has("S");
  conceptSprites.forEach((sprite, key) => {
    sprite.visible = key === morph;
  });

  const [title, baseDetail] = labText[morph];
  const detail = conceptReady.has(morph)
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
let view = isolatedProof ? "follow" : "race";
let raceState = "countdown";
let countdownRemaining = countdownDuration;
let goFlashRemaining = 0;
const finishOrder = [];

const ranks = () => [...racers].sort((a, b) => {
  if (a.finished && b.finished) return a.finishPlace - b.finishPlace;
  if (a.finished) return -1;
  if (b.finished) return 1;
  return b.distance - a.distance;
});
const rankOf = (r) => ranks().findIndex((x) => x === r) + 1;

function gapAhead(r, lane = Math.round(r.laneF)) {
  let gap = 999;
  for (const other of racers) {
    if (other === r || other.finished || Math.round(other.laneF) !== lane) continue;
    const d = other.distance - r.distance;
    if (d > 0 && d < gap) gap = d;
  }
  return gap;
}

function laneFree(r, lane) {
  return racers.every((other) =>
    other === r ||
    other.finished ||
    Math.round(other.laneF) !== lane ||
    Math.abs(other.distance - r.distance) > 6.5
  );
}

function chooseLane(r) {
  const options = Array.from({ length: laneCount }, (_, lane) => lane).filter((lane) => lane !== Math.round(r.laneF) && laneFree(r, lane));
  if (!options.length) return null;
  options.sort((a, b) => gapAhead(r, b) - gapAhead(r, a));
  return options[0];
}

function phase(r) {
  if (r.finished) return "FINISH";
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

function formatRaceTime(ms) {
  const total = Math.max(0, ms) / 1000;
  const minutes = Math.floor(total / 60);
  const seconds = Math.floor(total % 60);
  const hundredths = Math.floor((total % 1) * 100);
  return `${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}.${String(hundredths).padStart(2, "0")}`;
}

function resultInterpretationFor(racer) {
  const stats = racer.agentStats;
  const fatigue = Math.round(100 - racer.stamina);
  const compatibility = compatibilityScoreFor(racer);
  if (compatibility < 99) return `Compatibility ${compatibility}% constrained some Agent commands.`;
  if (stats.failed > 0) return `${stats.failed} failed execution${stats.failed === 1 ? "" : "s"} need review.`;
  if (stats.partial >= 3) return "Several commands were only partially executed.";
  if (fatigue >= 80) return "Race completed under heavy fatigue.";
  if (stats.laneMoves >= 3) return "High lane-change activity shaped this run.";
  if (racer.finishPlace <= 3) return "Clean execution with a podium result.";
  return "Execution was mostly stable; compare policy and pace for the next run.";
}

function renderResultAgentSummary(racer) {
  if (!racer?.agent) return;
  const stats = racer.agentStats;
  const fatigue = Math.round(100 - racer.stamina);
  const historyCount = racer.agent.raceHistory.length;

  document.querySelector("#resultAgentIdentity").textContent =
    `${racer.agent.id} ${racer.agent.name} / ${racer.agent.version}`;
  const compatibilityScore = compatibilityScoreFor(racer);
  document.querySelector("#resultAgentPolicy").textContent =
    `${racer.agent.policy.label.toUpperCase()} · COMPAT ${compatibilityScore}%`;
  document.querySelector("#resultDecisions").textContent = String(stats.decisions);
  document.querySelector("#resultSuccess").textContent = String(stats.success);
  document.querySelector("#resultPartial").textContent = String(stats.partial);
  document.querySelector("#resultFailed").textContent = String(stats.failed);
  document.querySelector("#resultLaneMoves").textContent = String(stats.laneMoves);
  document.querySelector("#resultCompatibility").textContent = `${compatibilityScoreFor(racer)}%`;
  document.querySelector("#resultFinalFatigue").textContent = `${fatigue}%`;
  document.querySelector("#resultAgentRecord").textContent = `Race history ${historyCount}`;
  document.querySelector("#resultAgentInterpretation").textContent = resultInterpretationFor(racer);

  stage.dataset.resultAgentSummary = "ready";
  stage.dataset.resultAgentDecisions = String(stats.decisions);
  stage.dataset.resultAgentFailed = String(stats.failed);
  stage.dataset.resultAgentCompatibility = String(compatibilityScoreFor(racer));
  stage.dataset.resultAgentCompatibility = String(compatibilityScore);
}
function updateRaceStateDataset() {
  stage.dataset.raceState = raceState;
  stage.dataset.finishCount = String(finishOrder.length);
}

function beginRace() {
  raceState = "running";
  goFlashRemaining = 650;
  raceBanner.hidden = false;
  raceBanner.textContent = "GO";
  raceBanner.classList.add("go");
  updateRaceStateDataset();
}

function finishRace() {
  if (raceState === "finished") return;
  raceState = "finished";
  raceBanner.hidden = true;
  raceBanner.classList.remove("go");
  paused = false;
  document.querySelector("#pause").textContent = "Pause";

  const ordered = [...racers].sort((a, b) => a.finishPlace - b.finishPlace);
  for (const r of ordered) {
    r.agent.raceHistory.push({
      place: r.finishPlace,
      time: r.finishTime,
      creatureId: r.id,
      morph: r.morph,
      agentVersion: r.agent.version,
      policy: r.agent.policy.key,
      compatibility: compatibilityScoreFor(r),
      finalFatigue: Math.round(100 - r.stamina),
      summary: { ...r.agentStats }
    });
  }
  resultsList.innerHTML = ordered.map((r) => `
    <div class="result-row ${r.id === selectedId ? "selected" : ""}">
      <span class="place">#${r.finishPlace}</span>
      <span><span class="result-name">${r.name}</span><span class="result-morph"> #${String(r.id).padStart(2, "0")}</span><small class="result-agent">${r.agent.id} ${r.agent.name} · ${r.agent.policy.label}</small></span>
      <span class="result-morph">${r.morph}</span>
      <span class="result-time">${formatRaceTime(r.finishTime)}</span>
    </div>
  `).join("");

  resultHeadline.textContent = `#${selected.finishPlace} ${selected.name} — ${formatRaceTime(selected.finishTime)}`;
  renderResultAgentSummary(selected);
  resultsPanel.hidden = false;
  updateRaceStateDataset();
}

function updateRaceLifecycle(dt) {
  if (paused) return;

  if (raceState === "countdown") {
    countdownRemaining -= dt;
    const value = Math.max(1, Math.ceil(countdownRemaining / 1000));
    raceBanner.hidden = false;
    raceBanner.classList.remove("go");
    raceBanner.textContent = String(value);
    if (countdownRemaining <= 0) beginRace();
    return;
  }

  if (raceState === "running" && goFlashRemaining > 0) {
    goFlashRemaining -= dt;
    if (goFlashRemaining <= 0) {
      raceBanner.hidden = true;
      raceBanner.classList.remove("go");
    }
  }
}

function update(dt) {
  if (paused || raceState !== "running") return;
  const raceDt = fastFinishProof ? dt * 8 : dt;
  elapsed += raceDt;
  const sec = raceDt / 1000;

  for (const r of racers) {
    if (r.finished) {
      r.speed = 0;
      continue;
    }
    r.cooldown = Math.max(0, r.cooldown - raceDt);
    const currentPhase = phase(r);
    const gap = gapAhead(r);
    const position = rankOf(r);
    const policy = r.agent.policy;
    const compatibility = compatibilityFor(r);
    let target = morphTarget(r) * compatibility;

    if (currentPhase === "START") target *= policy.startBias;
    else if (currentPhase === "MID") target *= policy.midBias;
    else if (currentPhase === "BUILD") target *= policy.buildBias;

    if (r.stamina < policy.preserveAt) {
      target *= 0.88;
      r.decision = "PRESERVE";
      r.command = "EASE";
    } else if (gap < policy.overtakeGap && r.cooldown <= 0) {
      const nextLane = chooseLane(r);
      if (nextLane !== null) {
        r.lane = nextLane;
        r.cooldown = policy.laneCooldown;
        r.decision = "OVERTAKE";
        r.command = nextLane < r.laneF ? "MOVE INSIDE" : "MOVE OUTSIDE";
        target *= 1.025;
      } else {
        target *= 0.90;
        r.decision = "BLOCKED";
        r.command = "WAIT";
      }
    } else if (currentPhase === "FINAL") {
      target *= policy.finalBoost;
      r.decision = "ATTACK";
      r.command = "PUSH";
    } else if (position > policy.advanceAt && currentPhase !== "START") {
      target *= policy.advanceBoost;
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
    r.stamina = Math.max(0, r.stamina - (0.018 + 0.038 * load * load) * r.drain * raceDt / 1000);
    r.laneF = THREE.MathUtils.lerp(r.laneF, r.lane, Math.min(1, raceDt * 0.0032));
    recordAgentEvent(r);

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

    if (r.obj.userData.sRunAnimated) {
      const speedRatio = THREE.MathUtils.clamp(r.speed / Math.max(1, r.cruise), 0, 1.15);
      const frameMs = THREE.MathUtils.lerp(145, 72, speedRatio);
      const phaseOffset = (r.id * 41) % Math.round(frameMs * sRunFrames.length);
      const frameIndex = Math.floor((elapsed + phaseOffset) / frameMs) % sRunFrames.length;
      applySRunFrame(r, frameIndex);
    } else if (r.obj.userData.pCutoutRig) {
      const speedRatio = THREE.MathUtils.clamp(r.speed / Math.max(1, r.cruise), 0, 1.15);
      const frameMs = THREE.MathUtils.lerp(160, 86, speedRatio);
      const frameIndex = Math.floor((elapsed + r.id * 37) / frameMs) % 6;
      applyPCutoutRigMotion(r, frameIndex);
    } else if (staticMotionProfile[r.morph]) {
      const speedRatio = THREE.MathUtils.clamp(r.speed / Math.max(1, r.cruise), 0, 1.15);
      const profile = staticMotionProfile[r.morph];
      const frameMs = THREE.MathUtils.lerp(165, 88, speedRatio) / profile.rate;
      const phaseOffset = (r.id * 53) % Math.round(frameMs * staticMotionFrames.length);
      const frameIndex = Math.floor((elapsed + phaseOffset) / frameMs) % staticMotionFrames.length;
      applyStaticSpriteMotion(r, frameIndex);
    }

    r.dustTimer = Math.max(0, (r.dustTimer ?? 0) - raceDt);
    if (r.speed > 7 && r.dustTimer <= 0) {
      spawnDust(r, tangent);
      r.dustTimer = r.id === selectedId ? 155 : 265 + (r.id % 4) * 42;
    }

    if (r.distance >= raceMeters) {
      r.finished = true;
      r.finishPlace = finishOrder.length + 1;
      r.finishTime = elapsed;
      r.decision = "FINISHED";
      r.command = `PLACE #${r.finishPlace}`;
      r.speed = 0;
      finishOrder.push(r.id);
      recordAgentEvent(r, true);
      stage.dataset.finishCount = String(finishOrder.length);
      if (r.obj.userData.sRunAnimated) applySRunFrame(r, 5);
      else if (r.obj.userData.pCutoutRig) applyPCutoutRigMotion(r, 5);
      else if (staticMotionProfile[r.morph]) applyStaticSpriteMotion(r, 5);
    }
  }

  if (finishOrder.length === racers.length) finishRace();

  ring.position.set(selected.obj.position.x, 0.08, selected.obj.position.z);
  tacticalMarkers.forEach((marker, index) => {
    const r = racers[index];
    marker.position.set(r.obj.position.x, 2.8, r.obj.position.z);
  });
  racerShadows.forEach((shadow, index) => {
    const r = racers[index];
    shadow.position.x = r.obj.position.x;
    shadow.position.z = r.obj.position.z;
    const bob = Math.max(0, r.obj.position.y - 0.98);
    const shrink = THREE.MathUtils.clamp(1 - bob * 1.8, 0.72, 1);
    shadow.scale.set(1.55 * shrink, 0.62 * shrink, 1);
  });
  updateDust(fastFinishProof ? dt * 8 : dt);
}

function setCamera() {
  const selectedPos = selected.obj.position.clone();
  const t = (selected.distance / raceMeters) % 1;
  const tangent = curve.getTangentAt(t).normalize();
  const side = new THREE.Vector3(-tangent.z, 0, tangent.x);

  const speedRatio = THREE.MathUtils.clamp(selected.speed / Math.max(1, selected.cruise), 0, 1.2);
  const targetFov = view === "follow"
    ? THREE.MathUtils.lerp(isMobile ? 52 : 44, isMobile ? 62 : 54, speedRatio)
    : view === "race"
      ? THREE.MathUtils.lerp(isMobile ? 52 : 44, isMobile ? 66 : 58, speedRatio)
      : (isMobile ? 50 : 42);
  camera.fov = THREE.MathUtils.lerp(camera.fov, targetFov, 0.09);
  camera.updateProjectionMatrix();

  const lab = view === "lab";
  const tactical = view === "tactical";
  scene.fog = (lab || tactical) ? null : raceFog;
  scene.background = new THREE.Color(lab ? 0x202a35 : 0x9bc6dc);
  raceEnvironment.forEach((obj) => { obj.visible = !lab; });
  racers.forEach((r) => { r.obj.visible = !lab && !tactical && (!isolatedProof || r.id === isolatedProofRacerId); });
  ring.visible = !lab && !tactical;
  racerShadows.forEach((shadow, index) => {
    shadow.visible = !lab && !tactical && (!isolatedProof || racers[index].id === isolatedProofRacerId);
  });
  tacticalMarkers.forEach((marker) => { marker.visible = tactical; });
  labGroup.visible = lab;
  labFloor.visible = lab;
  document.querySelector(".hud-race").hidden = lab;
  document.querySelector(".hud-mini").hidden = lab || pRigIsolatedProof;
  document.querySelector(".hud-selected").hidden = lab || pRigIsolatedProof;
  document.querySelector("#agentPanel").hidden = lab || pRigIsolatedProof;
  document.querySelector("#morphSwitcher").hidden = !lab;
  document.querySelector("#labLabel").hidden = !lab;

  if (lab) {
    camera.up.set(0, 1, 0);
    camera.position.lerp(new THREE.Vector3(0, 2.7, isMobile ? 12.5 : 11.5), 0.20);
    camera.lookAt(0, 1.25, 0);
  } else if (view === "follow") {
    camera.up.set(0, 1, 0);
    const isolatedBack = pRigIsolatedProof ? -1.55 : -1.2;
    const isolatedSide = pRigIsolatedProof ? 4.8 : 4.1;
    const isolatedHeight = pRigIsolatedProof ? 1.95 : 1.72;
    const followBack = isolatedProof ? (isMobile ? -1.5 : isolatedBack) : (isMobile ? -2.8 : -1.8);
    const followSide = isolatedProof ? (isMobile ? 4.3 : isolatedSide) : (isMobile ? 5.6 : 4.8);
    const followHeight = isolatedProof ? (isMobile ? 1.92 : isolatedHeight) : (isMobile ? 2.68 : 2.12);
    const shake = Math.max(0, speedRatio - 0.48) * (isolatedProof ? 0.08 : 0.075);
    const desired = selectedPos.clone()
      .addScaledVector(tangent, followBack)
      .addScaledVector(side, followSide + Math.sin(elapsed * 0.023) * shake)
      .add(new THREE.Vector3(0, followHeight + Math.sin(elapsed * 0.031) * shake * 0.6, 0));
    camera.position.lerp(desired, 0.15);
    const lookTarget = selectedPos.clone()
      .addScaledVector(tangent, 2.4)
      .addScaledVector(side, Math.sin(elapsed * 0.017) * shake * 0.45)
      .add(new THREE.Vector3(0, 0.50, 0));
    camera.lookAt(lookTarget);
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

    const raceBack = isMobile ? -7.4 : -8.2;
    const raceSide = isMobile ? 13.3 : 12.6;
    const raceHeight = isMobile ? 6.2 : 5.9;
    camera.position.lerp(
      center.clone().addScaledVector(leaderTangent, raceBack).addScaledVector(leaderSide, raceSide).add(new THREE.Vector3(0, raceHeight, 0)),
      0.065
    );
    camera.lookAt(center.clone().addScaledVector(leaderTangent, 2.8).add(new THREE.Vector3(0, 0.62, 0)));
    stage.dataset.raceCamera = "wide-pack";
  }

  const selectedCameraDistance = camera.position.distanceTo(selected.obj.position);
  racers.forEach((r) => {
    let targetOpacity = 1;
    if (view === "follow" && r.id !== selectedId && r.obj.visible) {
      const d = camera.position.distanceTo(r.obj.position);
      if (d < selectedCameraDistance - 0.55) targetOpacity = 0.02;
      else if (d < selectedCameraDistance + 0.20) targetOpacity = 0.22;
    }

    const rig = r.obj.userData.raceRig;
    if (rig) {
      rig.traverse((part) => {
        if (!part.material || part.material.opacity === undefined) return;
        part.material.opacity = THREE.MathUtils.lerp(part.material.opacity, targetOpacity, 0.24);
      });
      return;
    }

    const material = r.obj.userData.raceSprite?.material;
    if (!material || material.opacity === undefined) return;
    material.opacity = THREE.MathUtils.lerp(material.opacity, targetOpacity, 0.24);
  });
  stage.dataset.followOcclusionFade = "enabled";
}

function updateHud() {
  const ordered = ranks();
  const position = rankOf(selected);
  const gapValue = gapAhead(selected);
  const currentPhase = phase(selected);
  const sec = elapsed / 1000;
  const progress = THREE.MathUtils.clamp(selected.distance / raceMeters, 0, 1);
  const remaining = Math.max(0, raceMeters - selected.distance);
  const leader = ordered[0];
  const leaderGap = leader === selected ? 0 : Math.max(0, leader.distance - selected.distance);
  const finalCharge = currentPhase === "FINAL" && !selected.finished;

  document.querySelector("#position").textContent = `${position} / 18`;
  document.querySelector("#speed").textContent = Math.round(selected.speed);
  const fatigue = Math.round(100 - selected.stamina);
  document.querySelector("#fatigue").textContent = `${fatigue}%`;
  const fatigueFill = document.querySelector("#fatigueFill");
  if (fatigueFill) {
    fatigueFill.style.width = `${fatigue}%`;
    fatigueFill.classList.toggle("high", fatigue >= 65 && fatigue < 85);
    fatigueFill.classList.toggle("critical", fatigue >= 85);
  }
  stage.dataset.creatureFatigue = String(fatigue);
  document.querySelector("#morph").textContent = `${selected.morph} / ${morphLabel[selected.morph].toUpperCase()}`;
  document.querySelector("#decision").textContent = `${selected.decision} / ${selected.command}`;
  document.querySelector("#morphName").textContent = `${selected.morph} — ${morphLabel[selected.morph]}`;
  document.querySelector("#lane").textContent = String(Math.round(selected.laneF) + 1);
  document.querySelector("#gap").textContent = gapValue < 900 ? `${gapValue.toFixed(1)} m` : "—";
  document.querySelector("#phase").textContent = currentPhase;
  document.querySelector("#clock").textContent =
    `${String(Math.floor(sec / 60)).padStart(2, "0")}:${String(Math.floor(sec % 60)).padStart(2, "0")}.${String(Math.floor((sec % 1) * 100)).padStart(2, "0")}`;

  const progressFill = document.querySelector("#raceProgressFill");
  const remainingLabel = document.querySelector("#remaining");
  const leaderGapLabel = document.querySelector("#leaderGap");
  const sectionLabel = document.querySelector("#raceSection");
  if (progressFill) progressFill.style.width = `${(progress * 100).toFixed(1)}%`;
  if (remainingLabel) remainingLabel.textContent = selected.finished ? "FINISHED" : `${Math.ceil(remaining)} m to go`;
  if (leaderGapLabel) leaderGapLabel.textContent = leader === selected ? "LEADER" : `+${leaderGap.toFixed(1)} m`;
  if (sectionLabel) sectionLabel.textContent = currentPhase;
  document.querySelector(".hud-race")?.classList.toggle("final", finalCharge);
  stage.dataset.hudTelemetry = "active";
  stage.dataset.raceSection = currentPhase;
  stage.dataset.remainingMeters = String(Math.ceil(remaining));

  const agentLogEl = document.querySelector("#agentLog");
  const selectedLog = selected.agentLog ?? [];
  if (agentLogEl) {
    if (!selectedLog.length) {
      agentLogEl.innerHTML = '<p class="agent-log-empty">No decisions yet.</p>';
    } else {
      agentLogEl.innerHTML = selectedLog.slice(-5).reverse().map((event) => `
        <div class="agent-log-row ${event.result.toLowerCase()}">
          <time>${formatRaceTime(event.time)}</time>
          <div class="agent-log-main">
            <b>${event.order}</b>
            <span>${event.reason} · F${event.fatigue}% · #${event.position}</span>
          </div>
          <span class="agent-log-result">${event.result}</span>
        </div>
      `).join("");
    }
  }
  stage.dataset.agentLogEvents = String(selectedLog.length);

  const rankingNow = performance.now();
  if (rankingNow - lastRankingPaint >= 220 || raceState === "finished") {
    ordered.forEach((r, index) => {
      let row = rankingPanel.querySelector(`[data-racer-id="${r.id}"]`);
      if (!row) {
        row = document.createElement("div");
        row.className = "rank-row";
        row.dataset.racerId = String(r.id);
        row.setAttribute("role", "button");
        row.tabIndex = 0;
        row.setAttribute("aria-label", `Select #${String(r.id).padStart(2, "0")} ${r.name}`);
        row.innerHTML = `
          <b class="rank-pos"></b>
          <span><i class="dot"></i><span class="rank-copy"></span><span class="badge"></span></span>
          <span class="rank-value"></span>
        `;
        row.querySelector(".dot").style.background = r.color;
        row.querySelector(".rank-copy").textContent = `#${String(r.id).padStart(2, "0")} ${r.name}`;
        row.querySelector(".badge").textContent = r.morph;
      }

      row.classList.toggle("selected", r.id === selectedId);
      row.querySelector(".rank-pos").textContent = String(index + 1);
      row.querySelector(".rank-value").textContent = r.finished ? `#${r.finishPlace}` : r.speed.toFixed(1);
      rankingPanel.append(row);
    });
    lastRankingPaint = rankingNow;
  }
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
  finishOrder.length = 0;
  racers.forEach((r, i) => {
    if (r.agent.pendingPolicyKey) {
      const nextPolicy = agentPolicyByKey(r.agent.pendingPolicyKey);
      if (nextPolicy && nextPolicy.key !== r.agent.policy.key) {
        r.agent.versionNumber += 1;
        r.agent.version = `v${r.agent.versionNumber}`;
        r.agent.policy = { ...nextPolicy };
        r.agent.versionHistory.push({
          version: r.agent.version,
          profile: nextPolicy.key
        });
      }
      r.agent.pendingPolicyKey = null;
    }

    r.distance = Math.max(0, (17 - i) * 1.1);
    r.lane = i % laneCount;
    r.laneF = i % laneCount;
    r.stamina = 100;
    r.speed = 0;
    r.cooldown = 0;
    r.dustTimer = 0;
    r.finished = false;
    r.finishPlace = null;
    r.finishTime = null;
    r.agentLog.length = 0;
    r.agentStats.decisions = 0;
    r.agentStats.success = 0;
    r.agentStats.partial = 0;
    r.agentStats.failed = 0;
    r.agentStats.laneMoves = 0;
    r.lastAgentLogSignature = null;
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
  paused = false;
  raceState = "countdown";
  countdownRemaining = countdownDuration;
  goFlashRemaining = 0;
  resultsPanel.hidden = true;
  raceBanner.hidden = false;
  raceBanner.classList.remove("go");
  raceBanner.textContent = String(Math.max(1, Math.ceil(countdownDuration / 1000)));
  document.querySelector("#pause").textContent = "Pause";
  lastAgentCommand = "";
  lastAgentRacerId = null;
  agentPulseUntil = performance.now() + 420;
  agentToastUntil = performance.now() + 1050;
  updateRaceStateDataset();
  updateAgentSetupUi();
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
    const rawDt = Math.max(0, now - last);
    const dt = Math.min(45, rawDt);
    last = now;
    updateRaceLifecycle(rawDt);
    update(dt);
    setCamera();
    orientAnimatedSRunPlanes();
    orientPCutoutRigs();
    orientRaceSpritesToTravel();
    updateAgentVisual(now);
    renderer.render(scene, camera);
    updateHud();
    drawMiniMap();

    renderedFrames += 1;
    if (renderedFrames === 2) {
      runtimeStatus.hidden = true;
      if (sRunIsolatedProof) stage.dataset.sRunProof = "isolated";
      if (pRigIsolatedProof) stage.dataset.pCutoutProof = "isolated";
    }
  } catch (error) {
    paused = true;
    failRuntime(error);
    renderer.setAnimationLoop(null);
  }
}
renderer.setAnimationLoop(frame);

function syncViewUi() {
  document.querySelector("#viewLabel").textContent =
    view === "lab" ? "MORPH LAB" : view === "race" ? "RACE VIEW" : view === "follow" ? "FOLLOW VIEW" : "TACTICAL VIEW";
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
}

document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => {
    view = button.dataset.view;
    resize();
    syncViewUi();
  });
});
syncViewUi();

document.querySelectorAll("[data-morph]").forEach((button) => {
  button.addEventListener("click", () => {
    setLabMorph(button.dataset.morph);
  });
});

document.querySelector("#pause").addEventListener("click", (event) => {
  if (raceState === "finished") return;
  paused = !paused;
  event.currentTarget.textContent = paused ? "Resume" : "Pause";
  if (paused) {
    raceBanner.hidden = false;
    raceBanner.classList.remove("go");
    raceBanner.textContent = "PAUSED";
  } else {
    updateRaceLifecycle(0);
    if (raceState === "running" && goFlashRemaining <= 0) raceBanner.hidden = true;
  }
});

document.querySelector("#reset").addEventListener("click", resetRace);
document.querySelector("#rematch").addEventListener("click", resetRace);
