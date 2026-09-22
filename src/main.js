import * as THREE from "three";
import { OBJLoader } from "three/addons/loaders/OBJLoader.js";
import { MTLLoader } from "three/addons/loaders/MTLLoader.js";
import "./styles.css";

const canvas = document.querySelector("#game");
const stage = document.querySelector("#stage");
const isMobile = matchMedia("(pointer: coarse)").matches || innerWidth < 800;
const proofMode = new URLSearchParams(location.search).get("proof");
const sRunIsolatedProof = proofMode === "s-run";
const fastFinishProof = proofMode === "finish";
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

  stage.dataset.trackPresentation = "v4";
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

const racers = [];
let selectedId = 1;
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
    dustTimer: 0,
    finished: false,
    finishPlace: null,
    finishTime: null,
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
    marker.scale.setScalar(isSelected ? 1.22 : 1);
  });

  ring.position.set(selected.obj.position.x, 0.08, selected.obj.position.z);
}

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
const sRunRacers = [];
let sRunSheetTexture = null;
const sBillboardParentQ = new THREE.Quaternion();
const sBillboardCameraQ = new THREE.Quaternion();

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
  return mesh;
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
        racer.obj.add(raceSprite);
        racer.obj.userData.raceSprite = raceSprite;
        if (morph === "S") installSRunSpriteFor(racer);
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
let view = sRunIsolatedProof ? "follow" : "race";
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
  resultsList.innerHTML = ordered.map((r) => `
    <div class="result-row ${r.id === selectedId ? "selected" : ""}">
      <span class="place">#${r.finishPlace}</span>
      <span><span class="result-name">${r.name}</span><span class="result-morph"> #${String(r.id).padStart(2, "0")}</span></span>
      <span class="result-morph">${r.morph}</span>
      <span class="result-time">${formatRaceTime(r.finishTime)}</span>
    </div>
  `).join("");

  resultHeadline.textContent = `#${selected.finishPlace} ${selected.name} — ${formatRaceTime(selected.finishTime)}`;
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
    r.stamina = Math.max(0, r.stamina - (0.018 + 0.038 * load * load) * r.drain * raceDt / 1000);
    r.laneF = THREE.MathUtils.lerp(r.laneF, r.lane, Math.min(1, raceDt * 0.0032));

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
      stage.dataset.finishCount = String(finishOrder.length);
      if (r.obj.userData.sRunAnimated) applySRunFrame(r, 5);
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
  racers.forEach((r) => { r.obj.visible = !lab && !tactical && (!sRunIsolatedProof || r.id === sRunProofRacerId); });
  ring.visible = !lab && !tactical;
  racerShadows.forEach((shadow, index) => {
    shadow.visible = !lab && !tactical && (!sRunIsolatedProof || racers[index].id === sRunProofRacerId);
  });
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
    const followBack = sRunIsolatedProof ? (isMobile ? -1.5 : -1.2) : (isMobile ? -2.3 : -1.8);
    const followSide = sRunIsolatedProof ? (isMobile ? 4.3 : 4.1) : (isMobile ? 4.6 : 4.8);
    const followHeight = sRunIsolatedProof ? (isMobile ? 1.92 : 1.72) : (isMobile ? 2.42 : 2.12);
    const shake = Math.max(0, speedRatio - 0.48) * (sRunIsolatedProof ? 0.10 : 0.075);
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
    const sprite = r.obj.userData.raceSprite;
    const material = sprite?.material;
    if (!material || material.opacity === undefined) return;

    let targetOpacity = 1;
    if (view === "follow" && r.id !== selectedId && r.obj.visible) {
      const d = camera.position.distanceTo(r.obj.position);
      if (d < selectedCameraDistance - 0.55) targetOpacity = 0.02;
      else if (d < selectedCameraDistance + 0.20) targetOpacity = 0.22;
    }
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
  document.querySelector("#stamina").textContent = Math.round(selected.stamina);
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

  document.querySelector("#ranking").innerHTML = ordered.map((r, index) => `
    <div class="rank-row ${r.id === selectedId ? "selected" : ""}" data-racer-id="${r.id}" role="button" tabindex="0" aria-label="Select #${String(r.id).padStart(2, "0")} ${r.name}">
      <b>${index + 1}</b>
      <span><i class="dot" style="background:${r.color}"></i>#${String(r.id).padStart(2, "0")} ${r.name}<span class="badge">${r.morph}</span></span>
      <span>${r.finished ? `#${r.finishPlace}` : r.speed.toFixed(1)}</span>
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
  finishOrder.length = 0;
  racers.forEach((r, i) => {
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
  updateRaceStateDataset();
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
    renderer.render(scene, camera);
    updateHud();
    drawMiniMap();

    renderedFrames += 1;
    if (renderedFrames === 2) {
      runtimeStatus.hidden = true;
      if (sRunIsolatedProof) stage.dataset.sRunProof = "isolated";
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
