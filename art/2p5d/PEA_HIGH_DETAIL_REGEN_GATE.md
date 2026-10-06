# P/E/A High-Detail Motion Regeneration Gate

Status: RASTER_PHASE_TRANSFER_REJECTED / ASSET_REGENERATION_REQUIRED

## Fixed conclusions

The current production P/E/A high-detail six-frame sheets are not good enough as final race animation.

The Motion First canonical P/E/A gaits were captured as 12 direct states per cycle and reviewed both as isolated sheets and in the 2.5D race runtime.

### Motion donor

KEEP:

- 12 direct gait states, no image interpolation
- P: phase separation reads clearly at race size
- E: phase separation reads, but final high-detail regeneration should increase extension contrast
- A: fore/hind exchange remains readable at race size
- runtime gate confirms all 12 frames cycle for P/E/A

REJECT as final art:

- low-poly Motion First donor appearance

Production is unchanged.

## Rejected high-detail transfer experiments

### v1 — deep piecewise phase transfer

Method:

- preserve high-detail source art
- split body / front lower region / rear lower region
- apply donor-derived affine motion to intermediate frames

Result: REJECT.

Observed:

- P: missing/cut limb pieces in intermediate frames
- E: chest/pelvis rectangular slicing and severe seam artifacts
- A: cleaner than P/E but still not safe as a shared method

### v2 — distal-limb-only transfer

Method:

- keep torso visually fixed
- move only distal front/rear limb regions
- no optical flow and no crossfade

Result: REJECT.

Observed:

- P: reduced body damage, but intermediate limb loss/dark seams remain
- E: duplicate limb lines and broken roots are obvious
- A: dark overlap/ghost-like limb remnants remain

## Rejected earlier methods

- bidirectional / optical-flow interpolation: smear, double heads/limbs, shape collapse
- temporal crossfade: visible double image / ghosting

## Required next route

Do not continue threshold tuning or raster interpolation.

Use the approved motion donor as the pose specification and regenerate high-detail P/E/A artwork for the 12 direct phases.

Requirements:

- preserve each existing P/E/A visual identity
- 4x3 / 12-frame sheet
- direct pose artwork, not frame interpolation
- transparent background
- consistent scale / camera / lighting
- semantic even frames:
  CONTACT / PUSH / LIFT / FLIGHT / REACH / LAND
- odd frames:
  actual intermediate gait states matching the mf12 donor
- S remains untouched

Promotion sequence:

1. regenerate one morph candidate
2. isolated 12-frame visual review
3. race-size runtime review
4. only then regenerate/promote the other morphs
5. production switch remains forbidden until all three pass
