# Tripo S Motion Bench — Review Ledger

Branch: `exp/tripo-s-motion-bench-20261003`

Status: `T0_NOT_RUN`

Input: `public/models/evowild-s/focus-rigged-v5.glb`

Base commit: `d25553169e4406f5af660fc5559e075163aac6ff`

## T0 import / rig compatibility

Import result: `UNSET`

Four limbs intact: `UNSET`

Head / neck / tail intact: `UNSET`

Orientation usable: `UNSET`

Animation preprocessing result: `UNSET`

Export format: `UNSET`

T0 decision: `UNSET`

Allowed:

- `PASS_TO_T1`
- `REJECT_IMPORT`

Reason: `UNSET`

## T1 one-sprint gate

Prompt:

`maximum-effort forward quadrupedal sprint, explosive long stride, strong shoulder and pelvis drive, stable forward travel`

Raw artifact: `UNSET`

Normalized artifact: `UNSET`

### Measurements

| Check | Motion First v5 | Tripo T1 | Note |
|---|---|---|---|
| stance foot skating | UNSET | UNSET | UNSET |
| penetration / floating | UNSET | UNSET | UNSET |
| fore/hind phase coherence | UNSET | UNSET | UNSET |
| stride direction | UNSET | UNSET | UNSET |
| root / cadence match | UNSET | UNSET | UNSET |
| shoulder / chest drive | UNSET | UNSET | UNSET |
| pelvis drive | UNSET | UNSET | UNSET |
| spinal compression / extension | UNSET | UNSET | UNSET |
| neck / head follow-through | UNSET | UNSET | UNSET |
| tail behavior | UNSET | UNSET | UNSET |
| SIDE readability | UNSET | UNSET | UNSET |
| LOW readability | UNSET | UNSET | UNSET |
| CHASE readability | UNSET | UNSET | UNSET |
| FRONT readability | UNSET | UNSET | UNSET |
| export / replay stability | baseline | UNSET | UNSET |

T1 decision: `UNSET`

Allowed:

- `EXPAND`
- `KEEP_AS_REFERENCE`
- `REJECT`

Reason: `UNSET`

Exact next action: `RUN_T0`

## T2 full bench

Run only when T1 = `EXPAND`.

| Case | Rep | raw export | runtime replay | contact | phase | root/cadence | whole-body | multi-view | usable |
|---|---:|---|---|---|---|---|---|---|---|
| steady-run | 0 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| steady-run | 1 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| steady-run | 2 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| fast-gallop | 0 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| fast-gallop | 1 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| fast-gallop | 2 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| max-sprint | 0 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| max-sprint | 1 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| max-sprint | 2 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| launch | 0 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| launch | 1 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |
| launch | 2 | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET | UNSET |

## Final comparison

Motion First strengths: `UNSET`

UniMate strengths: `UNSET / NO_REAL_OUTPUT_YET`

Tripo strengths: `UNSET`

Contact correction required: `UNSET`

Speed remapping required: `UNSET`

Final decision: `UNSET`

Allowed:

- `PASS_TO_HYBRID`
- `KEEP_AS_REFERENCE`
- `REJECT`
