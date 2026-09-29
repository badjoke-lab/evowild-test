# EvoWild Run — S-type recovery checkpoint

current_stage: S-blockout-v7 broader anterior thorax correction saved, review pending
branch: feat/s-creature-model
current_model_file: output/S-blockout-v7.blend

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

next_action: Inspect v7 side/front/front34 against reference 01. Specifically confirm the v6 smile-crease is gone and the anterior thorax no longer hangs as a rounded lower bulge.

quality_issues:
- v6 is REVISE: the central-only chest lift created a visible horizontal smile-crease/shelf in front and front34. The lower-neck width remains accepted; the remaining correction must be broader and shallower across the anterior thorax.
- The creature remains an unfinished blockout.
- Crown, shoulder planes, hindlimb joints, and feet still retain the prior v2 issues.

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
