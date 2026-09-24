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

const MODEL_URL = `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-rigged.glb`;
const TARGET_HEIGHT = 1.42;

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
  model.rotation.set(0, -Math.PI / 2, 0);
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

function tuneMaterials(model: THREE.Group, kart: IKart) {
  model.traverse((node) => {
    const mesh = node as THREE.Mesh;
    if (!mesh.isMesh) return;
    mesh.castShadow = false;
    mesh.receiveShadow = true;
    mesh.frustumCulled = true;

    const tune = (material: THREE.Material) => {
      const m = material.clone() as THREE.MeshStandardMaterial;
      if ('color' in m && m.color) {
        m.color.lerp(kart.stats.color, 0.16);
      }
      if ('roughness' in m) m.roughness = Math.max(0.5, m.roughness ?? 0.5);
      if ('metalness' in m) m.metalness = Math.min(0.32, m.metalness ?? 0.15);
      return m;
    };

    mesh.material = Array.isArray(mesh.material)
      ? mesh.material.map(tune)
      : tune(mesh.material);
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
