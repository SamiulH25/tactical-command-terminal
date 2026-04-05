# Tactical Command Terminal — Project Documentation

> Turn-based mech deckbuilder with degraded CRT terminal aesthetic, built with
> Python + Pygame-CE.  Fully playable at 1920x1080 with proportional scaling.

---

## 1. High-Level Overview

The player is a **Coordinator** — a political dissident in the **Free Systems
Alliance (FSA)** — directing mech combat from orbit across a 25-floor planetary
campaign.  The entire game is presented inside a **physical CRT monitor** with
scanlines, vignette, and phosphor glow.  Every screen is a degraded tactical
terminal.

**Core loop:** Deploy a mech → pick encounters → play directives in combat →
earn credits/reputation → advance to the next floor → repeat through 25 floors
→ reach one of five endings.

---

## 2. Entry Point

### `main.py`
Bootstraps Pygame-CE, creates three core objects, then delegates to
`game_flow.run_game()`:

1. **`MonitorFrame`** — draws a physical CRT monitor bezel around the game
   content (dark bezel, inner shadow, glass glare, power LED, stand).
2. **`TerminalRenderer`** — applies CRT effects (scanlines, vignette, flicker)
   to the 1920x1080 game surface each frame.
3. **`display`** — the full Pygame window surface (1920x1080, windowed by
   default).

Error handling writes tracebacks to `crash.log` and always calls `pygame.quit()`
in a `finally` block.

---

## 3. Architecture Layers

```
┌─ main.py ──────────────────────────────────────────┐
│  MonitorFrame  │  TerminalRenderer  │  display      │
└─────────────────────────────────────────────────────┘
                          │
┌─ game_flow.py ─────────────────────────────────────┐
│  Game (state machine) + all screen wiring           │
└─────────────────────────────────────────────────────┘
                          │
┌─ src/screens/ ─────────────────────────────────────┐
│  MainMenu  │  MechSelect  │  ShipMenu               │
│  FloorSelect  │  CombatScreen  │  VictoryScreen     │
│  GameOverScreen  │  EventScreen  │  RewardScreen    │
│  FloorTransition                                    │
└─────────────────────────────────────────────────────┘
                          │
┌─ src/ui/ ──────────────────────────────────────────┐
│  Panel  │  TerminalButton  │  GridView              │
│  DirectiveView  │  MechView  │  CombatHUD            │
│  WarCommsWidget  │  TypingText  │  layout.py         │
└─────────────────────────────────────────────────────┘
                          │
┌─ src/systems/ ─────────────────────────────────────┐
│  combat  │  ai  │  los  │  deckbuilder              │
│  narrative  │  progression  │  endings              │
│  save_load  │  comms  │  war_comms  │  combat_comms  │
└─────────────────────────────────────────────────────┘
                          │
┌─ src/models/ ──────────────────────────────────────┐
│  mech  │  card  │  grid  │  faction  │  campaign    │
│  encounter  │  equipment  │  pilot  │  data_loader  │
└─────────────────────────────────────────────────────┘
                          │
┌─ data/ ────────────────────────────────────────────┐
│  mechs/*.json  │  cards/*.json  │  equipment/*.json │
│  pilots/*.json                                      │
└─────────────────────────────────────────────────────┘
```

### Dependency Rules (enforced by `--strict` mypy)
- **Models** depend on nothing (pure data).
- **Systems** depend on Models only — no UI, no screens.
- **UI** depends on Models and config — no screens, no systems
  (except `WarCommsWidget` → `war_comms.py`, a pure-text module).
- **Screens** depend on UI components, Models, and Systems.
- **`game_flow.py`** is the only file that wires everything together.

---

## 4. Core Systems

### 4.1 Combat System (`src/systems/combat.py`)

The single source of truth for a combat encounter.

