# S Authority R0-A3 v2 Review

Decision: **KEEP / ACCEPT R0-A3**

Authority:

`references/00_s_type_modeling_image_v1.png`

Candidate:

`output/S-authority-r0-a3-v2.blend`

Actual reviewed renders:

- `output/review/authority-r0-a3-v2/S_authority_r0_a3_v2_side.png`
- `output/review/authority-r0-a3-v2/S_authority_r0_a3_v2_front.png`
- `output/review/authority-r0-a3-v2/S_authority_r0_a3_v2_front34.png`
- `output/review/authority-r0-a3-v2/S_authority_r0_a3_v2_rear34.png`
- `output/review/authority-r0-a3-v2/S_authority_r0_a3_v2_back.png`

## Why v2 passes R0-A3

R0-A3 is a limb segment-rhythm / silhouette gate, not final surface cleanup.

Compared with the rejected v1 isotropic radial scaling:

- the forelimb elbow/carpal zones no longer read as circular collars;
- the hindlimb stifle/hock transition no longer reads as a single round bulb;
- upper segments retain athletic mass without uniformly inflating the whole limb;
- joint zones use stronger sagittal depth than lateral width, producing a directional angular break;
- distal shafts are visibly slimmer laterally and remain long;
- SIDE and FRONT34 now read as upper mass -> angular joint -> long narrow distal segment rather than ball -> rod;
- FRONT/BACK preserve a narrow racing-leg read instead of thick cylindrical columns;
- feet/toes were not altered.

Validation:

- max displacement: 0.03264
- upper lateral mean: fore 1.1791x / hind 1.1915x
- joint sagittal mean: fore 1.2853x / hind 1.3270x
- distal lateral mean: fore 0.9652x / hind 0.9686x
- topology/manifold/hard locks: PASS

## Qualification

Visible voxel/facet roughness at proximal roots and some local section transitions is **not accepted as final surfacing**. It is deferred to the later surface/continuity pass after the authority silhouette sequence is complete.

This acceptance claims only that the R0-A3 limb segment rhythm is sufficient to continue.

## Locked for R0-A4

Keep exact:

- accepted R0-A1 head / crest / neck;
- accepted R0-A2 shoulder / thorax / waist / pelvis;
- accepted R0-A3 limb segment rhythm above the contact-foot boundary;
- tail;
- body topology outside the foot support.

Next gate:

**R0-A4 split racing feet**

The old generic three-toe geometry is explicitly rejected as final S morphology.

R0-A5 long layered tail remains blocked until R0-A4 passes.
