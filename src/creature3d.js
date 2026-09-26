import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { clone as cloneSkeletonSafe } from "three/addons/utils/SkeletonUtils.js";

export const CREATURE_3D_PROFILES = {
  sHunyuan2mvRaw: {
    id: "s-hunyuan2mv-raw",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-raw.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.78,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "multiview_shape_candidate_unapproved",
    notes: [
      "Generated from SIDE/FRONT/BACK/3Q references with Hunyuan3D-2mv.",
      "Raw shape-only output: very high polygon count, disconnected/degenerate geometry, no production material.",
      "Use only to judge multiview silhouette fidelity before cleanup or retopology."
    ]
  },
  sHunyuan2mvClean: {
    id: "s-hunyuan2mv-clean",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-clean.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.78,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "multiview_clean_candidate",
    notes: [
      "Hunyuan multiview shape with degenerate triangles removed and only the largest connected component retained.",
      "Shape-only validation asset; source for subsequent simplification tests."
    ]
  },
  sHunyuan2mvLod1: {
    id: "s-hunyuan2mv-lod1",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod1.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.78,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "multiview_simplify_candidate",
    notes: [
      "Hunyuan multiview raw shape simplified to 20% target ratio in CI.",
      "Shape-only validation asset; not production-ready."
    ]
  },
  sHunyuan2mvLod2: {
    id: "s-hunyuan2mv-lod2",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod2.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.82,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "multiview_simplify_candidate",
    notes: [
      "Hunyuan multiview raw shape simplified to 8% target ratio in CI.",
      "Shape-only validation asset; not production-ready."
    ]
  },
  sHunyuan2mvRigged: {
    id: "s-hunyuan2mv-rigged-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-rigged.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.22,
      minRoughness: 0.52,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "heuristic_rig_proof_not_final_art",
    notes: [
      "LOD2 Hunyuan mesh with a Blender-generated 13-bone armature and 25-frame run cycle.",
      "Used only to prove real skeletal deformation in-browser before evaluating learned auto-rigging.",
      "Heuristic weights and motion are not approved final animation."
    ]
  },
  sHunyuan2mvRiggedV2: {
    id: "s-hunyuan2mv-rigged-v2-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-rigged-v2.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.22,
      minRoughness: 0.52,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "heuristic_gait_v2_proof_not_final_art",
    notes: [
      "LOD2 Hunyuan mesh with gait-v2 asymmetric four-leg phasing, recovery flex, torso compression and counter-motion.",
      "Animation-quality proof only; not approved final animation."
    ]
  },
  sHunyuan2mvLod4Rigged: {
    id: "s-hunyuan2mv-lod4-rigged-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod4-rigged.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.12,
      minRoughness: 0.64,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "heuristic_lod4_rig_proof_not_final_art",
    notes: [
      "LOD4 Hunyuan mesh with a Blender-generated 13-bone armature and 25-frame run cycle.",
      "Used to prove many simultaneously animated racers in-browser; not approved final animation."
    ]
  },
  sHunyuan2mvRiggedV21: {
    id: "s-hunyuan2mv-rigged-v21-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-rigged-v21.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.22,
      minRoughness: 0.52,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "heuristic_gait_v2_1_proof_not_final_art",
    notes: [
      "LOD2 gait-v2.1: retains asymmetric phase design while reducing leg, torso, neck and bob amplitudes.",
      "Animation-quality proof only; not approved final animation."
    ]
  },
  sHunyuan2mvLod4RiggedV2: {
    id: "s-hunyuan2mv-lod4-rigged-v2-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod4-rigged-v2.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.12,
      minRoughness: 0.64,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "heuristic_gait_v2_proof_not_final_art",
    notes: [
      "LOD4 Hunyuan mesh using the same gait-v2 cycle for 18-racer race-view validation.",
      "Animation-quality proof only; not approved final animation."
    ]
  },
  sHunyuan2mvLod4RiggedV21: {
    id: "s-hunyuan2mv-lod4-rigged-v21-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod4-rigged-v21.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.12,
      minRoughness: 0.64,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "heuristic_gait_v2_1_proof_not_final_art",
    notes: [
      "LOD4 gait-v2.1 for 18-racer race-view validation.",
      "Animation-quality proof only; not approved final animation."
    ]
  },
  sHunyuan2mvRiggedV3: {
    id: "s-hunyuan2mv-rigged-v3-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-rigged-v3.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.22,
      minRoughness: 0.52,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "multi_joint_rig_v3_proof_not_final_art",
    notes: [
      "LOD2 Hunyuan mesh with 19-bone v3 rig: pelvis/chest split and independent foot bones.",
      "Improved side/front-hind weighting constraints; animation-quality proof only."
    ]
  },
  sHunyuan2mvLod4RiggedV3: {
    id: "s-hunyuan2mv-lod4-rigged-v3-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod4-rigged-v3.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.12,
      minRoughness: 0.64,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "multi_joint_rig_v3_proof_not_final_art",
    notes: [
      "LOD4 19-bone v3 race rig for 18-racer browser validation.",
      "Independent feet approximate a flatter contact phase without full IK."
    ]
  },
  sHunyuan2mvRiggedV31: {
    id: "s-hunyuan2mv-rigged-v31-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-rigged-v31.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.22,
      minRoughness: 0.52,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "contact_phased_rig_v3_1_proof_not_final_art",
    notes: [
      "LOD2 19-bone v3.1 with explicit stance, push-off, recovery and landing timing.",
      "Contact-phase proof only; not approved final animation."
    ]
  },
  sHunyuan2mvLod4RiggedV31: {
    id: "s-hunyuan2mv-lod4-rigged-v31-proof",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod4-rigged-v31.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.12,
      minRoughness: 0.64,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "contact_phased_rig_v3_1_proof_not_final_art",
    notes: [
      "LOD4 19-bone v3.1 contact-phased race rig.",
      "Contact-phase proof only; not approved final animation."
    ]
  },
  sHunyuan2mvStyled: {
    id: "s-hunyuan2mv-styled-prototype",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod2.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.22,
      minRoughness: 0.52,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "prototype_material_only",
    notes: [
      "Uses the semantic Hunyuan LOD2 geometry with a procedural vertex-color material.",
      "Silver-white / cool-blue / cyan palette is only for in-engine readability testing.",
      "This is not an AI-generated source-fidelity texture and is not final art."
    ]
  },
  sHunyuan2mvStyledLod3: {
    id: "s-hunyuan2mv-styled-lod3",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod3.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.18,
      minRoughness: 0.58,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "prototype_material_lod",
    notes: ["Styled semantic Hunyuan mid-distance race LOD; prototype material only."]
  },
  sHunyuan2mvStyledLod4: {
    id: "s-hunyuan2mv-styled-lod4",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod4.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.12,
      minRoughness: 0.64,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1,
      prototypeVertexPalette: true
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "prototype_material_lod",
    notes: ["Styled semantic Hunyuan far-distance race LOD; prototype material only."]
  },
  sHunyuan2mvLod3: {
    id: "s-hunyuan2mv-lod3",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod3.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.84,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "multiview_simplify_candidate",
    notes: [
      "Hunyuan clean multiview shape simplified to 4% target ratio.",
      "Intended as mid/far race LOD candidate."
    ]
  },
  sHunyuan2mvLod4: {
    id: "s-hunyuan2mv-lod4",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-hunyuan2mv-lod4.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.86,
      side: "double",
      preserveBaseColorMap: false,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "multiview_simplify_candidate",
    notes: [
      "Hunyuan clean multiview shape simplified to 2% target ratio.",
      "Intended only as far-distance race LOD candidate."
    ]
  },
  sTripoSr3q: {
    id: "s-triposr-3q-crop30",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-triposr-3q.glb`,
    rotation: [-Math.PI / 2, 0, 0],
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
      "Generated with TripoSR on GitHub Actions CPU from the cleaned 3/4 crop30 reference.",
      "Geometry is nearly one connected component and uses vertex colors.",
      "Not approved as final EvoWild S-Type; retained for direct engine comparison."
    ]
  },
  sTripoSrSide: {
    id: "s-triposr-side-authority",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-triposr-side.glb`,
    rotation: [-Math.PI / 2, 0, 0],
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
  sSf3dCorrectedLod1: {
    id: "s-sf3d-corrected-lod1",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-corrected-lod1.glb`,
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
    status: "lod_candidate",
    notes: [
      "Derived from corrected SF3D candidate with glTF Transform simplification at ratio 0.5.",
      "Base color is preserved; normal/roughness/metalness maps are disabled at this distance after browser stress validation."
    ]
  },
  sSf3dCorrectedLod2: {
    id: "s-sf3d-corrected-lod2",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-corrected-lod2.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.68,
      side: "front",
      preserveBaseColorMap: true,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "lod_candidate",
    notes: [
      "Derived from corrected SF3D candidate with glTF Transform simplification at ratio 0.25.",
      "Texture/material preservation is validated by browser load tests before use."
    ]
  },
  sSf3dCorrectedLod3: {
    id: "s-sf3d-corrected-lod3",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-corrected-lod3.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.72,
      side: "front",
      preserveBaseColorMap: true,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "lod_candidate",
    notes: [
      "Derived from corrected SF3D candidate with glTF Transform simplification at ratio 0.125.",
      "Intended only for far-distance race rendering; keeps base color but disables normal/roughness/metalness maps."
    ]
  },
  sSf3dCorrectedLod2Lite: {
    id: "s-sf3d-corrected-lod2-lite",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-corrected-lod2-lite.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.68,
      side: "front",
      preserveBaseColorMap: true,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "lod_candidate",
    notes: [
      "LOD2 with the normal texture removed from the GLB and unused texture/image data pruned.",
      "Intended for mid/far race rendering after visual and performance validation."
    ]
  },
  sSf3dCorrectedLod3Lite: {
    id: "s-sf3d-corrected-lod3-lite",
    morph: "S",
    url: `${import.meta.env.BASE_URL}models/evowild-s-sf3d-corrected-lod3-lite.glb`,
    rotation: [0, 0, 0],
    material: {
      metalness: 0.0,
      minRoughness: 0.72,
      side: "front",
      preserveBaseColorMap: true,
      preserveNormalMap: false,
      preserveRoughnessMap: false,
      preserveMetalnessMap: false,
      maxAnisotropy: 1
    },
    placements: {
      lab: { targetHeight: 3.2, groundY: 0.03 },
      race: { targetHeight: 1.7, groundY: -0.92 },
      benchmark: { targetHeight: 1.28, groundY: 0.03 }
    },
    status: "lod_candidate",
    notes: [
      "LOD3 with the normal texture removed from the GLB and unused texture/image data pruned.",
      "Intended only for far-distance race rendering."
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

function applyPrototypeVertexPalette(node) {
  if (!node.geometry?.getAttribute("position")) return;

  const geometry = node.geometry.clone();
  if (!geometry.getAttribute("normal")) {
    geometry.computeVertexNormals();
  }
  geometry.computeBoundingBox();
  const box = geometry.boundingBox;
  const size = new THREE.Vector3();
  box.getSize(size);

  const position = geometry.getAttribute("position");
  const colors = new Float32Array(position.count * 3);

  const silver = new THREE.Color(0xdce7eb);
  const coolBlue = new THREE.Color(0x5d87a8);
  const cyan = new THREE.Color(0x5fe7ee);
  const color = new THREE.Color();

  const dx = Math.max(1e-6, size.x);
  const dy = Math.max(1e-6, size.y);
  const dz = Math.max(1e-6, size.z);

  for (let i = 0; i < position.count; i++) {
    const nx = (position.getX(i) - box.min.x) / dx;
    const ny = (position.getY(i) - box.min.y) / dy;
    const nz = (position.getZ(i) - box.min.z) / dz;

    color.copy(silver);

    // Cool blue underside and flank treatment.
    const sideDistance = Math.abs(nx - 0.5) * 2;
    if (ny < 0.33 || (sideDistance > 0.58 && ny < 0.68)) {
      color.lerp(coolBlue, 0.58);
    }

    // Cyan only on ridge/extremity zones so it reads as a device/accent cue,
    // not as a fake all-over texture.
    const dorsal = ny > 0.82;
    const longitudinalTip = nz < 0.08 || nz > 0.92;
    if (dorsal || (longitudinalTip && ny > 0.55)) {
      color.lerp(cyan, 0.72);
    }

    colors[i * 3] = color.r;
    colors[i * 3 + 1] = color.g;
    colors[i * 3 + 2] = color.b;
  }

  geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  node.geometry = geometry;
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

  if (normalized.map) {
    if (materialProfile.preserveBaseColorMap === false) {
      normalized.map = null;
    } else {
      normalized.map.colorSpace = THREE.SRGBColorSpace;
      const maxSupported = renderer?.capabilities?.getMaxAnisotropy?.() ?? 1;
      const requested = materialProfile.maxAnisotropy ?? 1;
      normalized.map.anisotropy = Math.min(requested, maxSupported);
      normalized.map.needsUpdate = true;
    }
  }

  if (materialProfile.preserveNormalMap === false) {
    normalized.normalMap = null;
  }
  if (materialProfile.preserveRoughnessMap === false) {
    normalized.roughnessMap = null;
  }
  if (materialProfile.preserveMetalnessMap === false) {
    normalized.metalnessMap = null;
  }

  if (materialProfile.prototypeVertexPalette) {
    normalized.vertexColors = true;
    if (normalized.color) normalized.color.set(0xffffff);
    if ("emissive" in normalized) {
      normalized.emissive.set(0x071b20);
      normalized.emissiveIntensity = 0.18;
    }
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

    if (effectiveProfile.material?.prototypeVertexPalette) {
      applyPrototypeVertexPalette(node);
    }

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
    prototypeMatrix: mesh.matrixWorld.clone(),
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
