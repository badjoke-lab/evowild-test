# EvoWild Run — UniMate S Motion Bench v0.1

Status: **isolated experiment / not production-approved**

Branch: `exp/unimate-s-motion-bench-20261001`

Base branch: `feat/simplified-race-finish-review-v1-20261001`

Base commit: `a9636e027be9a85e650a0588cb0d344514e69525`

UniMate upstream pin: `Friedrich-M/UniMate@2c5b384715aa63d8639b1ed7eb74bfe614570c7a`

## Purpose

Determine whether UniMate materially improves whole-body locomotion for the current Motion First S runner without weakening the existing foot-contact / speed-matching work.

This is a separate lane. It does not modify the accepted Motion First runtime, the S modeling lane, Sakura, Sprite, 2.5D, or Hunyuan experiments.

## Input lock

Use:

`public/models/evowild-s/focus-rigged-v5.glb`

Reason:

- it is the current near-camera Motion First S runtime asset;
- it has the accepted 19-bone rig family used by the current lane;
- v31 is explicitly rejected for Motion First motion quality and must not be substituted here;
- geometry quality is not being judged in this experiment.

Do not use the rebuild/modeling-lane S asset until its own shape gate is approved and it has a compatible rig.

## What the current UniMate release actually supports

At the pinned upstream commit:

- custom-rig preprocessing exists through `run_preprocess_char.sh`;
- it can emit a canonicalized rig, `cond.npy`, and motion feature NPZs;
- generated feature NPZs can be applied back to the canonicalized rig with `run_animate_lbs.sh`;
- the public inference CLI still builds its target skeletons through the dataset loader and does **not** expose a direct `--cond_path` argument.

Therefore this bench does **not** pretend there is already a one-command arbitrary-rig inference path.

The bench uses an isolated compatibility bridge:

1. preprocess the EvoWild S asset into a standalone feature directory;
2. copy the released checkpoint config;
3. keep the released model architecture, checkpoint and normalization statistics unchanged;
4. point the config's existing `objaverse.path` slot at the isolated EvoWild feature directory;
5. set `dataset.dataset_list=["objaverse"]` only for this inference copy;
6. sample the EvoWild object type discovered from its generated `cond.npy`;
7. drive the canonicalized S mesh with the generated feature motions.

This is an experiment-side routing workaround, not an upstream patch and not a production dependency.

## Motion set

Generate three repetitions for each prompt:

- steady forward run;
- fast gallop / bound;
- maximum-effort sprint;
- explosive acceleration from a low start.

Prompts must describe motion only. Do not describe appearance, species lore, camera work, race UI, color, or environment.

## Required outputs

The experiment must produce:

- the canonicalized S GLB from UniMate preprocessing;
- `cond.npy`;
- generated feature NPZs for every prompt / repetition;
- animated GLBs driven by those generated motions;
- a result ledger using the review template in `docs/reviews/unimate-s-motion-bench-review-template.md`.

A later commit may add a browser compare page only after real generated GLBs exist. No mock comparison page is allowed.

## Review gate

Review the generated motions against the current Motion First v5 baseline.

Check all of the following:

- foot skating during stance;
- foot penetration / floating;
- fore/hind phase coherence;
- stride direction;
- root travel vs leg cadence;
- shoulder/chest contribution;
- pelvis drive;
- spinal compression / extension;
- neck/head follow-through;
- tail behavior;
- launch posture;
- high-speed readability from SIDE / LOW / CHASE / FRONT;
- loop seam if the clip is looped;
- repeatability across three samples.

Decision values:

- `PASS_TO_HYBRID` — UniMate body motion is clearly useful; retain/restore EvoWild contact correction and speed matching on top.
- `KEEP_AS_REFERENCE` — some useful whole-body ideas, but not usable as runtime motion.
- `REJECT` — no material improvement or severe topology/contact failures.

Do not mark UniMate as the production animation solution from a skeleton preview alone.

## Hybrid target if the bench passes

The intended runtime architecture is:

`UniMate whole-body clip -> EvoWild contact correction / foot locking -> speed-to-cadence matching -> race-state blending -> Three.js runtime`

UniMate does not replace Race Engine movement, camera direction, or Agent decisions.

## Execution

Use:

`scripts/unimate/run-evo-s-bench.sh`

The script intentionally requires an already prepared UniMate environment and released checkpoint directory. It does not silently start paid GPU infrastructure.
