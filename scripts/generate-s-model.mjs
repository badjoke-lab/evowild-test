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

const root = new THREE.Group();
root.name = "EvoWild_Sprint_S";

addMesh(root, "body", loftGeometry([
  [-1.72, 1.12, 0.22, 0.26],
  [-1.42, 1.14, 0.42, 0.46],
  [-0.95, 1.18, 0.55, 0.54],
  [-0.35, 1.22, 0.60, 0.56],
  [ 0.20, 1.26, 0.55, 0.52],
  [ 0.68, 1.34, 0.48, 0.47],
  [ 0.98, 1.43, 0.30, 0.34]
]), materials.body);

addMesh(root, "chest", loftGeometry([
  [-0.85, 0.98, 0.18, 0.34],
  [-0.20, 0.96, 0.22, 0.40],
  [ 0.55, 1.02, 0.23, 0.38],
  [ 0.90, 1.16, 0.16, 0.26]
], 14), materials.under);

addMesh(root, "back_ridge", loftGeometry([
  [-1.18, 1.53, 0.06, 0.26],
  [-0.45, 1.66, 0.09, 0.30],
  [ 0.25, 1.64, 0.10, 0.27],
  [ 0.70, 1.58, 0.07, 0.20]
], 12), materials.accent);

addTube(root, "neck", [
  [0.78, 1.38, 0],
  [1.02, 1.58, 0],
  [1.24, 1.76, 0],
  [1.45, 1.90, 0]
], 0.23, materials.accent, 12);

addMesh(root, "head", loftGeometry([
  [1.28, 1.88, 0.23, 0.25],
  [1.55, 1.94, 0.28, 0.30],
  [1.86, 1.94, 0.26, 0.27],
  [2.12, 1.88, 0.19, 0.20],
  [2.37, 1.79, 0.08, 0.12]
], 16), materials.body);

addMesh(root, "jaw", loftGeometry([
  [1.52, 1.78, 0.08, 0.22],
  [1.88, 1.76, 0.10, 0.20],
  [2.26, 1.72, 0.05, 0.10]
], 12), materials.under);

for (const side of [-1, 1]) {
  addTube(root, `horn_${side}`, [
    [ 1.58, 2.14, 0.10 * side],
    [ 1.35, 2.38, 0.12 * side],
    [ 0.96, 2.62, 0.14 * side],
    [ 0.50, 2.78, 0.16 * side],
    [-0.02, 2.90, 0.18 * side]
  ], 0.050, materials.accent, 8);

  addTube(root, `crest_${side}`, [
    [1.36, 2.09, 0.16 * side],
    [1.10, 2.28, 0.18 * side],
    [0.82, 2.34, 0.20 * side]
  ], 0.026, materials.accent, 7);

  const eye = addMesh(root, `eye_${side}`, new THREE.SphereGeometry(0.07, 12, 8), materials.eye);
  eye.position.set(1.93, 1.98, 0.235 * side);
}

const legs = [
  ["hindL", -0.92, -0.38],
  ["hindR", -0.92,  0.38],
  ["foreL",  0.56, -0.34],
  ["foreR",  0.56,  0.34]
];

for (const [name, x, z] of legs) {
  const hip = [x, 0.92, z];
  const knee = x < 0 ? [x + 0.18, 0.52, z] : [x - 0.10, 0.52, z];
  const ankle = x < 0 ? [x - 0.08, 0.12, z] : [x + 0.06, 0.12, z];
  const foot = [x + 0.16, 0.02, z];

  addTaperedSegment(root, `${name}_upper`, hip, knee, 0.115, 0.085, materials.body, 10);
  addTaperedSegment(root, `${name}_lower`, knee, ankle, 0.080, 0.055, materials.accent, 10);
  addTaperedSegment(root, `${name}_hoof`, ankle, foot, 0.060, 0.040, materials.accent, 8);
}

for (const [i, x, z] of [
  [0,  0.52, -0.43],
  [1,  0.52,  0.43],
  [2, -0.92, -0.44],
  [3, -0.92,  0.44]
]) {
  const plate = addMesh(root, `muscle_plate_${i}`, new THREE.SphereGeometry(0.24, 14, 9), materials.accent);
  plate.scale.set(1.0, 1.35, 0.65);
  plate.position.set(x, 1.13, z);
}

addTube(root, "tail", [
  [-1.58, 1.25, 0],
  [-1.95, 1.35, 0],
  [-2.28, 1.48, 0],
  [-2.62, 1.62, 0],
  [-2.92, 1.70, 0]
], 0.065, materials.accent, 9);

const bridge = addMesh(root, "cue_bridge", new THREE.BoxGeometry(0.38, 0.10, 0.72), materials.band);
bridge.position.set(1.72, 2.06, 0);

for (const side of [-1, 1]) {
  const pod = addMesh(root, `cue_pod_${side}`, new THREE.BoxGeometry(0.18, 0.22, 0.10), materials.cyan);
  pod.position.set(1.74, 1.98, 0.35 * side);
}

root.updateMatrixWorld(true);

const exporter = new OBJExporter();
const obj = exporter.parse(root);
const mtl = `# EvoWild Run S prototype
newmtl S_body
Kd 0.46 0.60 0.73
Ks 0.08 0.10 0.12
Ns 55

newmtl S_accent
Kd 0.13 0.21 0.31
Ks 0.10 0.14 0.18
Ns 70

newmtl S_under
Kd 0.72 0.78 0.82
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
