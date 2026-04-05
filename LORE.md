# TURN-BASED MECH GAME - LORE & CANON

**Last Updated:** April 1, 2026  
**Document Version:** 2.0

---

## TABLE OF CONTENTS

1. [World Overview](#world-overview)
2. [Player Role - The Coordinator](#player-role---the-coordinator)
3. [The Tactical Display](#the-tactical-display)
4. [Factions](#factions)
5. [Campaign Story](#campaign-story)
6. [Mech Units](#mech-units)
7. [Lore Rules & Canon](#lore-rules--canon)
8. [Tone & Style Guide](#tone--style-guide)
9. [Narrative Conventions](#narrative-conventions)

---

## WORLD OVERVIEW

**Setting:** A distant planetary conflict in a gritty, grounded sci-fi universe.

**Conflict:** The Free Systems Alliance (FSA) is conducting a planetary campaign to capture an enemy-held world. You are a **Tactical Coordinator** stationed aboard an orbiting command vessel, directing mech pilots and resources from a distance.

**Technology Level:**
- **LOW-TECH MECHS:** Slow, weighty machines with minimal thruster technology
- **Primary weapons:** Kinetic (ballistic, autocannons, missiles, shotguns)
- **Experimental tech:** Some energy weapons exist but are rare/unreliable
- **No hover/float mechanics:** Mechs are earthbound, heavy, and grounded
- Movement is deliberate, combat is measured
- Radio/comm communications work but are subject to interference
- Dropships and mechanized infantry exist
- No aliens - purely human factions
- No AI companions or holograms (no "smart" technology)
- **Limited telemetry:** Your display shows low-resolution, geometric representations of units due to signal degradation and bandwidth constraints

**Aesthetic:** The entire game is presented through a **degraded tactical command terminal**. You are not seeing the battlefield directly - you are viewing a low-quality telemetry feed with geometric IFF symbols, scanlines, signal noise, and compressed data. Think **NORAD command center** meets **Battletech** with a **Cold War-era military terminal** vibe.

---

## PLAYER ROLE - THE COORDINATOR

### Identity
- **Name:** Not specified (player can choose or use default callsign)
- **Role:** Tactical Coordinator / Mission Commander in the FSA
- **Background:** Spoke out against FSA leadership's tyranny/ethics
- **Status:** Political dissident, considered expendable
- **Motivation:** Prove your competence despite being set up to fail

### Not a Pilot
- You are **not** on the ground. You are in a command vessel or bunker.
- You do not fight directly. You issue orders, allocate resources, and manage pilots.
- Your "view" of the battlefield is a **low-resolution tactical display** - geometric shapes, IFF tags, and telemetry data.
- The geometric, minimalist art style is **diegetic** - it's what your terminal actually shows, not an artistic abstraction.
- Signal degradation, scanlines, and compression artifacts are part of the experience.

### Not a Chosen One
- You were **not** prophesied or specially trained
- You are a regular coordinator who angered the wrong people
- Command gave you this mission hoping you'd fail
- Your success or failure will be politically useful either way

### How Your Past Matters
- Your dissident status may affect how pilots and NPCs treat you:
  - Rebels might respect you more if they learn why you're here
  - CC prisoners might share intelligence if you seem sympathetic
  - FSA loyalists (if encountered) might refuse to cooperate or actively sabotage
- Your choices throughout can either reinforce or change this reputation

---

## THE TACTICAL DISPLAY

### Why Everything Looks Geometric

The game's visual style is **diegetic** - everything you see is what the Coordinator's terminal displays:

- **Mechs are geometric IFF symbols** - simple shapes with faction colors, because the telemetry feed only transmits position, identity, and basic status
- **Terrain is simplified** - the grid shows what your sensors can detect: walls, elevation, cover, water
- **Cards are command directives** - not physical objects, but tactical orders you issue to your pilots
- **UI elements are terminal readouts** - monospace fonts, scanlines, signal noise, compression artifacts
- **No detailed sprites** - bandwidth limitations mean you get symbols, not pictures

### Visual Language

| Element | Display Representation | Reason |
|---------|----------------------|--------|
| Friendly mechs | Geometric shapes + faction color | IFF transponder data |
| Enemy mechs | Red/dark geometric shapes | Hostile IFF or inferred |
| Terrain | Simplified grid with terrain markers | Sensor sweep data |
| Damage | Floating numbers + screen shake | Telemetry spike |
| Cards | Command directives with type colors | Tactical order interface |
| UI panels | Terminal windows with borders | Command console layout |
| Transitions | Static, signal loss, re-acquire | Comm interference |

### What This Means for Art

- **No detailed mech sprites needed** - geometric IFF symbols are canon
- **Scanlines and noise are features, not bugs** - they're signal degradation
- **Monospace/terminal fonts** reinforce the command terminal aesthetic
- **Limited color palette** - tactical displays use specific colors for specific data types
- **CRT effects** are part of the terminal hardware, not a stylistic overlay

### Terminal Display Implementation

The Coordinator's terminal has specific visual conventions that must be followed consistently:

**Typography:**
- All text uses a **monospace terminal font** (e.g., Courier New, Consolas, or pixel font like Terminus)
- Headers and labels are **UPPERCASE** like terminal readouts
- Input fields and selection cursors may include a **blinking cursor** (`█` or `▮`)
- No proportional fonts anywhere — the entire interface is character-cell based

**Data Formatting:**
- Numbers are **fixed-width** with zero-padding: `HP: 028/030`, `OL: 004/010`, `CR: 0150`
- Status indicators use **bracketed tags**: `[ACTIVE]`, `[STANDBY]`, `[OFFLINE]`, `[CRITICAL]`, `[ENGAGED]`
- Timestamps prefix messages: `04:12:33 // ENGAGEMENT START`
- Coordinates use grid notation: `GRID 14,07` not `Position: 14,7`

**UI Containers:**
- Panels are styled as **terminal windows** with thin borders and corner brackets
- Section titles use `>` prefix: `> UNIT STATUS`, `> DIRECTIVE QUEUE`, `> SECTOR MAP`
- Divider lines are rendered as `─────────────────` or `═════════════`
- No rounded corners, gradients, or modern UI elements — everything is boxy and utilitarian

**Combat Grid:**
- Grid lines are **faint scanlines**, not solid borders
- Terrain markers are **ASCII-style symbols** overlaid on tiles: `█` (wall), `▲` (high ground), `░` (cover), `~` (water)
- Range indicators are **dashed lines**, not filled highlights
- Unit positions show IFF symbol + callsign tag: `◈ ALPHA-1`

**Card/Directive Display:**
- Cards are formatted as **command line entries**, not playing cards:
  ```
  > DIRECTIVE: AUTOCANNON BURST
    TYPE: ATTACK | DMG: 06 | OL: 02
    [EXECUTE]
  ```
- Card types have type-color coding but maintain terminal aesthetic
- Hover reveals additional telemetry: range, pattern, keywords
- No card art — text-only directives with type icons

**Transitions:**
- Scene changes include **brief static burst** then `> SIGNAL RE-ACQUIRED`
- Combat start sequence: `> CONNECTING TO TACTICAL FEED...` → `> LINK ESTABLISHED`
- Death/Defeat: `> SIGNAL LOST`, screen fades to static
- Floor transitions: `> UPLOADING SECTOR DATA...` → `> SECTOR N LOADED`
- All transitions feel like comm link interruptions, not UI animations

**Audio (if implemented):**
- Keyboard clicks on button press
- Terminal beep on errors or warnings
- Radio static on scene transitions
- Low hum for terminal background ambience

**What NOT to Do:**
- No rounded button corners or soft shadows
- No card illustrations or character portraits (except procedural terminal-style operator IDs)
- No smooth animations — everything snaps or has brief static interference
- No modern UI patterns (hamburger menus, floating action buttons, etc.)
- No "game-y" elements like health bars with hearts or star ratings

---

## FACTIONS

### 1. FREE SYSTEMS ALLIANCE (FSA)

**Role:** Player faction - the "liberators"  
**Display Colors:** Varied by mech variant:
- Bastion: Green
- Raptor: Teal
- Anvil: Olive
- Warden: Blue
- Wraith: Purple

**Philosophy:** Trying to liberate the planet from enemy control. Whether they're truly freedom fighters or imperialist invaders is left ambiguous.

**Organization:** Fleet-based, with named outposts (Alpha, Bravo, Charlie, Delta) and command centers.

**Mechs:** Vanguard-class frames with standardized FSA livery.

**Tone in comms:** Professional, mission-focused, military bearing.

---

### 2. CRIMSON COMPACT (CC)

**Role:** Main enemy faction - defenders of the planet  
**Display Colors:** Deep red and black

**Philosophy:** Defending their territory against the invading FSA. They're the established power on this planet.

**Organization:** Structured military with command hierarchy, defense networks, communication arrays.

**Mechs:** Heavily armored, aggressive designs. Names like Warden, Bastion, Siege reflect defensive/fortification themes.

**Tone in intercepted comms:** Ruthless, determined, fighting for their homeland.

---

### 3. REBELS

**Role:** Unaligned third faction - can be allies or enemies  
**Display Colors:** Rust orange, olive, mismatched (scrap-built appearance)

**Philosophy:** Surviving in the warzone. They're opportunists, scavengers, and independent operators.

**Mechs:** Jury-rigged, modified civilian or captured military frames. Junk-built but effective.

**Tone in intercepted comms:** Cynical, pragmatic, survival-focused. "Everyone's just trying to get by."

---

## CAMPAIGN STORY

### Premise

You are a Tactical Coordinator in the **Free Systems Alliance**. You were **not** the most qualified, nor were you the first choice. You were assigned this mission because you spoke out against the FSA's tyranny - your political dissent made you disposable. Command gave you a suicide operation, hoping you'd either fail spectacularly or prove their point about "troublemakers."

Now it's your job to direct pilots, manage resources, and coordinate assaults across 25 floors of hostile territory. Survive. Thrive. Show them what a "dissident" can really do.

The planet is defended by the **Crimson Compact**, who have established their rule here. They're not cartoon villains - they're defending their home against invaders. Meanwhile, the **Rebels** - scavengers and survivors - watch from the sidelines, ready to exploit whatever chaos you create.

Your choices throughout the mission will determine:
- Who helps you (if anyone)
- Who opposes you
- What kind of resistance you face
- Whether you become a hero, a villain, or just another statistic

### 25-Floor Structure

The campaign is divided into 5 sectors, each with 5 floors (outposts):

1. **Floors 1-5: Outpost Alpha** - Insertion, first contact
2. **Floors 6-10: Outpost Bravo** - Resistance increases
3. **Floors 11-15: Outpost Charlie** - Deep enemy territory
4. **Floors 16-20: Outpost Delta** - Final approach
5. **Floors 21-25: Enemy Command Fortress** - Final assault

### Narrative Beats

**Opening (Floors 1-3):**
- Dropship insertion confirmed
- First outpost - proving your capability as a coordinator
- Enemy patrols converging
- Intel confirms objectives

**Mid Campaign (Floors 6-15):**
- Enemy adaptations - they learn your tactics
- **Decision points arise:** encounters with civilians, prisoners, downed pilots
- **Potential ally encounters** based on previous choices
- Salvage opportunities (abandoned mechs, supply depots)
- **Moral choices** with lasting consequences
- Early decisions begin manifesting as altered enemy compositions

**Late Campaign (Floors 16-25):**
- **Consequences of earlier choices come to fruition**
- Allies you saved may appear as reinforcements
- Enemies you spared may return as hostile or offer surrender
- Rebels you helped may provide crucial support or betray you
- Your reputation precedes you - CC may adapt tactics specifically to counter your style
- Enemy reinforcements arrive (or don't, based on your path)
- Planet's defense network active (may be disabled if you made key alliances)
- Final push to command center
- Showdown with enemy commander
- **Multiple ending possibilities** based on accumulated decisions

### Floor-Specific Narratives

| Floor | Narrative Event |
|-------|-----------------|
| 1 | INSERTION COMPLETE. Begin assault. |
| 5 | OUTPOST ALPHA CLEARED. First base down. |
| 6 | New sector entered. Resistance escalating. |
| 10 | OUTPOST BRAVO CLEARED. Half the planet yours. |
| 11 | Deep enemy territory. No turning back. |
| 15 | OUTPOST CHARLIE CLEARED. Command within reach. |
| 16 | Final sector. Everything enemy has left is here. |
| 20 | OUTPOST DELTA CLEARED. One fortress remains. |
| 25 | FINAL ASSAULT. Enemy commander awaits. |

### Victory Condition

Defeat the enemy commander on floor 25 and secure the planet's command network.

### Defeat

Your forces are destroyed. No extraction. Another coordinator needed.

---

## MECH UNITS

### Technology Constraints

All mechs share these characteristics:
- **Slow and deliberate movement** - no jetpacks or hover capability
- **Weighty presence** - mechs feel like 20+ ton machines
- **Limited thrusters** - jumping/leaping is possible but constrained
- **Ground-based combat** - verticality limited to terrain elevation, not flying
- **Kinetic weapons dominate** - autocannons, missiles, rifles, shotguns
- **Experimental energy weapons** exist but are rare, overheating, unreliable
- **No energy shields as standard** - only reactive/ablative armor systems
- **Short range engagement** - despite having range stats, tactical reality is mech-scale distances

### FSA Vanguard Variants

These are the **coordinator-available mech frames**. Each has distinct IFF symbol shapes:

1. **Bastion** (Green)
   - Role: Tank
   - IFF Shape: Wide rectangle/square
   - Traits: Heavy armor, high HP, defensive capabilities
   - Movement: Slowest, deliberate repositioning
   - Expected playstyle: Frontline absorber that controls space

2. **Raptor** (Teal)
   - Role: Scout
   - IFF Shape: Diamond/triangle
   - Traits: Better mobility (still not "fast"), low armor, flanking capability
   - Movement: Fastest of the Vanguard line, but still constrained
   - Expected playstyle: Positional advantage, hit-and-run tactics

3. **Anvil** (Olive)
   - Role: Heavy
   - IFF Shape: Wide hexagon
   - Traits: Heavy weapons, slowest movement, highest damage output
   - Movement: Deliberate, needs planning to reposition
   - Expected playstyle: Breakthrough assault, destroy high-value targets

4. **Warden** (Blue)
   - Role: Defender
   - IFF Shape: Circle with cross
   - Traits: Support capabilities, protective abilities, medium armor
   - Movement: Average, holds position well
   - Expected playstyle: Area denial, team defense

5. **Wraith** (Purple)
   - Role: Stealth/Glass Cannon
   - IFF Shape: Narrow chevron
   - Traits: Evasion, precision strikes, extremely fragile
   - Movement: Average mobility, relies on not being hit
   - Expected playstyle: Surgical strikes, ambush from cover

**Note:** These variants should have unique starting decks and IFF symbol shapes that reflect their **low-tech, grounded** nature. No unrealistic mobility or energy-based defenses.

### Enemy Faction Mechs

**Crimson Compact (CC):**
- CC_Bastion.tres
- CC_Sentinel.tres
- CC_Siege.tres
- CC_Warden.tres

**Rebels:**
- Rebel_Ghost.tres
- Rebel_Rustbucket.tres
- Rebel_Warlord.tres

**Base Enemies:**
- Standard mech chassis (Artillery, Heavy, Scout, Sentinel, Striker, Support)

---

## CHOICES & BRANCHING ENCOUNTERS

The campaign features **decision-based encounters** that change based on player choices throughout the game. These decisions should affect:

### Encounter Types

1. **Combat Encounters**
   - Enemy composition can vary based on previous choices
   - Example: Spared Rebels earlier → they may appear as allies later
   - Example: Showed mercy to CC soldiers → they might surrender or offer truce

2. **Event Rooms**
   - Narrative choices with lasting consequences
   - Should have 2-3 options with meaningful outcomes
   - Consequences can appear 3-10 floors later

3. **NPC Interactions**
   - Decisions about whether to help, ignore, or attack neutral parties
   - Affects who appears in later rooms (friends or enemies)
   - Example: Rescue downed pilot → they join your cause later
   - Example: Loot abandoned supply depot → Rebels remember your greed

### Decision Tracking

The game should track:
- **Moral choices** (help vs. harm, spare vs. kill)
- **Faction reputation** (FSA loyalty, CC mercy, Rebel trust)
- **Key events** (allies made, enemies spared, innocents harmed)
- **Resource decisions** (spared supplies vs. taken them)

### Branching Paths

Choices should create multiple paths through the 25-floor campaign:
- **Allied path:** Helped many → get support from factions, easier fights
- **Neutral path:** Mostly self-focused → standard progression
- **Vengeful path:** Ruthless → more enemies, but better loot from defeated foes
- **Sympathetic path:** Spared enemies → potential for peace or betrayal

### Implementation Notes

- Decisions should be stored in a persistent decision log (array of choice IDs)
- Floor generation and enemy spawning should query decision log
- NPC appearances/dialogues should reflect past choices
- Multiple endings possible based on overall moral alignment

---

## LORE RULES & CANON

### What Is Canon

1. **Factions:** FSA (invaders), CC (defenders), Rebels (neutrals)
2. **Setting:** Single planet being conquered by coordinated insertion
3. **25-floor campaign** with 5 outposts + final fortress
4. **Named locations:** Outposts Alpha/Bravo/Charlie/Delta, Command Fortress
5. **Tone:** Gritty military sci-fi, command terminal aesthetic, tactical display framing
6. **Tech level:** Mechs, dropships, radio comms, no aliens, limited telemetry
7. **Visual framing:** Everything is viewed through a degraded command terminal

### What Is NOT Canon (Avoid)

- Fantasy elements (magic, dragons, etc.)
- Space opera tropes (galactic empires, jedi, etc.)
- Cartoonish or comedic tones (unless specifically requested)
- Anime tropes (giant mecha pilots screaming attacks)
- Superhero elements (mutants, superpowers)
- Historical Earth references (keep it original)
- Fourth-wall breaks
- **High-tech gravity manipulation** - mechs are heavy and earthbound
- **Jetpacks/hover mechs** - thrusters are minimal, movement is ground-based
- **Sentient AI** - no friendly AI companions or holograms
- **Energy shields that block everything** - limited, situational shields only
- **Instant teleportation** - movement is deliberate and constrained
- **"Rule of cool" over realism** - mechs should feel like heavy industrial machines
- **Detailed realistic sprites** - the terminal only shows geometric IFF symbols
- **High-fidelity graphics** - signal degradation limits display quality

### Faction Portrayal Rules

**FSA:**
- **Not monolithic.** Contains both idealistic liberators and cynical authoritarians
- Leadership has **tyrannical tendencies** - they exile/dissidents, conduct questionable operations
- Regular troops are often just following orders, not fully aware of politics
- They genuinely believe they're liberating the planet (or at least claim to)
- The coordinator's dissident status means some FSA elements might **actively work against you**

**CC:**
- Defending their home - **sympathetic angle required**
- Not mustache-twirling villains - they have families, culture, legitimate grievances
- Can surrender, retreat, or fight to death based on tactical situation
- Professional military, not mindless drones

**Rebels:**
- **Primarily survivors**, not ideologues
- Scrappy, pragmatic, cynical
- Will help if paid, promised supplies, or if it serves their interests
- Will fight if threatened or if the price is right

---

## TONE & STYLE GUIDE

### Narrative Voice

**Objective, tactical, understated.** Think military briefings, after-action reports, command terminal readouts.

**Examples:**
- Good: "Outpost Alpha secured. Enemy resistance neutralized."
- Good: "Scanners show enemy patrols converging. They know you're here."
- Bad: "YOU ARE THE CHOSEN ONE! GLORY AWAITS!"
- Bad: "The enemy are EVIL MONSTERS who must be DESTROYED!"

### Card Flavor Text (if adding)

Should fit the tone:
- Tactical: "Flanking maneuver - bonus damage if attacking from side"
- Grim: "Overwatch protocol - fire on any target that moves"
- Practical: "Field repair protocols - patch armor in combat"

NOT:
- Silly: "This one goes to 11"
- Edgy: "BLOOD FOR THE BLOOD GOD"
- Cheesy: "Feel the power of friendship!"

---

## NARRATIVE CONVENTIONS

### Naming Conventions

**Mech Names:**
- FSA: Bastion, Raptor, Anvil, Warden, Wraith (descriptive, thematic)
- CC: Names suggesting fortification/defense
- Rebels: Rustbucket, Ghost, Warlord (scrap-built or imposing)

**Card Names:**
- Clear, descriptive: "Autocannon Burst", "Patch Up", "Dash"
- No flamboyant anime-style names
- Functional first, flashy second

**Locations:**
- Military designations: Outpost Alpha, Sector 7, Command Fortress
- No fantasy names like "Mordor" or "Elvenhome"

### Dialogue Guidelines

NPCs (if added) should speak like trained military personnel or hardened survivors:
- Concise
- Professional (or appropriately cynical for Rebels)
- No lengthy monologues
- Minimal profanity (keep it T-rated but gritty)

### Comms/Transmission Style

All narrative text should be framed as **terminal readouts** or **radio transmissions**:
- "INCOMING TRANSMISSION - OUTPOST ALPHA"
- "SIGNAL DEGRADED - RECONSTRUCTING..."
- "MISSION UPDATE: SECTOR 3 CLEARED"
- "WARNING: TELEMETRY INTERFERENCE DETECTED"

---

## ADDING NEW LORE

When adding new content to the game, ensure it follows these guidelines:

### New Mechs
1. Name should fit the faction naming convention
2. Color palette should match faction (FSA=varied, CC=red/black, Rebels=rust/mismatched)
3. IFF symbol should be geometrically distinct from existing mechs
4. Card distribution should match role (tank=movement+armor, scout=movement+evasion, etc.)
5. If giving unique abilities, make them tactical, not magical

### New Cards
1. Name should be clear and descriptive
2. Flavor text (if added) should be 1-2 lines maximum, tactical tone
3. Effects should be mechanical, not "magical"
4. Frame as "directives" or "protocols" not "spells" or "powers"

### New Events/Rooms
1. Narrative text should be under 3 sentences
2. Choices should have meaningful risk/reward
3. No "you find a magic sword" - more like "supply cache with usable equipment"
4. Consequences should be logical, not random fantasy outcomes
5. Frame as intercepted transmissions or sensor reports

### New Factions?
**Currently no plans for new factions.** If adding:
- Must fit the established world (human factions on this planet)
- Must have clear motivation and aesthetic
- Must not break existing lore (unless it's a retcon)

---

## LORE IMPLEMENTATION MAP

This section maps lore requirements to specific UI screens and game elements.
Every piece of text in the game must follow these conventions.

### Main Menu — "Terminal Boot Screen"

The main menu is the Coordinator's first contact with the command terminal after boot.

**Greeting:** `> Hello Coordinator` (NOT "MECH COMMAND" or any game title)
**Subtitle:** `> Tactical Command Terminal v2.7.1` (version number adds authenticity)

**Menu buttons** (numbered CLI commands):
```
[1] NEW DEPLOYMENT
[2] RESUME SESSION
[3] TERMINATE LINK
```

**Status panel** (right side):
```
> SESSION STATUS
UNITS: 01 / 05
DEEPEST: --
STATUS: [STANDBY]
LINK: SECURE
```

**Hover descriptions** (typed at bottom when hovering buttons):
- NEW DEPLOYMENT: `> Initialize new deployment sequence. Select unit and equipment.`
- RESUME SESSION: `> Restore previous session from last checkpoint.`
- TERMINATE LINK: `> Disconnect from tactical network. Return to desktop.`

**Locked state** (no save file): `[2] RESUME SESSION [LOCKED]`

**Terminal ID** (top-left bezel): `> FSA-TD-47` (Terminal Designation 47)
**Channel** (top-right bezel): `CH:01 // LINK ACTIVE`
**Auth** (bottom bezel): `[AUTHORIZED PERSONNEL ONLY]`

### MechSelect — "Deployment Wizard"

Multi-step wizard framed as a deployment authorization sequence.

**Header format:** `> DEPLOYMENT WIZARD` with step indicator:
- `STEP 1/4: UNIT SELECTION`
- `STEP 2/4: EQUIPMENT LOADOUT`
- `STEP 3/4: OPERATOR ASSIGNMENT`
- `STEP 4/4: CONFIRMATION`

**Unit list format:**
```
> AVAILABLE UNITS
  [1] BASTION    HP:030  OL:012  [ACTIVE]
  [2] RAPTOR     HP:020  OL:008  [ACTIVE]
  [3] ANVIL      HP:035  OL:014  [ACTIVE]
  [4] WARDEN     HP:025  OL:010  [ACTIVE]
  [5] WRAITH     HP:018  OL:008  [LOCKED]
```

**Preview panel:**
```
> SELECTED UNIT
  UNIT: BASTION
  FRAME: Heavy Plating
  HP: 030/030
  OL: 00/012
  CARDS: 08
  STATUS: [READY FOR DEPLOYMENT]
```

**Navigation buttons:** `[BACK]` / `[NEXT]` → `[DEPLOY]` on final step

**Deploy confirmation text:**
```
> DEPLOYMENT AUTHORIZED
  UNIT: BASTION
  OPERATOR: [Pilot Name]
  DROP ZONE: Outpost Alpha
  ESTIMATED OPPOSITION: MODERATE
  
  [CONFIRM DEPLOYMENT]
```

### ShipMenu — "Mission Command"

The inter-combat hub where the Coordinator reviews status and selects next target.

**Top bar:**
```
> MISSION COMMAND                    Floor 1 - Outpost Alpha    CR:0150
```

**Tab labels:** `[BRIEFING]` / `[OPERATIONS]`

**Briefing tab — Mech card:**
```
> ACTIVE UNIT
  BASTION                           STANDARD FRAME
  OP: Aggressive Pilot
  [HEAVY PLATING] Take 25% less damage from all attacks
  
  HP: ████████████████████░░░░  025/030
  OL: ████░░░░░░░░░░░░░░░░░░  04/012
  
  WEAPON: Autocannon  (+3 dmg)
  ARMOR: Light Plating  (+5 HP)
  UTILITY: Field Medic
```

**Briefing tab — Stats panel:**
```
> PERFORMANCE METRICS
  FLOORS CLEARED:    00
  ENEMIES DEFEATED:  000
  CARDS PLAYED:      000
  CREDITS EARNED:    0150
```

**Briefing tab — Deck overview:**
```
> DECK MANIFEST
  DECK: 12 cards
  ─────────────────
  COMBAT (6):
    Autocannon Burst    DMG:06 OL:02
    Rifle Fire          DMG:04 OL:01
    ...
  MOVEMENT (4):
    Advance             RNG:03 OL:01
    ...
  REPAIR (2):
    Patch Up            HEAL:05 OL:02
    ...
```

**Operations tab — Mission log:**
```
> MISSION LOG
  [Floor-specific narrative text here]
  Example: "Dropship insertion confirmed. Enemy patrols detected at 
  Outpost Alpha perimeter. Intel suggests light resistance."
```

**Operations tab — Room selection:**
```
> SELECT NEXT TARGET
  [ASSAULT] Enemy Patrol     RISK: HIGH     REWARD: Salvage
  [SALVAGE] Wreckage Site    RISK: LOW      REWARD: Equipment
  [R&R] Forward Camp         RISK: NONE     REWARD: Rest/Repair
```

**IMPORTANT:** All references to "Coins" must be "Credits" (CR:XXXX format).
The game's currency is military credits, not coins.

### HUD — "Tactical Feed"

In-combat display showing real-time telemetry.

**Top bar format:**
```
ALPHA          HP:025/030  OL:04/12  EN:03/03  DECK:12  CR:0150
YOUR TURN                                              [END TURN]
```

**Phase messages** (flash briefly):
- `> COMBAT START`
- `> YOUR TURN`
- `> ENEMY TURN`
- `> VICTORY`
- `> SIGNAL LOST` (defeat)

**Card format** (directives, not playing cards):
```
> DIRECTIVE: AUTOCANNON BURST
  TYPE: ATTACK | DMG: 06 | OL: 02
  [EXECUTE]
```

**IMPORTANT:** No "Hints" label showing "Click card -> Click tile".
This breaks terminal immersion. Tutorials must be framed as system prompts.

### CombatHUD — "Engagement Feed"

Full combat display with party/enemy panels.

**Party section:**
```
> FRIENDLY UNITS
  ◈ ALPHA-1    HP:025/030  [ENGAGED]
  ◈ BRAVO-1    HP:030/030  [STANDBY]
```

**Enemy section:**
```
> HOSTILE CONTACTS
  ◆ HOSTILE-A  HP:015/020  [ACTIVE]
  ◆ HOSTILE-B  HP:020/020  [ACTIVE]
```

**Phase label:**
```
> PHASE: COMBAT
```

### VictoryScreen — "Mission Complete"

```
> MISSION COMPLETE
  OPERATIONAL REPORT
  
  FLOORS CLEARED:     05
  ENEMIES DEFEATED:   023
  CARDS PLAYED:       187
  CREDITS EARNED:     0450
  CASUALTIES:         001
  
  OUTPOST ALPHA CLEARED. First base down.
  
  [RETURN TO BASE]
```

### GameOverUI — "Signal Lost"

```
> SIGNAL LOST
  UNIT LOST IN ACTION
  
  FLOORS CLEARED:     03
  FINAL POSITION:     GRID 14,07
  
  No extraction available. Another coordinator needed.
  
  [REDEPLOY]    [RETURN TO BASE]
```

### PauseMenu — "Operations Halted"

```
> OPERATIONS HALTED
  [PAUSED]
  
  [1] RESUME OPERATIONS
  [2] SAVE SESSION
  [3] RETURN TO BASE
```

### MerchantUI — "Supply Depot"

```
> SUPPLY DEPOT
  Floor 3 - Outpost Alpha    CR:0150
  
  [1] Autocannon Barrel    CR:0050  [PURCHASE]
  [2] Light Plating         CR:0030  [PURCHASE]
  [3] Field Medic Kit       CR:0040  [PURCHASE]
  
  [CLOSE]
```

### Scene Transitions

All scene changes must include terminal-style transition text:

**Main Menu → MechSelect:**
```
> INITIATING DEPLOYMENT SEQUENCE...
> LOADING UNIT DATABASE...
```

**MechSelect → Main (deploy):**
```
> DEPLOYMENT CONFIRMED
> CONNECTING TO TACTICAL FEED...
> LINK ESTABLISHED
```

**Floor transitions:**
```
> UPLOADING SECTOR DATA...
> SECTOR N LOADED
> SIGNAL RE-ACQUIRED
```

**Combat start:**
```
> ENGAGEMENT DETECTED
> SWITCHING TO TACTICAL FEED...
> LINK ESTABLISHED
```

**Victory:**
```
> HOSTILES NEUTRALIZED
> SECTOR CLEARED
> RETURNING TO COMMAND FEED...
```

**Defeat:**
```
> TELEMETRY FAILURE
> SIGNAL LOST
> ALL UNITS OFFLINE
```

### Color Conventions by Context

| Context | Color | Hex | Usage |
|---------|-------|-----|-------|
| Terminal text | Green phosphor | `#26D940` | Primary text, borders |
| Dim text | Dark green | `#147326` | Secondary labels, inactive |
| Bright text | Bright green | `#33FF57` | Hover states, active |
| Enemy/hostile | Red | `#E63333` | Enemy units, danger |
| Warning | Amber | `#D98C1A` | Overload, warnings |
| FSA friendly | Cyan | `#33CC99` | Friendly units |
| Disabled | Gray | `#666666` | Locked content |
| Background | Near-black | `#050803` | Screen background |
| Panel bg | Dark green-black | `#080C04` | Panel backgrounds |

---

## LORE IMPLEMENTATION MAP

This section maps lore requirements to specific UI screens and game elements.
Every piece of text in the game must follow these conventions.

### Main Menu — "Terminal Boot Screen"

The main menu is the Coordinator's first contact with the command terminal after boot.

**Greeting:** `> Hello Coordinator` (NOT "MECH COMMAND" or any game title)
**Subtitle:** `> Tactical Command Terminal v2.7.1` (version number adds authenticity)

**Menu buttons** (numbered CLI commands):
```
[1] NEW DEPLOYMENT
[2] RESUME SESSION
[3] TERMINATE LINK
```

**Status panel** (right side):
```
> SESSION STATUS
UNITS: 01 / 05
DEEPEST: --
STATUS: [STANDBY]
LINK: SECURE
```

**Hover descriptions** (typed at bottom when hovering buttons):
- NEW DEPLOYMENT: `> Initialize new deployment sequence. Select unit and equipment.`
- RESUME SESSION: `> Restore previous session from last checkpoint.`
- TERMINATE LINK: `> Disconnect from tactical network. Return to desktop.`

**Locked state** (no save file): `[2] RESUME SESSION [LOCKED]`

**Terminal ID** (top-left bezel): `> FSA-TD-47` (Terminal Designation 47)
**Channel** (top-right bezel): `CH:01 // LINK ACTIVE`
**Auth** (bottom bezel): `[AUTHORIZED PERSONNEL ONLY]`

### MechSelect — "Deployment Wizard"

Multi-step wizard framed as a deployment authorization sequence.

**Header format:** `> DEPLOYMENT WIZARD` with step indicator:
- `STEP 1/4: UNIT SELECTION`
- `STEP 2/4: EQUIPMENT LOADOUT`
- `STEP 3/4: OPERATOR ASSIGNMENT`
- `STEP 4/4: CONFIRMATION`

**Unit list format:**
```
> AVAILABLE UNITS
  [1] BASTION    HP:030  OL:012  [ACTIVE]
  [2] RAPTOR     HP:020  OL:008  [ACTIVE]
  [3] ANVIL      HP:035  OL:014  [ACTIVE]
  [4] WARDEN     HP:025  OL:010  [ACTIVE]
  [5] WRAITH     HP:018  OL:008  [LOCKED]
```

**Preview panel:**
```
> SELECTED UNIT
  UNIT: BASTION
  FRAME: Heavy Plating
  HP: 030/030
  OL: 00/012
  CARDS: 08
  STATUS: [READY FOR DEPLOYMENT]
```

**Navigation buttons:** `[BACK]` / `[NEXT]` → `[DEPLOY]` on final step

**Deploy confirmation text:**
```
> DEPLOYMENT AUTHORIZED
  UNIT: BASTION
  OPERATOR: [Pilot Name]
  DROP ZONE: Outpost Alpha
  ESTIMATED OPPOSITION: MODERATE
  
  [CONFIRM DEPLOYMENT]
```

### ShipMenu — "Mission Command"

The inter-combat hub where the Coordinator reviews status and selects next target.

**Top bar:**
```
> MISSION COMMAND                    Floor 1 - Outpost Alpha    CR:0150
```

**Tab labels:** `[BRIEFING]` / `[OPERATIONS]`

**Briefing tab — Mech card:**
```
> ACTIVE UNIT
  BASTION                           STANDARD FRAME
  OP: Aggressive Pilot
  [HEAVY PLATING] Take 25% less damage from all attacks
  
  HP: ████████████████████░░░░  025/030
  OL: ████░░░░░░░░░░░░░░░░░░  04/012
  
  WEAPON: Autocannon  (+3 dmg)
  ARMOR: Light Plating  (+5 HP)
  UTILITY: Field Medic
```

**Briefing tab — Stats panel:**
```
> PERFORMANCE METRICS
  FLOORS CLEARED:    00
  ENEMIES DEFEATED:  000
  CARDS PLAYED:      000
  CREDITS EARNED:    0150
```

**Briefing tab — Deck overview:**
```
> DECK MANIFEST
  DECK: 12 cards
  ─────────────────
  COMBAT (6):
    Autocannon Burst    DMG:06 OL:02
    Rifle Fire          DMG:04 OL:01
    ...
  MOVEMENT (4):
    Advance             RNG:03 OL:01
    ...
  REPAIR (2):
    Patch Up            HEAL:05 OL:02
    ...
```

**Operations tab — Mission log:**
```
> MISSION LOG
  [Floor-specific narrative text here]
  Example: "Dropship insertion confirmed. Enemy patrols detected at 
  Outpost Alpha perimeter. Intel suggests light resistance."
```

**Operations tab — Room selection:**
```
> SELECT NEXT TARGET
  [ASSAULT] Enemy Patrol     RISK: HIGH     REWARD: Salvage
  [SALVAGE] Wreckage Site    RISK: LOW      REWARD: Equipment
  [R&R] Forward Camp         RISK: NONE     REWARD: Rest/Repair
```

**IMPORTANT:** All references to "Coins" must be "Credits" (CR:XXXX format).
The game's currency is military credits, not coins.

### HUD — "Tactical Feed"

In-combat display showing real-time telemetry.

**Top bar format:**
```
ALPHA          HP:025/030  OL:04/12  EN:03/03  DECK:12  CR:0150
YOUR TURN                                              [END TURN]
```

**Phase messages** (flash briefly):
- `> COMBAT START`
- `> YOUR TURN`
- `> ENEMY TURN`
- `> VICTORY`
- `> SIGNAL LOST` (defeat)

**Card format** (directives, not playing cards):
```
> DIRECTIVE: AUTOCANNON BURST
  TYPE: ATTACK | DMG: 06 | OL: 02
  [EXECUTE]
```

**IMPORTANT:** No "Hints" label showing "Click card -> Click tile".
This breaks terminal immersion. Tutorials must be framed as system prompts.

### CombatHUD — "Engagement Feed"

Full combat display with party/enemy panels.

**Party section:**
```
> FRIENDLY UNITS
  ◈ ALPHA-1    HP:025/030  [ENGAGED]
  ◈ BRAVO-1    HP:030/030  [STANDBY]
```

**Enemy section:**
```
> HOSTILE CONTACTS
  ◆ HOSTILE-A  HP:015/020  [ACTIVE]
  ◆ HOSTILE-B  HP:020/020  [ACTIVE]
```

**Phase label:**
```
> PHASE: COMBAT
```

### VictoryScreen — "Mission Complete"

```
> MISSION COMPLETE
  OPERATIONAL REPORT
  
  FLOORS CLEARED:     05
  ENEMIES DEFEATED:   023
  CARDS PLAYED:       187
  CREDITS EARNED:     0450
  CASUALTIES:         001
  
  OUTPOST ALPHA CLEARED. First base down.
  
  [RETURN TO BASE]
```

### GameOverUI — "Signal Lost"

```
> SIGNAL LOST
  UNIT LOST IN ACTION
  
  FLOORS CLEARED:     03
  FINAL POSITION:     GRID 14,07
  
  No extraction available. Another coordinator needed.
  
  [REDEPLOY]    [RETURN TO BASE]
```

### PauseMenu — "Operations Halted"

```
> OPERATIONS HALTED
  [PAUSED]
  
  [1] RESUME OPERATIONS
  [2] SAVE SESSION
  [3] RETURN TO BASE
```

### MerchantUI — "Supply Depot"

```
> SUPPLY DEPOT
  Floor 3 - Outpost Alpha    CR:0150
  
  [1] Autocannon Barrel    CR:0050  [PURCHASE]
  [2] Light Plating         CR:0030  [PURCHASE]
  [3] Field Medic Kit       CR:0040  [PURCHASE]
  
  [CLOSE]
```

### Scene Transitions

All scene changes must include terminal-style transition text:

**Main Menu → MechSelect:**
```
> INITIATING DEPLOYMENT SEQUENCE...
> LOADING UNIT DATABASE...
```

**MechSelect → Main (deploy):**
```
> DEPLOYMENT CONFIRMED
> CONNECTING TO TACTICAL FEED...
> LINK ESTABLISHED
```

**Floor transitions:**
```
> UPLOADING SECTOR DATA...
> SECTOR N LOADED
> SIGNAL RE-ACQUIRED
```

**Combat start:**
```
> ENGAGEMENT DETECTED
> SWITCHING TO TACTICAL FEED...
> LINK ESTABLISHED
```

**Victory:**
```
> HOSTILES NEUTRALIZED
> SECTOR CLEARED
> RETURNING TO COMMAND FEED...
```

**Defeat:**
```
> TELEMETRY FAILURE
> SIGNAL LOST
> ALL UNITS OFFLINE
```

### Color Conventions by Context

| Context | Color | Hex | Usage |
|---------|-------|-----|-------|
| Terminal text | Green phosphor | `#26D940` | Primary text, borders |
| Dim text | Dark green | `#147326` | Secondary labels, inactive |
| Bright text | Bright green | `#33FF57` | Hover states, active |
| Enemy/hostile | Red | `#E63333` | Enemy units, danger |
| Warning | Amber | `#D98C1A` | Overload, warnings |
| FSA friendly | Cyan | `#33CC99` | Friendly units |
| Disabled | Gray | `#666666` | Locked content |
| Background | Near-black | `#050803` | Screen background |
| Panel bg | Dark green-black | `#080C04` | Panel backgrounds |

---

## LORE INTEGRATION CHECKLIST

Before implementing new content, ask:

- [ ] Does it fit the gritty military sci-fi tone?
- [ ] Does it respect faction identities?
- [ ] Would this feel out of place in a Battletech/XCOM universe?
- [ ] Is the language understated, not florid?
- [ ] Are names descriptive rather than "cool"?
- [ ] Does it make sense in the context of "coordinating from orbit"?
- [ ] Would this be something a tactical coordinator would actually see/do?
- [ ] Does the visual style fit the degraded terminal aesthetic?
- [ ] Does all text use `>` prefix on headers?
- [ ] Are numbers zero-padded to fixed width?
- [ ] Are status indicators in bracketed tags?
- [ ] Is "Credits" used instead of "Coins"?

If any answer is "no", reconsider or adjust.

---

## CANON FAQ

**Q: Are there aliens?**  
A: No. All conflicts are human-on-human.

**Q: Is there FTL travel?**  
A: Not addressed. Keep it focused on the planetary conflict.

**Q: What year is it?**  
A: Not specified. "Far future" but not a specific date.

**Q: Are there non-mech units?**  
A: Mentioned: infantry, dropships, but they're background. Mechs are the focus.

**Q: What happened before the campaign?**  
A: The FSA has been fighting to take this planet. You're part of a final push, but not because you're special - because they wanted to get rid of you.

**Q: Why is it a solo mission?**  
A: Political reasons. You spoke out against FSA leadership's tyranny. They assigned you this mission to either fail or prove a point. It's not that you're the only one capable - you're the one they wanted to dispose of.

**Q: Are you the last person left?**  
A: No. There are other FSA forces, CC defenders, Rebel factions, and civilians on the planet. You're just alone in your command position.

**Q: Do choices really affect the game?**  
A: Yes. Decisions about helping or harming NPCs, sparing or killing enemies, and choosing which factions to aid should create branching encounters. These manifest as different enemy compositions, ally appearances, room events, and ultimately multiple possible endings.

**Q: What technology level is this?**  
A: Low-tech mech warfare. Think industrial machines with guns, not sleek sci-fi with lasers and hover. Thrusters are minimal, movement is ground-based and slow, weapons are mostly kinetic (bullets, missiles). Energy weapons exist but are experimental, unreliable, or rare.

**Q: Can mechs fly or hover?**  
A: No. Mechs are earthbound. They might have jump jets for limited vertical mobility, but no sustained flight or hovering. Movement is deliberately slow and weighty.

**Q: What about AI or smart technology?**  
A: Very limited. No sentient AI companions, no holographic assistants. Technology is mechanical and analog-feeling. Computers exist but are tools, not characters.

**Q: Is the FSA good or evil?**  
A: Both perspectives are valid. The FSA leadership has tyrannical tendencies (they exile dissidents on suicide missions), but regular troops may genuinely believe they're liberators. The CC are defending their homes but are also occupying forces. Morality is nuanced.

**Q: Can I reconcile with the FSA?**  
A: Possibly. If you succeed in your mission despite being a dissident, you might gain recognition. But the leadership that assigned you may still view you as a threat. Your fate after the campaign depends on your choices and reputation.

**Q: What's the tone?**  
A: Gritty, grounded, military sci-fi. Emphasis on weight, consequence, and survival. Not heroic fantasy - you're a coordinator in a command terminal trying to keep your pilots alive, with political baggage weighing you down.

**Q: Why does everything look geometric and low-res?**  
A: Because you're viewing a degraded tactical telemetry feed. Your terminal receives IFF transponder data, not video. The geometric shapes, scanlines, and noise are what your display actually shows - it's not an artistic choice, it's a diegetic constraint of the technology available to you.

**Q: Can mechs have detailed sprites?**  
A: No. The lore explicitly states that your terminal only shows geometric IFF symbols due to bandwidth and signal limitations. Detailed sprites would break the diegetic framing.
