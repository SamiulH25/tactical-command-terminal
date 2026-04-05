"""Grid and terrain definitions for the tactical combat map.

The combat grid is a rectangular array of cells.  Each cell has a terrain
type that affects movement cost, cover bonus, and line of sight.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TerrainType(Enum):
    """Terrain classification for a grid cell."""

    OPEN = auto()  #: No cover, normal movement
    COVER = auto()  #: Partial cover, normal movement
    WALL = auto()  #: Impassable solid obstacle
    HIGH_GROUND = auto()  #: Elevated terrain, movement cost +1
    WATER = auto()  #: Difficult terrain, movement cost +2


@dataclass(frozen=True)
class GridCell:
    """A single tile on the combat grid.

    Invariants:
    - Coordinates are non-negative.
    - ``terrain`` is a valid ``TerrainType``.
    """

    col: int
    """Column index (0-based, left to right)."""

    row: int
    """Row index (0-based, top to bottom)."""

    terrain: TerrainType = TerrainType.OPEN
    """Terrain type of this cell."""

    @property
    def is_passable(self) -> bool:
        """Whether a mech can move into this cell."""
        return self.terrain != TerrainType.WALL

    @property
    def movement_cost(self) -> int:
        """Action points required to move into this cell.

        Returns:
            1 for open/cover, 2 for high ground, 3 for water,
            ``-1`` for walls (impassable).
        """
        costs: dict[TerrainType, int] = {
            TerrainType.OPEN: 1,
            TerrainType.COVER: 1,
            TerrainType.WALL: -1,
            TerrainType.HIGH_GROUND: 2,
            TerrainType.WATER: 3,
        }
        return costs[self.terrain]

    @property
    def cover_bonus(self) -> int:
        """Evasion bonus from terrain cover.

        Returns:
            10 for cover cells, 0 otherwise.
        """
        if self.terrain == TerrainType.COVER:
            return 10
        return 0

    @property
    def symbol(self) -> str:
        """ASCII symbol used for the terminal display."""
        symbols: dict[TerrainType, str] = {
            TerrainType.OPEN: " ",
            TerrainType.COVER: "\u2591",  # ░
            TerrainType.WALL: "\u2588",  # █
            TerrainType.HIGH_GROUND: "\u25b2",  # ▲
            TerrainType.WATER: "~",
        }
        return symbols[self.terrain]

    def validate(self) -> None:
        """Raise ``ValueError`` if coordinates are invalid.

        Raises:
            ValueError: If ``col`` or ``row`` is negative.
        """
        if self.col < 0:
            raise ValueError(f"col {self.col} must be >= 0")
        if self.row < 0:
            raise ValueError(f"row {self.row} must be >= 0")


@dataclass
class CombatGrid:
    """A rectangular grid of cells representing the battlefield.

    The grid is indexed as ``grid[row][col]`` (row-major).
    """

    width: int
    """Number of columns."""

    height: int
    """Number of rows."""

    cells: list[list[GridCell]]
    """2D array of cells: ``cells[row][col]``."""

    def __post_init__(self) -> None:
        """Validate grid dimensions and cell integrity."""
        self.validate()

    def get_cell(self, col: int, row: int) -> GridCell:
        """Return the cell at the given coordinates.

        Args:
            col: Column index.
            row: Row index.

        Returns:
            The cell at ``(col, row)``.

        Raises:
            IndexError: If coordinates are out of bounds.
        """
        if not (0 <= col < self.width):
            raise IndexError(f"col {col} out of range [0, {self.width})")
        if not (0 <= row < self.height):
            raise IndexError(f"row {row} out of range [0, {self.height})")
        return self.cells[row][col]

    def is_valid(self, col: int, row: int) -> bool:
        """Check whether coordinates are within the grid bounds."""
        return 0 <= col < self.width and 0 <= row < self.height

    def validate(self) -> None:
        """Raise ``ValueError`` if the grid structure is invalid.

        Raises:
            ValueError: If dimensions are non-positive, row lengths are
                inconsistent, or cell coordinates don't match their position.
        """
        if self.width <= 0:
            raise ValueError(f"width {self.width} must be > 0")
        if self.height <= 0:
            raise ValueError(f"height {self.height} must be > 0")
        if len(self.cells) != self.height:
            raise ValueError(f"Expected {self.height} rows, got {len(self.cells)}")
        for r, row_data in enumerate(self.cells):
            if len(row_data) != self.width:
                raise ValueError(f"Row {r} has {len(row_data)} cols, expected {self.width}")
            for c, cell in enumerate(row_data):
                if cell.col != c or cell.row != r:
                    raise ValueError(
                        f"Cell at [{r}][{c}] has mismatched coords ({cell.col}, {cell.row})"
                    )
