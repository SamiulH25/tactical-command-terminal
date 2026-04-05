"""Terminal text helpers — formatting utilities for the CRT aesthetic.

Every piece of text in the game must follow the lore-accurate terminal
style: zero-padded numbers, bracketed status tags, ``>`` prefix on
headers, and ASCII dividers.  This module centralises those rules.
"""

from __future__ import annotations

# Block characters for HP/OL bars
BLOCK_FULL: str = "\u2588"  # █
BLOCK_HALF: str = "\u2593"  # ▓
BLOCK_EMPTY: str = "\u2591"  # ░

# Divider characters
THIN_DIVIDER: str = "\u2500"  # ─
THICK_DIVIDER: str = "\u2550"  # ═

# Status tag constants
TAG_ACTIVE: str = "[ACTIVE]"
TAG_STANDBY: str = "[STANDBY]"
TAG_OFFLINE: str = "[OFFLINE]"
TAG_CRITICAL: str = "[CRITICAL]"
TAG_ENGAGED: str = "[ENGAGED]"
TAG_LOCKED: str = "[LOCKED]"


def pad(value: int | float, width: int = 3) -> str:
    """Zero-pad a number to fixed width.

    Lore: ``028/030``, ``004/010``, ``0150``

    Args:
        value: The number to format.
        width: Minimum character width (padded with leading zeros).

    Returns:
        Zero-padded string.
    """
    return f"{int(value):0{width}d}"


def ratio_bar(
    current: int,
    maximum: int,
    bar_width: int = 20,
) -> str:
    """Build a block-character progress bar string.

    Example: ``████████████████░░░░``  (16/20 filled)

    Args:
        current: Current value.
        maximum: Maximum value.
        bar_width: Number of block characters.

    Returns:
        String of block characters showing fill ratio.
    """
    if maximum <= 0:
        return BLOCK_EMPTY * bar_width
    current = max(0, min(current, maximum))
    filled = round(current / maximum * bar_width)
    return BLOCK_FULL * filled + BLOCK_EMPTY * (bar_width - filled)


def status_tag(current: int, maximum: int) -> str:
    """Return a status tag based on a value's ratio to its max.

    - Ratio > 0.5 → ``[ACTIVE]``
    - Ratio > 0.25 → ``[STANDBY]``
    - Ratio > 0 → ``[CRITICAL]``
    - Ratio == 0 → ``[OFFLINE]``

    Args:
        current: Current value.
        maximum: Maximum value.
    """
    if maximum <= 0:
        return TAG_OFFLINE
    ratio = current / maximum
    if ratio > 0.5:
        return TAG_ACTIVE
    if ratio > 0.25:
        return TAG_STANDBY
    if ratio > 0:
        return TAG_CRITICAL
    return TAG_OFFLINE


def divider(length: int = 30, thick: bool = False) -> str:
    """Return a horizontal divider line.

    Args:
        length: Number of characters.
        thick: Use ``═`` instead of ``─``.
    """
    char = THICK_DIVIDER if thick else THIN_DIVIDER
    return char * length


def header(text: str, width: int = 40) -> str:
    """Format a header line with ``>`` prefix.

    Example: ``> UNIT STATUS─────────────────``

    Args:
        text: The header label (without ``>``).
        width: Total line width including prefix and filler.
    """
    prefix = f"> {text}"
    remaining = max(0, width - len(prefix))
    return prefix + THIN_DIVIDER * remaining


def coord(col: int, row: int) -> str:
    """Format grid coordinates in lore-accurate notation.

    Example: ``GRID 14,07``

    Args:
        col: Column index.
        row: Row index.
    """
    return f"GRID {pad(col, 2)},{pad(row, 2)}"
