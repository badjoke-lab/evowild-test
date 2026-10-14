# EvoWild Run S — V3 Independent Visual Review

Date: 2026-10-14 UTC
Branch: `exp/s-hunyuan-shoulder-sculpt-20261013`
Blender Actions run: https://github.com/badjoke-lab/evowild-test/actions/runs/38503887704

## Status

**TECHNICAL: PASS. ARTISTIC: REVISE. GAME: NOT APPROVED.**

The real `S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend` has been saved and reopened with genuine Hunyuan geometry, 38,802 vertices and 77,684 faces. V3 branched from V1 to remove the V2 ridge/recess notch, while retaining V2 as a separate rejected comparison.

Actual visual contact sheets inspected:
- `BASE_V1_V2_V3_SHOULDER_DETAIL.jpg`
- `BASE_V1_V2_V3_FIVE_VIEW.jpg`
- `CANONICAL_V3_SIDE_FRONT_34.jpg`
Highest authority SHA256: `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.

## What was measurably improved

- The **dark shoulder slit visible in V2 SIDE/FRONT34 is no longer present in V3**. This is the primary achieved corrective objective.
- Front shoulder width quantile: V1 `0.39216657`, V2 `0.38198099`, V3 `0.38063011` Blender units on the same defined region.
- Modified from V1: 12,072 vertices, max displacement `0.00870445` Blender units.
- No new flipped face normals or degenerate triangles; original 2 degenerate faces remain.
- Originals, V1 and V2 unchanged; no animation, rigging or main merge.

## Rejected characteristics despite technical success

1. SIDE/FRONT34 shoulder remains a **rounded generic bulge**, not the canonical layered, angled, planar shoulder / pectoral / upper arm system.
2. FRONT silhouette is somewhat narrower but still too wide and characterless in the outer shoulder. Width alone does not meet the artistic gate.
3. No readable sculpted overlap/surface transition with the illustrated white shoulder plate over the dark pectoral cavity or a convincingly distinct upper-arm direction.
4. The source mesh's severe mismatches of crest, tail, leg/feet, and body appearance remain untouched. V3 is therefore far from approval as the S creature.

## V2 notch mesh measurements (diagnostic, not causal proof)

The V2-to-V1 actual mesh check found 302 shoulder triangles whose normal turns by more than 20 degrees, including 28 triangles above 45 degrees; 1 shoulder triangle's area fell below half, and 7 rose above twice their V1 area. This supports a mesh-surface distortion concern but cannot by itself identify which triangles directly caused the black slit in the render. A separate artist inspection would be required for that causal claim.

## Hard stop to repeated parametric inflation

**NO V4 consisting of wider/narrower Gaussian brush amplitudes.**
V1/V2/V3 demonstrate that deterministic broad brush fields are technically edit-capable but fail the art-directed canonical morphology objective.

Next valid lane: **interactive Blender Sculpt/Edit Mode under canonical SIDE / FRONT / FRONT34 image guidance**. Use proportional surface sculpt / oriented plane creation, retopo if explicitly justified, iterative viewport screenshot review; preserve base geometry as the starting asset and separate editable V4 `.blend`. Do not add disconnected muscle spheres/armor. When completed, provide actual 5-view renders, reference comparisons, saved `.blend`, and reject/keep decision.

The only online Remote Desktop Commander device currently is the unrelated crypto-agent-bot; it MUST NOT be used for Blender. The prior Codespaces devices are offline. Therefore there is no currently established *live* GUI session for the assistant to operate; connecting one is a prerequisite for manual interactive sculpt. GitHub Actions batch Blender remains functional for automated diagnostics, rendering and save verification, not an adequate substitute for a live art-direction view.

No claim of artistic success, no motion gate transition.
