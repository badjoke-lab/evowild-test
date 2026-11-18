# D3-C original S rig audit — verified 2026-10-30

## Actual evidence
- [Native rig JSON](rig-inventory.json) produced by [GitHub Actions #41005210114](https://github.com/badjoke-lab/evowild-test/actions/runs/41005210114), source `scripts/audit_s_d3c_rig.py`.
- Actual source `public/models/evowild-s/review/focus-contact-v3.glb`, SHA256 `78dd511cd82aa8afef04a7d61f21b68d4391a9a3143acbaa4b6473b9f8a42a6f`; original file was not changed.
- 38,813 mesh vertices; 21 skinned joints; native `EvoWild_S_Run_V5` animation, 58 channels.
- **No joint whose name denotes an independent shoulder, scapula or clavicle** appears in skin joints. This is not evidence that chest/upper-arm rotations are impossible; it is evidence that an independent scapular controller is absent.

## Verified hierarchy (from GLB node parents)

```text
root
└─ pelvis
   └─ spine
      └─ chest
         ├─ neck ─ head
         ├─ fore_L_upper ─ fore_L_lower ─ fore_L_foot
         └─ fore_R_upper ─ fore_R_lower ─ fore_R_foot
```

- Both `fore_*_upper` bones are direct children of `chest`.
- Existing upper arm / forearm vertices have substantial actual influence:
  - `fore_L_upper`: 3,099 vertices with weight >.1, equivalent weighted sum ~2,240.15
  - `fore_R_upper`: 3,057 vertices with weight >.1, equivalent weighted sum ~2,217.36
  - `chest`: 4,566 vertices with weight >.1, equivalent weighted sum ~1,531.15
- The native clip has rotation/translation/scale tracks for both upper/lower foreleg chains and the chest.
- Crucially, `src/s_contact_ik.js` computes shoulder/upper and elbow/lower rotations afresh with a two-bone solver on **every frame** to hit the world-space sole target. Custom authored transforms applied before IK to these same bones get overwritten, unless restructured.

## Decision

**True independent scapular protraction cannot be authored in the current runtime skeleton without adding/authoring appropriate joint(s), mapping nearby vertex weights and ensuring the animation clips remain compatible.** Simply increasing `foreReach` or chest rotation under the present IK is not equivalent, as demonstrated by D3-A and D3-B actual WebGL video reviews.

**Gate: NO GO for another cosmetic `push-v6` JS-only workaround.** Keep `push-v3` and repaired opt-in `push-v5` unchanged (D3-B numerical KEEP, visual REVISE). No promotion of the runtime GLB or manifest.

## Concrete next authoring unit — separate experimental rig

1. Author **L/R scapula pivots** between chest and respective upper bones **only in a separate editable GLB/Blender working candidate**; preserve the S canonical silhouette, original vertex positions, rest pose, and mesh topology at entry. Their pivot location and weighted coverage must be derived from the actual surface and existing bind matrices, not guessed positions.
2. Inspect original shoulder geometry/weights at front and rear 3/4. Reweight only local shoulder skin region to permit visible scapular glide without clipping/chest collapse. Ensure the original rest world-space positions and native animation poses remain invariant when scapula motion = 0.
3. Animate coherent scapula advance/retract, upper-arm swing, elbow fold/reach and chest reaction; preserve fore/hind contact targets by solving foot IK **after** scapula/chest pose (but do not erase authored scapula rotation).
4. Before judging sprint animation: rebuild a compatible export and show same-camera SIDE/FRONT/CHASE/LOW/REAR_3_4 actual source renders and continuous cycle videos, ensure no race integration and all old D2-D/D3-B contact gates still hold when enabled.
5. Compare against the canonical `art/s-creature/references/00_s_type_modeling_image_v1.png` SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6` on its own source branch. The separate `exp/s-fullbody-zero-verify-20261017` R9 sculpt lane remains **unapproved** and is not a drop-in rigged runtime replacement; do not quietly merge its geometry with the current GLB.
6. If the Blender authoring environment or matching original rigged .blend is unavailable, report that blocker and carry forward this actual measured rig report. Do not claim new shoulder animation was executed.

The above is an *authoring specification*, not a claim that a new rig or S-quality animation has already been created. Visual quality remains **REVISE**.
