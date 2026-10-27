# D1-B — mesh-based rolling support, review-only candidate

D1-A was committed/pushed separately at `f14849675d02a66bbdeecba4db81136e9517d586` (checkpoint `5a7b661`) before D1-B. D1-B implementation checkpoint: `b7d8cf2`; final evidence follows that checkpoint. Completed 2026-10-27 JST. **Overall S animation: REVISE; no production promotion.**

Open `s-run-review.html?rig=contact-v3&toe=roll-v1`. Omit `toe` for the unchanged C1/C2 flat-contact baseline. This is a runtime-only opt-in candidate using the unchanged `focus-contact-v3.glb`. No GLB, source mesh, native clip, production manifest, ground, camera, race physics, Agent or HUD changes.

## Implementation and contact definitions

`src/s_toe_roll.js` derives a lower support envelope from the D1-A actual distal mesh vertices. These rigid terminal vertices have weight 1.0. Fore `_foot` and hind `_toe` terminal bones retain their existing distinct two-link/three-link chains. Rear/front refer only to the mesh's trailing/leading portions, not an assumed human or horse foot.

Early stance preserves the existing flat orientation (first 25% of fore stance; 45% of hind stance). Then the actual terminal bone rotates up to 22° fore / 28° hind, with IK joint translation compensating around the actual supporting vertex. Support moves forward only where two actual mesh vertices meet the ground. Both positions are continuous at that change. Each segment has zero angular velocity and acceleration at its boundaries; segment duration is proportional to the square root of its angular span. During the first 30% of swing, pitch returns smoothly along the same path. The C1/C2 distance/cadence integrator, persistent stance anchors, event splitting, velocity-preserving recovery target and zero-speed freeze are retained.

The instantaneous terminal orientation/translation comes from integrated phase, not a rate-dependent position reset. Support world coordinates are measured by independently skinning the selected vertex, not by trusting the IK target. A wider distal guard region includes blended vertices and detects penetration outside the rigid support group.

**Old definition retained:** `stanceSlip` / `legacyAllPatchMovement` is movement of the entire original B1 sole patch during declared stance. It now includes the intentionally rising rear part. It increases to roughly 0.8–4.7cm over these profiles and no longer measures only planted material. The old flat-mode tests and thresholds are unchanged and pass.

**New definition alongside it:** `supportSlip` accumulates horizontal displacement only while the same real support vertex remains active within one touchdown. A switch to a different vertex is a support transfer, not movement of the same planted material. The ground-plane error and vertex-switch/lift-off/landing continuity tests separately constrain those transitions. `FLAT_SUPPORT`, `TOE_SUPPORT`, and `SWING` durations/IDs/coordinates are recorded separately. “Flat” means the unchanged early-stance orientation; this irregular sculpt never places every sole vertex exactly on Y=0. No force distribution or physical center-of-pressure simulation is claimed.

## Measured comparison

[Full before/after per-profile summary](summary.json), [support vertex intervals](roll-descriptors.json), and fourteen `*-trace.json.gz` files preserve actual sole coordinates, surface minima, rear/front group positions, support points, pitch, IK residuals, joint angles, phase and integration state at 240Hz. Three steady rates (0.5/1/1.5) plus continuous acceleration/deceleration and two abrupt C2 profiles are included on both sides.

Worst values over all seven after profiles (slip is accumulated per profile, height in cm):

|Foot|Support slip mm|Penetration m|Rear-side rise cm|Minimum recovery peak cm|Command velocity residual m/s|Joint angles °|
|---|---:|---:|---:|---:|---:|---:|
|fore_L|0.000329|0|7.69|33.99|0.006870|102.39–155.07|
|fore_R|0.000269|0|7.38|33.99|0.007518|103.85–150.08|
|hind_L|0.000818|0|4.60|47.98|0.005987|48.67–158.68|
|hind_R|0.000703|0|4.92|47.98|0.004137|48.87–159.24|

All four feet: zero-time speed-switch jump **0**, IK reach error **0**, measured guard penetration **0**. Maximum support-plane error <0.001mm. Hind recovery remains 47.98–48.00cm, matching the flat baseline. Native segment lengths remain unchanged within floating-point tolerance. Pitch is measured from the actual distal mesh; its original small tilt is retained, so absolute pitch ranges are about −0.57→−22.57°, −1.14→−23.14°, −1.92→−29.92°, −2.31→−30.31°.

The maximum finite-difference velocity residual increased from baseline ~0.00599m/s to ~0.00752m/s, still below the existing 0.02m/s bound. This is a worse numerical residual, not an improvement to claim. Boundary probes at ±10µs cover support switches, lift-off and landing: max residual ~0.000670m/s, zero-time jump0, freeze0. Initial linear facet timing failed at ~0.031m/s; a first timing revision still failed ~0.0216m/s. The final square-root allocation fixes the failure without weakening thresholds. [Initial failure log](initial-velocity-failure.log).

