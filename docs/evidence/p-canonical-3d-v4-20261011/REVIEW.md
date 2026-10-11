# P canonical v4 — actual GLB image review

**Decision: REVISE, production HOLD.** Reference remains `public/concept/P.webp`. This review is about character identity and real rendered anatomy; workflow success is not shape approval.

## Verified deliverables
- Candidate: `public/models/evowild-p/p-canonical-v4.glb` (2,155,896 bytes, 60,152 authored triangles, 17 bones).
- Real model rendering, five rest views: `SIDE.png`, `FRONT.png`, `FRONT34.png`, `REAR34.png`, `BACK.png`.
- Reference and older models in side-by-side: `comparison-v1-v2-v3-v4.png`.
- Run study: `running-review.mp4`, `running-contact-sheet.png` and `run-authoring-check.json`.
- Browser loading: desktop five views, Pixel 7 emulation SIDE/FRONT34, no captured errors or failed requests.
- Dedicated GitHub Actions `38112185984`: SUCCESS, model/renders committed at `abe158280cf55ac26710be126b127d8a0ba1daa5`.

## Anatomical decision from actual images
| Region | Observed vs v3 | Assessment |
| --- | --- | --- |
| Upper forelimb | The severe flat-ended box of v3 is softened into a rounded swelling and tapered elbow shape in SIDE and FRONT34. The red muscle remains prominent. | **Partial positive**; better than v3 in this localized feature |
| Chest, scapula and forelimb junction | Main upper arm still visually detaches from shoulder and chest, with visible discontinuity at the near-vertical muscle boundary. A rounder loft does not produce continuous anatomical topology. | **REVISE; principal blocker** |
| Canonical overall proportions | v3's compact body retained. Compared with the source P, the upper torso still appears long, more barrel-like, and less layered/weight-bearing, while the gray shins are relatively thin and smooth. | **REVISE** |
| Head, mouth and crest | Inherited v3 simplified geometric muzzle and relatively detached blades; reference has more interlocking, carefully defined planes. | **REVISE** |
| Rear haunch/tail | Segmented red attachments and synthetic-looking tail-tip shapes remain. Rear topology lacks authoritative reference. | **UNVERIFIED / REVISE** |
| Foot placement, gait, loop | Only the same 0.8-second provisional in-place motion is captured. IK reach clips=0 is **not** proof of fixed real-world sole contacts, low penetration or acceptable racing gait. | **NOT APPROVED** |

The authored triangle count went from v3 **74,488** to v4 **60,152**, while GLB size decreased from 2,643,324 to 2,155,896 bytes. Smaller geometry is useful but not a success criterion for visual fidelity by itself.

## Next technical decision — stop repetitive isolated-lobe tuning
The problem is no longer simply the radius of a leg loft. V1 used detached red lobes; v3 made a box; v4 rounds the box. The underlying shoulder/chest/upper-arm **continuous surface** is still wrong.

The next candidate must replace the **chest-scapula-forelimb anatomy construction**, using either a genuinely joined surface (with carefully inspected remesh/retopology/skinning consequences) or controlled sculpted mesh continuity. Simply replacing the isolated forearm with another loft of slightly different dimensions will not pass.

Propose and verify **one** joined-anatomy approach in a review-only branch/asset; compare real five-view renders before any gait/18-runner performance integration. Preserve v1-v4, all canon assets, 2.5D, and main. Explicitly distinguish unknown rear/face structure inferred from single-view source.

**Do not merge or declare creature completion.**
