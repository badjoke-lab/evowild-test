# EvoWild S — QEM five-view visual gate (2026-10-10)

**Decision: REJECT for final S morphology.** This is independent of the 13-bone IK limited PASS. The visual comparison uses actual Blender renders, not generated stand-ins.

## Canonical locked authority, source and evidence

- **ONLY canonical S picture:** `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA-256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`. Restored to this experiment as the **identical Git blob** from `exp/s-creature-vibe-modeling`; CI runs `sha256sum --check`.
- Preserved original donor: `art/s-creature/experiments/trellis2-pixal3d/candidates/trellis2-seed0000/t2-qem-repair/S-trellis2-qem-repair-best.glb`. No R1/R0 substitution.
- Original real geometry and real weighted rig: 29,948 vertices, 59,932 triangular faces, 13 deform bones.
- Source-and-frame13 real five-view contact sheet: `stride-ladder-ik-v3/review/QEM_V3_REAL_FIVE_VIEW_BEFORE_AFTER.jpg`. The 5 matching actual views are SIDE / FRONT / FRONT34 / REAR34 / BACK.
- Full authority alongside actual renders: `stride-ladder-ik-v3/review/SOURCE_AUTHORITY_IMAGE_REVIEW_ONLY.jpg`, copied from the hash-checked actual S reference.
- Both source and animated renders use Blender Workbench gray; **material color agreement cannot be assessed from these renders**.

## Actual visible discrepancies — no false visual PASS

1. **Body and back, REJECT.** Authority S reference has a lean **but substantial, musculature-defined** torso, connected shoulders and haunches, and a more coherent topline. The actual source silhouette exhibits an exaggerated pronounced back arch/waist dip, thin belly and abrupt muscle transitions. These defects remain in the IK pose.
2. **Tail, REJECT.** Authority requires a notably **long, multi-segment blade/feather-like armored tail** of deliberate orientation. The current actual source shows a very short, thin tail stub/spur, not the same anatomy.
3. **Limbs and feet, REVISE.** Current visible forefoot/hindfoot profiles are coarse and flattened, with over-stretched visual length and uneven link/joint volumes; do not accept the existing skeleton landmark guesses as artist-approved limb anatomy. Compare shoulder-elbow-wrist and hip-stifle-hock precisely before retopo or gait amplification.
4. **Head + crest, REVISE.** The broad long-swept crest idea is present in silhouette, but the source's doubled/slender projections and simplified head do not reproduce the authoritative layered crest lamina, integrated brow device and refined head-neck attachment.
5. **Surface shell / coloration, UNTESTED.** Gray Workbench inspection does not evaluate blue-white armor surface patterns, highlights, or actual materials; lack of color in the render is not, by itself, evidence of a missing texture.

**Meaning:** Motion-lane real geometry validation does not establish appearance suitability. **Production S still 0.** No main merge, no claim of S authority match.

## Next *implementation* gates: shape before racing

- Lock donor QEM mesh unchanged and add a **separate morphology copy** / shape-key variant. Preserve exact original and history. Do not overwrite the v3 pass meshes or their test evidence.
- Prioritize **tail length/segmentation** and **torso/back-topline and abdomen continuity** on the *same real mesh*. Change **one region at a time**, render identical 5 views, score against the same canonical image, and reject if side/front or quarter views worsen.
- Do not use R1 proxies, generic low-poly boxes or detached pasted fins as substitutes. Tail segmentation may need new deformation-friendly topology, which must be separately identified as topological editing, not claimed as preservation of identical face counts.
- After morphology and visible approval, independently re-run QEM/contact triangle QA plus weight reassignment, new gait and race-game benchmarking; no inherited PASS label across changed geometry.

This file is an explicit rejection gate, not an artist-certified completion.
