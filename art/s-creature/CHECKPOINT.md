# EvoWild Run — S-type recovery checkpoint

current_stage: experimental Vibe Gate A1-v10 reviewed REVISE; crest-only v11 side-lamina-width correction required
branch: exp/s-creature-vibe-modeling
current_model_file: output/S-vibe-a1-v10.blend

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

next_action: Build A1-v11 from output/S-vibe-a1-v10.blend. Edit CREST ONLY. Keep all non-crest geometry fixed. Preserve approximately the v10 FRONT/BACK plate projection while increasing SIDE lamina width and curvature by reducing roll angle proportionally as width increases. Render SIDE/FRONT/FRONT34/BACK and STOP.

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

gate_a_status: REVIEW_PENDING
modeling_status: STOPPED
gate_a_source: fresh empty scene; no v12 donor geometry used
gate_a_cage_vertices: 760
gate_a_done: small wedge head; six skull-rooted layered rear-swept crest plates; tapered non-tubular neck; compact thorax / narrow waist / light pelvis; distinct fore/hind joint chains; three toes per foot; tapered aerodynamic tail
gate_a_render_geometry_unchanged: true
gate_a_scope: S only; no eyes, Cue Band, materials/textures/color design, animation or final retopology
gate_a_limitation: low-complexity cage with overlapping limb/toe roots; no production welding or surface refinement
gate_a_renders:
- output/review/rebuild-v1/S_rebuild_side.png
- output/review/rebuild-v1/S_rebuild_front.png
- output/review/rebuild-v1/S_rebuild_front34.png
- output/review/rebuild-v1/S_rebuild_rear34.png
- output/review/rebuild-v1/S_rebuild_back.png

gate_a_v1_decision: REVISE
gate_a_v1_reason: The fresh rebuild removes the v12 single central horn and is a better starting direction, but the Gate A silhouette still misses the approved modeling image. Side view is too long-necked and tube-like, torso is too long/flat and under-massed at the shoulder, limbs still read as rods, and the crest becomes two tall horn-like prongs from front/back instead of backward-swept layered cranial plates.
gate_a_v1_keep: fresh-rebuild approach; small wedge head intent; no v12 donor geometry; multi-plate crest concept; narrow waist intent; distinct fore/hind chains; multi-toe feet.
gate_a_v2_priority: Gate A is subdivided by S_CREATURE_MODELING_WORKFLOW.md. Immediate priority is A1 head/crest/neck only. A2 thorax/waist/pelvis, A3 limbs, A4 tail and A5 global review are blocked until the preceding gate is accepted.
process_lock: S_CREATURE_MODELING_WORKFLOW.md
self_style_rule: AI free-form modeling workflow is prohibited; reference landmarks and target/keep_fixed/review cameras must be declared before edits.

vibe_lane: exp/s-creature-vibe-modeling
vibe_gate_a1_status: REVIEW_PENDING
vibe_modeling_status: STOPPED
vibe_a1_fixed_geometry_unchanged: true
vibe_a1_scope: head / crest / neck only
vibe_a1_renders:
- output/review/vibe-a1/S_vibe_a1_side.png
- output/review/vibe-a1/S_vibe_a1_front.png
- output/review/vibe-a1/S_vibe_a1_front34.png
- output/review/vibe-a1/S_vibe_a1_back.png


vibe_gate_a1_decision: REJECT
vibe_gate_a1_reason: Side/front34 crest became broad horizontal slabs; FRONT still contains horn-like prongs and neck is too broad/flat. Do not continue from S-vibe-a1.blend.
vibe_gate_a1_v2_source: output/S-rebuild-v1.blend
vibe_gate_a1_v2_lock: S_VIBE_A1_REFERENCE_ANALYSIS.md

vibe_gate_a1_v2_status: REVIEW_PENDING
vibe_gate_a1_v2_source: output/S-rebuild-v1.blend
vibe_gate_a1_v2_fixed_geometry_unchanged: true
vibe_gate_a1_v2_renders:
- output/review/vibe-a1-v2/S_vibe_a1_v2_side.png
- output/review/vibe-a1-v2/S_vibe_a1_v2_front.png
- output/review/vibe-a1-v2/S_vibe_a1_v2_front34.png
- output/review/vibe-a1-v2/S_vibe_a1_v2_back.png


vibe_gate_a1_v2_decision: REVISE
vibe_gate_a1_v2_keep: head and neck proportions; improved FRONT crest clustering; all non-A1 geometry lock.
vibe_gate_a1_v2_problem: SIDE/FRONT34 crest is too horizontal and reads as a bundle of needles instead of C5/H6 rear-upward layered blades.
vibe_gate_a1_v3_exact_edit: crest only; keep all head/neck/body/limb/tail vertices fixed. Increase rear-upward blade arc while keeping distal tips converged near sagittal plane.

