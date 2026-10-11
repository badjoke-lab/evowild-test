# P canonical 3D v3: real-image review (2026-10-11)

**Decision: REVISE / production HOLD. Do not promote or merge.**

## Authority and evidence
- Highest P species reference: `public/concept/P.webp` (unchanged).
- Earlier candidates: `public/models/evowild-p/p-canonical-v1.glb`, `p-canonical-v2.glb`.
- v3: `public/models/evowild-p/p-canonical-v3.glb`, generated and committed by GitHub Actions `38104798557` as commit `d891133aa8c5c3811b80834e1cc8f0454906a134`.
- Actual visual comparison: `comparison-v1-v2-v3.png`.
- Actual v3 5-view captures: `SIDE.png`, `FRONT.png`, `FRONT34.png`, `REAR34.png`, `BACK.png`.
- Provisional gait review: `running-contact-sheet.png` and `running-review.mp4`.
- Browser validation: no page errors or failed requests in saved desktop and Pixel 7 emulation results; no physical Android test.

## What the actual images show

| Anatomy | v3 against v2 and canonical | Decision |
| --- | --- | --- |
| Fore–aft silhouette and volume | 12.5% longitudinal compression makes v3 more compact and reduces v2's overlong rear-body impression. Still not fully matched to the original high/forward P shoulder and chest. | **KEEP hypothesis only**, not approved final proportions |
| Upper arm and shoulder | Removing the detached red shell simplified the topology, but the replacement single loft becomes a **boxy, flat-ended red column** in SIDE and FRONT34. More mechanical than the canonical P's interlocking curved muscle masses; some v2 views read more organic. | **REJECT current forelimb construction** |
| Chest-to-shoulder transition | Shoulder remains partially detached from upper forelimb and chest, despite mesh/color changes. | **REVISE; needs integrated anatomical surface** |
| Back/flank | Red dorsal mass still reads as a smooth uninterrupted shell; the canonical has more segmented interlocking musculature and a pronounced shoulder/waist relationship. | **REVISE** |
| Head/crest | v2 baseline inherited; swept crest broadly directional but the dark planar muzzle and upright front-view roots remain simplified. | **REVISE** |
| Elbow/wrist/sole | Hard joint boundaries persist. Paired screenshots/0.8s gait clips do not prove contact-lock or sliding reduction. | **NOT APPROVED** |
| Rear view | A plausible inferred shape, but no canonical rear turnaround exists to certify it. | **UNVERIFIED** |

## Build and cost

The isolated v3 Blender / browser / capture / artifact commit workflow completed SUCCESS. This confirms a real versioned model and reproducible captures, **not character quality**.

v3: **74,488 authored triangles; 2,643,324 bytes GLB; 17 bones**. V2: 56,152 authored triangles; 2,020,324 bytes GLB. Geometric complexity increased approximately 33% without demonstrating a comparable visual-quality gain. No 18-runner performance benchmark has been performed; optimize only after anatomy is accepted.

## Next modification gate

1. **Preserve v3 as a negative/partial-positive comparison**, not a new modeling authority.
2. Keep the hypothesis of a more compact, high-chested torso, but do not assume 0.875 globally is an approved ratio; compare actual shoulder-to-haunch landmarks to the original.
3. Reconstruct the red shoulder–upper arm–dark forearm as a continuous curved anatomical volume, avoiding both v2's detached lobe and v3's squared-off tube; use a single sculpted outer contour and review from FRONT34/FRONT/REAR34, not only SIDE.
4. Define shoulder, elbow, wrist and foot landmarks in model space so future rig weighting can preserve their shapes in flexion.
5. Hold the 18-runner production race, 2.5D lane, S/E/A, main, and automatic model promotion unchanged.
6. Only after **shape KEEP** assess gait, true rendered sole contact and 18-runner FPS/identifiability.

**No completion or user approval is implied.**
