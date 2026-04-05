"""Proportional layout helpers.

All UI positioning uses a base resolution of 1920x1080.  The ``s()``
function scales raw coordinates to the actual display size, keeping
everything proportional regardless of resolution.

Usage::

    from src.ui.layout import s

    # Scale a single value (width or x position)
    x = s(80)          # 80px at 1920 width → scaled to current width

    # Scale a rect (x, y, w, h)
    rx, ry, rw, rh = s(30, 60, 400, 200)

    # Scale only position, keep natural height
    rx, ry = s(70, 110)
"""

from __future__ import annotations

import pygame

# Base resolution — all coordinates are defined against this
_BASE_W: int = 1920
_BASE_H: int = 1080

# Cached scale factors — updated when display is queried
_sx: float = 1.0
_sy: float = 1.0


def _refresh_scale(display: pygame.Surface) -> None:
    """Update cached scale factors from the current display surface."""
    global _sx, _sy
    w, h = display.get_size()
    _sx = w / _BASE_W
    _sy = h / _BASE_H


def s(
    x: int,
    y: int,
    w: int | None = None,
    h: int | None = None,
    display: pygame.Surface | None = None,
) -> tuple[int, ...]:
    """Scale coordinates proportionally from the 1920x1080 base.

    Args:
        x: Horizontal position in base pixels.
        y: Vertical position in base pixels.
        w: Optional width in base pixels (scaled on X axis).
        h: Optional height in base pixels (scaled on Y axis).
        display: Optional display surface to read size from.
            If ``None``, uses the cached scale factors (refresh
            with :func:`refresh` first).

    Returns:
        Scaled ``(x, y)`` or ``(x, y, w, h)`` as integers.
    """
    if display is not None:
        _refresh_scale(display)

    rx = int(x * _sx)
    ry = int(y * _sy)
    if w is not None and h is not None:
        return (rx, ry, int(w * _sx), int(h * _sy))
    return (rx, ry)


def refresh(display: pygame.Surface) -> None:
    """Refresh the cached scale factors.

    Call this once at the start of each ``render()`` or ``on_enter()``
    to ensure scaling is correct for the current display size.
    """
    _refresh_scale(display)


def sx(value: int) -> int:
    """Scale a horizontal value only.

    Args:
        value: Pixel value at 1920px width.

    Returns:
        Scaled value for the current display width.
    """
    return int(value * _sx)


def sy(value: int) -> int:
    """Scale a vertical value only.

    Args:
        value: Pixel value at 1080px height.

    Returns:
        Scaled value for the current display height.
    """
    return int(value * _sy)
