# EvoWild Run — Design Specification v0.1

Status: Draft  
Project name: EvoWild Run (provisional)  
Purpose: Current design baseline before Race Agent design  
Last updated: 2026-09-22

Visual system map:

https://whimsical.com/evowild-run/evowild-run-game-structure-v0-1-7CNfLG8AoC7nKkcmvH2D6F

---

## 1. Purpose of this document

This document records the current game-design baseline for EvoWild Run.

It is not a final game specification.

The project is still in an early design and validation stage, and several major systems remain undecided.

The purpose of this document is to separate:

- decisions that are already fixed,
- the current design direction,
- ideas that are still provisional,
- and questions that remain open.

The Whimsical system map is the visual representation of the current structure.

This Markdown document is the detailed written specification.

When the design changes, both should be updated when the change affects their scope.

---

## 2. Status labels

The following labels are used throughout this document.

### FIXED

A project-level rule currently treated as a constraint.

Changing it would be an explicit design change.

### CURRENT

The design currently being used as the working direction.

It may still change as prototypes and later systems are developed.

### PROPOSED

An idea that has been accepted for further design or testing, but is not yet a settled implementation requirement.

### TBD

Not yet decided.

No implementation should assume a specific answer unless required for an isolated prototype.

---

# 3. Project premise

## 3.1 Basic game concept

**CURRENT**

EvoWild Run is a game built around fictional racing Creatures.

The current core loop is:

**genetic information → individual abilities and traits → race results → selection of future parents → next generation**

The game is intended to combine:

- individual Creatures,
- raising,
- breeding,
- inheritance,
- bloodlines across generations,
- racing,
- and competition under different environmental conditions.

These mechanics are not treated as inherently novel.

The design goal is to determine how they should interact to form EvoWild Run as a game.

---

# 4. Blockchain-related constraints

## 4.1 Wallet participation requirement

**FIXED**

Wallet connection must not be a mandatory condition for participating in the game.

A player must be able to participate without connecting a blockchain wallet.

This does not mean wallet integration is prohibited.

Optional wallet-linked interactions may exist later.

The exact effects of wallet connection are still TBD.

---

## 4.2 Game-specific token

**FIXED**

EvoWild Run will not issue a game-specific token under the current project rules.

The game must not depend on owning a project token in order to function.

---

## 4.3 Creature NFTs

**FIXED**

Creatures will not be issued as NFTs.

The game is not being designed around selling Creature NFTs or making NFT trading the primary gameplay or economic loop.

---

## 4.4 Play-to-Earn

**FIXED**

Play-to-Earn is not the purpose of EvoWild Run.

Economic rewards must not define the core reason to play the game.

---

## 4.5 Why blockchain remains under consideration

**CURRENT**

The project is testing whether blockchain can have a meaningful role after removing:

- mandatory wallet entry,
- a game-specific token,
- Creature NFTs,
- and Play-to-Earn as the main premise.

Possible areas where blockchain may eventually be useful include long-lived and externally verifiable history such as:

- Creature history,
- bloodline history,
- Course history,
- competition history.

No final blockchain scope has been chosen.

Whether some or all of these records should instead remain in a conventional database is still TBD.

---

# 5. Creature system

## 5.1 Creature identity

**CURRENT**

Each Creature is an individual.

Creatures are not intended to be interchangeable copies of a single stat template.

Individual differences must matter to gameplay.

The exact identity model and data schema are TBD.

---

## 5.2 Genetic information

**CURRENT**

Creatures have inheritable information that affects the abilities and traits expressed by an individual.

Current conceptual flow:

**Genetic information  
→ individual abilities and traits  
→ race performance/results  
→ parent selection  
→ next generation**

The detailed genome representation has not yet been defined.

---

## 5.3 Inheritance

**CURRENT**

Traits from parent Creatures influence offspring.

The system should support bloodlines developing across multiple generations.

The exact rules for:

- inheritance,
- recombination,
- mutation,
- dominance,
- hidden traits,
- and trait ranges

are TBD.

No specific genetic model should yet be treated as final.

---

## 5.4 Raising / development

**CURRENT**

A Creature is not intended to be completely determined at birth.

Raising or development after birth must affect the individual in some way.

The boundary between:

- inherited characteristics,
- trainable characteristics,
- permanent development,
- temporary condition

is TBD.

---

## 5.5 Universal optimum

**CURRENT DESIGN GOAL**

The game should avoid converging too easily toward one universally strongest Creature.

A Creature may be advantageous under one set of race conditions and less advantageous under another.

This is one reason Course and race conditions are intended to affect which traits are valuable.

---

# 6. Race system

## 6.1 Purpose of racing

**CURRENT**

Racing is the main environment in which Creatures are tested against competition conditions.

Race results feed back into future breeding decisions.

Conceptually:

**Creature  
+ Course / race conditions  
→ Race  
→ Race Result  
→ Parent Selection  
→ Breeding  
→ Next Generation**

