# D3-C v2 — actual authored candidate, still REVISE

## Decision

**Technical continuity / preserved assets: KEEP within the review lane.** Independent v2 GLB, real shoulder/arm/elbow skin motion and original contact limits pass. This is not production approval.

**S run visual quality: REVISE.** Recovery is visibly stronger than v1, but the five views do not yet establish the requested powerful, coordinated sprint. No promotion, main merge, production manifest change or other species work.

## What changed in the actual model and runtime

`d3c-scapula-author-v2.glb` adds 14 authored translation/rotation tracks over the existing 23-joint rig: scapular glide and rotation, upper-arm advance, elbow folding, pelvis push, spine/chest loading and neck/head/tail response. The native v1 clip, skin, mesh and rest bindings remain byte-preserved. Cubic review tracks are evaluated after the existing D2-D body pose; FK of the authored humerus/elbow guides the airborne fore-foot IK targets. The actual grounded sole anchors remain authoritative.

Scapular rest translations are restored every evaluation, preventing accumulated movement on repeated dt=0. The v2 shoulder curve includes analytic tangents instead of inheriting the v1 LINEAR-key velocity corner at phase .75. The preserved final authoring uses 18° humerus / −34° elbow additions; the earlier local 26°/−42° cramped trial was not restored. Its lost screenshots are not claimed as evidence here.

The stand-alone full pose clip is playable in a GLTF viewer, but **the measured contact behavior requires the review runtime IK adapter**. The exported pose clip is not an offline IK-baked animation. Chest loading is animation, not a force/center-of-mass simulation.

## Same-condition visual comparison

Actual WebGL movies, 24 successive simulation steps per cycle, 1×, starting phase .64. Originals retain the same camera, ground and lighting. `previews/` only arranges cropped screenshots for inspection; all 240 uncropped PNG frames remain in `frames/`. No image generation, frame interpolation or raster motion was used.

| View | v1 | v2 | Observed improvement and remaining problem |
| --- | --- | --- | --- |
| SIDE | [movie](before-SIDE.mp4) | [movie](after-SIDE.mp4) | At .14–.31, elbow folding and forward shoulder travel now clearly lift the fore feet. At .31 both front feet crowd beneath the chest; the transition to .47 extension still reads as an isolated foreleg action. Stronger articulation is not yet a convincing whole-body sprint. |
| FRONT | [movie](before-FRONT.mp4) | [movie](after-FRONT.mp4) | Recovery is more visible around .31. No obvious gross lateral leg crossing in the inspected frames, but inherited heavy shadow conceals shoulder surface detail; this view cannot approve weighting quality. |
| CHASE | [movie](before-CHASE.mp4) | [movie](after-CHASE.mp4) | Higher recovery can be seen beside the trunk, but hind legs and tail obscure it; the trunk still looks comparatively steady and upright. Improvement is smaller than SIDE. |
| LOW | [movie](before-LOW.mp4) | [movie](after-LOW.mp4) | Support and lifted fore feet remain distinguishable. No obvious new ground intersection in the sampled sequence; small gaps/slip require the actual-vertex measurements below, not the colored diagnostic dots. Pelvis-to-chest drive remains visually weak. |
| REAR 3/4 | [movie](before-REAR_3_4.mp4) | [movie](after-REAR_3_4.mp4) | Fore recovery and the changing shoulder outline are clearer at .14–.31. Head/neck remain upright, the rear drive does not read as a forceful whole-body action, and feet cluster under the chest. Still REVISE. |

Direct inspection used the saved ordered frames 00/04/08/12/16/20 (phases .64/.807/.973/.14/.307/.473), their five contact sheets, and full-size SIDE and desktop/Pixel 7 images. The MP4 files encode the real consecutive browser renders. This records frame-sequence inspection, not a claim of personally watching normal-speed MP4 playback or user acceptance.

[Desktop before](desktop-before.png) / [after](desktop-after.png), [Pixel 7 emulation before](android-before.png) / [after](android-after.png). The entire creature and feet remain visible in these review-page captures. Physical Android hardware, race-size rendering and 18-body performance were not tested.

## Fresh measurements

Seven integrated profiles: steady 0.5/1/1.5×, acceleration, deceleration, abrupt fore and hind changes. Measurements use actual skinned sole vertices and the active toe-roll support, not only target coordinates. See [contact summary](contact-summary.json), `v2-*-summary.json` and compressed raw traces.

| Quantity | v2 measured worst case |
| --- | ---: |
| Guard penetration / IK reach error / dt=0 jump | 0 m |
| Active support accumulated slip | 0.000870 mm |
| Active support gap | 0.423742 mm |
| Sole speed continuity residual | 0.005987 m/s |
| Sampled 310-vertex body/limb residual | 0.003592 m/s |
| Minimum hind recovery height | 47.980 cm |
| Fore recovery height | 63.706–65.368 cm |
| Solved joint angles | 48.671–161.421° |

Old all-patch displacement remains in each summary as `legacyAllPatchMovement`; the non-support part of a rolling sole is allowed to move. It is not mislabeled support slip. Limits remain 1 mm contact/jump, 0.02 m/s residual, 35–178° joints and original recovery limits.

At 1×, a separate 97-phase diagnostic seek comparison measured fore shoulder travel relative to root translation: v1 3.60 cm, v2 L16.49/R19.25 cm. Elbow minima changed v1 L96.50/R91.69° to v2 L62.39/R54.29°. Sampled matched-pose elbow folding increased by up to 36.41° and actual body vertices moved by up to 6.30 cm. These quantify articulation, not quality. The relatively tight new elbow minima are a visual-review concern, despite staying inside constraints.

Pelvis/chest maximum angular distance from phase-zero at 1× changes 2.571/3.343° → 3.443/4.015°. Head is 3.188° → 2.695°. Root vertical motion is unchanged (1.545 cm span). `articulation-samples.json` records body and limb poses at .5/1/1.5×; this is explicitly a diagnostic phase-seek sample, separate from the integrated speed traces.

## Identity and scope

The canonical S reference from modeling-branch commit `48b39d8b64aa5146dc2028876b448c3e884295e6`, `art/s-creature/references/00_s_type_modeling_image_v1.png`, was read and hash-checked (`93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`). No reference or geometry was modified. The inherited gray GLB's head posture and silhouette are not newly approved against that image. The model remains a review candidate.

## Next bounded authoring unit

Keep v1 and this v2 intact. First measure and inspect the fore-recovery transition .14–.47 and its relationship to hind support, especially .25–.35 where the feet cluster. Adjust the timing/path of the authored shoulder–upper-arm–elbow recovery in a new candidate, rather than blindly increasing amplitudes or changing anatomy. Recheck actual skin separation, retained rear push and chest response in SIDE/REAR 3/4, then the same contact/velocity tests. Do not hide the issue with camera/ground changes or promote to 18 racers.
