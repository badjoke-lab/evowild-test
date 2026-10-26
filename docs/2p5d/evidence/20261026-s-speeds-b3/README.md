# B3 — S speed validation, REVISE

B2 was published at `2db8745`, checkpoint `52263dd`, before this unit. Immutable v2 versus the same separate v3 GLB/controller. Ground Y=0; no body/camera offset to hide contact. No source asset, race or production-manifest change.

## Measurements at all three speeds

Each row uses 241 actual skinned-world vertex samples over a complete cycle. The six gzip JSON traces retain every sampled sole vertex, lowest vertex, target, controller stage and joint coordinates. [Summary and phase arrays](summary.json). Regenerate with Vite on 4173: `CHROMIUM_PATH=/usr/bin/chromium node scripts/validate_s_contact_speeds.mjs`.

| Rate | Travel m/s | Period s, v2 → v3 | Stride/travel per cycle m, v2 → v3 | v3 cadence Hz |
| --- | ---: | ---: | ---: | ---: |
| 0.5× | 2.0 | 2.083333 → 0.589256 | 4.166667 → 1.178511 | 1.6971 |
| 1× | 4.0 | 1.041667 → 0.416667 | 4.166667 → 1.666667 | 2.4000 |
| 1.5× | 6.0 | 0.694444 → 0.340207 | 4.166667 → 2.041241 | 2.9394 |

v2 scales its native cycle and translation by the same rate, retaining a 4.166667m stride and the same per-cycle slide. v3 varies cadence with √rate and stride with √rate independently; `stride × cadence = travel speed` at every rate. These are isolated diagnostic values, not race balance changes.

All figures below compare the **same fixed sole IDs** and unchanged B1 support definition (minY <=25mm, including penetrating frames). Support is a geometric candidate interval, not measured force. Strict plane = |minY|<=1mm. Controller stance is explicitly authored CONTACT/PUSH and exists only for v3; its values are `null` for v2, never a claim of zero slip in the broken baseline. Full lateral, world positions, joint ranges and phase data are in the summary/traces.

| Rate | Foot | Penetration mm, before → after | 25mm-band forward slip m, before → after | Lateral slip m, before → after | Recovery m, before → after | Support candidate s, before → after | v3 declared stance s | v3 strict-plane slip mm |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.5 | fore_L | 44.66 → 0.000 | 2.6825 → 0.0464 | 0.0252 → 0.000000 | 0.230 → 0.340 | 1.3281 → 0.1817 | 0.0982 | 1.194 |
| 0.5 | fore_R | 56.93 → 0.000 | 2.8016 → 0.0491 | 0.0246 → 0.000000 | 0.214 → 0.340 | 1.3108 → 0.1841 | 0.0982 | 1.710 |
| 0.5 | hind_L | 141.62 → 0.000 | 3.2434 → 0.0329 | 0.0444 → 0.000000 | 0.112 → 0.480 | 1.5972 → 0.1989 | 0.1350 | 0.744 |
| 0.5 | hind_R | 134.25 → 0.000 | 3.1511 → 0.0329 | 0.0438 → 0.000000 | 0.129 → 0.480 | 1.5625 → 0.1989 | 0.1326 | 1.190 |
| 1 | fore_L | 44.66 → 0.000 | 2.6825 → 0.0656 | 0.0252 → 0.000000 | 0.230 → 0.340 | 0.6641 → 0.1285 | 0.0694 | 1.689 |
| 1 | fore_R | 56.93 → 0.000 | 2.8016 → 0.0695 | 0.0246 → 0.000000 | 0.214 → 0.340 | 0.6554 → 0.1302 | 0.0694 | 2.419 |
| 1 | hind_L | 141.62 → 0.000 | 3.2434 → 0.0465 | 0.0444 → 0.000000 | 0.112 → 0.480 | 0.7986 → 0.1406 | 0.0955 | 1.053 |
| 1 | hind_R | 134.25 → 0.000 | 3.1511 → 0.0465 | 0.0438 → 0.000000 | 0.129 → 0.480 | 0.7812 → 0.1406 | 0.0938 | 1.684 |
| 1.5 | fore_L | 44.66 → 0.000 | 2.6825 → 0.0803 | 0.0252 → 0.000000 | 0.230 → 0.340 | 0.4427 → 0.1049 | 0.0567 | 2.068 |
| 1.5 | fore_R | 56.93 → 0.000 | 2.8016 → 0.0851 | 0.0246 → 0.000000 | 0.214 → 0.340 | 0.4369 → 0.1063 | 0.0567 | 2.962 |
| 1.5 | hind_L | 141.62 → 0.000 | 3.2434 → 0.0569 | 0.0444 → 0.000000 | 0.112 → 0.480 | 0.5324 → 0.1148 | 0.0780 | 1.289 |
| 1.5 | hind_R | 134.25 → 0.000 | 3.1511 → 0.0569 | 0.0438 → 0.000000 | 0.129 → 0.480 | 0.5208 → 0.1148 | 0.0765 | 2.062 |

