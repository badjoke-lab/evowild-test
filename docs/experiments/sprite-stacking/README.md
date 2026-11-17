# EvoWild Run — isolated sprite-stacking experiment (2026-11-18)

Branch: `exp/2p5d-sprite-stacking-20261118`. No production lane, original model, design reference, animation or main integration changes. Free local tools only.

## Source selection and identity limits

Inspected origin/main cde1bd7, D3-C authoring ec969514, full-body 8c7ad6a, modeling 48b39d8. Chosen existing D3-C v2, rather than the original broken foot weights or procedural S: it has independent scapula articulation, existing sole-contact IK and reproducible 23-joint four-leg motion. D3-C v3 is also available but still has a REVISE visual verdict; v2 supplies the stable documented comparison baseline requested here. Neither is production-approved artwork.

Copied unchanged `public/models/evowild-s/review/d3c-scapula-author-v2.glb` from ec969514 to the isolated `public/exp-sprite-stacking/assets/source.glb` (SHA256 6edb45e7aeb3179104d5b406d09eaa1f34da6baf09ddc9a6a0535d7e96f3f1c0). Copied its six IK/body/sole modules byte-for-byte, plus the existing 1600m oval geometry. The thin pose adapter reproduces `toe=roll-v3&body=push-v5&shoulder=authored-v2`. Do not use the standalone authored clip to claim measured contact: it requires the IK adapter.

The user-specified shape reference is copied from modeling commit 48b39d8, `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA256 93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6. The canonical shared sheet/index and 2.5D lock were also read. No creature design was generated or changed.

**Source limitation:** D3-C v2 and the main canonical S GLBs have no material, UV, texture image, or vertex colors. They are neutral gray/white review meshes. This experiment preserves that source appearance and transparency outside cross sections; it cannot establish preservation of the blue/white painted reference texture that is absent from those GLBs. No replacement texture is invented. Inherited body/crest silhouette and gait limitations are not new visual approval.

## Pipeline

1. `node scripts/stacking-poses.mjs`: evaluate existing native/body/authored/IK runtime, integrate one cycle into 48 actual skinned poses, keep all four feet and body/shoulder/head/tail motion; save positions/normals/sole data under work/.
2. `python scripts/stacking-slices.py --workers 4`: intersect triangle edges with horizontal planes at the center of each of 16/32/64/128 bands; parity-fill the solid, bake declared creature-local Lambert shading and coverage alpha; trim and pack PNG atlases. 12/24-frame sets are exact nested samples of the same 48-pose cycle.
3. Browser runtime and evidence: in progress at initial source checkpoint.

No runtime polygons are needed for Canvas stacking. Source GLB is reserved for offline baking and the explicitly labeled comparison renderer. RGBA-only slices cannot relight with a world-fixed light; local baked light is declared for matched comparisons. Horizontal planes also cannot reproduce roll/pitch or fully correct silhouette at grazing elevation without additional sampling.

`vendor/` contains locally installed Three.js 0.181.x (MIT; included license). The reference sprite-stacking repository's technique was read; its code was not copied. UI8 /fly could not be retrieved from this environment and is not claimed as visually inspected.
