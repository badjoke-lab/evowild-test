# S authority visual hull v1–v2 — real-model review and stop decision

**Actual morphology verdict: REJECT for both v1 and v2.**

## Provenance and reproducibility

The exact primary source is `art/s-creature/references/00_s_type_modeling_image_v1.png` (SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`). All four raw panels and extracted masks are in `art/s-creature/experiments/authority-visualhull/`; the original verified PNG is unaltered.

- Side/front segmentation: workflow `37940396172` — SUCCESS. Masks are review aids, NOT approved cutout sprites.
- 2-view hull: workflow `37940866992` — SUCCESS. Initial GLB import axis was incorrect; upright correction workflow `37941311500` — SUCCESS.
- 3-view hull: workflow `37941847940` — SUCCESS. Real mesh generated from SIDE/FRONT/FRONT34; BACK held out.
- Production `main` and all current game/race/creature branches remain untouched.

## 2-view actual image decision

`hull-v1/upright-v1/review/S_upright_3D_vs_authority_4views.jpg`:

- SIDE: broad silhouette resembles the source from a distance, but poor cross-section and extreme stair-stepping are present.
- FRONT: approximate total outline but blocky and flattened facial/limb masses.
- FRONT34/BACK: **severe geometry ambiguity**, replicated limb-like extrusions and unnatural stepped surfaces. Reject.
- The training side/front voxel-mask IoUs near 1.0 are **not evidence of accurate 3D**. They are tautological with silhouette intersection.
- Raw generated mesh: 312,134 triangles, one watertight component; **technical validity did not translate into visual validity**.

## 3-view actual image decision

`hull-v2-three-view/upright/review/S_threeview_reference_versus_mesh.jpg`:

- Adding the approved 3/4 view reduced some of the obviously multiplied limb contours, but the chest, shoulders and leg geometry are still severely rough and structurally nonsensical.
- SIDE/FRONT silhouette training IoU 0.860 / 0.912; geometric agreement decreased to satisfy the 3/4 constraint.
- BACK (held out): poor anatomical form compared to approved posterior anatomy. The artist-designed tail plates and split-foot forms do not survive volumetric carving.
- The carcass resembles stacked extrusions. It cannot be rigged to S-quality animation without recreating its surface topology.
- Actual mesh: 227,152 triangles, one watertight component, positive signed volume. This only confirms mesh closure.
- QEM reduction was intentionally rejected when it broke topology.
- **REJECT** full-body morphology and deformation readiness.

## Method stop rule

**Do not run v3, v4, etc. with more silhouette voxels, higher grid resolution, or small blur changes.** The failure mode is fundamental: these concept-sheet views do not constrain internal anatomy or the posterior limbs sufficiently to recover a good-quality 3D character via visual hull. Additional slices and smoothing cannot substitute for anatomical sculpting, UV/normal work or careful rig topology.

## What remains worth reusing

- Locked reference / verified hashes, direction-specific masks, panel bounds and five-view review camera definitions.
- The numeric shape silhouette can be used as a **non-rendered target guide** for a human-sculpted production mesh (silhouette tolerances), not as the gameplay creature itself.
- Existing motion-first runtime can be adapted only **after** a complete S design and rig is accepted.

## Next production dependency (unvalidated)

A real multiview character sculpt/retopology workflow with direct shape edits by a 3D artist or reliable specialist character-modeling system, not another scripted primitive mesh, single-view image-to-3D guess or voxel silhouette-extrusion. Demand before proceeding:

1. side/front/front34/rear34/back images of the *same* full-body mesh vs the locked design
2. no sagittal horn; skull-integrated paired swept lamina
3. expressive shoulder/hip anatomy, separated split feet and layered tail, not tubes or attached slabs
4. connected, skinnable deforming surface, then real walk/run video in the Motion First engine.

Completed/approved game creature count stays **0**.
