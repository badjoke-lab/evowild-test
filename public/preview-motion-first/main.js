import * as THREE from "three";

const canvas = document.querySelector("#scene");
const loading = document.querySelector("#loading");
const raceStateEl = document.querySelector("#raceState");
const distanceEl = document.querySelector("#distanceReadout");
const fpsEl = document.querySelector("#fpsReadout");
const speedEl = document.querySelector("#speedReadout");
const morphEl = document.querySelector("#morphReadout");
const runnerNameEl = document.querySelector("#runnerName");
const positionEl = document.querySelector("#positionReadout");
const cameraEl = document.querySelector("#cameraReadout");
const runnerSelect = document.querySelector("#runnerSelect");
const pauseButton = document.querySelector("#pauseButton");
const restartButton = document.querySelector("#restartButton");
const cameraButtons = [...document.querySelectorAll(".cam")];

const RACE_DISTANCE = 1600;
const LANE_COUNT = 9;
const LANE_WIDTH = 2.55;
const TRACK_WIDTH = LANE_COUNT * LANE_WIDTH + 5;
const RUNNER_COUNT = 18;
const WORLD_END = 1800;
const params = new URLSearchParams(window.location.search);
const INSPECT_MODE = params.get("inspect") === "1";
const MOTION_REVIEW_MODE = params.get("motion") === "1" || window.location.pathname.includes("/preview-motion-first-gait/");
const TAU = Math.PI * 2;
const S_GAIT = {
  baseY: 1.60,
  reviewBaseY: 2.16,
  minStrideWorld: 3.8,
  maxStrideWorld: 6.2,
  stance: 0.30,
  swingLift: 0.50,
  chestBaseZ: 0.58,
  pelvisBaseZ: -0.70,
  chestBaseY: 0.01,
  pelvisBaseY: -0.05
};

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x92a7b3);
scene.fog = new THREE.Fog(0x92a7b3, 55, 230);

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: "high-performance"
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.5));
renderer.setSize(window.innerWidth, window.innerHeight, false);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.0;

const camera = new THREE.PerspectiveCamera(
  58,
  window.innerWidth / window.innerHeight,
  0.1,
  500
);
scene.add(camera);

const hemi = new THREE.HemisphereLight(0xe8f2ff, 0x31412d, 2.25);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xfff2dd, 3.0);
sun.position.set(-24, 38, -20);
scene.add(sun);

const clock = new THREE.Clock();
const cameraLook = new THREE.Vector3();
const desiredCamera = new THREE.Vector3();
const desiredLook = new THREE.Vector3();
const tempV = new THREE.Vector3();

const COLORS = [
  0xe65050, 0x3a88e8, 0x56be6e, 0xe2bd43, 0x965ce7, 0x48c7c4,
  0xee7d38, 0xe05ca4, 0x94c54d, 0x6988ef, 0xd7d7d7, 0xc8884d,
  0x5bce9e, 0xb666e6, 0xe3a9a0, 0x71b1de, 0xd4d05a, 0x9b9b9b
];

const MORPHS = {
  S: {
    label: "SPRINT",
    body: [0.78, 0.82, 1.28],
    pelvis: [0.72, 0.76, 1.05],
    head: [0.46, 0.48, 0.72],
    neck: 0.95,
    leg: 1.38,
    legWidth: 0.13,
    tail: 1.75,
    cadence: 1.24,
    stride: 1.16,
    bob: 0.10,
    pitch: 0.11,
    footLift: 0.58,
    contact: 0.82,
    laneLean: 0.10,
    baseSpeed: 22.8,
    accel: 3.0
  },
  P: {
    label: "POWER",
    body: [1.03, 1.05, 1.24],
    pelvis: [1.04, 1.02, 1.05],
    head: [0.62, 0.60, 0.70],
    neck: 0.72,
    leg: 1.12,
    legWidth: 0.19,
    tail: 1.38,
    cadence: 0.92,
    stride: 0.98,
    bob: 0.17,
    pitch: 0.08,
    footLift: 0.42,
    contact: 1.05,
    laneLean: 0.07,
    baseSpeed: 21.8,
    accel: 3.45
  },
  E: {
    label: "ENDURE",
    body: [0.88, 0.88, 1.42],
    pelvis: [0.84, 0.84, 1.13],
    head: [0.52, 0.52, 0.66],
    neck: 0.92,
    leg: 1.27,
    legWidth: 0.15,
    tail: 1.55,
    cadence: 1.00,
    stride: 1.08,
    bob: 0.105,
    pitch: 0.065,
    footLift: 0.46,
    contact: 0.94,
    laneLean: 0.085,
    baseSpeed: 22.15,
    accel: 2.75
  },
  A: {
    label: "AGILITY",
    body: [0.85, 0.82, 1.13],
    pelvis: [0.82, 0.80, 0.98],
    head: [0.48, 0.48, 0.62],
    neck: 0.72,
    leg: 1.18,
    legWidth: 0.145,
    tail: 1.72,
    cadence: 1.14,
    stride: 1.01,
    bob: 0.125,
    pitch: 0.08,
    footLift: 0.54,
    contact: 0.88,
    laneLean: 0.145,
    baseSpeed: 22.25,
    accel: 3.15
  }
};

function mat(color, roughness = 0.9) {
  return new THREE.MeshStandardMaterial({
    color,
    roughness,
    metalness: 0,
    flatShading: true
  });
}

function makeMesh(geometry, material, parent, position = [0, 0, 0], scale = [1, 1, 1]) {
  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(...position);
  mesh.scale.set(...scale);
  parent.add(mesh);
  return mesh;
}

