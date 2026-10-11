# P 2.5D world support-band movement audit

**Status:** research measurement only. No edits to the 12-frame P asset or default visual cadence behavior.

Measure the real RGBA image's contact band (alpha >12 on canvas rows 291–295, grouped into foot-like bands) for each phase. For contact phases [1,2,3,4,10,11,12], estimate its projected world location using the selected creature's actual race distance, asset pixel band centre, renderer sprite draw width and camera metres-per-pixel. Sample 200 deterministic 33 ms intervals in each of baseline and distance-locked phase-clock mode. Record same-pose contact-band travel and comparison graph.

**Limits:** the most-forward band is not a verified anatomical foot ID; phase transitions can switch feet, and the 2.5D bitmap can move as one piece. It is a stance-support proxy, not genuine contact IK or a proof that slip is fixed. Do not promote either cadence policy merely because this audit passes.

Reference `public/concept/P.webp`, P run-sheet, S/E/A, main and 3D remain unchanged.
