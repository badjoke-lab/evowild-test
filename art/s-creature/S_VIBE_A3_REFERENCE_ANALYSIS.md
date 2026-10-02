# S Vibe Lane — Gate A3 Reference Analysis

Status: LOCKED FOR A3a
Lane: exp/s-creature-vibe-modeling
Source model: output/S-vibe-a2b-v1.blend

## A2 closure

Gate A2 (thorax / waist / pelvis): ACCEPTED for the experimental lane.

Accepted source:
- output/S-vibe-a2b-v1.blend

## Reference authority for limbs

Primary:
- references/01_s_body_primary.png — S Sprint body and limb proportion authority
- references/02_s_silhouette.png — S global silhouette authority

Secondary:
- references/06_leg_foot_variants.png — joint/distal-limb/foot design language only

Important:
The repository does not lock S to one numbered L1-L6 variant.
Do not invent such an assignment.
Use the S Sprint body image for the actual S limb rhythm.

## Current limb problem

The current forelimbs still read as low-complexity rods:
- proximal shoulder/upper-limb mass is too blunt
- joint rhythm is weak at silhouette scale
- elbow and wrist transitions are not sufficiently distinct
- distal taper exists but the whole chain reads like connected cones
- the large proximal forelimb cage competes with the accepted thorax

Feet are already small multi-toed racing feet and are NOT part of A3a.

## A3 subdivision

Do not edit all four limbs together.

### A3a — forelimb chain only

Editable:
- S_forelimb_L
- S_forelimb_R

Hard fixed:
- complete core body geometry
- accepted crest
- both hindlimbs
- all fore toes / feet
- all hind toes / feet
- tail
- object topology / vertex counts

Single hypothesis:
Improve forelimb joint rhythm and proximal-to-distal taper without changing the foot or the accepted torso.

Target side rhythm:
- shoulder root remains near current attachment
- upper arm descends slightly rearward
- elbow becomes a readable posterior hinge
- forearm returns forward toward a light wrist
- distal segment remains long and narrow
- foot/toes remain exactly fixed

Target mass rhythm:
- shoulder/root: reduced from current bulky cone, but still readable
- upper arm: athletic, not cylindrical
- elbow: small but legible joint change
- forearm: narrower
- wrist/distal: light
- no hoof/paw mass

### A3a target chain centers and radii

The existing 7-station / 8-sided forelimb topology is preserved.

For each side, use mirrored X.

Station 0 shoulder/root:
- center X = ±0.115
- Y = -0.030
- Z = 0.985
- lateral radius = 0.068
- sagittal radius = 0.095

Station 1 upper arm:
- X = ±0.148
- Y = 0.035
- Z = 0.845
- lateral radius = 0.056
- sagittal radius = 0.070

Station 2 elbow:
- X = ±0.158
- Y = 0.125
- Z = 0.685
- lateral radius = 0.040
- sagittal radius = 0.046

Station 3 wrist-direction hinge:
- X = ±0.153
- Y = -0.070
- Z = 0.515
- lateral radius = 0.027
- sagittal radius = 0.038

Station 4 distal forelimb:
- X = ±0.150
- Y = -0.220
- Z = 0.230
- lateral radius = 0.018
- sagittal radius = 0.023

Station 5 distal joint:
- X = ±0.150
- Y = -0.255
- Z = 0.105
- lateral radius = 0.021
- sagittal radius = 0.020

Station 6 foot-root interface:
- unchanged center = current source center
- reduced/light radius only if required to preserve current toe interface
- toe objects themselves remain exact-match fixed

## Acceptance

SIDE:
- shoulder/elbow/wrist rhythm is readable without exaggeration
- chain does not read as one rod
- no detached-looking shoulder cone
- distal limb remains long/light

FRONT / FRONT34:
- forelimbs remain narrow
- shoulder roots do not overwhelm thorax
- no new splayed-leg look

Hard validation:
- only S_forelimb_L and S_forelimb_R vertex coordinates may change
- their topology and vertex counts remain identical
- feet/toes are byte-coordinate unchanged
- complete core, crest and hindlimbs are exact-coordinate unchanged

Stop after SIDE / FRONT / FRONT34 / BACK.
Do not start A3b hindlimbs automatically.
