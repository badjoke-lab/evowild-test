# EvoWild Run — Kimodo / ARDY Motion Feasibility v0.1

Status: **isolated experiment / not a production dependency**

Branch: `exp/kimodo-ardy-motion-feasibility-20261004`

Base main: `475e1ff6c1e047b227fa400215714994edc40368` (2026-10-04)

## 1. Purpose

Evaluate whether NVIDIA Kimodo or ARDY can materially improve EvoWild Run motion work without weakening the existing Motion First lane.

This experiment is intentionally isolated. It must not overwrite or redefine:

- `public/preview-motion-first/`
- the accepted Motion First gait/contact behavior;
- S creature geometry or rig assets;
- race director behavior already merged to `main`.

The experiment is successful only if it produces a measurable motion benefit that can be transferred safely into EvoWild's quadruped controller.

## 2. Current upstream facts

### Kimodo

Kimodo is an offline controllable motion-generation system. The public release supports text plus kinematic constraints including root paths/waypoints, full-body keyframes, and sparse joint/end-effector constraints.

Released skeleton families are human/humanoid-oriented: SOMA, Unitree G1, and SMPL-X. The current repository does not provide a documented supported workflow for training an EvoWild custom quadruped checkpoint.

Kimodo can export BVH. It is therefore useful as a motion-authoring/reference source, but not as a drop-in S-creature runtime animator.

### ARDY

ARDY was released by NVIDIA in July 2026 as an autoregressive real-time motion-generation system related to Kimodo. It supports streaming text prompts, target velocity / waypoint locomotion control, root paths, full-body keyframes, and sparse joint constraints.

Released checkpoints currently cover Core and Unitree G1 skeletons. The public README says SOMA support is coming soon. No released EvoWild-style quadruped checkpoint exists.

ARDY is the more relevant upstream for game-runtime research because it is explicitly interactive and autoregressive. Kimodo remains the stronger offline authoring/reference baseline.

## 3. Direct-use decision

### Current decision: **NO-GO for direct S quadruped animation**

Do not:

- retarget a humanoid pose sequence directly onto the S quadruped and call it solved;
- replace the current S gait/IK/controller with Kimodo or ARDY;
- add either framework to the production web runtime;
- add GPU inference as a gameplay requirement;
- claim quadruped support that the released models do not provide.

The useful question is narrower:

> Can Kimodo/ARDY produce root-motion, cadence, stance timing, acceleration/deceleration, and turning signals that improve the existing EvoWild controller?

## 4. Experiment gates

### Gate K0 — Environment and upstream sanity

Required:

- confirm CUDA-capable NVIDIA test host;
- confirm Python/PyTorch compatibility;
- confirm model license selected for the checkpoint;
- confirm text-encoder access where required;
- keep all generated artifacts outside production paths.

Use:

`python scripts/kimodo-ardy/check_environment.py`

PASS means a suitable external GPU host is identified. A non-NVIDIA development machine is valid for authoring and analysis but does not count as an inference PASS.

### Gate K1 — Kimodo offline baseline

Use a SOMA RP checkpoint.

Generate and export at least these source motions:

1. steady forward sprint;
2. acceleration into sprint;
3. deceleration from sprint;
4. curved / waypoint-controlled run;
5. lateral direction change.

Required outputs:

- source prompt/constraint config;
- generated motion;
- BVH export;
- short visual capture.

Do not retarget to S yet.

### Gate A1 — ARDY interactive baseline

Use a released Core or G1 checkpoint.

Test:

1. steady target velocity;
2. live speed increase/decrease;
3. waypoint turn;
4. left/right steering;
5. prompt transition while locomotion continues.

Required outputs:

- checkpoint and acceleration mode;
- hardware;
- native FPS;
- replanning settings;
- exported session/motion;
- capture proving continuous generation.

PASS requires stable interactive generation on the test host. It is not enough for one short clip to render eventually.

### Gate B1 — Signal extraction, not pose retargeting

Extract only transferable motion descriptors:

- root forward speed;
- acceleration/deceleration curve;
- heading / turn rate;
- step cadence;
- stance and recovery timing;
- left/right phase relation;
- vertical center-of-mass rhythm;
- turn-entry and turn-exit timing.

Map these descriptors into the existing EvoWild quadruped controller as parameters/targets.

Do **not** map humanoid joint rotations directly onto S bones.

### Gate C1 — Motion First A/B comparison

Compare against current `main` Motion First S behavior.

Required views:

- SIDE;
- LOW;
- CHASE;
- FRONT or front 3/4;
- dense-pack context when relevant.

A transfer candidate is KEEP only if it improves at least one of:

- visible planted-foot stability;
- acceleration/deceleration readability;
- turn/lane-change body timing;
- cadence/stride transition quality;
- motion variation without loss of species identity;

and does not degrade the others.

If no clear improvement survives visual review, close this lane with **NO INTEGRATION**.

## 5. Hardware rule

Kimodo and ARDY are CUDA/NVIDIA-oriented research stacks. This repo must not assume that the normal EvoWild development machine can run inference.

Use external GPU compute only for the isolated generation experiment. Generated motion data may be brought back into the repository only after license and quality review.

Production EvoWild remains browser/runtime independent of Kimodo/ARDY.

## 6. License rule

Code licenses and model/data licenses are separate.

Before retaining any generated artifact, record:

- upstream repository commit;
- checkpoint exact name/version;
- checkpoint license;
- training-data license statement supplied by the publisher;
- whether commercial use is permitted for the selected checkpoint/data.

Do not generalize the Apache-2.0 code license to model weights or datasets.

## 7. Upstream references

- Kimodo: https://github.com/nv-tlabs/kimodo
- ARDY: https://github.com/nv-tlabs/ardy

## 8. Next execution point

The next real execution is **Gate K0 on an NVIDIA GPU host**.

Until that exists, the only valid work in this branch is:

- environment probing;
- test-case definition;
- import/export tooling;
- evaluation tooling;
- upstream compatibility review.

No claim of generated EvoWild motion is permitted before K1/A1 artifacts exist.
