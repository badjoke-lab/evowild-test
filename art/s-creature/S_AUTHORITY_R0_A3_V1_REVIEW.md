# S Authority R0-A3 v1 Review

Decision: **REVISE**

Authority:

`references/00_s_type_modeling_image_v1.png`

Candidate:

`output/S-authority-r0-a3-v1.blend`

Actual reviewed renders:

- `output/review/authority-r0-a3-v1/S_authority_r0_a3_v1_side.png`
- `output/review/authority-r0-a3-v1/S_authority_r0_a3_v1_front.png`
- `output/review/authority-r0-a3-v1/S_authority_r0_a3_v1_front34.png`
- `output/review/authority-r0-a3-v1/S_authority_r0_a3_v1_rear34.png`
- `output/review/authority-r0-a3-v1/S_authority_r0_a3_v1_back.png`

## What v1 proves

- limb-only support and hard locks work;
- accepted R0-A1 / R0-A2 geometry is preserved;
- upper forelimb and hindlimb mass can be increased without touching feet or topology;
- the generic uniform-rod read is reduced.

Validation passed with max displacement 0.05430. Mean upper radial ratio is 1.3137 fore / 1.3721 hind.

## Why v1 does not pass

### Forelimb

The upper limb has more mass, but the elbow/carpal regions become round ring-like swellings. FRONT and FRONT34 read as circular collars attached to a long rod.

The authority uses angular, directional joint planes and blade-like projections, not symmetric radial bulbs.

### Hindlimb

The thigh is stronger, but the stifle/hock transition becomes a large rounded block/bulb. SIDE / FRONT34 show an abrupt ball-to-stick transition into the distal shaft.

The authority requires a compact muscular thigh, an angular backward/forward joint break, then a long narrow metapodial-like distal segment.

### Distal shafts

The distal segments remain too cylindrical. They need a more directional front/back profile and slightly narrower lateral read without changing final foot geometry.

## R0-A3 v2

Do **not** accumulate from v1.

Source remains the accepted:

`output/S-authority-r0-a2-v2.blend`

Replace isotropic radial scaling with anisotropic limb-section shaping:

- proximal upper segments: moderate lateral + sagittal mass;
- joint zones: low lateral expansion but directional sagittal projection;
- distal shafts: keep slim laterally, modest front/back depth only;
- preserve contact/foot region and all separate toe meshes exactly.

R0-A4 remains blocked.
