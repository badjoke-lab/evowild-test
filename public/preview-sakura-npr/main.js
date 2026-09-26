import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { cel } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/toon.js";
import { Pipeline } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/post.js";

const canvas = document.querySelector("#view");
const loading = document.querySelector("#loading");
const fpsEl = document.querySelector("#fps");
const clipEl = document.querySelector("#clip");

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: true,
  powerPreference: "high-performance",
  stencil: false
});
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xcbdcf0);
scene.fog = new THREE.Fog(0xdce5ef, 20, 70);

const camera = new THREE.PerspectiveCamera(44, 1, 0.1, 120);
camera.rotation.order = "YXZ";

const hemi = new THREE.HemisphereLight(0xdcecff, 0xb6a6c6, 1.12);
scene.add(hemi);

const sun = new THREE.DirectionalLight(0xfff1d8, 2.25);
sun.position.set(-7, 11, 8);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -8;
sun.shadow.camera.right = 8;
sun.shadow.camera.top = 8;
sun.shadow.camera.bottom = -8;
sun.shadow.camera.near = 0.1;
sun.shadow.camera.far = 40;
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.035;
scene.add(sun);

const fill = new THREE.DirectionalLight(0xa9bdf5, 1.08);
fill.position.set(7, 5, -6);
scene.add(fill);

const bounce = new THREE.DirectionalLight(0xd8cbe8, 0.34);
bounce.position.set(2, -3, 6);
scene.add(bounce);

const stage = new THREE.Group();
scene.add(stage);

const road = new THREE.Mesh(
  new THREE.PlaneGeometry(18, 120),
  cel({ color: 0x8e8a9c, bands: 3, tint: 0x6c5f8c, flat: true })
);
road.rotation.x = -Math.PI / 2;
road.position.y = -0.035;
road.receiveShadow = true;
stage.add(road);

const laneMat = new THREE.MeshBasicMaterial({ color: 0xf4f2f6 });
const stripes = [];
for (let i = 0; i < 26; i += 1) {
  const stripe = new THREE.Mesh(new THREE.PlaneGeometry(0.085, 2.2), laneMat);
  stripe.rotation.x = -Math.PI / 2;
  stripe.position.set(-2.4, -0.025, -28 + i * 3.6);
  stage.add(stripe);
  stripes.push(stripe);
  const stripe2 = stripe.clone();
  stripe2.position.x = 2.4;
  stage.add(stripe2);
  stripes.push(stripe2);
}

for (let i = 0; i < 22; i += 1) {
  const marker = new THREE.Mesh(
    new THREE.BoxGeometry(0.12, 0.8, 0.12),
    cel({ color: i % 2 ? 0xf4c033 : 0xfaf6ef, bands: 2, tint: 0x6c5f8c })
  );
  marker.position.set(i % 2 ? -4.8 : 4.8, 0.4, -34 + i * 3.3);
  marker.castShadow = true;
  stage.add(marker);
}

const originals = new Map();
const toonMaterials = new Map();
let model = null;
let mixer = null;
let renderMode = "sakura";
let cameraMode = "threeq";
let modelHeight = 2.2;

function materialToCel(src) {
  if (Array.isArray(src)) return src.map(materialToCel);
  if (!src) return cel({ color: 0xffffff, bands: 3, tint: 0x6c5f8c, cache: false });
  return cel({
    color: src.color?.getHex?.() ?? 0xffffff,
    bands: 3,
    tint: 0x6c5f8c,
    flat: false,
    map: src.map ?? null,
    transparent: !!src.transparent,
    opacity: src.opacity ?? 1,
    side: src.side ?? THREE.FrontSide,
    alphaTest: src.alphaTest ?? 0,
    depthWrite: src.depthWrite ?? true,
    vertexColors: !!src.vertexColors,
    cache: false
  });
}

function setModelMaterials(mode) {
  if (!model) return;
  model.traverse((o) => {
    if (!o.isMesh) return;
    if (!originals.has(o.uuid)) {
      originals.set(o.uuid, o.material);
      toonMaterials.set(o.uuid, materialToCel(o.material));
    }
    o.material = mode === "original" ? originals.get(o.uuid) : toonMaterials.get(o.uuid);
    o.castShadow = true;
    o.receiveShadow = true;
  });
}

const pipeline = new Pipeline(renderer, scene, camera, { pixelBudget: 3.2e6 });

