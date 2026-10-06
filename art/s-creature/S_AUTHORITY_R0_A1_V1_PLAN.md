# S Authority R0-A1 v1 Plan

Status: LOCKED FOR EXECUTION  
Lane: `exp/s-creature-vibe-modeling`

## Authority

Highest-priority image:

`art/s-creature/references/00_s_type_modeling_image_v1.png`

- dimensions: 1448 x 1086
- bytes: 1,982,782
- SHA-256: `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`

This image overrides old A1/A4/A5 morphology acceptances.

## Source / output

Technical donor only:

`output/S-vibe-b2a-v5.blend`

Output:

`output/S-authority-r0-v1.blend`

The donor is globally rejected as S morphology. It is used only to preserve all non-R0-A1 geometry unchanged for this gate.

## R0-A1 editable scope

Only:

1. head silhouette;
2. paired dominant crest blades;
3. compact secondary crest blades at the skull base;
4. neck line through the neck root transition.

Body vertices are editable only in the forward head/neck spatial support. The old separate crest object is discarded and rebuilt.

## Locked hypothesis

The authority mismatch is not a local smoothing defect. The old S reads too deer/gazelle-like because the head-neck-crest unit is too upright, too tubular, and dominated by thin comb-like crest strips.

R0-A1 v1 will therefore:

- extend the head forward into a longer wedge;
- lower the head line into a faster racing posture;
- deepen and broaden the neck through the middle/root without changing the torso;
- replace the old four-strip crest with two dominant broad blades;
- make the two dominant blades sweep strongly rearward/upward;
- keep the pair visibly separated from FRONT and BACK;
- add only compact secondary blades near the skull base so the result does not return to a thin multi-prong comb.

## Hard-fixed geometry

For this gate, keep exact:

- all body vertices outside the declared head/neck support;
- torso / shoulder / waist / pelvis;
- forelimbs and hindlimbs outside the head-neck support;
- all toe objects;
- feet;
- tail;
- body topology and vertex count;
- all review cameras;
- all non-crest mesh objects except body vertices inside the R0-A1 support.

No R0-A2 body remassing, R0-A3 limb changes, R0-A4 foot changes, or R0-A5 tail changes are allowed.

## Review requirement

Render exactly:

- SIDE
- FRONT
- FRONT34
- REAR34
- BACK

Then stop with `REVIEW_PENDING / STOPPED`.

No R0-A2 work is permitted until the five actual images are compared against the authority PNG and R0-A1 receives KEEP/acceptance.