function addWorld() {
  const groundMat = new THREE.MeshStandardMaterial({ color: 0x4f6844, roughness: 1 });
  const ground = new THREE.Mesh(new THREE.PlaneGeometry(160, WORLD_END + 500), groundMat);
  ground.rotation.x = -Math.PI / 2;
  ground.position.set(0, -0.03, WORLD_END / 2 - 100);
  scene.add(ground);

  const trackMat = new THREE.MeshStandardMaterial({ color: 0x3a4146, roughness: 1 });
  const track = new THREE.Mesh(new THREE.PlaneGeometry(TRACK_WIDTH, WORLD_END + 200), trackMat);
  track.rotation.x = -Math.PI / 2;
  track.position.set(0, 0, WORLD_END / 2 - 50);
  scene.add(track);

  const shoulderMat = new THREE.MeshStandardMaterial({ color: 0xc1a16a, roughness: 1 });
  [-TRACK_WIDTH / 2 - 1.3, TRACK_WIDTH / 2 + 1.3].forEach((x) => {
    const shoulder = new THREE.Mesh(
      new THREE.PlaneGeometry(2.2, WORLD_END + 200),
      shoulderMat
    );
    shoulder.rotation.x = -Math.PI / 2;
    shoulder.position.set(x, 0.008, WORLD_END / 2 - 50);
    scene.add(shoulder);
  });

  const lineMat = new THREE.MeshBasicMaterial({
    color: 0xd8dde0,
    transparent: true,
    opacity: 0.62
  });

  for (let lane = 1; lane < LANE_COUNT; lane += 1) {
    const x = -((LANE_COUNT - 1) * LANE_WIDTH) / 2 + lane * LANE_WIDTH - LANE_WIDTH / 2;
    const line = new THREE.Mesh(
      new THREE.PlaneGeometry(0.055, WORLD_END + 180),
      lineMat
    );
    line.rotation.x = -Math.PI / 2;
    line.position.set(x, 0.015, WORLD_END / 2 - 50);
    scene.add(line);
  }

  const railGeo = new THREE.BoxGeometry(0.10, 0.62, 4.6);
  const railMat = new THREE.MeshStandardMaterial({ color: 0xd7dbd6, roughness: 0.92 });
  const railCount = 2 * 210;
  const rails = new THREE.InstancedMesh(railGeo, railMat, railCount);
  const matrix = new THREE.Matrix4();
  let index = 0;
  for (let i = -10; i < 200; i += 1) {
    const z = i * 9;
    for (const side of [-1, 1]) {
      matrix.makeTranslation(side * (TRACK_WIDTH / 2 + 2.55), 0.48, z);
      rails.setMatrixAt(index++, matrix);
    }
  }
  scene.add(rails);

  const postGeo = new THREE.BoxGeometry(0.13, 1.05, 0.13);
  const postMat = new THREE.MeshStandardMaterial({ color: 0xe7e7df, roughness: 1 });
  const posts = new THREE.InstancedMesh(postGeo, postMat, 2 * 180);
  index = 0;
  for (let i = -6; i < 174; i += 1) {
    const z = i * 10.5;
    for (const side of [-1, 1]) {
      matrix.makeTranslation(side * (TRACK_WIDTH / 2 + 2.55), 0.52, z);
      posts.setMatrixAt(index++, matrix);
    }
  }
  scene.add(posts);

  const treeTrunkGeo = new THREE.CylinderGeometry(0.14, 0.19, 1.4, 5);
  const treeTrunkMat = new THREE.MeshStandardMaterial({ color: 0x62513b, roughness: 1 });
  const treeTopGeo = new THREE.ConeGeometry(0.9, 2.1, 7);
  const treeTopMat = new THREE.MeshStandardMaterial({ color: 0x355d3f, roughness: 1 });
  const treeCount = 64;
  const trunks = new THREE.InstancedMesh(treeTrunkGeo, treeTrunkMat, treeCount);
  const tops = new THREE.InstancedMesh(treeTopGeo, treeTopMat, treeCount);
  const m1 = new THREE.Matrix4();
  const m2 = new THREE.Matrix4();
  for (let i = 0; i < treeCount; i += 1) {
    const side = i % 2 === 0 ? -1 : 1;
    const row = Math.floor(i / 2);
    const z = 10 + row * 47 + (i % 5) * 3;
    const x = side * (TRACK_WIDTH / 2 + 7.5 + (i % 3) * 1.7);
    m1.makeTranslation(x, 0.7, z);
    m2.compose(
      new THREE.Vector3(x, 2.1, z),
      new THREE.Quaternion(),
      new THREE.Vector3(1 + (i % 4) * 0.08, 1 + (i % 3) * 0.09, 1 + (i % 4) * 0.08)
    );
    trunks.setMatrixAt(i, m1);
    tops.setMatrixAt(i, m2);
  }
  scene.add(trunks, tops);

  const standMat = new THREE.MeshStandardMaterial({ color: 0x8c969d, roughness: 1 });
  for (let i = 0; i < 8; i += 1) {
    const stand = new THREE.Mesh(new THREE.BoxGeometry(9, 3.3, 20), standMat);
    stand.position.set(
      (i % 2 === 0 ? -1 : 1) * (TRACK_WIDTH / 2 + 12.5),
      1.65,
      120 + i * 190
    );
    scene.add(stand);
  }

  const markerMat = new THREE.MeshBasicMaterial({ color: 0xf2f2ec });
  for (let z = 100; z <= RACE_DISTANCE; z += 100) {
    const marker = new THREE.Mesh(new THREE.BoxGeometry(0.38, 1.5, 0.12), markerMat);
    marker.position.set(TRACK_WIDTH / 2 + 4.0, 0.75, z);
    scene.add(marker);
  }
}

function makeLeg(parent, colorMat, legLength, width, x, z, phaseOffset) {
  const hip = new THREE.Group();
  hip.position.set(x, 0.0, z);
  parent.add(hip);

  const upperLen = legLength * 0.52;
  const lowerLen = legLength * 0.48;

  const upper = makeMesh(
    new THREE.CylinderGeometry(width * 0.78, width, upperLen, 5),
    colorMat,
    hip,
    [0, -upperLen / 2, 0]
  );

  const knee = new THREE.Group();
  knee.position.y = -upperLen;
  hip.add(knee);

  makeMesh(
    new THREE.CylinderGeometry(width * 0.58, width * 0.72, lowerLen, 5),
    colorMat,
    knee,
    [0, -lowerLen / 2, 0]
  );

  const foot = makeMesh(
    new THREE.BoxGeometry(width * 1.55, width * 0.65, width * 2.25),
    colorMat,
    knee,
    [0, -lowerLen - width * 0.15, width * 0.46]
  );

  return { hip, knee, foot, phaseOffset, upperLen, lowerLen };
}

function makeTaperedPlate(length, width, height, material, parent, position = [0, 0, 0]) {
  const rearZ = -length / 2;
  const frontZ = length / 2;
  const tipWidth = width * 0.16;
  const tipHeight = height * 0.34;

  const vertices = new Float32Array([
    -width / 2, -height / 2, rearZ,
     width / 2, -height / 2, rearZ,
     width / 2,  height / 2, rearZ,
    -width / 2,  height / 2, rearZ,
    -tipWidth / 2, -tipHeight / 2, frontZ,
     tipWidth / 2, -tipHeight / 2, frontZ,
     tipWidth / 2,  tipHeight / 2, frontZ,
    -tipWidth / 2,  tipHeight / 2, frontZ
  ]);

  const indices = [
    0, 1, 2, 0, 2, 3,
    4, 6, 5, 4, 7, 6,
    0, 4, 5, 0, 5, 1,
    1, 5, 6, 1, 6, 2,
    2, 6, 7, 2, 7, 3,
    3, 7, 4, 3, 4, 0
  ];

  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute("position", new THREE.BufferAttribute(vertices, 3));
  geometry.setIndex(indices);
  geometry.computeVertexNormals();

  const mesh = new THREE.Mesh(geometry, material);
  mesh.position.set(...position);
  parent.add(mesh);
  return mesh;
}

function makeSprintLimb(parent, upperMat, lowerMat, jointMat, plateMat, side, fore) {
  const hip = new THREE.Group();
  hip.position.set(
    side * (fore ? 0.38 : 0.35),
    fore ? -0.12 : -0.10,
    fore ? 0.26 : -0.25
  );
  parent.add(hip);

  // S uses similarly long fore/hind limbs so full-speed stance targets
  // stay inside the reachable envelope instead of snapping at IK limits.
  const upperLen = 0.82;
  const lowerLen = 0.68;
  const cannonLen = 0.34;

  const upper = makeMesh(
    new THREE.CylinderGeometry(0.085, 0.135, upperLen, 6),
    upperMat,
    hip,
    [0, -upperLen / 2, 0.055]
  );
  upper.rotation.z = side * (fore ? 0.035 : 0.055);

  const knee = new THREE.Group();
  knee.position.set(0, -upperLen, 0.10);
  hip.add(knee);

  makeMesh(
    new THREE.IcosahedronGeometry(fore ? 0.115 : 0.125, 0),
    jointMat,
    knee,
    [0, 0, 0]
  );

  const lower = makeMesh(
    new THREE.CylinderGeometry(0.058, 0.092, lowerLen, 6),
    lowerMat,
    knee,
    [0, -lowerLen / 2, 0.07]
  );
  lower.rotation.z = side * (fore ? -0.025 : 0.025);

  const ankle = new THREE.Group();
  ankle.position.set(0, -lowerLen, 0.13);
  knee.add(ankle);

  makeMesh(
    new THREE.IcosahedronGeometry(0.088, 0),
    jointMat,
    ankle,
    [0, 0, 0]
  );

  const cannon = makeMesh(
    new THREE.CylinderGeometry(0.040, 0.056, cannonLen, 5),
    upperMat,
    ankle,
    [0, -cannonLen / 2, 0.045]
  );
  cannon.rotation.z = side * -0.018;

  const foot = new THREE.Group();
  foot.position.set(0, -cannonLen, 0.09);
  ankle.add(foot);

  const sole = makeMesh(
    new THREE.BoxGeometry(0.17, 0.075, 0.36),
    jointMat,
    foot,
    [0, -0.02, 0.11]
  );
  sole.rotation.x = -0.10;

  [-1, 1].forEach((toeSide) => {
    const toe = makeTaperedPlate(
      0.32,
      0.075,
      0.060,
      plateMat,
      foot,
      [toeSide * 0.052, -0.01, 0.27]
    );
    toe.rotation.x = -0.09;
    toe.rotation.y = toeSide * 0.08;
  });

  return {
    hip,
    knee,
    ankle,
    foot,
    phaseOffset: fore
      ? (side < 0 ? TAU * 0.50 : TAU * 0.58)
      : (side < 0 ? 0 : TAU * 0.08),
    upperLen,
    lowerLen,
    cannonLen,
    side,
    fore
  };
}