At all three constant speeds: measured maximum penetration is zero to displayed precision; v3 declared-stance accumulated patch slip is below 0.001mm, and reach residual is zero. Strict-plane accumulated slip remains 0.74–2.97mm because that band also includes first/last near-ground swing samples. The broader unchanged 25mm band retains 3.3–8.6cm of movement; it has not been removed from the comparison. For example, hind-left 1× band slip per meter traveled improves from .7784m/m to .0279m/m, so improvement is not solely from shortening the cycle.

## Real WebGL evidence

96 browser frames: both rigs × three rates × SIDE/CHASE/LOW/REAR 3/4 × four consecutive quarter-cycle poses. Each `*-views.json` records the matching runtime state. B2 retains [denser 12-phase sequences](../20261026-s-contact-b2/frames) and [PC/Pixel 7 before/after pairs](../20261026-s-contact-b2/README.md). The focused B3 tests run live animation at every speed on both devices; physical Android is untested.

| Rate | Before SIDE / rear | After SIDE / rear | Live rear-quarter screen recording |
| --- | --- | --- | --- |
| .5× | [SIDE](hind-v2-0.5-SIDE-3.png) / [rear](hind-v2-0.5-REAR_3_4-3.png) | [SIDE](contact-v3-0.5-SIDE-3.png) / [rear](contact-v3-0.5-REAR_3_4-3.png) | [.5× video](live-rear-0.5.mp4) |
| 1× | [SIDE](hind-v2-1-SIDE-3.png) / [rear](hind-v2-1-REAR_3_4-3.png) | [SIDE](contact-v3-1-SIDE-3.png) / [rear](contact-v3-1-REAR_3_4-3.png) | [1× video](live-rear-1.mp4) |
| 1.5× | [SIDE](hind-v2-1.5-SIDE-3.png) / [rear](hind-v2-1.5-REAR_3_4-3.png) | [SIDE](contact-v3-1.5-SIDE-3.png) / [rear](contact-v3-1.5-REAR_3_4-3.png) | [1.5× video](live-rear-1.5.mp4) |

Videos are actual Chromium CDP screencast frames encoded using their original wall timestamps, with no generated/interpolated poses. [Capture observations](live-video-observations.json) explicitly record wall duration and simulated travel/cycles. This software-rendered headless environment is slow: existing dt cap makes simulated time advance less than wall time. Therefore these videos prove live articulated movement and contact visibility, **not target-device framerate or real-time sprint performance**. `scripts/record_s_contact_live.mjs` reproduces them.

## Failed transition criterion / next repair

[Instantaneous .5× →1.5× transition diagnostic](speed-transitions.json): maximum actual sole-vertex jump is **.126981m at phase .2** (hind-left in contact) and **.112702m at phase .7** (fore-left in contact), without elapsed simulation time. This is a **new v3 controller limitation**, not one of the pre-existing CI failures. Constant-rate planting does not solve variable-rate world anchors. No claim of full speed-change acceptance; overall **REVISE**.

Next bounded implementation: latch each foot's world contact anchor at touchdown; integrate travel/cadence continuously through acceleration; keep the anchor fixed until toe-off; replan swing targets with continuous position/velocity instead of recomputing `distance + stride × phase` after a rate jump. Add a regression reproducing the two phases above and requiring <1mm discontinuity without flipping knees or stretching segments. Save this separately before attempting toe-roll/push polish.

## Five-stage judgment

| Stage | Current judgment |
| --- | --- |
| Contact | Improved across .5/1/1.5 steady speeds. Sudden speed changes break the anchor: REVISE. |
| Push | Visible planted leg extension; fixed distal orientation lacks a rolling toe-off and forceful propulsion: REVISE. |
| Recovery | Rear sole lifts to ~.48m at every speed; folding is visible in SIDE/LOW/rear. Distal orientation remains stiff: improved, REVISE. |
| Flight | Continuous steady-rate body/limb motion in all four views. Rate jump discontinuity and headless runtime slowdown prevent acceptance: REVISE. |
| Extension | Returns to ground without sampled reach saturation/inverse knee in steady cycles. Foot pitch and dynamic target continuity need work: REVISE. |

Canonical S geometry/silhouette remains intact; inherited material/crest mismatch remains open. No KEEP, baked export, production integration, P/E/A or 18-runner propagation.

## Tests and existing failures

[6 focused tests PASS](tests.log): both devices, all three steady speeds, real animation advance, actual sole contact/recovery/ranges, independent B1 mesh-probe regression. [2 metric-semantics tests PASS](metric-semantics-tests.log) verify missing controller data is unknown, not zero. [Build PASS](build.log), existing chunk-size warning. The transition diagnostic above **fails the quality criterion** despite these scoped tests passing.

B1 Actions [40322444560](https://github.com/badjoke-lab/evowild-test/actions/runs/40322444560): build PASS, 114 passed / 3 known failures / 81 skipped. Failures remain desktop/Android historical PUSH comparison and intermittent desktop AGILITY; no B1-specific failure. B2 Actions [40323960662](https://github.com/badjoke-lab/evowild-test/actions/runs/40323960662) was in progress at inspection. B3 Actions pending publication; do not claim global CI green.
