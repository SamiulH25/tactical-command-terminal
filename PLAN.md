# TACTICAL COMMAND TERMINAL — GAME DEVELOPMENT PLAN

**Project:** Turn-Based Mech Deckbuilder (Python + Pygame-CE)
**Engine:** Pygame-CE 2.5+ (Python 3.10+)
**Target Platform:** Windows (primary), Linux/macOS (secondary)
**Last Updated:** April 4, 2026

---

## TECHNOLOGY STACK

| Layer | Choice | Reason |
|-------|--------|--------|
| **Language** | Python 3.10+ | Readable, fast iteration, user preference |
| **Framework** | Pygame-CE 2.5+ | Community-maintained, active, 2D-focused |
| **Rendering** | Pygame Surface + pixel manipulation | Full control over CRT effects, scanlines, geometric art |
| **Font** | Terminus / Consolas (monospace) | Terminal authenticity |
| **Audio** | Pygame mixer | SFX: keyboard clicks, terminal beeps, radio static, CRT hum |
| **Testing** | `unittest` (stdlib) + `pytest` | Unit tests for all game logic |
| **Data** | JSON files | Mech definitions, card pools, floor configs, narrative events |
| **Serialization** | JSON (save files) | Human-readable, easy to debug |

---

## PROJECT STRUCTURE

```
TestPythonGame/
├── PLAN.md                  ← This document
├── LORE.md                  ← Lore/canon reference
├── requirements.txt         ← pygame-ce, pytest
├── pyproject.toml           ← Project metadata + pytest config
├── main.py                  ← Entry point: boot the game
│
├── src/
│   ├── __init__.py
│   ├── config.py            ← Constants: colors, fonts, screen size, timing
│   ├── constants.py         ← Lore constants: faction names, outpost names
│   ├── game.py              ← Main Game loop, state machine
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── terminal.py      ← TerminalRenderer: CRT effects, scanlines, phosphor glow
│   │   ├── effects.py       ← Static burst, screen shake, flicker, signal transitions
│   │   ├── audio.py         ← SoundManager: SFX playback, ambient CRT hum
│   │   ├── input.py         ← InputHandler: mouse + keyboard, CLI-style input
│   │   └── timer.py         ← GameTimer: turn clocks, animation timing
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── mech.py          ← Mech dataclass: HP, OL, cards, faction, IFF shape
│   │   ├── card.py          ← Directive dataclass: type, damage, overload, keywords
│   │   ├── faction.py       ← Faction enum, color mappings
│   │   ├── grid.py          ← Grid cell, terrain types, pathfinding
│   │   ├── encounter.py     ← Encounter definitions: combat, event, merchant, rest
│   │   ├── floor.py         ← Floor: list of encounters, narrative text
│   │   ├── campaign.py      ← Campaign: 25 floors, decision log, reputation tracking
│   │   └── save_data.py     ← Save file structure, serialization helpers
│   │
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── combat.py        ← Turn resolution, damage calc, overload mechanics
│   │   ├── directive.py     ← Directive queue, draw/discard, execution logic
│   │   ├── targeting.py     ← Target selection, range validation, pattern resolution
│   │   ├── ai.py            ← Enemy AI: target priority, directive selection
│   │   ├── deckbuilder.py   ← Deck construction, card rewards, merchant purchases
│   │   ├── narrative.py     ← Decision tracking, branching encounters, reputation
│   │   └── save_load.py     ← Save/load session to JSON
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── widget.py        ← Base Widget: position, render, click handling
│   │   ├── panel.py         ← Panel: bordered terminal window, title, content area
│   │   ├── button.py        ← TerminalButton: [EXECUTE], [BACK], numbered CLI buttons
│   │   ├── text.py          ← TypingText, TerminalText, monospace text rendering
│   │   ├── grid_view.py     ← Combat grid renderer: cells, terrain markers, IFF symbols
│   │   ├── card_view.py     ← Directive display: terminal-formatted card entries
│   │   ├── mech_view.py     ← Mech status panel: HP/OL bars, status tags
│   │   ├── hud.py           ← CombatHUD: top bar, party/enemy panels, phase label
│   │   └── transition.py    ← Scene transition overlay: static burst, text crawl
│   │
│   └── screens/
│       ├── __init__.py
│       ├── base_screen.py   ← Screen base class: handle_input, render, transition
│       ├── main_menu.py     ← Terminal boot screen: greeting, menu, status panel
│       ├── mech_select.py   ← Deployment wizard: unit select, equipment, operator, confirm
│       ├── ship_menu.py     ← Mission Command: briefing, operations, room selection
│       ├── combat.py        ← Main combat screen: grid, directives, enemy turns
│       ├── victory.py       ← Mission complete: operational report
│       ├── game_over.py     ← Signal lost: defeat screen
│       ├── merchant.py      ← Supply depot: purchase directives/equipment
│       ├── event_screen.py  ← Narrative event: text + choices
│       └── pause.py         ← Operations halted: resume, save, quit
│
├── data/
│   ├── mechs/
│   │   ├── fsa_bastion.json
│   │   ├── fsa_raptor.json
│   │   ├── fsa_anvil.json
│   │   ├── fsa_warden.json
│   │   ├── fsa_wraith.json
│   │   ├── cc_bastion.json
│   │   ├── cc_sentinel.json
│   │   ├── cc_siege.json
│   │   ├── cc_warden.json
│   │   ├── rebel_ghost.json
│   │   ├── rebel_rustbucket.json
│   │   └── rebel_warlord.json
│   ├── cards/
│   │   ├── combat.json      ← Attack directives
│   │   ├── movement.json    ← Movement directives
│   │   ├── repair.json      ← Repair directives
│   │   ├── utility.json     ← Utility directives
│   │   └── enemy.json       ← Enemy-only directives
│   ├── campaign/
│   │   ├── floor_01.json    ← Floor definitions (25 total)
│   │   ├── floor_02.json
│   │   │   ...
│   │   └── floor_25.json
│   └── narrative/
│       ├── events.json      ← Event encounter definitions
│       └── comms.json       ← Intercepted comm text per faction/floor range
│
├── assets/
│   ├── fonts/
│   │   └── terminus.ttf     ← Monospace terminal font
│   └── sfx/
│       ├── keypress.wav     ← Keyboard click
│       ├── beep.wav         ← Terminal beep/error
│       ├── static.wav       ← Radio static burst
│       ├── hum.wav          ← CRT background hum (looping)
│       ├── engage.wav       ← Combat engagement sound
│       └── victory.wav      ← Mission complete tone
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py          ← Pytest fixtures: test mechs, cards, grids
│   ├── test_mech.py         ← Mech creation, HP/OL clamping, death
│   ├── test_card.py         ← Directive validation, keyword checks
│   ├── test_combat.py       ← Turn resolution, damage calculation, overload
│   ├── test_deckbuilder.py  ← Deck construction, draw, shuffle, discard
│   ├── test_targeting.py    ← Range validation, pattern targeting, LOS
│   ├── test_ai.py           ← Enemy target priority, directive selection
│   ├── test_campaign.py     ← Floor progression, floor unlock logic
│   ├── test_narrative.py    ← Decision tracking, reputation calculation
│   ├── test_save_load.py    ← Serialization round-trip, corruption handling
│   ├── test_terminal.py     ← CRT effect application, color mapping
│   └── test_integration.py  ← Full combat flow, full floor progression
│
└── tools/
    ├── validate_data.py     ← Validate all JSON data files
    └── generate_floors.py   ← Procedural floor generation helper (dev only)
```