function createSprintCreature(color, index) {
  const cfg = MORPHS.S;
  const root = new THREE.Group();
  const bodyMaster = new THREE.Group();
  bodyMaster.position.y = 2.16;
  root.add(bodyMaster);

  const baseColor = new THREE.Color(color);
  const primary = mat(baseColor);
  const secondary = mat(baseColor.clone().multiplyScalar(0.78));
  const joint = mat(baseColor.clone().multiplyScalar(0.48), 0.78);
  const underside = mat(0x252b31, 0.82);
  const plate = new THREE.MeshStandardMaterial({
    color: baseColor.clone().lerp(new THREE.Color(0xc7d7df), 0.28),
    roughness: 0.60,
    metalness: 0.04,
    flatShading: true
  });
  const cue = new THREE.MeshStandardMaterial({
    color: 0x18222b,
    emissive: baseColor.clone().multiplyScalar(0.48),
    emissiveIntensity: 0.9,
    roughness: 0.34,
    metalness: 0.12,
    flatShading: true
  });

  const chestPivot = new THREE.Group();
  chestPivot.position.set(0, 0.01, 0.58);
  bodyMaster.add(chestPivot);

  const pelvisPivot = new THREE.Group();
  pelvisPivot.position.set(0, -0.05, -0.70);
  bodyMaster.add(pelvisPivot);

  // Longer, shallower body masses create a continuous racing silhouette.
  makeMesh(
    new THREE.IcosahedronGeometry(0.60, 1),
    primary,
    chestPivot,
    [0, 0, 0.02],
    [0.68, 0.56, 1.34]
  );

  makeMesh(
    new THREE.IcosahedronGeometry(0.56, 1),
    secondary,
    pelvisPivot,
    [0, -0.02, -0.01],
    [0.66, 0.54, 1.27]
  );

  const waist = makeMesh(
    new THREE.CylinderGeometry(0.245, 0.29, 0.92, 7),
    secondary,
    bodyMaster,
    [0, -0.06, -0.08]
  );
  waist.rotation.x = Math.PI / 2;

  // Low dark underside is structural separation, not a visible black rod.
  const keel = makeMesh(
    new THREE.BoxGeometry(0.34, 0.12, 1.36),
    underside,
    bodyMaster,
    [0, -0.34, -0.05]
  );
  keel.rotation.x = 0.015;

  // Tapered shoulder armor replaces the v1 rectangular slabs.
  [-1, 1].forEach((side) => {
    const shoulder = makeTaperedPlate(
      0.88,
      0.20,
      0.11,
      plate,
      chestPivot,
      [side * 0.34, 0.19, 0.08]
    );
    shoulder.rotation.y = side * 0.045;
    shoulder.rotation.x = -0.08;

    const flank = makeTaperedPlate(
      0.68,
      0.16,
      0.08,
      secondary,
      pelvisPivot,
      [side * 0.29, 0.14, -0.06]
    );
    flank.rotation.y = side * -0.035;
    flank.rotation.x = 0.06;
  });

  const spinePlate = makeTaperedPlate(
    1.42,
    0.12,
    0.09,
    plate,
    bodyMaster,
    [0, 0.39, -0.10]
  );
  spinePlate.rotation.x = -0.02;

  // The S neck stays low and forward, with less empty visual gap than v1.
  const neckPivot = new THREE.Group();
  neckPivot.position.set(0, 0.10, 0.98);
  chestPivot.add(neckPivot);

  // Collar mass closes the chest/neck seam without making the neck vertical.
  makeMesh(
    new THREE.IcosahedronGeometry(0.29, 1),
    primary,
    neckPivot,
    [0, -0.025, -0.05],
    [0.92, 0.74, 1.08]
  );

  const neck = makeMesh(
    new THREE.CylinderGeometry(0.155, 0.245, 0.82, 6),
    primary,
    neckPivot,
    [0, -0.005, 0.39]
  );
  neck.rotation.x = Math.PI / 2 - 0.045;

  const neckKeel = makeTaperedPlate(
    0.78,
    0.16,
    0.07,
    underside,
    neckPivot,
    [0, -0.145, 0.37]
  );
  neckKeel.rotation.x = -0.015;

  const headPivot = new THREE.Group();
  headPivot.position.set(0, 0.045, 0.56);
  neckPivot.add(headPivot);

  // Smaller wedge-like head.
  makeMesh(
    new THREE.IcosahedronGeometry(0.36, 1),
    primary,
    headPivot,
    [0, 0, 0.24],
    [0.58, 0.45, 1.12]
  );

  const muzzle = makeMesh(
    new THREE.ConeGeometry(0.15, 0.46, 5),
    secondary,
    headPivot,
    [0, -0.055, 0.67]
  );
  muzzle.rotation.x = Math.PI / 2;

  // Integrated rearward crest: shorter than v1 and rooted into the skull line.
  const crestRoot = new THREE.Group();
  crestRoot.position.set(0, 0.20, 0.08);
  headPivot.add(crestRoot);

  const crestUpper = makeTaperedPlate(
    1.10,
    0.16,
    0.085,
    plate,
    crestRoot,
    [0, 0.035, -0.43]
  );
  crestUpper.rotation.x = -0.055;
  crestUpper.rotation.z = 0.01;

  const crestLower = makeTaperedPlate(
    0.80,
    0.105,
    0.065,
    underside,
    crestRoot,
    [0, -0.075, -0.29]
  );
  crestLower.rotation.x = 0.015;

  // Small cheek fins make the head read as one designed structure from FRONT.
  [-1, 1].forEach((side) => {
    const cheek = makeTaperedPlate(
      0.40,
      0.085,
      0.055,
      plate,
      headPivot,
      [side * 0.19, -0.03, 0.22]
    );
    cheek.rotation.y = side * 0.18;
  });

  const eyeMat = new THREE.MeshBasicMaterial({ color: 0xbdeeff });
  [-1, 1].forEach((side) => {
    makeMesh(
      new THREE.SphereGeometry(0.029, 5, 4),
      eyeMat,
      headPivot,
      [side * 0.18, 0.055, 0.50]
    );
  });

  // Slim Cue Band; side modules no longer dominate head width.
  const cueBand = new THREE.Group();
  cueBand.position.set(0, 0.075, 0.24);
  headPivot.add(cueBand);

  const bandTop = makeMesh(
    new THREE.BoxGeometry(0.42, 0.055, 0.13),
    cue,
    cueBand,
    [0, 0.13, 0]
  );
  bandTop.rotation.x = -0.07;

  [-1, 1].forEach((side) => {
    makeMesh(
      new THREE.BoxGeometry(0.070, 0.17, 0.15),
      cue,
      cueBand,
      [side * 0.225, 0.015, 0.02]
    );
    makeMesh(
      new THREE.SphereGeometry(0.043, 6, 4),
      new THREE.MeshBasicMaterial({ color: side < 0 ? 0xffc24a : 0x62ddff }),
      cueBand,
      [side * 0.255, 0.015, 0.07]
    );
  });

  const legs = {
    fl: makeSprintLimb(chestPivot, primary, secondary, joint, plate, -1, true),
    fr: makeSprintLimb(chestPivot, primary, secondary, joint, plate, 1, true),
    hl: makeSprintLimb(pelvisPivot, secondary, primary, joint, plate, -1, false),
    hr: makeSprintLimb(pelvisPivot, secondary, primary, joint, plate, 1, false)
  };

  // Tail stays long enough to read as a balancing organ without dominating LOW.
  const tailBase = new THREE.Group();
  tailBase.position.set(0, 0.05, -0.70);
  tailBase.rotation.x = -0.14;
  pelvisPivot.add(tailBase);

  const tailSegments = [];
  let tailParent = tailBase;
  const tailLengths = [0.46, 0.40, 0.34];

  tailLengths.forEach((segLen, i) => {
    const jointNode = new THREE.Group();
    if (i > 0) jointNode.position.z = -tailLengths[i - 1];
    tailParent.add(jointNode);

    const seg = makeMesh(
      new THREE.CylinderGeometry(
        Math.max(0.035, 0.080 - i * 0.016),
        Math.max(0.045, 0.105 - i * 0.018),
        segLen,
        5
      ),
      i === 0 ? secondary : primary,
      jointNode,
      [0, 0, -segLen / 2]
    );
    seg.rotation.x = Math.PI / 2;
    tailSegments.push(jointNode);
    tailParent = jointNode;
  });

  const tailBlade = makeTaperedPlate(
    0.30,
    0.12,
    0.075,
    plate,
    tailParent,
    [0, 0, -0.12]
  );
  tailBlade.scale.z = -1;

  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.20,
    depthWrite: false
  });
  const shadow = new THREE.Mesh(new THREE.CircleGeometry(1.0, 18), shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.scale.set(0.88, 1.48, 1);
  shadow.position.y = 0.025;
  root.add(shadow);

  root.userData = {
    cfg,
    morphKey: "S",
    index,
    bodyMaster,
    chestPivot,
    pelvisPivot,
    neckPivot,
    headPivot,
    tailSegments,
    legs,
    phase: index * 0.61,
    turnLean: 0,
    accelLean: 0,
    neckLag: -0.04,
    headLag: 0,
    tailPitchState: tailSegments.map(() => 0),
    tailYawState: tailSegments.map(() => 0),
    strideLength: S_GAIT.minStrideWorld,
    maxStanceSlip: 0
  };

  return root;
}

