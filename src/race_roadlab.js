import * as THREE from "three";

/*
 * EvoWild Run Road Lab — WebGL 2.5D
 *
 * Creature: 2D animated S run-sheet billboard.
 * Course/environment: real 3D geometry rendered with Three.js.
 *
 * The earlier MIT pseudo-3D experiment remains documented in
 * /THIRD_PARTY_NOTICES.md, but this renderer no longer depends on that
 * projection code.
 */

const host = document.querySelector(".roadlab");
const canvas = document.querySelector("#roadCanvas");
const board = document.querySelector("#board");
const ui = {
  phase: document.querySelector("#phase"),
  clock: document.querySelector("#clock"),
  remain: document.querySelector("#remain"),
  rank: document.querySelector("#rank"),
  speed: document.querySelector("#speed")
};

const BASE = import.meta.env.BASE_URL || "/";
const RACER_COUNT = 8;
const LANES = 6;
const TRACK_WIDTH = 48;
const TRACK_SEGMENTS = 260;
const RACE_METERS = 1200;
const SELECTED_ID = 1;

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function lerp(a, b, t) {
  return a + (b - a) * t;
}

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  alpha: false,
  powerPreference: "high-performance"
});
const compactGpu = window.matchMedia?.("(max-width: 720px)")?.matches;
renderer.setPixelRatio(Math.min(devicePixelRatio || 1, compactGpu ? 1.05 : 1.35));
renderer.shadowMap.enabled = !compactGpu;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.08;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x7ba6bd);
scene.fog = new THREE.FogExp2(0x9fb7b6, 0.00175);

const camera = new THREE.PerspectiveCamera(46, 16 / 9, 0.1, 1800);

const hemi = new THREE.HemisphereLight(0xc9e7f2, 0x35543d, 2.15);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xffe7bc, 3.4);
sun.position.set(180, 260, 120);
sun.castShadow = true;
sun.shadow.mapSize.set(1024, 1024);
sun.shadow.camera.left = -140;
sun.shadow.camera.right = 140;
sun.shadow.camera.top = 140;
sun.shadow.camera.bottom = -140;
sun.shadow.camera.near = 1;
sun.shadow.camera.far = 520;
sun.shadow.bias = -0.00035;
scene.add(sun);

const sunDisc = new THREE.Mesh(
  new THREE.SphereGeometry(13, 24, 16),
  new THREE.MeshBasicMaterial({ color: 0xffe5a8, fog: false })
);
sunDisc.position.set(240, 170, -320);
scene.add(sunDisc);

function makeGrassTexture() {
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 512;
  const g = c.getContext("2d");
  g.fillStyle = "#3d704d";
  g.fillRect(0,0,512,512);

  for (let i=0;i<7200;i++) {
    const x=Math.random()*512;
    const y=Math.random()*512;
    const l=.8+Math.random()*2.8;
    const tone=Math.random();
    g.strokeStyle = tone>.5
      ? `rgba(132,166,101,${.035+Math.random()*.055})`
      : `rgba(19,69,43,${.03+Math.random()*.06})`;
    g.lineWidth=.45+Math.random()*.8;
    g.beginPath();
    g.moveTo(x,y);
    g.lineTo(x+(Math.random()-.5)*1.4,y-l);
    g.stroke();
  }

  const tex=new THREE.CanvasTexture(c);
  tex.wrapS=THREE.RepeatWrapping;
  tex.wrapT=THREE.RepeatWrapping;
  tex.repeat.set(34,34);
  tex.colorSpace=THREE.SRGBColorSpace;
  tex.anisotropy=Math.min(8,renderer.capabilities.getMaxAnisotropy());
  return tex;
}

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(1500, 1500),
  new THREE.MeshStandardMaterial({
    map: makeGrassTexture(),
    color: 0xb7c49f,
    roughness: 1,
    metalness: 0
  })
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = -2.1;
ground.receiveShadow = true;
scene.add(ground);

const dustMax = 140;
const dustPositions = new Float32Array(dustMax * 3);
const dustGeometry = new THREE.BufferGeometry();
dustGeometry.setAttribute("position", new THREE.BufferAttribute(dustPositions, 3));
const dustMaterial = new THREE.PointsMaterial({
  color: 0xc89463,
  size: 2.8,
  transparent: true,
  opacity: .38,
  depthWrite: false,
  sizeAttenuation: true
});
const dustPoints = new THREE.Points(dustGeometry, dustMaterial);
dustPoints.frustumCulled = false;
scene.add(dustPoints);
const dust = Array.from({length:dustMax},()=>({life:0,p:new THREE.Vector3(),v:new THREE.Vector3()}));
let dustCursor = 0;

