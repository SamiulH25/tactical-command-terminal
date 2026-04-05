# Tactical Command Terminal

**Turn-based mech deckbuilder with a degraded CRT terminal aesthetic.**

You are a Tactical Coordinator aboard an orbiting command vessel, directing
mech pilots across 25 floors of hostile territory.  The entire game is
presented through a degraded tactical command terminal — geometric IFF
symbols, scanlines, signal noise, and compressed data.

---

## Quick Start

### Requirements

- **Python 3.10+**
- **Pygame-CE 2.5+** (community edition)

### Installation

```bash
# Clone or download this repository
cd TestPythonGame

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

### Controls

| Input | Action |
|-------|--------|
| **Mouse click** | Select buttons, directives, encounters |
| **1, 2, 3** | Keyboard shortcuts for numbered menu options |
| **ESC** | Quit the game / return to previous screen |

---

## Game Structure

### Campaign

The campaign spans **25 floors** across 5 sectors:

| Floors | Sector | Outpost |
|--------|--------|---------|
| 1-5 | Alpha | First contact, light resistance |
| 6-10 | Bravo | Resistance increases |
| 11-15 | Charlie | Deep enemy territory |
| 16-20 | Delta | Final approach |
| 21-25 | Command Fortress | Final assault |

### Mechs

Five FSA Vanguard variants, each with unique IFF shapes and roles:

| Mech | Role | IFF Shape | Playstyle |
|------|------|-----------|-----------|
| **Bastion** | Tank | Square | Frontline absorber |
| **Raptor** | Scout | Diamond | Flanking, hit-and-run |
| **Anvil** | Heavy | Hexagon | Breakthrough assault |
| **Warden** | Defender | Circle + cross | Area denial, team defense |
| **Wraith** | Stealth | Chevron | Surgical strikes, glass cannon |

### Directives (Cards)

Your "deck" of tactical orders.  Each directive has:
- **Type**: Combat (attack), Movement (reposition), Repair (heal), Utility (buff)
- **Overload Cost**: OL consumed when played
- **Range**: Maximum targeting distance
- **Pattern**: Single target, line, area, etc.

---

## Architecture

```
src/
├── core/          # Terminal renderer, effects, audio
├── models/        # Data: mechs, directives, factions, grid, campaign
├── systems/       # Game logic: combat, AI, deckbuilding, narrative, save/load
├── ui/            # UI components: panels, buttons, views, HUD
└── screens/       # Full screens: menu, combat, campaign hub, events
```

All game data (mechs, directives, equipment, encounters) is defined in
JSON files under `data/`.  Add new content without touching code.

---

## Configuration

Create a `config.json` in the project root to override defaults:

```json
{
  "master_volume": 0.5,
  "crt_effects": true,
  "font_size": 16,
  "window_scale": 1.0
}
```

| Setting | Range | Default | Description |
|---------|-------|---------|-------------|
| `master_volume` | 0.0-1.0 | 0.5 | Audio volume |
| `crt_effects` | bool | true | Enable scanlines and flicker |
| `font_size` | int > 0 | 16 | Font size in pixels |
| `window_scale` | 0.25-2.0 | 1.0 | Display scale factor |

---

## Save Files

Save files are stored in `saves/slot_1.json` through `slot_3.json`.
Three save slots are available.  Save files are human-readable JSON.

---

## Development

### Quality Gates

Every commit must pass all four checks:

```bash
ruff check src/ main.py tests/
ruff format --check src/ main.py tests/
mypy src/ main.py tests/ --strict
pytest tests/ -v
```

### Run All Tests

```bash
pytest tests/ -v --cov=src --cov-report=term-missing
```

### Project Structure

See `PLAN.md` for the full development plan and phase breakdown.

---

## License

This project is a work in progress.  All rights reserved.

---

## Credits

Built with Pygame-CE.  Lore and design inspired by the tactical command
terminal aesthetic of BattleTech and similar military sci-fi universes.