function createCreature(morphKey, color, index) {
  if (morphKey === "S") {
    return createSprintCreature(color, index);
  }

  const cfg = MORPHS[morphKey];
  const root = new THREE.Group();
  const bodyMaster = new THREE.Group();
  bodyMaster.position.y = 2.05 + (cfg.leg - 1.15) * 0.48;
  root.add(bodyMaster);

  const primary = mat(color);
  const darker = mat(new THREE.Color(color).multiplyScalar(0.72));
  const accent = new THREE.MeshStandardMaterial({
    color: 0x161a1d,
    emissive: new THREE.Color(color).multiplyScalar(0.42),
    emissiveIntensity: 0.8,
    roughness: 0.45,
    flatShading: true
  });

  const chestPivot = new THREE.Group();
  chestPivot.position.z = 0.47;
  bodyMaster.add(chestPivot);

  const pelvisPivot = new THREE.Group();
  pelvisPivot.position.z = -0.54;
  bodyMaster.add(pelvisPivot);

  makeMesh(
    new THREE.SphereGeometry(0.68, 8, 6),
    primary,
    chestPivot,
    [0, 0, 0],
    cfg.body
  );

  makeMesh(
    new THREE.SphereGeometry(0.62, 8, 6),
    darker,
    pelvisPivot,
    [0, -0.02, 0],
    cfg.pelvis
  );

  const neckPivot = new THREE.Group();
  neckPivot.position.set(0, 0.30, 1.09);
  chestPivot.add(neckPivot);

  const neck = makeMesh(
    new THREE.CylinderGeometry(0.26, 0.34, cfg.neck, 6),
    primary,
    neckPivot,
    [0, cfg.neck * 0.28, cfg.neck * 0.28]
  );
  neck.rotation.x = Math.PI * 0.31;

  const headPivot = new THREE.Group();
  headPivot.position.set(0, cfg.neck * 0.57, cfg.neck * 0.60);
  neckPivot.add(headPivot);

  makeMesh(
    new THREE.SphereGeometry(0.50, 7, 5),
    primary,
    headPivot,
    [0, 0, 0.23],
    cfg.head
  );

  const muzzle = makeMesh(
    new THREE.ConeGeometry(0.25, 0.58, 6),
    darker,
    headPivot,
    [0, -0.03, 0.72]
  );
  muzzle.rotation.x = Math.PI / 2;

  const crest = makeMesh(
    new THREE.ConeGeometry(morphKey === "P" ? 0.22 : 0.15, morphKey === "P" ? 0.48 : 0.72, 5),
    darker,
    headPivot,
    [0, 0.42, 0.02]
  );
  crest.rotation.x = morphKey === "A" ? -0.72 : -0.48;

  const cueBand = makeMesh(
    new THREE.TorusGeometry(0.38, 0.065, 5, 16, Math.PI * 1.45),
    accent,
    headPivot,
    [0, 0.10, 0.26]
  );
  cueBand.rotation.set(Math.PI / 2, 0, Math.PI * 0.75);

  const eyeMat = new THREE.MeshBasicMaterial({ color: 0xeef7ff });
  [-1, 1].forEach((side) => {
    makeMesh(
      new THREE.SphereGeometry(0.038, 5, 4),
      eyeMat,
      headPivot,
      [side * 0.22 * cfg.head[0], 0.08, 0.64]
    );
  });

  const frontX = 0.43 * cfg.body[0];
  const rearX = 0.40 * cfg.pelvis[0];
  const legs = {
    fl: makeLeg(chestPivot, primary, cfg.leg, cfg.legWidth, -frontX, -0.10, 0.00),
    fr: makeLeg(chestPivot, primary, cfg.leg, cfg.legWidth, frontX, -0.10, Math.PI * 0.42),
    hl: makeLeg(pelvisPivot, darker, cfg.leg * 1.03, cfg.legWidth * 1.05, -rearX, -0.02, Math.PI * 1.03),
    hr: makeLeg(pelvisPivot, darker, cfg.leg * 1.03, cfg.legWidth * 1.05, rearX, -0.02, Math.PI * 1.42)
  };

  const tailBase = new THREE.Group();
  tailBase.position.set(0, 0.15, -1.08 * cfg.pelvis[2]);
  pelvisPivot.add(tailBase);

  const tailSegments = [];
  let tailParent = tailBase;
  for (let i = 0; i < 3; i += 1) {
    const segLen = cfg.tail / 3;
    const joint = new THREE.Group();
    if (i > 0) joint.position.z = -segLen;
    tailParent.add(joint);
    const seg = makeMesh(
      new THREE.CylinderGeometry(
        Math.max(0.045, 0.12 - i * 0.026),
        Math.max(0.06, 0.16 - i * 0.030),
        segLen,
        5
      ),
      darker,
      joint,
      [0, 0, -segLen / 2]
    );
    seg.rotation.x = Math.PI / 2;
    tailSegments.push(joint);
    tailParent = joint;
  }

  const shadowMat = new THREE.MeshBasicMaterial({
    color: 0x000000,
    transparent: true,
    opacity: 0.22,
    depthWrite: false
  });
  const shadow = new THREE.Mesh(new THREE.CircleGeometry(1.0, 18), shadowMat);
  shadow.rotation.x = -Math.PI / 2;
  shadow.scale.set(morphKey === "P" ? 1.45 : 1.15, morphKey === "S" ? 1.6 : 1.35, 1);
  shadow.position.y = 0.025;
  root.add(shadow);

  root.userData = {
    cfg,
    morphKey,
    index,
    bodyMaster,
    chestPivot,
    pelvisPivot,
    neckPivot,
    headPivot,
    tailSegments,
    legs,
    phase: index * 0.61,
    turnLean: 0,
    accelLean: 0
  };

  return root;
}

