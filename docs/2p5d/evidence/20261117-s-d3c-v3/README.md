# S D3-C v3 — authored fore recovery, review only

Independent model: `public/models/evowild-s/review/d3c-scapula-author-v3.glb` (23 joints, 2,271,944 bytes), SHA256 **f894573f8f89e6d3067e64494dcecf300c6083d76f80c7890813e544c2a86822**. Runtime: `s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v5&shoulder=authored-v3`. Use `shoulder=authored-v2` for the preserved baseline.

**Overall visual verdict: REVISE.** The folded forefeet now separate in height and progress toward extension; the chest/rear drive still does not read as a powerful whole-body sprint. This candidate is not promoted. [Detailed visual review](VISUAL_REVIEW.md) records improvements, remaining defects and the inspection method.

## Actual authoring and diagnosis

[Cause isolation](DIAGNOSIS.md) used native FK, first IK, repeated zero-guide IK, authored FK guide and D3-B-cancelled ablations on actual skin. Repeated IK displacement was0; D3-B was not the deep-fold cause. v2 superimposed a broad elbow fold over an already folded IK pose. At .307 its guide added17.5/29.9cm upward displacement. The defect was visual clustering, not a demonstrated3D foot collision.

The final v3 authors a sequence instead of simply lifting the feet higher. With `u` denoting the existing airborne interval and `pulse` the smooth sin⁴ window:

| GLB track | Final authored addition (degrees) |
| --- | --- |
| Left upper arm | +18 × pulse(u,0,.90), earlier advance |
| Right upper arm | +18 × pulse(u,.22,1), following advance |
| Left lower arm | −20 × pulse(u,0,.70) +14 × pulse(u,.32,.88), fold then extension |
| Right lower arm | −14 × pulse(u,.08,.78), shorter fold |

No offsets are applied during stance. Values and first derivatives vanish at entry/exit. Maximum additions are not larger than v2. Existing scapula, chest, pelvis and rear-support poses remain, with timing of fore extension now falling within rear push. Actual body vertices and hind soles in .14–.473 are unchanged (zero measured drift). Motion is not a simulated floor-force/COM system.

New coverage also exposed an **existing** v2 native-body velocity corner at .72, including constant speed: .645773m/s at sampled vertex33125. V3 adds the independent `D3C_V3_Native_Join` GLB clip over .712–.728 with matched endpoint tangents; its native-pose correction preserves the existing load rotations. D2-D/D3-B modules were not rewritten. [Actual displacement](native-join-extent.json): max root change0.04025mm; sampled body-skin change0.34890mm at1×, zero outside the splice. Ground and camera are unchanged; this is local interpolation of existing poses, not a body shift to hide contact.

All original geometry, skin weights, rest nodes, bind buffers, materials and v1/v2 animation data remain intact; see [integrity report](asset-integrity.json) and `verify_s_d3c_v3.py`. The GLB contains full pose, preserved source and review-control clips. Measured contact still requires runtime IK; the standalone pose animation is not an offline IK-baked export.

## Tests and measurements

Final curve: [8/8 affected PC/Pixel7 Playwright cases PASS](extension-final-tests.log), seven speed profiles and20 sampled switch phases including both splice edges. The [earlier full14/14](targeted-tests.log) also covers six unchanged v2/D2-D baseline cases. Those six were not needlessly repeated after the last GLB-only fore-curve change. [Final build PASS](build.log), existing bundle-size warning only.

Failure history is retained: [initial12pass/2fail](initial-tests-failed.log) exposed the inherited .72 corner; [targeted correction2/2PASS](native-join-targeted-tests.log). The [first extension6pass/2fail](extension-first-tests-failed.log) missed the new review-only10cm endpoint-height separation guard (9.595cm); advancing the upper-arm timing, without relaxing the guard, gives15.456cm. These are authored-motion review checks, not new gameplay/species rules.

