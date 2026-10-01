# EvoWild Run — S-type recovery checkpoint

current_stage: S morphology reset locked; Gate A silhouette rebuild next
branch: feat/s-creature-model
current_model_file: output/S-blockout-v12.blend

done:
- Opened the saved S-blockout-v2.blend directly.
- Used S_EDITABLE_SOURCE as the edit source.
- Narrowed the lower two Neck_integrated_keel cross sections by 15%.
- Applied the local lower-neck/chest-junction deformation to the continuous surface.
- Preserved the continuous central skull and crest vertices.
- Saved the interrupted state as output/S-blockout-v3-recovery.blend.
- Stopped Blender, render, and modeling work for recovery.
- Applied the specified ventral-only lower-neck/chest junction displacement once to the continuous surface (6738 vertices), preserving lateral coordinates and topology.
- Saved output/S-blockout-v4.blend without rendering or GLB export.

- Applied second deterministic ventral-only correction (18% max of ventral excess with smooth section/radial falloff); lateral width/topology/protected forward region unchanged.

- Applied v6 anterior-thorax correction once: central lower-front chest moved backward/upward under the specified smooth bounds while X, topology, vertex count, neck width, forelimb/scapular protected surfaces, and all other regions remained fixed.

- Applied v7 broader thorax correction from v5 baseline; v6 was not used as input. Field widened laterally and displacement reduced to avoid the central smile-crease while keeping X/topology/count/neck width/root protections fixed.

- Applied v8 sternum-plane correction from v7: only the remaining central lower-chest lobe was moved toward a shallow sloped ventral plane; X/topology/count/neck width/root protections remain fixed.

- Applied v9 constrained Y/Z sternum relaxation from v8: five weighted local iterations, X/topology/count/neck width/root protections and boundaries fixed.

- Applied v10 broader shallow lift plus weighted Y/Z fairing from v7 clean baseline; v8/v9 fold geometry not inherited. X/topology/count/neck width/root protections fixed.

- Applied v11 explicit-local thorax correction from v7 clean baseline. Manual Y/Z fairing touched active vertices only; all non-active vertices and all X coordinates remained unchanged.

next_action: Read S_MODELING_IMAGE_LOCK.md and S_MORPHOLOGY_RESET_PLAN.md, then create S-rebuild-v1 as a new silhouette cage. Do not patch v12 and do not create a single central horn.

quality_issues:
- v6 is REVISE: the central-only chest lift created a visible horizontal smile-crease/shelf in front and front34. The lower-neck width remains accepted; the remaining correction must be broader and shallower across the anterior thorax.
- The creature remains an unfinished blockout.
- Global morphology mismatch: current S is too deer/gazelle-like and the head/crest silhouette is wrong. The single sagittal horn/crown is unsupported by the authoritative S references and must be removed/rebuilt.

blockers: none

review_status: v3 recovery review rendered / not accepted
review_renders_v3_recovery:
- output/review/v3-recovery/S_blockout_front.png
- output/review/v3-recovery/S_blockout_side.png
- output/review/v3-recovery/S_blockout_front34.png
- output/review/v3-recovery/S_blockout_rear34.png

review_status_v4: v4 review rendered / not accepted
review_renders_v4:
- output/review/v4/S_blockout_front.png
- output/review/v4/S_blockout_side.png
- output/review/v4/S_blockout_front34.png
- output/review/v4/S_blockout_rear34.png

review_status_v5: v5 review rendered / not accepted
review_renders_v5:
- output/review/v5/S_blockout_front.png
- output/review/v5/S_blockout_side.png
- output/review/v5/S_blockout_front34.png
- output/review/v5/S_blockout_rear34.png

neck_subtask_decision: KEEP
neck_subtask_reason: v5 no longer reads too narrow in front/front34; further ventral-only neck deformation gives diminishing returns. Remaining mismatch is primarily anterior thorax/shoulder massing, not neck width.

review_status_v6: v6 review rendered / not accepted
review_renders_v6:
- output/review/v6/S_blockout_front.png
- output/review/v6/S_blockout_side.png
- output/review/v6/S_blockout_front34.png
- output/review/v6/S_blockout_rear34.png