**`CombatState`** manages:
- **Hand** (up to 5 directives), **draw pile**, **discard pile**
- **Energy** (resets each turn) and **max energy**
- **Mechs on the grid** (`MechOnGrid` — mech + position + friendly flag)
- **Phase** (`PLAYER_DIRECTIVE_SELECT` → `PLAYER_TARGETING` →
  `PLAYER_ANIMATING` → `ENEMY_TURN` → `COMBAT_COMPLETE`)

**Key methods:**
- `begin_combat()` — shuffles deck, draws 5 cards.
- `start_player_turn()` / `end_player_turn()` — discards hand, resets OL,
  draws new hand.
- `play_directive(index)` — moves a card from hand to discard, decrements
  energy.
- `check_completion()` — returns `CombatResult.VICTORY`, `DEFEAT`, or `None`.

**Current limitation:** `play_directive()` only discards the card and spends
energy. Actual damage resolution, targeting, and movement are wired through
the combat screen but not yet applied to enemy HP.

### 4.2 Enemy AI (`src/systems/ai.py`)

Deterministic enemy turn controller.

**Target priority:** Lowest HP first, then closest enemy.
**Directive selection:** Highest damage affordable and in range.
**Fallback:** Move toward nearest friendly.

### 4.3 Line of Sight (`src/systems/los.py`)

Bresenham raycasting through the grid.  Blocked by `WALL` terrain only.
Used by AI to determine if an attack is valid.

### 4.4 Deck Builder (`src/systems/deckbuilder.py`)

Composes the player's directive deck from three sources:
1. **Frame** starting directives
2. **Pilot** starting directives
3. **Equipment** granted directives

`build_deployed_mech()` creates a fully configured `DeployedMech` with all
stat bonuses (HP, OL, evasion, weapon damage) applied.

### 4.5 Narrative Engine (`src/systems/narrative.py`)

Processes player choices in narrative events.  Adjusts faction reputation,
credits, may rescue allies.  Choices are filtered by `requires` and `forbids`
decision tags.

### 4.6 Floor Progression (`src/systems/progression.py`)

Generates 25 floor templates.  Each floor has:
- **1 combat encounter** (always present)
- **2 optional encounters** (merchant, rest, event)

Special narrative text for milestone floors (1, 5, 6, 10, 11, 15, 16, 20, 25).

### 4.7 Endings (`src/systems/endings.py`)

Five endings evaluated in priority order:
1. **Betrayed** — player has a betrayal-tagged decision
2. **Redeemed** — FSA reputation ≥ 50
3. **Liberator** — Rebel + CC reputation both ≥ 20
4. **Conqueror** — Rebel + CC reputation both ≤ -40
5. **Exile** — default fallback

### 4.8 Save/Load (`src/systems/save_load.py`)

Versioned JSON serialization.  Three save slots.  Handles corruption and
version mismatches gracefully by returning defaults.

### 4.9 War Comms (`src/systems/war_comms.py`)

**193 lore-accurate messages** across three weighted tiers:
- **60% FSA Broadcast** (98 messages) — positive, morale-boosting
- **30% Intercepted** (60 messages) — Rebel/CC chatter, fragmentary reports
- **10% FSA Internal Leak** (35 messages) — dark truths about the FSA

### 4.10 Combat Comms (`src/systems/combat_comms.py`)

Contextual combat messages triggered by events (engagement start, damage
taken, enemy destroyed, player low HP, overload warning, enemy turn, ambient).
Messages are deduplicated and vary by floor range and faction reputation.

---

## 5. Data Models

### 5.1 Mechs (`src/models/mech.py`)
- **`MechFrame`** (frozen) — template loaded from JSON (HP, OL, evasion, IFF
  shape, starting directives, equipment slots, role).
- **`DeployedMech`** (mutable) — combat-ready mech with frame + pilot +
  equipment bonuses applied.  Tracks current HP/OL, deck, status.

