"""Grid layout templates — named battlefield configurations.

Each layout defines a distinct combat terrain with unique strategic
properties.  Layouts are selected by floor range and mission type.
"""

from __future__ import annotations

from dataclasses import dataclass

from src.models.grid import GridCell, TerrainType

# ---------------------------------------------------------------------------
# Layout templates — each is a 12x10 grid described as a list of strings.
#
# Legend:
#   ' ' = OPEN        '.' = COVER
#   '#' = WALL        '^' = HIGH_GROUND
#   '~' = WATER
# ---------------------------------------------------------------------------

_LAYOUT_MAP: dict[str, list[str]] = {}


def _register(name: str, rows: list[str]) -> None:
    _LAYOUT_MAP[name] = rows


# 1. OPEN PLAINS — minimal cover, long sight lines
_register(
    "open_plains",
    [
        "            ",
        "   ^^^^     ",
        "            ",
        "  .      .  ",
        "            ",
        "  .      .  ",
        "            ",
        "  .      .  ",
        "            ",
        "            ",
    ],
)

# 2. URBAN RUINS — scattered walls and cover, close-quarters
_register(
    "urban_ruins",
    [
        "  .  .  .   ",
        "  ##  .  ## ",
        "  ##  .  ## ",
        "  .   .   . ",
        " .  ##  .   ",
        " .  ##  .   ",
        "  .   .   . ",
        "  ##  .  ## ",
        "  ##  .  ## ",
        "  .  .  .   ",
    ],
)

# 3. CANYON PASS — narrow corridor, ambush potential
_register(
    "canyon_pass",
    [
        " #       #  ",
        " #       #  ",
        " #  . .  #  ",
        " #  . .  #  ",
        "    . .     ",
        "    . .     ",
        " #  . .  #  ",
        " #  . .  #  ",
        " #       #  ",
        " #       #  ",
    ],
)

# 4. FLOODED BASIN — water hazards force channeled movement
_register(
    "flooded_basin",
    [
        "   .  .     ",
        "  ~~~~  .   ",
        "  ~  ~  .   ",
        "  ~  ~  .   ",
        " . ~~ ~~ .  ",
        " . ~~ ~~ .  ",
        "  .  ~  ~   ",
        "  .  ~  ~   ",
        "  .  ~~~~   ",
        "     .  .   ",
    ],
)

# 5. FORTIFIED COMPOUND — walls creating kill zones
_register(
    "fortified_compound",
    [
        " ##  ..  ## ",
        " ##  ..  ## ",
        "  .  ##  .  ",
        "  .  ##  .  ",
        " ..      .. ",
        " ..      .. ",
        "  .  ##  .  ",
        "  .  ##  .  ",
        " ##  ..  ## ",
        " ##  ..  ## ",
    ],
)

# 6. RIDGE LINE — high ground advantage positions
_register(
    "ridge_line",
    [
        " ^^^^^^^^^^ ",
        " ^  .  .  ^ ",
        "            ",
        "  .  ..  .  ",
        "            ",
        "            ",
        "  .  ..  .  ",
        "            ",
        " ^  .  .  ^ ",
        " ^^^^^^^^^^ ",
    ],
)

# 7. BRIDGE CROSSING — choke point over water
_register(
    "bridge_crossing",
    [
        "~~~~~~~~~~~ ",
        "~~   ..   ~~",
        "~~   ..   ~~",
        "~~~~~~~~~~~ ",
        "~~~~~~~~~~~ ",
        "~~~~~~~~~~~ ",
        "~~   ..   ~~",
        "~~   ..   ~~",
        "~~~~~~~~~~~ ",
        "~~~~~~~~~~~ ",
    ],
)

# 8. CRATER FIELD — scattered cover and high ground
_register(
    "crater_field",
    [
        "  . ^ .  ^  ",
        " ^   .   .  ",
        "  .  .  .   ",
        " .  ^  .  . ",
        "  .  .  ^ . ",
        " .  .  .  . ",
        "  ^ .  .  ^ ",
        " .  .  ^ .  ",
        "  . ^ .  .  ",
        " ^  .  . ^  ",
    ],
)

# 9. COMMAND BUNKER — tight corridors, boss arena
_register(
    "command_bunker",
    [
        " ########## ",
        " # .    . # ",
        " # .    . # ",
        " #  ####  # ",
        " #  #  #  # ",
        " #  #  #  # ",
        " #  ####  # ",
        " # .    . # ",
        " # .    . # ",
        " ########## ",
    ],
)

# 10. ASSAULT LANDING — open approach with scattered cover
_register(
    "assault_landing",
    [
        "            ",
        "  .  .  .   ",
        "            ",
        " .  ##  .   ",
        " .  ##  .   ",
        "            ",
        "  .  .  .   ",
        "            ",
        "  .  .  .   ",
        "            ",
    ],
)

# 11. TRENCH NETWORK — connected cover lines
_register(
    "trench_network",
    [
        "  . . . . . ",
        "  . . . . . ",
        "            ",
        "  . . . . . ",
        "  . . . . . ",
        "            ",
        "  . . . . . ",
        "  . . . . . ",
        "            ",
        "            ",
    ],
)

