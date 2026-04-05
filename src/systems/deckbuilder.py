"""Deck composition — builds a combat deck from mech, pilot, and equipment.

A mech's starting deck is the **sum of its parts**:

1. **Frame directives** — ``MechFrame.starting_directives``
2. **Pilot directives** — ``Pilot.starting_directives``
3. **Equipment directives** — ``Equipment.directives_granted`` for each
   equipped item (weapon, armour, utility slots)

The ``compose_deck()`` function resolves all three sources into a single
flat list of directive IDs.  The actual ``Directive`` objects are resolved
later by the combat system when it loads the full card pool.
"""

from __future__ import annotations

from src.models.data_loader import GameData
from src.models.mech import DeployedMech, MechFrame
from src.models.pilot import Pilot


def _resolve_equipment_directives(
    mech_frame: MechFrame,
    game_data: GameData,
) -> list[str]:
    """Collect directive IDs granted by a mech frame's equipped items.

    For each equipment slot defined on the frame, look up the equipment
    in ``game_data`` and gather its ``directives_granted`` list.

    Args:
        mech_frame: The mech frame with equipment slot definitions.
        game_data: Loaded game data containing all equipment.

    Returns:
        Flat list of directive IDs from all equipped items.
    """
    directives: list[str] = []
    for _slot_name, equip_id in mech_frame.equipment_slots.items():
        if equip_id is None:
            continue
        equip = game_data.get_equipment(equip_id)
        if equip is None:
            continue
        directives.extend(equip.directives_granted)
    return directives


def compose_deck(
    mech_frame: MechFrame,
    pilot: Pilot,
    game_data: GameData,
) -> list[str]:
    """Build the complete starting deck from all mech parts.

    The deck is assembled in this order:
    1. Frame starting directives (the core deck)
    2. Pilot starting directives (archetype additions)
    3. Equipment granted directives (weapon / armour / utility extras)

    Args:
        mech_frame: The base mech frame template.
        pilot: The pilot assigned to this mech.
        game_data: Loaded game data for equipment look-up.

    Returns:
        A flat list of directive IDs forming the starting deck.
    """
    deck: list[str] = []

    # 1. Frame directives
    deck.extend(mech_frame.starting_directives)

    # 2. Pilot directives
    deck.extend(pilot.starting_directives)

    # 3. Equipment directives
    deck.extend(_resolve_equipment_directives(mech_frame, game_data))

    return deck


def build_deployed_mech(
    mech_frame: MechFrame,
    pilot: Pilot,
    game_data: GameData,
    callsign: str | None = None,
) -> DeployedMech:
    """Create a fully configured ``DeployedMech`` ready for combat.

    This function composes the deck from all parts, applies pilot and
    equipment stat bonuses to the frame's base values, and returns a
    mutable combat-ready mech.

    Args:
        mech_frame: The base mech frame template.
        pilot: The pilot assigned to this mech.
        game_data: Loaded game data for equipment look-up.
        callsign: Override for the pilot's callsign.  Defaults to the
            pilot's archetype name.

    Returns:
        A ``DeployedMech`` with HP/OL/deck computed from all parts.
    """
    assigned_callsign = callsign if callsign is not None else pilot.callsign

    # --- Compute composite stats from all parts ---
    max_hp = mech_frame.hp + pilot.hp_bonus
    max_ol = mech_frame.overload + pilot.ol_bonus
    weapon_bonus = pilot.damage_bonus
    evasion = mech_frame.evasion + pilot.evasion_bonus
    ol_discount = 0

    # Apply equipment modifiers
    for _slot_name, equip_id in mech_frame.equipment_slots.items():
        if equip_id is None:
            continue
        equip = game_data.get_equipment(equip_id)
        if equip is None:
            continue
        max_hp += equip.hp_bonus
        evasion += equip.evasion_bonus
        if equip.slot == "weapon":
            weapon_bonus += equip.damage_bonus
        ol_discount += equip.ol_discount

    # Ensure non-negative derived values
    max_hp = max(1, max_hp)
    evasion = max(0, min(100, evasion))
    ol_discount = max(0, ol_discount)

    # --- Compose the deck from all parts ---
    deck = compose_deck(mech_frame, pilot, game_data)

    mech = DeployedMech(
        frame=mech_frame,
        pilot_callsign=assigned_callsign,
        pilot_type=pilot.operator_type,
        max_hp=max_hp,
        max_ol=max_ol,
        current_hp=max_hp,
        current_ol=0,
        weapon_bonus=weapon_bonus,
        evasion=evasion,
        ol_discount=ol_discount,
        deck=deck,
    )
    mech.validate()
    return mech