---

## CODE QUALITY STANDARDS

These requirements apply to **every phase, every file, every commit**. No exceptions.

### Architecture Principles

| Principle | Rule |
|-----------|------|
| **Single Responsibility** | Each class has one reason to change. Each function does one thing. |
| **Separation of Concerns** | Models know nothing about UI. Systems know nothing about rendering. Screens orchestrate, components render. |
| **Dependency Direction** | Dependencies flow inward: `screens → systems → models → core`. Models never import UI. Core never imports game logic. |
| **No Globals** | Game state lives in the `Game` class and is passed explicitly. No module-level mutable state. |
| **No Magic Numbers** | All constants live in `config.py` or are module-level named constants. |
| **No Dead Code** | No unused imports, no commented-out code, no unreachable branches. |

### Modularity Requirements

| Rule | Enforcement |
|------|------------|
| **Max file size:** 300 lines | Files exceeding this must be split. Exceptions: `combat.py`, `game.py` (max 500 lines with documented justification). |
| **Max function length:** 40 lines | Longer functions must be decomposed into named helpers. |
| **Max nesting depth:** 3 levels | Deeper nesting indicates a design problem — extract helper or use early returns. |
| **No circular imports** | Enforced by import order and dependency direction rules. |
| **Interfaces via base classes** | `Widget`, `Screen`, `Model` base classes define contracts. Subclasses implement. |
| **Data classes are immutable where possible** | Use `frozen=True` on dataclasses. Use `replace()` for modifications. |
| **Systems are pure where practical** | Systems take state, return new/modified state. No hidden side effects. |

### Type Safety

| Rule | Detail |
|------|--------|
| **Type hints on every function signature** | All parameters and return types annotated. |
| **No `Any` type** | Use union types (`X | Y`), protocols, or generics instead. |
| **No untyped `self`** | Instance attributes typed in `__init__` or class body. |
| **mypy clean** | `mypy src/` must pass with zero errors. Added to test suite. |

### Error Handling Standards

