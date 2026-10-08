# S type R4 head–neck reconstruction — real image review

**Verdict: REJECT. The R4 model must not be used for game or follow-on modeling.**

R4 output: `r4-head-neck/S-authority-head-neck-r4.blend`, `S-authority-head-neck-r4.glb`.
Real 5-view comparison: `r4-head-neck/review/R3_vs_R4_real_five_view.jpg`.

What physically happened in R4:

- Removed 74,617 faces in head/neck ROI of the original TRELLIS-generated GLB, without changing vertices outside it.
- Added a newly modeled full-length head/neck loft plus two broad main lamina, secondary blades, and temporal surfaces.
- Workbench actually rendered 5 standard directions and generated a R3-vs-R4 contact sheet; workflow 37814240922 succeeded.

Visual review: **FAIL**.

- SIDE / FRONT34: smooth loft becomes an oversized, tubular mass with abrupt shoulder attachment. Significantly worse than R3; contradicts the approved dark, tapering athletic S neck.
- FRONT / BACK: body/head segmentation and crest bases remain disconnected; no anatomical integration established.
- The two sweeping crest sheets have more side-profile surface area, but do not compensate for destroyed original silhouette.
- Feet, pelvis, and body remain the original unapproved TRELLIS donor. No animation / topology / rig readiness.

The loft must be **discarded in its entirety**. R5 is a separately tested crest-only variant using the original donor's head and neck, not a continuation of R4's enlarged neck. Don't claim the R4 approach was a success based on closed mesh generation or CI success.

Authoritative S artwork is `art/s-creature/references/00_s_type_modeling_image_v1.png`, SHA256 `93befcfdbe8863abd3140ec6b92d9f06ca2dcbf70bb551334eb063831b9831f6`.
