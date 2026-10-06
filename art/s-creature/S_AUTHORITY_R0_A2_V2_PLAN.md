# S Authority R0-A2 v2 Plan

Status: **LOCKED FOR EXECUTION**

Source:

`output/S-authority-r0-v2.blend`

Do not use R0-A2 v1 as geometry input.

Authority:

`references/00_s_type_modeling_image_v1.png`

Prior review:

`S_AUTHORITY_R0_A2_V1_REVIEW.md` → **REVISE**

## One correction hypothesis

R0-A2 v1 failed because the mass field treated the already-unioned proximal leg roots like axial torso.

v2 keeps the same shoulder -> tuck -> pelvis intent but weights the deformation by source-space lateral distance.

Central axial torso receives most of the mass change. Large-|X| proximal limb-root vertices receive only a small residual deformation.

## Locked fields

A2 envelope remains:

- Y = -0.16 .. 1.14
- Z >= 0.66
- accepted R0-A1 region remains exact.

Lateral centralness:

- full strength at |X| <= 0.11;
- smooth fade from |X| 0.11 to 0.21;
- near-zero torso mass gain at the outer proximal limb root.

Targets:

- shoulder center Y 0.05: central lateral gain up to +30%;
- shoulder ventral depth up to 0.085 and dorsal lift up to 0.030, both root-faded;
- waist center Y 0.52: central lateral reduction up to 20%;
- waist ventral tuck up to 0.125, concentrated on axial abdomen;
- pelvis center Y 0.88: central lateral gain up to +28%;
- pelvis ventral depth up to 0.045 and dorsal/rump lift up to 0.050, root-faded.

## Expected visual change from v1

- FRONT / FRONT34: remove shoulder wing/cape silhouette;
- SIDE / REAR34: remove hanging bulb at proximal hindlimb root;
- preserve readable deep abdominal tuck;
- keep substantial shoulder and rump, but concentrate them into athletic axial mass.

## Hard fixed

- R0-A1 head/neck coordinates;
- entire accepted crest mesh;
- body topology and vertex count;
- vertices outside A2 envelope;
- feet/toes;
- tail beyond A2 envelope;
- review cameras.

## Hard limits

- max displacement <= 0.16;
- outer-root vertices with source |X| >= 0.18: max displacement <= 0.065;
- body remains manifold;
- central shoulder width ratio: 1.12 .. 1.34;
- central waist width ratio: 0.78 .. 0.94;
- central pelvis width ratio: 1.10 .. 1.32.

Render SIDE / FRONT / FRONT34 / REAR34 / BACK and stop.

R0-A3 remains blocked.
