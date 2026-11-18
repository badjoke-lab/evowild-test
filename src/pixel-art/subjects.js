import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone } from 'three/addons/utils/SkeletonUtils.js';
import { createContactIK } from '../s_contact_ik.js';
import { createAuthoredDrive } from '../s_authored_drive.js';
import { createBodyCoupling } from '../s_body_coupling.js';
import { identifyFootSurfaces } from '../s_foot_contact_geometry.js';
import { selectSolePatches } from '../s_sole_metrics.js';

export const MESH_LAYER = 1;
export const POINT_LAYER = 2;
export const MAX_POINTS = 12000;
export const ASSET = 'models/evowild-s/review/d3c-scapula-author-v2.glb';
export const WORLD_SCALE = 2.85 / 1.28;

export function seededRandom(seed) {
  return () => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 4294967296;
  };
}

export async function loadSubject() {
  const gltf = await new GLTFLoader().loadAsync(`${import.meta.env.BASE_URL}${ASSET}`);
  const model = gltf.scene;
  const mesh = model.getObjectByProperty('isSkinnedMesh', true);
  const clip = gltf.animations.find(({ name }) => name === 'EvoWild_S_Run_V5');
  const authored = gltf.animations.find(({ name }) => name === 'D3C_V2_Drive_Pose');
  if (!mesh || !clip || !authored) throw new Error('D3-C v2 の骨格と走行クリップが見つかりません。');

  mesh.layers.set(MESH_LAYER);
  mesh.frustumCulled = false; // Keep the full pack in the measurement while turning.

  // Use the same world scale and bind-pose placement as s-run-review.html.
  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  model.scale.setScalar(2.85 / box.getSize(new THREE.Vector3()).y);
  model.updateMatrixWorld(true);
  box.setFromObject(model);
  const center = box.getCenter(new THREE.Vector3());
  model.position.set(-center.x, -box.min.y, -center.z);
  model.updateMatrixWorld(true);
  const patches = selectSolePatches(mesh);
  const footSurfaces = identifyFootSurfaces(mesh, patches);
  return { model, mesh, clip, authored, patches, footSurfaces, surface: sampleSurface(mesh.geometry) };
}

function lowDiscrepancy(index) {
  let value = 0;
  for (let bit = .5; index > 0; bit *= .5, index >>>= 1) value += (index & 1) * bit;
  return value;
}

function sampleSurface(geometry) {
  const { position, skinIndex, skinWeight } = geometry.attributes;
  const index = geometry.index;
  const triangleCount = index.count / 3;
  const a = new THREE.Vector3();
  const b = new THREE.Vector3();
  const c = new THREE.Vector3();
  const edge = new THREE.Vector3();
  const areas = new Float64Array(triangleCount);
  let area = 0;
  for (let triangle = 0; triangle < triangleCount; triangle++) {
    a.fromBufferAttribute(position, index.getX(triangle * 3));
    b.fromBufferAttribute(position, index.getX(triangle * 3 + 1));
    c.fromBufferAttribute(position, index.getX(triangle * 3 + 2));
    area += edge.subVectors(b, a).cross(c.sub(a)).length() * .5;
    areas[triangle] = area;
  }

  // Each entry remembers the exact triangle and its barycentric coordinates in rest space.
  const ids = new Float32Array(MAX_POINTS * 3);
  const barycentric = new Float32Array(MAX_POINTS * 2);
  const random = seededRandom(73015);
  const offset = random();
  for (let i = 0; i < MAX_POINTS; i++) {
    const target = ((lowDiscrepancy(i + 1) + offset) % 1) * area;
    let low = 0;
    let high = triangleCount - 1;
    while (low < high) {
      const mid = (low + high) >>> 1;
      if (areas[mid] > target) high = mid;
      else low = mid + 1;
    }
    const ai = index.getX(low * 3);
    const bi = index.getX(low * 3 + 1);
    const ci = index.getX(low * 3 + 2);
    const root = Math.sqrt(random());
    const v = root * random();
    const w = root - v;
    ids.set([ai, bi, ci], i * 3);
    barycentric.set([v, w], i * 2);

  }
  const points = new THREE.BufferGeometry();
  points.setAttribute('position', new THREE.BufferAttribute(ids, 3));
  points.setAttribute('sampleUV', new THREE.BufferAttribute(barycentric, 2));

  const width = 256;
  const height = Math.ceil(position.count * 3 / width);
  const data = new Float32Array(width * height * 4);
  for (let i = 0; i < position.count; i++) {
    data.set([position.getX(i), position.getY(i), position.getZ(i), 1], i * 12);
    data.set([skinIndex.getX(i), skinIndex.getY(i), skinIndex.getZ(i), skinIndex.getW(i)], i * 12 + 4);
    data.set([skinWeight.getX(i), skinWeight.getY(i), skinWeight.getZ(i), skinWeight.getW(i)], i * 12 + 8);
  }
  const vertices = new THREE.DataTexture(data, width, height, THREE.RGBAFormat, THREE.FloatType);
  vertices.needsUpdate = true;
  return { points, vertices };
}

