import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { PAL } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/palette.js";
import { cel } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/toon.js";
import { Pipeline } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/post.js";
import { buildSky } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/sky.js";
import { setOutlineResolution } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/core/outline.js";
import { buildWorld } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/world/index.js";
import { basisAt, normalAt, positionAt } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/world/planet.js";
import { centerX, ROAD_HALF } from "https://cdn.jsdelivr.net/gh/Kenton-GMI/sakura-crossing@de01898e89c7f6ab3fad93fa802f0f5ac66fbd81/src/world/street.js";

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
const pipeline = new Pipeline(renderer, scene, camera, { pixelBudget: 2.4e6 });
pipeline.forceScale = 1.15;

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

const crestPoint = new THREE.Vector3();

function smooth01(x) {
  x = THREE.MathUtils.clamp(x, 0, 1);
  return x * x * (3 - 2 * x);
}

function repairWeightedHeadCrest(root) {
  let changed = 0;
  let maxShift = 0;

  root.updateMatrixWorld(true);

  root.traverse((o) => {
    if (!o.isSkinnedMesh || !o.geometry?.attributes?.position) return;
    const skinIndex = o.geometry.attributes.skinIndex;
    const skinWeight = o.geometry.attributes.skinWeight;
    if (!skinIndex || !skinWeight || !o.skeleton) return;

    const headIndex = o.skeleton.bones.findIndex((b) => b.name === "head");
    if (headIndex < 0) return;

    const g = o.geometry.clone();
    const pos = g.attributes.position;
    const eligible = [];

    for (let i = 0; i < pos.count; i += 1) {
      let headWeight = 0;
      for (let k = 0; k < 4; k += 1) {
        if (skinIndex.getComponent(i, k) === headIndex) {
          headWeight += skinWeight.getComponent(i, k);
        }
      }
      if (headWeight < 0.18) continue;
      crestPoint.fromBufferAttribute(pos, i);
      eligible.push({ i, x: crestPoint.x, y: crestPoint.y, z: crestPoint.z, w: headWeight });
    }

    if (eligible.length < 8) return;

    const minY = Math.min(...eligible.map((p) => p.y));
    const maxY = Math.max(...eligible.map((p) => p.y));
    const minZ = Math.min(...eligible.map((p) => p.z));
    const maxZ = Math.max(...eligible.map((p) => p.z));
    const centerX = (Math.min(...eligible.map((p) => p.x)) + Math.max(...eligible.map((p) => p.x))) * 0.5;
    const yStart = minY + (maxY - minY) * 0.60;
    const zStart = minZ + (maxZ - minZ) * 0.65;

    for (const p of eligible) {
      if (p.y <= yStart || p.z <= zStart) continue;

      const hy = smooth01((p.y - yStart) / Math.max(1e-6, maxY - yStart));
      const hz = smooth01((p.z - zStart) / Math.max(1e-6, maxZ - zStart));
      const hw = smooth01((p.w - 0.18) / 0.45);
      const strength = hy * (0.55 + 0.45 * hz) * (0.70 + 0.30 * hw);

      // Narrow only the high swept crest. The face, muzzle and broad crest
      // base remain unchanged. This mirrors the successful Blender-side
      // diagnosis but keeps the experiment isolated to this page.
      const scaleX = 1.0 - 0.62 * strength;
      const oldX = p.x;
      const nextX = centerX + (p.x - centerX) * scaleX;
      const nextZ = p.z - 0.010 * strength;

      pos.setXYZ(p.i, nextX, p.y, nextZ);
      changed += 1;
      maxShift = Math.max(maxShift, Math.abs(oldX - nextX));
    }

    if (changed) {
      pos.needsUpdate = true;
      g.computeVertexNormals();
      g.computeBoundingBox();
      g.computeBoundingSphere();
      o.geometry = g;
    }
  });

  canvas.dataset.headCrestRepair = changed ? "skin-weight-v18" : "none";
  canvas.dataset.headCrestChangedVertices = String(changed);
  canvas.dataset.headCrestMaxShift = maxShift.toFixed(6);
}
const basisMatrix = new THREE.Matrix4();
const groundWorld = new THREE.Vector3();
const targetWorld = new THREE.Vector3();
const camWorld = new THREE.Vector3();
const upWorld = new THREE.Vector3();

