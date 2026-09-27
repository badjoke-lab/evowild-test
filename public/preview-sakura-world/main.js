import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { PAL } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/palette.js";
import { cel } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/toon.js";
import { Pipeline } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/post.js";
import { buildSky } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/sky.js";
import { setOutlineResolution } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/outline.js";
import { buildWorld } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/world/index.js";
import { basisAt, normalAt, positionAt } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/world/planet.js";

const canvas = document.querySelector("#view");
const loading = document.querySelector("#loading");
const fpsEl = document.querySelector("#fps");
const clipEl = document.querySelector("#clip");
const speedEl = document.querySelector("#speed");

const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: false,
  powerPreference: "high-performance",
  stencil: false
});
renderer.setPixelRatio(1);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.NoToneMapping;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.setClearColor(new THREE.Color(PAL.fog), 1);

const scene = new THREE.Scene();
scene.fog = new THREE.Fog(PAL.fog, 44, 205);

const camera = new THREE.PerspectiveCamera(46, 1, 0.25, 600);
camera.rotation.order = "YXZ";

const sun = new THREE.DirectionalLight(PAL.sun, 2.25);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.camera.left = -34;
sun.shadow.camera.right = 34;
sun.shadow.camera.top = 34;
sun.shadow.camera.bottom = -34;
sun.shadow.camera.near = 1;
sun.shadow.camera.far = 200;
sun.shadow.bias = -0.0004;
sun.shadow.normalBias = 0.035;
scene.add(sun, sun.target);

const fill = new THREE.DirectionalLight(PAL.fill, 1.08);
scene.add(fill, fill.target);

const bounce = new THREE.DirectionalLight(0xd8cbe8, 0.34);
scene.add(bounce, bounce.target);

const hemi = new THREE.HemisphereLight(PAL.hemiSky, PAL.hemiGround, 1.12);
scene.add(hemi);

const sky = buildSky(scene, 500);
const world = buildWorld(scene);
const pipeline = new Pipeline(renderer, scene, camera, { pixelBudget: 4.6e6 });

const SUN_LOCAL = new THREE.Vector3(-52, 62, 56);
const FILL_LOCAL = new THREE.Vector3(48, 26, -44);
const BOUNCE_LOCAL = new THREE.Vector3(10, -18, 40);
const lightOffset = new THREE.Vector3();
const lightOrigin = new THREE.Vector3();

function seatLight(light, local, basis, origin) {
  lightOffset.set(0, 0, 0)
    .addScaledVector(basis.east, local.x)
    .addScaledVector(basis.up, local.y)
    .addScaledVector(basis.north, local.z);
  light.target.position.copy(origin);
  light.position.copy(origin).add(lightOffset);
}

const runnerAnchor = new THREE.Group();
scene.add(runnerAnchor);

let model = null;
let mixer = null;
let modelHeight = 2.0;
let cameraMode = "threeq";
let runZ = 13.6;
const runX = 1.85;
const runSpeed = 5.5;
speedEl.textContent = runSpeed.toFixed(1) + " m/s";

function materialToCel(src) {
  if (Array.isArray(src)) return src.map(materialToCel);
  return cel({
    color: src?.color?.getHex?.() ?? 0xe3e0df,
    bands: 3,
    tint: 0x6c5f8c,
    flat: false,
    map: src?.map ?? null,
    transparent: !!src?.transparent,
    opacity: src?.opacity ?? 1,
    side: src?.side ?? THREE.FrontSide,
    alphaTest: src?.alphaTest ?? 0,
    depthWrite: src?.depthWrite ?? true,
    vertexColors: !!src?.vertexColors,
    cache: false
  });
}

function applyRunnerMaterials(root) {
  root.traverse((o) => {
    if (!o.isMesh) return;
    o.material = materialToCel(o.material);
    o.castShadow = true;
    o.receiveShadow = true;
  });
}

const samplePoint = new THREE.Vector3();
const sampleBox = new THREE.Box3();

function addCentralHeadMass(root) {
  root.updateMatrixWorld(true);
  sampleBox.setFromObject(root);
  const minY = sampleBox.min.y;
  const maxY = sampleBox.max.y;
  const height = Math.max(0.001, maxY - minY);
  const threshold = minY + height * 0.76;

  const samples = [];
  root.traverse((o) => {
    if (!o.isMesh || !o.geometry?.attributes?.position) return;
    const pos = o.geometry.attributes.position;
    for (let i = 0; i < pos.count; i += 1) {
      samplePoint.fromBufferAttribute(pos, i);
      o.localToWorld(samplePoint);
      if (samplePoint.y >= threshold) samples.push(samplePoint.clone());
    }
  });
  if (samples.length < 8) return;

  let minX = Infinity, maxX = -Infinity, minTopY = Infinity, maxTopY = -Infinity, zSum = 0;
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
    minTopY + spanY * 0.08,
    zSum / samples.length
  );

  const geo = new THREE.IcosahedronGeometry(1, 2);
  geo.scale(spanX * 0.58, spanY * 0.25, spanX * 0.70);
  geo.computeVertexNormals();
  const mat = cel({ color: 0xd8d5e1, bands: 3, tint: 0x6b6486, flat: false, cache: false });
  const mass = new THREE.Mesh(geo, mat);
  mass.name = "SakuraWorld_head_mass";
  mass.castShadow = true;
  mass.receiveShadow = true;

  const headBone = root.getObjectByName("head");
  const anchor = headBone || root;
  anchor.updateMatrixWorld(true);
  const local = centerWorld.clone();
  anchor.worldToLocal(local);
  mass.position.copy(local);
  anchor.add(mass);
  canvas.dataset.headMassCorrection = headBone ? "head-cap-bone-v17" : "root-fallback";
}

