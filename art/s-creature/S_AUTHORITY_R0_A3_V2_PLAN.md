# S Authority R0-A3 v2 Plan

Status: **LOCKED FOR EXECUTION**

Source: `output/S-authority-r0-a2-v2.blend`

Do not use R0-A3 v1 geometry as input.

Authority: `references/00_s_type_modeling_image_v1.png`

Prior review: `S_AUTHORITY_R0_A3_V1_REVIEW.md` → **REVISE**

## One correction hypothesis

v1 failed because isotropic radial scaling turns joint zones into circular collars/bulbs.

v2 uses an anisotropic local section around the mirrored limb centerline:

- lateral axis: projected world X;
- sagittal axis: perpendicular direction in the local Y/Z plane;
- upper segments: moderate lateral and sagittal gain;
- joint zones: small lateral gain, larger sagittal gain;
- long distal shafts: slightly narrower laterally, only small sagittal depth;
- contact/foot boundary: exact.

## Section profiles

Forelimb stations, each `(x,y,z, lateral_scale, sagittal_scale)`:

- (0.155, 0.040, 0.82, 1.28, 1.34)
- (0.168, 0.105, 0.68, 1.10, 1.20)
- (0.163,-0.030, 0.52, 1.07, 1.34)
- (0.155,-0.170, 0.34, 0.94, 1.04)
- (0.150,-0.235, 0.20, 1.00, 1.14)
- (0.150,-0.255, 0.12, 1.00, 1.00)

Hindlimb:

- (0.155, 0.740, 0.82, 1.34, 1.40)
- (0.175, 0.665, 0.73, 1.10, 1.18)
- (0.169, 0.820, 0.568,1.07, 1.38)
- (0.160, 1.020, 0.34, 0.94, 1.05)
- (0.153, 1.070, 0.22, 1.00, 1.14)
- (0.150, 0.990, 0.12, 1.00, 1.00)

## Support and hard locks

- source Z 0.12 .. 0.84;
- fore support Y -0.35 .. 0.28;
- hind support Y 0.48 .. 1.18;
- nearest centerline distance <= 0.095;
- high overlap zone Z > 0.72 and |X| < 0.115 remains exact;
- source Z < 0.12 remains exact;
- all separate toe meshes exact;
- accepted R0-A1/R0-A2 outside limb support exact;
- tail exact;
- topology and cameras exact.

## Hard limits

- max displacement <= 0.055;
- manifold edge count 0;
- upper lateral mean growth: fore 1.12..1.30, hind 1.15..1.34;
- joint sagittal mean growth >= 1.18;
- distal lateral mean growth <= 1.02;
- render SIDE / FRONT / FRONT34 / REAR34 / BACK and stop.

R0-A4 remains blocked.