export function createSubject(source, material, index) {
  const root = new THREE.Group();
  const motionRoot = new THREE.Group();
  const model = clone(source.model);
  motionRoot.add(model);
  root.add(motionRoot);
  root.updateMatrixWorld(true);
  const mesh = model.getObjectByProperty('isSkinnedMesh', true);
  const { clip, authored, patches, footSurfaces } = source;
  const ik = createContactIK(mesh, patches, {
    toeSurfaces: footSurfaces, continuousToe: true, toeRoundingWidth: .0015, foreReach: true
  });
  const body = createBodyCoupling(mesh, clip, { smoothReturn: true, smoothNativeJoin: true, driveFlex: false, foreLoad: true });
  const drive = createAuthoredDrive(mesh, clip, authored);
  const mixer = new THREE.AnimationMixer(model);
  mixer.clipAction(clip).play();
  mesh.skeleton.computeBoneTexture();
  const points = new THREE.Points(source.surface.points, material(mesh, source.surface.vertices));
  points.frustumCulled = false;
  points.layers.set(POINT_LAYER);
  mesh.add(points);
  const placement = new THREE.Vector3();
  const phase = (index * .61803398875) % 1;
  let contact;

  // Evaluate the unmodified review pipeline at its physical world coordinates.
  // Recenter only the completed pose for the viewer's fixed camera and crowd layout.
  function pose(state) {
    root.position.set(0, 0, 0);
    motionRoot.position.z = state.distance;
    const time = state.cycles * clip.duration;
    mixer.setTime(time);
    body.apply(time, state.poseRate);
    drive.applyBody(time);
    root.updateMatrixWorld(true);
    ik.apply();
    contact = ik.apply(drive.swingGuides(ik.limbs));
    root.position.copy(placement);
    root.position.z -= state.distance;
    root.updateMatrixWorld(true);
  }

  return {
    root, placement, mesh, points, kinematics: ik.kinematics,
    get contact() { return contact; },
    step(dt, rate) { pose(ik.advance(dt, rate)); },
    reset(rate, seconds = 0) {
      const k = ik.kinematics(rate || 1);
      const cycles = rate ? phase + seconds * k.cadence : 0;
      pose(ik.reset(cycles, cycles * k.stride, rate));
    }
  };
}

export function layoutSubjects(subjects, count) {
  const columns = count === 1 ? 1 : Math.ceil(Math.sqrt(count * 1.45));
  const rows = Math.ceil(count / columns);
  for (let i = 0; i < subjects.length; i++) {
    const x = i % columns;
    const z = Math.floor(i / columns);
    subjects[i].root.visible = i < count;
    subjects[i].placement.set((x - (columns - 1) * .5) * 1.38 * WORLD_SCALE, 0, (z - (rows - 1) * .5) * 2.15 * WORLD_SCALE);
  }
  return Math.hypot((columns - 1) * 1.38, (rows - 1) * 2.15) * WORLD_SCALE;
}