### 5.2 Directives (`src/models/card.py`)
Cards the player plays in combat.  Types: `COMBAT`, `MOVEMENT`, `REPAIR`,
`UTILITY`.  Each has a target pattern (`NONE`, `SINGLE`, `LINE`, `CONE`,
`AREA`, `SELF`, `ALL_HOSTILES`), damage, OL cost, and range.

### 5.3 Combat Grid (`src/models/grid.py`)
10×10 grid with terrain types: `OPEN`, `COVER`, `WALL`, `HIGH_GROUND`,
`WATER`.  Each cell has passability, movement cost, cover bonus, and an
ASCII symbol.

### 5.4 Campaign (`src/models/campaign.py`)
Persistent playthrough state: current floor, faction reputation, stats
(enemies defeated, cards played, credits earned, floors cleared), unlocked
mechs/equipment, allies rescued.

### 5.5 Data Loader (`src/models/data_loader.py`)
Auto-discovers all JSON files in `data/mechs/`, `data/cards/`,
`data/equipment/`, `data/pilots/`.  Maps string enums to Python enums,
validates every entry, detects duplicates.

### 5.6 Equipment, Pilots, Factions, Encounters
All frozen dataclasses loaded from JSON.  Equipment grants stat bonuses and
optional directives.  Pilots provide stat modifiers and starting cards.
Factions (FSA, Crimson Compact, Rebel) have unique colors and IFF shapes.

---

## 6. Screens

### 6.1 Main Menu (`src/screens/main_menu.py`)
Terminal boot screen.  Greeting ("Hello Coordinator" with blinking cursor),
3 buttons, session status panel, system boot text, tactical summary box,
and the war effort comms feed.

### 6.2 Mech Select (`src/screens/mech_select.py`)
4-step deployment wizard:
1. **Unit Selection** — pick from 5 FSA mechs
2. **Operator Assignment** — pick pilot type
3. **Equipment Loadout** — accordion-style expandable slots
4. **Confirmation** — full preview panel on the right

Navigation validates prerequisites (must select mech before proceeding).

### 6.3 Ship Menu (`src/screens/ship_menu.py`)
Inter-combat hub with two tabs:
- **Briefing** — mech stats, deck manifest (grouped by directive type), cached
  per mech ID for performance.
- **Operations** — mission log, 3 room buttons (Assault, Salvage, R&R), war
  comms widget.

### 6.4 Floor Select (`src/screens/floor_select.py`)
Shows 3 encounter buttons for the current floor.  Narrative intro text
and floor progress (X/25).  Combat encounters trigger `CombatScreen`; rest
encounters heal the mech; merchant/event encounters are placeholders.

### 6.5 Combat Screen (`src/screens/combat.py`)
Primary engagement display:
- **GridView** (left/center) — terrain, IFF symbols, unit placement
- **Directive Queue** (right panel) — clickable hand cards
- **CombatHUD** (overlay) — top bar, party panel, enemy panel, phase label
- **Comms Log** (bottom-left) — scrolling combat flavor text

Flow: `begin_combat()` → player plays directives → hand empties → auto-end
turn → enemy AI processes → completion check → victory or defeat.

### 6.6 Victory / Game Over / Event / Reward / Floor Transition
Each is a focused screen with specific UI elements and a callback to continue
the game loop.  Victory shows an operational report.  Game Over shows "SIGNAL
LOST" with stats.  Event screen presents narrative choices.  Reward screen
offers directive selections.  Floor transition plays static burst + text crawl.

---

## 7. UI System

### 7.1 Proportional Scaling (`src/ui/layout.py`)
All screen positions are defined in **1920x1080 base coordinates** and scaled
via `s(x, y, w, h)`, `sx()`, `sy()`.  The scaling factors are computed once
from the actual display size and cached.

