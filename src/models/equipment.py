"""Equipment definitions — weapons, armour, and utility modules.

Each equipment piece is a frozen dataclass loaded from JSON.  Equipment
provides passive modifiers (damage, HP, evasion) and/or grants directives
to the mech's deck.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Equipment:
    """A single equipment module that can be slotted on a mech.

    Invariants:
    - ``damage_bonus`` and ``hp_bonus`` may be negative (e.g. heavy weapon
      reduces HP due to weight).
    - ``directives_granted`` contains directive IDs, resolved at load time.
    """

    id: str
    """Unique equipment identifier (e.g. ``"autocannon_mk1"``)."""

    name: str
    """Human-readable name (e.g. ``"Autocannon Mk.1"``)."""

    slot: str
    """Equipment slot: ``"weapon"``, ``"armor"``, or ``"utility"``."""

    damage_bonus: int = 0
    """Flat damage modifier applied to all attack directives."""

    hp_bonus: int = 0
    """Flat HP modifier applied to the mech's maximum HP."""

    evasion_bonus: int = 0
    """Flat evasion modifier (percentage chance to dodge an attack)."""

    ol_discount: int = 0
    """Reduces overload cost of directives of matching type."""

    directives_granted: list[str] = field(default_factory=list)
    """List of directive IDs added to the mech's deck when equipped."""

    description: str = ""
    """Short lore text shown in the briefing screen."""

    def validate(self) -> None:
        """Raise ``ValueError`` if any field is out of range.

        Raises:
            ValueError: If ``id`` or ``name`` is empty, ``slot`` is invalid,
                or numeric values exceed plausible bounds.
        """
        if not self.id:
            raise ValueError("Equipment id must be non-empty")
        if not self.name:
            raise ValueError("Equipment name must be non-empty")
        valid_slots = {"weapon", "armor", "utility"}
        if self.slot not in valid_slots:
            raise ValueError(f"Equipment slot '{self.slot}' not in {valid_slots}")
        if not (-100 <= self.damage_bonus <= 100):
            raise ValueError(f"damage_bonus {self.damage_bonus} out of range [-100, 100]")
        if not (-1000 <= self.hp_bonus <= 1000):
            raise ValueError(f"hp_bonus {self.hp_bonus} out of range [-1000, 1000]")
        if not (-50 <= self.evasion_bonus <= 50):
            raise ValueError(f"evasion_bonus {self.evasion_bonus} out of range [-50, 50]")
        if not (0 <= self.ol_discount <= 10):
            raise ValueError(f"ol_discount {self.ol_discount} out of range [0, 10]")
