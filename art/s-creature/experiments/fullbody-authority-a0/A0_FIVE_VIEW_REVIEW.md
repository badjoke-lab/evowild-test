# S-type A0 full-body original reconstruction — visual review

Status: **REJECT / DO NOT PROMOTE.**

## Actual delivered evidence
- Fresh independent model: `S-fullbody-authority-A0.blend` / `S-fullbody-authority-A0.glb` (not derived from TRELLIS or R0-R5 donor geometry).
- Workflow: `37839016311`.
- Five real orthographic views: `review/S_A0_real_five_view_contact.jpg`.
- Approved reference and real five views in one sheet:
  `review/S_A0_authority_reference_and_real_views.jpg`.
- Structural geometry record: `A0_GEOMETRY_FACTS.json`; 32 separately authored pieces; head-neck-thorax-pelvis is a continuous loft, but arms, armor, crest, feet and tail vanes are independent intersecting parts. Not a single skinning-ready watertight mesh.

## Mandatory 5-view verdict
Against the *exact authoritative image* `00_s_type_modeling_image_v1.png` (SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`):

- SIDE **FAIL**: the neck looks like a tube and the body a uniform cylinder; approved original has anatomically sculpted neck-to-shoulder, pronounced chest/waist planes and athletic pelvic mass.
- FRONT **FAIL**: simple round blunt skull instead of narrow wedge/cue band form; pair of crest blades separated but too narrow in frontal width; foreleg girth and attachments are generic and cylindrical.
- FRONT34 **FAIL**: shoulder, thigh, limb articulations read as extruded tubing; shoulder/pelvic armor pieces visibly pasted-on, not integrated.
- REAR34/BACK **FAIL**: tail only loosely matches feather construction, hip/leg musculature does not preserve original S silhouette.
- SPLIT FEET **FAIL**: technically separated toes but unreadable at game scale; exact racing-foot shape is unfulfilled.

## Technical verdict
- Experiment proves free Blender/Actions can produce new editable geometry, GLB and five-view screenshots without imported donor. **This does NOT establish design feasibility.**
- No topology / rig / natural gait / original art fidelity approval.
- Current hand-authored loft/tube method also reproduces the very low-quality generic appearance that prompted this reset.
- **Stop using procedural primitive lofts as the final 3D artistic modeling approach.** Do not waste further passes on only numerical radius or plate changes.
- Next credible production needs direct multi-view sculpt / anatomy-guided retopology from the original locked sheet with explicit trained artistic review, or accept a different visual medium. Neither has been validated to the required quality.
- No changes to production main, race runtime or legacy S model branches.
