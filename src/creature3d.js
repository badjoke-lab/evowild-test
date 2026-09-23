import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { clone as cloneSkeletonSafe } from "three/addons/utils/SkeletonUtils.js";

export const CREATURE_3D_PROFILES = {
  sTripoSrSide: {
    id: "s-triposr-side-authority",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-triposr-side.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.72,
      side: "front",
      preserveBaseColorMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "candidate_unapproved",
    notes: [
      "Generated with TripoSR on GitHub Actions CPU from the SIDE authority reference.",
      "Geometry is mostly one connected component and uses vertex colors rather than texture maps.",
      "Not approved as final EvoWild S-Type; retained for direct engine comparison."
    ]
  },
  sSf3dWhite: {
    id: "s-sf3d-crop30-white",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-white.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.08,
      minRoughness: 0.52,
      side: "front",
      preserveBaseColorMap: true,
      maxAnisotropy: 4
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "candidate_unapproved",
    notes: [
      "Generated from the same corrected crop30 3/4 reference with white background preserved.",
      "Tests whether manual alpha cutout was flattening depth cues.",
      "Not approved as final EvoWild S-Type."
    ]
  },
  sSf3dCorrected: {
    id: "s-sf3d-corrected-candidate",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-corrected.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.08,
      minRoughness: 0.52,
      side: "front",
      preserveBaseColorMap: true,
      maxAnisotropy: 4
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "candidate_unapproved",
    notes: [
      "Generated from the corrected single-creature crop on Stable Fast 3D.",
      "Input-contamination artifact is removed, but silhouette fidelity still requires visual review.",
      "Use front-side rendering by default; the source GLB is not approved as a final EvoWild S-Type."
    ]
  },
  sSf3dSide: {
    id: "s-sf3d-side-authority",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-side.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.08,
      minRoughness: 0.52,
      side: "front",
      preserveBaseColorMap: true,
      maxAnisotropy: 4
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "rejected_comparison",
    notes: [
      "Generated from the SIDE authority reference only.",
      "Browser comparison confirmed it is heavier (16,112 triangles) and visually less faithful than the corrected 3/4 candidate.",
      "Rejected as the active SF3D candidate; retained only as evidence and for direct comparison."
    ]
  },
  sSf3dPrototype: {
    id: "s-sf3d-clean-prototype",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-clean.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.08,
      minRoughness: 0.52,
      side: "double",
      preserveBaseColorMap: true,
      maxAnisotropy: 4
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "prototype_only",
    notes: [
      "Generated from the first Stable Fast 3D input that contained partial-image contamination.",
      "Use as a loader/performance validation asset, not as an approved EvoWild S-Type model."
    ]
  }
};

function resolveSide(side) {
  if (side === "front") return THREE.FrontSide;
  if (side === "back") return THREE.BackSide;
  return THREE.DoubleSide;
}

function normalizeMaterial(material, renderer, profile) {
  const normalized = material.clone();
  const materialProfile = profile.material || {};

  if ("metalness" in normalized && Number.isFinite(materialProfile.metalness)) {
    normalized.metalness = materialProfile.metalness;
  }
  if ("roughness" in normalized && Number.isFinite(materialProfile.minRoughness)) {
    normalized.roughness = Math.max(materialProfile.minRoughness, normalized.roughness ?? materialProfile.minRoughness);
  }
  if (normalized.color) normalized.color.set(0xffffff);

  if (normalized.map && materialProfile.preserveBaseColorMap !== false) {
    normalized.map.colorSpace = THREE.SRGBColorSpace;
    const maxSupported = renderer?.capabilities?.getMaxAnisotropy?.() ?? 1;
    const requested = materialProfile.maxAnisotropy ?? 1;
    normalized.map.anisotropy = Math.min(requested, maxSupported);
    normalized.map.needsUpdate = true;
  }

  normalized.side = resolveSide(materialProfile.side);
  normalized.needsUpdate = true;
  return normalized;
}

export function cloneCreature3D(source) {
  // SkeletonUtils.clone is safe for the current static mesh and also avoids
  // having to redesign this adapter when a future accepted GLB is rigged.
  return cloneSkeletonSafe(source);
}

export function inspectCreature3D(model) {
  let triangles = 0;
  let meshes = 0;
  const materials = new Set();
  const textures = new Set();

  model.traverse((node) => {
    if (!node.isMesh || !node.geometry) return;
    meshes += 1;
    const geometry = node.geometry;
    triangles += geometry.index
      ? geometry.index.count / 3
      : (geometry.getAttribute("position")?.count || 0) / 3;

    const nodeMaterials = Array.isArray(node.material) ? node.material : [node.material];
    for (const material of nodeMaterials) {
      if (!material) continue;
      materials.add(material.uuid);
      if (material.map) textures.add(material.map.uuid);
      if (material.normalMap) textures.add(material.normalMap.uuid);
      if (material.roughnessMap) textures.add(material.roughnessMap.uuid);
      if (material.metalnessMap) textures.add(material.metalnessMap.uuid);
    }
  });

  model.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(model);
  const size = box.getSize(new THREE.Vector3());

  return {
    triangles: Math.round(triangles),
    meshes,
    materials: materials.size,
    textures: textures.size,
    bounds: {
      x: Number(size.x.toFixed(5)),
      y: Number(size.y.toFixed(5)),
      z: Number(size.z.toFixed(5))
    }
  };
}

