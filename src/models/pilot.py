"""Pilot definitions — operator types and their combat modifiers.

Pilots are assigned to a mech frame and provide passive bonuses that
affect how the mech performs in combat.  The pilot's callsign is chosen
at deployment time; the operator type is selected from a predefined pool.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Pilot:
    """A mech pilot / operator.

    Pilots provide passive modifiers that are applied on top of the mech
    frame's base stats.  The ``callsign`` is set at deployment; the
    ``operator_type`` is chosen from the available pool.
    """

    callsign: str
    """Player-chosen or default callsign (e.g. ``"Alpha-1"``)."""

    operator_type: str
    """Pilot archetype: ``"aggressive"``, ``"defensive"``, ``"tactical"``,
    ``"scout"``, ``"engineer"``.  Each type grants different bonuses."""

    damage_bonus: int = 0
    """Flat damage bonus applied to all attack directives."""

    hp_bonus: int = 0
    """Flat HP bonus added to the mech's maximum HP."""

    ol_bonus: int = 0
    """Additional overload capacity."""

    evasion_bonus: int = 0
    """Evasion percentage bonus."""

    starting_directives: list[str] = field(default_factory=list)
    """Extra directive IDs granted to the starting deck."""

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is invalid.

        Raises:
            ValueError: If ``callsign`` or ``operator_type`` is empty,
                or numeric bonuses exceed plausible bounds.
        """
        if not self.callsign:
            raise ValueError("Pilot callsign must be non-empty")
        if not self.operator_type:
            raise ValueError("Pilot operator_type must be non-empty")
        valid_types = {"aggressive", "defensive", "tactical", "scout", "engineer"}
        if self.operator_type not in valid_types:
            raise ValueError(f"operator_type '{self.operator_type}' not in {valid_types}")
        if not (-50 <= self.damage_bonus <= 50):
            raise ValueError(f"damage_bonus {self.damage_bonus} out of range [-50, 50]")
        if not (-500 <= self.hp_bonus <= 500):
            raise ValueError(f"hp_bonus {self.hp_bonus} out of range [-500, 500]")
        if not (0 <= self.ol_bonus <= 50):
            raise ValueError(f"ol_bonus {self.ol_bonus} out of range [0, 50]")
        if not (-30 <= self.evasion_bonus <= 30):
            raise ValueError(f"evasion_bonus {self.evasion_bonus} out of range [-30, 30]")