function placeRunner() {
  const runX = centerX(runZ);
  const ground = world.heightAt(runX, runZ);
  const b = basisAt(runX, runZ);
  basisMatrix.makeBasis(b.east, b.up, b.north);
  runnerAnchor.quaternion.setFromRotationMatrix(basisMatrix);
  runnerAnchor.position.copy(positionAt(runX, ground, runZ, groundWorld));

  positionAt(runX, ground + modelHeight * 0.48, runZ, targetWorld);

  let dx = 0, dz = 0, eye = modelHeight * 0.28;
  if (cameraMode === "front") { dz = -4.8; eye = modelHeight * 0.20; }
  else if (cameraMode === "chase") { dz = 4.6; eye = modelHeight * 0.34; }
  else if (cameraMode === "side") { dx = -ROAD_HALF * 0.68; eye = modelHeight * 0.85; }
  else { dx = ROAD_HALF * 0.72; dz = 3.6; eye = modelHeight * 0.28; }

  canvas.dataset.cameraLongitudinalOffset = dz.toFixed(2);
  canvas.dataset.cameraMode = cameraMode;
  const cz = runZ + dz;
  const cx = centerX(cz) + dx;
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

function setCameraMode(mode) {
  cameraMode = mode;
  document.querySelectorAll("[data-camera]").forEach((b) => {
    b.classList.toggle("active", b.dataset.camera === mode);
  });
  placeRunner();
}

document.querySelectorAll("[data-camera]").forEach((btn) => {
  btn.addEventListener("click", () => setCameraMode(btn.dataset.camera));
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

    repairWeightedHeadCrest(model);
    applyRunnerMaterials(model);

    if (gltf.animations.length) {
      mixer = new THREE.AnimationMixer(model);
      const clip = gltf.animations.find((c) => c.name === "EvoWild_S_Run_V5") || gltf.animations[0];
      mixer.clipAction(clip).reset().play();
      clipEl.textContent = clip.name || "run clip";
    } else {
      clipEl.textContent = "no embedded clip";
    }

    canvas.dataset.asset = "focus-rigged-v5.glb";
    canvas.dataset.headMassCorrection = "removed-v18";
    canvas.dataset.renderLane = "sakura-world";
    canvas.dataset.upstreamWorld = "de01898e89c7f6ab3fad93fa802f0f5ac66fbd81";
    canvas.dataset.cameraAxisFix = "2";
    canvas.dataset.runDirection = "-Z";
    canvas.dataset.upstreamOutline = "1";
    canvas.dataset.animationCount = String(gltf.animations.length);
    canvas.dataset.worldSimulation = "frozen-render-environment";
    canvas.dataset.pipelineScale = String(pipeline.forceScale);
    placeRunner();
    pipeline.render();
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
let renderPaused = false;

function renderOnce() {
  sky.dome.position.copy(camera.position);
  sky.clouds.position.copy(camera.position);
  pipeline.render();
}

function pauseRendering() {
  renderPaused = true;
}

function resumeRendering() {
  clock.getDelta();
  renderPaused = false;
}

function frame() {
  const dt = Math.min(clock.getDelta(), 1 / 20);

  if (!renderPaused) {
    mixer?.update(dt);

    // The imported district is used as a rendered race environment here, not as
    // the original walkable simulation. Keep trains/petals/interactables frozen:
    // updating the entire upstream simulation every frame starves camera input
    // on low-power/headless GPUs while adding nothing to this lane's goal.
    if (model) {
      // The rig faces toward decreasing authored Z in this world. Advance in
      // that direction so the creature is not visually running backwards.
      runZ -= runSpeed * dt;
      if (runZ < -18) runZ = 18;
      placeRunner();
    }

    fpsFrames += 1;
    fpsTime += dt;
    if (fpsTime >= 0.6) {
      fpsEl.textContent = Math.round(fpsFrames / fpsTime) + " FPS";
      fpsFrames = 0;
      fpsTime = 0;
    }

    renderOnce();
  }

  requestAnimationFrame(frame);
}
frame();

window.__sakuraWorldLane = {
  scene, camera, renderer, pipeline, world, runnerAnchor,
  get model(){ return model; },
  get runZ(){ return runZ; },
  setCameraMode,
  pauseRendering,
  resumeRendering,
  renderOnce,
  THREE
};