# EvoWild Run — S-type recovery checkpoint

current_stage: S-rebuild-v10 Gate A saved and five views rendered; REVIEW_PENDING / STOPPED
branch: feat/s-creature-model
current_model_file: output/S-rebuild-v10.blend

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

next_action: Review S-rebuild-v10 Gate A only; await decision. Do not proceed to Gate B.

quality_issues:
- v6 is REVISE: the central-only chest lift created a visible horizontal smile-crease/shelf in front and front34. The lower-neck width remains accepted; the remaining correction must be broader and shallower across the anterior thorax.
- The creature remains an unfinished blockout.
- Global morphology mismatch: current S is too deer/gazelle-like and the head/crest silhouette is wrong. The single sagittal horn/crown is unsupported by the authoritative S references and must be removed/rebuilt.

blockers: none

review_status: S-rebuild-v3 Gate A review pending / not accepted
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
gate_a_output: output/S-rebuild-v3.blend
v12_role: rejected morphology baseline; technical donor/checkpoint only

gate_a_status: REVIEW_PENDING
modeling_status: STOPPED
gate_a_source: output/S-rebuild-v2.blend; no v12 geometry used
gate_a_cage_vertices: 760
gate_a_done: Lowered six-plate crest envelope; outward/rearward fan instead of upright prongs or arch; posterior cranium broadened, muzzle retained; Effective neck shortened with lower forward carriage and stronger base flare into withers and chest; Compact withers/thorax strengthened, narrow rising waist retained and light pelvis elevated; Fore upper segment shortened, elbow raised; hind knee forward and hock rearward with sharper chain angles; Tail and all toe geometry unchanged from v2
gate_a_render_geometry_unchanged: true
gate_a_scope: S only; no eyes, Cue Band, materials/textures/color design, animation or final retopology
gate_a_limitation: low-complexity cage with overlapping limb/toe roots; no production welding or surface refinement
gate_a_renders:
- output/review/rebuild-v3/S_rebuild_side.png
- output/review/rebuild-v3/S_rebuild_front.png
- output/review/rebuild-v3/S_rebuild_front34.png
- output/review/rebuild-v3/S_rebuild_rear34.png
- output/review/rebuild-v3/S_rebuild_back.png

gate_a_v1_decision: REVISE
gate_a_v1_reason: The fresh rebuild removes the v12 single central horn and is a better starting direction, but the Gate A silhouette still misses the approved modeling image. Side view is too long-necked and tube-like, torso is too long/flat and under-massed at the shoulder, limbs still read as rods, and the crest becomes two tall horn-like prongs from front/back instead of backward-swept layered cranial plates.
gate_a_v1_keep: fresh-rebuild approach; small wedge head intent; no v12 donor geometry; multi-plate crest concept; narrow waist intent; distinct fore/hind chains; multi-toe feet.
gate_a_v2_priority: crest/head silhouette -> neck proportion -> compact thorax/waist/pelvis -> readable limb joints -> tail length/terminal blade.

gate_a_v2_task: S_REBUILD_V2_TASK.md
gate_a_v2_base_remote_commit: d43db097d9263eb45feda275ae74430589d67808
gate_a_v2_geometry_sha256: 3ce2210a16642f0ac32d8356c3b926c5e3cc6f9cd74e1f4bf17e8bb89548381a
gate_a_v2_done: Saved v2 from v1 with requested silhouette corrections; exactly five view types rendered; 760 vertices/topology retained; geometry unchanged during render.
gate_a_v2_acceptance: pending user review; no PASS claimed
gate_a_v2_limitations: low-complexity faceted plates and overlapping limb/toe roots remain; silhouette acceptance has not been determined

gate_a_v2_decision: REVISE
gate_a_v2_reason: v2 improves side sweep and shortens the overall body/tail, but FRONT/BACK still read as a paired upright horn/arch; neck remains too pipe-like; shoulder/thorax still lacks the locked athletic massing; fore/hind limbs remain too rod-like and insufficiently differentiated. Global silhouette is not yet close enough to the approved modeling image.
gate_a_v2_keep: shorter tail; more rearward crest in SIDE; more compact torso; fresh rebuild basis; S-only scope.
gate_a_v3_priority: eliminate upright horn read in FRONT/BACK -> taper/angle neck into shoulder -> stronger compact thorax/shoulder mass -> distinct fore/hind joint rhythm -> verify tail and pelvis balance.

gate_a_v3_task: S_REBUILD_V3_TASK.md
gate_a_v3_base_remote_commit: 70bf73b78e2a35bf642741d278e914707155edf1
gate_a_v3_geometry_sha256: d37619ae5d18eeadb110407fa2903c9bcecd592363731ae6ac01d812d5d00f57
gate_a_v3_done: Saved v3 from v2; low outward/rearward crest fan, shorter flared neck, stronger compact withers/thorax, distinct fore/hind joint rhythm. Tail and toes unchanged. 760 vertices and topology retained; exactly five views rendered with geometry unchanged.
gate_a_v3_acceptance: REVIEW_PENDING; no PASS claimed
gate_a_v3_limitations: Low-complexity faceted plates and overlapping limb/toe roots remain; whole silhouette similarity and shoulder/neck proportions need user review. No further modeling authorized.

