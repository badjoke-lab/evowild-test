# S Authority R0-A4 v2 Plan

Status: **LOCKED FOR EXECUTION**

Source: `output/S-authority-r0-a3-v2.blend`

Do not use R0-A4 v1 geometry as input.

Authority: `references/00_s_type_modeling_image_v1.png`

Prior review: `S_AUTHORITY_R0_A4_V1_REVIEW.md` → **REVISE**

## One correction hypothesis

v1 failed because the split logic existed only as tiny distal fork tips.

v2 builds a visible integrated racing foot:

- a compact proximal base/cuff around the distal limb endpoint;
- two dominant blade-like prongs that own SIDE/FRONT/BACK silhouette;
- modest lateral divergence;
- stronger vertical/sagittal blade depth for a low hoof/wedge read;
- one short rear stabilizer, always subordinate.

## Target dimensions

Per foot:

- base/cuff length: 0.050 .. 0.065;
- dominant prong forward length: fore 0.165, hind 0.155;
- dominant tip separation: 0.058 .. 0.074;
- dominant prong half-width: root 0.014 .. 0.017, mid 0.016 .. 0.019;
- dominant blade half-depth: root 0.018 .. 0.022, mid 0.020 .. 0.024;
- tip minimum Z: 0.010 .. 0.016;
- rear spur length <= 0.050 and < 33% of dominant length.

## Hard fixed

- entire continuous body;
- accepted R0-A1/A2/A3 geometry;
- body topology / vertex count;
- crest;
- tail;
- cameras.

Only new foot appendage meshes are created after removing the original 12 generic toe meshes.

## Review

Render SIDE / FRONT / FRONT34 / REAR34 / BACK and stop.

R0-A5 remains blocked until R0-A4 is accepted.