| Rule | Detail |
|------|--------|
| **No bare `except:`** | Always catch specific exceptions. `except Exception:` only as last resort with logging. |
| **No silent failures** | Every exception is either handled with user-visible feedback, logged, or re-raised. |
| **No `try/except` for flow control** | Use validation before operations, not exception catching for expected conditions. |
| **Every public method validates its inputs** | Invalid inputs raise `ValueError` or `TypeError` with descriptive messages. |
| **Resource cleanup in `finally` or context managers** | File handles, surfaces, audio — all cleaned up deterministically. |
| **Graceful degradation** | Missing asset → fallback, not crash. Corrupt save → new game with warning. |

### Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | `snake_case.py` | `combat.py`, `grid_view.py` |
| Classes | `PascalCase` | `TerminalRenderer`, `DirectiveQueue` |
| Functions/methods | `snake_case` | `resolve_damage()`, `handle_click()` |
| Constants | `UPPER_SNAKE_CASE` | `MAX_OL`, `PHOSPHOR_GREEN` |
| Private members | Leading underscore | `_render_scanlines()`, `_validate_target()` |
| Dataclass fields | `snake_case` | `max_hp`, `iff_shape` |

### Documentation Standards

| Element | Requirement |
|---------|------------|
| **Module docstring** | Every file starts with one-line summary of its purpose. |
| **Class docstring** | Every class has a docstring explaining its role and invariants. |
| **Public method docstring** | Args, return value, and exceptions raised documented. |
| **Complex logic** | Inline comments explain *why*, not *what*. |
| **No TODO comments in committed code** | TODOs belong in the task tracker. If unavoidable, must include issue reference. |

### Code Review Checklist (Every Commit)

- [ ] No linting errors (`ruff check src/` or `flake8 src/`)
- [ ] No type errors (`mypy src/`)
- [ ] All new code has tests
- [ ] All tests pass
- [ ] No unused imports
- [ ] No magic numbers
- [ ] Error handling is explicit, not silent
- [ ] Follows dependency direction (no backward imports)
- [ ] File size within limits
- [ ] Lore-compliant (if adding content)

### Tooling

| Tool | Purpose | Command |
|------|---------|---------|
| **ruff** | Linting + formatting | `ruff check src/ && ruff format --check src/` |
| **mypy** | Type checking | `mypy src/ --strict` |
| **pytest** | Testing | `pytest tests/ -v --cov=src --cov-report=term-missing` |
| **validate_data.py** | JSON schema validation | `python tools/validate_data.py` |

All four must pass before any phase is marked complete.

### Zero-Mistake Policy

"Zero mistakes" means:

1. **No runtime crashes** — Every possible user input and game state is handled.
2. **No logic bugs** — Every function behaves exactly as its docstring and tests specify.
3. **No data corruption** — Save/load round-trips are bit-identical for unchanged state.
4. **No visual glitches** — CRT effects render correctly at all resolutions. Text never clips or overlaps.
5. **No orphan branches** — Every `if` has a tested `else` or documented unreachable case.

This is enforced by:
- **Test coverage ≥ 80%** on models and systems (100% on critical paths: combat resolution, save/load)
- **CI pipeline** runs linter, type checker, and tests on every commit
- **Manual playtest** at every milestone — automated tests catch logic bugs; playtests catch feel bugs

---

## PHASE BREAKDOWN

Each phase is **independently testable** and produces a working (if incomplete) build.

---

### PHASE 1: Foundation — "Terminal Boot"

**Goal:** Get a window on screen with CRT aesthetic and basic state machine.

**Sub-phases:**

| # | Task | Files | Tests |
|---|------|-------|-------|
| 1.1 | Project scaffolding: `main.py`, `src/` layout, `requirements.txt`, `pyproject.toml` | `main.py`, `requirements.txt`, `pyproject.toml` | — |
| 1.2 | `config.py`: screen size (1024x768), colors (green phosphor palette), font config, timing constants | `src/config.py` | `test_config.py` — verify color hex values, screen dimensions |
| 1.3 | `TerminalRenderer`: scanline overlay, phosphor glow, CRT curvature (barrel distortion via surface manipulation), flicker | `src/core/terminal.py` | `test_terminal.py` — render surface has scanlines, colors match palette |
| 1.4 | `Game` state machine: screen stack, screen transitions, basic event loop | `src/game.py`, `src/screens/base_screen.py` | `test_game.py` — screen push/pop, transition trigger |
| 1.5 | `MainMenu` screen: boot text greeting, 3 buttons, status panel, terminal bezel | `src/screens/main_menu.py`, `src/ui/panel.py`, `src/ui/button.py`, `src/ui/text.py` | `test_main_menu.py` — button hover/click, correct text rendering |
| 1.6 | Input handler: mouse clicks on UI, keyboard shortcuts (numbered commands) | `src/core/input.py` | `test_input.py` — key bindings, mouse-to-button mapping |
| 1.7 | **Milestone:** Launch game → see green CRT terminal with working menu → click button → see static transition → blank screen | — | **Integration test** |