const seamPoint = new THREE.Vector3();
const seamBox = new THREE.Box3();

function smoothstep01(t) {
  t = THREE.MathUtils.clamp(t, 0, 1);
  return t * t * (3 - 2 * t);
}

function correctHeadSilhouette(root) {
  root.updateMatrixWorld(true);
  seamBox.setFromObject(root);
  const minY = seamBox.min.y;
  const maxY = seamBox.max.y;
  const height = Math.max(0.001, maxY - minY);
  const topThreshold = minY + height * 0.76;

  // Do not crush the imported horn/crest geometry. Instead, measure the
  // actual upper silhouette and insert a thin tapered membrane between the
  // two lobes. From FRONT/CHASE it closes the accidental "split head"; from
  // SIDE it is nearly edge-on and leaves the swept crest profile intact.
  const samples = [];
  let sourceMaterial = null;

  root.traverse((o) => {
    if (!o.isMesh || !o.geometry?.attributes?.position) return;
    if (!sourceMaterial && o.material) {
      sourceMaterial = Array.isArray(o.material) ? o.material[0] : o.material;
    }
    const pos = o.geometry.attributes.position;
    for (let i = 0; i < pos.count; i += 1) {
      seamPoint.fromBufferAttribute(pos, i);
      o.localToWorld(seamPoint);
      if (seamPoint.y >= topThreshold) samples.push(seamPoint.clone());
    }
  });

  if (samples.length < 8) return;

  let minX = Infinity;
  let maxX = -Infinity;
  let minTopY = Infinity;
  let maxTopY = -Infinity;
  let zSum = 0;
  for (const p of samples) {
    minX = Math.min(minX, p.x);
    maxX = Math.max(maxX, p.x);
    minTopY = Math.min(minTopY, p.y);
    maxTopY = Math.max(maxTopY, p.y);
    zSum += p.z;
  }

  const spanX = Math.max(0.02, maxX - minX);
  const spanY = Math.max(0.06, maxTopY - minTopY);
  const centerWorld = new THREE.Vector3(
    (minX + maxX) * 0.5,
    minTopY + spanY * 0.43,
    zSum / samples.length
  );

  const bridgeW = spanX * 0.48;
  const bridgeH = spanY * 0.68;
  const topW = bridgeW * 0.34;

  const positions = new Float32Array([
    -bridgeW * 0.5, -bridgeH * 0.5, 0,
     bridgeW * 0.5, -bridgeH * 0.5, 0,
     topW * 0.5,     bridgeH * 0.5, 0,
    -topW * 0.5,     bridgeH * 0.5, 0
  ]);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  geo.setIndex([0, 1, 2, 0, 2, 3]);
  geo.computeVertexNormals();

  const bridgeMat = cel({
    color: sourceMaterial?.color?.getHex?.() ?? 0xe9e7e2,
    bands: 3,
    tint: 0x6c5f8c,
    flat: false,
    map: sourceMaterial?.map ?? null,
    side: THREE.DoubleSide,
    cache: false
  });

  const bridge = new THREE.Mesh(geo, bridgeMat);
  bridge.name = "SakuraNPR_head_bridge";
  bridge.userData.noOutline = true;
  bridge.renderOrder = -1;

  const centerLocal = centerWorld.clone();
  root.worldToLocal(centerLocal);
  bridge.position.copy(centerLocal);
  root.add(bridge);
  root.updateMatrixWorld(true);

  canvas.dataset.headSilhouetteCorrection = "bridge";
}
const cameraForward = new THREE.Vector3();
const cameraSide = new THREE.Vector3();
const cameraUp = new THREE.Vector3(0, 1, 0);
const cameraTarget = new THREE.Vector3();

function getModelForward(target = cameraForward) {
  // The source asset's head points down local -Z. The runtime rotates the
  // model 180 degrees, so derive every named camera from that actual axis
  // instead of hard-coded world coordinates.
  target.set(0, 0, -1);
  if (model) target.applyQuaternion(model.quaternion);
  target.y = 0;
  return target.normalize();
}

