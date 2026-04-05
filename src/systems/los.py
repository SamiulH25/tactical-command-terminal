"""Line of Sight system — visibility computation on the tactical grid.

The Coordinator's telemetry feed only reveals hostiles within LOS of at
least one friendly mech.  Walls and high-ground terrain block LOS.
The implementation uses a standard Bresenham raycaster adapted for
grid-based terrain blocking.

Lore rationale:  Signal degradation and bandwidth constraints mean your
display can only show units that are actively transmitting IFF data
within line of sight of your sensors.  Walls, bunkers, and elevation
interrupt the telemetry feed.
"""

from __future__ import annotations

import math

from src.models.grid import CombatGrid, TerrainType


def _lerp_int(a: int, b: int, t: float) -> int:
    """Linear interpolation between two integers at fraction *t*."""
    return a + round((b - a) * t)


def bresenham_cells(col0: int, row0: int, col1: int, row1: int) -> list[tuple[int, int]]:
    """Return all cells intersected by a line from (col0,row0) to (col1,row1).

    Uses Bresenham's algorithm adapted to return every cell the line
    passes through, including the start and end cells.

    Args:
        col0: Starting column.
        row0: Starting row.
        col1: Ending column.
        row1: Ending row.

    Returns:
        Ordered list of ``(col, row)`` tuples from start to end.
    """
    cells: list[tuple[int, int]] = []
    dc = abs(col1 - col0)
    dr = abs(row1 - row0)
    sc = 1 if col0 < col1 else -1
    sr = 1 if row0 < row1 else -1
    err = dc - dr
    c, r = col0, row0

    while True:
        cells.append((c, r))
        if c == col1 and r == row1:
            break
        e2 = 2 * err
        if e2 > -dr:
            err -= dr
            c += sc
        if e2 < dc:
            err += dc
            r += sr
    return cells


def has_los(
    grid: CombatGrid,
    from_col: int,
    from_row: int,
    to_col: int,
    to_row: int,
) -> bool:
    """Check whether there is an unblocked line of sight between two cells.

    LOS is blocked by **WALL** terrain.  The origin and destination
    cells themselves are not checked (a unit can see into/through a wall
    cell if it is standing on one).

    Args:
        grid: The combat grid.
        from_col: Origin column.
        from_row: Origin row.
        to_col: Target column.
        to_row: Target row.

    Returns:
        ``True`` if no wall blocks the line between the two cells.
    """
    if not grid.is_valid(from_col, from_row) or not grid.is_valid(to_col, to_row):
        return False

    path = bresenham_cells(from_col, from_row, to_col, to_row)
    # Check intermediate cells only (exclude endpoints)
    for col, row in path[1:-1]:
        cell = grid.get_cell(col, row)
        if cell.terrain == TerrainType.WALL:
            return False
    return True


def grid_distance(col0: int, row0: int, col1: int, row1: int) -> float:
    """Euclidean distance in grid cells between two positions.

    Args:
        col0: First column.
        row0: First row.
        col1: Second column.
        row1: Second row.

    Returns:
        Euclidean distance as a float.
    """
    return math.sqrt((col1 - col0) ** 2 + (row1 - row0) ** 2)


def cells_in_range(
    grid: CombatGrid,
    from_col: int,
    from_row: int,
    max_range: int,
) -> list[tuple[int, int]]:
    """Return all cells within *max_range* grid cells (Chebyshev distance).

    This is the "square" range used by most directives.

    Args:
        grid: The combat grid.
        from_col: Origin column.
        from_row: Origin row.
        max_range: Maximum range in cells (inclusive).

    Returns:
        List of ``(col, row)`` tuples within range, excluding the origin.
    """
    result: list[tuple[int, int]] = []
    for dr in range(-max_range, max_range + 1):
        for dc in range(-max_range, max_range + 1):
            if dc == 0 and dr == 0:
                continue
            nc, nr = from_col + dc, from_row + dr
            if grid.is_valid(nc, nr):
                result.append((nc, nr))
    return result


def visible_enemies(
    grid: CombatGrid,
    enemy_positions: list[tuple[int, int]],
    friendly_positions: list[tuple[int, int]],
) -> set[tuple[int, int]]:
    """Return the set of enemy positions visible to at least one friendly.

    An enemy is visible if any friendly mech has an unblocked LOS to it.

    Args:
        grid: The combat grid.
        enemy_positions: List of ``(col, row)`` for all hostiles.
        friendly_positions: List of ``(col, row)`` for all friendlies.

    Returns:
        Set of visible enemy ``(col, row)`` tuples.
    """
    visible: set[tuple[int, int]] = set()
    for ec, er in enemy_positions:
        for fc, fr in friendly_positions:
            if has_los(grid, fc, fr, ec, er):
                visible.add((ec, er))
                break  # Visible to at least one friendly
    return visible
