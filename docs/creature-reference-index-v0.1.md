# EvoWild Creature Reference Index v0.1

This file is the repository entry point for creature visual references used by the Motion First lane.

## Core concept assets

- [Full creature reference sheet (repository copy)](./references/evowild-creature-reference-sheet-20260921.jpg)


| Reference | Purpose |
| --- | --- |
| [S.webp](../public/concept/S.webp) | Sprint body / silhouette reference |
| [P.webp](../public/concept/P.webp) | Power body / silhouette reference |
| [E.webp](../public/concept/E.webp) | Endurance body / silhouette reference |
| [A.webp](../public/concept/A.webp) | Agility body / silhouette reference |
| [s-run-sheet.svg](../public/concept/s-run-sheet.svg) | S locomotion / running reference |

## Design-sheet rules captured for implementation

The creature concept sheet defines the following design requirements and variation system. These points are recorded here so implementation work does not depend on remembering a conversation screenshot.

### Global rules

- head stays small;
- eyes stay restrained;
- do not mix recognizable faces from existing animals;
- legs, torso segmentation, and body structure need their own species logic;
- individual differences must look like morphological variation of one species, not interchangeable costume parts;
- colors and patterns may be non-natural;
- even an early / simplified version must remain identifiable through silhouette and color;
- every race individual wears a Cue Band.

### Primary morphs

- **S — Sprint:** slender, long-legged, highest-speed emphasis.
- **P — Power:** thick chest / muscular mass, acceleration and force emphasis.
- **E — Endurance:** long, light, stable body for sustained running.
- **A — Agility:** low center of mass, flexible body, corner / poor-surface emphasis.

### Head variation family

The sheet includes a controlled family of head forms:

- standard;
- elongated;
- broad;
- low-carriage;
- high-carriage;
- crest-emphasis.

These remain variations of the same underlying head anatomy.

### Crest / horn variation family

The sheet includes:

- none;
- small;
- rear-flowing;
- branched;
- plate-like;
- branching / antler-like.

Crests are structural extensions of the head/body design. They must not look like arbitrary accessories.

### Tail variation family

The sheet includes multiple tail families covering:

- short;
- standard;
- long;
- bifurcated;
- plate / blade-like;
- flowing / streamlined.

Tail form may strongly alter silhouette and balance impression, but still belongs to the same species.

### Limb / foot variation family

The sheet includes controlled differences such as:

- standard;
- slender;
- thick;
- multi-jointed;
- plate-like;
- claw-like.

The purpose is to avoid simply copying a familiar real-world animal leg.

### Surface / marking variation family

The sheet allows:

- plain;
- bands;
- spots;
- lightning-like markings;
- emissive patterns;
- translucent treatment.

These are secondary to body structure.

### Color

The sheet explicitly permits strong non-natural palettes. Color is useful for individual recognition, but must not be the only difference between S/P/E/A.

### Race readability

The race example in the sheet establishes a minimum requirement: even with simplified rendering, runners should remain distinguishable through:

- silhouette;
- body type;
- color;
- markings;
- Cue Band.

### Cue Band

The Cue Band is a head-mounted race instruction device shared by all runners.

Its visual language includes:

- a band / frame fitted to the species head;
- side cue elements;
- signal / status light;
- readable orientation from multiple angles.

The device must adapt to head variation without changing its function.

## Implementation links

- [Motion First Creature Standard](./motion-first-creature-standard-v0.1.md)
- [Motion First Development Plan](./motion-first-development-plan-v0.1.md)

Any Motion First creature implementation should start from this index and the linked files before editing geometry or gait.
