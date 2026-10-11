# S Type real four-view source trace and 3D review — 2026-10-11

## Sole reference / unchanged
Original user-approved art/s-creature/references/00_s_type_modeling_image_v1.png, SHA256 93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6, 1448x1086. Includes actual SIDE FRONT BACK FRONT34 plus detailed crest/feet/tail. Never replace this image.

## Verified original-source pixel contour asset (keep)
- SIDE: 190 simplified original-native coordinate vertices.
- FRONT: 60.
- BACK: 53.
- FRONT34: 107.
- Full source and overlaid verification: canonical-4view-pixel-trace-v1/SOURCE_VS_ACTUAL_PIXEL_TRACE_FOUR_VIEWS.jpg
- Machine-readable native pixels: canonical-4view-pixel-trace-v1/ACTUAL_CANONICAL_S_PIXEL_CONTOURS.json
- These are source-image tracing scaffolds, not production-ready 3D or artist-certified precise outlines.

## Two genuine Blender 3D geometry attempts and actual-image verdict

V0: source-carved 93,490 vertices / 186,976 triangles, Blender/GLB/five views persisted. **REJECT**. Segmentation wrongly filled the whole SIDE external contour, including the ground line; thus all open space between legs became a featureless curtain. Its supposed 0.995 source-mask IoU was self-consistency with this INCORRECT filled silhouette — NOT visual match.

V1: rebuilt mask from exact original image dark/saturated ink, removed ground baseline, preserved underbelly between-legs open air, filled only genuinely enclosed white patches. Genuine Blender 103,358 vertices / 206,724 triangles, source X/Z and SIDE Y/Z physical projections. Real 5 Blender views and independent editable Blender + GLB saved under multiview-visual-hull-v1. Correct source-ink SIDE negative-space window is 100% open; the source masks were no longer V0's wrongly filled contour. Measured 0.978 SIDE / 0.977 FRONTBACK are only projection self-consistency with algorithm INPUT masks — NOT true morphology acceptance.

**V1 REJECT after actual image review.** SIDE outline now shows the long crest, back curve, four separated legs and swept tail, BUT interior torso has unnatural repeated horizontal ribs, and real FRONT34/REAR34 have overlapping extra legs / broken shoulder, spine, thigh volumes. The real FULL BODY geometry does not resemble the anatomical layered original S sufficiently, has no adequate original 3D armor plating/surface details and no articulated playable rig.

Actual source-vs-V1 images:
multiview-visual-hull-v1/review/REAL_CANONICAL_S_SOURCE_VS_VOLUME_V1_4VIEWS.jpg

Actual 5 views:
multiview-visual-hull-v1/review/REAL_SOURCE_CARVED_VOLUME_V1_5VIEW.jpg

Actual QA:
multiview-visual-hull-v1/REAL_SOURCE_MULTIVIEW_VOLUME_V1_QA.json

Actual original source Blender:
multiview-visual-hull-v1/S-ORIGINAL-SOURCE-3VIEW-VOLUME-V1-UNAPPROVED.blend
and S-ORIGINAL-SOURCE-3VIEW-VOLUME-V1-UNAPPROVED.glb

## Stop and next legitimate modeling step

**Stop brute-force automatic full-figure volumetric hull generation, just as the rejected tubular A0 and inflated QEM were halted.** 2D silhouettes do not uniquely specify authentic surface anatomy or even correct positioning of four limbs in oblique views. Better pixel IoU is NOT better 3D S creature.

Retain actual native source contours as image-plane shape constraints. A real Blender mesh artist/sculpt pass is required: construct continuous shoulder/thorax/hip anatomy, actual FRONT/REAR shoulder widths, long swept twin blade crest, split racing toes, and anatomically rooted/layered tail plate volumes. Explicitly compare actual five-view Blender results against original SIDE, FRONT, BACK, FRONT34 before rigging or any claim of morphology acceptance. No new master images, no more artificial model pass from numeric tests. QEM/R5/A0/V0/V1 REJECT. Main unchanged. Completed canonical S count 0.
