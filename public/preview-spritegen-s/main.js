import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const FRAME_COUNT = 8;
const CELL = 256;
const PLAYBACK_FPS = 12;
const MODEL_URL = "../models/evowild-s/focus-rigged-v5.glb";
const REQUIRED_CLIP = "EvoWild_S_Run_V5";

const sourceCanvas = document.querySelector("#source");
const previewCanvas = document.querySelector("#preview");
const atlasCanvas = document.querySelector("#atlas");
const previewCtx = previewCanvas.getContext("2d");
const atlasCtx = atlasCanvas.getContext("2d");
const stateEl = document.querySelector("#state");
const clipEl = document.querySelector("#clip");
const frameCountEl = document.querySelector("#frameCount");
const exportButton = document.querySelector("#export");

const renderer = new THREE.WebGLRenderer({
  canvas: sourceCanvas,
  alpha: true,
  antialias: true,
  preserveDrawingBuffer: true,
  powerPreference: "high-performance"
});
renderer.setPixelRatio(1);
renderer.setSize(sourceCanvas.width, sourceCanvas.height, false);
renderer.setClearColor(0x000000, 0);
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;

const scene = new THREE.Scene();
const camera = new THREE.OrthographicCamera(-2, 2, 2, -2, 0.01, 100);

scene.add(new THREE.HemisphereLight(0xf2f6ff, 0x28311f, 2.45));
const key = new THREE.DirectionalLight(0xfff0d7, 3.0);
key.position.set(-6, 9, -4);
scene.add(key);
const rim = new THREE.DirectionalLight(0xb9d8ff, 1.15);
rim.position.set(6, 5, 7);
scene.add(rim);

let model = null;
let mixer = null;
let clip = null;
let frames = [];
let animationHandle = 0;
let playbackStart = 0;

function setStatus(kind, text) {
  stateEl.className = "pill " + kind;
  stateEl.textContent = text;
}

function normalizeMaterials(root) {
  root.traverse((node) => {
    if (!node.isMesh) return;
    node.frustumCulled = false;
    node.castShadow = false;
    node.receiveShadow = false;
    const list = Array.isArray(node.material) ? node.material : [node.material];
    for (const material of list.filter(Boolean)) {
      material.side = THREE.DoubleSide;
      if ("roughness" in material) material.roughness = Math.max(material.roughness ?? 0.5, 0.5);
      if ("metalness" in material) material.metalness = Math.min(material.metalness ?? 0, 0.2);
      material.needsUpdate = true;
    }
  });
}

function fitSideCamera() {
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());
  const center = box.getCenter(new THREE.Vector3());

  // Runtime forward is +Z after the canonical 180 degree alignment.
  // A camera on -X maps world +Z to screen-right.
  const horizontal = Math.max(size.z * 1.28, 2.2);
  const vertical = Math.max(size.y * 1.24, 2.2);
  const half = Math.max(horizontal, vertical) * 0.5;

  camera.left = -half;
  camera.right = half;
  camera.top = half;
  camera.bottom = -half;
  camera.near = 0.01;
  camera.far = Math.max(30, size.x * 6 + 20);
  camera.position.set(center.x - Math.max(8, size.x * 4), center.y, center.z);
  camera.lookAt(center);
  camera.updateProjectionMatrix();

  sourceCanvas.dataset.forwardAxis = "+Z";
  sourceCanvas.dataset.screenFacing = "right";
  sourceCanvas.dataset.cameraAxis = "-X";
}

function drawFrameNumber(ctx, n, x, y) {
  ctx.save();
  ctx.fillStyle = "rgba(11,15,20,.78)";
  ctx.fillRect(x + 8, y + 8, 30, 24);
  ctx.fillStyle = "#f4f7fb";
  ctx.font = "700 13px system-ui";
  ctx.textBaseline = "middle";
  ctx.textAlign = "center";
  ctx.fillText(String(n), x + 23, y + 20);
  ctx.restore();
}