---

## 6.2 Race types

**TBD**

Specific race categories have not been finalized.

There is currently no canonical list such as:

- sprint,
- endurance,
- obstacle,

or equivalent categories.

They must not be treated as decided game modes.

---

## 6.3 Race condition diversity

**CURRENT**

Race environments should differ enough that different Creature characteristics can become advantageous.

Candidate Course/race variables currently include:

- total distance,
- width,
- corner radius / corner sharpness,
- straight length,
- elevation,
- slope,
- surface,
- corner count,
- bottlenecks,
- weather,
- surrounding environment.

These are current design variables, not yet a complete schema.

---

## 6.4 Examples of condition effects

**CURRENT CONCEPT**

Examples include:

- long straights may increase the value of top speed,
- sharp corners may increase the value of cornering ability,
- major elevation changes may increase the value of climbing ability or endurance,
- narrow sections may make positioning more important,
- mud, sand or snow may make surface aptitude important.

These examples describe the intended relationship between Course conditions and Creature suitability.

They are not yet final Race Engine formulas.

---

## 6.5 Player activity during a race

**TBD**

The exact role of the player after a race begins has not yet been finalized.

Open questions include:

- direct control,
- pre-race strategy,
- commands during the race,
- automated decision-making,
- AI-assisted decision-making,
- or combinations of these.

Race Agent design is intentionally outside v0.1 and is the next major design topic.

---

# 7. Course system

## 7.1 Course as competitive environment

**CURRENT**

A Course is not intended to be only scenery.

Course conditions affect which Creature abilities and traits are advantageous.

Conceptual relationship:

**Course conditions  
→ advantageous abilities and traits change  
→ race results change  
→ different parents may be selected  
→ bloodlines may develop in different directions**

---

## 7.2 Course data

**CURRENT DIRECTION**

The Race Engine should eventually be able to treat the Course as structured data rather than relying entirely on handcrafted race logic.

Candidate Course data includes:

- segments,
- length,
- width,
- curvature,
- slope,
- elevation,
- surface,
- environment,
- weather,
- rules.

The final Course schema is TBD.

---

# 8. Course Builder

## 8.1 Player-created Courses

**PROPOSED / CURRENT DIRECTION**

Players should eventually be able to create Courses.

The initial direction is modular Course construction rather than unrestricted professional 3D modelling.

Candidate modules include:

- Straight,
- Left Curve,
- Right Curve,
- Uphill,
- Downhill,
- Narrow,
- Wide,
- Bridge,
- Tunnel,
- Mud,
- Sand,
- Grass,
- Rock,
- Snow.

The module list is provisional.

---

## 8.2 Relationship to breeding

**CURRENT DESIGN GOAL**

A player-created Course should be able to function as a competitive environment that affects breeding decisions.

Players may:

- breed Creatures for existing Courses,
- create Courses that test particular Creature characteristics,
- create environments that encourage different breeding directions.

The Course Builder is therefore connected to the Creature / breeding system rather than existing only as a decorative editor.

---

## 8.3 Course validation

**PROPOSED**

Player-created Courses should eventually pass validation before being used in higher-trust competitive contexts.

A previously discussed lifecycle is:

**Draft → Test → Community → Validated → Official**

This lifecycle is provisional.

Validation rules have not yet been defined.

---

## 8.4 Course history

**CURRENT DIRECTION**

Courses may have persistent identity and history.

Possible recorded information includes:

- Course ID,
- creator,
- first publication date,
- layout identity / hash,
- races held,
- official use,
- Course records,
- record-holding Creatures.

The exact storage model is TBD.

---

# 9. Breeding and selection loop

## 9.1 Current loop

**CURRENT**

The current conceptual gameplay loop is:

1. A Creature exists with inherited and developed characteristics.
2. The Creature competes under specific Course/race conditions.
3. Race results are produced.
4. Players evaluate those results.
5. Players select future parents.
6. Breeding creates the next generation.
7. The new generation is raised and tested again.

This loop may later be expanded by systems such as Race Agent, more detailed training, competition formats and optional wallet-linked interactions.

---

## 9.2 Selection is player-driven

**CURRENT**

Race results provide information for breeding decisions.

A race result does not automatically define a single objectively best parent.

Because conditions differ, the value of an individual depends partly on what the player wants to breed for.

---

# 10. History and records

## 10.1 History as a game concept

**CURRENT**

History is expected to exist across several types of entities:

- Creature history,
- bloodline history,
- Race history,
- Course history.

The purpose is not only to store current state but also to preserve how that state developed.

---

## 10.2 Storage authority

**TBD**

It has not yet been decided which records belong in:

- a conventional database,
- blockchain,
- both,
- or another storage layer.

No system should currently assume that all history belongs on-chain.

---

# 11. Player-created ecosystem

## 11.1 Current direction

