# EvoWild Run — S Morphology Authority Contract

Status: LOCKED

Primary visual authority:

`art/s-creature/references/00_s_type_modeling_image_v1.png`

Source identity:

- user-confirmed image: **EvoWild Run — S TYPE / SPRINT MORPH**
- original dimensions: **1448 × 1086**
- original PNG size: **1,982,782 bytes**
- original SHA-256: `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`

## Authority order

1. `00_s_type_modeling_image_v1.png` — final global S morphology authority.
2. `01_s_body_primary.png`, `02_s_silhouette.png`, and the remaining part sheets — diagnostic/supporting references only.
3. Written proportion ranges — drift guards only.
4. Existing meshes/renders — implementation candidates, never authority.

If any lower-level reference conflicts with the primary image, the primary image wins.

## Review rule

No S morphology candidate can be accepted from one view.

Every morphology gate must compare at least:

- SIDE
- FRONT
- FRONT34
- REAR34
- BACK

against the primary authority image.

A gate must be rejected if a hard-fail trait appears even when local topology/validation passes.

## Separation from motion tests

The Tripo/Hunyuan carrier meshes are not morphology authorities.

A successful rig or animation test proves only technical motion feasibility. Production S animation must ultimately be retargeted/retested on a morphology-approved S asset.
