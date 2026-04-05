"""Encounter and floor definitions — the building blocks of the campaign.

An encounter is a single event the player faces: combat, narrative event,
merchant (supply depot), or rest (R&R).  A floor contains 1-5 encounters
arranged as a node map the player navigates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto


class EncounterType(Enum):
    """Kind of encounter."""

    COMBAT = auto()  #: Fight enemies on the grid
    EVENT = auto()  #: Narrative choice with consequences
    MERCHANT = auto()  #: Supply depot — buy directives / equipment
    REST = auto()  #: R&R — repair, heal, remove debuffs


@dataclass(frozen=True)
class EnemySpawn:
    """Defines an enemy mech to place on the grid.

    Invariants:
    - ``mech_id`` references a valid mech frame ID.
    - ``grid_col`` and ``grid_row`` are non-negative.
    """

    mech_id: str
    """ID of the enemy mech frame to spawn."""

    grid_col: int = 0
    """Starting column on the combat grid."""

    grid_row: int = 0
    """Starting row on the combat grid."""

    def validate(self) -> None:
        """Raise ``ValueError`` if fields are invalid."""
        if not self.mech_id:
            raise ValueError("EnemySpawn mech_id must be non-empty")
        if self.grid_col < 0:
            raise ValueError(f"grid_col {self.grid_col} must be >= 0")
        if self.grid_row < 0:
            raise ValueError(f"grid_row {self.grid_row} must be >= 0")


@dataclass(frozen=True)
class Encounter:
    """A single encounter the player can face.

    Invariants:
    - ``id`` is unique within the campaign data set.
    - Combat encounters have at least one enemy spawn.
    - Event encounters have at least one choice.
    """

    id: str
    """Unique encounter identifier."""

    encounter_type: EncounterType
    """Kind of encounter."""

    narrative_text: str = ""
    """Text displayed before the encounter begins."""

    enemies: list[EnemySpawn] = field(default_factory=list)
    """Enemy mechs to spawn (combat encounters only)."""

    choices: list[dict[str, str]] = field(default_factory=list)
    """Player choices for event encounters.  Each dict has
    ``{"text": "...", "outcome_id": "..."}``."""

    rewards: dict[str, int] = field(default_factory=dict)
    """Post-combat rewards: ``{"credits": 50, "card_pick": 1}``."""

    grid_layout: str = ""
    """Optional grid layout ID for combat encounters."""

    def validate(self) -> None:
        """Raise ``ValueError`` if the encounter is malformed.

        Raises:
            ValueError: If ``id`` is empty, combat encounters have no
                enemies, or event encounters have no choices.
        """
        if not self.id:
            raise ValueError("Encounter id must be non-empty")
        if self.encounter_type == EncounterType.COMBAT and not self.enemies:
            raise ValueError(f"Combat encounter '{self.id}' must have at least one enemy")
        if self.encounter_type == EncounterType.EVENT and not self.choices:
            raise ValueError(f"Event encounter '{self.id}' must have at least one choice")


# ---------------------------------------------------------------------------
# Outpost / sector naming — per-lore naming conventions.
# ---------------------------------------------------------------------------

OUTPOST_NAMES: dict[tuple[int, int], str] = {
    (1, 5): "Outpost Alpha",
    (6, 10): "Outpost Bravo",
    (11, 15): "Outpost Charlie",
    (16, 20): "Outpost Delta",
    (21, 25): "Command Fortress",
}


def outpost_name_for_floor(floor_number: int) -> str:
    """Return the outpost name for a given floor number (1-25).

    Args:
        floor_number: 1-based floor index.

    Returns:
        The outpost name string.

    Raises:
        ValueError: If floor_number is outside [1, 25].
    """
    if not (1 <= floor_number <= 25):
        raise ValueError(f"floor_number {floor_number} out of range [1, 25]")
    for (start, end), name in OUTPOST_NAMES.items():
        if start <= floor_number <= end:
            return name
    # Fallback (should not happen if OUTPOST_NAMES covers 1-25)
    return "Unknown Sector"


@dataclass(frozen=True)
class Floor:
    """A single floor (outpost level) in the campaign.

    Each floor contains a list of encounters.  The player selects one
    encounter to engage, then advances to the next floor.
    """

    number: int
    """1-based floor number."""

    encounters: list[Encounter]
    """Encounters available on this floor."""

    narrative_text: str = ""
    """Intro text shown when the floor is first loaded."""

    outpost_name: str = ""
    """Human-readable outpost label (auto-derived from number)."""

    def __post_init__(self) -> None:
        """Auto-derive outpost name if not provided."""
        if not self.outpost_name:
            object.__setattr__(self, "outpost_name", outpost_name_for_floor(self.number))

    def validate(self) -> None:
        """Raise ``ValueError`` if the floor is malformed.

        Raises:
            ValueError: If ``number`` is outside [1, 25], there are no
                encounters, or any encounter fails validation.
        """
        if not (1 <= self.number <= 25):
            raise ValueError(f"floor number {self.number} out of range [1, 25]")
        if not self.encounters:
            raise ValueError(f"Floor {self.number} must have at least one encounter")
        for enc in self.encounters:
            enc.validate()
