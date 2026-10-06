# S Authority R0-A2 v1 Review

Decision: **REVISE**

Authority:

`references/00_s_type_modeling_image_v1.png`

SHA-256:

`93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`

Candidate:

`output/S-authority-r0-a2-v1.blend`

Reviewed actual renders:

- `output/review/authority-r0-a2-v1/S_authority_r0_a2_v1_side.png`
- `output/review/authority-r0-a2-v1/S_authority_r0_a2_v1_front.png`
- `output/review/authority-r0-a2-v1/S_authority_r0_a2_v1_front34.png`
- `output/review/authority-r0-a2-v1/S_authority_r0_a2_v1_rear34.png`
- `output/review/authority-r0-a2-v1/S_authority_r0_a2_v1_back.png`

## What v1 gets right

- the old uniform deer/gazelle torso is broken up into shoulder -> tucked waist -> pelvis rhythm;
- the abdominal tuck is now clearly readable in SIDE;
- pelvis mass is larger than the rejected donor;
- accepted R0-A1 head / crest / neck stayed fixed;
- hard-scope and topology validation passed.

## Why v1 does not pass

### Shoulder / anterior thorax — REVISE

The shoulder width field is too strong and too uniform across the continuous union.

Validation confirms a shoulder width ratio of **1.4162x**. In FRONT / FRONT34 / REAR34 this reads as laterally hanging wing/cape-like masses rather than the authority's compact athletic shoulder and upper forelimb volume.

The next revision must keep stronger central thorax mass while fading the lateral gain toward the existing proximal forelimb root.

### Waist — KEEP DIRECTION, REDUCE DISTORTION

The tuck direction is correct. The ventral floor rose by **0.0768**, which creates the required racing waist.

Do not remove the tuck. Rebuild it from the accepted R0-A1 v2 source with a torso-centered field so nearby limb-root geometry is not dragged with the abdomen.

### Pelvis / upper hindquarter — REVISE

The pelvis is larger, but the continuous-body field also inflates the proximal hindlimb root. SIDE / FRONT34 / REAR34 show a bulbous hanging upper-thigh mass and an abrupt transition into the thin distal limb.

The next revision must concentrate volume in the axial pelvis / rump and taper deformation strongly toward large-|X| proximal leg geometry.

## Next

Do **not** continue from v1 geometry.

Build **R0-A2 v2 from the accepted R0-A1 source**:

`output/S-authority-r0-v2.blend`

Locked correction:

- central-body-weighted lateral field;
- milder shoulder gain;
- preserve deep waist tuck with reduced lateral root drag;
- pelvis gain concentrated near the torso centerline;
- proximal limb roots receive only a small residual deformation;
- R0-A1 head/crest/neck remain exact.

R0-A3 remains blocked until R0-A2 passes.
