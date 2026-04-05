"""JSON data loaders — read, validate, and construct model objects.

Each loader function reads a specific JSON file, validates the schema,
and returns a list or dict of model instances.  All loaders raise
``ValueError`` with descriptive messages on invalid data.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.models.card import Directive, DirectiveType, TargetPattern
from src.models.equipment import Equipment
from src.models.faction import Faction, IFFShape
from src.models.mech import MechFrame
from src.models.pilot import Pilot

logger = logging.getLogger(__name__)

# Base path for all data files (project root / data).
_DATA_ROOT = Path(__file__).resolve().parents[2] / "data"

# ---------------------------------------------------------------------------
# Enum look-up tables for JSON string → enum conversion.
# ---------------------------------------------------------------------------

_FACTION_MAP: dict[str, Faction] = {
    "FSA": Faction.FSA,
    "CRIMSON_COMPACT": Faction.CRIMSON_COMPACT,
    "REBEL": Faction.REBEL,
}

_IFF_MAP: dict[str, IFFShape] = {
    "SQUARE": IFFShape.SQUARE,
    "DIAMOND": IFFShape.DIAMOND,
    "HEXAGON": IFFShape.HEXAGON,
    "CIRCLE_CROSS": IFFShape.CIRCLE_CROSS,
    "CHEVRON": IFFShape.CHEVRON,
    "TRIANGLE": IFFShape.TRIANGLE,
    "RECTANGLE": IFFShape.RECTANGLE,
    "CIRCLE": IFFShape.CIRCLE,
    "CROSS": IFFShape.CROSS,
}

_DIRECTIVE_TYPE_MAP: dict[str, DirectiveType] = {
    "COMBAT": DirectiveType.COMBAT,
    "MOVEMENT": DirectiveType.MOVEMENT,
    "REPAIR": DirectiveType.REPAIR,
    "UTILITY": DirectiveType.UTILITY,
}

_PATTERN_MAP: dict[str, TargetPattern] = {
    "NONE": TargetPattern.NONE,
    "SINGLE": TargetPattern.SINGLE,
    "LINE": TargetPattern.LINE,
    "CONE": TargetPattern.CONE,
    "AREA": TargetPattern.AREA,
    "SELF": TargetPattern.SELF,
    "ALL_HOSTILES": TargetPattern.ALL_HOSTILES,
}


def _load_json(path: Path) -> Any:
    """Load and return parsed JSON from *path*.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Data file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------------------
# Mech frame loader
# ---------------------------------------------------------------------------


def load_mech_frames(path: Path | None = None) -> list[MechFrame]:
    """Load mech frame definitions from JSON.

    Args:
        path: Optional override path.  Defaults to ``data/mechs/*.json``.

    Returns:
        List of validated ``MechFrame`` objects.

    Raises:
        ValueError: If any frame fails validation.
    """
    if path is None:
        # Load all mech JSON files from all subdirectories.
        frames: list[MechFrame] = []
        mech_dir = _DATA_ROOT / "mechs"
        for json_file in sorted(mech_dir.glob("*.json")):
            frames.extend(load_mech_frames(json_file))
        return frames

    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data).__name__}")

    frames = []
    for entry in data:
        faction = _FACTION_MAP.get(entry.get("faction", ""))
        if faction is None:
            raise ValueError(f"Invalid faction '{entry.get('faction')}' in {path}")
        iff = _IFF_MAP.get(entry.get("iff_shape", "SQUARE"), IFFShape.SQUARE)
        equip: dict[str, str | None] = entry.get("equipment_slots", {})

        frame = MechFrame(
            id=entry["id"],
            name=entry["name"],
            faction=faction,
            hp=entry["hp"],
            overload=entry["overload"],
            evasion=entry.get("evasion", 0),
            iff_shape=iff,
            starting_directives=entry.get("starting_directives", []),
            equipment_slots={k: v for k, v in equip.items() if v is not None},
            trait=entry.get("trait", ""),
            role=entry.get("role", ""),
        )
        frame.validate()
        frames.append(frame)
    logger.info("Loaded %d mech frames from %s", len(frames), path.name)
    return frames


# ---------------------------------------------------------------------------
# Equipment loader
# ---------------------------------------------------------------------------


def load_equipment(path: Path | None = None) -> list[Equipment]:
    """Load equipment definitions from JSON.

    Returns:
        List of validated ``Equipment`` objects.
    """
    if path is None:
        equip_dir = _DATA_ROOT / "equipment"
        items: list[Equipment] = []
        for json_file in sorted(equip_dir.glob("*.json")):
            items.extend(load_equipment(json_file))
        return items

    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data).__name__}")

    items = []
    for entry in data:
        equip = Equipment(
            id=entry["id"],
            name=entry["name"],
            slot=entry["slot"],
            damage_bonus=entry.get("damage_bonus", 0),
            hp_bonus=entry.get("hp_bonus", 0),
            evasion_bonus=entry.get("evasion_bonus", 0),
            ol_discount=entry.get("ol_discount", 0),
            directives_granted=entry.get("directives_granted", []),
            description=entry.get("description", ""),
        )
        equip.validate()
        items.append(equip)
    logger.info("Loaded %d equipment items from %s", len(items), path.name)
    return items