gate_a_v3_decision: REVISE
gate_a_v3_reason: v3 is a real improvement over v2: the crest no longer reads as upright horns and the body is more compact. However Gate A still fails the locked silhouette because the crest plates read as flat pasted-on fins in FRONT/FRONT34, distal limbs still read as rods, the shoulder/pelvis joint masses are too abrupt and geometric, and the overall stance remains more generic ungulate than the approved alien racing silhouette.
gate_a_v3_keep: low rearward crest envelope; shorter flared neck; compact torso; sharper fore/hind chain differentiation; shorter tail from v2.
gate_a_v4_rule: one structural silhouette pass only; no more percentage-only nudges. Rebuild crest roots and limb segment masses as connected forms while preserving Gate A low complexity.


gate_a_v4_task: S_REBUILD_V4_TASK.md
gate_a_v4_execution_status: READY_TO_EXECUTE


gate_a_v4_done: Structural Gate A pass executed from v3; crest roots integrated, thorax compacted, limb masses differentiated; five views rendered.
gate_a_v4_acceptance: REVIEW_PENDING; no PASS claimed
gate_a_v4_geometry_sha256: 5c25e613bead347cb7277d142eadc92aa014445046c870bbea1bc67221a52797
gate_a_v4_renders:
- output/review/rebuild-v4/S_rebuild_side.png
- output/review/rebuild-v4/S_rebuild_front.png
- output/review/rebuild-v4/S_rebuild_front34.png
- output/review/rebuild-v4/S_rebuild_rear34.png
- output/review/rebuild-v4/S_rebuild_back.png

gate_a_v4_decision: REVISE
gate_a_v4_reason: v4 is cleaner than v3 but still fails the locked S silhouette. SIDE remains generic ungulate; FRONT keeps a shield-like thorax; crest reads as bilateral ear/fan geometry rather than narrow skull-integrated rearward laminae; distal limbs remain visually rod-like from front/back.
gate_a_v4_keep: compact thorax depth direction; small wedge head; distinct fore/hind joint rhythm; three-toed feet concept.
gate_a_v5_rule: do not patch v4 geometry. Build a fresh Gate A cage from empty scene with narrower thorax/front silhouette, vertically layered rear-swept crest, stronger limb taper/joint rhythm, and forward-balanced racing posture.
gate_a_v5_task: S_REBUILD_V5_TASK.md


gate_a_v5_done: Fresh Gate A structural cage built from empty scene; five views rendered; v4/v12 morphology not used.
gate_a_v5_acceptance: REVIEW_PENDING; no PASS claimed
gate_a_v5_geometry_sha256: 07cdf197799e6454c4aa33d5ae48a29f039328c8fb310f2423498dd4ec53bd66
gate_a_v5_renders:
- output/review/rebuild-v5/S_rebuild_side.png
- output/review/rebuild-v5/S_rebuild_front.png
- output/review/rebuild-v5/S_rebuild_front34.png
- output/review/rebuild-v5/S_rebuild_rear34.png
- output/review/rebuild-v5/S_rebuild_back.png

gate_a_v5_decision: REVISE
gate_a_v5_reason: FRONT/BACK show the crest as two tall paired horns, which is a hard fail under S_MODELING_IMAGE_LOCK.md. SIDE/FRONT34 improve the compact body direction, so v5 body/limbs are retained for the next correction.
gate_a_v5_keep: v5 fresh-body proportions; narrower front thorax; fore/hind chain differentiation; small three-toed feet; tapered tail.
gate_a_v6_rule: crest-only correction. Lower the crest vertical envelope and keep strong rearward projection so FRONT/BACK no longer read as paired horns. All body, limb, foot and tail vertices must remain bit-identical to v5.


gate_a_v6_done: Crest-only correction executed from v5; all non-crest geometry preserved exactly; five views rendered.
gate_a_v6_acceptance: REVIEW_PENDING; no PASS claimed
gate_a_v6_geometry_sha256: 37fa98fd103ac9087bd9043e724721f52fe85cd45020067a7831b338c84ca17e
gate_a_v6_renders:
- output/review/rebuild-v6/S_rebuild_side.png
- output/review/rebuild-v6/S_rebuild_front.png
- output/review/rebuild-v6/S_rebuild_front34.png
- output/review/rebuild-v6/S_rebuild_rear34.png
- output/review/rebuild-v6/S_rebuild_back.png

