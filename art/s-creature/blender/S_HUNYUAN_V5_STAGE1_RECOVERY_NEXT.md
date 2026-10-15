# EvoWild Run S-Type V5 — resume after the rejected 44-vertex relax

**This is a corrective continuation.** Previous Codex CLI Stage 1 locally edited 44 vertices, reduced face count under 0.45 from 40→36 but degraded minimum face-area ratio 0.250682→0.242568. It correctly reverted *all coordinates* to V4 and did not push a finished V5. Do not present this as V5 completion. Existing local untracked `review-v5` failed-stage logs, screenshots, and `S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_WORKING.blend` must be preserved; do not run git clean/reset to remove them.

## New experimentally verified, **unsaved** V5 candidate

Real GitHub Actions Blender 4.3.2 test: https://github.com/badjoke-lab/evowild-test/actions/runs/38727279046

- Generator script: `art/s-creature/blender/s_hunyuan_v5_constrained_local_recovery_proposals.py`.
- Result JSON: `review-v5-proposals/V5_LOCAL_RECOVERY_CANDIDATE_SEARCH.json`.
- Winner data: `review-v5-proposals/V5_RECOVERY_GEOMETRIC_PROPOSAL.npz` (actual vertex ID and proposed coordinates from genuine V4).
- Search: 49 candidates, 7 numerically safe.
- Winner: 7 graph-neighbor rings, interpolation toward actual V3 by alpha 0.12, **807 moved vertices, max delta 0.003675 local units**.
- V3-relative area ratio min: **0.250682→0.322936** (numeric).
- Count of selected shoulder faces with area ratio below 0.45: **40→23**.
- No reversed normals, no new degenerates, no movement outside designated shoulder/chest vertex ROI.
- This is **not** an artistic visual KEEP. Reject if broad shoulder becomes over-rounded, a dark slit appears, or the diagonal shoulder / pectoral plane is visually worse.

## Direct local Codex CLI instructions (same live Blender MCP 127.0.0.1:9876)

1. Check that Blender is currently connected. If not, re-enable the local Blender MCP server. Avoid repeated forced GUI restarts while a live Blender 4.3.2 process is running.
2. In `~/evowild-test-sculpt`, inspect `git status --short` and branch. Then `git pull --ff-only origin exp/s-hunyuan-shoulder-sculpt-20261013` **without deleting untracked V5 files**.
3. Read `V5_LOCAL_RECOVERY_CANDIDATE_SEARCH.json` and confirm the best candidate is marked `geometry_gate: PASS` and target counts match.
4. In Blender MCP, open the already saved `review-v5/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_WORKING.blend` (if not loaded). Ensure the actual mesh is still the reverted V4 coordinate state. If it differs, stop; do not destroy the user's work. Use existing GUI to keep current view settings.
5. Execute the precise local read-only-verified candidate as a **live preview only**, using `blender.execute_blender_code` with `exec(compile(open(path).read(),path,'exec'))` where `path` is the absolute local path of `art/s-creature/blender/s_hunyuan_v5_mcp_preview_recovery.py`.
   - The script requires exact V4 coordinates in the working file; makes a backup `review-v5/V5_RECOVERY_PREVIEW_BEFORE.npy`; uses actual BMesh Edit Mode; verifies 807 changed vertex coordinates; **does not save the .blend**.
   - If the MCP connection resets, first check scene info and backup before retrying. **Never run twice with a remaining preview backup.**
6. Collect actual `blender.look` views at matched camera framing: SIDE, FRONT, FRONT34 and especially shoulder/pectoral close-up. Check against the original reference and V4. Inspect two sides, rear shoulder line, underarm and triangularity.
7. If the image looks worse, run `art/s-creature/blender/s_hunyuan_v5_mcp_revert_preview.py` via MCP. It restores all 38,802 coordinates exactly and removes the temporary backup on success. Record rejection evidence. **Do not push or approve an unsound candidate.**
8. If the candidate is visibly acceptable as a transition repair, save a new **Stage 1 checkpoint** `review-v5/S_HUNYUAN_SHOULDER_CHEST_SCULPT_V5_STAGE1.blend` (not the final V5). Preserve WORKING/V4. Mark `STAGE1_TECHNICAL_PASS_VISUAL_CHECKED` only if saved/reloaded and compared. Store real camera closeups and before/after measurements.
9. Only after Stage 1 accepted, do a small local art-directed move on the oblique upper-shoulder contour and the pectoral/upper-arm distinction. Use actual viewport feedback between each edit; no repeat of broad single-plane flattening/Gaussian bulk scaling. Do not use numeric area recovery as a substitute for the required canonical artistic overlap.
10. At the first new structural or artistic failure, revert the *new* proposal, preserve evidence, and report a specific failure. Do not blindly retry the earlier failed 44-vertex relax. If corrected, produce final V5 .blend and real 5-view + 3 detailed renders, save/reopen, SHA tests, and an independent KEEP/REVISE; push to the same branch.

**Protected:** original Hunyuan, V1–V4, canonical PNG SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`, main, crypto trading VM.

**Current completion state:** prevalidated V5 Stage 1 candidate is committed, not yet applied/reviewed in the user's live GUI. No V5 model ready for game/rig/animation.
