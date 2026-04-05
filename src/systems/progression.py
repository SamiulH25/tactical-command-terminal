"""Floor progression manager — controls the 25-floor campaign flow.

Overhauled to use the new mission system and grid layouts.  Each floor
now features:
- Dynamic mission types (Patrol, Assault, Defense, Extraction, etc.)
- Varied enemy compositions based on floor and mission type
- Grid layouts selected from named battlefield configurations
- Boss encounters on milestone floors (5, 10, 15, 20, 25)
- Elite encounters with tougher enemies and better rewards
- Rich narrative text that scales with floor progression

Lore framing: Each floor represents an outpost or sector the FSA is
pushing through. The Coordinator receives updated telemetry data for
each new sector, with signal degrading and re-acquiring between floors.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.models.campaign import Campaign
from src.models.encounter import Encounter
from src.models.missions import (
    generate_combat_encounter,
    generate_event_encounter,
    generate_merchant_encounter,
    generate_rest_encounter,
    is_boss_floor,
)


@dataclass(frozen=True)
class FloorTemplate:
    """A pre-defined encounter layout for a floor.

    Each floor has 3 encounter nodes the player can choose between:
    - 1 combat encounter (mandatory progression)
    - 1 event or merchant (optional)
    - 1 rest (optional)
    """

    floor_number: int
    combat: Encounter
    optional_a: Encounter
    optional_b: Encounter
    narrative_intro: str = ""
    narrative_outro: str = ""


# ---------------------------------------------------------------------------
# Floor-specific narrative text
# ---------------------------------------------------------------------------

FLOOR_NARRATIVES: dict[int, tuple[str, str]] = {
    1: (
        "INSERTION COMPLETE. Dropship touch-down confirmed.",
        "Outpost Alpha perimeter secured. First contact made.",
    ),
    2: (
        "Second floor breached. Enemy resistance minimal.",
        "Scout reports: CC forces falling back to prepared positions.",
    ),
    3: (
        "Sector sweep complete. Hostile signatures confirmed.",
        "Enemy adapting to our tactics. Adjust your approach.",
    ),
    4: (
        "Forward momentum maintained. Fourth floor active.",
        "Intercepted comm: CC commander requests reinforcements.",
    ),
    5: (
        "BOSS FLOOR: Crimson Compact Commander detected.",
        "Outpost Alpha CLEARED. CC forces retreating to Bravo. Resistance will increase.",
    ),
    6: (
        "New sector entered. Outpost Bravo perimeter detected.",
        "Enemy fortifications denser here. Stay sharp, Coordinator.",
    ),
    7: (
        "Bravo sector engagement underway.",
        "CC deploying heavier units. Expect increased resistance.",
    ),
    8: (
        "Deepening push into Bravo territory.",
        "Supply lines stretching. Salvage operations recommended.",
    ),
    9: (
        "Penetrating outer Bravo defences.",
        "Intelligence: CC war council detected in sector.",
    ),
    10: (
        "BOSS FLOOR: Outpost Bravo Commander identified.",
        "Outpost Bravo CLEARED. Half the planet's defences down. Charlie awaits.",
    ),
    11: (
        "Deep enemy territory. No turning back.",
        "All comms jammed. Telemetry feed unstable.",
    ),
    12: (
        "Charlie perimeter breached. Heavy contact.",
        "CC field marshal coordinating defences personally.",
    ),
    13: (
        "Charlie sector advance. Enemy dig-in confirmed.",
        "Trench networks and bunkers detected throughout sector.",
    ),
    14: (
        "Pushing through Charlie heartland.",
        "Elite hostile signatures multiplying. Exercise extreme caution.",
    ),
    15: (
        "BOSS FLOOR: Charlie sector warlord located.",
        "Outpost Charlie CLEARED. Command fortress within reach.",
    ),
    16: (
        "Final approach. Enemy fortress defences active.",
        "No supply lines. No reinforcements. Push forward.",
    ),
    17: (
        "Fortress outer defences engaged.",
        "CC deploying everything they have left. Maximum threat level.",
    ),
    18: (
        "Breaking through fortress mid-layer.",
        "Enemy commander broadcasting rallying frequencies. Morale critical.",
    ),
    19: (
        "Fortress core approaching. Resistance fanatical.",
        "All CC remnants converging on command centre.",
    ),
    20: (
        "BOSS FLOOR: Fortress deputy commander engaged.",
        "Outpost Delta CLEARED. One fortress remains. Final assault imminent.",
    ),
    21: (
        "Final sector. Everything enemy has is here.",
        "CC general mobilising personal guard. Prepare for decisive battle.",
    ),
    22: (
        "Closing on command centre.",
        "Enemy desperate. Expect unconventional tactics.",
    ),
    23: (
        "Final defences crumbling. Push through.",
        "CC command signal strengthening. They know we're coming.",
    ),
    24: (
        "Outer command breached. Final floor ahead.",
        "All units stand by for decisive engagement.",
    ),
    25: (
        "FINAL ASSAULT. Enemy commander awaits.",
        "This is it. All or nothing, Coordinator.",
    ),
}


def _default_floor(floor_num: int) -> FloorTemplate:
    """Generate a floor template using the new mission system.

    Args:
        floor_num: 1-based floor number (1-25).

    Returns:
        A ``FloorTemplate`` with combat, optional, and rest encounters.
    """
    intro, outro = FLOOR_NARRATIVES.get(
        floor_num,
        (
            f"Floor {floor_num:02d} telemetry acquired. Sector scan complete.",
            f"Floor {floor_num:02d} status updated. Awaiting orders.",
        ),
    )

    # Combat encounter — uses the new mission system
    force_boss = is_boss_floor(floor_num)
    combat = generate_combat_encounter(floor_num, force_boss=force_boss)

    # Optional A: alternate between merchant and event
    if floor_num % 3 == 0:
        optional_a = generate_merchant_encounter(floor_num)
    else:
        optional_a = generate_event_encounter(floor_num)

    # Optional B: rest
    optional_b = generate_rest_encounter(floor_num)

    return FloorTemplate(
        floor_number=floor_num,
        combat=combat,
        optional_a=optional_a,
        optional_b=optional_b,
        narrative_intro=intro,
        narrative_outro=outro,
    )


@dataclass
class FloorProgression:
    """Manages the sequential flow through 25 floors.

    Usage::

        progression = FloorProgression(campaign)
        template = progression.get_floor_template()  # Current floor
        progression.advance()  # Move to next floor
    """

    campaign: Campaign
    _templates: dict[int, FloorTemplate] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Pre-generate all 25 floor templates."""
        for i in range(1, 26):
            self._templates[i] = _default_floor(i)

    def get_floor_template(self) -> FloorTemplate | None:
        """Return the template for the current campaign floor.

        Returns:
            The floor template, or ``None`` if floor 0 (pre-deployment).
        """
        if self.campaign.current_floor <= 0:
            return None
        return self._templates.get(self.campaign.current_floor)

    def get_encounters(self) -> list[Encounter] | None:
        """Return the list of encounters for the current floor.

        Returns:
            [combat, optional_a, optional_b] or ``None``.
        """
        template = self.get_floor_template()
        if template is None:
            return None
        return [template.combat, template.optional_a, template.optional_b]

    def advance(self) -> int:
        """Advance to the next floor and return the new floor number.

        Updates the campaign's floor counter and records the floor
        as cleared.

        Returns:
            The new floor number.

        Raises:
            ValueError: If already at floor 25.
        """
        old_floor = self.campaign.current_floor
        new_floor = self.campaign.advance_floor()
        self.campaign.floors_cleared = old_floor
        return new_floor

    def get_transition_text(self, from_floor: int, to_floor: int) -> str:
        """Generate the terminal transition text between two floors.

        Lore-accurate format::

            > UPLOADING SECTOR DATA...
            > SECTOR N LOADED
            > SIGNAL RE-ACQUIRED

        Args:
            from_floor: The floor we're leaving.
            to_floor: The floor we're entering.

        Returns:
            Multi-line transition string.
        """
        template = self._templates.get(to_floor)
        intro = template.narrative_intro if template else ""
        lines = [
            "> UPLOADING SECTOR DATA...",
            f"> SECTOR {to_floor:02d} LOADED",
        ]
        if intro:
            lines.append(f"> {intro}")
        lines.append("> SIGNAL RE-ACQUIRED")
        return "\n".join(lines)

    def get_outpost_name(self) -> str:
        """Return the outpost name for the current floor."""
        return self.campaign.outpost_name
