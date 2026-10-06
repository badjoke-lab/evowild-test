# S Authority R0-A3 v1 Plan

Status: **LOCKED FOR EXECUTION**

Source:

`output/S-authority-r0-a2-v2.blend`

Accepted gates:

- R0-A1 head / paired crest / neck;
- R0-A2 shoulder / thorax / waist / pelvis.

Authority:

`references/00_s_type_modeling_image_v1.png`

## Scope

R0-A3 edits only the continuous-body forelimb and hindlimb segment envelope.

Do not edit:

- accepted head / crest / neck;
- accepted shoulder / thorax / waist / pelvis;
- separate toe meshes or final foot shape;
- tail;
- cameras;
- topology.

## Authority mismatch

Current limbs remain thin generic rods.

The authority requires:

- substantial proximal forelimb and hindlimb segments;
- clear shaft vs joint rhythm;
- angular knee / hock read;
- long lightweight distal segments;
- no uniform tube/rod silhouette.

## Method

Use mirrored piecewise limb centerlines and scale only the radial distance from each centerline.

Body vertices qualify only when:

- source Z is between 0.12 and 0.84;
- source |X| is at least 0.095;
- forelimb: Y < 0.28 and near the fore chain;
- hindlimb: Y > 0.48 and near the hind chain;
- distance to the selected chain <= 0.12.

This intentionally leaves the accepted axial body mass and the feet/contact zone fixed.

## Segment profiles

Forelimb radial scale:

- upper segment near Z 0.82: ~1.45;
- first joint near Z 0.68: ~1.25;
- elbow/carpal rhythm near Z 0.52: ~1.38;
- long shaft near Z 0.34: ~1.08;
- distal joint near Z 0.20: ~1.22;
- near-foot boundary Z 0.12: ~1.05.

Hindlimb radial scale:

- upper thigh near Z 0.82: ~1.55;
- stifle near Z 0.73: ~1.28;
- hock transition near Z 0.57: ~1.42;
- long distal shaft near Z 0.34: ~1.10;
- distal joint near Z 0.22: ~1.24;
- near-foot boundary Z 0.12: ~1.05.

## Hard limits

- accepted R0-A1 / R0-A2 geometry outside limb support exact;
- all separate toe meshes exact;
- body topology / vertex count unchanged;
- manifold edge count stays 0;
- max limb displacement <= 0.065;
- feet/contact region Z < 0.12 exact;
- render SIDE / FRONT / FRONT34 / REAR34 / BACK and stop.

R0-A4 split racing foot remains blocked until R0-A3 passes.