gate_a_v6_decision: REVISE
gate_a_v6_reason: Paired-horn hard fail is removed, but the neck still reads too long/tubular and FRONT/BACK keep near-parallel rod-like limb silhouettes. Global read remains too generic ungulate.
gate_a_v6_keep: crest envelope and rearward flow; v5 thorax/waist/pelvis; three-toed feet; tapered tail.
gate_a_v7_rule: lock crest, thorax, waist, pelvis and tail. Change only head/neck station placement plus fore/hind limb chains to create visible joint rhythm from FRONT/BACK.


gate_a_v7_done: Head-neck shortened and limb frontal-plane joint rhythm added; crest/torso/pelvis/tail/toes locked; five views rendered.
gate_a_v7_acceptance: REVIEW_PENDING; no PASS claimed
gate_a_v7_geometry_sha256: 700d2b8e1ca8cea608bdeb2618843942f7f85785af68e9ff5625174b8538dd62

gate_a_v7_decision: REVISE
gate_a_v7_reason: v7 removes the paired-horn failure, shortens the effective neck, and improves frontal limb-axis rhythm. Gate A still fails because FRONT34/REAR34 show abrupt cone-like shoulder/thigh roots, distal limbs remain too visually tubular, and the global read is still too close to a generic slim ungulate rather than the locked alien racing organism.
gate_a_v7_keep: v7 crest envelope; shortened head-neck chain; compact thorax/waist/pelvis; frontal-plane joint offsets; three-toed feet; tapered tail.
gate_a_v8_priority: shoulder/pelvis-to-limb integration -> tapered distal limb cross-sections -> re-check global non-ungulate silhouette. No Gate B.


gate_a_v8_done: Limb-root integration and distal taper pass executed from v7; core/toes locked; five views rendered.
gate_a_v8_acceptance: REVIEW_PENDING; no PASS claimed
gate_a_v8_geometry_sha256: 998286cb18f907082c81e11e3a1d2e3b486a832cf2f3cab39c603353651b6e61
gate_a_v8_renders:
- output/review/rebuild-v8/S_rebuild_side.png
- output/review/rebuild-v8/S_rebuild_front.png
- output/review/rebuild-v8/S_rebuild_front34.png
- output/review/rebuild-v8/S_rebuild_rear34.png
- output/review/rebuild-v8/S_rebuild_back.png

gate_a_v8_decision: REVISE
gate_a_v8_reason: Root overlap and taper improved, but FRONT34/REAR34 still show cone-like shoulder/thigh transitions and FRONT/BACK still read as long tubular distal limbs. The remaining limitation is the sparse limb-ring topology, not the locked core silhouette.
gate_a_v8_keep: entire v8 core body/head/crest/neck/tail; frontal-plane joint offsets; three-toed feet.
gate_a_v9_rule: rebuild only the four limb mesh objects with additional root/transition/distal rings. Core and toe meshes must remain bit-identical. Gate A only.


gate_a_v9_done: Four limb cages rebuilt with denser root/joint/distal transition rings; core/toes locked; five views rendered.
gate_a_v9_acceptance: REVIEW_PENDING; no PASS claimed
gate_a_v9_geometry_sha256: 91d96d535e0db7128cd06a68d47babd5ec5c05ef50cff83ac9d54c5f43aa0732
gate_a_v9_renders:
- output/review/rebuild-v9/S_rebuild_side.png
- output/review/rebuild-v9/S_rebuild_front.png
- output/review/rebuild-v9/S_rebuild_front34.png
- output/review/rebuild-v9/S_rebuild_rear34.png
- output/review/rebuild-v9/S_rebuild_back.png

gate_a_v9_decision: REVISE
gate_a_v9_reason: Denser limb topology improves root continuity and distal taper, but canonical reference comparison shows the crest is still materially wrong: it is too horizontal and plate-bundle-like. public/concept/S.webp and reference 04 C5 require a narrow rear-upward directional crest integrated into the skull line.
gate_a_v9_keep: entire v9 body and all limb/toe geometry.
gate_a_v10_rule: crest-only reference-alignment. Preserve all non-crest vertices exactly. Rearward reach stays long; vertical rise increases modestly; lateral spread narrows and tips converge toward the center so FRONT/BACK do not revert to paired horns.


gate_a_v10_done: Crest-only canonical alignment executed from v9; all non-crest geometry locked; five views rendered.
gate_a_v10_acceptance: REVIEW_PENDING; no PASS claimed
gate_a_v10_geometry_sha256: 48c1fb5bf72505a7062118b4a91cd03ab80c404bf39c946a3a0e2e1619c7fbb6
gate_a_v10_renders:
- output/review/rebuild-v10/S_rebuild_side.png
- output/review/rebuild-v10/S_rebuild_front.png
- output/review/rebuild-v10/S_rebuild_front34.png
- output/review/rebuild-v10/S_rebuild_rear34.png
- output/review/rebuild-v10/S_rebuild_back.png