function seeded(i, salt = 1) {
  const x = Math.sin((i + 1) * 12.9898 + salt * 78.233) * 43758.5453;
  return x - Math.floor(x);
}

function laneToX(lane) {
  return (lane - (LANE_COUNT - 1) / 2) * LANE_WIDTH;
}

const runners = [];

function createRunners() {
  const morphKeys = ["S", "P", "E", "A"];

  for (let i = 0; i < RUNNER_COUNT; i += 1) {
    const morph = morphKeys[i % morphKeys.length];
    const creature = createCreature(morph, COLORS[i % COLORS.length], i);
    const lane = i % LANE_COUNT;
    const row = Math.floor(i / LANE_COUNT);

    const runner = {
      id: i,
      name: `Runner ${String(i + 1).padStart(2, "0")}`,
      morph,
      cfg: MORPHS[morph],
      group: creature,
      lane,
      targetLane: lane,
      laneX: laneToX(lane),
      distance: -row * 3.2 - seeded(i, 4) * 1.5,
      speed: 0,
      targetSpeed: 0,
      phaseBias: seeded(i, 8) * Math.PI * 2,
      staminaBias: 0.96 + seeded(i, 7) * 0.08,
      speedBias: 0.965 + seeded(i, 3) * 0.07,
      nextLaneDecision: 190 + seeded(i, 11) * 210,
      laneChangeStartedAt: -999
    };

    creature.position.set(runner.laneX, 0, runner.distance);
    scene.add(creature);
    runners.push(runner);

    const option = document.createElement("option");
    option.value = String(i);
    option.textContent = `${runner.name} · ${morph}`;
    runnerSelect.append(option);
  }
}

function resetRace() {
  raceTime = 0;
  finished = false;
  paused = false;
  pauseButton.textContent = "PAUSE";
  raceStateEl.textContent = "RUNNING";

  runners.forEach((runner, i) => {
    const row = Math.floor(i / LANE_COUNT);
    runner.lane = i % LANE_COUNT;
    runner.targetLane = runner.lane;
    runner.laneX = laneToX(runner.lane);
    runner.distance = -row * 3.2 - seeded(i, 4) * 1.5;
    runner.speed = 0;
    runner.targetSpeed = 0;
    runner.nextLaneDecision = 190 + seeded(i, 11) * 210;
    runner.group.position.set(runner.laneX, 0, runner.distance);
  });
}

function maybeChangeLane(runner) {
  if (runner.distance < runner.nextLaneDecision || runner.distance > RACE_DISTANCE - 180) return;

  const options = [];
  if (runner.lane > 0) options.push(runner.lane - 1);
  if (runner.lane < LANE_COUNT - 1) options.push(runner.lane + 1);

  if (options.length && seeded(runner.id, Math.floor(runner.distance / 100) + 31) > 0.42) {
    runner.targetLane = options[Math.floor(seeded(runner.id, Math.floor(runner.distance / 90) + 44) * options.length)];
    runner.lane = runner.targetLane;
    runner.laneChangeStartedAt = raceTime;
  }

  runner.nextLaneDecision += 260 + seeded(runner.id, Math.floor(runner.distance / 70) + 51) * 260;
}

function updateRunner(runner, dt) {
  const cfg = runner.cfg;
  const progress = THREE.MathUtils.clamp(runner.distance / RACE_DISTANCE, 0, 1);

  const launch = THREE.MathUtils.smoothstep(raceTime, 0, 4.8);
  let phaseBoost = 1;

  if (runner.morph === "S") {
    phaseBoost = progress < 0.30 ? 1.045 : progress > 0.78 ? 0.99 : 1.015;
  } else if (runner.morph === "P") {
    phaseBoost = progress < 0.20 ? 1.055 : progress > 0.78 ? 0.985 : 1.0;
  } else if (runner.morph === "E") {
    phaseBoost = progress < 0.25 ? 0.985 : progress > 0.68 ? 1.035 : 1.01;
  } else if (runner.morph === "A") {
    phaseBoost = 1.0 + Math.sin(progress * Math.PI * 5 + runner.phaseBias) * 0.009;
  }

  runner.targetSpeed = cfg.baseSpeed * runner.speedBias * phaseBoost * launch;
  const accelRate = cfg.accel * (runner.targetSpeed >= runner.speed ? 1 : 0.62);
  runner.speed = THREE.MathUtils.damp(runner.speed, runner.targetSpeed, accelRate, dt);

  if (!finished) runner.distance += runner.speed * dt;

  maybeChangeLane(runner);

  const targetX = laneToX(runner.targetLane);
  const oldX = runner.laneX;
  runner.laneX = THREE.MathUtils.damp(runner.laneX, targetX, runner.morph === "A" ? 2.7 : 2.05, dt);
  const lateralVelocity = (runner.laneX - oldX) / Math.max(dt, 0.001);

  runner.group.position.x = runner.laneX;
  runner.group.position.z = runner.distance;

  if (runner.morph === "S") {
    const speedRatio = THREE.MathUtils.clamp(runner.speed / Math.max(cfg.baseSpeed, 1), 0, 1.2);
    const strideLength = THREE.MathUtils.lerp(
      S_GAIT.minStrideWorld,
      S_GAIT.maxStrideWorld,
      THREE.MathUtils.smoothstep(speedRatio, 0.18, 1.0)
    );
    runner.group.userData.strideLength = strideLength;
    runner.group.userData.phase +=
      dt * (runner.speed / Math.max(strideLength, 0.01)) * TAU;
  } else {
    const phaseRate = 4.2 * cfg.cadence * (0.25 + runner.speed / Math.max(cfg.baseSpeed, 1));
    runner.group.userData.phase += dt * phaseRate;
  }
  updateCreaturePose(runner, lateralVelocity, dt);
}

function wrap01(value) {
  return ((value % 1) + 1) % 1;
}

function solveSprintLeg(leg, targetY, targetZ, footPitch, turnLean) {
  const l1 = leg.upperLen;
  const l2 = leg.lowerLen + leg.cannonLen;
  const rawDistance = Math.hypot(targetY, targetZ);
  const distance = THREE.MathUtils.clamp(
    rawDistance,
    Math.abs(l1 - l2) + 0.04,
    l1 + l2 - 0.025
  );
  leg.ikClamped = Math.abs(rawDistance - distance) > 0.002;

  const direction = Math.atan2(-targetZ, -targetY);
  const hipCos = THREE.MathUtils.clamp(
    (l1 * l1 + distance * distance - l2 * l2) / (2 * l1 * distance),
    -1,
    1
  );
  const kneeCos = THREE.MathUtils.clamp(
    (l1 * l1 + l2 * l2 - distance * distance) / (2 * l1 * l2),
    -1,
    1
  );

  const hipOffset = Math.acos(hipCos);
  const kneeBend = Math.PI - Math.acos(kneeCos);

  leg.hip.rotation.x = direction + hipOffset;
  leg.knee.rotation.x = -kneeBend;
  leg.ankle.rotation.x = 0.06 + kneeBend * 0.10;
  leg.foot.rotation.x =
    footPitch -
    leg.hip.rotation.x -
    leg.knee.rotation.x -
    leg.ankle.rotation.x;
  leg.hip.rotation.z = leg.side * turnLean * 0.22;
}

