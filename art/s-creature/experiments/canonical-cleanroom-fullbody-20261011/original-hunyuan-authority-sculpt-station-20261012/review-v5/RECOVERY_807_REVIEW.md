# V5 recovery continuation — Stage 1 retained, final art REVISE

2026-10-15, live native Blender 4.3.2 through Blender MCP. Branch: `exp/s-hunyuan-shoulder-sculpt-20261013`.

## Retained actual mesh edit

The already saved WORKING file was opened in the GUI. Its 38,802 vertex positions and 77,684 triangles matched genuine V4 exactly before editing. The committed, Actions-tested 807-vertex NPZ was applied with the prescribed BMesh Edit Mode preview script. No 44-vertex relax was retried. Matched SIDE / FRONT / FRONT34 viewport images were inspected before saving.

The lower shoulder/pectoral transition is slightly softer. Broad plate orientation and front width remain stable; there is no clear new slit or extra rounding. This is acceptable as a transition repair checkpoint, not a completed shoulder sculpt. The existing large flat shoulder face and abrupt posterior crease remain visible.

Saved separately as `S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_STAGE1.blend`, reopened twice, and verified bit-exact against the expected coordinates. The original WORKING file and all earlier rejected-stage local evidence were left untouched. The preview backup remains local; do not rerun the preview over the accepted checkpoint.

| Check | V4 | Stage 1 |
| --- | ---: | ---: |
| Minimum V3-relative face area | 0.25068208 | 0.32293604 |
| Shoulder faces below 0.45 | 40 | 23 |
| Front width quantile | 0.36285915 | 0.36285915 |

807 vertices changed, maximum displacement 0.00367470; zero changes outside the allowed ROI, zero new reversed or degenerate faces relative to V4, identical connectivity, zero boundary/nonmanifold edges. Exhaustive self-intersection testing was not performed. Full measurements, hotspot face IDs and hashes are in `STAGE1_807_TECHNICAL_VERIFICATION.json`.

## Stage 2 rejected before mutation

One bounded graph-neighborhood proposal attempted to lower the rear upper-shoulder contour obliquely and inset a small pectoral region on both sides. It proposed 498 vertex changes, maximum 0.00761577. Preflight detected **7 face orientation reversals** and a minimum V3 area ratio of **0.03089278**. The gate stopped execution before BMesh mutation or any new blend save.

The same calculation was rerun only to preserve rejection evidence; no revised candidate or live edit was attempted. `STAGE2_REJECTED_PREFLIGHT.json` and `STAGE2_REJECTED_PROPOSAL.npz` document this rejected proposal. The live mesh was checked against Stage 1 and matched exactly. No rollback was necessary because the failed proposal never reached the mesh. Per the recovery brief's first-failure rule, further Stage 2 sculpt trials stopped.

## Actual images and quality gate

Eight genuine live-Blender Cycles renders were produced: SIDE, FRONT, FRONT34, REAR34, BACK, plus SIDE/FRONT/FRONT34 details. They use V4's 1000×800, 24-sample CPU Cycles, clay lighting and fixed V3 framing. Noise is retained; no retouching or AI reconstruction. `STAGE1_RENDER_PROGRESS.json` records all eight completed renders.

- `V4_V5_STAGE1_FIVE_VIEW.jpg`: matched V4 / Stage 1 full-body views.
- `V4_V5_STAGE1_SHOULDER_DETAIL.jpg`: matched detail triptychs.
- `CANONICAL_V4_V5_STAGE1_DETAIL.jpg`: unchanged reference pixel crops, V4 and Stage 1.
- `807_PREVIEW_*.png` / `V4_BEFORE_*.png`: matched actual viewport evidence.
- `STAGE1_CHECK_LEFT_SIDE.png` / `STAGE1_CHECK_REAR34.png`: additional opposite-side and posterior-shoulder viewport inspection after reopen.

Evidence-based artistic verdict: **REVISE**. The numerical transition repair is retained, but SIDE and FRONT34 still read as one broad flat shoulder mass with an abrupt rear crease. The canonical's oblique layered contour and pectoral/upper-arm separation are not achieved. FRONT width is preserved but that alone does not satisfy the reference. Existing crest, lower leg/hoof and tail deviations are also visible in full-body views. No final `...V5.blend`, game-ready approval, rigging or animation delivery is claimed. This verdict is the acting agent's image review, not an external human approval.

V3, V4 and canonical PNG hashes match the protected values. No tracked original Hunyuan, V1–V4 or reference file was edited; main was not switched to or modified. Only the valid Stage 1 checkpoint, its evidence, the rejected proposal data and supporting scripts are committed.
