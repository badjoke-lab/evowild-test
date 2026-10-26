# B1 — Actual S sole surface measurement, REVISE

Immutable input: `focus-hind-fit-v2.glb`, SHA-256 `efa804ea4c3e2a2d272918e6982da12a365f1759140f50fa6d3f586c5fd2bede`. No rig, mesh or animation changes in this unit. Ground stays world Y=0.

`src/s_sole_metrics.js` chooses fixed vertex IDs from the bottom 0.012 model units of each separate foot in bind POSITION geometry, removes duplicate positions, then samples **actual Three.js SkinnedMesh.getVertexPosition + matrixWorld**. It uses neither bone origins nor weight-group centroids. [Patch IDs and bind points](sole-patches.json); [241 complete samples including all world vertices](hind-v2-1-trace.json.gz); [metrics and inferred phases](summary.json); [real LOW browser view](low.png). Raw trace is gzip-compressed JSON, not a substitute summary.

One native cycle, 240 intervals (4.34ms at 1×), 1.041667s, diagnostic travel 4.166667m at 4m/s. This is measurement of the existing broken gait, not a movement specification. Plane tolerance 0.025m. Support candidate means minY <= tolerance, **including penetration** so broken contact cannot disappear from slip measurements. Valid plane-band time and penetrating time are also reported separately. Support duration requires both adjacent samples in this set. Slip sums absolute forward/lateral movement of the same vertex IDs, averaged across the patch; it does not follow a changing lowest vertex. Recovery height is the maximum lower envelope of the patch. Patch selection is a sole-contact candidate, not a force measurement.

| Foot | Vertices | Penetration m | Forward slip m | Lateral slip m | Support candidate s | Recovery m |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| fore_L | 47 | 0.0447 | 2.6825 | 0.0252 | 0.6641 | 0.2301 |
| fore_R | 53 | 0.0569 | 2.8016 | 0.0246 | 0.6554 | 0.2140 |
| hind_L | 35 | 0.1416 | 3.2434 | 0.0444 | 0.7986 | 0.1115 |
| hind_R | 40 | 0.1342 | 3.1511 | 0.0438 | 0.7812 | 0.1287 |

CONTACT/PUSH/RECOVERY/FLIGHT/EXTENSION annotations are explicitly inferred from vertical velocity and relative longitudinal motion; penetration has an independent flag. A PUSH label does not establish propulsion. No KEEP decision follows from this classification.

Reproduce with Vite on port 4173: `CHROMIUM_PATH=/usr/bin/chromium node scripts/measure_s_soles.mjs`. [4 focused tests PASS](tests.log), on desktop and Pixel 7 emulation: known stationary/sliding patch arithmetic and independent vertex-ID world probes at mid-cycle. [Build PASS](build.log). No old full journey suite repeated.

Next B2: preserve v2 and produce a separate candidate, use these sole patches for contact targets, constrain joint reach and bend direction, and restore hind recovery height. Then B3 compares all three speeds. B1 does not repair the gait. Prior four-view evidence remains in [Unit A](../20261026-s-hind-fit/README.md).