function updateSprintPose(runner, lateralVelocity, dt) {
  const ud = runner.group.userData;
  const cfg = runner.cfg;
  const speedRatio = THREE.MathUtils.clamp(runner.speed / cfg.baseSpeed, 0, 1.18);
  const phase = ud.phase + runner.phaseBias;
  const cycle = wrap01(phase / TAU);
  const strideLength =
    ud.strideLength ||
    THREE.MathUtils.lerp(S_GAIT.minStrideWorld, S_GAIT.maxStrideWorld, speedRatio);

  const accelError = (runner.targetSpeed - runner.speed) / Math.max(cfg.baseSpeed, 1);
  ud.accelLean = THREE.MathUtils.damp(ud.accelLean, accelError * 1.45, 8.5, dt);
  ud.turnLean = THREE.MathUtils.damp(
    ud.turnLean,
    THREE.MathUtils.clamp(-lateralVelocity * cfg.laneLean * 0.16, -0.22, 0.22),
    10.0,
    dt
  );

  // Gallop cycle: rear drive -> fore catch -> compression -> suspension.
  const rearDrive = Math.max(0, Math.sin((cycle - 0.02) * TAU));
  const foreCatch = Math.max(0, Math.sin((cycle - 0.50) * TAU));
  const suspension = Math.pow(Math.max(0, -Math.sin((cycle - 0.08) * TAU)), 1.35);
  const load = Math.max(rearDrive, foreCatch);
  const spineWave = Math.sin((cycle - 0.12) * TAU);
  const spineExtend = 0.5 + 0.5 * spineWave;

  const baseY = INSPECT_MODE && !MOTION_REVIEW_MODE ? S_GAIT.reviewBaseY : S_GAIT.baseY;
  ud.bodyMaster.position.y =
    baseY +
    suspension * 0.115 * speedRatio -
    load * 0.050 * speedRatio;

  // Longitudinal body deformation is essential: the runner must not read as
  // a rigid hull with four animated sticks.
  const longStretch = (spineExtend - 0.5) * 0.18 * speedRatio;
  const verticalCompression = load * 0.055 * speedRatio;
  ud.chestPivot.position.z = S_GAIT.chestBaseZ + longStretch * 0.48;
  ud.pelvisPivot.position.z = S_GAIT.pelvisBaseZ - longStretch * 0.60;
  ud.chestPivot.position.y = S_GAIT.chestBaseY - verticalCompression * 0.55;
  ud.pelvisPivot.position.y = S_GAIT.pelvisBaseY - verticalCompression * 0.45;

  const contactPitch =
    -rearDrive * 0.030 +
    foreCatch * 0.042 -
    suspension * 0.018;

  ud.bodyMaster.rotation.x =
    -0.082 * speedRatio -
    ud.accelLean * 0.11 +
    contactPitch;
  ud.bodyMaster.rotation.z = ud.turnLean;

  ud.chestPivot.rotation.x =
    -spineWave * 0.090 * speedRatio -
    foreCatch * 0.040 +
    suspension * 0.018;
  ud.pelvisPivot.rotation.x =
    spineWave * 0.125 * speedRatio +
    rearDrive * 0.045 -
    suspension * 0.020;
  ud.chestPivot.rotation.y = -Math.sin(phase * 0.5) * 0.016 * speedRatio;
  ud.pelvisPivot.rotation.y = Math.sin(phase * 0.5) * 0.024 * speedRatio;

  // Root travel lets the shoulder and hip participate in the stride instead
  // of forcing the knee/ankle chain to create all apparent motion.
  Object.values(ud.legs).forEach((leg) => {
    const localCycle = wrap01((phase + leg.phaseOffset) / TAU);
    const strideRoot = Math.sin(localCycle * TAU);
    const liftRoot = Math.max(0, -Math.sin(localCycle * TAU));

    leg.hip.position.z =
      (leg.fore ? 0.26 : -0.25) +
      strideRoot * (leg.fore ? 0.075 : 0.090) * speedRatio;
    leg.hip.position.y =
      (leg.fore ? -0.12 : -0.10) +
      liftRoot * 0.035 * speedRatio -
      load * 0.012;
  });

  const stanceDuration = S_GAIT.stance;
  const stanceSweep = strideLength * stanceDuration;
  const halfSweep = stanceSweep * 0.5;

  Object.values(ud.legs).forEach((leg) => {
    const localCycle = wrap01((phase + leg.phaseOffset) / TAU);
    const fore = leg.fore;
    const nominalReach = fore ? 1.43 : 1.40;

    let targetZ;
    let targetY;
    let footPitch;

    if (localCycle < stanceDuration) {
      const u = localCycle / stanceDuration;
      // Keep the world-space foot stationary: runner root travel is linear,
      // so stance sweep must remain linear too. Shape loading vertically instead.
      targetZ = THREE.MathUtils.lerp(halfSweep, -halfSweep, u);

      // Catch compresses, mid-stance stabilizes, toe-off extends.
      const compression = Math.sin(u * Math.PI);
      targetY =
        -nominalReach +
        compression * 0.016 -
        load * 0.010;
      footPitch = THREE.MathUtils.lerp(-0.055, 0.115, u);

      const worldStridePoint = runner.distance + targetZ;
      if (!leg.stanceActive) {
        leg.stanceActive = true;
        leg.stanceAnchor = worldStridePoint;
      }
      const slip = Math.abs(worldStridePoint - leg.stanceAnchor);
      ud.maxStanceSlip = Math.max(ud.maxStanceSlip || 0, slip);
    } else {
      leg.stanceActive = false;
      const u = (localCycle - stanceDuration) / (1 - stanceDuration);

      // Recovery is intentionally asymmetric:
      // fold fast after toe-off, stay compact, then extend before touchdown.
      const advance = u < 0.58
        ? 0.5 * Math.pow(u / 0.58, 1.55)
        : 0.5 + 0.5 * (1 - Math.pow(1 - (u - 0.58) / 0.42, 2.2));
      const liftShape = Math.pow(Math.sin(u * Math.PI), 1.15);
      const earlyFold = Math.pow(Math.max(0, Math.sin(Math.min(1, u / 0.48) * Math.PI)), 1.35);

      targetZ = THREE.MathUtils.lerp(-halfSweep, halfSweep, advance);
      targetY =
        -nominalReach +
        liftShape * S_GAIT.swingLift +
        earlyFold * 0.055;
      footPitch =
        -0.23 * liftShape +
        THREE.MathUtils.lerp(0.06, -0.04, Math.min(1, u / 0.92));
    }

    solveSprintLeg(leg, targetY, targetZ, footPitch, ud.turnLean);
  });

  // Damped stabilization. Neck absorbs torso motion; head remains calmer.
  const neckTarget =
    -0.040 -
    ud.chestPivot.rotation.x * 0.30 +
    suspension * 0.012;
  ud.neckLag = THREE.MathUtils.damp(
    ud.neckLag ?? neckTarget,
    neckTarget,
    9.0,
    dt
  );
  ud.neckPivot.rotation.x = ud.neckLag;

  const headTarget =
    -ud.neckLag * 0.46 -
    ud.bodyMaster.rotation.x * 0.16 -
    foreCatch * 0.008;
  ud.headLag = THREE.MathUtils.damp(
    ud.headLag ?? headTarget,
    headTarget,
    12.5,
    dt
  );
  ud.headPivot.rotation.x = ud.headLag;
  ud.headPivot.rotation.z = -ud.turnLean * 0.48;

  // Tail uses per-segment damped targets, with slower response toward the tip.
  ud.tailSegments.forEach((joint, i) => {
    const pitchTarget =
      0.035 +
      ud.pelvisPivot.rotation.x * (0.24 + i * 0.09) -
      suspension * (0.018 + i * 0.007);
    const yawTarget =
      -ud.turnLean * (0.52 + i * 0.18) +
      Math.sin(phase * 0.45 - i * 0.42) * (0.022 + i * 0.010) * speedRatio;

    const pitchRate = 10.5 - i * 1.4;
    const yawRate = 9.5 - i * 1.2;
    ud.tailPitchState[i] = THREE.MathUtils.damp(
      ud.tailPitchState[i] ?? pitchTarget,
      pitchTarget,
      Math.max(4.5, pitchRate),
      dt
    );
    ud.tailYawState[i] = THREE.MathUtils.damp(
      ud.tailYawState[i] ?? yawTarget,
      yawTarget,
      Math.max(4.0, yawRate),
      dt
    );

    joint.rotation.x = ud.tailPitchState[i];
    joint.rotation.y = ud.tailYawState[i];
  });

  if (MOTION_REVIEW_MODE) {
    const legs = Object.values(ud.legs);
    canvas.dataset.ikClamped = legs.some((leg) => leg.ikClamped) ? "1" : "0";
    canvas.dataset.maxStanceSlip = String(ud.maxStanceSlip || 0);
    const bodyStretch =
      Math.abs(ud.chestPivot.position.z - S_GAIT.chestBaseZ) +
      Math.abs(ud.pelvisPivot.position.z - S_GAIT.pelvisBaseZ);
    ud.maxBodyStretch = Math.max(ud.maxBodyStretch || 0, bodyStretch);
    canvas.dataset.maxBodyStretch = String(ud.maxBodyStretch);
  }
}