const basisMatrix = new THREE.Matrix4();
const groundWorld = new THREE.Vector3();
const targetWorld = new THREE.Vector3();
const camWorld = new THREE.Vector3();
const upWorld = new THREE.Vector3();

function placeRunner() {
  const ground = world.heightAt(runX, runZ);
  const b = basisAt(runX, runZ);
  basisMatrix.makeBasis(b.east, b.up, b.north);
  runnerAnchor.quaternion.setFromRotationMatrix(basisMatrix);
  runnerAnchor.position.copy(positionAt(runX, ground, runZ, groundWorld));

  positionAt(runX, ground + modelHeight * 0.48, runZ, targetWorld);

  let dx = 0, dz = 0, eye = modelHeight * 0.28;
  if (cameraMode === "front") { dz = 5.7; eye = modelHeight * 0.20; }
  else if (cameraMode === "chase") { dz = -6.4; eye = modelHeight * 0.30; }
  else if (cameraMode === "side") { dx = 5.4; eye = modelHeight * 0.22; }
  else { dx = 4.6; dz = 4.8; eye = modelHeight * 0.30; }

  const cx = runX + dx;
  const cz = runZ + dz;
  const cground = world.heightAt(cx, cz);
  positionAt(cx, cground + modelHeight * 0.62 + eye, cz, camWorld);
  normalAt(cx, cz, upWorld);
  camera.position.copy(camWorld);
  camera.up.copy(upWorld);
  camera.lookAt(targetWorld);

  const lightBasis = basisAt(runX, runZ);
  lightOrigin.copy(runnerAnchor.position);
  seatLight(sun, SUN_LOCAL, lightBasis, lightOrigin);
  seatLight(fill, FILL_LOCAL, lightBasis, lightOrigin);
  seatLight(bounce, BOUNCE_LOCAL, lightBasis, lightOrigin);
  hemi.position.copy(lightBasis.up);
}

function resize() {
  const w = innerWidth;
  const h = innerHeight;
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  pipeline.setSize(w, h);
  setOutlineResolution(pipeline.size.x, pipeline.size.y);
}
addEventListener("resize", resize);
resize();

document.querySelectorAll("[data-camera]").forEach((btn) => {
  btn.addEventListener("click", () => {
    cameraMode = btn.dataset.camera;
    document.querySelectorAll("[data-camera]").forEach((b) => b.classList.toggle("active", b === btn));
    placeRunner();
  });
});

const loader = new GLTFLoader();
loader.load(
  "../models/evowild-s/focus-rigged-v5.glb",
  (gltf) => {
    model = gltf.scene;
    model.rotation.y = Math.PI;
    runnerAnchor.add(model);

    const box = new THREE.Box3().setFromObject(model);
    const size = new THREE.Vector3();
    const center = new THREE.Vector3();
    box.getSize(size);
    box.getCenter(center);
    model.position.x -= center.x;
    model.position.y -= box.min.y;
    model.position.z -= center.z;
    modelHeight = Math.max(1, size.y);

    applyRunnerMaterials(model);
    addCentralHeadMass(model);

    if (gltf.animations.length) {
      mixer = new THREE.AnimationMixer(model);
      const clip = gltf.animations.find((c) => c.name === "EvoWild_S_Run_V5") || gltf.animations[0];
      mixer.clipAction(clip).reset().play();
      clipEl.textContent = clip.name || "run clip";
    } else {
      clipEl.textContent = "no embedded clip";
    }

    canvas.dataset.asset = "focus-rigged-v5.glb";
    canvas.dataset.renderLane = "sakura-world";
    canvas.dataset.upstreamWorld = "de01898e89c7f6ab3fad93fa802f0f5ac66fbd81";
    canvas.dataset.cameraAxisFix = "1";
    canvas.dataset.upstreamOutline = "1";
    canvas.dataset.animationCount = String(gltf.animations.length);
    placeRunner();
    loading.classList.add("hidden");
  },
  undefined,
  (err) => {
    console.error(err);
    loading.textContent = "S model load failed";
  }
);

const clock = new THREE.Clock();
let fpsFrames = 0;
let fpsTime = 0;

function frame() {
  const dt = Math.min(clock.getDelta(), 1 / 20);
  mixer?.update(dt);
  world.update(dt);

  if (model) {
    runZ += runSpeed * dt;
    placeRunner();
  }

  sky.dome.position.copy(camera.position);
  sky.clouds.position.copy(camera.position);

  fpsFrames += 1;
  fpsTime += dt;
  if (fpsTime >= 0.6) {
    fpsEl.textContent = Math.round(fpsFrames / fpsTime) + " FPS";
    fpsFrames = 0;
    fpsTime = 0;
  }

  pipeline.render();
  requestAnimationFrame(frame);
}
frame();

window.__sakuraWorldLane = {
  scene, camera, renderer, pipeline, world, runnerAnchor,
  get model(){ return model; },
  get runZ(){ return runZ; },
  THREE
};