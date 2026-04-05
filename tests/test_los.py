"""Tests for the Line of Sight system."""

import pytest

from src.models.grid import CombatGrid, GridCell, TerrainType
from src.systems.los import (
    bresenham_cells,
    cells_in_range,
    grid_distance,
    has_los,
    visible_enemies,
)


class TestBresenhamCells:
    """Verify Bresenham raycasting."""

    def test_horizontal_line(self) -> None:
        """Horizontal line should return all intermediate cells."""
        cells = bresenham_cells(0, 0, 5, 0)
        assert cells == [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]

    def test_vertical_line(self) -> None:
        """Vertical line should return all intermediate cells."""
        cells = bresenham_cells(0, 0, 0, 4)
        assert cells == [(0, 0), (0, 1), (0, 2), (0, 3), (0, 4)]

    def test_diagonal_line(self) -> None:
        """Diagonal line should step through cells."""
        cells = bresenham_cells(0, 0, 3, 3)
        assert len(cells) == 4  # (0,0) through (3,3)
        assert cells[0] == (0, 0)
        assert cells[-1] == (3, 3)

    def test_same_cell(self) -> None:
        """Same start and end should return single cell."""
        cells = bresenham_cells(5, 5, 5, 5)
        assert cells == [(5, 5)]


class TestLOS:
    """Verify line of sight computation."""

    def _make_grid(self) -> CombatGrid:
        """10x10 grid with a wall at column 5, rows 0-9."""
        cells = [
            [
                GridCell(col=c, row=r, terrain=TerrainType.WALL if c == 5 else TerrainType.OPEN)
                for c in range(10)
            ]
            for r in range(10)
        ]
        return CombatGrid(width=10, height=10, cells=cells)

    def test_los_clear_path(self) -> None:
        """No wall between source and target should give LOS."""
        grid = self._make_grid()
        assert has_los(grid, 0, 0, 4, 0) is True

    def test_los_blocked_by_wall(self) -> None:
        """Wall in the middle of the path should block LOS."""
        grid = self._make_grid()
        assert has_los(grid, 0, 0, 9, 0) is False

    def test_los_same_side_of_wall(self) -> None:
        """Both cells on same side of wall should have LOS."""
        grid = self._make_grid()
        assert has_los(grid, 6, 0, 9, 0) is True

    def test_los_invalid_from(self) -> None:
        """Out-of-bounds origin should return False."""
        grid = self._make_grid()
        assert has_los(grid, -1, 0, 5, 0) is False

    def test_los_invalid_to(self) -> None:
        """Out-of-bounds target should return False."""
        grid = self._make_grid()
        assert has_los(grid, 0, 0, 15, 0) is False

    def test_los_cover_not_block(self) -> None:
        """Cover terrain should NOT block LOS."""
        cells = [
            [
                GridCell(col=c, row=0, terrain=TerrainType.COVER if c == 3 else TerrainType.OPEN)
                for c in range(6)
            ]
        ]
        grid = CombatGrid(width=6, height=1, cells=cells)
        assert has_los(grid, 0, 0, 5, 0) is True


class TestGridDistance:
    """Verify distance computation."""

    def test_same_cell(self) -> None:
        """Distance to self should be zero."""
        assert grid_distance(5, 5, 5, 5) == pytest.approx(0.0)

    def test_adjacent(self) -> None:
        """Adjacent cells should have distance 1."""
        assert grid_distance(0, 0, 1, 0) == pytest.approx(1.0)

    def test_diagonal(self) -> None:
        """Diagonal should be sqrt(2)."""
        assert grid_distance(0, 0, 1, 1) == pytest.approx(2.0**0.5)


class TestCellsInRange:
    """Verify range computation."""

    def _make_grid(self) -> CombatGrid:
        cells = [[GridCell(col=c, row=r) for c in range(10)] for r in range(10)]
        return CombatGrid(width=10, height=10, cells=cells)

    def test_range_one(self) -> None:
        """Range 1 should return 8 surrounding cells."""
        grid = self._make_grid()
        result = cells_in_range(grid, 5, 5, 1)
        assert len(result) == 8  # 3x3 minus centre

    def test_range_two(self) -> None:
        """Range 2 should return 24 cells."""
        grid = self._make_grid()
        result = cells_in_range(grid, 5, 5, 2)
        assert len(result) == 24  # 5x5 minus centre

    def test_range_clipped_at_edge(self) -> None:
        """Range near edge should only include valid cells."""
        grid = self._make_grid()
        result = cells_in_range(grid, 0, 0, 2)
        for col, row in result:
            assert 0 <= col < 10
            assert 0 <= row < 10

    def test_range_excludes_origin(self) -> None:
        """Origin cell should not be in the result."""
        grid = self._make_grid()
        result = cells_in_range(grid, 5, 5, 3)
        assert (5, 5) not in result


class TestVisibleEnemies:
    """Verify enemy visibility through LOS."""

    def _make_grid(self) -> CombatGrid:
        cells = [[GridCell(col=c, row=r) for c in range(10)] for r in range(10)]
        return CombatGrid(width=10, height=10, cells=cells)

    def test_all_visible_no_walls(self) -> None:
        """On open grid, all enemies should be visible."""
        grid = self._make_grid()
        friendlies = [(5, 5)]
        enemies = [(0, 0), (9, 0), (0, 9), (9, 9)]
        visible = visible_enemies(grid, enemies, friendlies)
        assert visible == set(enemies)

    def test_none_visible_when_blocked(self) -> None:
        """If all friendlies are surrounded by walls, no enemies visible."""
        # Place friendlies and enemies such that walls block all LOS
        cells = [
            [
                GridCell(col=c, row=r, terrain=TerrainType.WALL if c == 5 else TerrainType.OPEN)
                for c in range(10)
            ]
            for r in range(10)
        ]
        grid = CombatGrid(width=10, height=10, cells=cells)
        friendlies = [(2, 5)]
        enemies = [(8, 5)]
        visible = visible_enemies(grid, enemies, friendlies)
        assert visible == set()

    def test_partial_visibility(self) -> None:
        """Some enemies may be visible while others are not."""
        grid = self._make_grid()
        friendlies = [(5, 5)]
        enemies = [(5, 4), (5, 6), (9, 9)]
        visible = visible_enemies(grid, enemies, friendlies)
        assert len(visible) >= 2  # At least the close ones