# 12. FINAL STAND — circular arena, boss fight
_register(
    "final_stand",
    [
        " # # # # # #",
        " #  .  .  # ",
        "#  . .. .  #",
        "#  .    .  #",
        "#  .    .  #",
        "#  .    .  #",
        "#  . .. .  #",
        " #  .  .  # ",
        " #  .  .  # ",
        " # # # # # #",
    ],
)


# ---------------------------------------------------------------------------
# Layout registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GridLayout:
    """A named battlefield terrain configuration.

    Attributes:
        name: Unique layout identifier (e.g. ``"urban_ruins"``).
        rows: 12-column, 10-row ASCII map using the terrain legend.
        width: Map width in cells (always 12).
        height: Map height in cells (always 10).
    """

    name: str
    rows: list[str]
    width: int = 12
    height: int = 10

    def validate(self) -> None:
        """Raise ``ValueError`` if the layout is malformed.

        Checks:
        - Exactly *height* rows.
        - Each row exactly *width* characters.
        - Only valid terrain characters.
        """
        valid_chars = set(" .#^~")
        if len(self.rows) != self.height:
            raise ValueError(
                f"Layout '{self.name}': expected {self.height} rows, got {len(self.rows)}"
            )
        for r, row in enumerate(self.rows):
            if len(row) != self.width:
                raise ValueError(
                    f"Layout '{self.name}' row {r}: expected {self.width} chars, got {len(row)}"
                )
            for c, ch in enumerate(row):
                if ch not in valid_chars:
                    raise ValueError(f"Layout '{self.name}' ({c},{r}): invalid character {ch!r}")

    def build_grid(self) -> src.models.grid.CombatGrid:
        """Construct a :class:`CombatGrid` from this layout.

        Returns:
            A fully validated 12x10 CombatGrid with terrain populated.
        """
        from src.models.grid import CombatGrid

        self.validate()
        char_to_terrain: dict[str, TerrainType] = {
            " ": TerrainType.OPEN,
            ".": TerrainType.COVER,
            "#": TerrainType.WALL,
            "^": TerrainType.HIGH_GROUND,
            "~": TerrainType.WATER,
        }
        cells: list[list[GridCell]] = []
        for r, row in enumerate(self.rows):
            cell_row: list[GridCell] = []
            for c, ch in enumerate(row):
                cell_row.append(GridCell(col=c, row=r, terrain=char_to_terrain[ch]))
            cells.append(cell_row)
        return CombatGrid(width=self.width, height=self.height, cells=cells)


# Build registry of all layouts
ALL_LAYOUTS: dict[str, GridLayout] = {}
for _lname, _lrows in _LAYOUT_MAP.items():
    _layout = GridLayout(name=_lname, rows=_lrows)
    _layout.validate()
    ALL_LAYOUTS[_layout.name] = _layout


# ---------------------------------------------------------------------------
# Layout selection by floor range and mission context
# ---------------------------------------------------------------------------

# Floor range → list of possible layout names.
_FLOOR_LAYOUTS: dict[tuple[int, int], list[str]] = {
    (1, 5): [
        "open_plains",
        "urban_ruins",
        "canyon_pass",
        "assault_landing",
    ],
    (6, 10): [
        "flooded_basin",
        "fortified_compound",
        "ridge_line",
        "trench_network",
        "crater_field",
    ],
    (11, 15): [
        "canyon_pass",
        "fortified_compound",
        "bridge_crossing",
        "crater_field",
        "trench_network",
    ],
    (16, 20): [
        "urban_ruins",
        "ridge_line",
        "bridge_crossing",
        "fortified_compound",
        "crater_field",
    ],
    (21, 25): [
        "command_bunker",
        "final_stand",
        "fortified_compound",
        "ridge_line",
    ],
}

# Special layouts for boss / elite encounters
_BOSS_LAYOUTS = ["command_bunker", "final_stand"]
_ELITE_LAYOUTS = ["fortified_compound", "ridge_line", "canyon_pass"]


def get_layouts_for_floor(
    floor_num: int, is_boss: bool = False, is_elite: bool = False
) -> list[str]:
    """Return possible grid layout names for a given floor.

    Args:
        floor_num: Current floor (1-25).
        is_boss: If True, return boss-specific layouts.
        is_elite: If True, return elite layouts.

    Returns:
        List of layout name strings.
    """
    if is_boss:
        return list(_BOSS_LAYOUTS)
    if is_elite:
        return list(_ELITE_LAYOUTS)
    for (lo, hi), layouts in _FLOOR_LAYOUTS.items():
        if lo <= floor_num <= hi:
            return list(layouts)
    return ["open_plains"]


def get_random_layout(floor_num: int, is_boss: bool = False, is_elite: bool = False) -> GridLayout:
    """Pick a random layout appropriate for the given floor.

    Args:
        floor_num: Current floor (1-25).
        is_boss: Boss encounter flag.
        is_elite: Elite encounter flag.

    Returns:
        A randomly selected GridLayout.
    """
    import random

    options = get_layouts_for_floor(floor_num, is_boss, is_elite)
    name = random.choice(options)
    return ALL_LAYOUTS[name]


# Avoid circular import at module level.
import src.models.grid  # noqa: E402