function spawnDustAt(position, tangent, amount=2) {
  for(let i=0;i<amount;i++){
    const d=dust[dustCursor++%dustMax];
    d.life=.46 + Math.random()*.34;
    d.p.copy(position);
    d.p.x += (Math.random()-.5)*1.4;
    d.p.z += (Math.random()-.5)*1.4;
    d.p.y += .3 + Math.random()*.35;
    d.v.copy(tangent).multiplyScalar(-12 - Math.random()*10);
    d.v.x += (Math.random()-.5)*2.4;
    d.v.z += (Math.random()-.5)*2.4;
    d.v.y = 1.2 + Math.random()*2.1;
  }
}

function updateDust(dt){
  for(let i=0;i<dustMax;i++){
    const d=dust[i];
    if(d.life>0){
      d.life-=dt;
      d.p.addScaledVector(d.v,dt);
      d.v.y-=3.8*dt;
      dustPositions[i*3]=d.p.x;
      dustPositions[i*3+1]=d.p.y;
      dustPositions[i*3+2]=d.p.z;
    } else {
      dustPositions[i*3]=9999;
      dustPositions[i*3+1]=9999;
      dustPositions[i*3+2]=9999;
    }
  }
  dustGeometry.attributes.position.needsUpdate=true;
}

function makeDirtTexture() {
  const c = document.createElement("canvas");
  c.width = 512;
  c.height = 512;
  const g = c.getContext("2d");
  g.fillStyle = "#8b5d39";
  g.fillRect(0, 0, 512, 512);

  for (let i = 0; i < 5200; i++) {
    const v = 78 + Math.floor(Math.random() * 72);
    const a = .025 + Math.random() * .065;
    g.fillStyle = `rgba(${v+35},${v},${Math.max(35,v-28)},${a})`;
    const x = Math.random() * 512;
    const y = Math.random() * 512;
    const w = 1 + Math.random() * 6;
    const h = .5 + Math.random() * 1.6;
    g.fillRect(x, y, w, h);
  }

  g.strokeStyle = "rgba(63,39,25,.16)";
  g.lineWidth = 1.2;
  for (let i = 0; i < 28; i++) {
    const x = 14 + i * 18 + (i % 3) * 3;
    g.beginPath();
    g.moveTo(x, 0);
    g.bezierCurveTo(x + 5, 130, x - 4, 360, x + 3, 512);
    g.stroke();
  }

  const tex = new THREE.CanvasTexture(c);
  tex.wrapS = THREE.RepeatWrapping;
  tex.wrapT = THREE.RepeatWrapping;
  tex.repeat.set(2.2, 2.6);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
  return tex;
}

const controlPoints = [
  new THREE.Vector3(-175, 5, -18),
  new THREE.Vector3(-148, 10, -125),
  new THREE.Vector3(-58, 18, -188),
  new THREE.Vector3(58, 13, -184),
  new THREE.Vector3(154, 6, -120),
  new THREE.Vector3(198, 2, -18),
  new THREE.Vector3(168, 10, 92),
  new THREE.Vector3(82, 22, 164),
  new THREE.Vector3(-30, 26, 186),
  new THREE.Vector3(-138, 14, 126),
  new THREE.Vector3(-198, 6, 48)
];

const trackCurve = new THREE.CatmullRomCurve3(controlPoints, true, "catmullrom", 0.28);
const trackLength = trackCurve.getLength();

const up = new THREE.Vector3(0, 1, 0);
function trackFrame(u) {
  const center = trackCurve.getPointAt((u % 1 + 1) % 1);
  const tangent = trackCurve.getTangentAt((u % 1 + 1) % 1).normalize();
  const side = new THREE.Vector3().crossVectors(up, tangent).normalize();
  const bank = Math.sin(u * Math.PI * 6.0) * 0.045 + Math.sin(u * Math.PI * 2.0) * 0.025;
  return { center, tangent, side, bank };
}

