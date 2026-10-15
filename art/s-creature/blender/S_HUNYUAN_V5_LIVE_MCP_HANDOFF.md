# EvoWild Run — S Hunyuan V5 live Blender MCP handoff

**Status:** The V5 surface diagnostic succeeded on GitHub Actions, but **NO V5 sculpt has been performed**. V4 is technically valid but artistically REVISE. This document is a **specific executable art-direction brief for the local Codex CLI connected to the user's Blender 4.3.2 GUI through Blender MCP**; do not substitute another background bulk-blur / Gaussian sculpt or report success from tool setup alone.

## Source and environment

- GitHub repository: `badjoke-lab/evowild-test`
- Branch: `exp/s-hunyuan-shoulder-sculpt-20261013`; **never edit main**
- Local working checkout established on the user's Mac: `~/evowild-test-sculpt`
- Blender 4.3.2 (Intel Mac), MCP add-on port 9876, Codex CLI. Previous successful calls: `blender.get_scene_info`, `blender.look` (`mode: viewport`), `blender.execute_blender_code`.
- The Mac has **not** been remotely attached to this ChatGPT session; Codex CLI on the Mac must operate the native Blender process. No crypto bot VM.
- First fetch newest remote to obtain this diagnostic; inspect working-tree modifications before `git pull --ff-only`. Do not overwrite local edits.

**Canonical reference:** `art/s-creature/references/00_s_type_modeling_image_v1.png` SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.

**V4 source:** `art/s-creature/experiments/canonical-cleanroom-fullbody-20261011/original-hunyuan-authority-sculpt-station-20261012/review-v4/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V4.blend` SHA256 `38efa5c29e5ac7b1a6a6afba1256d498763e0f8d3b8e7435d9b38b4b183e879e`.

**V3 comparison:** same station `review-v3/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V3.blend` SHA256 `820f6ade08f626db7d163dade691fd03e6fa54aa75e8d43ae38ef617252623ec`.

Real mesh datablock: `geometry_0`, 38,802 vertices and 77,684 triangles; no replacement mesh or externally generated 2D output may qualify as a sculpt.

## Verified diagnostic evidence (2026-10-15)

- Reproducible GitHub Actions: https://github.com/badjoke-lab/evowild-test/actions/runs/38720635841 (**SUCCESS**).
- Script: `art/s-creature/blender/s_hunyuan_v5_surface_diagnostic.py`
- JSON face IDs, world-space centers, normals and V3→V4 area ratios: `review-v5-diagnostic/V4_COMPRESSED_FACE_DIAGNOSTIC.json`
- Visual face distortion map of SIDE/FRONT/FRONT34: `review-v5-diagnostic/V4_FACE_DISTORTION_3_VIEW.jpg`
- Mask categories: **red** means face compressed to <45% V3 area; **orange** means <75%; **purple** means changed face normal by >=25 degrees. Color masks indicate geometric change, *not automatically an art defect*.
- Approximately 40 faces in the wide shoulder/upper-arm scope have V4 area ratios <0.45.
- Minimum V4/V3 face area ratio: `0.25068208`, the previously reported V4 safety gate boundary.
- Named hotspot examples (face index, V4/V3 ratio, world-space center):
  - Right: `65666` (`0.25068`, `[0.09277,-0.41434,-0.13918]`)
  - Right: `65664` (`0.26000`, `[0.09313,-0.40752,-0.14482]`)
  - Left: `12157` (`0.29007`, `[-0.16531,-0.40817,-0.14257]`)
  - Left: `12159` (`0.29536`, `[-0.16468,-0.41538,-0.13645]`)
- These bilateral compressed-face bands lie near the lower outside shoulder/pectoral transition. They are **localized targets for inspection**; not proof of a slit, intersection or a precise anatomy boundary. The same masks also show many purple/orange faces along the shoulder rear edge and underside.
- Previous v4 valid result: 8,691 vertices edited from V3, preserved connectivity and source, no new flipped or degenerate faces, but plate still looks like a large abruptly flattened block. Independent conclusion: **REVISE**.

## Live V5 process — follow this in order

### Stage 0: Secure the real file and establish exact repeatable comparison