**CRT Effects Required in Phase 1:**
- Scanlines (every other row darkened)
- Phosphor green text on near-black background
- Subtle screen flicker (random brightness ±3%)
- Terminal bezel overlay (corner brackets, terminal ID, channel indicator)

**Error Handling:**
- Font load failure → fallback to system monospace
- Invalid screen state → log error, reset to main menu
- Surface creation failure → graceful degradation

---

### PHASE 2: Data Models — "Unit Database"

**Goal:** All game data defined in JSON, loaded into Python objects, fully validated.

**Sub-phases:**

| # | Task | Files | Tests |
|---|------|-------|-------|
| 2.1 | `Mech` dataclass: name, faction, HP, max_HP, OL, max_OL, cards, IFF shape/color, traits | `src/models/mech.py` | `test_mech.py` — HP clamping, death detection, IFF symbol assignment |
| 2.2 | `Directive` (card) dataclass: name, type, damage/heal/move values, overload cost, keywords, range, pattern | `src/models/card.py` | `test_card.py` — value validation, keyword parsing |
| 2.3 | `Faction` enum + color mappings per lore doc | `src/models/faction.py` | `test_faction.py` — color lookup, faction name validation |
| 2.4 | `GridCell` + `TerrainType`: wall, cover, high ground, water, open | `src/models/grid.py` | `test_grid.py` — terrain type validation, movement cost lookup |
| 2.5 | `Encounter` types: combat, event, merchant, rest with associated data | `src/models/encounter.py` | `test_encounter.py` — encounter creation, type validation |
| 2.6 | `Floor` definition: encounters list, narrative text, outpost name | `src/models/floor.py` | `test_floor.py` — floor validation, encounter count |
| 2.7 | `Campaign` model: 25 floors, decision log, reputation dict, current floor tracker | `src/models/campaign.py` | `test_campaign.py` — floor progression, decision append |
| 2.8 | JSON data loaders: mech loader, card loader, floor loader with validation | `data/` JSON files + loader in `src/models/` | `test_data_loading.py` — all JSON files load, schema validation |
| 2.9 | `validate_data.py` tool: check all JSON files against schemas | `tools/validate_data.py` | Run against all data files |
| 2.10 | **Milestone:** All 12 mechs defined, all card types defined, data validation tool passes | — | **Full data validation test** |

**Error Handling:**
- Missing JSON file → clear error with file path
- Invalid JSON schema → detailed error with field name and expected type
- Duplicate mech/card IDs → error with conflict details
- HP/OL values out of range → clamp with warning

---

### PHASE 3: UI System — "Command Console"

**Goal:** Reusable UI components that render as terminal windows with proper styling.

**Sub-phases:**

| # | Task | Files | Tests |
|---|------|-------|-------|
| 3.1 | `Widget` base class: rect, render(), handle_click(), hover state | `src/ui/widget.py` | `test_widget.py` — positioning, click detection, hover |
| 3.2 | `Panel`: terminal window with corner brackets, title with `>` prefix, bordered content area | `src/ui/panel.py` | `test_panel.py` — border rendering, title formatting |
| 3.3 | `TerminalButton`: `[1] NEW DEPLOYMENT` style, hover brightens, click animation | `src/ui/button.py` | `test_button.py` — label formatting, hover/click behavior |
| 3.4 | `TypingText`: character-by-character reveal animation, configurable speed | `src/ui/text.py` | `test_text.py` — typing animation complete, skip animation |
| 3.5 | `MechView`: mech status panel — HP/OL bars (block characters), status tags `[ACTIVE]`/`[CRITICAL]` | `src/ui/mech_view.py` | `test_mech_view.py` — bar rendering at various HP%, tag formatting |
| 3.6 | `CardView` (DirectiveView): terminal-formatted directive entry with type color, hover tooltip | `src/ui/card_view.py` | `test_card_view.py` — formatting, type colors, hover tooltip |
| 3.7 | `GridView`: combat grid with terrain markers, faint scanlines, range indicators (dashed lines) | `src/ui/grid_view.py` | `test_grid_view.py` — cell rendering, terrain symbols, range overlay |
| 3.8 | `CombatHUD`: top bar, party panel, enemy panel, phase label | `src/ui/hud.py` | `test_hud.py` — all panels render, data binding to models |
| 3.9 | **Milestone:** UI mock screen showing all components rendering correctly | — | **UI integration test** |

