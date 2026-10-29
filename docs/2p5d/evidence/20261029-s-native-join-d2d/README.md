# S D2-D — original WebGL motion evidence

These videos and images are unretouched WebGL captures from the existing candidate GLB, camera and lighting. No rendered or generated creature substitute was used.

- **Before:** `s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v2`
- **After:** `s-run-review.html?rig=contact-v3&toe=roll-v3&body=push-v3`
- **Normal full cycle:** `before-{SIDE,CHASE,LOW,REAR_3_4}.mp4` and matching `after-*.mp4` at 57.6fps, 24 real frames per native cycle. Complete frame PNGs are included under `frames/`.
- **Dense join:** `before-*-join-slow80x.mp4` and `after-*-join-slow80x.mp4`, 17 real WebGL frames at phases .632 through .648, .001 per sample, displayed at 30fps (80x slow). No in-between frames synthesized.
- **Still comparisons:** `before/after-*-phase-{632,638,640,642,648}.png` at identical view/phase.
- **Device emulation:** `desktop-before/after.png`, `android-before/after.png`; Pixel 7 is emulated, not a physical Android test.
- **Raw readings:** `join-observations.json`, `visual-observations.json`, `focused-test.log`.

**Gate:** D2-D numerical continuity scoped KEEP from prior measured tests; overall S visual-quality REVISE pending human review of these real videos. This pipeline does not claim qualitative acceptance, physical Android runtime, or production integration. GLB, race manifest, main and unrelated stages unchanged.
