# S-type clean-room A0 — first actual entirely-new editable 3D silhouette, NOT ACCEPTED

Date: 2026-10-11 UTC
Branch: `exp/s-canonical-fullbody-rebuild-20261011`
Source: `art/s-creature/references/00_s_type_modeling_image_v1.png`, exactly **1448×1086, 1,982,782 bytes**, SHA256 **`93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`**, user approved and the **sole** highest-authority modeling image. The real source PNG was checked by GitHub Actions and is packed into the editable .blend as a Blender image datablock.

## Why complete restart rather than another donor revision

Already observed:
- Previous source-QEM M/N/BODY-V2 mesh fixes improved connectivity and geometry metrics but **failed the visual S type**.
- Real authority-TRELLIS T1 and R5 correct some crest shape but the body remains wrong; donor has **6,155 disconnected components**, no playable mesh, no full S resemblance.
- Old S-blockout R0 stages failed the canonical silhouette despite dozens of small modifications.
- Incremental fixes of the inherited wrong animal are **not evidence of usable S modeling progress**. These are archived technical tests, not S geometry baselines.

## What actually changed in A0

Actual new Blender scene initialized with `bpy.ops.wm.read_factory_settings(use_empty=True)`. **Never loads donor blend or donor GLB.** Scripts only create new original meshes following the exact image's structure and anatomy text diagnostics (which remain subordinate to the PNG). The scene includes visible 3D representations for these independently editable shapes:

- continuous lightweight thorax / **dramatically tucked waist** / higher haunches;
- deep flared shoulder into tapering neck and small wedge racing skull;
- **two distinct large swept cranial lamina blades**, plus paired temporal secondaries; NO single midline horn;
- white shoulder/chest layered side armor; blue haunch and segmented hip plates;
- **four separate fore/hind kinematic chains** with different elbows/knees/hocks and actual physical split feet;
- long swept tail core and **six** separately sculptable 3D feather/armor laminae.

Actual saved A0 output:
- `a0-full-silhouette/S-fullbody-canonical-cleanroom-A0-UNAPPROVED.blend` — **194,236 bytes** Blender native real 3D, exact original art packed.
- `a0-full-silhouette/S-fullbody-canonical-cleanroom-A0-UNAPPROVED.glb` — **289,660 bytes** editable-exported actual glTF mesh.
- **41 true mesh objects**, 8,544 physical 3D vertices, 8,210 polygon faces; no imported QEM geometry.
- Five real Blender renders in `a0-full-silhouette/review/S_CLEANROOM_A0_ACTUAL_3D_{SIDE,FRONT,FRONT34,REAR34,BACK}.png`.
- `a0-full-silhouette/review/ACTUAL_CANONICAL_CLEANROOM_A0_FIVE_VIEW.jpg` — direct five-view screenshot contact sheet, NOT a generated concept image.
- `a0-full-silhouette/review/ORIGINAL_S_REFERENCE_VS_NEW_A0_REAL_3D.jpg` — screenshot of **same actual original reference crop** next to new real Blender model, not a replacement reference.
- `a0-full-silhouette/A0_REAL_FULLBODY_CLEANROOM_QA.json` — machine-checkable properties, all non-approval flags explicit.
- Actions run [38148342639](https://github.com/badjoke-lab/evowild-test/actions/runs/38148342639) fully SUCCESS. Initial packaging run [38148263539](https://github.com/badjoke-lab/evowild-test/actions/runs/38148263539) failed on a JSON report field spelling only; Blender .blend/GLB/5 views were already generated; corrected and reran.

## Explicit STOP / no fake approval

**This is a rough A0 silhouette candidate, not an accepted S type creature or verified improvement in modeling quality.** In particular:

- Visual source likeness has **not been approved** by reviewing the actual five renders; every revision must be compared to the original PNG.
- Primitive anatomical shapes and separated armor plates are **staging meshes**: not an integrated manifold, production game topology or physically reliable rig.
- No rig, running cycle, camera test in the game, material fidelity gate, GPU benchmark, or production shader.
- No claimed model quality superiority from Actions success or increased mesh count.
- S full creature approved: **0**; production `main` unchanged.

## Next pass MUST be visually decisive

Open the actual A0 contact sheet and original-reference side-by-side first. **If the creature still resembles the incorrect deer/gazelle or its global proportions are wrong, reject A0 outright and do not proceed to detail, smoothing, rig or another local topology search.**

If it has an acceptably distinct global S-type silhouette, the next task is actual artistic multi-view sculpting of head/crest roots, shoulder armor integration, haunch/waist line, split racing foot detail and layered long tail, in that order dictated by mismatches visible in the exact five orthographic comparisons. No acceptance without approved five-view match. The 3D mesh object count is not a success metric.