**PROPOSED**

The wider design may eventually support different player-created roles, including:

- Creature breeding,
- Race Agent creation,
- Course creation,
- Course part creation,
- tournament / competition organization.

Only Creature and Course-related parts are in the current v0.1 system map.

The other roles require later specifications.

---

# 12. Course-related monetization principles

## 12.1 Competitive advantage

**CURRENT PRINCIPLE**

Monetization must not directly sell stronger competitive performance.

The working principle is:

**Players may pay for greater creative freedom, but not for different competitive rules.**

Previously discussed paid Course Builder value may include:

- greater creative freedom,
- storage,
- expression,
- management tools,
- analysis,
- publication features.

Exact plans, prices and tiers are TBD.

---

## 12.2 Current broader principle

**CURRENT PRINCIPLE**

The project should not sell:

- stronger Creature abilities,
- guaranteed victory,
- direct competitive superiority.

A previously discussed direction is to monetize creation, expression, management or commercial visibility rather than raw competitive power.

This remains subject to later business-model design.

---

# 13. Naming rights and commercial Course identity

**PROPOSED / LATER**

A future system may allow naming or sponsorship rights for:

- races,
- race series,
- Courses.

Commercial names should be separable from canonical Course identity.

Temporary sponsorship history may also be recorded.

This is not part of the initial implementation.

---

# 14. Wallet-linked interaction

**TBD**

Wallet connection is optional by project rule.

A wallet-connected mode or wallet-linked interaction may later affect some aspect of the game or Creature presentation/state.

The exact design is not yet fixed.

No implementation should currently assume:

- what assets are recognized,
- what effects they have,
- whether effects are visual or mechanical,
- how long effects last,
- or where validation occurs.

This requires a separate specification later.

---

# 15. Systems intentionally not yet specified

The following major systems are outside the normative scope of v0.1.

### Race Agent

TBD.

Known design work exists, but it should be specified separately after this baseline is accepted.

### Race Engine

Only high-level relationships are defined.

Detailed physics, simulation, collision, movement, overtaking, commands, stamina, failure states and scoring are TBD.

### Creature Genome Schema

TBD.

### Creature State Schema

TBD.

### Training System

TBD.

### Race Categories

TBD.

### Competition / Tournament Rules

TBD.

### Multiplayer architecture

TBD.

### Account and login architecture

TBD.

### Wallet-linked mode

TBD.

### Blockchain architecture

TBD.

### Database architecture

TBD.

### Final client platform

TBD.

The game has not yet been committed to Web, Unity, Unreal Engine or another final runtime.

### Final Creature visual design

TBD.

Current prototypes and concept art are validation material and must not automatically be treated as final production design.

---

# 16. Relationship to the current prototype repository

Repository:

`badjoke-lab/evowild-test`

The current repository is a test bed.

Its present implementation is used to validate race presentation and technical feasibility.

The current README describes a prototype with:

- 18 simultaneous racers,
- S / P / E / A low-poly body morphs,
- client-side Three.js rendering,
- Race / Follow / Tactical cameras,
- heading,
- acceleration,
- blocking,
- lane changes,
- overtakes,
- no server-side rendering,
- no live LLM calls.

These implementation details are prototype facts.

They are **not automatically canonical game-design requirements**.

A prototype feature only becomes a project requirement when it is explicitly adopted into the design specification.

Likewise, a design concept in this document should not be described as implemented until it has actually been validated in code.

---

# 17. Source-of-truth rules

For future development, use the following distinction.

## Written design specification

This document and later versioned specifications define detailed game-design intent.

## Whimsical system map

The Whimsical board defines the current visual relationships between major systems.

Current board:

https://whimsical.com/evowild-run/evowild-run-game-structure-v0-1-7CNfLG8AoC7nKkcmvH2D6F

## Prototype code

The repository defines what has actually been implemented and tested.

## Public development posts

DEV posts document the project's design history and thought process.

They are historical records of what was being considered at the time.

They should not override a newer explicit design specification.

---

# 18. Change discipline

When a design decision changes:

1. state explicitly what changed,
2. update this specification if the change affects its scope,
3. update the Whimsical diagram if system relationships changed,
4. update or add tests/prototypes where implementation is affected,
5. do not rewrite older development posts to make the design history appear cleaner than it was.

Historical design changes are part of the project record.

---

# 19. Current next design area

The next major design area after this v0.1 baseline is:

**Race participation / Race Agent / Creature State**

Questions include:

- what the player decides before the race,
- what the player can influence during the race,
- what an Agent decides,
- what commands an Agent may issue,
- how a Creature attempts to execute commands,
- how ability, fatigue, temperament, compatibility, surroundings and Course conditions affect execution,
- how AI and non-AI users operate under the same Race Engine rules.

These questions are not answered by this v0.1 specification.

They should be handled in the next design revision or a dedicated Race Agent specification.