export function fitCreature3D(model, {
  renderer,
  profile,
  placement = "race",
  targetHeight,
  groundY,
  materialSide
}) {
  const placementProfile = profile.placements?.[placement] || {};
  const desiredHeight = targetHeight ?? placementProfile.targetHeight ?? 1;
  const desiredGroundY = groundY ?? placementProfile.groundY ?? 0;

  const [rx, ry, rz] = profile.rotation || [0, 0, 0];
  model.rotation.set(rx, ry, rz);
  model.updateMatrixWorld(true);

  const initialBox = new THREE.Box3().setFromObject(model);
  const initialSize = initialBox.getSize(new THREE.Vector3());
  const height = Math.max(0.001, initialSize.y);
  model.scale.multiplyScalar(desiredHeight / height);
  model.updateMatrixWorld(true);

  const fittedBox = new THREE.Box3().setFromObject(model);
  const center = fittedBox.getCenter(new THREE.Vector3());
  model.position.x -= center.x;
  model.position.z -= center.z;
  model.position.y += desiredGroundY - fittedBox.min.y;
  model.updateMatrixWorld(true);

  const effectiveProfile = materialSide
    ? { ...profile, material: { ...(profile.material || {}), side: materialSide } }
    : profile;

  model.traverse((node) => {
    if (!node.isMesh) return;
    node.frustumCulled = true;
    node.castShadow = false;
    node.receiveShadow = false;

    if (Array.isArray(node.material)) {
      node.material = node.material.map((material) => normalizeMaterial(material, renderer, effectiveProfile));
    } else if (node.material) {
      node.material = normalizeMaterial(node.material, renderer, effectiveProfile);
    }
  });

  return model;
}

export function createStaticCreatureInstanceBatch(source, {
  renderer,
  profile,
  placement = "benchmark",
  count,
  materialSide,
  transforms = []
}) {
  const instanceCount = Math.max(0, Number.parseInt(count, 10) || 0);
  if (!instanceCount) {
    return { supported: false, reason: "count_zero", object: null };
  }

  const prototype = fitCreature3D(cloneCreature3D(source), {
    renderer,
    profile,
    placement,
    materialSide
  });
  prototype.updateMatrixWorld(true);

  const meshes = [];
  prototype.traverse((node) => {
    if (node.isMesh) meshes.push(node);
  });

  if (meshes.length !== 1) {
    return {
      supported: false,
      reason: `requires_single_mesh_got_${meshes.length}`,
      object: null
    };
  }

  const mesh = meshes[0];
  if (mesh.isSkinnedMesh) {
    return { supported: false, reason: "skinned_mesh", object: null };
  }
  if (Array.isArray(mesh.material)) {
    return { supported: false, reason: "multi_material_mesh", object: null };
  }

  const batch = new THREE.InstancedMesh(mesh.geometry, mesh.material, instanceCount);
  batch.name = `Creature3D_Instanced_${profile.id}_${instanceCount}`;
  batch.frustumCulled = false;
  batch.castShadow = false;
  batch.receiveShadow = false;

  const rootMatrix = new THREE.Matrix4();
  const finalMatrix = new THREE.Matrix4();
  const position = new THREE.Vector3();
  const quaternion = new THREE.Quaternion();
  const scale = new THREE.Vector3(1, 1, 1);
  const euler = new THREE.Euler();

  for (let i = 0; i < instanceCount; i++) {
    const transform = transforms[i] || {};
    const p = transform.position || [0, 0, 0];
    const r = transform.rotation || [0, 0, 0];
    const s = transform.scale || [1, 1, 1];

    position.set(p[0] ?? 0, p[1] ?? 0, p[2] ?? 0);
    euler.set(r[0] ?? 0, r[1] ?? 0, r[2] ?? 0);
    quaternion.setFromEuler(euler);
    scale.set(s[0] ?? 1, s[1] ?? 1, s[2] ?? 1);
    rootMatrix.compose(position, quaternion, scale);

    finalMatrix.multiplyMatrices(rootMatrix, mesh.matrixWorld);
    batch.setMatrixAt(i, finalMatrix);
  }

  batch.instanceMatrix.needsUpdate = true;
  batch.computeBoundingSphere();

  const geometry = mesh.geometry;
  const triangles = geometry.index
    ? geometry.index.count / 3
    : (geometry.getAttribute("position")?.count || 0) / 3;

  return {
    supported: true,
    reason: null,
    object: batch,
    meshCount: 1,
    trianglesPerInstance: Math.round(triangles),
    expectedTriangles: Math.round(triangles * instanceCount)
  };
}

export function loadCreature3D(profile) {
  return new Promise((resolve, reject) => {
    new GLTFLoader().load(
      profile.url,
      (gltf) => {
        gltf.scene.name = `Creature3D_Source_${profile.id}`;
        resolve({
          source: gltf.scene,
          animations: gltf.animations || [],
          stats: inspectCreature3D(gltf.scene),
          profile
        });
      },
      undefined,
      reject
    );
  });
}
