# P 3D v6 — independent actual-image review (2026-10-12)

**Overall shape: REVISE / production HOLD.** Keep only as a versioned research candidate. No automatic merge, race integration or completion claim.

## Evidence lineage

- Canonical authority: `public/concept/P.webp`, unchanged.
- Previous: `p-canonical-v5.glb`, SHA-256 `07cb11db521956de5e8e82d0871977b2fb7a9e56b67934789f74b54710efc820`.
- New: `public/models/evowild-p/p-canonical-v6.glb`, SHA-256 `b21685fc6e0cb2c70cb42bb693cbad96f8fb659a6d3f0587220e7e06cc5da036`.
- 73,448 authored triangles, 2,604,556 bytes, 17 bones. The same counts as v5 do **not** mean it is the same GLB; binary hashes differ.
- The **first** v6 screenshots at commit `101fb5207` mistakenly loaded v5 because the capture script default was `v5`. Those early screenshots are **invalid for v6 visual review**.
- Recapture workflow `38151136812`: SUCCESS. Correct v6 screenshots, comparison and 4-cycle run footage committed as `4047a3231997e2983c998ce56c42a74c3e83e28a`.
- Correct evidence: `comparison-canonical-v5-v6.png`, `SIDE.png`, `FRONT34.png`, `FRONT.png`, `REAR34.png`, `BACK.png`, `running-review.mp4`, `running-contact-sheet.png`, `browser-validation.json`, `topology-check.json`, `gltf-validation.json`.
- Browser capture now checks that the status label contains the exact requested asset version, preventing future silent v5 reuse.

## Visual results: P.webp vs v5 vs actual v6

| Area | Visible finding | Assessment |
| --- | --- | --- |
| Scapula and upper arm | v6 adds a real raised shoulder and tapered muscle ridge on the joined skin, slightly strengthening the upper arm silhouette. | **Partial improvement** over v5 locally |
| Chest-to-shoulder anatomy | Still reads as a straight hanging block from a rounded shoulder. Canonical P has more distinct, interlocking, structurally plausible red/slate muscle forms. | **REVISE / major blocker** |
| Thorax to waist | Long, smooth, tapered red dorsal surface; canonical is high-chested with individually readable shoulder and flank masses. | **REVISE** |
| Head / crest / tail | Inherited simplified muzzle, separate crest blades and tail details remain materially different from the canonical drawing. | **REVISE** |
| Feet / running | The 6.4 second four-cycle footage is real GLB rendering, but the run is a minimal in-place loop with no tracked world-space foot lock or production 18-runner verification. | **NOT APPROVED** |
| Other viewing angles | Front and back are informed guesses because the available highest reference is primarily a three-quarter pose. | **UNVERIFIED where no canonical view exists** |

## Engineering checks (not shape approval)

GLTF validator errors=0, warnings=0. One connected anatomy component (24,074 vertices), boundary edges=0, non-manifold edges=0, 13,011 vertices with blended skin weights. Desktop 5-view and emulated Pixel 7 SIDE/FRONT34 screenshots captured with no browser errors or failed requests. Correct v6 film is 6.4 s / 192 frames / 4 cycles per SIDE and FRONT34 view.

## Decision — change modeling method, not just another radius

Further iterative numerical bulges on the v5/v6 procedural solid are not justified: v6 changes the shoulder surface but remains visibly distant from the canonical P. **Do not blindly schedule another parameter-tuning v7.** Next modeling experiment should prioritize an artistically guided, reference-anchored silhouette and major muscle planes in Blender, with separately marked inferred views. It must review static shape before advancing rig/locomotion. Preserve existing approved/reference assets; do not switch the 18-runner game.

**KEEP** the separated GLBs, reproducible captures, and connected topology research. **REVISE** anatomical match and foot-lock. **HOLD** production adoption.
