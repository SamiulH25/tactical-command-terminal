"""Combat grid view — renders the tactical grid with terrain markers and units.

The grid is displayed as the Coordinator sees it through the degraded
telemetry feed: faint scanline borders, ASCII terrain symbols, and
geometric IFF shapes for units.

Terrain markers (per lore)::

    █  wall
    ░  cover
    ▲  high ground
    ~  water
"""

from __future__ import annotations

import pygame

from src import config
from src.models.faction import FACTION_COLOUR
from src.models.grid import CombatGrid, GridCell, TerrainType
from src.models.mech import DeployedMech

# Minimum cell size for readability
_MIN_CELL = 32


class GridView:
    """A renderable view of a :class:`CombatGrid` with unit overlays.

    The view automatically scales cells to fit the allocated rect while
    maintaining integer pixel boundaries.
    """

    def __init__(
        self,
        x: int,
        y: int,
        width: int,
        height: int,
        grid: CombatGrid,
    ) -> None:
        """Create a GridView.

        Args:
            x: Left edge in pixels.
            y: Top edge in pixels.
            width: View width in pixels.
            height: View height in pixels.
            grid: The combat grid to display.
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.grid = grid
        self._cell_w = max(_MIN_CELL, width // grid.width)
        self._cell_h = max(_MIN_CELL, height // grid.height)
        # Actual grid pixel size
        self._grid_w = self._cell_w * grid.width
        self._grid_h = self._cell_h * grid.height
        # Offset to centre the grid in the view
        self._offset_x = x + (width - self._grid_w) // 2
        self._offset_y = y + (height - self._grid_h) // 2

        # Unit position map: (col, row) → (DeployedMech, friendly)
        self._units: dict[tuple[int, int], tuple[DeployedMech, bool]] = {}

    # ------------------------------------------------------------------
    # Unit management
    # ------------------------------------------------------------------

    def place_unit(self, col: int, row: int, mech: DeployedMech, friendly: bool = True) -> None:
        """Place a mech on the grid at the given coordinates.

        Args:
            col: Grid column.
            row: Grid row.
            mech: The mech to place.
            friendly: ``True`` for allies, ``False`` for hostiles.
        """
        self._units[(col, row)] = (mech, friendly)

    def clear_units(self) -> None:
        """Remove all unit placements."""
        self._units.clear()

    def remove_unit(self, col: int, row: int) -> None:
        """Remove a unit at the given coordinates."""
        self._units.pop((col, row), None)

    # ------------------------------------------------------------------
    # Coordinate helpers
    # ------------------------------------------------------------------

    def cell_rect(self, col: int, row: int) -> pygame.Rect:
        """Return the pixel rect for a grid cell."""
        return pygame.Rect(
            self._offset_x + col * self._cell_w,
            self._offset_y + row * self._cell_h,
            self._cell_w,
            self._cell_h,
        )

    def pixel_to_cell(self, px: int, py: int) -> tuple[int, int] | None:
        """Convert a pixel position to grid coordinates.

        Returns:
            ``(col, row)`` tuple or ``None`` if outside the grid.
        """
        col = (px - self._offset_x) // self._cell_w
        row = (py - self._offset_y) // self._cell_h
        if self.grid.is_valid(col, row):
            return (col, row)
        return None

    # ------------------------------------------------------------------
    # Rendering — terrain
    # ------------------------------------------------------------------

    @staticmethod
    def _terrain_colour(terrain: TerrainType) -> tuple[int, int, int]:
        """Return the display colour for a terrain type.

        Colours are chosen to be clearly distinguishable on the dark
        CRT terminal background while maintaining the green-phosphor
        aesthetic.  Each terrain has a distinct visual identity:

        - OPEN: near-black empty space
        - COVER: muted green with visible shade (foliage/debris)
        - WALL: neutral gray solid obstruction
        - HIGH_GROUND: amber-tinted elevation
        - WATER: deep blue tint (visible only by shade difference)
        """
        colours: dict[TerrainType, tuple[int, int, int]] = {
            TerrainType.OPEN: (5, 8, 3),
            TerrainType.COVER: (12, 35, 10),
            TerrainType.WALL: (45, 45, 45),
            TerrainType.HIGH_GROUND: (22, 30, 10),
            TerrainType.WATER: (6, 14, 30),
        }
        return colours.get(terrain, config.COLOR_BG)

    @staticmethod
    def _terrain_symbol(terrain: TerrainType) -> str:
        """Return the ASCII/Unicode marker for terrain."""
        symbols: dict[TerrainType, str] = {
            TerrainType.OPEN: " ",
            TerrainType.COVER: "\u2591",  # ░
            TerrainType.WALL: "\u2588",  # █
            TerrainType.HIGH_GROUND: "\u25b2",  # ▲
            TerrainType.WATER: "~",
        }
        return symbols[terrain]

    def _draw_cell(
        self,
        surface: pygame.Surface,
        cell: GridCell,
        font: pygame.font.Font,
        highlight: bool = False,
    ) -> None:
        """Render a single grid cell."""
        crect = self.cell_rect(cell.col, cell.row)

        # Background
        base_colour = self._terrain_colour(cell.terrain)
        if highlight:
            colour: tuple[int, int, int] = tuple(min(255, c + 15) for c in base_colour)  # type: ignore[assignment]
        else:
            colour = base_colour
        pygame.draw.rect(surface, colour, crect)

        # Border — faint scanline
        border_col = (20, 40, 16)
        pygame.draw.rect(surface, border_col, crect, 1)

        # Terrain symbol
        sym = self._terrain_symbol(cell.terrain)
        if sym.strip():
            sym_surf = font.render(sym, True, config.PHOSPHOR_DIM)
            sx = crect.left + (crect.width - sym_surf.get_width()) // 2
            sy = crect.top + (crect.height - sym_surf.get_height()) // 2
            surface.blit(sym_surf, (sx, sy))

    # ------------------------------------------------------------------
    # Rendering — IFF symbols for units
    # ------------------------------------------------------------------

    @staticmethod
    def _iff_shape_symbol(shape_name: str) -> str:
        """Return a single-character IFF symbol for a mech shape."""
        symbols: dict[str, str] = {
            "SQUARE": "\u25c8",  # ◇
            "DIAMOND": "\u25c6",  # ◆
            "HEXAGON": "\u2b22",  # ⬢
            "CIRCLE_CROSS": "\u25c9",  # ◉
            "CHEVRON": "\u27e9",  # ⟩
            "TRIANGLE": "\u25b2",  # ▲
            "RECTANGLE": "\u25ac",  # ▬
            "CIRCLE": "\u25cf",  # ●
            "CROSS": "\u271b",  # ✛
        }
        return symbols.get(shape_name, "\u25c6")

    def _draw_unit(
        self,
        surface: pygame.Surface,
        mech: DeployedMech,
        friendly: bool,
        crect: pygame.Rect,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
    ) -> None:
        """Render a mech's IFF symbol and callsign on a cell."""
        # IFF symbol
        sym = self._iff_shape_symbol(mech.frame.iff_shape.name)
        if friendly:
            sym_col = FACTION_COLOUR.get(mech.frame.faction, config.PHOSPHOR_GREEN)
        else:
            sym_col = config.COLOR_ENEMY
        sym_surf = font.render(sym, True, sym_col)
        sx = crect.left + (crect.width - sym_surf.get_width()) // 2
        sy = crect.top + max(0, crect.height // 2 - sym_surf.get_height())
        surface.blit(sym_surf, (sx, sy))

        # Callsign tag
        tag = (
            mech.pilot_callsign.split("-")[0] if "-" in mech.pilot_callsign else mech.pilot_callsign
        )
        tag_surf = small_font.render(tag, True, sym_col)
        tx = crect.left + (crect.width - tag_surf.get_width()) // 2
        ty = sy + sym_surf.get_height() - 2
        surface.blit(tag_surf, (tx, ty))

    # ------------------------------------------------------------------
    # Main render
    # ------------------------------------------------------------------

    def render(
        self,
        surface: pygame.Surface,
        font: pygame.font.Font,
        small_font: pygame.font.Font,
        highlight_cell: tuple[int, int] | None = None,
    ) -> None:
        """Draw the full grid with terrain and all placed units.

        Args:
            surface: Target surface.
            font: Font for IFF symbols.
            small_font: Font for terrain markers and callsign tags.
            highlight_cell: Optional ``(col, row)`` to highlight.
        """
        for row in range(self.grid.height):
            for col in range(self.grid.width):
                cell = self.grid.get_cell(col, row)
                hl = highlight_cell == (col, row)
                self._draw_cell(surface, cell, small_font, highlight=hl)

                # Unit overlay
                if (col, row) in self._units:
                    mech, friendly = self._units[(col, row)]
                    crect = self.cell_rect(col, row)
                    self._draw_unit(surface, mech, friendly, crect, font, small_font)
