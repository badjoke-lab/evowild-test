import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";

const loader = new GLTFLoader();
const clay = new THREE.MeshStandardMaterial({
  color: 0x8796ad,
  roughness: 0.72,
  metalness: 0.03
});

async function loadModel(url) {
  const gltf = await loader.loadAsync(url);
  const root = gltf.scene;
  root.traverse((node) => {
    if (node.isMesh) {
      node.material = clay.clone();
      node.castShadow = true;
      node.receiveShadow = true;
    }
  });
  return root;
}

function fitModel(root) {
  const box = new THREE.Box3().setFromObject(root);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  root.position.sub(center);
  return { size, span: Math.max(size.x, size.y, size.z) };
}

function setup(canvas) {
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: false });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
  renderer.setClearColor(0x0e1420, 1);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(28, 1, 0.01, 200);
  scene.add(new THREE.HemisphereLight(0xeaf2ff, 0x263144, 2.2));

  const key = new THREE.DirectionalLight(0xffffff, 3.2);
  key.position.set(4, 6, 5);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x9ec7ff, 2.0);
  rim.position.set(-4, 2, -5);
  scene.add(rim);

  return { renderer, scene, camera };
}

async function mount(canvasId, url, mode) {
  const canvas = document.getElementById(canvasId);
  const { renderer, scene, camera } = setup(canvas);
  const root = await loadModel(url);
  const { size, span } = fitModel(root);
  scene.add(root);

  const distance = span * 2.1;
  if (mode === "side") camera.position.set(distance, span * 0.10, 0);
  else camera.position.set(distance * 0.82, span * 0.16, distance * 0.82);
  camera.lookAt(0, 0, 0);
  camera.near = span * 0.01;
  camera.far = span * 10;
  camera.updateProjectionMatrix();

  function resize() {
    const rect = canvas.getBoundingClientRect();
    const w = Math.max(1, Math.floor(rect.width));
    const h = Math.max(1, Math.floor(rect.height));
    if (canvas.width !== w || canvas.height !== h) renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
  }
  resize();
  renderer.render(scene, camera);
  return { size };
}

const base = "/models/evowild-s/source-lod2.glb";
const v2 = "/models/evowild-s/source-lod2-shape-v2.glb";

try {
  const results = await Promise.all([
    mount("base-side", base, "side"),
    mount("v2-side", v2, "side"),
    mount("base-34", base, "threequarter"),
    mount("v2-34", v2, "threequarter")
  ]);
  document.body.dataset.shapeReview = "ready";
  document.body.dataset.baseSize = results[0].size.toArray().map(v => v.toFixed(4)).join(",");
  document.body.dataset.v2Size = results[1].size.toArray().map(v => v.toFixed(4)).join(",");
} catch (error) {
  console.error("SHAPE_V2_REVIEW_ERROR", error);
  document.body.dataset.shapeReview = "error";
  document.body.dataset.shapeError = String(error?.stack || error);
}
