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

function frameCamera() {
  const y = modelHeight * 0.48;
  const target = new THREE.Vector3(0, y, 0);
  const dist = Math.max(4.2, modelHeight * 2.6);
  if (cameraMode === "side") camera.position.set(dist, y * 1.05, 0);
  else if (cameraMode === "front") camera.position.set(0, y * 1.04, dist);
  else if (cameraMode === "chase") camera.position.set(0, y * 1.08, -dist);
  else camera.position.set(dist * 0.72, y * 1.15, dist * 0.72);
  camera.lookAt(target);
}

function resize() {
  const w = innerWidth;
  const h = innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  pipeline.setSize(w, h);
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
    modelHeight = Math.max(1, size.y);

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