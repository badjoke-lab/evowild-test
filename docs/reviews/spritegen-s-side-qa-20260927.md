# S sprite motion QA — 2026-09-27

## Scope

S / Sprint only.

Reviewed outputs from the dedicated `spritegen-s-poc` CI artifact.

## Reference extraction verdict

**FAIL**

The technical extraction path works: eight transparent frames are produced, atlas export works, and 2D playback advances. The motion itself is not acceptable as sprint animation.

Observed problems:

- excessive whole-body/head pitch compared with limb articulation;
- fore/hind limb phase separation is weak;
- foot contact is difficult to read;
- several frames differ mainly in body carriage rather than a complete gait cycle;
- the result does not communicate high-speed sprinting strongly enough.

## Consequence

Do not wire this V5 extraction into the race runtime as a final 2.5D run.

Keep it only as a negative comparison baseline.

## Next action

Run the exported S side source through the pinned sprite-gen motion pipeline for `idle,run`. Accept SIDE only if the result clearly improves:

1. independent limb cycling;
2. stance/contact readability;
3. silhouette and identity stability;
4. wrap seam continuity.

Do not proceed to 3/4 front, 3/4 rear, rear, P, E or A until SIDE passes.
