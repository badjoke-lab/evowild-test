# P/E/A MF12 Direct-Gait Review

Status: RUNTIME_REVIEW_PENDING

## Purpose

The current high-detail P/E/A six-frame sheets remain visually rough in motion.
Optical-flow interpolation was rejected because it introduced smear, limb collapse,
and double-image artifacts.

This branch uses the already-reviewed Motion First procedural P/E/A gaits as a
motion reference and captures twelve real gait states per cycle. No image
interpolation is used.

## Candidate assets

- `public/concept/p-run-sheet-mf12-v1.webp`
- `public/concept/e-run-sheet-mf12-v1.webp`
- `public/concept/a-run-sheet-mf12-v1.webp`

Layout: 4x3 / 12 direct frames.

Even indices correspond to:
CONTACT / PUSH / LIFT / FLIGHT / REACH / LAND.

Odd indices are actual intermediate gait states sampled from the canonical gait.

## Runtime review

Use only:

`race-quality.html?peaSprite=mf12`

Normal `race-quality.html` continues to use the existing high-detail six-frame
P/E/A assets. S is unchanged in both modes.

Promotion is forbidden until the isolated race-size review passes.
