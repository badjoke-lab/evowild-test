# EvoWild Run — Race Agent / AI / Creature State Specification v0.1

Status: Draft / adopted direction where explicitly stated  
Project name: EvoWild Run (provisional)  
Source: Existing Race Agent / AI / Creature State design memo  
Last updated: 2026-09-22

> Note: An earlier memo used the label "EVOLINE RACING". The current project name used in this repository is "EvoWild Run". This document preserves the substance of that memo without treating the earlier label as the canonical project title.

---

## 1. Basic policy

In EvoWild Run races, the player does not directly control the Creature after the race starts.

The player's main roles are:

- breeding Creatures
- selecting the Creature to enter
- selecting the Course
- configuring race strategy
- configuring the Race Agent
- watching the race
- analysing the result
- applying what was learned to later breeding and strategy

After the start, the race proceeds through the Race Engine and the Race Agent assigned to each Creature.

---

## 2. Every entrant has a Race Agent

Every racing Creature has a Race Agent in a common format regardless of whether the player uses AI.

The Race Engine must not have separate rule systems for:

- players who do not use AI
- players who use AI
- advanced users
- beginners

All entrants are processed under the same Agent schema and the same Race Engine rules.

---

## 3. Non-AI user flow

Normal users do not need to edit an Agent File directly.

The game UI can expose understandable choices and generate the internal Race Agent from them.

Candidate settings include:

### Start

- Push forward
- Standard
- Hold back

### Base pace

- Conserve
- Standard
- Aggressive

### Positioning

- Prefer inside
- Natural
- Prefer outside

### In traffic

- Wait
- Look for an opening
- Overtake aggressively

### Stamina usage

- Conservation focused
- Balanced
- Race-winning focused

### Spurt timing

- Early
- Standard
- Late

### When fatigue is high

- Slow down
- Maintain
- Push through

Beginner presets may also include:

- Front-runner
- Stalker / forward-running
- Balanced
- Closer
- Deep closer

The exact names and exposed settings remain subject to UI design.

---

## 4. Agent File

Race Agent settings are represented internally as a common Agent File.

An Agent created from the normal UI and an Agent File produced by an external AI or advanced user must resolve to the same format.

Example:

```json
{
  "agent_version": 1,
  "start_style": "HOLD",
  "base_pace": "CONSERVE",
  "lane_preference": "OUTSIDE",
  "rules": [
    {
      "when": {
        "remaining_distance_lte": 400
      },
      "action": {
        "pace": "ATTACK"
      }
    }
  ]
}
```

Every Agent File must pass a Validator.

AI users do not receive commands that are unavailable to non-AI users.

The final schema and validator rules are not yet defined.

---

## 5. AI usage

A user may ask their preferred AI system to create or improve an Agent File.

Example request:

> Create or improve an Agent File based on this Creature's abilities, its last 20 races and the current Course conditions.

The game should avoid dependence on one specific AI service.

Possible tools include:

- ChatGPT
- Claude
- Gemini
- local AI
- other compatible systems

At minimum, the game can remain service-agnostic by accepting an Agent File and validating it.

### Live AI Agent

A Live Agent in which an external AI makes real-time decisions during a race is not part of the initial specification.

Latency, API outages, model-performance differences, paid-tier differences and competitive fairness require separate evaluation.

Live AI is therefore deferred.

---

## 6. The Agent issues commands; it does not directly control the Creature

The Race Agent does not directly determine Creature movement.

Basic structure:

```text
Agent evaluates the situation
↓
Agent issues a command
↓
Creature attempts to execute it
↓
Abilities, fatigue, temperament, compatibility, surroundings, Course conditions, etc. are evaluated
↓
Actual action outcome
```

Therefore:

**Agent command != guaranteed execution**

---

## 7. Command outcomes

Even a tactically correct Agent decision may not be executed exactly as intended.

Example:

```text
Agent:
ATTACK now

Creature:
high fatigue

Result:
accelerates, but effect is reduced
```

Another example:

```text
Agent:
MOVE OUTSIDE

Creature:
low agility / outside lane blocked

Result:
lane change fails
```

