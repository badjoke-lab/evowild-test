import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { clone as cloneSkeletonSafe } from 'three/addons/utils/SkeletonUtils.js';
import type { Ctx, IKart, System } from '../types';

type RacerVisual = {
  kart: IKart;
  root: THREE.Group;
  mixer: THREE.AnimationMixer | null;
  action: THREE.AnimationAction | null;
};

const MODEL_URL = `${(import.meta as any).env.BASE_URL}models/evowild-s-hunyuan2mv-rigged.glb`;
const TARGET_HEIGHT = 1.62;

function hideKartGeometry(kart: IKart) {
  const keepShadow = kart.object.userData.shadowBlob as THREE.Object3D | undefined;
  kart.object.traverse((node) => {
    if (node === keepShadow) return;
    const renderable = node as THREE.Mesh;
    if (renderable.isMesh || (renderable as THREE.InstancedMesh).isInstancedMesh) {
      renderable.visible = false;
      renderable.castShadow = false;
    }
  });
  if (keepShadow) keepShadow.visible = true;
}

function fitCreature(model: THREE.Group) {
  // Rig metadata: Y is up, body length is Z, head is on -Z.
  // Kart Royale drives along local +Z, so rotate the creature 180°.
  model.rotation.set(0, Math.PI, 0);
  model.updateMatrixWorld(true);

  const box0 = new THREE.Box3().setFromObject(model);
  const size0 = box0.getSize(new THREE.Vector3());
  const height = Math.max(0.001, size0.y);
  model.scale.multiplyScalar(TARGET_HEIGHT / height);
  model.updateMatrixWorld(true);

  const box1 = new THREE.Box3().setFromObject(model);
  const center = box1.getCenter(new THREE.Vector3());
  model.position.x -= center.x;
  model.position.z -= center.z;
  model.position.y -= box1.min.y;
  model.updateMatrixWorld(true);
}

function applyEvoWildPalette(mesh: THREE.Mesh) {
  const source = mesh.geometry;
  const position = source?.getAttribute('position');
  if (!position) return;

  const geometry = source.clone();
  if (!geometry.getAttribute('normal')) geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  if (!box) return;

  const size = box.getSize(new THREE.Vector3());
  const dx = Math.max(1e-6, size.x);
  const dy = Math.max(1e-6, size.y);
  const dz = Math.max(1e-6, size.z);
  const colors = new Float32Array(position.count * 3);

  const silver = new THREE.Color(0x8fa4ad);
  const coolBlue = new THREE.Color(0x314f63);
  const cyan = new THREE.Color(0x3b9bad);
  const color = new THREE.Color();

  for (let i = 0; i < position.count; i++) {
    const nx = (position.getX(i) - box.min.x) / dx;
    const ny = (position.getY(i) - box.min.y) / dy;
    const nz = (position.getZ(i) - box.min.z) / dz;

    color.copy(silver);
    const sideDistance = Math.abs(nx - 0.5) * 2;
    if (ny < 0.33 || (sideDistance > 0.58 && ny < 0.68)) {
      color.lerp(coolBlue, 0.64);
    }
    const dorsal = ny > 0.82;
    const longitudinalTip = nz < 0.08 || nz > 0.92;
    if (dorsal || (longitudinalTip && ny > 0.55)) {
      color.lerp(cyan, 0.68);
    }

    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;
  }

  geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  mesh.geometry = geometry;
}

function tuneMaterials(model: THREE.Group, _kart: IKart) {
  model.traverse((node) => {
    const mesh = node as THREE.Mesh;
    if (!mesh.isMesh) return;

    applyEvoWildPalette(mesh);
    mesh.castShadow = false;
    mesh.receiveShadow = true;
    mesh.frustumCulled = true;

    const material = new THREE.MeshStandardMaterial({
      color: 0xffffff,
      vertexColors: true,
      roughness: 0.72,
      metalness: 0.08,
      envMapIntensity: 0.48,
      side: THREE.DoubleSide,
    });
    material.emissive.set(0x000000);
    material.emissiveIntensity = 0;
    material.toneMapped = true;
    mesh.material = material;
  });
}

export class EvoWildRacers implements System {
  private visuals: RacerVisual[] = [];

  async init(ctx: Ctx) {
    const gltf = await new GLTFLoader().loadAsync(MODEL_URL);
    const clip = gltf.animations.find((item) => item.name === 'EvoWild_S_Run') ?? gltf.animations[0] ?? null;

    for (const kart of ctx.race.karts) {
      hideKartGeometry(kart);

      const creature = cloneSkeletonSafe(gltf.scene) as THREE.Group;
      creature.name = `evowild_s_${kart.id}`;
      fitCreature(creature);
      tuneMaterials(creature, kart);

      const body = (kart.object.userData.body as THREE.Group | undefined) ?? kart.object;
      body.add(creature);

      let mixer: THREE.AnimationMixer | null = null;
      let action: THREE.AnimationAction | null = null;
      if (clip) {
        mixer = new THREE.AnimationMixer(creature);
        action = mixer.clipAction(clip);
        action.setLoop(THREE.LoopRepeat, Infinity);
        action.play();
      }

      this.visuals.push({ kart, root: creature, mixer, action });
    }

    const root = document.documentElement;
    root.dataset.evowildRacers = 'ready';
    root.dataset.evowildRacerCount = String(this.visuals.length);
    root.dataset.evowildRacerModel = 'hunyuan-rigged-s';
    root.dataset.evowildRacerClip = clip?.name ?? 'none';

    (window as any).__evowildRacers = {
      count: this.visuals.length,
      model: 'hunyuan-rigged-s',
      animation: clip?.name ?? null,
    };
  }

  update(_ctx: Ctx, dt: number) {
    for (const visual of this.visuals) {
      if (!visual.mixer || !visual.action) continue;
      const speed = Math.max(0, visual.kart.forwardSpeed);
      visual.action.timeScale = THREE.MathUtils.clamp(speed / 18, 0.38, 1.55);
      visual.mixer.update(dt);
    }
  }
}
