import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import "./tripo_motion_review.css";

const canvas = document.querySelector("#scene");
const statusEl = document.querySelector("#status");
const cameraReadout = document.querySelector("#cameraReadout");
const clipReadout = document.querySelector("#clipReadout");
const boneReadout = document.querySelector("#boneReadout");
const viewButtons = [...document.querySelectorAll("[data-view]")];

const isMobile = matchMedia("(pointer: coarse)").matches || innerWidth < 800;
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: !isMobile,
  powerPreference: "default",
  precision: "mediump"
});
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.02;
renderer.setPixelRatio(Math.min(devicePixelRatio, isMobile ? 1.25 : 1.5));

const scene = new THREE.Scene();
scene.background = new THREE.Color(0xb7c4ca);
scene.fog = new THREE.Fog(0xb7c4ca, 80, 190);

const camera = new THREE.PerspectiveCamera(42, 1, 0.01, 500);
scene.add(camera);

scene.add(new THREE.HemisphereLight(0xeaf4ff, 0x313830, 1.45));
const key = new THREE.DirectionalLight(0xffefd4, 1.9);
key.position.set(20, 30, 14);
scene.add(key);
const fill = new THREE.DirectionalLight(0x8bb6d7, 0.5);
fill.position.set(-18, 12, -16);
scene.add(fill);

const ground = new THREE.Mesh(
  new THREE.PlaneGeometry(240, 240),
  new THREE.MeshStandardMaterial({ color: 0x657462, roughness: 1 })
);
ground.rotation.x = -Math.PI / 2;
ground.position.y = 0;
scene.add(ground);

const grid = new THREE.GridHelper(80, 80, 0xd8ddd8, 0x879087);
grid.position.y = 0.002;
scene.add(grid);

let model = null;
let mixer = null;
let activeView = "SIDE";
let referenceRadius = 2;
let floorY = 0;
const dynamicBox = new THREE.Box3();
const center = new THREE.Vector3();
const size = new THREE.Vector3();
const clock = new THREE.Clock();

function setStatus(text, state) {
  statusEl.textContent = text;
  statusEl.dataset.state = state;
  document.body.dataset.reviewState = state;
}

function countBones(root) {
  let bones = 0;
  root.traverse((node) => {
    if (node.isBone) bones += 1;
  });
  return bones;
}

function setActiveView(view) {
  activeView = view;
  cameraReadout.textContent = view;
  for (const button of viewButtons) {
    button.dataset.active = button.dataset.view === view ? "1" : "0";
  }
}
for (const button of viewButtons) {
  button.addEventListener("click", () => setActiveView(button.dataset.view));
}
setActiveView("SIDE");

function updateBounds() {
  if (!model) return;
  dynamicBox.setFromObject(model);
  if (dynamicBox.isEmpty()) return;
  dynamicBox.getCenter(center);
  dynamicBox.getSize(size);
  referenceRadius = Math.max(0.6, size.length() * 0.46);
  floorY = dynamicBox.min.y;
  ground.position.y = floorY - 0.015;
  grid.position.y = floorY - 0.012;
}

function updateCamera() {
  if (!model) return;
  updateBounds();

  const r = referenceRadius;
  const target = center.clone().add(new THREE.Vector3(0, size.y * 0.08, 0));

  if (activeView === "SIDE") {
    camera.position.set(center.x + r * 2.5, center.y + r * 0.45, center.z);
  } else if (activeView === "LOW") {
    camera.position.set(center.x + r * 2.25, floorY + r * 0.34, center.z + r * 0.18);
  } else if (activeView === "CHASE") {
    camera.position.set(center.x, center.y + r * 0.48, center.z + r * 2.65);
  } else {
    camera.position.set(center.x, center.y + r * 0.48, center.z - r * 2.65);
  }

  camera.lookAt(target);
  camera.near = Math.max(0.01, r * 0.015);
  camera.far = Math.max(120, r * 25);
  camera.updateProjectionMatrix();
}

function resize() {
  renderer.setSize(innerWidth, innerHeight, false);
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

const assetUrl = `${import.meta.env.BASE_URL}experiments/tripo-s/t1-steady-run.glb`;
const loader = new GLTFLoader();

loader.load(
  assetUrl,
  (gltf) => {
    model = gltf.scene;
    scene.add(model);

    const clips = gltf.animations || [];
    const bones = countBones(model);
    boneReadout.textContent = `bones ${bones}`;
    document.body.dataset.boneCount = String(bones);
    document.body.dataset.clipCount = String(clips.length);

    updateBounds();

    if (!clips.length) {
      clipReadout.textContent = "clip NONE";
      setStatus("ERROR_NO_ANIMATION", "error");
      return;
    }

    const clip = clips[0];
    clipReadout.textContent = `${clip.name || "clip0"} ${clip.duration.toFixed(2)}s`;
    document.body.dataset.clipDuration = clip.duration.toFixed(4);
    document.body.dataset.clipName = clip.name || "clip0";

    mixer = new THREE.AnimationMixer(model);
    const action = mixer.clipAction(clip);
    action.setLoop(THREE.LoopRepeat, Infinity);
    action.play();

    setStatus("READY", "ready");
  },
  undefined,
  (error) => {
    console.error("Tripo T1 review asset failed to load", error);
    setStatus("ERROR_LOAD", "error");
  }
);

function animate() {
  requestAnimationFrame(animate);
  const dt = Math.min(clock.getDelta(), 0.05);
  if (mixer) mixer.update(dt);
  updateCamera();
  renderer.render(scene, camera);
}
requestAnimationFrame(animate);
