# AutoSprite S Sprint Trial v0.1

## Scope

This lane evaluates **S / Sprint only**. Do not generate or integrate P, E, or A here.

The source-of-truth visual input is:

- `public/concept/S.webp`
- `docs/creature-reference-index-v0.1.md`
- `docs/references/evowild-creature-reference-sheet-20260921.jpg`

Existing procedural 3D creatures and the existing 2.5D bob/tilt motion are not shape references.

## User-side AutoSprite action

Generate exactly one animation first:

- Character image: `public/concept/S.webp`
- Animation: Run or a custom high-speed quadruped/creature sprint
- Direction: use the race-facing side view for the first pass
- Export: regular AutoSprite PNG spritesheet + JSON atlas
- Do not spend credits on idle/walk/jump/attack or P/E/A yet

After export, provide the ZIP here. The integration lane will normalize the filenames.

## Repository file contract

The runtime looks for exactly:

- `public/autosprite/s/sprint.png`
- `public/autosprite/s/sprint.json`

The JSON may use standard AutoSprite `frames` data and optional `animations` / `meta.framerate` fields.

## Runtime behavior

Page: `race-autosprite-s.html`

- S uses the AutoSprite frames when both export files exist.
- S's old fake bob/tilt motion is disabled while AutoSprite is active.
- P/E/A keep the existing static reference assets for comparison only.
- If the export files are absent, the page visibly reports that it is using the baseline fallback.
- No generated asset is accepted as production merely because it loads.

## Acceptance gate

Judge the actual running loop on:

1. S silhouette remains recognizably the same creature across frames.
2. Head, limbs, tail and Cue Band do not mutate frame-to-frame.
3. Foot contact and stride read as forward sprint rather than floating.
4. Body orientation remains coherent with track direction.
5. No severe background-removal halo or clipped anatomy.
6. At race scale, the motion remains readable.
7. It is materially better than the static-image bob/tilt baseline.

If any of 1-5 fails badly, stop and regenerate S. Do not expand to other morphs.