const RUN_DIRECTIONS = ["side","front_3q","front","back_3q","back"];
const runAssetSpecs = [
  { key:"S:side", morph:"S", direction:"side", asset:"s-side-run-sheet.svg", cols:3, rows:2 },
  { key:"S:front_3q", morph:"S", direction:"front_3q", asset:"s-front-3q-run-sheet.webp", cols:6, rows:1 },
  { key:"S:front", morph:"S", direction:"front", asset:"s-front-run-sheet.webp", cols:6, rows:1 },
  { key:"S:back_3q", morph:"S", direction:"back_3q", asset:"s-back-3q-run-sheet.webp", cols:6, rows:1 },
  { key:"S:back", morph:"S", direction:"back", asset:"s-back-run-sheet.webp", cols:6, rows:1 },

  { key:"P:side", morph:"P", direction:"side", asset:"p-side-run-strip.svg", cols:6, rows:1 },
  { key:"P:front_3q", morph:"P", direction:"front_3q", asset:"p-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:0 },
  { key:"P:front", morph:"P", direction:"front", asset:"p-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:1 },
  { key:"P:back_3q", morph:"P", direction:"back_3q", asset:"p-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:2 },
  { key:"P:back", morph:"P", direction:"back", asset:"p-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:3 },

  { key:"E:side", morph:"E", direction:"side", asset:"e-side-run-strip.svg", cols:6, rows:1 },
  { key:"E:front_3q", morph:"E", direction:"front_3q", asset:"e-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:0 },
  { key:"E:front", morph:"E", direction:"front", asset:"e-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:1 },
  { key:"E:back_3q", morph:"E", direction:"back_3q", asset:"e-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:2 },
  { key:"E:back", morph:"E", direction:"back", asset:"e-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:3 },

  { key:"A:side", morph:"A", direction:"side", asset:"a-side-run-strip.svg", cols:6, rows:1 },
  { key:"A:front_3q", morph:"A", direction:"front_3q", asset:"a-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:0 },
  { key:"A:front", morph:"A", direction:"front", asset:"a-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:1 },
  { key:"A:back_3q", morph:"A", direction:"back_3q", asset:"a-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:2 },
  { key:"A:back", morph:"A", direction:"back", asset:"a-multidirection-run-atlas.svg", cols:6, rows:4, fixedRow:3 }
];
const availableMorphs = new Set(runAssetSpecs.map(x=>x.morph));
host.dataset.directionSet = "five-directions-all-morphs";
host.dataset.loadedMorphTarget = [...availableMorphs].join(",");
host.dataset.loadedDirectionTarget = RUN_DIRECTIONS.join(",");

function requiredDirectionForView(tangent, racerPosition) {
  const toCamera = camera.position.clone().sub(racerPosition);
  toCamera.y = 0;
  if (toCamera.lengthSq() < 0.0001) return "side";
  toCamera.normalize();

  const forward = tangent.clone();
  forward.y = 0;
  forward.normalize();

  const dot = clamp(forward.dot(toCamera), -1, 1);
  const absDot = Math.abs(dot);

  // side: camera within ±22.5° of a true side-on view.
  if (absDot <= 0.383) return "side";
  // diagonal: between side and head/tail-on.
  if (absDot <= 0.924) return dot > 0 ? "front_3q" : "back_3q";
  return dot > 0 ? "front" : "back";
}

function buildRibbon(width, yLift, material, lateralCenter = 0) {
  const positions = [];
  const uvs = [];
  const indices = [];
  const rows = 2;

  for (let i = 0; i <= TRACK_SEGMENTS; i++) {
    const u = i / TRACK_SEGMENTS;
    const { center, side, bank } = trackFrame(u);
    for (let j = 0; j <= rows; j++) {
      const f = j / rows - .5;
      const lateral = lateralCenter + f * width;
      const p = center.clone().addScaledVector(side, lateral);
      p.y += yLift + bank * lateral;
      positions.push(p.x, p.y, p.z);
      uvs.push(j / rows, u * 12);
    }
  }

  for (let i = 0; i < TRACK_SEGMENTS; i++) {
    for (let j = 0; j < rows; j++) {
      const a = i * (rows + 1) + j;
      const b = a + rows + 1;
      indices.push(a, b, a + 1, b, b + 1, a + 1);
    }
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setAttribute("uv", new THREE.Float32BufferAttribute(uvs, 2));
  geo.setIndex(indices);
  geo.computeVertexNormals();

  const mesh = new THREE.Mesh(geo, material);
  mesh.receiveShadow = true;
  return mesh;
}

const trackMat = new THREE.MeshStandardMaterial({
  map: makeDirtTexture(),
  color: 0xd5a06f,
  roughness: .94,
  metalness: 0
});
const track = buildRibbon(TRACK_WIDTH, 0, trackMat);
scene.add(track);

const shoulderMat = new THREE.MeshStandardMaterial({
  color: 0x756f63,
  roughness: .97,
  metalness: 0
});
scene.add(buildRibbon(TRACK_WIDTH + 4.6, -.18, shoulderMat));

function makeLaneStrip(offset, stripWidth, color, opacity = 1) {
  const positions = [];
  const indices = [];
  const material = new THREE.MeshBasicMaterial({
    color,
    transparent: opacity < 1,
    opacity,
    side: THREE.DoubleSide,
    depthWrite: opacity >= 1
  });

  for (let i = 0; i <= TRACK_SEGMENTS; i++) {
    const u = i / TRACK_SEGMENTS;
    const { center, side, bank } = trackFrame(u);
    for (const sign of [-1, 1]) {
      const lateral = offset + sign * stripWidth * .5;
      const p = center.clone().addScaledVector(side, lateral);
      p.y += .12 + bank * lateral;
      positions.push(p.x, p.y, p.z);
    }
  }

  for (let i = 0; i < TRACK_SEGMENTS; i++) {
    const a = i * 2;
    indices.push(a, a + 2, a + 1, a + 2, a + 3, a + 1);
  }

  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
  geo.setIndex(indices);
  return new THREE.Mesh(geo, material);
}

for (let lane = 1; lane < LANES; lane++) {
  const offset = -TRACK_WIDTH / 2 + lane * (TRACK_WIDTH / LANES);
  const strip = makeLaneStrip(offset, .18, 0xd8bb91, .22);
  strip.renderOrder = 3;
  scene.add(strip);
}

const edgeA = makeLaneStrip(-TRACK_WIDTH/2 + .42, .30, 0xead8b9, .72);
const edgeB = makeLaneStrip(TRACK_WIDTH/2 - .42, .30, 0xead8b9, .72);
edgeA.renderOrder = edgeB.renderOrder = 3;
scene.add(edgeA, edgeB);

function offsetCurve(offset, lift = 2.1) {
  const pts = [];
  for (let i = 0; i < 96; i++) {
    const u = i / 96;
    const { center, side, bank } = trackFrame(u);
    const p = center.clone().addScaledVector(side, offset);
    p.y += lift + bank * offset;
    pts.push(p);
  }
  return new THREE.CatmullRomCurve3(pts, true, "catmullrom", .2);
}

const railMaterial = new THREE.MeshStandardMaterial({
  color: 0xcfd9da,
  roughness: .42,
  metalness: .52
});
for (const offset of [-TRACK_WIDTH/2 - 2.3, TRACK_WIDTH/2 + 2.3]) {
  const nearSide = offset > 0;
  const rail = new THREE.Mesh(
    new THREE.TubeGeometry(offsetCurve(offset, nearSide ? 1.25 : 2.35), 220, nearSide ? .13 : .20, 5, true),
    railMaterial
  );
  rail.castShadow = false;
  scene.add(rail);
}

const postGeo = new THREE.CylinderGeometry(.20, .26, 4.4, 6);
const postMat = new THREE.MeshStandardMaterial({ color: 0xc7d1d2, roughness: .52, metalness: .35 });
const postCount = 72;
const posts = new THREE.InstancedMesh(postGeo, postMat, postCount * 2);
posts.castShadow = false;
posts.receiveShadow = true;
const dummy = new THREE.Object3D();
let postIndex = 0;
for (let i = 0; i < postCount; i++) {
  const u = i / postCount;
  const { center, side, bank } = trackFrame(u);
  for (const offset of [-TRACK_WIDTH/2 - 2.3, TRACK_WIDTH/2 + 2.3]) {
    const p = center.clone().addScaledVector(side, offset);
    p.y += 2.2 + bank * offset;
    dummy.position.copy(p);
    dummy.rotation.set(0, 0, 0);
    dummy.updateMatrix();
    posts.setMatrixAt(postIndex++, dummy.matrix);
  }
}
scene.add(posts);

function addMountains() {
  const farMat = new THREE.MeshStandardMaterial({ color: 0x6f817f, roughness: 1, flatShading: true });
  const midMat = new THREE.MeshStandardMaterial({ color: 0x526b63, roughness: 1, flatShading: true });

  for (let i=0;i<30;i++) {
    const a=(i/30)*Math.PI*2;
    const radius=430 + (i%5)*18;
    const h=42 + ((i*37)%58);
    const w=42 + ((i*23)%44);
    const mat=i%3===0 ? midMat : farMat;
    const mountain=new THREE.Mesh(new THREE.ConeGeometry(1,1,9),mat);
    mountain.scale.set(w,h,w*.72);
    mountain.position.set(Math.cos(a)*radius,h*.47-10,Math.sin(a)*radius);
    mountain.rotation.y=a*.7 + (i%4)*.13;
    mountain.receiveShadow=true;
    scene.add(mountain);

    if(i%2===0){
      const shoulder=new THREE.Mesh(new THREE.IcosahedronGeometry(1,1),mat);
      shoulder.scale.set(w*.72,h*.42,w*.58);
      shoulder.position.set(
        Math.cos(a)*radius + Math.sin(a)*w*.34,
        h*.22-9,
        Math.sin(a)*radius - Math.cos(a)*w*.34
      );
      shoulder.rotation.y=a;
      scene.add(shoulder);
    }
  }
}
addMountains();

function addGrandstand(u, sideSign) {
  const { center, side, tangent } = trackFrame(u);
  const root = new THREE.Group();
  const pos = center.clone().addScaledVector(side, sideSign * (TRACK_WIDTH/2 + 46));
  root.position.copy(pos);

  const yaw = Math.atan2(tangent.x, tangent.z);
  root.rotation.y = yaw;

  const baseMat = new THREE.MeshStandardMaterial({ color: 0x31434c, roughness: .8 });
  const seatMat = new THREE.MeshStandardMaterial({ color: 0x667980, roughness: .9 });
  for (let tier = 0; tier < 4; tier++) {
    const tierMesh = new THREE.Mesh(
      new THREE.BoxGeometry(46, 3.0, 7),
      tier % 2 ? seatMat : baseMat
    );
    tierMesh.position.set(0, 2.0 + tier*2.7, sideSign * (-tier*1.8));
    tierMesh.castShadow = true;
    tierMesh.receiveShadow = true;
    root.add(tierMesh);
  }
  const roof = new THREE.Mesh(
    new THREE.BoxGeometry(54, 1.0, 11),
    new THREE.MeshStandardMaterial({ color: 0xd4d9d6, roughness: .42, metalness: .24 })
  );
  roof.position.set(0, 13.7, sideSign * -6.4);
  root.add(roof);
  scene.add(root);
}
addGrandstand(.22, 1);
addGrandstand(.61, -1);

const billboardMat = new THREE.MeshBasicMaterial({ color: 0x153643 });
const glowMat = new THREE.MeshBasicMaterial({ color: 0x64d7f7 });
for (const u of [.16,.31,.47,.68,.84]) {
  const { center, side, tangent } = trackFrame(u);
  const sign = Math.floor(u*100)%2 ? 1 : -1;
  const root = new THREE.Group();
  root.position.copy(center.clone().addScaledVector(side,sign*(TRACK_WIDTH/2+17)));
  root.rotation.y = Math.atan2(tangent.x,tangent.z);
  const panel = new THREE.Mesh(new THREE.BoxGeometry(16,6,.7),billboardMat);
  panel.position.y=5.4;
  root.add(panel);
  const bar = new THREE.Mesh(new THREE.BoxGeometry(10,.55,.82),glowMat);
  bar.position.set(0,5.4,.5);
  root.add(bar);
  scene.add(root);
}

function addTracksideTrees() {
  const trunkGeo = new THREE.CylinderGeometry(.24,.42,4.9,6);
  const crownGeo = new THREE.DodecahedronGeometry(2.7,0);
  const trunkMat = new THREE.MeshStandardMaterial({ color:0x4a3828, roughness:1 });
  const crownMat = new THREE.MeshStandardMaterial({ color:0x28543b, roughness:1, flatShading:true });
  const count = 92;
  const trunks = new THREE.InstancedMesh(trunkGeo,trunkMat,count);
  const crowns = new THREE.InstancedMesh(crownGeo,crownMat,count*3);
  const d = new THREE.Object3D();
  const c = new THREE.Color();
  let crownIndex=0;

  for(let i=0;i<count;i++){
    const u=(i+.27)/count;
    const {center,side}=trackFrame(u);
    const sign=i%2===0?1:-1;
    const distance=TRACK_WIDTH/2 + 20 + (i%7)*5.2;
    const p=center.clone().addScaledVector(side,sign*distance);
    p.y += 2.15;
    const scale=.68 + ((i*17)%10)/22;

    d.position.copy(p);
    d.scale.set(scale,scale,scale);
    d.rotation.y=(i*1.71)%Math.PI;
    d.updateMatrix();
    trunks.setMatrixAt(i,d.matrix);

    const crownBase=p.clone();
    crownBase.y += 5.4*scale;
    const lobes=[
      [-1.25,0,.15,1.00,1.22,.92],
      [1.20,.18,-.20,.94,1.12,1.02],
      [.05,1.45,.28,1.14,1.30,1.08]
    ];

    for(const [ox,oy,oz,sx,sy,sz] of lobes){
      d.position.set(
        crownBase.x + ox*scale,
        crownBase.y + oy*scale,
        crownBase.z + oz*scale
      );
      d.scale.set(scale*sx,scale*sy,scale*sz);
      d.rotation.set((i%3)*.08,(i*.73)%Math.PI,(i%2)*.06);
      d.updateMatrix();
      crowns.setMatrixAt(crownIndex,d.matrix);
      c.setHSL(.31 + ((i+crownIndex)%5)*.008,.34,.24 + ((i*3)%6)*.012);
      crowns.setColorAt(crownIndex,c);
      crownIndex++;
    }
  }

  trunks.castShadow=false;
  crowns.castShadow=false;
  crowns.instanceColor.needsUpdate=true;
  scene.add(trunks,crowns);
}
addTracksideTrees();

function createShadow() {
  const geo = new THREE.CircleGeometry(1, 28);
  const mat = new THREE.MeshBasicMaterial({
    color: 0x1b130f,
    transparent: true,
    opacity: .22,
    depthWrite: false
  });
  const m = new THREE.Mesh(geo, mat);
  m.rotation.x = -Math.PI / 2;
  m.scale.set(6.2, 2.5, 1);
  return m;
}

const names = ["Vela","Aster","Mica","Rook","Nacre","Ilex","Lumen","Tern"];
const morphSeed = ["S","P","E","A","S","P","E","A"];
const laneSeed = [2,4,1,5,3,0,4,1];
const startGap = [0,2.5,-1.5,4.5,-3.5,6.5,8.0,-5.0];
const baseSpeed = [29.8,29.6,30.0,29.5,29.9,29.6,30.0,29.7];

const racers = [];
const textureLoader = new THREE.TextureLoader();

function frameTexture(baseTexture, cols, rows) {
  const t = baseTexture.clone();
  t.needsUpdate = true;
  t.wrapS = THREE.RepeatWrapping;
  t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(1/cols,1/rows);
  t.colorSpace = THREE.SRGBColorSpace;
  return t;
}

function setFrame(texture, frame, cols, rows, fixedRow = null) {
  const col = frame % cols;
  const row = fixedRow == null ? Math.floor(frame / cols) : fixedRow;
  texture.offset.x = col / cols;
  texture.offset.y = (rows - 1 - row) / rows;
}

function createRacers(assetMap) {
  for (let i = 0; i < RACER_COUNT; i++) {
    const morph = morphSeed[i];
    const directions = {};

    for (const direction of RUN_DIRECTIONS) {
      const entry = assetMap[`${morph}:${direction}`];
      if (!entry) continue;
      directions[direction] = {
        texture: frameTexture(entry.texture, entry.spec.cols, entry.spec.rows),
        spec: entry.spec
      };
    }

    if (!directions.side) throw new Error(`Missing SIDE run asset for morph ${morph}`);

    const mat = new THREE.SpriteMaterial({
      map: directions.side.texture,
      transparent: true,
      depthWrite: false,
      alphaTest: .04,
      color: 0xffffff
    });
    const sprite = new THREE.Sprite(mat);
    sprite.scale.set(10.6,10.6,1);
    sprite.renderOrder = 8;
    scene.add(sprite);

    const shadow = createShadow();
    scene.add(shadow);

    const marker = new THREE.Mesh(
      new THREE.ConeGeometry(.75,1.8,3),
      new THREE.MeshBasicMaterial({ color: 0x63dcff })
    );
    marker.rotation.z = Math.PI;
    marker.visible = i === 0;
    scene.add(marker);

    racers.push({
      id:i+1,
      name:names[i],
      morph,
      lane:laneSeed[i],
      laneF:laneSeed[i],
      targetLane:laneSeed[i],
      baseSpeed:baseSpeed[i],
      speed:baseSpeed[i],
      totalDistance:startGap[i],
      stamina:100,
      seed:i*1.73,
      cooldown:0,
      sprite,
      shadow,
      marker,
      directions,
      currentDirection:"side",
      frame:-1,
      requiredDirection:"side"
    });
  }
  host.dataset.state = "ready";
}

function loadRunAsset(spec) {
  return new Promise((resolve, reject) => {
    textureLoader.load(
      BASE + "concept/" + spec.asset,
      (tex) => {
        tex.colorSpace = THREE.SRGBColorSpace;
        tex.minFilter = THREE.LinearMipmapLinearFilter;
        tex.magFilter = THREE.LinearFilter;
        tex.generateMipmaps = true;
        tex.anisotropy = Math.min(8, renderer.capabilities.getMaxAnisotropy());
        resolve([spec.key, { texture:tex, spec }]);
      },
      undefined,
      reject
    );
  });
}

Promise.all(runAssetSpecs.map(loadRunAsset)).then((entries) => {
  const assetMap = Object.fromEntries(entries);
  createRacers(assetMap);
  host.dataset.loadedMorphs = [...new Set(runAssetSpecs.map(x=>x.morph))].join(",");
}).catch((err) => {
  host.dataset.state = "asset-error";
  console.error(err);
});

function rankOrder() {
  return [...racers].sort((a,b)=>b.totalDistance-a.totalDistance);
}

function updateRacer(r, dt) {
  r.cooldown = Math.max(0,r.cooldown-dt);

  const lapU = ((r.totalDistance % trackLength)+trackLength)%trackLength / trackLength;
  const late = lapU > .76 ? 1.025 : lapU > .52 ? 1.010 : 1;
  const fatigue = .91 + .09*(r.stamina/100);
  const pulse = 1 + Math.sin(performance.now()*.0011+r.seed)*.006;
  const targetSpeed = r.baseSpeed*late*fatigue*pulse;
  r.speed += (targetSpeed-r.speed)*Math.min(1,dt*1.8);

  const ahead = racers
    .filter(o=>o!==r && Math.round(o.laneF)===Math.round(r.laneF) && o.totalDistance>r.totalDistance && o.totalDistance-r.totalDistance<18)
    .sort((a,b)=>a.totalDistance-b.totalDistance)[0];

  if(ahead && r.cooldown<=0){
    const options=[r.targetLane-1,r.targetLane+1].filter(l=>l>=0&&l<LANES);
    const free=options.find(l=>racers.every(o=>o===r || Math.round(o.laneF)!==l || Math.abs(o.totalDistance-r.totalDistance)>16));
    if(free!==undefined){
      r.targetLane=free;
      r.cooldown=1.0;
    }
  }

  r.laneF += (r.targetLane-r.laneF)*Math.min(1,dt*3.2);
  r.totalDistance += r.speed*dt;
  r.stamina = Math.max(20,r.stamina-(.016+Math.max(0,r.speed/r.baseSpeed-1)*.12)*dt);
}

function placeRacer(r, elapsedMs) {
  const u = (((r.totalDistance % trackLength)+trackLength)%trackLength) / trackLength;
  const { center, side, bank, tangent } = trackFrame(u);
  const laneWidth = TRACK_WIDTH / LANES;
  const lateral = -TRACK_WIDTH/2 + laneWidth*(r.laneF+.5);
  const p = center.clone().addScaledVector(side,lateral);
  p.y += 2.7 + bank*lateral;
  r.sprite.position.copy(p);

  const requiredDirection = requiredDirectionForView(tangent, p);
  const dirEntry = r.directions[requiredDirection];
  const directionReady = Boolean(dirEntry);
  r.requiredDirection = requiredDirection;
  r.sprite.visible = directionReady;
  r.shadow.visible = directionReady;
  r.marker.visible = r.id === SELECTED_ID && directionReady;

  const frameMs = 94 - clamp((r.speed-r.baseSpeed)*2.4,-10,12);
  const frame = Math.floor((elapsedMs+r.id*43)/frameMs)%6;

  if (directionReady && r.currentDirection !== requiredDirection) {
    r.currentDirection = requiredDirection;
    r.sprite.material.map = dirEntry.texture;
    r.sprite.material.needsUpdate = true;
    setFrame(
      dirEntry.texture,
      frame,
      dirEntry.spec.cols,
      dirEntry.spec.rows,
      dirEntry.spec.fixedRow ?? null
    );
  }

  if(frame!==r.frame){
    r.frame=frame;
    if (directionReady) {
      setFrame(
        dirEntry.texture,
        frame,
        dirEntry.spec.cols,
        dirEntry.spec.rows,
        dirEntry.spec.fixedRow ?? null
      );
    }
    if(frame===0 || frame===5){
      spawnDustAt(r.shadow.position, tangent, r.id===SELECTED_ID ? 5 : 3);
    }
  }

  r.sprite.material.rotation = -bank * .75 + Math.sin((elapsedMs + r.id*37) * .010) * .012;

  const bobByMorph = {
    S:[0,.08,.32,.58,.30,0],
    P:[0,.04,.18,.34,.16,0],
    E:[0,.03,.12,.22,.10,0],
    A:[0,.10,.38,.64,.30,0]
  };
  const bob=(bobByMorph[r.morph] || bobByMorph.S)[frame];
  r.sprite.position.y += bob;

  const scaleByMorph = { S:9.8, P:10.6, E:10.0, A:9.6 };
  const drawScale=(scaleByMorph[r.morph] || 10.2) + (r.id===SELECTED_ID ? .28 : 0);

  const here = p.clone().project(camera);
  const ahead = p.clone().addScaledVector(tangent, 2).project(camera);
  const facingSign = requiredDirection === "side" && ahead.x > here.x ? -1 : 1;
  r.sprite.scale.set(drawScale * facingSign,drawScale,1);

  r.shadow.position.copy(center.clone().addScaledVector(side,lateral));
  r.shadow.position.y += .18 + bank*lateral;
  r.shadow.scale.set(r.morph==="P" ? 6.2 : 5.7, r.morph==="A" ? 1.9 : 2.15, 1);

  r.marker.position.copy(p);
  r.marker.position.y += 10.2;
}

const camPos = new THREE.Vector3();
const camLook = new THREE.Vector3();
const desiredCam = new THREE.Vector3();
const desiredLook = new THREE.Vector3();

const SHOTS = [
  { key:"side",     side:31, along:0,   height:6.8, lookAhead:5,  fov:43 },
  { key:"front_3q", side:22, along:27,  height:7.6, lookAhead:2,  fov:46 },
  { key:"front",    side:6,  along:31,  height:8.1, lookAhead:-1, fov:48 },
  { key:"back_3q",  side:20, along:-27, height:7.2, lookAhead:8,  fov:46 },
  { key:"back",     side:6,  along:-31, height:7.8, lookAhead:11, fov:48 }
];
const shotParam = new URLSearchParams(location.search).get("shot");
const shotAliases = { front3q:"front_3q", back3q:"back_3q" };
const forcedShotKey = shotAliases[shotParam] || shotParam || null;

function currentShot() {
  if (forcedShotKey) return SHOTS.find(s=>s.key===forcedShotKey) || SHOTS[0];
  const seconds=elapsed/1000;
  const slot=Math.floor(seconds/5.2)%SHOTS.length;
  return SHOTS[slot];
}

function updateCamera(dt) {
  if(!racers.length)return;
  const me = racers[0];
  const u = (((me.totalDistance % trackLength)+trackLength)%trackLength) / trackLength;
  const { center, tangent, side, bank } = trackFrame(u);
  const laneWidth = TRACK_WIDTH/LANES;
  const lateral = -TRACK_WIDTH/2 + laneWidth*(me.laneF+.5);
  const target = center.clone().addScaledVector(side,lateral);
  target.y += 2.6 + bank*lateral;

  const shot=currentShot();
  host.dataset.cameraMode=shot.key;

  desiredCam.copy(target)
    .addScaledVector(side,shot.side)
    .addScaledVector(tangent,shot.along)
    .add(new THREE.Vector3(0,shot.height,0));

  desiredLook.copy(target)
    .addScaledVector(tangent,shot.lookAhead)
    .add(new THREE.Vector3(0,2.2,0));

  const posAlpha=1-Math.pow(.0007,dt);
  const lookAlpha=1-Math.pow(.0018,dt);
  camPos.lerp(desiredCam,posAlpha);
  camLook.lerp(desiredLook,lookAlpha);

  const gaitImpact = [0,.06,.17,.30,.15,0][me.frame<0?0:me.frame];
  camera.position.copy(camPos);
  camera.position.y += gaitImpact*.13;
  camera.lookAt(camLook);

  const speedRatio=clamp(me.speed/me.baseSpeed,.94,1.06);
  camera.fov = lerp(camera.fov,shot.fov+(speedRatio-1)*16,.10);
  camera.updateProjectionMatrix();
}

function fmt(ms){
  const t=ms/1000;
  const m=Math.floor(t/60);
  const s=Math.floor(t%60);
  const cs=Math.floor((t-Math.floor(t))*100);
  return `${String(m).padStart(2,"0")}:${String(s).padStart(2,"0")}.${String(cs).padStart(2,"0")}`;
}
function phaseOf(progress){
  if(progress<.12)return "START";
  if(progress<.60)return "MID";
  if(progress<.84)return "BUILD";
  return "FINAL";
}

let elapsed=0;
let last=performance.now();
let lastBoardPaint=0;

function updateUI(now){
  if(!racers.length)return;
  const me=racers[0];
  const order=rankOrder();
  const rank=order.findIndex(r=>r===me)+1;
  const progress=(((me.totalDistance%trackLength)+trackLength)%trackLength)/trackLength;

  ui.phase.textContent=phaseOf(progress);
  ui.clock.textContent=fmt(elapsed);
  ui.remain.textContent=`${Math.max(0,Math.round((1-progress)*RACE_METERS))} m to go`;
  ui.rank.textContent=rank;
  ui.speed.textContent=me.speed.toFixed(1);

  host.dataset.running="true";
  host.dataset.frame=String(me.frame);
  host.dataset.renderer="webgl-3d-course-2d-creatures";
  host.dataset.selectedDirection=me.requiredDirection || "side";
  host.dataset.directionReady=Boolean(me.directions[me.requiredDirection || "side"]) ? "true" : "false";
  host.dataset.selectedMorph=me.morph;

  if(now-lastBoardPaint>150){
    lastBoardPaint=now;
    const lead=order[0].totalDistance;
    board.innerHTML=order.slice(0,6).map((r,i)=>{
      const gap=Math.max(0,lead-r.totalDistance);
      return `<div class="board-row ${r===me?"me":""}">
        <span class="p">${i+1}</span>
        <span class="n">#${String(r.id).padStart(2,"0")} ${r.morph} · ${r.name}</span>
        <span class="g">${i===0?"LEAD":"+"+gap.toFixed(1)+"m"}</span>
      </div>`;
    }).join("");
  }
}

function resize(){
  const w=Math.max(320,canvas.clientWidth);
  const h=Math.max(480,canvas.clientHeight);
  renderer.setSize(w,h,false);
  camera.aspect=w/h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(canvas);
resize();

function animate(now){
  try {
    const dt=Math.min(.05,(now-last)/1000);
    last=now;
    elapsed+=dt*1000;

    for(const r of racers){
      updateRacer(r,dt);
      placeRacer(r,elapsed);
    }
    updateCamera(dt);
    updateUI(now);

    renderer.render(scene,camera);
    requestAnimationFrame(animate);
  } catch (error) {
    host.dataset.runtimeError = String(error?.message || error);
    console.error("ROADLAB_RUNTIME_ERROR", error);
  }
}

requestAnimationFrame(now=>{
  last=now;
  if(racers.length){
    const me=racers[0];
    const u=(((me.totalDistance%trackLength)+trackLength)%trackLength)/trackLength;
    const {center,tangent,side}=trackFrame(u);
    const shot=currentShot();
    camPos.copy(center)
      .addScaledVector(side,shot.side)
      .addScaledVector(tangent,shot.along)
      .add(new THREE.Vector3(0,shot.height,0));
    camLook.copy(center)
      .addScaledVector(tangent,shot.lookAhead)
      .add(new THREE.Vector3(0,2.2,0));
    camera.position.copy(camPos);
    camera.lookAt(camLook);
  }
  animate(now);
});