function frameCamera() {
  const y = modelHeight * 0.48;
  const dist = Math.max(4.2, modelHeight * 2.6);
  cameraTarget.set(0, y, 0);

  const forward = getModelForward();
  cameraSide.crossVectors(cameraUp, forward).normalize();

  camera.position.copy(cameraTarget);
  if (cameraMode === "side") {
    camera.position
      .addScaledVector(cameraSide, dist)
      .addScaledVector(cameraUp, modelHeight * 0.10);
  } else if (cameraMode === "front") {
    camera.position
      .addScaledVector(forward, dist)
      .addScaledVector(cameraUp, modelHeight * 0.10);
  } else if (cameraMode === "chase" || cameraMode === "follow") {
    camera.position
      .addScaledVector(forward, -dist)
      .addScaledVector(cameraUp, modelHeight * 0.13);
  } else {
    camera.position
      .addScaledVector(cameraSide, dist * 0.72)
      .addScaledVector(forward, dist * 0.72)
      .addScaledVector(cameraUp, modelHeight * 0.16);
  }
  camera.lookAt(cameraTarget);
}

function resize() {
  const w = innerWidth;
  const h = innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  pipeline.setSize(w, h);
  // Keep the borrowed screen-space ink from exaggerating the imported
  // head seam while retaining the overall Sakura Crossing line treatment.
  pipeline.ink.mat.uniforms.uSens.value = 0.0058;
  pipeline.ink.mat.uniforms.uConcave.value = 0.034;
  pipeline.ink.mat.uniforms.uConcaveAmount.value = 0.28;
}
addEventListener("resize", resize);
resize();

document.querySelectorAll("[data-mode]").forEach((btn) => {
  btn.addEventListener("click", () => {
    renderMode = btn.dataset.mode;
    document.querySelectorAll("[data-mode]").forEach((b) => b.classList.toggle("active", b === btn));
    setModelMaterials(renderMode);
  });
});

document.querySelectorAll("[data-camera]").forEach((btn) => {
  btn.addEventListener("click", () => {
    cameraMode = btn.dataset.camera;
    document.querySelectorAll("[data-camera]").forEach((b) => b.classList.toggle("active", b === btn));
    frameCamera();
  });
});

const loader = new GLTFLoader();
loader.load(
  "../models/evowild-s/focus-rigged-v5.glb",
  (gltf) => {
    model = gltf.scene;
    model.rotation.y = Math.PI;
    stage.add(model);

    const box = new THREE.Box3().setFromObject(model);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    model.position.x -= center.x;
    model.position.y -= box.min.y;
    model.position.z -= center.z;
    model.updateMatrixWorld(true);

    correctHeadSilhouette(model);

    const correctedBox = new THREE.Box3().setFromObject(model);
    const correctedSize = new THREE.Vector3();
    correctedBox.getSize(correctedSize);
    modelHeight = Math.max(1, correctedSize.y);

    setModelMaterials(renderMode);

    if (gltf.animations.length) {
      mixer = new THREE.AnimationMixer(model);
      const clip = gltf.animations.find((c) => c.name === "EvoWild_S_Run_V5") || gltf.animations[0];
      const action = mixer.clipAction(clip);
      action.reset().play();
      clipEl.textContent = clip.name || "run clip";
    } else {
      clipEl.textContent = "no embedded clip";
    }

    frameCamera();
    loading.classList.add("hidden");
    canvas.dataset.asset = "focus-rigged-v5.glb";
    canvas.dataset.renderLane = "sakura-npr";
    canvas.dataset.nativeForwardAxis = "-Z";
    canvas.dataset.runtimeForwardAxis = "+Z";
    canvas.dataset.cameraAxisFix = "1";
    canvas.dataset.animationCount = String(gltf.animations.length);
  },
  undefined,
  (err) => {
    console.error(err);
    loading.textContent = "model load failed";
  }
);

const clock = new THREE.Clock();
let fpsFrames = 0;
let fpsTime = 0;
function tick() {
  const dt = Math.min(clock.getDelta(), 1 / 20);
  mixer?.update(dt);

  for (const stripe of stripes) {
    stripe.position.z -= 11.5 * dt;
    if (stripe.position.z < -31) stripe.position.z += 93.6;
  }

  fpsFrames += 1;
  fpsTime += dt;
  if (fpsTime >= 0.6) {
    fpsEl.textContent = Math.round(fpsFrames / fpsTime) + " FPS";
    fpsFrames = 0;
    fpsTime = 0;
  }

  if (renderMode === "sakura") {
    pipeline.render();
  } else {
    renderer.setRenderTarget(null);
    renderer.render(scene, camera);
  }
  requestAnimationFrame(tick);
}
tick();

window.__nprLane = { scene, camera, renderer, pipeline, get model(){ return model; }, THREE };