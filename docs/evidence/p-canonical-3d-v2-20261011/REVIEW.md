# Canonical P 3D v2 — post-generation review

**Decision: REVISE shape; KEEP v2 as a versioned comparison candidate only.** Not a production model, not an approved gait, and not an 18-runner race integration.

## Verified outputs

- P v1 retained: `public/models/evowild-p/p-canonical-v1.glb`.
- P v2 actual Blender-exported GLB: `public/models/evowild-p/p-canonical-v2.glb` (2,020,324 bytes).
- v2 five browser-rendered rest views: `SIDE.png`, `FRONT.png`, `FRONT34.png`, `REAR34.png`, `BACK.png`.
- Direct canonical/v1/v2 comparison: `comparison-v1-v2.png`.
- v2 animation evidence: `running-contact-sheet.png`, `running-review.mp4`.
- Browser validation: `browser-validation.json`; 17-bone provisional rig, 56,152 Blender-authored triangles reported. Review outputs are isolated from the production race.

Evidence directory: `docs/evidence/p-canonical-3d-v2-20261011/`.

Dedicated GitHub Actions `38103776912` completed SUCCESS; exported model, real captures, and evidence were committed by that run as `8b6173e48bf6c23128be18dfe8c1ab566846c701`.

## Direct visual assessment versus canonical P

| Criterion | v1 to v2 | Remaining problem |
| --- | --- | --- |
| Swept crest | **Localized improvement**: lowers and rakes the major blades rearward. | Still too isolated and spiky from FRONT; original P has a more integrated head silhouette. |
| Skull/jaw | **Small directional improvement**: narrower front planes. | Angular block-like muzzle, mechanical jaw, eye/cue-device proportions uncertain. |
| Shoulder/chest | **Modest contour change**: shoulder relief and high thoracic mass refined. | Red upper arm still reads as an attached oval; reference muscle groups are more interconnected. |
| Elbow/knee | Sphere caps replaced by tendon lofts. | Distinct hard color/mesh junctions remain and flexion deforms mechanically. |
| Dorsal body | Some upper-hull contour shaping. | Still substantially too long, straight-backed and continuous relative to compact/heavy canonical P. |
| Tail | Shorter, less blunt trailing tip. | Tip remains thick and segmented with simplified color detail. |
| Foot anatomy | Preserved v1's split digit and claw forms. | Evenly spaced, smooth toes remain; no validated contact. |

**The overall visual gap remains large.** A lower crest and thinner tail are not sufficient to call this faithful to the canonical P concept. The v2 is closer in selected elements, but the full creature remains unapproved.

## Motion limits

This includes the **same minimal in-place 0.8 s study**, not a revised racing locomotion solution. Captured SIDE/FRONT34 samples demonstrate deformation and leg activity but **cannot establish low foot sliding, friction, correct running speed, world-space foot contacts, 18-runner readability, mobile performance, or production readiness**.

## Required next gate

1. Prioritize **torso/chest proportions and continuous forelimb/shoulder topology**; the current segmented surface is the major identity limitation.
2. Correct the face + cranial/crest root as one shape, not separate spikes, preserving the same canonical P reference.
3. Revisit skinning/rig joint deformation only once the static silhouette passes comparison.
4. Produce the same five renders + silhouette view as actual GLB evidence; get shape approval **before** altering the production 18-runner race.
5. Preserve reference, v1, v2, 2.5D and main until reviewed.

**Do not promote this version.**
