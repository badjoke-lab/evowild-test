# EvoWild Run S — independent review of connected shoulder-layer pilot
Date: 2026-10-15 (UTC). Source commit: `cd12bedc32270d8bb8c3eb91864a4477bb4f7001`.

**Verdict:** Actual Blender shape modification is **TECHNICAL PASS**. Art-direction milestone is **KEEP ONLY AS A PROTECTED EXPERIMENTAL CHECKPOINT**, **REVISE before using this shoulder shape in canonical S**. This overrides no saved asset; it explicitly distinguishes the producing agent's own local KEEP from independent acceptance.

## Evidence independently inspected

- Genuine `CANONICAL_STAGE1_LAYER_PILOT.jpg` (SIDE, FRONT, FRONT34 closeups, canonical/Stage1/new side by side).
- Genuine `CANONICAL_STAGE1_LAYER_FIVE_VIEWS.jpg` (canonical / old / new at full-body side/front/front34/rear34/back).
- `CANONICAL_STAGE1_RIGHT_FINAL.jpg` (one-side pilot).
- `REVIEW.md`, `FINAL_GEOMETRY_VERIFICATION.json`, `SAVE_RELOAD_VERIFIED.json`, `ONE_SIDE_ART_GATE.json`; final model was successfully committed.
- The source producer identified ONE_SIDE local KEEP and recognized that it was not independent. This review provides an independent artistic assessment.

## Demonstrated progress

1. Previous broad circular/plain shoulder bulge was turned into identifiable separately oriented **connected mesh panels**; this is a real topological edit rather than a simple small vertex offset.
2. The posterolateral shoulder-to-pectoral boundary is newly distinguishable in SIDE and FRONT34. There is a stronger diagonal sheet silhouette, especially from SIDE.
3. BOTH sides were built, different from the previous 807-vertex transition-only Stage1.
4. Blend source protected; saved/reloaded mesh fingerprint exact; actual 5-view and 3 detailed real Blender renders committed.

## Remaining defects visible in the actual contact sheets

**Blocking:** The new shoulder panel remains **too large, flat and uniformly polygonal**. It reads as a single rigid overlay/shield attached to the previous creature, rather than canonical overlapping, articulated musculature/plates.

- SIDE: broad almost planar center; straight-edged diagonal lower seam terminates abruptly in a dark V / wedge. Canonical rounded compound surfaces turn into the pectoral area more continuously; multiple overlapping crest lines, not one slab.
- FRONT: canonical elongated twin white shoulder bulges taper toward upper arms with a central dark chest. The pilot remains broad and slabby at the superior outer shoulder, with extra sharp linear boundaries. It has not convincingly acquired the desired narrowing and articulated contour across the upper arm.
- FRONT34: polygonal sheet floats perceptually above a large dark triangular fold; leading edge and posterior transition still show conspicuous unnatural angles. Canonical has layered rounded/angled plates with coherent overlap under matched material. Source reference illustrations and rendered 3D are not identical poses/angles: avoid falsely quantifying pixel similarity without alignment.
- Full body: crest/head, slenderness of limbs/feet, tail and overall upper-body shape still visibly differ substantially from canonical S. The shoulder experiment does not permit S approval.

The saved pilot is therefore a **useful topology milestone** but its current geometry is **not a final accepted shoulder**. It should not be mirrored further, added to animation or merged into main.

## Technical evidence and limitations

| Measurement | Stage1 | Pilot |
|---|---:|---:|
| Vertices | 38,802 | 40,957 |
| Triangulated faces | 77,684 | 81,994 |
| Connected components | 7 | 7 |
| Nonmanifold edges | 0 | 0 |
| Degenerate tiny faces | 2 | 2 |
| Non-adjacent BVH candidate contacts | 7 | 7 |

The BVH test found no **additional** nonadjacent candidate contacts; this is not exhaustive proof of zero self-intersection, no skinning defects, or production rig-readiness. There are pre-existing structural defects.

## Next single corrective experiment (no more bulk sculpt)

Make a separate `review-v5-shoulder-layer-revision/S_HUNYUAN_SHOULDER_LAYER_REVISION_A.blend`, branching **from the saved PILOT**, retaining its topological success. Focus on only one side and ONLY the new layer region:

1. **Plate boundary:** replace straight hard perimeter with an anatomically motivated oblique taper. Round the geometric thickness transition along the leading and inferior edge; retain sharpness only where the canonical exhibits a legitimate seam. No arbitrary surface subdivision that erases the ridge.
2. **Layering:** do not substitute a giant one-piece polygonal sheet for several tilted shoulder planes. Break up directional surface normals by deliberate BMesh edge-loop editing of the existing connected panel and its root; provide surface orientation continuity into pectoral mass. Avoid detached added balls/plates or uniform smooth brush inflation.
3. **Pectoral-underarm gap:** reduce the conspicuous black V-shaped wedge on SIDE/FRONT34; confirm it is actual cavity/occlusion rather than an accidental geometric overlap, thin bridge, or shading artifact by mesh inspection and local normals.
4. **FRONT width:** match the slender shoulder-to-upper-arm direction from canonical; verify narrowness without swallowing the lower chest. A mere quantile width measurement is insufficient.
5. **Compare early:** save a checkpoint and collect matched SIDE, FRONT, FRONT34 real closeups after each substantial edit. Show before PILOT, revision and canonical; keep both sides untouched until revised one side passes a genuine visual gate.
6. **Safety:** no new self-intersection candidate, winding failure, nonmanifold boundary, new degenerates; verify saved/reloaded fingerprints, protected input SHA, no change outside shoulder ROI. Rigging only after full model approval.
7. **Decision:** if visual correction only shifts the panel or changes its shading without achieving overlapping morphology, **REVISE** and stop. No made-up KEEP.

This file is a review and scope gate, **not** proof of a subsequent revision or a new Blender edit. It preserves the existing pilot and its topological achievement.