function renderFrameAt(time) {
  mixer.setTime(time);
  model.updateMatrixWorld(true);
  renderer.clear();
  renderer.render(scene, camera);

  const frame = document.createElement("canvas");
  frame.width = sourceCanvas.width;
  frame.height = sourceCanvas.height;
  frame.getContext("2d").drawImage(sourceCanvas, 0, 0);
  return frame;
}

function buildAtlas() {
  atlasCtx.clearRect(0, 0, atlasCanvas.width, atlasCanvas.height);
  for (let i = 0; i < frames.length; i += 1) {
    const col = i % 4;
    const row = Math.floor(i / 4);
    const x = col * CELL;
    const y = row * CELL;
    atlasCtx.drawImage(frames[i], x, y, CELL, CELL);
    drawFrameNumber(atlasCtx, i + 1, x, y);
  }
}

function playLoop(now) {
  if (!frames.length) return;
  if (!playbackStart) playbackStart = now;
  const elapsed = (now - playbackStart) / 1000;
  const frameIndex = Math.floor(elapsed * PLAYBACK_FPS) % frames.length;
  previewCtx.clearRect(0, 0, previewCanvas.width, previewCanvas.height);
  previewCtx.drawImage(frames[frameIndex], 0, 0, previewCanvas.width, previewCanvas.height);
  previewCanvas.dataset.frame = String(frameIndex);
  animationHandle = requestAnimationFrame(playLoop);
}

async function buildFrames(gltf) {
  model = gltf.scene;
  model.rotation.y = Math.PI;
  normalizeMaterials(model);
  scene.add(model);

  clip = gltf.animations.find((candidate) => candidate.name === REQUIRED_CLIP) || gltf.animations[0];
  if (!clip) throw new Error("No animation clip in canonical S runtime asset.");

  mixer = new THREE.AnimationMixer(model);
  const action = mixer.clipAction(clip);
  action.reset().play();
  action.paused = true;

  fitSideCamera();

  clipEl.textContent = clip.name + " · " + clip.duration.toFixed(2) + "s";
  sourceCanvas.dataset.asset = "focus-rigged-v5.glb";
  sourceCanvas.dataset.clip = clip.name;
  sourceCanvas.dataset.frameCount = String(FRAME_COUNT);
  sourceCanvas.dataset.sourceKind = "canonical-s-runtime";
  sourceCanvas.dataset.extraction = "deterministic-3d-to-2d";

  frames = [];
  for (let i = 0; i < FRAME_COUNT; i += 1) {
    const t = (i / FRAME_COUNT) * clip.duration;
    frames.push(renderFrameAt(t));
    frameCountEl.textContent = (i + 1) + " / " + FRAME_COUNT;
    await new Promise((resolve) => requestAnimationFrame(resolve));
  }

  buildAtlas();
  exportButton.disabled = false;
  setStatus("ready", "READY");
  sourceCanvas.dataset.ready = "1";
  atlasCanvas.dataset.ready = "1";
  atlasCanvas.dataset.frames = String(frames.length);
  atlasCanvas.dataset.transparent = "1";

  cancelAnimationFrame(animationHandle);
  playbackStart = 0;
  animationHandle = requestAnimationFrame(playLoop);
}

exportButton.addEventListener("click", () => {
  const a = document.createElement("a");
  a.download = "evowild-s-run-side-8f.png";
  a.href = atlasCanvas.toDataURL("image/png");
  a.click();
});

const loader = new GLTFLoader();
loader.load(
  MODEL_URL,
  (gltf) => {
    buildFrames(gltf).catch((error) => {
      console.error(error);
      setStatus("fail", "FAILED");
      clipEl.textContent = error.message;
      sourceCanvas.dataset.ready = "0";
    });
  },
  undefined,
  (error) => {
    console.error(error);
    setStatus("fail", "FAILED");
    clipEl.textContent = "model load failed";
    sourceCanvas.dataset.ready = "0";
  }
);

window.__spriteGenSPoc = {
  get frames() { return frames; },
  get clip() { return clip; },
  get model() { return model; },
  renderer,
  scene,
  camera
};