# ---------------------------------------------------------------------------
# Pilot loader
# ---------------------------------------------------------------------------


def load_pilots(path: Path | None = None) -> dict[str, Pilot]:
    """Load pilot operator type definitions from JSON.

    Returns:
        Dict mapping operator_type string → ``Pilot`` object.
    """
    if path is None:
        pilot_dir = _DATA_ROOT / "pilots"
        result: dict[str, Pilot] = {}
        for json_file in sorted(pilot_dir.glob("*.json")):
            result.update(load_pilots(json_file))
        return result

    data = _load_json(path)
    if not isinstance(data, dict) or "operator_types" not in data:
        raise ValueError(f"Expected {{'operator_types': ...}} in {path}")

    result = {}
    for key, entry in data["operator_types"].items():
        pilot = Pilot(
            callsign=entry.get("callsign", key),
            operator_type=key,
            damage_bonus=entry.get("damage_bonus", 0),
            hp_bonus=entry.get("hp_bonus", 0),
            ol_bonus=entry.get("ol_bonus", 0),
            evasion_bonus=entry.get("evasion_bonus", 0),
            starting_directives=entry.get("starting_directives", []),
        )
        pilot.validate()
        result[key] = pilot
    logger.info("Loaded %d pilot types from %s", len(result), path.name)
    return result


# ---------------------------------------------------------------------------
# Directive loader
# ---------------------------------------------------------------------------


def load_directives(path: Path | None = None) -> dict[str, Directive]:
    """Load directive (card) definitions from JSON.

    Returns:
        Dict mapping directive ID → ``Directive`` object.
    """
    if path is None:
        card_dir = _DATA_ROOT / "cards"
        result: dict[str, Directive] = {}
        for json_file in sorted(card_dir.glob("*.json")):
            result.update(load_directives(json_file))
        return result

    data = _load_json(path)
    if not isinstance(data, list):
        raise ValueError(f"Expected list in {path}, got {type(data).__name__}")

    result = {}
    for entry in data:
        dtype = _DIRECTIVE_TYPE_MAP.get(entry.get("directive_type", ""))
        if dtype is None:
            raise ValueError(f"Invalid directive_type '{entry.get('directive_type')}' in {path}")
        pattern = _PATTERN_MAP.get(entry.get("pattern", "NONE"), TargetPattern.NONE)
        keywords = frozenset(entry.get("keywords", []))

        directive = Directive(
            id=entry["id"],
            name=entry["name"],
            directive_type=dtype,
            damage=entry.get("damage", 0),
            heal=entry.get("heal", 0),
            overload_cost=entry.get("overload_cost", 0),
            range_=entry.get("range_", 0),
            move_range=entry.get("move_range", 0),
            pattern=pattern,
            keywords=keywords,
            description=entry.get("description", ""),
        )
        directive.validate()
        if directive.id in result:
            raise ValueError(f"Duplicate directive id '{directive.id}' in {path}")
        result[directive.id] = directive
    logger.info("Loaded %d directives from %s", len(result), path.name)
    return result


# ---------------------------------------------------------------------------
# Master loader — convenience function that loads everything.
# ---------------------------------------------------------------------------


class GameData:
    """Container for all loaded game data.

    Use :func:`load_all_data` to populate this.
    """

    def __init__(self) -> None:
        """Create an empty data container."""
        self.mech_frames: list[MechFrame] = []
        self.equipment: list[Equipment] = []
        self.pilots: dict[str, Pilot] = {}
        self.directives: dict[str, Directive] = {}

    def get_mech(self, mech_id: str) -> MechFrame | None:
        """Look up a mech frame by ID."""
        for frame in self.mech_frames:
            if frame.id == mech_id:
                return frame
        return None

    def get_equipment(self, equip_id: str) -> Equipment | None:
        """Look up equipment by ID."""
        for eq in self.equipment:
            if eq.id == equip_id:
                return eq
        return None

    def get_directive(self, directive_id: str) -> Directive | None:
        """Look up a directive by ID."""
        return self.directives.get(directive_id)

    def get_pilot(self, operator_type: str) -> Pilot | None:
        """Look up a pilot by operator type."""
        return self.pilots.get(operator_type)


def load_all_data() -> GameData:
    """Load all JSON data files and return a populated ``GameData``.

    Returns:
        A ``GameData`` instance with all mechs, equipment, pilots, and
        directives loaded and validated.

    Raises:
        ValueError: If any data file fails validation.
    """
    data = GameData()
    data.mech_frames = load_mech_frames()
    data.equipment = load_equipment()
    data.pilots = load_pilots()
    data.directives = load_directives()
    logger.info(
        "All data loaded — %d mechs, %d equipment, %d pilots, %d directives",
        len(data.mech_frames),
        len(data.equipment),
        len(data.pilots),
        len(data.directives),
    )
    return data