Candidate outcome grades:

- Excellent
- Success
- Partial
- Failed
- Backfire

Outcomes must not be pure random rolls.

They should be derived from the relevant Creature state, Course state, local race situation and Agent compatibility.

The exact formula is TBD.

---

## 8. Factors that may affect execution

Candidate inputs include:

- Genome
- Phenotype
- Speed
- Acceleration
- Stamina
- Agility
- Temperament
- current fatigue
- current speed
- Course width
- corners
- slope
- surface
- weather
- Creatures in front / behind / left / right
- congestion
- Agent compatibility
- other temporary states

Therefore, the same Agent used with multiple Creatures should not necessarily produce the same behaviour or result.

---

## 9. Creature-Agent compatibility

A strong Agent is not expected to be optimal for every Creature.

Example:

```text
Agent:
repeated aggressive ATTACK decisions

×

Creature:
cautious temperament and slow response

→ reduced effectiveness is possible
```

Conversely, a more aggressive Creature paired with an aggressive Agent may perform better under some conditions.

The intended design supports research such as:

**"This bloodline works well with this Agent."**

This connects breeding research with Agent design.

The exact compatibility model is TBD.

---

## 10. Visual representation of the Race Agent

The Race Agent is represented in the race view, not only as internal data.

It should not be represented as a humanoid jockey.

Reasons include:

- the Creature remains the visual focus
- no rider model or riding animation is required
- the system is easier to support across different Creature body shapes
- implementation burden is lower
- the Agent can be visually represented as "intelligence"

### Current visual direction

A small sphere / orb follows above and behind each Creature.

Candidate behaviour:

- follows the Creature
- floats slightly
- remains subtle in the normal state
- reacts more strongly when issuing important commands

---

## 11. Visualising Agent actions

When an Agent issues a command, it may be represented using:

- colour
- glow
- pulse
- ring
- short animation
- icon

The Creature may show a corresponding effect.

### ATTACK / spurt

Agent:

- warmer colour
- stronger glow
- faster pulse

Creature:

- acceleration effect
- stronger movement expression

### CONSERVE

Agent:

- blue-toned state
- slow pulse

Creature:

- minimal effect
- stable running expression

### MOVE OUTSIDE

Agent:

- lateral animation
- directional arrow

Creature:

- lane / path change
- temporary intended-path line

### Congestion avoidance

Agent:

- warning flash
- `!` indicator

Creature:

- deceleration
- avoidance
- lane / path adjustment

These are visual-design directions, not final production effects.

---

## 12. Command pop-ups

Colour and animation alone may not communicate why an Agent acted.

Important Agent commands should therefore support short pop-ups.

Example:

```text
AGENT
ATTACK
Final-phase spurt
```

```text
AGENT
MOVE OUTSIDE
Congestion detected ahead
```

Execution results may also be shown.

```text
SUCCESS
Path secured
```

```text
PARTIAL
Acceleration reduced by fatigue
```

```text
FAILED
No outside path available
```

This allows spectators to understand:

**decision → command → execution → result**

---

## 13. Creature state display

The current state of a Creature should be inspectable during a race.

Fatigue is a required race-state display under the current direction.

### Minimum always-visible information

- Creature name / ID
- current position
- fatigue
- current Agent strategy

Example:

```text
EV-027
4th

FATIGUE 61%
██████░░░░

AGENT: CONSERVE
```

### Fatigue

The UI currently prefers "fatigue" over "remaining stamina" because it may be easier to read intuitively.

Example interpretation:

- 10%: barely fatigued
- 50%: substantially consumed
- 80%: high fatigue
- 95%: near limit

Numeric value plus bar is the current direction.

---

## 14. Temporary Creature states

Candidate temporary states include:

- Calm
- Focused
- Excited
- Nervous
- Boxed in
- Unbalanced
- Recovering

Not every state should be permanently displayed.

Important states may appear through icons or short labels.

The final state list and transitions are TBD.

---

## 15. Spectator-game objective

Because the player does not directly control the Creature after the start, spectators need to be able to understand:

