# EvoWild S original-QEM 13-bone stride extension V4 (2026-10-10)

**Motion-only verdict:** `PASS_LIMITED_THREE_CYCLE_IK` at 0.080 world units per cycle, with 3 alternating-diagonal cycles, 49 keyed integer samples, 48 half-frame samples, original 29,948 vertices/59,932 faces and 13 deform bones. **S-type visual gate: REJECT. Production S: 0.**

## Immutable authority

The exact canonical `art/s-creature/references/00_s_type_modeling_image_v1.png` has SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6` and CI confirms this SHA. TRELLIS2 original QEM donor GLB SHA-256 `e440263d0204fcf33a4cc6fc5c84b5390d766d6ffb570abd4ac614cbc7cdc92f`, unchanged. Never substitute R0/R1 or alter production main.

## Tested ladder (3 cycles each)

| World root travel / 16-frame cycle | Test gate | Reason |
| ---: | --- | --- |
| 0.192 | FAIL | Evaluated mesh deformation condition violated |
| 0.160 | FAIL | Evaluated mesh deformation condition violated |
| 0.144 | FAIL | Evaluated mesh deformation condition violated |
| 0.128 | FAIL | Evaluated mesh deformation condition violated |
| 0.112 | FAIL | Evaluated mesh deformation condition violated |
| 0.096 | FAIL | Evaluated mesh deformation condition violated |
| 0.080 | PASS LIMITED | All recorded contact, triangle and 3-cycle seam checks passed |

At 0.080, total body-world travel = 0.240 (9.41% of body height 2.55 over 3 cycles). Max grounded patch XY error = **0.00000206** world units; max evaluated triangle area ratio = **1.76796** (cap 2.0). Cycle rest pose max relative mesh seam difference = **7.82e-7** world units. The *tested* safe boundary is in the bracket 0.080 PASS versus 0.096 FAIL, **not a proven continuous monotonic mathematical maximum**.

Real detailed evidence is in `stride-extended-ik-v4/REAL_THREE_CYCLE_IK_QA.json`, `stride-extended-ik-v4/S-QEM-13bone-stride-extended-v4.blend`, and `stride-extended-ik-v4/review/` (genuine one-cycle GIF, original vs pose five-direction renders and authority reference preview). Actions [38030551237](https://github.com/badjoke-lab/evowild-test/actions/runs/38030551237) succeeded.

## Critical separate morphology decision

The actual V3 source/pose 5-view comparison under `QEM_V3_ACTUAL_FIVE_VIEW_SHAPE_GATE.md` rejected the torso and tail and required limb/head-crest revisions. Increased locomotion numerical pass **does not override** that rejection. The longer armor-plated fan tail and more muscular/even torso of the actual S authority are missing in the original QEM. Workbench gray does not test materials, so do not assert color mismatches from the renders.

## Next gate

1. Preserve donor and V4 animated blend immutable; morphology repair only on an independently named trial asset and only after actual five-view observation.
2. Evaluate tail geometry region first (existing vertices-only A variant, no claim it can create segmentation). Preserve failed variants.
3. Diagnose *which triangle IDs* fail at >0.080 before targeted joint weights or local deformation topology revisions. Face count alone is insufficient for repair.
4. After a morphology trial actually passes visual review, re-run rigging, foot contact, half-frame and 3-cycle audit on that changed asset. No reuse of old PASS across altered geometry.
5. Production approval requires five-view canonical resemblance, credible anatomy, meaningful gallop mechanics, 18-creature game benchmark and frame stability. Not yet achieved.
