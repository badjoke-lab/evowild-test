import fs from "node:fs";
import path from "node:path";
import * as THREE from "three";
import { OBJExporter } from "three/addons/exporters/OBJExporter.js";

const outDir = path.resolve("public/models");
fs.mkdirSync(outDir, { recursive: true });

const materials = {
  body: new THREE.MeshStandardMaterial({ name: "S_body" }),
  accent: new THREE.MeshStandardMaterial({ name: "S_accent" }),
  under: new THREE.MeshStandardMaterial({ name: "S_under" }),
  band: new THREE.MeshStandardMaterial({ name: "CueBand_dark" }),
  cyan: new THREE.MeshStandardMaterial({ name: "CueBand_cyan" }),
  eye: new THREE.MeshStandardMaterial({ name: "Eye_cyan" })
};

function loftGeometry(sections, radial = 18) {
  const positions = [];
  const indices = [];

  for (const [x, cy, ry, rz] of sections) {
    for (let j = 0; j < radial; j++) {
      const a = j / radial * Math.PI * 2;
      positions.push(x, cy + Math.cos(a) * ry, Math.sin(a) * rz);
    }
  }

  for (let i = 0; i < sections.length - 1; i++) {
    for (let j = 0; j < radial; j++) {
      const n = (j + 1) % radial;
      const a = i * radial + j;
      const b = i * radial + n;
      const c = (i + 1) * radial + j;
      const d = (i + 1) * radial + n;
      indices.push(a, c, b, b, c, d);
    }
  }

  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  g.setIndex(indices);
  g.computeVertexNormals();
  return g;
}

function addMesh(group, name, geometry, material) {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.name = name;
  group.add(mesh);
  return mesh;
}

function addTube(group, name, points, radius, material, radial = 10) {
  const curve = new THREE.CatmullRomCurve3(points.map((p) => new THREE.Vector3(...p)));
  const mesh = addMesh(
    group,
    name,
    new THREE.TubeGeometry(curve, Math.max(8, points.length * 4), radius, radial, false),
    material
  );
  return mesh;
}

function addTaperedSegment(group, name, a, b, r0, r1, material, radial = 10) {
  const va = new THREE.Vector3(...a);
  const vb = new THREE.Vector3(...b);
  const dir = vb.clone().sub(va);
  const length = dir.length();
  const mesh = addMesh(
    group,
    name,
    new THREE.CylinderGeometry(r1, r0, length, radial, 2, false),
    material
  );
  mesh.position.copy(va.clone().add(vb).multiplyScalar(0.5));
  mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
  return mesh;
}

function profilePrismGeometry(profile, zHalf = 0.04) {
  const positions = [];
  const indices = [];
  const n = profile.length;

  for (const z of [-zHalf, zHalf]) {
    for (const [x, y] of profile) positions.push(x, y, z);
  }

  for (let i = 1; i < n - 1; i++) {
    indices.push(0, i + 1, i);
    indices.push(n, n + i, n + i + 1);
  }

  for (let i = 0; i < n; i++) {
    const next = (i + 1) % n;
    indices.push(i, next, n + i, next, n + next, n + i);
  }

  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  g.setIndex(indices);
  g.computeVertexNormals();
  return g;
}

const root = new THREE.Group();
root.name = "EvoWild_Sprint_S";

// Long, light racing torso: narrow waist, visible shoulder/haunch masses, no barrel body.
addMesh(root, "body", loftGeometry([
  [-1.68, 1.22, 0.18, 0.23],
  [-1.38, 1.23, 0.34, 0.38],
  [-0.92, 1.25, 0.42, 0.44],
  [-0.34, 1.27, 0.45, 0.46],
  [ 0.18, 1.30, 0.40, 0.42],
  [ 0.62, 1.38, 0.38, 0.39],
  [ 0.92, 1.48, 0.23, 0.27]
], 20), materials.body);

addMesh(root, "underbody", loftGeometry([
  [-1.05, 1.03, 0.12, 0.28],
  [-0.45, 1.00, 0.16, 0.34],
  [ 0.20, 1.03, 0.17, 0.34],
  [ 0.76, 1.15, 0.13, 0.25]
], 14), materials.under);

// Dark dorsal structure that makes the silhouette read like the concept instead of a generic animal.
addMesh(root, "dorsal_ridge", loftGeometry([
  [-1.26, 1.48, 0.05, 0.24],
  [-0.72, 1.62, 0.08, 0.30],
  [-0.10, 1.66, 0.09, 0.31],
  [ 0.48, 1.62, 0.08, 0.27],
  [ 0.76, 1.56, 0.05, 0.18]
], 12), materials.accent);

// Angular side armor/muscle plates: avoid toy-like circular joints.
const shoulderPlate = [
  [0.26, 1.13],
  [0.42, 1.57],
  [0.72, 1.67],
  [0.96, 1.46],
  [0.86, 1.16],
  [0.54, 1.04]
];
const haunchPlate = [
  [-1.28, 1.08],
  [-1.18, 1.49],
  [-0.92, 1.61],
  [-0.62, 1.46],
  [-0.64, 1.12],
  [-0.96, 1.02]
];
for (const side of [-1, 1]) {
  const shoulder = addMesh(root, `shoulder_plate_${side}`, profilePrismGeometry(shoulderPlate, 0.055), materials.accent);
  shoulder.position.z = 0.37 * side;

  const haunch = addMesh(root, `haunch_plate_${side}`, profilePrismGeometry(haunchPlate, 0.055), materials.accent);
  haunch.position.z = 0.39 * side;
}

