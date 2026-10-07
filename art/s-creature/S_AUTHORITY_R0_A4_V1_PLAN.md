# S Authority R0-A4 v1 Plan

Status: **LOCKED FOR EXECUTION**

Source:

`output/S-authority-r0-a3-v2.blend`

Accepted prior gates:

- R0-A1 head / crest / neck
- R0-A2 body mass
- R0-A3 limb segment rhythm

Highest authority:

`references/00_s_type_modeling_image_v1.png`

## Problem

The old Gate-A foot morphology is explicitly invalid as final S morphology.

Current foot read:

- three small generic toe rods per foot;
- paw / generic digit language;
- no strong split racing-contact silhouette;
- weak SIDE wedge;
- weak FRONT/BACK bilateral split.

Authority foot read:

- compact specialized racing foot;
- two dominant prong / hoof-like contact structures;
- clear central split from FRONT/BACK;
- long low wedge from SIDE;
- light angular construction rather than a paw.

## R0-A4 v1 hypothesis

Do not distort the old three-toe meshes.

Delete the 12 old generic toe objects and replace each foot with a new purpose-built assembly:

1. **two dominant split prongs**
   - paired left/right around the distal limb center;
   - diverge slightly laterally;
   - extend forward/down into a low aerodynamic contact wedge;
   - blade-like cross-section, not cylindrical toes;

2. **small rear stabilizer spur**
   - subordinate to the split pair;
   - short and high;
   - must not turn the foot back into a three-equal-toe paw.

The main silhouette must be owned by the two split prongs.

## Coordinate lock

Front = negative Y.

Existing distal contact centers are preserved as attachment landmarks:

- fore L/R: approximately |X| 0.150, Y -0.268, Z 0.060;
- hind L/R: approximately |X| 0.150, Y 0.970, Z 0.060.

## Hard fixed

- entire continuous body mesh and all body vertices;
- R0-A1 / R0-A2 / R0-A3 accepted geometry;
- body topology / vertex count;
- accepted crest;
- tail;
- review cameras.

Only old toe meshes may be removed and new foot appendage meshes added.

## Geometry target

Per foot:

- 2 dominant prongs;
- 1 subordinate rear spur;
- dominant prong forward length 0.105 .. 0.125;
- dominant pair tip separation 0.040 .. 0.060;
- dominant prong minimum Z approximately 0.010 .. 0.018;
- rear spur forward/back envelope must remain less than 45% of dominant prong length.

The dominant pair must remain visibly split in FRONT and BACK.

## Review

Render exactly:

- SIDE
- FRONT
- FRONT34
- REAR34
- BACK

Then stop with `REVIEW_PENDING / STOPPED`.

R0-A5 long layered tail remains blocked until R0-A4 is accepted.
