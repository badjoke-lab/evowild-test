# Motion First S v1 Visual Review — 2026-09-25

Status: **FAIL — Phase A remains open**

Evidence source:

- CI run: `36158907021`
- isolated inspection mode: `preview-motion-first/?inspect=1`
- reviewed views: SIDE / LOW / CHASE / FRONT
- implementation baseline: main after PR #24 and inspection harness PR #26

This review is evaluated against:

- `docs/references/evowild-creature-reference-sheet-20260921.jpg`
- `public/concept/S.webp`
- `docs/motion-first-creature-standard-v0.1.md`

## What improved from the original primitive

- the neck is no longer a tall vertical generic-animal neck;
- the head is smaller and more directional;
- a rear-flowing crest is present;
- the body is split into front/rear masses;
- the tail is articulated;
- the Cue Band follows the head rather than floating around a generic skull;
- the S runner can be isolated and reviewed consistently from multiple cameras.

These are implementation improvements only. They do not make v1 acceptable.

## Blocking defects

### 1. SIDE silhouette is still not the concept creature

The body reads as a collection of primitives rather than one continuous evolved racing organism.

Observed:

- chest and pelvis are too round / bulbous;
- the waist is too abrupt;
- head-to-body spacing is too long;
- the neck/head transition feels partially detached;
- shoulder plates are large rectangular slabs;
- crest elements read as separate spikes rather than integrated head structure.

Required correction:

- longer, lower, more continuous torso;
- shallower chest and pelvis;
- shorter visual gap from chest to head;
- tapered plates, not rectangular panels;
- crest rooted into the skull/neck line.

### 2. Limb design is too stick-like

Observed:

- lower limbs become long black rods;
- joint hierarchy is readable as construction pieces rather than anatomy;
- feet are small block/toe assemblies with weak contact silhouette;
- front/rear limb structure does not yet resemble the concept sheet.

Required correction:

- keep non-real-animal anatomy, but make each limb read as one designed structure;
- reduce black exposed segment length;
- increase taper and directional joints;
- improve foot profile and ground-contact area;
- preserve long-leg S proportions without looking skeletal.

### 3. FRONT view fails species identity

Observed:

- the creature becomes tall and bird/giraffe-like from the front;
- chest width and head/neck relation are not convincing;
- shoulder plates dominate the silhouette;
- limbs collapse visually into narrow sticks.

Required correction:

- broaden the structural chest slightly while keeping it shallow;
- lower the neck line;
- reduce shoulder-panel width;
- give forelimbs clearer lateral separation and designed joint shapes.

### 4. LOW view exposes tail and underside problems

Observed:

- tail dominates the frame;
- tail length and upward angle are excessive;
- underside is mostly disconnected primitive shapes;
- feet and lower limbs do not hold up close to ground level.

Required correction:

- shorten tail and lower its default line;
- reduce blade size;
- clean the underside connection between chest, waist, pelvis and limb roots;
- strengthen foot/contact geometry.

### 5. Cue Band is still too blocky

Observed:

- side modules are rectangular blocks;
- the device is readable, but not yet integrated with the intended streamlined head.

Required correction:

- thinner band;
- smaller side modules;
- keep the status lights;
- preserve the head silhouette rather than widening it.

## Decision

**Do not begin Phase B gait work yet.**

The next implementation pass remains Phase A and must alter only the S body / limbs / tail / Cue Band geometry.

P / E / A stay as placeholders.

## v2 target

S v2 must achieve:

- continuous low forward silhouette in SIDE;
- no large rectangular shoulder slabs;
- no long black stick lower legs;
- shorter/lower tail;
- better structural continuity in FRONT and LOW;
- recognizably closer to `public/concept/S.webp` before gait quality is evaluated.