### 7.2 Components
| Component | Purpose |
|---|---|
| **Panel** | Bordered rectangle with optional `>`-prefixed title |
| **TerminalButton** | Clickable button with hover, keyboard shortcuts, enabled/disabled |
| **GridView** | Renders terrain backgrounds, grid borders, IFF shape overlays |
| **DirectiveView** | Renders a card as a terminal command entry with hover keywords |
| **MechView** | Compact status line: IFF symbol, callsign, HP/OL bars, status tag |
| **CombatHUD** | Full combat overlay: top bar, party panel, enemy panel, phase label |
| **WarCommsWidget** | Scrolling comms feed with TypingText animation (3 messages + 1 typing) |
| **TypingText** | Character-by-character reveal with configurable speed and word-wrapping |

### 7.3 Text Utilities (`src/ui/text.py`)
`pad()` (zero-padded numbers), `ratio_bar()` (block character progress bars),
`status_tag()` ([ACTIVE]/[STANDBY]/[CRITICAL]/[OFFLINE]), `divider()`,
`header()`, `coord()`.

---

## 8. CRT Effects (`src/core/terminal.py`)

Three effects are **active** each frame:
1. **Flicker** — sinusoidal brightness oscillation at 3 Hz, 8% intensity
2. **Vignette** — pre-rendered radial gradient (40 concentric circles, quadratic
   falloff)
3. **Scanlines** — pre-rendered horizontal dark lines every 2 rows at alpha 90

Six effects are **stubbed** (need safe additive-only implementations):
chromatic aberration, noise grain, phosphor bloom, afterimage, signal glitch,
barrel distortion.

---

## 9. Monitor Frame (`src/core/monitor_frame.py`)

Wraps the 1920x1080 game surface inside a physical CRT monitor:
- **Dark bezel** (20px thick)
- **Inner screen shadow** (top/left edges)
- **Glass glare** (diagonal semi-transparent polygon)
- **Power LED** (bottom-right, green)
- **Stand** (trapezoidal base)

The game surface is scaled via `pygame.transform.smoothscale` to fit within
the bezel while maintaining 16:9 aspect ratio.

---

## 10. Audio (`src/core/audio.py`)

All sounds are **generated programmatically via numpy** — no external audio
files.  Provides keyboard clicks, beeps, error sounds, static burst, combat
engagement sweep, victory chord, and a looping CRT hum background.

---

## 11. Complete Game Flow

```
1. main.py initializes Pygame, MonitorFrame, TerminalRenderer
2. game_flow.py creates Campaign, GameData, SoundManager, Game
3. MainMenu is pushed — player sees "Hello Coordinator" + war comms
4. Player clicks [1] NEW DEPLOYMENT
5. MechSelect wizard (4 steps) → DeployedMech is built
6. ShipMenu (Briefing/Operations tabs) → player picks an action
7. FloorSelectionScreen → player picks one of 3 encounters
8. If Combat:
   a. CombatScreen begins — 5 cards drawn, comms start
   b. Player clicks cards to play them (costs energy + OL)
   c. Hand empties → auto-end turn
   d. EnemyAI processes all hostiles (LOS check → attack or move)
   e. Completion check → VictoryScreen or GameOverScreen
9. If Rest: heal 5 HP, gain 10 credits
10. If Merchant/Event: placeholder (no implementation yet)
11. RewardScreen → player picks a directive from 3 choices
12. FloorTransition → static burst + text crawl
13. Loop back to FloorSelectionScreen for next floor
14. After floor 25 → EndingCalculator determines one of 5 endings
```

---

## 12. Data Files

| Directory | Files | Content |
|---|---|---|
| `data/mechs/` | 3 JSON files | 12 mech frames (5 FSA, 4 CC, 3 Rebel) |
| `data/cards/` | 4 JSON files | 16 directives (5 combat, 4 movement, 1 repair, 6 utility) |
| `data/equipment/` | 1 JSON file | 14 equipment modules (4 weapons, 5 armor, 5 utility) |
| `data/pilots/` | 1 JSON file | 5 pilot types (aggressive, defensive, tactical, scout, engineer) |
| `data/campaign/` | empty | Planned for data-driven floor configs |
| `data/narrative/` | empty | Planned for event/comms data |

