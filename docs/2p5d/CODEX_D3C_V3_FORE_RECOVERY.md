# EvoWild Run — D3-C v3 focused fore-recovery authoring (Codex execution unit)

## Starting authority (17 November 2026)
- Repository: `badjoke-lab/evowild-test`, isolated branch: `exp/d3c-scapula-authoring`. **Fetch current remote HEAD before edits**.
- Preserve the existing `d3c-scapula-author-v1.glb` and `d3c-scapula-author-v2.glb` and D3-B/D2-D production-independent baseline, manifest, main, and the still-Draft PR #132 branch.
- Read `docs/2p5d/HANDOFF_STATE.json`, `docs/2p5d/evidence/20261117-s-d3c-v2/VISUAL_REVIEW.md`, `articulation-summary.json`, `contact-summary.json`, and actual `frames/after-{SIDE,REAR_3_4}/` + `previews/{SIDE,REAR_3_4}.jpg`; inspect v2 code in `scripts/author_s_d3c_v2.py`, `src/s_authored_drive.js`, `src/s_contact_ik.js`, `src/s_run_review.js`.
- v2 report commit `21b42bbb98fbe6b1da744fcd811d5fec0e83f563`. In locally captured tests, **16 passed**. Five paired original WebGL videos and 240 frames are already saved; **do not recreate them merely to rediscover the same defect**.
- Actions for prior commit `995f9ea` actually failed **before tests**, because `npm ci` found no package-lock. Fixed workflow install to `npm install --no-package-lock` in `9689bbbc161dd0a82a8818ec513abd6b857cf5a2`. Check its new Actions result independently; do not confuse old CI failure with new S test regressions.

## Measured visual defect and scope
The `v2` authoring added 23-joint shoulder rig animation with scapula glide and rotation, humerus advance, elbow recovery, pelvis/spine/chest loading. It is technically stable but remains visually **REVISE**.

In the same-camera actual captured full-cycle frames, at global phase **.14** (frame12) the fore recovery rises; around **.307** (frame16) both fore feet collect directly below the chest; by **.473** (frame20) they extend again. This appears in SIDE and REAR 3/4 and is *not* resolved by stronger overall amplitude. The trunk/head still look too upright from the rear three-quarter view.

At 1× diagnostic phase seeks:
- minimum elbow angle v1: L ~96.50°, R ~91.69°; v2 L ~62.39°, R ~54.29°. This is **considerably tighter**, though the project mechanical limit is broader.
- fore shoulder travel relative to root v1 3.60 cm; v2 L16.49 cm / R19.25 cm.
- actual 1× v2 max fore recovery height around 63.7–65.4 cm across integrated profiles. A higher lift alone is not a better gallop.
- v2 pelvis/chest angular ranges ~3.44° / 4.01°, head ~2.70°; rear drive still weak at game size.

## Execute D3-C v3 (not just another plan)
1. **Diagnose cause before modifying animation.** Quantify both fore-foot skinned-vertex trajectories relative to chest, global/root z, inter-forefoot 3D distance and projected screen-space overlap at phases `.14,.20,.25,.28,.30,.32,.35,.40,.47`, distinguishing (a) authored `fore_*_upper/lower` FK swing guide, (b) D3-B existing `foreReach`, and (c) existing contact IK targets. Log fore support/swing stage, elbow angle, shoulder position and phase offsets. Check the two-pass IK in `pose()` (first contact solve then `swingGuides`, then second solve): determine whether it contributes to cramping before changing it. Measure v1 vs v2 under identical view/camera.
2. **Author one physically bounded recovery-path/timing hypothesis** as a new opt-in `d3c-scapula-author-v3.glb` + `shoulder=authored-v3`. Keep v1 and v2 byte-identical. Rephase left and right fore recovery as required by measured support offsets (do not arbitrarily change stance anchors); avoid both feet simultaneously collapsing beneath the sternum. Blend the elbow fold and shoulder glide so that fore lift spreads across .14–.47 and transitions smoothly to extension. Do not simply raise forefoot height or increase humerus/elbow rotation amplitudes. Preserve original rig/rest topology and identity.
3. The swing guide must have at least **continuous position and velocity** at its entry/exit and on abrupt effective-rate changes. **During stance, do not apply authored foot offsets.** Keep anchor world-locked and solve contact after authored shoulder/chest pose. No global bob, viewpoint change, generated lookalike images, fake interframes or ignored failures.
4. Test locally first: exact sole skin vertices and toe-roll under `.5,1,1.5` speed, acceleration, deceleration, abrupt fore/hind switches; `dt=0` repeatability; no new IK reach error, penetration, zero-time jump or slipped planted sole, and hind recovery preserved. Retain current limits (<1 mm supported slip/gap/jump, <.02m/s sole velocity residual, existing joint bounds) **without relaxing thresholds**. Re-run only tests affected by the change plus original-vs-v2 conservation; CI can validate independently.
5. **Before/after actual WebGL comparison** of v2 vs v3: SIDE/FRONT/CHASE/LOW/REAR_3_4, complete same-speed real 1× cycle plus dense same-phase stills `.14,.20,.25,.28,.307,.32,.35,.40,.473` in SIDE and REAR 3/4. Include desktop and Pixel 7 emulation only as emulator, not a physical-device performance claim. Inspect normal-speed actual video if available; say explicitly if only frames were seen.
6. Save a new, separate `docs/2p5d/evidence/20261117-s-d3c-v3/` package containing GLB SHA, source-pose integrity, trajectory analysis, original/synth-free frames, five paired real videos, test logs, and KEEP/REVISE visual decision. Commit/push to the *same experiment branch*. Update `HANDOFF_STATE.json` and verify remote; keep PR #132 Draft/unmerged and main untouched.

## Quality gate
The v3 candidate is **not** adopted merely because it passes regression tests or spreads the fore feet apart numerically. It must show recognizably better chest–shoulder–elbow timing, readable separate forelimbs at .25–.35 (SIDE, REAR 3/4), and an improved hind-push-to-chest visual sequence. If not, keep v2 and declare REVISE, identifying the actual physical/rig limitation rather than adding another cosmetic sinusoid. The creature’s canonical S model remains independently unapproved; do not assert that this experiment fixes R9/Blender silhouette.

## Expected final report
- new remote SHA and files changed; exact v2 preservation evidence
- root-cause measurements and one specific tested recovery-path hypothesis
- regression test passes and failures (separate local from Actions)
- actual 5-direction v2-v3 video links and phase stills
- visual-quality verdict with exact remaining defect