// Slender rising neck and small wedge-shaped head.
addTube(root, "neck", [
  [0.78, 1.42, 0],
  [1.00, 1.58, 0],
  [1.20, 1.74, 0],
  [1.38, 1.86, 0]
], 0.16, materials.accent, 12);

addMesh(root, "head", loftGeometry([
  [1.28, 1.85, 0.17, 0.21],
  [1.52, 1.91, 0.22, 0.25],
  [1.78, 1.92, 0.21, 0.23],
  [2.02, 1.88, 0.15, 0.17],
  [2.26, 1.81, 0.065, 0.105]
], 16), materials.body);

addMesh(root, "jaw", loftGeometry([
  [1.48, 1.74, 0.06, 0.18],
  [1.82, 1.73, 0.075, 0.17],
  [2.18, 1.69, 0.035, 0.085]
], 10), materials.accent);

// Signature long blade horns sweep backwards from a compact head.
const hornProfile = [
  [ 1.54, 2.05],
  [ 1.26, 2.24],
  [ 0.78, 2.49],
  [ 0.22, 2.71],
  [-0.34, 2.84],
  [ 0.12, 2.57],
  [ 0.72, 2.31],
  [ 1.46, 1.99]
];
for (const side of [-1, 1]) {
  const horn = addMesh(root, `horn_blade_${side}`, profilePrismGeometry(hornProfile, 0.032), materials.accent);
  horn.position.z = 0.11 * side;

  const secondary = addMesh(root, `secondary_horn_${side}`, profilePrismGeometry([
    [1.42, 2.02],
    [1.18, 2.16],
    [0.88, 2.30],
    [0.55, 2.37],
    [0.82, 2.20],
    [1.36, 1.98]
  ], 0.022), materials.accent);
  secondary.position.z = 0.16 * side;

  const eye = addMesh(root, `eye_${side}`, new THREE.SphereGeometry(0.055, 12, 8), materials.eye);
  eye.position.set(1.91, 1.94, 0.205 * side);
}

// Long angular legs with visible upper/lower segments and small feet.
for (const [name, x, z, rear] of [
  ["hindL", -0.88, -0.32, true],
  ["hindR", -0.88,  0.32, true],
  ["foreL",  0.55, -0.30, false],
  ["foreR",  0.55,  0.30, false]
]) {
  const hip = [x, 1.02, z];
  const knee = rear ? [x + 0.22, 0.58, z] : [x - 0.12, 0.57, z];
  const ankle = rear ? [x - 0.09, 0.15, z] : [x + 0.06, 0.15, z];
  const foot = rear ? [x + 0.16, 0.035, z] : [x + 0.22, 0.035, z];

  addTaperedSegment(root, `${name}_upper`, hip, knee, 0.095, 0.065, materials.body, 10);
  addTaperedSegment(root, `${name}_lower`, knee, ankle, 0.065, 0.040, materials.accent, 9);
  addTaperedSegment(root, `${name}_foot`, ankle, foot, 0.045, 0.028, materials.accent, 8);
}

// Short aerodynamic tail instead of a horse-like tail.
addTube(root, "tail", [
  [-1.56, 1.28, 0],
  [-1.84, 1.35, 0],
  [-2.10, 1.42, 0],
  [-2.32, 1.45, 0]
], 0.045, materials.accent, 9);

// Thin cyan body accents make the race silhouette readable without relying on white highlights.
for (const side of [-1, 1]) {
  const stripe = addMesh(root, `body_accent_${side}`, new THREE.BoxGeometry(0.72, 0.055, 0.035), materials.cyan);
  stripe.position.set(0.08, 1.48, 0.44 * side);
  stripe.rotation.z = -0.10;
}

// Low-profile race Cue Band.
const bridge = addMesh(root, "cue_bridge", new THREE.BoxGeometry(0.30, 0.075, 0.58), materials.band);
bridge.position.set(1.66, 2.01, 0);

for (const side of [-1, 1]) {
  const pod = addMesh(root, `cue_pod_${side}`, new THREE.BoxGeometry(0.14, 0.17, 0.085), materials.cyan);
  pod.position.set(1.69, 1.96, 0.29 * side);
}
root.updateMatrixWorld(true);

const exporter = new OBJExporter();
const obj = exporter.parse(root);
const mtl = `# EvoWild Run S prototype
newmtl S_body
Kd 0.70 0.79 0.87
Ks 0.08 0.10 0.12
Ns 55

newmtl S_accent
Kd 0.13 0.21 0.31
Ks 0.10 0.14 0.18
Ns 70

newmtl S_under
Kd 0.86 0.89 0.92
Ks 0.05 0.06 0.07
Ns 35

newmtl CueBand_dark
Kd 0.07 0.09 0.13
Ks 0.22 0.25 0.30
Ns 110

newmtl CueBand_cyan
Kd 0.14 0.81 1.00
Ke 0.05 0.35 0.55
Ks 0.30 0.35 0.40
Ns 140

newmtl Eye_cyan
Kd 0.35 0.91 1.00
Ke 0.12 0.50 0.65
Ks 0.35 0.40 0.45
Ns 160
`;

fs.writeFileSync(path.join(outDir, "evowild-s.obj"), `mtllib evowild-s.mtl\n${obj}`);
fs.writeFileSync(path.join(outDir, "evowild-s.mtl"), mtl);
console.log("generated public/models/evowild-s.obj");