---

## 13. Test Suite

**345 tests** across 20 test files, all passing:

| File | What it tests |
|---|---|
| `test_combat.py` | CombatState lifecycle, card play, completion detection |
| `test_combat_comms.py` | Message selection, damage thresholds, faction comms |
| `test_config.py` | Config constant validity (screen size, FPS, font sizes) |
| `test_deckbuilder.py` | Deck composition from frame + pilot + equipment |
| `test_effects.py` | ShakeEffect, FloatingNumber, StaticBurst, PhosphorGlow |
| `test_game.py` | Screen stack push/pop/replace, lifecycle callbacks |
| `test_grid_campaign.py` | Grid passability, Campaign serialization |
| `test_los.py` | Bresenham LOS, distance, range queries |
| `test_main.py` | Pygame init, display size, monitor frame |
| `test_models.py` | MechFrame validation, DeployedMech bonuses, directive validation |
| `test_monitor_frame.py` | Construction, screen rect, blit, bezel thickness |
| `test_narrative.py` | NarrativeEngine resolution, reputation, endings |
| `test_progression.py` | Floor templates, encounter generation, transitions |
| `test_save_load.py` | Save/load round-trip, corruption handling, user config |
| `test_terminal.py` | Scanlines, vignette, flicker, combined effects, stub safety |
| `test_typing_text.py` | Typewriter speed, wrapping, skip behavior |
| `test_ui.py` | Panel dimensions, button hover/click/keyboard, rendering |

---

## 14. Known Limitations & Technical Debt

1. **Combat damage not applied** — `play_directive()` discards the card and
   spends energy but does not deal damage or move mechs.
2. **Victory/Game Over button callbacks are stubs** — `_on_return` and the
   victory button's `_btn._on_click` wiring use fragile private attribute access.
3. **CRT effects partially implemented** — only 3 of 9 effects are active.
   The other 6 are stubbed as "needs safe additive-only implementation".
4. **`user_config.py` is unused** — the systems file exists but is not imported
   anywhere.
5. **HUD creates MechView every render** — `CombatHUD._update_hud()` instantiates
   new `MechView` objects each frame.  Could be cached.
6. **`data/campaign/` and `data/narrative/` are empty** — floor generation is
   procedural in code, not data-driven.
7. **Private attribute access** — `victory_screen._btn._on_click` in
   `game_flow.py` is a hack to wire the victory button callback after screen
   creation.

---

## 15. Quality Gates

Every change passes all four checks:
- `ruff check` — linting (zero errors)
- `ruff format` — formatting (all files formatted)
- `mypy --strict` — type checking (zero errors across 75 files)
- `pytest` — tests (345/345 passing in ~1.5s)

---

## 16. Config Constants (`src/config.py`)

| Category | Key | Value |
|---|---|---|
| **Display** | `SCREEN_WIDTH` / `SCREEN_HEIGHT` | 1920 / 1080 |
| | `FULLSCREEN` | `False` |
| | `MONITOR_BEZEL` | 20px |
| **Fonts** | `FONT_SIZE` / `FONT_SIZE_HEADER` / `FONT_SIZE_SMALL` | 20 / 26 / 16 |
| **CRT Effects** | `SCANLINE_ALPHA` / `SCANLINE_SPACING` | 90 / 2 |
| | `FLICKER_INTENSITY` / `FLICKER_FREQUENCY` | 0.08 / 3.0 Hz |
| | `VIGNETTE_STRENGTH` | 0.4 |
| **War Comms** | `_COMMS_INTERVAL` / `_TYPE_SPEED` | 12s / 12 chars/sec |

---

*This document reflects the codebase as of the current state.  All file paths
are relative to the project root (`C:\Users\Admin\Documents\Games\TestPythonGame`).*