**Terminal Styling Rules (enforced in UI):**
- All text: monospace, `>` prefix on headers
- Numbers: zero-padded (`025/030`, `00/012`)
- Status: bracketed tags (`[ACTIVE]`, `[STANDBY]`, `[OFFLINE]`, `[CRITICAL]`)
- Dividers: `─────────────────`
- No rounded corners, gradients, or modern UI elements
- Type colors: green (text), red (enemy), amber (warning), cyan (friendly)

**Error Handling:**
- Text overflow in panel → truncate with `...` and log warning
- Missing font glyph → substitute with `?` character
- Button outside panel bounds → log error, render anyway

---

### PHASE 4: Combat Engine — "Engagement Feed"

**Goal:** Full turn-based combat on a grid with directive play, targeting, enemy AI.

**Sub-phases:**

| # | Task | Files | Tests |
|---|------|-------|-------|
| 4.1 | `CombatState`: combat initialization with mechs, grid setup, turn order | `src/systems/combat.py` | `test_combat.py` — combat setup, mech placement, turn order |
| 4.2 | `DirectiveQueue`: hand management — draw, play, discard, shuffle, deck exhaustion | `src/systems/directive.py` | `test_directive.py` — draw X cards, play card, discard, reshuffle |
| 4.3 | `TargetingSystem`: click-to-target, range validation, pattern (single, line, area) | `src/systems/targeting.py` | `test_targeting.py` — in-range check, line/area pattern resolution |
| 4.4 | Directive execution: attack (damage calc), movement (reposition), repair (heal), utility (buff/shield) | `src/systems/combat.py` | `test_combat.py` — damage formula, movement validation, heal amount |
| 4.5 | Overload (OL) system: track OL per turn, OL cost on directives, turn reset, overload penalty | `src/systems/combat.py` | `test_combat.py` — OL accumulation, penalty trigger, reset |
| 4.6 | Enemy AI: target priority (lowest HP mech first), directive selection from enemy deck | `src/systems/ai.py` | `test_ai.py` — enemy picks valid target, plays valid directive |
| 4.7 | Enemy turn resolution: sequential enemy actions, damage application, OL tracking | `src/systems/combat.py`, `src/systems/ai.py` | `test_combat.py` — full enemy turn, state after resolution |
| 4.8 | Death/removal: mech destruction, victory/defeat detection, cleanup | `src/systems/combat.py` | `test_combat.py` — all enemies dead → victory, all friendlies dead → defeat |
| 4.9 | `CombatScreen`: wire all UI + systems together — playable combat loop | `src/screens/combat.py` | `test_integration.py` — full combat flow from start to victory/defeat |
| 4.10 | **Milestone:** Playable combat against 1-2 enemies — play cards, move, attack, end turn, enemy responds, win/lose | — | **Full combat integration test** |

**Error Handling:**
- Invalid directive target → reject with terminal error message
- OL exceeded → apply penalty (skip next directive), log event
- Deck exhausted with no discard → player can only End Turn
- Null pointer on mech removal → defensive checks before cleanup
- Combat state corruption → save debug snapshot, reset to safe state

---

### PHASE 5: Campaign Flow — "Mission Command"

**Goal:** Navigate the 25-floor campaign with inter-combat screens.

**Sub-phases:**

| # | Task | Files | Tests |
|---|------|-------|-------|
| 5.1 | `MechSelectScreen` (Deployment Wizard): 4-step wizard — unit, equipment, operator, confirm | `src/screens/mech_select.py` | `test_mech_select.py` — step navigation, validation, deployment |
| 5.2 | `ShipMenu` (Mission Command): Briefing tab (mech stats, deck overview) + Operations tab (mission log, room select) | `src/screens/ship_menu.py` | `test_ship_menu.py` — tab switching, data display, room selection |
| 5.3 | Floor progression: complete floor → unlock next → floor transition text | `src/models/campaign.py`, `src/game.py` | `test_campaign.py` — sequential floor unlock, transition trigger |
| 5.4 | `MerchantScreen` (Supply Depot): purchase directives/equipment with Credits | `src/screens/merchant.py` | `test_merchant.py` — purchase, credit deduction, inventory update |
| 5.5 | `EventScreen` (narrative events): text + 2-3 choices with consequences | `src/screens/event_screen.py` | `test_event_screen.py` — choice selection, consequence application |
| 5.6 | Reward system: post-combat rewards — card pick, credits, equipment | `src/systems/deckbuilder.py` | `test_deckbuilder.py` — card reward selection, deck update |
| 5.7 | `VictoryScreen` + `GameOverScreen`: operational report, return to base | `src/screens/victory.py`, `src/screens/game_over.py` | `test_victory.py`, `test_game_over.py` — stats display, navigation |
| 5.8 | `PauseMenu`: resume, save session, return to base | `src/screens/pause.py` | `test_pause.py` — save creation, navigation |
| 5.9 | **Milestone:** Full loop — select mech → briefing → combat → rewards → next floor → merchant → combat → victory | — | **Campaign loop integration test** |

