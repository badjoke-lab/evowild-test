# EvoWild Run — 2.5D Game-First Delivery Plan
Date: 2026-10-24
Status: working plan; no changes to canonical decisions unless separately approved.

## Why this exists
The project has over-invested in Creature art experiments while the game loop remains fragmented. This lane builds a playable game around existing S/P/E/A placeholders. It runs independently of 3D S work and the experimental P rig. No REVISE art is promoted.

## Current audited state (main cde1bd7c)
- 2.5D `race-quality.html`: 18 racers, 1600m default course, four morph 6-frame run sheets, fixed-step race, overtaking, lane changes, course-looking terrain and banking, PUSH/CONSERVE/CLEAR Agent feedback, results.
- This 2.5D runtime used one hardcoded distance and visual terrain, not modular Course conditions with competitive impact.
- The separate Motion First simplified race has four preconfigured race courses, Race Entry and Agent choices/history. Those mechanics are potential donors, **not proof of completion in the 2.5D runtime**.
- `feat/2p5d-roadlab-isolated-20260925` has an isolated road rendering experiment, not a production Course Builder.
- Creature reference lock in `AGENTS.md` and `docs/2p5d-creature-reference-lock.md` is mandatory.

## Product target: complete first player loop
HOME → STABLE (view/select Creature) → COURSE (choose or build)
→ ENTRY (Creature + Agent + plan) → WATCH RACE → RESULTS
→ HISTORY → select breeding parents → NEXT GENERATION → STABLE.

The initial version is browser-first and wallet-free. A connected wallet remains strictly optional; monetization must not sell race advantages. Creature runs are observational; the assigned Agent acts via predefined rules, not player movement controls.

## Parallel workstreams and integration gates
1. **Course Engine and Race Integration** (this branch)
   - Structured segments with distance, width, curve, grade, surface, weather.
   - Pick different Course presets inside the existing 2.5D race; render course state.
   - Pace and stamina effects must be calculated per runner and segment; no scripted winner or fake course bonus.
   - Preserve the original Ridge 1600 result logic for default profile.
   - Gate: deterministic cross-course classification comparisons, mobile + desktop playback, pass existing race tests.
2. **Course Builder** (next)
   - Module list (straight, curves, climbs, descents, narrow/wide, terrain); visual editor of segment order and parameters.
   - Validate continuous segments and distance bounds; save draft locally; export/import Course JSON.
   - Preview a real race on the created Course without changing game source code.
   - Later: Course ID, record/history, publication, moderation and trustworthy validation.
   - Gate: edits change actual race inputs and outcome; invalid modules cannot be raced; shareable Course JSON round-trips.
3. **Player Entry, Race Setup and Results**
   - Select owned Creature and assigned Race Agent from a stable view.
   - Show Course Fit, current traits, strategy, known limits, choose one entry; do not silently control all 18 Agents.
   - Race viewing remains observational; retain fixed-step reproducibility, finish order and per-race evidence.
   - Gate: Home → Entry → Race → Result can be completed without debug query strings.
4. **Genetics, Lifespan and Breeding**
   - Define versioned Genome/Creature schema, inheritance with bounded variation, age/lifespan, retirement, parent IDs, generation, family tree.
   - Breed from selected valid parents and create an owned offspring; the offspring's actual characteristics affect future race conditions.
   - Gate: child has valid parent provenance, reproducible inherited attributes, and does not overwrite parents; retirement rules enforced.
5. **Persistent Stable, History and Asynchronous Competition**
   - Establish account-free local prototype first with explicit versioned save/import/export, then choose remote authority as a separate design decision.
   - Preserve Creature/race/Agent/Course history and recorded Course versions for replay and audit.
   - Later: schedules, asynchronous challenges, tournament and user-created Course publication with anti-cheat design.
   - Gate: reload and version migration preserve all saved history; multiplayer claims need server verification.
6. **Presentation & Content Quality (independent from game engine)**
   - Camera composition, speed, road rendering, environmental readability, HUD/collision, desktop and mobile.
   - S/P/E/A assets get independent identity and motion KEEP gates. 3D cannot block Course/Agent/Breeding delivery.
   - Gate: no paper-cutout motion, no ungrounded redesign; racing remains legible at game size.

## Work order now
- Slice A (implemented in this branch): Course data module, profile selector, segment-based pace/stamina, terrain, surface state, regression tests.
- Slice B: demonstrate that the **same 18 racers** produce genuinely different distributions in at least 3 selected courses. Tune only evidence-backed effects, not hardcoded winners.
- Slice C: functional modular Course Builder that supplies exactly the same race input as presets.
- Slice D: Game menu and Stable/Entry/Result navigation with persistent local state.
- Slice E: versioned genealogy, lifespan and breeding loop.
- Slice F: broader game integration, asynchronous play and eventual production architecture.
- Creature art corrections continue in a **separate** workstream, with no hard dependency for A–E.

## Current slice limitations (be explicit)
- Course presets are **prototype**, not finalized race formats or official rules.
- Sections apply per-segment factors for pace/stamina, derived terrain and a visible active surface. Narrow width currently increases congestion-related pace loss; it does not yet physically close lanes.
- It does not implement user Course editing, weather transitions, alternate track topology or a player economy.
- Do not call this finished or deploy it as canonical until test runs and visual inspection are recorded.

## Verification policy
A green CI run is not itself a visual quality gate. Record the source commit, desktop/mobile captures, real game-level results, and KEEP/REVISE. Test new Course options and the unchanged default independently. Do not merge to main before explicit quality review.