thorax_v6_decision: REVISE
thorax_v6_reason: front/front34 show a new horizontal smile-crease caused by the narrow central displacement/protection boundary; side improvement is insufficient to justify keeping that artifact.
thorax_v6_recovery_rule: build v7 from S-blockout-v5.blend, not from v6.

review_status_v7: v7 review rendered / not accepted
review_renders_v7:
- output/review/v7/S_blockout_front.png
- output/review/v7/S_blockout_side.png
- output/review/v7/S_blockout_front34.png
- output/review/v7/S_blockout_rear34.png

thorax_v7_decision: REVISE
thorax_v7_reason: v7 successfully removes the v6 smile-crease, but front/front34 still show a distinct rounded central sternum lobe hanging between the shoulders; side remains heavier than reference 01.
thorax_v7_keep: use v7 as base; do not revert to v5 and do not reintroduce v6 central-only field.

review_status_v8: v8 review rendered / not accepted
review_renders_v8:
- output/review/v8/S_blockout_front.png
- output/review/v8/S_blockout_side.png
- output/review/v8/S_blockout_front34.png
- output/review/v8/S_blockout_rear34.png

thorax_v8_decision: REVISE
thorax_v8_reason: side profile is lighter and closer to target, but front/front34 introduce a stronger folded smile/crease across the sternum. Do not revert the whole shape; keep v8 position and relax only the local Y/Z surface continuity.
thorax_v8_keep: preserve v8 overall chest position as v9 base.

review_status_v9: v9 review rendered / not accepted
review_renders_v9:
- output/review/v9/S_blockout_front.png
- output/review/v9/S_blockout_side.png
- output/review/v9/S_blockout_front34.png
- output/review/v9/S_blockout_rear34.png

thorax_v9_decision: REVISE
thorax_v9_reason: the constrained relax moved 2982 vertices but max total delta was only 0.00142, so front/front34 are visually almost unchanged from v8 and the sternum fold remains.
thorax_v10_base: use S-blockout-v7.blend as the clean no-fold baseline; do not inherit v8/v9 fold geometry.

review_status_v10: v10 review rendered / not accepted
review_renders_v10:
- output/review/v10/S_blockout_front.png
- output/review/v10/S_blockout_side.png
- output/review/v10/S_blockout_front34.png
- output/review/v10/S_blockout_rear34.png

thorax_v10_decision: REVISE
thorax_v10_reason: visual continuity improved, but validation shows 186089 of 186133 vertices changed after the LaplacianSmooth modifier, violating the hard scope lock that all non-target regions remain fixed. v10 is invalid regardless of appearance.
thorax_v11_base: use S-blockout-v7.blend. Reimplement fairing manually on the explicit active vertex set; do not use a Blender smoothing modifier.

review_status_v11: v11 review rendered / not accepted
review_renders_v11:
- output/review/v11/S_blockout_front.png
- output/review/v11/S_blockout_side.png
- output/review/v11/S_blockout_front34.png
- output/review/v11/S_blockout_rear34.png

review_status_v12: rebuilt and three-view review rendered; user acceptance pending
- Reconstructed anterior thorax from fixed boundary; all X, neck, forelimb roots, scapular outer ridge, topology and vertex count preserved.

global_v12_decision: REJECT
global_v12_reason: The current model diverges materially from the authoritative S reference silhouette. The procedural build hard-coded a single `Sagittal_crown` plus bilateral `Temporal_sweep` geometry, which reads as a large horn and does not match the reference head/crest structure. Continuing chest-only refinement would polish the wrong baseline.
global_reset_priority: head/crest silhouette -> neck/head proportion -> thorax/shoulder massing -> limb joint language -> feet/tail. S only.

modeling_image_lock: S_MODELING_IMAGE_LOCK.md
reset_plan: S_MORPHOLOGY_RESET_PLAN.md
gate_a_output: output/S-rebuild-v1.blend
v12_role: rejected morphology baseline; technical donor/checkpoint only
