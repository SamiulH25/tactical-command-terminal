"""Faction definitions and colour mappings.

All factions in the game are represented by this enum.  Each faction
has a canonical display colour used for IFF symbols and UI accents.
Colours are sourced from ``src.config`` to keep rendering data central.
"""

from __future__ import annotations

from enum import Enum, auto

import src.config as _cfg

RGB = tuple[int, int, int]


class Faction(Enum):
    """Canonical factions in the conflict."""

    FSA = auto()  #: Free Systems Alliance — player faction
    CRIMSON_COMPACT = auto()  #: CC — main enemy faction
    REBEL = auto()  #: Unaligned scavengers / third faction


# ---------------------------------------------------------------------------
# Colour look-up table — maps each faction to a display RGB tuple.
# ---------------------------------------------------------------------------

FACTION_COLOUR: dict[Faction, tuple[int, int, int]] = {
    Faction.FSA: _cfg.PHOSPHOR_GREEN,
    Faction.CRIMSON_COMPACT: _cfg.COLOR_ENEMY,
    Faction.REBEL: _cfg.COLOR_WARNING,
}


# ---------------------------------------------------------------------------
# IFF symbol shapes — geometric identifiers per mech class.
# ---------------------------------------------------------------------------


class IFFShape(Enum):
    """Geometric IFF transponder shapes drawn on the tactical display."""

    SQUARE = auto()  #: Bastion — wide rectangle
    DIAMOND = auto()  #: Raptor — diamond / triangle
    HEXAGON = auto()  #: Anvil — wide hexagon
    CIRCLE_CROSS = auto()  #: Warden — circle with cross
    CHEVRON = auto()  #: Wraith — narrow chevron
    TRIANGLE = auto()  #: CC Sentinel — inverted triangle
    RECTANGLE = auto()  #: CC Siege — tall rectangle
    CIRCLE = auto()  #: Generic circle (support mechs)
    CROSS = auto()  #: Cross / plus (utility)
