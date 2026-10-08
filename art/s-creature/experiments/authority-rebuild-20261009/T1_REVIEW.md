# EvoWild S authority-input TRELLIS v1 — actual model decision

**Decision: REJECT for S morphology and game asset. Retain as experimental comparison only.**

## Provenance
- Branch: `exp/s-authority-shape-20261009`
- Authority: `art/s-creature/references/00_s_type_modeling_image_v1.png` on `exp/s-creature-vibe-modeling`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
- Input: `authority-front34-clean-v1.png` (crop of exact authority artwork, SHA256 `b45b0d2419c2b5b590fd81a4c757c27f80a88bced074ae7b4aeb8d37f982b6db`). This is the *corrected* input; the earlier text-masking run broke the crest and is excluded from review.
- Generation: official public Microsoft TRELLIS.2, seed 0 / resolution 1024. Evidence recovered intact from workflow run `37799572375` by run `37800039565`.
- Actual output: `S-authority-trellis-v1.glb`, SHA256 `59b24b4851821e43397bb62d4a3f2d31523d11960dab34634e8288dcd2e3af9f`.
- Five actual Blender Workbench orthographic views: `review/authority_trellis_v1_{side,front,front34,rear34,back}.png`, contact sheet `review/authority_trellis_v1_five_view_contact.jpg`.

## Visual review (five actual images, not inferred from technical validation)
- **FRONT / BACK: FAIL**. Central solitary narrow upright needle/spear rather than the authority's **two separated dominant crest blades**. Hard fail under the authoritative lock.
- **SIDE / FRONT34: FAIL**. Basic long-limbed proportion exists but the head and upper body still lack the reference-specific angled cranial armour; body and legs read too generic/deer-like.
- **FEET: FAIL**. Contact silhouette remains hoof-like and does not match the detailed split racing-foot sheet.
- **TAIL: IMPROVED BUT NOT ACCEPTED**. Generated tail is longer and layered compared to the old short-stub sample, but blade/feather construction and pelvis connection are not approved.
- No materials, rig, deformation, animation or actual game-performance acceptance is claimed.

## Structural audit
See `T1_GEOMETRY_AUDIT.json`:
- 294,082 triangle faces and 208,060 vertices.
- 1 GLB geometry object but **6,155 disconnected mesh components**.
- Not watertight, not volume.
- Treat as generated morphology reference, never as a playable mesh.
- The dominant front crest is not proven to be an independently safe, game-ready piece. Do not artificially bifurcate one needle and claim a fixed cranial model.

## Consequence / stop
- REJECT T1 as S final appearance; T2 game-ready mesh repair, rigging and Motion First integration are BLOCKED.
- Keep the approved image unchanged and retain `S-authority-trellis-v1.glb` only as review evidence / potential sculpt donor.
- Next construction is **reference-directed manual/topology-first anatomical modeling** of the dual cranial blades, sculpted skull/neck/shoulders, split feet and layered tail. Any future replacement candidate requires the same five-view actual-image review before mesh optimization.
- Do not merge this branch to main, `feat/s-creature-model`, or Motion First.