1. Verify SHA256 of reference, V3 and V4. Check clean branch; no main changes, no remote merge.
2. Use MCP to open V4 in the *running Blender GUI*, verify actual object/mesh stats with `get_scene_info` and/or `execute_blender_code`, inspect actual SIDE, FRONT and FRONT34 by `look`.
3. Create and save a separately named `review-v5/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_WORKING.blend` **before** sculpting. Never overwrite V4.
4. Set full reference sheet plus its pixel-exact shoulder crops side-by-side in Blender; saved cameras, zoom, clay material, exposure and render settings should match V4 comparisons as closely as possible.
5. Select one severely compressed hotspot face cluster on the actual mesh by polygon ID; use a viewport overlay/selection screenshot to confirm **which visible shoulder region** those indices correspond to. If the visible hotspot is not in the offending facet boundary, correct the selection before editing. Do not select wide 8k-vertex fields by guesswork.

### Stage 1: Repair V4's compressed transition locally

1. Preserve V4 checkpoint in memory and file.
2. In Blender Edit Mode or Sculpt Mode (via supported MCP), **relax/reposition only face-adjacent vertices in the marked compressed band**, while maintaining the neighboring broader shoulder plate's orientation and original edge flow.
3. Prefer brush/neighbor normal/tangential operations that remain on the actual contiguous surface, not surface-to-single-plane projection, Gaussian volumes, or disjoint primitive panels.
4. Work separately on the two sides with symmetry checked explicitly; do not use global smoothing that destroys shoulder detail.
5. Do a small proposal then capture **real** FRONT34 and SIDE viewport images; revert if the outer plate becomes boxier, a dark slit emerges, or upper-arm silhouette thickens excessively.
6. Verify changed vertices are in selected shoulder/pectoral ROI, face connectivity unchanged, no new inverted triangles or degenerates, and **compressed face count under 0.45 is lower than 40** where feasible. Track min-area ratio; it must not become *worse* than V4. Report specific face/vertex IDs improved. Numeric gain alone never qualifies as art KEEP.

### Stage 2: Directional shoulder overlap rather than another flattened box

Once Stage 1 succeeds, create **one** readable oblique upper-shoulder transition across the existing continuous surface, with a gentle recessed dark-pectoral junction toward the arm. Preserve the canonical front’s narrow vertical shoulder contours. Use actual Sculpt/Edit Mode changes informed by camera screenshots and the canonical sheet. Geometry must clearly avoid block-flat or ball-round appearance. Keep a rollback checkpoint.

Do not claim true overlapping detached armor unless an art-directed topology change is specifically justified and vetted. Existing-mesh surface relief is permitted, but no arbitrary added plates/spheres.

### Stage 3: Proof and hard STOP/KEEP gate

- Generate genuine SIDE / FRONT / FRONT34 / REAR34 / BACK and detailed SIDE / FRONT / FRONT34 using stable identical cameras/materials to V4.
- Generate a V4 vs V5 same-framing triptych, and canonical vs V5 detail comparison.
- Save the edited `review-v5/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5.blend` separately only if there was actual mesh improvement; reopen with Blender, compare coordinates and topology, recheck SHA of immutable inputs.
- Capture topology diagnostics (new reversed faces/degens=0, bounded local displacement, area distortion statistics, continuity and, if available, self-intersection checks).
- Provide the honest independent **KEEP/REVISE** judgment. KEEP only if no visible pinched seam, meaningful oblique layer in FRONT34 and SIDE, proportionally narrow FRONT and discernible pectoral/upper-arm transition.
- If any stage fails, preserve logs and screenshots but **REVISE and halt** rather than make arbitrary changes.
- Commit/push only valid candidate, images, stage logs and independent review to `exp/s-hunyuan-shoulder-sculpt-20261013`. Keep V1–V4, canonical PNG, original Hunyuan, and main completely unchanged. No animation/rigging/game deployment.

## Important state distinction

**Verified:** V4 original can be edited by native Blender MCP, V5 baseline diagnosis completed in GitHub Actions.

**Not done:** V5 real Edit/Sculpt Mode modification, V5 .blend creation, visual approval.

This handoff is not permission to auto-approve the overall S creature. Crest, leg, hoof, rear and tail still differ from canonical and remain separate rejection conditions.
