# EvoWild Run P 3D — independent v7b rescue static review

**2026-10-14 / RESULT: SHAPE REVISE, PRODUCTION REJECT / HOLD.**

This is not Codex's lost original v8. The local commit `cc1dab82305370c8954fa51124750c2feb612f50` was not on GitHub and its original workspace was inaccessible because the Codex execution server rejected process creation. It would be misleading to call the reconstruction "v8 restored".

## Real deliverables

- Branch: `exp/p-3d-rescue-20261014`, intentionally isolated from `fix/3d-p-canonical-model-20261011`.
- Source: `art/p-creature/workspaces/P-v7b-rescue-static.blend`.
- Actual re-importable GLB: `public/models/evowild-p/p-canonical-v7b-rescue.glb`.
- Reference: `public/concept/P.webp`, untouched.
- Actual five-view GLB renders: `SIDE.png`, `FRONT.png`, `FRONT34.png`, `REAR34.png`, `BACK.png`, `five-views.webp`.
- Canonical/v7/v7b contact sheet: `canonical-v7-v7b-comparison.webp`.
- Procedural evidence: `AUTHORING.json`, `RENDER_PROVENANCE.json`, `VALIDATION.json`.
- GitHub Actions `38510117428`: successful Blender 4.3.2 build, actual GLB roundtrip render, evidence packaging and branch push.

## Verified engineering

- Sculpt moved 2,770 real vertices on the shared thorax/scapular/pectoral skin (max displacement 0.163 Blender units).
- Modified 9 tail-root cage vertices before surface subdivision.
- Exact Blender boolean union of the adjusted root and continuous trunk was successful: **1 connected component, 0 boundary edges, 0 non-manifold edges**.
- The initial union accidentally produced an all-white tail due to missing vertex-color attributes; that failed capture is superseded by the corrected asset. Tail material painting now covers **2,664 face loops** and rerender confirms the white defect is gone.
- The rebuilt GLB is **static only**, 0 animations, no armature. No running-motion claim can be made.

## Art review against the actual canonical reference

| Part | Real visual finding | Gate |
| --- | --- | --- |
| Pectoral/chest | Large uninterrupted grey plane remains unlike canonical separated chest muscle groups. | REVISE |
| Shoulder/scapula | Mild relief increase, but red muscle layering and shoulder-to-arm anatomy remain oversimplified. | REVISE |
| Front limbs | Long narrow shins and overly straight tube-like profile compared with dense, heavy canonical forelimbs. | REVISE |
| Tail root | **Topology KEEP** for the integrated connection; actual silhouette is still a short thin taper, unlike canonical broad muscular tail. | Shape REVISE |
| Head / crest | Existing stylized simplified head and oversized linear crest still deviate from canonical contours. | REVISE |
| 5-view robustness | Actual angles recorded; rear/frontal shape inferred from one primary authority illustration. No verified unseen views. | UNVERIFIED |

**Decision:** Reusable technical result is the connected tail-root mesh and verified GLB evidence pipeline. Reject any claim that this candidate reaches the static shape gate or restores v8. Do not make a v7c of Gaussian/radius tweaks. A reference-visible Blender sculpt/retopology of the entire muscle structure is required to materially close the shape gap.

Do not merge main, change the original 3D branch, overwrite versions v1–v7, or modify 2.5D. If the original Codex v8 becomes accessible again, audit and save it separately without overwriting this rescue experiment.
