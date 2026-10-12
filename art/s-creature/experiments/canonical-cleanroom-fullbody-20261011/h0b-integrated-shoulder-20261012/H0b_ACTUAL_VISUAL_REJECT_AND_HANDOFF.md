# EvoWild Run S — H0b genuine integrated shoulder trial (2026-10-12)

**Overall: REJECT.** H0b is a completed Blender *experiment*, not an accepted S type, not a new modeling base, not game ready. H1 remains blocked.

## Fixed original authoritative reference and untouched modeling source

- Sole user-approved S design image: `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6` / 1448×1086 / 1,982,782 bytes.
- Edit started from **original unmodified Hunyuan 3-view Blender**, not the rejected H0 output: `art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/hunyuan2mv-original-source-20261012/HUNYUAN2MV_S_THREEVIEW_REAL_ASSET_UNAPPROVED.blend`; SHA256 `6651109695536db026d9b52fe10c3fa829cab82915cda1955a5f56eedcec4345`.
- Original geometry 38,802 vertices / 77,684 triangles. No QEM, R5, A0, Visual Hull or old H0 geometry imported.
- Branch: `exp/s-h0b-integrated-shoulder-20261012`. `main` and original source image and model untouched.

## What was ACTUALLY modeled and run

- A new **native original-body-mesh shape key** `H0b_INTEGRATED_SHOULDER_AND_CHEST_ONLY` edits the shoulder and chest polygon surface, with three Y/Z patch domains driving subtly planar ridges, negative crease lines and anterior chest taper. There are **ZERO newly added external armor mesh objects**; unlike failed H0's 17 separate pads, 3,873 existing original mesh faces receive test plate materials.
- Direct local 3D vertex edits affect 4,995 actual body vertices, max real evaluated vertex shift **0.0191755 units**. Hip, distal limbs, head, crest and tail are protected from edits.
- Native mesh total remains 38,802 vertices / 77,684 faces. Original Hunyuan itself contains 12 degenerate faces; candidate also contains 12. **0 newly degenerate faces, 0 flipped normals, 0 under-half/double-area healthy original faces, 0 new shoulder-region BVH overlaps.** Local strain projection corrected 29 rounds without replacing the mesh. **Limited technical geometry PASS.** These facts are recorded under `H0b_REAL_NATIVE_SURFACE_QA.json`.
- The actual output `S_H0b_original_Hunyuan_integrated_shoulder_TRIAL.blend` retains the original base in its Basis shape key and the experimental shoulder/chest changes separately.
- GitHub Actions finished actual Blender and saved all 5 matching camera images for unchanged BASE and H0b, plus SAME-COLOR (CLAY) comparisons.
- Included the **actual previously REJECTED H0** view PNGs for proper side-by-side comparison, not as geometry or authority inputs. H0 renders retain the original camera/scale/resolution.
- Real comparison: `review/H0b_CANONICAL_VS_H0_VS_BASE_5VIEW.jpg`. Actual purely geometric comparison: `review/H0b_BASE_VS_SINGLE_COLOR_5VIEW.jpg`.
- H0b source script: `art/s-creature/blender/s_h0b_integrated_shoulder_sculpt.py` and comparison script `s_h0b_render_comparison_sheet.py`. Execution workflow `.github/workflows/s-h0b-integrated-original-skin-20261012.yml`.

## Actual five-angle image assessment

| Angle | What changed | Visual decision |
| --- | --- | --- |
| SIDE | Small contiguous white/ivory patch and ridge on front shoulder only; 3D shape changes are small | **FAIL**: visual reads as irregular speckled/scabbed region, not the canonical layered forward-swept shoulder plates; original slender torso/shoulder mismatch essentially unchanged |
| FRONT | Narrow, roughly mirrored pale shoulder patches replace H0's large round pad silhouette | **FAIL**: patch looks noisy, shoulders remain smooth rounded biology instead of angular plate/chest transitional shape |
| FRONT34 | Shoulder still intact with body, but pale patch boundary remains ragged; no long diagonal overlapping plate design | **FAIL**: no convincing resemblance gain over original Hunyuan in canonical armoring geometry |
| REAR34 | No changes beyond the indirect shoulder visibility; waist, hip and legs intentionally unchanged | **NOT IMPROVED**: source still lacks original back/side armor arrangements |
| BACK | Unchanged intentional original geometry | **NO IMPROVEMENT**: no claim of new full S quality |

**Same-color CLAY images support rejection**: a choppy rough shoulder surface appears, not strongly sculpted continuous armor; color segmentation alone exaggerates the apparent improvement. Even though an external pad was not added, it does not automatically yield good armor.

### Decision and next realistic corrective method

- **H0b = REJECT for visual quality, KEEP only as technical method experiment** showing genuine unchanged native Hunyuan skin editing and face/material mapping feasibility.
- **H0 = REJECT. Original Hunyuan 3-view remains the best provisional S-shape candidate, NOT finished S.** No unverified improvement claims.
- Do not start H1, rig or race animation; no `main` changes.
- Do **NOT** launch H0c by moving Gaussian or patch distance-field parameters. Programmatic mask painting + micro displacement inherently generated noisy, arbitrary islands, not designed overlapping S armor. A further scripted patch swap would repeat H0/H0b's central failure.
- True follow-up is an **artist-controlled actual Blender edit of the original Hunyuan skin**, with the *real four-view user source* visible as image planes and explicit shoulder-to-thorax plate silhouettes laid out in 3D, *not arbitrary ellipse or auto projected masks*. First manually block a real broad tapered continuous directional shoulder/forechest transition **within the original skin**, prove a meaningful three-view geometric improvement with clay renders, then resolve plates/edge bevels. The next result is to be judged by actual source+BASE+candidate five views; texture alone is not a PASS.
- Do not quietly replace the S modeling reference or claim the original Hunyuan is production approved.

**Approved S creatures: 0. The experiment is stopped after genuine visual rejection.**