**Error Handling:**
- No credits for purchase → disable button, show `[INSUFFICIENT CREDITS]`
- Invalid floor progression → log error, repeat current floor
- Campaign data missing → generate default floor, log warning
- Save file corrupted → offer new deployment, warn about lost data

---

### PHASE 6: CRT/Terminal Effects — "Signal Degradation"

**Goal:** Full terminal immersion — effects on every interaction and transition.

**Sub-phases:**

| # | Task | Files | Tests |
|---|------|-------|-------|
| 6.1 | Scanline overlay (Phase 1 basic → production quality): per-pixel, configurable intensity | `src/core/terminal.py` | `test_terminal.py` — scanline pattern correctness |
| 6.2 | Screen flicker: random brightness oscillation, configurable frequency | `src/core/terminal.py` | `test_terminal.py` — flicker range within bounds |
| 6.3 | Static burst transition: full-screen noise for 0.3-0.5s on scene changes | `src/core/effects.py` | `test_effects.py` — static burst duration, noise pattern |
| 6.4 | Screen shake: offset surface randomly for N frames on damage | `src/core/effects.py` | `test_effects.py` — shake magnitude decays over duration |
| 6.5 | Floating damage numbers: brief numeric popup at mech position | `src/core/effects.py` | `test_effects.py` — number spawn, rise animation, fade out |
| 6.6 | Typing animation: character-by-character text reveal on narrative text | `src/ui/text.py` | `test_text.py` — typing speed, skip completion |
| 6.7 | Signal loss/Re-acquire: fade to static, then new scene with `> SIGNAL RE-ACQUIRED` | `src/ui/transition.py` | `test_transition.py` — full sequence: fade → static → reveal |
| 6.8 | Audio SFX: keypress, beep, static, CRT hum (looping), engage, victory | `src/core/audio.py`, `assets/sfx/` | `test_audio.py` — SFX playback, loop control, volume |
| 6.9 | **Milestone:** Every scene change has static burst, every combat action has feedback (shake, numbers, audio) | — | **Effects integration test** |

**CRT Effect Specifications:**

| Effect | Implementation | Trigger |
|--------|---------------|---------|
| Scanlines | Dark horizontal lines every 2nd row, 30% opacity | Permanent overlay |
| Phosphor glow | Text has slight green halo (blurred copy behind) | Permanent on text surfaces |
| Flicker | Random ±3% brightness per frame, 2Hz | Permanent |
| Static burst | Random pixel noise, full screen, 0.3-0.5s | Scene transitions |
| Screen shake | Surface offset ±2-5px, decaying, 0.2s | Damage taken |
| Floating numbers | White numbers, rise + fade, 0.8s | Damage dealt/healed |
| Typing text | One char per frame (configurable speed) | Narrative text, comm messages |
| CRT curvature | Barrel distortion on final render surface (optional, performance-dependent) | Permanent (if perf allows) |
| Signal fade | Alpha interpolation to black/static, 0.5s | Death, defeat, floor complete |

**Error Handling:**
- SFX file missing → log warning, continue without sound
- Surface too small for effect → skip effect, log debug message
- Audio device unavailable → disable all audio, show terminal warning
- Performance drop from CRT effects → provide config toggle to disable curvature

---

### PHASE 7: Narrative System — "Decision Log"

**Goal:** Branching encounters, reputation tracking, consequences across the campaign.

**Sub-phases:**

| # | Task | Files | Tests |
|---|------|-------|-------|
| 7.1 | `DecisionLog`: persistent array of choice IDs, query by type/floor | `src/models/campaign.py`, `src/systems/narrative.py` | `test_narrative.py` — append, query, filter decisions |
| 7.2 | `ReputationSystem`: track FSA loyalty, CC mercy, Rebel trust as numeric values | `src/systems/narrative.py` | `test_narrative.py` — reputation update, threshold lookup |
| 7.3 | Event encounter branching: different options/outcomes based on reputation | `src/screens/event_screen.py`, `src/systems/narrative.py` | `test_narrative.py` — event variation based on reputation |
| 7.4 | Combat encounter variation: enemy composition changes based on decisions | `src/systems/combat.py`, `src/systems/narrative.py` | `test_narrative.py` — different enemy sets for different reputations |
| 7.5 | NPC appearance system: saved allies appear as reinforcements, spared enemies return | `src/systems/narrative.py` | `test_narrative.py` — ally spawn logic, enemy return logic |
| 7.6 | Intercepted comms: faction-specific comm text based on floor range and reputation | `data/narrative/comms.json` | `test_comms.py` — correct comm text for context |
| 7.7 | Multiple endings: victory conditions vary based on accumulated choices | `src/screens/victory.py` | `test_endings.py` — ending variation based on decision log |
| 7.8 | **Milestone:** Play through 5+ floors with meaningful choices that alter encounters and narrative | — | **Narrative integration test** |

