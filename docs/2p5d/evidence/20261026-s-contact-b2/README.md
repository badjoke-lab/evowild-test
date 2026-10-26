# B2 — S sole-contact IK and recovery candidate v3, REVISE

B1 was pushed and remote verified at `2df5c21`, checkpoint `5ea6d03`, before B2 started. This is an isolated review candidate; original GLBs, v1, v2, the production manifest, race engine, Agent and HUD are unchanged.

Candidate is **a pair**: `public/models/evowild-s/review/focus-contact-v3.glb` plus `src/s_contact_ik.js`. The GLB retains the native clip; the new locomotion is applied in the browser **after** the native animation. It is not a newly baked exportable GLB clip. Open `s-run-review.html?rig=contact-v3`. [Asset report](asset-report.json). `python3 scripts/build_s_contact_candidate.py` checks the immutable v2 source hash before producing the separate file.

## Implementation

- POSITION, NORMAL, indices, all rest joint positions, inverse binds and native animation samples remain byte-exact. 4,934 distal foot vertices receive localized sole weights, blended from Y=-.70 to -.78 model units. Every measured sole vertex is rigidly attached to its actual terminal joint; torso/neck weights are unchanged.
- The actual skinned bind-pose sole point defines the terminal-joint offset. Using the raw POSITION point initially left a 5.4mm error; measuring the skinned point removes that error without moving the body, ground or camera.
- A two-segment analytic solve places the knee on the existing forward bend side. The hind solve retains the v2 hock-to-toe segment and solves hip/knee/hock, then restores the terminal foot orientation. Segment lengths remain fixed. Reach error and joint angles are emitted each frame. At 1×, all sampled reach errors are zero, fore knee angles 102–154°, hind knee 50–133°, hock 91–156°.
- Stance targets move backward relative to the body at exactly travel speed, remaining fixed in world space at constant speed. Continuous cubic longitudinal recovery preserves velocity across lift/landing; a smooth vertical arc raises front soles 34cm and hind soles 48cm. The body/chest/neck retains native motion. Fore stance phase .64/.72 follows the existing low-body interval; hind .15/.24 precedes it. These are diagnostic controller timings, not game balance rules.
- Cadence = 2.4√rate cycles/s, travel = 4×rate m/s, stride = travel/cadence. At 1× this gives .416667s and 1.666667m per cycle. Cadence and stride both change with rate; B3 must validate all rates. Abrupt in-stance speed switching remains unverified here.

## Actual vertices, before/after at 1×

| Foot | Penetration m | Forward support slip m | Recovery m | Support candidate s |
| --- | ---: | ---: | ---: | ---: |
| fore_L | 0.0447 → 0.0000 | 2.6825 → 0.0656 | 0.2301 → 0.3400 | 0.6641 → 0.1285 |
| fore_R | 0.0569 → 0.0000 | 2.8016 → 0.0695 | 0.2140 → 0.3400 | 0.6554 → 0.1302 |
| hind_L | 0.1416 → 0.0000 | 3.2434 → 0.0465 | 0.1115 → 0.4800 | 0.7986 → 0.1406 |
| hind_R | 0.1342 → 0.0000 | 3.1511 → 0.0465 | 0.1287 → 0.4800 | 0.7812 → 0.1406 |

The unchanged B1 25mm support band includes near-ground swing frames. Therefore the residual 4.6–6.9cm band slip is retained rather than hidden; it is not the same as controller-declared stance slip. Dedicated tests independently require every actual patch vertex to stay within 1mm per step throughout consecutive declared CONTACT/PUSH samples and the sole to remain within 1mm of Y=0. v2 and v3 cycle lengths differ: compare both per-cycle totals and travel-normalized values, not totals alone. [Full world-vertex trace](contact-v3-1-trace.json.gz), [summary](summary.json).

## Real browser evidence and quality

Same geometry, ground and four camera positions as [v2 before frames](../20261026-s-hind-fit/frames). [After SIDE](frames/SIDE), [CHASE](frames/CHASE), [LOW](frames/LOW), [REAR 3/4](frames/REAR_3_4): 12 consecutive phase samples per view, native body plus real articulated IK, no image interpolation. [Rear-quarter video](rear-quarter.mp4): these actual 12 frames at 28.8fps, one .416667s cycle. [Runtime observations](frames/native-observations.json) record running time advancing and zero browser errors.

| Device | Before v2 | After v3 |
| --- | --- | --- |
| PC 1280×800 | [image](desktop-hind-v2.png) | [image](desktop-contact-v3.png) |
| Pixel 7 emulation | [image](android-hind-v2.png) | [image](android-contact-v3.png) |

Physical Android not tested. Same phase .4 and rear camera in device pairs. Shape/silhouette remains the existing S, including inherited gray material and crest differences from the formal reference. No newly generated mock/art.

| Stage | Observation | Decision |
| --- | --- | --- |
| Contact | Foot surface reaches fixed ground; prior deep burial is removed. Flat terminal orientation is mechanically rigid and needs rolling contact review. | Improved, REVISE |
| Push | Stance leg extends as body passes the planted foot. Toe-off lacks a convincing rolling push and force transfer. | REVISE |
| Recovery | Rear hock/knee fold and sole clears to .48m vs .11–.13m; clearly visible in SIDE/LOW/rear. Constant distal orientation still looks stiff. | Improved, REVISE |
| Flight | Body and limb motion is continuous; four-view shots retain neck/chest and S silhouette. Timing and weight transfer still feel schematic. | REVISE |
| Extension | Continuous forward return connects to landing; no 1× reach clamp or inverse knee solution in sampled cycle. Terminal foot pitch is too constant. | REVISE |

Numerical improvement is not visual approval. No production promotion, sprite extraction or 18-runner/P/E/A expansion.

## Verification / next unit

[Focused tests](tests.log): immutable geometry/rest/clip, actual sole stance, recovery, reach/angle bounds on PC and Pixel 7. [Build](build.log). Prior `af446c7` Actions [40297092762](https://github.com/badjoke-lab/evowild-test/actions/runs/40297092762): build PASS, 110 passed / 3 known failures / 81 skipped; historical PUSH comparison on both devices and intermittent desktop AGILITY. No S-specific prior failure. New B2 Actions pending publication.

B3 next: measure v2/v3 at .5/1/1.5, retain unchanged 25mm metric and add a strict plane-band check, summarize per-foot range and reach, compare actual multi-view movement, and test rate transitions explicitly. Save as a separate commit.