- why the Creature accelerated
- why it could not move
- why an Agent command failed
- why it faded late

By exposing Race Agent decisions and Creature State, the race should become more than a position display.

The intended experience is:

**a race where the player reads decisions and outcomes**

---

## 16. Feedback into breeding

Agent failures and Creature states should feed into later breeding decisions.

Example:

```text
Repeated failures when moving outside
↓
Suspect insufficient Agility
↓
Breed with a higher-Agility bloodline
↓
Test improvement in the next generation
```

Another example:

```text
Weak response to late ATTACK commands
↓
Analyse Stamina / Acceleration / Temperament
↓
Change the Agent or change breeding direction
```

This creates the loop:

**breeding → Agent configuration → race → state analysis → next breeding decision**

---

## 17. Treating the Race Agent as an independent in-game entity

**UNDER CONSIDERATION**

The Race Agent may be treated not only as temporary strategy configuration but as an in-game entity separate from the Creature.

Conceptually:

```text
Race Agent
- Agent ID
- Name
- Creator
- Current Owner
- Strategy Definition
- Version
- Race History
- Win / Result History
- Compatibility History
- Ownership History
```

This could support long-term use, improvement and history accumulation around one Agent identity.

This is not yet a fully adopted implementation requirement.

---

## 18. Agent history

**UNDER CONSIDERATION**

An Agent may have history separate from Creature history.

Candidate fields:

- creation time
- creator
- current owner
- version history
- number of races
- wins
- placings / results
- Creatures used
- bloodlines used
- Courses used
- conditions where it performs well
- official compatibility history
- tournament usage
- major wins
- ownership-transfer history

Example:

```text
Agent #A-0192
Name: Needle

Creator: User A
Current Owner: User B

Races: 284
Wins: 51

Version:
v1 → v2 → v3 → ... → v17

Strong compatibility:
Lineage X
Long Distance
Wet Course
```

---

## 19. Agent improvement and versioning

**UNDER CONSIDERATION**

An Agent may be updated after analysing race results.

Example:

```text
Agent v1
↓
20 races
↓
Weakness analysis
↓
Agent v2
↓
Further testing
↓
Agent v3
```

External AI may also be used to help produce an improved version.

Example:

> Analyse the last 50 races of this Agent and produce an improved version.

Whether a version update remains the same Agent identity or creates a new Agent identity is TBD.

At minimum, the design direction is to make versions traceable.

```text
Agent ID
└─ v1
   └─ v2
      └─ v3
```

---

## 20. User-to-user Agent transfer

**UNDER CONSIDERATION**

If Race Agents become independent in-game entities, ownership transfer between users may be supported.

Example:

```text
User A
↓
creates and improves Agent #A-0192
↓
uses it in many races
↓
transfers it to User B
↓
User B continues using the same historical Agent
```

After transfer, the following should remain if this model is adopted:

- creator
- prior owners
- historical results
- version history
- major achievements

The intended principle is:

**Ownership may change, but the Agent's history continues.**

---

## 21. Separation of Agent File logic and Agent identity

Because Agent Files can be handled outside the game and may be produced by external AI, strategy logic cannot be assumed to be uncopyable.

Therefore, the design separates:

**strategy logic**

from

**the in-game Agent entity**

Even if the strategy content is copied, the copied strategy does not inherit:

- Agent ID
- canonical creation history
- official race record
- version history
- ownership history
- tournament achievements
- official Creature compatibility record
- other game-recorded history

The intended principle is:

**A strategy can be imitated, but the history accumulated by an Agent cannot simply be duplicated.**

This distinction is especially important if Agent ownership transfer is later adopted.

---

## 22. Agent Builder as a player role

**UNDER CONSIDERATION**

If Agents become independent entities, an additional player role may emerge:

**Agent Builder / Agent Designer**

Possible player specialisations include:

- Creature breeder
- race-focused player
- Agent strategy designer / improver
- Course designer
- tournament organiser

Agent Builders could research and create:

- Course-specific Agents
- distance-specific Agents
- bloodline-specific Agents
- temperament-specific Agents
- special-condition Agents

