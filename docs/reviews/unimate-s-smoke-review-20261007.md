# UniMate S Smoke Review — 2026-10-07

Branch: `exp/unimate-s-motion-bench-20261001`

Source generation run: `37260023741`

Postprocess run: `37497922470`

Generated asset commit: `03bdd46d49a0fb2ab027de0bf9e1c4db184cf512`

Input: `public/models/evowild-s/focus-rigged-v5.glb`

Checkpoint: `Linzhan/UniMate/unimate_uniml3d_f60_v2/checkpoint_step_100000.pt`

Prompt: `An object runs forward at a steady athletic pace with coordinated four-limb locomotion.`

## What is now proven

- EvoWild S custom-rig preprocessing succeeds.
- The S rig is accepted as an 18-joint custom topology after UniMate canonicalization.
- Explicit facing resolution succeeds.
- The released v2 checkpoint can sample the S topology on a free GitHub Actions CPU runner.
- A real 60-frame / 30 fps generated motion was produced.
- The generated `.npy` can be driven back onto the canonicalized S rig and exported as an animated GLB.
- Review artifacts are durable in `public/unimate-bench/smoke/`.

This closes the basic feasibility question. UniMate is not blocked by the S topology.

## Smoke quality result

Current decision: **KEEP_AS_REFERENCE / NOT PASS_TO_HYBRID YET**

The first steady-run sample is not strong enough to replace or augment Motion First v5 yet.

Measured vertical excursion of generated feet versus the current v5 source clip:

| foot | UniMate smoke span | current v5 span | ratio |
| --- | ---: | ---: | ---: |
| fore_L | 0.2797 | 0.5696 | 49.1% |
| fore_R | 0.2989 | 0.5547 | 53.9% |
| hind_L | 0.0523 | 0.4967 | 10.5% |
| hind_R | 0.0646 | 0.5052 | 12.8% |

The rear-limb excursion is especially weak in this sample. That is consistent with the review animation: it moves, but it does not yet read as a convincing full-body race gait.

Other smoke diagnostics:

- generated root XZ net travel: `0.1512`
- generated root XZ path length: `0.3523`
- generated root vertical span: `0.0437`
- current v5 is authored essentially in-place, so root travel is not a direct quality comparison.

The generated foot low-phase speeds are also inconsistent across limbs. This means the smoke clip must **not** be marked contact-safe.

## Interpretation

Do not reject UniMate from one sample. The pipeline works; prompt/sample quality is the unresolved issue.

The next gate is a small prompt-diversity bench, not a 12-sample full bake:

1. steady run
2. fast gallop / bound
3. maximum sprint
4. explosive launch

One sample each, same S topology, same checkpoint, same seed family.

If none of those four produces materially stronger rear-limb and whole-body motion, stop this lane at `KEEP_AS_REFERENCE`.

If at least one is clearly stronger, expand only that motion family to three repetitions and compare against Motion First v5 before any runtime integration.