function updateCreaturePose(runner, lateralVelocity, dt = 1 / 60) {
  if (runner.morph === "S") {
    updateSprintPose(runner, lateralVelocity, dt);
    return;
  }

  const ud = runner.group.userData;
  const cfg = runner.cfg;
  const phase = ud.phase + runner.phaseBias;
  const speedRatio = THREE.MathUtils.clamp(runner.speed / cfg.baseSpeed, 0, 1.18);
  const bodyBob = Math.abs(Math.sin(phase * 0.5)) * cfg.bob * speedRatio;
  const strideDrive = cfg.stride * (0.35 + speedRatio * 0.65);

  ud.bodyMaster.position.y =
    2.05 + (cfg.leg - 1.15) * 0.48 + bodyBob;

  const accelError = (runner.targetSpeed - runner.speed) / Math.max(cfg.baseSpeed, 1);
  ud.accelLean = THREE.MathUtils.lerp(ud.accelLean, accelError * 1.7, 0.08);
  ud.turnLean = THREE.MathUtils.lerp(
    ud.turnLean,
    THREE.MathUtils.clamp(-lateralVelocity * cfg.laneLean * 0.18, -0.25, 0.25),
    0.12
  );

  ud.bodyMaster.rotation.x =
    -cfg.pitch * speedRatio - ud.accelLean * 0.12 + Math.sin(phase) * 0.016;
  ud.bodyMaster.rotation.z = ud.turnLean;
  ud.chestPivot.rotation.x = Math.sin(phase) * 0.028 * speedRatio;
  ud.pelvisPivot.rotation.x = -Math.sin(phase + 0.42) * 0.038 * speedRatio;
  ud.pelvisPivot.rotation.y = Math.sin(phase * 0.5) * 0.038 * speedRatio;
  ud.chestPivot.rotation.y = -Math.sin(phase * 0.5) * 0.028 * speedRatio;

  ud.neckPivot.rotation.x =
    -0.08 + Math.sin(phase * 0.5 + 0.8) * 0.048 * speedRatio;
  ud.headPivot.rotation.x =
    -Math.sin(phase * 0.5 + 1.4) * 0.055 * speedRatio;
  ud.headPivot.rotation.z = -ud.turnLean * 0.55;

  Object.values(ud.legs).forEach((leg, idx) => {
    const lp = phase + leg.phaseOffset;
    const s = Math.sin(lp);
    const forward = s * 0.88 * strideDrive;
    const stance = Math.cos(lp);
    const kneeBend =
      (stance < 0 ? Math.abs(stance) * 0.88 : 0.18 + Math.max(0, s) * 0.28) *
      cfg.footLift;

    leg.hip.rotation.x = forward;
    leg.knee.rotation.x = -0.22 - kneeBend;
    leg.foot.rotation.x = -forward * 0.28 + kneeBend * 0.54;

    const outerBias = idx % 2 === 0 ? -1 : 1;
    leg.hip.rotation.z = outerBias * ud.turnLean * 0.25;
  });

  ud.tailSegments.forEach((joint, i) => {
    const lag = phase * 0.42 - i * 0.52;
    joint.rotation.y =
      Math.sin(lag) * (0.16 + i * 0.035) * speedRatio - ud.turnLean * (0.55 + i * 0.18);
    joint.rotation.x =
      0.18 + Math.sin(lag * 0.82 + 0.7) * (0.06 + i * 0.022) * speedRatio;
  });
}

function rankings() {
  return [...runners].sort((a, b) => b.distance - a.distance);
}

let selectedRunner = 0;
let requestedCamera = "AUTO";
let actualCamera = "PACK";
let paused = false;
let finished = false;
let raceTime = 0;
let fpsAccumulator = 0;
let fpsFrames = 0;

function autoCameraMode() {
  if (raceTime < 3.4) return "PACK";
  const cycle = (raceTime - 3.4) % 25;
  if (cycle < 5.0) return "CHASE";
  if (cycle < 9.0) return "LOW";
  if (cycle < 14.0) return "SIDE";
  if (cycle < 18.5) return "PACK";
  if (cycle < 22.0) return "FRONT";
  return "CHASE";
}

function packCenter(out) {
  let x = 0;
  let z = 0;
  let count = 0;
  const leaders = rankings().slice(0, 10);
  leaders.forEach((r) => {
    x += r.group.position.x;
    z += r.group.position.z;
    count += 1;
  });
  out.set(x / count, 1.8, z / count);
  return out;
}