The goal is to allow a user-created and research-oriented culture to exist around Agents as well as Creatures.

---

## 23. Agent within the wider user-created ecosystem

The current wider design considers at least these possible user-created domains:

```text
Creature
Race Agent
Course
Competition / Tournament
```

The creator, user, improver and evaluator of each may be different people.

Example:

```text
Breeder
↓
creates / develops Creatures

Agent Builder
↓
creates Race Agents

Course Designer
↓
creates Courses

Tournament Organizer
↓
combines Creatures, Agents and Courses into competitions
```

Race Agent is intended to be one component of this wider user-created ecosystem.

---

## 24. Possible future relationship between Agent and blockchain

**TBD / LATER**

If blockchain integration is used, important Agent history may become a candidate for public proof.

Candidates include:

- Agent creation
- Agent ID
- ownership transfer
- major versions
- major tournament achievements
- important results

The design does not assume every strategy setting or every race is written to blockchain.

A possible direction is:

```text
Agent History
↓
important events
↓
Hash / Proof
↓
Public Blockchain
```

The exact blockchain recording scope is a later decision.

---

## 25. Agent monetisation

**UNDECIDED / LATER**

An Agent monetisation model may be possible if Agents become independent in-game entities.

This is not an adopted monetisation decision.

It is also not part of initial development.

Candidate models include:

- free users can create a limited number of Agents
- one or two free Agents as an example allowance
- paid creation beyond the free allowance
- per-Agent one-time purchase
- Agent-capacity-based pricing

The following remain undecided:

- free Agent count
- price
- one-time purchase vs subscription
- transfer rules
- resale rules
- fees
- whether an Agent market exists

If transferable ownership is adopted, a one-time purchase model may align more naturally with the ownership concept than a recurring access fee, but this is only a consideration.

Paid users should not receive stronger Race commands unavailable to free users under the current direction.

AI / non-AI and free / paid users should remain subject to the same basic command system and Validator rules.

---

# 26. Current provisional specification

The current adopted or adopted-direction items are:

1. Every racing Creature has a Race Agent.
2. Non-AI users can create a Race Agent through the normal UI.
3. External AI can also produce Agent Files.
4. AI and non-AI users use the same Race Engine rules.
5. The Agent issues commands, but commands are not guaranteed to succeed.
6. Command outcomes are affected by Creature abilities, fatigue, temperament, compatibility, Course conditions and surrounding race state.
7. The Race Agent is visually represented as a small orb following above and behind the Creature.
8. Agent commands are communicated through colour / glow / animation and short pop-ups.
9. Execution results can also be shown as success / partial success / failure-style outcomes.
10. Creature race state is visible, and fatigue is a required display.
11. Live AI Agent real-time decision making is deferred and excluded from the initial implementation.
12. Treating Race Agent as an independent in-game entity is under consideration.
13. Agent ID, creator, owner, version, results and compatibility history are candidate persistent data if independent Agent identity is adopted.
14. User-to-user transfer of Agents is under consideration.
15. Agent File strategy logic is separated conceptually from in-game Agent identity, history and ownership.
16. Agent Builder / Agent Designer is a target player role under consideration.
17. The wider design should support Creature / Agent / Course / Competition as possible user-created domains.
18. Blockchain recording scope for Agents is deferred.
19. Agent monetisation is undecided and, if adopted, belongs to a later phase.
20. Paid Agent functionality should not create exclusive stronger race commands under the current direction.

---

# 27. Next specification work

This document defines the Race Agent concept and its relationship to Creature state at a high level.

The next specification work should define the executable race semantics needed by the Race Engine:

- canonical Agent command vocabulary
- observable inputs available to an Agent
- decision timing / tick model
- rule evaluation order
- command conflicts and precedence
- Creature State schema
- temporary-state transitions
- command execution model
- Excellent / Success / Partial / Failed / Backfire semantics
- compatibility model
- fatigue model
- path / congestion model
- race logs and replayable decision history
- Validator requirements
- Agent File versioning rules

These should be defined before treating the Agent File example as an implementation-ready schema.