**Error Handling:**
- Decision references non-existent event → log error, use default outcome
- Reputation value out of range → clamp to [-100, 100], log warning
- Missing narrative text for branch → use fallback generic text
- Ally reinforcement data missing → skip reinforcement, log warning

---

### PHASE 8: Polish & Ship — "Link Established"

**Goal:** Complete playthrough, save/load, bug fixes, performance, release prep.

**Sub-phases:**

| # | Task | Files | Tests |
|---|------|-------|-------|
| 8.1 | Save/load system: serialize campaign state to JSON, load and resume | `src/systems/save_load.py` | `test_save_load.py` — round-trip serialization, corruption detection |
| 8.2 | All 25 floor JSON files with varied encounters, narrative text, outpost names | `data/campaign/floor_01.json` – `floor_25.json` | `test_campaign.py` — all floors load, encounter variety |
| 8.3 | Full narrative event set: 15+ events with branching choices | `data/narrative/events.json` | `test_narrative.py` — all events parse, choices valid |
| 8.4 | Complete card pool: balanced directive sets for all mech variants | `data/cards/*.json` | `test_deckbuilder.py` — deck balance, card variety |
| 8.5 | Full playthrough test: start → floor 25 → victory, document bugs | Manual + scripted test | Bug log → fix → re-test |
| 8.6 | Performance optimization: maintain 60fps with CRT effects, optimize grid rendering | Profile + optimize | Performance benchmark |
| 8.7 | Error handling audit: all edge cases covered, no crashes, graceful degradation | All files | Negative tests, edge case tests |
| 8.8 | Config file: user-configurable settings (volume, CRT effects toggle, font size) | `config.json` | Config load/save, validation |
| 8.9 | Release packaging: requirements.txt, README with setup instructions, executable build (PyInstaller) | `requirements.txt`, `README.md` | Clean install test on fresh machine |
| 8.10 | **Milestone:** Shippable game — full 25-floor campaign, save/load, no crashes, 60fps | — | **Full regression test suite** |

**Error Handling:**
- Save file from older version → migration script or clear warning
- PyInstaller build fails → fallback to source distribution
- Performance below 60fps → auto-disable CRT curvature, reduce flicker frequency
- Unhandled exception in production → catch-all handler, save crash log, return to main menu

---

## TESTING STRATEGY

### Quality Gates

Before any code is committed, **all four** checks must pass:

```bash
ruff check src/ && ruff format --check src/   # Linting + formatting
mypy src/ --strict                             # Type checking
pytest tests/ -v --cov=src                     # Tests + coverage
python tools/validate_data.py                  # Data validation
```

A phase is **not complete** until all gates pass. No exceptions, no "we'll fix it later."

### Unit Tests (every phase)
- **Every model class** has tests for: construction with valid data, construction with invalid data (rejects correctly), edge cases (zero HP, empty deck, max overload)
- **Every system class** has tests for: normal operation, boundary conditions, error conditions, state transitions
- **Every UI component** has tests for: rendering (no crash), click handling, hover state
- Test coverage target: **80%+** on `src/models/` and `src/systems/`, **100%** on `src/systems/combat.py` damage resolution and `src/systems/save_load.py`

### Integration Tests (milestone of each phase)
- Phase 1: Menu → transition → blank screen
- Phase 2: All data files load without errors, validation tool passes
- Phase 3: All UI components render correctly on mock screen
- Phase 4: Full combat loop (play cards → enemy turn → victory/defeat)
- Phase 5: Full campaign loop (briefing → combat → rewards → next floor)
- Phase 6: All CRT effects active and performant (≥60fps)
- Phase 7: Narrative choices alter future encounters
- Phase 8: Full 25-floor playthrough

### Error Handling Tests (every phase)
Every error path is tested, not just the happy path:

| Scenario | Expected Behavior |
|----------|------------------|
| Invalid input data | `ValueError` with field name and expected type |
| Missing asset file | Log warning, use fallback default, continue |
| Corrupt save file | Log error, offer new game, never crash |
| Surface creation failure | Graceful degradation, log error |
| Audio device unavailable | Disable audio, show terminal warning message |
| JSON schema violation | Reject with detailed error, list all violations |
| State corruption | Save debug snapshot, reset to safe state, log full traceback |
| Division by zero (damage calc) | Defensive check, log error, use default value |
| Empty deck | Player can only End Turn, no crash |
| No valid targets | Reject directive play, return to hand, show terminal error |

### Negative Tests
Tests that verify the system **correctly rejects** bad input:
- Mech with negative HP → rejected
- Directive with negative damage → rejected
- Floor with no encounters → rejected
- Campaign with missing floor files → error with path
- Save file with wrong version → migration attempt or rejection with message

