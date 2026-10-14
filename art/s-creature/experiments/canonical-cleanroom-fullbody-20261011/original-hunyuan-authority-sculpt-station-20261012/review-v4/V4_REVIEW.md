# S Hunyuan V4 — live Blender MCP Edit Mode review

**TECHNICAL: PASS. ARTISTIC: REVISE. KEEP: NO. GAME: NOT APPROVED.**

Executed in the user's running Blender 4.3.2 GUI on macOS, through Blender MCP. This is a saved and reopened real mesh revision, not a proposed sculpt or a GitHub Actions batch result. Work branch: `exp/s-hunyuan-shoulder-sculpt-20261013`, source commit `042e6eddb4f769837594c07b8e7ec54c05a6223d`.

## Authority and source protection

- Only highest authority: `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Actual V3 source: `../review-v3/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend`, SHA256 `820f6ade08f626db7d163dade691fd03e6fa54aa75e8d43ae38ef617252623ec`.
- Both hashes matched before loading and after V4 save/reload. The source V3 topology and coordinates were also read from its actual mesh datablock and compared with the starting checkpoint.
- Original Hunyuan, V1 and V2 were not fetched or touched. No tracked files from earlier work were modified. No main changes, merge, VM access, animation or rig edits.

## Actual operation sequence

1. Sparse clone of the target branch; hash verification. First Blender action was `bpy.ops.wm.open_mainfile` on the real V3, replacing the default scene without saving it.
2. `get_scene_info` and `look` camera images of SIDE, FRONT and FRONT34. `geometry_0` confirmed at 38,802 vertices / 77,684 faces.
3. Save separate V4 work copy. Display the full canonical image in the GUI Image Editor; load and pack unretouched pixel crops into reference-image empties. Align their image planes to the orthographic camera orientations, with approximate crest-to-foot height and SIDE longitudinal alignment. These are guides, not evidence that the source body proportions match. Crop rectangles are in `REFERENCE_CROPS.json`.
4. Enter actual Edit Mode; `bmesh.from_edit_mesh` moves existing vertices in a feathered polygon toward an oblique shoulder plane. Inspect FRONT34 through `look`.
5. Edit the lower pectoral and upper-arm faces toward separate oriented planes, with a broad transition into the thoracic underside. Inspect FRONT.
6. Try a posterior sheet, inspect its enlarged FRONT34 image, and **reject/restore** it because a sharp dark border resembles a slit. Its log explicitly records rejection; its coordinates are not in final V4.
7. Local neighboring-vertex Taubin relaxation, then inspect the enlarged FRONT34. The face-safety line search retained only 0.16777216 of this proposal; the resulting maximum move was 0.0018413, so this was a small transition adjustment.
8. A shallow upper diagonal sheet, followed by a tangential y shear to incline the shoulder surface; inspect after each operation. No Gaussian fields, sculpt brush emulation, disconnected armor, muscle spheres, mesh additions or topology replacement.
9. Actual Cycles CPU renders in the same live Blender: 1000 × 800, 24 samples, no denoising. Render V3 from its verified source coordinates and V4 with identical cameras and lighting; restore V4 coordinates in a `finally` block after each render.
10. Save compressed V4, reopen it, compare all coordinates and all faces exactly. Retrieve scene info and viewport image again after reload.

This used Blender's real Edit Mode through MCP Python, not manual mouse-driven Sculpt Mode strokes. The API exposed `sculpt.brush_stroke`, but edits were performed through BMesh so that mesh proposals and face safety could be checked precisely.

## Measured changes

- Final changed vertices from V3: **8,691**; maximum displacement **0.05523428** Blender units; mean displacement over changed vertices **0.00618398**.
- Defined FRONT shoulder-width quantile: V3 **0.38074460**, V4 **0.36571716**, a **3.95% reduction**. This is a region measurement, not the whole-object bounding box or a measure of artistic fidelity.
- Vertex and face counts unchanged; one mesh object. Source topology exact, save/reload exact, vertices outside shoulder/chest/upper-arm ROI unchanged.
- Newly reversed face normals: **0**. Newly degenerate faces: **0**. Source's existing **2** degenerate faces remain. Boundary edges: 0; nonmanifold edges: 0. Minimum valid area ratio to V3: **0.25068208**.
- Exhaustive self-intersection testing was not performed. These checks do not prove the source or revision is free of every intersection or rendering defect.
- V4 SHA256: `38efa5c29e5ac7b1a6a6afba1256d498763e0f8d3b8e7435d9b38b4b183e879e`.

## Visual decision: REVISE

The actual comparison images show a broad readable shoulder plane instead of V3's round generic swelling, a slightly narrower frontal contour, and a more angular pectoral-to-arm transition. The rejected posterior slit is not retained.

However, the canonical shoulder has several distinct diagonally overlapping sheets. V4 still reads as a large flattened deltoid cap with only a shallow upper transition. The pectoral and upper arm still merge too much; their direction and separation do not yet reproduce the reference. The underside transition remains rough in the source's triangulated surface. Crest, tail and feet remain the mismatching source forms. These shortcomings prevent KEEP and creature approval.

## Review artifacts

- [Editable V4](S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend)
- [V3 / V4 five views](V3_V4_FIVE_VIEW.jpg)
- [V3 / V4 shoulder, chest and upper-arm detail](V3_V4_SHOULDER_CHEST_UPPERARM.jpg)
- [Canonical / V3 / V4 full views](CANONICAL_V3_V4.jpg)
- [Canonical / V3 / V4 shoulder detail](CANONICAL_V3_V4_SHOULDER_DETAIL.jpg)
- `V4_SIDE.png`, `V4_FRONT.png`, `V4_FRONT34.png`, `V4_REAR34.png`, `V4_BACK.png`: full actual Cycles renders. `V4_DETAIL_{SIDE,FRONT,FRONT34}.png`: enlargement renders. Matching V3 renders are also provided.
- [Technical verification](V4_TECHNICAL_VERIFICATION.json), stage logs, compressed source-to-final mesh delta, and file hashes.

The Blender scripts in `art/s-creature/blender/s_hunyuan_v4_*.py` capture the executed methods. They use the current blend path for workspace discovery. Render and verification scripts require a V4 scene and local `V3_BASE_COORDS.npy`; reconstruct that baseline from the protected V3 or the published delta. These are tools for live step-by-step work, not an unattended instruction to rerun accepted and rejected stages in sequence. Source/review files must remain protected.
