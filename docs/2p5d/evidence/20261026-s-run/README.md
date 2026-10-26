# S native run: first bounded unit (2026-10-26)

**REVISE. Do not extract/promote this motion into 2.5D racing or expand to P/E/A/18 runners.**
User superseded the side-sprite camera/scale task: inspect actual S skin animation first.

## Runtime and evidence

Open `/evowild-test/s-run-review.html` after `npm run dev`. This isolated one-S WebGL review loads the actual canonical `public/models/evowild-s/focus-rigged-v5.glb`, 38,813 vertices / 19 bones / native `EvoWild_S_Run_V5` clip (1.0416666s). No procedural creature fallback, no image deformation, no regenerated artwork. SHA-256 `e879cae6835f405f93787b96dfbcc1858ff540dadaf12988d549d56d922362a2`. Shape source `source-lod2.glb` stays unchanged (`ff68f2b02c36609f5f64a59b7490a5cf66be91f9b4b4da017a5e44901a583bdf`). Canonical reference: `public/concept/S.webp` and `docs/references/evowild-creature-reference-sheet-20260921.jpg`; Motion First standard and prior Phase B/C rejection reviews were read.

- [SIDE frames](aligned/SIDE), [CHASE frames](aligned/CHASE), [LOW frames](aligned/LOW), [REAR 3/4 frames](aligned/REAR_3_4): 12 consecutive, evenly spaced native clip phases per direction, real Chromium 960×640 screenshots.
- [Native observations](aligned/native-observations.json): RAF animation/time/translation advances before capture, then deterministic native animation sampling; no browser errors.
- [Initial alignment evidence](../20261025-s-native-run): previous yaw=180° showed the front in cameras labelled rear. **Those initial labels are incorrect.** The isolated review now uses yaw=0°: observed mesh head points +Z and follows +Z motion. Manifest's -Z assumption is not silently rewritten. Corrected rear images show the tail/haunches nearest camera.
- Cyan/orange points observe fore/hind **bone weight groups**, not guaranteed anatomical toes. Initial evidence footer's “足先観測” was inaccurate and is corrected in current runtime. Zero fore-foot weights fall back to lower-leg groups, explicitly exposed in JSON; orange hind-foot weights visibly deform the upper body.

Reproduce (dev server port 4173): `CHROMIUM_PATH=/usr/bin/chromium node scripts/capture_s_run_review.mjs`. Set CHROMIUM_PATH only when using system Chromium. Skin inspection: `python3 scripts/inspect_s_glb_skin.py public/models/evowild-s/focus-rigged-v5.glb` (NumPy required).

## Shape / rig / motion findings

| Area | Observed problem | Decision |
| --- | --- | --- |
| Shape/identity | Original mesh bytes preserved; gray untextured model and split crest differ from blue/white formal S reference. Do not redesign or use optional headfix as a shortcut. | REVISE; no shape editing in this unit |
| Rig | Both fore-foot bones have **zero** influence. Hind-foot groups appear at neck/head height. Bind-space head is at Y=-0.582, while actual head is above the body: skeleton/mesh coordinate spaces require correction. [Weight report](native-weights.json). | REVISE; repair bind alignment and weights before judging native gait |
| Motion | SIDE shows rigid/sliding legs and large chest/neck deformation; LOW/REAR show leg overlap and insufficient recovery. Foot-to-ground penetration/hover occurs. Contact → push → recovery → flight → extension does not read as a valid gallop. | REVISE; no 2.5D sprite export |
| Runtime | Actual skin deformation, world movement and follow views implemented. Speed 0 freezes animation/translation; 0.5×/1×/1.5× scale both. 4m/s is an isolated diagnostic value, not a race specification. | Functional proof only; speed-scaling does not prove contact quality |

Mock01 calls for a readable rear-quarter sprint. These captures establish the correct observation direction, but **do not meet its running quality**. Native clip is not usable for production extraction. No race physics, agent, HUD, saved results, source GLB, reference image or hash changed. Prior v31 rejection and procedural Phase B/C acceptance are not evidence of this asset passing.

Next bounded unit: correct skeleton/mesh coordinate alignment and reweight an isolated candidate while preserving the original vertex/index bytes; rerun these four views and contact diagnostics. Keep originals/manifest untouched. A clip-loading test is not visual KEEP.