### Performance Tests
- Grid rendering: ≤5ms per frame at 100x100 grid
- CRT effects: ≤2ms overhead per frame
- Full scene render: ≥60fps sustained
- Memory: no growth over 1000-frame idle test

### Test Commands
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Run specific phase tests
pytest tests/test_mech.py tests/test_card.py tests/test_combat.py -v

# Run integration tests
pytest tests/test_integration.py -v

# Run performance tests
pytest tests/test_performance.py -v

# Full quality gate
ruff check src/ && ruff format --check src/ && mypy src/ --strict && pytest tests/ --cov=src -v
```

---

## CRT/TERMINAL EFFECT REQUIREMENTS (Summary)

Every screen and interaction must reinforce the **degraded command terminal** aesthetic:

| Requirement | Implementation | Phase |
|---|---|---|
| Green phosphor color palette | Config-defined, enforced in TerminalRenderer | 1 |
| Scanline overlay | Per-pixel surface manipulation, 30% opacity lines | 1, 6 |
| Monospace terminal font | Terminus/Consolas, loaded in config | 1 |
| `>` prefix on all headers | Enforced in Panel and text rendering | 3 |
| Zero-padded numbers | Format helper function, enforced in all UI | 3 |
| Bracketed status tags | `[ACTIVE]`, `[CRITICAL]`, etc. — helper function | 3 |
| Typing animation | Character-by-character reveal, skippable | 6 |
| Static burst on transitions | Full-screen noise, 0.3-0.5s | 6 |
| Screen shake on damage | Random offset, decaying, 0.2s | 6 |
| Floating damage numbers | Rise + fade, 0.8s | 6 |
| Signal fade/Re-acquire | Alpha interpolation, static, text reveal | 6 |
| CRT hum (audio) | Looping low-frequency hum | 6 |
| Keyboard click SFX | On button press | 6 |
| Terminal beep on errors | On invalid actions | 6 |
| No modern UI elements | No rounded corners, gradients, shadows — enforced in code review | All |

---

## ASSUMPTIONS & DECISIONS

| Decision | Rationale |
|----------|-----------|
| **Pygame-CE over Pygame** | Community edition is actively maintained, Python 3.14 support |
| **JSON over TOML/YAML** | stdlib support, no extra dependencies, easy to validate |
| **Dataclasses over plain classes** | Type hints, auto-generated `__init__`, easy serialization |
| **1024x768 resolution** | 4:3 aspect ratio matches CRT terminal aesthetic |
| **No sprite art** | Lore explicitly requires geometric IFF symbols only |
| **Deterministic combat** | No randomness in targeting — only card draw is random |
| **Single-player only** | Lore is solo coordinator experience |
| **No multiplayer** | Not in lore scope, would complicate architecture |
| **Python 3.10+ required** | Match patterns, type union syntax (`X | Y`), dataclass features |

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| Pygame performance with CRT effects | Profile early, provide config toggle to disable curvature |
| Scope creep on 25 floors | Start with 5 floors, expand incrementally |
| Complex branching narrative | Use decision log + reputation thresholds, not unique code paths |
| JSON data file errors | Validation tool runs in CI, schema enforcement on load |
| Test coverage gaps | Enforce 80% coverage on models/systems, integration tests for screens |
| Audio asset availability | Generate SFX programmatically if needed (simple waveforms) |
| Type errors slipping through | `mypy --strict` in quality gate, no `Any` allowed |
| Circular imports breaking modules | Dependency direction enforced by linter + architectural review |
| Files growing beyond limits | Hard limit enforced in code review, refactor before merging |
| Silent bugs in combat logic | 100% test coverage on damage resolution, property-based tests for edge cases |
| UI rendering glitches | Pixel-level assertions in UI tests, manual playtest at every milestone |

---

## PROGRESSION RULES

1. **Each phase must pass all four quality gates before starting the next** — linter, type checker, tests, data validation
2. **Milestone builds must be playable** (even if content is minimal)
3. **No phase depends on future phase content** — each is self-contained
4. **Tests are written alongside code, not after** — no code without its tests in the same commit
5. **Lore compliance checked at every milestone** — review against LORE.md
6. **No dead code ships** — every function, class, and branch is exercised by a test
7. **No phase is "mostly done"** — a phase is done when every sub-task is done and every test passes
8. **Refactoring is allowed at any time** but must not break tests or change behavior
9. **Performance regressions block progression** — if a phase drops below 60fps, it doesn't pass
10. **Code review on every commit** — the checklist in Code Quality Standards is not optional

---

## NEXT STEP

Review this plan. When you're ready, I'll begin with **Phase 1: Foundation** — project scaffolding, terminal renderer, and main menu.
