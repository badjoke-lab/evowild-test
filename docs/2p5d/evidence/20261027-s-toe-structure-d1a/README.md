# D1-A — S distal-foot structure and contact identification

Input verified at `025edfcd92e0c46119b325602a491b6556434772`. C1/C2 locomotion, anchors and recovery are unchanged. Same immutable v3 GLB; no asset or production-manifest edit. Formal `public/concept/S.webp` and the canonical reference sheet were inspected: retain S's narrow, non-real-animal distal structures. “Rear/heel-side” below is only the low region toward -Z, not an imported human heel or horse hoof joint.

`src/s_foot_contact_geometry.js` selects unique actual distal mesh vertices (existing S region and raw Y<-.78), confirms terminal weights, and records their actual SkinnedMesh bind-world coordinates. Rear/front groups are the trailing/leading fifth of the near-bottom surface along +Z travel. The support candidate at a given pitch minimizes rotated world Y across the **whole selected distal surface**, rather than assuming the old narrow sole patch remains the lowest surface.

[Exact IDs, world geometry and terminal joints](structure.json); [241-frame existing-gait trace](baseline-cycle.json.gz); [angle-probe results](terminal-rotation-probes.json); [summary](summary.json). Forefoot uses its existing `_foot` terminal node on a two-link chain; hindfoot uses the separate `_toe` terminal after the fitted hock on its three-link chain. No new anatomy or joints.

| Foot | Unique distal vertices | Existing pitch ° | Rear-region height during stance mm | Rotated lowest-vertex candidates |
| --- | ---: | ---: | ---: | --- |
| fore_L | 155 | -0.56993–-0.56993 | 13.14–13.14 | 0°:738, 5°:2534, 10°:2534, 15°:2534, 20°:3131, 25°:3131, 30°:3131, 35°:3131 |
| fore_R | 147 | -1.14336–-1.14335 | 14.05–14.05 | 0°:34245, 5°:35603, 10°:35609, 15°:35609, 20°:35609, 25°:35609, 30°:35609, 35°:35609 |
| hind_L | 114 | -1.92025–-1.92025 | 11.36–11.36 | 0°:2502, 5°:2502, 10°:2502, 15°:3865, 20°:3865, 25°:3865, 30°:3865, 35°:3865 |
| hind_R | 110 | -2.30814–-2.30812 | 14.46–14.46 | 0°:34209, 5°:34209, 10°:34209, 15°:34209, 20°:34209, 25°:34942, 30°:34942, 35°:34942 |

All selected vertices have terminal influence 1.0; all old B1 sole IDs are included. Existing baseline pitch changes by less than .00002° across the cycle: the fixed-foot-posture issue is measured, not inferred from loading success. Rear-region stance height remains constant (~11–14mm), reflecting sculpt relief rather than a heel-rise action.

Diagnostic terminal probes rotate each **actual terminal bone** by 0..35° around its current joint, then resample actual vertices. Tests confirm the measured pitch change, preserved point separation and independent mesh probes. These establish representable rigid distal rotation, **not a safe planted gait range**: uncompensated joint rotation can penetrate the ground. D1-B must solve the chain against actual contact vertices, keep ground Y=0, validate all joints/reach and choose conservative fore/hind amplitudes separately. Geometric sweep vertices switch at different angles in each foot; a single universal pivot would be incorrect.

[Existing SIDE](baseline-SIDE.png) / [LOW](baseline-LOW.png) are real browser views. [Two focused PC/Pixel7 tests PASS](tests.log); [build PASS](build.log), existing chunk warning only. No C1/C2 reimplementation. Canonical S/source geometry is retained; overall REVISE.

Next D1-B after publication: use these real support vertices to roll during late stance, lift the rear surface, then continuously return foot pitch during early recovery. Retain C1/C2 time integration and contact state; expose the rolling candidate separately from the unchanged flat-contact baseline so old full-patch metrics/tests remain available. Report both old all-patch movement and new active-support slip; do not weaken thresholds or call noncontact heel movement a slip.