vibe_gate_a1_v3_status: REVIEW_PENDING
vibe_gate_a1_v3_scope: crest only
vibe_gate_a1_v3_head_neck_unchanged: true
vibe_gate_a1_v3_non_a1_geometry_unchanged: true
vibe_gate_a1_v3_renders:
- output/review/vibe-a1-v3/S_vibe_a1_v3_side.png
- output/review/vibe-a1-v3/S_vibe_a1_v3_front.png
- output/review/vibe-a1-v3/S_vibe_a1_v3_front34.png
- output/review/vibe-a1-v3/S_vibe_a1_v3_back.png


vibe_gate_a1_v3_decision: REJECT
vibe_gate_a1_v3_reason: SIDE rear-upward direction improved, but FRONT regressed to two tall symmetric horns. The bilateral 3+3 crest construction is the failure source.
vibe_gate_a1_v4_source: output/S-vibe-a1-v2.blend
vibe_gate_a1_v4_keep: all v2 head/neck vertices and all non-crest geometry
vibe_gate_a1_v4_exact_edit: replace crest construction/topology only. Remove bilateral paired 3+3 extrusion and rebuild a compact skull-rooted overlapping laminar fan. Do not tune v3 coordinates further.

vibe_gate_a1_v4_status: REVIEW_PENDING
vibe_gate_a1_v4_scope: crest topology only; v2 head/neck and all non-crest geometry fixed
vibe_gate_a1_v4_renders:
- output/review/vibe-a1-v4/S_vibe_a1_v4_side.png
- output/review/vibe-a1-v4/S_vibe_a1_v4_front.png
- output/review/vibe-a1-v4/S_vibe_a1_v4_front34.png
- output/review/vibe-a1-v4/S_vibe_a1_v4_back.png


vibe_gate_a1_v4_decision: REJECT
vibe_gate_a1_v4_reason: bilateral horn towers were removed, but FRONT collapses to a single central needle and SIDE remains a straight sword bundle. Straight-prism blade representation is rejected.
vibe_gate_a1_v5_source: output/S-vibe-a1-v2.blend
vibe_gate_a1_v5_exact_edit: crest only; replace straight prisms with curved tapered laminar blades sampled along smooth centerlines. Preserve v2 head/neck and all non-crest geometry.

vibe_gate_a1_v5_status: REVIEW_PENDING
vibe_gate_a1_v5_scope: curved crest only; v2 head/neck and all non-crest geometry fixed
vibe_gate_a1_v5_renders:
- output/review/vibe-a1-v5/S_vibe_a1_v5_side.png
- output/review/vibe-a1-v5/S_vibe_a1_v5_front.png
- output/review/vibe-a1-v5/S_vibe_a1_v5_front34.png
- output/review/vibe-a1-v5/S_vibe_a1_v5_back.png


vibe_gate_a1_v5_decision: REVISE
vibe_gate_a1_v5_keep: curved laminar crest representation and four-layer crown projection. No return to v1-v4 crest constructions.
vibe_gate_a1_v5_reason: crest representation is materially improved, but A1 still fails global head/neck proportion: neck remains too long and head sits too high/forward relative to the S reference.
vibe_gate_a1_v6_source: output/S-vibe-a1-v5.blend
vibe_gate_a1_v6_exact_edit: neck proportion + rigid head/crest placement only. Preserve head shape, crest shape, thorax and all limbs/tail. Move head+crest as one rigid unit closer/lower to thorax and rebuild only neck stations 5-7 for a shorter continuous transition.

vibe_gate_a1_v6_status: REVIEW_PENDING
vibe_gate_a1_v6_scope: neck proportion + rigid head/crest placement only
vibe_gate_a1_v6_renders:
- output/review/vibe-a1-v6/S_vibe_a1_v6_side.png
- output/review/vibe-a1-v6/S_vibe_a1_v6_front.png
- output/review/vibe-a1-v6/S_vibe_a1_v6_front34.png
- output/review/vibe-a1-v6/S_vibe_a1_v6_back.png