## Browser evidence and visual judgment

All images are actual WebGL renders, not new art or mockups. 24 consecutive frames per view/baseline cover one native cycle from phase0.64, advancing simulation by 1/(2.4×24)s each frame. Eight MP4s encode these frames at57.6fps without interpolation. Idle animation callbacks are disabled only in the capture page; explicit runtime steps still update the skin and render each frame. These are deterministic simulation-time recordings, **not a realtime frame-rate or physical Android performance measurement**. Browser page errors:0.

|View|Before|After|Frames|
|---|---|---|---|
|SIDE|[video](before-SIDE.mp4)|[video](after-SIDE.mp4)|[before](frames/before-SIDE/) / [after](frames/after-SIDE/)|
|LOW|[video](before-LOW.mp4)|[video](after-LOW.mp4)|[before](frames/before-LOW/) / [after](frames/after-LOW/)|
|CHASE|[video](before-CHASE.mp4)|[video](after-CHASE.mp4)|[before](frames/before-CHASE/) / [after](frames/after-CHASE/)|
|REAR 3/4|[video](before-REAR_3_4.mp4)|[video](after-REAR_3_4.mp4)|[before](frames/before-REAR_3_4/) / [after](frames/after-REAR_3_4/)|

PC1280×800: [before](desktop-before.png) / [after](desktop-after.png). Pixel7 Chromium emulation: [before](android-before.png) / [after](android-after.png). Per-frame states: [visual-observations.json](visual-observations.json).

Inspected SIDE/LOW late fore support around frames03–05 and hind support/lift around17–20, plus CHASE/REAR3/4 and Pixel7. Compared with the flat baseline, the rear sole region rises and the tip carries support; the terminal foot no longer keeps a fixed pitch through push-off. The visible change is small at this fixed camera distance, especially on mobile and from behind. No new obvious inversion or foot fold appears in these samples. Body/neck shape and existing silhouette are retained.

|Aspect|Decision|Observed limitation|
|---|---|---|
|Actual mesh contact/support transfer|KEEP for isolated diagnostic candidate|Ground and same-vertex slip gates pass; physical pressure/load distribution is not modeled.|
|Toe roll / push-off|REVISE visually|Heel-side lift is visible, but the staged mesh-facet rolling has zero-speed points and can read as mechanical; it does not yet convey strong propulsion.|
|Recovery|KEEP for preserved contact regression; REVISE overall|~48cm hind recovery is retained; broader body/limb coordination remains from C1/C2.|
|Flight / extension / rear-quarter running|REVISE|Weight acceptance and full-body propulsion are still insufficient; deliberately outside D1 scope.|
|Canonical appearance / race readiness|REVISE|Unchanged gray/faceted inherited candidate, unresolved silhouette/detail issues; no approved production sprite or 18-runner integration.|

No global visual KEEP follows from test success. The newly introduced tradeoff is visible terminal rotation with multiple facet-wise easing intervals; assess a less mechanical support roll before broader weight-transfer work. Do not hide it by moving the camera/ground/model.

## Validation and restart

- D1-A:2 dedicated PC/Pixel7 cases PASS; separate evidence directory.
- D1-B plus unchanged C1/C2: **8/8 PASS** in5.4m. [test log](targeted-tests.log). All seven profiles on both devices; boundary/freeze checks; no old threshold changes.
- Production build PASS, existing bundle-size warning only. [build log](build.log).
- Baseline Actions40370002226: user-reported124passed /3knownfailed /81skipped. Known failures are race-quality PUSH (both devices) and desktop Motion First AGILITY. Intermediate D1-B Actions40433832747 was still running when this evidence was written; build step passed. Final remote CI status is recorded in HANDOFF_STATE; do not infer a green full suite from local checks.
- Preserved source GLB/v1/v2/v3 hashes: [asset-integrity.json](asset-integrity.json).

Reproduce with `CHROMIUM_PATH=/usr/bin/chromium node scripts/measure_s_toe_roll.mjs`, `node scripts/capture_s_toe_roll.mjs` (same environment variable), and `npx playwright test tests/s-toe-roll.spec.js tests/s-contact-transitions.spec.js tests/s-contact-acceleration.spec.js`. Start the existing Vite preview/dev server at4173; the workspace's local config points to system Chromium.

D1 implementation and bounded verification are complete. Next session: fetch remote/read HANDOFF, inspect D1 SIDE/LOW/REAR videos with `?rig=contact-v3&toe=roll-v1`, and review the remaining mechanical roll before any separately authorized weight-transfer/flight/extension unit. Do not repeat D1-A, C1/C2, or regenerate/modify GLBs.
