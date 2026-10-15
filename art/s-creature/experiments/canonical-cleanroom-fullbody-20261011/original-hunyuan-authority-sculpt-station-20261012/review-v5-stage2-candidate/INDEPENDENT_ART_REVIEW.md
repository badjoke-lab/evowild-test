# EvoWild Run S / V5 Stage 2 independent art review (2026-10-15)

**Technical result: PASS. Artistic result: REVISE. Not a final V5.**

## Verified outputs

- Actual GitHub Actions Blender 4.3.2: https://github.com/badjoke-lab/evowild-test/actions/runs/38733458456
- Unapproved real mesh: `S_HUNYUAN_SHOULDER_CHEST_V5_STAGE2_CANDIDATE_UNAPPROVED.blend`
- Canonical / V4 / retained Stage 1 / candidate real image: `CANONICAL_V4_STAGE1_STAGE2_DETAIL.jpg`.
- Numeric outcome: 42 scaled/subdivided trials; 40 passed preflight; winner oblique-only alpha 0.45, 298 vertices moved, max delta 0.003427 units. V3-relative global minimum face area ratio 0.322936 (unchanged), 23 severe shoulder faces (unchanged), 0 newly inverted faces, 0 new degenerates. Frontal width quantile unchanged.
- Input immutable Stage1 SHA256 `96b1bbc709f1db0dcd559540e28bd79d3863cfcc73ea2a5d916a020108a91f53`; canonical reference SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Trial preserves original Hunyuan, v1–v4, Stage1 and main. The experimental file is not approved.

## Direct visual comparison

Viewed all three actual Blender rendered detail cameras SIDE, FRONT, FRONT34 alongside the canonical crop.

The candidate shows at most a subtle contour adjustment; it does **not** solve the structural deficiency in the shoulder/pectoral/upper-arm group. The upper shoulder surface is still a broad near-flat mound, abruptly bounded by a darker rear line. The canonically distinct oblique shoulder sheet is not a legible three-dimensional layer/plane, the pectoral groove is not convincingly resolved, and the upper arm is insufficiently differentiated. The front remains broad rather than the illustrated narrow directional anatomy.

**REVISE**: technical face metrics do not prove an art improvement. No KEEP and no rigging, game deployment or animation approval.

## Stop the currently ineffective method

Do **not** continue tiny scaled copies of `STAGE2_REJECTED_PROPOSAL.npz` or minor Gaussian inflation. Iteratively choosing a shape via face-area constraints has repeatedly generated sub-millimeter differences without visually matching the authority drawing.

## Next actual-model technique

- Use the retained `review-v5/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_STAGE1.blend` as the only starting point of an **isolated art-directed pilot**; leave all protected files untouched.
- In the user's live Mac Blender 4.3.2 + Codex CLI + Blender MCP, identify 3D landmark vertices for: (a) superior shoulder beginning, (b) diagonal scapular/plate ridge end, (c) dark pectoral cavity boundary, (d) proximal upper-arm transition. These must be identified on actual SIDE and FRONT34 viewport screenshots AND the canonical art, not inferred solely from coordinate masks.
- Artistically reshape **one shoulder side first**. A disconnected sphere or pasted primitive is prohibited. If a true thin projecting shoulder edge is impossible on the existing surface, permit an isolated proof of mesh face-region inset/extrusion/retopology as part of the *same connected mesh*. Unlike V4/V5 small displacement checks, a topological redesign may be necessary; this is a new explicit experiment and must not be misreported as topology preserved.
- Move/extrude sculpt facets under multiple camera checks until one clearly angled upper sheet overlies a recessed pectoral plane, with readable distinction into upper arm. Keep the front narrow. Use meaningful visible changes, not tiny rounding.
- Save pilot separately `review-v5-shoulder-structure-pilot/S_HUNYUAN_SHOULDER_LAYER_PILOT.blend`; always collect exact topology and self-intersection checks if possible, backup and protect the source. Require actual SIDE/FRONT/FRONT34 screenshots at each stage and matched renders of before and after. Revert poor trials.
- Do **not** mirror a failed right shoulder onto both sides. Only mirror after one-side art KEEP at reference comparison.
- No global model approval yet: head, crest, tail and limbs still need separate reference comparison.

No live Blender GUI connection to the user's Mac is present in this assistant's current remote devices; the unrelated crypto trading VM is explicitly off limits. This step can be performed by Codex CLI in the Mac's own live Blender MCP session, or by another authorized native-GUI controller.
