# S D3 full-cycle visual and gait review — 2026-10-29

## Scope and source integrity
- This review applies only to the existing skinned S runtime review candidate, **not** the R8C/R9 Blender zero-rebuild production asset.
- Actual same-camera WebGL frames and videos: [D2-D baseline](../20261029-s-native-join-d2d/) and [D3 push-v4 trial](./).
- Before: `rig=contact-v3&toe=roll-v3&body=push-v3`; trial: `rig=contact-v3&toe=roll-v3&body=push-v4`.
- Review of stored real frames: all four views sampled at phase .64; full-cycle SIDE and REAR_3_4 frames at .64,.81,.97,.14,.31,.47; direct push-v3 vs v4 stills at approximately .31 and .47 in SIDE and REAR_3_4. Videos were captured and archived; this review does **not** claim real-time playback was directly observed here.
- No GLB, rest geometry, production manifest, other morphs, camera, HUD or main promotion.

## Measured full-cycle findings (96 intervals + endpoints per condition)

Baseline push-v3 at rates .5/1/1.5:
- Pelvis vertical span **0.015445 m**; pelvis angular excursion from initial **2.5708°**; spine **4.0997°**, chest **3.3429°**, head **2.0576°**.
- Same body displacement/angle range at all three tested speed settings. Cadence and stride vary with rate, but the native-body pose envelope does not.
- Support anchors: **0 feet 42/97**, **1 foot 34/97**, **2 feet 21/97**, 3 or 4 feet none. Therefore there is a model-level all-feet-off-ground interval. Do **not** say the gait lacks an airborne phase, and do not treat these samples as physical collision proof.
- Maximum IK reach error in recorded profiles: **0**.
- The opt-in native-join D2-D numerical correction remains scoped KEEP.

Opt-in D3 push-v4 (same original GLB, phase .15-.53 hind-drive angular flex, no fake vertical bob):
| Effective speed | Baseline pelvis angular spread | Trial pelvis angular spread | Trial spine spread |
| --- | ---: | ---: | ---: |
| 0.5× | 2.571° | 2.565° | 4.100° |
| 1× | 2.571° | 3.956° | 4.519° |
| 1.5× | 2.571° | 5.894° | 5.271° |

- Chest stays near 3.34°, head near 2.045°; the change is concentrated in the hip/back, not an actual redesign of forelimb reach or thorax action.
- Support distribution remains 42/34/21 over 97 phase samples at all three tested speeds. Max reach error remains 0.
- [Actions #40870899739](https://github.com/badjoke-lab/evowild-test/actions/runs/40870899739): success; focused Playwright **8 passed** (desktop + Pixel 7 emulation); four-view real WebGL video capture, identical-camera stills and body/contact metrics archived. Physical Android runtime was not tested.

## Visual verdict

**REVISE for full S motion and visual identity.** In the examined SIDE/REAR_3_4 sequences, front legs reach forward only modestly, torso extension/compression is not convincingly transmitted through chest/neck, and the sprint still resembles a set of moving legs under a comparatively steady trunk. D3 push-v4 changes visible pelvis alignment slightly around phase .31, but representative same-camera frames show insufficient overall improvement to promote the variant. Small angular spread alone does not establish physical propulsion, weighting, or user-perceived animation quality.

**Candidate decisions:**
- Preserve `push-v3` as the scoped D2-D review baseline.
- Preserve `push-v4` only as opt-in diagnostic experiment. **Not** default, **not** production, **not** a whole-S KEEP.
- Do not spend another cycle on the native .64 micro-join unless a new measured regression appears.

## Next bounded work

**D3-B: front-limb extension and whole-torso propulsion, one hypothesis.**
Inspect the native shoulder/upper/lower arm chain and both front support transitions over phases .6–1.0, contrasted with the hind push .15–.47. Build a separate opt-in candidate with coherent forward reach and chest/shoulder weight transfer; do not globally bob the body, shift skinned vertices artificially, violate original S silhouette, or change GLB/rest geometry. Keep both existing variants for A/B capture. Gate on sole anchoring, zero-time rate-switch invariance, clearance, hip/fore IK reach and visible SIDE/CHASE/LOW/REAR_3_4 full-cycle improvement. If the reference native animation cannot support this without mesh deformation, return REVISE and route the corrective gait to the separate Blender animation authoring lane instead of masking it with timer curves.

The canonical S reference remains `art/s-creature/references/00_s_type_modeling_image_v1.png`. This study does **not** approve S silhouette or the R8C/R9 sculpt lane.