vibe_gate_a1_v6_decision: REVISE
vibe_gate_a1_v6_keep: v5 curved laminar crest; v6 shorter neck; lowered/closer rigid head+crest placement.
vibe_gate_a1_v6_reason: neck/head placement is materially improved, but direct comparison to the locked S references shows the crest still reads as four near-parallel horizontal fins in SIDE/FRONT34 and as a comb of vertical prongs in FRONT/BACK. The reference reads as a compact layered cranial crest with a dominant rear-upward primary lamina and shorter subordinate layers.
vibe_gate_a1_v7_source: output/S-vibe-a1-v6.blend
vibe_gate_a1_v7_keep: v6 head shape, v6 neck proportion/placement, thorax, waist, pelvis, all limbs, feet and tail
vibe_gate_a1_v7_exact_edit: crest only; reduce equal-spacing/parallel-blade construction. Build one dominant rear-upward skull-integrated primary lamina with shorter overlapping subordinate layers. Keep FRONT/BACK silhouette narrow and avoid horn/needle/comb readings.
vibe_gate_a1_next: Render v7 SIDE/FRONT/FRONT34/BACK and STOP. Do not start A2.

vibe_gate_a1_v7_status: REVIEW_PENDING
vibe_gate_a1_v7_scope: crest only
vibe_gate_a1_v7_noncrest_geometry_unchanged: true
vibe_gate_a1_v7_renders:
- output/review/vibe-a1-v7/S_vibe_a1_v7_side.png
- output/review/vibe-a1-v7/S_vibe_a1_v7_front.png
- output/review/vibe-a1-v7/S_vibe_a1_v7_front34.png
- output/review/vibe-a1-v7/S_vibe_a1_v7_back.png

vibe_gate_a1_v7_decision: REVISE
vibe_gate_a1_v7_keep: SIDE/FRONT34 rear-upward layered fan direction; v6 head/neck; all non-crest geometry lock.
vibe_gate_a1_v7_problem: FRONT/BACK still read as narrow vertical horn needles because lamina broad faces are nearly edge-on to those cameras.
vibe_gate_a1_v8_exact_edit: crest only; preserve v7 centerline family but rotate/roll lamina face orientation and modestly broaden the front projection. Do not create bilateral horn towers and do not edit head/neck/body.

vibe_gate_a1_v8_status: REVIEW_PENDING
vibe_gate_a1_v8_scope: crest face orientation only
vibe_gate_a1_v8_noncrest_geometry_unchanged: true
vibe_gate_a1_v8_renders:
- output/review/vibe-a1-v8/S_vibe_a1_v8_side.png
- output/review/vibe-a1-v8/S_vibe_a1_v8_front.png
- output/review/vibe-a1-v8/S_vibe_a1_v8_front34.png
- output/review/vibe-a1-v8/S_vibe_a1_v8_back.png

vibe_gate_a1_v9_status: REVIEW_PENDING
vibe_gate_a1_v9_scope: crest only / multi-angle reference reconstruction
vibe_gate_a1_v9_noncrest_geometry_unchanged: true
vibe_gate_a1_v9_renders:
- output/review/vibe-a1-v9/S_vibe_a1_v9_side.png
- output/review/vibe-a1-v9/S_vibe_a1_v9_front.png
- output/review/vibe-a1-v9/S_vibe_a1_v9_front34.png
- output/review/vibe-a1-v9/S_vibe_a1_v9_back.png

vibe_gate_a1_v9_decision: REVISE
vibe_gate_a1_v9_keep: two broad primary lamina concept, subordinate layers, reference-driven multi-angle construction, all non-crest geometry lock.
vibe_gate_a1_v9_problem: FRONT reads as two oversized separated rabbit-ear plates; SIDE primary plate mass is too thick and tall relative to the approved S reference.
vibe_gate_a1_v10_exact_edit: crest only; lower/narrow the primary laminae, reduce lateral center separation, keep broad plate-face projection, sharpen faceting, and preserve rearward sweep.

vibe_gate_a1_v10_status: REVIEW_PENDING
vibe_gate_a1_v10_scope: crest only / compact crisp plate correction
vibe_gate_a1_v10_noncrest_geometry_unchanged: true
vibe_gate_a1_v10_renders:
- output/review/vibe-a1-v10/S_vibe_a1_v10_side.png
- output/review/vibe-a1-v10/S_vibe_a1_v10_front.png
- output/review/vibe-a1-v10/S_vibe_a1_v10_front34.png
- output/review/vibe-a1-v10/S_vibe_a1_v10_back.png

vibe_gate_a1_v10_decision: REVISE
vibe_gate_a1_v10_keep: compact close two-primary FRONT/BACK projection, lower crest height, skull-integrated root position, all non-crest geometry lock.
vibe_gate_a1_v10_problem: SIDE/FRONT34 laminae became too thin and straight, reading as sword strips rather than C5-style plates.
vibe_gate_a1_v11_exact_edit: crest only; increase Y/Z plate half-width and centerline curvature while reducing roll angle so X/front projection stays approximately v10-sized.