function updateCamera(dt) {
  const focus = runners[selectedRunner];
  const focusPos = focus.group.position;
  actualCamera = requestedCamera === "AUTO" ? autoCameraMode() : requestedCamera;

  let targetFov = 58;

  if (INSPECT_MODE || MOTION_REVIEW_MODE) {
    if (actualCamera === "SIDE") {
      desiredCamera.set(focusPos.x + 7.8, 3.0, focusPos.z);
      desiredLook.set(focusPos.x, 1.55, focusPos.z);
      targetFov = 42;
    } else if (actualCamera === "LOW") {
      desiredCamera.set(focusPos.x + 2.0, 1.15, focusPos.z - 5.4);
      desiredLook.set(focusPos.x, 1.45, focusPos.z + 0.8);
      targetFov = 50;
    } else if (actualCamera === "CHASE") {
      desiredCamera.set(focusPos.x + 3.9, 3.0, focusPos.z - 6.8);
      desiredLook.set(focusPos.x, 1.55, focusPos.z + 0.6);
      targetFov = 44;
    } else if (actualCamera === "FRONT") {
      desiredCamera.set(focusPos.x - 2.7, 2.6, focusPos.z + 6.7);
      desiredLook.set(focusPos.x, 1.55, focusPos.z - 0.2);
      targetFov = 44;
    } else {
      desiredCamera.set(focusPos.x + 5.5, 4.5, focusPos.z - 5.8);
      desiredLook.set(focusPos.x, 1.55, focusPos.z);
      targetFov = 43;
    }

    camera.position.x = THREE.MathUtils.damp(camera.position.x, desiredCamera.x, 7.5, dt);
    camera.position.y = THREE.MathUtils.damp(camera.position.y, desiredCamera.y, 7.5, dt);
    camera.position.z = THREE.MathUtils.damp(camera.position.z, desiredCamera.z, 7.5, dt);
    cameraLook.x = THREE.MathUtils.damp(cameraLook.x, desiredLook.x, 8.5, dt);
    cameraLook.y = THREE.MathUtils.damp(cameraLook.y, desiredLook.y, 8.5, dt);
    cameraLook.z = THREE.MathUtils.damp(cameraLook.z, desiredLook.z, 8.5, dt);
    camera.fov = THREE.MathUtils.damp(camera.fov, targetFov, 8.0, dt);
    camera.updateProjectionMatrix();
    camera.lookAt(cameraLook);
    return;
  }

  if (actualCamera === "CHASE") {
    desiredCamera.set(
      focusPos.x + 5.2,
      4.4,
      focusPos.z - 11.8
    );
    desiredLook.set(focusPos.x, 1.75, focusPos.z + 10.5);
    targetFov = 61;
  } else if (actualCamera === "LOW") {
    desiredCamera.set(
      focusPos.x + 2.4,
      1.55,
      focusPos.z - 8.0
    );
    desiredLook.set(focusPos.x, 1.42, focusPos.z + 15);
    targetFov = 72;
  } else if (actualCamera === "SIDE") {
    const side = focusPos.x <= 0 ? -1 : 1;
    desiredCamera.set(
      side * (TRACK_WIDTH / 2 + 11.5),
      4.2,
      focusPos.z - 0.6
    );
    desiredLook.set(focusPos.x, 1.65, focusPos.z + 1.5);
    targetFov = 52;
  } else if (actualCamera === "FRONT") {
    desiredCamera.set(
      focusPos.x - 3.0,
      3.2,
      focusPos.z + 10.6
    );
    desiredLook.set(focusPos.x, 1.65, focusPos.z - 5.5);
    targetFov = 60;
  } else {
    const center = packCenter(tempV);
    desiredCamera.set(
      center.x + 11,
      12.8,
      center.z - 21
    );
    desiredLook.set(center.x, 1.5, center.z + 7);
    targetFov = 54;
  }

  const transitionRate = requestedCamera === "AUTO" ? 2.6 : 3.8;
  camera.position.x = THREE.MathUtils.damp(camera.position.x, desiredCamera.x, transitionRate, dt);
  camera.position.y = THREE.MathUtils.damp(camera.position.y, desiredCamera.y, transitionRate, dt);
  camera.position.z = THREE.MathUtils.damp(camera.position.z, desiredCamera.z, transitionRate, dt);

  cameraLook.x = THREE.MathUtils.damp(cameraLook.x, desiredLook.x, transitionRate + 0.8, dt);
  cameraLook.y = THREE.MathUtils.damp(cameraLook.y, desiredLook.y, transitionRate + 0.8, dt);
  cameraLook.z = THREE.MathUtils.damp(cameraLook.z, desiredLook.z, transitionRate + 0.8, dt);

  if (actualCamera === "LOW" || actualCamera === "CHASE") {
    const shake = Math.min(focus.speed / 25, 1) * (actualCamera === "LOW" ? 0.035 : 0.018);
    camera.position.y += Math.sin(raceTime * 17) * shake;
    camera.position.x += Math.sin(raceTime * 13.7) * shake * 0.4;
  }

  camera.fov = THREE.MathUtils.damp(camera.fov, targetFov, 4.2, dt);
  camera.updateProjectionMatrix();
  camera.lookAt(cameraLook);
}

function updateHud(dt) {
  const focus = runners[selectedRunner];
  const rank = rankings().findIndex((r) => r.id === focus.id) + 1;
  distanceEl.textContent = `${Math.max(0, Math.floor(focus.distance))} / ${RACE_DISTANCE} m`;
  speedEl.textContent = `${focus.speed.toFixed(1)} m/s`;
  morphEl.textContent = focus.morph;
  runnerNameEl.textContent = `${focus.name} · ${MORPHS[focus.morph].label}`;
  positionEl.textContent = `${rank} / ${RUNNER_COUNT}`;
  cameraEl.textContent = actualCamera;

  fpsAccumulator += dt;
  fpsFrames += 1;
  if (fpsAccumulator >= 0.5) {
    fpsEl.textContent = `${Math.round(fpsFrames / fpsAccumulator)} FPS`;
    fpsAccumulator = 0;
    fpsFrames = 0;
  }
}

function finishCheck() {
  if (finished) return;
  const leader = rankings()[0];
  if (leader.distance >= RACE_DISTANCE) {
    finished = true;
    paused = true;
    raceStateEl.textContent = "FINISHED";
    pauseButton.textContent = "RESUME";
  }
}

cameraButtons.forEach((button) => {
  button.addEventListener("click", () => {
    requestedCamera = button.dataset.camera;
    cameraButtons.forEach((b) => b.classList.toggle("active", b === button));
  });
});

runnerSelect.addEventListener("change", () => {
  selectedRunner = Number(runnerSelect.value);
});

pauseButton.addEventListener("click", () => {
  if (finished && paused) {
    finished = false;
  }
  paused = !paused;
  pauseButton.textContent = paused ? "RESUME" : "PAUSE";
  raceStateEl.textContent = paused ? "PAUSED" : "RUNNING";
});

restartButton.addEventListener("click", () => {
  resetRace();
});

window.addEventListener("keydown", (event) => {
  const keys = {
    Digit1: "AUTO",
    Digit2: "CHASE",
    Digit3: "LOW",
    Digit4: "PACK",
    Digit5: "SIDE",
    Digit6: "FRONT"
  };
  if (keys[event.code]) {
    requestedCamera = keys[event.code];
    cameraButtons.forEach((b) => b.classList.toggle("active", b.dataset.camera === requestedCamera));
  }
  if (event.code === "Space") {
    event.preventDefault();
    pauseButton.click();
  }
});

window.addEventListener("resize", () => {
  renderer.setSize(window.innerWidth, window.innerHeight, false);
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
});

addWorld();
createRunners();
resetRace();

if (INSPECT_MODE || MOTION_REVIEW_MODE) {
  selectedRunner = 0;
  runnerSelect.value = "0";
  const focus = runners[0];

  runners.forEach((runner, index) => {
    runner.group.visible = index === 0;
  });

  focus.lane = 4;
  focus.targetLane = 4;
  focus.laneX = 0;
  focus.distance = 80;
  focus.speed = focus.cfg.baseSpeed;
  focus.targetSpeed = focus.cfg.baseSpeed;
  focus.nextLaneDecision = Number.POSITIVE_INFINITY;
  focus.group.position.set(0, 0, focus.distance);
  focus.group.userData.phase = 1.18;
  focus.group.userData.strideLength = S_GAIT.maxStrideWorld;
  updateCreaturePose(focus, 0);

  raceTime = 6;
  requestedCamera = "SIDE";
  actualCamera = "SIDE";
  cameraButtons.forEach((button) => {
    button.classList.toggle("active", button.dataset.camera === "SIDE");
  });

  if (INSPECT_MODE) {
    paused = true;
    pauseButton.textContent = "RESUME";
    raceStateEl.textContent = "INSPECT";
  } else {
    paused = false;
    pauseButton.textContent = "PAUSE";
    raceStateEl.textContent = "MOTION REVIEW";
  }
}

const isolatedReview = INSPECT_MODE || MOTION_REVIEW_MODE;
camera.position.set(isolatedReview ? 7.8 : 11, isolatedReview ? 3.0 : 13, isolatedReview ? 80 : -22);
cameraLook.set(0, 1.6, isolatedReview ? 80 : 8);
camera.lookAt(cameraLook);

loading.classList.add("hidden");

function animate() {
  const rawDt = clock.getDelta();
  const dt = Math.min(rawDt, 0.035);

  if (!paused) {
    raceTime += dt;
    runners.forEach((runner) => updateRunner(runner, dt));
    finishCheck();
  } else {
    runners.forEach((runner) => updateCreaturePose(runner, 0, dt));
  }

  updateCamera(dt);
  updateHud(dt);
  renderer.render(scene, camera);
  requestAnimationFrame(animate);
}

requestAnimationFrame(animate);
