# S Authority R0-A2 v1 Plan

Status: **LOCKED FOR EXECUTION**

Accepted input:

`output/S-authority-r0-v2.blend`

Accepted prior gate:

`S_AUTHORITY_R0_A1_V2_REVIEW.md` → **KEEP / ACCEPT R0-A1**

Highest authority:

`references/00_s_type_modeling_image_v1.png`

## Scope

R0-A2 edits only:

- shoulder / anterior thorax mass;
- waist / abdominal tuck;
- pelvis / upper hindquarter mass.

R0-A1 head, dominant crest pair, secondary crest and neck line are hard-locked.

R0-A3 distal leg rhythm, R0-A4 split feet and R0-A5 long layered tail remain blocked.

## Authority mismatch to correct

Current donor body still reads as a light smooth deer/gazelle scaffold:

- shoulder/chest is too narrow and weak;
- torso transitions into a long nearly uniform tube;
- abdominal tuck is too shallow;
- pelvis/upper hindquarter is too small relative to the shoulder;
- shoulder → tucked waist → pelvis rhythm from the authority is absent.

## Locked v1 hypothesis

Use one smooth coordinate field on the existing continuous body, with no topology change:

1. **Shoulder / thorax**
   - expand lateral mass strongly;
   - deepen the anterior thorax;
   - keep the transition into the accepted neck fixed at the A1 boundary.

2. **Waist**
   - narrow lateral mass moderately;
   - raise the ventral abdomen to create the authority's deep racing tuck;
   - preserve the dorsal line as much as possible.

3. **Pelvis / upper hindquarter**
   - expand lateral mass;
   - add controlled vertical depth;
   - stop before the tail and distal hindlimb envelope.

## Hard fixed

- every R0-A1 head/neck vertex;
- entire accepted crest object;
- body topology / vertex count;
- all body vertices outside the declared A2 mass envelope;
- distal limbs below the A2 body envelope;
- all separate toe objects;
- feet;
- tail beyond the pelvis envelope;
- cameras.

Because the donor body is already a continuous union, the proximal limb root surface inside the shoulder/pelvis envelope is treated as part of the body junction. Distal limb segments remain fixed for R0-A3.

## Review

Render SIDE / FRONT / FRONT34 / REAR34 / BACK and stop.

Decision must be based on actual images against the exact authority. Do not start R0-A3 before R0-A2 acceptance.


## Numeric execution lock

Coordinate convention: front = negative Y.

A2 body envelope:

- Y: -0.16 .. 1.14
- Z: >= 0.66
- every R0-A1 vertex (source-space Y <= -0.18 and Z >= 0.84) remains exact;
- all vertices outside the A2 envelope remain exact.

Mass fields:

- shoulder / anterior thorax center Y = 0.05, support -0.16 .. 0.36;
- waist center Y = 0.52, support 0.26 .. 0.78;
- pelvis / upper hindquarter center Y = 0.88, support 0.62 .. 1.14.

Target deformation:

- shoulder lateral scale: up to +42%;
- shoulder ventral deepening: up to 0.105;
- shoulder dorsal lift: up to 0.035;
- waist lateral scale: down to 74%;
- waist ventral tuck: raise by up to 0.145 while preserving dorsal line;
- pelvis lateral scale: up to +34%;
- pelvis ventral deepening: up to 0.055;
- pelvis dorsal lift: up to 0.045.

Hard limits:

- body topology and vertex count unchanged;
- non-manifold edge count remains 0;
- max body displacement <= 0.19;
- R0-A1 head/neck body coordinates exact;
- accepted crest mesh exact;
- all toe meshes exact;
- review cameras exact;
- render only SIDE / FRONT / FRONT34 / REAR34 / BACK and stop.
