"""Save/load system — serializes and deserializes game state to JSON.

The save file contains all persistent campaign state:
- Campaign progress (current floor, credits, stats)
- Decision log (array of choice IDs)
- Faction reputation scores
- Rescued allies
- Unlocked equipment and mech frames

Save files are versioned for future migration.  Corrupted or outdated
saves are rejected with a clear error message.

Lore framing:  Save files are "session snapshots" uploaded to the
command vessel's archive system.  Loading is "restoring session from
checkpoint."
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.models.campaign import Campaign

logger = logging.getLogger(__name__)

# Current save file version.  Increment when schema changes.
_SAVE_VERSION: int = 1

# Default save directory (relative to project root)
_SAVE_DIR: Path = Path("saves")


@dataclass(frozen=True)
class SaveData:
    """Complete save file contents.

    Invariants:
    - ``version`` matches _SAVE_VERSION for current saves.
    - ``campaign`` is a valid campaign dict.
    """

    version: int
    """Save file schema version."""

    campaign: dict[str, Any]
    """Serialized campaign state."""

    # Future fields (Phase 8+):
    # deck: list[str]  # Current deck state
    # equipment: list[str]  # Currently equipped items

    def validate(self) -> None:
        """Raise ``ValueError`` if save data is invalid.

        Raises:
            ValueError: If version doesn't match or campaign data is missing.
        """
        if self.version != _SAVE_VERSION:
            raise ValueError(
                f"Save version {self.version} does not match expected version {_SAVE_VERSION}"
            )
        if not self.campaign:
            raise ValueError("Save data missing campaign information")


@dataclass(frozen=True)
class SaveMetadata:
    """Summary info shown in the resume session list."""

    version: int
    current_floor: int
    outpost_name: str
    floors_cleared: int
    credits: int
    timestamp: str  # ISO format timestamp


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def campaign_to_dict(campaign: Campaign) -> dict[str, Any]:
    """Serialize a Campaign to a dictionary for JSON storage.

    Args:
        campaign: The campaign to serialize.

    Returns:
        Dictionary with all campaign fields.
    """
    return {
        "current_floor": campaign.current_floor,
        "decision_log": list(campaign.decision_log),
        "reputation": dict(campaign.reputation),
        "enemies_defeated": campaign.enemies_defeated,
        "cards_played": campaign.cards_played,
        "credits_earned": campaign.credits_earned,
        "casualties": campaign.casualties,
        "floors_cleared": campaign.floors_cleared,
        "current_credits": campaign.current_credits,
        "unlocked_equipment": list(campaign.unlocked_equipment),
        "unlocked_mechs": list(campaign.unlocked_mechs),
        "allies_rescued": list(campaign.allies_rescued),
    }


def dict_to_campaign(data: dict[str, Any]) -> Campaign:
    """Deserialize a campaign dictionary back to a Campaign object.

    Args:
        data: Dictionary from :func:`campaign_to_dict`.

    Returns:
        A populated Campaign object.
    """
    campaign = Campaign(
        current_floor=data.get("current_floor", 0),
        decision_log=list(data.get("decision_log", [])),
        reputation=dict(data.get("reputation", {})),
        enemies_defeated=data.get("enemies_defeated", 0),
        cards_played=data.get("cards_played", 0),
        credits_earned=data.get("credits_earned", 0),
        casualties=data.get("casualties", 0),
        floors_cleared=data.get("floors_cleared", 0),
        current_credits=data.get("current_credits", 150),
        unlocked_equipment=list(data.get("unlocked_equipment", [])),
        unlocked_mechs=list(data.get("unlocked_mechs", [])),
        allies_rescued=list(data.get("allies_rescued", [])),
    )
    campaign.validate()
    return campaign


def create_save_data(campaign: Campaign) -> SaveData:
    """Create a SaveData snapshot from the current campaign.

    Args:
        campaign: The campaign to save.

    Returns:
        A validated SaveData object.
    """
    save = SaveData(
        version=_SAVE_VERSION,
        campaign=campaign_to_dict(campaign),
    )
    save.validate()
    return save


# ---------------------------------------------------------------------------
# File I/O
# ---------------------------------------------------------------------------


def get_save_path(slot: int = 1) -> Path:
    """Return the file path for a save slot.

    Args:
        slot: Save slot number (1-3).

    Returns:
        Path to the save file.

    Raises:
        ValueError: If slot is not 1-3.
    """
    if not (1 <= slot <= 3):
        raise ValueError(f"Save slot must be 1-3, got {slot}")
    return _SAVE_DIR / f"slot_{slot}.json"


def save_game(campaign: Campaign, slot: int = 1) -> Path:
    """Save the current campaign state to a file.

    Args:
        campaign: The campaign to save.
        slot: Save slot number (1-3).

    Returns:
        The path the save was written to.

    Raises:
        ValueError: If save data validation fails.
        OSError: If the file cannot be written.
    """
    save_data = create_save_data(campaign)
    save_path = get_save_path(slot)
    save_path.parent.mkdir(parents=True, exist_ok=True)

    save_dict = {
        "version": save_data.version,
        "campaign": save_data.campaign,
    }

    with save_path.open("w", encoding="utf-8") as fh:
        json.dump(save_dict, fh, indent=2)

    logger.info("Game saved to slot %d: %s", slot, save_path)
    return save_path


def load_game(slot: int = 1) -> Campaign | None:
    """Load a campaign from a save slot.

    Args:
        slot: Save slot number (1-3).

    Returns:
        The loaded Campaign, or ``None`` if the slot is empty.

    Raises:
        ValueError: If the save file is corrupted or version mismatch.
        FileNotFoundError: If the save file does not exist.
    """
    save_path = get_save_path(slot)
    if not save_path.is_file():
        return None

    with save_path.open("r", encoding="utf-8") as fh:
        raw: dict[str, Any] = json.load(fh)

    version = raw.get("version", 0)
    if version != _SAVE_VERSION:
        raise ValueError(
            f"Save slot {slot} is version {version}, "
            f"expected {_SAVE_VERSION}.  "
            f"Save file may be from a different game version."
        )

    campaign_data = raw.get("campaign")
    if campaign_data is None:
        raise ValueError(f"Save slot {slot} is corrupted (missing campaign)")

    campaign = dict_to_campaign(campaign_data)
    logger.info("Game loaded from slot %d: %s", slot, save_path)
    return campaign


def get_save_metadata(slot: int = 1) -> SaveMetadata | None:
    """Return summary info for a save slot without full deserialization.

    Args:
        slot: Save slot number (1-3).

    Returns:
        SaveMetadata if the slot exists, else ``None``.
    """
    save_path = get_save_path(slot)
    if not save_path.is_file():
        return None

    try:
        with save_path.open("r", encoding="utf-8") as fh:
            raw: dict[str, Any] = json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None

    camp = raw.get("campaign", {})
    from src.models.encounter import outpost_name_for_floor

    floor = camp.get("current_floor", 0)
    outpost = "Pre-Deployment"
    if floor > 0:
        try:
            outpost = outpost_name_for_floor(floor)
        except ValueError:
            outpost = "Unknown Sector"

    return SaveMetadata(
        version=raw.get("version", 0),
        current_floor=floor,
        outpost_name=outpost,
        floors_cleared=camp.get("floors_cleared", 0),
        credits=camp.get("current_credits", 0),
        timestamp=save_path.stat().st_mtime.__str__(),
    )


def delete_save(slot: int = 1) -> bool:
    """Delete a save file.

    Args:
        slot: Save slot number (1-3).

    Returns:
        ``True`` if the file was deleted, ``False`` if it didn't exist.
    """
    save_path = get_save_path(slot)
    if save_path.is_file():
        save_path.unlink()
        logger.info("Save slot %d deleted", slot)
        return True
    return False