| Measured quantity | v2 | Final v3 |
| --- | ---: | ---: |
| Elbow L/R at .307 | 74.68° /55.10° | 105.16° /74.57° |
| Minimum elbows in .14–.473 | 62.37° /54.27° | 84.82° /74.23° |
| Fore surface centroid forward separation at .307 | 13.03cm | 28.51cm |
| Fore recovery maximum, profile range | 63.71–65.37cm | 45.97–47.09cm |
| Minimum hind recovery | 47.98cm | 47.98cm |
| Penetration / IK reach error / dt=0 jump | 0 | 0 |
| Max accumulated active-support slip | .000870mm | .000870mm |
| Max active-support gap | .423742mm | .423742mm |
| Max sole velocity residual | .005987m/s | .005987m/s |

Final sampled body/limb speed residual remains below .02m/s (max~.008396m/s including splice edges). These are finite sampled checks, not a proof at every possible phase/rate. All original contact, joint-angle35–178°, recovery and speed limits remain unchanged. Non-support sole motion during toe roll remains separately reported as `legacyAllPatchMovement`.

Raw evidence: [contact summary](contact-summary.json), seven `v3-*.json.gz` integrated actual-vertex traces, [recovery summary](recovery-authored-v3-summary.json), `recovery-*.json` ablations, [before-join probes](boundary-probe-before-join.json), [after-join probes](boundary-probe.json). Phase-seek recovery measurements are separate from integrated-time contact tests.

Corrected v2 Actions[43897785827](https://github.com/badjoke-lab/evowild-test/actions/runs/43897785827) SUCCESS was independently confirmed. New v3 Actions status is **unverified**: the environment's API route returns403 and the connector cannot list push-triggered runs. The workflow uses the corrected lockfile-free install. [Access record](actions-status.json); do not interpret unavailable CI as a test success. Historical race PUSH/AGILITY failures were not rerun or modified.

## Real comparison evidence

[Paired viewer](compare.html), [capture provenance](capture-provenance.json), [video/frame validation](capture-validation.json). All videos are actual WebGL renders,24 consecutive frames/1× cycle,57.6fps (~.416667sec), no generated or interpolated images. The same v2 videos/120frames were reused byte-for-byte; v3 was recaptured after each meaningful visual revision. `pre-extension/` retains the rejected earlier v3 movies and phase images.

| Direction | v2 | Final v3 |
| --- | --- | --- |
| SIDE | [video](before-SIDE.mp4) | [video](after-SIDE.mp4) |
| FRONT | [video](before-FRONT.mp4) | [video](after-FRONT.mp4) |
| CHASE | [video](before-CHASE.mp4) | [video](after-CHASE.mp4) |
| LOW | [video](before-LOW.mp4) | [video](after-LOW.mp4) |
| REAR3/4 | [video](before-REAR_3_4.mp4) | [video](after-REAR_3_4.mp4) |

`frames/`:240 complete-cycle original screenshots. `dense/`:90 original matched images, all five views at .14/.20/.25/.28/.307/.32/.35/.40/.473. Unchanged v2 dense images were reused after final revision. `previews/` only crops/arranges those images for inspection.

Desktop[before](desktop-before.png)/[after](desktop-after.png), Pixel7 emulation[before](android-before.png)/[after](android-after.png). These are simulation-time browser captures, not physical Android performance measurements.

## Reproduce / resume

Start Vite on port4173. Run `python3 scripts/verify_s_d3c_v3.py`, the three specs `s-d3c-v3`, `s-d3c-recovery`, `s-native-join` with Playwright. Local config only selected installed Chromium and reused the server; thresholds unchanged. Authoring uses `python3 scripts/author_s_d3c_v3.py`; it reads immutable v2 and writes only v3.

For new evidence, use `CHROMIUM_PATH=/usr/bin/chromium D3C_VARIANTS=authored-v3 node scripts/measure_s_d3c_recovery.mjs`, `measure_s_d3c_join_extent.mjs`, and `capture_s_d3c_v3.mjs`. Do not rerun completed capture solely to resume. See HANDOFF and the review's concrete next unit. Main, production manifest, original GLBs, other species and unapproved R9 geometry were untouched; PR132 remains the separate parent lane.
